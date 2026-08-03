"""Adda delete + cancel safety (owner rule 2026-07-22).

YEH FILE KYU HAI?
─────────────────
An Adda is the factory's heart. It must NOT be deletable accidentally, and NEVER
when workers earn from it or money is booked. This suite pins:

  • super_admin ONLY may cancel/delete (manager + worker refused)
  • hard-delete allowed ONLY for a pristine batch (no completed stage, no
    settlement / earning / allocation / reported production / barcode)
  • each block reason refuses the delete AND leaves the Adda intact
  • the model-level `delete()` guard fires even on a raw shell delete
  • cancel_adda soft-abandons (status→CANCELLED, history logged, open tasks
    auto-cancelled) and is itself money-guarded (no delete/cancel once settled)
  • the Django admin delete surface is disabled (old M-5 ProtectedError-500)
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from accounts.models import Skill, User
from accounts.skills import SKILL_CUTTING_MASTER
from inventory.models import Role
from production.admin import AddaAdmin
from production.models import (
    Adda, AddaStageRecord, Product, ProductSize, WorkerStageAllocation,
    WorkerStageContribution, WorkerStageTask,
)
from production.services import cancel_adda, create_adda, delete_adda
from django.contrib import admin as django_admin
from expense.models import AddaSettlement, StageWorkAssignment
from raw_materials.models import ClothColor
from tracking.models import AddaHistory, BarcodeBatch


def _user(email, *, role_code, is_super, skills=()):
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(
        email=email, password='x', is_superuser=is_super, is_staff=is_super)
    u.role = role
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class AddaDeleteFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.get(code='T-SHIRT')
        # super_admin also carries the cutting skill so create_adda's "some
        # skilled user must exist" guard (spec D6) passes.
        cls.super_admin = _user('sa@x.com', role_code='super_admin',
                                is_super=True, skills=[SKILL_CUTTING_MASTER])
        cls.manager = _user('mgr@x.com', role_code='manager', is_super=False)
        cls.worker = _user('wkr@x.com', role_code='worker', is_super=False)

    def _fresh_adda(self):
        """A brand-new (pristine) batch — layering SR + streams, no work yet."""
        return create_adda(user=self.super_admin, product=self.product)

    def _first_sr(self, adda):
        return AddaStageRecord.objects.filter(adda=adda).first()


class PristineDeleteTests(AddaDeleteFixture):
    def test_pristine_adda_is_safe_to_delete(self):
        adda = self._fresh_adda()
        self.assertEqual(adda.deletion_block_reason(), '')
        self.assertTrue(adda.can_delete)

    def test_super_admin_deletes_pristine_adda(self):
        adda = self._fresh_adda()
        code = delete_adda(adda, user=self.super_admin, reason='created by mistake')
        self.assertFalse(Adda.objects.filter(code=code).exists())

    def test_delete_rejects_manager_and_worker(self):
        for actor in (self.manager, self.worker):
            adda = self._fresh_adda()
            with self.assertRaises(PermissionDenied):
                delete_adda(adda, user=actor, reason='x')
            self.assertTrue(Adda.objects.filter(pk=adda.pk).exists())

    def test_delete_requires_reason(self):
        adda = self._fresh_adda()
        with self.assertRaises(ValidationError):
            delete_adda(adda, user=self.super_admin, reason='   ')
        self.assertTrue(Adda.objects.filter(pk=adda.pk).exists())


class DeleteBlockedTests(AddaDeleteFixture):
    """Every block reason refuses the delete AND keeps the Adda."""

    def _assert_blocked(self, adda):
        self.assertNotEqual(adda.deletion_block_reason(), '')
        with self.assertRaises(ValidationError):
            delete_adda(adda, user=self.super_admin, reason='try')
        self.assertTrue(Adda.objects.filter(pk=adda.pk).exists())

    def test_blocked_by_completed_stage(self):
        adda = self._fresh_adda()
        sr = self._first_sr(adda)
        sr.completed_at = timezone.now()
        sr.save(update_fields=['completed_at'])
        self._assert_blocked(adda)

    def test_blocked_by_settlement(self):
        adda = self._fresh_adda()
        AddaSettlement.objects.create(reference='ADST-DELTEST', adda=adda)
        self._assert_blocked(adda)

    def test_blocked_by_earning_assignment(self):
        adda = self._fresh_adda()
        StageWorkAssignment.objects.create(
            stage_record=self._first_sr(adda), worker=self.worker,
            allocated_quantity=Decimal('1'), earning_rate_snapshot=Decimal('1'),
            earning_amount_snapshot=Decimal('1'))
        self._assert_blocked(adda)

    def test_blocked_by_allocation(self):
        adda = self._fresh_adda()
        WorkerStageAllocation.objects.create(
            stage_record=self._first_sr(adda), worker=self.worker,
            allocated_quantity=Decimal('1'), created_by=self.super_admin)
        self._assert_blocked(adda)

    def test_blocked_by_reported_production(self):
        adda = self._fresh_adda()
        task = WorkerStageTask.objects.create(
            stage_record=self._first_sr(adda), worker=self.worker)
        WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('5'), good_quantity=Decimal('5'))
        self._assert_blocked(adda)

    def test_blocked_by_barcode(self):
        adda = self._fresh_adda()
        size = ProductSize.objects.filter(product=self.product).first()
        color = ClothColor.objects.create(name='DEL-TEST-RED', hex_code='#ff0000')
        BarcodeBatch.objects.create(
            adda=adda, product=self.product, color=color, size=size,
            start_seq=1, end_seq=5, total_pieces=5)
        self._assert_blocked(adda)

    def test_model_delete_guard_raises_on_unsafe(self):
        # Raw shell/admin `adda.delete()` must ALSO refuse an unsafe delete.
        adda = self._fresh_adda()
        AddaSettlement.objects.create(reference='ADST-GUARD', adda=adda)
        with self.assertRaises(ValidationError):
            adda.delete()
        self.assertTrue(Adda.objects.filter(pk=adda.pk).exists())


class CancelTests(AddaDeleteFixture):
    def test_cancel_sets_status_logs_and_cancels_open_tasks(self):
        adda = self._fresh_adda()
        task = WorkerStageTask.objects.create(
            stage_record=self._first_sr(adda), worker=self.worker,
            status=WorkerStageTask.Status.ASSIGNED)
        cancel_adda(adda, user=self.super_admin, reason='wrong product picked')
        adda.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(adda.status, Adda.Status.CANCELLED)
        self.assertEqual(task.status, WorkerStageTask.Status.CANCELLED)
        self.assertTrue(AddaHistory.objects.filter(
            adda=adda, change_type=AddaHistory.ChangeType.ADDA_CANCELLED).exists())

    def test_cancel_rejects_non_super_admin(self):
        for actor in (self.manager, self.worker):
            adda = self._fresh_adda()
            with self.assertRaises(PermissionDenied):
                cancel_adda(adda, user=actor, reason='x')

    def test_cancel_requires_reason(self):
        adda = self._fresh_adda()
        with self.assertRaises(ValidationError):
            cancel_adda(adda, user=self.super_admin, reason='')

    def test_cancel_blocked_by_settlement(self):
        adda = self._fresh_adda()
        AddaSettlement.objects.create(reference='ADST-CANTEST', adda=adda)
        with self.assertRaises(ValidationError):
            cancel_adda(adda, user=self.super_admin, reason='try')
        adda.refresh_from_db()
        self.assertNotEqual(adda.status, Adda.Status.CANCELLED)

    def test_cancel_blocked_when_completed(self):
        adda = self._fresh_adda()
        adda.status = Adda.Status.COMPLETED
        adda.save(update_fields=['status'])
        with self.assertRaises(ValidationError):
            cancel_adda(adda, user=self.super_admin, reason='try')


class AdminAndViewTests(AddaDeleteFixture):
    def test_admin_delete_permission_disabled(self):
        model_admin = AddaAdmin(Adda, django_admin.site)
        req = RequestFactory().get('/admin/')
        req.user = self.super_admin
        self.assertFalse(model_admin.has_delete_permission(req))

    def test_delete_confirm_get_gated(self):
        adda = self._fresh_adda()
        url = reverse('production:adda-delete', kwargs={'code': adda.code})
        # worker → 403 (SuperAdminOnlyMixin)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        # super_admin → 200 confirm page
        self.client.force_login(self.super_admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_delete_confirm_shows_block_reason_when_unsafe(self):
        adda = self._fresh_adda()
        AddaSettlement.objects.create(reference='ADST-VIEW', adda=adda)
        self.client.force_login(self.super_admin)
        resp = self.client.get(
            reverse('production:adda-delete', kwargs={'code': adda.code}))
        self.assertNotEqual(resp.context['block_reason'], '')
