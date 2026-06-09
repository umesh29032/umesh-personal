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
    """Raise ValidationError if a payable stage has no (non-voided) worker allocation.
    No-op for non-payable stages. Partial allocations pass."""
    if not stage_is_payable(stage_record.workflow_stage):
        return
    # production -> expense: the declared one-way edge (lazy import).
    from expense.models import StageWorkAssignment
    has_allocation = StageWorkAssignment.objects.filter(
        stage_record=stage_record, voided_at__isnull=True,
    ).exists()
    if not has_allocation:
        raise ValidationError(
            "This stage credits workers — allocate at least one worker before completing it."
        )
