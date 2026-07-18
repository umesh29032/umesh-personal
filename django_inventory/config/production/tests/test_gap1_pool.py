"""GAP-1 (production-hardening 2026-07-11, ratified formula): the ops pool is
the Σ-over-streams read (frozen lifecycle §2 — was `.first()` = ONE arbitrary
lane), and multi-component products are capped at GARMENT-EQUIVALENT sets per
SIZE (BUNDLE review Q4: sewing hears 45 sets, never 143 pieces; cloth colour =
component attribute). Single-component products stay byte-identical (min over
one pattern IS its piece count). Provider absent/failing ⇒ legacy math
(fail-open)."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from production.models import (Adda, AddaProductSizeColorPieceBreakdown,
                               AddaStageRecord, CuttingPieceBreakup,
                               CuttingRecord, CuttingStream, Product,
                               ProductPattern, ProductPatternAssignment,
                               ProductSize, Stage, WorkflowStage)
from production.services import pool_service
from raw_materials.models import ClothColor

User = get_user_model()


class _PoolWorld(TestCase):
    """A product with three mandatory components (Body ×1, Panel ×1, Cuff ×2)
    + one OPTIONAL component (Loop), cut across TWO body lanes + one panel
    lane + one cuff lane, two sizes, three colours."""

    def setUp(self):
        role = Role.objects.get(code='super_admin')
        self.mgr = User.objects.create_user('gap1@test.local', password='x',
                                            is_superuser=True)
        self.mgr.role = role
        self.mgr.save()
        self.product = Product.objects.create(code='GP1', name='Gap1')
        self.s_m = ProductSize.objects.create(product=self.product, code='m',
                                              label='M', display_order=1)
        self.s_l = ProductSize.objects.create(product=self.product, code='l',
                                              label='L', display_order=2)
        self.navy = ClothColor.objects.create(name='GP1 Navy')
        self.grey = ClothColor.objects.create(name='GP1 Grey')
        self.black = ClothColor.objects.create(name='GP1 Black')
        cutting = Stage.objects.get(code='cutting')
        ops = (Stage.objects.filter(code='side_seam_close').first()
               or Stage.objects.exclude(
                   code__in=('layering', 'cutting_pattern',
                             'cutting')).first())
        self.ws_cut = WorkflowStage.objects.create(
            product=self.product, stage=cutting, order=1,
            cost_rate=Decimal('1'), allocation_dimensions='color_size')
        self.ws_ops = WorkflowStage.objects.create(
            product=self.product, stage=ops, order=2,
            cost_rate=Decimal('1'), allocation_dimensions='color_size')
        self.adda = Adda.objects.create(code='GP1-001', product=self.product,
                                        current_stage=self.ws_ops)
        # Blueprint mandatory-ness crosses the ADR-H wall via registry #6 —
        # production tests MOCK the provider (the REAL derivation is proven
        # patterns_ai-side in test_mandatory_provider.py; that direction may
        # import production, never the reverse — purity guard enforces it).
        self.pats = {}
        mandatory_ids = set()
        for name, per, optional in [('Body', 1, False), ('Panel', 1, False),
                                    ('Cuff', 2, False), ('Loop', 1, True)]:
            pat = ProductPattern.objects.create(code=f'GP1-{name.upper()}',
                                                name=f'GP1 {name}')
            ProductPatternAssignment.objects.create(
                product=self.product, pattern=pat, pieces_count=per)
            if not optional:
                mandatory_ids.add(pat.pk)
            self.pats[name] = pat
        self._provider = mock.patch.object(
            pool_service, 'MANDATORY_PATTERNS_PROVIDER',
            lambda product, _ids=frozenset(mandatory_ids): set(_ids))
        self._provider.start()
        def _safe_stop():
            try:
                self._provider.stop()
            except RuntimeError:
                pass   # already swapped out by a test
        self.addCleanup(_safe_stop)
        self.ops_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_ops,
            started_at=timezone.now())

    def _lane_cut(self, group, seq, rows):
        """rows = [(pattern, color, size, n)] — one cutting lane with breakups
        AND the matching verified APSCPB rows (pool_good's source)."""
        lane = CuttingStream.objects.create(
            adda=self.adda, fabric_group=group, sequence=seq,
            is_blocking=True, reason='' if seq == 1 else 'Split lay')
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_cut, stream=lane,
            started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=sr,
                                          pieces_cut=sum(r[3] for r in rows))
        dims = {}
        for pat, color, size, n in rows:
            CuttingPieceBreakup.objects.create(
                cutting_record=cr, pattern=pat, color=color, size=size,
                count=n)
            dims[(color, size)] = dims.get((color, size), 0) + n
        for (color, size), n in dims.items():
            AddaProductSizeColorPieceBreakdown.objects.create(
                cutting_record=cr, adda=self.adda, product=self.product,
                size=size, color=color, verified_piece_count=n,
                created_by=self.mgr)
        return lane

    def _cut_default_world(self):
        # body cycle 1: Body M25 L25 navy · cycle 2: Body M20 L20 navy
        self._lane_cut('body', 1, [(self.pats['Body'], self.navy, self.s_m, 25),
                                   (self.pats['Body'], self.navy, self.s_l, 25)])
        self._lane_cut('body', 2, [(self.pats['Body'], self.navy, self.s_m, 20),
                                   (self.pats['Body'], self.navy, self.s_l, 20)])
        # panel: M40 L38 grey
        self._lane_cut('panel', 1, [(self.pats['Panel'], self.grey, self.s_m, 40),
                                    (self.pats['Panel'], self.grey, self.s_l, 38)])
        # cuff (×2/garment): M86 L80 black
        self._lane_cut('trim', 1, [(self.pats['Cuff'], self.black, self.s_m, 86),
                                   (self.pats['Cuff'], self.black, self.s_l, 80)])
        # garment truth: M = min(45, 40, 86//2=43) = 40 · L = min(45, 38, 40) = 38


