"""Stage manufacturing-cost service — freeze / clear the cost snapshot.

YEH FILE KYU HAI?
─────────────────
Har stage execution (AddaStageRecord) ki MANUFACTURING COST yahan freeze hoti
hai — price-at-time-of-order pattern. Rate `WorkflowStage` pe bind karta hai
(editable over time); completion pe method+rate+quantity+computed cost
`AddaStageRecord` pe FREEZE ho jaate hain. Baad mein rate edit karo to purane
Adda ki cost nahi badalti.

YEH WORKER PAY NAHI HAI. `processing_cost` = manufacturing cost (product
costing + profitability). Worker earnings allocation-driven hain aur future
`expense` app mein compute hongi.

Single-writer: yehi module `AddaStageRecord` ke cost_* columns likhta hai,
apne dedicated `save(update_fields=[cost cols])` se — taaki complete_* ke
narrow update_fields lists naye columns ko silently drop na karein.

Freeze site: `adda_service.advance_to_next_stage` (the one choke point every
complete_* funnels through). Clear site: har `reopen_*`.

C-1 / ADR-0009 — THE COST DUALITY (read before writing ANY cost report):
processing_cost (standard cost: ws.cost_rate × handler quantity, role-
independent) and settled worker earnings (actual pay: role-aware frozen rate ×
reported/verified quantity, SWA + ledger) are TWO MEASUREMENTS OF THE SAME
LABOR for credits_workers stages. NEVER add them. Full Adda cost = material
(G1) + ACTUAL settled labor + processing_cost of NON-payable stages only
(+ future overhead, era-stamped). Standard-vs-actual is a future VARIANCE
report, never a sum. Per-Adda actual labor = Σ non-voided SWA snapshots (both
eras) — never WSC.expected_*, never Σ AddaSettlement totals.
"""
from __future__ import annotations

import logging  # module logger — debug-trace money writes (cost freeze/clear)
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from production.models import CostMethod

logger = logging.getLogger(__name__)

# Columns this module owns — written together as one atomic UPDATE.
_COST_FIELDS = [
    'cost_method_snapshot', 'cost_rate_snapshot', 'cost_quantity_snapshot',
    'processing_cost', 'cost_frozen_at', 'updated_at',
]
_CENT = Decimal('0.01')


def _quantity_for(sr, method: str) -> Decimal | None:
    """Resolve the cost quantity from the stage's HANDLER (registry-driven, M2.10#2).

    Delegates to the stage handler's cost_quantity (which reads the typed record):
      per_layer  → LayeringRecord.lay_count
      per_bundle → CuttingBundle row count
      per_piece  → CuttingRecord.pieces_cut OR BarcodeGenerationRecord.total_barcodes
      fixed_cost → None (quantity-independent)

    Returns None when no quantity is available (unpriced → processing_cost stays
    NULL, never 0) OR when the stage has no registered handler (preserves the
    pre-M2.10 fallback). NULL != 0.00 — see compute_processing_cost.
    """
    if method == CostMethod.FIXED:
        return None
    # Import-safe here: production.stages.base does not back-import cost_service.
    from production.stages import base as stage_registry
    code = sr.workflow_stage.stage.code
    if not stage_registry.has(code):
        return None
    return stage_registry.get(code).cost_quantity(sr)


def compute_processing_cost(sr) -> tuple[str, Decimal | None, Decimal | None, Decimal | None]:
    """Pure compute (no DB write) → (method, rate, quantity, processing_cost).

    Used by freeze_stage_cost + the invariant test. Encodes all the rules:
      • grouped (billed elsewhere)  → ('', None, None, 0.00)
      • unpriced (no method/rate)   → (method, rate, None, None)
      • fixed_cost                  → (method, rate, None, rate)
      • per_x with quantity         → (method, rate, qty, quantize(rate*qty))
      • per_x missing quantity      → (method, rate, None, None)
    """
    ws = sr.workflow_stage
    # Grouped stage: labour billed at the payer stage → priced-zero (NOT NULL).
    if ws.cost_billed_at_id is not None:
        return '', None, None, Decimal('0.00')

    method = ws.cost_method or ''
    rate = ws.cost_rate
    if not method or rate is None:
        return method, rate, None, None   # unpriced — honest NULL, never 0
    if method == CostMethod.FIXED:
        return method, rate, None, rate.quantize(_CENT, rounding=ROUND_HALF_UP)
    qty = _quantity_for(sr, method)
    if qty is None:
        return method, rate, None, None
    cost = (rate * qty).quantize(_CENT, rounding=ROUND_HALF_UP)
    return method, rate, qty, cost


