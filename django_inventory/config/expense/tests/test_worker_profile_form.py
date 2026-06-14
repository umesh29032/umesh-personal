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
