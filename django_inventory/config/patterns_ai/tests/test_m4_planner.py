"""M4 — the Manufacturing Planner (plan §§1-24 + owner refinements
R1-R10): Marker Recipe (ManufacturingStrategy) · Marker Plan persisted
with the layout · G3 layer-multiplier math · G4 roll fields · plan
dialog/queue chrome · §18-d retirements · the GENERICITY GUARD (the
engine never knows a garment name — automated wall)."""
import json
import pathlib
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (ApprovedLayout, GeneratedMarkerCandidate,
                                ManufacturingStrategy, MarkerGenerationRun)
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services import strategy_service
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M4Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m4p@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='M4P', name='M4 Planner')
        # NUMERIC size chart — the genericity proof for index colors
        cls.s28 = ProductSize.objects.create(product=cls.product,
                                             code='28', label='28',
                                             display_order=1)
        cls.s30 = ProductSize.objects.create(product=cls.product,
                                             code='30', label='30',
                                             display_order=2)
        cls.body = cls._piece('m4p-body', 'Body', is_pair=True,
                              pieces_count=2)
        cls.pocket = cls._piece('m4p-pocket', 'Pocket', pieces_count=2)
        for piece in (cls.body, cls.pocket):
            d = geo.get_or_create_draft(user=cls.mgr, piece=piece)
            from patterns_ai.models import PieceSizeGeometry
            for size in (cls.s28, cls.s30):
                PieceSizeGeometry.objects.create(       # fixture only
                    version=d, size=size, geometry=rect_um(300, 200),
                    trust_grade='photo_calibrated', created_by=cls.mgr)
            geo.confirm_version(user=cls.mgr, version=d)

    @classmethod
    def _piece(cls, code, name, is_pair=False, pieces_count=1):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=pieces_count)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group='body',
                                is_pair=is_pair)

    @classmethod
    def _layout(cls, layering_type='single', ratio=None, notes='',
                recipe=''):
        from patterns_ai.services import marker_generation_service as gen
        run = MarkerGenerationRun.objects.create(   # fixture-shaped run
            product=cls.product, usable_width_mm=1040,
            params={'schema_version': 1, 'manual': True, 'table': True,
                    'fabric_group': 'body', 'ratio': ratio or {},
                    'layering_type': layering_type,
                    'layer_multiplier': gen.LAY_MULTIPLIER[layering_type],
                    'recipe': recipe, 'notes': notes, 'pieces': []},
            pipeline_version='table-v1', created_by=cls.mgr)
        cand = GeneratedMarkerCandidate.objects.create(
            run=run, engine='table',
            placements={'schema_version': 1, 'placements': [
                {'key': f'{cls.body.pk}:{cls.s28.pk}', 'instance': 1,
                 'mirrored': False, 'rotation_deg': 0,
                 'polygon_mm': SQUARE},
                {'key': f'{cls.body.pk}:{cls.s28.pk}', 'instance': 2,
                 'mirrored': True, 'rotation_deg': 0,
                 'polygon_mm': SQUARE},
                {'key': f'{cls.pocket.pk}:{cls.s30.pk}', 'instance': 3,
                 'mirrored': False, 'rotation_deg': 0,
                 'polygon_mm': SQUARE}]},
            marker_length_mm=500,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 3})
        from django.utils import timezone
        return ApprovedLayout.objects.create(
            product=cls.product, candidate=cand, name='M4 fixture',
            layout_uid=f'LAY-M4P-{cand.pk:06d}', version_no=cand.pk,
            fabric_group='body', approved_by=cls.mgr,
            approved_at=timezone.now())


