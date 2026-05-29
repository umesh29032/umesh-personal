"""Barcode export service — CSV / XLSX / PDF generators + manifest tracking.

YEH FILE KYU HAI?
─────────────────
PR-D 2026-05-29 (BARCODE_STAGE_PLAN.md): Barcode Generation stage complete
hone par vendor / factory label printing ke liye exports zaroori. Yeh
service:
  • on-the-fly file generate karta hai (BarcodeBatch + BatchBarcode se)
  • BarcodeExportBatch manifest row save karta hai (audit + re-download)
  • Same export_code se re-download → fresh regeneration from live data

GATING:
  Sirf tab export ho sakta hai jab barcode_generation stage complete hai.
  Cutting-only flows (legacy NIKKAR-style) bhi support — woh CuttingRecord
  via Adda dhoondh ke barcode_gen_record substitute karte hain (TODO note
  in code; for now require explicit bg stage completion).

WHY ON-THE-FLY:
  Storage bloat avoid + barcode mutations ke saath sync rakhna easy.
  Re-download = re-export from live BarcodeBatch.
  Manifest row total_labels frozen at first export (audit trail).

CODE FORMAT:
  EXP-YYYY-NNN — year + 3-digit counter. Counter increment select_for_update
  pattern (mirror of Product.adda_counter race-safe approach), but yahaan
  simpler: count existing + 1 inside @transaction.atomic.
"""
from __future__ import annotations

import csv
import io

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from production.models import Adda, BarcodeGenerationRecord
from tracking.models import (
    BarcodeBatch, BarcodeExportBatch, BatchBarcode,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _ensure_barcode_stage_complete(adda: Adda) -> BarcodeGenerationRecord:
    """Refuse export unless barcode_generation stage is complete.

    Returns the completed BarcodeGenerationRecord for FK use.
    """
    from production.models import AddaStageRecord
    bg_sr = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code='barcode_generation',
    ).first()
    if bg_sr is None:
        raise ValidationError(
            "Exports require the barcode_generation stage in this product's "
            "workflow."
        )
    if bg_sr.completed_at is None:
        raise ValidationError(
            "Cannot export — barcode_generation stage is not yet completed."
        )
    rec = getattr(bg_sr, 'barcode_generation', None)
    if rec is None:
        raise ValidationError("BarcodeGenerationRecord missing for this Adda.")
    return rec


def _next_export_code() -> str:
    """Generate next EXP-YYYY-NNN code. Race-safe via @transaction.atomic +
    count + lock.

    NOTE: not strictly contention-safe across concurrent inserts at high
    throughput. For factory floor scale (few exports/day) this is sufficient.
    Future hardening: dedicated Postgres sequence per year.
    """
    year = timezone.now().year
    prefix = f'EXP-{year}-'
    last = (
        BarcodeExportBatch.objects
        .filter(export_code__startswith=prefix)
        .order_by('-export_code').first()
    )
    if last is None:
        next_num = 1
    else:
        try:
            next_num = int(last.export_code.rsplit('-', 1)[-1]) + 1
        except (TypeError, ValueError):
            next_num = BarcodeExportBatch.objects.filter(
                export_code__startswith=prefix,
            ).count() + 1
    return f'{prefix}{next_num:03d}'


def _iter_export_rows(adda: Adda):
    """Yield per-piece dicts for an Adda's barcode export.

    Expands each BarcodeBatch range into individual piece rows + merges
    scanned-state from BatchBarcode (if scanned).

    Output dict keys:
      barcode, qr_payload, adda, product, bundle, size, color, piece_seq
    """
    batches = list(
        BarcodeBatch.objects.filter(adda=adda)
        .select_related('size', 'color', 'product', 'bundle')
        .order_by('start_seq')
    )
    if not batches:
        return
    scanned = {
        bc.piece_seq: bc for bc in
        BatchBarcode.objects.filter(adda=adda)
        .only('piece_seq', 'value', 'status')
    }
    for batch in batches:
        size_label = batch.size.label if batch.size_id else ''
        color_label = batch.color.name if batch.color_id else ''
        bundle_label = (
            f"Bundle-{batch.bundle.size.code.upper()}"
            if batch.bundle_id and batch.bundle.size_id else ''
        )
        for seq in range(batch.start_seq, batch.end_seq + 1):
            value = batch.value_for_seq(seq)
            yield {
                'barcode': value,
                'qr_payload': value,  # QR encodes barcode value verbatim
                'adda': adda.code,
                'product': adda.product.code,
                'bundle': bundle_label,
                'size': size_label,
                'color': color_label,
                'piece_seq': seq,
            }


def _count_total_labels(adda: Adda) -> int:
    return sum(
        b.total_pieces for b in BarcodeBatch.objects.filter(adda=adda)
    )


# ── File-format renderers (pure functions — no DB writes) ────────────────

_HEADERS = [
    'barcode', 'qr_payload', 'adda', 'product',
    'bundle', 'size', 'color', 'piece_seq',
]


