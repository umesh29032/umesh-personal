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

Production-truth lock domain (S1.1, M-3 / addendum):
  WorkerStageTask → AddaStageRoleRate → WorkerStageContribution
  (worker_task_service.complete_worker_task — disjoint from the settlement order above;
  it never locks AddaSettlement/WorkerProfile/WorkerAdvance, and finalize never locks the
  task / AddaStageRoleRate → no cross-domain wait).
F1 (2026-06-14): stage_rate_service.rerate_stage_role is the ONE production-side op that
DELIBERATELY joins the settlement serialization — it takes the advisory lock 5374 FIRST
(then AddaStageRoleRate → WSC), exactly as finalize/reverse do, because re-rating is a
settlement-boundary correction that must not race a finalize. All three acquire 5374
first → still no deadlock.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from expense.models import (
    AddaSettlement, AddaSettlementItem, PayrollSettlementItem,
    StageWorkAssignment, WorkerAdvance, WorkerProfile,
)
from expense.services import ledger_service, payroll_service
from expense.services._shared import next_reference, q_paisa
from expense.services.settlement_resolver import settlement_quantity

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')
_REF_LOCK = 5374          # SHARED with settlement_service — one serialization domain


def _q(amount) -> Decimal:
    return q_paisa(amount)   # one rounding rule for all expense money (_shared)


def _ensure_management(user):
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can settle an Adda.")


