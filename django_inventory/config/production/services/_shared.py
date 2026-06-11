"""Shared service primitives — authorization helpers across stages.

YEH FILE KYU HAI?
─────────────────
Stages (layering, cutting, future) share role/skill auth gates. Common code
lives here so per-stage service files stay focused on the stage's own state
transitions.

Pattern (per-stage service file):
    from production.services._shared import (
        _ensure_can_manage, _ensure_management, _ensure_assigned_worker, ...
    )
"""
from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError

from accounts.skills import SKILL_CUTTING_MASTER_HELPER, user_has_skill
from accounts.services import MANAGEMENT_ROLES, PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role
from production.constants import STAGE_LAYERING
from production.models import Adda, AddaStageRecord

logger = logging.getLogger(__name__)


def _ensure_can_manage(user):
    """Production role gate (super_admin / manager / worker)."""
    if not user_has_role(user, PRODUCTION_ROLES):
        raise PermissionDenied("requires production role")


def _ensure_management(user):
    """Management role gate ({super_admin, manager}). For worker assignment etc."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("requires management role (super_admin/manager)")


def _ensure_assigned_worker(stage_record: AddaStageRecord, user):
    """User is assigned worker OR management. Super_admin bypasses via role."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    # V2-1b: assignment = an active (non-cancelled) WorkerStageTask, not the M2M.
    if not stage_record.is_worker_assigned(user):
        raise PermissionDenied("not assigned to this stage")


def _ensure_layering_skill(user):
    """Layering stage ACCESS gate — P3.1: data-driven via Stage.access_by_skill/role
    (the SAME policy the view gate uses, so view + mutation access stay consistent;
    management bypass is built into user_can_access_stage). Adding/retuning a stage's
    skills is now pure config — no edit here."""
    # Lazy import: access_service is a sibling in production.services.
    from production.services.access_service import user_can_access_stage
    if not user_can_access_stage(user, STAGE_LAYERING):
        raise PermissionDenied("requires access to the Layering stage")


def _ensure_can_complete_layering(user):
    """Layering→Cutting transition: only cutting_master_helper (super_admin bypass)."""
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied("only cutting_master_helper can complete Layering stage")


# ── Shared stage-reopen skeleton (Template Method) ───────────────────────────

def reopen_stage_record(*, adda: Adda, stage_code: str, stage_label: str, user,
                        guard=None, teardown=None) -> AddaStageRecord:
    """Common skeleton for every per-stage `reopen_*` service (layering / cutting /
    cutting_pattern / barcode_generation). Owns the invariant ALL reopens share;
    each stage passes its OWN `guard` + `teardown` so the stage-specific logic
    stays local + visible at the call site (no hidden framework).

    Skeleton (in order):
      1. management-role gate
      2. find this product's WorkflowStage(stage_code)   → ValidationError if absent
      3. select_for_update its AddaStageRecord           → ValidationError if absent
      4. refuse if already open (completed_at is None)
      5. guard(adda, sr, wf)   — stage-specific refusal checks (may raise)
      6. teardown(sr)          — stage-specific child-row cleanup
      7. clear completed_at/by (+ any fields teardown reports) and save
      8. cost_service.clear_stage_cost(sr)   — unfreeze the frozen processing cost
      9. reset Adda → current_stage=wf, status=IN_PROGRESS, completed_at=None
     10. log AddaHistory.STAGE_REOPENED ; return the reopened sr

    guard(adda, sr, wf): raise ValidationError to refuse. None = no extra checks.
    teardown(sr) -> Iterable[str] | None: delete/reset this stage's child rows;
      may set sr.draft_* attrs and RETURN the extra sr field names it changed so
      they persist in the step-7 save. None/[] = nothing extra to save.

    NOTE: the CALLER must be @transaction.atomic (this uses select_for_update).
    """
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied(
            f"only super_admin or manager can reopen the {stage_label} stage"
        )

    wf = adda.product.workflow_stages.filter(stage__code=stage_code).first()
    if wf is None:
        raise ValidationError(f"This product has no {stage_label} stage configured.")

    try:
        sr = AddaStageRecord.objects.select_for_update().get(
            adda=adda, workflow_stage=wf,
        )
    except AddaStageRecord.DoesNotExist:
        raise ValidationError(f"{stage_label} stage has never been started.")
    if sr.completed_at is None:
        raise ValidationError(f"{stage_label} is already open for edits.")

    # V2-3 PR-A (D-V3.2): a settlement-credited stage cannot reopen. Production
    # actions never perform hidden financial actions — settlement money moves
    # ONLY through the settlement lifecycle (reverse / supersede), so the owner
    # must reverse the settlement first, then reopen. (SR row is locked above;
    # finalize locks the same rows, so this check cannot race a finalize.)
    from expense.models import StageWorkAssignment as _SWA
    settled_refs = sorted(set(
        _SWA.objects.filter(stage_record=sr, voided_at__isnull=True,
                            adda_settlement__isnull=False)
        .values_list('adda_settlement__reference', flat=True)
    ))
    if settled_refs:
        raise ValidationError(
            f"{stage_label} earnings were settled by {', '.join(settled_refs)} — "
            "reverse that settlement first (Adda Settlements screen), then reopen."
        )

    if guard is not None:
        guard(adda, sr, wf)

    extra_fields = list(teardown(sr) or []) if teardown is not None else []

    sr.completed_at = None
    sr.completed_by = None
    sr.save(update_fields=['completed_at', 'completed_by', *extra_fields, 'updated_at'])

    # Reopen clears the frozen manufacturing cost — re-complete re-freezes it
    # against the current rate + corrected quantity (price-at-time-of-order).
    from production.services.cost_service import clear_stage_cost
    clear_stage_cost(sr)

    # PAY-3 (narrowed V2-3 PR-A): reopen reverses the ALLOCATION-era worker
    # earnings for this stage (era-A only — adda_settlement IS NULL). The frozen
    # manufacturing cost is cleared above; era-A ledger credits must be voided
    # too, else reopening leaves payable overstated. Re-complete re-allocates.
    # Settlement-era (era-B) lines never reach here — the block above refuses
    # reopen while any exist. (production -> expense, the allowed one-way edge.)
    from expense.services import void_allocation
    for assignment in list(
        _SWA.objects.filter(stage_record=sr, voided_at__isnull=True,
                            adda_settlement__isnull=True)
    ):
        void_allocation(assignment, user=user)

    adda.current_stage = wf
    adda.status = Adda.Status.IN_PROGRESS
    adda.completed_at = None
    adda.save(update_fields=['current_stage', 'status', 'completed_at'])

    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(adda, AddaHistory.ChangeType.STAGE_REOPENED, user, stage_from=None, stage_to=wf)

    logger.info(
        "stage.reopen code=%s adda=%s sr=%s to_stage=%s user=%s",
        stage_code, adda.code, sr.pk, wf.pk, getattr(user, 'pk', None),
    )
    return sr


def downstream_started_guard(adda, sr, wf):
    """Reusable reopen guard (layering + cutting_pattern): refuse if ANY later
    stage has been started — partial rollback of a touched downstream stage is
    unsafe. Admin must unwind the later stage first."""
    started = (
        AddaStageRecord.objects
        .filter(adda=adda, workflow_stage__order__gt=wf.order)
        .exclude(started_at__isnull=True)
        .exists()
    )
    if started:
        raise ValidationError(
            f"Cannot reopen {wf.stage.name} — a downstream stage has already "
            "started. Reopen requires no later stages to have been touched."
        )
