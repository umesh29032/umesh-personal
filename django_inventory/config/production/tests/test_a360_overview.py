"""A360 (roadmap phase) tests — the per-Adda management overview (plan v2).

Pins: worker LEAK (zero A360 bytes for non-management) · math (expected/
settled non-overlap, variance, honest-NULL) · Stage Health (done/active/
blocked-via-the-single-stalled-predicate/waiting) · monthly ₹ suppression on
the board · per-stage-only contribution share (honest-metrics rule) ·
GENERICNESS (source inspection: no stage-name literals in the builder) ·
costing page relabel + variance · query bound.
"""
import inspect
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import WorkerProfile
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement,
)
from production.models import (
    Adda, AddaStageRecord, CostMethod, Product, Stage, WorkflowStage,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)
from production.views.a360 import build_a360


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class _Base(TestCase):
    """Two payable stages (₹5/pc + fixed ₹100); w1 piece-rate, w2 monthly."""

    def setUp(self):
        self.mgmt = _role_user('a360-mgmt@test', 'manager')
        self.w1 = _role_user('a360-w1@test', 'worker')
        self.w2 = _role_user('a360-w2@test', 'worker')
        WorkerProfile.objects.create(user=self.w2,
                                     pay_basis=WorkerProfile.PayBasis.MONTHLY)
        self.product = Product.objects.create(code='A36', name='A360 P')
        s1, _ = Stage.objects.get_or_create(code='a36_s1', defaults={'name': 'A36 One'})
        s2, _ = Stage.objects.get_or_create(code='a36_s2', defaults={'name': 'A36 Two'})
        self.ws1 = WorkflowStage.objects.create(
            product=self.product, stage=s1, order=1,
            cost_rate=Decimal('5'), credits_workers=True)
        self.ws2 = WorkflowStage.objects.create(
            product=self.product, stage=s2, order=2,
            cost_rate=Decimal('100'), cost_method=CostMethod.FIXED,
            credits_workers=True)
        self.adda = Adda.objects.create(code='A36-001', product=self.product,
                                        current_stage=self.ws1)
        self.sr1 = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws1, started_at=timezone.now())
        set_stage_workers(self.sr1, [self.w1.pk, self.w2.pk])
        for w, q in ((self.w1, '30'), (self.w2, '10')):
            t = self.sr1.worker_tasks.get(worker=w)
            report_contributions(t, [{'reported_quantity': q}], actor=w)
            complete_worker_task(t, actor=w)

    def _overview(self):
        rows = []
        for ws in self.product.workflow_stages.select_related('stage').order_by('order'):
            sr = self.adda.stage_records.filter(workflow_stage=ws).first()
            if sr and sr.completed_at:
                state = 'completed'
            elif self.adda.current_stage and self.adda.current_stage.order == ws.order:
                state = 'in_progress'
            else:
                state = 'pending'
            rows.append({'workflow_stage': ws, 'stage_type': ws.stage.code,
                         'label': ws.stage.name, 'state': state, 'sr': sr,
                         'snap': None, 'has_access': True})
        return rows


class GenericnessTests(TestCase):
    def test_builder_contains_no_stage_name_literals(self):
        """Owner requirement: future stages need ZERO A360 changes — enforced
        by source inspection (the module may never branch on a stage name)."""
        import production.views.a360 as mod
        src = inspect.getsource(mod)
        for name in ('layering', 'cutting_pattern', "'cutting'", '"cutting"',
                     'barcode_generation', 'pattern_design'):
            self.assertNotIn(name, src,
                             f"a360.py must stay stage-generic; found {name!r}")


