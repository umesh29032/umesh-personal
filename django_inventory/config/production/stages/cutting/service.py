"""Cutting stage service — full lifecycle (PR3 2026-05-28).

PRODUCTION FLOW MEIN POSITION:
  Layering → (Pattern Design) → Cutting

CUTTING STAGE MATLAB:
  Layered cloth + verified patterns ko actual cut pieces mein convert
  karna. Cutting master:
    - start_cutting     → workers assign hote hain
    - upsert_breakup_row → ek (size, color, pattern) ke pieces count
    - save_cutting_draft → notes + partial breakup persist (no advance)
    - complete_cutting  → strict validation + barcode generation + advance
    - reopen_cutting    → admin unlock (refused if any barcode scanned)

DUAL-PATH `complete_cutting`:
  Backward-compat: agar `pieces_cut` int paas hoti hai aur breakup rows
  empty hain to legacy single-shot path use hota (NIKKAR-style products
  without cutting_pattern stage). Workspace path: breakup rows pre-populated
  + pieces_cut auto-derived. Discriminator = `pieces_cut` argument.

SUGGESTED BREAKUP FORMULA:
  layers_total × Σ ProductPatternAssignment.pieces_count × allocation_pct / 100
  per (pattern, size, color) — equal-share across distinct rolls' colors.

PERMISSIONS:
  • start_cutting        → MANAGEMENT_ROLES (assign workers)
  • upsert/delete row    → cutting_master OR cutting_master_helper skill
                           (management bypass)
  • complete_cutting     → cutting_master_helper skill OR super_admin
  • reopen_cutting       → MANAGEMENT_ROLES
"""
from __future__ import annotations

import logging
from typing import Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from accounts.services import MANAGEMENT_ROLES, ROLE_SUPER_ADMIN, user_has_role
from production.constants import (
    STAGE_BARCODE_GENERATION, STAGE_CUTTING, STAGE_CUTTING_PATTERN, STAGE_LAYERING,
)
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingBundle,
    CuttingBundleItem, CuttingPatternRecord, CuttingPieceBreakup,
    CuttingRecord, ProductPatternAssignment, ProductSize,
    WorkflowStage,
)
from production.services.adda_service import advance_to_next_stage

from production.services._shared import reopen_stage_record

# Module logger — debug fan-out of multi-table / cross-app cutting writes.
logger = logging.getLogger(__name__)

# M6 — completion LISTENERS (the ARCHIVE_VALIDATORS inversion, reviewed
# in MANUFACTURING_INTEGRATION_REVIEW §4): patterns_ai registers a
# stamper in apps.ready(); each listener is called (adda, stage_record)
# AFTER a successful completion, individually wrapped — a listener
# failure NEVER breaks cutting (logged instead).
CUTTING_COMPLETE_LISTENERS = []


# ── Auth gates ─────────────────────────────────────────────────────────────

