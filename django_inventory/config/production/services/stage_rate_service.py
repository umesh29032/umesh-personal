"""AddaStageRoleRate lifecycle — sole writer of the frozen payable-rate snapshot
(Foundation S2, addendum M-5 + contracts 1 & 2).

Production-truth domain. The snapshot is the RESOLVED payable rate
(cost_service.resolved_payable_rate: grouped→0 / role override / base / 0) per
(AddaStageRecord, role):
  • snapshotted at stage-record creation (gives the owner an edit window),
  • editable via edit_until_lock() until the stage's FIRST task completion,
  • IMMUTABLE after — locked_at set in the completing transaction (contract 1).
complete_worker_task + settlement read this, never the live workflow (M-5).

Contract 1 (race determinism): edit_until_lock() and complete_worker_task() both
select_for_update the SAME row in the documented lock order (task →
AddaStageRoleRate) — the lock winner decides; a locked row refuses edits.

Contract 2 (fallback scope): the snapshot is created atomically with the stage
record. complete's safety-net create + WARNING surfaces any missed creation site
(legit silence only for pre-S2 records; on a fresh DB any warning = a bug).

M1 (owner ruling 2026-06-14): rate immutability is per (stage_record, role), NOT
per stage — one role's completion locks only that role's rate row.

S1.1 — rerate_stage_role(): super-admin override of the completion lock, bounded by
SETTLEMENT instead (owner rate-correction requirement). Recalcs completed-but-
unsettled expected_*, refuses once actively settled, writes an append-only
RateCorrectionAudit (mandatory reason). Lock order (F1, 2026-06-14): advisory 5374
(the settlement serialization lock — shared with finalize/reverse) → AddaStageRoleRate
row → WorkerStageContribution rows. Taking 5374 FIRST serializes rerate against finalize
so the settled-check can't be overtaken; all three take 5374 first → no deadlock. (rerate
DELIBERATELY joins the settlement boundary — it is not disjoint from it.)
"""
import logging
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

logger = logging.getLogger('production')

# F1 (hostile-review fix 2026-06-14): the SETTLEMENT serialization advisory lock,
# shared verbatim with expense.adda_settlement_service._REF_LOCK (5374). This is a
# DELIBERATE settlement-boundary choice — rerate is a settlement-boundary operation, so
# it must serialize against finalize/reverse (which hold this same lock). It is NOT a
# generic locking pattern for other services: only rerate / finalize / reverse take 5374,
# and taking it here is what closes the rerate-vs-finalize race (the unguarded settled-
# check could otherwise be overtaken by a concurrent finalize writing settlement_line).
_SETTLEMENT_REF_LOCK = 5374


def ensure_stage_role_rates(stage_record) -> int:
    """Idempotent: snapshot the resolved payable rate per PRODUCTION_ROLE for this
    stage record if absent. Race-safe (get_or_create per row). Returns the count
    CREATED (0 = already present). Call atomically at every AddaStageRecord
    creation site."""
    from accounts.models import Role
    from accounts.services import PRODUCTION_ROLES
    from production.models import AddaStageRoleRate
    from production.services import cost_service

    if AddaStageRoleRate.objects.filter(stage_record=stage_record).exists():
        return 0   # fast path — snapshots already exist
    ws = stage_record.workflow_stage
    created = 0
    for role in Role.objects.filter(code__in=PRODUCTION_ROLES):
        _, was_created = AddaStageRoleRate.objects.get_or_create(
            stage_record=stage_record, role=role,
            defaults={'rate': cost_service.resolved_payable_rate(ws, role)},
        )
        created += int(was_created)
    return created


def frozen_rate_for(stage_record, role, *, lock=False):
    """The frozen (rate, row) for (stage_record, role). lock=True →
    select_for_update the row (caller must be atomic) so complete serializes vs
    edit_until_lock (contract 1). Returns (None, None) if no snapshot — caller
    falls back to the live resolution + warns (contract 2 / pre-S2 records)."""
    from production.models import AddaStageRoleRate
    qs = AddaStageRoleRate.objects.filter(stage_record=stage_record, role=role)
    if lock:
        qs = qs.select_for_update()
    row = qs.first()
    return (row.rate, row) if row is not None else (None, None)


def mark_locked(row) -> None:
    """Lock the rate row on first completion → immutable. Idempotent."""
    if row is not None and row.locked_at is None:
        row.locked_at = timezone.now()
        row.save(update_fields=['locked_at', 'updated_at'])


