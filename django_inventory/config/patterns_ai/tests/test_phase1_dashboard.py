"""Phase 1 — the PATTERN DASHBOARD (owner-frozen platform entry) +
the geometry-contract truth stamp.

Covers: workflow-step dashboard (1 Blueprint → 2 Manager → 3 DCT),
entry redirect, gate law on the DCT step, chooser, worker 403,
GET-writes-nothing, and geometry_contract_version on every service
write path (create + reuse + edit + confirm + copy-forward + DXF)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PatternPiece, PieceSizeGeometry
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class _P1Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p1@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('p1w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='P1D', name='P1 Dash')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        pattern = ProductPattern.objects.create(code='p1-front',
                                                name='Front Panel')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        cls.front = geo.create_piece(user=cls.mgr, product=cls.product,
                                     pattern=pattern, fabric_group='body')

    def _get(self, qs=''):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:dashboard') + qs)


class DashboardPageTests(_P1Base):
    def test_workflow_steps_rendered(self):
        # M2 conscious update (UI freeze §1/§2.1): the dashboard is the
        # 5-STATION RAIL — station 2 = the Studio (Browse = the shelf);
        # "Pattern Manager" is no longer a rail station.
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('Pattern Dashboard', html)
        self.assertIn('Pattern Blueprint', html)                # station 1
        self.assertIn('Pattern Intelligence Studio', html)      # station 2
        self.assertIn('Digital Cutting Table', html)            # station 3
        self.assertIn('Layout Library', html)                   # station 4
        self.assertIn('Manufacturing', html)                    # station 5
        # the workflow reads as a sequence, not flat cards
        self.assertIn('flow-arrow', html)
        # Phase 2: station 1 targets the patterns_ai Blueprint module (D-1)
        self.assertIn(reverse('patterns_ai:blueprint')
                      + f'?product={self.product.pk}', html)
        self.assertIn(reverse('patterns_ai:studio')
                      + f'?product={self.product.pk}', html)

    def test_dct_step_gated_until_a_size_is_ready(self):
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('aria-disabled="true"', html)             # nothing ready
        self.assertIn('no size is ready yet', html)
        self.assertNotIn(reverse('patterns_ai:cutting-table',
                                 args=[self.product.pk]), html)
        # make S Ready: confirm the only required piece for S
        d = geo.get_or_create_draft(user=self.mgr, piece=self.front)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=self.size_s, geometry=rect_um(480, 660),
            trust_grade='photo_calibrated', created_by=self.mgr)
        geo.confirm_version(user=self.mgr, version=d)
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn(reverse('patterns_ai:cutting-table',
                              args=[self.product.pk]), html)
        self.assertNotIn('no size is ready yet', html)
        self.assertIn('1/1 size Ready', html)                   # ready line

    def test_chooser_worker_and_unknown_product(self):
        bare = self._get().content.decode()
        self.assertIn('Pick a product', bare)
        self.assertIn(self.product.code, bare)
        self.client.force_login(self.worker)
        r = self.client.get(reverse('patterns_ai:dashboard')
                            + f'?product={self.product.pk}')
        self.assertEqual(r.status_code, 403)
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('patterns_ai:dashboard')
                            + '?product=999999')
        self.assertEqual(r.status_code, 404)

    def test_get_writes_nothing(self):
        before = (PatternPiece.objects.count(),
                  PieceSizeGeometry.objects.count())
        self._get(f'?product={self.product.pk}')
        self._get()
        self.assertEqual(before, (PatternPiece.objects.count(),
                                  PieceSizeGeometry.objects.count()))


class EntryRedirectTests(_P1Base):
    def test_patterns_action_redirects_to_dashboard(self):
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('production:product-patterns',
                                    args=[self.product.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'],
                         reverse('patterns_ai:dashboard')
                         + f'?product={self.product.pk}')

    def test_entry_requires_login(self):
        r = self.client.get(reverse('production:product-patterns',
                                    args=[self.product.pk]))
        self.assertEqual(r.status_code, 302)
        # anonymous → LOGIN_URL ('/app/') with ?next= back here
        self.assertIn('?next=', r['Location'])
        self.assertNotIn('/patterns/dashboard', r['Location'])

    def test_manager_carries_dashboard_backlink_and_dct_rename(self):
        self.client.force_login(self.mgr)
        html = self.client.get(reverse('patterns_ai:piece-list')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn(reverse('patterns_ai:dashboard')
                      + f'?product={self.product.pk}', html)
        self.assertIn('Open Digital Cutting Table', html)
        self.assertNotIn('>🪡 Open Cutting Table<', html)


class GeometryContractStampTests(_P1Base):
    """The truth stamp: every single-writer write path stamps the
    semantic contract; legacy rows read the default."""

    def test_stamp_on_dxf_and_edit_and_confirm(self):
        d = geo.get_or_create_draft(user=self.mgr, piece=self.front)
        row = PieceSizeGeometry.objects.create(     # legacy-shaped fixture
            version=d, size=self.size_s, geometry=rect_um(480, 660),
            trust_grade='photo_calibrated', created_by=self.mgr)
        # M4.5 conscious update: the default follows the bumped constant
        self.assertEqual(row.geometry_contract_version, 'adr-c.3')  # default
        # manual edit path re-stamps the CURRENT contract
        pts = [[0, 0], [480000, 0], [480000, 660000], [0, 660000]]
        row = geo.edit_draft_geometry(user=self.mgr, version=d,
                                      size=self.size_s, outer_um=pts)
        self.assertEqual(row.geometry_contract_version,
                         geo.GEOMETRY_CONTRACT_VERSION)
        # confirm path normalizes + re-stamps
        geo.confirm_version(user=self.mgr, version=d)
        row.refresh_from_db()
        self.assertEqual(row.geometry_contract_version,
                         geo.GEOMETRY_CONTRACT_VERSION)
        # copy-forward CARRIES the original stamp (payload unchanged)
        nxt = geo.start_next_version(user=self.mgr, piece=self.front)
        copied = nxt.size_geometries.get(size=self.size_s)
        self.assertEqual(copied.geometry_contract_version,
                         row.geometry_contract_version)

    def test_constant_is_the_single_source(self):
        # M4.5 CONSCIOUS bump to adr-c.3 (fold_edge; owner-approved
        # fold plan §Q2) — this pin exists to force exactly this
        # deliberate edit on every contract change (third time).
        self.assertEqual(geo.GEOMETRY_CONTRACT_VERSION, 'adr-c.3')
        field = PieceSizeGeometry._meta.get_field(
            'geometry_contract_version')
        self.assertEqual(field.default, geo.GEOMETRY_CONTRACT_VERSION)
