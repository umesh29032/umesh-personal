"""RMX-C (Phase 17) — the read-path proofs per the frozen RMX-B spec:
bulk-vs-reference-loop parity (the ORIGINAL M13 algorithm lives HERE as the
independent reference — the queue-batching precedent) · delegation parity ·
assembly component fidelity (Decision-2/-3) · consumption-in-period semantics ·
the one-rupee-once reconciliation identities (leftover chain · straddle month ·
intake conservation) · honest-NULL · read-only purity."""

from datetime import datetime
from decimal import Decimal

from django.db import models as djm
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import StageWorkAssignment
from production.models import (
    Adda, AddaStageRecord, LayeringRollEntry, Product,
    RemainingClothOfClothRoll, Stage, WorkflowStage,
)
from production.services.cost_service import (
    full_cost_for_adda, full_costs_for_addas, material_cost_for_adda,
    material_costs_for_addas, material_consumption_in_period,
)
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services.roll_service import material_purchases_in_period

D = Decimal


def reference_material_loop(adda):
    """THE ORIGINAL M13 per-Adda algorithm, verbatim — the independent parity
    reference for the bulk arm (never shipped again; test-only)."""
    zero = D('0.00')
    consumed = zero
    unpriced = 0
    for e in (LayeringRollEntry.objects
              .filter(stage_record__adda=adda).select_related('roll')):
        if e.roll.cost_per_kg is None:
            unpriced += 1
            continue
        consumed += ((e.weight_verified_kg or e.roll.weight_kg)
                     * e.roll.cost_per_kg)
    remnant = zero
    for r in (RemainingClothOfClothRoll.objects
              .filter(layering_entry__stage_record__adda=adda)
              .select_related('layering_entry__roll')):
        if r.remaining_weight_kg is not None and \
                r.layering_entry.roll.cost_per_kg is not None:
            remnant += r.remaining_weight_kg * r.layering_entry.roll.cost_per_kg
    leftover_in = zero
    for lo in (RemainingClothOfClothRoll.objects
               .filter(consumed_in_adda=adda, is_consumed=True)
               .select_related('roll')):
        if lo.remaining_weight_kg is not None and lo.roll.cost_per_kg is not None:
            leftover_in += lo.remaining_weight_kg * lo.roll.cost_per_kg
        elif lo.roll.cost_per_kg is None:
            unpriced += 1
    consumed += leftover_in
    return {'consumed': consumed, 'remnant': remnant,
            'net': consumed - remnant, 'unpriced_rolls': unpriced,
            'leftover_in': leftover_in,
            'has_material': consumed > 0 or unpriced > 0}


