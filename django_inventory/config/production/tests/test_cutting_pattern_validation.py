"""Tests for the upgraded Cutting Pattern stage validation (PR2).

YEH FILE KYU HAI?
─────────────────
Cutting Pattern stage ko spec-compliant banaya: verify per-pattern
(CuttingPatternVerification) + size proportions lock
(CuttingPatternSizeAllocation). complete_pattern_stage 3 naye validation
rules enforce karta hai:
  • saari ProductPatternAssignment rows verified
  • ≥1 size allocation row
  • allocation sum == 100

Test coverage:
  • verify_pattern create + idempotent re-verify
  • verify_pattern rejects cross-product assignment
  • unverify_pattern deletes row (toggle off)
  • set_size_allocation full-replace
  • set_size_allocation rejects size not on product
  • set_size_allocation rejects duplicate sizes
  • complete_pattern_stage refuses unverified assignments
  • complete_pattern_stage refuses zero allocations
  • complete_pattern_stage refuses non-100 sum
  • complete_pattern_stage happy path (verified + sum=100 + ≥1 photo)
"""
from io import BytesIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import STAGE_CUTTING_PATTERN
from production.models import (
    Adda, AddaStageRecord, CuttingPatternRecord, CuttingPatternSizeAllocation,
    CuttingPatternVerification, Product, ProductPattern,
    ProductPatternAssignment, ProductSize, Stage, WorkflowStage,
)
from production.services import (
    attach_pattern_photo, complete_pattern_stage, create_adda,
    set_size_allocation, unverify_pattern, verify_pattern,
)


def _user(email, *, role_code='super_admin', is_super=True, skills=()):
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(
        email=email, password='x',
        is_superuser=is_super, is_staff=is_super,
    )
    u.role = role
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


def _png_upload(name='p.png') -> SimpleUploadedFile:
    """1x1 PNG as multipart upload — keeps Pillow happy."""
    buf = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


class CuttingPatternFixture(TestCase):
    """Common setup — T-SHIRT product with patterns + sizes + adda at pattern stage."""

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.get(code='T-SHIRT')
        # Ensure cutting_pattern is in the product's workflow (default seed
        # only attaches layering + cutting). Insert between them at order=2.
        cp_stage = Stage.objects.get(code='cutting_pattern')
        # Bump existing stages at order>=2 to make room for cutting_pattern at 2.
        WorkflowStage.objects.filter(
            product=cls.product, order__gte=2,
        ).update(order=99)  # tmp to avoid unique conflict
        cls.pattern_wf, created = WorkflowStage.objects.get_or_create(
            product=cls.product, stage=cp_stage,
            defaults={'order': 2},
        )
        if not created:
            cls.pattern_wf.order = 2
            cls.pattern_wf.save(update_fields=['order'])
        # Re-shift the bumped ones back to 3+
        bumped = WorkflowStage.objects.filter(
            product=cls.product, order=99,
        ).order_by('id')
        for i, ws in enumerate(bumped):
            ws.order = 3 + i
            ws.save(update_fields=['order'])

        # Wipe + seed patterns for this product (idempotent for re-run).
        ProductPatternAssignment.objects.filter(product=cls.product).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front Panel'},
        )[0]
        cls.back = ProductPattern.objects.get_or_create(
            code='back', defaults={'name': 'Back Panel'},
        )[0]
        cls.sleeve = ProductPattern.objects.get_or_create(
            code='sleeve', defaults={'name': 'Sleeve'},
        )[0]
        cls.a_front = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.front, pieces_count=1,
        )
        cls.a_back = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.back, pieces_count=1,
        )
        cls.a_sleeve = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.sleeve, pieces_count=2,
        )

        # Sizes for this product
        cls.s = ProductSize.objects.create(
            product=cls.product, code='s', label='Small', display_order=1,
        )
        cls.m = ProductSize.objects.create(
            product=cls.product, code='m', label='Medium', display_order=2,
        )
        cls.l = ProductSize.objects.create(
            product=cls.product, code='l', label='Large', display_order=3,
        )

    def setUp(self):
        # admin needs cutting_master skill for create_adda's pool check.
        self.admin = _user(
            f'admin{id(self)}@cp.test',
            skills=['cutting_master', 'cutting_master_helper'],
        )
        self.adda = create_adda(self.admin, product=self.product)
        # Force-advance adda to cutting_pattern stage (bypass layering completion).
        self.adda.current_stage = self.pattern_wf
        self.adda.save(update_fields=['current_stage'])
        # Bootstrap an AddaStageRecord + CuttingPatternRecord.
        from django.utils import timezone
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(),
        )
        self.record = CuttingPatternRecord.objects.create(stage_record=self.sr)


