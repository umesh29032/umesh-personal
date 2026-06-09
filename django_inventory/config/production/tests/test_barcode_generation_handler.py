"""M2.5: BarcodeGenerationHandler adapter parity.

Registered; panel_context delegates to the snapshot; complete() delegates to
complete_barcode_generation (via patch — the delegation pattern is already proven
end-to-end by the layering/pattern handler tests).
"""
from unittest.mock import patch

from django.test import TestCase

from accounts.models import Skill, User
from production.constants import STAGE_BARCODE_GENERATION
from production.models import Product, Stage, WorkflowStage
from production.services import create_adda, get_barcode_snapshot
from production.stages import base
from production.stages.barcode_generation.handler import BarcodeGenerationHandler


class BarcodeGenerationHandlerParityTest(TestCase):
    def setUp(self):
        bg = Stage.objects.get_or_create(
            code='barcode_generation', defaults={'name': 'Barcode Generation'})[0]
        self.product = Product.objects.create(code='BGHAND', name='Barcode Handler Test')
        self.wf = WorkflowStage.objects.create(product=self.product, stage=bg, order=1)
        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.admin = User.objects.create_user(
            email='bgh@test', password='x', is_superuser=True, is_staff=True)
        self.admin.skills.add(skill)
        self.adda = create_adda(self.admin, product=self.product)

    def test_autodiscover_registered_handler(self):
        handler = base.get(STAGE_BARCODE_GENERATION)
        self.assertIsInstance(handler, BarcodeGenerationHandler)
        self.assertFalse(handler.pays_workers)
        self.assertEqual(handler.template_partial, 'production/_stage_panel_barcode_gen.html')

    def test_panel_context_delegates_to_snapshot(self):
        ctx = base.get(STAGE_BARCODE_GENERATION).panel_context(self.adda, None)
        self.assertEqual(set(ctx.keys()), set(get_barcode_snapshot(self.adda).keys()))

    def test_complete_delegates_to_service(self):
        with patch('production.services.complete_barcode_generation') as m:
            base.get(STAGE_BARCODE_GENERATION).complete(
                user_id=self.admin.pk, adda=self.adda, record=None, data={})
        m.assert_called_once()
        kwargs = m.call_args.kwargs
        self.assertEqual(kwargs['adda'], self.adda)
        self.assertEqual(kwargs['user'], self.admin)
