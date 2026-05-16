"""Karigar (worker) queries — every method is row-level scoped to the user."""
from __future__ import annotations

from django.db.models import Count, Q, Sum

from ..constants import BatchStageStatus, BatchStatus, MachineAssignmentStatus
from ..models import (
    Batch, BatchStage, BatchStageMachineAssignment,
    BatchOperation, BatchUserAssignment,
)


class WorkerService:
    """All queries scoped to a single user — safe to expose to karigars."""

    # ── Active / current work ───────────────────────────────────────────────

    @staticmethod
    def current_assignments(user):
        """Machine assignments currently in progress for this user."""
        return (
            BatchStageMachineAssignment.objects
            .filter(worker=user, status__in=[
                MachineAssignmentStatus.ASSIGNED, MachineAssignmentStatus.IN_PROGRESS,
            ])
            .select_related('batch_stage__batch', 'batch_stage__stage', 'machine', 'skill_used')
            .order_by('-assigned_at')
        )

    @staticmethod
    def active_batches(user):
        """Distinct batches the user is currently involved in (via assignment or machine)."""
        batch_ids = set(
            BatchUserAssignment.objects
            .filter(user=user, is_active=True, batch__status=BatchStatus.WIP)
            .values_list('batch_id', flat=True)
        )
        batch_ids.update(
            BatchStageMachineAssignment.objects
            .filter(worker=user, status__in=[
                MachineAssignmentStatus.ASSIGNED, MachineAssignmentStatus.IN_PROGRESS,
            ])
            .values_list('batch_stage__batch_id', flat=True)
        )
        return (
            Batch.objects.filter(pk__in=batch_ids)
            .select_related('batch_type', 'current_stage')
            .order_by('-updated_at')
        )

    # ── History ─────────────────────────────────────────────────────────────

    @staticmethod
    def past_batches(user):
        """Completed batches this user worked on."""
        ids = set(
            BatchUserAssignment.objects
            .filter(user=user, batch__status=BatchStatus.COMPLETED)
            .values_list('batch_id', flat=True)
        )
        ids.update(
            BatchOperation.objects
            .filter(user=user, batch__status=BatchStatus.COMPLETED)
            .values_list('batch_id', flat=True)
        )
        return (
            Batch.objects.filter(pk__in=ids)
            .select_related('batch_type')
            .order_by('-completed_date')
        )

    # ── Stats ───────────────────────────────────────────────────────────────

    @staticmethod
    def summary(user) -> dict:
        active = WorkerService.active_batches(user).count()
        past = WorkerService.past_batches(user).count()
        pieces = (
            BatchOperation.objects
            .filter(user=user)
            .aggregate(total=Sum('output_quantity'))['total']
            or 0
        )
        stage_breakdown = list(
            BatchOperation.objects
            .filter(user=user)
            .values('stage__name')
            .annotate(output=Sum('output_quantity'), sessions=Count('id'))
            .order_by('-output')
        )
        return {
            'active_batches': active,
            'past_batches': past,
            'total_pieces': pieces,
            'stage_breakdown': stage_breakdown,
        }
