"""Cutting stage service — Stage 2 lifecycle.

Pattern matches layering_service.py. Currently just complete_cutting; future
will expand (start_cutting, per-piece breakup, ...) like Layering did.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from production.constants import STAGE_CUTTING
from production.models import Adda, AddaStageRecord, CuttingRecord
from production.services.adda_service import advance_to_next_stage

from ._shared import _ensure_can_manage


@transaction.atomic
def complete_cutting(
    *,
    adda: Adda,
    pieces_cut: int,
    worker_ids: list[int],
    notes: str,
    user,
) -> CuttingRecord:
    """Cutting stage finalize → N BatchBarcode rows auto-generate."""
    _ensure_can_manage(user)
    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_CUTTING:
        raise ValidationError("Adda is not at Cutting stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if pieces_cut < 1:
        raise ValidationError("pieces_cut must be >= 1")

    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=stage,
        started_at=timezone.now(),
        completed_at=timezone.now(), completed_by=user,
    )
    sr.workers.set(worker_ids or [])

    cr = CuttingRecord.objects.create(
        stage_record=sr, pieces_cut=pieces_cut, notes=notes,
    )

    from tracking.services import generate_for_cutting
    generate_for_cutting(cr)

    advance_to_next_stage(adda, user)
    return cr
