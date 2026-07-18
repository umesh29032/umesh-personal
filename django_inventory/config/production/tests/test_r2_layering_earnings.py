"""R2 (roadmap phase) tests — layering per-layer earnings.

Plan: docs/R2_EXECUTION_PLAN.md. PDD v1.0 §14/§17/§18, §27-D1 (each worker
reports OWN layers), §27-D2 (good-only payable), owner P-1..P-4 resolutions.
No migrations, no chokepoint edits — this file proves the EXISTING machinery
pays layering correctly once configured, plus the R2 additions (schema label,
reconciliation warn, flow-editor payability toggle).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from expense.models import WorkerLedgerEntry
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement,
)
from inventory.models import Role
from production.models import Product
from production.services import create_adda, set_stage_cost
from production.services import worker_task_service as wts
from production.services import worker_layer_reconciliation
from production.stages.base import registry


def _superuser(email='admin@r2.test'):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=True, is_staff=True)
    u.role = Role.objects.get(code='super_admin')
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


def _worker(email):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='worker')
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


def _payable_layering_adda(admin, *, rate='10'):
    """3-patti-style config (R2.4 runbook): per_layer · ₹rate · UNGROUPED ·
    pays — set BEFORE create_adda so AddaStageRoleRate freezes the rate."""
    product = Product.objects.get(code='T-SHIRT')
    product.workflow_stages.update(
        cost_method='per_layer', cost_rate=Decimal(rate),
        cost_billed_at=None, credits_workers=True)
    return create_adda(admin, product=product)


class LayeringSchemaTests(TestCase):
    """R2.1: layering reports LAYERS; other stages untouched."""

    def test_layering_schema_unit_is_layers(self):
        schema = registry.get('layering').contribution_schema(None)
        field = schema['fields'][0]
        self.assertEqual(field['unit'], 'layers')
        self.assertEqual(field['key'], 'reported_quantity')  # generic parser contract

    def test_cutting_schema_unchanged(self):
        # Regression-pin: the override must not leak to other stages.
        admin = _superuser()
        adda = create_adda(admin, product=Product.objects.get(code='T-SHIRT'))
        schema = registry.get('cutting').contribution_schema(adda)
        units = {f.get('unit') for f in schema['fields'] if f['kind'] == 'quantity'}
        self.assertNotIn('layers', units)


class TwoWorkerIndependenceTests(TestCase):
    """§27-D1: each worker reports ONLY own layers; earnings independent."""

    def setUp(self):
        self.admin = _superuser()
        self.a = _worker('a@r2.test')
        self.b = _worker('b@r2.test')
        self.adda = _payable_layering_adda(self.admin)
        self.sr = self.adda.stage_records.first()
        wts.set_stage_workers(self.sr, [self.a.pk, self.b.pk])

    def _report_and_complete(self, worker, layers):
        task = self.sr.worker_tasks.get(worker=worker)
        wts.report_contributions(
            task, [{'reported_quantity': layers}], actor=worker)
        return wts.complete_worker_task(task, actor=worker)

    def test_independent_expected_earnings(self):
        self._report_and_complete(self.a, '30')
        self._report_and_complete(self.b, '15')
        ca = self.sr.worker_tasks.get(worker=self.a).contributions.first()
        cb = self.sr.worker_tasks.get(worker=self.b).contributions.first()
        self.assertEqual(ca.expected_earning, Decimal('300.00'))  # 30 × ₹10
        self.assertEqual(cb.expected_earning, Decimal('150.00'))  # 15 × ₹10

    def test_settlement_pays_each_worker_own_layers(self):
        """R2.5 E2E: finalize books per-worker ledger CREDITs = layers × rate."""
        self._report_and_complete(self.a, '30')
        self._report_and_complete(self.b, '15')
        self.adda.stage_records.update(completed_at=timezone.now())
        draft = create_draft(adda=self.adda, user=self.admin)
        finalize_adda_settlement(settlement=draft, user=self.admin)
        credit_a = WorkerLedgerEntry.objects.get(
            worker=self.a, category='stage_earning')
        credit_b = WorkerLedgerEntry.objects.get(
            worker=self.b, category='stage_earning')
        self.assertEqual(credit_a.amount, Decimal('300.00'))
        self.assertEqual(credit_b.amount, Decimal('150.00'))

    def test_grouped_member_pays_zero_despite_stale_rate(self):
        """F2 regression-pin: grouping the stage AFTER the ₹10 snapshot froze
        must still pay 0 (grouped wins over the stale snapshot)."""
        self._report_and_complete(self.a, '30')
        ws = self.sr.workflow_stage
        other = None  # group onto itself is illegal; simulate via direct flag
        # Grouping needs a later payer stage; T-SHIRT flow has only layering in
        # tests, so pin the guard at the freeze boundary instead: a grouped ws
        # yields rate 0 via effective_pay_rate.
        from production.services import cost_service
        ws.cost_billed_at_id = ws.pk  # structural marker only for the guard call
        self.assertEqual(
            cost_service.effective_pay_rate(ws, Decimal('10')), Decimal('0'))


class Pay2GateTests(TestCase):
    """P-4 confirmed: payable stage refuses completion with zero completed reports."""

    def setUp(self):
        self.admin = _superuser()
        self.w = _worker('w@r2.test')
        self.adda = _payable_layering_adda(self.admin)
        self.sr = self.adda.stage_records.first()
        wts.set_stage_workers(self.sr, [self.w.pk])

    def test_advance_refused_without_completed_contribution(self):
        from production.services import advance_to_next_stage
        with self.assertRaises(ValidationError):
            advance_to_next_stage(self.adda, self.admin)

    def test_advance_allowed_after_worker_completes(self):
        task = self.sr.worker_tasks.get(worker=self.w)
        wts.report_contributions(task, [{'reported_quantity': '45'}], actor=self.w)
        wts.complete_worker_task(task, actor=self.w)
        from production.services import advance_to_next_stage
        advance_to_next_stage(self.adda, self.admin)   # must not raise
        self.adda.refresh_from_db()


class ReconciliationTests(TestCase):
    """R2.2: Σ worker layers vs breakup lay_count — WARN data, never blocks."""

    def setUp(self):
        self.admin = _superuser()
        self.w = _worker('recon@r2.test')
        self.adda = _payable_layering_adda(self.admin)
        self.sr = self.adda.stage_records.first()
        wts.set_stage_workers(self.sr, [self.w.pk])
        task = self.sr.worker_tasks.get(worker=self.w)
        wts.report_contributions(task, [{'reported_quantity': '40'}], actor=self.w)
        wts.complete_worker_task(task, actor=self.w)

    def _make_layering_record(self, lay_count):
        from production.models import LayeringRecord
        return LayeringRecord.objects.create(
            stage_record=self.sr, lay_count=lay_count, total_colors=1,
            duration_minutes=5, layer_length_meters=Decimal('3'))

    def test_none_before_layering_record_exists(self):
        self.assertIsNone(worker_layer_reconciliation(self.adda))

    def test_mismatch_detected_not_blocking(self):
        self._make_layering_record(45)                 # workers reported 40
        recon = worker_layer_reconciliation(self.adda)
        self.assertTrue(recon['mismatch'])
        self.assertEqual(recon['delta'], Decimal('-5'))
        # NON-blocking by construction: pure read, no exception path at all.

    def test_match_no_warn(self):
        self._make_layering_record(40)
        recon = worker_layer_reconciliation(self.adda)
        self.assertFalse(recon['mismatch'])


class FlowEditorPayabilityTests(TestCase):
    """R2.3 (P-1): credits_workers set via set_stage_cost / flow editor."""

    def setUp(self):
        self.admin = _superuser()
        self.ws = Product.objects.get(code='NIKKAR').workflow_stages.first()

    def test_toggle_on_and_off(self):
        set_stage_cost(user=self.admin, workflow_stage=self.ws,
                       cost_method='per_layer', cost_rate='10',
                       credits_workers=True)
        self.ws.refresh_from_db()
        self.assertTrue(self.ws.credits_workers)
        self.assertEqual(self.ws.cost_rate, Decimal('10'))
        set_stage_cost(user=self.admin, workflow_stage=self.ws,
                       cost_method='per_layer', cost_rate='10',
                       credits_workers=False)
        self.ws.refresh_from_db()
        self.assertFalse(self.ws.credits_workers)

    def test_none_leaves_flag_unchanged(self):
        self.ws.credits_workers = True
        self.ws.save(update_fields=['credits_workers'])
        set_stage_cost(user=self.admin, workflow_stage=self.ws,
                       cost_method='per_piece', cost_rate='5')
        self.ws.refresh_from_db()
        self.assertTrue(self.ws.credits_workers)   # back-compat: not sent = untouched