class VerifyPatternTests(CuttingPatternFixture):
    def test_creates_verification_row(self):
        v = verify_pattern(
            record=self.record, assignment=self.a_front, user=self.admin,
        )
        self.assertEqual(v.assignment, self.a_front)
        self.assertEqual(v.verified_by, self.admin)
        self.assertEqual(self.record.verifications.count(), 1)

    def test_idempotent_re_verify_updates_note(self):
        verify_pattern(
            record=self.record, assignment=self.a_front,
            note='first', user=self.admin,
        )
        verify_pattern(
            record=self.record, assignment=self.a_front,
            note='second', user=self.admin,
        )
        self.assertEqual(self.record.verifications.count(), 1)
        self.assertEqual(
            self.record.verifications.first().note, 'second',
        )

    def test_rejects_cross_product_assignment(self):
        other_product = Product.objects.exclude(pk=self.product.pk).first()
        if not other_product:
            self.skipTest("Need a second product for cross-product test.")
        other_pattern, _ = ProductPattern.objects.get_or_create(
            code='collar', defaults={'name': 'Collar'},
        )
        other_assignment = ProductPatternAssignment.objects.create(
            product=other_product, pattern=other_pattern, pieces_count=1,
        )
        with self.assertRaises(ValidationError):
            verify_pattern(
                record=self.record, assignment=other_assignment,
                user=self.admin,
            )

    def test_locks_after_stage_completed(self):
        # Manually mark stage_record completed
        from django.utils import timezone
        self.sr.completed_at = timezone.now()
        self.sr.completed_by = self.admin
        self.sr.save(update_fields=['completed_at', 'completed_by'])
        with self.assertRaises(ValidationError):
            verify_pattern(
                record=self.record, assignment=self.a_front, user=self.admin,
            )


class UnverifyPatternTests(CuttingPatternFixture):
    def test_deletes_row(self):
        verify_pattern(
            record=self.record, assignment=self.a_front, user=self.admin,
        )
        self.assertEqual(self.record.verifications.count(), 1)
        unverify_pattern(
            record=self.record, assignment=self.a_front, user=self.admin,
        )
        self.assertEqual(self.record.verifications.count(), 0)

    def test_noop_when_absent(self):
        # No prior verification — should silently succeed.
        unverify_pattern(
            record=self.record, assignment=self.a_front, user=self.admin,
        )
        self.assertEqual(self.record.verifications.count(), 0)


