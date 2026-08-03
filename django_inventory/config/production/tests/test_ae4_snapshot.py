"""AE-4 — Super-Admin Production Snapshot. Verifies stage_snapshot numbers reconcile with
DB truth (totals, per-bundle rollup, per-worker×bundle detail), management-only access, and
whole/partial accounting. Self-contained fixture (cutting COLOR_SIZE → overlock)."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, Skill, User
from production.constants import ALLOC_DIM_COLOR_SIZE, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingRecord, Product,
    ProductSize, Stage, WorkerStageTask, WorkflowStage,
)
from production.services import pool_service, stage_snapshot
from production.services.worker_task_service import (
    complete_worker_task, save_draft_contributions,
)
from raw_materials.models import ClothColor


def _user(email, code, skills=()):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code)
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get_or_create(name=s, defaults={'label': s})[0])
    return u


class SnapshotTests(TestCase):
    def setUp(self):
        self.red = ClothColor.objects.get_or_create(name='AE4 Red')[0]
        self.blue = ClothColor.objects.get_or_create(name='AE4 Blue')[0]
        cut = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})[0]
        ov = Stage.objects.get_or_create(code='overlock', defaults={'name': 'Overlock'})[0]
        ov.access_by_skill.add(Skill.objects.get_or_create(name='overlock_operator', defaults={'label': 'OV'})[0])
        self.p = Product.objects.create(code='AE4', name='AE4')
        cws = WorkflowStage.objects.create(product=self.p, stage=cut, order=1,
                                           cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.ows = WorkflowStage.objects.create(product=self.p, stage=ov, order=2,
                                                cost_rate=Decimal('5'), credits_workers=True,
                                                allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.m = ProductSize.objects.create(product=self.p, code='m', label='M', display_order=1)
        self.l = ProductSize.objects.create(product=self.p, code='l', label='L', display_order=2)
        self.adda = Adda.objects.create(code='AE4-001', product=self.p,
                                        current_stage=self.ows, status=Adda.Status.IN_PROGRESS)
        self.mgr = _user('ae4-mgr@t', 'super_admin')
        self.manager = _user('ae4-manager@t', 'manager')
        csr = AddaStageRecord.objects.create(adda=self.adda, workflow_stage=cws,
                                             started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=csr, pieces_cut=180)
        for c, s, n in [(self.red, self.m, 100), (self.blue, self.l, 80)]:
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=self.adda, product=self.p, cutting_record=cr, color=c, size=s,
                verified_piece_count=n, created_by=self.mgr)
        self.sr = AddaStageRecord.objects.create(adda=self.adda, workflow_stage=self.ows,
                                                 started_at=timezone.now())
        self.w1 = _user('ae4-w1@t', 'worker', skills=['overlock_operator'])
        self.w2 = _user('ae4-w2@t', 'worker', skills=['overlock_operator'])
        for w in (self.w1, self.w2):
            WorkerStageTask.objects.create(stage_record=self.sr, worker=w,
                                           status=WorkerStageTask.Status.ASSIGNED)
        # w1 whole Red/M (100); w2 partial Blue/L (30). w1 reports 40 of Red/M.
        pool_service.allocate_whole(self.sr, self.w1, actor=self.mgr, color_id=self.red.id, size_id=self.m.id)
        pool_service.allocate(self.sr, self.w2, qty=30, actor=self.mgr, color_id=self.blue.id, size_id=self.l.id, mode='partial')
        t1 = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w1)
        save_draft_contributions(t1, [{
            'color_id': self.red.id, 'size_id': self.m.id, 'reported_quantity': '40',
            'alter_quantity': '0', 'missing_quantity': '0', 'damaged_quantity': '0'}], actor=self.w1)
        complete_worker_task(t1, actor=self.w1)

    def test_totals_reconcile_with_db(self):
        t = stage_snapshot(self.sr)['totals']
        self.assertEqual(t['bundles'], 2)
        self.assertEqual((t['whole'], t['partial']), (1, 1))
        self.assertEqual(t['workers'], 2)
        self.assertEqual(t['allocated'], Decimal('130'))   # 100 + 30
        self.assertEqual(t['completed'], Decimal('40'))    # w1 reported 40
        self.assertEqual(t['remaining'], Decimal('90'))    # 130 - 40
        self.assertEqual(t['unassigned'], Decimal('50'))   # Red 0 left + Blue 50 left

    def test_bundle_rollup(self):
        by = {(b['color_id'], b['size_id']): b for b in stage_snapshot(self.sr)['bundles']}
        red = by[(self.red.id, self.m.id)]
        self.assertEqual((red['total'], red['assigned'], red['available'], red['completed']),
                         (Decimal('100'), Decimal('100'), Decimal('0'), Decimal('40')))
        self.assertEqual(red['progress'], 40)
        blue = by[(self.blue.id, self.l.id)]
        self.assertEqual((blue['assigned'], blue['available']), (Decimal('30'), Decimal('50')))

    def test_allocation_detail(self):
        rows = {(a['worker'].email, a['color'].name): a for a in stage_snapshot(self.sr)['allocations']}
        r = rows[('ae4-w1@t', 'AE4 Red')]
        self.assertEqual((r['mode'], r['allocated'], r['completed'], r['remaining']),
                         ('whole', Decimal('100'), Decimal('40'), Decimal('60')))
        self.assertEqual(r['expected_earning'], Decimal('200.00'))   # 40 × ₹5
        self.assertEqual(r['status'], 'done')                        # task locked
        self.assertIsNotNone(r['started_at'])

    def test_access_management_only(self):
        url = '/production/addas/AE4-001/snapshot/'
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(url).status_code, 200)      # super admin
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(url).status_code, 200)      # manager
        self.client.force_login(self.w1)
        self.assertEqual(self.client.get(url).status_code, 403)      # worker blocked

    def test_page_renders_numbers(self):
        self.client.force_login(self.mgr)
        html = self.client.get('/production/addas/AE4-001/snapshot/').content.decode()
        # mode tags render lowercase in HTML (CSS uppercases them visually)
        for needle in ('Production Snapshot', 'AE4 Red', 'mode-tag whole',
                       'mode-tag partial', '₹200.00', 'Allocations'):
            self.assertIn(needle, html)
