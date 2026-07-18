"""Phase-6 M5 tests — Layout switcher (Rule F), profile prefills
(Rule G), no hidden work (Rule I)."""
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from production.models import Product
from patterns_ai.models import (GeneratedMarkerCandidate,
                                MarkerGenerationRun, ProductionLayout)
from patterns_ai.services import fabric_profile_service as fps

User = get_user_model()

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M5Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m5@test.local', password='x', role=mgr)
        cls.product = Product.objects.create(code='M5P', name='M5 Product')
        cls.l1 = cls._layout(cls.product)          # oldest
        cls.l2 = cls._layout(cls.product)
        cls.l3 = cls._layout(cls.product)          # newest

    @classmethod
    def _layout(cls, product, width=900):
        run = MarkerGenerationRun.objects.create(   # test fixture only
            product=product, usable_width_mm=width,
            params={'schema_version': 1, 'ratio': {}},
            pipeline_version='t', created_by=cls.mgr)
        return GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': [
                {'key': 'F·m', 'instance': 1, 'mirrored': False,
                 'rotation_deg': 0, 'polygon_mm': SQUARE}]},
            marker_length_mm=100,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 1})

    def _workspace_html(self, layout):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:workspace',
                                       args=[layout.pk])).content.decode()

    @staticmethod
    def _menu_items(html):
        # lsw-item anchors exist only inside the switcher — document order
        return re.findall(r'class="lsw-item[^"]*"\s+href="[^"]*">([^<]+)</a>',
                          html)


class SwitcherOrderingTests(_M5Base):
    """Rule F: ★ production → drafts newest-first → ＋ Generate New."""

    def test_order_with_production_layout(self):
        ProductionLayout.objects.create(
            product=self.product, approved_layout=self.l1,
            approved_by=self.mgr, approved_at=timezone.now())
        html = self._workspace_html(self.l2)
        items = self._menu_items(html)
        self.assertEqual(items[0], f'★ Production · #{self.l1.pk}')
        self.assertEqual(items[1:-1], [f'Draft · #{self.l3.pk}',
                                       f'Draft · #{self.l2.pk}'])
        self.assertEqual(items[-1], '＋ Generate New Layout')
        # the production layout is NOT duplicated in the drafts section
        self.assertEqual(
            [i for i in items if i == f'★ Production · #{self.l1.pk}'],
            [f'★ Production · #{self.l1.pk}'])
        self.assertNotIn(f'Draft · #{self.l1.pk}', items)

    def test_order_without_production_layout(self):
        html = self._workspace_html(self.l2)
        items = self._menu_items(html)
        self.assertNotIn('★', ''.join(items))
        self.assertEqual(items, [f'Draft · #{self.l3.pk}',
                                 f'Draft · #{self.l2.pk}',
                                 f'Draft · #{self.l1.pk}',
                                 '＋ Generate New Layout'])

    def test_items_are_plain_links(self):
        # Rule I structurally: the menu is a list of <a href> to workspace
        # pages + one to Generate — no forms, no POST, no JS-built actions.
        html = self._workspace_html(self.l2)
        menu = html.split('id="lswmenu"')[1].split('lsw-new')[0]
        self.assertIn(reverse('patterns_ai:workspace', args=[self.l3.pk]),
                      menu)
        self.assertIn(reverse('patterns_ai:generate')
                      + f'?product={self.product.pk}', html)
        self.assertNotIn('<form', menu)

    def test_current_layout_marked(self):
        html = self._workspace_html(self.l2)
        self.assertRegex(html, r'lsw-item cur[^>]*>Draft · #%d' % self.l2.pk)

    def test_discard_prompt_wording_present(self):
        html = self._workspace_html(self.l2)
        self.assertIn('Discard changes and open another layout?', html)


class RuleINoHiddenWorkTests(_M5Base):
    def test_opening_layouts_writes_nothing(self):
        self.client.force_login(self.mgr)
        counts = (MarkerGenerationRun.objects.count(),
                  GeneratedMarkerCandidate.objects.count(),
                  ProductionLayout.objects.count())
        for layout in (self.l1, self.l2, self.l3, self.l1):
            self.client.get(reverse('patterns_ai:workspace',
                                    args=[layout.pk]))
        self.assertEqual(counts,
                         (MarkerGenerationRun.objects.count(),
                          GeneratedMarkerCandidate.objects.count(),
                          ProductionLayout.objects.count()))


class RuleGPrefillTests(_M5Base):
    def test_generate_form_prefills_from_profile(self):
        fps.set_fabric_profile(user=self.mgr, product=self.product,
                               default_width_mm=1500,
                               default_spacing_mm='5.0')
        self.client.force_login(self.mgr)
        html = self.client.get(
            reverse('patterns_ai:generate')
            + f'?product={self.product.pk}').content.decode()
        self.assertIn('name="usable_width_mm"', html)
        self.assertRegex(html, r'usable_width_mm[^>]*value="1500"')
        self.assertRegex(html, r'spacing_mm[^>]*value="5.0"')

    def test_generate_form_without_profile_keeps_defaults(self):
        self.client.force_login(self.mgr)
        html = self.client.get(
            reverse('patterns_ai:generate')
            + f'?product={self.product.pk}').content.decode()
        self.assertRegex(html, r'usable_width_mm[^>]*value=""')
        self.assertRegex(html, r'spacing_mm[^>]*value="3"')

    def test_saved_layout_always_shows_its_own_values(self):
        # Rule G display law: profile 1500 must NOT leak into a saved
        # 900mm layout's editor.
        fps.set_fabric_profile(user=self.mgr, product=self.product,
                               default_width_mm=1500,
                               default_spacing_mm='5.0')
        html = self._workspace_html(self.l3)
        self.assertRegex(html, r'id="fw"[^>]*value="900"')
        self.assertIn('Fabric width: 900 mm', html)
        self.assertNotRegex(html, r'id="fw"[^>]*value="1500"')

    def test_profile_change_leaves_layout_pages_byte_stable(self):
        def stable(html):     # only the per-request CSRF token may differ
            return re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"',
                          'CSRF', html)
        html_before = stable(self._workspace_html(self.l2))
        fps.set_fabric_profile(user=self.mgr, product=self.product,
                               default_width_mm=2222,
                               default_spacing_mm='9.5')
        html_after = stable(self._workspace_html(self.l2))
        self.assertEqual(html_before, html_after)
