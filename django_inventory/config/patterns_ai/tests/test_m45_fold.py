"""M4.5 — FOLD from the cutting room (plan §§0-8 + R2 capabilities +
R3 three-concepts): adr-c.3 fold_edge (twins) · fold_service
detect/unfold/validate · capabilities contract · readiness law upgrade ·
lay fold-edges · per-placement content math · placement modes chrome."""
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (ApprovedLayout, GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry)
from patterns_ai.services import fold_service
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import pattern_design_facade as facade
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services.units import validate_canonical_geometry
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


def half_um(w_mm, h_mm):
    """A half-pattern: rectangle with its LEFT edge = the fold line."""
    p = rect_um(w_mm, h_mm)
    p['features']['fold_edge'] = {
        'p1_um': [0, int(h_mm * 1000)], 'p2_um': [0, 0]}
    return p


class _FoldBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m45@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='M45P', name='M45 Fold')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        # Back = ON FOLD half-pattern · Pocket = normal
        cls.back = cls._piece('m45-back', 'Back', on_fold=True,
                              pieces_count=1)
        cls.pocket = cls._piece('m45-pocket', 'Pocket', pieces_count=2)

    @classmethod
    def _piece(cls, code, name, on_fold=False, is_pair=False,
               pieces_count=1):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=pieces_count)
        p = geo.create_piece(user=cls.mgr, product=cls.product,
                             pattern=pattern, fabric_group='body',
                             is_pair=is_pair, on_fold=on_fold)
        return p

    @classmethod
    def _confirm(cls, piece, payload):
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(          # fixture only
            version=draft, size=cls.size_s, geometry=payload,
            trust_grade='photo_calibrated', created_by=cls.mgr)
        return geo.confirm_version(user=cls.mgr, version=draft)


class ContractC3Tests(_FoldBase):
    def test_twin_accepts_and_refuses_fold_edge_shapes(self):
        p = half_um(200, 400)
        self.assertEqual(validate_canonical_geometry(p), [])
        p['features']['fold_edge'] = {'p1_um': [0, 0],
                                      'p2_um': [200000, 0]}   # horizontal
        self.assertIn('fold_edge must be vertical',
                      validate_canonical_geometry(p))
        p['features']['fold_edge'] = {'p1_um': 'nope'}
        self.assertIn('fold_edge needs integer p1_um/p2_um pairs',
                      validate_canonical_geometry(p))

    def test_constant_and_default_bumped_consciously(self):
        # the pin exists to FORCE this deliberate edit (third time)
        self.assertEqual(geo.GEOMETRY_CONTRACT_VERSION, 'adr-c.3')
        field = PieceSizeGeometry._meta.get_field(
            'geometry_contract_version')
        self.assertEqual(field.default, 'adr-c.3')

    def test_fold_service_validate_rules(self):
        p = rect_um(200, 400)
        fe = {'p1_um': [0, 400000], 'p2_um': [0, 0]}
        self.assertEqual(fold_service.validate_fold_edge(p, fe), [])
        bad = {'p1_um': [0, 400000], 'p2_um': [200000, 400000]}
        self.assertTrue(any('must be vertical' in m for m in
                            fold_service.validate_fold_edge(p, bad)))
        stranger = {'p1_um': [5, 5], 'p2_um': [0, 0]}
        self.assertIn('fold_edge points must be outline vertices',
                      fold_service.validate_fold_edge(p, stranger))

    def test_unfold_derives_the_opened_piece(self):
        p = half_um(200, 400)
        opened = fold_service.unfold_outline(p)
        self.assertEqual(max(q[0] for q in opened), 400000)   # 2 × 200 mm
        self.assertEqual(max(q[1] for q in opened), 400000)
        # derived only — the stored payload still holds the HALF
        self.assertEqual(max(q[0] for q in p['outer']), 200000)

    def test_detect_proposes_the_vertical_edge(self):
        best = fold_service.detect_fold_edge(rect_um(200, 400))
        self.assertIsNotNone(best)
        self.assertEqual(best['p1_um'][0], best['p2_um'][0])


class EditorFoldEdgeTests(_FoldBase):
    def test_mark_validate_and_clear_via_single_writer(self):
        draft = geo.get_or_create_draft(user=self.mgr, piece=self.back)
        PieceSizeGeometry.objects.create(
            version=draft, size=self.size_s, geometry=rect_um(200, 400),
            trust_grade='uncalibrated', created_by=self.mgr)
        row = geo.edit_draft_geometry(
            user=self.mgr, version=draft, size=self.size_s,
            outer_um=rect_um(200, 400)['outer'],
            fold_edge={'p1_um': [0, 400000], 'p2_um': [0, 0]})
        self.assertIsNotNone(fold_service.get_fold_edge(row.geometry))
        self.assertEqual(row.geometry_contract_version, 'adr-c.3')
        with self.assertRaises(ValidationError):    # horizontal refused
            geo.edit_draft_geometry(
                user=self.mgr, version=draft, size=self.size_s,
                outer_um=row.geometry['outer'],
                fold_edge={'p1_um': [0, 0], 'p2_um': [200000, 0]})
        row = geo.edit_draft_geometry(
            user=self.mgr, version=draft, size=self.size_s,
            outer_um=row.geometry['outer'], fold_edge=None)
        self.assertIsNone(fold_service.get_fold_edge(row.geometry))


