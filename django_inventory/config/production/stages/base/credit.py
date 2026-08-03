"""Worker-credit payability + completion guard (PAY-2 / M2.7).

Centralized in the stage engine (not stage-specific) so every stage inherits the
same rule: a PAYABLE stage cannot complete with ZERO worker allocations (partial
allocations are allowed — reconciliation reports catch under-allocation). Payability
is data-driven via WorkflowStage.credits_workers — never a hardcoded stage name
(see docs/TARGET_ARCHITECTURE.md for why the flag lives on WorkflowStage).

Wired into adda_service.advance_to_next_stage (the single choke point all completions
funnel through) in M2.7c. Legacy completions opt out (enforce_worker_credit=False).
"""
from __future__ import annotations

from django.core.exceptions import ValidationError


def stage_is_payable(workflow_stage) -> bool:
    """True if completing this stage must credit workers.

    Data-driven: the credits_workers flag AND self-paid. A grouped member
    (cost_billed_at set) has its labour billed — and its workers allocated — at the
    PAYER stage, so the member itself is not enforced here; the payer is.
    """
    return bool(workflow_stage.credits_workers) and workflow_stage.cost_billed_at_id is None


def ensure_worker_credit(stage_record) -> None:
    """Raise ValidationError if a payable stage has no worker credit. No-op for
    non-payable stages. Partial credit passes.

    PA-10-1 (completes the V2-3 cutover this guard's comment flagged): the credit
    truth-source is flag-aware, because the StageWorkAssignment only exists in two
    eras and the default era doesn't create it until AFTER stage completion:
      • LEDGER_CREDIT_AT_ALLOCATION=True (rollback lever, era-A): allocation books
        the earning up front → credit = a non-voided StageWorkAssignment.
      • settlement-first DEFAULT (flag off): allocate_stage_work refuses, and the
        settlement SWA is created at FINALIZE (after completion) — so reading SWA
        here blocked EVERY cutting completion in the documented default config.
        Credit = the production truth settlement will actually pay: a COMPLETED/
        VERIFIED WorkerStageContribution on this stage (the _settleable_lines
        predicate). Same gate INTENT ("don't complete a payable stage with nobody
        credited"); only the source moves from the transitional SWA to production truth.
    """
    if not stage_is_payable(stage_record.workflow_stage):
        return
    from django.conf import settings
    if getattr(settings, 'LEDGER_CREDIT_AT_ALLOCATION', False):
        # era-A only. production -> expense: the declared one-way edge (lazy import).
        from expense.models import StageWorkAssignment
        if not StageWorkAssignment.objects.filter(
                stage_record=stage_record, voided_at__isnull=True).exists():
            raise ValidationError(
                "This stage credits workers — allocate at least one worker before completing it."
            )
        return
    # settlement-first: credit = the completed production truth the settlement pays.
    from production.models import WorkerStageContribution, WorkerStageTask
    if not WorkerStageContribution.objects.filter(
            task__stage_record=stage_record,
            task__status__in=(WorkerStageTask.Status.COMPLETED,
                              WorkerStageTask.Status.VERIFIED)).exists():
        raise ValidationError(
            "This stage credits workers — at least one worker must complete their "
            "reported work before the stage can be completed."
        )
