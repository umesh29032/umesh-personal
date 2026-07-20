"""OP-1 hardening pins (owner-approved fixes, 2026-07-06).

J-1  downstream pool consumes verified-else-good (verification = final truth)
C-2  report choice values must be members of the worker's schema options
H-1  verified ≤ good (never create) and ≤ allocation where one exists
H-2  allocation void refused once submitted production no longer fits
J-2  report form prefills one row per allocated colour+size pair
J-3  stage panels show Stage.name, never the url slug
H-3  worker role stripped from factory-wide sidebar rules (menu+URL together)
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE
from production.models import (
    Adda, ProductSize, Stage, StagePoolSnapshot, WorkerStageTask,
    WorkflowStage,
)
from raw_materials.models import ClothColor


def _user(email, role_code='worker', skills=()):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get_or_create(
            name=s, defaults={'label': s.replace('_', ' ').title()})[0])
    return u


class HardeningWorld(TestCase):
    """Two COLOR_SIZE ops (dye → press) — same shape as test_op1_operations."""

    def setUp(self):
        from production.models import Product
        skill, _ = Skill.objects.get_or_create(
            name='hrd_operator', defaults={'label': 'Hrd Operator'})
        self.s_dye = Stage.objects.create(code='hrd_dye', name='Dye')
        self.s_press = Stage.objects.create(code='hrd_press', name='Press Finish')
        for s in (self.s_dye, self.s_press):
            s.access_by_skill.add(skill)

        self.product = Product.objects.create(code='HRD', name='HRD Tee')
        self.ws1 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_dye, order=1,
            cost_rate=Decimal('5'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.ws2 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_press, order=2,
            cost_rate=Decimal('3'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.adda = Adda.objects.create(
            code='HRD-001', product=self.product,
            current_stage=self.ws1, status=Adda.Status.IN_PROGRESS)

        self.red = ClothColor.objects.create(name='HRD Red', hex_code='#cc0000')
        self.blue = ClothColor.objects.create(name='HRD Blue', hex_code='#0000cc')
        self.size_m = ProductSize.objects.create(
            product=self.product, code='m', label='M', display_order=1)

        self.mgr = _user('hrd-mgr@test', 'super_admin')
        self.w1 = _user('hrd-w1@test', skills=['hrd_operator'])
        self.w2 = _user('hrd-w2@test', skills=['hrd_operator'])

    # ── helpers ────────────────────────────────────────────────────────────
    def _start_dye(self, workers):
        from production.stages.generic_stage.service import start_generic_stage
        return start_generic_stage(adda=self.adda, stage_code='hrd_dye',
                                   worker_ids=[w.pk for w in workers], user=self.mgr)

    def _report(self, sr, worker, lines):
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        task = WorkerStageTask.objects.get(stage_record=sr, worker=worker)
        report_contributions(task, lines, actor=worker)
        complete_worker_task(task, actor=worker)
        return task

    def _allocate(self, sr, worker, color, size, qty):
        from production.services import pool_service
        return pool_service.allocate(
            sr, worker, qty=Decimal(qty), actor=self.mgr,
            color_id=color.pk if color else None,
            size_id=size.pk if size else None)

    # ── J-1: pool freezes verified-else-good ───────────────────────────────
    def test_materialize_pool_uses_verified_else_good(self):
        from production.services.worker_task_service import set_verified_quantity
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        task = self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk},
            {'reported_quantity': '50', 'color_id': self.blue.pk, 'size_id': self.size_m.pk},
        ])
        red_line = task.contributions.get(color_id=self.red.pk)
        set_verified_quantity(red_line, '46', actor=self.mgr)   # manager correction
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        pool = {(r.color_id, r.size_id): r.good
                for r in StagePoolSnapshot.objects.filter(stage_record=sr1)}
        self.assertEqual(pool[(self.red.pk, self.size_m.pk)], Decimal('46'))
        self.assertEqual(pool[(self.blue.pk, self.size_m.pk)], Decimal('50'))

    # ── C-2: membership at parse ───────────────────────────────────────────
    def test_forged_choice_value_refused_at_parse(self):
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk},
            {'reported_quantity': '50', 'color_id': self.blue.pk, 'size_id': self.size_m.pk},
        ])
        from production.stages.generic_stage.service import complete_generic_stage
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        # press: w2 allocated ONLY Red — a POST carrying Blue must be refused
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        self._allocate(sr2, self.w2, self.red, self.size_m, '10')
        self.client.force_login(self.w2)
        url = reverse('production:worker-report', args=[self.adda.code, 'hrd_press'])
        resp = self.client.post(url, {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.blue.pk),      # NOT allocated to w2
            'line-0-size_id': str(self.size_m.pk),
            'line-0-reported_quantity': '5',
        }, follow=True)
        self.assertContains(resp, 'not in your assigned work')
        task = WorkerStageTask.objects.get(stage_record=sr2, worker=self.w2)
        self.assertEqual(task.contributions.count(), 0)   # nothing written
        self.assertNotEqual(task.status, WorkerStageTask.Status.COMPLETED)
        # the allocated dim still submits fine
        resp = self.client.post(url, {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.red.pk),
            'line-0-size_id': str(self.size_m.pk),
            'line-0-reported_quantity': '8',
        }, follow=True)
        task.refresh_from_db()
        self.assertEqual(task.status, WorkerStageTask.Status.COMPLETED)

    # ── H-1: verification reduces or confirms, never creates ──────────────
    def test_verified_cannot_exceed_reported_good(self):
        from production.services.worker_task_service import set_verified_quantity
        sr1 = self._start_dye([self.w1])
        task = self._report(sr1, self.w1, [
            {'reported_quantity': '30', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        line = task.contributions.get()
        with self.assertRaisesMessage(ValidationError, 'never creates'):
            set_verified_quantity(line, '31', actor=self.mgr)
        set_verified_quantity(line, '28', actor=self.mgr)   # reduce OK
        line.refresh_from_db()
        self.assertEqual(line.verified_quantity, Decimal('28'))

    def test_verified_capped_by_allocation_when_one_exists(self):
        from production.services.worker_task_service import set_verified_quantity
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        self._allocate(sr2, self.w2, self.red, self.size_m, '20')
        # AE-1: over-report is now hard-blocked (reported ≤ allocated always), so the
        # allocation-cap on verify is redundant — the binding cap is verified ≤ reported
        # good. Worker reports 20; verify may only confirm/reduce, never exceed reported.
        task = self._report(sr2, self.w2, [
            {'reported_quantity': '20', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        line = task.contributions.get()
        with self.assertRaisesMessage(ValidationError, 'reported good'):
            set_verified_quantity(line, '22', actor=self.mgr)   # 22 > reported 20
        set_verified_quantity(line, '18', actor=self.mgr)
        line.refresh_from_db()
        self.assertEqual(line.verified_quantity, Decimal('18'))

    def test_verify_still_usable_on_unsplit_stage(self):
        """allocated == 0 (rollout, manager never split) → good-ceiling only."""
        from production.services.worker_task_service import set_verified_quantity
        sr1 = self._start_dye([self.w1])
        task = self._report(sr1, self.w1, [
            {'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        line = task.contributions.get()
        set_verified_quantity(line, '35', actor=self.mgr)   # no allocation → OK
        line.refresh_from_db()
        self.assertEqual(line.verified_quantity, Decimal('35'))

    # ── H-2: void refused once production no longer fits ──────────────────
    def test_void_refused_after_submitted_production(self):
        from production.services import pool_service
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        wsa = self._allocate(sr2, self.w2, self.red, self.size_m, '20')
        self._report(sr2, self.w2, [
            {'reported_quantity': '15', 'color_id': self.red.pk, 'size_id': self.size_m.pk,
             'alter_quantity': '2', 'missing_quantity': '1'}])   # produced 18
        with self.assertRaisesMessage(ValidationError, 'Cannot void'):
            pool_service.void_allocation(wsa, actor=self.mgr)
        wsa.refresh_from_db()
        self.assertIsNone(wsa.voided_at)

    def test_void_allowed_when_remaining_allocation_covers_production(self):
        from production.services import pool_service
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        first = self._allocate(sr2, self.w2, self.red, self.size_m, '20')
        second = self._allocate(sr2, self.w2, self.red, self.size_m, '25')
        self._report(sr2, self.w2, [
            {'reported_quantity': '18', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        # produced 18; void the 25-row → remaining 20 still covers 18
        pool_service.void_allocation(second, actor=self.mgr)
        second.refresh_from_db()
        self.assertIsNotNone(second.voided_at)
        # voiding the 20-row too would leave 0 < 18 → refused
        with self.assertRaisesMessage(ValidationError, 'Cannot void'):
            pool_service.void_allocation(first, actor=self.mgr)

    def test_void_before_any_report_stays_free(self):
        from production.services import pool_service
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk}])
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        wsa = self._allocate(sr2, self.w2, self.red, self.size_m, '20')
        pool_service.void_allocation(wsa, actor=self.mgr)   # no production yet
        wsa.refresh_from_db()
        self.assertIsNotNone(wsa.voided_at)

    # ── J-2: prefilled rows per allocated pair ─────────────────────────────
    def test_report_form_prefills_one_row_per_allocated_pair(self):
        from production.stages.generic_stage.service import complete_generic_stage
        sr1 = self._start_dye([self.w1])
        self._report(sr1, self.w1, [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk},
            {'reported_quantity': '50', 'color_id': self.blue.pk, 'size_id': self.size_m.pk},
        ])
        complete_generic_stage(adda=self.adda, stage_code='hrd_dye', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='hrd_press',
                                  worker_ids=[self.w2.pk], user=self.mgr)
        self._allocate(sr2, self.w2, self.red, self.size_m, '10')
        self._allocate(sr2, self.w2, self.blue, self.size_m, '15')
        self.client.force_login(self.w2)
        resp = self.client.get(
            reverse('production:worker-report', args=[self.adda.code, 'hrd_press']))
        lines = resp.context['form_lines']
        self.assertEqual(len(lines), 2)   # one per allocated pair, no draft yet
        selected = []
        for fields in lines:
            for f in fields:
                if f['key'] == 'color_id':
                    selected.append(next(o['value'] for o in f['options'] if o['selected']))
        self.assertEqual(set(selected), {self.red.pk, self.blue.pk})

    # ── J-3: panel titles use the display name ─────────────────────────────
    def test_stage_panel_shows_display_name_not_slug(self):
        self._start_dye([self.w1])
        self.client.force_login(self.mgr)
        resp = self.client.get(
            reverse('production:stage-panel', args=[self.adda.code, 'hrd_dye']))
        self.assertEqual(resp.context['stage_label'], 'Dye')
        resp = self.client.get(
            reverse('production:stage-panel', args=[self.adda.code, 'hrd_press']))
        self.assertEqual(resp.context['stage_label'], 'Press Finish')
        self.assertNotContains(resp, 'Hrd_press')

    # ── H-3: worker stripped from factory-wide sidebar rules ──────────────
    def test_worker_sidebar_lockdown(self):
        from accounts.services import can_access_url_name
        for url_name in ('raw_materials:roll-list', 'raw_materials:dashboard',
                         'production:adda-list', 'production:dashboard',
                         'tracking:dashboard'):
            self.assertFalse(can_access_url_name(self.w1, url_name), url_name)
        mgr_role_user = _user('hrd-realmgr@test', 'manager')
        self.assertTrue(can_access_url_name(mgr_role_user, 'production:adda-list'))