def _ensure_cutting_skill(user):
    """Upsert / delete row — master or helper skill required (mgmt bypass)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        raise PermissionDenied(
            "requires cutting_master or cutting_master_helper skill"
        )


def _ensure_can_complete_cutting(user):
    """Complete + advance — helper skill or super_admin only."""
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied(
            "only cutting_master_helper can complete the cutting stage"
        )


# ── Stage discovery helpers ────────────────────────────────────────────────

def _cutting_workflow_stage(adda: Adda) -> WorkflowStage | None:
    """Iss Adda ke Product ka cutting WorkflowStage row return."""
    return adda.product.workflow_stages.filter(stage__code=STAGE_CUTTING).first()


def _pattern_record_for_adda(adda: Adda, stream=None) -> CuttingPatternRecord | None:
    """Pattern stage ka CuttingPatternRecord (if pattern stage in workflow + completed).

    GAP-2 (final audit 2026-07-11): stream=lane ⇒ THAT lane's record (legacy
    NULL rows adopt, same Q as lane_stage_record) — completion validations must
    read the LANE's truth, never an arbitrary sibling lane's. stream=None keeps
    the old adda-level read for the informational console paths."""
    pattern_wf = adda.product.workflow_stages.filter(
        stage__code=STAGE_CUTTING_PATTERN,
    ).first()
    if pattern_wf is None:
        return None
    from django.db.models import Q
    qs = AddaStageRecord.objects.filter(adda=adda, workflow_stage=pattern_wf)
    if stream is not None:
        qs = qs.filter(Q(stream=stream) | Q(stream__isnull=True))
    sr = qs.order_by('stream_id').first()
    if sr is None:
        return None
    return getattr(sr, 'cutting_pattern', None)


def _get_or_create_cutting_stage_record(adda: Adda,
                                        stream=None) -> AddaStageRecord:
    """Lazy-create AddaStageRecord for cutting stage (lane-scoped).

    Streams: the gate is the LANE's readiness — its pattern check must be
    complete before its cutting opens (pointer equality retired).
    """
    wf = _cutting_workflow_stage(adda)
    if wf is None:
        raise ValidationError("This product does not include the cutting stage.")
    from django.db.models import Q
    from production.services.adda_service import (
        lane_stage_record, resolve_stream)
    lane = resolve_stream(adda, stream)
    # refuse ONLY a started-but-unchecked pattern on THIS lane (a missing
    # record = legacy/blind flows, exactly the old pointer behavior)
    pattern_open = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code='cutting_pattern',
        completed_at__isnull=True).filter(
        Q(stream=lane) | Q(stream__isnull=True)).exists()
    if pattern_open:
        raise ValidationError(
            f"Complete the {lane.label} pattern check before its cutting.")
    sr = lane_stage_record(adda, wf, lane, create=True,
                           defaults={'started_at': timezone.now()})
    created = getattr(sr, '_lane_created', False)
    if created and not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    if created:
        # PA-10-3 (Contract 2): snapshot the frozen payable-rate AT creation, like
        # every other SR site (create_adda/start_layering/barcode). Idempotent. Without
        # it, the cutting rate snapshot was late-created at first worker completion with
        # a spurious "snapshot_missing_at_complete" WARNING (the codebase treats that as
        # a bug signal) + no pre-completion rate row existed. Caller is @transaction.atomic.
        from production.services.stage_rate_service import ensure_stage_role_rates
        ensure_stage_role_rates(sr)
    return sr


def _get_or_create_cutting_record(adda: Adda, stream=None) -> CuttingRecord:
    """CuttingRecord lazy-create — pieces_cut default 0 jab tak complete."""
    sr = _get_or_create_cutting_stage_record(adda, stream=stream)
    cr, _ = CuttingRecord.objects.get_or_create(
        stage_record=sr, defaults={'pieces_cut': 0, 'notes': ''},
    )
    return cr


def _product_has_barcode_gen_stage(adda: Adda) -> bool:
    """Iss Adda ke product workflow mein barcode_generation stage hai ya nahi?

    Determines whether cutting completion should inline-generate barcodes
    (back-compat for legacy products) or defer to the barcode_generation
    stage. Per BARCODE_STAGE_PLAN.md D3.
    """
    return adda.product.workflow_stages.filter(
        stage__code=STAGE_BARCODE_GENERATION,
    ).exists()


def _materialize_breakdown(cr: CuttingRecord, user) -> int:
    """Cutting bundles ko per-(size, color) aggregate karke
    AddaProductSizeColorPieceBreakdown rows freeze karta hai.

    Aggregation: SUM(CuttingBundleItem.count) GROUP BY (bundle.size_id, color_id).
    Pattern dimension collapse hota — barcode generation patterns mein
    interested nahi (sticker pe sirf size + color print hota).

    Idempotent: get_or_create ensures re-run pe duplicate row nahi banta
    (unique_together cutting_record + size + color).

    Returns: total breakdown rows materialised.

    Side effects:
      • Writes AddaProductSizeColorPieceBreakdown rows (get_or_create per
        (size, color), or one NULL/NULL legacy row from pieces_cut).
    """
    from collections import defaultdict
    adda = cr.stage_record.adda
    product = adda.product
    # Streams redesign: the lane's BREAKUP rows are the first-class actual
    # (owner Cutting spec); bundle items = legacy fallback.
    brk = list(cr.breakup.select_related('size', 'color'))
    if brk:
        agg = defaultdict(int)
        for b in brk:
            agg[(b.size_id, b.color_id)] += b.count
        for (size_id, color_id), count in agg.items():
            AddaProductSizeColorPieceBreakdown.objects.get_or_create(
                cutting_record=cr, size_id=size_id, color_id=color_id,
                defaults={
                    'adda': adda, 'product': product, 'bundle': None,
                    'verified_piece_count': count,
                    'created_by': user,
                },
            )
        logger.info(
            "cutting.materialize_breakdown adda=%s cutting_record=%s rows=%s mode=breakup",
            adda.code, cr.id, len(agg),
        )
        return len(agg)
    items = list(
        CuttingBundleItem.objects
        .filter(bundle__cutting_record=cr)
        .select_related('bundle')
    )
    if items:
        # Per (size, color) sum + remember first bundle FK for each key
        agg: dict[tuple[int, int], int] = defaultdict(int)
        bundle_by_key: dict[tuple[int, int], int] = {}
        for it in items:
            key = (it.bundle.size_id, it.color_id)
            agg[key] += it.count
            bundle_by_key.setdefault(key, it.bundle_id)
        for (size_id, color_id), count in agg.items():
            AddaProductSizeColorPieceBreakdown.objects.get_or_create(
                cutting_record=cr, size_id=size_id, color_id=color_id,
                defaults={
                    'adda': adda, 'product': product,
                    'bundle_id': bundle_by_key[(size_id, color_id)],
                    'verified_piece_count': count,
                    'created_by': user,
                },
            )
        logger.info(
            "cutting.materialize_breakdown adda=%s cutting_record=%s rows=%s mode=bundles",
            adda.code, cr.id, len(agg),
        )
        return len(agg)
    # Legacy: no bundle items → single (NULL, NULL) row from pieces_cut.
    if cr.pieces_cut > 0:
        AddaProductSizeColorPieceBreakdown.objects.get_or_create(
            cutting_record=cr, size=None, color=None,
            defaults={
                'adda': adda, 'product': product, 'bundle': None,
                'verified_piece_count': cr.pieces_cut,
                'created_by': user,
            },
        )
        logger.info(
            "cutting.materialize_breakdown adda=%s cutting_record=%s rows=1 "
            "mode=legacy pieces_cut=%s",
            adda.code, cr.id, cr.pieces_cut,
        )
        return 1
    return 0


# ── Snapshot + suggestion (read-only) ──────────────────────────────────────

def preview_barcode_batches(adda: Adda) -> list[dict]:
    """Compute the BarcodeBatch ranges that WOULD be generated on complete.

    Useful for UI preview before user clicks "Mark Complete". Reads bundle
    items, aggregates by (size, color), and lays out contiguous seq ranges
    using the same allocation order as tracking.generate_for_cutting.

    Returns: list of dicts:
        {'bundle', 'size', 'color', 'start_seq', 'end_seq', 'total'}
    Empty list if no bundle items exist yet.
    """
    cr = CuttingRecord.objects.filter(stage_record__adda=adda).first()
    if cr is None:
        return []
    items = list(
        CuttingBundleItem.objects
        .filter(bundle__cutting_record=cr)
        .select_related('bundle__size', 'color')
    )
    if not items:
        return []

    from collections import defaultdict
    agg: dict[tuple[int, int], int] = defaultdict(int)
    ref: dict[tuple[int, int], dict] = {}
    for it in items:
        if it.count <= 0:
            continue
        key = (it.bundle.size_id, it.color_id)
        agg[key] += it.count
        ref.setdefault(key, {
            'bundle': it.bundle,
            'size': it.bundle.size,
            'color': it.color,
        })

    # Sort by (size.display_order, size.code, color.name) for determinism —
    # match tracking.barcode_service._allocation_key.
    sorted_keys = sorted(
        agg.keys(),
        key=lambda k: (
            ref[k]['size'].display_order if ref[k]['size'] else 0,
            ref[k]['size'].code if ref[k]['size'] else '',
            ref[k]['color'].name if ref[k]['color'] else '',
        ),
    )

    preview: list[dict] = []
    next_seq = 1
    for k in sorted_keys:
        count = agg[k]
        info = ref[k]
        preview.append({
            'bundle': info['bundle'],
            'size': info['size'],
            'color': info['color'],
            'start_seq': next_seq,
            'end_seq': next_seq + count - 1,
            'total': count,
        })
        next_seq += count
    return preview


def get_cutting_snapshot(adda: Adda, stream=None) -> dict:
    """Lightweight snapshot — drives cutting workspace state.

    Mirrors get_layering_snapshot / get_pattern_snapshot shape.
    """
    wf = _cutting_workflow_stage(adda)
    if wf is None:
        return {'state': 'absent'}
    qs = AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf)
    if stream is not None:
        from django.db.models import Q
        qs = qs.filter(Q(stream=stream) | Q(stream__isnull=True))
    sr = qs.order_by('stream_id').first()
    if sr is None:
        return {'state': 'not_started', 'workflow_stage': wf}
    cr = getattr(sr, 'cutting', None)
    breakup = list(cr.breakup.select_related('size', 'color', 'pattern', 'roll').all()) if cr else []
    if cr:
        bundles = list(
            cr.bundles.select_related('size')
            .prefetch_related('items__pattern', 'items__color')
            .order_by('size__display_order', 'size__code')
        )
    else:
        bundles = []
    # PR11: bundle view shows color × count aggregate (pattern collapsed).
    # Each bundle gets `.color_summary` = list of dicts sorted by color name.
    for bundle in bundles:
        agg: dict[int, dict] = {}
        for it in bundle.items.all():
            cid = it.color_id
            entry = agg.setdefault(cid, {
                'color': it.color, 'count': 0, 'patterns': set(),
            })
            entry['count'] += it.count
            entry['patterns'].add(it.pattern.name)
        bundle.color_summary = sorted(agg.values(), key=lambda e: e['color'].name)
    bundle_total = sum(b.total_pieces for b in bundles)
    return {
        'state': 'completed' if sr.completed_at else 'in_progress',
        'workflow_stage': wf,
        'stage_record': sr,
        'cutting_record': cr,
        'breakup': breakup,
        'bundles': bundles,
        'breakup_total': sum(row.count for row in breakup),
        'bundle_total': bundle_total,
        # total_pieces = bundle total (drives barcodes); breakup is informational.
        'total_pieces': bundle_total,
        'started_at': sr.started_at,
        'completed_at': sr.completed_at,
        'completed_by': sr.completed_by,
    }


def _layout_content(adda: Adda):
    """Phase 8C — the manufacturing contract's MARKER CONTENT via the
    registered provider (the 8B inversion; production imports nothing).
    Returns ({(pattern_id, size_id): count}, [layout_uids]) or
    (None, []) when no contract / no provider / provider failure — the
    classic formula stays the fallback FOREVER."""
    from production.stages.cutting_pattern import handler as _cp
    if _cp.LAYOUT_PROVIDER is None:
        return None, []
    try:
        panel = _cp.LAYOUT_PROVIDER(adda)
    except Exception:                                   # noqa: BLE001
        logger.exception('layout provider failed for adda %s', adda.pk)
        return None, []
    rows = (panel or {}).get('content_by_pattern_size') or []
    if not rows:
        return None, []
    content = {(r['pattern_id'], r['size_id']): int(r['count'])
               for r in rows}
    return content, (panel or {}).get('layout_uids', [])


def get_suggestion_source(adda: Adda) -> dict:
    """What feeds the pre-fill — the honest workspace label.
    {'kind': 'layout', 'uids': [...]} | {'kind': 'formula'}."""
    content, uids = _layout_content(adda)
    if content:
        return {'kind': 'layout', 'uids': uids}
    return {'kind': 'formula'}


def layout_reconciliation(adda: Adda) -> dict | None:
    """Phase 8C — ADVISORY expected-vs-actual (the count hierarchy):
    expected(size) = marker content × lay_count (production's OWN plies
    truth — the provider never touches plies); actual(size) = Σ live
    CuttingBundleItem counts. NEVER blocks, NEVER writes — warnings
    explain; the operator's numbers remain the manufacturing truth."""
    from django.db.models import Sum
    content, uids = _layout_content(adda)
    if not content:
        return None
    layering_record = _get_layering_record_for_adda(adda)
    if layering_record is None or layering_record.lay_count <= 0:
        return None
    lay = layering_record.lay_count
    expected: dict[int, int] = {}
    for (_pattern_id, size_id), n in content.items():
        expected[size_id] = expected.get(size_id, 0) + n * lay
    # GAP-5: the actuals are the BREAKUP rows (adda-wide, every lane) — the
    # same truth completion uses; live bundle items remain the legacy
    # fallback for pre-streams data (bundles are post-join containers now).
    actual: dict[int, int] = {}
    for row in (CuttingPieceBreakup.objects
                .filter(cutting_record__stage_record__adda=adda)
                .values('size_id')
                .annotate(total=Sum('count'))):
        actual[row['size_id']] = row['total'] or 0
    if not actual:
        cr = CuttingRecord.objects.filter(stage_record__adda=adda).first()
        if cr is not None:
            for row in (CuttingBundleItem.objects
                        .filter(bundle__cutting_record=cr)
                        .values('bundle__size_id')
                        .annotate(total=Sum('count'))):
                actual[row['bundle__size_id']] = row['total'] or 0
    size_labels = dict(adda.product.sizes.values_list('pk', 'label'))
    mismatches = []
    for size_id in sorted(set(expected) | set(actual)):
        e, a = expected.get(size_id, 0), actual.get(size_id, 0)
        if e != a:
            mismatches.append({'size_id': size_id,
                               'label': size_labels.get(size_id, size_id),
                               'expected': e, 'actual': a})
    return {'uids': uids, 'expected': expected, 'actual': actual,
            'mismatches': mismatches}