class MultiLaneSumTests(_PoolWorld):
    def test_single_component_sums_across_lanes(self):
        """One mandatory pattern (Body only, others uncut+unassigned): available
        = Σ over BOTH body lanes per dim — the LOWER-002 recut case (was: one
        arbitrary lane; recut pieces invisible / negative)."""
        for name in ('Panel', 'Cuff', 'Loop'):
            ProductPatternAssignment.objects.filter(
                pattern=self.pats[name]).delete()
        # single mandatory component ⇒ provider path degrades to legacy
        self._provider.stop()
        replacement = mock.patch.object(
            pool_service, 'MANDATORY_PATTERNS_PROVIDER',
            lambda product: {self.pats['Body'].pk})
        replacement.start()
        self.addCleanup(replacement.stop)
        self._lane_cut('body', 1, [(self.pats['Body'], self.navy, self.s_m, 32)])
        self._lane_cut('body', 2, [(self.pats['Body'], self.navy, self.s_m, 2)])
        self.assertEqual(
            pool_service.available(self.ops_sr, color_id=self.navy.pk,
                                   size_id=self.s_m.pk),
            Decimal('34'))   # 32 + 2, never 32 or 2

    def test_sources_are_all_lanes_at_nearest_order(self):
        self._cut_default_world()
        sources = pool_service._upstream_pool_sources(self.ops_sr)
        self.assertEqual(len(sources), 4)   # every cutting lane


class GarmentEquivalentTests(_PoolWorld):
    def test_available_capped_at_sets_per_size(self):
        self._cut_default_world()
        # navy M pieces = 45 but sets(M) = 40 → capped
        self.assertEqual(
            pool_service.available(self.ops_sr, color_id=self.navy.pk,
                                   size_id=self.s_m.pk), Decimal('40'))
        # grey L pieces = 38 = the bottleneck itself
        self.assertEqual(
            pool_service.available(self.ops_sr, color_id=self.grey.pk,
                                   size_id=self.s_l.pk), Decimal('38'))
        # cuff ÷2 respected: black M pieces 86, sets 40 → 40
        self.assertEqual(
            pool_service.available(self.ops_sr, color_id=self.black.pk,
                                   size_id=self.s_m.pk), Decimal('40'))

    def test_optional_component_never_zeroes_the_pool(self):
        """Loop (optional) has ZERO cut pieces — mandatory-only min ignores it."""
        self._cut_default_world()
        self.assertGreater(
            pool_service.available(self.ops_sr, color_id=self.navy.pk,
                                   size_id=self.s_m.pk), Decimal('0'))

    def test_allocation_draws_down_sets_at_size_grain(self):
        self._cut_default_world()
        worker = User.objects.create_user('gp1w@test.local', password='x')
        pool_service.allocate(self.ops_sr, worker, qty=Decimal('35'),
                              actor=self.mgr, color_id=self.navy.pk,
                              size_id=self.s_m.pk)
        # 40 sets − 35 drawn = 5 left for M, ANY colour
        self.assertEqual(
            pool_service.available(self.ops_sr, color_id=self.grey.pk,
                                   size_id=self.s_m.pk), Decimal('5'))
        with self.assertRaisesMessage(ValidationError, 'only 5'):
            pool_service.allocate(self.ops_sr, worker, qty=Decimal('6'),
                                  actor=self.mgr, color_id=self.grey.pk,
                                  size_id=self.s_m.pk)

    def test_provider_absent_falls_back_to_legacy_per_dim(self):
        self._cut_default_world()
        with mock.patch.object(pool_service, 'MANDATORY_PATTERNS_PROVIDER',
                               None):
            self.assertEqual(
                pool_service.available(self.ops_sr, color_id=self.navy.pk,
                                       size_id=self.s_m.pk),
                Decimal('45'))   # Σ lanes per dim, uncapped (legacy shape)
