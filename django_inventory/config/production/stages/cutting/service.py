"""Cutting stage service — full lifecycle (PR3 2026-05-28).

PRODUCTION FLOW MEIN POSITION:
  Layering → (Cutting Pattern) → Cutting

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
    STAGE_BARCODE_GENERATION, STAGE_CUTTING, STAGE_CUTTING_PATTERN,
)
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingBundle,
    CuttingBundleItem, CuttingPatternRecord, CuttingPieceBreakup,
    CuttingRecord, ProductPatternAssignment, ProductSize,
    WorkflowStage,
)
from production.services.adda_service import advance_to_next_stage

from production.services._shared import _ensure_can_manage, reopen_stage_record

# Module logger — debug fan-out of multi-table / cross-app cutting writes.
logger = logging.getLogger(__name__)


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


def _pattern_record_for_adda(adda: Adda) -> CuttingPatternRecord | None:
    """Pattern stage ka CuttingPatternRecord (if pattern stage in workflow + completed)."""
    pattern_wf = adda.product.workflow_stages.filter(
        stage__code=STAGE_CUTTING_PATTERN,
    ).first()
    if pattern_wf is None:
        return None
    sr = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage=pattern_wf,
    ).first()
    if sr is None:
        return None
    return getattr(sr, 'cutting_pattern', None)


def _get_or_create_cutting_stage_record(adda: Adda) -> AddaStageRecord:
    """Lazy-create AddaStageRecord for cutting stage.

    Pre-condition: Adda abhi cutting stage pe ho.
    """
    wf = _cutting_workflow_stage(adda)
    if wf is None:
        raise ValidationError("This product does not include the cutting stage.")
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not currently at the cutting stage.")
    sr, created = AddaStageRecord.objects.get_or_create(
        adda=adda, workflow_stage=wf,
        defaults={'started_at': timezone.now()},
    )
    if created and not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    return sr


def _get_or_create_cutting_record(adda: Adda) -> CuttingRecord:
    """CuttingRecord lazy-create — pieces_cut default 0 jab tak complete."""
    sr = _get_or_create_cutting_stage_record(adda)
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


def get_cutting_snapshot(adda: Adda) -> dict:
    """Lightweight snapshot — drives cutting workspace state.

    Mirrors get_layering_snapshot / get_pattern_snapshot shape.
    """
    wf = _cutting_workflow_stage(adda)
    if wf is None:
        return {'state': 'absent'}
    sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()
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

    pattern_record = _pattern_record_for_adda(adda)
    if pattern_record is None:
        return []
    allocations = list(pattern_record.size_allocations.select_related('size').all())
    if not allocations:
        return []

    # Distinct colors from layering rolls_used (frozen at layering complete).
    # `set()` ensures uniqueness regardless of M2M JOIN duplicates.
    colors = sorted(set(
        layering_record.rolls_used.values_list('cloth_color_id', flat=True)
    ))
    if not colors:
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


def _get_layering_record_for_adda(adda: Adda):
    """Layering stage ka typed record (None agar layering nahi hua)."""
    layering_wf = adda.product.workflow_stages.filter(stage__code='layering').first()
    if layering_wf is None:
        return None
    sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=layering_wf).first()
    if sr is None:
        return None
    return getattr(sr, 'layering', None)


# ── Write services ─────────────────────────────────────────────────────────

@transaction.atomic
def start_cutting(*, adda: Adda, worker_ids: Iterable[int], user) -> AddaStageRecord:
    """Manager workers assign karta hai → stage formally start.

    Side effects:
      • Writes AddaStageRecord (lazy get_or_create) + its workers M2M.
      • Calls tracking.log_adda → writes AddaHistory (WORKERS_ASSIGNED).
    """
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can start the cutting stage")
    sr = _get_or_create_cutting_stage_record(adda)
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
def create_bundle(
    *, adda: Adda, size_id: int, bundle_number: str = '', user,
) -> CuttingBundle:
    """Explicit bundle header create (PR9 two-step flow).

    Idempotent: same size → returns existing bundle (and updates bundle_number
    if newly provided). Doesn't create any items.

    Side effects:
      • Writes CuttingBundle (get_or_create per (cutting_record, size)).
      • Lazy-creates AddaStageRecord + CuttingRecord if missing.
      • On first create: calls tracking.log_adda → AddaHistory (BUNDLE_CREATED).
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")

    if not ProductSize.objects.filter(pk=size_id, product=adda.product).exists():
        raise ValidationError(
            f"Size {size_id} not configured on product {adda.product.code}.",
        )

    cr = _get_or_create_cutting_record(adda)
    bundle, created = CuttingBundle.objects.get_or_create(
        cutting_record=cr, size_id=size_id,
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
                 stage_record=sr, metadata={'bundle_id': bundle.id, 'size_id': size_id})
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


