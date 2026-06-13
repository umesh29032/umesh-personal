"""Denormalized-counter reconciliation (DM-4 / P5.3) — READ-ONLY.

Some counters are denormalized (stored = SUM of child rows) for read speed:
  • CuttingRecord.pieces_cut          == SUM(its CuttingPieceBreakup.count)
  • BarcodeGenerationRecord.total_barcodes == SUM(the Adda's BarcodeBatch.total_pieces)

If a re-sync is ever missed, the stored value drifts silently. This verifier
recomputes the source SUM and reports mismatches, so a periodic `reconcile_denorm`
command (or CI) catches drift. Bulk-annotated → a FIXED query count, no N+1.
(Worker-pay reconciliation is separate — see expense.services.reconciliation_service.)
"""
from django.db.models import Sum


def reconcile_denorm() -> list[dict]:
    """Return one dict per MISMATCH: {model, pk, adda, field, stored, source}.
    Empty list = every denormalized counter matches its source."""
    from production.models import BarcodeGenerationRecord, CuttingRecord

    out: list[dict] = []

    for r in (
        CuttingRecord.objects
        .annotate(_src=Sum('breakup__count'))
        .values('pk', 'pieces_cut', '_src', 'stage_record__adda__code')
    ):
        src = r['_src'] or 0
        if r['pieces_cut'] != src:
            out.append({
                'model': 'CuttingRecord', 'pk': r['pk'],
                'adda': r['stage_record__adda__code'], 'field': 'pieces_cut',
                'stored': r['pieces_cut'], 'source': src,
            })

    for r in (
        BarcodeGenerationRecord.objects
        .annotate(_src=Sum('stage_record__adda__barcode_batches__total_pieces'))
        .values('pk', 'total_barcodes', '_src', 'stage_record__adda__code')
    ):
        src = r['_src'] or 0
        if r['total_barcodes'] != src:
            out.append({
                'model': 'BarcodeGenerationRecord', 'pk': r['pk'],
                'adda': r['stage_record__adda__code'], 'field': 'total_barcodes',
                'stored': r['total_barcodes'], 'source': src,
            })

    return out
