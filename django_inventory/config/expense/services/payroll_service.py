"""Payroll read service — aggregations + per-worker access scoping. No writes.

Everything here is derived live from the ledger (never a stored total).
"""
from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum

from accounts.services import MANAGEMENT_ROLES, user_has_perm, user_has_role
from expense.models import (
    PayrollSettlement, PayrollSettlementItem, StageWorkAssignment,
    WorkerAdvance, WorkerLedgerEntry,
)

_ZERO = Decimal('0.00')
_ET = WorkerLedgerEntry.EntryType
_CAT = WorkerLedgerEntry.Category
# Credit categories that count as real earnings. Other credits (e.g. a REVERSAL
# credit written when a settlement payment is undone) must NOT inflate earnings.
_EARNING_CATS = (_CAT.STAGE_EARNING, _CAT.PRODUCTION_EARNING)


# ── Advances (separate loan pool, derived — never stored) ──────────────────

def advance_remaining(advance: WorkerAdvance) -> Decimal:
    """How much of one advance is still outstanding = amount − Σ recovered."""
    recovered = (
        PayrollSettlementItem.objects.filter(advance=advance)
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
        PayrollSettlementItem.objects.filter(advance__worker=worker)
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
        PayrollSettlementItem.objects.filter(advance__worker=worker)
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
    """Adda counts + pieces produced for a worker (Q1/Q2). From non-voided
    allocations: pieces = Σ allocated_quantity; Adda buckets by status."""
    from production.models import Adda
    base = StageWorkAssignment.objects.filter(worker=worker, voided_at__isnull=True)
    pieces = base.aggregate(s=Sum('allocated_quantity'))['s'] or _ZERO
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
