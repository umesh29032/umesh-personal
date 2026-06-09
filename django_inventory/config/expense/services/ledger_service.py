"""Ledger service — the SOLE writer of WorkerLedgerEntry.

Append-only + immutable: rows are never UPDATE/DELETE'd. Corrections happen via
`reverse_entry` (an opposite-direction entry linked by `reverses`). Running
balance is NEVER stored — `worker_balance` recomputes it from SUM(credits) −
SUM(debits) every time. No signals; callers wrap in their own atomic block.
"""
from __future__ import annotations

import logging  # stdlib logging — module logger for ledger money writes
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum

from expense.models import WorkerLedgerEntry

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')


def _create_entry(*, worker, entry_type, category, amount, entry_date,
                  created_by=None, assignment=None, advance=None, settlement=None,
                  reverses=None, notes=''):
    """Low-level writer. amount must be positive; direction = entry_type.

    Side effects:
      - INSERT WorkerLedgerEntry (1 row; append-only, never UPDATE/DELETE).
    """
    # str() first so a stray float can't sneak in a binary-expansion value;
    # quantize to paisa so every ledger row is exactly 2dp.
    amt = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if amount is not None else None
    if amt is None or amt <= 0:
        raise ValidationError("Ledger amount must be greater than 0.")
    entry = WorkerLedgerEntry.objects.create(
        worker=worker, entry_type=entry_type, category=category,
        amount=amt, entry_date=entry_date, created_by=created_by,
        assignment=assignment, advance=advance, settlement=settlement,
        reverses=reverses, notes=notes,
    )
    logger.info(
        "ledger.entry.write entry_id=%s worker_id=%s type=%s category=%s amount=%s reverses_id=%s",
        entry.pk, worker.pk if worker is not None else None, entry_type, category, amt, reverses,
    )
    return entry


def log_credit(*, worker, category, amount, entry_date, created_by=None,
               assignment=None, notes=''):
    """Add a credit (increases payable) — e.g. a stage earning.

    Side effects:
      - INSERT WorkerLedgerEntry (1 CREDIT row) via _create_entry.
    """
    entry = _create_entry(
        worker=worker, entry_type=WorkerLedgerEntry.EntryType.CREDIT,
        category=category, amount=amount, entry_date=entry_date,
        created_by=created_by, assignment=assignment, notes=notes,
    )
    logger.info(
        "ledger.credit entry_id=%s worker_id=%s category=%s amount=%s assignment_id=%s",
        entry.pk, worker.pk if worker is not None else None, category, entry.amount, assignment,
    )
    return entry


def log_debit(*, worker, category, amount, entry_date, created_by=None,
              advance=None, settlement=None, notes=''):
    """Add a debit (reduces payable) — e.g. a settlement payment / advance recovery.

    Side effects:
      - INSERT WorkerLedgerEntry (1 DEBIT row) via _create_entry.
    """
    entry = _create_entry(
        worker=worker, entry_type=WorkerLedgerEntry.EntryType.DEBIT,
        category=category, amount=amount, entry_date=entry_date,
        created_by=created_by, advance=advance, settlement=settlement, notes=notes,
    )
    logger.info(
        "ledger.debit entry_id=%s worker_id=%s category=%s amount=%s advance_id=%s settlement_id=%s",
        entry.pk, worker.pk if worker is not None else None, category, entry.amount, advance, settlement,
    )
    return entry


def reverse_entry(entry: WorkerLedgerEntry, *, actor=None, notes=''):
    """Undo an entry by writing an opposite-direction REVERSAL row (never edit).

    A credit is reversed by a debit of equal amount (and vice-versa).

    Side effects:
      - INSERT WorkerLedgerEntry (1 opposite-direction REVERSAL row) via _create_entry.
    """
    if entry.reverses_id is not None:
        raise ValidationError("Cannot reverse a reversal entry.")
    if entry.reversed_by.exists():
        raise ValidationError("This entry has already been reversed.")
    opposite = (
        WorkerLedgerEntry.EntryType.DEBIT
        if entry.entry_type == WorkerLedgerEntry.EntryType.CREDIT
        else WorkerLedgerEntry.EntryType.CREDIT
    )
    reversal = _create_entry(
        worker=entry.worker, entry_type=opposite,
        category=WorkerLedgerEntry.Category.REVERSAL, amount=entry.amount,
        entry_date=entry.entry_date, created_by=actor, reverses=entry,
        notes=notes or f"Reversal of #{entry.pk}",
    )
    logger.info(
        "ledger.reverse reversal_id=%s reverses_entry_id=%s worker_id=%s new_type=%s amount=%s",
        reversal.pk, entry.pk, entry.worker.pk if entry.worker is not None else None, opposite, entry.amount,
    )
    return reversal


def worker_balance(worker) -> Decimal:
    """Live payable = SUM(credits) − SUM(debits). Never stored."""
    agg = WorkerLedgerEntry.objects.filter(worker=worker).aggregate(
        credit=Sum('amount', filter=Q(entry_type=WorkerLedgerEntry.EntryType.CREDIT)),
        debit=Sum('amount', filter=Q(entry_type=WorkerLedgerEntry.EntryType.DEBIT)),
    )
    return (agg['credit'] or _ZERO) - (agg['debit'] or _ZERO)
