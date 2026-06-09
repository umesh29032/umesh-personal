# Target Architecture — Kapil Enterprises ERP

> Companion to [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md). Describes the **end-state** the
> remediation drives toward. Status: APPROVED 2026-06-09. Not yet built.

## Governing principle

> **Architect for multi-factory / async / scale. Do NOT implement them.**
> Build seams, not features. A 8.5–9/10 system at low complexity beats a forced
> 10/10 carrying enterprise machinery this business does not yet need
> (today: 1 factory, few users, low-thousands of Addas).

Three concrete applications of the principle:
- Multi-factory → nullable `factory` FK + scoping helpers. NO factory switcher UI / admin / dashboards / per-factory RBAC UX.
- Async → keep service boundaries task-movable. NO Celery/Redis built now.
- Scale → cheap in-process wins (kill N+1, paginate, ledger snapshots). NO premature infra.

## App dependency graph (end state — strictly acyclic, CI-enforced)

```
core
 └─ accounts              identity + RBAC; depends on NOTHING domain-specific
     └─ raw_materials
         └─ production              ──facade──▶ tracking    (logs; one-way)
             │                      ──facade──▶ expense     (books earnings; one-way, primitives)
             └─ inventory           (RBAC infra / Access hub / dashboards)
                 └─ storefront
```

**Module-import edges (what `.importlinter` enforces):**
- `production → expense` is a **declared one-way edge**. Stage completion books worker
  earnings by calling the `expense` earnings facade with **ids + primitives only**
  (worker_id, qty, rate, source ids). The call lives in **exactly one file**
  (`stages/base/service.py`) — individual stage handlers NEVER import expense.
- `production → tracking` one-way (logging facade).
- `expense → production` and `tracking → production` module imports are **removed**
  (see resolutions below). Data-level FKs (`StageWorkAssignment → production.AddaStageRecord`)
  stay as **string refs** — string FKs are NOT import edges, so no cycle.
- `accounts` is domain-free — the `accounts→production` sync edge is relocated (see C4 / M4).

