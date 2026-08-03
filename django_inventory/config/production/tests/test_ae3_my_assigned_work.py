"""AE-3 — worker "My Assigned Work" dashboard + per-bundle report scoping.

Verifies: the dashboard lists a worker's active bundle allocations as cards with a
workload summary; the report page scopes to ONE bundle via ?color=&size= (colour/size
locked, no add-line); isolation (a worker never sees another's bundle / can't report an
unallocated pair); live progress after a submit. Self-contained fixture.
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingRecord, Product,
    ProductSize, Stage, WorkerStageTask, WorkflowStage,
)
from production.services import bundle_service, pool_service
from raw_materials.models import ClothColor


def _user(email, code, skills=()):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code)
    u.save()
    for s in skills:
        from accounts.models import Skill
        u.skills.add(Skill.objects.get_or_create(name=s, defaults={'label': s})[0])
    return u


class _World(TestCase):
    def setUp(self):
        self.red = ClothColor.objects.get_or_create(name='AE3 Red')[0]
        self.blue = ClothColor.objects.get_or_create(name='AE3 Blue')[0]
        cut = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})[0]
        ov = Stage.objects.get_or_create(code='overlock', defaults={'name': 'Overlock'})[0]
        from accounts.models import Skill
        skill = Skill.objects.get_or_create(name='overlock_operator', defaults={'label': 'OV'})[0]
        ov.access_by_skill.add(skill)
        self.p = Product.objects.create(code='AE3', name='AE3')
        cws = WorkflowStage.objects.create(product=self.p, stage=cut, order=1,
                                           cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.ows = WorkflowStage.objects.create(product=self.p, stage=ov, order=2,
                                                cost_rate=Decimal('5'), credits_workers=True,
                                                allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.m = ProductSize.objects.create(product=self.p, code='m', label='M', display_order=1)
        self.l = ProductSize.objects.create(product=self.p, code='l', label='L', display_order=2)
        self.adda = Adda.objects.create(code='AE3-001', product=self.p,
                                        current_stage=self.ows, status=Adda.Status.IN_PROGRESS)
        self.mgr = _user('ae3-mgr@t', 'super_admin')
        csr = AddaStageRecord.objects.create(adda=self.adda, workflow_stage=cws,
                                             started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=csr, pieces_cut=180)
        for c, s, n in [(self.red, self.m, 100), (self.blue, self.l, 80)]:
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=self.adda, product=self.p, cutting_record=cr, color=c, size=s,
                verified_piece_count=n, created_by=self.mgr)
        self.ssr = AddaStageRecord.objects.create(adda=self.adda, workflow_stage=self.ows,
                                                  started_at=timezone.now())
        self.w1 = _user('ae3-w1@t', 'worker', skills=['overlock_operator'])
        self.w2 = _user('ae3-w2@t', 'worker', skills=['overlock_operator'])
        for w in (self.w1, self.w2):
            WorkerStageTask.objects.create(stage_record=self.ssr, worker=w,
                                           status=WorkerStageTask.Status.ASSIGNED)
        # w1 holds Red/M (whole 100) + Blue/L partial 30; w2 holds nothing yet
        pool_service.allocate_whole(self.ssr, self.w1, actor=self.mgr,
                                    color_id=self.red.id, size_id=self.m.id)
        pool_service.allocate(self.ssr, self.w1, qty=30, actor=self.mgr,
                              color_id=self.blue.id, size_id=self.l.id, mode='partial')


class DashboardTests(_World):
    def test_my_assigned_work_lists_worker_bundles_with_summary(self):
        data = bundle_service.my_assigned_work(self.w1)
        self.assertEqual(len(data['cards']), 2)                 # Red/M + Blue/L
        self.assertEqual(data['summary']['bundles'], 2)
        self.assertEqual(data['summary']['allocated'], Decimal('130'))   # 100 + 30
        self.assertEqual(data['summary']['remaining'], Decimal('130'))
        # w2 has no allocation → empty
        self.assertEqual(len(bundle_service.my_assigned_work(self.w2)['cards']), 0)

    def test_dashboard_page_renders_for_worker(self):
        self.client.force_login(self.w1)
        resp = self.client.get('/production/my-work/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'My Assigned Work')
        self.assertContains(resp, 'AE3 Red')
        self.assertContains(resp, 'Active bundles')

    def test_live_progress_updates_after_submit(self):
        # w1 reports 40 good on Red/M → completed 40, remaining 60
        from production.services.worker_task_service import (
            complete_worker_task, save_draft_contributions,
        )
        task = WorkerStageTask.objects.get(stage_record=self.ssr, worker=self.w1)
        save_draft_contributions(task, [{
            'color_id': self.red.id, 'size_id': self.m.id, 'reported_quantity': '40',
            'alter_quantity': '0', 'missing_quantity': '0', 'damaged_quantity': '0'}],
            actor=self.w1)
        complete_worker_task(task, actor=self.w1)
        cards = {(c['color_id'], c['size_id']): c
                 for c in bundle_service.my_assigned_work(self.w1)['cards']}
        red = cards[(self.red.id, self.m.id)]
        self.assertEqual((red['completed'], red['remaining']), (Decimal('40'), Decimal('60')))


class ReportScopingTests(_World):
    def _url(self, color, size):
        return f'/production/addas/AE3-001/report/overlock/?color={color}&size={size}'

    def test_single_bundle_locks_colour_size_and_hides_add_line(self):
        self.client.force_login(self.w1)
        resp = self.client.get(self._url(self.red.id, self.m.id))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['single_bundle'])
        self.assertEqual(resp.context['bundle_label'], 'AE3 Red · M')
        self.assertContains(resp, 'Your bundle')
        self.assertNotContains(resp, 'Add another')       # single-bundle: no add-line

    def test_scoped_submit_records_only_that_bundle(self):
        self.client.force_login(self.w1)
        resp = self.client.post(self._url(self.red.id, self.m.id), {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.red.id), 'line-0-size_id': str(self.m.id),
            'line-0-reported_quantity': '40', 'line-0-alter_quantity': '0',
            'line-0-missing_quantity': '0', 'line-0-damaged_quantity': '0'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        c = bundle_service.worker_bundles(self.ssr, self.w1)
        red = [x for x in c if x['color_id'] == self.red.id][0]
        self.assertEqual(red['completed'], Decimal('40'))

    def test_bad_bundle_param_falls_back_to_full_form(self):
        # size the worker was NOT allocated (Red/L) → not single_bundle (defence in depth)
        self.client.force_login(self.w1)
        resp = self.client.get(self._url(self.red.id, self.l.id))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['single_bundle'])

    def test_over_report_still_hard_blocked_in_scoped_mode(self):
        self.client.force_login(self.w1)
        self.client.post(self._url(self.red.id, self.m.id), {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.red.id), 'line-0-size_id': str(self.m.id),
            'line-0-reported_quantity': '101', 'line-0-alter_quantity': '0',
            'line-0-missing_quantity': '0', 'line-0-damaged_quantity': '0'}, follow=True)
        task = WorkerStageTask.objects.get(stage_record=self.ssr, worker=self.w1)
        self.assertNotEqual(task.status, WorkerStageTask.Status.COMPLETED)   # 101 > 100
