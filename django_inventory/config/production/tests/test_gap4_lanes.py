"""GAP-4 (production-hardening, final ledger item): the Add-lane lifecycle
(CUTTING_STREAM_LIFECYCLE §1–§9 verbatim — sole writers
`adda_service.add_stream` / `cancel_stream` + append-only history events),
worker lane ISOLATION on the consoles (owner UI law: a worker sees only the
lanes assigned to them; a sibling lane by URL is refused; a single own lane
auto-selects with zero lane chrome), and the cancelled-lane exclusions."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, Skill
from production.models import (Adda, AddaStageRecord, CuttingStream, Product,
                               ProductSize, Stage, WorkflowStage)
from production.services.adda_service import (add_stream, cancel_stream,
                                              preproduction_joined)
from tracking.models import AddaHistory

User = get_user_model()


class _LaneWorld(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user('g4mgr@test.local', password='x',
                                            is_superuser=True)
        self.mgr.role = Role.objects.get(code='super_admin')
        self.mgr.save()
        self.worker = User.objects.create_user('g4w@test.local', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        self.worker.skills.add(Skill.objects.get(name='cutting_master'))
        self.product = Product.objects.create(code='GP4', name='Gap4')
        cutting = Stage.objects.get(code='cutting')
        self.ws_cut = WorkflowStage.objects.create(
            product=self.product, stage=cutting, order=1,
            cost_rate=Decimal('1'))
        self.adda = Adda.objects.create(code='GP4-001', product=self.product,
                                        current_stage=self.ws_cut)
        self.body = CuttingStream.objects.create(
            adda=self.adda, fabric_group='body', sequence=1, is_blocking=True)
        self.trim = CuttingStream.objects.create(
            adda=self.adda, fabric_group='trim', sequence=1,
            is_blocking=False)


class AddStreamTests(_LaneWorld):
    def test_management_only(self):
        with self.assertRaises(PermissionDenied):
            add_stream(self.adda, fabric_group='body', reason='Recut',
                       user=self.worker)

    def test_reason_mandatory(self):
        with self.assertRaisesMessage(ValidationError, 'reason is required'):
            add_stream(self.adda, fabric_group='body', reason='  ',
                       user=self.mgr)

    def test_unknown_group_refused_blueprint_law(self):
        with self.assertRaisesMessage(ValidationError, 'Blueprint change'):
            add_stream(self.adda, fabric_group='lining', reason='Recut',
                       user=self.mgr)

    def test_sequence_is_max_plus_one_even_past_cancelled(self):
        l2 = add_stream(self.adda, fabric_group='body',
                        reason='Split lay', user=self.mgr)
        self.assertEqual(l2.sequence, 2)
        cancel_stream(self.adda, stream=l2, reason='Mistake', user=self.mgr)
        l3 = add_stream(self.adda, fabric_group='body',
                        reason='Split lay again', user=self.mgr)
        self.assertEqual(l3.sequence, 3)   # never reused (§5)

    def test_blocking_inherited_from_group(self):
        lane = add_stream(self.adda, fabric_group='trim',
                          reason='New color lot', user=self.mgr)
        self.assertFalse(lane.is_blocking)   # trim group is optional-only
        lane_b = add_stream(self.adda, fabric_group='body',
                            reason='Recut', user=self.mgr)
        self.assertTrue(lane_b.is_blocking)

    def test_completed_adda_refused(self):
        self.adda.status = Adda.Status.COMPLETED
        self.adda.save(update_fields=['status'])
        with self.assertRaisesMessage(ValidationError, 'NEW Adda'):
            add_stream(self.adda, fabric_group='body', reason='Recut',
                       user=self.mgr)

    def test_history_event_written(self):
        lane = add_stream(self.adda, fabric_group='body',
                          reason='Additional production', user=self.mgr)
        ev = AddaHistory.objects.get(adda=self.adda,
                                     change_type='stream_added')
        self.assertEqual(ev.metadata['stream_id'], lane.pk)
        self.assertEqual(ev.metadata['reason'], 'Additional production')


class CancelStreamTests(_LaneWorld):
    def test_derived_seq1_never_cancellable(self):
        with self.assertRaisesMessage(ValidationError, 'derived lane'):
            cancel_stream(self.adda, stream=self.body, reason='x',
                          user=self.mgr)

    def test_started_lane_never_cancellable(self):
        l2 = add_stream(self.adda, fabric_group='body', reason='Recut',
                        user=self.mgr)
        AddaStageRecord.objects.create(adda=self.adda,
                                       workflow_stage=self.ws_cut, stream=l2,
                                       started_at=timezone.now())
        with self.assertRaisesMessage(ValidationError, 'lives'):
            cancel_stream(self.adda, stream=l2, reason='x', user=self.mgr)

    def test_cancel_writes_event_and_leaves_join(self):
        l2 = add_stream(self.adda, fabric_group='body', reason='Recut',
                        user=self.mgr)
        # blocking uncut lane holds the join …
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_cut, stream=self.body,
            started_at=timezone.now(), completed_at=timezone.now())
        self.assertFalse(preproduction_joined(self.adda))
        cancel_stream(self.adda, stream=l2, reason='Declared twice',
                      user=self.mgr)
        # … and cancelling the empty lane releases it (exclusion law)
        self.assertTrue(preproduction_joined(self.adda))
        ev = AddaHistory.objects.get(adda=self.adda,
                                     change_type='stream_cancelled')
        self.assertEqual(ev.metadata['reason'], 'Declared twice')


class WorkerLaneIsolationTests(_LaneWorld):
    """Console-level law: worker sees ONLY their lane."""

    def setUp(self):
        super().setUp()
        from production.services.worker_task_service import add_stage_worker
        self.sr_body = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_cut, stream=self.body,
            started_at=timezone.now())
        self.sr_trim = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_cut, stream=self.trim,
            started_at=timezone.now())
        add_stage_worker(self.sr_body, self.worker)   # body lane ONLY

    def test_sibling_lane_by_url_refused(self):
        self.client.force_login(self.worker)
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/cutting/workspace/'
            f'?stream={self.trim.pk}')
        self.assertEqual(resp.status_code, 403)

    def test_bare_url_auto_selects_the_workers_single_lane(self):
        self.client.force_login(self.worker)
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/cutting/workspace/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['needs_lane_choice']
                         if 'needs_lane_choice' in resp.context else False)
        self.assertEqual(resp.context['active_lane'].pk, self.body.pk)

    def test_manager_still_sees_every_lane(self):
        self.client.force_login(self.mgr)
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/cutting/workspace/'
            f'?stream={self.trim.pk}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['active_lane'].pk, self.trim.pk)