def freeze_stage_cost(sr, *, user=None):
    """Freeze the manufacturing-cost snapshot onto a completed stage record.

    Idempotent — safe to re-run on re-complete after a reopen; overwrites the
    snapshot and advances cost_frozen_at. Does its OWN save(update_fields=[...])
    so it never depends on the caller's narrow update_fields list.

    Side effects:
      • Writes AddaStageRecord cost columns (cost_method_snapshot,
        cost_rate_snapshot, cost_quantity_snapshot, processing_cost,
        cost_frozen_at, updated_at) — the frozen money snapshot.
      • Reads WorkflowStage (method/rate/cost_billed_at) + typed stage records
        (LayeringRecord/CuttingRecord/CuttingBundle/BarcodeGenerationRecord) via
        compute_processing_cost for the quantity. No cross-app service calls.
    """
    method, rate, qty, cost = compute_processing_cost(sr)
    sr.cost_method_snapshot = method
    sr.cost_rate_snapshot = rate
    sr.cost_quantity_snapshot = qty
    sr.processing_cost = cost
    sr.cost_frozen_at = timezone.now()
    sr.save(update_fields=_COST_FIELDS)
    logger.info(
        "cost.freeze adda=%s stage_record=%s workflow_stage=%s method=%s "
        "rate=%s qty=%s processing_cost=%s user=%s",
        getattr(sr, 'adda_id', None), sr.pk, sr.workflow_stage_id,
        method or None, rate, qty, cost, getattr(user, 'pk', None),
    )
    return sr


def clear_stage_cost(sr):
    """Wipe the cost snapshot (for reopen). A reopened-but-not-recompleted
    stage must carry NO money; re-complete re-freezes via advance_to_next_stage.

    Side effects:
      • Writes AddaStageRecord cost columns (cost_method_snapshot,
        cost_rate_snapshot, cost_quantity_snapshot, processing_cost,
        cost_frozen_at, updated_at) back to empty/NULL — clears the money
        snapshot. No reads of other models, no cross-app service calls.
    """
    sr.cost_method_snapshot = ''
    sr.cost_rate_snapshot = None
    sr.cost_quantity_snapshot = None
    sr.processing_cost = None
    sr.cost_frozen_at = None
    sr.save(update_fields=_COST_FIELDS)
    logger.info(
        "cost.clear adda=%s stage_record=%s workflow_stage=%s",
        getattr(sr, 'adda_id', None), sr.pk, sr.workflow_stage_id,
    )
    return sr


def role_rate_for(workflow_stage, role):
    """Per-role rate override for a stage (Q7), or None to fall back to the
    stage's binding cost_rate. Drives worker EARNING (allocation + the V2
    expected-rate freeze); the stage's manufacturing processing_cost stays on
    ws.cost_rate (role-independent).

    C-1 (ADR-0009): a GROUPED MEMBER stage (cost_billed_at set) never yields a
    role rate — the payer stage's grouped rate covers the whole group, so a
    surviving WorkflowStageRoleRate row on a member must not become a second
    payment at settlement. Member contributions freeze rate None → settle ₹0."""
    if workflow_stage.cost_billed_at_id is not None:
        return None
    if role is None:
        return None
    from production.models import WorkflowStageRoleRate
    rr = WorkflowStageRoleRate.objects.filter(
        workflow_stage=workflow_stage, role=role,
    ).first()
    return rr.cost_rate if rr is not None else None


def resolved_payable_rate(workflow_stage, role):
    """The FROZEN payable rate a worker of `role` earns on this stage — the single
    source for both the AddaStageRoleRate snapshot (Foundation S2) and the
    complete-time freeze in complete_worker_task. Encodes the full resolution:
      grouped MEMBER stage (cost_billed_at set) → 0 (paid via the payer; never twice)
      else → per-role override (role_rate_for) → else stage base ws.cost_rate → else 0.
    NOTE: the grouped-member → 0 short-circuit MUST come first — role_rate_for
    returns None for a grouped member, which would otherwise fall through to the
    base rate (a second payment). Same order as the legacy complete-time logic."""
    if workflow_stage.cost_billed_at_id is not None:
        return Decimal('0')
    return role_rate_for(workflow_stage, role) or workflow_stage.cost_rate or Decimal('0')


