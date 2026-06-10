"""P0.6 — performance baseline (the M5 regression oracle).

Locks query counts on hot read paths so an accidental N+1 (or a prefetch removed)
fails CI instead of silently degrading production. Counts are EXACT against a FIXED
small fixture; if a legitimate change moves a count, update it here CONSCIOUSLY (the
point is that the number can't move silently).

Started 2026-06-10 with the dashboard context builder (V2-1b/1c-iv touched its
worker-scoping + active_workers reads). Extend with more hot pages (costing, adda
list, cutting workspace, allocation panel) as M5 progresses.
"""
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from inventory.views.dashboard import _build_dashboard_context
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage
from production.services.worker_task_service import set_stage_workers


class DashboardQueryBaselineTest(TestCase):
    """Hot path: the unified dashboard context builder, worker vs management."""

    def setUp(self):
        self.product = Product.objects.create(code='PERF', name='Perf Product')
        lay = Stage.objects.get_or_create(code='layering', defaults={'name': 'Layering'})[0]
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.ws_lay = WorkflowStage.objects.create(
            product=self.product, stage=lay, order=1, cost_rate=Decimal('0'))
        WorkflowStage.objects.create(
            product=self.product, stage=cut, order=2, cost_rate=Decimal('0'))
        # Two in-progress Addas, each at layering with a started stage record.
        self.addas = []
        for i in (1, 2):
            adda = Adda.objects.create(
                code=f'PERF-00{i}', product=self.product, current_stage=self.ws_lay)
            sr = AddaStageRecord.objects.create(
                adda=adda, workflow_stage=self.ws_lay, started_at=timezone.now())
            self.addas.append((adda, sr))

        self.worker = User.objects.create_user(email='perf-w@test', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        # Assign the worker to Adda #1's layering (active task) so the worker path has data.
        set_stage_workers(self.addas[0][1], [self.worker.pk])

        self.admin = User.objects.create_user(
            email='perf-a@test', password='x', is_superuser=True, is_staff=True)
        self.admin.role = Role.objects.get(code='super_admin')
        self.admin.save()
        self.rf = RequestFactory()

    def _ctx(self, user, *, is_admin_view):
        req = self.rf.get('/')
        req.user = user
        return _build_dashboard_context(req, is_admin_view=is_admin_view)

    def test_worker_dashboard_query_count(self):
        # Worker sees ONLY their assigned Adda (V2-1c-iv isolation).
        with self.assertNumQueries(WORKER_DASHBOARD_QUERIES):
            self._ctx(self.worker, is_admin_view=False)

    def test_management_dashboard_query_count(self):
        # Management sees all in-progress Addas.
        with self.assertNumQueries(MANAGEMENT_DASHBOARD_QUERIES):
            self._ctx(self.admin, is_admin_view=True)


# Locked baselines (FIXED fixture: 2 Addas at layering, 1 worker assigned). Update
# CONSCIOUSLY if a real change moves them — a silent move = an N+1 regression.
# NOTE 2026-06-10: these are HIGH (per-Adda snapshot/pipeline work) — M5/P5.1 should
# bring them down; when it does, lower these numbers in the same commit.
WORKER_DASHBOARD_QUERIES = 14   # was 20 — P5.1 skip unrendered layering snapshot for non-skilled
MANAGEMENT_DASHBOARD_QUERIES = 25   # TODO P5.1: batch the per-Adda layering snapshot (skilled path)
