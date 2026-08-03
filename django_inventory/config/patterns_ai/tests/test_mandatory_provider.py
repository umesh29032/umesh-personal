"""Registry #6 (GAP-1 grain): the REAL Blueprint-side derivation of mandatory
Production Components — patterns_ai-side test (this direction may import
production; the reverse is refused by test_purity)."""
from django.test import TestCase

from patterns_ai.models import PatternPiece
from patterns_ai.services.mandatory_patterns_provider import (
    mandatory_pattern_ids_for_product)
from production.models import Product, ProductPattern
from production.services import pool_service


class MandatoryProviderTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code='MPP', name='Provider')

    def _piece(self, name, optional):
        pat = ProductPattern.objects.create(code=f'MPP-{name.upper()}',
                                            name=f'MPP {name}')
        PatternPiece.objects.create(product=self.product, pattern=pat,
                                    fabric_group='body',
                                    is_optional=optional)
        return pat

    def test_mandatory_is_any_non_optional_piece(self):
        # (PatternPiece is unique per (product, pattern) — one flag per
        # component today; the provider's any-non-optional rule is written
        # for a future multi-piece grain but reduces to the row's flag.)
        body = self._piece('Body', optional=False)
        loop = self._piece('Loop', optional=True)
        ids = mandatory_pattern_ids_for_product(self.product)
        self.assertIn(body.pk, ids)
        self.assertNotIn(loop.pk, ids)

    def test_registry_is_wired_by_app_ready(self):
        # apps.py ready() registered the provider on the production hook
        self.assertIs(pool_service.MANDATORY_PATTERNS_PROVIDER,
                      mandatory_pattern_ids_for_product)
