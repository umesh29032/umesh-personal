"""RMX-D (Phase 17) — the surfaces: the Material Spend window + the costing
page's Model-B completion. Identity matrices (the D2 PERMANENT rule proven),
the 4-layer roll-wall re-proof (owner order), content == the certified RMX-C
services, honest-NULL banners, empty states, and read-only purity."""

from datetime import datetime
from decimal import Decimal

from django.apps import apps
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import Adda, AddaStageRecord, LayeringRollEntry, Product, Stage, WorkflowStage
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation

D = Decimal


def _user(email, code, super_=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=super_)
    u.role = Role.objects.get(code=code)
    u.save()
    return u


class _World(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sa = _user('rmxd-sa@test', 'super_admin', super_=True)
        cls.mgr = _user('rmxd-mgr@test', 'manager')
        cls.worker = _user('rmxd-w@test', 'worker')
        cls.acct = _user('rmxd-acct@test', 'accountant')
        cls.listing = _user('rmxd-list@test', 'listing_team')
        ct = ClothType.objects.create(name='RMXD-COTTON')
        col = ClothColor.objects.create(name='RMXD-RED')
        loc = StorageLocation.objects.create(name='RMXD-RACK', code='RMXD')
        cls.priced = ClothRoll.objects.create(
            roll_id='RMXD-R1', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 3).date(),
            weight_kg=D('10.00'), cost_per_kg=D('100.00'),
            supplier='RMXD Supplier')
        cls.unpriced = ClothRoll.objects.create(
            roll_id='RMXD-R2', cloth_type=ct, cloth_color=col,
            storage_location=loc, purchased_date=datetime(2026, 7, 4).date(),
            weight_kg=D('5.00'), cost_per_kg=None)
        product = Product.objects.create(code='RMXD', name='RMXD P')
        stage, _ = Stage.objects.get_or_create(code='rmxd_s',
                                               defaults={'name': 'RMXD S'})
        ws = WorkflowStage.objects.create(product=product, stage=stage,
                                          order=1, cost_rate=D('3'),
                                          credits_workers=True)
        cls.adda = Adda.objects.create(code='RMXD-A1', product=product)
        sr = AddaStageRecord.objects.create(adda=cls.adda, workflow_stage=ws,
                                            started_at=timezone.now())
        e = LayeringRollEntry.objects.create(stage_record=sr, roll=cls.priced)
        LayeringRollEntry.objects.filter(pk=e.pk).update(
            attached_at=timezone.make_aware(datetime(2026, 7, 10, 12)))
        e2 = LayeringRollEntry.objects.create(stage_record=sr, roll=cls.unpriced)
        LayeringRollEntry.objects.filter(pk=e2.pk).update(
            attached_at=timezone.make_aware(datetime(2026, 7, 11, 12)))

    URL = None

    def _get(self, user, url):
        if user:
            self.client.force_login(user)
        r = self.client.get(url)
        self.client.logout()
        return r


