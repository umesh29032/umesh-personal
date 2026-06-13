"""PAY-3 (M1.2): reopening a stage reverses its worker EARNINGS, not just the
frozen manufacturing cost.

Before the fix, reopen cleared the stage's processing_cost but left the
allocation-driven WorkerLedgerEntry credits standing, so the payable ledger
overstated what the factory owed after any reopen. The fix lives in the shared
reopen skeleton (production.services._shared.reopen_stage_record), so it applies
to EVERY stage's reopen — this test exercises it via cutting_pattern (the
simplest reopen: no teardown, just the downstream guard).
"""
from decimal import Decimal

from django.db.models import Sum
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Skill, User
from expense.models import WorkerLedgerEntry
from expense.services import allocate_stage_work
from production.models import AddaStageRecord, Product, Stage, WorkflowStage
from production.services import create_adda, reopen_pattern_stage


def _balance(worker):
    qs = WorkerLedgerEntry.objects.filter(worker=worker)
    credit = qs.filter(entry_type=WorkerLedgerEntry.EntryType.CREDIT).aggregate(s=Sum('amount'))['s'] or 0
    debit = qs.filter(entry_type=WorkerLedgerEntry.EntryType.DEBIT).aggregate(s=Sum('amount'))['s'] or 0
    return credit - debit


# V2-3 PR-B lever-regression pin: this suite exercises the LEGACY allocation
# path, kept alive behind the rollback lever. Default is settlement-only.
@override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
class ReopenVoidsWorkerPayTest(TestCase):
    def setUp(self):
        cp = Stage.objects.get_or_create(code='cutting_pattern', defaults={'name': 'Cutting Pattern'})[0]
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='PAYTEST', name='Pay Reopen Test')
        # pattern is first (so create_adda lands there); cutting gives it a "next".
        self.pattern_wf = WorkflowStage.objects.create(
            product=self.product, stage=cp, order=1, cost_rate=Decimal('10'))
        WorkflowStage.objects.create(product=self.product, stage=cut, order=2)

        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.mgr = User.objects.create_user(
            email='pay-mgr@test', password='x', is_superuser=True, is_staff=True)
        self.mgr.skills.add(skill)
        self.worker = User.objects.create_user(email='pay-worker@test', password='x')

        self.adda = create_adda(self.mgr, product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf, started_at=timezone.now())

    def test_reopen_voids_worker_credits(self):
        # Allocate 5 units @ rate 10 -> 50 credited to the worker.
        assignment = allocate_stage_work(
            user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=5)
        self.assertEqual(_balance(self.worker), Decimal('50.00'))
        self.assertIsNone(assignment.voided_at)

        # Mark the stage completed so it can be reopened.
        self.sr.completed_at = timezone.now()
        self.sr.completed_by = self.mgr
        self.sr.save(update_fields=['completed_at', 'completed_by'])

        # Reopen — must reverse the worker credit (balance back to 0) and void the
        # assignment, in addition to clearing the frozen manufacturing cost.
        reopen_pattern_stage(adda=self.adda, user=self.mgr)

        assignment.refresh_from_db()
        self.assertIsNotNone(assignment.voided_at, "assignment should be voided on reopen")
        self.assertEqual(_balance(self.worker), Decimal('0.00'),
                         "worker payable must net to 0 after reopen reverses the credit")
        # The reversal is an explicit ledger entry (immutable ledger: never deleted).
        self.assertEqual(
            WorkerLedgerEntry.objects.filter(
                worker=self.worker, entry_type=WorkerLedgerEntry.EntryType.DEBIT).count(),
            1, "expected exactly one reversal debit")
