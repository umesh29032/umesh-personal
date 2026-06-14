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
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger('production')


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
