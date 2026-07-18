"""R10-B pins — the config-only operation archetype (frozen rule 11).

THE open-closed proof: a brand-new machine operation created as PURE
CONFIGURATION (Stage row + access skill + flow position/rate) must report,
capture good/alter/missing, complete, advance, freeze cost and pay through
the existing engine with ZERO stage-specific code.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, MachineType, Stage, StageCategory, WorkflowStage,
    WorkerStageTask,
)
from production.stages.base import registry


def _user(email, role_code='worker', skills=()):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get_or_create(
            name=s, defaults={'label': s.replace('_', ' ').title()})[0])
    return u


class GenericOperationWorld(TestCase):
    """One config-only Overlock operation on a fresh product flow."""

    def setUp(self):
        self.mt = MachineType.objects.create(code='overlock_machine',
                                             name='Overlock Machine')
        self.cat = StageCategory.objects.get(code='stitching')
        self.stage = Stage.objects.create(
            code='overlock', name='Overlock', work_type='machine',
            machine_type=self.mt, category=self.cat)
        skill, _ = Skill.objects.get_or_create(
            name='overlock_operator', defaults={'label': 'Overlock Operator'})
        self.stage.access_by_skill.add(skill)

        from production.models import Product
        self.product = Product.objects.create(code='R10B', name='R10B Tee')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1,
            cost_rate=Decimal('5'), credits_workers=True)
        self.adda = Adda.objects.create(
            code='R10B-001', product=self.product,
            current_stage=self.ws, status=Adda.Status.IN_PROGRESS)

        self.mgr = _user('r10b-mgr@test', 'super_admin')
        self.worker = _user('r10b-w@test', skills=['overlock_operator'])

    # ── registry fallback ─────────────────────────────────────────────────
    def test_registry_serves_the_archetype_without_a_package(self):
        self.assertTrue(registry.has('overlock'))
        handler = registry.get('overlock')
        from production.stages.generic_stage.handler import GenericStageHandler
        self.assertIsInstance(handler, GenericStageHandler)
        self.assertEqual(handler.name, 'Overlock')
        with self.assertRaises(KeyError):
            registry.get('no-such-stage')

    # ── full lifecycle: start → report(good/alter/missing) → complete ─────
    def test_config_only_lifecycle_end_to_end(self):
        from production.stages.generic_stage.service import (
            complete_generic_stage, start_generic_stage,
        )
        sr = start_generic_stage(adda=self.adda, stage_code='overlock',
                                 worker_ids=[self.worker.pk], user=self.mgr)
        self.assertIsNotNone(sr.started_at)
        # S2 rate snapshot froze at start
        self.assertTrue(sr.role_rates.exists())

        # Worker phone report through the ONE chokepoint — with observations.
        task = WorkerStageTask.objects.get(stage_record=sr, worker=self.worker)
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        report_contributions(task, [{
            'reported_quantity': '50', 'alter_quantity': '3',
            'missing_quantity': '1'}], actor=self.worker)
        c = task.contributions.get()
        self.assertEqual((c.good_quantity, c.alter_quantity, c.missing_quantity),
                         (Decimal('50'), Decimal('3'), Decimal('1')))
        complete_worker_task(task, actor=self.worker)
        c.refresh_from_db()
        # D2: only GOOD pays — expected = 50 × ₹5, alter/missing analytics only.
        self.assertEqual(c.expected_earning, Decimal('250.00'))

        complete_generic_stage(adda=self.adda, stage_code='overlock',
                               user=self.mgr)
        sr.refresh_from_db()
        self.adda.refresh_from_db()
        self.assertIsNotNone(sr.completed_at)
        self.assertEqual(self.adda.status, Adda.Status.COMPLETED)  # last stage
        # Standard cost froze from Σ good (5 × 50).
        self.assertEqual(sr.processing_cost, Decimal('250.00'))

    def test_worker_report_view_round_trips_alter_missing(self):
        from production.stages.generic_stage.service import start_generic_stage
        start_generic_stage(adda=self.adda, stage_code='overlock',
                            worker_ids=[self.worker.pk], user=self.mgr)
        self.client.force_login(self.worker)
        url = reverse('production:worker-report',
                      kwargs={'code': self.adda.code, 'stage_type': 'overlock'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        for label in ('Good pieces', 'Alter pieces', 'Missing / lost', 'Damaged / scrap'):
            self.assertIn(label, html)
        resp = self.client.post(url, {
            'action': 'submit', 'line-count': '1',
            'line-0-reported_quantity': '20',
            'line-0-alter_quantity': '2',
            'line-0-missing_quantity': '1'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        sr = AddaStageRecord.objects.get(adda=self.adda)
        c = sr.worker_tasks.get(worker=self.worker).contributions.get()
        self.assertEqual((c.good_quantity, c.alter_quantity, c.missing_quantity),
                         (Decimal('20'), Decimal('2'), Decimal('1')))

    def test_generic_endpoints_and_gates(self):
        # start = management only
        self.client.force_login(self.worker)
        start_url = reverse('production:generic-stage-start',
                            kwargs={'code': self.adda.code, 'stage_type': 'overlock'})
        resp = self.client.post(start_url, {'workers': [self.worker.pk]})
        # ProductionRoleMixin passes (worker role) but the service refuses.
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(AddaStageRecord.objects.filter(adda=self.adda).exists())
        # mgmt starts via the endpoint
        self.client.force_login(self.mgr)
        self.client.post(start_url, {'workers': [self.worker.pk]})
        sr = AddaStageRecord.objects.get(adda=self.adda)
        self.assertTrue(sr.is_worker_assigned(self.worker))
        # assigned worker WITH access completes via the endpoint (after report)
        task = sr.worker_tasks.get(worker=self.worker)
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        report_contributions(task, [{'reported_quantity': '5'}], actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        self.client.force_login(self.worker)
        resp = self.client.post(
            reverse('production:generic-stage-complete',
                    kwargs={'code': self.adda.code, 'stage_type': 'overlock'}),
            {'embedded': '1'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('stage-advanced', resp['Location'])   # F-3 bounce
        sr.refresh_from_db()
        self.assertIsNotNone(sr.completed_at)

    def test_panel_renders_machine_section(self):
        from production.stages.generic_stage.service import start_generic_stage
        start_generic_stage(adda=self.adda, stage_code='overlock',
                            worker_ids=[self.worker.pk], user=self.mgr)
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('production:stage-panel', kwargs={
            'code': self.adda.code, 'stage_type': 'overlock'}) + '?embedded=1')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('Overlock Machine', html)      # machine section
        self.assertIn('Good', html)                  # output board


class CategoryPresentationTests(TestCase):
    def test_grouping_preserves_flow_order_and_degenerate_flat(self):
        from production.views.presentation import grouped_or_flat
        pre = StageCategory.objects.get(code='pre_production')
        stitch = StageCategory.objects.get(code='stitching')

        class S:      # stage stub
            def __init__(self, cat): self.category = cat
        class E:      # overview-entry stub
            def __init__(self, cat): self.stage = S(cat)

        groups, grouped = grouped_or_flat(
            [E(pre), E(pre), E(stitch), E(stitch), E(stitch)],
            stage_of=lambda e: e.stage)
        self.assertTrue(grouped)
        self.assertEqual([g['label'] for g in groups],
                         ['Pre Production', 'Stitching'])
        self.assertEqual([len(g['items']) for g in groups], [2, 3])
        # single category → flat (no header noise — the owner's rule)
        _, grouped = grouped_or_flat([E(pre), E(pre)], stage_of=lambda e: e.stage)
        self.assertFalse(grouped)


class GenericReopenTests(GenericOperationWorld):
    """M6-campaign regression (2026-07-11): reopen_generic_stage lacked
    @transaction.atomic — the shared skeleton's select_for_update raised
    TransactionManagementError (HTTP 500) on the FIRST live generic-stage
    reopen. Siblings (cutting/barcode/pattern) were already atomic."""

    def test_reopen_generic_stage_works_and_refloats(self):
        from production.stages.generic_stage.service import (
            complete_generic_stage, reopen_generic_stage, start_generic_stage,
        )
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        sr = start_generic_stage(adda=self.adda, stage_code='overlock',
                                 worker_ids=[self.worker.pk], user=self.mgr)
        task = WorkerStageTask.objects.get(stage_record=sr,
                                           worker=self.worker)
        report_contributions(task, [{'reported_quantity': '10'}],
                             actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        complete_generic_stage(adda=self.adda, stage_code='overlock',
                               user=self.mgr)
        sr.refresh_from_db()
        self.assertIsNotNone(sr.completed_at)

        reopened = reopen_generic_stage(adda=self.adda,
                                        stage_code='overlock', user=self.mgr)
        self.assertEqual(reopened.pk, sr.pk)
        reopened.refresh_from_db()
        self.assertIsNone(reopened.completed_at)      # unlocked
        self.assertIsNone(reopened.cost_frozen_at)    # cost re-floated

    def test_reopen_generic_stage_via_view(self):
        # the exact 500 path: POST the reopen endpoint end-to-end
        from production.stages.generic_stage.service import (
            complete_generic_stage, start_generic_stage,
        )
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        sr = start_generic_stage(adda=self.adda, stage_code='overlock',
                                 worker_ids=[self.worker.pk], user=self.mgr)
        task = WorkerStageTask.objects.get(stage_record=sr,
                                           worker=self.worker)
        report_contributions(task, [{'reported_quantity': '5'}],
                             actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        complete_generic_stage(adda=self.adda, stage_code='overlock',
                               user=self.mgr)
        self.client.force_login(self.mgr)
        url = reverse('production:generic-stage-reopen', kwargs={
            'code': self.adda.code, 'stage_type': 'overlock'})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)       # not 500
        sr.refresh_from_db()
        self.assertIsNone(sr.completed_at)