def get_suggested_breakup(adda: Adda) -> list[dict]:
    """Pre-fill suggestion — formula based on layering + pattern stage data.

    Formula:
        layers_total = LayeringRecord.lay_count (SUM across rolls)
        for each ProductPatternAssignment (pattern, pieces_per_adda):
          pattern_total = layers_total × pieces_per_adda
          for each CuttingPatternSizeAllocation (size, pct):
            size_share = pattern_total × pct / 100
            for each distinct color in layering.rolls_used:
              color_share = round(size_share / num_distinct_colors)
              suggestions[(pattern, size, color)] = color_share

    Returns: list of {pattern_id, size_id, color_id, count} dicts.

    Edge cases:
      • No layering record / no lay_count → empty list (workspace shows
        "Suggestion unavailable" hint)
      • No pattern stage / no allocations → empty list
      • Result counts are integer (round-half-up)
    """
    layering_record = _get_layering_record_for_adda(adda)
    if layering_record is None or layering_record.lay_count <= 0:
        return []
    layers_total = layering_record.lay_count

    # Distinct colors from layering rolls_used (frozen at layering complete).
    # `set()` ensures uniqueness regardless of M2M JOIN duplicates.
    colors = sorted(set(
        layering_record.rolls_used.values_list('cloth_color_id', flat=True)
    ))
    if not colors:
        return []

    # ── Phase 8C: the manufacturing CONTRACT is the numbers source when
    # a layout usage exists — expected = MARKER CONTENT × lay_count
    # (count hierarchy: content from the approved layout, plies from
    # layering — production's own truth). ADVISORY prefill, same shape,
    # operator overrides freely. No contract → classic formula below.
    content, _uids = _layout_content(adda)
    if content:
        suggestions: list[dict] = []
        num_colors = len(colors)
        for (pattern_id, size_id), per_marker in sorted(content.items()):
            size_share = per_marker * layers_total
            per_color = round(size_share / num_colors)
            for color_id in colors:
                suggestions.append({'pattern_id': pattern_id,
                                    'size_id': size_id,
                                    'color_id': color_id,
                                    'count': per_color})
        return suggestions

    pattern_record = _pattern_record_for_adda(adda)
    if pattern_record is None:
        return []
    allocations = list(pattern_record.size_allocations.select_related('size').all())
    if not allocations:
        return []

    assignments = list(
        adda.product.pattern_assignments.select_related('pattern').all()
    )
    if not assignments:
        return []

    suggestions: list[dict] = []
    num_colors = len(colors)
    for a in assignments:
        pattern_total = layers_total * a.pieces_count
        for alloc in allocations:
            size_share = pattern_total * alloc.proportion_pct / 100
            # Distribute equally across distinct colors. round() half-up.
            per_color = round(size_share / num_colors)
            for color_id in colors:
                suggestions.append({
                    'pattern_id': a.pattern_id,
                    'size_id': alloc.size_id,
                    'color_id': color_id,
                    'count': per_color,
                })
    return suggestions


def _get_layering_record_for_adda(adda: Adda, stream=None):
    """Layering stage ka typed record (None agar layering nahi hua)."""
    layering_wf = adda.product.workflow_stages.filter(stage__code=STAGE_LAYERING).first()
    if layering_wf is None:
        return None
    from django.db.models import Q
    qs = AddaStageRecord.objects.filter(adda=adda, workflow_stage=layering_wf)
    if stream is not None:
        qs = qs.filter(Q(stream=stream) | Q(stream__isnull=True))
    sr = qs.order_by('stream_id').first()
    if sr is None:
        return None
    return getattr(sr, 'layering', None)


# ── Write services ─────────────────────────────────────────────────────────

@transaction.atomic
def start_cutting(*, adda: Adda, worker_ids: Iterable[int], user,
                  stream=None) -> AddaStageRecord:
    """Manager workers assign karta hai → stage formally start.

    Side effects:
      • Writes AddaStageRecord (lazy get_or_create) + its workers M2M.
      • Calls tracking.log_adda → writes AddaHistory (WORKERS_ASSIGNED).
    """
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can start the cutting stage")
    sr = _get_or_create_cutting_stage_record(adda, stream=stream)
    worker_id_list = list(worker_ids)
    from production.services.worker_task_service import set_stage_workers
    set_stage_workers(sr, worker_id_list)   # dual-write: M2M (authoritative) + WorkerStageTask
    if not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
             stage_record=sr, metadata={'worker_ids': worker_id_list})
    logger.info(
        "cutting.start adda=%s stage_record=%s worker_count=%s worker_ids=%s",
        adda.code, sr.id, len(worker_id_list), worker_id_list,
    )
    return sr


# ── Actual Bundle Entry (PR8 + PR9 2026-05-28) ──────────────────────────────
# Bundle = per-size manufacturing container.
# CuttingBundle: one per (cutting_record, size). total_pieces denormalized.
# CuttingBundleItem: pattern × color × count inside the bundle.
# Barcode generator iterates items, aggregates by (size, color).
#
# PR9 two-step UI flow:
#   1. create_bundle(size, bundle_number)     → explicit header creation
#   2. add_item_to_bundle(bundle, pat, col, count) → add items scoped to bundle
# add_bundle_item(...) kept as shortcut (size picker + auto-bundle).

def _recompute_bundle_total(bundle: CuttingBundle) -> None:
    """Re-sum bundle.total_pieces from items + save. Called on item write/del."""
    total = sum(it.count for it in bundle.items.all())
    if bundle.total_pieces != total:
        bundle.total_pieces = total
        bundle.save(update_fields=['total_pieces', 'updated_at'])


@transaction.atomic
def _ensure_bundling_open(adda: Adda) -> None:
    """GAP-5 (frozen PROPOSAL §3 / final review §4): bundles are POST-JOIN,
    Adda-level complete-product containers. Creation/consumption is refused
    until every blocking lane's cutting is complete — the garment exists only
    at the join. (Pre-GAP-5 the writers anchored to ONE lane's cutting record
    and refused AFTER it completed — post-join bundling was impossible on
    multi-lane Addas; found live in the Bundle Assembly review.)"""
    from production.services.adda_service import preproduction_joined
    if not preproduction_joined(adda):
        raise ValidationError(
            "Bundling unlocks when every cutting lane is complete — "
            "finish the remaining lane(s) first.")


