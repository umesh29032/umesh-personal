"""OP-1 pins — multi-worker dimension-scoped operations (S4 consumer wiring).

The business story under test (owner spec 2026-07-05): a manager splits the
upstream piece pool by colour+size among the operation's workers; each worker
BLIND-reports good/alter/missing against their own dims (never shown pool
quantities); the manager board carries allocated/reported/verified/expected;
money still moves ONLY through the frozen good×rate settlement path.

World: two config-only COLOR_SIZE operations (dye → press) so the SPS
materialize path is exercised (cutting overrides it; base path was consumer-
less until OP-1). Cutting-sourced allocation is covered by the browser E2E.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE
from production.models import (
    Adda, ProductSize, Stage, StagePoolSnapshot, WorkerStageAllocation,
    WorkerStageTask, WorkflowStage,
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


class Op1World(TestCase):
    def setUp(self):
        from production.models import Product
        skill, _ = Skill.objects.get_or_create(
            name='op1_operator', defaults={'label': 'Op1 Operator'})
        self.s_dye = Stage.objects.create(code='op1_dye', name='Dye')
        self.s_press = Stage.objects.create(code='op1_press', name='Press')
        for s in (self.s_dye, self.s_press):
            s.access_by_skill.add(skill)

        self.product = Product.objects.create(code='OP1', name='OP1 Tee')
        self.ws1 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_dye, order=1,
            cost_rate=Decimal('5'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.ws2 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_press, order=2,
            cost_rate=Decimal('5'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.adda = Adda.objects.create(
            code='OP1-001', product=self.product,
            current_stage=self.ws1, status=Adda.Status.IN_PROGRESS)

        self.red = ClothColor.objects.create(name='OP1 Red', hex_code='#cc0000')
        self.blue = ClothColor.objects.create(name='OP1 Blue', hex_code='#0000cc')
        self.size_m = ProductSize.objects.create(
            product=self.product, code='m', label='M', display_order=1)

        self.mgr = _user('op1-mgr@test', 'super_admin')
        self.w1 = _user('op1-w1@test', skills=['op1_operator'])
        self.w2 = _user('op1-w2@test', skills=['op1_operator'])

    def _run_stage1(self, lines=None):
        """Dye produces the pool: Red/M 50 + Blue/M 50 (via the chokepoint)."""
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        from production.stages.generic_stage.service import (
            complete_generic_stage, start_generic_stage,
        )
        sr1 = start_generic_stage(adda=self.adda, stage_code='op1_dye',
                                  worker_ids=[self.w1.pk], user=self.mgr)
        task = WorkerStageTask.objects.get(stage_record=sr1, worker=self.w1)
        report_contributions(task, lines or [
            {'reported_quantity': '50', 'color_id': self.red.pk, 'size_id': self.size_m.pk},
            {'reported_quantity': '50', 'color_id': self.blue.pk, 'size_id': self.size_m.pk},
        ], actor=self.w1)
        complete_worker_task(task, actor=self.w1)
        complete_generic_stage(adda=self.adda, stage_code='op1_dye', user=self.mgr)
        return sr1

    # ── flow editor grain control ──────────────────────────────────────────
    def test_flow_editor_sets_grain_and_enforces_monotonicity(self):
        self.client.force_login(self.mgr)
        url = reverse('production:product-flow', args=[self.product.pk])
        # NONE ← the same Save that sets cost (config-over-hardcoding).
        resp = self.client.post(url, {
            'action': 'set_cost', 'workflow_stage_id': self.ws2.pk,
            'cost_method': self.ws2.cost_method, 'cost_rate': '5',
            'credits_workers': '1', 'work_split': 'none'})
        self.assertEqual(resp.status_code, 302)
        self.ws2.refresh_from_db()
        self.assertEqual(self.ws2.allocation_dimensions, 'none')
        # Re-fining downstream is refused by the service (grain monotonicity):
        # quantity(ws1) then color_size(ws2) again → violation surfaces as a message.
        self.client.post(url, {
            'action': 'set_cost', 'workflow_stage_id': self.ws1.pk,
            'cost_method': self.ws1.cost_method, 'cost_rate': '5',
            'credits_workers': '1', 'work_split': 'quantity'})
        self.ws1.refresh_from_db()
        self.assertEqual(self.ws1.allocation_dimensions, 'quantity')
        resp = self.client.post(url, {
            'action': 'set_cost', 'workflow_stage_id': self.ws2.pk,
            'cost_method': self.ws2.cost_method, 'cost_rate': '5',
            'credits_workers': '1', 'work_split': 'color_size'}, follow=True)
        self.ws2.refresh_from_db()
        self.assertEqual(self.ws2.allocation_dimensions, 'none')   # rolled back
        self.assertContains(resp, 'finer piece-pool grain')

    # ── engine seam: materialize at complete, clear at reopen ─────────────
    def test_pool_materializes_at_complete_and_clears_on_reopen(self):
        sr1 = self._run_stage1()
        rows = {(r.color_id, r.size_id): r.good
                for r in StagePoolSnapshot.objects.filter(stage_record=sr1)}
        self.assertEqual(rows, {(self.red.pk, self.size_m.pk): Decimal('50'),
                                (self.blue.pk, self.size_m.pk): Decimal('50')})
        from production.stages.generic_stage.service import reopen_generic_stage
        reopen_generic_stage(adda=self.adda, stage_code='op1_dye', user=self.mgr)
        self.assertFalse(StagePoolSnapshot.objects.filter(stage_record=sr1).exists())

    # ── allocation endpoints ───────────────────────────────────────────────
    def _start_stage2(self):
        from production.stages.generic_stage.service import start_generic_stage
        return start_generic_stage(adda=self.adda, stage_code='op1_press',
                                   worker_ids=[self.w1.pk, self.w2.pk], user=self.mgr)

    def test_allocate_and_void_endpoints(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        self.client.force_login(self.mgr)
        url = reverse('production:generic-stage-allocate',
                      kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        # AE-2 WHOLE mode (default) — takes the whole remaining bundle (50), no qty needed.
        resp = self.client.post(url, {
            'worker': self.w1.pk, 'dim_pair': f'{self.red.pk}:{self.size_m.pk}',
            'mode': 'whole'})
        self.assertEqual(resp.status_code, 302)
        wsa = WorkerStageAllocation.objects.get(stage_record=sr2)
        self.assertEqual((wsa.worker_id, wsa.allocated_quantity, wsa.allocation_mode),
                         (self.w1.pk, Decimal('50'), 'whole'))
        # PARTIAL over-allocation refused (pool now empty — only 0 available).
        resp = self.client.post(url, {
            'worker': self.w2.pk, 'dim_pair': f'{self.red.pk}:{self.size_m.pk}',
            'mode': 'partial', 'qty': '1'}, follow=True)
        self.assertContains(resp, 'only 0')
        self.assertEqual(WorkerStageAllocation.objects.filter(
            stage_record=sr2).count(), 1)
        # Void returns the quantity to the pool.
        void_url = reverse('production:generic-stage-alloc-void',
                           kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        self.client.post(void_url, {'allocation_id': wsa.pk})
        wsa.refresh_from_db()
        self.assertIsNotNone(wsa.voided_at)
        from production.services import pool_service
        self.assertEqual(pool_service.available(sr2, self.red.pk, self.size_m.pk),
                         Decimal('50'))

    def test_worker_cannot_allocate(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        self.client.force_login(self.w1)
        url = reverse('production:generic-stage-allocate',
                      kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        self.client.post(url, {'worker': self.w1.pk, 'color_id': self.red.pk,
                               'size_id': self.size_m.pk, 'qty': '10'})
        self.assertFalse(WorkerStageAllocation.objects.filter(
            stage_record=sr2).exists())

    # ── blind reporting: schema scoped to the worker's allocation ─────────
    def test_schema_scopes_choices_to_own_allocation_without_quantities(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        from production.services import pool_service
        pool_service.allocate(sr2, self.w1, qty=Decimal('50'), actor=self.mgr,
                              color_id=self.red.pk, size_id=self.size_m.pk)
        from production.stages.base import registry
        schema = registry.get('op1_press').contribution_schema(self.adda, worker=self.w1)
        by_key = {f['key']: f for f in schema['fields']}
        self.assertEqual([o['label'] for o in by_key['color_id']['options']],
                         ['OP1 Red'])          # Blue NOT offered — not his
        self.assertEqual([o['label'] for o in by_key['size_id']['options']], ['M'])
        # Blind rule: schema carries dimensions ONLY — never the allocated
        # quantity. Asserted structurally: a raw substring check
        # (assertNotIn('50', str(schema))) is order-fragile — in full-suite
        # runs the ClothColor PK itself can be 50 ('value': 50) and false-flag.
        for f in schema['fields']:
            self.assertNotIn('allocated', f)
            self.assertNotIn('value', f)        # values live only on choice OPTIONS
            for opt in f.get('options', []):
                self.assertIn(opt['value'],
                              {self.red.pk, self.size_m.pk})   # dim ids, never qty
        for line in schema.get('initial_lines', []):
            self.assertEqual(set(line), {'color_id', 'size_id'})
        # w2 has no allocation → empty options.
        schema2 = registry.get('op1_press').contribution_schema(self.adda, worker=self.w2)
        self.assertEqual({f['key']: f['options'] for f in schema2['fields']
                          if f['kind'] == 'choice'},
                         {'color_id': [], 'size_id': []})

    def test_report_view_blind_and_dims_carry_to_freeze(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        from production.services import pool_service
        pool_service.allocate(sr2, self.w1, qty=Decimal('50'), actor=self.mgr,
                              color_id=self.red.pk, size_id=self.size_m.pk)
        self.client.force_login(self.w1)
        url = reverse('production:worker-report',
                      kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        resp = self.client.get(url)
        html = resp.content.decode()
        self.assertIn('OP1 Red', html)
        self.assertNotIn('OP1 Blue', html)          # someone else's colour
        # Blind rule: no pool/allocation words or values reach the report page
        # ('50' as a bare substring would false-positive on base-CSS font weights).
        for leak in ('Available', 'llocated', 'pieces were cut', '>50<'):
            self.assertNotIn(leak, html)
        resp = self.client.post(url, {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.red.pk),
            'line-0-size_id': str(self.size_m.pk),
            'line-0-reported_quantity': '48',
            'line-0-alter_quantity': '1',
            'line-0-missing_quantity': '1'})
        task = WorkerStageTask.objects.get(stage_record=sr2, worker=self.w1)
        c = task.contributions.get()
        self.assertEqual((c.color_id, c.size_id), (self.red.pk, self.size_m.pk))
        self.assertEqual((c.good_quantity, c.alter_quantity, c.missing_quantity),
                         (Decimal('48'), Decimal('1'), Decimal('1')))
        # D2: expected froze on GOOD only (48 × ₹5) — alter/missing observe.
        self.assertEqual(c.expected_earning, Decimal('240.00'))
        self.assertEqual(task.status, WorkerStageTask.Status.COMPLETED)

    def test_over_allocation_submit_hard_refused(self):
        # AE-1 (owner ruling): over-report is HARD-refused at SUBMIT (no soft warning).
        # Draft may hold anything; submit (= complete) enforces the bound.
        self._run_stage1()
        sr2 = self._start_stage2()
        from production.services import pool_service
        pool_service.allocate(sr2, self.w1, qty=Decimal('10'), actor=self.mgr,
                              color_id=self.red.pk, size_id=self.size_m.pk)
        self.client.force_login(self.w1)
        url = reverse('production:worker-report',
                      kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        resp = self.client.post(url, {
            'action': 'submit', 'line-count': '1',
            'line-0-color_id': str(self.red.pk),
            'line-0-size_id': str(self.size_m.pk),
            'line-0-reported_quantity': '25'}, follow=True)   # 25 > 10 allocated
        self.assertContains(resp, 'allocated')   # hard refusal message
        task = WorkerStageTask.objects.get(stage_record=sr2, worker=self.w1)
        self.assertNotEqual(task.status, WorkerStageTask.Status.COMPLETED)

    # ── lenses: management board vs worker slice ───────────────────────────
    def test_panel_lenses_management_board_vs_worker_slice(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        from production.services import pool_service
        pool_service.allocate(sr2, self.w1, qty=Decimal('50'), actor=self.mgr,
                              color_id=self.red.pk, size_id=self.size_m.pk)
        panel = reverse('production:stage-panel',
                        kwargs={'code': self.adda.code, 'stage_type': 'op1_press'})
        # Manager: AE-2 bundle allocation panel + board with Allocated/Expected columns.
        self.client.force_login(self.mgr)
        html = self.client.get(panel).content.decode()
        for needle in ('Allocate bundles', 'Remaining', 'Allocated',
                       'Expected', 'op1-w2@test'):
            self.assertIn(needle, html)
        # Worker: own slice only — no colleague, no pool numbers, no allocation panel.
        self.client.force_login(self.w1)
        html = self.client.get(panel).content.decode()
        self.assertIn('Your work', html)
        self.assertIn('OP1 Red', html)               # own dims chip
        self.assertNotIn('op1-w2@test', html)        # colleague hidden
        self.assertNotIn('Allocate bundles', html)   # allocation panel hidden
        w2_panel_html = html
        self.assertNotIn('OP1 Blue', w2_panel_html)  # unallocated colour hidden

    def test_adda_detail_overview_totals_management_only(self):
        # L2: factory totals (stage tiles) are a management surface now.
        self._run_stage1()
        detail = reverse('production:adda-detail', kwargs={'code': self.adda.code})
        self.client.force_login(self.mgr)
        self.assertContains(self.client.get(detail), 'class="stages-overview"')
        self.client.force_login(self.w1)
        resp = self.client.get(detail)
        if resp.status_code == 200:   # worker may reach the page (assigned)
            # the DIV render, not the CSS/JS comments that name the feature
            self.assertNotContains(resp, 'class="stages-overview"')
            self.assertNotContains(resp, 'stage_snapshot')

    # ── decoupling stands (frozen rule: allocation ⊥ money) ───────────────
    def test_allocation_never_touches_money(self):
        self._run_stage1()
        sr2 = self._start_stage2()
        from production.services import pool_service
        wsa = pool_service.allocate(sr2, self.w1, qty=Decimal('50'),
                                    actor=self.mgr, color_id=self.red.pk,
                                    size_id=self.size_m.pk)
        money_fields = {'rate', 'earning', 'cost', 'amount', 'settlement'}
        for f in wsa._meta.get_fields():
            self.assertFalse(any(m in f.name for m in money_fields),
                             f'money-looking field on WSA: {f.name}')
