"""P19A regression tests (2026-07-20) — the two release-blocking runtime bugs.

C-1: `start_layering` lost its @transaction.atomic to an inserted helper
     (decorator-hijack) → select_for_update in set_stage_workers raised
     TransactionManagementError on every roster-update POST. TestCase wraps
     each test in a transaction and can NEVER see this class, so the C-1 test
     runs under TransactionTestCase with a real request — the H-2 tier.

C-2: WorkerReportView resolved the stage record with a single-row .get();
     pre-production stages carry one SR per LANE (streams redesign), so any
     multi-lane Adda 500'd with MultipleObjectsReturned before the permission
     check, for every role.

Both tests are fully self-contained (own product/stage/skill/users) — no
migration-seed reliance, safe under TransactionTestCase's flush.
"""
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Skill, User
from production.models import (
    AddaStageRecord, Product, Stage, WorkerStageTask, WorkflowStage,
)
from production.services import create_adda
from production.services.adda_service import add_stream, resolve_stream


def _mk_world(tag):
    """Product with a layering flow + super-admin + skilled worker."""
    layering = Stage.objects.get_or_create(
        code='layering', defaults={'name': 'Layering'})[0]
    skill = Skill.objects.get_or_create(
        name='cutting_master', defaults={'label': 'Cutting Master'})[0]
    layering.access_by_skill.add(skill)
    product = Product.objects.create(code=f'P19A-{tag}', name=f'P19A {tag}')
    WorkflowStage.objects.create(product=product, stage=layering, order=1)
    admin = User.objects.create_user(
        email=f'p19a-admin-{tag}@test', password='x',
        is_superuser=True, is_staff=True)
    worker = User.objects.create_user(email=f'p19a-worker-{tag}@test', password='x')
    worker.skills.add(skill)
    return product, admin, worker


class LayeringStartTransactionTest(TransactionTestCase):
    """C-1: the roster-update POST must succeed in a REAL (autocommit) request."""

    def test_layering_start_post_assigns_workers(self):
        product, admin, worker = _mk_world('C1')
        adda = create_adda(admin, product=product)

        self.client.force_login(admin)
        resp = self.client.post(
            f'/production/addas/{adda.code}/layering/start/',
            {'workers': [worker.pk]})
        # Pre-fix: TransactionManagementError → 500. Post-fix: redirect.
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            WorkerStageTask.objects.filter(
                stage_record__adda=adda, worker=worker)
            .exclude(status=WorkerStageTask.Status.CANCELLED).exists())

        # Roster UPDATE (the owner's exact repro: "when i try to update the
        # workers") — re-POST must also succeed and stay idempotent.
        resp = self.client.post(
            f'/production/addas/{adda.code}/layering/start/',
            {'workers': [worker.pk]})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            WorkerStageTask.objects.filter(
                stage_record__adda=adda, worker=worker)
            .exclude(status=WorkerStageTask.Status.CANCELLED).count(), 1)