**Two cycles that exist TODAY and how each is broken (do not pretend they're already gone):**
1. **`production ↔ expense`** (REAL now: `stage_views.py:59-61` imports `expense.models`/`expense.services`;
   `expense/allocation_service.py` imports `production.cost_service` + `CuttingBundleItem`).
   → Break by: (a) production calls an `expense` earnings facade with primitives from the
   base stage service only; (b) `expense` stops importing production code (rate + item data
   passed in, not fetched). Net: one-way `production → expense`.
2. **`production ↔ tracking`** (`tracking.services` reads production models for barcode gen/export).
   → A logging *facade* only fixes `production→tracking`. The `tracking→production` half requires
   an **ownership MOVE**: relocate barcode-assembly into `production`, leaving `tracking` a dumb
   range/scan primitive. That is a cross-app model+data migration — its own phase (M4.2), not a one-liner.

- Every cross-app call goes through a published `services/__init__.py` facade.
- `.importlinter` **forbids** cycles and deep imports — convention becomes contract.

## Production app — stage engine

Folder structure mirrors the business domain (shop floor = directory tree):

```
production/
├── apps.py                 # ready() → registry.autodiscover()
├── models/                 # ENGINE/SHARED models ONLY — never moved:
│   │                       #   Adda, AddaStageRecord (polymorphic parent),
│   │                       #   WorkflowStage, Stage, Product
├── services/__init__.py    # PUBLISHED facade (only cross-app entry point)
├── urls.py                 # central routing → stages/<stage>/views
└── stages/
    ├── base/               # FRAMEWORK code (not a stage)
    │   ├── handler.py      #   StageHandler ABC + StageService template
    │   └── registry.py     #   register() / get() / autodiscover()
    ├── layering/
    │   ├── handler.py  service.py  views.py  models.py   # LayeringRecord lives here
    ├── cutting_pattern/
    │   ├── handler.py  service.py  views.py  models.py
    ├── cutting/            # split by RESPONSIBILITY (it has 3), not by LOC
    │   ├── handler.py
    │   ├── bundle_service.py
    │   ├── breakup_service.py
    │   ├── completion_service.py
    │   ├── views.py  models.py
    └── barcode_generation/
        ├── handler.py  service.py  views.py  models.py
    # future: stitching/  finishing/  packing/  → just add a folder
```

### Model placement rule
```
SHARED / ENGINE  → production/models/             (Adda, AddaStageRecord, WorkflowStage, Stage, Product)
STAGE-SPECIFIC   → production/stages/<stage>/models.py  (typed records, bundles, breakups…)
```
`AddaStageRecord` is the engine parent → stays central. Only its typed children move.

**Discovery mechanism (this is load-bearing — `apps.ready()` is TOO LATE for model registration):**
- Every moved model MUST declare `class Meta: app_label = 'production'` (models outside the
  conventional `<app>/models` module are otherwise not attributed to the app).
- `production/models/__init__.py` must import each stage's models **at model-load time**
  (a small import-time autodiscovery loop over `stages/*/models.py`, NOT in `apps.ready()`).
- Only then is the table attributed to `production` with the **same db_table** → **no schema
  migration** for the move. Skip either step → Django errors or generates spurious migrations.

⚠️ Consequence for "add a stage": a new stage's `models.py` becomes visible via the import-time
autodiscovery, so no manual edit — BUT this autodiscovery is the mechanism that makes it work.
The "zero edits" claim depends on it existing (built in M2.1).

### File-split rule (inside a stage)
Split `service.py` into more files **when it has more than one reason to change**
(multiple responsibilities / hard to navigate / hard to test in isolation).
LOC is a *signal*, not a law — a 700-line clean file beats a 300-line tangled one.
Today only `cutting/` earns the split (bundle + breakup + completion).

## The stage dispatch — before vs after

Before (scattered across 6+ sites):
```python
if stage_type == 'layering': ...
elif stage_type == 'cutting': ...      # + cost_service._quantity_for, adda_service first-stage,
elif stage_type == 'barcode_generation': ...   #   adda_views snapshot map — all branch the same way
```

After (one registry, open-closed):
```python
handler = registry.get(adda.current_stage.stage_type)
ctx = handler.panel_context(adda, record)
handler.complete(user=user, adda=adda, record=record, data=data)
```

### StageHandler contract
```python
class StageHandler(ABC):
    code: str
    template_partial: str
    required_skill: str | None        # data-driven via Stage.access_by_skill
    pays_workers: bool
    def panel_context(self, adda, record): ...
    def start(self, *, user_id, adda, record, data): ...
    # Handlers return DATA, never touch money. They are pure of expense.
    def complete(self, *, user_id, adda, record, data) -> CompletionResult: ...
    def reopen(self, *, user_id, record) -> ReopenResult: ...
    def cost_quantity(self, record) -> Decimal: ...
```
**Earnings seam (R1 — the part that keeps `production↔expense` from re-forming):**
The base `StageService` (in `stages/base/`) — NOT the individual handler — owns the single
`expense` call. `complete()` returns a `CompletionResult` listing worker allocations
`[(worker_id, qty, rate, source_ids)]`; the base service passes those primitives to the
`expense` earnings facade inside the atomic block. `reopen()` returns the assignments to void.
→ `production → expense` import lives in ONE file; every handler stays expense-free.
**Async-readiness rule (M5 seam):** service signatures take **ids + primitives** (`user_id`,
not a `request`/`user` object) and return serializable results — so a service can later move
to a background task with no signature change.

### Add a new stage (the realistic win)
```
mkdir stages/stitching/  +  write handler.py (+ service.py, views.py, models.py)
→ models autodiscovered, handler self-registers, costed, paid, skill-gated.
```
Edits to existing files: **+1 line** in `production/urls.py` (route include). Everything else is
open-closed. (Honest claim — NOT "zero edits": central routing + import-time model autodiscovery
are deliberate single touch-points, proven minimal by an open-closed test in M2.10.)

## Request flow — "complete a stage" (end state)
```
POST .../stage/cutting/complete
  → StageCompleteView (thin)
      → StageService.complete()  @transaction.atomic
            → SELECT FOR UPDATE Adda            # WF-4 lock: no double-advance
            → handler = registry.get('cutting')
            → result = handler.complete(...)    # handler returns DATA, no money
            • freeze processing_cost
            • expense_facade.book_earnings(result.allocations)   # the ONE prod→expense call (primitives)
            • advance Adda.current_stage
            • tracking_facade.log_adda(...)                      # one-way edge
      → reconciliation invariant: Σ earnings == processing_cost  # PAY-4
```
Only `StageService` (base) imports the expense + tracking facades. Handlers stay pure.

## RBAC (end state)
```
super_admin bypass ─┐
Role + permissions  ├─▶ permission/ (request-cached)
Skill ⇄ Stage.access_by_skill ─▶ access_service  (views AND mutations; no hardcoded skill constants)
Factory scope ─▶ current_factory() chokepoint + no-op scoping manager
SIDEBAR (code) ──auto-seeds──▶ SidebarItemRule (DB)   # no dual-source drift
```

### Factory seam — TRUE seam, NO columns yet (C2 correction)
The principle is "architect for multi-factory, do NOT implement it." Adding a nullable
`factory` FK to Adda/ClothRoll/**ledger**/**settlement** now would be *implementing* it —
schema churn on immutable financial tables, and **half-scoping is a cross-factory data-leak
risk** (if some tenant tables get the column and others don't, enabling multi-factory later
leaks across sites). So the seam is:
- A single `current_factory()` helper (returns the one default factory today).
- A scoping chokepoint (manager/queryset method) every tenant-data query routes through —
  a **no-op** while there is one factory.
- **NO `factory` columns added now.** When site #2 is funded: add the FK to **ALL** tenant-data
  tables in one migration wave + flip the chokepoint from no-op to real filter. That migration
  is the *implementation*; today we only build the chokepoint it will plug into.

## What stays untouched (already excellent — do not rewrite)
Immutable worker ledger · single-writer services · frozen cost snapshots · PROTECT
on_delete posture · data-driven flow composition · `core` abstract bases ·
machine-enforced acyclic import contract.
