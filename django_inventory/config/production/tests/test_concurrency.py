"""Concurrency tests (M1.1 / WF-4) — stage completion is race-safe.

Two people hitting "complete" on the same Adda stage at the same instant must NOT
both advance it (double-advance / double-cost-freeze). The fix: each complete_*
locks its AddaStageRecord with select_for_update before re-checking completed_at,
so the second completer blocks, then sees the stage already done and is rejected.

This drives two genuinely-parallel completers via the _concurrency harness and
asserts exactly one wins. Without the lock, both would pass the completed_at
check and advance (len(ok) == 2) — so this test detects the regression.

TransactionTestCase is required: threads commit to a shared DB (a plain TestCase
wraps each test in one transaction the threads can't see). It also flushes the DB
afterwards, which would wipe migration-seeded rows — so this test is fully
SELF-CONTAINED (creates its own product/stages/skill/flow, no seed reliance, no
serialized_rollback, which collides with ContentType rows in the full suite).
"""
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase
from django.utils import timezone
from PIL import Image

from accounts.models import Skill, User
from production.models import (
    Adda, AddaStageRecord, CuttingPatternRecord, Product, ProductPattern,
    ProductPatternAssignment, ProductSize, Stage, WorkflowStage,
)
from production.services import (
    attach_pattern_photo, complete_pattern_stage, create_adda,
    set_size_allocation, verify_pattern,
)
from production.tests._concurrency import run_in_parallel


def _png():
    buf = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buf, 'PNG')
    return SimpleUploadedFile('p.png', buf.getvalue(), content_type='image/png')


class StageCompletionConcurrencyTest(TransactionTestCase):
    def setUp(self):
        # Self-contained: build a throwaway product whose flow is
        # cutting_pattern (order 1) -> cutting (order 2). No migration-seed reliance.
        cp = Stage.objects.get_or_create(code='cutting_pattern', defaults={'name': 'Cutting Pattern'})[0]
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='CONCTEST', name='Concurrency Test Product')
        self.wf = WorkflowStage.objects.create(product=self.product, stage=cp, order=1)
        WorkflowStage.objects.create(product=self.product, stage=cut, order=2)

        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.admin = User.objects.create_user(
            email='conc-admin@test', password='x', is_superuser=True, is_staff=True)
        self.admin.skills.add(skill)

        assigns = []
        for code, name, n in [('cf', 'Front', 1), ('cb', 'Back', 1), ('cs', 'Sleeve', 2)]:
            pat = ProductPattern.objects.get_or_create(code=code, defaults={'name': name})[0]
            assigns.append(ProductPatternAssignment.objects.create(
                product=self.product, pattern=pat, pieces_count=n))
        sizes = [
            ProductSize.objects.create(product=self.product, code=c, label=c.upper(), display_order=i)
            for i, c in enumerate(['s', 'm', 'l'], 1)
        ]

        # create_adda sets current_stage = first stage (cutting_pattern). It only
        # auto-creates a stage record for layering, so make the pattern one here.
        self.adda = create_adda(self.admin, product=self.product)
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.wf, started_at=timezone.now())
        record = CuttingPatternRecord.objects.create(stage_record=sr)

        # Preconditions for a clean complete: >=1 photo + all verified + sizes == 100.
        attach_pattern_photo(stage_record=sr, uploaded_image=_png(), caption='x', user=self.admin)
        for a in assigns:
            verify_pattern(record=record, assignment=a, user=self.admin)
        set_size_allocation(record=record, user=self.admin, allocations=[
            {'size_id': sizes[0].id, 'proportion_pct': 30},
            {'size_id': sizes[1].id, 'proportion_pct': 50},
            {'size_id': sizes[2].id, 'proportion_pct': 20},
        ])

    def test_two_concurrent_completes_advance_only_once(self):
        adda_pk = self.adda.pk
        admin = self.admin

        def complete():
            # Each thread fetches its own Adda instance, mirroring two requests.
            adda = Adda.objects.get(pk=adda_pk)
            return complete_pattern_stage(adda=adda, user=admin)

        results = run_in_parallel([complete, complete])
        ok = [r for r, exc in results if exc is None]
        errs = [exc for r, exc in results if exc is not None]

        # Exactly one completer wins; the other is cleanly rejected (ValidationError),
        # not a crash / IntegrityError / a second advance.
        self.assertEqual(len(ok), 1, f"expected exactly 1 success, got {len(ok)}; errs={errs}")
        self.assertEqual(len(errs), 1, f"expected exactly 1 rejection, got {errs}")
        self.assertIsInstance(errs[0], ValidationError)

        # The Adda advanced exactly once (off the pattern stage); the stage record
        # was completed exactly once.
        adda = Adda.objects.get(pk=adda_pk)
        self.assertNotEqual(adda.current_stage_id, self.wf.id,
                            "Adda did not advance past the pattern stage")
        sr = AddaStageRecord.objects.get(adda_id=adda_pk, workflow_stage=self.wf)
        self.assertIsNotNone(sr.completed_at)
