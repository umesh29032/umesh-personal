"""Tests for unified stage tracking (PR-2) — AddaHistory event wiring.

Verifies the new ChangeType events get logged with stage_record + metadata:
WORKERS_ASSIGNED (create_adda + start_*), COST_FROZEN (advance).
"""
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product
from production.services import advance_to_next_stage, create_adda
from tracking.models import AddaHistory


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='track@adda.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class UnifiedTrackingTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='NIKKAR')   # layering -> cutting

    def _types(self, adda):
        return set(
            AddaHistory.objects.filter(adda=adda).values_list('change_type', flat=True)
        )

    def test_create_adda_logs_workers_assigned(self):
        adda = create_adda(self.user, product=self.product)
        types = self._types(adda)
        self.assertIn('created', types)
        self.assertIn('workers_assigned', types)
        wa = AddaHistory.objects.get(adda=adda, change_type='workers_assigned')
        self.assertIsNotNone(wa.stage_record)              # bound to execution row
        self.assertIn('worker_ids', wa.metadata)           # payload carried

    def test_add_bundle_item_logs_bundle_created(self):
        # Regression for the audit's P3: the lazy-create path (add_bundle_item)
        # must also log BUNDLE_CREATED, not just create_bundle.
        from production.models import ProductSize, ProductPattern, ProductPatternAssignment
        from production.services import add_bundle_item
        from raw_materials.models import ClothColor
        adda = create_adda(self.user, product=self.product)
        cutting_wf = self.product.workflow_stages.get(stage__code='cutting')
        adda.current_stage = cutting_wf            # add_bundle_item requires being at cutting
        adda.save(update_fields=['current_stage'])
        size = ProductSize.objects.create(product=self.product, code='m', label='M')
        pat, _ = ProductPattern.objects.get_or_create(code='bc-test', defaults={'name': 'Front'})
        ProductPatternAssignment.objects.get_or_create(
            product=self.product, pattern=pat, defaults={'pieces_count': 1})
        color, _ = ClothColor.objects.get_or_create(name='Red')
        add_bundle_item(adda=adda, size_id=size.id, pattern_id=pat.id,
                        color_id=color.id, count=10, user=self.user)
        self.assertTrue(
            AddaHistory.objects.filter(adda=adda, change_type='bundle_created').exists())

    def test_advance_logs_cost_frozen_and_stage_advanced(self):
        adda = create_adda(self.user, product=self.product)
        advance_to_next_stage(adda, self.user)
        types = self._types(adda)
        self.assertIn('cost_frozen', types)
        self.assertIn('stage_advanced', types)
        cf = AddaHistory.objects.filter(adda=adda, change_type='cost_frozen').first()
        self.assertIsNotNone(cf.stage_record)
        # unpriced stage -> metadata cost is None (honest), not 0
        self.assertIsNone(cf.metadata.get('cost'))
