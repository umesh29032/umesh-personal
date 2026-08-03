"""Phase-16 performance regression tests — settlement read path.

PA-16-1 + PA-16-2: the settlement-detail DRAFT screen (a money-approval page)
must be O(1) in the number of contribution lines / workers. Two N+1s were
removed:
  • PA-16-1 — _settleable_lines now select_relates
    task__stage_record__workflow_stage__stage (the preview/queue read
    c.task.stage_record.workflow_stage.stage.name PER LINE → 2 queries/line).
  • PA-16-2 — the draft view batches outstanding advances for all workers in
    2 queries (outstanding_advances_bulk) instead of calling
    outstanding_advances() per worker (2 queries/worker).

These tests assert SCALE-INVARIANCE (same query count at 2 line counts) rather
than a hardcoded absolute, so they catch a re-introduced N+1 without breaking on
unrelated count drift. Mirrors production/tests/test_perf_baseline.py.
"""
from decimal import Decimal

from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)
from expense.services import payroll_service, record_advance
from expense.services.adda_settlement_service import create_draft


def _super(email):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=True, is_staff=True)
    u.role = Role.objects.get(code='super_admin')
    u.save()
    return u


def _payable_adda_with_lines(prefix, n_workers, *, advance=False):
    """One payable cutting stage with `n_workers` completed contributions
    (→ n_workers settleable lines), all stages closed. Returns the Adda."""
    product = Product.objects.create(code=f'{prefix}P', name=f'{prefix} P')
    pay, _ = Stage.objects.get_or_create(code=f'{prefix}_cut',
                                         defaults={'name': f'{prefix} Cut'})
    ws = WorkflowStage.objects.create(product=product, stage=pay, order=1,
                                      cost_rate=Decimal('3'), credits_workers=True)
    adda = Adda.objects.create(code=f'{prefix}-001', product=product)
    sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws,
                                        started_at=timezone.now())
    roster = [User.objects.create_user(email=f'{prefix}-w{i}@test', password='x')
              for i in range(n_workers)]
    set_stage_workers(sr, [u.pk for u in roster])
    mgmt = _super(f'{prefix}-m@test')
    for u in roster:
        task = WorkerStageTask.objects.get(stage_record=sr, worker=u)
        report_contributions(task, [{'reported_quantity': '10'}], actor=u)
        complete_worker_task(task, actor=u)
        if advance:
            record_advance(user=mgmt, worker=u, amount=Decimal('50'))
    sr.completed_at = timezone.now()
    sr.save(update_fields=['completed_at'])
    return adda, mgmt


class SettlementDetailDraftN1Test(TestCase):
    """PA-16-1/2: draft settlement-detail query count is FLAT vs #lines."""

    def _draft_view_queries(self, prefix, n_workers):
        adda, mgmt = _payable_adda_with_lines(prefix, n_workers, advance=True)
        s = create_draft(adda=adda, user=mgmt)
        c = Client()
        c.force_login(mgmt)
        url = reverse('expense:adda-settlement-detail', args=[s.reference])
        with CaptureQueriesContext(connection) as cap:
            resp = c.get(url)
        self.assertEqual(resp.status_code, 200)
        return len(cap)

    def test_query_count_flat_vs_lines(self):
        # 2 workers (2 lines, 2 advances) vs 6 workers (6 lines, 6 advances).
        # Pre-fix this grew by 4 queries PER extra worker/line (workflow_stage +
        # stage + 2 outstanding_advances). Now it must be identical.
        q_small = self._draft_view_queries('SDN2', 2)
        q_large = self._draft_view_queries('SDN6', 6)
        self.assertEqual(
            q_small, q_large,
            f"settlement-detail draft N+1: {q_small}q at 2 lines but "
            f"{q_large}q at 6 lines (must be flat — PA-16-1/2)")


class OutstandingAdvancesBulkTest(TestCase):
    """PA-16-2: the bulk helper is 2 queries for ANY worker count AND returns
    rows identical to per-worker outstanding_advances (semantics preserved)."""

    def setUp(self):
        self.mgmt = _super('oab-m@test')
        self.workers = []
        for i in range(5):
            w = User.objects.create_user(email=f'oab-w{i}@test', password='x')
            # vary: some 0, some 1, some 2 advances → some workers absent from map
            for _ in range(i % 3):
                record_advance(user=self.mgmt, worker=w, amount=Decimal('40'))
            self.workers.append(w)

    def test_two_queries_regardless_of_worker_count(self):
        with self.assertNumQueries(2):
            payroll_service.outstanding_advances_bulk(self.workers)

    def test_bulk_matches_per_worker(self):
        bulk = payroll_service.outstanding_advances_bulk(self.workers)
        for w in self.workers:
            single = payroll_service.outstanding_advances(w)
            got = bulk.get(w.pk, [])
            self.assertEqual(
                [(r['advance'].pk, r['remaining']) for r in got],
                [(r['advance'].pk, r['remaining']) for r in single],
                f"bulk disagrees with per-worker for {w.email}")

    def test_empty_input(self):
        with self.assertNumQueries(0):
            self.assertEqual(payroll_service.outstanding_advances_bulk([]), {})
