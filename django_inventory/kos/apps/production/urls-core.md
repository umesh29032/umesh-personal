---
id: app-production-urls-core
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Production's dashboards, product masters, flow editor, pattern library, and stage-library URLs — each one's full learning story."
related: [app-production-urls]
---

# production URLs · Part 1 — Dashboards · Products · Flow Editor · Libraries (26)

> 📂 [URL index](urls.md) · [production app](README.md) · [LOS home](../../README.md)
> All management-lane unless noted; every URL also sidebar-rule gated.

---

### `/production/` — `dashboard`
**Purpose:** the floor's home — Addas by state, at a glance. **Why:** the owner's morning starts with "kya chal raha hai."
**Method:** GET → `AddaDashboardView` (`views/dashboard.py`). **Reads:** grouped Adda/state aggregates. **Writes/locks:** none.
**Why simple:** pure read over states other URLs maintain — dashboards borrow correctness, never create it.
**Perf:** bulk queries (fixed-cost-for-3-Addas pinned pattern). **Tests:** `test_perf_baseline.py`.
**Learn:** [query-performance](../../concepts/postgresql/query-performance.md).

### `stalled/` — `stalled-addas`
**Purpose:** which batches are STUCK (no progress). **Why:** stalls are money sleeping on the floor; surfacing them is management's nudge.
**Method:** GET → `StalledAddaListView` (`views/dashboard.py`) → template `production/stalled_addas.html`.
**Service:** `operations_digest.stalled_stage_records()` — the SAME function that feeds the dashboard's Stalled tile (one stalled-calc path → tile count and this list always reconcile).
**Access:** `ProductionRoleMixin` + sidebar-rule gated; worker isolation — non-management see only stalled Addas they hold a live task on (same rule as dashboard/history).
Read-only; staleness derived from ASR timestamps (duration is AUTO — owner rule).
**Why simple:** derived filter over existing truth. **Lesson:** design timestamps once, get monitoring free.

