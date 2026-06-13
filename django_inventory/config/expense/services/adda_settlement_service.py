"""AddaSettlement — the V2-2 Adda-centric EARNING + RECOVERY-DECISION event.

THE SOLE WRITER of AddaSettlement + AddaSettlementItem (ADR-0002; CI gate
[4b/4] enforces) and of era-B StageWorkAssignment lines (gate [4c/4]).
ADRs in force here: 0005 (truth split) · 0007 (eras + lever) · 0009 (labor
sourcing). WHAT BREAKS WITHOUT the single door: double-pay (same line settled
twice), deadlocks (lock order lives HERE), and unauditable money (the
item↔SWA↔ledger↔WSC provenance loop is written in one transaction). Model A (ARCHITECTURE_V2 §11, locked): finalize books
financial truth — STAGE_EARNING credits + ADVANCE_RECOVERY debits via
ledger_service — and moves NO cash. Payment stays the separate worker-centric
PayrollSettlement event. Drafts carry no money and no frozen rows.

Cross-era double-credit guard (ADR-0007 Option A, Part-13 exact provenance):
  era-B (settlement-era): a contribution row with a non-voided
    `settlement_line` SWA is ALREADY CREDITED — skipped exactly, per row.
  era-A (allocation-era): any non-voided SWA on the same (worker, stage_record)
    that is NOT a settlement line (no settled_contributions) marks that
    worker-stage as allocation-credited — its contribution lines are skipped
    COARSELY (conservative: never double-credit; the UI labels these
    "already credited at allocation", per the ADR's reporting note).

Lock order (deadlock-free, global, mirrors create_settlement — §11.5):
  pg advisory xact lock 5374 (shared with SETL refs)
  → AddaSettlement row (double-finalize reject)
  → AddaStageRecord rows (freeze the quantity inputs)
  → per-worker WorkerProfile → that worker's WorkerAdvance rows.
"""
from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from expense.models import (
    AddaSettlement, AddaSettlementItem, PayrollSettlementItem,
    StageWorkAssignment, WorkerAdvance, WorkerProfile,
)
from expense.services import ledger_service, payroll_service

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')
_REF_LOCK = 5374          # SHARED with settlement_service — one serialization domain


def _q(amount) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _ensure_management(user):
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can settle an Adda.")


def _next_reference() -> str:
    """ADST-0001, … — gap-tolerant; caller holds the advisory lock."""
    last = (
        AddaSettlement.objects.order_by('-id')
        .values_list('reference', flat=True).first()
    )
    n = 0
    if last and last.startswith('ADST-'):
        try:
            n = int(last.split('-', 1)[1])
        except (ValueError, IndexError):
            n = AddaSettlement.objects.count()
    return f"ADST-{n + 1:04d}"


def _payable_stage_records(adda):
    """Stage records of this Adda whose WorkflowStage credits workers (data-driven
    payability — R1 I6) and which are COMPLETED (the §11.5 draft gate; holds by
    construction post-F3/F8)."""
    return list(
        adda.stage_records
        .select_related('workflow_stage__stage')
        .filter(workflow_stage__credits_workers=True)
    )


def _settleable_lines(stage_records):
    """All COMPLETED contribution lines of payable stages, with the cross-era
    guard applied. Returns (lines, skipped_era_a, skipped_era_b) where each line
    is a WorkerStageContribution joined to its task."""
    from production.models import WorkerStageContribution, WorkerStageTask

    sr_ids = [sr.pk for sr in stage_records]
    candidates = list(
        WorkerStageContribution.objects
        .filter(task__stage_record_id__in=sr_ids,
                task__status__in=(WorkerStageTask.Status.COMPLETED,
                                  WorkerStageTask.Status.VERIFIED))
        .select_related('task', 'task__worker', 'task__stage_record',
                        'color', 'size', 'settlement_line')
    )
    # era-A coarse map: (worker_id, stage_record_id) pairs already credited by a
    # non-voided NON-settlement SWA (settlement SWAs are recognized by having
    # settled_contributions; era-A rows never do).
    era_a_pairs = set(
        StageWorkAssignment.objects
        .filter(stage_record_id__in=sr_ids, voided_at__isnull=True,
                adda_settlement__isnull=True)      # STRUCTURAL era marker (PR-C)
        .values_list('worker_id', 'stage_record_id')
    )
    lines, skip_a, skip_b = [], [], []
    for c in candidates:
        if c.settlement_line_id and c.settlement_line.voided_at is None:
            skip_b.append(c)                                  # era-B exact
        elif (c.task.worker_id, c.task.stage_record_id) in era_a_pairs:
            skip_a.append(c)                                  # era-A coarse
        else:
            lines.append(c)
    return lines, skip_a, skip_b


