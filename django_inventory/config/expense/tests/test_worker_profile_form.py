"""PA-06-1/PA-06-2: WorkerProfileForm validation (master-data integrity).

opening_advance feeds Advance Outstanding (money) → must be >= 0. Bank/IFSC/account
details are validated (blank-tolerant) so malformed payout data can't be saved.
"""
from django.test import TestCase

from expense.forms import WorkerProfileForm


class WorkerProfileFormValidationTests(TestCase):
    def _form(self, **over):
        data = {'opening_advance': '0'}
        data.update(over)
        return WorkerProfileForm(data=data)

    def test_negative_opening_advance_rejected(self):
        f = self._form(opening_advance='-5')
        self.assertFalse(f.is_valid())
        self.assertIn('opening_advance', f.errors)

    def test_zero_and_positive_opening_advance_ok(self):
        self.assertTrue(self._form(opening_advance='0').is_valid())
        self.assertTrue(self._form(opening_advance='500.00').is_valid())

    def test_minimal_no_bank_details_ok(self):
        self.assertTrue(self._form().is_valid())

    def test_bad_ifsc_rejected(self):
        f = self._form(bank_account_name='X', bank_account_number='123456789', bank_ifsc='BAD')
        self.assertFalse(f.is_valid())
        self.assertIn('bank_ifsc', f.errors)

    def test_good_ifsc_lowercase_normalised(self):
        f = self._form(bank_account_name='X', bank_account_number='123456789', bank_ifsc='hdfc0001234')
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['bank_ifsc'], 'HDFC0001234')

    def test_non_numeric_account_rejected(self):
        f = self._form(bank_account_name='X', bank_ifsc='HDFC0001234', bank_account_number='12AB56789')
        self.assertFalse(f.is_valid())
        self.assertIn('bank_account_number', f.errors)

    def test_account_number_without_ifsc_or_name_rejected(self):
        # half-entered bank details → failed payout; require the set together
        f = self._form(bank_account_number='123456789')
        self.assertFalse(f.is_valid())

    def test_full_valid_bank_details_ok(self):
        f = self._form(bank_account_name='Asha Devi', bank_account_number='123456789012',
                       bank_ifsc='HDFC0001234')
        self.assertTrue(f.is_valid(), f.errors)


class WorkerProfileServiceWriteTests(TestCase):
    """RCP-1A F3: the profile save goes through payroll_service.update_payout_profile
    (chokepoint — opening_advance is a displayed ₹ figure, WP-A informational).
    Behaviour preserved; opening_advance changes are audit-logged old→new + actor."""

    def setUp(self):
        from accounts.models import User
        from inventory.models import Role
        self.mgr = User.objects.create_user(email='wp-mgr@test.test', password='x')
        self.mgr.role = Role.objects.get(code='manager')
        self.mgr.save()
        self.worker = User.objects.create_user(email='wp-worker@test.test', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()

    def test_view_saves_via_service(self):
        from django.urls import reverse
        from expense.models import WorkerProfile
        self.client.force_login(self.mgr)
        resp = self.client.post(
            reverse('expense:worker-profile', args=[self.worker.pk]),
            {'opening_advance': '750.00'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            str(WorkerProfile.objects.get(user=self.worker).opening_advance),
            '750.00')

    def test_service_rejects_negative(self):
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from expense.services.payroll_service import update_payout_profile
        with self.assertRaises(ValidationError):
            update_payout_profile(self.worker, actor=self.mgr,
                                  opening_advance=Decimal('-1'))

    def test_opening_advance_change_is_logged(self):
        from decimal import Decimal
        from expense.services.payroll_service import update_payout_profile
        with self.assertLogs('expense.services.payroll_service', level='INFO') as logs:
            update_payout_profile(self.worker, actor=self.mgr,
                                  opening_advance=Decimal('100.00'))
        self.assertTrue(any('opening_advance.change' in l for l in logs.output))

    def test_view_no_longer_calls_form_save(self):
        # Law-4 pin: the money field is never written by a bare form.save().
        import inspect
        from expense import views as v
        src = inspect.getsource(v.WorkerProfileEditView.form_valid)
        code_lines = [l for l in src.splitlines() if not l.strip().startswith('#')]
        self.assertNotIn('form.save()', '\n'.join(code_lines))
        self.assertIn('update_payout_profile', src)