def effective_pay_rate(workflow_stage, candidate_rate):
    """F2 (hostile-review fix 2026-06-14) — the STRUCTURAL grouped→0 guard, applied
    ANYWHERE a contribution's expected_rate / expected_earning is (re)computed: complete,
    rerate, and the settlement money-boundary. A grouped MEMBER stage (cost_billed_at set)
    must NEVER pay (C-1 / ADR-0009 double-pay prevention), so grouped status WINS over any
    candidate rate — including a STALE non-zero AddaStageRoleRate snapshot frozen before the
    stage was grouped. This is a hard structural invariant, not a business preference.
    A360 follow-up (owner rule, 2026-07-05): a NON-PAYABLE stage
    (`credits_workers=False`) behaves EXACTLY like a grouped member — rate 0,
    expected 0, no earning anywhere — instead of freezing a non-zero
    expectation the settlement funnel would never pay and UIs had to hide.
    ONE consistent rule across freeze / rerate / settlement / dashboards.
    Returns 0 for a grouped member or non-payable stage; otherwise the candidate
    unchanged (rate-freezing intact for non-structural edits — M-5)."""
    if workflow_stage.cost_billed_at_id is not None or not workflow_stage.credits_workers:
        return Decimal('0')
    return candidate_rate


def adda_cost_summary(adda) -> dict:
    """Per-Adda manufacturing-cost rollup (Q3/Q4/Q8). Honest-NULL: surfaces how
    many stages are unpriced rather than coercing NULL→0 (which would silently
    understate true cost). total_cost sums only frozen, priced rows.
    """
    from django.db.models import Sum
    from production.models import AddaStageRecord
    rows = list(
        AddaStageRecord.objects.filter(adda=adda)
        .select_related('workflow_stage__stage')
        .order_by('workflow_stage__order')
    )
    stages = [{
        'stage': sr.workflow_stage.stage.name,
        'method': sr.cost_method_snapshot or sr.workflow_stage.cost_method,
        'cost': sr.processing_cost,
        'frozen': sr.cost_frozen_at is not None,
    } for sr in rows]
    total = (
        AddaStageRecord.objects.filter(adda=adda, processing_cost__isnull=False)
        .aggregate(s=Sum('processing_cost'))['s']
    )
    unpriced = sum(
        1 for sr in rows
        if sr.completed_at is not None and sr.processing_cost is None
    )
    return {'stages': stages, 'total_cost': total, 'unpriced_count': unpriced}


def _material_value_expr(weight_field, price_field):
    """The ONE Decision-5 valuation expression (SQL side): weight × purchase
    ₹/kg — 2dp × 2dp ⇒ 4dp scale, matching the original Python derive's
    Decimal arithmetic exactly (byte-parity requirement, RMX-C)."""
    from django.db.models import DecimalField, ExpressionWrapper, F
    return ExpressionWrapper(
        weight_field * F(price_field),
        output_field=DecimalField(max_digits=14, decimal_places=4))


