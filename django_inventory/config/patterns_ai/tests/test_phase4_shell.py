"""Phase 4 — the Digital Cutting Table SHELL: the permanent workspace
(owner amendments 1–7). Read-only; palette = confirmed designs of READY
sizes only, FABRIC GROUP → size; frozen toolbar; honest gate."""
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


class _P4Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p4@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('p4w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='P4S', name='P4 Shell')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.size_l = ProductSize.objects.create(product=cls.product,
                                                code='l', label='L',
                                                display_order=2)
        # BODY piece: confirmed for S (S = Ready) — L stays not ready
        cls.front = cls._piece('p4-front', 'Front Panel', 'body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.front)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size_s, geometry=rect_um(480, 660),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)
        # RIB piece: OPTIONAL, confirmed for S — second fabric group
        cls.rib = cls._piece('p4-rib', 'Neck Rib', 'rib')
        geo.set_piece_optional(user=cls.mgr, piece=cls.rib,
                               is_optional=True)
        d2 = geo.get_or_create_draft(user=cls.mgr, piece=cls.rib)
        PieceSizeGeometry.objects.create(
            version=d2, size=cls.size_s, geometry=rect_um(300, 40),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d2)
        # a DRAFT-only piece: must never reach the palette
        cls.pocket = cls._piece('p4-pocket', 'Pocket', 'body')
        geo.set_piece_optional(user=cls.mgr, piece=cls.pocket,
                               is_optional=True)
        d3 = geo.get_or_create_draft(user=cls.mgr, piece=cls.pocket)
        PieceSizeGeometry.objects.create(
            version=d3, size=cls.size_s, geometry=rect_um(120, 130),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        # not confirmed — stays draft

    @classmethod
    def _piece(cls, code, name, group):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group=group)

    def _get(self, pk=None):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[pk or self.product.pk]))


class ShellStructureTests(_P4Base):
    def test_all_permanent_regions_render(self):
        html = self._get().content.decode()
        self.assertIn('Pattern Library', html)              # amendment 1
        self.assertIn('Digital Fabric Workspace', html)     # amendment 2
        # Phase 5 conscious rework: the empty-state message became the
        # interactive hint (canvas is now live)
        self.assertIn('Import patterns from the library', html)
        self.assertIn('Layout Information', html)           # amendment 3
        for slot in ('Cut Plan', 'Ratio', 'Imported Pieces',
                     'Placed Pieces', 'Utilization', 'Approval Status',
                     'History'):
            self.assertIn(slot, html)
        self.assertIn('Approved Layout Library', html)      # amendment 7
        # Phase 7 conscious rework: the section is LIVE — empty state
        # invites the save→approve pipeline
        self.assertIn('No approved layouts yet', html)
        for slot in ('Remaining', 'Canvas Length'):         # amendment 4
            self.assertIn(slot, html)

    def test_toolbar_frozen_order_disabled_with_phases(self):
        html = self._get().content.decode()
        # 6A conscious rework: buttons COME ALIVE as their phase arrives
        # (Grid is live now) — the ORDER stays frozen regardless of tag.
        # M4 conscious updates (owner-approved plan): AI wording = R5
        # "Suggest Better Layout"; the legacy Generate link RETIRED from
        # navigation (§18-d).
        toolbar = html[html.index('cutting table tools'):
                       html.index('</div>', html.index('cutting table tools'))]
        order = ['Import', 'Select', 'Rotate', 'Mirror', 'Zoom', 'Grid',
                 'Suggest Better Layout', 'Approve Layout', 'Export']
        positions = [toolbar.find(f'>{label}<') for label in order]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))      # frozen order
        self.assertIn('Import — Phase 5', html)
        self.assertIn('id="tb-ai"', html)
        # Phase 7 conscious rework: Approve + Export arrived —
        # Approve = link armed after Save; Export = approved-only gate
        self.assertIn('id="tb-approve"', html)
        self.assertIn('id="tb-export"', html)
        self.assertIn('id="tb-grid"', html)                 # Grid live (6A)
        # §18-d: the legacy generate link is GONE from the toolbar
        self.assertNotIn('Generate (current tool)', html)

    def test_palette_grouped_fabric_group_first_confirmed_only(self):
        # M4 conscious update (§18-c): the left panel is the IMPORT
        # QUEUE (Blueprint × Marker Plan, client-derived). The server
        # still ships ONLY confirmed designs of ready sizes in the
        # payload — the frozen consumption law, asserted on the data.
        import json as _json
        html = self._get().content.decode()
        self.assertIn('Import Queue', html)
        start = html.index('id="ws-payload"')
        payload = _json.loads(
            html[html.index('>', start) + 1:html.index('</script>', start)])
        names = {m['name'] for m in payload.values()}
        groups = {m['group'] for m in payload.values()}
        self.assertIn('Front Panel', names)
        self.assertIn('Neck Rib', names)
        self.assertNotIn('Pocket', names)      # draft never reaches DCT
        self.assertEqual(groups, {'body', 'rib'})
        # non-ready size = honest muted line
        self.assertIn('L — not ready', html)

    def test_gate_not_ready_redirects_with_message(self):
        bare = Product.objects.create(code='P4B', name='Bare')
        ProductSize.objects.create(product=bare, code='m', label='M',
                                   display_order=1)
        r = self._get(bare.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'],
                         reverse('patterns_ai:dashboard')
                         + f'?product={bare.pk}')
        follow = self.client.get(r['Location']).content.decode()
        self.assertIn('Digital Cutting Table is locked', follow)

    def test_worker_403_unknown_404_and_get_writes_nothing(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:cutting-table',
                    args=[self.product.pk])).status_code, 403)
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:cutting-table',
                    args=[999999])).status_code, 404)
        before = (PatternPiece.objects.count(),
                  PieceSizeGeometry.objects.count())
        self._get()
        self.assertEqual(before, (PatternPiece.objects.count(),
                                  PieceSizeGeometry.objects.count()))

    def test_shell_accepts_no_post(self):
        self.client.force_login(self.mgr)
        r = self.client.post(reverse('patterns_ai:cutting-table',
                                     args=[self.product.pk]), {})
        self.assertEqual(r.status_code, 405)                # read-only shell
