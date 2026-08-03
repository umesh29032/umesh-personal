"""R8 (roadmap phase) tests — Pattern Design redesign (spec-of-record:
docs/STAGE_TRIO_SPEC_IMPACT_2026_07_05.md).

Pins: display rename (identifier frozen) · generic admin_snapshot architecture
(shape, prev-stage injection, management-only, worker leak) · phone checklist
(schema mode, tick sync = SAME verification rows as the console, submit-all
rule, fixed pay qty=1) · fixed-pay double-guard · lead-time analytics ·
recon fixed_cost classify.
"""
import io
from decimal import Decimal

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, CostMethod, Product, ProductPattern,
    ProductPatternAssignment, Stage, WorkflowStage, WorkerStageTask,
)
from production.stages import base as stage_registry
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _png(name='p.png'):
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), 'white').save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def _role_user(email, role_code, *, skill=None, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    if skill:
        u.skills.add(Skill.objects.get(name=skill))
    return u


class _Base(TestCase):
    """Real stage codes (layering / cutting_pattern) so the registry + pattern
    services engage. Layering completed; Adda sits at Pattern Design."""

    def setUp(self):
        self.mgmt = _role_user('r8-mgmt@test', 'manager')
        self.master = _role_user('r8-pm@test', 'worker', skill='cutting_master')
        self.other = _role_user('r8-w2@test', 'worker', skill='cutting_master')
        self.product = Product.objects.create(code='R8P', name='R8 Pattern P')
        lay_stage, _ = Stage.objects.get_or_create(
            code='layering', defaults={'name': 'Layering'})
        pat_stage, _ = Stage.objects.get_or_create(
            code='cutting_pattern', defaults={'name': 'Pattern Design'})
        self.ws_lay = WorkflowStage.objects.create(
            product=self.product, stage=lay_stage, order=1,
            cost_rate=Decimal('10'), cost_method=CostMethod.PER_LAYER,
            credits_workers=False)
        self.ws_pat = WorkflowStage.objects.create(
            product=self.product, stage=pat_stage, order=2,
            cost_rate=Decimal('500'), cost_method=CostMethod.FIXED,
            credits_workers=True)
        for name in ('Front', 'Back'):
            p = ProductPattern.objects.create(name=f'R8 {name}',
                                              code=f'r8-{name.lower()}')
            ProductPatternAssignment.objects.create(
                product=self.product, pattern=p, pieces_count=1)
        self.adda = Adda.objects.create(code='R8P-001', product=self.product,
                                        current_stage=self.ws_pat)
        now = timezone.now()
        self.sr_lay = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_lay,
            started_at=now, completed_at=now)
        self.sr_pat = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_pat, started_at=now)
        set_stage_workers(self.sr_pat, [self.master.pk])
        self.task = self.sr_pat.worker_tasks.get(worker=self.master)
        self.handler = stage_registry.get('cutting_pattern')

    def _ids(self):
        return list(self.product.pattern_assignments.values_list('id', flat=True))


class RenameTests(_Base):
    def test_seeded_stage_displays_pattern_design_identifier_frozen(self):
        s = Stage.objects.get(code='cutting_pattern')
        self.assertEqual(s.code, 'cutting_pattern')      # frozen identifier
        self.assertTrue(stage_registry.has('cutting_pattern'))
        self.assertEqual(self.handler.name, 'Pattern Design')


class GenericSnapshotTests(_Base):
    def test_layering_admin_snapshot_shape_and_prev_injection(self):
        snap = stage_registry.get('layering').admin_snapshot(self.adda)
        self.assertEqual(snap['title'], 'Layering — reference')
        self.assertTrue(any(s['label'] == 'Totals' for s in snap['sections']))
        from production.views.stage_views import prev_admin_snapshot
        prev = prev_admin_snapshot(self.adda, 'cutting_pattern')
        self.assertEqual(prev['title'], 'Layering — reference')
        # First stage has no previous.
        self.assertIsNone(prev_admin_snapshot(self.adda, 'layering'))

    def test_default_admin_snapshot_is_none(self):
        # Open-closed: stages that don't override expose nothing.
        self.assertIsNone(stage_registry.get('cutting').admin_snapshot(self.adda))

    def test_panel_gates_snapshot_to_management_only(self):
        url = f'/production/addas/{self.adda.code}/stage/cutting_pattern/'
        self.client.force_login(self.mgmt)
        self.assertContains(self.client.get(url), 'management reference')
        self.client.force_login(self.master)               # skilled worker
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'management reference')  # leak test
        self.assertNotContains(resp, 'Layering — reference')