class SetSizeAllocationTests(CuttingPatternFixture):
    def test_full_replace_creates_rows(self):
        set_size_allocation(
            record=self.record,
            allocations=[
                {'size_id': self.s.id, 'proportion_pct': 30},
                {'size_id': self.m.id, 'proportion_pct': 50},
                {'size_id': self.l.id, 'proportion_pct': 20},
            ],
            user=self.admin,
        )
        rows = list(self.record.size_allocations.order_by('size__display_order'))
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(r.proportion_pct for r in rows), 100)

    def test_replace_wipes_previous(self):
        set_size_allocation(
            record=self.record,
            allocations=[{'size_id': self.s.id, 'proportion_pct': 100}],
            user=self.admin,
        )
        set_size_allocation(
            record=self.record,
            allocations=[{'size_id': self.m.id, 'proportion_pct': 60}],
            user=self.admin,
        )
        rows = list(self.record.size_allocations.all())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].size, self.m)
        self.assertEqual(rows[0].proportion_pct, 60)

    def test_rejects_size_not_on_product(self):
        # Make a size on a different product
        other_product = Product.objects.exclude(pk=self.product.pk).first()
        if not other_product:
            self.skipTest("Need a second product for cross-product test.")
        foreign = ProductSize.objects.create(
            product=other_product, code='xxl', label='Foreign',
        )
        with self.assertRaises(ValidationError):
            set_size_allocation(
                record=self.record,
                allocations=[{'size_id': foreign.id, 'proportion_pct': 50}],
                user=self.admin,
            )

    def test_rejects_duplicate_sizes(self):
        with self.assertRaises(ValidationError):
            set_size_allocation(
                record=self.record,
                allocations=[
                    {'size_id': self.s.id, 'proportion_pct': 40},
                    {'size_id': self.s.id, 'proportion_pct': 60},
                ],
                user=self.admin,
            )

    def test_rejects_pct_over_100(self):
        with self.assertRaises(ValidationError):
            set_size_allocation(
                record=self.record,
                allocations=[{'size_id': self.s.id, 'proportion_pct': 150}],
                user=self.admin,
            )


class CompletePatternStageValidationTests(CuttingPatternFixture):
    def _attach_photo(self):
        # Need at least one photo for any complete attempt (existing rule).
        attach_pattern_photo(
            stage_record=self.sr, uploaded_image=_png_upload(),
            caption='proof', user=self.admin,
        )

    def _verify_all(self):
        verify_pattern(record=self.record, assignment=self.a_front, user=self.admin)
        verify_pattern(record=self.record, assignment=self.a_back, user=self.admin)
        verify_pattern(record=self.record, assignment=self.a_sleeve, user=self.admin)

    def _lock_sizes_100(self):
        set_size_allocation(
            record=self.record,
            allocations=[
                {'size_id': self.s.id, 'proportion_pct': 30},
                {'size_id': self.m.id, 'proportion_pct': 50},
                {'size_id': self.l.id, 'proportion_pct': 20},
            ],
            user=self.admin,
        )

    def test_refuses_when_no_verifications(self):
        self._attach_photo()
        self._lock_sizes_100()
        with self.assertRaisesMessage(ValidationError, 'verified'):
            complete_pattern_stage(adda=self.adda, user=self.admin)

    def test_refuses_when_partial_verifications(self):
        self._attach_photo()
        self._lock_sizes_100()
        verify_pattern(record=self.record, assignment=self.a_front, user=self.admin)
        # only 1 of 3 — refuse
        with self.assertRaisesMessage(ValidationError, '1 of 3'):
            complete_pattern_stage(adda=self.adda, user=self.admin)

    def test_refuses_when_no_size_allocations(self):
        self._attach_photo()
        self._verify_all()
        with self.assertRaisesMessage(ValidationError, 'size'):
            complete_pattern_stage(adda=self.adda, user=self.admin)

    def test_refuses_when_allocation_sum_not_100(self):
        self._attach_photo()
        self._verify_all()
        set_size_allocation(
            record=self.record,
            allocations=[
                {'size_id': self.s.id, 'proportion_pct': 40},
                {'size_id': self.m.id, 'proportion_pct': 40},
            ],
            user=self.admin,
        )
        with self.assertRaisesMessage(ValidationError, '80%'):
            complete_pattern_stage(adda=self.adda, user=self.admin)

    def test_happy_path_advances_stage(self):
        self._attach_photo()
        self._verify_all()
        self._lock_sizes_100()
        complete_pattern_stage(adda=self.adda, user=self.admin)
        self.sr.refresh_from_db()
        self.assertIsNotNone(self.sr.completed_at)
        self.assertEqual(self.sr.completed_by, self.admin)
        # Adda should have advanced to next stage (cutting) or completed
        self.adda.refresh_from_db()
        self.assertNotEqual(self.adda.current_stage.stage.code, STAGE_CUTTING_PATTERN)