@transaction.atomic
def create_draft(*, adda, user, notes='') -> AddaSettlement:
    """Open a DRAFT settlement — a recomputable scratchpad. No money, no frozen
    rows. Gate: at least one payable stage exists and ALL payable stages are
    completed (quantities final)."""
    _ensure_management(user)
    payable = _payable_stage_records(adda)
    if not payable:
        raise ValidationError("This Adda has no payable stages to settle.")
    incomplete = [sr for sr in payable if sr.completed_at is None]
    if incomplete:
        names = ', '.join(sr.workflow_stage.stage.code for sr in incomplete)
        raise ValidationError(f"Payable stage(s) not completed yet: {names}.")
    if connection.vendor == 'postgresql':
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])
    settlement = AddaSettlement.objects.create(
        reference=_next_reference(), adda=adda, notes=notes)
    logger.info("adda_settlement.draft ref=%s adda=%s by=%s",
                settlement.reference, adda.code, user.pk)
    return settlement


def preview_lines(settlement):
    """Read-only helper for the draft screen: settleable lines + the skipped
    (already-credited) ones so the UI can label the three classes (ADR-0007)."""
    stage_records = _payable_stage_records(settlement.adda)
    return _settleable_lines(stage_records)


def settlement_queue():
    """Read-only management queue (PR-D). Every Adda with payable stages is
    classified:
      ready   — all payable stages completed AND uncredited lines exist
      waiting — payable stage(s) still open (names listed, so the owner knows
                exactly what blocks the settlement)
    Fully-credited Addas (no uncredited lines) drop out of the queue — their
    history lives in the settlements list. Open drafts are attached so the UI
    links to them instead of stacking duplicates."""
    from production.models import Adda

    addas = (
        Adda.objects
        .filter(stage_records__workflow_stage__credits_workers=True)
        .distinct().select_related('product').order_by('code')
    )
    drafts = {
        d.adda_id: d for d in
        AddaSettlement.objects.filter(status=AddaSettlement.Status.DRAFT)
    }
    ready, waiting = [], []
    for adda in addas:
        payable = _payable_stage_records(adda)
        incomplete = [sr.workflow_stage.stage.name for sr in payable
                      if sr.completed_at is None]
        if incomplete:
            waiting.append({'adda': adda, 'incomplete': incomplete,
                            'draft': drafts.get(adda.pk)})
            continue
        lines, skip_a, skip_b = _settleable_lines(payable)
        if not lines:
            continue                       # fully credited — nothing pending
        expected = sum(
            _q((c.verified_quantity if c.verified_quantity is not None
                else c.reported_quantity) * (c.expected_rate or _ZERO))
            for c in lines)
        ready.append({
            'adda': adda,
            'lines': len(lines),
            'workers': len({c.task.worker_id for c in lines}),
            'expected': _q(expected),
            'skipped_era_a': len(skip_a),
            'skipped_era_b': len(skip_b),
            'draft': drafts.get(adda.pk),
        })
    return {'ready': ready, 'waiting': waiting}


@transaction.atomic
def discard_draft(*, settlement, user):
    """Delete a DRAFT scratchpad (PR-D). Safe by construction: drafts carry no
    money, no frozen rows, no inbound FKs — only finalize writes those. NOT a
    history deletion (work-that-happened immutability untouched)."""
    _ensure_management(user)
    settlement = (AddaSettlement.objects.select_for_update()
                  .get(pk=settlement.pk))
    if settlement.status != AddaSettlement.Status.DRAFT:
        raise ValidationError(
            f"Only a draft can be discarded (status: {settlement.status}).")
    ref, adda_code = settlement.reference, settlement.adda.code
    settlement.delete()
    logger.info("adda_settlement.discard ref=%s adda=%s by=%s",
                ref, adda_code, user.pk)


