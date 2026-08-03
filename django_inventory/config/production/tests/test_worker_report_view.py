"""V2-1c-iii pt.2b — worker report view: access, schema rendering, draft/submit,
locked state, badges, and the OPEN-CLOSED PROOF for the report surface (a
synthetic handler with a non-Cutting schema must render + round-trip with zero
view/template edits — P2_SCHEMA_RENDER_VALIDATION §5 residual-risk guard).
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from production.models import (
    Adda, AddaStageRecord, Product, ProductSize, Stage, WorkflowStage,
    WorkerStageTask,
)
from production.stages.base import registry
from production.stages.base.handler import (
    CompletionResult, ReopenResult, StageHandler,
)
from raw_materials.models import ClothColor


def _mk_stage_env(*, stage_code, product_code, adda_code, rate='10'):
    """Product + Stage + WorkflowStage + Adda + started AddaStageRecord."""
    product = Product.objects.create(code=product_code, name=f'{product_code} P')
    # Migrations seed the well-known stage codes — reuse the row if it exists.
    stage, _ = Stage.objects.get_or_create(
        code=stage_code, defaults={'name': stage_code.title()})
    ws = WorkflowStage.objects.create(
        product=product, stage=stage, order=1, cost_rate=Decimal(rate),
        credits_workers=True)   # A360 rule: non-payable freezes 0 — fixtures mean PAYABLE
    adda = Adda.objects.create(code=adda_code, product=product)
    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=ws, started_at=timezone.now())
    return product, stage, ws, adda, sr


def _grant_stage_access(user, stage):
    """C-3 (freeze closeout): the report view now requires LIVE Stage Access
    on top of assignment — grant the persona a skill wired to the stage."""
    from accounts.models import Skill
    skill, _ = Skill.objects.get_or_create(
        name='cutting_master', defaults={'label': 'Cutting Master'})
    stage.access_by_skill.add(skill)
    user.skills.add(skill)


class WorkerReportViewTest(TestCase):
    """Cutting-schema route (the shipped reference handler)."""

    def setUp(self):
        self.product, self.stage, self.ws, self.adda, self.sr = _mk_stage_env(
            stage_code='cutting', product_code='WRV', adda_code='WRV-001')
        # Seeded master data already includes 'Red' — reuse, don't duplicate.
        self.color, _ = ClothColor.objects.get_or_create(
            name='Red', defaults={'hex_code': '#c0392b'})
        self.size = ProductSize.objects.create(
            product=self.product, label='M', display_order=1, is_active=True)
        self.worker = User.objects.create_user(email='wrv-worker@test', password='x')
        self.stranger = User.objects.create_user(email='wrv-stranger@test', password='x')
        _grant_stage_access(self.worker, self.stage)
        self.task = WorkerStageTask.objects.create(
            stage_record=self.sr, worker=self.worker)
        self.url = reverse('production:worker-report', args=['WRV-001', 'cutting'])

    # ── access ───────────────────────────────────────────────────────────
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('?next=', resp['Location'])   # LOGIN_URL redirect

    def test_unassigned_user_403(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_cancelled_task_403(self):
        self.task.status = WorkerStageTask.Status.CANCELLED
        self.task.save(update_fields=['status'])
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    # ── schema rendering ─────────────────────────────────────────────────
    def test_get_renders_schema_fields(self):
        self.client.force_login(self.worker)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        # Cutting schema declares Colour + Size + Quantity — labels come from the
        # schema, the template hardcodes nothing.
        self.assertIn('Colour', html)
        self.assertIn('Size', html)
        self.assertIn('Quantity', html)
        self.assertIn('Red', html)            # colour option chip
        self.assertIn('line-template', html)  # blank-line template present
        self.assertNotIn('expected_earning', html)   # no money on worker screen

    def test_embedded_uses_chromeless_template(self):
        self.client.force_login(self.worker)
        resp = self.client.get(self.url + '?embedded=1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'production/worker_report_embedded.html')
        self.assertIn('stage-panel-resize', resp.content.decode())

    # ── draft ────────────────────────────────────────────────────────────
    def _draft_post(self, qty='120', extra=None):
        data = {'action': 'draft', 'line-count': '1',
                'line-0-color_id': str(self.color.pk),
                'line-0-size_id': str(self.size.pk),
                'line-0-reported_quantity': qty}
        data.update(extra or {})
        return self.client.post(self.url, data, follow=True)

    def test_draft_saves_lines_and_stays_editable(self):
        self.client.force_login(self.worker)
        resp = self._draft_post()
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.IN_PROGRESS)
        self.assertTrue(self.task.is_draft)
        c = self.task.contributions.get()
        self.assertEqual(c.reported_quantity, Decimal('120'))
        self.assertEqual(c.color_id, self.color.pk)
        self.assertIsNone(c.expected_rate)          # Option B: no money at draft
        self.assertIn('Save draft', resp.content.decode())   # still editable

    def test_draft_replaces_previous_draft(self):
        self.client.force_login(self.worker)
        self._draft_post(qty='120')
        self._draft_post(qty='80')
        self.assertEqual(self.task.contributions.count(), 1)
        self.assertEqual(self.task.contributions.get().reported_quantity, Decimal('80'))

    def test_blank_lines_skipped(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {
            'action': 'draft', 'line-count': '3',
            'line-0-reported_quantity': '10',
            # line 1 entirely blank; line 2 has a colour but no qty → both skipped
            'line-2-color_id': str(self.color.pk),
        })
        self.assertEqual(self.task.contributions.count(), 1)

    # ── submit & complete ────────────────────────────────────────────────
    def test_submit_completes_freezes_and_locks(self):
        self.client.force_login(self.worker)
        resp = self.client.post(self.url, {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.color.pk),
            'line-0-size_id': str(self.size.pk),
            'line-0-reported_quantity': '120'}, follow=True)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)
        c = self.task.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('10'))
        self.assertEqual(c.expected_earning, Decimal('1200.00'))
        html = resp.content.decode()
        self.assertIn('has been submitted', html)        # locked banner (D5)
        self.assertNotIn('id="report-form"', html)       # no form when locked
        self.assertNotIn('1200', html.split('has been submitted')[1][:2000]
                         if 'has been submitted' in html else html)  # no money shown

    def test_locked_task_rejects_further_posts(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {'action': 'submit', 'line-count': '1',
                                    'line-0-reported_quantity': '5'})
        resp = self.client.post(self.url, {'action': 'draft', 'line-count': '1',
                                           'line-0-reported_quantity': '99'},
                                follow=True)
        self.assertEqual(self.task.contributions.get().reported_quantity, Decimal('5'))
        self.assertIn('completed', resp.content.decode().lower())   # error message

    def test_submit_without_lines_rejected(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {'action': 'submit', 'line-count': '0'})
        self.task.refresh_from_db()
        self.assertNotEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_invalid_choice_value_rejected(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {'action': 'draft', 'line-count': '1',
                                    'line-0-color_id': 'evil',
                                    'line-0-reported_quantity': '10'})
        self.assertEqual(self.task.contributions.count(), 0)


class SyntheticHandlerOpenClosedTest(TestCase):
    """THE open-closed proof for the report surface: a stage whose schema is NOT
    Cutting-shaped (size+qty in 'bundles'; no colour) renders and round-trips
    through the SAME view/template with zero edits."""

    STAGE_CODE = 'synthetic_qa_stage'

    class _Handler(StageHandler):
        code = 'synthetic_qa_stage'
        name = 'Synthetic QA Stage'
        template_partial = ''

        def snapshot(self, adda):
            return {}

        def panel_context(self, request, adda, record):
            return {}

        def start(self, *, user_id, adda, record, data):
            return None

        def complete(self, *, user_id, adda, record, data):
            return CompletionResult()

        def reopen(self, *, user_id, record):
            return ReopenResult()

        def cost_quantity(self, record):
            return None

        def contribution_schema(self, adda, worker=None):
            from production.models import ProductSize
            sizes = ProductSize.objects.filter(product=adda.product)
            return {
                'line_label': 'bundle line',
                'fields': [
                    {'key': 'size_id', 'kind': 'choice', 'label': 'Bundle Size',
                     'required': True,
                     'options': [{'value': s.pk, 'label': s.label} for s in sizes]},
                    {'key': 'reported_quantity', 'kind': 'quantity',
                     'label': 'Bundles', 'required': True, 'unit': 'bundles'},
                ],
            }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Snapshot the real registry — clear()+autodiscover() can NOT restore it
        # (handler modules are already in sys.modules, so re-import is a no-op).
        cls._registry_snapshot = registry.all_handlers()

    def setUp(self):
        if not registry.has(self.STAGE_CODE):
            registry.register(self._Handler)
        self.product, self.stage, self.ws, self.adda, self.sr = _mk_stage_env(
            stage_code=self.STAGE_CODE, product_code='SYN', adda_code='SYN-001',
            rate='3')
        self.size = ProductSize.objects.create(
            product=self.product, label='JUMBO', display_order=1, is_active=True)
        self.worker = User.objects.create_user(email='syn-worker@test', password='x')
        _grant_stage_access(self.worker, self.stage)
        self.task = WorkerStageTask.objects.create(
            stage_record=self.sr, worker=self.worker)
        self.url = reverse('production:worker-report',
                           args=['SYN-001', self.STAGE_CODE])

    @classmethod
    def tearDownClass(cls):
        # Restore the snapshotted registry for the classes that run after this one.
        registry.clear()
        for handler in cls._registry_snapshot.values():
            registry.register(handler)
        super().tearDownClass()

    def test_renders_synthetic_schema_not_cutting(self):
        self.client.force_login(self.worker)
        html = self.client.get(self.url).content.decode()
        self.assertIn('Bundle Size', html)
        self.assertIn('bundles', html)
        self.assertIn('JUMBO', html)
        self.assertNotIn('Colour', html)   # the proof: nothing Cutting-shaped leaked

    def test_round_trip_draft_then_submit(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {
            'action': 'draft', 'line-count': '1',
            'line-0-size_id': str(self.size.pk),
            'line-0-reported_quantity': '7'})
        c = self.task.contributions.get()
        self.assertEqual(c.size_id, self.size.pk)
        self.assertIsNone(c.color_id)
        self.assertEqual(c.reported_quantity, Decimal('7'))
        self.client.post(self.url, {
            'action': 'submit', 'line-count': '1',
            'line-0-size_id': str(self.size.pk),
            'line-0-reported_quantity': '7'})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)
        c = self.task.contributions.get()
        self.assertEqual(c.expected_earning, Decimal('21.00'))   # 7 × 3

    def test_required_choice_enforced_from_schema(self):
        self.client.force_login(self.worker)
        self.client.post(self.url, {
            'action': 'draft', 'line-count': '1',
            'line-0-reported_quantity': '7'})   # missing required size
        self.assertEqual(self.task.contributions.count(), 0)


class DashboardReportBadgeTest(TestCase):
    """pt.2c: the My Active Stages badge reflects the worker's task state."""

    def setUp(self):
        self.product, self.stage, self.ws, self.adda, self.sr = _mk_stage_env(
            stage_code='cutting', product_code='BDG', adda_code='BDG-001')
        self.adda.status = Adda.Status.IN_PROGRESS
        self.adda.save(update_fields=['status'])
        self.worker = User.objects.create_user(email='bdg-worker@test', password='x')
        _grant_stage_access(self.worker, self.stage)
        self.task = WorkerStageTask.objects.create(
            stage_record=self.sr, worker=self.worker)
        self.url = reverse('inventory:my_dashboard')

    def _badge(self):
        self.client.force_login(self.worker)
        return self.client.get(self.url).content.decode()

    def test_badge_progression(self):
        self.assertIn('Report needed', self._badge())
        from production.services.worker_task_service import (
            complete_worker_task, save_draft_contributions)
        save_draft_contributions(self.task, [{'reported_quantity': '5'}],
                                 actor=self.worker)
        self.assertIn('Draft saved', self._badge())
        complete_worker_task(self.task, actor=self.worker)
        self.assertIn('Submitted', self._badge())