class CapabilitiesContractTests(_FoldBase):
    """R2-A: ONE named shape from the existing pattern-owned fields."""

    def test_capabilities_dict_and_opened_derivation(self):
        self._confirm(self.back, half_um(200, 400))
        lib = facade.product_design_library(self.product)
        row = next(r for r in lib['sections'][0]['rows']
                   if r['piece_id'] == self.back.pk)
        caps = row['capabilities']
        self.assertTrue(caps['fold'])              # wished AND edge marked
        self.assertEqual(caps['rotation'], 'two_way')
        self.assertFalse(caps['mirror'])
        self.assertEqual(caps['count'], 1)
        self.assertTrue(row['has_fold_edge'])
        self.assertEqual(row['opened_dims']['w_mm'], 400.0)
        self.assertEqual(row['fold_x_mm'], 0.0)

    def test_fold_wished_without_edge_is_not_capable(self):
        self._confirm(self.back, rect_um(200, 400))   # NO fold edge
        lib = facade.product_design_library(self.product)
        row = next(r for r in lib['sections'][0]['rows']
                   if r['piece_id'] == self.back.pk)
        self.assertFalse(row['capabilities']['fold'])
        self.assertTrue(row['capabilities']['fold_wished'])
        self.assertIsNone(row['opened_outline_mm'])


class ReadinessLawTests(_FoldBase):
    """The oldest honest blocker retires — WITH a named fix."""

    def test_on_fold_with_edge_is_ready(self):
        self._confirm(self.back, half_um(200, 400))
        self._confirm(self.pocket, rect_um(140, 160))
        lib = facade.product_design_library(self.product)
        self.assertTrue(lib['sections'][0]['ready'])
        self.assertTrue(lib['summary']['any_size_ready'])
        self.assertEqual(
            [b for b in lib['summary']['blockers'] if 'fold' in b], [])

    def test_on_fold_without_edge_blocks_with_named_fix(self):
        self._confirm(self.back, rect_um(200, 400))   # no edge
        self._confirm(self.pocket, rect_um(140, 160))
        lib = facade.product_design_library(self.product)
        self.assertFalse(lib['sections'][0]['ready'])
        self.assertTrue(any('mark its fold edge' in m for m in
                            lib['sections'][0]['required_missing']))
        self.assertTrue(any('mark the fold edge in the Studio' in b
                            for b in lib['summary']['blockers']))


class ContentMathTests(_FoldBase):
    """Q4: fold placements open to multiplier ÷ 2; legacy byte-identity."""

    def _layout(self, layering_type, placements):
        from patterns_ai.services import marker_generation_service as gen
        run = MarkerGenerationRun.objects.create(
            product=self.product, usable_width_mm=1040,
            params={'schema_version': 1, 'table': True,
                    'layering_type': layering_type,
                    'layer_multiplier': gen.LAY_MULTIPLIER[layering_type],
                    'fold_edges': gen.LAY_FOLD_EDGES[layering_type]},
            pipeline_version='table-v1', created_by=self.mgr)
        cand = GeneratedMarkerCandidate.objects.create(
            run=run, engine='table',
            placements={'schema_version': 1, 'placements': placements},
            marker_length_mm=500,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True,
                          'piece_count': len(placements)})
        return ApprovedLayout.objects.create(
            product=self.product, candidate=cand, name='f',
            layout_uid=f'LAY-M45P-{cand.pk:06d}', version_no=cand.pk,
            fabric_group='body', approved_by=self.mgr,
            approved_at=timezone.now())

    def test_fold_placement_opens_to_one_on_double_folded(self):
        key = f'{self.back.pk}:{self.size_s.pk}'
        lay = self._layout('double_folded', [
            {'key': key, 'instance': 1, 'polygon_mm': SQUARE,
             'rotation_deg': 0, 'mirrored': False, 'on_fold': True},
            {'key': f'{self.pocket.pk}:{self.size_s.pk}', 'instance': 2,
             'polygon_mm': SQUARE, 'rotation_deg': 0, 'mirrored': False},
        ])
        # fold: 2÷2 = 1 · normal: 2 → per-size total 1 + 2 = 3
        self.assertEqual(usage_svc.marker_content(lay),
                         {self.size_s.pk: 3})

    def test_legacy_placements_unchanged(self):
        key = f'{self.pocket.pk}:{self.size_s.pk}'
        lay = self._layout('double', [
            {'key': key, 'instance': 1, 'polygon_mm': SQUARE,
             'rotation_deg': 0, 'mirrored': False}])
        self.assertEqual(usage_svc.marker_content(lay),
                         {self.size_s.pk: 2})     # exact M4 math

    def test_lay_vocabulary_recorded_and_validated(self):
        from patterns_ai.services import marker_generation_service as gen
        self.assertEqual(gen.LAY_FOLD_EDGES['double_folded'], 1)
        self.assertEqual(gen.LAY_FOLD_EDGES['tubular'], 2)
        self.assertEqual(gen.LAY_FOLD_EDGES['double'], 0)   # legacy=open
        self.assertEqual(gen.LAY_MULTIPLIER['double_open'], 2)
        with self.assertRaises(ValidationError):
            gen.save_table_layout(
                user=self.mgr, product=self.product, width_mm=1000,
                height_mm=2000, spacing_mm=0, fabric_group='body',
                placements=[], layering_type='pleated')


