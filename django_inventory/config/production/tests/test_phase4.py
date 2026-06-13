"""Phase 4 tests — auto-populated Layering, retro-tag signal, activity timeline.

Covers:
  • create_adda auto-creates Layering stage_record + auto-populates workers M2M
  • create_adda raises ValidationError when no skilled users exist
  • Retro-tag: User.skills.add(cutting_master_helper) → user added to active Layerings
  • Retro-tag does NOT touch completed Adda stage_records
  • Layering worker queryset returns only skilled users
  • adda_activity returns sorted, filtered events
  • user_activity_across_addas honors user filter
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.forms._shared import _layering_worker_queryset
from production.models import WorkerStageTask, AddaStageRecord, Product
from production.services import (
    adda_activity, attach_roll_to_layering, complete_layering,
    create_adda, record_remaining_cloth, sync_layering_workers_for_skill,
    user_activity_across_addas,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
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


class CreateAddaAutoTagTests(TestCase):
    def test_creates_layering_stage_record_with_skilled_workers(self):
        admin = _user('adm@p4.test', skills=['cutting_master'])
        helper = _user('helper@p4.test', role_code='worker', is_super=False,
                       skills=['cutting_master_helper'])
        adda = create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        sr = AddaStageRecord.objects.get(
            adda=adda,
            workflow_stage__stage__code='layering',
        )
        self.assertIsNotNone(sr.started_at)
        self.assertIsNone(sr.completed_at)
        worker_pks = {u.pk for u in sr.active_workers}
        self.assertEqual(worker_pks, {admin.pk, helper.pk})

    def test_rejects_create_adda_when_no_skilled_users(self):
        # Admin with NO cutting_master skill — pool is empty
        admin = _user('plain@p4.test')
        with self.assertRaises(ValidationError):
            create_adda(admin, product=Product.objects.get(code='NIKKAR'))

    def test_archived_product_rejected_before_skill_check(self):
        # Order check: archived product → ValidationError even without skilled users
        admin = _user('plain2@p4.test')
        product = Product.objects.get(code='NIKKAR')
        product.is_active = False
        product.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            create_adda(admin, product=product)


class RetroTagTests(TestCase):
    def test_new_skill_user_retro_tagged_to_active_layering(self):
        admin = _user('adm@retro.test', skills=['cutting_master'])
        adda = create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        sr = AddaStageRecord.objects.get(
            adda=adda,
            workflow_stage__stage__code='layering',
        )
        # New helper user added AFTER adda exists.
        late = _user('late@retro.test', role_code='worker', is_super=False)
        self.assertFalse(sr.is_worker_assigned(late))
        late.skills.add(Skill.objects.get(name='cutting_master_helper'))
        # No signal anymore (CLAUDE.md rule #4) — retro-tag is an EXPLICIT call,
        # made by the user-management service after skills change.
        sync_layering_workers_for_skill(late)
        self.assertTrue(sr.is_worker_assigned(late))

    def test_retro_tag_skips_completed_stage_records(self):
        admin = _user('adm@retro2.test',
                      skills=['cutting_master', 'cutting_master_helper'])
        # Complete a layering on adda1
        adda1 = create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': red, 'qty': 1}],
        )
        sr1 = AddaStageRecord.objects.get(
            adda=adda1, workflow_stage__stage__code='layering',
        )
        entry = attach_roll_to_layering(
            stage_record=sr1, roll=rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=admin,
        )
        record_remaining_cloth(
            entry=entry, remaining_weight_kg=Decimal('0'),
            remaining_length_meters=Decimal('0'), user=admin,
        )
        complete_layering(
            adda=adda1, duration_minutes=10,
            layer_length_meters=Decimal('1.5'),
            per_entry_layers={entry.pk: 3},
            notes='', user=admin,
        )
        sr1.refresh_from_db()
        self.assertIsNotNone(sr1.completed_at)

        # Even when the retro-tag sync runs, it must NOT add them to the
        # COMPLETED adda1's stage_record (only active layerings get tagged).
        late = _user('late@retro2.test', role_code='worker', is_super=False)
        late.skills.add(Skill.objects.get(name='cutting_master_helper'))
        sync_layering_workers_for_skill(late)
        self.assertFalse(sr1.is_worker_assigned(late))

    def test_sync_helper_callable_directly(self):
        admin = _user('adm@dir.test', skills=['cutting_master'])
        create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        u = _user('dir@dir.test', role_code='worker', is_super=False,
                  skills=['cutting_master_helper'])
        # First explicit sync tags them onto the active layering; a SECOND sync
        # must be idempotent (no double-add).
        sync_layering_workers_for_skill(u)
        before = WorkerStageTask.objects.filter(worker=u).exclude(
            status=WorkerStageTask.Status.CANCELLED).count()
        sync_layering_workers_for_skill(u)
        after = WorkerStageTask.objects.filter(worker=u).exclude(
            status=WorkerStageTask.Status.CANCELLED).count()
        self.assertEqual(before, after)


class LayeringWorkerQuerysetTests(TestCase):
    def test_returns_only_skilled_users(self):
        _user('m@q.test', role_code='manager', is_super=False)   # manager, no skill
        cm = _user('cm@q.test', role_code='worker', is_super=False,
                   skills=['cutting_master'])
        cmh = _user('cmh@q.test', role_code='worker', is_super=False,
                    skills=['cutting_master_helper'])
        emails = set(_layering_worker_queryset().values_list('email', flat=True))
        self.assertIn(cm.email, emails)
        self.assertIn(cmh.email, emails)
        self.assertNotIn('m@q.test', emails)


class ActivityTimelineTests(TestCase):
    def setUp(self):
        self.admin = _user('adm@act.test',
                           skills=['cutting_master', 'cutting_master_helper'])
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        self.rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': red, 'qty': 1}],
        )
        sr = AddaStageRecord.objects.get(adda=self.adda, workflow_stage__stage__code='layering')
        attach_roll_to_layering(
            stage_record=sr, roll=self.rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=self.admin,
        )

    def test_adda_activity_returns_events_sorted_desc(self):
        events = adda_activity(self.adda)
        self.assertGreater(len(events), 0)
        # Newest first
        ts = [e.at for e in events]
        self.assertEqual(ts, sorted(ts, reverse=True))
        # At least one event references the roll's roll_id (target = display_summary now,
        # which includes id + type + color + width — substring match is enough)
        targets = [e.target for e in events]
        self.assertTrue(any(self.rolls[0].roll_id in t for t in targets))

    def test_user_activity_across_addas_filters_by_user(self):
        outsider = _user('out@act.test', role_code='worker', is_super=False)
        events_admin = user_activity_across_addas(self.admin, limit=50)
        events_outsider = user_activity_across_addas(outsider, limit=50)
        self.assertGreater(len(events_admin), 0)
        self.assertEqual(len(events_outsider), 0)
