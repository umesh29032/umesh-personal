"""BatchBarcode generation + QR rendering + scan-status updates.

YEH FILE KYU HAI?
─────────────────
Cutting stage complete hone par piece-level barcodes auto-generate hote hain.
Industrial-grade QR rendering (ECC Q = 25% damage tolerance) — shop-floor stickers
dirty/torn ho jaayein bhi scan hote rahein.

One-shot guarantee:
  Same Adda pe dobara generate karne ki koshish karoge to IntegrityError.
  Pehli call existence check kar leta hai — race-safe via @transaction.atomic.
"""
from __future__ import annotations

import base64
import io

from django.db import IntegrityError, transaction
from django.urls import reverse

from tracking.models import BatchBarcode


@transaction.atomic
def generate_for_cutting(cutting_record) -> int:
    """N BatchBarcode rows bulk-insert karta hai is Adda ke liye.

    500 pieces ka cutting → 500 barcodes ek hi INSERT mein.
    Same Adda pe duplicate call ho jaaye to IntegrityError (one-shot rule).
    """
    adda = cutting_record.stage_record.adda
    # Existence check — agar barcodes pehle se hain to no-op + error
    if BatchBarcode.objects.filter(adda=adda).exists():
        raise IntegrityError(f"barcodes already generated for {adda.code}")

    count = cutting_record.pieces_cut
    # List comprehension — N rows memory mein banao, phir single INSERT
    rows = [
        BatchBarcode(
            adda=adda,
            piece_seq=i,
            value=f"{adda.code}-{i:04d}",   # e.g. 'T-SHIRT-001-0042'
        )
        for i in range(1, count + 1)
    ]
    # bulk_create = ek hi INSERT statement — N round-trips bachte hain
    BatchBarcode.objects.bulk_create(rows)
    return count


def qr_data_uri(barcode: BatchBarcode, base_url: str, *, box_size: int = 6) -> str:
    """Barcode ke scan URL ka QR PNG data: URI return karta hai (base64 encoded).

    Industrial settings:
      • ECC level Q (25% damage tolerance) — sticker thoda dirty/torn ho bhi
        to scan hota rahega. Cloth factory mein zaruri.
      • 4-module quiet zone (ISO 18004 minimum) — bina border QR scanner confuse hota hai.
      • box_size pixels per QR module — caller decide karta hai print density
        (small/medium/large sticker sizes).

    On-demand render, DB mein store nahi. base_url request.build_absolute_uri('/')
    se aata hai → URLs sahi hostname pe banti hain.
    """
    # Lazy import — qrcode lib har request load karne ki zarurat nahi
    import qrcode
    from qrcode.constants import ERROR_CORRECT_Q
    # reverse() = URL name se URL banao (kabhi hardcode mat karo)
    payload = base_url.rstrip('/') + reverse('tracking:scan', args=[barcode.value])

    qr = qrcode.QRCode(
        version=None,                  # version auto-pick — sabse chhota jo URL fit kare
        error_correction=ERROR_CORRECT_Q,
        box_size=box_size,             # pixels per QR module
        border=4,                       # quiet zone — ISO 18004 required
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # PNG bytes → base64 → data: URI (img src mein directly embeddable)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


@transaction.atomic
def mark_status(user, barcode: BatchBarcode, status: str) -> BatchBarcode:
    """Barcode ka status update — packed/dispatched/missing. Scan flow se called."""
    # Validate status against TextChoices ka dict — invalid value rejected
    if status not in dict(BatchBarcode.Status.choices):
        from django.core.exceptions import ValidationError
        raise ValidationError(f"invalid status '{status}'")
    barcode.status = status
    barcode.save(update_fields=['status'])
    return barcode
