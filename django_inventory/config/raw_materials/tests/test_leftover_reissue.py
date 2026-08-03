"""V1.1 item-2 (2026-07-12): the leftover RE-ISSUE wiring around the LOCKED
`consume_leftover` writer (C-1/ADR-0009: whole piece · valued at the SOURCE
roll's ₹/kg forever · one-shot · append-only · never back into the source
Adda) — the console door, the consuming-Adda history row, and the material
derive counting reused cloth exactly once across Addas."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from production.models import (Adda, AddaStageRecord, LayeringRollEntry,
                               Product, RemainingClothOfClothRoll, Stage,
                               WorkflowStage)
from production.services.cost_service import material_cost_for_adda
from raw_materials.models import (ClothColor, ClothRoll, ClothType,
                                  StorageLocation)
from raw_materials.services.roll_service import consume_leftover
from tracking.models import AddaHistory

User = get_user_model()


class _LeftoverWorld(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user('lore@test.local', password='x',
                                            is_superuser=True)
        self.mgr.role = Role.objects.get(code='super_admin')
        self.mgr.save()
        self.worker = User.objects.create_user('lorew@test.local',
                                               password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        ctype = ClothType.objects.first() or ClothType.objects.create(
            name='LO Knit')
        loc = StorageLocation.objects.first() or StorageLocation.objects.create(
            name='LO Rack')
        color = ClothColor.objects.create(name='LO Green')
        self.roll = ClothRoll.objects.create(
            roll_id='LO-R1', cloth_type=ctype, cloth_color=color,
            storage_location=loc, weight_kg=Decimal('25'), width_inch=60,
            cost_per_kg=Decimal('200'),
            purchased_date=timezone.now().date())
        self.product = Product.objects.create(code='LOR', name='Leftover')
        ws = WorkflowStage.objects.create(
            product=self.product, stage=Stage.objects.get(code='layering'),
            order=1, cost_rate=Decimal('1'))
        self.source = Adda.objects.create(code='LOR-001',
                                          product=self.product,
                                          current_stage=ws)
        self.target = Adda.objects.create(code='LOR-002',
                                          product=self.product,
                                          current_stage=ws)
        sr = AddaStageRecord.objects.create(
            adda=self.source, workflow_stage=ws, started_at=timezone.now())
        entry = LayeringRollEntry.objects.create(
            stage_record=sr, roll=self.roll,
            width_verified_inch=60, weight_verified_kg=Decimal('25'))
        self.leftover = RemainingClothOfClothRoll.objects.create(
            layering_entry=entry, roll=self.roll, source_adda=self.source,
            remaining_weight_kg=Decimal('2.5'),
            remaining_length_meters=Decimal('1.2'), created_by=self.mgr)


class ConsumeWiringTests(_LeftoverWorld):
    def test_consume_writes_consuming_adda_history(self):
        consume_leftover(self.mgr, leftover=self.leftover, adda=self.target)
        ev = AddaHistory.objects.get(adda=self.target,
                                     change_type='roll_assigned')
        self.assertIn('leftover', ev.note)
        self.assertIn('LOR-001', ev.note)

    def test_one_shot_and_never_home(self):
        with self.assertRaisesMessage(ValidationError, 'produced it'):
            consume_leftover(self.mgr, leftover=self.leftover,
                             adda=self.source)
        consume_leftover(self.mgr, leftover=self.leftover, adda=self.target)
        with self.assertRaisesMessage(ValidationError, 'already consumed'):
            consume_leftover(self.mgr, leftover=self.leftover,
                             adda=self.target)

    def test_material_counts_exactly_once_across_addas(self):
        """Source pays consumed − remnant; the consumer pays the remnant at
        the SOURCE price — Σ across both = the cloth actually taken."""
        src_before = material_cost_for_adda(self.source)
        # 25 kg × 200 − 2.5 kg × 200
        self.assertEqual(src_before['net'], Decimal('4500.00'))
        consume_leftover(self.mgr, leftover=self.leftover, adda=self.target)
        tgt = material_cost_for_adda(self.target)
        self.assertEqual(tgt['leftover_in'], Decimal('500.00'))
        self.assertEqual(tgt['net'], Decimal('500.00'))
        src_after = material_cost_for_adda(self.source)
        self.assertEqual(src_after['net'], Decimal('4500.00'))
        self.assertEqual(src_after['net'] + tgt['net'], Decimal('5000.00'))

    def test_console_door_gates_and_works(self):
        # worker refused at the view wall
        self.client.force_login(self.worker)
        resp = self.client.post(
            f'/production/addas/{self.target.code}/layering/use-leftover/',
            {'leftover': self.leftover.pk})
        self.assertIn(resp.status_code, (302, 403))
        self.leftover.refresh_from_db()
        self.assertFalse(self.leftover.is_consumed)
        # management succeeds through the same door
        self.client.force_login(self.mgr)
        resp = self.client.post(
            f'/production/addas/{self.target.code}/layering/use-leftover/',
            {'leftover': self.leftover.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.leftover.refresh_from_db()
        self.assertTrue(self.leftover.is_consumed)
        self.assertEqual(self.leftover.consumed_in_adda_id, self.target.pk)
