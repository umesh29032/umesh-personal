"""OI-C1 (BOD-D, owner Option B 2026-07-18) — settlement_queue() batched
read-path. Two permanent pins:

1. PARITY: the batched queue output equals an independent per-Adda
   recomputation through the UNTOUCHED shared funnel helpers
   (_payable_stage_records + _settleable_lines per Adda) — the exact
   pre-optimization algorithm — on a mixed world (multi-worker ready ·
   waiting · monthly-skip · fully-credited dropout).
2. BUDGET: query count is volume-independent (6 regardless of Adda count).

Behavior identity was ALSO proven on the primary DB (before/after JSON
byte-identical, md5 16120ae04547345cc1152a13d1514f78; 35 → 6 queries) —
recorded in BOD_BUILD_LOG §BOD-D.
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import WorkerProfile
from expense.services.adda_settlement_service import (
    _payable_stage_records, _settleable_lines, create_draft,
    finalize_adda_settlement, settlement_queue,
)
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


class QueueBatchingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mgmt = User.objects.create_user(email='qb-mgmt@test', password='x')
        cls.mgmt.role = Role.objects.get(code='manager')
        cls.mgmt.save()
        cls.w1 = User.objects.create_user(email='qb-w1@test', password='x')
        cls.w2 = User.objects.create_user(email='qb-w2@test', password='x')
        cls.w_monthly = User.objects.create_user(email='qb-wm@test', password='x')
        WorkerProfile.objects.create(user=cls.w_monthly,
                                     pay_basis=WorkerProfile.PayBasis.MONTHLY)
        cls.product = Product.objects.create(code='QBP', name='QB Prod')
        stage, _ = Stage.objects.get_or_create(
            code='qb_stitch', defaults={'name': 'QB Stitch'})
        cls.stage = stage

    def _adda(self, code, rate='3'):
        ws = WorkflowStage.objects.create(
            product=Product.objects.create(code=f'P{code}', name=f'P {code}'),
            stage=self.stage, order=1,
            cost_rate=Decimal(rate), credits_workers=True)
        adda = Adda.objects.create(code=code, product=ws.product)
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws, started_at=timezone.now())
        return adda, sr

    def _work(self, worker, sr, qty):
        current = {t.worker_id for t in sr.worker_tasks.exclude(
            status=WorkerStageTask.Status.CANCELLED)}
        set_stage_workers(sr, list(current | {worker.pk}))
        task = WorkerStageTask.objects.get(stage_record=sr, worker=worker)
        report_contributions(task, [{'reported_quantity': str(qty)}], actor=worker)
        complete_worker_task(task, actor=worker)

    def _close(self, sr):
        sr.completed_at = timezone.now()
        sr.save(update_fields=['completed_at'])

    def _build_world(self):
        # READY-1: two workers (50+30 @ ₹3 = ₹240), one monthly line skipped.
        a1, sr1 = self._adda('QB-R1')
        self._work(self.w1, sr1, 50)
        self._work(self.w2, sr1, 30)
        self._work(self.w_monthly, sr1, 99)     # excluded: pay basis MONTHLY
        self._close(sr1)
        # READY-2: one worker (10 @ ₹3 = ₹30).
        a2, sr2 = self._adda('QB-R2')
        self._work(self.w1, sr2, 10)
        self._close(sr2)
        # WAITING: payable stage still open.
        a3, sr3 = self._adda('QB-W1')
        self._work(self.w2, sr3, 5)
        # DROPOUT: fully credited (finalized) — must vanish from the queue.
        a4, sr4 = self._adda('QB-D1')
        self._work(self.w1, sr4, 7)
        self._close(sr4)
        finalize_adda_settlement(
            settlement=create_draft(adda=a4, user=self.mgmt), user=self.mgmt)
        return a1, a2, a3, a4

    def test_batched_queue_equals_per_adda_funnel_recomputation(self):
        a1, a2, a3, a4 = self._build_world()
        q = settlement_queue()

        self.assertEqual([r['adda'].code for r in q['ready']],
                         ['QB-R1', 'QB-R2'])
        self.assertEqual([r['adda'].code for r in q['waiting']], ['QB-W1'])
        r1 = q['ready'][0]
        self.assertEqual((r1['lines'], r1['workers'], r1['expected'],
                          r1['skipped_monthly'], r1['skipped_era_b']),
                         (2, 2, Decimal('240.00'), 1, 0))
        r2 = q['ready'][1]
        self.assertEqual((r2['lines'], r2['workers'], r2['expected']),
                         (1, 1, Decimal('30.00')))
        self.assertEqual(q['waiting'][0]['incomplete'], ['QB Stitch'])

        # Independent recomputation: the ORIGINAL per-Adda algorithm through the
        # untouched shared funnel — must agree with the batched result exactly.
        for row in q['ready']:
            payable = _payable_stage_records(row['adda'])
            lines, skip_a, skip_b, skip_m = _settleable_lines(payable)
            self.assertEqual(row['lines'], len(lines))
            self.assertEqual(row['workers'],
                             len({c.task.worker_id for c in lines}))
            self.assertEqual((row['skipped_era_a'], row['skipped_era_b'],
                              row['skipped_monthly']),
                             (len(skip_a), len(skip_b), len(skip_m)))
        # Dropout: fully-credited Adda contributes zero queue rows.
        all_codes = [r['adda'].code for r in q['ready'] + q['waiting']]
        self.assertNotIn('QB-D1', all_codes)

    def test_query_count_is_volume_independent(self):
        self._build_world()
        with self.assertNumQueries(6):
            settlement_queue()
        # Double the world — count must NOT grow with Adda volume.
        a5, sr5 = self._adda('QB-R3')
        self._work(self.w2, sr5, 4)
        self._close(sr5)
        self._adda('QB-W2')
        with self.assertNumQueries(6):
            settlement_queue()
