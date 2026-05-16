"""Service layer for BatchType and its stage-template management."""
from __future__ import annotations

import logging
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import BatchType, BatchTypeStage, Stage

logger = logging.getLogger(__name__)


class BatchTypeService:
    """CRUD + stage-template editing for product categories (T-Shirt, Lower, 3-Patti, …)."""

    # ── CRUD ──────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create(data: dict, user) -> BatchType:
        data['created_by'] = user
        obj = BatchType.objects.create(**data)
        logger.info("BatchType '%s' created by %s", obj.code, user)
        return obj

    @staticmethod
    @transaction.atomic
    def update(obj: BatchType, data: dict) -> BatchType:
        for field, value in data.items():
            setattr(obj, field, value)
        obj.save()
        return obj

    # ── Stage template management ────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def set_stages(batch_type: BatchType, stages: Iterable[dict]) -> None:
        """
        Replace the stage template of a BatchType.

        `stages` is an ordered iterable of dicts: {stage_id, sequence_order, is_mandatory}.
        Does not touch already-running batches — historical `BatchStage` rows are isolated clones.
        """
        seen_stage_ids: set[int] = set()
        seen_orders: set[int] = set()
        cleaned: list[dict] = []

        for raw in stages:
            try:
                stage_id = int(raw['stage_id'])
                order = int(raw['sequence_order'])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValidationError("Each stage entry needs 'stage_id' and 'sequence_order'.") from exc

            if stage_id in seen_stage_ids:
                raise ValidationError(f"Stage id {stage_id} is listed twice in the template.")
            if order in seen_orders:
                raise ValidationError(f"Sequence order {order} is listed twice.")
            seen_stage_ids.add(stage_id)
            seen_orders.add(order)
            cleaned.append({
                'stage_id': stage_id,
                'sequence_order': order,
                'is_mandatory': bool(raw.get('is_mandatory', True)),
            })

        cleaned.sort(key=lambda row: row['sequence_order'])

        BatchTypeStage.objects.filter(batch_type=batch_type).delete()
        BatchTypeStage.objects.bulk_create([
            BatchTypeStage(
                batch_type=batch_type,
                stage_id=row['stage_id'],
                sequence_order=row['sequence_order'],
                is_mandatory=row['is_mandatory'],
            )
            for row in cleaned
        ])
        logger.info("BatchType '%s' template set to %d stages", batch_type.code, len(cleaned))

    @staticmethod
    def get_template(batch_type: BatchType):
        return (
            BatchTypeStage.objects
            .filter(batch_type=batch_type)
            .select_related('stage')
            .order_by('sequence_order')
        )

    @staticmethod
    def available_stages_for(batch_type: BatchType):
        """Active stages that are not already in this type's template."""
        used_ids = BatchTypeStage.objects.filter(batch_type=batch_type).values_list('stage_id', flat=True)
        return Stage.objects.filter(is_active=True).exclude(pk__in=used_ids).order_by('category', 'name')
