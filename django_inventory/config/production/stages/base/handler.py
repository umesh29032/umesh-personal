"""StageHandler contract + completion result types (M2 stage engine).

A StageHandler is the per-stage strategy the registry dispatches to, replacing the
scattered `if stage_type == '...'` branches. Handlers are PURE of money and
cross-app concerns: complete() returns a CompletionResult describing the work
done; the base StageService (added when the first stage migrates in M2.2) owns the
single side-effecting sequence — freeze cost, book worker earnings via the expense
facade, advance the Adda, log history.

R1 decision (locked here): confining the production->expense edge to the base
service (ONE file) is what keeps the cycle from re-forming. Individual handlers
never import expense — they hand the base service primitives (WorkerAllocation)
and the base books them. Service signatures take ids + primitives (user_id, not a
request) so a stage can later move to a background task with no signature change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class WorkerAllocation:
    """One worker's share of a stage's work, as PRIMITIVES (no ORM objects), so the
    base service can book it through the expense facade without the handler
    importing expense."""

    worker_id: int
    quantity: Decimal
    # Optional precise source (cutting allocates per CuttingBundleItem); None for
    # coarse stages that allocate at the stage level.
    bundle_item_id: int | None = None
    notes: str = ''


@dataclass
class CompletionResult:
    """What a stage's complete() returns. The base StageService consumes it to book
    worker earnings and advance the Adda. Empty allocations = the stage credits no
    worker; payability is enforced via WorkflowStage.credits_workers (M2.7)."""

    allocations: list[WorkerAllocation] = field(default_factory=list)
    notes: str = ''


@dataclass
class ReopenResult:
    """Extra AddaStageRecord field names a stage's reopen changed (so the base save
    persists them), mirroring the existing reopen Template Method's teardown."""

    extra_saved_fields: list[str] = field(default_factory=list)


class StageHandler(ABC):
    """Per-stage strategy. A subclass sets the class attributes and implements the
    hooks, then registers itself (typically `register(MyHandler)` at module load).

    Class attributes:
      code            stable stage code, matches production.Stage.code + URLs
      name            display label
      template_partial path to the stage's panel partial
      required_skill  skill code gating the stage, or None (data-driven via
                      production.Stage.access_by_skill is preferred — see M3.1)

    Payability (does completing this stage credit workers?) is NOT a handler
    attribute — it lives on WorkflowStage.credits_workers (data). See cost/credit.
    """

    code: str = ''
    name: str = ''
    template_partial: str = ''
    required_skill: str | None = None

    @abstractmethod
    def snapshot(self, adda) -> dict:
        """Lightweight, request-free stage state (drives the Adda overview tiles +
        embedded mini-panels). Mirrors the service get_*_snapshot."""

    @abstractmethod
    def panel_context(self, request, adda, record) -> dict:
        """Full render context for the stage's standalone/embedded panel
        (request-coupled: forms, permissions). Delegates to the view builder in the
        adapter phase; owns the logic after it moves into the package."""

    @abstractmethod
    def start(self, *, user_id: int, adda, record, data: dict):
        """Begin the stage (assign workers / init the typed record)."""

    @abstractmethod
    def complete(self, *, user_id: int, adda, record, data: dict) -> CompletionResult:
        """Validate + finalize the typed record. Return the work allocations for
        the base service to book. MUST NOT touch money or other apps."""

    @abstractmethod
    def reopen(self, *, user_id: int, record) -> ReopenResult:
        """Stage-specific teardown for reopening (delete/reset typed child rows).

        F4 (owner triage 2026-06-11): reopen SEMANTICS are a deliberate per-stage
        choice — pick one explicitly, never inherit by accident:
          • DESTRUCTIVE  (layering): typed record deleted, header copied to
            drafts; work is re-entered.
          • SOFT UNLOCK  (cutting_pattern): record/evidence/verifications kept;
            re-complete sails through satisfied gates.
        Either way, auto-cancelled worker tasks stay cancelled — manager
        re-assignment is the recovery path (F3 lifecycle)."""

    @abstractmethod
    def cost_quantity(self, record) -> Decimal | None:
        """The quantity this stage's processing cost is computed against
        (pieces / bundles / layers), read from the typed record. Returns None when
        no quantity is available (unpriced) — NOT 0, so processing_cost stays NULL
        (NULL = unpriced; 0.00 = priced-zero / grouped). See cost_service."""

    def contribution_schema(self, adda) -> dict:
        """Declare the fields a WORKER reports for this stage's contribution lines —
        the open-closed seam that keeps the worker report form stage-agnostic.

        Default = a single quantity. A stage OVERRIDES to add dimensions/measures
        (Cutting adds colour + size). The report view + template render + parse
        generically from this schema; adding a stage needs NO worker-UI edit.

        Shape:
            {'line_label': str,
             'fields': [{'key', 'kind', 'label', 'required', ...}, ...]}
        `kind`: 'choice' (→ chip-picker; carries 'options':[{value,label,swatch?}])
                | 'quantity' (→ numeric input; carries 'unit').
        `key` maps 1:1 to the generic `lines` dict the services accept
        (color_id / size_id / reported_quantity / bundle_item_id).

        Stage-specific measures beyond today's columns (machine hours, defect count,
        roll weight…) are a LOCKED future extension: a nullable `attributes` JSONB
        on WorkerStageContribution + schema fields that map into it — added additively
        when a real stage needs it. See docs/archive/reviews/V2_FOUNDATION_REVIEW.md (F1, locked).
        """
        return {
            'line_label': 'line',
            'fields': [
                {'key': 'reported_quantity', 'kind': 'quantity',
                 'label': 'Quantity', 'required': True, 'unit': 'pieces'},
            ],
        }

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<StageHandler {self.code!r}>"
