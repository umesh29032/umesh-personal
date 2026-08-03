"""PA-05A-4 behavior, Phase-2 home: the Blueprint module must not 500 on
a tampered/non-numeric `pieces_count`. `int('abc')` would raise ValueError;
the Blueprint view safe-parses (clamp ≥1, fall back to 1) before the
atomic register_pattern_definition writer runs.
(Phase 2 conscious rework: the old ProductPatternsEditView retired — the
same guarantee now lives on `patterns_ai:blueprint` action=add.)"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import Role
from production.models import Product, ProductPatternAssignment


class PatternPiecesCountSafeParseTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='ppc-admin@t.com', password='pw', is_superuser=True,
            is_staff=True)
        self.admin.role = Role.objects.get(code='super_admin')
        self.admin.save()
        self.client.force_login(self.admin)
        self.product = Product.objects.create(code='PPC', name='PPC Prod')
        self.url = reverse('patterns_ai:blueprint')

    def _add(self, count_raw):
        return self.client.post(self.url, {
            'product': self.product.pk, 'action': 'add',
            'name': f'Front {count_raw}', 'fabric_group': 'body',
            'pieces_count': count_raw,
        })

    def test_non_numeric_pieces_count_does_not_500(self):
        resp = self._add('abc')
        self.assertIn(resp.status_code, (302, 200))   # graceful, not 500
        a = ProductPatternAssignment.objects.filter(
            product=self.product, pattern__name='Front abc').first()
        self.assertIsNotNone(a)
        self.assertEqual(a.pieces_count, 1)            # fell back to 1

    def test_negative_pieces_count_clamped_to_one(self):
        self._add('-5')
        a = ProductPatternAssignment.objects.get(
            product=self.product, pattern__name='Front -5')
        self.assertEqual(a.pieces_count, 1)
