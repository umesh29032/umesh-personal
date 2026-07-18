"""Invariant tests for denormalized counters — audit follow-up 2026-05-29.

YEH FILE KYU HAI?
─────────────────
`CuttingBundle.total_pieces` aur `CuttingPieceBreakup.consumed_count`
denormalized hain — service recompute karta hai, koi DB trigger nahi.
Agar koi future PR service ko bypass kare ya recompute call bhool jaaye,
in counters mein drift ho jaayega.

Yeh test suite har mutation path ke baad invariant verify karta hai:
  • bundle.total_pieces  ==  SUM(items.count) for that bundle
  • breakup.consumed_count == SUM(item.count where item.source_breakup=breakup)

Tests pass = denormalised state DB-derived state ke equal hai.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import STAGE_CUTTING, STAGE_LAYERING
from production.models import (
    AddaStageRecord, CuttingBundle, CuttingBundleItem, CuttingPatternRecord, CuttingPatternSizeAllocation,
    CuttingPieceBreakup, Product, ProductPattern, ProductPatternAssignment,
    ProductSize, Stage, WorkflowStage, LayeringRecord,
)
from production.services import (
    add_item_to_bundle, add_pieces_to_bundle, create_adda, create_bundle,
    delete_bundle, delete_bundle_item, start_cutting, upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _admin(email):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(
        email=email, password='x', is_superuser=True, is_staff=True,
    )
    u.role = role
    u.save()
    for s in ('cutting_master', 'cutting_master_helper'):
        u.skills.add(Skill.objects.get(name=s))
    return u


def _bundle_invariant_holds(bundle: CuttingBundle) -> bool:
    """bundle.total_pieces equals SUM(items.count)?"""
    actual = sum(it.count for it in bundle.items.all())
    return bundle.total_pieces == actual


def _breakup_invariant_holds(breakup: CuttingPieceBreakup) -> bool:
    """breakup.consumed_count equals SUM(item.count where source=this)?"""
    actual = sum(
        it.count for it in
        CuttingBundleItem.objects.filter(source_breakup=breakup)
    )
    return breakup.consumed_count == actual


class CounterInvariantFixture(TestCase):
    """Build an Adda at cutting stage with 3 breakup rows ready to consume."""

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.get(code='T-SHIRT')

        # Ensure cutting_pattern WorkflowStage at order=2 (mirrors test_cutting_workflow).
        cp_stage = Stage.objects.get(code='cutting_pattern')
        WorkflowStage.objects.filter(product=cls.product, order__gte=2).update(order=99)
        cls.pattern_wf, _ = WorkflowStage.objects.get_or_create(
            product=cls.product, stage=cp_stage, defaults={'order': 2},
        )
        cls.pattern_wf.order = 2
        cls.pattern_wf.save(update_fields=['order'])
        for i, ws in enumerate(WorkflowStage.objects.filter(
            product=cls.product, order=99,
        ).order_by('id')):
            ws.order = 3 + i
            ws.save(update_fields=['order'])

        cls.layering_wf = WorkflowStage.objects.get(
            product=cls.product, stage__code=STAGE_LAYERING,
        )
        cls.cutting_wf = WorkflowStage.objects.get(
            product=cls.product, stage__code=STAGE_CUTTING,
        )

        # Patterns + Assignments (1 Front + 1 Back).
        ProductPatternAssignment.objects.filter(product=cls.product).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front Panel'},
        )[0]
        cls.back = ProductPattern.objects.get_or_create(
            code='back', defaults={'name': 'Back Panel'},
        )[0]
        ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.front, pieces_count=1,
        )
        ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.back, pieces_count=1,
        )

        # Sizes
        cls.s_m = ProductSize.objects.create(
            product=cls.product, code='m', label='Medium', display_order=1,
        )
        cls.s_l = ProductSize.objects.create(
            product=cls.product, code='l', label='Large', display_order=2,
        )

    def setUp(self):
        self.admin = _admin(f'inv{id(self)}@inv.test')
        cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        self.rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': self.red, 'qty': 2}],
        )
        self.adda = create_adda(self.admin, product=self.product)

        # Complete Layering manually
        layering_sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage=self.layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = self.admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        layering_record = LayeringRecord.objects.create(
            stage_record=layering_sr, lay_count=10, total_colors=1,
            duration_minutes=30, layer_length_meters=Decimal('2.0'),
        )
        layering_record.rolls_used.set(self.rolls)

        # Complete Cutting Pattern with full size allocation
        pattern_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(), completed_at=timezone.now(),
            completed_by=self.admin,
        )
        record = CuttingPatternRecord.objects.create(stage_record=pattern_sr)
        CuttingPatternSizeAllocation.objects.create(
            record=record, size=self.s_m, proportion_pct=60,
        )
        CuttingPatternSizeAllocation.objects.create(
            record=record, size=self.s_l, proportion_pct=40,
        )

        # Advance adda to cutting
        self.adda.current_stage = self.cutting_wf
        self.adda.save(update_fields=['current_stage'])

        # Start cutting stage + create breakup rows.
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.b_front_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        self.b_back_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.back.id, count=20, user=self.admin,
        )
        self.b_front_l = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.front.id, count=15, user=self.admin,
        )
        # GAP-5: bundling is POST-JOIN — stamp the cutting lane complete.
        from production.models import CuttingRecord as _CR
        for sr in AddaStageRecord.objects.filter(
                adda=self.adda, workflow_stage=self.cutting_wf,
                completed_at__isnull=True):
            _CR.objects.get_or_create(stage_record=sr,
                                      defaults={'pieces_cut': 0})
            sr.completed_at = timezone.now()
            sr.completed_by = self.admin
            sr.save(update_fields=['completed_at', 'completed_by'])


class BundleTotalPiecesInvariantTests(CounterInvariantFixture):
    """CuttingBundle.total_pieces == SUM(items.count) holds across mutations."""

    def test_empty_bundle_is_zero(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        bundle.refresh_from_db()
        self.assertEqual(bundle.total_pieces, 0)
        self.assertTrue(_bundle_invariant_holds(bundle))

    def test_after_add_pieces(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[
                {'breakup_id': self.b_front_m.id, 'take_count': 10},
                {'breakup_id': self.b_back_m.id, 'take_count': 8},
            ],
            user=self.admin,
        )
        bundle.refresh_from_db()
        self.assertEqual(bundle.total_pieces, 18)
        self.assertTrue(_bundle_invariant_holds(bundle))

    def test_after_incremental_add(self):
        """Same breakup pe phir add — count badhe, invariant tooto na."""
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': self.b_front_m.id, 'take_count': 5}],
            user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': self.b_front_m.id, 'take_count': 3}],
            user=self.admin,
        )
        bundle.refresh_from_db()
        self.assertEqual(bundle.total_pieces, 8)
        self.assertTrue(_bundle_invariant_holds(bundle))

    def test_after_delete_item(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[
                {'breakup_id': self.b_front_m.id, 'take_count': 10},
                {'breakup_id': self.b_back_m.id, 'take_count': 7},
            ],
            user=self.admin,
        )
        bundle.refresh_from_db()
        front_item = bundle.items.get(pattern=self.front)
        delete_bundle_item(adda=self.adda, item_id=front_item.id, user=self.admin)
        bundle.refresh_from_db()
        # Front item gone → only back item's 7 remain.
        self.assertEqual(bundle.total_pieces, 7)
        self.assertTrue(_bundle_invariant_holds(bundle))


class BreakupConsumedCountInvariantTests(CounterInvariantFixture):
    """CuttingPieceBreakup.consumed_count == SUM(items where source=row)."""

    def test_initial_zero(self):
        self.b_front_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 0)
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))

    def test_after_add_pieces(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': self.b_front_m.id, 'take_count': 12}],
            user=self.admin,
        )
        self.b_front_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 12)
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))

    def test_after_delete_item_restores(self):
        """Item delete → consumed_count wapas zero."""
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': self.b_front_m.id, 'take_count': 12}],
            user=self.admin,
        )
        item = CuttingBundleItem.objects.get(
            bundle=bundle, source_breakup=self.b_front_m,
        )
        delete_bundle_item(adda=self.adda, item_id=item.id, user=self.admin)
        self.b_front_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 0)
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))

    def test_after_delete_bundle_restores_all(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[
                {'breakup_id': self.b_front_m.id, 'take_count': 10},
                {'breakup_id': self.b_back_m.id, 'take_count': 8},
            ],
            user=self.admin,
        )
        delete_bundle(adda=self.adda, bundle_id=bundle.id, user=self.admin)
        self.b_front_m.refresh_from_db()
        self.b_back_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 0)
        self.assertEqual(self.b_back_m.consumed_count, 0)
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))
        self.assertTrue(_breakup_invariant_holds(self.b_back_m))

    def test_manual_add_resyncs_source_consumed_count(self):
        """Regression: add_item_to_bundle overwriting a SOURCED item's count must
        re-sync that breakup's consumed_count. Before the fix the counter stayed
        stale (drift), so consumed_count could diverge from actual cut pieces."""
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': self.b_front_m.id, 'take_count': 12}],
            user=self.admin,
        )
        self.b_front_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 12)
        # Manual add lands on the same (bundle, front, red) row → count overwritten.
        add_item_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            pattern_id=self.front.id, color_id=self.red.id, count=5, user=self.admin,
        )
        self.b_front_m.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 5)   # re-synced, not stale 12
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))

    def test_multiple_breakups_independent(self):
        """Front + back consumed counts track independently."""
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[
                {'breakup_id': self.b_front_m.id, 'take_count': 9},
                {'breakup_id': self.b_back_m.id, 'take_count': 11},
            ],
            user=self.admin,
        )
        self.b_front_m.refresh_from_db()
        self.b_back_m.refresh_from_db()
        self.b_front_l.refresh_from_db()
        self.assertEqual(self.b_front_m.consumed_count, 9)
        self.assertEqual(self.b_back_m.consumed_count, 11)
        # Unused breakup unchanged.
        self.assertEqual(self.b_front_l.consumed_count, 0)
        self.assertTrue(_breakup_invariant_holds(self.b_front_m))
        self.assertTrue(_breakup_invariant_holds(self.b_back_m))
        self.assertTrue(_breakup_invariant_holds(self.b_front_l))