def _get_bundle_for_adda(adda: Adda, bundle_id: int) -> CuttingBundle:
    """Adda-level bundle lookup: new rows anchor on `adda` (cutting_record
    NULL); legacy rows (pre-streams) anchor via their cutting record — both
    editable post-join."""
    from django.db.models import Q
    try:
        return (CuttingBundle.objects.select_related('size')
                .get(Q(adda=adda) | Q(cutting_record__stage_record__adda=adda),
                     pk=bundle_id))
    except CuttingBundle.DoesNotExist:
        raise ValidationError("Bundle does not belong to this Adda.")


def create_bundle(
    *, adda: Adda, size_id: int, bundle_number: str = '', user,
    stream=None) -> CuttingBundle:
    """Explicit bundle header create — POST-JOIN, Adda-anchored (GAP-5).

    Idempotent: same size → returns existing bundle (and updates bundle_number
    if newly provided). Doesn't create any items. `stream` is accepted for
    caller compatibility and ignored — a bundle spans every lane.

    Side effects:
      • Writes CuttingBundle (get_or_create per (adda, size), cutting_record NULL
        — the shipped conditional unique).
      • On first create: tracking.log_adda → AddaHistory (BUNDLE_CREATED).
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)

    if not ProductSize.objects.filter(pk=size_id, product=adda.product).exists():
        raise ValidationError(
            f"Size {size_id} not configured on product {adda.product.code}.",
        )

    bundle, created = CuttingBundle.objects.get_or_create(
        adda=adda, cutting_record=None, size_id=size_id,
        defaults={'total_pieces': 0, 'bundle_number': (bundle_number or '')[:40]},
    )
    if not created and bundle_number:
        new_num = bundle_number[:40]
        if bundle.bundle_number != new_num:
            bundle.bundle_number = new_num
            bundle.save(update_fields=['bundle_number', 'updated_at'])
    if created:
        from tracking.services import log_adda
        from tracking.models import AddaHistory
        log_adda(adda, AddaHistory.ChangeType.BUNDLE_CREATED, user,
                 metadata={'bundle_id': bundle.id, 'size_id': size_id})
    logger.info(
        "cutting.create_bundle adda=%s bundle=%s size_id=%s created=%s",
        adda.code, bundle.id, size_id, created,
    )
    return bundle


def _recompute_breakup_consumed(breakup: CuttingPieceBreakup) -> None:
    """Re-sum CuttingBundleItem.count for this breakup row + save."""
    total = sum(
        it.count for it in
        CuttingBundleItem.objects.filter(source_breakup=breakup)
    )
    if breakup.consumed_count != total:
        breakup.consumed_count = total
        breakup.save(update_fields=['consumed_count', 'updated_at'])


def _resync_group_consumed(adda: Adda, pattern_id: int, color_id: int) -> None:
    """GAP-5: when a bundle line has consumed from SEVERAL lanes' breakups
    (source_breakup=NULL), per-row attribution is gone — re-derive it at the
    GROUP grain: Σ consumed over the Adda's (pattern, colour) breakups must
    equal Σ item counts for that (pattern, colour) across the Adda's bundles.
    Distribution is deterministic oldest-lane-first (leftover truth is the
    group total; which physical row 'gave' a piece is not a business fact)."""
    from django.db.models import Q, Sum
    taken = (CuttingBundleItem.objects
             .filter(Q(bundle__adda=adda)
                     | Q(bundle__cutting_record__stage_record__adda=adda),
                     pattern_id=pattern_id, color_id=color_id)
             .aggregate(s=Sum('count'))['s'] or 0)
    rows = list(CuttingPieceBreakup.objects
                .select_for_update()
                .filter(cutting_record__stage_record__adda=adda,
                        pattern_id=pattern_id, color_id=color_id)
                .order_by('id'))
    remaining = taken
    for row in rows:
        give = min(row.count, remaining)
        remaining -= give
        if row.consumed_count != give:
            row.consumed_count = give
            row.save(update_fields=['consumed_count', 'updated_at'])


@transaction.atomic
def create_bundle_with_pieces(
    *, adda: Adda, size_id: int, bundle_number: str = '',
    selections: list[dict], user,
    stream=None) -> CuttingBundle:
    """One-shot atomic: create bundle header + consume pieces in one tx (PR12).

    selections = [{'breakup_id': int, 'take_count': int}, ...]

    Workflow:
      1. create_bundle(size, bundle_number) → header (idempotent per size)
      2. add_pieces_to_bundle(bundle, selections) → consume from inventory

    Empty selections OK — creates header alone. Allows "empty bundle" if
    user wants to populate later via per-bundle form.

    Returns the bundle (with `total_pieces` reflecting consumed items).
    """
    bundle = create_bundle(
        adda=adda, size_id=size_id,
        bundle_number=bundle_number, user=user,
    )
    # Only call add_pieces if there are non-zero selections — empty array
    # would trip add_pieces_to_bundle's "no valid selections" guard.
    valid = [
        s for s in (selections or [])
        if int(s.get('take_count') or 0) > 0
    ]
    if valid:
        add_pieces_to_bundle(
            adda=adda, bundle_id=bundle.id,
            selections=valid, user=user,
        )
        bundle.refresh_from_db()
    return bundle


@transaction.atomic
def bundle_ready_sets(*, adda: Adda, size_id: int, user) -> tuple:
    """GAP-5 one-tap slip: bundle every currently-COMPLETE unbundled garment
    set of one size — takes sets × pieces-per-garment from each mandatory
    component's breakups (oldest lane first), through the normal
    create_bundle + add_pieces writers (post-join gates apply). Returns
    (bundle, sets_bundled). Derive decides the number; the bundle row only
    records the act."""
    from production.services import pool_service
    needs = pool_service._mandatory_pattern_needs(adda)
    if not needs:
        raise ValidationError(
            "This product has a single component — bundle from the cutting "
            "rows directly.")
    rows = list(CuttingPieceBreakup.objects
                .select_for_update()
                .filter(cutting_record__stage_record__adda=adda,
                        size_id=size_id, pattern_id__in=needs)
                .order_by('id'))
    free = {}
    for b in rows:
        free[b.pattern_id] = free.get(b.pattern_id, 0) + (b.count - b.consumed_count)
    sets = min((free.get(pid, 0) // need for pid, need in needs.items()),
               default=0)
    if sets <= 0:
        raise ValidationError(
            "No complete unbundled garment sets for this size yet — check the "
            "readiness panel for the limiting component.")
    selections = []
    for pid, need in needs.items():
        take_left = sets * need
        for b in (r for r in rows if r.pattern_id == pid):
            take = min(take_left, b.count - b.consumed_count)
            if take > 0:
                selections.append({'breakup_id': b.pk, 'take_count': take})
                take_left -= take
            if take_left == 0:
                break
    bundle = create_bundle_with_pieces(
        adda=adda, size_id=size_id, selections=selections, user=user)
    return bundle, sets


@transaction.atomic
def add_pieces_to_bundle(
    *, adda: Adda, bundle_id: int,
    selections: list[dict], user,
    stream=None) -> list[CuttingBundleItem]:
    """Multi-select consumption flow (PR10).

    selections = [{'breakup_id': int, 'take_count': int}, ...]

    For each selection:
      • lock breakup row
      • validate take_count <= available_count (count - consumed_count)
      • create CuttingBundleItem(bundle, breakup.pattern, breakup.color,
          count, source_breakup=breakup)
        - if same (bundle, pattern, color, source_breakup) exists, increment.
      • increment breakup.consumed_count

    Atomic — any over-take rejects the whole batch.

    Side effects:
      • Writes CuttingBundleItem rows (get_or_create / count increment).
      • Updates CuttingPieceBreakup.consumed_count (locked rows).
      • Recomputes + writes CuttingBundle.total_pieces.
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)
    bundle = _get_bundle_for_adda(adda, bundle_id)

    created_items: list[CuttingBundleItem] = []
    breakup_to_recompute: set[int] = set()

    for sel in selections or []:
        try:
            breakup_id = int(sel.get('breakup_id') or 0)
            take_count = int(sel.get('take_count') or 0)
        except (TypeError, ValueError):
            raise ValidationError("Invalid selection payload.")
        if take_count <= 0:
            continue
        try:
            # GAP-5: breakups from EVERY lane of this Adda — a bundle spans
            # the streams (complete-product container).
            breakup = (
                CuttingPieceBreakup.objects
                .select_for_update()
                .get(pk=breakup_id, cutting_record__stage_record__adda=adda)
            )
        except CuttingPieceBreakup.DoesNotExist:
            raise ValidationError(
                f"Cutting piece row {breakup_id} not found for this Adda.",
            )
        available = breakup.count - breakup.consumed_count
        if take_count > available:
            raise ValidationError(
                f"{breakup.pattern.name}/{breakup.color.name}: only {available} "
                f"available, cannot take {take_count}.",
            )
        # GAP-5: the DB truth is unique (bundle, pattern, color) — cross-LANE
        # takes of the same component INCREMENT one line. `source_breakup`
        # stays only while a line has a single source; a second source blanks
        # it (provenance lives on each breakup row's consumed_count).
        item, item_created = CuttingBundleItem.objects.get_or_create(
            bundle=bundle, pattern=breakup.pattern, color=breakup.color,
            defaults={'count': take_count, 'source_breakup': breakup},
        )
        if not item_created:
            item.count = item.count + take_count
            update = ['count', 'updated_at']
            if item.source_breakup_id and item.source_breakup_id != breakup.pk:
                item.source_breakup = None
                update.append('source_breakup')
            item.save(update_fields=update)
        breakup.consumed_count = breakup.consumed_count + take_count
        breakup.save(update_fields=['consumed_count', 'updated_at'])
        created_items.append(item)
        breakup_to_recompute.add(breakup.id)

    if not created_items:
        raise ValidationError("No valid selections (all take counts were zero).")

    _recompute_bundle_total(bundle)
    logger.info(
        "cutting.add_pieces_to_bundle adda=%s bundle=%s items=%s "
        "breakups_touched=%s bundle_total=%s",
        adda.code, bundle.id, len(created_items),
        len(breakup_to_recompute), bundle.total_pieces,
    )
    return created_items