@transaction.atomic
def edit_until_lock(stage_record, role, new_rate, *, actor):
    """Management edits a snapshot rate BEFORE the stage's first completion.
    select_for_update the row (contract 1); refuse if locked or negative."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import AddaStageRoleRate

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Management only.")
    row = (AddaStageRoleRate.objects.select_for_update()
           .get(stage_record=stage_record, role=role))
    if row.locked_at is not None:
        raise ValidationError(
            "Rate is locked — a task has completed on this stage. Reverse the "
            "settlement and re-rate instead of editing.")
    if new_rate < 0:
        raise ValidationError("Rate cannot be negative.")
    row.rate = new_rate
    row.save(update_fields=['rate', 'updated_at'])
    logger.info("stage_rate.edit sr=%s role=%s rate=%s by=%s",
                stage_record.pk, role.pk, new_rate, getattr(actor, 'pk', None))
    return row


@transaction.atomic
def rerate_stage_role(stage_record, role, new_rate, *, actor, reason):
    """Super-admin re-rate of a (stage_record, role) AFTER the first-completion
    lock but BEFORE settlement (owner requirement 2026-06-14, S1.1).

    Distinct from edit_until_lock (management, pre-lock-only, the normal config
    window): this OVERRIDES the contract-1 lock for the owner, and is bounded by
    SETTLEMENT instead — refused once any contribution of this (stage_record, role)
    is ACTIVELY settled (mirrors set_verified_quantity: reverse the settlement
    first). Recalculates expected_rate + expected_earning on every completed-but-
    unsettled contribution of this (stage_record, role) — EXACT mirror of complete's
    freeze (reported_quantity × rate, ROUND_HALF_UP) — so payroll/settlement previews
    reflect the correction with NO per-worker manual edit. Writes an append-only
    RateCorrectionAudit row (mandatory `reason`) in the same transaction.

    Lock order (F1): pg advisory xact lock 5374 (the SETTLEMENT serialization lock,
    shared with finalize/reverse) → AddaStageRoleRate row → WorkerStageContribution rows.
    Taking 5374 FIRST serializes rerate against finalize/reverse — so the settled-check
    below cannot be overtaken by a concurrent finalize writing settlement_line (the
    rerate-vs-finalize race). All three operations acquire 5374 first → no deadlock.
    Returns (row, recalc_count).
    """
    from accounts.services import ADMIN_ROLES, user_has_role
    from production.models import (
        AddaStageRoleRate, RateCorrectionAudit,
        WorkerStageContribution, WorkerStageTask,
    )

    if not user_has_role(actor, ADMIN_ROLES):
        raise PermissionDenied("Only a super admin can correct a stage rate.")
    if not (reason and reason.strip()):
        raise ValidationError("A reason is required for a rate correction.")
    if new_rate < 0:
        raise ValidationError("Rate cannot be negative.")

    # F1: serialize against settlement (finalize/reverse hold this same lock) BEFORE the
    # settled-check — closes the window where a concurrent finalize writes settlement_line
    # between an unguarded check and the recalc. rerate is a settlement-boundary op.
    with connection.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(%s)', [_SETTLEMENT_REF_LOCK])

    # Gate (lock order): the rate row.
    row = (AddaStageRoleRate.objects.select_for_update()
           .get(stage_record=stage_record, role=role))

    # Refuse if ANY contribution of this (sr, role) is actively settled (not voided).
    settled = (WorkerStageContribution.objects
               .filter(task__stage_record=stage_record, role_snapshot=role,
                       settlement_line__isnull=False,
                       settlement_line__voided_at__isnull=True)
               .exists())
    if settled:
        raise ValidationError(
            "A settlement already booked this stage's pay — reverse or void that "
            "settlement first, then correct the rate.")

    old_rate = row.rate
    row.rate = new_rate
    row.save(update_fields=['rate', 'updated_at'])

    # F2: grouped→0 STRUCTURAL guard — if this stage is a grouped member, the effective
    # pay is 0 regardless of new_rate (a grouped member never pays; grouped wins).
    from production.services import cost_service
    effective = cost_service.effective_pay_rate(stage_record.workflow_stage, new_rate)

    # Recalc completed/verified-but-unsettled contributions (voided lines re-open,
    # so they ARE included). Lock the WSC rows (of=self: nullable settlement_line join).
    recalc = (WorkerStageContribution.objects.select_for_update(of=('self',))
              .filter(task__stage_record=stage_record, role_snapshot=role,
                      task__status__in=(WorkerStageTask.Status.COMPLETED,
                                        WorkerStageTask.Status.VERIFIED)))
    n = 0
    for c in recalc:
        c.expected_rate = effective
        # S3: recalc on the PAYABLE good (mirror of complete's freeze).
        c.expected_earning = (c.good_quantity * effective).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
        c.save(update_fields=['expected_rate', 'expected_earning', 'updated_at'])
        n += 1

    RateCorrectionAudit.objects.create(
        stage_record=stage_record, role=role, old_rate=old_rate, new_rate=new_rate,
        recalc_count=n, reason=reason.strip(), actor=actor,
    )
    logger.warning("stage_rate.rerate sr=%s role=%s %s->%s recalc=%s by=%s reason=%r",
                   stage_record.pk, role.pk, old_rate, new_rate, n,
                   getattr(actor, 'pk', None), reason.strip()[:80])
    return row, n
