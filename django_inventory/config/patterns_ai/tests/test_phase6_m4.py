"""Phase-6 M4 tests — smart redirect (owner-locked priority), entry
button, Rules C/D/E (§2b)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry,
                                ProductionLayout)
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M4Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m4@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m4w@test.local', password='x', role=wk)

    def _login(self, user):
        self.client.force_login(user)

    @staticmethod
    def _product(code):
        return Product.objects.create(code=code, name=f'{code} name')

    @classmethod
    def _piece(cls, product, code, name):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=product,
                                pattern=pattern, fabric_group='body')

    @classmethod
    def _confirmed_geometry(cls, product, piece):
        size = (ProductSize.objects.filter(product=product).first()
                or ProductSize.objects.create(product=product, code='m',
                                              label='M', display_order=1))
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(       # test fixture only
            version=draft, size=size, geometry=rect_um(200, 300),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)
        return size

    @classmethod
    def _saved_layout(cls, product, ratio=None):
        run = MarkerGenerationRun.objects.create(   # test fixture only
            product=product, usable_width_mm=900,
            params={'schema_version': 1, 'ratio': ratio or {}},
            pipeline_version='t', created_by=cls.mgr)
        return GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': [
                {'key': 'Front·m', 'instance': 1, 'mirrored': False,
                 'rotation_deg': 0, 'polygon_mm': SQUARE}]},
            marker_length_mm=100,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 1})


class SmartRedirectPriorityTests(_M4Base):
    """M4 §18-d CONSCIOUS REWRITE (owner-confirmed retirements): the
    ★ ProductionLayout designation + generator-era workspace/generate
    chain left NAVIGATION. New decision table: ready size → the Digital
    Cutting Table · pieces → the Studio · nothing → Blueprint."""

    def _tool(self, product):
        return self.client.get(reverse('patterns_ai:tool',
                                       args=[product.pk]))

    def test_1_ready_size_goes_to_cutting_table(self):
        p = self._product('M4A')
        piece = self._piece(p, 'm4a-front', 'Front')
        self._confirmed_geometry(p, piece)      # the only piece → ready
        # a ★ designation exists but NO LONGER steers navigation (§18-d)
        lay = self._saved_layout(p)
        ProductionLayout.objects.create(
            product=p, approved_layout=lay, approved_by=self.mgr,
            approved_at=timezone.now())
        self._login(self.mgr)
        r = self._tool(p)
        self.assertRedirects(r, reverse('patterns_ai:cutting-table',
                                        args=[p.pk]))

    def test_2_saved_layouts_alone_do_not_steer(self):
        # drafts exist but nothing is ready → the Studio (not the old
        # workspace — §18-d)
        p = self._product('M4B')
        self._piece(p, 'm4b-front', 'Front')
        self._saved_layout(p)
        self._login(self.mgr)
        r = self._tool(p)
        self.assertRedirects(r, reverse('patterns_ai:studio')
                             + f'?product={p.pk}')

    def test_3_confirmed_geometry_means_ready_goes_to_table(self):
        p = self._product('M4C')
        piece = self._piece(p, 'm4c-front', 'Front')
        self._confirmed_geometry(p, piece)
        self._login(self.mgr)
        r = self._tool(p)
        self.assertRedirects(r, reverse('patterns_ai:cutting-table',
                                        args=[p.pk]))

    def test_4_pieces_only_goes_to_studio(self):
        p = self._product('M4D')
        self._piece(p, 'm4d-front', 'Front')   # piece, draft-less
        self._login(self.mgr)
        r = self._tool(p)
        self.assertRedirects(r, reverse('patterns_ai:studio')
                             + f'?product={p.pk}')

    def test_5_nothing_goes_to_register(self):
        p = self._product('M4E')
        self._login(self.mgr)
        r = self._tool(p)
        # fetch_redirect_response=False — the Blueprint is perm-gated
        # (change_productpattern) and this mgr-role user only proves the
        # REDIRECT target, not Blueprint access.
        self.assertRedirects(r, reverse('patterns_ai:blueprint')
                             + f'?product={p.pk}',
                             fetch_redirect_response=False)

    def test_draft_geometry_is_not_confirmed(self):
        # draft-only geometry must NOT count as ready
        p = self._product('M4F')
        piece = self._piece(p, 'm4f-front', 'Front')
        size = ProductSize.objects.create(product=p, code='m', label='M',
                                          display_order=1)
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        PieceSizeGeometry.objects.create(
            version=draft, size=size, geometry=rect_um(200, 300),
            trust_grade='photo_calibrated', created_by=self.mgr)
        self._login(self.mgr)
        r = self._tool(p)                       # unconfirmed ⇒ the Studio
        self.assertRedirects(r, reverse('patterns_ai:studio')
                             + f'?product={p.pk}')


class RedirectGuardsAndAuditTests(_M4Base):
    def test_worker_403(self):
        p = self._product('M4G')
        self._login(self.worker)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:tool', args=[p.pk])).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        p = self._product('M4H')
        r = self.client.get(reverse('patterns_ai:tool', args=[p.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertNotIn('patterns', r['Location'].split('?')[0])

    def test_tampered_and_inactive_404(self):
        self._login(self.mgr)
        self.assertEqual(self.client.get('/patterns/tool/999999/')
                         .status_code, 404)
        inactive = Product.objects.create(code='M4I', name='gone',
                                          is_active=False)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:tool', args=[inactive.pk]))
            .status_code, 404)

    def test_rule_e_decision_logged(self):
        p = self._product('M4J')
        self._login(self.mgr)
        with self.assertLogs('patterns_ai.views', level='INFO') as logs:
            self.client.get(reverse('patterns_ai:tool', args=[p.pk]))
        line = '\n'.join(logs.output)
        self.assertIn('patterns.tool.redirect', line)
        self.assertIn(f'product={p.pk}', line)
        # M4 conscious update: an empty product routes to the Blueprint
        self.assertIn('reason="blueprint"', line)
        self.assertIn(f'user={self.mgr.pk}', line)


class EntryButtonTests(_M4Base):
    """The production page carries ONE URL — template-level only."""

    def test_button_rendered_for_management(self):
        p = self._product('M4K')
        # the page itself is perm-gated (change_productpattern);
        # super_admin = the seeded management owner role (implicit bypass)
        sa = User.objects.create_user(
            'm4sa@test.local', password='x',
            role=Role.objects.get(code='super_admin'))
        self._login(sa)
        # Phase 1 conscious rework: product-patterns is now the platform
        # entry — it REDIRECTS to the Pattern Dashboard (owner correction:
        # Patterns opens the dashboard, not any page directly). The Manager
        # link now lives on the Blueprint page (STEP 2 hand-off).
        r = self.client.get(reverse('production:product-patterns',
                                    args=[p.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'],
            reverse('patterns_ai:dashboard') + f'?product={p.pk}')
        # Phase 2: the Blueprint module moved into patterns_ai (D-1);
        # the production URL is a redirect. Follow to the real module.
        r = self.client.get(reverse('production:product-pattern-blueprint',
                                    args=[p.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Pattern Blueprint')
        self.assertContains(r, 'Pattern Manager')       # STEP 2 hand-off
        self.assertContains(r,
            reverse('patterns_ai:piece-list') + f'?product={p.pk}')

    def test_worker_never_sees_the_page(self):
        p = self._product('M4L')
        self._login(self.worker)
        # Phase 1: entry redirects (login-only); the Blueprint page keeps
        # the strict perm gate; the dashboard itself 403s workers.
        r = self.client.get(reverse('production:product-pattern-blueprint',
                                    args=[p.pk]))
        self.assertIn(r.status_code, (302, 403))   # perm gate blocks page
        r = self.client.get(reverse('patterns_ai:dashboard')
                            + f'?product={p.pk}')
        self.assertEqual(r.status_code, 403)

    def test_boundary_production_template_has_no_python_import(self):
        # ADR-H: composition is URL-only; production python never imports
        # patterns_ai (the purity wall re-asserts the import direction).
        # Phase 2 conscious rework: the production editor template retired
        # (Blueprint lives in patterns_ai). The wall to re-assert is the
        # PYTHON one: production's redirect views reach patterns_ai by URL
        # NAME only — no import anywhere in production/views.
        import pathlib
        import production
        views_dir = pathlib.Path(production.__file__).parent / 'views'
        for py in views_dir.glob('*.py'):
            self.assertNotIn('import patterns_ai', py.read_text(),
                             f'{py.name} crosses the ADR-H wall')


class RuleDContextStripTests(_M4Base):
    def test_workspace_shows_product_layout_ratio_width(self):
        p = self._product('M4M')
        size = ProductSize.objects.create(product=p, code='m', label='M',
                                          display_order=1)
        layout = self._saved_layout(p, ratio={str(size.pk): 3})
        self._login(self.mgr)
        r = self.client.get(reverse('patterns_ai:workspace',
                                    args=[layout.pk]))
        self.assertContains(r, 'M4M name (M4M)')          # product chip
        self.assertContains(r, f'Layout #{layout.pk}')
        self.assertContains(r, 'Ratio: M×3')
        self.assertContains(r, 'Fabric width: 900 mm')
        self.assertNotContains(r, '★ Production')          # no designation

    def test_workspace_marks_production_layout(self):
        p = self._product('M4N')
        layout = self._saved_layout(p)
        ProductionLayout.objects.create(
            product=p, approved_layout=layout, approved_by=self.mgr,
            approved_at=timezone.now())
        self._login(self.mgr)
        r = self.client.get(reverse('patterns_ai:workspace',
                                    args=[layout.pk]))
        self.assertContains(r, '★ Production')

    def test_rule_c_no_product_selector_in_editor(self):
        p = self._product('M4O')
        layout = self._saved_layout(p)
        self._login(self.mgr)
        html = self.client.get(reverse('patterns_ai:workspace',
                                       args=[layout.pk])).content.decode()
        self.assertNotIn('name="product"', html)   # no product switch UI