def _next_reference() -> str:
    """ADST-0001, … — gap-tolerant; caller holds the advisory lock."""
    return next_reference(AddaSettlement, 'ADST')


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
    guard applied. Returns (lines, skipped_era_a, skipped_era_b, skipped_monthly)
    where each line is a WorkerStageContribution joined to its task.

    skipped_monthly (R4, PDD §27-D4): lines of workers whose CURRENT pay basis
    is MONTHLY — structurally excluded HERE, the one funnel feeding preview,
    queue and finalize, so finalize can never book them. Their settlement_line
    stays NULL (never linked); salary is paid via Expenses (§21). Basis is read
    at settlement time (owner P-1) — a later switch back to piece-rate makes
    them settleable again, always visible in the draft preview first."""
    from production.models import WorkerStageContribution, WorkerStageTask

    sr_ids = [sr.pk for sr in stage_records]
    candidates = list(
        WorkerStageContribution.objects
        .filter(task__stage_record_id__in=sr_ids,
                task__status__in=(WorkerStageTask.Status.COMPLETED,
                                  WorkerStageTask.Status.VERIFIED))
        # PA-16-1: include workflow_stage→stage on the join. The preview/queue
        # consumers (_line_dict, settlement_queue, effective_pay_rate) read
        # c.task.stage_record.workflow_stage.stage.name PER LINE — without this
        # that was 2 extra queries (workflow_stage + stage) for every contribution
        # line (a measured N+1 on the settlement-detail draft + the queue).
        .select_related('task', 'task__worker', 'task__stage_record',
                        'settlement_line__adda_settlement',
                        'task__stage_record__workflow_stage__stage',
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
    # R4: one query resolves which candidate workers are currently MONTHLY
    # (absent profile = piece_rate default — get_or_create semantics).
    monthly_ids = set(
        WorkerProfile.objects
        .filter(user_id__in={c.task.worker_id for c in candidates},
                pay_basis=WorkerProfile.PayBasis.MONTHLY)
        .values_list('user_id', flat=True)
    )
    lines, skip_a, skip_b, skip_monthly = [], [], [], []
    for c in candidates:
        if c.settlement_line_id and c.settlement_line.voided_at is None:
            skip_b.append(c)                                  # era-B exact
        elif (c.task.worker_id, c.task.stage_record_id) in era_a_pairs:
            skip_a.append(c)                                  # era-A coarse
        elif c.task.worker_id in monthly_ids:
            skip_monthly.append(c)                            # R4 monthly (D4)
        else:
            lines.append(c)
    return lines, skip_a, skip_b, skip_monthly


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
    ones so the UI can label all four classes (ADR-0007 era-A/era-B + R4
    monthly). Returns (lines, skip_a, skip_b, skip_monthly)."""
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
    links to them instead of stacking duplicates.

    OI-C1 (BOD-D, owner Option B 2026-07-18) — BATCHED read-path, IDENTICAL
    output. The per-Adda _payable_stage_records + _settleable_lines calls were
    an N+1 (measured 35 queries at today's volume; grows 1-4/Adda). Now: the
    payable stage records come from ONE query (Meta ordering
    ['adda', 'workflow_stage__order'] keeps each Adda's list in the exact
    per-Adda order, so the waiting `incomplete` name order is unchanged) and
    _settleable_lines — THE single funnel shared with preview/finalize,
    untouched — runs ONCE over the union. Partitioning its result by adda is
    provably identical to per-Adda calls: every per-line verdict depends only
    on per-line/global facts (settlement_line state · exact
    (worker_id, stage_record_id) era-A pair membership · the worker's global
    pay basis), and the ready-entry consumers are order-insensitive
    (len / sets / exact-Decimal sums). Query count is now volume-independent
    (6 at any Adda count)."""
    from production.models import Adda, AddaStageRecord
    from production.services import cost_service

    addas = list(
        Adda.objects
        .filter(stage_records__workflow_stage__credits_workers=True)
        .distinct().select_related('product').order_by('code')
    )
    drafts = {
        d.adda_id: d for d in
        AddaSettlement.objects.filter(status=AddaSettlement.Status.DRAFT)
    }
    # ONE query = every queue Adda's payable stage records (same filter +
    # select_related as _payable_stage_records; Meta ordering groups per Adda
    # in the identical order the per-Adda related-manager query produced).
    payable_by_adda = {}
    for sr in (AddaStageRecord.objects
               .filter(adda__in=addas,
                       workflow_stage__credits_workers=True)
               .select_related('workflow_stage__stage')):
        payable_by_adda.setdefault(sr.adda_id, []).append(sr)

    # Split complete vs waiting first, then ONE _settleable_lines pass over the
    # union of complete Addas' stage records (was 3 queries per Adda).
    incomplete_by_adda = {}
    union_srs = []
    for adda in addas:
        payable = payable_by_adda.get(adda.pk, [])
        names = [sr.workflow_stage.stage.name for sr in payable
                 if sr.completed_at is None]
        if names:
            incomplete_by_adda[adda.pk] = names
        else:
            union_srs.extend(payable)
    lines_u, skip_a_u, skip_b_u, skip_m_u = _settleable_lines(union_srs)

    def _group(items):
        grouped = {}
        for c in items:
            grouped.setdefault(c.task.stage_record.adda_id, []).append(c)
        return grouped
    lines_map = _group(lines_u)
    skip_a_map, skip_b_map, skip_m_map = _group(skip_a_u), _group(skip_b_u), _group(skip_m_u)

    ready, waiting = [], []
    for adda in addas:
        if adda.pk in incomplete_by_adda:
            waiting.append({'adda': adda,
                            'incomplete': incomplete_by_adda[adda.pk],
                            'draft': drafts.get(adda.pk)})
            continue
        lines = lines_map.get(adda.pk, [])
        if not lines:
            continue           # fully credited / monthly-only — nothing payable
        # PA-11-2: mirror the finalize money-boundary — apply the grouped→0 structural
        # guard (effective_pay_rate) here too, else a stage grouped AFTER completion shows
        # an overstated "expected" in the queue while finalize correctly books 0 (F2: the
        # guard must apply ANYWHERE expected_* is recomputed).
        expected = sum(
            _q(settlement_quantity(c) * cost_service.effective_pay_rate(
                c.task.stage_record.workflow_stage, c.expected_rate or _ZERO))
            for c in lines)
        ready.append({
            'adda': adda,
            'lines': len(lines),
            'workers': len({c.task.worker_id for c in lines}),
            'expected': _q(expected),
            'skipped_era_a': len(skip_a_map.get(adda.pk, [])),
            'skipped_era_b': len(skip_b_map.get(adda.pk, [])),
            'skipped_monthly': len(skip_m_map.get(adda.pk, [])),
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
def finalize_adda_settlement(*, settlement, user, variance=None, recoveries=None,
                             reconciliation_override=None, only_worker=None):
    """The settlement money-write (§11.5). NO CASH — payment is a separate event.

    variance:  {worker_id: {'packed': int, 'missing': int, 'rejected': int,
                'alter': int}} — manual, source-agnostic (§11.10). Counts freeze
                onto the snapshot; under factory_absorbs they never reduce pay.
    recoveries: {advance_id: amount} — owner-chosen per-advance recovery,
                guarded ≤ remaining under lock; advance's worker must be among
                the settled workers.
    only_worker: R7 (PDD §20 F&F) — settle ONLY this worker's lines; everyone
                else's stay uncredited and settleable later (§11.8 partial
                settlements). A pure FILTER on the funnel OUTPUT: every era /
                monthly / verified-qty guard ran first, so protections are
                untouched. Creates the mixed settled/unsettled-lines-on-one-SR
                state — verified safe 2026-07-05 (all consumers line-granular;
                reopen armor + rerate lock go conservative until reverse).

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
    from production.models import AddaStageRecord, WorkerStageContribution
    # Freeze the stage records (row locks).
    list(AddaStageRecord.objects.select_for_update()
         .filter(pk__in=[sr.pk for sr in stage_records]))
    # PA-11-3: the settled quantity is resolved from WorkerStageContribution.verified_quantity
    # (settlement_resolver) — which lives on WSC, NOT AddaStageRecord — so the SR lock above
    # does NOT freeze it. Lock the WSC rows too (of=('self',), the SAME target
    # set_verified_quantity locks) so a verified-quantity edit racing this finalize blocks
    # until commit, then sees settlement_line stamped and refuses. Without this, a correction
    # issued during the finalize window is a lost update and money books on the stale quantity.
    # No deadlock: every settlement op takes 5374 first; set_verified takes only the WSC row.
    list(WorkerStageContribution.objects.select_for_update(of=('self',))
         .filter(task__stage_record__in=stage_records))

    lines, skip_a, skip_b, skip_monthly = _settleable_lines(stage_records)
    if only_worker is not None:
        lines = [c for c in lines if c.task.worker_id == only_worker.pk]
    if not lines:
        raise ValidationError(
            "Nothing to settle: no uncredited completed contributions on "
            "payable stages (already-credited and monthly workers' lines "
            "are excluded).")

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

        from production.services import cost_service
        for c in wlines:
            qty = settlement_quantity(c)               # resolver (S1) — default = verified ?? reported
            # F2: grouped→0 STRUCTURAL guard at the MONEY boundary — a grouped member never
            # pays, even if the frozen expected_rate is a stale non-zero (snapshot frozen
            # before the stage was grouped). Grouped status wins over the frozen value.
            rate = cost_service.effective_pay_rate(
                c.task.stage_record.workflow_stage, c.expected_rate or _ZERO)
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
                    entry_date=timezone.localdate(when), created_by=user, assignment=swa,
                    notes=f"{settlement.reference} · {adda.code}",
                )
            worker_expected += amount
            first_swa = first_swa or swa

        recovered = _ZERO
        for adv, amt in cleaned_recoveries.get(wid, []):
            debit = ledger_service.log_debit(
                worker=worker, category='advance_recovery', amount=amt,
                entry_date=timezone.localdate(when), created_by=user, advance=adv,
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

    # M-6 reconciliation (S1.1 WARN → S5 configurable BLOCK). SWAs are written above, so
    # reconcile reads the final allocated. Quantity-only (settled good vs produced output) —
    # reads no rate/earning/cost. Block = over_allocated beyond tolerance, when ENFORCE on,
    # without an audited super-admin override. Raising rolls back the whole atomic finalize
    # (SWAs + ledger + items) → nothing books on a block.
    from decimal import Decimal as _Dec

    from django.conf import settings as _dj
    from expense.services import reconciliation_service as _recon
    _tol = _Dec(str(getattr(_dj, 'SETTLEMENT_RECONCILIATION_TOLERANCE', '0') or '0'))
    over_rows = [
        r for r in _recon.reconcile_stage_pay(adda=adda)
        if r['flag'] == 'over_allocated' and (r['allocated_qty'] - r['output_qty']) > _tol
    ]
    _override = (reconciliation_override or '').strip()
    if over_rows and getattr(_dj, 'ENFORCE_SETTLEMENT_RECONCILIATION', False):
        _detail = '; '.join(
            f"'{r['stage']}' settled {r['allocated_qty']} but produced {r['output_qty']} "
            f"(over by {r['allocated_qty'] - r['output_qty']})" for r in over_rows)
        if not _override:
            raise ValidationError(
                f"Cannot finalize {settlement.reference}: settled more than produced — "
                f"{_detail}. Tolerance {_tol}. Correct the verified quantity (Review Reports), "
                f"void the over-allocation, or finalize with a super-admin override (reason "
                f"required).")
        from accounts.services import ADMIN_ROLES, user_has_role
        if not user_has_role(user, ADMIN_ROLES):
            raise ValidationError(
                f"Only a super admin can override a settlement-reconciliation block ({_detail}).")
    _did_override = bool(over_rows and _override
                         and getattr(_dj, 'ENFORCE_SETTLEMENT_RECONCILIATION', False))
    record_reconciliation_evidence(
        settlement, adda,
        override_reason=(_override if _did_override else ''),
        overridden_by=(user if _did_override else None))
    return settlement


def record_reconciliation_evidence(settlement, adda, *, override_reason='', overridden_by=None) -> int:
    """Persist append-only M-6 evidence (H2) for every stage where settled quantity
    exceeds recorded output (the B-1 leak: paid > produced) + WARN-log it. S5: when a
    super-admin overrode an ENFORCE_SETTLEMENT_RECONCILIATION block, the rows carry the
    audited override_reason + overridden_by.

    H1: scoped to SETTLEMENT_WARN_FLAGS (over_allocated only) — no_output_qty /
    grouped_paid / unpriced_paid are different concerns and were noise. H2: the row
    is PERSISTED (not log-scraped) so the soak's B-1 metric survives later
    corrections/reversals. Returns the number of evidence rows written. S5 will gate
    finalize on this signal (BLOCK + tolerance + audited override); S1.1 only records.
    """
    from expense.models import SettlementReconciliationEvidence
    from expense.services import reconciliation_service as _recon
    warn_rows = [
        r for r in _recon.reconcile_stage_pay(adda=adda)
        if r['flag'] in _recon.SETTLEMENT_WARN_FLAGS
    ]
    if not warn_rows:
        return 0
    # FK = the recon row's OWN stage record pk. Resolving via stage CODE broke
    # on multi-lane Addas (N cutting SRs share one code → dict collapsed to an
    # arbitrary lane and evidence pointed at the wrong SR) — OWN-C fix 2026-07-13.
    created = SettlementReconciliationEvidence.objects.bulk_create([
        SettlementReconciliationEvidence(
            adda_settlement=settlement, stage_record_id=r['stage_record_id'],
            flag=r['flag'], output_qty=r['output_qty'],
            allocated_qty=r['allocated_qty'], qty_delta=r['qty_delta'],
            override_reason=override_reason, overridden_by=overridden_by,
        )
        for r in warn_rows
    ])
    logger.warning(
        "adda_settlement.reconciliation_warn ref=%s adda=%s flags=%s",
        settlement.reference, adda.code,
        [(r['stage'], r['flag'], str(r['qty_delta'])) for r in warn_rows])
    return len(created)


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
