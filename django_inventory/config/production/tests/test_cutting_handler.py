"""M2.4: CuttingHandler adapter parity.

Registered + pays_workers True; panel_context delegates to the cutting snapshot;
complete() delegates to complete_cutting_from_bundles (proven via patch to avoid
cutting's heavy bundle/breakdown setup — the delegation pattern itself is already
exercised end-to-end by the layering/pattern handler tests).
"""
from unittest.mock import patch

from django.test import TestCase

from accounts.models import Skill, User
from production.constants import STAGE_CUTTING
from production.models import Product, Stage, WorkflowStage
from production.services import create_adda, get_cutting_snapshot
from production.stages import base
from production.stages.cutting.handler import CuttingHandler


class CuttingHandlerParityTest(TestCase):
    def setUp(self):
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='CUTHAND', name='Cutting Handler Test')
        self.wf = WorkflowStage.objects.create(product=self.product, stage=cut, order=1)
        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.admin = User.objects.create_user(
            email='cuth@test', password='x', is_superuser=True, is_staff=True)
        self.admin.skills.add(skill)
        self.adda = create_adda(self.admin, product=self.product)  # current_stage = cutting

    def test_autodiscover_registered_handler(self):
        handler = base.get(STAGE_CUTTING)
        self.assertIsInstance(handler, CuttingHandler)
        self.assertTrue(handler.pays_workers)
        self.assertEqual(handler.template_partial, 'production/_stage_panel_cutting.html')

    def test_panel_context_delegates_to_snapshot(self):
        ctx = base.get(STAGE_CUTTING).panel_context(self.adda, None)
        self.assertEqual(set(ctx.keys()), set(get_cutting_snapshot(self.adda).keys()))

    def test_complete_delegates_to_from_bundles(self):
        with patch('production.services.complete_cutting_from_bundles') as m:
            base.get(STAGE_CUTTING).complete(
                user_id=self.admin.pk, adda=self.adda, record=None, data={})
        m.assert_called_once()
        kwargs = m.call_args.kwargs
        self.assertEqual(kwargs['adda'], self.adda)
        self.assertEqual(kwargs['user'], self.admin)
