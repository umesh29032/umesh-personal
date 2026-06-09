"""BarcodeBatch range allocation + per-piece scan state + QR rendering.

YEH FILE KYU HAI?
─────────────────
Cutting stage complete pe har (color, size) ke liye ek BarcodeBatch
range create hota hai. Per-piece BatchBarcode rows lazy — sirf scan ya
status update pe ban-te hain.

Storage model (PR6 2026-05-28):
  Old (PR4):  500 pieces → 500 BatchBarcode rows ek INSERT mein.
  New (PR6):  500 pieces → 5 BarcodeBatch rows (1 per color/size combo).
              Individual BatchBarcode lazy: jab scan ho tab create.

Range allocation rule (deterministic):
  CuttingPieceBreakup rows ko (size.display_order, size.code, color.name) se
  sort karo, phir contiguous seq ranges allocate. Reruns same result dete hain.

One-shot guarantee:
  Same Adda pe dobara generate_for_cutting → IntegrityError.

Industrial QR rendering:
  ECC level Q (25% damage tolerance) — sticker dirty/torn ho bhi scan.
  4-module quiet zone (ISO 18004 required).
"""
from __future__ import annotations

import base64
import io
import logging
from collections import defaultdict

from django.db import IntegrityError, transaction
from django.urls import reverse

from tracking.models import BarcodeBatch, BatchBarcode

# Module logger — for debugging cross-app barcode-range writes + scan state.
logger = logging.getLogger(__name__)


def _compact_code(s: str, max_len: int = 8) -> str:
    """Color/size/pattern codes ko display labels mein fit karne ke liye.

    Whitespace strip + uppercase + non-alnum drop + truncate. Used by
    BarcodeBatch.__str__ aur templates — value format mein nahi.
    """
    if not s:
        return ''
    cleaned = ''.join(c for c in s.upper() if c.isalnum())
    return cleaned[:max_len]


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

    Workflow:
        suggested breakup → cutting master verifies (informational)
        actual bundles    → karigar enters per-size with items (pattern × color)
        barcode generator → iterates items, aggregates by (size, color)

    DUAL PATH:
      WORKSPACE  → bundle items exist → aggregate by (color, size),
                   allocate contiguous seq ranges, bulk_create batches.
      LEGACY     → no items → single batch covering 1..pieces_cut.

    Returns: total pieces covered across all batches.
    Raises IntegrityError if any BarcodeBatch already exists for this Adda.

    Side effects:
      - Writes BarcodeBatch rows (bulk_create, one per (size, color) combo;
        or a single legacy batch via _generate_legacy_batch).
      - Reads production.CuttingBundleItem (cross-app) to source per-combo counts.
    """
    adda = cutting_record.stage_record.adda
    if BarcodeBatch.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcode batches already generated for {adda.code}")

    # Lazy import — avoid circular at module load.
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

    Naya canonical path: barcode_generation stage iss function ko call karta
    hai. AddaProductSizeColorPieceBreakdown rows ko (size, color) sort karke
    contiguous seq ranges allocate karta — same deterministic key as
    generate_for_cutting.

    DIFFERENCE FROM generate_for_cutting:
      generate_for_cutting    → reads CuttingBundleItem (live, can change)
      generate_from_breakdown → reads AddaProductSizeColorPieceBreakdown
                                (frozen at cutting completion — manufacturing
                                 truth)

    Both produce identical BarcodeBatch shape. New stage uses this; legacy
    inline cutting path keeps generate_for_cutting for back-compat.

    Raises IntegrityError if any BarcodeBatch already exists for this Adda.
    Returns: total pieces covered across all batches.
    """
    from production.models import AddaProductSizeColorPieceBreakdown
    sr = barcode_gen_record.stage_record
    adda = sr.adda
    if BarcodeBatch.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcode batches already generated for {adda.code}")

    # Source = breakdown rows. Find them via the cutting_record on this Adda.
    # Production model has Adda → cutting_record via stage_record chain.
    from production.models import AddaStageRecord
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


# ── Value parse + range lookup ─────────────────────────────────────────────