@transaction.atomic
def add_item_to_bundle(
    *, adda: Adda, bundle_id: int, pattern_id: int, color_id: int,
    count: int, user,
    stream=None) -> CuttingBundleItem:
    """Add or update one item inside an existing bundle (size scoped via FK).

    Idempotent: same (bundle, pattern, color) → count UPDATE.
    Validates bundle belongs to this adda's cutting record.

    Side effects:
      • Writes CuttingBundleItem (update_or_create).
      • If item sourced from a breakup: recomputes CuttingPieceBreakup.consumed_count.
      • Recomputes + writes CuttingBundle.total_pieces.
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)
    if count < 1:
        raise ValidationError("Item count must be >= 1.")
    bundle = _get_bundle_for_adda(adda, bundle_id)

    if not ProductPatternAssignment.objects.filter(
        pattern_id=pattern_id, product=adda.product,
    ).exists():
        raise ValidationError(
            f"Pattern not assigned to product {adda.product.code}.",
        )

    item, _ = CuttingBundleItem.objects.update_or_create(
        bundle=bundle, pattern_id=pattern_id, color_id=color_id,
        defaults={'count': count},
    )
    # Consumed-count sync: single-source lines re-sum their breakup; multi-
    # source (source NULL) lines re-derive the whole (pattern,colour) group —
    # GAP-5, see _resync_group_consumed. Pure-manual worlds (no breakups) no-op.
    if item.source_breakup_id is not None:
        _recompute_breakup_consumed(item.source_breakup)
    elif CuttingPieceBreakup.objects.filter(
            cutting_record__stage_record__adda=adda,
            pattern_id=pattern_id, color_id=color_id).exists():
        _resync_group_consumed(adda, pattern_id, color_id)
    _recompute_bundle_total(bundle)
    logger.info(
        "cutting.add_item_to_bundle adda=%s bundle=%s item=%s pattern_id=%s "
        "color_id=%s count=%s bundle_total=%s",
        adda.code, bundle.id, item.id, pattern_id, color_id, count,
        bundle.total_pieces,
    )
    return item


@transaction.atomic
def add_bundle_item(
    *, adda: Adda, size_id: int, pattern_id: int, color_id: int,
    count: int, bundle_number: str = '', user,
    stream=None) -> CuttingBundleItem:
    """Add or update one bundle line item (pattern × color × count).

    Bundle (per-size header) lazy-created on first item for that size.
    bundle_number, if passed, updates the bundle's label (last write wins).
    Same (bundle, pattern, color) duplicate → count UPDATE.

    Side effects:
      • Lazy-creates AddaStageRecord + CuttingRecord if missing.
      • Writes CuttingBundle (get_or_create per (cutting_record, size)).
      • Writes CuttingBundleItem (update_or_create).
      • On bundle create: calls tracking.log_adda → AddaHistory (BUNDLE_CREATED).
      • If item sourced from a breakup: recomputes CuttingPieceBreakup.consumed_count.
      • Recomputes + writes CuttingBundle.total_pieces.
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)
    if count < 1:
        raise ValidationError("Item count must be >= 1.")

    if not ProductSize.objects.filter(pk=size_id, product=adda.product).exists():
        raise ValidationError(
            f"Size {size_id} not configured on product {adda.product.code}.",
        )
    if not ProductPatternAssignment.objects.filter(
        pattern_id=pattern_id, product=adda.product,
    ).exists():
        raise ValidationError(
            f"Pattern not assigned to product {adda.product.code}.",
        )

    bundle, bundle_created = CuttingBundle.objects.get_or_create(
        adda=adda, cutting_record=None, size_id=size_id,
        defaults={'total_pieces': 0, 'bundle_number': (bundle_number or '')[:40]},
    )
    if bundle_created:
        # Log BUNDLE_CREATED on the lazy-create path too (parity with
        # create_bundle) so the Adda timeline never misses a bundle event.
        from tracking.services import log_adda
        from tracking.models import AddaHistory
        log_adda(adda, AddaHistory.ChangeType.BUNDLE_CREATED, user,
                 metadata={'bundle_id': bundle.id, 'size_id': size_id})
    if bundle_number and bundle.bundle_number != bundle_number[:40]:
        bundle.bundle_number = bundle_number[:40]
        bundle.save(update_fields=['bundle_number', 'updated_at'])

    item, _ = CuttingBundleItem.objects.update_or_create(
        bundle=bundle, pattern_id=pattern_id, color_id=color_id,
        defaults={'count': count},
    )
    # Consumed-count sync — same GAP-5 rule as add_item_to_bundle.
    if item.source_breakup_id is not None:
        _recompute_breakup_consumed(item.source_breakup)
    elif CuttingPieceBreakup.objects.filter(
            cutting_record__stage_record__adda=adda,
            pattern_id=pattern_id, color_id=color_id).exists():
        _resync_group_consumed(adda, pattern_id, color_id)
    _recompute_bundle_total(bundle)
    logger.info(
        "cutting.add_bundle_item adda=%s bundle=%s item=%s size_id=%s "
        "pattern_id=%s color_id=%s count=%s bundle_total=%s",
        adda.code, bundle.id, item.id, size_id, pattern_id, color_id, count,
        bundle.total_pieces,
    )
    return item


