"""Block-2A model tests — schema behaves as specified (constraints, enums,
uniques, append-only states). No services exist yet; rows are built directly
IN TESTS ONLY (production code must use the single-writers from Block 2B).
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from production.models import Adda, Product, ProductPattern, WorkflowStage, Stage
from patterns_ai.models import (
    CalibrationMat, Marker, MarkerOutcome, MarkerUsage,
    PatternPiece, PatternPieceVersion, SuggestionEvent,
)

User = get_user_model()


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pai2a@test.local', password='x')
        cls.product = Product.objects.create(code='PAI-P1', name='PAI Product')
        stage, _ = Stage.objects.get_or_create(code='pai_s1', defaults={'name': 'PAI S1'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=stage, order=1)
        cls.adda = Adda.objects.create(code='PAI-001', product=cls.product,
                                       current_stage=ws)
        cls.pattern = ProductPattern.objects.create(name='PAI Front')

    def marker(self, **kw):
        defaults = dict(reference=f'MRK-{Marker.objects.count() + 1:06d}',
                        product=self.product, origin=Marker.Origin.MANUAL_PHOTO,
                        usable_width_mm=940, usable_width_band=94,
                        created_by=self.user)
        defaults.update(kw)
        return Marker.objects.create(**defaults)


class MatTests(_Base):
    def test_retired_requires_reason(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CalibrationMat.objects.create(mat_code='MAT-X', status='retired')

    def test_lifecycle_states(self):
        m = CalibrationMat.objects.create(mat_code='MAT-01')
        self.assertEqual(m.status, 'uncommissioned')
        m.status, m.status_reason = 'retired', 'stretched'
        m.save()   # reason present → allowed


class PieceTests(_Base):
    def test_unique_per_product(self):
        PatternPiece.objects.create(product=self.product, pattern=self.pattern)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PatternPiece.objects.create(product=self.product, pattern=self.pattern)

    def test_version_chain_constraints(self):
        piece = PatternPiece.objects.create(product=self.product, pattern=self.pattern)
        v1 = PatternPieceVersion.objects.create(piece=piece, version_no=1,
                                                created_by=self.user)
        self.assertEqual(v1.status, 'draft')
        # duplicate version_no refused
        with self.assertRaises(IntegrityError), transaction.atomic():
            PatternPieceVersion.objects.create(piece=piece, version_no=1)
        # rejected requires reason
        with self.assertRaises(IntegrityError), transaction.atomic():
            PatternPieceVersion.objects.create(piece=piece, version_no=2,
                                               status='rejected')
        # confirmed requires audit pair
        with self.assertRaises(IntegrityError), transaction.atomic():
            PatternPieceVersion.objects.create(piece=piece, version_no=3,
                                               status='confirmed')
        ok = PatternPieceVersion.objects.create(
            piece=piece, version_no=4, status='confirmed',
            confirmed_by=self.user, confirmed_at=timezone.now())
        self.assertEqual(ok.status, 'confirmed')


class MarkerTests(_Base):
    def test_manual_marker_minimal(self):
        m = self.marker(label="Master's tube layout",
                        construction=Marker.Construction.TUBULAR,
                        ratio={'schema_version': 1, 'counts': {'1': 2, '2': 2}})
        self.assertEqual(m.status, 'candidate')
        self.assertEqual(str(m), f'{m.reference} [manual_photo/candidate]')

    def test_adda_iff_temporary_both_directions(self):
        # temporary WITHOUT adda → refused
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.marker(origin=Marker.Origin.ADDA_TEMPORARY)
        # non-temporary WITH adda → refused
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.marker(origin=Marker.Origin.MANUAL_PHOTO, adda=self.adda)
        # temporary WITH adda → allowed
        t = self.marker(origin=Marker.Origin.ADDA_TEMPORARY, adda=self.adda)
        self.assertEqual(t.adda_id, self.adda.pk)

    def test_negative_status_requires_reason_and_lineage(self):
        base = self.marker()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.marker(status=Marker.Status.REJECTED)
        nxt = self.marker(supersedes=base, benchmarked_against=base,
                          status=Marker.Status.RETIRED, status_reason='replaced')
        self.assertEqual(nxt.supersedes_id, base.pk)
        # PROTECT lineage: base cannot vanish under nxt
        with self.assertRaises(IntegrityError), transaction.atomic():
            base.delete()


class UsageOutcomeTests(_Base):
    def test_usage_and_facts_only_outcome(self):
        m = self.marker()
        u = MarkerUsage.objects.create(marker=m, adda=self.adda, plies=30,
                                       repeats=3, confirmed_by=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MarkerUsage.objects.create(marker=m, adda=self.adda, plies=0,
                                       confirmed_by=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            u.voided_at = timezone.now(); u.save()   # void w/o reason refused
        u.refresh_from_db()
        o = MarkerOutcome.objects.create(
            usage=u, fabric_in_mm=45000, garments_cut=60, garments_packed=54,
            quality_flags={'schema_version': 1, 'flags': ['dev_fixture']},
            recorded_by=self.user)
        # facts only — no derived-metric fields exist on the row (F6)
        for forbidden in ('utilization', 'meters_per_garment', 'rupees'):
            self.assertFalse(hasattr(o, forbidden))
        # one outcome per usage
        with self.assertRaises(IntegrityError), transaction.atomic():
            MarkerOutcome.objects.create(usage=u, recorded_by=self.user)


class SuggestionTests(_Base):
    def test_rejection_requires_reason(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            SuggestionEvent.objects.create(
                product=self.product, source='garment_template:tshirt@r1',
                payload={'schema_version': 1}, outcome='rejected')
        ok = SuggestionEvent.objects.create(
            product=self.product, source='garment_template:tshirt@r1',
            payload={'schema_version': 1}, outcome='rejected',
            outcome_reason='wrong garment type', decided_by=self.user,
            decided_at=timezone.now())
        self.assertEqual(ok.outcome, 'rejected')