class MaterialSpendMatrixTests(_World):
    def test_identity_matrix_d2_permanent_rule(self):
        url = reverse('expense:material-spend')
        self.assertEqual(self._get(None, url).status_code, 302)       # anon
        for u in (self.worker, self.acct, self.listing):
            self.assertIn(self._get(u, url).status_code, (302, 403), u.email)
        for u in (self.mgr, self.sa):                                 # D2: mgmt OK
            self.assertEqual(self._get(u, url).status_code, 200, u.email)

    def test_post_is_405_read_only_by_shape(self):
        self.client.force_login(self.sa)
        self.assertEqual(self.client.post(
            reverse('expense:material-spend'), {}).status_code, 405)

    def test_content_equals_the_certified_services(self):
        from production.services.cost_service import material_consumption_in_period
        from raw_materials.services.roll_service import material_purchases_in_period
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('expense:material-spend') + '?month=2026-07')
        self.assertEqual(r.context['consumption'],
                         material_consumption_in_period(2026, 7))
        self.assertEqual(r.context['purchases'],
                         material_purchases_in_period(2026, 7))
        body = r.content.decode()
        self.assertIn('₹1000.00', body)          # consumed 10kg × ₹100
        self.assertIn('material costing is incomplete', body)   # honest-NULL
        self.assertIn('purchased without a price', body)

    def test_empty_month_states(self):
        self.client.force_login(self.mgr)
        body = self.client.get(reverse('expense:material-spend')
                               + '?month=2026-01').content.decode()
        self.assertIn('No production consumption recorded for 2026-01', body)
        self.assertIn('No purchases recorded for 2026-01', body)

    def test_no_factory_expense_number_on_the_page(self):
        # ADR-0011: material and factory money never blend — the page carries
        # a sibling LINK, not a FactoryExpense value.
        from expense.services.expense_service import record_expense
        record_expense(category='rent', amount=D('7777.77'),
                       expense_date=datetime(2026, 7, 5).date(), actor=self.mgr)
        self.client.force_login(self.mgr)
        body = self.client.get(reverse('expense:material-spend')
                               + '?month=2026-07').content.decode()
        self.assertNotIn('7777.77', body)
        self.assertIn('Factory expenses', body)   # the sibling link

    def test_page_renders_write_nothing(self):
        before = {m._meta.label: m.objects.count() for m in apps.get_models()}
        self.client.force_login(self.mgr)
        self.client.get(reverse('expense:material-spend') + '?month=2026-07')
        after = {m._meta.label: m.objects.count() for m in apps.get_models()}
        # force_login writes a session row — the ONLY sanctioned delta.
        for state in (before, after):
            for key in [k for k in state if k.lower() == 'sessions.session']:
                state.pop(key)
        self.assertEqual(after, before)


class CostingPageCompletionTests(_World):
    def test_columns_come_from_the_certified_assembly(self):
        from production.services.cost_service import full_costs_for_addas
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('production:costing'))
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.context['rows'] if x['adda'].pk == self.adda.pk)
        fc = full_costs_for_addas([self.adda.pk])[self.adda.pk]
        self.assertEqual(row['material_net'], fc['material']['net'])
        self.assertEqual(row['full_cost'], fc['full_cost'])
        self.assertEqual(row['material_unpriced_rolls'],
                         fc['material']['unpriced_rolls'])
        body = r.content.decode()
        self.assertIn('Full Cost (ADR-0009)', body)
        self.assertIn('Material (net)', body)
        self.assertIn('Full cost (ADR-0009, shown Addas)', body)   # grand tile

    def test_costing_identity_matrix(self):
        url = reverse('production:costing')
        self.assertEqual(self._get(None, url).status_code, 302)
        for u in (self.worker, self.acct, self.listing):
            self.assertIn(self._get(u, url).status_code, (302, 403), u.email)
        for u in (self.mgr, self.sa):
            self.assertEqual(self._get(u, url).status_code, 200)


class FourLayerWallReProofTests(_World):
    """The D2 order: per-roll pricing stays protected while aggregates open."""

    def test_manager_sees_aggregates_but_never_per_roll_price(self):
        self.client.force_login(self.mgr)
        spend = self.client.get(reverse('expense:material-spend')
                                + '?month=2026-07').content.decode()
        self.assertIn('₹1000.00', spend)                     # aggregate visible
        detail = self.client.get(
            reverse('raw_materials:roll-detail', args=[self.priced.pk])
        ).content.decode()
        self.assertNotIn('100.00', detail)                   # per-roll ₹ hidden
        self.assertNotIn('RMXD Supplier', detail)            # supplier hidden
        self.assertNotIn('Cost', detail.split('Manufacturing')[0]
                         if 'Manufacturing' in detail else detail)

    def test_sa_still_sees_per_roll_financials(self):
        self.client.force_login(self.sa)
        detail = self.client.get(
            reverse('raw_materials:roll-detail', args=[self.priced.pk])
        ).content.decode()
        self.assertIn('100.00', detail)
        self.assertIn('RMXD Supplier', detail)

    def test_service_layer_gate_intact(self):
        # Layer 2 of the wall: a non-financial user submitting financials.
        from raw_materials.services import roll_service
        from django.core.exceptions import PermissionDenied, ValidationError
        with self.assertRaises((PermissionDenied, ValidationError)):
            roll_service.update_roll_details(self.mgr, roll=self.priced,
                                             supplier='sneaky',
                                             cost_per_kg=D('1'))