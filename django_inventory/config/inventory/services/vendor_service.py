"""Service layer for Vendor and VendorDispatch."""
from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..constants import DispatchStatus
from ..models import Vendor, VendorDispatch, Batch, BatchStage

logger = logging.getLogger(__name__)


class VendorService:
    @staticmethod
    @transaction.atomic
    def create(data: dict) -> Vendor:
        return Vendor.objects.create(**data)

    @staticmethod
    @transaction.atomic
    def update(vendor: Vendor, data: dict) -> Vendor:
        for k, v in data.items():
            setattr(vendor, k, v)
        vendor.save()
        return vendor


class DispatchService:
    @staticmethod
    @transaction.atomic
    def create(batch: Batch, vendor: Vendor, data: dict, user) -> VendorDispatch:
        data.setdefault('status', DispatchStatus.SCHEDULED)
        dispatch = VendorDispatch.objects.create(
            batch=batch, vendor=vendor, created_by=user, **data,
        )
        logger.info("Dispatch created: batch=%s vendor=%s", batch.batch_number, vendor.name)
        return dispatch

    @staticmethod
    @transaction.atomic
    def mark_dispatched(dispatch: VendorDispatch) -> VendorDispatch:
        if dispatch.status != DispatchStatus.SCHEDULED:
            raise ValidationError("Only SCHEDULED dispatches can be marked dispatched.")
        dispatch.status = DispatchStatus.IN_TRANSIT
        dispatch.dispatched_at = dispatch.dispatched_at or timezone.now()
        dispatch.save(update_fields=['status', 'dispatched_at', 'updated_at'])
        return dispatch

    @staticmethod
    @transaction.atomic
    def mark_delivered(dispatch: VendorDispatch, received_qty: int, transit_wastage: int = 0) -> VendorDispatch:
        if dispatch.status not in (DispatchStatus.SCHEDULED, DispatchStatus.IN_TRANSIT):
            raise ValidationError("Dispatch is already in a terminal state.")
        if received_qty + transit_wastage > dispatch.dispatched_qty:
            raise ValidationError("Received + wastage cannot exceed dispatched quantity.")
        dispatch.received_qty = received_qty
        dispatch.transit_wastage = transit_wastage
        dispatch.status = DispatchStatus.DELIVERED
        dispatch.received_at = timezone.now()
        dispatch.save()
        return dispatch
