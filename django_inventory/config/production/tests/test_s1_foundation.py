"""Foundation S1 — AddaStageRoleRate (resolved-rate snapshot, role_snapshot,
first-completion lock, edit-until-lock, live-fallback) + resolved_payable_rate.

Contracts (addendum): M-5 frozen-at-stage-start + role snapshot; contract 1
(immutable-after-first-completion, lock-serialized edit/complete); contract 2
(snapshot mandatory for S1 records, warn-fallback only for pre-S2); grouped→₹0.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expense.models import StageWorkAssignment
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, AddaStageRoleRate, Product, RateCorrectionAudit, Stage,
    WorkflowStage, WorkflowStageRoleRate, WorkerStageTask,
)
from production.services import cost_service, stage_rate_service
from production.services._shared import reopen_stage_record
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _worker(email, code='worker'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code)
    u.save()
    return u


def _stage_record(*, cost_rate='5', grouped=False, code='s1s'):
    product = Product.objects.create(code='S1' + code, name='S1 ' + code)
    stage, _ = Stage.objects.get_or_create(code=code, defaults={'name': code})
    payer = None
    if grouped:
        payer = WorkflowStage.objects.create(
            product=product, stage=Stage.objects.get_or_create(code=code + 'p', defaults={'name': 'payer'})[0],
            order=2, cost_rate=Decimal('9'), credits_workers=True)
    ws = WorkflowStage.objects.create(
        product=product, stage=stage, order=1,
        cost_rate=Decimal(cost_rate), credits_workers=True,
        cost_billed_at=payer)
    adda = Adda.objects.create(code='S1-' + code, product=product, status=Adda.Status.IN_PROGRESS)
    sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws, started_at=timezone.now())
    return sr, ws


class ResolvedPayableRateTests(TestCase):
    def test_base_rate(self):
        sr, ws = _stage_record(cost_rate='5')
        self.assertEqual(cost_service.resolved_payable_rate(ws, Role.objects.get(code='worker')), Decimal('5'))

    def test_role_override(self):
        sr, ws = _stage_record(cost_rate='5', code='ovr')
        r = Role.objects.get(code='worker')
        WorkflowStageRoleRate.objects.create(workflow_stage=ws, role=r, cost_rate=Decimal('7'))
        self.assertEqual(cost_service.resolved_payable_rate(ws, r), Decimal('7'))

    def test_grouped_member_is_zero(self):
        sr, ws = _stage_record(cost_rate='5', grouped=True, code='grp')
        # grouped MEMBER → 0 even though cost_rate=5 (paid via payer; never twice)
        self.assertEqual(cost_service.resolved_payable_rate(ws, Role.objects.get(code='worker')), Decimal('0'))


class SnapshotTests(TestCase):
    def test_ensure_creates_resolved_snapshots_per_production_role(self):
        sr, ws = _stage_record(cost_rate='5', code='snap')
        stage_rate_service.ensure_stage_role_rates(sr)
        rows = AddaStageRoleRate.objects.filter(stage_record=sr)
        self.assertEqual(rows.count(), 3)   # super_admin, manager, worker
        self.assertTrue(all(r.rate == Decimal('5') for r in rows))
        self.assertTrue(all(r.locked_at is None for r in rows))

    def test_ensure_is_idempotent(self):
        sr, ws = _stage_record(code='idem')
        self.assertEqual(stage_rate_service.ensure_stage_role_rates(sr), 3)
        self.assertEqual(stage_rate_service.ensure_stage_role_rates(sr), 0)   # no-op second time

    def test_grouped_snapshot_is_zero(self):
        sr, ws = _stage_record(cost_rate='5', grouped=True, code='gsnap')
        stage_rate_service.ensure_stage_role_rates(sr)
        self.assertTrue(all(r.rate == Decimal('0') for r in AddaStageRoleRate.objects.filter(stage_record=sr)))


class CompleteFreezeTests(TestCase):
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='cmp')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.w = _worker('s1-cmp@test')
        set_stage_workers(self.sr, [self.w.pk])
        self.task = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w)
        report_contributions(self.task, [{'reported_quantity': '10'}], actor=self.w)

    def test_complete_freezes_rate_role_and_locks(self):
        complete_worker_task(self.task, actor=self.w)
        c = self.task.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('5'))           # frozen from snapshot
        self.assertEqual(c.expected_earning, Decimal('50.00'))    # 10 × 5
        self.assertEqual(c.role_snapshot, self.w.role)            # role frozen
        row = AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.w.role)
        self.assertIsNotNone(row.locked_at)                       # first completion → immutable

    def test_role_change_after_lock_does_not_reprice(self):
        # M-10 integrity: freeze, then change the live workflow rate — frozen stays.
        complete_worker_task(self.task, actor=self.w)
        self.ws.cost_rate = Decimal('999')
        self.ws.save(update_fields=['cost_rate'])
        c = self.task.contributions.get()
        c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('5'))           # NOT 999
        # and the frozen snapshot is unchanged
        self.assertEqual(AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.w.role).rate, Decimal('5'))

    def test_live_fallback_warns_when_snapshot_absent(self):
        # Simulate a pre-S2 record: delete snapshots → complete must still pay the
        # resolved rate (live fallback) and not crash.
        AddaStageRoleRate.objects.filter(stage_record=self.sr).delete()
        with self.assertLogs('production', level='WARNING') as cm:
            complete_worker_task(self.task, actor=self.w)
        self.assertEqual(self.task.contributions.get().expected_rate, Decimal('5'))
        self.assertTrue(any('snapshot_missing_at_complete' in m or 'live_fallback' in m for m in cm.output))


class EditUntilLockTests(TestCase):
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='edit')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.mgr = _worker('s1-mgr@test', code='manager')
        self.worker_role = Role.objects.get(code='worker')

    def test_edit_before_lock(self):
        stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)
        self.assertEqual(AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.worker_role).rate, Decimal('8'))

    def test_edit_refuses_non_management(self):
        with self.assertRaises(PermissionDenied):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=_worker('s1-w2@test'))

    def test_edit_refuses_negative(self):
        with self.assertRaises(ValidationError):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('-1'), actor=self.mgr)

    def test_edit_refuses_after_lock(self):
        row = AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.worker_role)
        stage_rate_service.mark_locked(row)
        with self.assertRaisesMessage(ValidationError, 'locked'):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)

    def test_edited_rate_is_what_complete_freezes(self):
        stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)
        w = _worker('s1-ew@test')
        set_stage_workers(self.sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=self.sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)
        self.assertEqual(t.contributions.get().expected_rate, Decimal('8'))   # edited, not 5


class RerateTests(TestCase):
    """S1.1: super-admin re-rate override (Option 1) — keeps the M1 completion lock
    for normal edits, but a super-admin can correct UNTIL settlement with auto-recalc."""
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='rr')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.w = _worker('s1-rr-w@test')                    # role=worker
        self.admin = _worker('s1-rr-admin@test', code='super_admin')
        self.worker_role = Role.objects.get(code='worker')
        set_stage_workers(self.sr, [self.w.pk])
        self.task = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w)
        report_contributions(self.task, [{'reported_quantity': '10'}], actor=self.w)
        complete_worker_task(self.task, actor=self.w)       # freezes rate=5, LOCKS worker row

    def test_recalcs_completed_unsettled(self):
        row, n = stage_rate_service.rerate_stage_role(
            self.sr, self.worker_role, Decimal('8'), actor=self.admin, reason='wrong rate at setup')
        self.assertEqual(n, 1)
        c = self.task.contributions.get(); c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('8'))
        self.assertEqual(c.expected_earning, Decimal('80.00'))   # 10 × 8
        self.assertEqual(AddaStageRoleRate.objects.get(
            stage_record=self.sr, role=self.worker_role).rate, Decimal('8'))

    def test_overrides_the_completion_lock(self):
        # The worker row IS locked (a completion happened) → edit_until_lock refuses,
        # but rerate (super-admin) overrides until settlement.
        self.assertIsNotNone(AddaStageRoleRate.objects.get(
            stage_record=self.sr, role=self.worker_role).locked_at)
        with self.assertRaises(ValidationError):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('7'), actor=self.admin)
        stage_rate_service.rerate_stage_role(self.sr, self.worker_role, Decimal('7'), actor=self.admin, reason='x')
        self.assertEqual(AddaStageRoleRate.objects.get(
            stage_record=self.sr, role=self.worker_role).rate, Decimal('7'))

    def test_refuses_non_super_admin(self):
        mgr = _worker('s1-rr-mgr@test', code='manager')
        with self.assertRaises(PermissionDenied):
            stage_rate_service.rerate_stage_role(self.sr, self.worker_role, Decimal('8'), actor=mgr, reason='x')

    def test_refuses_empty_reason(self):
        with self.assertRaisesMessage(ValidationError, 'reason'):
            stage_rate_service.rerate_stage_role(self.sr, self.worker_role, Decimal('8'), actor=self.admin, reason='   ')

    def test_refuses_negative(self):
        with self.assertRaises(ValidationError):
            stage_rate_service.rerate_stage_role(self.sr, self.worker_role, Decimal('-1'), actor=self.admin, reason='x')

    def test_refuses_when_actively_settled(self):
        c = self.task.contributions.get()
        swa = StageWorkAssignment.objects.create(
            stage_record=self.sr, worker=self.w, entered_by=self.w, allocated_quantity=Decimal('10'),
            earning_rate_snapshot=Decimal('5'), earning_amount_snapshot=Decimal('50'))
        c.settlement_line = swa; c.save(update_fields=['settlement_line'])
        with self.assertRaisesMessage(ValidationError, 'settlement'):
            stage_rate_service.rerate_stage_role(self.sr, self.worker_role, Decimal('8'), actor=self.admin, reason='x')

    def test_allowed_after_settlement_voided(self):
        c = self.task.contributions.get()
        swa = StageWorkAssignment.objects.create(
            stage_record=self.sr, worker=self.w, entered_by=self.w, allocated_quantity=Decimal('10'),
            earning_rate_snapshot=Decimal('5'), earning_amount_snapshot=Decimal('50'),
            voided_at=timezone.now())                       # reversed → re-rate allowed again
        c.settlement_line = swa; c.save(update_fields=['settlement_line'])
        row, n = stage_rate_service.rerate_stage_role(
            self.sr, self.worker_role, Decimal('9'), actor=self.admin, reason='re-rate after reversal')
        self.assertEqual(n, 1)
        c.refresh_from_db(); self.assertEqual(c.expected_rate, Decimal('9'))

    def test_writes_append_only_audit(self):
        stage_rate_service.rerate_stage_role(
            self.sr, self.worker_role, Decimal('8'), actor=self.admin, reason='typo at setup')
        a = RateCorrectionAudit.objects.get(stage_record=self.sr, role=self.worker_role)
        self.assertEqual(a.old_rate, Decimal('5'))
        self.assertEqual(a.new_rate, Decimal('8'))
        self.assertEqual(a.recalc_count, 1)
        self.assertEqual(a.actor, self.admin)
        self.assertEqual(a.reason, 'typo at setup')


class CreationSiteWiringTests(TestCase):
    """M4: every AddaStageRecord creation path must produce rate snapshots — not just
    the ensure_stage_role_rates helper. Catches a removed call at a creation site."""
    def test_create_adda_snapshots_first_stage(self):
        from production.services import create_adda
        product = Product.objects.create(code='WIRE', name='Wire')
        stage, _ = Stage.objects.get_or_create(code='layering', defaults={'name': 'Layering'})
        WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                     cost_rate=Decimal('4'), credits_workers=True)
        admin = _worker('wire-admin@test', code='super_admin')
        # create_adda requires a cutting_master-skilled user to exist.
        from accounts.models import Skill
        admin.skills.add(Skill.objects.get_or_create(
            name='cutting_master', defaults={'label': 'Cutting Master'})[0])
        adda = create_adda(user=admin, product=product)
        sr = adda.stage_records.first()
        self.assertIsNotNone(sr)
        rows = AddaStageRoleRate.objects.filter(stage_record=sr)
        self.assertEqual(rows.count(), 3)                   # super_admin, manager, worker
        self.assertTrue(all(r.rate == Decimal('4') for r in rows))


class RerateUITests(TestCase):
    """S1.1 UI: thin super-admin 'Correct Rate' flow — gated + applies via the service."""
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='ui')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.adda = self.sr.adda
        self.admin = _worker('ui-admin@test', code='super_admin')
        self.mgr = _worker('ui-mgr@test', code='manager')
        self.worker_role = Role.objects.get(code='worker')

    def test_list_requires_super_admin(self):
        url = reverse('production:stage-rates', kwargs={'code': self.adda.code})
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_correct_post_applies_and_recalcs(self):
        w = _worker('ui-w@test'); set_stage_workers(self.sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=self.sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)
        url = reverse('production:stage-rate-correct', kwargs={
            'code': self.adda.code, 'sr_id': self.sr.pk, 'role_id': self.worker_role.pk})
        self.client.force_login(self.admin)
        resp = self.client.post(url, {'new_rate': '8', 'reason': 'ui correction', 'confirm': 'on'})
        self.assertEqual(resp.status_code, 302)
        c = t.contributions.get(); c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('8'))

    def test_correct_requires_confirm(self):
        url = reverse('production:stage-rate-correct', kwargs={
            'code': self.adda.code, 'sr_id': self.sr.pk, 'role_id': self.worker_role.pk})
        self.client.force_login(self.admin)
        resp = self.client.post(url, {'new_rate': '8', 'reason': 'no confirm'})   # confirm missing
        self.assertEqual(resp.status_code, 200)             # re-render with error, no redirect
        self.assertEqual(AddaStageRoleRate.objects.get(
            stage_record=self.sr, role=self.worker_role).rate, Decimal('5'))   # unchanged


class GroupedGuardTests(TestCase):
    """F2 (hostile-review fix): grouped→0 is a STRUCTURAL invariant — a grouped member
    never pays, even if its AddaStageRoleRate snapshot is a STALE non-zero (frozen before
    the stage was grouped). Grouped status wins at complete, rerate, and the money boundary."""

    def _ungrouped_then_grouped(self, code='f2g'):
        product = Product.objects.create(code='F2' + code, name='F2 ' + code)
        stage, _ = Stage.objects.get_or_create(code=code, defaults={'name': code})
        payer_stage, _ = Stage.objects.get_or_create(code=code + 'p', defaults={'name': 'payer'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('5'), credits_workers=True)
        payer = WorkflowStage.objects.create(product=product, stage=payer_stage, order=2,
                                             cost_rate=Decimal('9'), credits_workers=True)
        adda = Adda.objects.create(code='F2-' + code, product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws, started_at=timezone.now())
        stage_rate_service.ensure_stage_role_rates(sr)        # snapshot rate=5 (UNGROUPED)
        ws.cost_billed_at = payer; ws.save(update_fields=['cost_billed_at'])   # group it AFTER
        return sr, ws

    def test_snapshot_stale_nonzero_but_complete_pays_zero(self):
        sr, ws = self._ungrouped_then_grouped()
        worker_role = Role.objects.get(code='worker')
        # the frozen snapshot is a STALE non-zero (5) — grouped guard must override it.
        self.assertEqual(AddaStageRoleRate.objects.get(stage_record=sr, role=worker_role).rate, Decimal('5'))
        w = _worker('f2g-w@test')
        set_stage_workers(sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)
        c = t.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('0'))        # grouped wins over stale 5
        self.assertEqual(c.expected_earning, Decimal('0.00'))

    def test_rerate_on_grouped_stage_pays_zero(self):
        sr, ws = self._ungrouped_then_grouped(code='f2r')
        w = _worker('f2r-w@test')
        set_stage_workers(sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)
        admin = _worker('f2r-adm@test', code='super_admin')
        stage_rate_service.rerate_stage_role(sr, Role.objects.get(code='worker'),
                                             Decimal('8'), actor=admin, reason='attempt re-rate')
        c = t.contributions.get(); c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('0'))        # grouped wins over rerate 8
        self.assertEqual(c.expected_earning, Decimal('0.00'))

    def test_effective_pay_rate_helper(self):
        sr, ws = self._ungrouped_then_grouped(code='f2h')
        self.assertEqual(cost_service.effective_pay_rate(ws, Decimal('5')), Decimal('0'))   # grouped
        ungrouped_sr, ungrouped_ws = _stage_record(cost_rate='5', code='f2hu')
        self.assertEqual(cost_service.effective_pay_rate(ungrouped_ws, Decimal('5')), Decimal('5'))


class ReopenRefloatTests(TestCase):
    """F4 (hostile-review fix): reopen re-floats the worker rate SYMMETRICALLY with the
    manufacturing-cost re-freeze — re-resolve + unlock AddaStageRoleRate, so re-complete
    re-freezes at the current resolved value (grouped→0 via the F2 structural guard)."""

    def _completed_stage(self, *, cost_rate='5', code='f4'):
        sr, ws = _stage_record(cost_rate=cost_rate, code=code)
        stage_rate_service.ensure_stage_role_rates(sr)
        w = _worker(f'f4-{code}@test')
        set_stage_workers(sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)                 # freeze rate=5, lock the row
        sr.completed_at = timezone.now(); sr.save(update_fields=['completed_at'])  # stage done
        return sr, ws

    def test_reopen_refloats_and_unlocks(self):
        sr, ws = self._completed_stage()
        worker_role = Role.objects.get(code='worker')
        row = AddaStageRoleRate.objects.get(stage_record=sr, role=worker_role)
        self.assertEqual(row.rate, Decimal('5')); self.assertIsNotNone(row.locked_at)
        ws.cost_rate = Decimal('8'); ws.save(update_fields=['cost_rate'])   # config changed
        admin = _worker('f4-adm@test', code='super_admin')
        reopen_stage_record(adda=sr.adda, stage_code=ws.stage.code,
                            stage_label=ws.stage.name, user=admin)
        row.refresh_from_db()
        self.assertEqual(row.rate, Decimal('8'))         # re-resolved from current config
        self.assertIsNone(row.locked_at)                 # unlocked
        # re-complete would re-freeze at the new resolved value:
        rate, _ = stage_rate_service.frozen_rate_for(sr, worker_role)
        self.assertEqual(rate, Decimal('8'))

    def test_reopen_grouped_refloats_to_zero(self):
        sr, ws = self._completed_stage(code='f4g')
        payer_stage, _ = Stage.objects.get_or_create(code='f4gp', defaults={'name': 'payer'})
        payer = WorkflowStage.objects.create(product=ws.product, stage=payer_stage, order=9,
                                             cost_rate=Decimal('9'))
        ws.cost_billed_at = payer; ws.save(update_fields=['cost_billed_at'])   # grouped now
        admin = _worker('f4g-adm@test', code='super_admin')
        reopen_stage_record(adda=sr.adda, stage_code=ws.stage.code,
                            stage_label=ws.stage.name, user=admin)
        row = AddaStageRoleRate.objects.get(stage_record=sr, role=Role.objects.get(code='worker'))
        self.assertEqual(row.rate, Decimal('0'))         # grouped re-resolves to 0
        self.assertIsNone(row.locked_at)
