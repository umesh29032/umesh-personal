"""CUTTING STREAMS (frozen redesign 2026-07-11) — the lane laws:
derivation from the Blueprint provider · independent lane walks · the
JOIN gate (= every BLOCKING lane's cutting complete) · non-blocking
lanes never gate · resolve_stream semantics. Single-lane byte-identity
is proven by the whole legacy suite staying green (542 tests)."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, Skill
from production.models import (Adda, AddaStageRecord, Product, Stage, StageCategory, WorkflowStage)
from production.services import adda_service
from production.services.adda_service import (advance_lane, create_adda,
                                              resolve_stream)

User = get_user_model()


def _mgr():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user('streams@test.local', password='x',
                                 is_superuser=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class _StreamsWorld(TestCase):
    """A trio-flow product; the fabric-groups provider is mocked per test
    (the REAL provider is patterns_ai's — its own truth is proven by the
    live DEV-NICKAR derivation)."""

    def setUp(self):
        self.mgr = _mgr()
        self.product = Product.objects.create(code='STRM', name='Streams')
        StageCategory.objects.get(code='pre_production')
        order = 0
        self.trio = {}
        for code in ('layering', 'cutting_pattern', 'cutting'):
            order += 1
            stage = Stage.objects.filter(code=code).first()
            self.trio[code] = WorkflowStage.objects.create(
                product=self.product, stage=stage, order=order,
                cost_rate=Decimal('1'))

    def _adda_with_groups(self, groups):
        with mock.patch.object(adda_service, 'FABRIC_GROUPS_PROVIDER',
                               lambda product: groups):
            return create_adda(self.mgr, product=self.product)

    def _complete(self, adda, lane, code):
        ws = self.trio[code]
        sr, _ = AddaStageRecord.objects.get_or_create(
            adda=adda, workflow_stage=ws, stream=lane,
            defaults={'started_at': timezone.now()})
        sr.completed_at = timezone.now()
        sr.save(update_fields=['completed_at'])
        advance_lane(adda, stream=lane, leaving_sr=sr, user=self.mgr,
                     enforce_worker_credit=False)
        adda.refresh_from_db()
        return adda


class DerivationTests(_StreamsWorld):
    def test_two_groups_derive_two_lanes(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True},
            {'fabric_group': 'other', 'blocking': True}])
        lanes = list(adda.cutting_streams.order_by('fabric_group'))
        self.assertEqual([(s.fabric_group, s.sequence, s.is_blocking)
                          for s in lanes],
                         [('body', 1, True), ('other', 1, True)])
        # one layering SR PER LANE, auto-started at creation
        self.assertEqual(
            AddaStageRecord.objects.filter(
                adda=adda, workflow_stage=self.trio['layering'],
                stream__isnull=False).count(), 2)

    def test_single_group_is_todays_behavior(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True}])
        self.assertEqual(adda.cutting_streams.count(), 1)
        # resolve_stream(None) finds it — zero caller churn
        self.assertEqual(resolve_stream(adda).fabric_group, 'body')

    def test_provider_failure_fails_closed_to_one_lane(self):
        def boom(product):
            raise RuntimeError('provider down')
        with mock.patch.object(adda_service, 'FABRIC_GROUPS_PROVIDER', boom):
            adda = create_adda(self.mgr, product=self.product)
        self.assertEqual(adda.cutting_streams.count(), 1)

    def test_resolve_refuses_ambiguity_on_multi_lane(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True},
            {'fabric_group': 'other', 'blocking': True}])
        with self.assertRaisesMessage(ValidationError, 'multiple'):
            resolve_stream(adda)
        lane = adda.cutting_streams.get(fabric_group='other')
        self.assertEqual(resolve_stream(adda, lane.pk).pk, lane.pk)


class JoinGateTests(_StreamsWorld):
    def test_join_waits_for_every_blocking_lane(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True},
            {'fabric_group': 'other', 'blocking': True}])
        body = adda.cutting_streams.get(fabric_group='body')
        other = adda.cutting_streams.get(fabric_group='other')

        # lane A walks its whole trio — the Adda must NOT leave
        # pre-production while lane B is uncut
        for code in ('layering', 'cutting_pattern', 'cutting'):
            adda = self._complete(adda, body, code)
        self.assertEqual(adda.status, Adda.Status.IN_PROGRESS)
        self.assertIsNotNone(adda.current_stage)
        self.assertIn(adda.current_stage.stage.code,
                      ('layering', 'cutting_pattern', 'cutting'))

        # lane B finishes → THE JOIN (flow ends at cutting ⇒ COMPLETED)
        for code in ('layering', 'cutting_pattern', 'cutting'):
            adda = self._complete(adda, other, code)
        self.assertEqual(adda.status, Adda.Status.COMPLETED)
        self.assertIsNone(adda.current_stage)

    def test_non_blocking_lane_never_gates(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True},
            {'fabric_group': 'trim', 'blocking': False}])
        body = adda.cutting_streams.get(fabric_group='body')
        for code in ('layering', 'cutting_pattern', 'cutting'):
            adda = self._complete(adda, body, code)
        # trim (optional pieces only) untouched — join fired anyway
        self.assertEqual(adda.status, Adda.Status.COMPLETED)

    def test_join_is_cutting_only_not_all_trio(self):
        # a lane may skip ahead (legacy blind flows): completing CUTTING
        # for every blocking lane joins even if pattern rows are absent
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True}])
        lane = adda.cutting_streams.get()
        adda = self._complete(adda, lane, 'cutting')
        self.assertEqual(adda.status, Adda.Status.COMPLETED)


class LaneLookupTests(_StreamsWorld):
    def test_legacy_null_stream_row_is_adopted(self):
        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True}])
        lane = adda.cutting_streams.get()
        ws = self.trio['cutting']
        legacy = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws)          # pre-redesign shape
        from production.services.adda_service import lane_stage_record
        found = lane_stage_record(adda, ws, lane)
        self.assertEqual(found.pk, legacy.pk)
        found.refresh_from_db()
        self.assertEqual(found.stream_id, lane.pk)  # adopted

    def test_zero_lane_adda_gets_default_provisioned(self):
        adda = Adda.objects.create(code='STRM-RAW', product=self.product,
                                   current_stage=self.trio['layering'])
        lane = resolve_stream(adda)
        self.assertEqual((lane.fabric_group, lane.sequence), ('body', 1))


class CrossFabricCompletionTests(_StreamsWorld):
    """GAP-2 (final implementation audit 2026-07-11, found live on NKS/SHA):
    the cutting-completion validations must read the LANE's layering colors
    and the LANE's pattern-stage sizes — a cream trim lane was refused
    ("Color … not in layered rolls") against the body lane's navy rolls."""

    def _lay_lane(self, adda, lane, color, helper):
        """Minimal real layering for one lane: start + roll + complete."""
        from production.stages.layering.service import (
            attach_roll_to_layering, complete_layering, save_layering_draft,
            start_layering)
        from raw_materials.models import (ClothRoll, ClothType,
                                          StorageLocation)
        ctype = ClothType.objects.first() or ClothType.objects.create(
            name='XF Knit')
        loc = StorageLocation.objects.first() or StorageLocation.objects.create(
            name='XF Rack')
        roll = ClothRoll.objects.create(
            roll_id=f'XF-{lane.fabric_group}-{lane.sequence}',
            cloth_color=color, cloth_type=ctype, storage_location=loc,
            weight_kg=Decimal('10'), width_inch=60, cost_per_kg=100,
            purchased_date=timezone.now().date())
        sr = start_layering(adda=adda, worker_ids=[helper.pk], user=self.mgr,
                            stream=lane)
        entry = attach_roll_to_layering(
            stage_record=sr, roll=roll, width_verified_inch=60,
            weight_verified_kg=Decimal('10'), user=helper, stream=lane)
        save_layering_draft(
            adda=adda, layer_length_meters=Decimal('4'), duration_minutes=None,
            notes=None, per_entry_data={entry.pk: {
                'layers': 5, 'leftover_length': Decimal('0.2'),
                'leftover_weight': Decimal('0.2')}},
            user=helper, stream=lane)
        complete_layering(
            adda=adda, duration_minutes=30, layer_length_meters=Decimal('4'),
            per_entry_layers={entry.pk: 5}, notes='', user=helper, stream=lane)

    def test_cross_fabric_lane_completes_with_its_own_colors(self):
        """Two lanes, two DIFFERENT cloth colors — BOTH complete via the full
        service path (before GAP-2 the second lane was impossible)."""
        from production.models import (ProductPattern,
                                       ProductPatternAssignment, ProductSize)
        from production.stages.cutting.service import (
            complete_cutting_from_bundles, start_cutting, upsert_breakup_row)
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions)
        from raw_materials.models import ClothColor

        helper = self.mgr  # super_admin passes skill gates; roster = himself
        # product bits: one size, one pattern per lane's fabric group
        size = ProductSize.objects.create(product=self.product, code='m',
                                          label='M', display_order=1)
        navy = ClothColor.objects.create(name='XF Navy')
        grey = ClothColor.objects.create(name='XF Grey')
        pat_body = ProductPattern.objects.create(code='XF-BODY', name='XF Body')
        pat_panel = ProductPattern.objects.create(code='XF-PANEL',
                                                  name='XF Panel')
        for pat in (pat_body, pat_panel):
            ProductPatternAssignment.objects.create(
                product=self.product, pattern=pat, pieces_count=1)
        # drop the pattern stage from the flow: lane readiness then only needs
        # layering (keeps the fixture small; the pattern-record read is
        # exercised by the size-allocation assertion below staying silent)
        self.trio['cutting_pattern'].delete()

        adda = self._adda_with_groups([
            {'fabric_group': 'body', 'blocking': True},
            {'fabric_group': 'panel', 'blocking': True}])
        body = adda.cutting_streams.get(fabric_group='body')
        panel = adda.cutting_streams.get(fabric_group='panel')

        self._lay_lane(adda, body, navy, helper)
        self._lay_lane(adda, panel, grey, helper)

        def cut(lane, color, pat, n):
            start_cutting(adda=adda, worker_ids=[helper.pk], user=self.mgr,
                          stream=lane)
            upsert_breakup_row(adda=adda, size_id=size.pk, color_id=color.pk,
                               pattern_id=pat.pk, count=n, user=helper,
                               stream=lane)
            task = adda.stage_records.get(
                stream=lane, workflow_stage=self.trio['cutting']
            ).worker_tasks.get(worker=helper)
            report_contributions(task, [{
                'reported_quantity': n, 'color_id': color.pk,
                'size_id': size.pk}], actor=helper)
            complete_worker_task(task, actor=helper)
            complete_cutting_from_bundles(adda=adda, user=helper, stream=lane)

        cut(body, navy, pat_body, 10)
        # THE GAP-2 case: grey pieces on the panel lane — its own lay is grey;
        # before the fix this raised "Color id=… not in layered rolls"
        cut(panel, grey, pat_panel, 8)

        adda.refresh_from_db()
        done = adda.stage_records.filter(
            workflow_stage=self.trio['cutting'],
            completed_at__isnull=False).count()
        self.assertEqual(done, 2)   # both fabric lanes completed lawfully
