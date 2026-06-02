"""Tests for PR-3: set_stage_cost (R1 mandatory rate) + R3 grouping guards."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import CostMethod, Product, Stage
from production.services import (
    add_stage_to_product_flow, remove_stage_from_product_flow, set_stage_cost,
)


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='flowcost@adda.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class SetStageCostTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.product = Product.objects.get(code='NIKKAR')   # layering(1) -> cutting(2)
        self.layering = self.product.workflow_stages.get(order=1)
        self.cutting = self.product.workflow_stages.get(order=2)

    def test_self_paid_sets_method_and_rate(self):
        set_stage_cost(user=self.user, workflow_stage=self.cutting,
                       cost_method=CostMethod.PER_PIECE, cost_rate='2.50')
        self.cutting.refresh_from_db()
        self.assertEqual(self.cutting.cost_method, 'per_piece')
        self.assertEqual(self.cutting.cost_rate, Decimal('2.5000'))
        self.assertIsNone(self.cutting.cost_billed_at_id)

    def test_rate_required_for_self_paid(self):
        with self.assertRaises(ValidationError):
            set_stage_cost(user=self.user, workflow_stage=self.cutting,
                           cost_method=CostMethod.PER_PIECE, cost_rate=None)

    def test_rate_must_be_positive(self):
        with self.assertRaises(ValidationError):
            set_stage_cost(user=self.user, workflow_stage=self.cutting,
                           cost_method=CostMethod.PER_PIECE, cost_rate='0')

    def test_group_member_bills_at_later_priced_payer(self):
        # Price the payer (cutting) first.
        set_stage_cost(user=self.user, workflow_stage=self.cutting,
                       cost_method=CostMethod.PER_PIECE, cost_rate='2')
        # Group layering -> cutting.
        set_stage_cost(user=self.user, workflow_stage=self.layering,
                       cost_method=CostMethod.PER_LAYER, cost_rate='',
                       cost_billed_at_id=self.cutting.pk)
        self.layering.refresh_from_db()
        self.assertEqual(self.layering.cost_billed_at_id, self.cutting.pk)
        self.assertIsNone(self.layering.cost_rate)   # member rate nulled

    def test_cannot_bill_at_earlier_stage(self):
        set_stage_cost(user=self.user, workflow_stage=self.layering,
                       cost_method=CostMethod.PER_LAYER, cost_rate='1')
        with self.assertRaises(ValidationError):
            set_stage_cost(user=self.user, workflow_stage=self.cutting,
                           cost_method=CostMethod.PER_PIECE, cost_rate='',
                           cost_billed_at_id=self.layering.pk)

    def test_payer_must_be_priced(self):
        # cutting left unpriced -> grouping layering at it must fail
        with self.assertRaises(ValidationError):
            set_stage_cost(user=self.user, workflow_stage=self.layering,
                           cost_method=CostMethod.PER_LAYER, cost_rate='',
                           cost_billed_at_id=self.cutting.pk)

    def test_remove_payer_with_members_blocked(self):
        set_stage_cost(user=self.user, workflow_stage=self.cutting,
                       cost_method=CostMethod.PER_PIECE, cost_rate='2')
        set_stage_cost(user=self.user, workflow_stage=self.layering,
                       cost_method=CostMethod.PER_LAYER, cost_rate='',
                       cost_billed_at_id=self.cutting.pk)
        with self.assertRaises(ValidationError):
            remove_stage_from_product_flow(user=self.user, workflow_stage=self.cutting)

    def test_add_stage_seeds_default_cost(self):
        cp_stage = Stage.objects.get(code='cutting_pattern')
        cp_stage.default_cost_method = CostMethod.FIXED
        cp_stage.default_cost_rate = Decimal('5')
        cp_stage.save(update_fields=['default_cost_method', 'default_cost_rate'])
        ws = add_stage_to_product_flow(user=self.user, product=self.product, stage=cp_stage)
        self.assertEqual(ws.cost_method, 'fixed_cost')
        self.assertEqual(ws.cost_rate, Decimal('5.0000'))
