"""View + access-scoping tests for the expense/payroll UI."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from expense.models import PayrollSettlement, WorkerAdvance, WorkerProfile


def _manager():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='mgr@v.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class ExpenseViewTests(TestCase):
    def setUp(self):
        self.mgr = _manager()
        self.worker = User.objects.create_user(email='w@v.test', password='x')
        self.other = User.objects.create_user(email='o@v.test', password='x')

    def test_worker_sees_own_earnings(self):
        self.client.force_login(self.worker)
        resp = self.client.get(reverse('expense:my-earnings'))
        self.assertEqual(resp.status_code, 200)

    def test_worker_can_view_own_detail_not_others(self):
        self.client.force_login(self.worker)
        own = self.client.get(reverse('expense:worker-detail', args=[self.worker.pk]))
        self.assertEqual(own.status_code, 200)
        other = self.client.get(reverse('expense:worker-detail', args=[self.other.pk]))
        self.assertEqual(other.status_code, 403)

    def test_overview_management_only(self):
        self.client.force_login(self.worker)
        denied = self.client.get(reverse('expense:payroll-overview'))
        self.assertNotEqual(denied.status_code, 200)   # redirect or 403
        self.client.force_login(self.mgr)
        ok = self.client.get(reverse('expense:payroll-overview'))
        self.assertEqual(ok.status_code, 200)

    def test_manager_records_advance(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(reverse('expense:advance-add'), {
            'worker': self.worker.pk, 'amount': '50', 'advance_date': '', 'notes': '',
        })
        self.assertEqual(resp.status_code, 302)   # redirect on success
        self.assertTrue(WorkerAdvance.objects.filter(worker=self.worker, amount=50).exists())

    def test_settlement_view_management_only(self):
        url = reverse('expense:settlement-create', args=[self.worker.pk])
        self.client.force_login(self.worker)
        self.assertNotEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_manager_settles_worker(self):
        # Give the worker earnings + an advance, then settle via the view.
        from decimal import Decimal
        from production.models import AddaStageRecord, Product
        from production.services import create_adda
        from expense.services import allocate_stage_work, record_advance, worker_balance, advance_outstanding
        adda = create_adda(self.mgr, product=Product.objects.get(code='NIKKAR'))
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=adda.current_stage)
        ws = sr.workflow_stage
        ws.cost_billed_at = None  # ungroup layering (migration 0026) to price it for earning tests
        ws.cost_rate = Decimal('2'); ws.save(update_fields=['cost_billed_at', 'cost_rate'])
        allocate_stage_work(user=self.mgr, stage_record=sr, worker=self.worker, allocated_quantity=10)  # payable 20
        adv = record_advance(user=self.mgr, worker=self.worker, amount=8)                                # outstanding 8

        self.client.force_login(self.mgr)
        url = reverse('expense:settlement-create', args=[self.worker.pk])
        resp = self.client.post(url, {
            'amount_paid': '15', 'method': 'cash', 'settlement_date': '', 'notes': '',
            f'recover_{adv.id}': '5',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(PayrollSettlement.objects.filter(worker=self.worker).exists())
        self.assertEqual(worker_balance(self.worker), Decimal('0.00'))         # 20 − 15 − 5
        self.assertEqual(advance_outstanding(self.worker), Decimal('3.00'))    # 8 − 5

    def test_manager_edits_worker_profile(self):
        self.client.force_login(self.mgr)
        url = reverse('expense:worker-profile', args=[self.worker.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url, {
            'phone': '9990001112', 'bank_account_name': 'W Test', 'bank_account_number': '123',
            'bank_ifsc': 'HDFC0001', 'upi_id': 'w@upi', 'joining_date': '', 'opening_advance': '0',
            'is_active': 'on', 'notes': '',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(WorkerProfile.objects.get(user=self.worker).phone, '9990001112')

    def test_worker_cannot_open_advance_form(self):
        self.client.force_login(self.worker)
        resp = self.client.get(reverse('expense:advance-add'))
        self.assertNotEqual(resp.status_code, 200)


class PayrollDataIsolationTests(TestCase):
    """Locks the IDOR invariant (OWASP A01): a worker can never READ or WRITE
    another worker's payroll — via view OR action. Only management can. Two
    workers are given REAL earnings so a regression that leaks data would fail."""

    def setUp(self):
        from production.models import AddaStageRecord, Product
        from production.services import create_adda
        from expense.services import allocate_stage_work
        self.mgr = _manager()
        self.a = User.objects.create_user(email='a@iso.test', password='x')
        self.b = User.objects.create_user(email='b@iso.test', password='x')
        adda = create_adda(self.mgr, product=Product.objects.get(code='NIKKAR'))
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=adda.current_stage)
        ws = sr.workflow_stage
        ws.cost_billed_at = None  # ungroup layering (migration 0026) to price it for earning tests
        ws.cost_rate = Decimal('2'); ws.save(update_fields=['cost_billed_at', 'cost_rate'])
        allocate_stage_work(user=self.mgr, stage_record=sr, worker=self.a, allocated_quantity=10)  # A earns 20
        allocate_stage_work(user=self.mgr, stage_record=sr, worker=self.b, allocated_quantity=7)   # B earns 14

    def test_worker_cannot_read_another_workers_detail(self):
        self.client.force_login(self.a)
        resp = self.client.get(reverse('expense:worker-detail', args=[self.b.pk]))
        self.assertEqual(resp.status_code, 403)   # never renders B's data

    def test_my_earnings_is_self_scoped(self):
        self.client.force_login(self.a)
        resp = self.client.get(reverse('expense:my-earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['viewed_worker'], self.a)
        self.assertEqual(resp.context['summary']['total_earnings'], Decimal('20.00'))  # A's, not B's 14

    def test_worker_cannot_settle_another_worker(self):
        # Write-side IDOR: a worker must not be able to create a settlement for B.
        self.client.force_login(self.a)
        url = reverse('expense:settlement-create', args=[self.b.pk])
        self.client.post(url, {'amount_paid': '5', 'method': 'cash', 'settlement_date': '', 'notes': ''})
        self.assertFalse(PayrollSettlement.objects.filter(worker=self.b).exists())

    def test_worker_cannot_record_advance_for_another(self):
        self.client.force_login(self.a)
        self.client.post(reverse('expense:advance-add'), {
            'worker': self.b.pk, 'amount': '50', 'advance_date': '', 'notes': '',
        })
        self.assertFalse(WorkerAdvance.objects.filter(worker=self.b).exists())
