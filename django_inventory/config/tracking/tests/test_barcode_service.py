"""Tests for tracking barcode_service."""
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User
from inventory.models import Role
from production.models import Product
from production.services import (
    attach_roll_to_layering, complete_cutting, complete_layering,
    create_adda, record_remaining_cloth, start_layering,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BarcodeBatch, BatchBarcode
from tracking.services import generate_for_cutting, get_or_create_piece, resolve_value


def _user():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='admin@bc.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    return u


def _seed_completed_cutting():
    """Helper: build an Adda all the way through Layering, leaving it at Cutting stage."""
    from accounts.models import Skill

    user = _user()
    # Phase 4: create_adda requires ≥1 skilled user before the call
    user.skills.add(Skill.objects.get(name='cutting_master'))
    cotton = ClothType.objects.get(name='Cotton')
    red = ClothColor.objects.get(name='Red')
    loc = StorageLocation.objects.get(code='ROHINI')
    prod = Product.objects.get(code='NIKKAR')
    rolls = bulk_create_rolls(user=user, cloth_type=cotton, storage_location=loc,
                              purchased_date=date.today(),
                              breakup=[{'color': red, 'qty': 1}])
    adda = create_adda(user, product=prod)
    sr = start_layering(adda=adda, worker_ids=[user.pk], user=user)
    entries = []
    for r in rolls:
        entries.append(attach_roll_to_layering(
            stage_record=sr, roll=r,
            width_verified_inch=40, weight_verified_kg=Decimal('20'),
            user=user,
        ))
    # Leftover record mandatory before complete
    for e in entries:
        record_remaining_cloth(
            entry=e, remaining_weight_kg=Decimal('0'), remaining_length_meters=Decimal('0'),
            user=user,
        )
    complete_layering(
        adda=adda, duration_minutes=10,
        layer_length_meters=Decimal('1.5'),
        per_entry_layers={e.pk: 3 for e in entries},
        notes='', user=user,
    )
    return user, adda


class BarcodeGenerationTests(TestCase):
    def test_pieces_count_matches_batch_total(self):
        """PR6: One BarcodeBatch row covers all pieces in legacy flow."""
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=7, worker_ids=[user.pk], notes='', user=user)
        batches = list(BarcodeBatch.objects.filter(adda=adda))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 7)
        self.assertEqual(batches[0].start_seq, 1)
        self.assertEqual(batches[0].end_seq, 7)

    def test_legacy_batch_has_null_size_and_color(self):
        """Legacy single-batch path has null size + color (no breakup metadata)."""
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=3, worker_ids=[user.pk], notes='', user=user)
        batch = BarcodeBatch.objects.get(adda=adda)
        self.assertIsNone(batch.size)
        self.assertIsNone(batch.color)
        # Per-piece BatchBarcode lazy — no rows until scan.
        self.assertEqual(BatchBarcode.objects.filter(adda=adda).count(), 0)

    def test_resolve_value_walks_batch_range(self):
        """parse + resolve_value finds the right batch for a seq in range."""
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=4, worker_ids=[user.pk], notes='', user=user)
        # Mid-range seq
        hit = resolve_value(f'{adda.code}-0003')
        self.assertIsNotNone(hit)
        batch, seq = hit
        self.assertEqual(seq, 3)
        self.assertEqual(batch.adda_id, adda.id)
        # Out of range
        self.assertIsNone(resolve_value(f'{adda.code}-9999'))

    def test_get_or_create_piece_lazy(self):
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=4, worker_ids=[user.pk], notes='', user=user)
        batch = BarcodeBatch.objects.get(adda=adda)
        # No BatchBarcode rows yet
        self.assertEqual(BatchBarcode.objects.filter(adda=adda).count(), 0)
        piece = get_or_create_piece(batch, 2)
        self.assertEqual(piece.value, f'{adda.code}-0002')
        self.assertEqual(piece.batch_id, batch.id)
        # Idempotent
        piece2 = get_or_create_piece(batch, 2)
        self.assertEqual(piece.pk, piece2.pk)


