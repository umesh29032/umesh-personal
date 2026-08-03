"""R3 (roadmap phase) tests — C3 stage-completion guard (PDD §27-C3).

Plan: docs/R3_EXECUTION_PLAN.md. Default: a stage REFUSES completion while
assigned workers are pending. Super-Admin override with a MANDATORY reason →
audited COMPLETION_OVERRIDE history event (adda, stage, pending names+count,
actor, timestamp, reason) → F3 cancel proceeds with the reason stamped.
Guard lives at the advance_to_next_stage funnel → every stage inherits it.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product, WorkerStageTask
from production.services import advance_to_next_stage, create_adda
from production.services import worker_task_service as wts
from tracking.models import AddaHistory


def _user(email, role_code, *, superuser=False):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=superuser, is_staff=superuser)
    u.role = Role.objects.get(code=role_code)
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class CompletionGuardTests(TestCase):
    def setUp(self):
        self.admin = _user('sa@r3.test', 'super_admin', superuser=True)
        self.manager = _user('mgr@r3.test', 'manager')
        self.worker = _user('w@r3.test', 'worker')
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        self.sr = self.adda.stage_records.first()

    def _assign(self, *workers):
        wts.set_stage_workers(self.sr, [w.pk for w in workers])

    def _start_work(self, worker, qty='10'):
        """Worker ENTERS the workflow (reports lines, does NOT complete) —
        the transitional guard's blocking state (IN_PROGRESS)."""
        task = self.sr.worker_tasks.get(worker=worker)
        wts.report_contributions(task, [{'reported_quantity': qty}], actor=worker)
        return task

    def _complete_report(self, worker, qty='10'):
        task = self._start_work(worker, qty)
        wts.complete_worker_task(task, actor=worker)

    # ── default: BLOCK on started-but-unsubmitted (transitional B) ─────────

    def test_started_worker_blocks_and_names_them(self):
        self._assign(self.worker)
        self._start_work(self.worker)              # IN_PROGRESS = engaged
        with self.assertRaises(ValidationError) as ctx:
            advance_to_next_stage(self.adda, self.admin)
        msg = str(ctx.exception)
        self.assertIn('w@r3.test', msg)            # names the pending worker
        self.assertIn('STARTED work', msg)
        # Nothing mutated: task still active, no history event.
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.IN_PROGRESS)
        self.assertFalse(AddaHistory.objects.filter(
            adda=self.adda,
            change_type=AddaHistory.ChangeType.COMPLETION_OVERRIDE).exists())

    def test_assigned_untouched_does_not_block_transitional(self):
        """TRANSITIONAL COMPATIBILITY (owner 2026-07-04, B-now): auto-assigned
        workers who never touched the stage auto-cancel exactly as before
        (legacy F3) — they must NOT block, because create_adda still
        auto-assigns every skilled user. DELETE this test (and the guard's
        transitional filter) when the explicit-assignment migration lands."""
        self._assign(self.worker)                   # ASSIGNED, never engaged
        advance_to_next_stage(self.adda, self.admin)  # must not raise
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.CANCELLED)

    def test_no_assigned_workers_advances(self):
        # create_adda auto-assigns every cutting-master-skilled user to
        # layering — explicitly clear the roster (manager un-assign flow),
        # THEN completion must pass the guard.
        wts.set_stage_workers(self.sr, [])
        advance_to_next_stage(self.adda, self.admin)   # must not raise
        self.adda.refresh_from_db()

    def test_all_reported_advances_without_cancelling(self):
        self._assign(self.worker)
        self._complete_report(self.worker)
        advance_to_next_stage(self.adda, self.admin)
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.COMPLETED)

    # ── override path ─────────────────────────────────────────────────────

    def test_super_admin_override_with_reason(self):
        self._assign(self.worker)
        self._start_work(self.worker)               # engaged → guard live
        advance_to_next_stage(self.adda, self.admin,
                              override_pending_reason='worker absconded mid-Adda')
        # Task cancelled WITH the reason stamped.
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.CANCELLED)
        self.assertIn('worker absconded mid-Adda', task.notes)
        # Audit-complete history event (owner instruction).
        ev = AddaHistory.objects.get(
            adda=self.adda,
            change_type=AddaHistory.ChangeType.COMPLETION_OVERRIDE)
        self.assertEqual(ev.actor, self.admin)
        self.assertEqual(ev.stage_record_id, self.sr.pk)
        self.assertEqual(ev.metadata['pending_count'], 1)
        self.assertEqual(ev.metadata['reason'], 'worker absconded mid-Adda')
        self.assertIn('w@r3.test', ev.metadata['pending_workers'][0])
        self.assertTrue(ev.metadata['stage'])
        self.assertIsNotNone(ev.created_at)       # timestamp on the row itself

    def test_manager_cannot_override(self):
        self._assign(self.worker)
        self._start_work(self.worker)
        with self.assertRaises(PermissionDenied):
            advance_to_next_stage(self.adda, self.manager,
                                  override_pending_reason='trying anyway')
        # Refusal leaves no trace and cancels nothing.
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.IN_PROGRESS)
        self.assertFalse(AddaHistory.objects.filter(
            change_type=AddaHistory.ChangeType.COMPLETION_OVERRIDE).exists())

    def test_empty_reason_refused(self):
        self._assign(self.worker)
        self._start_work(self.worker)
        with self.assertRaises(ValidationError):
            advance_to_next_stage(self.adda, self.admin,
                                  override_pending_reason='   ')
        task = self.sr.worker_tasks.get(worker=self.worker)
        self.assertEqual(task.status, WorkerStageTask.Status.IN_PROGRESS)

    # ── PAY-2 interplay ───────────────────────────────────────────────────

    def test_payable_stage_partial_reports_block_then_override(self):
        # Payable + ungrouped so PAY-2 is live too (R2 config shape).
        self.adda.product.workflow_stages.update(
            cost_method='per_layer', cost_rate=Decimal('10'),
            cost_billed_at=None, credits_workers=True)
        w2 = _user('w2@r3.test', 'worker')
        self._assign(self.worker, w2)
        self._complete_report(self.worker)          # PAY-2 satisfied by one
        self._start_work(w2, qty='5')               # w2 engaged, not submitted
        with self.assertRaises(ValidationError):    # C3 still blocks on w2
            advance_to_next_stage(self.adda, self.admin)
        advance_to_next_stage(self.adda, self.admin,
                              override_pending_reason='w2 on leave, stage must move')
        self.assertEqual(
            self.sr.worker_tasks.get(worker=w2).status,
            WorkerStageTask.Status.CANCELLED)
        self.assertEqual(                            # completed work untouched
            self.sr.worker_tasks.get(worker=self.worker).status,
            WorkerStageTask.Status.COMPLETED)