@transaction.atomic
def delete_bundle_item(*, adda: Adda, item_id: int, user, stream=None) -> None:
    """Remove one line item. Restores consumed_count on source breakup row.
    Auto-deletes parent bundle if empty.

    Side effects:
      • Deletes CuttingBundleItem row.
      • If sourced from a breakup: recomputes CuttingPieceBreakup.consumed_count.
      • Recomputes CuttingBundle.total_pieces; deletes the bundle if now empty.
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)
    from django.db.models import Q
    item = CuttingBundleItem.objects.filter(
        Q(bundle__adda=adda)
        | Q(bundle__cutting_record__stage_record__adda=adda),
        pk=item_id,
    ).select_related('bundle', 'source_breakup').first()
    if item is None:
        return
    # A worker allocation (StageWorkAssignment, expense app) PROTECTs this item,
    # and those rows are immutable (never hard-deleted — voiding only flags them),
    # so ANY allocation history blocks deletion. Raw delete would 500 with
    # ProtectedError; refuse with a clear msg instead. Void an active allocation
    # to reverse the pay; the audit row (and so this item) stays for the record.
    if item.work_assignments.exists():
        raise ValidationError(
            "This item has worker allocation records and can't be deleted "
            "(its pay audit trail is permanent). Void any active allocation "
            "to reverse the pay; the row stays for the record.")
    bundle = item.bundle
    source = item.source_breakup
    pattern_id, color_id = item.pattern_id, item.color_id
    item.delete()
    if source is not None:
        _recompute_breakup_consumed(source)
    elif CuttingPieceBreakup.objects.filter(
            cutting_record__stage_record__adda=adda,
            pattern_id=pattern_id, color_id=color_id).exists():
        _resync_group_consumed(adda, pattern_id, color_id)   # multi-source line
    _recompute_bundle_total(bundle)
    bundle_deleted = bundle.total_pieces == 0
    if bundle_deleted:
        bundle.delete()
    logger.info(
        "cutting.delete_bundle_item adda=%s bundle=%s item=%s "
        "bundle_deleted=%s",
        adda.code, bundle.id, item_id, bundle_deleted,
    )


@transaction.atomic
def delete_bundle(*, adda: Adda, bundle_id: int, user, stream=None) -> None:
    """Remove entire bundle. Restores consumed_count on all source breakup rows.

    Side effects:
      • Deletes CuttingBundle (cascades its CuttingBundleItem rows).
      • Recomputes CuttingPieceBreakup.consumed_count for each source breakup.
    """
    _ensure_cutting_skill(user)
    _ensure_bundling_open(adda)
    from django.db.models import Q
    bundle = CuttingBundle.objects.filter(
        Q(adda=adda) | Q(cutting_record__stage_record__adda=adda),
        pk=bundle_id,
    ).first()
    if bundle is None:
        return
    # Any item in this bundle that carries worker-allocation history PROTECTs the
    # cascade (immutable audit rows) — refuse with a clear msg instead of a 500
    # ProtectedError.
    if CuttingBundleItem.objects.filter(
        bundle=bundle, work_assignments__isnull=False,
    ).exists():
        raise ValidationError(
            "This bundle has items with worker allocation records and can't be "
            "deleted (the pay audit trail is permanent).")
    # Collect attribution BEFORE delete (cascade drops the items): single-
    # source rows re-sum directly; multi-source lines (source NULL) re-derive
    # their (pattern, colour) group after the delete (GAP-5).
    source_ids = set(
        bundle.items.exclude(source_breakup__isnull=True)
        .values_list('source_breakup_id', flat=True)
    )
    group_keys = set(
        bundle.items.filter(source_breakup__isnull=True)
        .values_list('pattern_id', 'color_id')
    )
    bundle.delete()
    for sb in CuttingPieceBreakup.objects.filter(pk__in=source_ids):
        _recompute_breakup_consumed(sb)
    for pattern_id, color_id in group_keys:
        if CuttingPieceBreakup.objects.filter(
                cutting_record__stage_record__adda=adda,
                pattern_id=pattern_id, color_id=color_id).exists():
            _resync_group_consumed(adda, pattern_id, color_id)
    logger.info(
        "cutting.delete_bundle adda=%s bundle=%s source_breakups_recomputed=%s",
        adda.code, bundle_id, len(source_ids),
    )


@transaction.atomic
def upsert_breakup_row(
    *, adda: Adda, size_id: int, color_id: int, pattern_id: int,
    count: int, roll_id: int | None = None, user,
    stream=None) -> CuttingPieceBreakup:
    """Ek breakup row save/update (size, color, pattern) ke combination ke liye.

    Idempotent: same combo pe phir se call karo to row update (count + roll
    overwrite). count == 0 → delete row (helper convenience).
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda, stream=stream)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — breakup locked.")
    if count < 0:
        raise ValidationError("Piece count must be >= 0.")

    # Validate cross-product (size + pattern belong to this product).
    if not ProductSize.objects.filter(pk=size_id, product=adda.product).exists():
        raise ValidationError(
            f"Size {size_id} not configured on product {adda.product.code}.",
        )
    pattern_assignment = ProductPatternAssignment.objects.filter(
        pattern_id=pattern_id, product=adda.product,
    ).first()
    if pattern_assignment is None:
        raise ValidationError(
            f"Pattern not assigned to product {adda.product.code}.",
        )

    cr = _get_or_create_cutting_record(adda, stream=stream)

    if count == 0:
        # Convenience: count=0 → delete the row entirely.
        CuttingPieceBreakup.objects.filter(
            cutting_record=cr, size_id=size_id, color_id=color_id,
            pattern_id=pattern_id,
        ).delete()
        return None  # signal removal

    obj, created = CuttingPieceBreakup.objects.update_or_create(
        cutting_record=cr,
        size_id=size_id, color_id=color_id, pattern_id=pattern_id,
        defaults={'count': count, 'roll_id': roll_id},
    )
    return obj


@transaction.atomic
def delete_breakup_row(*, adda: Adda, breakup_id: int, user, stream=None) -> None:
    """Ek breakup row hatao."""
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda, stream=stream)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — breakup locked.")
    CuttingPieceBreakup.objects.filter(
        pk=breakup_id, cutting_record__stage_record=sr,
    ).delete()


@transaction.atomic
def save_cutting_draft(
    *, adda: Adda, notes: str | None = None, user,
    stream=None) -> CuttingRecord:
    """Notes save + ensure CuttingRecord exists. No advance, no validation."""
    _ensure_cutting_skill(user)
    cr = _get_or_create_cutting_record(adda, stream=stream)
    sr = cr.stage_record
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    if notes is not None:
        cr.notes = notes
        cr.save(update_fields=['notes', 'updated_at'])
    return cr


def complete_cutting(
    *, adda: Adda, user,
    pieces_cut: int | None = None,
    worker_ids: Iterable[int] | None = None,
    notes: str | None = None,
) -> CuttingRecord:
    """Back-compat DISPATCHER — prefer the two explicit entry points below.

    Kept so existing callers (mostly tests) keep working, but NEW code should
    call the named function for the path it means, so the permission gate +
    validation regime are obvious at the call site (no sentinel-overload):
      • `complete_cutting_legacy(...)`       — pieces_cut given; MANAGEMENT gate;
                                               single-shot (NIKKAR-style / tests).
      • `complete_cutting_from_bundles(...)` — pieces_cut=None; HELPER-SKILL gate;
                                               validates pre-saved bundle rows.
    Each path function owns its own @transaction.atomic.
    """
    if pieces_cut is not None:
        return complete_cutting_legacy(
            adda=adda, pieces_cut=pieces_cut,
            worker_ids=worker_ids or [], notes=notes or '', user=user,
        )
    return complete_cutting_from_bundles(adda=adda, user=user)


