"""V1.1 item-1 (2026-07-12): the roll DAMAGE lifecycle — a whole unusable
roll leaves available stock honestly (soft status, never delete), audited
with a mandatory reason; partial damage stays the audited weight-correction
path. Every 'available' read filters NOT_USED so DAMAGED self-excludes
from pickers, guards and counts."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from raw_materials.models import (ClothColor, ClothRoll, ClothType,
                                  StorageLocation)
from raw_materials.services.roll_service import (mark_roll_damaged,
                                                 restore_damaged_roll)
from tracking.models import ClothRollHistory

User = get_user_model()


class _RollWorld(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user('rdmg@test.local', password='x',
                                            is_superuser=True)
        self.mgr.role = Role.objects.get(code='super_admin')
        self.mgr.save()
        self.worker = User.objects.create_user('rdmgw@test.local',
                                               password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        ctype = ClothType.objects.first() or ClothType.objects.create(
            name='DMG Knit')
        loc = StorageLocation.objects.first() or StorageLocation.objects.create(
            name='DMG Rack')
        color = ClothColor.objects.create(name='DMG Blue')
        self.roll = ClothRoll.objects.create(
            roll_id='DMG-R1', cloth_type=ctype, cloth_color=color,
            storage_location=loc, weight_kg=Decimal('20'), width_inch=60,
            cost_per_kg=Decimal('100'),
            purchased_date=timezone.now().date())


class MarkDamagedTests(_RollWorld):
    def test_management_only(self):
        with self.assertRaises(PermissionDenied):
            mark_roll_damaged(self.worker, roll=self.roll, reason='water')

    def test_reason_mandatory(self):
        with self.assertRaisesMessage(ValidationError, 'reason is required'):
            mark_roll_damaged(self.mgr, roll=self.roll, reason='  ')

    def test_marks_and_audits(self):
        mark_roll_damaged(self.mgr, roll=self.roll,
                          reason='Water damage — monsoon leak in storage')
        self.roll.refresh_from_db()
        self.assertEqual(self.roll.status, ClothRoll.Status.DAMAGED)
        h = ClothRollHistory.objects.filter(
            roll=self.roll, change_type='status_changed').latest('created_at')
        self.assertIn('Water damage', h.note)
        self.assertEqual((h.old_value, h.new_value),
                         ('not_used', 'damaged'))

    def test_used_roll_refused(self):
        self.roll.status = ClothRoll.Status.USED
        self.roll.save(update_fields=['status'])
        with self.assertRaisesMessage(ValidationError, 'already consumed'):
            mark_roll_damaged(self.mgr, roll=self.roll, reason='late find')

    def test_damaged_roll_leaves_available_stock_and_pickers(self):
        mark_roll_damaged(self.mgr, roll=self.roll, reason='fungus')
        self.assertFalse(ClothRoll.objects.filter(
            status=ClothRoll.Status.NOT_USED, pk=self.roll.pk).exists())
        # the assign guard (status != NOT_USED refusal) now covers damage
        from raw_materials.services.roll_service import assign_roll_to_adda
        from production.models import Adda, Product, Stage, WorkflowStage
        product = Product.objects.create(code='DMG', name='Dmg')
        ws = WorkflowStage.objects.create(
            product=product, stage=Stage.objects.get(code='layering'),
            order=1, cost_rate=Decimal('1'))
        adda = Adda.objects.create(code='DMG-001', product=product,
                                   current_stage=ws)
        with self.assertRaises(ValidationError):
            assign_roll_to_adda(self.mgr, roll=self.roll, adda=adda,
                                weight_kg=Decimal('20'), width_inch=60)


class RestoreTests(_RollWorld):
    def test_restore_roundtrip_audited(self):
        mark_roll_damaged(self.mgr, roll=self.roll, reason='suspected fungus')
        restore_damaged_roll(self.mgr, roll=self.roll,
                             reason='Inspected — only the wrapper was stained')
        self.roll.refresh_from_db()
        self.assertEqual(self.roll.status, ClothRoll.Status.NOT_USED)
        notes = list(ClothRollHistory.objects.filter(
            roll=self.roll, change_type='status_changed')
            .values_list('note', flat=True))
        self.assertTrue(any('damaged:' in n for n in notes))
        self.assertTrue(any('restored:' in n for n in notes))

    def test_only_damaged_restores(self):
        with self.assertRaisesMessage(ValidationError, 'Only a damaged'):
            restore_damaged_roll(self.mgr, roll=self.roll, reason='x')

    def test_view_gate_worker_403(self):
        self.client.force_login(self.worker)
        resp = self.client.post(f'/raw-materials/rolls/{self.roll.pk}/damage/',
                                {'reason': 'water'})
        self.assertEqual(resp.status_code, 403)