class RecipeTests(_M4Base):
    """§4 — the Marker Recipe: manufacturing knowledge as data."""

    def _save(self, name='Body marker · 42″', **kw):
        return strategy_service.save_recipe(
            user=self.mgr, product=self.product, name=name,
            fabric_group='body', layering_type='double',
            piece_ids=[self.body.pk],
            size_ratio={self.s28.pk: 2}, **kw)

    def test_save_and_update_by_name(self):
        r = self._save(notes='42 inch only')
        self.assertEqual(r.layering_type, 'double')
        self.assertEqual(r.piece_ids, [self.body.pk])
        self.assertEqual(r.size_ratio, {str(self.s28.pk): 2})
        r2 = self._save(notes='updated')           # same name = update
        self.assertEqual(r.pk, r2.pk)
        self.assertEqual(r2.notes, 'updated')

    def test_refusals_are_honest(self):
        with self.assertRaises(ValidationError):
            self._save(name='')
        with self.assertRaises(ValidationError):
            strategy_service.save_recipe(
                user=self.mgr, product=self.product, name='x',
                fabric_group='nope')
        with self.assertRaises(ValidationError):
            strategy_service.save_recipe(
                user=self.mgr, product=self.product, name='x',
                fabric_group='body', piece_ids=[999999])

    def test_never_deleted_only_deactivated(self):
        r = self._save()
        with self.assertRaises(ValueError):
            r.delete()
        strategy_service.deactivate_recipe(user=self.mgr, recipe=r)
        r.refresh_from_db()
        self.assertFalse(r.is_active)
        self.assertFalse(strategy_service.active_recipes(
            self.product).filter(pk=r.pk).exists())

    def test_recipe_endpoint_round_trip(self):
        self.client.force_login(self.mgr)
        r = self.client.post(
            reverse('patterns_ai:table-recipe', args=[self.product.pk]),
            json.dumps({'name': 'Panel marker', 'fabric_group': 'body',
                        'layering_type': 'tubular',
                        'piece_ids': [self.pocket.pk],
                        'size_ratio': {str(self.s30.pk): 3}}),
            content_type='application/json')
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['recipes'][0]['name'], 'Panel marker')
        self.assertEqual(data['recipes'][0]['layering_type'], 'tubular')


class MultiplierMathTests(_M4Base):
    """G3 — layer_multiplier: recorded at save, consumed derive-at-read;
    legacy layouts (no key) stay byte-identical (multiplier 1)."""

    def test_single_lay_content_unchanged(self):
        lay = self._layout('single')
        self.assertEqual(usage_svc.layer_multiplier(lay), 1)
        self.assertEqual(usage_svc.marker_content(lay),
                         {self.s28.pk: 2, self.s30.pk: 1})

    def test_double_lay_doubles_content_and_expected(self):
        lay = self._layout('double', ratio={str(self.s28.pk): 1})
        self.assertEqual(usage_svc.layer_multiplier(lay), 2)
        self.assertEqual(usage_svc.marker_content(lay),
                         {self.s28.pk: 4, self.s30.pk: 2})

    def test_legacy_layout_without_key_multiplier_one(self):
        lay = self._layout('single')
        params = lay.candidate.run.params
        del params['layer_multiplier']
        MarkerGenerationRun.objects.filter(
            pk=lay.candidate.run_id).update(params=params)
        lay.candidate.run.refresh_from_db()
        self.assertEqual(usage_svc.layer_multiplier(lay), 1)

    def test_save_pipeline_validates_and_records_the_plan(self):
        from patterns_ai.services import marker_generation_service as gen
        with self.assertRaises(ValidationError):
            gen.save_table_layout(
                user=self.mgr, product=self.product, width_mm=1000,
                height_mm=2000, spacing_mm=0, fabric_group='body',
                placements=[], layering_type='folded-weird')
        with self.assertRaises(ValidationError):
            gen.save_table_layout(
                user=self.mgr, product=self.product, width_mm=1000,
                height_mm=2000, spacing_mm=0, fabric_group='body',
                placements=[], ratio={'x': 'y'})


class RollFieldsTests(TestCase):
    """G4 — ClothRoll planning facts (additive; raw_materials)."""

    def test_fields_exist_with_safe_defaults(self):
        from raw_materials.models import ClothRoll
        for f in ('usable_width_mm', 'stretch_class', 'is_one_way_nap',
                  'selvedge_note'):
            ClothRoll._meta.get_field(f)
        self.assertFalse(
            ClothRoll._meta.get_field('is_one_way_nap').default)


