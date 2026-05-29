"""Form clean-method tests — audit follow-up 2026-05-29.

YEH FILE KYU HAI?
─────────────────
Audit gap: PatternVerifyForm + SizeAllocationForm clean methods had no test
coverage. These forms guard the FK boundary between POST data and service
layer — cross-product / cross-record IDs must reject here.

Coverage:
  • PatternVerifyForm valid assignment + photo
  • PatternVerifyForm rejects cross-product assignment_id
  • PatternVerifyForm rejects cross-record photo_id
  • PatternVerifyForm OK with no photo
  • SizeAllocationForm valid size + proportion
  • SizeAllocationForm rejects cross-product size_id
  • SizeAllocationForm rejects proportion out of range
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import STAGE_LAYERING
from production.forms import PatternVerifyForm, SizeAllocationForm
from production.models import (
    Adda, AddaStageRecord, CuttingPatternPhoto, CuttingPatternRecord,
    LayeringRecord, Product, ProductPattern, ProductPatternAssignment,
    ProductSize, Stage, WorkflowStage,
)
from production.services import create_adda
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _admin(email='admin@form.test'):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(
        email=email, password='x', is_superuser=True, is_staff=True,
    )
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class _FormFixture(TestCase):
    """Shared fixture: two products (TSHIRT, NIKKAR), each with one Adda at
    cutting_pattern stage and one CuttingPatternRecord ready for form clean."""

    @classmethod
    def setUpTestData(cls):
        cls.tshirt = Product.objects.get(code='T-SHIRT')
        cls.nikkar = Product.objects.get(code='NIKKAR')

        # Ensure cutting_pattern WorkflowStage attached to T-SHIRT at order=2.
        cp_stage = Stage.objects.get(code='cutting_pattern')
        WorkflowStage.objects.filter(product=cls.tshirt, order__gte=2).update(order=99)
        cls.pattern_wf, _ = WorkflowStage.objects.get_or_create(
            product=cls.tshirt, stage=cp_stage, defaults={'order': 2},
        )
        cls.pattern_wf.order = 2
        cls.pattern_wf.save(update_fields=['order'])
        for i, ws in enumerate(WorkflowStage.objects.filter(
            product=cls.tshirt, order=99,
        ).order_by('id')):
            ws.order = 3 + i
            ws.save(update_fields=['order'])

        cls.layering_wf = WorkflowStage.objects.get(
            product=cls.tshirt, stage__code=STAGE_LAYERING,
        )

        # Patterns + assignments — on T-SHIRT only.
        ProductPatternAssignment.objects.filter(product=cls.tshirt).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front Panel'},
        )[0]
        cls.a_front_tshirt = ProductPatternAssignment.objects.create(
            product=cls.tshirt, pattern=cls.front, pieces_count=1,
        )
        # Cross-product control: same pattern, different product.
        cls.a_front_nikkar = ProductPatternAssignment.objects.create(
            product=cls.nikkar, pattern=cls.front, pieces_count=1,
        )

        # Sizes — one per product (for cross-product test).
        cls.size_tshirt = ProductSize.objects.create(
            product=cls.tshirt, code='m', label='Medium', display_order=1,
        )
        cls.size_nikkar = ProductSize.objects.create(
            product=cls.nikkar, code='28', label='28', display_order=1,
        )

    def setUp(self):
        self.admin = _admin(f'admin{id(self)}@form.test')
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': red, 'qty': 1}],
        )
        # T-SHIRT Adda, advance to cutting_pattern stage manually.
        self.adda = create_adda(self.admin, product=self.tshirt)
        # Complete layering manually.
        layering_sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage=self.layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = self.admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        lr = LayeringRecord.objects.create(
            stage_record=layering_sr, lay_count=5, total_colors=1,
            duration_minutes=20, layer_length_meters=Decimal('1.5'),
        )
        lr.rolls_used.set(rolls)
        # Advance to pattern stage + create record.
        self.adda.current_stage = self.pattern_wf
        self.adda.save(update_fields=['current_stage'])
        self.pattern_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(),
        )
        self.record = CuttingPatternRecord.objects.create(stage_record=self.pattern_sr)


class PatternVerifyFormCleanTests(_FormFixture):

    def test_valid_assignment_no_photo(self):
        form = PatternVerifyForm(
            {'assignment_id': self.a_front_tshirt.id},
            record=self.record,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['assignment'], self.a_front_tshirt)
        self.assertIsNone(form.cleaned_data.get('photo'))

    def test_rejects_cross_product_assignment(self):
        """assignment_id from NIKKAR product → reject (record is on T-SHIRT)."""
        form = PatternVerifyForm(
            {'assignment_id': self.a_front_nikkar.id},
            record=self.record,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('assignment_id', form.errors)

    def test_rejects_missing_assignment(self):
        form = PatternVerifyForm({}, record=self.record)
        self.assertFalse(form.is_valid())

    def test_valid_with_attached_photo(self):
        photo = CuttingPatternPhoto.objects.create(
            record=self.record, image='photos/test.jpg', uploaded_by=self.admin,
        )
        form = PatternVerifyForm(
            {'assignment_id': self.a_front_tshirt.id, 'photo_id': photo.id},
            record=self.record,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['photo'], photo)

    def test_rejects_photo_from_other_record(self):
        """photo_id belongs to a different record → reject."""
        # Fresh Adda on same product → fresh pattern stage record + photo.
        other_adda = create_adda(self.admin, product=self.tshirt)
        other_sr = AddaStageRecord.objects.create(
            adda=other_adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(),
        )
        other_record = CuttingPatternRecord.objects.create(stage_record=other_sr)
        other_photo = CuttingPatternPhoto.objects.create(
            record=other_record, image='photos/other.jpg', uploaded_by=self.admin,
        )
        form = PatternVerifyForm(
            {
                'assignment_id': self.a_front_tshirt.id,
                'photo_id': other_photo.id,
            },
            record=self.record,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('photo_id', form.errors)

    def test_rejects_assignment_id_zero(self):
        form = PatternVerifyForm(
            {'assignment_id': 0}, record=self.record,
        )
        self.assertFalse(form.is_valid())

    def test_note_truncated_max_length(self):
        long_note = 'x' * 500
        form = PatternVerifyForm(
            {'assignment_id': self.a_front_tshirt.id, 'note': long_note},
            record=self.record,
        )
        # max_length=200 → invalid.
        self.assertFalse(form.is_valid())
        self.assertIn('note', form.errors)


class SizeAllocationFormCleanTests(_FormFixture):

    def test_valid_size_and_pct(self):
        form = SizeAllocationForm(
            {'size_id': self.size_tshirt.id, 'proportion_pct': 60},
            product=self.tshirt,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['size_id'], self.size_tshirt.id)
        self.assertEqual(form.cleaned_data['proportion_pct'], 60)

    def test_rejects_cross_product_size(self):
        """size_id from NIKKAR product → reject for T-SHIRT context."""
        form = SizeAllocationForm(
            {'size_id': self.size_nikkar.id, 'proportion_pct': 50},
            product=self.tshirt,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('size_id', form.errors)

    def test_rejects_proportion_negative(self):
        form = SizeAllocationForm(
            {'size_id': self.size_tshirt.id, 'proportion_pct': -1},
            product=self.tshirt,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('proportion_pct', form.errors)

    def test_rejects_proportion_over_100(self):
        form = SizeAllocationForm(
            {'size_id': self.size_tshirt.id, 'proportion_pct': 150},
            product=self.tshirt,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('proportion_pct', form.errors)

    def test_proportion_zero_allowed(self):
        """Mid-edit drafts can have a 0% row — completion enforces sum=100."""
        form = SizeAllocationForm(
            {'size_id': self.size_tshirt.id, 'proportion_pct': 0},
            product=self.tshirt,
        )
        self.assertTrue(form.is_valid(), form.errors)