### `pending-reports/` — `pending-reports`
**Purpose:** worker reports awaiting management review. **Why:** the red-pen queue ([§review](urls-adda.md#addascodereview-reports--adda-report-review)) needs a feeder list.
**Method:** GET → `PendingReportListView`. Read-only over WSC/WST states.

### `costing/` — `costing`
**Purpose:** the manufacturing-cost dashboard. **Why:** "is Adda par kitna kharcha hua" — from FROZEN `processing_cost` snapshots.
**Method:** GET → `ProductionCostingView` (`views/costing_views.py`).
**Misconception guard:** cost here NEVER includes settled labor — summing both = double count (ADR-0009, a pinned refusal class).
**Learn:** [ADR-0009](../../../docs/adr/0009-cost-truth.md) · [money-story §cost](../../project/money-story.md).

---

### `products/` — `product-list` · `products/add/` — `product-create` · `products/<pk>/edit/` — `product-update` · `products/<pk>/archive/` — `product-archive`
**Purpose:** the manufacturing product master (T-SHIRT, NIKKAR — definitions, not catalog items).
**Why SA-only (all four):** master-data lockdown (MGT-A certified) — a product edit ripples into every future Adda's flow, rates, sizes; that blast radius is owner-only.
**Methods:** GET list · GET+POST forms · POST archive. **Handlers:** `views/product_views.py` (5 classes, SuperAdminOnlyMixin). **Service:** `product_service`.
**Archive ≠ delete:** `is_active=False` — soft-archive; dropdowns use `Model.active`, audits see all ([orm-and-managers](../../concepts/django/orm-and-managers.md)).
**Failure modes:** archive with live Addas → guarded; validation.
**Why simple:** CRUD over a master table — the DEPTH lives in what hangs off it (flow, sizes).
**Tests:** product suites + MGT-A certification probes.

### `products/<pk>/flow/` — `product-flow` ⭐ THE FLOW EDITOR
**Purpose:** define THIS product's pipeline: which stages, in what order, at what rate, which cost grouping, pay-eligibility, allocation grain ("Work split").
**Why it exists:** stages-as-data is the platform's core bet — the owner configures manufacturing without code.
**Method:** GET (editor) + POST (actions) → `ProductFlowEditView` (`views/flow_views.py`).
**Service:** `flow_service` — `add_stage_to_product_flow` / `remove` / `move` / `set_stage_cost` / `set_stage_grain` (all atomic, all loud).
**Validation (the teaching part):** grain MONOTONICITY down the flow (`_validate_grain_monotonicity`) · cost-grouping coherence (`_validate_cost_grouping`) — the editor refuses configurations that would corrupt pools or costing later. **Fail at config-time, not at Adda-time.**
**Writes:** `WorkflowStage` (+role rates). **Locks:** none needed — config, not concurrent money.
**Ripple (memorize):** existing Addas KEEP their frozen snapshots; only FUTURE Addas inherit edits ([models.md](models.md) frozen-snapshot law).
```
Journey: POST action → view (SA/mgmt gate) → flow_service.verb
[@atomic · monotonicity+grouping validation] → WorkflowStage rows → editor re-render
```
**Failure modes:** grain regression refused · grouping conflict refused · remove-stage-with-history guarded.
**DSA:** the flow = an ordered list the whole pipeline topologically obeys.
**Engineering Decision.**
*Problem:* every product manufactures differently, and the factory invents
new steps. *Options:* (A) hardcoded stage classes per product — deploy per
change; (B) one generic "stage" with a JSON blob — no validation, no gates;
(C) stages as configured ROWS (library + per-product WorkflowStage) with
handler packages only where behavior is truly custom. *Chosen:* C.
*Trade-offs:* config UIs to build+guard, config-time validation burden
(monotonicity, grouping). *Would we still choose it today?* **Yes** — R10-B
proved it: a whole new stage type shipped with zero new endpoints.
**Evolution Timeline.** Originally: four built-in stages, hardcoded order →
*problem:* every new step meant code → *refactor:* Stage library +
per-product flows + rates/grain/grouping on the editor → R10-B generic
stage platform (2026-07) → *current:* config-only stages ride five shared
endpoints → *future:* TM-1 tracking-mode lands on this editor; barcode
capture (TM-2) joins via C-TM's one door.
**Required knowledge:** [allocation §grain](../../features/allocation.md) · [service-layer](../../concepts/architecture/service-layer.md).
**Real question:** "PM: T-shirts need an Ironing step" → a ROW here, not code (R10-B) — see README's Real Engineering Questions.

### `products/<pk>/sizes/` — `product-sizes`
**Purpose:** per-product size chart (S/M/L/XL…). **Why:** cutting breakups + barcode ranges key on (size, color) — sizes are structure, not free text.
**Method:** GET+POST → `ProductSizesEditView`. **Service:** `product_size_service`. **Why simple:** master rows with referential integrity doing the real work.

### `products/<pk>/patterns/` — `product-patterns` · `…/patterns/blueprint/` — `product-pattern-blueprint`
**Purpose:** redirects into the patterns_ai app (Pattern Dashboard / Blueprint module).
**Why redirects exist:** the pattern platform moved to its own app (Phase-1/D-1 boundary, ADR-H); **old URLs keep working forever** — bookmarks are contracts. That's the whole lesson: renames ship as redirects, not 404s.
**Method:** GET → redirect views (`views/pattern_views.py`). **Why simple:** by design — one `HttpResponseRedirect` each.

---

### `patterns/` — `pattern-list` · `patterns/add/` — `pattern-add` · `patterns/<pk>/edit/` — `pattern-edit` · `patterns/<pk>/delete/` — `pattern-delete`
**Purpose:** the reusable ProductPattern library (Production Components: Body, Sleeve, Collar…).
**Why:** components are shared vocabulary across products; cutting counts and bundle itemization key on them.
**Methods:** standard CRUD, perm-gated (SA bypass). **Handlers:** `views/pattern_views.py`.
**Naming trap (misconception):** table keeps its historical name `ProductPattern`; docs/UI say **Production Component** (owner-ratified 2026-07-11) — the GLOSSARY entry explains; don't "fix" the model name.
**Delete:** guarded — components referenced by assignments/history protect themselves (PROTECT FKs).
**Learn:** [cutting](../../features/cutting.md) · [GLOSSARY](../../../GLOSSARY.md).

---

### `stages/` — `stage-list` · `stages/add/` — `stage-add` · `stages/<pk>/edit/` — `stage-edit` · `stages/<pk>/delete/` — `stage-delete`
**Purpose:** the global Stage LIBRARY — reusable step definitions holding access rules (skills/roles), work type (Manual|Machine ⇒ MachineType mandatory, DB CHECK), default rate.
**Why SA-only:** a Stage row is an ACCESS-CONTROL artifact (its skills gate who can even see stages built from it) + a money default — double-sensitive.
**Method:** CRUD → `views/stage_views.py`. **Why access lives ON the model:** replaced the old /stage-access/ page — one row = definition + gate, the same collapse-the-pair philosophy as SidebarItemRule ([rbac-access](../../features/rbac-access.md)).
**Model anchor (the machine-kind edit surface):** `Stage.work_type` + `Stage.machine_type` (FK → `production.MachineType`, PROTECT) in `config/production/models/core.py` — a stage declares WHAT KIND of machine it needs HERE, on the library row, not in the machines app. The pairing rule is DB CHECK `prod_stage_worktype_machinetype_pair` (Machine ⇒ type mandatory; Manual ⇒ type forbidden). Changing what kind(s) a stage accepts = this field + this CHECK + the machine-selection guard ([machines](../../features/machines.md)).
**Delete:** refused once WorkflowStages reference it (PROTECT).
**Tests:** stage CRUD perm probes (certified).

*R10-C data-driven masters — six URLs, shared teaching (rows-not-code: classifications change with the factory; enums would need deploys), each route individually below:*

### `stage-categories/` — `stage-category-list`
GET (SA) → `StageCategoryListView`. Display-grouping master list.
**Misconception guard:** `StageCategory` is DISPLAY ONLY — never gates workflow, money, or access ([models.md](models.md)). **Why simple:** a lookup table's power is in what references it.

### `stage-categories/add/` — `stage-category-add`
GET+POST (SA) → `StageCategoryCreateView`. One row in; every stage picker updates. **Why simple:** create-form over a two-field master.

### `stage-categories/<pk>/edit/` — `stage-category-edit`
GET+POST (SA) → `StageCategoryUpdateView`. Rename ripples to display everywhere INSTANTLY (referenced, not copied) — the argument FOR rows-not-code, live.

### `machine-types/` — `machine-type-list`
GET (SA) → `MachineTypeListView`. The machine KINDS master.
**The teaching line:** stages point at TYPES, never instances — planning names the kind, the floor picks the unit ([machines](../../features/machines.md)).

### `machine-types/add/` — `machine-type-add`
GET+POST (SA) → `MachineTypeCreateView`. New kind → immediately selectable on Machine stages (work type Machine ⇒ type mandatory, DB CHECK).

### `machine-types/<pk>/edit/` — `machine-type-edit`
GET+POST (SA) → `MachineTypeUpdateView`. **Why no delete route exists (learn from absence):** types referenced by machines/stages are PROTECT-anchored — retirement = archive semantics, not deletion.

## Learning Graph (this file)
**Before:** [README Mental Model](README.md). **After:** [urls-adda.md](urls-adda.md) — where these configurations become running batches.