class PlannerChromeTests(_M4Base):
    """§2 — the plan dialog, queue container, config hand-off, live
    estimate slots and R5 wording all reach the page (data only)."""

    def _html(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()

    def test_plan_dialog_and_queue_render(self):
        html = self._html()
        for needle in ('id="plan-dialog"', 'Marker Plan', 'Marker Recipe',
                       'id="plan-roll"', 'id="plan-width"',
                       'name="plan-lay"', 'id="plan-pieces"',
                       'id="plan-notes"', 'id="queue-body"',
                       'Import Queue', 'id="ai-verdict"'):
            self.assertIn(needle, html)
        # R2 live-estimate slots
        for cls_ in ('c-expected', 'c-waste', 'c-ratio', 'c-fabricw'):
            self.assertIn(cls_, html)
        # R5 wording — never "Optimize" on the button
        self.assertIn('Suggest Better Layout', html)

    def test_config_carries_numeric_chart_sizes_in_order(self):
        # F4 genericity proof: a 28/30 chart ships in CHART ORDER — the
        # client palette cycles by INDEX, names never matter
        html = self._html()
        start = html.index('id="ws-config"')
        cfg = json.loads(
            html[html.index('>', start) + 1:html.index('</script>', start)])
        self.assertEqual([s['label'] for s in cfg['sizes']], ['28', '30'])
        self.assertIn('urls', cfg)
        self.assertIn('recipe', cfg['urls'])

    def test_payload_carries_queue_inputs(self):
        html = self._html()
        start = html.index('id="ws-payload"')
        payload = json.loads(
            html[html.index('>', start) + 1:html.index('</script>', start)])
        row = payload[f'{self.body.pk}:{self.s28.pk}']
        # M4.5 R2-A conscious update: queue inputs live on the
        # capabilities contract now
        self.assertEqual(row['caps']['count'], 2)   # Blueprint count truth
        self.assertFalse(row['caps']['optional'])
        self.assertEqual(row['piece_id'], self.body.pk)
        self.assertEqual(row['size_id'], self.s28.pk)


class RetirementTests(_M4Base):
    """§18-d — the pre-platform trio is out of NAVIGATION (pages live)."""

    def test_home_points_at_the_platform(self):
        self.client.force_login(self.mgr)
        html = self.client.get(reverse('patterns_ai:home')
                               ).content.decode()
        self.assertIn(reverse('patterns_ai:dashboard'), html)
        for gone in ('manual-marker-new', 'generate', 'piece-list'):
            self.assertNotIn(reverse(f'patterns_ai:{gone}')
                             if gone != 'generate'
                             else '/patterns/generate/', html)

    def test_legacy_pages_stay_live(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:generate')).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:marker-list')).status_code, 200)


GARMENT_RE = re.compile(
    r'nickk?ar|t-?shirt|hoodie|polo|cargo|track ?pant', re.I)
# the two known COSMETIC docstring/help-text hits (M4 review §5 F2/F3)
GENERICITY_ALLOWLIST = {
    'patterns_ai/models/suggestions.py',        # help-text example
}


class GenericityGuardTests(TestCase):
    """§23 — the PERMANENT wall: no garment name may enter non-test
    engine/service/view code. Test data is the only legal home."""

    def test_no_garment_names_in_engine_code(self):
        config_dir = pathlib.Path(__file__).resolve().parents[2]
        roots = [config_dir / 'patterns_ai',
                 config_dir.parent / 'compute' / 'patterns_ai']
        offenders = []
        for root in roots:
            for py in root.rglob('*.py'):
                rel = str(py.relative_to(config_dir.parent))
                rel_cfg = str(py.relative_to(config_dir)) \
                    if config_dir in py.parents else rel
                if ('tests' in py.parts or 'migrations' in py.parts
                        or 'venv' in py.parts        # vendored 3rd-party
                        or rel_cfg in GENERICITY_ALLOWLIST):
                    continue
                text = py.read_text(errors='ignore')
                # strip comments — the wall guards CODE, not prose
                code = '\n'.join(line.split('#')[0]
                                 for line in text.splitlines())
                if GARMENT_RE.search(code):
                    offenders.append(rel)
        self.assertEqual(offenders, [],
                         'garment names leaked into engine code: '
                         f'{offenders}')