def material_costs_for_addas(adda_ids):
    """RMX-C (Phase 17, charter = PDD entry 8): the BULK material arm — the
    M13 per-Adda derive's exact rules as three GROUPED aggregates (entries +
    remnants + leftover-ins by adda). ONE valuation implementation;
    `material_cost_for_adda` delegates here (INERT; the original loop
    algorithm lives on inside the parity test as the independent reference —
    the queue-batching precedent). Returns {adda_id: {'consumed', 'remnant',
    'net', 'unpriced_rolls', 'leftover_in', 'has_material'}} with a row for
    EVERY requested id (empty Addas get the zero shape). READ-ONLY."""
    from decimal import Decimal

    from django.db.models import Count, F, Q, Sum, Value
    from django.db.models.functions import Coalesce, NullIf
    from production.models import LayeringRollEntry, RemainingClothOfClothRoll

    zero = Decimal('0.00')
    adda_ids = list(adda_ids)
    out = {pk: {'consumed': zero, 'remnant': zero, 'net': zero,
                'unpriced_rolls': 0, 'leftover_in': zero,
                'has_material': False} for pk in adda_ids}

    # Parity note: the original Python used `weight_verified_kg or roll.weight_kg`
    # — Decimal 0.00 is FALSY there, so a zero verified weight falls back to the
    # roll weight. NullIf(…, 0) replicates that exactly on the SQL side.
    entry_val = _material_value_expr(
        Coalesce(NullIf(F('weight_verified_kg'), Value(Decimal('0'))),
                 F('roll__weight_kg')),
        'roll__cost_per_kg')
    for r in (LayeringRollEntry.objects
              .filter(stage_record__adda_id__in=adda_ids)
              .values('stage_record__adda')
              .annotate(v=Sum(entry_val, filter=Q(roll__cost_per_kg__isnull=False)),
                        u=Count('id', filter=Q(roll__cost_per_kg__isnull=True)))):
        row = out[r['stage_record__adda']]
        row['consumed'] += r['v'] or zero
        row['unpriced_rolls'] += r['u']

    remnant_val = _material_value_expr(
        F('remaining_weight_kg'), 'layering_entry__roll__cost_per_kg')
    for r in (RemainingClothOfClothRoll.objects
              .filter(layering_entry__stage_record__adda_id__in=adda_ids)
              .values('layering_entry__stage_record__adda')
              .annotate(v=Sum(remnant_val,
                              filter=Q(layering_entry__roll__cost_per_kg__isnull=False)))):
        out[r['layering_entry__stage_record__adda']]['remnant'] += r['v'] or zero

    # V1.1 item-2 (locked C-1 rule): leftovers REUSED by an Adda count as its
    # material at the SOURCE roll's ₹/kg — never re-priced; the source Adda is
    # already net of the remnant it gave away ⇒ across Addas the intake value
    # is counted exactly once.
    lo_val = _material_value_expr(F('remaining_weight_kg'), 'roll__cost_per_kg')
    for r in (RemainingClothOfClothRoll.objects
              .filter(consumed_in_adda_id__in=adda_ids, is_consumed=True)
              .values('consumed_in_adda')
              .annotate(v=Sum(lo_val, filter=Q(roll__cost_per_kg__isnull=False)),
                        u=Count('id', filter=Q(roll__cost_per_kg__isnull=True)))):
        row = out[r['consumed_in_adda']]
        row['leftover_in'] += r['v'] or zero
        row['consumed'] += r['v'] or zero
        row['unpriced_rolls'] += r['u']

    for row in out.values():
        row['net'] = row['consumed'] - row['remnant']
        row['has_material'] = row['consumed'] > 0 or row['unpriced_rolls'] > 0
    return out


def material_cost_for_adda(adda):
    """M13 (2026-07-12): MATERIAL cost as a pure derive — Σ consumed roll value
    (verified kg × roll ₹/kg) minus remnant value, over the Adda's roll
    entries. Honest-NULL law: a consumed roll without a purchase price makes
    the figure INCOMPLETE (counted in `unpriced_rolls`, never as ₹0).
    Returns {'consumed', 'remnant', 'net', 'unpriced_rolls', 'has_material'}.
    Nothing stored — reconstructable by any auditor from raw tables.
    RMX-C (2026-07-18): delegates to the bulk arm — one valuation
    implementation (INERT, parity-pinned against the original loop)."""
    return material_costs_for_addas([adda.pk])[adda.pk]


