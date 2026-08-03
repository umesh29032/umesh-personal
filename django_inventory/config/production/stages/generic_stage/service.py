"""generic_stage service — start/complete/reopen for config-only operations.

Mirrors the barcode/layering service shape MINUS any typed record: a generic
operation's whole truth = AddaStageRecord + WorkerStageTask/Contribution
(good/alter/missing). All engine guards apply unchanged: rate snapshot at
start (S2), PAY-2 + C3 at advance, settled-block + downstream guard at
reopen, F3 auto-cancel of unreported tasks at complete.

Action-capability rule for GENERIC stages (V-1 register, code-level):
  start   = management only (roster = manager intent, frozen rule)
  complete= management OR an actively-assigned worker WITH live stage access
  reopen  = management only (the _shared skeleton enforces)
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role
from production.models import Adda, AddaStageRecord

logger = logging.getLogger(__name__)


def _workflow_stage(adda: Adda, stage_code: str):
    return adda.product.workflow_stages.filter(stage__code=stage_code).first()


def _get_stage_record(adda: Adda, stage_code: str):
    wf = _workflow_stage(adda, stage_code)
    if wf is None:
        return None
    return AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()


@transaction.atomic
def start_generic_stage(*, adda: Adda, stage_code: str, worker_ids, user) -> AddaStageRecord:
    """Mgmt assigns workers → stage started (SR get_or_create + rate snapshot)."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can start this stage")
    wf = _workflow_stage(adda, stage_code)
    if wf is None:
        raise ValidationError(
            f"This product's flow does not include the '{stage_code}' stage.")
    sr, created = AddaStageRecord.objects.get_or_create(
        adda=adda, workflow_stage=wf,
        defaults={'started_at': timezone.now()})
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    if sr.started_at is None:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at', 'updated_at'])
    # S2: freeze the payable-rate snapshot at stage-start (idempotent).
    from production.services.stage_rate_service import ensure_stage_role_rates
    ensure_stage_role_rates(sr)
    from production.services.worker_task_service import set_stage_workers
    set_stage_workers(sr, worker_ids)
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
             stage_record=sr, metadata={'worker_ids': list(worker_ids)})
    logger.info("generic_stage.start stage=%s adda=%s sr=%s workers=%s user=%s",
                stage_code, adda.code, sr.pk, list(worker_ids), user.pk)
    return sr


def _ensure_can_complete_generic(user, adda: Adda, stage_code: str, sr) -> None:
    """Generic action rule: management, or an assigned worker with LIVE access."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    from production.services import user_can_access_stage
    if not user_can_access_stage(user, stage_code):
        raise PermissionDenied("Access to this stage has been revoked.")
    if sr is None or not sr.is_worker_assigned(user):
        raise PermissionDenied("You are not assigned to this stage.")


@transaction.atomic
def complete_generic_stage(*, adda: Adda, stage_code: str, user,
                           override_pending_reason: str | None = None) -> AddaStageRecord:
    """Validate + finalize + advance. The engine owns the guards:
    PAY-2 (payable stage needs ≥1 completed report) and the C3 pending-worker
    block + super-admin override both live in advance_to_next_stage."""
    wf = _workflow_stage(adda, stage_code)
    if wf is None:
        raise ValidationError(
            f"This product's flow does not include the '{stage_code}' stage.")
    if adda.current_stage_id != wf.id:
        raise ValidationError(f"Adda is not at the '{stage_code}' stage.")
    try:
        # WF-4 pattern: lock the SR so a concurrent completer double-advance
        # is impossible.
        sr = AddaStageRecord.objects.select_for_update().get(
            adda=adda, workflow_stage=wf)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage has not been started.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    _ensure_can_complete_generic(user, adda, stage_code, sr)

    sr.completed_at = timezone.now()
    sr.completed_by = user
    sr.save(update_fields=['completed_at', 'completed_by', 'updated_at'])

    from production.services.adda_service import advance_to_next_stage
    advance_to_next_stage(adda, user,
                          override_pending_reason=override_pending_reason)
    logger.info("generic_stage.complete stage=%s adda=%s sr=%s user=%s",
                stage_code, adda.code, sr.pk, user.pk)
    return sr


@transaction.atomic
def reopen_generic_stage(*, adda: Adda, stage_code: str, user) -> AddaStageRecord:
    """Mgmt unlock via THE shared skeleton (settled-block + downstream-consumer
    guard + pool clear + rate re-float all owned there). No stage-specific
    guard/teardown — a generic operation has no typed record to tear down.
    M6-campaign fix 2026-07-11: the skeleton locks via select_for_update, so
    the caller must hold a transaction — the siblings (cutting/barcode/
    pattern) are @transaction.atomic; this one wasn't and 500'd on the first
    live generic-stage reopen."""
    from production.models import Stage
    from production.services._shared import reopen_stage_record
    label = Stage.objects.filter(code=stage_code).values_list(
        'name', flat=True).first() or stage_code
    return reopen_stage_record(
        adda=adda, stage_code=stage_code, stage_label=label, user=user)