@transaction.atomic
def complete_cutting_legacy(
    *, adda: Adda, pieces_cut: int, worker_ids: list[int], notes: str, user,
) -> CuttingRecord:
    """Legacy single-shot completion (pieces_cut given) — NIKKAR-style products
    with a simple flow + the test fixtures. MANAGEMENT-role gated. Public so the
    legacy CuttingCompleteView calls it explicitly (was `_complete_cutting_legacy`).

    Side effects:
      • Writes AddaStageRecord (created complete) + its workers M2M.
      • Writes CuttingRecord (pieces_cut, notes).
      • _materialize_breakdown → writes AddaProductSizeColorPieceBreakdown rows.
      • If product has no barcode_generation stage: calls
        tracking.generate_for_cutting → writes BarcodeBatch / barcode rows.
      • advance_to_next_stage → mutates Adda.current_stage/status, may freeze
        stage cost + write AddaHistory (cross-app: tracking + cost_service).
    """
    # Worker-cert fix (V1.1, 2026-07-12): docstring said MANAGEMENT but the
    # helper was `_ensure_can_manage` = PRODUCTION roles — any worker could
    # complete Cutting (advance + barcodes + cost freeze). Same naming trap
    # the M3 campaign fixed on AddaCreateView.
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can complete the cutting stage (legacy path)")
    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_CUTTING:
        raise ValidationError("Adda is not at Cutting stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if pieces_cut < 1:
        raise ValidationError("pieces_cut must be >= 1")

    # PA-09-1: this single-form path CREATEs the AddaStageRecord unconditionally.
    # But (adda, workflow_stage) is unique_together, and the SR may ALREADY exist —
    # start_cutting / any bundle-or-breakup op lazy-creates it, and reopen_cutting
    # keeps it. A second create → IntegrityError, which CuttingCompleteView's
    # `except (ValidationError, PermissionDenied)` does not catch → 500. Refuse
    # gracefully and point at the workspace (the path that handles an existing SR).
    if AddaStageRecord.objects.filter(adda=adda, workflow_stage=stage).exists():
        raise ValidationError(
            "Cutting has already been started for this Adda — complete it from the "
            "cutting workspace (or reopen and re-complete there). The single-form "
            "completion is only for a fresh cutting stage.")

    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=stage,
        started_at=timezone.now(),
        completed_at=timezone.now(), completed_by=user,
    )
    # S2: freeze the payable-rate snapshot at stage creation (addendum M-5/D-α).
    from production.services.stage_rate_service import ensure_stage_role_rates
    ensure_stage_role_rates(sr)
    from production.services.worker_task_service import set_stage_workers
    set_stage_workers(sr, worker_ids or [])   # dual-write (legacy complete: tasks seed 'completed')

    cr = CuttingRecord.objects.create(
        stage_record=sr, pieces_cut=pieces_cut, notes=notes,
    )

    # PR-B 2026-05-29: materialize breakdown even on legacy path (single
    # NULL-NULL row with verified_piece_count = pieces_cut). Future stages
    # see consistent shape regardless of which path produced data.
    _materialize_breakdown(cr, user)

    # Same back-compat branch as workspace path — products without
    # barcode_generation stage in workflow get inline barcode generation.
    inline_barcodes = not _product_has_barcode_gen_stage(adda)
    if inline_barcodes:
        from production.stages.barcode_generation.assembly import generate_for_cutting
        generate_for_cutting(cr)

    # Legacy compatibility path opts OUT of PAY-2 worker-credit enforcement
    # (decision: legacy flows are not part of the new payroll architecture).
    advance_to_next_stage(adda, user, enforce_worker_credit=False)
    logger.info(
        "cutting.complete path=legacy adda=%s cutting_record=%s pieces_cut=%s "
        "worker_count=%s inline_barcodes=%s",
        adda.code, cr.id, pieces_cut, len(worker_ids or []), inline_barcodes,
    )
    return cr