class ChecklistTests(_Base):
    def test_schema_is_checklist_mode(self):
        schema = self.handler.contribution_schema(self.adda)
        self.assertEqual(schema['mode'], 'checklist')
        self.assertEqual(len(schema['checklist']), 2)
        self.assertFalse(any(i['verified'] for i in schema['checklist']))

    def test_draft_ticks_sync_verifications_single_truth(self):
        ids = self._ids()
        self.handler.checklist_submit(task=self.task, checked_ids={ids[0]},
                                      photos=[], actor=self.master,
                                      action='draft')
        record = self.sr_pat.cutting_pattern
        self.assertEqual(record.verifications.count(), 1)
        # Console (service) sees the SAME row; unticking removes it.
        self.handler.checklist_submit(task=self.task, checked_ids=set(),
                                      photos=[], actor=self.master,
                                      action='draft')
        self.assertEqual(record.verifications.count(), 0)
        self.assertEqual(self.task.contributions.count(), 0)  # draft ≠ report

    def test_submit_requires_all_then_books_fixed_pay(self):
        ids = self._ids()
        with self.assertRaisesMessage(ValidationError, 'pending'):
            self.handler.checklist_submit(task=self.task,
                                          checked_ids={ids[0]}, photos=[],
                                          actor=self.master, action='submit')
        self.handler.checklist_submit(task=self.task, checked_ids=set(ids),
                                      photos=[_png()], actor=self.master,
                                      action='submit')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)
        c = self.task.contributions.get()
        self.assertEqual(c.good_quantity, Decimal('1'))
        self.assertEqual(c.expected_earning, Decimal('500.00'))  # fixed × 1
        self.assertEqual(self.sr_pat.cutting_pattern.photos.count(), 1)

    def test_view_checklist_post_end_to_end(self):
        ids = self._ids()
        self.client.force_login(self.master)
        url = f'/production/addas/{self.adda.code}/report/cutting_pattern/'
        resp = self.client.get(url)
        self.assertContains(resp, 'Verify each design')
        self.assertContains(resp, 'R8 Front')
        post = {f'check-{i}': '1' for i in ids}
        post['action'] = 'submit'
        resp = self.client.post(url, post, follow=True)
        self.assertContains(resp, 'submitted')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_tampered_check_key_never_500(self):
        self.client.force_login(self.master)
        url = f'/production/addas/{self.adda.code}/report/cutting_pattern/'
        resp = self.client.post(url, {'check-abc': '1', 'action': 'draft'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)


class FixedDoubleGuardTests(_Base):
    def test_second_completed_report_refused(self):
        ids = self._ids()
        self.handler.checklist_submit(task=self.task, checked_ids=set(ids),
                                      photos=[], actor=self.master,
                                      action='submit')
        set_stage_workers(self.sr_pat, [self.master.pk, self.other.pk])
        t2 = self.sr_pat.worker_tasks.get(worker=self.other)
        report_contributions(t2, [{'reported_quantity': '1'}],
                             actor=self.other)
        with self.assertRaisesMessage(ValidationError, 'fixed-pay'):
            complete_worker_task(t2, actor=self.other)
        # Per-piece stages unaffected: the guard is method-scoped.
        self.assertEqual(self.ws_lay.cost_method, CostMethod.PER_LAYER)


class LeadTimeAndReconTests(_Base):
    def test_lead_minutes_stamped_at_stage_complete(self):
        from production.stages.cutting_pattern.service import (
            complete_pattern_stage, ensure_pattern_record, set_size_allocation)
        from production.models import ProductSize
        ids = self._ids()
        self.handler.checklist_submit(task=self.task, checked_ids=set(ids),
                                      photos=[_png()], actor=self.master,
                                      action='submit')
        # Existing rule: stage COMPLETE needs the helper skill (unchanged by R8).
        self.master.skills.add(Skill.objects.get(name='cutting_master_helper'))
        size = ProductSize.objects.create(product=self.product, code='m',
                                          label='M')
        record = ensure_pattern_record(stage_record=self.sr_pat,
                                       user=self.master)
        set_size_allocation(record=record, user=self.master, allocations=[
            {'size_id': size.pk, 'proportion_pct': 100}])
        complete_pattern_stage(adda=self.adda, user=self.master)
        record.refresh_from_db()
        self.assertIsNotNone(record.lead_minutes_from_layering)
        self.assertGreaterEqual(record.lead_minutes_from_layering, 0)

    def test_recon_classifies_fixed_stage_ok(self):
        from expense.services.reconciliation_service import _classify
        self.assertEqual(
            _classify(Decimal('500'), None, Decimal('1'), Decimal('500'),
                      method='fixed_cost'), 'ok')
        self.assertEqual(
            _classify(Decimal('500'), None, Decimal('2'), Decimal('1000'),
                      method='fixed_cost'), 'over_allocated')
        # Non-fixed behavior unchanged.
        self.assertEqual(
            _classify(Decimal('300'), Decimal('100'), Decimal('120'),
                      Decimal('360')), 'over_allocated')
