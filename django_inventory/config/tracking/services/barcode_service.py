"""Per-piece scan state + QR rendering — the tracking PRIMITIVE.

P4.2 (2026-06-11): the range ASSEMBLY (generate_for_cutting /
generate_from_breakdown / _generate_legacy_batch) moved to
production.stages.barcode_generation.assembly — it reads cutting data, so it
is a production concern. This module keeps only ID/value-addressed scan,
QR render, and status logic and imports NO production (R1 §8 boundary).

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

from django.db import transaction
from django.urls import reverse

from tracking.models import BarcodeBatch, BatchBarcode

# Module logger — for debugging cross-app barcode-range writes + scan state.
logger = logging.getLogger(__name__)


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