class BarcodeBatchAllocationTests(TestCase):
    """PR6: batches aggregate by (size, color); patterns collapsed.
    Ranges allocated contiguously, deterministic order.
    """

    def _build_adda_with_bundles(self, bundle_specs):
        """bundle_specs = list of (size_code, color_obj, pattern_obj, count).
        PR7: bundles drive barcodes (not breakup).
        """
        from django.utils import timezone

        from accounts.models import Skill
        from production.constants import STAGE_CUTTING, STAGE_LAYERING
        from production.models import (
            AddaStageRecord, CuttingBundle, CuttingBundleItem, CuttingRecord,
            LayeringRecord, ProductPattern, ProductPatternAssignment,
            ProductSize, WorkflowStage,
        )

        user = _user()
        user.skills.add(Skill.objects.get(name='cutting_master'))
        cotton = ClothType.objects.get(name='Cotton')
        loc = StorageLocation.objects.get(code='ROHINI')
        prod = Product.objects.get(code='NIKKAR')

        colors_needed = list({spec[1] for spec in bundle_specs})
        roll_breakup = [{'color': c, 'qty': 1} for c in colors_needed]
        rolls = bulk_create_rolls(
            user=user, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=roll_breakup,
        )

        adda = create_adda(user, product=prod)
        layering_wf = WorkflowStage.objects.get(
            product=prod, stage__code=STAGE_LAYERING,
        )
        layering_sr = AddaStageRecord.objects.get(
            adda=adda, workflow_stage=layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = user
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        layering_record = LayeringRecord.objects.create(
            stage_record=layering_sr,
            lay_count=5, total_colors=len(colors_needed),
            duration_minutes=10, layer_length_meters=Decimal('1.5'),
        )
        layering_record.rolls_used.set(rolls)

        cutting_wf = WorkflowStage.objects.get(
            product=prod, stage__code=STAGE_CUTTING,
        )
        adda.current_stage = cutting_wf
        adda.save(update_fields=['current_stage'])

        cutting_sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=cutting_wf, started_at=timezone.now(),
        )
        cr = CuttingRecord.objects.create(stage_record=cutting_sr, pieces_cut=0)
        size_objs = {}
        for code, _color, _pattern, _count in bundle_specs:
            if code not in size_objs:
                size_objs[code] = ProductSize.objects.get_or_create(
                    product=prod, code=code,
                    defaults={'label': code.upper(), 'display_order': ord(code[0])},
                )[0]
        # Lazy-create bundles per-size + items inside (PR8 schema).
        bundles_by_size: dict = {}
        for size_code, color, pattern, count in bundle_specs:
            size = size_objs[size_code]
            bundle = bundles_by_size.get(size_code)
            if bundle is None:
                bundle, _ = CuttingBundle.objects.get_or_create(
                    cutting_record=cr, size=size,
                    defaults={'total_pieces': 0},
                )
                bundles_by_size[size_code] = bundle
            item, _ = CuttingBundleItem.objects.update_or_create(
                bundle=bundle, pattern=pattern, color=color,
                defaults={'count': count},
            )
            bundle.total_pieces = sum(it.count for it in bundle.items.all())
            bundle.save(update_fields=['total_pieces', 'updated_at'])

        return adda, cr

    def test_aggregates_patterns_into_single_batch_per_color_size(self):
        red = ClothColor.objects.get(name='Red')
        from production.models import ProductPattern
        front, _ = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front'},
        )
        back, _ = ProductPattern.objects.get_or_create(
            code='back', defaults={'name': 'Back'},
        )
        # Same (size_m, red) but different patterns — should collapse to ONE batch.
        adda, cr = self._build_adda_with_bundles([
            ('m', red, front, 10),
            ('m', red, back, 20),
        ])
        generate_for_cutting(cr)

        batches = list(BarcodeBatch.objects.filter(adda=adda))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 30)
        self.assertEqual(batches[0].start_seq, 1)
        self.assertEqual(batches[0].end_seq, 30)
        self.assertEqual(batches[0].color_id, red.id)

    def test_contiguous_ranges_across_multiple_color_size_combos(self):
        red = ClothColor.objects.get(name='Red')
        blue = ClothColor.objects.exclude(pk=red.pk).first()
        if not blue:
            self.skipTest("Need second color")
        from production.models import ProductPattern
        front, _ = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front'},
        )

        adda, cr = self._build_adda_with_bundles([
            ('s', red, front, 60),
            ('s', blue, front, 50),
            ('l', red, front, 40),
        ])
        generate_for_cutting(cr)

        batches = list(
            BarcodeBatch.objects.filter(adda=adda).order_by('start_seq')
        )
        self.assertEqual(len(batches), 3)
        # First batch starts at 1, then contiguous
        self.assertEqual(batches[0].start_seq, 1)
        self.assertEqual(batches[0].end_seq, batches[0].start_seq + batches[0].total_pieces - 1)
        self.assertEqual(batches[1].start_seq, batches[0].end_seq + 1)
        self.assertEqual(batches[2].start_seq, batches[1].end_seq + 1)
        # Total pieces = 150
        total = sum(b.total_pieces for b in batches)
        self.assertEqual(total, 150)