def full_costs_for_addas(adda_ids):
    """RMX-C (Phase 17): THE Decision-2 assembly (ADR-0009), extracted from
    the live A360 implementation — ONE assembly for every consumer (A360, the
    Manufacturing Costing surface, tests). Per adda: full_cost = material.net
    + settled_total (Σ non-voided SWA earning snapshots — the Decision-3
    source, never WSC.expected_*) + processing_cost of NON-payable priced
    stage records. Decision 1 honored: the PAYABLE standard is NOT a
    component (never summed with settled labor). Honest-NULL flags pass
    through untouched. READ-ONLY; constant query count."""
    from decimal import Decimal

    from django.db.models import Sum
    from expense.models import StageWorkAssignment
    from production.models import AddaStageRecord

    zero = Decimal('0.00')
    adda_ids = list(adda_ids)
    material = material_costs_for_addas(adda_ids)
    settled = {
        r['stage_record__adda']: r['s'] or zero for r in
        StageWorkAssignment.objects
        .filter(stage_record__adda_id__in=adda_ids, voided_at__isnull=True)
        .values('stage_record__adda')
        .annotate(s=Sum('earning_amount_snapshot'))
    }
    nonpayable = {
        r['adda']: r['s'] or zero for r in
        AddaStageRecord.objects
        .filter(adda_id__in=adda_ids, processing_cost__isnull=False,
                workflow_stage__credits_workers=False)
        .values('adda').annotate(s=Sum('processing_cost'))
    }
    out = {}
    for pk in adda_ids:
        mat = material[pk]
        s = settled.get(pk, zero)
        np_ = nonpayable.get(pk, zero)
        out[pk] = {'material': mat, 'settled_total': s,
                   'nonpayable_priced': np_,
                   'full_cost': mat['net'] + s + np_}
    return out


def full_cost_for_adda(adda):
    """Single-Adda convenience over the ONE assembly (RMX-C)."""
    return full_costs_for_addas([adda.pk])[adda.pk]


def material_consumption_in_period(year: int, month: int) -> dict:
    """RMX-C (Phase 17): CONSUMPTION-in-period — the per-Adda derive's
    valuation law TIME-SLICED (one law, two windows): + layering entries
    attached in the period − remnants weighed back in the period + stored
    leftovers reused in the period, every value at the SOURCE roll's purchase
    ₹/kg (Decision 5; never re-priced). Honest-NULL: unpriced events COUNTED,
    never ₹0. Period = local-calendar month over the event timestamps
    (attached_at / created_at / consumed_at). Σ over all periods ≡ Σ over all
    Addas of material_cost_for_adda(..)['net'] — the standing one-rupee-once
    reconciliation identity (test-pinned). READ-ONLY; three aggregates."""
    from datetime import datetime as _dt
    from decimal import Decimal

    from django.core.exceptions import ValidationError
    from django.db.models import Count, F, Q, Sum, Value
    from django.db.models.functions import Coalesce, NullIf
    from django.utils import timezone as _tz
    from production.models import LayeringRollEntry, RemainingClothOfClothRoll

    if not (1 <= month <= 12 and 2000 <= year <= 2100):
        raise ValidationError("Invalid period (expected a real year/month).")
    zero = Decimal('0.00')
    start = _tz.make_aware(_dt(year, month, 1))
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    end = _tz.make_aware(_dt(ny, nm, 1))

    entry_val = _material_value_expr(
        Coalesce(NullIf(F('weight_verified_kg'), Value(Decimal('0'))),
                 F('roll__weight_kg')),
        'roll__cost_per_kg')
    e = (LayeringRollEntry.objects
         .filter(attached_at__gte=start, attached_at__lt=end)
         .aggregate(v=Sum(entry_val, filter=Q(roll__cost_per_kg__isnull=False)),
                    u=Count('id', filter=Q(roll__cost_per_kg__isnull=True))))
    remnant_val = _material_value_expr(
        F('remaining_weight_kg'), 'layering_entry__roll__cost_per_kg')
    r = (RemainingClothOfClothRoll.objects
         .filter(created_at__gte=start, created_at__lt=end)
         .aggregate(v=Sum(remnant_val,
                          filter=Q(layering_entry__roll__cost_per_kg__isnull=False))))
    lo_val = _material_value_expr(F('remaining_weight_kg'), 'roll__cost_per_kg')
    lo = (RemainingClothOfClothRoll.objects
          .filter(is_consumed=True, consumed_at__gte=start, consumed_at__lt=end)
          .aggregate(v=Sum(lo_val, filter=Q(roll__cost_per_kg__isnull=False)),
                     u=Count('id', filter=Q(roll__cost_per_kg__isnull=True))))

    consumed = (e['v'] or zero) + (lo['v'] or zero)
    remnant = r['v'] or zero
    return {'period_key': f"{year:04d}-{month:02d}",
            'consumed': consumed, 'remnant_returned': remnant,
            'leftover_in': lo['v'] or zero,
            'total': consumed - remnant,
            'unpriced_events': e['u'] + lo['u']}