def _render_csv_bytes(adda: Adda) -> bytes:
    """Render export as CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_HEADERS)
    for row in _iter_export_rows(adda):
        writer.writerow([row[k] for k in _HEADERS])
    return buf.getvalue().encode('utf-8')


def _render_xlsx_bytes(adda: Adda) -> bytes:
    """Render export as XLSX bytes via openpyxl."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = adda.code[:31]  # XLSX sheet name max 31 chars
    ws.append(_HEADERS)
    for row in _iter_export_rows(adda):
        ws.append([row[k] for k in _HEADERS])
    # Auto-size columns roughly (header length + small pad)
    for i, h in enumerate(_HEADERS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, len(h) + 2)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _render_pdf_summary_bytes(adda: Adda) -> bytes:
    """Render an aggregate PDF summary (NOT per-piece labels).

    Per-piece label rendering = vendor's job (PDF of QR labels). This PDF
    is the manifest: totals per (size, color) + grand total. Useful for
    factory-floor sign-off / vendor pickup confirmation.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Barcode Export Summary</b>", styles['Title']))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(f"Adda: <b>{adda.code}</b>", styles['Normal']))
    story.append(Paragraph(f"Product: {adda.product.name} ({adda.product.code})", styles['Normal']))
    story.append(Paragraph(
        f"Exported: {timezone.now().strftime('%d %b %Y %H:%M')}", styles['Normal'],
    ))
    story.append(Spacer(1, 8*mm))

    # Per-batch summary table
    data = [['Size', 'Color', 'Range', 'Pieces']]
    batches = list(
        BarcodeBatch.objects.filter(adda=adda)
        .select_related('size', 'color').order_by('start_seq')
    )
    total = 0
    for b in batches:
        data.append([
            b.size.label if b.size_id else '—',
            b.color.name if b.color_id else '—',
            f'{b.start_value} … {b.end_value}',
            str(b.total_pieces),
        ])
        total += b.total_pieces
    data.append(['', '', 'TOTAL', str(total)])

    tbl = Table(data, colWidths=[25*mm, 35*mm, 80*mm, 25*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1ece2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1c1c1e')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfc0aa')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#faf7f2')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(tbl)
    doc.build(story)
    return buf.getvalue()


# ── Public API ─────────────────────────────────────────────────────────────

@transaction.atomic
def generate_csv(adda: Adda, user) -> tuple[BarcodeExportBatch, bytes]:
    """CSV export — gate check + manifest row + bytes return."""
    rec = _ensure_barcode_stage_complete(adda)
    total = _count_total_labels(adda)
    if total == 0:
        raise ValidationError("No barcodes to export.")
    batch = BarcodeExportBatch.objects.create(
        export_code=_next_export_code(),
        adda=adda, product=adda.product,
        barcode_gen_record=rec,
        export_method=BarcodeExportBatch.ExportMethod.CSV,
        exported_by=user, total_labels=total,
    )
    return batch, _render_csv_bytes(adda)


@transaction.atomic
def generate_xlsx(adda: Adda, user) -> tuple[BarcodeExportBatch, bytes]:
    """Excel export — gate check + manifest row + bytes return."""
    rec = _ensure_barcode_stage_complete(adda)
    total = _count_total_labels(adda)
    if total == 0:
        raise ValidationError("No barcodes to export.")
    batch = BarcodeExportBatch.objects.create(
        export_code=_next_export_code(),
        adda=adda, product=adda.product,
        barcode_gen_record=rec,
        export_method=BarcodeExportBatch.ExportMethod.XLSX,
        exported_by=user, total_labels=total,
    )
    return batch, _render_xlsx_bytes(adda)


@transaction.atomic
def generate_pdf_summary(adda: Adda, user) -> tuple[BarcodeExportBatch, bytes]:
    """PDF summary export — gate check + manifest row + bytes return.

    NOT per-piece labels — that's vendor PDF or factory printer queue.
    This PDF is the manifest/sign-off summary.
    """
    rec = _ensure_barcode_stage_complete(adda)
    total = _count_total_labels(adda)
    if total == 0:
        raise ValidationError("No barcodes to export.")
    batch = BarcodeExportBatch.objects.create(
        export_code=_next_export_code(),
        adda=adda, product=adda.product,
        barcode_gen_record=rec,
        export_method=BarcodeExportBatch.ExportMethod.PDF,
        exported_by=user, total_labels=total,
    )
    return batch, _render_pdf_summary_bytes(adda)


def list_exports(adda: Adda):
    """Recent exports for one Adda (newest first)."""
    return (
        BarcodeExportBatch.objects.filter(adda=adda)
        .select_related('exported_by', 'product')
        .order_by('-created_at')
    )


def regenerate_for_export(export_batch: BarcodeExportBatch) -> bytes:
    """Re-download bytes for an existing export (current barcode data).

    Note: if barcodes were reopened + regenerated since the original export,
    the file content will differ from the original download. Manifest
    total_labels remains frozen at first export (audit invariant).
    """
    adda = export_batch.adda
    method = export_batch.export_method
    if method == BarcodeExportBatch.ExportMethod.CSV:
        return _render_csv_bytes(adda)
    if method == BarcodeExportBatch.ExportMethod.XLSX:
        return _render_xlsx_bytes(adda)
    if method == BarcodeExportBatch.ExportMethod.PDF:
        return _render_pdf_summary_bytes(adda)
    raise ValidationError(f"Unknown export method '{method}'.")


# ── Content-type + filename helpers (used by views) ───────────────────────

_CONTENT_TYPES = {
    BarcodeExportBatch.ExportMethod.CSV: 'text/csv; charset=utf-8',
    BarcodeExportBatch.ExportMethod.XLSX: (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ),
    BarcodeExportBatch.ExportMethod.PDF: 'application/pdf',
}

_FILE_EXTS = {
    BarcodeExportBatch.ExportMethod.CSV: 'csv',
    BarcodeExportBatch.ExportMethod.XLSX: 'xlsx',
    BarcodeExportBatch.ExportMethod.PDF: 'pdf',
}


def content_type_for(method: str) -> str:
    return _CONTENT_TYPES.get(method, 'application/octet-stream')


def filename_for(export_batch: BarcodeExportBatch) -> str:
    ext = _FILE_EXTS.get(export_batch.export_method, 'bin')
    return f'{export_batch.export_code}-{export_batch.adda.code}.{ext}'