def parse_value(value: str) -> tuple[str, int] | None:
    """Split '{ADDA}-{SEQ:04d}' → (adda_code, seq). None if malformed."""
    if not value or '-' not in value:
        return None
    parts = value.rsplit('-', 1)
    if len(parts) != 2:
        return None
    adda_code, seq_str = parts
    try:
        seq = int(seq_str)
    except (TypeError, ValueError):
        return None
    if seq < 1:
        return None
    return adda_code, seq


def resolve_value(value: str) -> tuple[BarcodeBatch, int] | None:
    """Value se BarcodeBatch + seq find karo. None if no match."""
    parsed = parse_value(value)
    if parsed is None:
        return None
    adda_code, seq = parsed
    batch = (
        BarcodeBatch.objects
        .select_related('adda', 'product', 'color', 'size')
        .filter(adda__code=adda_code, start_seq__lte=seq, end_seq__gte=seq)
        .first()
    )
    if batch is None:
        return None
    return batch, seq


@transaction.atomic
def get_or_create_piece(batch: BarcodeBatch, seq: int) -> BatchBarcode:
    """Lazy-create BatchBarcode scan-state row for piece `seq` in `batch`.

    Idempotent: existing row returned. Pre-condition: seq ∈ batch range.

    Side effects:
      - May write one BatchBarcode row (get_or_create) for piece `seq`.
    """
    if not (batch.start_seq <= seq <= batch.end_seq):
        raise ValueError(f"seq {seq} not in batch {batch.start_seq}..{batch.end_seq}")
    value = batch.value_for_seq(seq)
    obj, created = BatchBarcode.objects.get_or_create(
        adda=batch.adda, piece_seq=seq,
        defaults={
            'value': value,
            'batch': batch,
            'size': batch.size,
            'color': batch.color,
            # roll + pattern not derivable from batch alone (pattern aggregated out).
        },
    )
    # Defensive: ensure batch FK populated for legacy rows.
    if obj.batch_id is None:
        obj.batch = batch
        obj.save(update_fields=['batch'])
    if created:
        logger.info(
            "barcode.piece_created adda=%s seq=%s value=%s batch_id=%s",
            batch.adda.code, seq, value, batch.id,
        )
    return obj


# ── QR rendering (unchanged) ───────────────────────────────────────────────


def qr_data_uri(barcode_or_value, base_url: str, *, box_size: int = 6) -> str:
    """Barcode value (or row) → QR PNG data URI.

    Accepts either a BatchBarcode row OR a raw value string. ECC Q (25%
    damage tolerance). 4-module quiet zone (ISO 18004).
    """
    import qrcode
    from qrcode.constants import ERROR_CORRECT_Q
    if isinstance(barcode_or_value, str):
        value = barcode_or_value
    else:
        value = barcode_or_value.value
    payload = base_url.rstrip('/') + reverse('tracking:scan', args=[value])

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_Q,
        box_size=box_size,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


# ── Status update — lazy create from batch + scan state ───────────────────


@transaction.atomic
def mark_status(user, barcode_value: str, status: str) -> BatchBarcode:
    """Barcode ka status update — packed/dispatched/missing.

    Accepts value string. Resolves via batch, lazy-creates BatchBarcode row
    if absent.

    Side effects:
      - Writes BatchBarcode.status (and may create the row via
        get_or_create_piece).
    """
    if status not in dict(BatchBarcode.Status.choices):
        from django.core.exceptions import ValidationError
        raise ValidationError(f"invalid status '{status}'")
    hit = resolve_value(barcode_value)
    if hit is None:
        from django.core.exceptions import ValidationError
        raise ValidationError(f"unknown barcode '{barcode_value}'")
    batch, seq = hit
    piece = get_or_create_piece(batch, seq)
    piece.status = status
    piece.save(update_fields=['status'])
    logger.info(
        "barcode.mark_status user=%s adda=%s seq=%s value=%s status=%s",
        getattr(user, 'id', None), batch.adda.code, seq, barcode_value, status,
    )
    return piece
