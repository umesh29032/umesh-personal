"""PA-05A-4: ProductPatternsEditView must not 500 on a tampered/non-numeric
`pieces_count`. `int('abc')` would raise ValueError; the view now safe-parses
(clamp ≥1, fall back to 1)."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import Role
from production.models import Product, ProductPattern, ProductPatternAssignment


class PatternPiecesCountSafeParseTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='ppc-admin@t.com', password='pw', is_superuser=True, is_staff=True)
        self.admin.role = Role.objects.get(code='super_admin')
        self.admin.save()
        self.client.force_login(self.admin)
        self.product = Product.objects.create(code='PPC', name='PPC Prod')
        self.pattern = ProductPattern.objects.create(code='front', name='Front Panel')
        self.url = reverse('production:product-patterns', args=[self.product.pk])

    def test_non_numeric_pieces_count_does_not_500(self):
        resp = self.client.post(self.url, {
            'action': 'add', 'pattern': self.pattern.pk, 'pieces_count': 'abc',
        })
        self.assertIn(resp.status_code, (302, 200))   # graceful, not 500
        a = ProductPatternAssignment.objects.filter(
            product=self.product, pattern=self.pattern).first()
        self.assertIsNotNone(a)
        self.assertEqual(a.pieces_count, 1)            # fell back to 1

    def test_negative_pieces_count_clamped_to_one(self):
        self.client.post(self.url, {
            'action': 'add', 'pattern': self.pattern.pk, 'pieces_count': '-5',
        })
        a = ProductPatternAssignment.objects.get(
            product=self.product, pattern=self.pattern)
        self.assertEqual(a.pieces_count, 1)
