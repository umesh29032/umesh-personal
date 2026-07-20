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
