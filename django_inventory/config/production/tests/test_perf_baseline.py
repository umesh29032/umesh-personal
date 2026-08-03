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
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from inventory.views.dashboard import _build_dashboard_context
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage
from production.services import attach_layering_snapshots
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


class ListViewQueryBaselineTest(TestCase):
    """P0.6: lock query counts for the management list/costing pages (full render,
    so a future per-row template N+1 fails CI). Fixed fixture = 3 Addas."""

    def setUp(self):
        from django.test import Client
        from inventory.models import Role
        self.product = Product.objects.create(code='LV', name='LV Product')
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cut, order=1, cost_rate=Decimal('0'))
        for i in (1, 2, 3):
            adda = Adda.objects.create(
                code=f'LV-00{i}', product=self.product, current_stage=self.ws)
            AddaStageRecord.objects.create(
                adda=adda, workflow_stage=self.ws, started_at=timezone.now())
        self.admin = User.objects.create_user(
            email='lv-admin@test', password='x', is_superuser=True, is_staff=True)
        self.admin.role = Role.objects.get(code='super_admin')
        self.admin.save()
        self.client = Client()
        self.client.force_login(self.admin)

    def test_adda_list_query_count(self):
        with self.assertNumQueries(ADDA_LIST_QUERIES):
            self.client.get(reverse('production:adda-list'))

    def test_costing_query_count(self):
        with self.assertNumQueries(COSTING_QUERIES):
            self.client.get(reverse('production:costing'))


# Locked full-render baselines (3-Adda fixture; includes sidebar/menu overhead).
# A silent move = a template/queryset N+1 regression — update CONSCIOUSLY.
# 11 → 8 (engineering sweep 2026-07-06, conscious): AddaListView queryset gained
# select_related('current_stage__stage') — get_stage_type_display no longer
# fires one Stage read per rendered row (3-Adda fixture ⇒ −3).
ADDA_LIST_QUERIES = 6
# 2026-08-02 (conscious, IMPROVEMENT): `user_role_codes()` is now request-cached
# like its two neighbours in permission_service. Every `user_has_role()` call used
# to fire a fresh `extra_roles` M2M query, so a page doing many role checks paid
# many queries for an answer that cannot change mid-request. Lowered here to LOCK
# the gain in — a future rise is a real regression.
# 9→10 (C-1, conscious): +1 aggregate for the unpriced-rolls honest-NULL map.
# 10 → 11 (M13, conscious): +1 payable-std aggregate — the like-for-like
# variance needs the payable-only Σ alongside the total frozen Σ.
# 11 → 16 (Phase-17 RMX-D 2026-07-18, conscious — Model-B completion): +5,
# ALL from the ONE certified Decision-2 assembly (full_costs_for_addas:
# material arm 3 grouped aggregates + SWA settled Σ + non-payable ASR Σ) —
# constant count regardless of Adda volume; the Material/Full-Cost columns'
# entire price.
COSTING_QUERIES = 14
# 2026-08-02 (conscious, IMPROVEMENT): `user_role_codes()` is now request-cached
# like its two neighbours in permission_service. Every `user_has_role()` call used
# to fire a fresh `extra_roles` M2M query, so a page doing many role checks paid
# many queries for an answer that cannot change mid-request. Lowered here to LOCK
# the gain in — a future rise is a real regression.


class BulkSnapshotN1Test(TestCase):
    """P5.1: attach_layering_snapshots is N+1-FREE — its query count must NOT grow
    with the number of Addas (the whole point of the batch)."""

    def _make_adda(self, code):
        adda = Adda.objects.create(code=code, product=self.product, current_stage=self.ws)
        AddaStageRecord.objects.create(
            adda=adda, workflow_stage=self.ws, started_at=timezone.now())
        return adda

    def setUp(self):
        self.product = Product.objects.create(code='BULK', name='Bulk Product')
        lay = Stage.objects.get_or_create(code='layering', defaults={'name': 'Layering'})[0]
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=lay, order=1, cost_rate=Decimal('0'))

    def test_query_count_is_flat_regardless_of_adda_count(self):
        one = [self._make_adda('BULK-001')]
        with self.assertNumQueries(BULK_SNAPSHOT_QUERIES):
            attach_layering_snapshots(one)
        # Same fixed cost for 3 Addas → no N+1.
        three = [self._make_adda('BULK-002'), self._make_adda('BULK-003'),
                 self._make_adda('BULK-004')]
        with self.assertNumQueries(BULK_SNAPSHOT_QUERIES):
            attach_layering_snapshots(three)
        # And the snapshots are actually attached.
        self.assertTrue(all(a.layering_snap['state'] == 'in_progress' for a in three))


# attach_layering_snapshots is bounded: WorkflowStages + stage records + 2 prefetch
# (worker_tasks, roll entries) + leftover sums = a FIXED count, NOT per-Adda.
BULK_SNAPSHOT_QUERIES = 5


# Locked baselines (FIXED fixture: 2 Addas at layering, 1 worker assigned). Update
# CONSCIOUSLY if a real change moves them — a silent move = an N+1 regression.
# NOTE 2026-06-10: these are HIGH (per-Adda snapshot/pipeline work) — M5/P5.1 should
# bring them down; when it does, lower these numbers in the same commit.
WORKER_DASHBOARD_QUERIES = 21   # 22 → 21: role-codes request-cache (2026-08-02).
                                # was 16 — C-2 freeze closeout 2026-07-05: the
                                # dashboard now consults the LIVE Stage-Access
                                # predicate (ONE stage_access_map call: Stage +
                                # skill/role principal reads) + one batched
                                # my-task-ids query for the accordion gate +
                                # assignment-scoped helper board. Bounded,
                                # not per-row — the price of hub-live visibility.
MANAGEMENT_DASHBOARD_QUERIES = 25   # 26 → 25: role-codes request-cache (2026-08-02).
                                    # was 21 (R1 reuse; R5 +1 expense aggregate).
                                    # C-2 2026-07-05: +5 — same single
                                    # stage_access_map (management short-circuits
                                    # inside it but principal/Stage reads still
                                    # run) + my_active_stages materialized before
                                    # the map. Bounded, not per-row.
