"""R6 (roadmap phase) tests — verified-quantity audit trail (PDD §31.1-F6).

`set_verified_quantity` now emits a DB-resident AddaHistory event
(VERIFIED_QTY_CORRECTED) carrying who/old/new/worker/stage/when — closing the
production-audit "verified-qty no-audit" debt. No-ops and refused corrections
emit NOTHING; the existing guards are regression-pinned.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
    set_verified_quantity,
)
from tracking.models import AddaHistory


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class VerifiedQtyAuditTests(TestCase):
    def setUp(self):
        self.mgmt = _role_user('r6-mgmt@test', 'manager')
        self.worker = _role_user('r6-w@test', 'worker')
        product = Product.objects.create(code='R6A', name='R6 Audit P')
        stage, _ = Stage.objects.get_or_create(
            code='r6a_stage', defaults={'name': 'R6A Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(code='R6A-001', product=product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(self.sr, [self.worker.pk])
        task = self.sr.worker_tasks.get(worker=self.worker)
        report_contributions(task, [{'reported_quantity': '20'}],
                             actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        self.c = task.contributions.get()

    def _events(self):
        return AddaHistory.objects.filter(
            adda=self.adda,
            change_type=AddaHistory.ChangeType.VERIFIED_QTY_CORRECTED)

    def test_set_emits_full_audit_event(self):
        set_verified_quantity(self.c, '18', actor=self.mgmt)
        ev = self._events().get()
        self.assertEqual(ev.actor, self.mgmt)
        self.assertEqual(ev.stage_record, self.sr)
        self.assertIsNotNone(ev.created_at)
        m = ev.metadata
        self.assertEqual(m['contribution'], self.c.pk)
        self.assertEqual(m['worker_id'], self.worker.pk)
        self.assertEqual(m['stage'], 'R6A Stage')
        self.assertEqual(m['reported'], '20.00')
        self.assertIsNone(m['old'])                    # first correction
        self.assertEqual(m['new'], '18')

    def test_clear_emits_event_with_new_none(self):
        set_verified_quantity(self.c, '18', actor=self.mgmt)
        set_verified_quantity(self.c, None, actor=self.mgmt)
        events = list(self._events().order_by('created_at'))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1].metadata['old'], '18.00')
        self.assertIsNone(events[1].metadata['new'])
        self.c.refresh_from_db()
        self.assertIsNone(self.c.verified_quantity)

    def test_noop_emits_nothing(self):
        set_verified_quantity(self.c, '18', actor=self.mgmt)
        set_verified_quantity(self.c, '18.00', actor=self.mgmt)  # same value
        self.assertEqual(self._events().count(), 1)
        set_verified_quantity(self.c, None, actor=self.mgmt)
        set_verified_quantity(self.c, None, actor=self.mgmt)     # clear twice
        self.assertEqual(self._events().count(), 2)

    def test_refusals_emit_nothing_guards_unchanged(self):
        with self.assertRaises(PermissionDenied):
            set_verified_quantity(self.c, '18', actor=self.worker)
        with self.assertRaises(ValidationError):
            set_verified_quantity(self.c, '-1', actor=self.mgmt)
        with self.assertRaises(ValidationError):
            set_verified_quantity(self.c, 'abc', actor=self.mgmt)
        self.assertEqual(self._events().count(), 0)
        self.c.refresh_from_db()
        self.assertIsNone(self.c.verified_quantity)