class MultiLaneWorkerReportTest(TestCase):
    """C-2: report page resolves lane-aware — never MultipleObjectsReturned."""

    @classmethod
    def setUpTestData(cls):
        cls.product, cls.admin, cls.worker = _mk_world('C2')
        cls.outsider = User.objects.create_user(
            email='p19a-outsider-C2@test', password='x')
        cls.adda = create_adda(cls.admin, product=cls.product)
        lane1 = resolve_stream(cls.adda, None)
        lane2 = add_stream(cls.adda, fabric_group=lane1.fabric_group,
                           reason='p19a test lane', user=cls.admin)
        ws = cls.adda.product.workflow_stages.get(stage__code='layering')
        # Two SRs for the SAME (adda, stage) — the shape that used to 500.
        sr1 = AddaStageRecord.objects.filter(
            adda=cls.adda, workflow_stage=ws).first()
        sr1.stream = lane1
        sr1.save(update_fields=['stream'])
        cls.sr2 = AddaStageRecord.objects.create(
            adda=cls.adda, workflow_stage=ws, stream=lane2)
        cls.task = WorkerStageTask.objects.create(
            stage_record=cls.sr2, worker=cls.worker,
            status=WorkerStageTask.Status.ASSIGNED)
        cls.url = f'/production/addas/{cls.adda.code}/report/layering/'

    def test_assigned_worker_gets_form_on_own_lane(self):
        self.client.force_login(self.worker)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['stage_record'].pk, self.sr2.pk)

    def test_stream_param_narrows_and_stays_isolated(self):
        self.client.force_login(self.worker)
        resp = self.client.get(f'{self.url}?stream={self.sr2.stream_id}')
        self.assertEqual(resp.status_code, 200)
        other = AddaStageRecord.objects.filter(
            adda=self.adda).exclude(pk=self.sr2.pk).first()
        resp = self.client.get(f'{self.url}?stream={other.stream_id}')
        self.assertEqual(resp.status_code, 403)   # no task on that lane

    def test_unassigned_worker_403_not_500(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_management_without_task_403_not_500(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_never_started_stage_is_404(self):
        self.client.force_login(self.worker)
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/report/cutting/')
        self.assertEqual(resp.status_code, 404)


class MultiLanePatternStartTest(TestCase):
    """AUDIT-2 P0-1: Pattern Design must be startable on a MULTI-LANE Adda.

    Pattern Design is part of the per-lane trio (Layering · Pattern Design ·
    Cutting), so its panel owes the same lane contract layering/cutting have:
    GAP-3 (bare multi-lane URL -> lane picker) + a `stream` on every form.
    Pre-fix the panel published no lane context, its forms carried no `stream`,
    and pattern-start silently no-op'd -> zero AddaStageRecord, flow dead at
    stage 2 on every multi-fabric product (e.g. a real T-shirt = body+rib+trim).
    """

    @classmethod
    def setUpTestData(cls):
        layering = Stage.objects.get_or_create(
            code='layering', defaults={'name': 'Layering'})[0]
        pattern = Stage.objects.get_or_create(
            code='cutting_pattern', defaults={'name': 'Pattern Design'})[0]
        skill = Skill.objects.get_or_create(
            name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        layering.access_by_skill.add(skill)
        pattern.access_by_skill.add(skill)
        cls.product = Product.objects.create(code='P0A2', name='P0 audit2')
        WorkflowStage.objects.create(
            product=cls.product, stage=layering, order=1)
        WorkflowStage.objects.create(
            product=cls.product, stage=pattern, order=2, cost_method='fixed_cost',
            cost_rate=500, credits_workers=True)
        cls.admin = User.objects.create_user(
            email='p0a2-admin@test', password='x',
            is_superuser=True, is_staff=True)
        cls.worker = User.objects.create_user(
            email='p0a2-worker@test', password='x')
        cls.worker.skills.add(skill)
        cls.adda = create_adda(cls.admin, product=cls.product)
        # Make it genuinely multi-lane, the shape that used to be unstartable.
        lane1 = resolve_stream(cls.adda, None)
        # Same fabric group — a NEW group would be a Blueprint change, which
        # add_stream correctly refuses (lifecycle §6).
        cls.lane2 = add_stream(cls.adda, fabric_group=lane1.fabric_group,
                               reason='p0 audit2 second lane', user=cls.admin)
        cls.lane1 = lane1
        # Pattern work on a lane opens only once THAT lane's layering is done
        # (a real per-lane sequencing gate) — satisfy it so the test exercises
        # the lane contract, not the gate.
        lay = AddaStageRecord.objects.filter(
            adda=cls.adda, workflow_stage__stage__code='layering').first()
        lay.stream = lane1
        lay.completed_at = timezone.now()
        lay.save(update_fields=['stream', 'completed_at'])
        AddaStageRecord.objects.create(
            adda=cls.adda, workflow_stage=lay.workflow_stage,
            stream=cls.lane2, completed_at=timezone.now())
        cls.panel = (f'/production/addas/{cls.adda.code}'
                     f'/stage/cutting_pattern/')

    def test_bare_multi_lane_panel_offers_a_lane_choice(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.panel)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['needs_lane_choice'])
        self.assertGreater(len(resp.context['lanes']), 1)

    def test_lane_scoped_panel_publishes_the_active_lane(self):
        self.client.force_login(self.admin)
        resp = self.client.get(f'{self.panel}?stream={self.lane1.pk}')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['needs_lane_choice'])
        self.assertEqual(resp.context['active_lane'].pk, self.lane1.pk)
        # The lane must reach the rendered forms, or the POST no-ops again.
        self.assertContains(resp, "h.name = 'stream'")
        self.assertContains(resp, f"h.value = '{self.lane1.pk}'")

    def test_pattern_start_creates_the_stage_record_on_that_lane(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            f'/production/addas/{self.adda.code}/pattern/start/',
            {'workers': [self.worker.pk], 'stream': self.lane1.pk})
        self.assertEqual(resp.status_code, 302)
        srs = AddaStageRecord.objects.filter(
            adda=self.adda, workflow_stage__stage__code='cutting_pattern')
        self.assertEqual(srs.count(), 1)            # pre-fix: 0
        self.assertEqual(srs.first().stream_id, self.lane1.pk)
        self.assertTrue(
            WorkerStageTask.objects.filter(
                stage_record=srs.first(), worker=self.worker)
            .exclude(status=WorkerStageTask.Status.CANCELLED).exists())

    def test_each_lane_gets_its_own_pattern_record(self):
        self.client.force_login(self.admin)
        for lane in (self.lane1, self.lane2):
            self.client.post(
                f'/production/addas/{self.adda.code}/pattern/start/',
                {'workers': [self.worker.pk], 'stream': lane.pk})
        streams = set(
            AddaStageRecord.objects
            .filter(adda=self.adda,
                    workflow_stage__stage__code='cutting_pattern')
            .values_list('stream_id', flat=True))
        self.assertEqual(streams, {self.lane1.pk, self.lane2.pk})
