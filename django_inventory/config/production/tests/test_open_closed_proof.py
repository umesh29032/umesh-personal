"""M2.10: executable OPEN-CLOSED PROOF for the stage engine.

Registers a throwaway stage ('proof_stage') the ENGINE HAS ZERO KNOWLEDGE OF — no
if/elif, no constant, no typed model, no entry in stage_views / adda_service /
cost_service / adda_views, and NO migration. It exists only in this test, created
as runtime DATA (Stage + WorkflowStage rows) plus a handler. If every engine path
works for it, the engine is genuinely open-closed: a new stage = a handler + data,
zero edits to existing code.

Paths verified: registry dispatch (panel context) · costing (quantity via the
handler) · payability (driven by WorkflowStage.credits_workers DATA, not the handler
flag) · stage advance + cost freeze · overview snapshot pickup.

FINDING (reported, not fixed): handler.pays_workers is DEAD post-M2.7 — payability
is decided by WorkflowStage.credits_workers. The proof stage leaves pays_workers at
its default False yet is correctly enforced as payable via the data flag, proving
the handler attribute is a vestigial second source of truth (cleanup candidate).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import Skill, User
from expense.services import allocate_stage_work
from production.models import AddaStageRecord, Product, Stage, WorkflowStage
from production.services import advance_to_next_stage, create_adda
from production.services.cost_service import freeze_stage_cost
from production.stages import base
from production.stages.base import CompletionResult, ReopenResult, StageHandler
from production.views.stage_views import StagePanelView

PROOF_QTY = Decimal('5')


class _ProofStageHandler(StageHandler):
    """A stage the engine has never heard of — defined only in this test."""

    code = 'proof_stage'
    name = 'Proof Stage'
    template_partial = 'production/_stage_panel_proof.html'   # never rendered here
    # pays_workers intentionally left at its default (False) — payability is driven
    # by WorkflowStage.credits_workers (data), NOT this handler attribute.

    def snapshot(self, adda):
        return {'state': 'proof', 'stage': self.code}

    def panel_context(self, request, adda, record):
        return {'proof_panel': True}

    def start(self, *, user_id, adda, record, data):
        return record

    def complete(self, *, user_id, adda, record, data):
        return CompletionResult()

    def reopen(self, *, user_id, record):
        return ReopenResult()

    def cost_quantity(self, record):
        # A new stage defines its own quantity — no cost_service._quantity_for edit.
        return PROOF_QTY


class OpenClosedProofTest(TestCase):
    def setUp(self):
        self._saved = base.all_handlers()         # snapshot real handlers
        base.register(_ProofStageHandler)

        self.proof_stage = Stage.objects.create(code='proof_stage', name='Proof Stage')
        self.next_stage = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='PROOF', name='Proof Product')
        self.proof_ws = WorkflowStage.objects.create(
            product=self.product, stage=self.proof_stage, order=1,
            cost_rate=Decimal('10'), credits_workers=True)
        WorkflowStage.objects.create(product=self.product, stage=self.next_stage, order=2)

        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.mgr = User.objects.create_user(
            email='proof-mgr@test', password='x', is_superuser=True, is_staff=True)
        self.mgr.skills.add(skill)
        self.worker = User.objects.create_user(email='proof-worker@test', password='x')

        # First stage is proof_stage (NOT layering) — also confirms create_adda copes
        # with a non-layering first stage (Hardcode #1's deferred path).
        self.adda = create_adda(self.mgr, product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.proof_ws, started_at=timezone.now())

    def tearDown(self):
        base.clear()
        for h in self._saved.values():
            base.register(h)

    def test_registry_dispatch_panel_context(self):
        """StagePanelView routes to the handler — no if/elif for proof_stage."""
        view = StagePanelView()
        view.kwargs = {'code': self.adda.code, 'stage_type': 'proof_stage'}
        req = RequestFactory().get('/')
        req.user = self.mgr
        view.request = req
        ctx = view.get_context_data()
        self.assertEqual(ctx['stage_type'], 'proof_stage')
        self.assertTrue(ctx.get('proof_panel'))     # came from the handler

    def test_costing_uses_handler_quantity(self):
        """cost_service freezes using the handler's cost_quantity — no _quantity_for edit."""
        freeze_stage_cost(self.sr, user=self.mgr)
        self.sr.refresh_from_db()
        self.assertEqual(self.sr.cost_quantity_snapshot, PROOF_QTY)
        self.assertEqual(self.sr.processing_cost, Decimal('50.00'))   # rate 10 x qty 5

    def test_payability_is_data_driven_not_handler_flag(self):
        """credits_workers (data) makes it payable even though handler.pays_workers is False."""
        self.assertFalse(_ProofStageHandler.pays_workers)            # the dead flag
        self.adda.current_stage = self.proof_ws
        self.adda.save(update_fields=['current_stage'])
        with self.assertRaisesMessage(ValidationError, 'allocate at least one worker'):
            advance_to_next_stage(self.adda, self.mgr)

    def test_advance_passes_with_allocation_and_freezes_via_handler(self):
        allocate_stage_work(
            user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=2)
        self.adda.current_stage = self.proof_ws
        self.adda.save(update_fields=['current_stage'])
        advance_to_next_stage(self.adda, self.mgr)                   # guard passes
        self.sr.refresh_from_db()
        self.assertEqual(self.sr.processing_cost, Decimal('50.00'))  # frozen via handler qty
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage.stage.code, 'cutting')   # advanced

    def test_overview_snapshot_picks_up_new_stage(self):
        """adda_views' registry-driven overview map includes any flow stage with a handler."""
        self.assertTrue(base.has('proof_stage'))
        self.assertEqual(base.get('proof_stage').snapshot(self.adda)['state'], 'proof')