class A360MathTests(_Base):
    def test_board_health_money_and_honest_metrics(self):
        a = build_a360(self.adda, self._overview())
        # Health: stage1 active (fresh), stage2 waiting.
        self.assertEqual([p['health'] for p in a['progress']],
                         ['active', 'waiting'])
        self.assertEqual(a['progress_pct'], 0)
        # Board: monthly ₹ suppressed, share is per-stage and honest.
        st = a['board'][0]
        by_email = {w['worker'].email: w for w in st['workers']}
        self.assertEqual(by_email['a360-w1@test']['share_pct'], 75)  # 30/40
        self.assertIsNone(by_email['a360-w2@test']['expected'])     # monthly
        self.assertTrue(by_email['a360-w2@test']['is_monthly'])
        self.assertEqual(by_email['a360-w1@test']['expected'], Decimal('150.00'))
        # Money strip: expected uncredited = w1 only (monthly excluded by the
        # funnel); nothing settled yet.
        self.assertEqual(a['expected_uncredited'], Decimal('150.00'))
        self.assertEqual(a['settled_total'], Decimal('0.00'))
        # Cost rows honest-NULL (nothing frozen yet).
        self.assertIsNone(a['cost_rows'][0]['cost'])

    def test_settle_moves_expected_to_settled_and_variance(self):
        from production.services.cost_service import freeze_stage_cost
        self.sr1.completed_at = timezone.now()
        self.sr1.save(update_fields=['completed_at'])
        freeze_stage_cost(self.sr1)
        s = create_draft(adda=self.adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        a = build_a360(self.adda, self._overview())
        self.assertEqual(a['expected_uncredited'], Decimal('0.00'))
        self.assertEqual(a['settled_total'], Decimal('150.00'))
        # std labor frozen from handler qty (base handler → None → unpriced ⇒
        # std stays 0 here) — variance = std − actual, a display subtraction.
        self.assertEqual(a['variance'], a['std_labor'] - Decimal('150.00'))
        # Worker rollup exists, quantities per-stage only (no mixed-unit total).
        self.assertNotIn('total_quantity', a['workers_rollup'][0])

    def test_blocked_health_uses_the_single_stalled_predicate(self):
        old = timezone.now() - timedelta(days=30)
        self.sr1.started_at = old
        self.sr1.save(update_fields=['started_at'])
        a = build_a360(self.adda, self._overview())
        self.assertEqual(a['progress'][0]['health'], 'blocked')


class A360ViewTests(_Base):
    URL = '/production/addas/A36-001/'

    def test_worker_leak_zero_bytes(self):
        self.client.force_login(self.w1)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        for marker in ('Adda 360', 'management overview', 'a360-strip',
                       'Variance (std'):
            self.assertNotContains(resp, marker)

    def test_management_sees_all_sections(self):
        self.client.force_login(self.mgmt)
        resp = self.client.get(self.URL)
        for marker in ('Adda 360', 'Expected (uncredited)', 'Stage timeline',
                       'with open tasks', 'Cost per stage'):
            self.assertContains(resp, marker)

    def test_query_bound(self):
        # A360 adds bounded reads to an already-heavy page. Pin CONSCIOUSLY
        # (PA-16 style): update this number only with a reviewed reason.
        self.client.force_login(self.mgmt)
        self.client.get(self.URL)                       # warm caches
        # 61 → 63 (R10-A) → 66 (R10-B) → 68 (OP-1 2026-07-05): +2 bounded reads —
        # generic contribution_schema now resolves the stage's WorkflowStage
        # (pool-grain check) once per generic stage on the page. Constant per
        # page, never per-row; re-pin CONSCIOUSLY only.
        # 68 → 65 (engineering sweep 2026-07-06, conscious): AddaDetailView now
        # select_related's product + current_stage__stage on get_object (−2) and
        # reuses the registry snapshot map instead of recomputing the layering/
        # pattern snapshots (−1).
        # 65 → 67 (P1 Block 1, conscious): +1 SIDEBAR MenuItem ('Pattern
        # Intelligence', patterns_ai) — each role-predicated menu item costs
        # its own extra_roles read per render (pre-existing pattern, now
        # surfaced by this pin; registered as a perf observation, not fixed
        # here — sidebar caching would be a frozen-code change).
        # 68 → 71 (GAP-5, conscious): +3 — preproduction_joined derive (cutting
        # ws + blocking lanes + completed lane SRs) now feeds the readiness/
        # bundling surface on every A360 render; garment_readiness itself
        # short-circuits on the single-component fixture (provider needs <2).
        # 71 → 72 (M12, conscious): +1 — the cost panel now Σs EVERY lane's
        # stage record per stage (one prefetch query) instead of reading the
        # single representative SR (the ₹280-vs-₹1408 cross-page bug).
        # 72 → 74 (M13, conscious): +2 — MATERIAL cost is now a live derive
        # on A360 (roll entries + remnants; verified kg × ₹/kg, honest-NULL
        # kept) feeding the Full-cost line + ₹/garment.
        # 74 → 75 (V1.1 item-2, conscious): +1 — reused-leftover value joins
        # the material derive (consumed_in_adda rows at source ₹/kg).
        # 75 → 76 (Phase-15 BOD-A 2026-07-18, conscious): +1 — the new
        # 'bod:dashboard' sidebar MenuItem costs one SidebarItemRule managed-
        # check per render (the inherent cost of ANY sidebar registry addition).
        # 76 → 78 (Phase-16 MEE-C 2026-07-18, conscious): +2 — the new
        # 'Recurring Expenses' MenuItem is VISIBLE to this manager, so it costs
        # its predicate's user_has_role (extra_roles M2M) query AND the
        # SidebarItemRule managed-check; the BOD item cost only +1 because its
        # SA-only predicate hides it for a manager before the rule check runs.
        # 78 → 80 (Phase-17 RMX-C 2026-07-18, conscious — spec-recorded §B.3):
        # the Decision-2 assembly extraction runs its OWN grouped SWA total +
        # non-payable ASR aggregate (the view keeps its per-SR display maps);
        # the material arm is 3-queries-for-3-loops neutral. The price of ONE
        # shared assembly across A360 + the costing surface.
        with self.assertNumQueries(80):
            self.client.get(self.URL)


class CostingPageTests(_Base):
    def test_relabel_and_variance_column(self):
        self.client.force_login(self.mgmt)
        resp = self.client.get('/production/costing/')
        # M13 (2026-07-12): variance compares LIKE with LIKE — payable std
        # vs settled; non-payable priced cost is its own honest column.
        self.assertContains(resp, 'Standard Labor (payable)')
        self.assertContains(resp, 'Non-payable priced')
        self.assertContains(resp, 'Actual Settled Labor')
        self.assertContains(resp, 'Variance (payable std')
        self.assertNotContains(resp, '>Mfg Cost<')
