"""Worker-pay reconciliation (PAY-4).

The integrity control both payroll design docs named as primary and that was
never built. For each COMPLETED stage that froze a manufacturing cost, it
compares the work actually allocated to workers against the stage's frozen
output, and flags:

  unpaid          cost frozen but NO worker credited            (PAY-2 gap)
  under_allocated workers credited for < the output quantity    (PAY-2 gap)
  over_allocated  workers credited for MORE than produced       (always a defect)
  grouped_paid    a billed-elsewhere member stage has its own allocations (defect)
  unpriced_paid   an unpriced stage somehow has earnings        (defect)

QUANTITY-based, not money-based: role-based rates (WorkflowStageRoleRate) make
Σ earnings legitimately differ from processing_cost, but allocated QUANTITY
should equal the stage's output quantity when work is fully allocated.

Read-only. Reads production.AddaStageRecord + expense.StageWorkAssignment
(expense -> production is the existing data direction).
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal

from django.db.models import Sum

from expense.models import StageWorkAssignment

# Always a defect — these should never happen by design.
HARD_FLAGS = frozenset({'over_allocated', 'grouped_paid', 'unpriced_paid', 'no_output_qty'})
# The M-6 settlement WARN (S1.1, H1) is the B-1 leak ONLY: paid MORE than produced.
# Scoped narrower than HARD_FLAGS on purpose — no_output_qty / grouped_paid /
# unpriced_paid are different integrity concerns (and can't be the S5 BLOCK basis,
# e.g. you can't block a fixed-cost stage for having no output qty). Surfacing them
# as settlement warnings was noise that drowned the real leak. The full HARD_FLAGS
# set stays the `reconcile_pay` integrity report's domain.
SETTLEMENT_WARN_FLAGS = frozenset({'over_allocated'})
# The known PAY-2 gap — expected until allocation is wired into every paying
# stage at completion (M2.7); reported as a warning, not a hard failure.
SOFT_FLAGS = frozenset({'unpaid', 'under_allocated'})
# Healthy / expected-zero states.
CLEAN_FLAGS = frozenset({'ok', 'grouped', 'unpriced'})


def _classify(cost, out_qty, alloc_qty, earnings, method=None) -> str:
    if cost is None:                                  # unpriced stage
        return 'unpriced_paid' if earnings > 0 else 'unpriced'
    if cost == 0:                                     # grouped member (paid at payer)
        return 'grouped_paid' if alloc_qty > 0 else 'grouped'
    # R8 (V-6 audit): fixed_cost is quantity-INDEPENDENT by design (frozen
    # cost = rate, out_qty = None) — without this branch every fixed stage
    # false-flagged 'no_output_qty'. Honest fixed check: paid ≤ the fixed
    # amount (the WP-4 double-guard makes > impossible; classify truthfully).
    if method == 'fixed_cost':
        return 'over_allocated' if earnings > cost else 'ok'
    if out_qty is None:                               # priced but no frozen qty — anomaly
        return 'no_output_qty'
    if alloc_qty == 0:
        return 'unpaid'
    if alloc_qty < out_qty:
        return 'under_allocated'
    if alloc_qty > out_qty:
        return 'over_allocated'
    return 'ok'


def reconcile_stage_pay(*, adda=None) -> list[dict]:
    """Return one reconciliation row per completed stage record (optionally scoped
    to a single Adda), ordered by adda code then stage order."""
    from production.models import AddaStageRecord

    srs = (
        AddaStageRecord.objects
        .filter(completed_at__isnull=False)
        .select_related('adda', 'workflow_stage__stage')
    )
    if adda is not None:
        srs = srs.filter(adda=adda)
    srs = srs.order_by('adda__code', 'workflow_stage__order')

    rows = []
    for sr in srs:
        agg = (
            StageWorkAssignment.objects
            .filter(stage_record=sr, voided_at__isnull=True)
            .aggregate(q=Sum('allocated_quantity'), m=Sum('earning_amount_snapshot'))
        )
        alloc_qty = agg['q'] or Decimal('0')
        earnings = agg['m'] or Decimal('0')
        cost = sr.processing_cost          # None=unpriced, 0=grouped, >0=self-paid
        out_qty = sr.cost_quantity_snapshot
        rows.append({
            'adda': sr.adda.code,
            'stage': sr.workflow_stage.stage.code,
            # Lanes: one stage code can have N stage records (one per stream) —
            # consumers needing the exact row (evidence FK) must use the pk,
            # never the code (OWN-C fix 2026-07-13).
            'stage_record_id': sr.pk,
            'processing_cost': cost,
            'output_qty': out_qty,
            'allocated_qty': alloc_qty,
            'earnings': earnings,
            'qty_delta': (out_qty - alloc_qty) if out_qty is not None else None,
            'flag': _classify(cost, out_qty, alloc_qty, earnings,
                              method=sr.cost_method_snapshot),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    """Roll reconciliation rows up into counts + hard/soft totals."""
    counts = Counter(r['flag'] for r in rows)
    return {
        'total': len(rows),
        'counts': dict(counts),
        'hard': sum(counts[f] for f in HARD_FLAGS),
        'soft': sum(counts[f] for f in SOFT_FLAGS),
        'clean': sum(counts[f] for f in CLEAN_FLAGS),
    }