@transaction.atomic
def finalize_adda_settlement(*, settlement, user, variance=None, recoveries=None):
    """The settlement money-write (§11.5). NO CASH — payment is a separate event.

    variance:  {worker_id: {'packed': int, 'missing': int, 'rejected': int,
                'alter': int}} — manual, source-agnostic (§11.10). Counts freeze
                onto the snapshot; under factory_absorbs they never reduce pay.
    recoveries: {advance_id: amount} — owner-chosen per-advance recovery,
                guarded ≤ remaining under lock; advance's worker must be among
                the settled workers.

    Side effects (money / multi-write):
      • advisory xact lock 5374 → ADST row lock → stage-record locks →
        per-worker WorkerProfile + WorkerAdvance locks.
      • Writes SWA earning lines (one per contribution line — D-S grain) and
        stamps WorkerStageContribution.settlement_line (provenance, Part 13)
        via update_fields (the chokepoint write-path exemption is documented
        in the check.sh gate).
      • ledger_service.log_credit(STAGE_EARNING, assignment=SWA) per line;
        ledger_service.log_debit(ADVANCE_RECOVERY) per recovery.
      • Writes PayrollSettlementItem rows parented to THIS AddaSettlement.
      • Freezes AddaSettlementItem per worker + the settlement totals.
      • tracking.log_adda(SETTLEMENT_FINALIZED) — the Adda-360 timeline event.
    """
    _ensure_management(user)
    variance = variance or {}
    recoveries = recoveries or {}

    if connection.vendor == 'postgresql':
        with connection.cursor() as cur:
            # Hinglish: poore settlement-system ka EK hi gate-lock — ref numbering
            # aur lock-ORDER dono race-safe; order todna = deadlock (§11.5).
            cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])

    settlement = (AddaSettlement.objects.select_for_update()
                  .get(pk=settlement.pk))
    if settlement.status != AddaSettlement.Status.DRAFT:
        raise ValidationError(
            f"Only a draft can be finalized (status: {settlement.status}).")

    adda = settlement.adda
    stage_records = _payable_stage_records(adda)
    from production.models import AddaStageRecord
    # Freeze quantity inputs (verified_quantity edits race) — row locks.
    list(AddaStageRecord.objects.select_for_update()
         .filter(pk__in=[sr.pk for sr in stage_records]))

    lines, skip_a, skip_b = _settleable_lines(stage_records)
    if not lines:
        raise ValidationError(
            "Nothing to settle: no uncredited completed contributions on "
            "payable stages (already-credited lines are excluded).")

    when = timezone.now()
    by_worker: dict[int, list] = {}
    for c in lines:
        by_worker.setdefault(c.task.worker_id, []).append(c)

    # Per-worker locks in a stable order (worker_id) — deadlock-safe.
    # Hinglish: sab transactions worker-locks ISI order me lein to circular
    # wait kabhi nahi banta — deadlock ka ilaaj order hai, luck nahi.
    workers = sorted(by_worker)
    for wid in workers:
        profile, _ = WorkerProfile.objects.get_or_create(user_id=wid)
        WorkerProfile.objects.select_for_update().get(pk=profile.pk)
    locked_advances = {
        a.id: a for a in WorkerAdvance.objects.select_for_update()
        .filter(worker_id__in=workers)
    }

    # Recovery validation up-front (before any money moves).
    # Hinglish: pehle SAARI recoveries check (≤ remaining, sahi worker), TAB
    # paisa likhna shuru — aadha-likha settlement kabhi exist nahi karta.
    cleaned_recoveries: dict[int, list[tuple[WorkerAdvance, Decimal]]] = {}
    for adv_id, amount in recoveries.items():
        amt = _q(amount)
        if amt <= _ZERO:
            continue
        adv = locked_advances.get(int(adv_id))
        if adv is None:
            raise ValidationError(
                f"Advance #{adv_id} does not belong to a settled worker.")
        remaining = payroll_service.advance_remaining(adv)
        if amt > remaining:
            raise ValidationError(
                f"Recovery {amt} exceeds advance #{adv.id} remaining {remaining}.")
        cleaned_recoveries.setdefault(adv.worker_id, []).append((adv, amt))

    expected_total = _ZERO
    totals = {'packed': 0, 'missing': 0, 'rejected': 0, 'alter': 0}

    for wid in workers:
        wlines = by_worker[wid]
        worker = wlines[0].task.worker
        outstanding_before = payroll_service.advance_outstanding(worker)
        worker_expected = _ZERO
        first_swa = None

        for c in wlines:
            qty = c.verified_quantity if c.verified_quantity is not None else c.reported_quantity
            rate = c.expected_rate or _ZERO            # frozen at complete (Option B)
            amount = _q(qty * rate)
            # D-S grain (locked): ONE SWA per contribution line — dimension-true.
            swa = StageWorkAssignment.objects.create(
                stage_record=c.task.stage_record, worker=worker,
                color=c.color, size=c.size,
                allocated_quantity=qty,
                earning_rate_snapshot=rate,
                earning_amount_snapshot=amount,
                entered_by=user,
                adda_settlement=settlement,        # structural era-B marker
                notes=f"settled via {settlement.reference}",
            )
            # Part-13 provenance: exact per-row era-B guard from here on.
            c.settlement_line = swa
            c.save(update_fields=['settlement_line', 'updated_at'])
            if amount > _ZERO:
                ledger_service.log_credit(
                    worker=worker, category='stage_earning', amount=amount,
                    entry_date=when.date(), created_by=user, assignment=swa,
                    notes=f"{settlement.reference} · {adda.code}",
                )
            worker_expected += amount
            first_swa = first_swa or swa

        recovered = _ZERO
        for adv, amt in cleaned_recoveries.get(wid, []):
            debit = ledger_service.log_debit(
                worker=worker, category='advance_recovery', amount=amt,
                entry_date=when.date(), created_by=user, advance=adv,
                notes=f"{settlement.reference} recovery adv#{adv.id}",
            )
            PayrollSettlementItem.objects.create(
                adda_settlement=settlement, advance=adv, amount_recovered=amt,
                ledger_entry=debit)
            recovered += amt

        v = variance.get(wid) or variance.get(str(wid)) or {}
        final_payable = worker_expected - recovered     # factory_absorbs: no deduction
        # Tie-out (invariant 6): the frozen snapshot must equal what was booked.
        assert final_payable == worker_expected - recovered
        AddaSettlementItem.objects.create(
            adda_settlement=settlement, worker=worker,
            expected_earning=worker_expected,
            advance_outstanding_before=outstanding_before,
            advance_recovered=recovered,
            final_payable=max(final_payable, _ZERO),
            variance_amount=_ZERO,                      # factory_absorbs
            packed_quantity=int(v.get('packed', 0)),
            missing_quantity=int(v.get('missing', 0)),
            rejected_quantity=int(v.get('rejected', 0)),
            alter_quantity=int(v.get('alter', 0)),
            settled_at=when, settled_by=user,
            earning_assignment=first_swa,
        )
        expected_total += worker_expected
        for k in totals:
            totals[k] += int(v.get(k, 0))

    settlement.status = AddaSettlement.Status.FINALIZED
    settlement.settled_at = when
    settlement.settled_by = user
    settlement.expected_total = expected_total
    settlement.packed_total = totals['packed']
    settlement.missing_total = totals['missing']
    settlement.rejected_total = totals['rejected']
    settlement.alter_total = totals['alter']
    settlement.variance_total = _ZERO                   # factory_absorbs
    settlement.save(update_fields=[
        'status', 'settled_at', 'settled_by', 'expected_total', 'packed_total',
        'missing_total', 'rejected_total', 'alter_total', 'variance_total',
        'updated_at'])

    # Adda-360 timeline event (Part 13).
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(adda, AddaHistory.ChangeType.SETTLEMENT_FINALIZED, user, metadata={
        'reference': settlement.reference,
        'expected_total': str(expected_total),
        'workers': len(workers),
        'lines': len(lines),
        'skipped_era_a': len(skip_a),
        'skipped_era_b': len(skip_b),
    })
    logger.info(
        "adda_settlement.finalize ref=%s adda=%s workers=%s lines=%s "
        "skipped_era_a=%s skipped_era_b=%s expected=%s",
        settlement.reference, adda.code, len(workers), len(lines),
        len(skip_a), len(skip_b), expected_total)
    return settlement