@transaction.atomic
def complete_cutting_from_bundles(*, adda: Adda, user,
                                  override_pending_reason: str | None = None,
                                  stream=None) -> CuttingRecord:
    """Workspace-path completion (pieces_cut=None). HELPER-SKILL gated. Public so
    CuttingWorkspaceCompleteView calls it explicitly (was
    `_complete_cutting_from_breakup`). Actual CuttingBundle rows drive validation
    + barcode generation; CuttingPieceBreakup is informational (verified plan only).

    Side effects (biggest fan-out in the codebase — completes + advances Cutting):
      • Updates CuttingRecord.pieces_cut (denormalized total from bundle items).
      • Stamps AddaStageRecord.completed_at / completed_by (state transition).
      • _materialize_breakdown → writes AddaProductSizeColorPieceBreakdown rows.
      • If product has no barcode_generation stage: calls cross-app
        tracking.generate_for_cutting → writes BarcodeBatch + barcode rows.
      • advance_to_next_stage → mutates Adda.current_stage/status, freezes the
        stage's processing cost (cost_service, money write) and writes
        AddaHistory via tracking (cross-app). Next stage's AddaStageRecord may
        be lazy-created downstream.
    """
    _ensure_can_complete_cutting(user)

    wf = _cutting_workflow_stage(adda)
    if wf is None:
        raise ValidationError("Product does not include the cutting stage.")
    from production.services.adda_service import (
        lane_stage_record, resolve_stream)
    lane = resolve_stream(adda, stream)

    # WF-4: lock the stage row so a concurrent completer blocks here and then
    # sees completed_at set below — prevents double-advance / double-freeze.
    sr = lane_stage_record(adda, wf, lane, for_update=True)
    if sr is None:
        raise ValidationError("Stage not started — assign workers first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    cr = getattr(sr, 'cutting', None)
    if cr is None:
        raise ValidationError("No cutting record yet — enter cut pieces first.")

    # Streams redesign: the LANE's actual = its CuttingPieceBreakup rows
    # (owner's Cutting spec: expected vs actual vs pending, per size×color×
    # pattern). Bundles moved POST-JOIN (complete-product containers).
    # Back-compat: lanes that entered actuals as bundles keep working.
    breakup_rows = list(cr.breakup.select_related('size', 'pattern', 'color'))
    items = [
        type('Row', (), {
            'count': b.count, 'pattern': b.pattern, 'pattern_id': b.pattern_id,
            'color': b.color, 'color_id': b.color_id,
            'bundle': type('B', (), {'size': b.size, 'size_id': b.size_id})(),
        })() for b in breakup_rows
    ]
    if not items:
        items = list(
            CuttingBundleItem.objects
            .filter(bundle__cutting_record=cr)
            .select_related('bundle__size', 'pattern', 'color')
        )
    if not items:
        raise ValidationError("Enter at least one cut piece row.")
    total = sum(it.count for it in items)
    if total <= 0:
        raise ValidationError("Total piece count must be > 0.")

    # Pattern stage allocations (if pattern stage in workflow).
    # GAP-2: the LANE's pattern record — a sibling lane's size allocations must
    # never validate (or block) this lane's completion.
    pattern_record = _pattern_record_for_adda(adda, stream=lane)
    if pattern_record is not None:
        allowed_size_ids = set(
            pattern_record.size_allocations.values_list('size_id', flat=True)
        )
        if allowed_size_ids:
            for it in items:
                if it.bundle.size_id not in allowed_size_ids:
                    raise ValidationError(
                        f"Size {it.bundle.size.code} not in pattern stage's batch sizes."
                    )

    # Every item.pattern must be assigned to this product.
    allowed_pattern_ids = set(
        adda.product.pattern_assignments.values_list('pattern_id', flat=True)
    )
    if allowed_pattern_ids:
        for it in items:
            if it.pattern_id not in allowed_pattern_ids:
                raise ValidationError(
                    f"Pattern {it.pattern.name} not assigned to product {adda.product.code}.",
                )

    # Color must be in layering rolls_used colors (if layering record exists).
    # GAP-2 (found live: NKS panel/grey refused against body/navy rolls): the
    # LANE's layering — cross-fabric lanes each carry their own roll colors.
    layering_record = _get_layering_record_for_adda(adda, stream=lane)
    if layering_record is not None:
        layered_color_ids = set(
            layering_record.rolls_used.values_list('cloth_color_id', flat=True)
        )
        if layered_color_ids:
            for it in items:
                if it.color_id not in layered_color_ids:
                    raise ValidationError(
                        f"Color id={it.color_id} not in layered rolls.",
                    )

    # ── M6 ENFORCEMENT GATES (flags default OFF — deploy → soak →
    # owner flips; MANUFACTURING_INTEGRATION_REVIEW §4). ERP-side
    # checks over provider-dict DATA; no new boundary crossing. ──
    from django.conf import settings as _settings
    if getattr(_settings, 'REQUIRE_APPROVED_LAYOUT', False):
        from production.stages.cutting_pattern import handler as _cp
        panel = None
        if _cp.LAYOUT_PROVIDER is not None:
            try:
                panel = _cp.LAYOUT_PROVIDER(adda)
            except Exception:
                logger.exception('layout provider failed during the '
                                 'REQUIRE_APPROVED_LAYOUT gate')
        if not (panel and panel.get('has_usage')):
            raise ValidationError(
                'REQUIRE_APPROVED_LAYOUT is on: this Adda has no active '
                'approved-layout contract — choose one on its '
                'Manufacturing Layouts page before completing cutting.')
    if getattr(_settings, 'ENFORCE_LAYOUT_RECONCILIATION', False):
        recon = layout_reconciliation(adda)
        tol = int(getattr(_settings, 'LAYOUT_RECONCILIATION_TOLERANCE', 0))
        if recon:
            hard = [m for m in recon['mismatches']
                    if abs(m['actual'] - m['expected']) > tol]
            if hard:
                lines = '; '.join(
                    f"size {m['label']}: expected {m['expected']} "
                    f"(marker × plies), cut {m['actual']}"
                    for m in hard)
                raise ValidationError(
                    'ENFORCE_LAYOUT_RECONCILIATION is on: the cut '
                    f'numbers differ from the approved layout ({lines}; '
                    f'tolerance {tol}). Correct the bundles or the '
                    'layout choice.')

    # Validation passed — denormalize total + stamp completion + materialize
    # the verified breakdown. Atomic within this @transaction.atomic.
    cr.pieces_cut = total
    cr.save(update_fields=['pieces_cut', 'updated_at'])
    sr.completed_at = timezone.now()
    sr.completed_by = user
    sr.save(update_fields=['completed_at', 'completed_by', 'updated_at'])

    # PR-B 2026-05-29: Cutting Stage materialises the verified breakdown.
    # Barcode generation no longer inline — it's a downstream stage.
    _materialize_breakdown(cr, user)

    # BACK-COMPAT: agar product workflow mein barcode_generation stage NHI
    # hai (legacy NIKKAR-style products), to barcodes yahin inline generate
    # ho jaate hain. Naye products jo bg stage include karte hain wo apne
    # barcode_generation stage par generate karenge.
    # R3: C3 guard + override live at the funnel (passthrough only).
    # Streams: the LANE finished its cut; the funnel fires the JOIN when
    # every blocking lane is done.
    from production.services.adda_service import (
        PRE_PRODUCTION_STAGE_CODES, advance_lane)
    advance_lane(adda, stream=lane, leaving_sr=sr, user=user,
                 override_pending_reason=override_pending_reason)
    adda.refresh_from_db(fields=['current_stage', 'status'])
    joined = (adda.current_stage is None
              or adda.current_stage.stage.code
              not in PRE_PRODUCTION_STAGE_CODES)

    # BACK-COMPAT: products without a barcode_generation stage generate
    # inline — but only AT THE JOIN (the complete product exists now),
    # covering every lane's cutting record.
    inline_barcodes = False
    if joined:
        from django.core.exceptions import ValidationError as _VE
        from tracking.models import BarcodeBatch as _BB
        from production.stages.barcode_generation.assembly import (
            append_uncovered_batches, generate_for_adda)
        if _BB.objects.filter(adda=adda).exists():
            # a LATE lane after identities exist: append its pieces
            # (identity law — sequences continue at Max+1). Zero deficit
            # (normal first-join with a barcode stage) = silent no-op.
            try:
                appended, lane_notes = append_uncovered_batches(adda)
            except _VE:
                appended, lane_notes = 0, []
            if appended:
                from tracking.services import log_adda as _log
                from tracking.models import AddaHistory as _AH
                _log(adda, _AH.ChangeType.BARCODES_GENERATED, user,
                     metadata={'appended': appended,
                               'lanes': lane_notes})
                # keep the barcode stage's own record honest (display)
                from production.models import BarcodeGenerationRecord
                rec = BarcodeGenerationRecord.objects.filter(
                    stage_record__adda=adda).first()
                if rec is not None:
                    rec.total_barcodes += appended
                    rec.save(update_fields=['total_barcodes',
                                            'updated_at'])
                inline_barcodes = True
        elif not _product_has_barcode_gen_stage(adda):
            generated = generate_for_adda(adda)
            # GAP-5 audit parity (final audit observability note): the INITIAL
            # join generation now logs the same event the append path does —
            # the history reconstructs both naming moments without ambiguity.
            from tracking.services import log_adda as _log
            from tracking.models import AddaHistory as _AH
            from production.models import CuttingStream as _CS
            _log(adda, _AH.ChangeType.BARCODES_GENERATED, user,
                 metadata={'generated': generated,
                           'lanes': [s.label for s in _CS.objects.filter(
                               adda=adda, cancelled_at__isnull=True)]})
            inline_barcodes = True

    # M6: completion listeners — traceability hooks (e.g. the layout-
    # usage stamp), each isolated so cutting NEVER fails on them.
    for listener in CUTTING_COMPLETE_LISTENERS:
        try:
            listener(adda, sr)
        except Exception:
            logger.exception('cutting completion listener %r failed '
                             '(completion unaffected)', listener)
    logger.info(
        "cutting.complete path=workspace adda=%s cutting_record=%s "
        "stage_record=%s pieces_cut=%s item_count=%s inline_barcodes=%s",
        adda.code, cr.id, sr.id, total, len(items), inline_barcodes,
    )
    return cr


@transaction.atomic
def reopen_cutting(*, adda: Adda, user) -> AddaStageRecord:
    """Admin-only: completed Cutting stage ko unlock for correction.

    Refusal conditions (PR-B 2026-05-29 extended):
      1. Any BatchBarcode row exists (lazy-created on scan → scan happened).
      2. Downstream `barcode_generation` stage has been started or completed
         (would corrupt downstream state on partial rollback).
      3. Any BarcodeExportBatch has been created for this Adda (vendor
         already has exported labels — rollback would orphan them).

    On reopen:
      • Delete AddaProductSizeColorPieceBreakdown rows (re-materialised on
        re-complete).
      • Delete BarcodeBatch rows (one-shot regeneration rule).
      • Clear sr.completed_at + completed_by.
      • Adda.current_stage → cutting wf, status → IN_PROGRESS.
      • AddaHistory.STAGE_REOPENED entry.

    Side effects:
      • Deletes AddaProductSizeColorPieceBreakdown + BarcodeBatch rows.
      • Clears AddaStageRecord.completed_at / completed_by (state transition).
      • cost_service.clear_stage_cost → unfreezes the stage's processing cost
        (money write, cross-app).
      • Mutates Adda.current_stage / status / completed_at.
      • tracking.log_adda → writes AddaHistory (STAGE_REOPENED).
    """
    def _guard(adda, sr, wf):
        from tracking.models import BatchBarcode, BarcodeExportBatch
        # 1: any scanned piece blocks reopen.
        if BatchBarcode.objects.filter(adda=adda).exists():
            raise ValidationError(
                "Cannot reopen — at least one barcode has been scanned in production."
            )
        # 2: downstream barcode_generation started/completed blocks (partial
        #    rollback would corrupt downstream state).
        bg_wf = adda.product.workflow_stages.filter(
            stage__code=STAGE_BARCODE_GENERATION,
        ).first()
        if bg_wf is not None and AddaStageRecord.objects.filter(
            adda=adda, workflow_stage=bg_wf,
        ).exclude(started_at__isnull=True).exists():
            raise ValidationError(
                "Cannot reopen — Barcode Generation stage has already been "
                "started. Reopen Barcode Generation first."
            )
        # 3: any export blocks reopen — vendor may have printed labels.
        if BarcodeExportBatch.objects.filter(adda=adda).exists():
            raise ValidationError(
                "Cannot reopen — barcode exports exist. Cancel exports first."
            )

    def _teardown(sr):
        # Delete the materialised breakdown (re-made on re-complete) + all
        # BarcodeBatch rows (one-shot regeneration rule).
        from tracking.models import BarcodeBatch
        AddaProductSizeColorPieceBreakdown.objects.filter(
            cutting_record=sr.cutting,
        ).delete()
        BarcodeBatch.objects.filter(adda=sr.adda).delete()
        return []

    return reopen_stage_record(
        adda=adda, stage_code=STAGE_CUTTING, stage_label='Cutting',
        user=user, guard=_guard, teardown=_teardown,
    )
