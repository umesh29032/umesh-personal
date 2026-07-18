"""R10-A pins — machine register + possession windows + the frozen-model
Stage columns. Frozen-architecture guards included: money isolation
(machines never imports expense/settlement) and the category fence
(engine/money paths never read Stage.category).
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from machines.models import Machine, MachineAssignment
from machines.services import machine_service
from production.models import MachineType, Stage, StageCategory


def _user(email, role_code='worker'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class StageOperationModelTests(TestCase):
    """M1: seeds + defaults + the work-type pair constraint."""

    def test_seeded_categories_and_cutting_machine_type(self):
        self.assertEqual(
            list(StageCategory.objects.values_list('code', flat=True)),
            ['pre_production', 'stitching', 'finishing', 'dispatch'])
        self.assertTrue(MachineType.objects.filter(code='cutting_machine').exists())

    def test_owner_defaults_applied(self):
        by_code = {s.code: s for s in Stage.objects.filter(
            code__in=['layering', 'cutting_pattern', 'cutting', 'barcode_generation'])}
        self.assertEqual(by_code['layering'].work_type, 'manual')
        self.assertIsNone(by_code['layering'].machine_type)
        self.assertEqual(by_code['cutting'].work_type, 'machine')
        self.assertEqual(by_code['cutting'].machine_type.code, 'cutting_machine')
        for s in by_code.values():
            self.assertEqual(s.category.code, 'pre_production')

    def test_pair_constraint_blocks_invalid_rows(self):
        from django.db import IntegrityError, transaction
        mt = MachineType.objects.get(code='cutting_machine')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Stage.objects.create(code='bad-machine', name='X', work_type='machine')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Stage.objects.create(code='bad-manual', name='X',
                                 work_type='manual', machine_type=mt)

    def test_machine_type_reusable_across_stages(self):
        mt = MachineType.objects.create(code='overlock_machine', name='Overlock Machine')
        Stage.objects.create(code='overlock', name='Overlock',
                             work_type='machine', machine_type=mt)
        Stage.objects.create(code='edge_finish', name='Edge Finishing',
                             work_type='machine', machine_type=mt)
        self.assertEqual(mt.stages.count(), 2)

    def test_category_fence_no_engine_reads(self):
        """Frozen rule 2 guard: no business service/money path reads
        Stage.category — display surfaces only."""
        import pathlib
        import re
        # Engine paths only: expense's WorkerLedgerEntry has its OWN unrelated
        # `category` field (ledger entry class) — the fence is about
        # Stage.category, which only Stage objects in the production engine
        # could ever read.
        roots = [
            pathlib.Path('production/services'),
            pathlib.Path('production/stages'),
        ]
        pat = re.compile(r'\.category\b|category__')
        offenders = []
        for root in roots:
            for f in root.rglob('*.py'):
                if pat.search(f.read_text()):
                    offenders.append(str(f))
        self.assertEqual(offenders, [])


class MachineServiceTests(TestCase):
    def setUp(self):
        self.mt = MachineType.objects.get(code='cutting_machine')
        self.mgr = _user('r10-mgr@test', 'super_admin')
        self.w1 = _user('r10-w1@test')
        self.w2 = _user('r10-w2@test')
        self.m = machine_service.create_machine(
            code='CM-001', name='Cutter #1', machine_type=self.mt, user=self.mgr)

    def test_duplicate_code_refused(self):
        with self.assertRaises(ValidationError):
            machine_service.create_machine(
                code='cm-001', name='dup', machine_type=self.mt)

    def test_code_immutable_after_assignment_history(self):
        machine_service.update_machine(self.m, code='CM-100')   # no history yet → ok
        machine_service.assign(machine=self.m, worker=self.w1)
        with self.assertRaises(ValidationError):
            machine_service.update_machine(self.m, code='CM-200')

    def test_assign_release_lifecycle_and_second_open_refused(self):
        a = machine_service.assign(machine=self.m, worker=self.w1)
        self.assertTrue(a.is_open)
        with self.assertRaises(ValidationError) as ctx:
            machine_service.assign(machine=self.m, worker=self.w2)
        self.assertIn('currently with', str(ctx.exception))   # names the holder
        machine_service.release(a)
        b = machine_service.assign(machine=self.m, worker=self.w2)
        self.assertEqual(
            MachineAssignment.objects.filter(machine=self.m).count(), 2)
        self.assertTrue(b.is_open)

    def test_same_day_sequential_windows(self):
        """§0.3 sharing scenario — DateTime windows allow two holders in one day."""
        start = timezone.now().replace(hour=8, minute=0)
        a = machine_service.assign(machine=self.m, worker=self.w1, start_at=start)
        machine_service.release(a, end_at=start + timedelta(hours=4))
        b = machine_service.assign(
            machine=self.m, worker=self.w2, start_at=start + timedelta(hours=4))
        self.assertTrue(b.is_open)

    def test_inactive_machine_refuses_assignment(self):
        machine_service.update_machine(self.m, status='maintenance')
        with self.assertRaises(ValidationError):
            machine_service.assign(machine=self.m, worker=self.w1)

    def test_release_before_start_refused(self):
        a = machine_service.assign(machine=self.m, worker=self.w1)
        with self.assertRaises(ValidationError):
            machine_service.release(a, end_at=a.start_at - timedelta(minutes=5))

    def test_counts(self):
        machine_service.create_machine(
            code='CM-002', name='Cutter #2', machine_type=self.mt,
            status='maintenance')
        machine_service.assign(machine=self.m, worker=self.w1)
        c = machine_service.register_counts()
        self.assertEqual((c['total'], c['active'], c['maintenance'], c['assigned_now']),
                         (2, 1, 1, 1))


class MachineViewsTests(TestCase):
    def setUp(self):
        self.mt = MachineType.objects.get(code='cutting_machine')
        self.mgr = _user('r10-vmgr@test', 'manager')
        self.worker = _user('r10-vw@test')

    def test_management_can_use_register(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(reverse('machines:list')).status_code, 200)
        resp = self.client.post(reverse('machines:add'), {
            'code': 'CM-010', 'name': 'Cutter #10',
            'machine_type': self.mt.pk, 'status': 'active', 'notes': ''})
        self.assertEqual(resp.status_code, 302)
        m = Machine.objects.get(code='CM-010')
        resp = self.client.post(reverse('machines:assign', args=[m.pk]),
                                {'worker': self.worker.pk})
        self.assertEqual(resp.status_code, 302)
        self.assertIsNotNone(machine_service.open_assignment_for(m))

    def test_edit_form_cannot_rename_code_with_history(self):
        """MGT-F-1 pin: bound ModelForm mutates instance.code before the service
        guard runs — guard must compare the DB row, not the in-memory instance."""
        self.client.force_login(self.mgr)
        m = machine_service.create_machine(
            code='CM-011', name='Cutter #11', machine_type=self.mt)
        machine_service.assign(machine=m, worker=self.worker)  # history exists
        resp = self.client.post(reverse('machines:edit', args=[m.pk]), {
            'code': 'CM-999', 'name': m.name,
            'machine_type': self.mt.pk, 'status': 'active', 'notes': ''})
        self.assertEqual(resp.status_code, 200)  # re-rendered form, not saved
        self.assertContains(resp, 'immutable')
        m.refresh_from_db()
        self.assertEqual(m.code, 'CM-011')

    def test_edit_form_renames_code_without_history(self):
        """MGT-F-1 companion: no assignment history → rename stays allowed."""
        self.client.force_login(self.mgr)
        m = machine_service.create_machine(
            code='CM-012', name='Cutter #12', machine_type=self.mt)
        resp = self.client.post(reverse('machines:edit', args=[m.pk]), {
            'code': 'CM-013', 'name': m.name,
            'machine_type': self.mt.pk, 'status': 'active', 'notes': ''})
        self.assertEqual(resp.status_code, 302)
        m.refresh_from_db()
        self.assertEqual(m.code, 'CM-013')

    def test_worker_403_everywhere(self):
        self.client.force_login(self.worker)
        for name, args in (('machines:list', []), ('machines:add', [])):
            self.assertEqual(
                self.client.get(reverse(name, args=args)).status_code, 403, name)

    def test_money_isolation_grep(self):
        """Frozen rule 6: the machines app never touches money modules."""
        import pathlib
        import re
        pat = re.compile(
            r'^\s*(from|import)\s+(expense|production\.services\.(cost_service|stage_rate_service))',
            re.M)
        offenders = [
            str(f) for f in pathlib.Path('machines').rglob('*.py')
            if pat.search(f.read_text())
        ]
        self.assertEqual(offenders, [])
