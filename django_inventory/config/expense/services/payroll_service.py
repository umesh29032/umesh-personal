"""Payroll read service — aggregations + per-worker access scoping.

Everything here is derived live from the ledger (never a stored total).
TWO writes live here: `set_pay_basis` (R4) — the SOLE writer of
WorkerPayBasisAudit — and `update_payout_profile` (RCP-1A F3, 2026-07-18) —
THE WorkerProfile payout-details writer incl. the displayed-₹ field
`opening_advance` (single-writer discipline, CLAUDE rule 5).
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum

from accounts.services import MANAGEMENT_ROLES, user_has_perm, user_has_role
from expense.models import (
    PayrollSettlement, PayrollSettlementItem, StageWorkAssignment,
    WorkerAdvance, WorkerLedgerEntry, WorkerPayBasisAudit, WorkerProfile,
)

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')
_ET = WorkerLedgerEntry.EntryType
_CAT = WorkerLedgerEntry.Category
# Credit categories that count as real earnings. Other credits (e.g. a REVERSAL
# credit written when a settlement payment is undone) must NOT inflate earnings.
_EARNING_CATS = (_CAT.STAGE_EARNING, _CAT.PRODUCTION_EARNING)


def payroll_totals() -> dict:
    """Factory-wide totals for the operations digest (P1-1). Same definitions as
    the payroll overview, aggregated at the DB (derived live, never stored):
      • pending_payable  = Σ ledger credits − Σ debits
      • advance_exposure = Σ advances given − Σ recovered
    """
    led = WorkerLedgerEntry.objects.aggregate(
        credits=Sum('amount', filter=Q(entry_type=_ET.CREDIT)),
        debits=Sum('amount', filter=Q(entry_type=_ET.DEBIT)),
    )
    pending_payable = (led['credits'] or _ZERO) - (led['debits'] or _ZERO)
    given = WorkerAdvance.objects.aggregate(s=Sum('amount'))['s'] or _ZERO
    # PA-12-A: exclude REVERSED recoveries (reversed_at set), exactly like
    # advance_remaining/advance_outstanding/outstanding_advances. Without it, a
    # reversed settlement's recovery still counts as recovered → factory-wide
    # advance_exposure is understated after any settlement reversal.
    recovered = (PayrollSettlementItem.objects.filter(reversed_at__isnull=True)
                 .aggregate(s=Sum('amount_recovered'))['s'] or _ZERO)
    return {'pending_payable': pending_payable,
            'advance_exposure': given - recovered}


# ── Advances (separate loan pool, derived — never stored) ──────────────────

def advance_remaining(advance: WorkerAdvance) -> Decimal:
    """How much of one advance is still outstanding = amount − Σ recovered."""
    recovered = (
        PayrollSettlementItem.objects.filter(advance=advance,
                                             reversed_at__isnull=True)
        .aggregate(s=Sum('amount_recovered'))['s'] or _ZERO
    )
    return advance.amount - recovered


def advance_outstanding(worker) -> Decimal:
    """Total advance still owed by a worker = Σ given − Σ recovered. Derived."""
    given = (
        WorkerAdvance.objects.filter(worker=worker)
        .aggregate(s=Sum('amount'))['s'] or _ZERO
    )
    recovered = (
        PayrollSettlementItem.objects.filter(advance__worker=worker,
                                             reversed_at__isnull=True)
        .aggregate(s=Sum('amount_recovered'))['s'] or _ZERO
    )
    return given - recovered


def outstanding_advances(worker):
    """Advances with a positive remaining balance (drives the settlement table).

    Shape: [{advance, amount, recovered, remaining}], oldest first.
    """
    advs = WorkerAdvance.objects.filter(worker=worker).order_by('advance_date', 'id')
    recovered_map = {
        r['advance']: r['s'] for r in
        # PA-11-1: exclude REVERSED recoveries (reversed_at set) — exactly like
        # advance_remaining / advance_outstanding. Without this filter a reversed
        # recovery still counts as recovered here, so after a settlement reversal the
        # restored advance is under-reported (or, if fully recovered-then-reversed,
        # drops out at the remaining>0 gate below) and the owner can't re-recover it.
        PayrollSettlementItem.objects.filter(advance__worker=worker,
                                             reversed_at__isnull=True)
        .values('advance').annotate(s=Sum('amount_recovered'))
    }
    out = []
    for a in advs:
        rec = recovered_map.get(a.id, _ZERO)
        remaining = a.amount - rec
        if remaining > _ZERO:
            out.append({'advance': a, 'amount': a.amount,
                        'recovered': rec, 'remaining': remaining})
    return out


def outstanding_advances_bulk(workers):
    """PA-16-2: batched `outstanding_advances` for MANY workers in 2 queries.

    The settlement-draft screen showed one worker's outstanding advances each
    (per-advance recovery inputs), calling outstanding_advances() in a loop →
    2 queries PER worker (a measured N+1 on a money-approval page). This returns
    {worker_id: [{advance, amount, recovered, remaining}]} with the SAME row shape
    and the SAME reversed_at filter, computed in 2 queries total regardless of the
    worker count. Workers with no positive-remaining advance are absent from the map.
    """
    ids = [getattr(w, 'pk', w) for w in workers]
    if not ids:
        return {}
    advs = (WorkerAdvance.objects.filter(worker_id__in=ids)
            .order_by('advance_date', 'id'))
    recovered_map = {
        r['advance']: r['s'] for r in
        PayrollSettlementItem.objects.filter(advance__worker_id__in=ids,
                                             reversed_at__isnull=True)
        .values('advance').annotate(s=Sum('amount_recovered'))
    }
    out: dict = {}
    for a in advs:
        rec = recovered_map.get(a.id, _ZERO)
        remaining = a.amount - rec
        if remaining > _ZERO:
            out.setdefault(a.worker_id, []).append(
                {'advance': a, 'amount': a.amount,
                 'recovered': rec, 'remaining': remaining})
    return out


def worker_advances(worker, *, limit=None):
    """All advances for a worker (newest first)."""
    qs = WorkerAdvance.objects.filter(worker=worker).order_by('-advance_date', '-id')
    return qs[:limit] if limit else qs


def worker_settlements(worker, *, limit=None):
    """Settlement history for a worker (newest first)."""
    qs = (
        PayrollSettlement.objects.filter(worker=worker)
        .order_by('-settlement_date', '-id')
    )
    return qs[:limit] if limit else qs


def can_view_worker(viewer, worker_id) -> bool:
    """A worker sees only their own payroll; management/admin see everyone.

    Never expose another worker's payroll without an explicit grant.
    """
    if not getattr(viewer, 'is_authenticated', False):
        return False
    if viewer.pk == worker_id:
        return True
    return (
        user_has_role(viewer, MANAGEMENT_ROLES)
        or user_has_perm(viewer, 'expense.view_all_payroll')
    )


def worker_summary(worker, *, since=None, until=None) -> dict:
    """Scoped payroll snapshot for one worker — drives the mobile dashboard.

    All figures are live sums (never stored):
      total_earnings    — Σ earning credits, net of voided-allocation reversals
      advance_outstanding — separate loan pool still owed (advance_outstanding())
      total_settled     — cash paid out across all settlements
      pending_payable   — Σcredits − Σdebits (what the factory still owes)
      earnings_in_window— earnings inside [since, until] (e.g. this month)
      last_settlement   — most recent PayrollSettlement, or None

    Under the settlement model advances do NOT debit the payable ledger, so
    pending_payable = earned − settled − recovered − deductions, never negative
    from an advance.
    """
    qs = WorkerLedgerEntry.objects.filter(worker=worker)

    # Reversals are netted by the CATEGORY of the entry they reverse (reverse_entry
    # writes an OPPOSITE-direction REVERSAL row linked via `reverses`):
    #   • undo an earning   → DEBIT/REVERSAL  → net out of total_earnings
    #   • undo a settlement → CREDIT/REVERSAL → net out of total_settled (and it
    #     must NOT count as a new earning, hence earnings is filtered to earning
    #     categories, not "all credits").
    # pending_payable nets ALL credits−debits, so it stays correct regardless.
    date_q = Q()
    if since is not None:
        date_q &= Q(entry_date__gte=since)
    if until is not None:
        date_q &= Q(entry_date__lte=until)
    earn_q = Q(entry_type=_ET.CREDIT, category__in=_EARNING_CATS)
    earn_rev_q = Q(category=_CAT.REVERSAL, reverses__category__in=_EARNING_CATS)
    settle_rev_q = Q(category=_CAT.REVERSAL, reverses__category=_CAT.SETTLEMENT_PAYMENT)

    agg = qs.aggregate(
        earned=Sum('amount', filter=earn_q),
        earned_reversed=Sum('amount', filter=earn_rev_q),
        credits=Sum('amount', filter=Q(entry_type=_ET.CREDIT)),
        debits=Sum('amount', filter=Q(entry_type=_ET.DEBIT)),
        settled=Sum('amount', filter=Q(entry_type=_ET.DEBIT, category=_CAT.SETTLEMENT_PAYMENT)),
        settled_reversed=Sum('amount', filter=settle_rev_q),
        earned_window=Sum('amount', filter=earn_q & date_q),
        earned_window_reversed=Sum('amount', filter=earn_rev_q & date_q),
    )
    earned = agg['earned'] or _ZERO
    earned_reversed = agg['earned_reversed'] or _ZERO
    credits = agg['credits'] or _ZERO
    debits = agg['debits'] or _ZERO
    settled = agg['settled'] or _ZERO
    settled_reversed = agg['settled_reversed'] or _ZERO
    last_settlement = (
        PayrollSettlement.objects.filter(worker=worker)
        .order_by('-settlement_date', '-id').first()
    )
    return {
        'total_earnings': earned - earned_reversed,    # net of voided allocations
        'advance_outstanding': advance_outstanding(worker),
        'total_settled': settled - settled_reversed,   # net of reversed settlements
        'pending_payable': credits - debits,
        'earnings_in_window': (agg['earned_window'] or _ZERO) - (agg['earned_window_reversed'] or _ZERO),
        'last_settlement': last_settlement,
    }


def worker_balance_breakdown(worker) -> dict:
    """Itemized derivation of a worker's payable — for reconciliation / disputes.

    Same bottom line as worker_summary's pending_payable, but broken into the
    components that net to it, so "why is the balance ₹X?" is a single call
    instead of re-doing the reversal-netting math by hand over raw ledger rows.
    All live sums (nothing stored); debits grouped by category.

    Shape:
      gross_earnings     — Σ earning credits (before reversal)
      earnings_reversed  — Σ reversal of earning rows (voided allocations)
      net_earnings       — gross − reversed
      debits_by_category — {category: Σ amount} across every DEBIT category
      total_credits / total_debits
      pending_payable    — credits − debits (the bottom line)
    """
    qs = WorkerLedgerEntry.objects.filter(worker=worker)
    earn_q = Q(entry_type=_ET.CREDIT, category__in=_EARNING_CATS)
    earn_rev_q = Q(category=_CAT.REVERSAL, reverses__category__in=_EARNING_CATS)
    agg = qs.aggregate(
        gross=Sum('amount', filter=earn_q),
        earn_reversed=Sum('amount', filter=earn_rev_q),
        credits=Sum('amount', filter=Q(entry_type=_ET.CREDIT)),
        debits=Sum('amount', filter=Q(entry_type=_ET.DEBIT)),
    )
    debits_by_cat = {
        r['category']: r['s'] for r in
        qs.filter(entry_type=_ET.DEBIT).values('category').annotate(s=Sum('amount'))
    }
    gross = agg['gross'] or _ZERO
    earn_reversed = agg['earn_reversed'] or _ZERO
    credits = agg['credits'] or _ZERO
    debits = agg['debits'] or _ZERO
    return {
        'gross_earnings': gross,
        'earnings_reversed': earn_reversed,
        'net_earnings': gross - earn_reversed,
        'debits_by_category': debits_by_cat,
        'total_credits': credits,
        'total_debits': debits,
        'pending_payable': credits - debits,
    }


def worker_ledger(worker, *, limit=None):
    """Recent ledger rows for a worker (newest first)."""
    qs = WorkerLedgerEntry.objects.filter(worker=worker).order_by('-created_at')
    return qs[:limit] if limit else qs


def worker_assignments(worker, *, limit=None):
    """Recent work allocations for a worker (newest first)."""
    qs = (
        StageWorkAssignment.objects.filter(worker=worker, voided_at__isnull=True)
        .select_related('stage_record__adda', 'bundle', 'size', 'color', 'pattern')
        .order_by('-created_at')
    )
    return qs[:limit] if limit else qs


def worker_production_stats(worker) -> dict:
    """Adda counts + pieces produced for a worker (Q1/Q2) — PRODUCTION truth
    (V2-3 PR-C, owner D-V3.3): pieces = Σ good_quantity on the worker's
    completed/verified tasks (S3 — payable-good, so productivity follows what
    settlement pays; good == reported in the thin slice), independent of settlement
    timing. Adda buckets come from assignment truth (non-cancelled tasks). Pre-V2-1c
    allocations that never had contributions are not counted — this is a productivity
    view, not a money view (the ledger is)."""
    from production.models import Adda, WorkerStageContribution, WorkerStageTask
    done = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED)
    pieces = (
        WorkerStageContribution.objects
        .filter(task__worker=worker, task__status__in=done)
        .aggregate(s=Sum('good_quantity'))['s'] or _ZERO
    )
    base = (WorkerStageTask.objects.filter(worker=worker)
            .exclude(status=WorkerStageTask.Status.CANCELLED))
    by_status = (
        base.values('stage_record__adda__status')
        .annotate(n=Count('stage_record__adda', distinct=True))
    )
    counts = {row['stage_record__adda__status']: row['n'] for row in by_status}
    return {
        'pieces_produced': pieces,
        'assigned_addas': base.values('stage_record__adda').distinct().count(),
        'active_addas': counts.get(Adda.Status.IN_PROGRESS, 0),
        'completed_addas': counts.get(Adda.Status.COMPLETED, 0),
    }


def _uncredited_lines(worker):
    """The worker's completed-but-UNCREDITED contribution lines — excludes
    lines already credited era-B (active settlement_line; a VOIDED line counts
    as unsettled again, mirroring the settlement guard) or era-A (non-voided
    allocation SWA on the same worker+stage, the same coarse pair rule the
    settlement uses). Shared by `unsettled_expected` + the R4 pay-basis
    warning, so both always agree on what "unsettled" means."""
    from production.models import WorkerStageContribution, WorkerStageTask
    done = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED)
    lines = (
        WorkerStageContribution.objects
        .filter(task__worker=worker, task__status__in=done)
        .filter(Q(settlement_line__isnull=True)
                | Q(settlement_line__voided_at__isnull=False))
        .select_related('task')
    )
    era_a_srs = set(
        StageWorkAssignment.objects
        .filter(worker=worker, voided_at__isnull=True,
                adda_settlement__isnull=True)
        .values_list('stage_record_id', flat=True)
    )
    return [c for c in lines if c.task.stage_record_id not in era_a_srs]


def unsettled_expected(worker):
    """Option B visibility (V2-3 PR-C): Σ frozen `expected_earning` of the
    worker's completed-but-UNCREDITED contribution lines — what a future Adda
    settlement would book. NEVER money (balances always come from the ledger).
    Non-overlapping with "Earned" by construction (see `_uncredited_lines`)."""
    return sum((c.expected_earning for c in _uncredited_lines(worker)
                if c.expected_earning is not None), _ZERO)


def unsettled_contribution_count(worker) -> int:
    """R4: how many uncredited contribution lines the worker has — the exact
    set whose settlement treatment flips with a pay-basis change (owner R4
    addendum: warn + explicit confirm before changing)."""
    return len(_uncredited_lines(worker))


# ── R4 (PDD §27-D4): pay basis — worker-level, never the stage ──────────────

def is_monthly(worker) -> bool:
    """Current pay basis, settlement-time semantics (owner P-1): read live,
    never snapshotted per contribution. Absent profile = piece-rate default."""
    return WorkerProfile.objects.filter(
        user=worker, pay_basis=WorkerProfile.PayBasis.MONTHLY).exists()


@transaction.atomic
def set_pay_basis(worker, new_basis, *, actor, confirmed=False):
    """THE pay-basis chokepoint (sole writer of WorkerPayBasisAudit).

    Guards, in order:
      • super_admin only (owner P-2) — a money-structure lever, manager is
        read-only; PermissionDenied otherwise.
      • valid basis + actually a change (no audit noise for no-ops).
      • owner R4 addendum: if the worker has unsettled contribution lines,
        require `confirmed=True` — warning + explicit confirmation, NOT a hard
        block. The refusal message carries the count for the UI to show.
    Writes profile (row-locked get_or_create) + append-only audit row that
    records the unsettled count the admin confirmed over.
    """
    from accounts.services import ROLE_SUPER_ADMIN
    if not user_has_role(actor, {ROLE_SUPER_ADMIN}):
        raise PermissionDenied("Only a Super Admin can change a worker's pay basis.")
    if new_basis not in WorkerProfile.PayBasis.values:
        raise ValidationError("Unknown pay basis.")
    # Serialize against settlement finalize/reverse (they hold this same lock
    # for their whole transaction) — same F1 pattern as rerate_stage_role.
    # Without it, a basis flip could commit between finalize's
    # _settleable_lines read and its money write, booking lines for a worker
    # who is monthly by commit time. pay basis is a settlement-boundary op.
    from django.db import connection
    if connection.vendor == 'postgresql':
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', [5374])
    # select_for_update: serialize concurrent basis changes AND pin the row a
    # concurrent settlement finalize would read (settlement-time semantics).
    profile, _ = WorkerProfile.objects.select_for_update().get_or_create(user=worker)
    if profile.pay_basis == new_basis:
        raise ValidationError("Pay basis is already set to that value.")
    unsettled = unsettled_contribution_count(worker)
    if unsettled and not confirmed:
        raise ValidationError(
            f"This worker has {unsettled} unsettled contribution line(s). "
            "Changing the pay basis changes how those lines settle "
            f"({'they will be EXCLUDED from settlement' if new_basis == WorkerProfile.PayBasis.MONTHLY else 'they will become PAYABLE at their frozen rates'}). "
            "Tick the confirmation to proceed.")
    old_basis = profile.pay_basis
    profile.pay_basis = new_basis
    profile.save(update_fields=['pay_basis', 'updated_at'])
    WorkerPayBasisAudit.objects.create(
        worker=worker, old_basis=old_basis, new_basis=new_basis,
        changed_by=actor, unsettled_lines_at_change=unsettled)
    logger.info("pay_basis.change worker=%s %s->%s by=%s unsettled=%s",
                worker.pk, old_basis, new_basis, actor.pk, unsettled)
    return profile


@transaction.atomic
def update_payout_profile(worker, *, actor, phone='', bank_account_name='',
                          bank_account_number='', bank_ifsc='', upi_id='',
                          joining_date=None, opening_advance=None,
                          is_active=True, notes=''):
    """THE WorkerProfile payout-details writer (RCP-1A F3, 2026-07-18).

    `opening_advance` is a DISPLAYED money fact (WP-A: informational — no
    computation reads it; recoverable pre-system advances go through
    `record_advance` as dated WorkerAdvance rows). F3 ruling: a management-
    facing ₹ figure still follows the pay-basis precedent (service chokepoint,
    never a bare form.save() in a view) — consistency + future-proofing if it
    ever becomes computational. Guards:
      • re-validated >= 0 here (never trust the form — mirrors set_pay_basis);
      • row-locked get_or_create (serialize vs concurrent settlement reads);
      • every opening_advance change audit-LOGGED old→new with actor (an
        append-only audit ROW like WorkerPayBasisAudit = a new table = U14
        owner-gated follow-up; the log trail is the interim record).
    `pay_basis` is deliberately NOT accepted — `set_pay_basis` (P-2 gate +
    audit row) stays the sole basis writer.
    """
    if opening_advance is None or opening_advance < 0:
        raise ValidationError("Opening advance must be zero or more.")
    profile, _ = WorkerProfile.objects.select_for_update().get_or_create(user=worker)
    old_advance = profile.opening_advance
    profile.phone = phone
    profile.bank_account_name = bank_account_name
    profile.bank_account_number = bank_account_number
    profile.bank_ifsc = bank_ifsc
    profile.upi_id = upi_id
    profile.joining_date = joining_date
    profile.opening_advance = opening_advance
    profile.is_active = is_active
    profile.notes = notes
    profile.save()
    if old_advance != opening_advance:
        logger.info("opening_advance.change worker=%s %s->%s by=%s",
                    worker.pk, old_advance, opening_advance, actor.pk)
    return profile


def worker_stage_earnings(worker):
    """Stage-wise earnings rollup (Q2): [{stage, earned, qty}] for non-voided work."""
    return list(
        StageWorkAssignment.objects.filter(worker=worker, voided_at__isnull=True)
        .values('stage_record__workflow_stage__stage__name')
        .annotate(earned=Sum('earning_amount_snapshot'), qty=Sum('allocated_quantity'))
        .order_by('stage_record__workflow_stage__stage__name')
    )


def worker_adda_earnings(worker, *, limit=None):
    """Per-Adda earnings + piece breakup for a worker (non-voided), newest Adda
    first. Each Adda lists the stages this worker did with pieces + earnings,
    plus an Adda total. Drives the 'Earnings by Adda' dashboard section.

    Shape: [{adda_code, product, status, stages:[{stage, pieces, earned}],
             total_pieces, total_earned}]
    NOTE: per-stage fields here are the baseline (stage · pieces · earned);
    stage-specific breakups (size/color, layers, etc.) to be refined per the
    owner's per-stage spec.
    """
    from collections import OrderedDict
    rows = (
        StageWorkAssignment.objects.filter(worker=worker, voided_at__isnull=True)
        .values(
            'stage_record__adda__code',
            'stage_record__adda__product__name',
            'stage_record__adda__status',
            'stage_record__workflow_stage__order',
            'stage_record__workflow_stage__stage__name',
        )
        .annotate(pieces=Sum('allocated_quantity'), earned=Sum('earning_amount_snapshot'))
        .order_by('-stage_record__adda__code', 'stage_record__workflow_stage__order')
    )
    addas: OrderedDict = OrderedDict()
    for r in rows:
        code = r['stage_record__adda__code']
        a = addas.setdefault(code, {
            'adda_code': code,
            'product': r['stage_record__adda__product__name'],
            'status': r['stage_record__adda__status'],
            'stages': [], 'total_pieces': _ZERO, 'total_earned': _ZERO,
        })
        a['stages'].append({
            'stage': r['stage_record__workflow_stage__stage__name'],
            'pieces': r['pieces'] or _ZERO,
            'earned': r['earned'] or _ZERO,
        })
        a['total_pieces'] += r['pieces'] or _ZERO
        a['total_earned'] += r['earned'] or _ZERO
    result = list(addas.values())
    return result[:limit] if limit else result
