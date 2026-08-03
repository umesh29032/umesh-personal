"""Barcode-range ASSEMBLY — production-owned (P4.2 relocation, 2026-06-11).

Moved verbatim from tracking.services.barcode_service. Assembly reads CUTTING
data (CuttingBundleItem / AddaProductSizeColorPieceBreakdown) to decide which
BarcodeBatch ranges exist — that is a production concern (R1 §8 / P4.2 Option A:
identity issuance orchestration lives in production; `tracking` stays the dumb
range/scan/history primitive and imports no production). This module WRITES
tracking.BarcodeBatch rows — a one-way production→tracking edge (allowed:
tracking sits BELOW production in the layering).

Range allocation rule (deterministic): sort by (size.display_order, size.code,
color.name), then allocate contiguous seq ranges. Reruns give same result.
One-shot guarantee: second generate for the same Adda → IntegrityError.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from django.db import IntegrityError, transaction

from tracking.models import BarcodeBatch

logger = logging.getLogger(__name__)


def _allocation_key(size, color) -> tuple:
    """Sort key for deterministic range allocation.

    Sequence: size display_order → size code → color name. Two
    Addas with same bundle structure get identical ranges.
    """
    size_order = size.display_order if size else 0
    size_code = size.code if size else ''
    color_name = color.name if color else ''
    return (size_order, size_code, color_name)


@transaction.atomic
def generate_for_cutting(cutting_record) -> int:
    """BarcodeBatch range rows create karta hai cutting_record.bundles.items se.

    PR8 (2026-05-28): bundle = per-size header; items = per (pattern, color, count)
    inside bundle. Aggregation by (size, color) collapses patterns.

    DUAL PATH:
      WORKSPACE  → bundle items exist → aggregate by (color, size),
                   allocate contiguous seq ranges, bulk_create batches.
      LEGACY     → no items → single batch covering 1..pieces_cut.

    Returns: total pieces covered across all batches.
    Raises IntegrityError if any BarcodeBatch already exists for this Adda.

    Side effects:
      - Writes BarcodeBatch rows (bulk_create, one per (size, color) combo;
        or a single legacy batch via _generate_legacy_batch).
      - Reads production.CuttingBundleItem to source per-combo counts.
    """
    adda = cutting_record.stage_record.adda
    if BarcodeBatch.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcode batches already generated for {adda.code}")

    from production.models import CuttingBundleItem
    items = list(
        CuttingBundleItem.objects
        .filter(bundle__cutting_record=cutting_record)
        .select_related('bundle__size', 'color')
    )

    batches: list[BarcodeBatch] = []

    if items:
        # Aggregate by (size_id, color_id) — sum across patterns + bundles
        # within same size. Track bundle_id per key (one bundle per size).
        agg: dict[tuple[int, int], int] = defaultdict(int)
        ref: dict[tuple[int, int], tuple] = {}
        bundle_by_key: dict[tuple[int, int], int] = {}
        for it in items:
            if it.count <= 0:
                continue
            key = (it.bundle.size_id, it.color_id)
            agg[key] += it.count
            ref.setdefault(key, (it.bundle.size, it.color))
            bundle_by_key.setdefault(key, it.bundle_id)

        if not agg:
            return _generate_legacy_batch(cutting_record, adda)

        sorted_keys = sorted(
            agg.keys(),
            key=lambda k: _allocation_key(*ref[k]),
        )

        next_seq = 1
        for (size_id, color_id) in sorted_keys:
            count = agg[(size_id, color_id)]
            start = next_seq
            end = next_seq + count - 1
            batches.append(BarcodeBatch(
                adda=adda, product=adda.product,
                color_id=color_id, size_id=size_id,
                bundle_id=bundle_by_key[(size_id, color_id)],
                start_seq=start, end_seq=end, total_pieces=count,
            ))
            next_seq = end + 1

        BarcodeBatch.objects.bulk_create(batches)
        total = next_seq - 1
        logger.info(
            "barcode.generate_for_cutting adda=%s batches=%s pieces=%s source=workspace",
            adda.code, len(batches), total,
        )
        return total

    return _generate_legacy_batch(cutting_record, adda)


def _generate_legacy_batch(cutting_record, adda) -> int:
    """Legacy single-batch path for simple flows (NIKKAR, no breakup).

    Side effects:
      - Writes one BarcodeBatch row covering 1..pieces_cut.
    """
    count = cutting_record.pieces_cut
    if count <= 0:
        return 0
    BarcodeBatch.objects.create(
        adda=adda, product=adda.product,
        color=None, size=None,
        start_seq=1, end_seq=count, total_pieces=count,
    )
    logger.info(
        "barcode.generate_for_cutting adda=%s batches=1 pieces=%s source=legacy",
        adda.code, count,
    )
    return count


@transaction.atomic
def generate_from_breakdown(barcode_gen_record) -> int:
    """PR-B 2026-05-29 — generate BarcodeBatch rows from breakdown snapshot.

    Canonical path: barcode_generation stage calls this. Sorts
    AddaProductSizeColorPieceBreakdown rows by (size, color) and allocates
    contiguous seq ranges — same deterministic key as generate_for_cutting.

    DIFFERENCE FROM generate_for_cutting:
      generate_for_cutting    → reads CuttingBundleItem (live, can change)
      generate_from_breakdown → reads AddaProductSizeColorPieceBreakdown
                                (frozen at cutting completion — manufacturing truth)

    Raises IntegrityError if any BarcodeBatch already exists for this Adda.
    Returns: total pieces covered across all batches.
    """
    from production.models import AddaProductSizeColorPieceBreakdown, AddaStageRecord
    sr = barcode_gen_record.stage_record
    adda = sr.adda
    if BarcodeBatch.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcode batches already generated for {adda.code}")

    # Source = breakdown rows. Find them via the cutting_record on this Adda.
    cutting_sr = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code='cutting',
    ).first()
    if cutting_sr is None:
        return 0
    cr = getattr(cutting_sr, 'cutting', None)
    if cr is None:
        return 0

    rows = list(
        AddaProductSizeColorPieceBreakdown.objects
        .filter(cutting_record=cr)
        .select_related('size', 'color', 'bundle')
    )
    if not rows:
        return 0

    sorted_rows = sorted(rows, key=lambda r: _allocation_key(r.size, r.color))
    batches: list[BarcodeBatch] = []
    next_seq = 1
    for r in sorted_rows:
        if r.verified_piece_count <= 0:
            continue
        start = next_seq
        end = next_seq + r.verified_piece_count - 1
        batches.append(BarcodeBatch(
            adda=adda, product=adda.product,
            color_id=r.color_id, size_id=r.size_id,
            bundle_id=r.bundle_id,
            start_seq=start, end_seq=end,
            total_pieces=r.verified_piece_count,
        ))
        next_seq = end + 1

    if batches:
        BarcodeBatch.objects.bulk_create(batches)
    return next_seq - 1

def generate_for_adda(adda) -> int:
    """Streams redesign (2026-07-11): inline generation at THE JOIN — one
    pass over EVERY lane's frozen AddaProductSizeColorPieceBreakdown rows
    (the complete product exists only now). Same batch/sequence semantics
    as generate_for_cutting; same one-shot guard."""
    if BarcodeBatch.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcode batches already generated for {adda.code}")
    from production.models import AddaProductSizeColorPieceBreakdown
    rows = list(
        AddaProductSizeColorPieceBreakdown.objects
        .filter(adda=adda)
        .select_related('size', 'color'))
    agg = defaultdict(int)
    ref = {}
    bundle_by_key = {}
    for r in rows:
        if not r.verified_piece_count:
            continue
        key = (r.size_id, r.color_id)
        agg[key] += r.verified_piece_count
        ref.setdefault(key, (r.size, r.color))
        bundle_by_key.setdefault(key, r.bundle_id)
    if not agg:
        return 0
    sorted_keys = sorted(agg.keys(), key=lambda k: _allocation_key(*ref[k]))
    batches = []
    next_seq = 1
    for key in sorted_keys:
        count = agg[key]
        batches.append(BarcodeBatch(
            adda=adda, product=adda.product,
            bundle_id=bundle_by_key[key],
            size_id=key[0], color_id=key[1],
            start_seq=next_seq, end_seq=next_seq + count - 1,
            total_pieces=count))
        next_seq += count
    BarcodeBatch.objects.bulk_create(batches)
    return next_seq - 1

def append_uncovered_batches(adda):
    """IDENTITY-LAW append (owner-approved readiness 2026-07-11): cover
    breakdown truth that arrived AFTER generation — a late Cutting
    Stream (recut / shortfall / added production). Per (size, color):
    deficit = Σ frozen breakdown − Σ already-batched; new batches start
    at Max(end_seq)+1. Sequences append forever, never renumber;
    existing identities and printed labels untouched.

    Returns (appended_total, lane_notes). Raises ValidationError when
    every cut piece already has an identity ("nothing new to cover").
    """
    from django.core.exceptions import ValidationError
    from django.db.models import Max
    from production.models import AddaProductSizeColorPieceBreakdown

    covered = defaultdict(int)
    for b in BarcodeBatch.objects.filter(adda=adda):
        covered[(b.size_id, b.color_id)] += b.total_pieces

    produced = defaultdict(int)
    ref = {}
    lane_notes = set()
    rows = (AddaProductSizeColorPieceBreakdown.objects
            .filter(adda=adda)
            .select_related('size', 'color',
                            'cutting_record__stage_record__stream'))
    for r in rows:
        key = (r.size_id, r.color_id)
        produced[key] += (r.verified_piece_count or 0)
        ref.setdefault(key, (r.size, r.color))
        stream = r.cutting_record.stage_record.stream
        if stream is not None:
            note = stream.label
            if stream.reason:
                note += f' ({stream.reason})'
            lane_notes.add(note)

    deficits = {k: produced[k] - covered.get(k, 0)
                for k in produced if produced[k] > covered.get(k, 0)}
    if not deficits:
        raise ValidationError(
            'Nothing new to cover — every cut piece already has an '
            'identity.')

    next_seq = (BarcodeBatch.objects.filter(adda=adda)
                .aggregate(m=Max('end_seq'))['m'] or 0) + 1
    batches = []
    for key in sorted(deficits, key=lambda k: _allocation_key(*ref[k])):
        count = deficits[key]
        batches.append(BarcodeBatch(
            adda=adda, product=adda.product, bundle=None,
            size_id=key[0], color_id=key[1],
            start_seq=next_seq, end_seq=next_seq + count - 1,
            total_pieces=count))
        next_seq += count
    BarcodeBatch.objects.bulk_create(batches)
    return next_seq - batches[0].start_seq if batches else 0, sorted(lane_notes)
