"""M2.3: CuttingPatternHandler adapter parity.

autodiscover registered it, panel_context delegates to the snapshot, and complete()
via the registry advances the stage exactly like the service. Adapter-only.
"""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from accounts.models import Skill, User
from production.constants import STAGE_CUTTING_PATTERN
from production.models import (
    AddaStageRecord, CuttingPatternRecord, Product, ProductPattern,
    ProductPatternAssignment, ProductSize, Stage, WorkflowStage,
)
from production.services import (
    attach_pattern_photo, create_adda, get_pattern_snapshot,
    set_size_allocation, verify_pattern,
)
from production.stages import base
from production.stages.cutting_pattern.handler import CuttingPatternHandler


def _png():
    buf = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buf, 'PNG')
    return SimpleUploadedFile('p.png', buf.getvalue(), content_type='image/png')


class CuttingPatternHandlerParityTest(TestCase):
    def setUp(self):
        cp = Stage.objects.get_or_create(code='cutting_pattern', defaults={'name': 'Cutting Pattern'})[0]
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='CPHAND', name='CP Handler Test')
        self.wf = WorkflowStage.objects.create(product=self.product, stage=cp, order=1)
        WorkflowStage.objects.create(product=self.product, stage=cut, order=2)
        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.admin = User.objects.create_user(
            email='cph@test', password='x', is_superuser=True, is_staff=True)
        self.admin.skills.add(skill)

    def _ready_adda(self):
        assigns = []
        for code, name, n in [('hf', 'F', 1), ('hb', 'B', 1)]:
            pat = ProductPattern.objects.get_or_create(code=code, defaults={'name': name})[0]
            assigns.append(ProductPatternAssignment.objects.create(
                product=self.product, pattern=pat, pieces_count=n))
        sizes = [ProductSize.objects.create(product=self.product, code=c, label=c.upper(), display_order=i)
                 for i, c in enumerate(['s', 'm'], 1)]
        adda = create_adda(self.admin, product=self.product)
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=self.wf, started_at=timezone.now())
        record = CuttingPatternRecord.objects.create(stage_record=sr)
        attach_pattern_photo(stage_record=sr, uploaded_image=_png(), caption='x', user=self.admin)
        for a in assigns:
            verify_pattern(record=record, assignment=a, user=self.admin)
        set_size_allocation(record=record, user=self.admin, allocations=[
            {'size_id': sizes[0].id, 'proportion_pct': 60},
            {'size_id': sizes[1].id, 'proportion_pct': 40},
        ])
        return adda, sr

    def test_autodiscover_registered_handler(self):
        handler = base.get(STAGE_CUTTING_PATTERN)
        self.assertIsInstance(handler, CuttingPatternHandler)
        self.assertFalse(handler.pays_workers)

    def test_panel_context_delegates_to_snapshot(self):
        adda, sr = self._ready_adda()
        ctx = base.get(STAGE_CUTTING_PATTERN).panel_context(adda, sr)
        self.assertEqual(set(ctx.keys()), set(get_pattern_snapshot(adda).keys()))

    def test_complete_via_handler_advances(self):
        adda, sr = self._ready_adda()
        base.get(STAGE_CUTTING_PATTERN).complete(
            user_id=self.admin.pk, adda=adda, record=sr, data={})
        adda.refresh_from_db()
        self.assertNotEqual(adda.current_stage_id, self.wf.id)   # advanced off pattern
        sr.refresh_from_db()
        self.assertIsNotNone(sr.completed_at)
