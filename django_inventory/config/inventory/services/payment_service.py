"""Service layer for vendor payments."""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ..constants import PaymentStatus
from ..models import Payment, Batch, Vendor, VendorDispatch

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    @transaction.atomic
    def record(batch: Batch, vendor: Vendor, amount: Decimal, data: dict, user,
               dispatch: VendorDispatch | None = None) -> Payment:
        if amount is None or Decimal(amount) <= 0:
            raise ValidationError("Payment amount must be positive.")
        payment = Payment.objects.create(
            batch=batch, vendor=vendor, dispatch=dispatch,
            amount=amount, created_by=user, received_at=data.get('received_at') or timezone.now(),
            status=data.get('status') or PaymentStatus.RECEIVED,
            mode=data.get('mode'), reference=data.get('reference', ''), notes=data.get('notes', ''),
        )
        logger.info("Payment recorded: batch=%s vendor=%s amount=%s", batch.batch_number, vendor.name, amount)
        return payment

    @staticmethod
    def total_received_for(batch: Batch) -> Decimal:
        return (
            Payment.objects
            .filter(batch=batch, status=PaymentStatus.RECEIVED)
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0')
        )
