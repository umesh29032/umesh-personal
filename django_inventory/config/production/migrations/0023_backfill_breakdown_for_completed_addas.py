"""Backfill AddaProductSizeColorPieceBreakdown for completed Addas.

YEH MIGRATION KYU HAI?
─────────────────────
PR-A 2026-05-29: naya breakdown model add hua hai jo Cutting Stage
completion par materialise hota hai. Yeh migration purane already-completed
Addas ke liye breakdown rows backfill karta hai — taaki dashboard +
future barcode-gen stage queries empty na dikhe.

ALGO:
  Har CuttingRecord ke liye:
    1. CuttingBundleItem rows aggregate karo by (bundle__size, color)
    2. Sum count per (size, color) — bundle FK pehle wala bundle (1 bundle
       per size per cutting record convention)
    3. AddaProductSizeColorPieceBreakdown row create karo (get_or_create
       — idempotent)
    4. created_by = NULL (system backfill, no user)

LEGACY (NO BUNDLE ITEMS):
  Cutting records jinmein koi bundle item nahi (NIKKAR-style legacy)
  ek single (size=NULL, color=NULL) row bana lete hain with
  verified_piece_count = cutting_record.pieces_cut. Yeh future-stage
  consumers ko consistent shape deta hai.

IDEMPOTENT:
  get_or_create unique_together(cutting_record, size, color) pe rely karta.
  Re-run safe.

REVERSE:
  No-op. Delete-by-script if needed manually.
"""
from collections import defaultdict

from django.db import migrations


def backfill_breakdown(apps, schema_editor):
    CuttingRecord = apps.get_model('production', 'CuttingRecord')
    CuttingBundleItem = apps.get_model('production', 'CuttingBundleItem')
    Breakdown = apps.get_model('production', 'AddaProductSizeColorPieceBreakdown')

    for cr in CuttingRecord.objects.select_related(
        'stage_record__adda__product',
    ).all():
        adda = cr.stage_record.adda
        product = adda.product

        # Aggregate CuttingBundleItem by (bundle.size_id, color_id).
        items = list(
            CuttingBundleItem.objects
            .filter(bundle__cutting_record=cr)
            .select_related('bundle')
        )
        if items:
            agg = defaultdict(int)
            bundle_by_key = {}
            for it in items:
                key = (it.bundle.size_id, it.color_id)
                agg[key] += it.count
                bundle_by_key.setdefault(key, it.bundle_id)

            for (size_id, color_id), count in agg.items():
                Breakdown.objects.get_or_create(
                    cutting_record=cr, size_id=size_id, color_id=color_id,
                    defaults={
                        'adda': adda,
                        'product': product,
                        'bundle_id': bundle_by_key[(size_id, color_id)],
                        'verified_piece_count': count,
                    },
                )
        else:
            # Legacy single-row fallback — no bundle structure.
            if cr.pieces_cut > 0:
                Breakdown.objects.get_or_create(
                    cutting_record=cr, size=None, color=None,
                    defaults={
                        'adda': adda,
                        'product': product,
                        'bundle': None,
                        'verified_piece_count': cr.pieces_cut,
                    },
                )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0022_seed_barcode_generation_stage'),
    ]

    operations = [
        migrations.RunPython(backfill_breakdown, reverse_noop),
    ]