class StudioProposalTests(_FoldBase):
    """R2-C: deterministic one-shot capability proposals."""

    def _work_url(self, piece):
        return reverse('patterns_ai:studio-work',
                       args=[piece.pk, self.size_s.pk])

    def test_fold_edge_proposal_and_accept(self):
        draft = geo.get_or_create_draft(user=self.mgr, piece=self.back)
        PieceSizeGeometry.objects.create(
            version=draft, size=self.size_s, geometry=rect_um(200, 400),
            trust_grade='uncalibrated', created_by=self.mgr)
        self.client.force_login(self.mgr)
        html = self.client.get(self._work_url(self.back)).content.decode()
        self.assertIn('Fold edge detected', html)
        self.assertIn('accept_fold_edge', html)
        r = self.client.post(self._work_url(self.back), {
            'action': 'accept_fold_edge',
            'fold_edge': json.dumps({'p1_um': [0, 400000],
                                     'p2_um': [0, 0]})})
        self.assertEqual(r.status_code, 302)
        row = draft.size_geometries.get(size=self.size_s)
        self.assertIsNotNone(fold_service.get_fold_edge(row.geometry))

    def test_symmetry_proposal_marks_fold_capable_once(self):
        draft = geo.get_or_create_draft(user=self.mgr, piece=self.pocket)
        PieceSizeGeometry.objects.create(
            version=draft, size=self.size_s, geometry=rect_um(140, 160),
            trust_grade='uncalibrated', created_by=self.mgr)
        self.client.force_login(self.mgr)
        html = self.client.get(
            self._work_url(self.pocket)).content.decode()
        # honest v1: expert-judgment affordance (a pocket has straight
        # edges too — only the human knows it is a half-pattern)
        self.assertIn('HALF pattern', html)
        self.assertIn('mark_fold_capable', html)
        r = self.client.post(self._work_url(self.pocket), {
            'action': 'mark_fold_capable',
            'fold_edge': json.dumps({'p1_um': [0, 160000],
                                     'p2_um': [0, 0]})})
        self.assertEqual(r.status_code, 302)
        self.pocket.refresh_from_db()
        self.assertTrue(self.pocket.on_fold)     # permanent knowledge
        # asked once: the proposal box is gone now
        html = self.client.get(
            self._work_url(self.pocket)).content.decode()
        self.assertNotIn('mark_fold_capable', html)


class DctChromeTests(_FoldBase):
    """Placement-mode buttons + lay radios + payload caps reach the page."""

    def test_payload_ships_caps_and_opened(self):
        self._confirm(self.back, half_um(200, 400))
        self._confirm(self.pocket, rect_um(140, 160))
        self.client.force_login(self.mgr)
        html = self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()
        start = html.index('id="ws-payload"')
        payload = json.loads(
            html[html.index('>', start) + 1:html.index('</script>', start)])
        back = payload[f'{self.back.pk}:{self.size_s.pk}']
        self.assertTrue(back['caps']['fold'])
        self.assertEqual(back['opened']['w'], 400.0)
        self.assertEqual(back['fold_x_mm'], 0.0)
        self.assertNotIn('grain', back)          # R2-A: caps replaced flags
        pocket = payload[f'{self.pocket.pk}:{self.size_s.pk}']
        self.assertFalse(pocket['caps']['fold'])
        self.assertNotIn('opened', pocket)
        # lay vocabulary + fold visuals in the chrome
        self.assertIn('value="double_folded"', html)
        self.assertIn('value="double_open"', html)
        self.assertIn('col-fold', html)
        self.assertIn('fabric-fold', html)


class BlueprintAdvisoryTests(_FoldBase):
    def test_fold_pair_contradiction_flagged(self):
        self._piece('m45-weird', 'Weird', on_fold=True, is_pair=True)
        sa = User.objects.create_user(
            'm45sa@test.local', password='x',
            role=Role.objects.get_or_create(code='super_admin',
                                            defaults={'name': 'SA'})[0])
        self.client.force_login(sa)
        html = self.client.get(reverse('patterns_ai:blueprint')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('fold+pair?', html)