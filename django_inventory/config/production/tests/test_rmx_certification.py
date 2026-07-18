"""RMX-E (Phase 17) — THE money-certification suite: one full-scenario world
(priced · unpriced · leftover chain · remnant · damaged · shared source roll ·
straddle months), every user-visible surface cross-checked against the ONE
certified source, the reconciliation identities, and the ADR-0011 separation
proven in BOTH directions."""

from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import StageWorkAssignment
from production.models import (
    Adda, AddaStageRecord, LayeringRollEntry, Product,
    RemainingClothOfClothRoll, Stage, WorkflowStage,
)
from production.services.cost_service import (
    full_costs_for_addas, material_cost_for_adda,
    material_consumption_in_period,
)
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services.roll_service import material_purchases_in_period

D = Decimal


class _CertWorld(TestCase):
    """The §B.7 scenario table as ONE world:
    R1 priced ₹100/kg 25kg (July) → A1 consumes 24kg verified (July), remnant
    2.5kg weighed back + reused by A2 (August, shared-source chain);
    R2 unpriced (July) → A2 consumes (July); R3 damaged ₹50/kg 5kg (August,
    never consumed); SWA labor + payable/non-payable priced stages on A1."""

    @classmethod
    def setUpTestData(cls):
        cls.sa = User.objects.create_user('cert-sa@test', 'x', is_superuser=True)
        cls.sa.role = Role.objects.get(code='super_admin')
        cls.sa.save()
        cls.mgr = User.objects.create_user('cert-mgr@test', 'x')
        cls.mgr.role = Role.objects.get(code='manager')
        cls.mgr.save()
        cls.worker = User.objects.create_user('cert-w@test', 'x')
        cls.worker.role = Role.objects.get(code='worker')
        cls.worker.save()
        product = Product.objects.create(code='CERT', name='Cert P')
        pay, _ = Stage.objects.get_or_create(code='cert_pay',
                                             defaults={'name': 'Cert Pay'})
        free, _ = Stage.objects.get_or_create(code='cert_free',
                                              defaults={'name': 'Cert Free'})
        cls.ws_pay = WorkflowStage.objects.create(
            product=product, stage=pay, order=1, cost_rate=D('3'),
            credits_workers=True)
        cls.ws_free = WorkflowStage.objects.create(
            product=product, stage=free, order=2, cost_rate=D('2'),
            credits_workers=False)
        ct = ClothType.objects.create(name='CERT-COTTON')
        col = ClothColor.objects.create(name='CERT-RED')
        loc = StorageLocation.objects.create(name='CERT-RACK', code='CERT')
        cls.r1 = ClothRoll.objects.create(
            roll_id='CERT-R1', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 3).date(),
            weight_kg=D('25.00'), cost_per_kg=D('100.00'))
        cls.r2 = ClothRoll.objects.create(
            roll_id='CERT-R2', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 4).date(),
            weight_kg=D('10.00'), cost_per_kg=None)
        cls.r3 = ClothRoll.objects.create(
            roll_id='CERT-R3', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 8, 1).date(),
            weight_kg=D('5.00'), cost_per_kg=D('50.00'),
            status=ClothRoll.Status.DAMAGED)

        def mk(code):
            a = Adda.objects.create(code=code, product=product)
            p = AddaStageRecord.objects.create(
                adda=a, workflow_stage=cls.ws_pay, started_at=timezone.now(),
                processing_cost=D('30.00'))
            f = AddaStageRecord.objects.create(
                adda=a, workflow_stage=cls.ws_free, started_at=timezone.now(),
                processing_cost=D('20.00'))
            return a, p, f

        cls.a1, cls.a1_pay, _ = mk('CERT-A1')
        cls.a2, cls.a2_pay, _ = mk('CERT-A2')
        july = timezone.make_aware(datetime(2026, 7, 10, 12))
        august = timezone.make_aware(datetime(2026, 8, 5, 12))
        e1 = LayeringRollEntry.objects.create(
            stage_record=cls.a1_pay, roll=cls.r1,
            weight_verified_kg=D('24.00'))
        LayeringRollEntry.objects.filter(pk=e1.pk).update(attached_at=july)
        e2 = LayeringRollEntry.objects.create(stage_record=cls.a2_pay, roll=cls.r2)
        LayeringRollEntry.objects.filter(pk=e2.pk).update(attached_at=july)
        rem = RemainingClothOfClothRoll.objects.create(
            roll=cls.r1, source_adda=cls.a1, layering_entry=e1,
            remaining_weight_kg=D('2.50'), remaining_length_meters=D('3.00'),
            is_consumed=True, consumed_in_adda=cls.a2, consumed_at=august)
        RemainingClothOfClothRoll.objects.filter(pk=rem.pk).update(created_at=august)
        StageWorkAssignment.objects.create(
            stage_record=cls.a1_pay, worker=cls.worker,
            allocated_quantity=D('10'), earning_rate_snapshot=D('3'),
            earning_amount_snapshot=D('30.00'))