@transaction.atomic
def create_bundle_with_pieces(
    *, adda: Adda, size_id: int, bundle_number: str = '',
    selections: list[dict], user,
) -> CuttingBundle:
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
def add_pieces_to_bundle(
    *, adda: Adda, bundle_id: int,
    selections: list[dict], user,
) -> list[CuttingBundleItem]:
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
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")

    try:
        bundle = CuttingBundle.objects.select_related('size').get(
            pk=bundle_id, cutting_record__stage_record=sr,
        )
    except CuttingBundle.DoesNotExist:
        raise ValidationError("Bundle does not belong to this Adda.")

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
            breakup = (
                CuttingPieceBreakup.objects
                .select_for_update()
                .get(pk=breakup_id, cutting_record__stage_record=sr)
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
        item, item_created = CuttingBundleItem.objects.get_or_create(
            bundle=bundle, pattern=breakup.pattern, color=breakup.color,
            source_breakup=breakup,
            defaults={'count': take_count},
        )
        if not item_created:
            item.count = item.count + take_count
            item.save(update_fields=['count', 'updated_at'])
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
) -> CuttingBundleItem:
    """Add or update one item inside an existing bundle (size scoped via FK).

    Idempotent: same (bundle, pattern, color) → count UPDATE.
    Validates bundle belongs to this adda's cutting record.

    Side effects:
      • Writes CuttingBundleItem (update_or_create).
      • If item sourced from a breakup: recomputes CuttingPieceBreakup.consumed_count.
      • Recomputes + writes CuttingBundle.total_pieces.
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")
    if count < 1:
        raise ValidationError("Item count must be >= 1.")

    try:
        bundle = CuttingBundle.objects.select_related('size').get(
            pk=bundle_id, cutting_record__stage_record=sr,
        )
    except CuttingBundle.DoesNotExist:
        raise ValidationError("Bundle does not belong to this Adda.")

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
    # If this (bundle,pattern,color) row was originally sourced from a breakup
    # (created via add_pieces_to_bundle), overwriting its count above leaves that
    # breakup's consumed_count stale → re-sync it. Purely-manual rows have no source.
    if item.source_breakup_id is not None:
        _recompute_breakup_consumed(item.source_breakup)
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
) -> CuttingBundleItem:
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
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")
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

    cr = _get_or_create_cutting_record(adda)
    bundle, bundle_created = CuttingBundle.objects.get_or_create(
        cutting_record=cr, size_id=size_id,
        defaults={'total_pieces': 0, 'bundle_number': (bundle_number or '')[:40]},
    )
    if bundle_created:
        # Log BUNDLE_CREATED on the lazy-create path too (parity with
        # create_bundle) so the Adda timeline never misses a bundle event.
        from tracking.services import log_adda
        from tracking.models import AddaHistory
        log_adda(adda, AddaHistory.ChangeType.BUNDLE_CREATED, user,
                 stage_record=sr, metadata={'bundle_id': bundle.id, 'size_id': size_id})
    if bundle_number and bundle.bundle_number != bundle_number[:40]:
        bundle.bundle_number = bundle_number[:40]
        bundle.save(update_fields=['bundle_number', 'updated_at'])

    item, _ = CuttingBundleItem.objects.update_or_create(
        bundle=bundle, pattern_id=pattern_id, color_id=color_id,
        defaults={'count': count},
    )
    # If this (bundle,pattern,color) row was originally sourced from a breakup
    # (created via add_pieces_to_bundle), overwriting its count above leaves that
    # breakup's consumed_count stale → re-sync it. Purely-manual rows have no source.
    if item.source_breakup_id is not None:
        _recompute_breakup_consumed(item.source_breakup)
    _recompute_bundle_total(bundle)
    logger.info(
        "cutting.add_bundle_item adda=%s bundle=%s item=%s size_id=%s "
        "pattern_id=%s color_id=%s count=%s bundle_total=%s",
        adda.code, bundle.id, item.id, size_id, pattern_id, color_id, count,
        bundle.total_pieces,
    )
    return item


@transaction.atomic
def delete_bundle_item(*, adda: Adda, item_id: int, user) -> None:
    """Remove one line item. Restores consumed_count on source breakup row.
    Auto-deletes parent bundle if empty.

    Side effects:
      • Deletes CuttingBundleItem row.
      • If sourced from a breakup: recomputes CuttingPieceBreakup.consumed_count.
      • Recomputes CuttingBundle.total_pieces; deletes the bundle if now empty.
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")
    item = CuttingBundleItem.objects.filter(
        pk=item_id, bundle__cutting_record__stage_record=sr,
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
    item.delete()
    if source is not None:
        _recompute_breakup_consumed(source)
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
def delete_bundle(*, adda: Adda, bundle_id: int, user) -> None:
    """Remove entire bundle. Restores consumed_count on all source breakup rows.

    Side effects:
      • Deletes CuttingBundle (cascades its CuttingBundleItem rows).
      • Recomputes CuttingPieceBreakup.consumed_count for each source breakup.
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — bundles locked.")
    bundle = CuttingBundle.objects.filter(
        pk=bundle_id, cutting_record__stage_record=sr,
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
    # Collect source breakup IDs before delete (cascade will drop items).
    source_ids = set(
        bundle.items.exclude(source_breakup__isnull=True)
        .values_list('source_breakup_id', flat=True)
    )
    bundle.delete()
    # Recompute consumed_count on each source breakup row.
    for sb in CuttingPieceBreakup.objects.filter(pk__in=source_ids):
        _recompute_breakup_consumed(sb)
    logger.info(
        "cutting.delete_bundle adda=%s bundle=%s source_breakups_recomputed=%s",
        adda.code, bundle_id, len(source_ids),
    )


@transaction.atomic
def upsert_breakup_row(
    *, adda: Adda, size_id: int, color_id: int, pattern_id: int,
    count: int, roll_id: int | None = None, user,
) -> CuttingPieceBreakup:
    """Ek breakup row save/update (size, color, pattern) ke combination ke liye.

    Idempotent: same combo pe phir se call karo to row update (count + roll
    overwrite). count == 0 → delete row (helper convenience).
    """
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
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

    cr = _get_or_create_cutting_record(adda)

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
def delete_breakup_row(*, adda: Adda, breakup_id: int, user) -> None:
    """Ek breakup row hatao."""
    _ensure_cutting_skill(user)
    sr = _get_or_create_cutting_stage_record(adda)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed — breakup locked.")
    CuttingPieceBreakup.objects.filter(
        pk=breakup_id, cutting_record__stage_record=sr,
    ).delete()


@transaction.atomic
def save_cutting_draft(
    *, adda: Adda, notes: str | None = None, user,
) -> CuttingRecord:
    """Notes save + ensure CuttingRecord exists. No advance, no validation."""
    _ensure_cutting_skill(user)
    cr = _get_or_create_cutting_record(adda)
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
    _ensure_can_manage(user)
    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_CUTTING:
        raise ValidationError("Adda is not at Cutting stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if pieces_cut < 1:
        raise ValidationError("pieces_cut must be >= 1")

    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=stage,
        started_at=timezone.now(),
        completed_at=timezone.now(), completed_by=user,
    )
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
def complete_cutting_from_bundles(*, adda: Adda, user) -> CuttingRecord:
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
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not at the cutting stage.")

    try:
        # WF-4: lock the stage row so a concurrent completer blocks here and then
        # sees completed_at set below — prevents double-advance / double-freeze.
        sr = AddaStageRecord.objects.select_for_update().get(adda=adda, workflow_stage=wf)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage not started — assign workers first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    cr = getattr(sr, 'cutting', None)
    if cr is None:
        raise ValidationError("No cutting record yet — add actual bundles first.")

    items = list(
        CuttingBundleItem.objects
        .filter(bundle__cutting_record=cr)
        .select_related('bundle__size', 'pattern', 'color')
    )
    if not items:
        raise ValidationError("Add at least one actual cutting bundle item.")
    total = sum(it.count for it in items)
    if total <= 0:
        raise ValidationError("Total piece count must be > 0.")

    # Pattern stage allocations (if pattern stage in workflow).
    pattern_record = _pattern_record_for_adda(adda)
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
    layering_record = _get_layering_record_for_adda(adda)
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
    inline_barcodes = not _product_has_barcode_gen_stage(adda)
    if inline_barcodes:
        from production.stages.barcode_generation.assembly import generate_for_cutting
        generate_for_cutting(cr)

    advance_to_next_stage(adda, user)
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