class _World(TestCase):
    """Two-Adda leftover-chain world: A1 consumes roll R1 (priced, 25kg @ ₹100)
    with a verified weight, returns a 2.5kg remnant; A2 reuses that leftover +
    consumes an UNPRICED roll R2. Plus SWA labor + payable/non-payable priced
    stages on A1 (assembly components)."""

    @classmethod
    def setUpTestData(cls):
        cls.sa = User.objects.create_user('rmx-sa@test', 'x', is_superuser=True)
        cls.sa.role = Role.objects.get(code='super_admin')
        cls.sa.save()
        cls.worker = User.objects.create_user('rmx-w@test', 'x')
        product = Product.objects.create(code='RMX', name='RMX P')
        pay, _ = Stage.objects.get_or_create(code='rmx_pay',
                                             defaults={'name': 'RMX Pay'})
        free, _ = Stage.objects.get_or_create(code='rmx_free',
                                              defaults={'name': 'RMX Free'})
        cls.ws_pay = WorkflowStage.objects.create(
            product=product, stage=pay, order=1, cost_rate=D('3'),
            credits_workers=True)
        cls.ws_free = WorkflowStage.objects.create(
            product=product, stage=free, order=2, cost_rate=D('2'),
            credits_workers=False)
        ct = ClothType.objects.create(name='RMX-COTTON')
        col = ClothColor.objects.create(name='RMX-RED')
        loc = StorageLocation.objects.create(name='RMX-RACK', code='RMX')
        cls.r1 = ClothRoll.objects.create(
            roll_id='RMX-R1', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 3).date(),
            weight_kg=D('25.00'), cost_per_kg=D('100.00'))
        cls.r2 = ClothRoll.objects.create(
            roll_id='RMX-R2', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 4).date(),
            weight_kg=D('10.00'), cost_per_kg=None)          # honest-NULL
        cls.r3 = ClothRoll.objects.create(
            roll_id='RMX-R3', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 8, 1).date(),
            weight_kg=D('5.00'), cost_per_kg=D('50.00'),
            status=ClothRoll.Status.DAMAGED)                  # Aug purchase, damaged

        def mk_adda(code):
            a = Adda.objects.create(code=code, product=product)
            sr_pay = AddaStageRecord.objects.create(
                adda=a, workflow_stage=cls.ws_pay,
                started_at=timezone.now(), processing_cost=D('30.00'))
            sr_free = AddaStageRecord.objects.create(
                adda=a, workflow_stage=cls.ws_free,
                started_at=timezone.now(), processing_cost=D('20.00'))
            return a, sr_pay, sr_free

        cls.a1, cls.a1_pay, cls.a1_free = mk_adda('RMX-A1')
        cls.a2, cls.a2_pay, cls.a2_free = mk_adda('RMX-A2')

        july = timezone.make_aware(datetime(2026, 7, 10, 12))
        august = timezone.make_aware(datetime(2026, 8, 5, 12))
        # A1 consumes R1 in JULY at a VERIFIED weight (24kg ≠ roll's 25kg).
        cls.e1 = LayeringRollEntry.objects.create(
            stage_record=cls.a1_pay, roll=cls.r1,
            weight_verified_kg=D('24.00'))
        LayeringRollEntry.objects.filter(pk=cls.e1.pk).update(attached_at=july)
        # A2 consumes the UNPRICED R2 in July.
        cls.e2 = LayeringRollEntry.objects.create(
            stage_record=cls.a2_pay, roll=cls.r2)
        LayeringRollEntry.objects.filter(pk=cls.e2.pk).update(attached_at=july)
        # Remnant weighed back in AUGUST (straddle month) from A1's entry.
        cls.rem = RemainingClothOfClothRoll.objects.create(
            roll=cls.r1, source_adda=cls.a1, layering_entry=cls.e1,
            remaining_weight_kg=D('2.50'), remaining_length_meters=D('3.00'),
            is_consumed=True, consumed_in_adda=cls.a2, consumed_at=august)
        RemainingClothOfClothRoll.objects.filter(pk=cls.rem.pk).update(
            created_at=august)
        # Settled labor on A1 (Decision-3 source): one voided (excluded).
        StageWorkAssignment.objects.create(
            stage_record=cls.a1_pay, worker=cls.worker,
            allocated_quantity=D('10'), earning_rate_snapshot=D('3'),
            earning_amount_snapshot=D('30.00'))
        StageWorkAssignment.objects.create(
            stage_record=cls.a1_pay, worker=cls.worker,
            allocated_quantity=D('5'), earning_rate_snapshot=D('3'),
            earning_amount_snapshot=D('15.00'), voided_at=timezone.now())


class BulkParityTests(_World):
    def test_bulk_equals_the_original_reference_loop_everywhere(self):
        bulk = material_costs_for_addas([self.a1.pk, self.a2.pk])
        for adda in (self.a1, self.a2):
            ref = reference_material_loop(adda)
            got = bulk[adda.pk]
            for key in ('consumed', 'remnant', 'net', 'leftover_in'):
                self.assertEqual(got[key], ref[key], f"{adda.code}.{key}")
            self.assertEqual(got['unpriced_rolls'], ref['unpriced_rolls'])
            self.assertEqual(got['has_material'], ref['has_material'])
        # concrete values (auditable): A1 = 24×100 − 250 remnant = 2150
        self.assertEqual(bulk[self.a1.pk]['net'], D('2150.00'))
        # A2 = leftover-in 2.5×100 (source price) + unpriced R2 counted
        self.assertEqual(bulk[self.a2.pk]['net'], D('250.00'))
        self.assertEqual(bulk[self.a2.pk]['unpriced_rolls'], 1)

    def test_delegation_parity(self):
        for adda in (self.a1, self.a2):
            self.assertEqual(material_cost_for_adda(adda),
                             material_costs_for_addas([adda.pk])[adda.pk])

    def test_zero_verified_weight_falls_back_like_the_original(self):
        # The Python `or` quirk: verified 0.00 → roll weight (NullIf parity).
        LayeringRollEntry.objects.filter(pk=self.e1.pk).update(
            weight_verified_kg=D('0.00'))
        ref = reference_material_loop(self.a1)
        got = material_cost_for_adda(self.a1)
        self.assertEqual(got['consumed'], ref['consumed'])
        self.assertEqual(got['consumed'], D('2500.00'))   # 25kg roll weight