class OneRupeeOnceCertification(_CertWorld):
    """Every surface shows THE same rupees; the identities hold."""

    def test_all_surfaces_agree_with_the_one_source(self):
        fc = full_costs_for_addas([self.a1.pk, self.a2.pk])
        # source truths
        self.assertEqual(fc[self.a1.pk]['material']['net'], D('2150.00'))
        self.assertEqual(fc[self.a2.pk]['material']['net'], D('250.00'))
        self.assertEqual(fc[self.a1.pk]['full_cost'], D('2200.00'))  # +30 SWA +20 np

        self.client.force_login(self.mgr)
        # SURFACE 1 — Manufacturing Costing: rows == the assembly
        costing = self.client.get(reverse('production:costing'))
        rows = {r['adda'].pk: r for r in costing.context['rows']}
        for a in (self.a1, self.a2):
            self.assertEqual(rows[a.pk]['material_net'],
                             fc[a.pk]['material']['net'])
            self.assertEqual(rows[a.pk]['full_cost'], fc[a.pk]['full_cost'])
        # SURFACE 2 — A360 (the adda detail context for management)
        detail = self.client.get(
            reverse('production:adda-detail', args=[self.a1.code]))
        a360 = detail.context.get('a360')
        self.assertIsNotNone(a360)
        self.assertEqual(a360['material_net'], fc[self.a1.pk]['material']['net'])
        self.assertEqual(a360['full_cost'], fc[self.a1.pk]['full_cost'])
        # SURFACE 3 — Material Spend: periods == the period services
        july = self.client.get(reverse('expense:material-spend') + '?month=2026-07')
        self.assertEqual(july.context['consumption'],
                         material_consumption_in_period(2026, 7))
        self.assertEqual(july.context['purchases'],
                         material_purchases_in_period(2026, 7))

    def test_the_reconciliation_identities(self):
        # Σ periods ≡ Σ Addas ≡ intake-consumed-once
        periods = (material_consumption_in_period(2026, 7)['total']
                   + material_consumption_in_period(2026, 8)['total'])
        addas = sum((material_cost_for_adda(a)['net']
                     for a in (self.a1, self.a2)), D('0'))
        self.assertEqual(periods, addas)
        self.assertEqual(periods, D('2400.00'))
        # month boundary detail: July +2400 · August net 0 (−250 rem +250 reuse)
        self.assertEqual(material_consumption_in_period(2026, 7)['total'],
                         D('2400.00'))
        self.assertEqual(material_consumption_in_period(2026, 8)['total'],
                         D('0.00'))
        # purchases: July = R1 only (R2 unpriced-counted); August = damaged R3
        july_p = material_purchases_in_period(2026, 7)
        self.assertEqual((july_p['total'], july_p['unpriced_rolls']),
                         (D('2500.0000'), 1))
        aug_p = material_purchases_in_period(2026, 8)
        self.assertEqual((aug_p['total'], aug_p['damaged_rolls']),
                         (D('250.0000'), 1))
        # damaged roll: absent from consumption everywhere
        self.assertEqual(material_consumption_in_period(2026, 8)['consumed'],
                         D('250.00'))   # only the leftover reuse, not R3
        # empty month: everything zero, nothing invented
        jan = material_consumption_in_period(2026, 1)
        self.assertEqual((jan['total'], jan['unpriced_events']), (D('0.00'), 0))


class Adr0011SeparationCertification(_CertWorld):
    """FactoryExpense ⊥ material — proven in BOTH directions."""

    def test_material_surfaces_carry_no_factory_expense_value(self):
        from expense.services.expense_service import record_expense
        record_expense(category='rent', amount=D('8888.88'),
                       expense_date=datetime(2026, 7, 5).date(), actor=self.mgr)
        self.client.force_login(self.mgr)
        for url in (reverse('expense:material-spend') + '?month=2026-07',
                    reverse('production:costing')):
            self.assertNotIn('8888.88', self.client.get(url).content.decode(), url)

    def test_factory_expense_surface_carries_no_material_value(self):
        self.client.force_login(self.mgr)
        body = self.client.get(reverse('expense:factory-expense-list')
                               + '?month=2026-07').content.decode()
        self.assertNotIn('2400.00', body)   # consumption total absent
        self.assertNotIn('2150.00', body)   # per-Adda material absent


class ReadOnlyAndPermissionCertification(_CertWorld):
    def test_every_surface_render_writes_nothing(self):
        from django.apps import apps
        self.client.force_login(self.mgr)
        urls = [reverse('production:costing'),
                reverse('expense:material-spend') + '?month=2026-07',
                reverse('production:adda-detail', args=[self.a1.code])]
        before = {m._meta.label: m.objects.count() for m in apps.get_models()}
        for u in urls:
            self.assertEqual(self.client.get(u).status_code, 200)
        after = {m._meta.label: m.objects.count() for m in apps.get_models()}
        self.assertEqual(after, before)

    def test_worker_reaches_no_material_money(self):
        self.client.force_login(self.worker)
        for name, kwargs in (('production:costing', {}),
                             ('expense:material-spend', {})):
            r = self.client.get(reverse(name, **({'args': kwargs} if False else {})))
            self.assertIn(r.status_code, (302, 403), name)
        # the worker's adda-detail render carries ZERO a360 bytes (leak law)
        r = self.client.get(reverse('production:adda-detail', args=[self.a1.code]))
        if r.status_code == 200:
            self.assertIsNone(r.context.get('a360'))
            self.assertNotIn('2150.00', r.content.decode())