@transaction.atomic
def reverse_adda_settlement(*, settlement, user, supersede=False, notes=''):
    """Correction truth (§11.5, R0 C5): NEVER edit — reverse, then optionally
    supersede. Restores tomorrow what a mistake booked today:

      1. every STAGE_EARNING credit of this settlement (targets = its
         earning_lines SWAs, structural) → compensating debit via
         ledger_service.reverse_entry (entry_date copied — nets in-period);
      2. every ADVANCE_RECOVERY debit (targets = its PayrollSettlementItems'
         ledger_entry) → compensating credit; the PSI row is STAMPED
         reversed_at (owner D-R: append-only, unsigned) so the advance
         outstanding SUM restores instantly;
      3. its SWA earning lines are soft-VOIDED (voided_at) — the era-B guard
         re-arms, so a successor settlement may re-credit those contributions;
      4. frozen AddaSettlementItems are NOT touched (the audit record of what
         was approved); status → REVERSED (or SUPERSEDED) + stamps;
      5. supersede=True additionally opens a fresh DRAFT with `supersedes`
         pointing back — settle again correctly.
      6. SETTLEMENT_REVERSED / SETTLEMENT_SUPERSEDED on the Adda timeline.

    Returns (settlement, successor_draft_or_None).
    """
    from expense.models import WorkerLedgerEntry

    _ensure_management(user)
    if connection.vendor == 'postgresql':
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])

    settlement = (AddaSettlement.objects.select_for_update()
                  .get(pk=settlement.pk))
    if settlement.status != AddaSettlement.Status.FINALIZED:
        raise ValidationError(
            f"Only a finalized settlement can be reversed (status: {settlement.status}).")

    when = timezone.now()

    # 1) earnings — exact structural target set.
    swas = list(settlement.earning_lines.select_for_update())
    credits = list(WorkerLedgerEntry.objects.filter(
        assignment__in=swas, entry_type='credit', category='stage_earning'))
    for entry in credits:
        ledger_service.reverse_entry(
            entry, actor=user,
            notes=f"reverse {settlement.reference}: {notes}".strip(': '))

    # 2) recoveries — restore advance outstanding (D-R stamp, never edit/sign).
    psis = list(settlement.recovery_lines.select_for_update()
                .filter(reversed_at__isnull=True))
    for psi in psis:
        if psi.ledger_entry_id:
            ledger_service.reverse_entry(
                psi.ledger_entry, actor=user,
                notes=f"reverse {settlement.reference} recovery adv#{psi.advance_id}")
        psi.reversed_at = when
        psi.save(update_fields=['reversed_at', 'updated_at'])

    # 3) void the earning lines — re-arms the double-credit guard.
    for swa in swas:
        swa.voided_at = when
        swa.save(update_fields=['voided_at', 'updated_at'])

    # 4) status + stamps (frozen items untouched).
    successor = None
    if supersede:
        settlement.status = AddaSettlement.Status.SUPERSEDED
    else:
        settlement.status = AddaSettlement.Status.REVERSED
    settlement.reversed_at = when
    settlement.reversed_by = user
    settlement.save(update_fields=['status', 'reversed_at', 'reversed_by',
                                   'updated_at'])

    # 5) successor draft.
    if supersede:
        successor = AddaSettlement.objects.create(
            reference=_next_reference(), adda=settlement.adda,
            supersedes=settlement,
            notes=f"supersedes {settlement.reference}. {notes}".strip('. '))

    # 6) timeline events.
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    change = (AddaHistory.ChangeType.SETTLEMENT_SUPERSEDED if supersede
              else AddaHistory.ChangeType.SETTLEMENT_REVERSED)
    log_adda(settlement.adda, change, user, metadata={
        'reference': settlement.reference,
        'credits_reversed': len(credits),
        'recoveries_reversed': len(psis),
        'successor': successor.reference if successor else None,
    })
    logger.info(
        "adda_settlement.reverse ref=%s supersede=%s credits=%s recoveries=%s "
        "successor=%s", settlement.reference, supersede, len(credits),
        len(psis), successor.reference if successor else None)
    return settlement, successor