class AssemblyTests(_World):
    def test_full_cost_components_decision_2(self):
        fc = full_costs_for_addas([self.a1.pk])[self.a1.pk]
        self.assertEqual(fc['settled_total'], D('30.00'))       # voided excluded
        self.assertEqual(fc['nonpayable_priced'], D('20.00'))   # free stage only
        self.assertEqual(fc['material']['net'], D('2150.00'))
        self.assertEqual(fc['full_cost'], D('2200.00'))
        # Decision 1: the PAYABLE standard (30.00) is NOT in the sum.
        self.assertNotEqual(fc['full_cost'],
                            fc['material']['net'] + fc['settled_total']
                            + fc['nonpayable_priced'] + D('30.00'))

    def test_nonpayable_per_ws_equals_per_sr(self):
        # The RMX-B equivalence obligation: a360's per-ws grouping ≡ flat per-SR.
        per_sr = (AddaStageRecord.objects
                  .filter(adda=self.a1, processing_cost__isnull=False,
                          workflow_stage__credits_workers=False)
                  .aggregate(s=djm.Sum('processing_cost'))['s'])
        by_ws = {}
        for sr in AddaStageRecord.objects.filter(adda=self.a1):
            if sr.processing_cost is not None:
                by_ws.setdefault(sr.workflow_stage, []).append(sr.processing_cost)
        per_ws = sum((sum(v, D('0')) for ws, v in by_ws.items()
                      if not ws.credits_workers), D('0'))
        self.assertEqual(per_sr, per_ws)
        self.assertEqual(full_cost_for_adda(self.a1)['nonpayable_priced'], per_sr)

    def test_a360_context_parity(self):
        # The switched view renders THE assembly's numbers (byte-equal keys).
        from production.views.a360 import build_a360
        stages_overview = [
            {'workflow_stage': self.ws_pay, 'label': 'RMX Pay',
             'stage_type': 'rmx_pay', 'sr': self.a1_pay, 'state': 'completed'},
            {'workflow_stage': self.ws_free, 'label': 'RMX Free',
             'stage_type': 'rmx_free', 'sr': self.a1_free, 'state': 'completed'},
        ]
        ctx = build_a360(self.a1, stages_overview, garment_sets=None)
        fc = full_costs_for_addas([self.a1.pk])[self.a1.pk]
        self.assertEqual(ctx['material_net'], fc['material']['net'])
        self.assertEqual(ctx['settled_total'], fc['settled_total'])
        self.assertEqual(ctx['nonpayable_priced'], fc['nonpayable_priced'])
        self.assertEqual(ctx['full_cost'], fc['full_cost'])
        self.assertEqual(ctx['material_unpriced_rolls'],
                         fc['material']['unpriced_rolls'])


class PeriodTests(_World):
    def test_purchases_in_period(self):
        july = material_purchases_in_period(2026, 7)
        self.assertEqual(july['total'], D('2500.0000'))   # R1 only (R2 unpriced)
        self.assertEqual((july['priced_rolls'], july['unpriced_rolls'],
                          july['damaged_rolls']), (1, 1, 0))
        aug = material_purchases_in_period(2026, 8)
        self.assertEqual(aug['total'], D('250.0000'))     # damaged R3 INCLUDED
        self.assertEqual(aug['damaged_rolls'], 1)

    def test_consumption_straddle_month(self):
        july = material_consumption_in_period(2026, 7)
        self.assertEqual(july['consumed'], D('2400.00'))  # A1 entry (24×100)
        self.assertEqual(july['remnant_returned'], D('0.00'))
        self.assertEqual(july['unpriced_events'], 1)      # R2 entry, honest
        aug = material_consumption_in_period(2026, 8)
        self.assertEqual(aug['remnant_returned'], D('250.00'))   # weighed back Aug
        self.assertEqual(aug['leftover_in'], D('250.00'))        # reused Aug
        self.assertEqual(aug['total'], D('0.00'))                # net zero in Aug

    def test_one_rupee_once_identity(self):
        # Σ periods ≡ Σ Addas ≡ intake counted once (the signature identity).
        periods = (material_consumption_in_period(2026, 7)['total']
                   + material_consumption_in_period(2026, 8)['total'])
        addas = sum((material_cost_for_adda(a)['net']
                     for a in (self.a1, self.a2)), D('0'))
        self.assertEqual(periods, addas)
        self.assertEqual(periods, D('2400.00'))   # 24kg consumed of R1, once
        # Purchases ≠ consumption (different honest questions, never blended):
        self.assertEqual(material_purchases_in_period(2026, 7)['total'],
                         D('2500.0000'))


class ReadOnlyPurityTests(_World):
    def test_derives_write_nothing(self):
        from django.apps import apps as djapps
        before = {m._meta.label: m.objects.count()
                  for m in djapps.get_models()}
        material_costs_for_addas([self.a1.pk, self.a2.pk])
        full_costs_for_addas([self.a1.pk, self.a2.pk])
        material_consumption_in_period(2026, 7)
        material_purchases_in_period(2026, 7)
        after = {m._meta.label: m.objects.count()
                 for m in djapps.get_models()}
        self.assertEqual(after, before)

    def test_no_write_tokens_in_the_new_read_paths(self):
        import re
        from pathlib import Path
        src = Path(__file__).resolve().parent.parent / 'services' / 'cost_service.py'
        text = src.read_text()
        engine_section = text[text.index('def _material_value_expr'):]
        self.assertIsNone(
            re.search(r"\.objects\.(create|update|delete|get_or_create|bulk_)",
                      engine_section))
        self.assertNotIn('.save(', engine_section)