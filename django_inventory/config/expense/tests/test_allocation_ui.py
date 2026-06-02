"""PR-6 tests: per-bundle-item allocation (service + view) + void."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    AddaStageRecord, CuttingBundle, CuttingBundleItem, CuttingRecord,
    Product, ProductPattern, ProductSize, WorkflowStageRoleRate,
)
from production.services import create_adda
from raw_materials.models import ClothColor
from expense.models import StageWorkAssignment
from expense.services import (
    allocate_stage_work, void_allocation, worker_balance, worker_summary,
    worker_production_stats, worker_stage_earnings, worker_adda_earnings,
)


def _manager():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='mgr@alloc.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class AllocationTests(TestCase):
    def setUp(self):
        self.mgr = _manager()
        self.worker = User.objects.create_user(email='w@alloc.test', password='x')
        self.adda = create_adda(self.mgr, product=Product.objects.get(code='NIKKAR'))
        # Build a priced cutting stage with one bundle item (direct ORM — avoids
        # driving the whole layering→cutting workflow).
        cutting_wf = self.adda.product.workflow_stages.get(stage__code='cutting')
        cutting_wf.cost_rate = Decimal('3')
        cutting_wf.save(update_fields=['cost_rate'])
        self.cutting_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=cutting_wf, started_at=timezone.now(),
        )
        cr = CuttingRecord.objects.create(stage_record=self.cutting_sr, pieces_cut=0)
        size = ProductSize.objects.create(product=self.adda.product, code='m', label='M')
        color, _ = ClothColor.objects.get_or_create(name='Red')
        pattern, _ = ProductPattern.objects.get_or_create(code='front-alloc', defaults={'name': 'Front'})
        bundle = CuttingBundle.objects.create(cutting_record=cr, size=size, total_pieces=10)
        self.item = CuttingBundleItem.objects.create(
            bundle=bundle, pattern=pattern, color=color, count=10,
        )

    def test_allocate_by_item_derives_dims_and_credits(self):
        a = allocate_stage_work(
            user=self.mgr, stage_record=self.cutting_sr, worker=self.worker,
            bundle_item=self.item, allocated_quantity=4,
        )
        self.assertEqual(a.earning_amount_snapshot, Decimal('12.00'))   # 3 × 4
        self.assertEqual(a.size_id, self.item.bundle.size_id)            # derived
        self.assertEqual(a.color_id, self.item.color_id)
        self.assertEqual(a.pattern_id, self.item.pattern_id)
        self.assertEqual(worker_balance(self.worker), Decimal('12.00'))

    def test_over_allocation_rejected(self):
        allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                            worker=self.worker, bundle_item=self.item, allocated_quantity=4)
        with self.assertRaises(ValidationError):
            allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                                worker=self.worker, bundle_item=self.item, allocated_quantity=7)  # 4+7 > 10

    def test_void_frees_quantity_and_reverses_credit(self):
        a = allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                                worker=self.worker, bundle_item=self.item, allocated_quantity=10)
        self.assertEqual(worker_balance(self.worker), Decimal('30.00'))
        void_allocation(a, user=self.mgr)
        self.assertEqual(worker_balance(self.worker), Decimal('0.00'))   # credit reversed
        # voided frees the item — can re-allocate the full count again
        allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                            worker=self.worker, bundle_item=self.item, allocated_quantity=10)
        self.assertEqual(worker_balance(self.worker), Decimal('30.00'))

    def test_void_nets_total_earnings_not_just_balance(self):
        a = allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                                worker=self.worker, bundle_item=self.item, allocated_quantity=5)
        self.assertEqual(worker_summary(self.worker)['total_earnings'], Decimal('15.00'))
        void_allocation(a, user=self.mgr)
        s = worker_summary(self.worker)
        self.assertEqual(s['total_earnings'], Decimal('0.00'))   # netted, not inflated
        self.assertEqual(s['pending_payable'], Decimal('0.00'))

    def test_role_based_rate_overrides_stage_rate(self):
        # worker's role gets a ₹5 override on the cutting stage (stage rate = ₹3)
        karigar = Role.objects.get(code='worker')
        self.worker.role = karigar
        self.worker.save(update_fields=['role'])
        cutting_wf = self.item.bundle.cutting_record.stage_record.workflow_stage
        WorkflowStageRoleRate.objects.create(
            workflow_stage=cutting_wf, role=karigar, cost_rate=Decimal('5'),
        )
        a = allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                                worker=self.worker, bundle_item=self.item, allocated_quantity=4)
        self.assertEqual(a.earning_rate_snapshot, Decimal('5.0000'))   # role rate, not 3
        self.assertEqual(a.earning_amount_snapshot, Decimal('20.00'))

    def test_worker_production_stats_and_stage_earnings(self):
        allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                            worker=self.worker, bundle_item=self.item, allocated_quantity=6)
        stats = worker_production_stats(self.worker)
        self.assertEqual(stats['pieces_produced'], Decimal('6'))
        self.assertEqual(stats['assigned_addas'], 1)
        se = worker_stage_earnings(self.worker)
        self.assertEqual(len(se), 1)
        self.assertEqual(se[0]['earned'], Decimal('18.00'))   # 3 × 6

    def test_worker_adda_earnings_breakup(self):
        allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                            worker=self.worker, bundle_item=self.item, allocated_quantity=5)
        ae = worker_adda_earnings(self.worker)
        self.assertEqual(len(ae), 1)
        a = ae[0]
        self.assertEqual(a['adda_code'], self.adda.code)
        self.assertEqual(a['total_pieces'], Decimal('5'))
        self.assertEqual(a['total_earned'], Decimal('15.00'))   # 3 × 5
        self.assertEqual(len(a['stages']), 1)
        self.assertEqual(a['stages'][0]['pieces'], Decimal('5'))

    def test_view_allocate_management_only(self):
        url = reverse('production:cutting-item-allocate', args=[self.adda.code, self.item.pk])
        # worker (no production role) blocked
        self.client.force_login(self.worker)
        self.client.post(url, {'worker_id': self.worker.pk, 'allocated_quantity': '2'})
        self.assertEqual(StageWorkAssignment.objects.filter(stage_record=self.cutting_sr).count(), 0)
        # manager allocates
        self.client.force_login(self.mgr)
        resp = self.client.post(url, {'worker_id': self.worker.pk, 'allocated_quantity': '2', 'notes': ''})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(StageWorkAssignment.objects.filter(stage_record=self.cutting_sr).count(), 1)

    def test_delete_item_with_live_allocation_refused_not_crash(self):
        """Deleting a bundle item that has a live worker allocation must raise a
        clean ValidationError, not a 500 ProtectedError (bundle_item is PROTECT)."""
        from production.services.cutting_service import delete_bundle_item
        # delete_bundle_item resolves the SR from the Adda's current stage.
        self.adda.current_stage = self.cutting_sr.workflow_stage
        self.adda.save(update_fields=['current_stage'])
        allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                            worker=self.worker, bundle_item=self.item, allocated_quantity=4)
        with self.assertRaisesMessage(ValidationError, 'audit trail is permanent'):
            delete_bundle_item(adda=self.adda, item_id=self.item.pk, user=self.mgr)
        self.assertTrue(CuttingBundleItem.objects.filter(pk=self.item.pk).exists())

    def test_delete_item_still_refused_after_void(self):
        """StageWorkAssignment is immutable (void only flags it), and bundle_item
        is PROTECT — so an item that was EVER allocated stays undeletable even
        after the allocation is voided. The pay audit trail is permanent."""
        from production.services.cutting_service import delete_bundle_item
        self.adda.current_stage = self.cutting_sr.workflow_stage
        self.adda.save(update_fields=['current_stage'])
        a = allocate_stage_work(user=self.mgr, stage_record=self.cutting_sr,
                                worker=self.worker, bundle_item=self.item, allocated_quantity=4)
        void_allocation(a, user=self.mgr)
        with self.assertRaisesMessage(ValidationError, "audit trail is permanent"):
            delete_bundle_item(adda=self.adda, item_id=self.item.pk, user=self.mgr)
        self.assertTrue(CuttingBundleItem.objects.filter(pk=self.item.pk).exists())
