"""Tests for the manufacturing-cost freeze (PR-1 stage costing).

Covers cost_service.freeze_stage_cost wired into advance_to_next_stage:
priced/unpriced/fixed/per_layer freeze, grouping (billed-elsewhere -> 0.00),
rate-edit immutability, and clear_stage_cost (reopen).
"""
from decimal import Decimal

from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    AddaStageRecord, CostMethod, LayeringRecord, Product,
)
from production.services import advance_to_next_stage, clear_stage_cost, create_adda


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='cost@adda.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class FreezeStageCostTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='NIKKAR')   # workflow = [layering, cutting]

    def _new_adda_at_layering(self):
        adda = create_adda(self.user, product=self.product)
        layering_wf = adda.current_stage
        # Layering ships grouped-at-cutting (migration 0026 → priced-zero). These
        # are cost-ENGINE unit tests, so ungroup the stage first; each test sets
        # the grouping it wants (test_grouped_stage_freezes_zero re-groups it).
        if layering_wf.cost_billed_at_id is not None:
            layering_wf.cost_billed_at = None
            layering_wf.save(update_fields=['cost_billed_at'])
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=layering_wf)
        return adda, layering_wf, sr

    def test_fixed_cost_freezes_rate_on_advance(self):
        adda, wf, sr = self._new_adda_at_layering()
        wf.cost_method = CostMethod.FIXED
        wf.cost_rate = Decimal('50')
        wf.save(update_fields=['cost_method', 'cost_rate'])

        advance_to_next_stage(adda, self.user)
        sr.refresh_from_db()
        self.assertEqual(sr.processing_cost, Decimal('50.00'))
        self.assertEqual(sr.cost_method_snapshot, 'fixed_cost')
        self.assertIsNone(sr.cost_quantity_snapshot)   # fixed ignores quantity
        self.assertIsNotNone(sr.cost_frozen_at)

    def test_per_layer_uses_lay_count(self):
        adda, wf, sr = self._new_adda_at_layering()
        LayeringRecord.objects.create(
            stage_record=sr, lay_count=10, total_colors=1, duration_minutes=5,
        )
        wf.cost_method = CostMethod.PER_LAYER
        wf.cost_rate = Decimal('2')
        wf.save(update_fields=['cost_method', 'cost_rate'])

        advance_to_next_stage(adda, self.user)
        sr.refresh_from_db()
        self.assertEqual(sr.cost_quantity_snapshot, Decimal('10.00'))
        self.assertEqual(sr.processing_cost, Decimal('20.00'))

    def test_unpriced_freezes_null_not_zero(self):
        adda, wf, sr = self._new_adda_at_layering()
        # default cost_method=per_piece, cost_rate=None -> unpriced
        advance_to_next_stage(adda, self.user)
        sr.refresh_from_db()
        self.assertIsNone(sr.processing_cost)        # honest NULL, never 0
        self.assertIsNotNone(sr.cost_frozen_at)      # still stamped (audit)

    def test_grouped_stage_freezes_zero(self):
        adda, wf, sr = self._new_adda_at_layering()
        cutting_wf = adda.product.workflow_stages.get(stage__code='cutting')
        wf.cost_billed_at = cutting_wf      # layering billed at cutting
        wf.cost_method = CostMethod.FIXED
        wf.cost_rate = Decimal('50')
        wf.save(update_fields=['cost_billed_at', 'cost_method', 'cost_rate'])

        advance_to_next_stage(adda, self.user)
        sr.refresh_from_db()
        self.assertEqual(sr.processing_cost, Decimal('0.00'))   # priced-zero, NOT null
        self.assertIsNone(sr.cost_rate_snapshot)
        self.assertIsNotNone(sr.cost_frozen_at)

    def test_rate_edit_does_not_rewrite_frozen_cost(self):
        adda, wf, sr = self._new_adda_at_layering()
        wf.cost_method = CostMethod.FIXED
        wf.cost_rate = Decimal('50')
        wf.save(update_fields=['cost_method', 'cost_rate'])
        advance_to_next_stage(adda, self.user)

        wf.cost_rate = Decimal('99')        # edit the template rate AFTER freeze
        wf.save(update_fields=['cost_rate'])
        sr.refresh_from_db()
        self.assertEqual(sr.processing_cost, Decimal('50.00'))   # history unchanged

    def test_clear_stage_cost_wipes_snapshot(self):
        adda, wf, sr = self._new_adda_at_layering()
        wf.cost_method = CostMethod.FIXED
        wf.cost_rate = Decimal('50')
        wf.save(update_fields=['cost_method', 'cost_rate'])
        advance_to_next_stage(adda, self.user)

        sr.refresh_from_db()
        clear_stage_cost(sr)
        sr.refresh_from_db()
        self.assertIsNone(sr.processing_cost)
        self.assertIsNone(sr.cost_rate_snapshot)
        self.assertIsNone(sr.cost_frozen_at)
        self.assertEqual(sr.cost_method_snapshot, '')
