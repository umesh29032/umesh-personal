"""GAP-5 (production-hardening 2026-07-11): bundle services in their FROZEN
post-join, Adda-level role (PROPOSAL §3 / final review §4) — creation refused
until every blocking lane's cutting is complete; bundles anchor on (adda,
size) with cutting_record NULL; consumption spans every lane's breakups;
cross-lane takes of one component INCREMENT the single (bundle, pattern,
color) line; readiness derive + one-tap slip; bundle rows never become a
second production truth (they only record the act)."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from production.models import (Adda, AddaStageRecord, CuttingBundle,
                               CuttingBundleItem, CuttingPieceBreakup,
                               CuttingRecord, CuttingStream, Product,
                               ProductPattern, ProductPatternAssignment,
                               ProductSize, Stage, WorkflowStage)
from production.services import pool_service
from production.stages.cutting.service import (add_pieces_to_bundle,
                                               bundle_ready_sets,
                                               create_bundle,
                                               create_bundle_with_pieces)
from raw_materials.models import ClothColor

User = get_user_model()


class _BundleWorld(TestCase):
    """Two-fabric product: Body (navy, ×1) + Panel (grey, ×1); two body lanes
    + one panel lane. Blocking lanes gate the join."""

    def setUp(self):
        role = Role.objects.get(code='super_admin')
        self.mgr = User.objects.create_user('gap5@test.local', password='x',
                                            is_superuser=True)
        self.mgr.role = role
        self.mgr.save()
        self.product = Product.objects.create(code='GP5', name='Gap5')
        self.size = ProductSize.objects.create(product=self.product, code='m',
                                               label='M', display_order=1)
        self.navy = ClothColor.objects.create(name='GP5 Navy')
        self.grey = ClothColor.objects.create(name='GP5 Grey')
        cutting = Stage.objects.get(code='cutting')
        self.ws_cut = WorkflowStage.objects.create(
            product=self.product, stage=cutting, order=1,
            cost_rate=Decimal('1'))
        self.adda = Adda.objects.create(code='GP5-001', product=self.product,
                                        current_stage=self.ws_cut)
        self.pat_body = ProductPattern.objects.create(code='GP5-BODY',
                                                      name='GP5 Body')
        self.pat_panel = ProductPattern.objects.create(code='GP5-PANEL',
                                                       name='GP5 Panel')
        for pat in (self.pat_body, self.pat_panel):
            ProductPatternAssignment.objects.create(
                product=self.product, pattern=pat, pieces_count=1)
        self._provider = mock.patch.object(
            pool_service, 'MANDATORY_PATTERNS_PROVIDER',
            lambda product: {self.pat_body.pk, self.pat_panel.pk})
        self._provider.start()
        self.addCleanup(self._provider.stop)

    def _lane(self, group, seq, pattern, color, count, complete=True):
        lane = CuttingStream.objects.create(
            adda=self.adda, fabric_group=group, sequence=seq,
            is_blocking=True, reason='' if seq == 1 else 'Split lay')
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_cut, stream=lane,
            started_at=timezone.now(),
            completed_at=timezone.now() if complete else None)
        cr = CuttingRecord.objects.create(stage_record=sr, pieces_cut=count)
        breakup = CuttingPieceBreakup.objects.create(
            cutting_record=cr, pattern=pattern, color=color, size=self.size,
            count=count)
        return lane, sr, breakup

    def _joined_world(self):
        _, _, self.b1 = self._lane('body', 1, self.pat_body, self.navy, 30)
        _, _, self.b2 = self._lane('body', 2, self.pat_body, self.navy, 12)
        _, _, self.p1 = self._lane('panel', 1, self.pat_panel, self.grey, 38)


class JoinGateTests(_BundleWorld):
    def test_bundling_refused_before_join(self):
        """A blocking lane's cutting still open ⇒ every bundle door refuses."""
        self._lane('body', 1, self.pat_body, self.navy, 30)
        self._lane('panel', 1, self.pat_panel, self.grey, 38, complete=False)
        with self.assertRaisesMessage(ValidationError, 'Bundling unlocks'):
            create_bundle(adda=self.adda, size_id=self.size.pk, user=self.mgr)

    def test_bundling_opens_at_join_and_anchors_on_adda(self):
        self._joined_world()
        bundle = create_bundle(adda=self.adda, size_id=self.size.pk,
                               user=self.mgr)
        self.assertEqual(bundle.adda_id, self.adda.pk)
        self.assertIsNone(bundle.cutting_record_id)   # Adda-level container
        # idempotent per (adda, size)
        again = create_bundle(adda=self.adda, size_id=self.size.pk,
                              user=self.mgr)
        self.assertEqual(again.pk, bundle.pk)


