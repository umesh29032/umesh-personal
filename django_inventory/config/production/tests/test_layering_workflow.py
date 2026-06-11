"""Tests for the expanded Layering stage workflow.

YEH FILE KYU HAI?
─────────────────
Naya layering workspace flow:
  start_layering → attach_roll_to_layering → update / detach → complete_layering

Test coverage:
  • start_layering RBAC + cutting_master skill requirement
  • attach_roll flips ClothRoll.status, creates entry
  • detach_roll reverses status + deletes entry
  • update_entry edits both entry and ClothRoll fields
  • complete_layering requires cutting_master_helper skill (super_admin bypass)
  • cannot complete without rolls
  • cannot attach after completion
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    AddaStageRecord, LayeringRollEntry, Product, RemainingClothOfClothRoll,
)
from production.services import (
    attach_roll_to_layering, complete_layering, create_adda,
    detach_roll_from_layering, record_remaining_cloth, remove_remaining_cloth,
    start_layering, update_layering_roll_entry,
)
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _user(email, *, role_code='super_admin', is_super=True, skills=()):
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(email=email, password='x',
                                  is_superuser=is_super, is_staff=is_super)
    u.role = role
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


def _seed_rolls_and_adda(user, qty=2):
    cotton = ClothType.objects.get(name='Cotton')
    red = ClothColor.objects.get(name='Red')
    loc = StorageLocation.objects.get(code='ROHINI')
    rolls = bulk_create_rolls(
        user=user, cloth_type=cotton, storage_location=loc,
        purchased_date=date.today(),
        breakup=[{'color': red, 'qty': qty}],
    )
    adda = create_adda(user, product=Product.objects.get(code='T-SHIRT'))
    return adda, rolls


class StartLayeringTests(TestCase):
    def test_creates_stage_record_with_started_at(self):
        admin = _user('a@s.test', skills=['cutting_master'])
        adda, _ = _seed_rolls_and_adda(admin)
        sr = start_layering(adda=adda, worker_ids=[admin.pk], user=admin)
        self.assertIsNotNone(sr.started_at)
        self.assertIsNone(sr.completed_at)
        self.assertEqual(sr.workflow_stage.stage_type, 'layering')
        self.assertTrue(sr.is_worker_assigned(admin))

    def test_requires_management_role(self):
        admin = _user('mgr@s.test', skills=['cutting_master'])
        adda, _ = _seed_rolls_and_adda(admin)
        # Karigar role — not management
        karigar = _user('k@s.test', role_code='worker', is_super=False,
                        skills=['cutting_master'])
        with self.assertRaises(PermissionDenied):
            start_layering(adda=adda, worker_ids=[karigar.pk], user=karigar)

    def test_requires_cutting_master_worker(self):
        # Need ≥1 skilled user in DB so create_adda passes the pool check
        _user('seed@s.test', role_code='worker', is_super=False,
              skills=['cutting_master'])
        admin = _user('a2@s.test')   # super_admin
        adda, _ = _seed_rolls_and_adda(admin)
        # start_layering with worker_ids who have NO cutting_master skill → reject
        nonskilled = _user('ns@s.test', role_code='worker', is_super=False)
        with self.assertRaises(ValidationError):
            start_layering(adda=adda, worker_ids=[nonskilled.pk], user=admin)

    def test_idempotent_reassign(self):
        admin = _user('a3@s.test', skills=['cutting_master'])
        adda, _ = _seed_rolls_and_adda(admin)
        sr1 = start_layering(adda=adda, worker_ids=[admin.pk], user=admin)
        sr2 = start_layering(adda=adda, worker_ids=[admin.pk], user=admin)
        self.assertEqual(sr1.pk, sr2.pk)
        self.assertEqual(AddaStageRecord.objects.filter(adda=adda).count(), 1)


class AttachRollTests(TestCase):
    def setUp(self):
        self.admin = _user('att@s.test', skills=['cutting_master'])
        self.adda, self.rolls = _seed_rolls_and_adda(self.admin, qty=2)
        self.sr = start_layering(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)

    def test_attach_flips_status_and_creates_entry(self):
        roll = self.rolls[0]
        self.assertEqual(roll.status, ClothRoll.Status.NOT_USED)
        entry = attach_roll_to_layering(
            stage_record=self.sr, roll=roll,
            width_verified_inch=42, weight_verified_kg=Decimal('25.5'),
            user=self.admin,
        )
        roll.refresh_from_db()
        self.assertEqual(roll.status, ClothRoll.Status.USED)
        self.assertEqual(roll.adda_id, self.adda.pk)
        self.assertEqual(entry.width_verified_inch, 42)
        self.assertEqual(entry.weight_verified_kg, Decimal('25.5'))
        self.assertEqual(LayeringRollEntry.objects.count(), 1)

    def test_skill_gate_rejects_unrelated_user(self):
        # Karigar role (NOT management) + not on workers list → must reject.
        # Manager role would bypass via _ensure_assigned_worker — that's by design.
        outsider = _user('o@s.test', role_code='worker', is_super=False)
        with self.assertRaises(PermissionDenied):
            attach_roll_to_layering(
                stage_record=self.sr, roll=self.rolls[0],
                width_verified_inch=40, weight_verified_kg=Decimal('20'),
                user=outsider,
            )

    def test_cannot_double_attach_same_roll(self):
        roll = self.rolls[0]
        attach_roll_to_layering(
            stage_record=self.sr, roll=roll,
            width_verified_inch=40, weight_verified_kg=Decimal('20'),
            user=self.admin,
        )
        with self.assertRaises(Exception):   # ValidationError ya IntegrityError dono allowed
            attach_roll_to_layering(
                stage_record=self.sr, roll=roll,
                width_verified_inch=40, weight_verified_kg=Decimal('20'),
                user=self.admin,
            )


class UpdateAndDetachTests(TestCase):
    def setUp(self):
        self.admin = _user('upd@s.test', skills=['cutting_master'])
        self.adda, self.rolls = _seed_rolls_and_adda(self.admin, qty=1)
        self.sr = start_layering(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.entry = attach_roll_to_layering(
            stage_record=self.sr, roll=self.rolls[0],
            width_verified_inch=40, weight_verified_kg=Decimal('20'),
            user=self.admin,
        )

    def test_update_entry_propagates_to_roll(self):
        update_layering_roll_entry(
            entry=self.entry,
            width_verified_inch=44,
            weight_verified_kg=Decimal('22.5'),
            notes='corrected',
            user=self.admin,
        )
        self.entry.refresh_from_db()
        self.rolls[0].refresh_from_db()
        self.assertEqual(self.entry.width_verified_inch, 44)
        self.assertEqual(self.entry.weight_verified_kg, Decimal('22.5'))
        self.assertEqual(self.entry.notes, 'corrected')
        self.assertEqual(self.rolls[0].width_inch, 44)
        self.assertEqual(self.rolls[0].weight_kg, Decimal('22.5'))

    def test_detach_reverses_roll_status(self):
        detach_roll_from_layering(entry=self.entry, user=self.admin)
        self.rolls[0].refresh_from_db()
        self.assertEqual(self.rolls[0].status, ClothRoll.Status.NOT_USED)
        self.assertIsNone(self.rolls[0].adda)
        self.assertFalse(LayeringRollEntry.objects.filter(pk=self.entry.pk).exists())


class CompleteLayeringTests(TestCase):
    def setUp(self):
        self.admin = _user('cmp@s.test', skills=['cutting_master', 'cutting_master_helper'])
        self.adda, self.rolls = _seed_rolls_and_adda(self.admin, qty=2)
        self.sr = start_layering(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.entries = []
        for r in self.rolls:
            self.entries.append(attach_roll_to_layering(
                stage_record=self.sr, roll=r,
                width_verified_inch=42, weight_verified_kg=Decimal('25'),
                user=self.admin,
            ))
        # Leftover mandatory before complete (Phase 6 rule)
        for e in self.entries:
            record_remaining_cloth(
                entry=e, remaining_weight_kg=Decimal('0'),
                remaining_length_meters=Decimal('0'), user=self.admin,
            )

    def _complete_args(self, **overrides):
        """Default kwargs for complete_layering — every entry gets 3 layers, 1.5m length."""
        args = {
            'adda': self.adda,
            'duration_minutes': 20,
            'layer_length_meters': Decimal('1.5'),
            'per_entry_layers': {e.pk: 3 for e in self.entries},
            'notes': '',
            'user': self.admin,
        }
        args.update(overrides)
        return args

    def test_complete_advances_adda_to_cutting(self):
        lr = complete_layering(**self._complete_args(notes='ok'))
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage.stage_type, 'cutting')
        # 2 entries × 3 layers each = 6 total
        self.assertEqual(lr.lay_count, 6)
        self.assertEqual(lr.layer_length_meters, Decimal('1.5'))
        self.assertEqual(lr.total_colors, 1)
        self.assertEqual(lr.rolls_used.count(), 2)
        # Per-roll data propagates to ClothRoll itself (for future Adda predictions)
        for roll in self.rolls:
            roll.refresh_from_db()
            self.assertEqual(roll.layers_on_roll, 3)
            self.assertEqual(roll.layer_length_meters, Decimal('1.5'))

    def test_cannot_complete_without_rolls(self):
        adda2, _ = _seed_rolls_and_adda(self.admin)
        start_layering(adda=adda2, worker_ids=[self.admin.pk], user=self.admin)
        with self.assertRaises(ValidationError):
            complete_layering(
                adda=adda2, duration_minutes=1,
                layer_length_meters=Decimal('1.0'),
                per_entry_layers={},
                notes='', user=self.admin,
            )

    def test_helper_skill_required(self):
        # Manager role, no helper skill, also no super_admin → reject
        manager = _user('m@s.test', role_code='manager', is_super=False,
                        skills=['cutting_master'])
        with self.assertRaises(PermissionDenied):
            complete_layering(**self._complete_args(user=manager))

    def test_superuser_bypasses_skill_gate(self):
        # admin has helper skill anyway, but also test bare super_admin
        admin2 = _user('s2@s.test')   # super, no skills
        complete_layering(**self._complete_args(user=admin2))
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage.stage_type, 'cutting')

    def test_cannot_attach_after_completion(self):
        complete_layering(**self._complete_args())
        # New roll, but stage_record already completed → reject
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        extra = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=[{'color': red, 'qty': 1}],
        )[0]
        with self.assertRaises(ValidationError):
            attach_roll_to_layering(
                stage_record=self.sr, roll=extra,
                width_verified_inch=42, weight_verified_kg=Decimal('25'),
                user=self.admin,
            )


class LayerMetricsAndLeftoverTests(TestCase):
    """Phase 6 tests — per-roll layers set at completion + RemainingClothOfClothRoll."""

    def setUp(self):
        self.admin = _user('p6@s.test', skills=['cutting_master', 'cutting_master_helper'])
        self.adda, self.rolls = _seed_rolls_and_adda(self.admin, qty=1)
        self.sr = start_layering(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.entry = attach_roll_to_layering(
            stage_record=self.sr, roll=self.rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=self.admin,
        )

    def test_complete_persists_per_roll_layers_and_overall_length(self):
        # Leftover required before complete (Phase 6)
        record_remaining_cloth(
            entry=self.entry, remaining_weight_kg=Decimal('0'),
            remaining_length_meters=Decimal('0'), user=self.admin,
        )
        complete_layering(
            adda=self.adda, duration_minutes=20,
            layer_length_meters=Decimal('1.50'),
            per_entry_layers={self.entry.pk: 12},
            notes='', user=self.admin,
        )
        self.entry.refresh_from_db()
        self.rolls[0].refresh_from_db()
        self.assertEqual(self.entry.layers_on_roll, 12)
        self.assertEqual(self.rolls[0].layers_on_roll, 12)
        self.assertEqual(self.rolls[0].layer_length_meters, Decimal('1.50'))

    def test_record_remaining_cloth_creates_row(self):
        lo = record_remaining_cloth(
            entry=self.entry,
            remaining_weight_kg=Decimal('2.50'),
            remaining_length_meters=Decimal('1.75'),
            notes='small piece',
            user=self.admin,
        )
        self.assertIsInstance(lo, RemainingClothOfClothRoll)
        self.assertEqual(lo.roll_id, self.rolls[0].pk)
        self.assertEqual(lo.source_adda_id, self.adda.pk)
        self.assertEqual(lo.layering_entry_id, self.entry.pk)
        self.assertEqual(lo.remaining_weight_kg, Decimal('2.50'))
        self.assertFalse(lo.is_consumed)

    def test_record_remaining_cloth_rejects_negative(self):
        # Zero allowed ("no leftover" case); negative is the actual invalid input.
        with self.assertRaises(ValidationError):
            record_remaining_cloth(
                entry=self.entry,
                remaining_weight_kg=Decimal('-1'),
                remaining_length_meters=Decimal('1'),
                user=self.admin,
            )
        with self.assertRaises(ValidationError):
            record_remaining_cloth(
                entry=self.entry,
                remaining_weight_kg=Decimal('1'),
                remaining_length_meters=Decimal('-1'),
                user=self.admin,
            )

    def test_remove_remaining_cloth_deletes_row(self):
        lo = record_remaining_cloth(
            entry=self.entry,
            remaining_weight_kg=Decimal('2'), remaining_length_meters=Decimal('1.5'),
            user=self.admin,
        )
        pk = lo.pk
        remove_remaining_cloth(leftover=lo, user=self.admin)
        self.assertFalse(RemainingClothOfClothRoll.objects.filter(pk=pk).exists())

    def test_remove_blocked_when_consumed(self):
        lo = record_remaining_cloth(
            entry=self.entry,
            remaining_weight_kg=Decimal('2'), remaining_length_meters=Decimal('1.5'),
            user=self.admin,
        )
        lo.is_consumed = True
        lo.save(update_fields=['is_consumed'])
        with self.assertRaises(ValidationError):
            remove_remaining_cloth(leftover=lo, user=self.admin)
