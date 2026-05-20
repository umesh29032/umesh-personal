"""Tests for production adda_service: per-product counter atomicity.

Phase 4: create_adda now requires at least one user with cutting_master or
cutting_master_helper skill. `_superuser()` therefore seeds that skill.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Adda, Product
from production.services import advance_to_next_stage, create_adda


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='admin@adda.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    # Phase 4: seed cutting_master skill so create_adda passes the skilled-pool check
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class CreateAddaTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='T-SHIRT')

    def test_first_adda_starts_at_001(self):
        a = create_adda(self.user, product=self.product)
        self.assertEqual(a.code, 'T-SHIRT-001')

    def test_counter_increments_per_product(self):
        a1 = create_adda(self.user, product=self.product)
        a2 = create_adda(self.user, product=self.product)
        a3 = create_adda(self.user, product=self.product)
        self.assertEqual(a1.code, 'T-SHIRT-001')
        self.assertEqual(a2.code, 'T-SHIRT-002')
        self.assertEqual(a3.code, 'T-SHIRT-003')

    def test_counter_is_per_product(self):
        ts = create_adda(self.user, product=self.product)
        nikkar = Product.objects.get(code='NIKKAR')
        nk = create_adda(self.user, product=nikkar)
        self.assertEqual(ts.code, 'T-SHIRT-001')
        self.assertEqual(nk.code, 'NIKKAR-001')

    def test_archived_product_is_rejected(self):
        self.product.is_active = False
        self.product.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            create_adda(self.user, product=self.product)


class AdvanceStageTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='NIKKAR')

    def test_advance_marks_completed_at_end(self):
        adda = create_adda(self.user, product=self.product)
        advance_to_next_stage(adda, self.user)
        adda.refresh_from_db()
        self.assertEqual(adda.current_stage.stage_type, 'cutting')
        advance_to_next_stage(adda, self.user)
        adda.refresh_from_db()
        self.assertEqual(adda.status, Adda.Status.COMPLETED)
        self.assertIsNone(adda.current_stage)