class CrossLaneConsumptionTests(_BundleWorld):
    def test_takes_span_lanes_and_increment_one_line(self):
        """Body from BOTH lanes lands on ONE (bundle, pattern, color) line —
        the DB-unique truth; multi-source blanks source_breakup; consumed
        tracks per physical row."""
        self._joined_world()
        bundle = create_bundle_with_pieces(
            adda=self.adda, size_id=self.size.pk, user=self.mgr,
            selections=[
                {'breakup_id': self.b1.pk, 'take_count': 30},
                {'breakup_id': self.b2.pk, 'take_count': 8},
                {'breakup_id': self.p1.pk, 'take_count': 38},
            ])
        self.assertEqual(bundle.total_pieces, 76)
        body_line = CuttingBundleItem.objects.get(bundle=bundle,
                                                  pattern=self.pat_body)
        self.assertEqual(body_line.count, 38)          # 30 + 8, one line
        self.assertIsNone(body_line.source_breakup_id)  # multi-source
        self.b1.refresh_from_db(); self.b2.refresh_from_db()
        self.assertEqual((self.b1.consumed_count, self.b2.consumed_count),
                         (30, 8))

    def test_over_take_refused_per_physical_row(self):
        self._joined_world()
        bundle = create_bundle(adda=self.adda, size_id=self.size.pk,
                               user=self.mgr)
        with self.assertRaisesMessage(ValidationError, 'only 12'):
            add_pieces_to_bundle(adda=self.adda, bundle_id=bundle.pk,
                                 user=self.mgr,
                                 selections=[{'breakup_id': self.b2.pk,
                                              'take_count': 13}])


class ReadinessAndSlipTests(_BundleWorld):
    def test_readiness_derives_sets_bottleneck_and_leftovers(self):
        self._joined_world()
        r = pool_service.garment_readiness(self.adda)
        row = r['sizes'][0]
        self.assertEqual(row['sets'], 38)              # min(42 body, 38 panel)
        self.assertEqual(row['bottleneck'], 'GP5 Panel')
        self.assertEqual(r['total_sets'], 38)

    def test_one_tap_slip_bundles_exactly_the_complete_sets(self):
        self._joined_world()
        bundle, sets = bundle_ready_sets(adda=self.adda, size_id=self.size.pk,
                                         user=self.mgr)
        self.assertEqual(sets, 38)
        self.assertEqual(bundle.total_pieces, 76)      # 38 × 2 components
        # leftovers = 4 body pieces (42 − 38), derived from count − consumed
        left = sum(b.count - b.consumed_count for b in
                   CuttingPieceBreakup.objects.filter(
                       cutting_record__stage_record__adda=self.adda))
        self.assertEqual(left, 4)
        # nothing new to bundle ⇒ honest refusal (derive says 0)
        with self.assertRaisesMessage(ValidationError, 'No complete'):
            bundle_ready_sets(adda=self.adda, size_id=self.size.pk,
                              user=self.mgr)

    def test_bundle_rows_never_gate_the_derive(self):
        """Bundle ≠ truth: deleting nothing / bundling nothing — the derive
        answers from CUT truth alone (sets exist before any bundle row)."""
        self._joined_world()
        self.assertEqual(pool_service.garment_readiness(
            self.adda)['total_sets'], 38)
        self.assertFalse(CuttingBundle.objects.filter(
            adda=self.adda).exists())
