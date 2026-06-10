# R1 — Manufacturing Stage-Domain Architecture Review

**Date:** 2026-06-10 · **Phase:** R1 (review only — no UI design, no code, no migrations) · **Status: 🔒 LOCKED — owner accepted D-R1.1…D-R1.10 in full, 2026-06-10.**
**Owner-emphasized principles (verbatim intent):** production output truth exists independently of barcode existence · MissingPiece and Alter/Rework must not depend on barcode existence · tracking owns identity and scan history · production owns quantity truth and work progression · scanning is a stage capability, not a stage archetype · issuing identity and consuming identity are separate responsibilities · future stages may optionally or mandatorily require scans through stage-level policy.
**Rev.2 (owner clarifications):** added §2A (formal Stage Contract definition), §5A (expected-piece truth vs identified-piece truth — Missing/Alter must never depend on barcode existence), §8A (barcode integration seam for scan-capable stages — architecture opening only, barcode lifecycle deferred to a future Barcode/Traceability review).
Scope set by owner: (1) manufacturing responsibilities · (2) stage output contracts · (3) contribution schemas · (4) costing units · (5) traceability boundaries · (6) MissingPiece integration · (7) Alter/Rework integration · (8) barcode ownership · (9) machine sub-stage model.
**Constraint honored throughout: stage NAMES are not finalized.** Everything below is expressed as capability contracts that survive renames, splits, and merges. Inputs: STAGE_DOMAIN_REVIEW_AGENDA, ARCHITECTURE_V2 (§11 locked), V2_FOUNDATION_REVIEW (F1/F2 locked), P4_2_BARCODE_DESIGN_REVIEW, ADR 0001-0007, `stages/base/handler.py` contract, R0 truth model.

---

## 0) The taxonomy-independence principle (frame for everything below)

A stage is **not** its name. A stage is:

> **a declared transformation** = (input contract, output contract, actor type, measures, payability, quality gates)

bound to an immutable identity (`Stage.code`) and a behavior package (`StageHandler` + typed record). The product workflow is an ordered list of such transformations. Renaming, splitting, or merging stages changes *which* transformations exist — never the *shape* of how a transformation declares itself. This review locks the shapes; the future taxonomy exercise only instantiates them.

**Invariants this review proposes to lock (valid under any future taxonomy):**

| # | Invariant |
|---|---|
| I1 | Stage identity = `Stage.code` (immutable); `name` = display. Already locked (V2_FOUNDATION). |
| I2 | Stage behavior = `StageHandler` + typed record; registered, autodiscovered, open-closed. New code NEVER adds stage-name conditionals (the ~30 legacy sites are a cleanup worklist, not a pattern). |
| I3 | The canonical dimensional grain of piece-producing output and worker contribution is **(adda, stage, color, size, quantity)**. Stage-local extra measures are additive (`attributes` JSONB seam), never a replacement for this grain. |
| I4 | What a worker reports = stage-declared via `contribution_schema()`; worker work always flows through WorkerStageTask + WorkerStageContribution — no parallel labor pipeline, ever (includes rework, §7). |
| I5 | Costing unit = data (`WorkflowStage.cost_method` + rate) interpreted by the handler (`cost_quantity()`); NULL = unpriced ≠ 0.00 = priced-zero. New units are additive enum values. |
| I6 | Payability = data (`WorkflowStage.credits_workers`), never a handler attribute or name check. |
| I7 | Quality gates are stage-handler-owned completion validations (MAY gate that stage); per-worker task `verified` NEVER gates (R0 C3). |
| I8 | Piece identity + scan state + history = the `tracking` primitive (ID/value-addressed, string-FK'd, importing no production). |
| I9 | Missing/Alter = lifecycle domains that READ production + scan truth and FEED settlement summaries through the §11.10 source-agnostic variance seam; settlement never owns their workflow. |
| I10 | Cross-app manufacturing references are IDs/values (string FKs) — extraction-ready; the only production→expense edge is the base-service facade (one file). |

---

## 1) Manufacturing responsibilities — the archetype map

Instead of naming stages, classify every current and future transformation into **responsibility archetypes**. Each archetype fixes the contract questions (what's consumed, what's produced, who acts, what's measured):

| Archetype | Consumes | Produces | Actor | Canonical measure | Payable? (typical) | Today's reference |
|---|---|---|---|---|---|---|
| **A. Material staging** | raw material units (rolls) | prepared material (layers) + remnants | worker | stage-native unit (layers; lengths) | yes | layering |
| **B. Geometry preparation** | prepared material + product pattern library | a cutting plan / marked geometry + evidence artifacts (photos/video) | skilled worker | none (plan, not pieces) | configurable | cutting_pattern |
| **C. Piece transformation** | upstream material/pieces | dimensioned pieces — grain I3 — + grouping artifacts (bundles) | worker(s) | pieces per (color,size) | yes | cutting; future stitching/thread-cutting/finishing |
| **D. Verification / QC** | another stage's output | accept/reject/defect facts | inspector/management | counts of inspected/accepted/rejected | usually no | CuttingPatternVerification (embedded today); future QC stages |
| **E. Identification** | dimensioned pieces | piece identities (barcode ranges) | system/worker | identities issued | configurable | barcode_generation |
| **F. Aggregation / dispatch** | identified pieces | packed/dispatched units + scan events | worker | scanned/packed counts | configurable | future packing/dispatch (scan primitive exists) |

**Rules this map fixes:**
1. Every stage (current or future) declares its archetype; the archetype determines which contract sections (§2-§4) apply. A stage may combine archetypes (today's cutting = C + seeds of E via breakdowns) — combined stages are candidates for future *splits*, which is a taxonomy decision, not an architecture one.
2. **D is currently embedded, not free-standing:** verification lives inside the B stage (pattern verification as a completion gate). The architecture must allow D as either (a) an embedded completion gate (today, I7) or (b) a free-standing workflow stage later — both already fit the WorkflowStage list + handler model. Nothing to build now.
3. Responsibility map per concrete stage = the future taxonomy exercise's deliverable; this table is its template.

## 2) Stage output contracts

**Current state:** output is implicit — each stage writes a typed OneToOne record (+ artifacts: roll entries, photos, bundles, breakdown rows, barcode ranges); downstream stages and dashboards read those records directly; `handler.snapshot(adda)` already provides a request-free read surface.

**Proposed contract (lock the rule, not new code):**
1. A stage's **output contract = its typed record + declared artifacts + the completion fact** (timestamp-derived). The handler's `snapshot()` is the canonical *read* surface for cross-stage and dashboard consumption.
2. **Downstream reads upstream ONLY via the typed record / snapshot surface — never via stage-name conditionals** (I2). Template elif chains and `stage__code` filters in cross-stage logic are legacy debt; the worklist is the existing `FUTURE-STAGE-REDESIGN` markers + the ~30 sites inventoried in R0.
3. **The piece-producing output grain is locked as I3** — (adda, stage, color, size, qty), today embodied by `AddaProductSizeColorPieceBreakdown` + bundle items. Any future C-archetype stage must emit this grain (its extra measures ride the additive seam). This is what keeps settlement (§11), Missing (§6), Alter (§7), and reporting valid through renames.
4. **Handover validation belongs to the consumer's `start()`/the producer's `complete()`** — stage-handler-owned (I7), not a global engine rule. (Today: cutting validates against layering's lay_count; pattern completion requires verification. Both stay handler-local.)
5. Deferred-additive: a formal `output_summary()` handler hook (machine-readable contract listing) — introduce only when a consumer (reporting, Missing auto-detection) actually needs programmatic discovery; `snapshot()` suffices today.

## 2A) Formal Stage Contract (the stable foundation beneath any taxonomy)

Every stage — current, renamed, split, merged, or future — is fully described by **one contract with nine fields**. The contract, not the stage name, is what the engine, costing, settlement, Missing/Alter, and reporting depend on. Taxonomy changes re-instantiate contracts; they never change the contract *shape*.

> **Where each field lives (all existing seams — no new infrastructure):** identity = `Stage.code`; behavior fields = `StageHandler` (typed record, `snapshot()`, `complete()` validations, `cost_quantity()`, `contribution_schema()`); policy fields = `WorkflowStage` data (`cost_method`, `cost_rate`, `credits_workers`, future `scan_policy` §8A, future `parent` FK §9).

| Contract field | Definition | Declared via |
|---|---|---|
| **1. Inputs** | What the stage consumes: upstream typed record(s)/snapshot facts + material/artifacts it requires to `start()` | handler `start()` preconditions |
| **2. Outputs** | The typed record + artifacts + completion fact; for piece-producing stages, MUST include grain I3 (adda, stage, color, size, qty) as **expected-piece truth** (§5A) | typed record + `snapshot()` |
| **3. Contribution Schema** | What a worker reports, per §3 archetype patterns | `contribution_schema()` |
| **4. Costing Unit** | (cost_method, `cost_quantity()`) pair; NULL=unpriced ≠ 0=priced-zero; processing-cost unit may differ from earning unit (§4) | WorkflowStage data + handler |
| **5. Completion Rule** | Stage-handler-owned validations that gate THIS stage's completion (I7); task-level `verified` never gates | handler `complete()` |
| **6. Traceability Level** | Which rung of the §5 ladder the stage writes: dimensional (expected-piece) and/or identified-piece (scan) | output grain + §8A scan policy |
| **7. Missing-Piece Detection Capability** | Whether/how the stage can surface shortfall: count-mismatch (dimensional, barcode-free) and/or scan-shortfall (identified) and/or manual (§6) | declared in contract; consumed by the future Missing module |
| **8. Alter/Rework Detection Capability** | Whether the stage can raise defects (as detected_stage) and/or receive rework tasks (as origin/rework stage) (§7) | declared in contract; consumed by the future Alter module |
| **9. Settlement Relevance** | `credits_workers` (payability) + whether outputs feed expected-earning freezes and the §11.10 variance seam | WorkflowStage data + §11 locks |

**Archetype defaults (a concrete stage starts from its archetype's row and overrides explicitly):**

| Field | A material | B geometry | C piece-transform | D verification | E identification | F dispatch |
|---|---|---|---|---|---|---|
| Inputs | raw units | prepared material + pattern lib | upstream material/pieces | another stage's output | dimensioned pieces | identified pieces |
| Outputs | prepared material + remnants | plan + evidence artifacts | **grain I3 pieces** + groupings | accept/reject facts | piece identities | packed/dispatch units + scan events |
| Contribution | native-unit qty | usually none | color+size+qty lines | none or counts | none/qty | scanned qty per dims |
| Costing unit | per_layer-like | usually unpriced | per_piece/per_bundle | usually unpriced | per_piece | per_piece/flat |
| Completion rule | handler-local | may require evidence/verification | qty validations vs upstream | inspection complete | ranges issued | scan/pack thresholds |
| Traceability | dimensional | none (artifact) | **dimensional (expected)** | dimensional | creates identified | identified |
| Missing detection | count-mismatch | n/a | count-mismatch | count-mismatch | range-vs-scan baseline | **scan-shortfall** |
| Alter detection | rare | as detected_stage | detected + origin + rework target | **primary detected_stage** | n/a | detected_stage |
| Settlement | payable typical | configurable | payable typical | usually not | configurable | configurable |

## 3) Contribution schemas (worker-report shapes per archetype)

`contribution_schema()` is built and locked (F1). What R1 adds: **the per-archetype schema patterns**, so future stages pick a pattern instead of inventing one:

| Archetype | Schema pattern | Columns vs `attributes` JSONB |
|---|---|---|
| A. Material staging | qty in stage-native unit (e.g. layers); optionally per-roll lines | existing columns suffice |
| B. Geometry prep | usually NO contribution lines (work is the artifact); if paid, a single completion-quantity | existing columns |
| C. Piece transformation | **the Cutting reference**: color + size + qty lines (I3) | existing columns; piece-type/defect-count = JSONB when first needed |
| D. Verification | none, or inspected/accepted/rejected counts | counts → JSONB on first real QC stage (first likely JSONB consumer) |
| E. Identification | none (system work) or qty | existing |
| F. Dispatch/packing | scanned/packed qty per (color,size) | existing columns (scan state is the source) |
| Machine sub-stages | qty + machine-hours / operation-count | **JSONB trigger** — the second likely consumer (§9) |

**Locks proposed:** (1) the pattern table above as guidance; (2) JSONB column lands with its FIRST real consumer (a D or machine stage), exactly per F1 — never speculatively; (3) contribution lines on C/F archetypes always carry color/size (already LOCK-NOW); (4) schemas remain per-stage declarations — this review does NOT freeze any future stage's concrete schema (taxonomy-dependent, intentionally open).

## 4) Costing units

**Current state:** `WorkflowStage.cost_method` ∈ {per_piece, per_bundle, per_layer} + `cost_rate`; `handler.cost_quantity()` maps the typed record to the unit (layering→lay_count, cutting→pieces or bundle-count, barcode→total_barcodes, pattern→None=unpriced); NULL/0 semantics locked; frozen `processing_cost` snapshot at advance; `credits_workers` separate (I6); worker `expected_*` freeze uses role-rate-or-stage-rate.

**Proposed locks:**
1. **Costing unit = (cost_method data, cost_quantity handler) pair** — extending to per_hour / per_operation / per_kg / flat is an additive enum value + handler arithmetic; no schema redesign. (Validates §2.3 of the master-context for costing.)
2. **Stage processing cost ≠ worker earning** are two separable computations sharing inputs: processing cost = what the Adda absorbs (frozen on the stage record); earning = what workers receive (today allocation-credit; post-V2-2 = contribution × rate at settlement, ADR 0007). Keep them decoupled — a stage may be priced but non-payable, payable but unpriced, or use different units for each (F2's swappable-earning lock, restated at the costing level).
3. **Unpriced ≠ zero** stays load-bearing (NULL semantics) for any future unit.

**Deferred:** time-rate earning model, machine amortization in stage cost, multi-rate (per-color/size) pricing — each additive when a real stage demands it.

## 5) Traceability boundaries

**The resolution ladder (lock as the boundary model):**

```
Adda (batch)                          production
 └ stage record (transformation fact) production
    └ (color, size) dimensional truth production   ← grain I3
       └ bundle / grouping artifact   production
          └ piece identity + scan state  tracking  ← primitive boundary (I8)
              └ append-only history      tracking
```

**Locks proposed:**
1. **Production owns batch/stage/dimensional truth; tracking owns piece-level identity, scan state, and history** — ID/value-addressed (string FKs), importing no production (target shape per P4.2 Option A).
2. **IDENTIFIED-piece truth begins at the identification archetype (E); EXPECTED-piece truth exists from the first piece-producing stage regardless** — see §5A (the two truths are distinct; production output truth never depends on barcodes). Any future requirement for earlier per-piece identity = a taxonomy decision to move E earlier, not a model change.
3. **Worker↔work trace anchor = WorkerStageTask/Contribution** (who, which stage, which dims, how much) — the anchor Missing/Alter point at (§6/§7).
4. Piece identity format `{adda.code}-{seq:04d}`, one-shot generation, stays canonical.
5. **Deferred:** full piece genealogy (piece → bundle → breakup → pattern → layer → roll). The capture seams exist today (those FK chains are recorded); do NOT build a genealogy surface until a consumer (Missing/Alter analytics, recall tracing) demands it.

## 5A) Expected-piece truth vs identified-piece truth (owner clarification — load-bearing)

Two distinct, independently valid truths about pieces:

| | **Expected-piece truth** | **Identified-piece truth** |
|---|---|---|
| What | How many pieces EXIST per (adda, stage, color, size) — production output reality | WHICH individual pieces exist and their state — per-piece identity + scan events |
| Source | Stage outputs at grain I3 (breakdowns, bundle items) + worker contributions (reported/verified qty) | `BarcodeBatch` ranges + `BatchBarcode` scan state |
| Owner | **production** | **tracking** (primitive, I8) |
| Exists when | ALWAYS — from the first piece-producing stage onward | only after an identification capability has run (and only for identified pieces) |
| Authority | **Authoritative for production output, costing, expected earnings, settlement quantities** | Authoritative for individual-piece location/status/genealogy |

**Locked rules:**
1. **Production output truth exists independently of barcode tracking.** A workflow with NO identification capability still has complete expected-piece truth, full costing, full settlement, and full Missing/Alter capability at the dimensional level. Barcodes ENRICH truth; they never CONSTITUTE it.
2. **Missing/Alter anchor on expected-piece truth** (dimensional anchor, §6/§7); identified-piece references (BatchBarcode IDs) are OPTIONAL enrichment when identification has run. Neither module may require barcode existence to open, progress, or resolve a case.
3. **Reconciliation between the two truths is a derived comparison** (expected count vs identified/scanned count per dims) — computed, never stored as a third truth; it is one Missing-detection source among three (§6), not the gate for any of them.
4. Settlement, expected-earning freezes, and variance entry read expected-piece truth only — already the shipped + locked behavior (§11); restated here so no future module accidentally couples money to scan state.

## 6) MissingPieceCase — integration points (contract now, model later)

**Detection sources (all three must be representable):**
- (a) **scan shortfall** — expected range (`BarcodeBatch`) vs scan state (`BatchBarcode`): post-identification truth;
- (b) **handover/count mismatch** — reported vs verified quantities at any stage (pre-identification, dimensional);
- (c) **manual report** — human notices loss.

**Integration contract to lock:**
1. **Case anchor grain:** (adda, detection_stage, color, size, quantity) — **anchored on EXPECTED-piece truth (§5A), never requiring barcode existence** — + mandatory `detection_stage`/`detected_at`/`detected_by` (R0 C4) + OPTIONAL piece refs (BatchBarcode IDs, enrichment when identification has run) + optional WorkerStageTask ref (last-handler traceability — context, NOT blame: factory_absorbs stands).
2. **Status writing:** `tracking.mark_status` remains the single piece-status writer; the Missing module becomes its first caller (piece-level effect), while the case row is the lifecycle (open/aging/resolved/recovered/written-off). Case lifecycle lives in the production/QC domain, NOT in tracking (tracking stays a primitive, I8) and NOT in settlement (I9).
3. **Settlement feed:** case summaries flow into the **already-locked §11.10 source-agnostic variance seam** (the same fields manual entry uses today) — zero settlement schema change. Variance remains visibility under factory_absorbs; future deduction policies plug in without schema change (§11 lock).
4. **Recovery/write-off are case-lifecycle outcomes**, auditable, append-only; a recovered piece flips scan state via `mark_status`, never edits history.
5. **Aging/reporting** read the case table + grain I3 — no new production columns required.

**Deferred to the module PR:** concrete model fields, state machine, list/report surfaces, auto-detection jobs (scan-shortfall sweep = a background-job-boundary candidate, §17 seams).

## 7) Alter/Rework — integration points (contract now, model later)

1. **Reference target:** piece (`BatchBarcode`) when identified; dimensional (adda, stage, color, size, qty) when not. Same duality as Missing — one rule for both incident domains.
2. **Two stage references, distinct:** `detected_stage` (where the defect surfaced) vs `origin_stage` (where it was caused — may be unknown; nullable, never fabricated). Lifecycle per master-context: open → in_rework → qc_pending → resolved / rejected / scrapped.
3. **Rework labor = normal work (I4):** entering rework spawns ordinary WorkerStageTask(s) on the relevant stage (re-run or dedicated rework stage — taxonomy decision later); contributions flow through the standard pipeline; the AlterCase links to those tasks. **No parallel rework-labor mechanism, ever.** Payability of rework = the same data-driven controls (credits_workers + rates), policy decided later.
4. **Outcomes feed settlement** via the same §11.10 variance seam (scrapped → shortfall counts; the reserved `alter_*` columns in the AddaSettlement design stay reserved). Rework cost attribution = factory_absorbs at launch; configurable later (no engine now).
5. **QC interplay:** `qc_pending` implies a D-archetype check — embedded gate today, possible free-standing stage later; both fit (§1 rule 2).

**Deferred:** defect-type taxonomy, model fields, analytics surfaces — module PR after taxonomy.

## 8) Barcode ownership boundaries — settle P4.2's D3

This review is the "manufacturing-domain review" P4.2 was parked behind. Proposed settlement of its open decisions:

1. **D3 — barcode MODELS stay in `tracking` permanently.** `BarcodeBatch`/`BatchBarcode`/`BarcodeExportBatch` are the piece-identity/scan primitive (I8) — string-FK'd, ID-addressed, reusable, extraction-ready. Identification is a *capability the workflow invokes*, not a production-owned table set. (Confirms P4.2's recommendation; removes its "could shift in the redesign" caveat.)
2. **D2 — layering direction: tracking BELOW production.** Assembly (reads cutting data to compose ranges) is production logic and relocates INTO production; tracking exposes range/scan/QR/history APIs taking IDs/values and imports zero production. One-way edge.
3. **D1 — view placement** stays an execution detail of the P4.2 PR (recommend per its doc: cross-cutting list/export/dashboard views → inventory/apps layer; stage-embedded panel → production).
4. **Whether identification remains a visible workflow stage** (today: optional `barcode_generation` stage) **or becomes an implicit post-C step** is a TAXONOMY question — deliberately not decided here. Both fit the locked boundary: orchestration in production (stage handler or service step), issuance primitive in tracking.

**Consequence:** P4.2 is **unparked** as a characterization-tested, small-PR code relocation (no data migration), schedulable independently of V2 phases.

## 8A) Barcode integration seam — scan-capable stages (architecture opening ONLY)

**Owner direction:** scanning may never be a dedicated standalone stage; future stages (Singer/Overlock/Flatlock/Covering machines, QC, Packing, …) may OPTIONALLY require scans; a stage may support scanning **without becoming an identification stage**. The barcode lifecycle itself is NOT designed here.

**The seam (lock the shape, build nothing):**
1. **Scanning is a stage CAPABILITY, not an archetype.** Issuing identity (archetype E) ≠ consuming identity (scanning). Any stage of any archetype may be scan-capable; being scan-capable changes nothing about its contract fields 1-4 and 9 (§2A); it extends field 6 (traceability) and — only under a `required` policy — adds a completion rule under field 5 (see point 5).
2. **Scan policy is DATA, per workflow placement:** a future additive `WorkflowStage.scan_policy ∈ {none, optional, required}` (column added only when the first scan-capable stage ships — same deferred-additive discipline as `parent` FK and the JSONB). `none` is today's universal value; nothing changes for existing stages.
3. **Scan validation is a handler hook seam:** a future optional `StageHandler.validate_scan(...)` (or equivalent) lets a stage impose stage-local rules (right Adda, right dims, sequence/frequency, duplicate handling) — handler-owned like every other gate (I7). `required` policy + handler validation TOGETHER define what "scanned enough to complete" means for that stage — definition deferred.
4. **Scan events land in the tracking primitive** (I8): conceptually (piece-or-value, stage, worker, timestamp, outcome) — ID/value-addressed, append-only, production-independent. Whether this is `BatchBarcode` status alone or a future `ScanEvent` log = deferred to the Barcode/Traceability review.
5. **Expected-piece truth stays authoritative** (§5A): a `required` scan policy may gate that stage's completion (a completion rule, field 5) but never replaces dimensional output truth, costing, or settlement inputs.

**Explicitly DEFERRED to the future Barcode/Traceability review:** the detailed ownership model beyond §8's boundary, scan lifecycle + states, genealogy, scan frequency/cadence rules, piece-truth promotion rules, offline/duplicate-scan handling, scanner UX. R1 locks only that the architecture stays OPEN for barcode-enabled stages via points 1-5.

## 9) Future machine sub-stage model

**Lock the shape + the trigger rule; build nothing:**
1. **Shape:** machine operations = sub-stages under a parent `WorkflowStage` via the already-reserved additive `parent` FK; the list stays flat until the first real machine stage ships. Sub-stage progress/readiness rolls UP to the parent (derived, never stored — consistent with §11's derived-progress lock). Advance gates evaluate at the parent.
2. **Trigger rule (when is a sub-stage justified?):** only when an operation needs (a) different workers/rates/payability than its siblings, OR (b) independently tracked progress/handover. Otherwise it is ONE stage whose contributions carry operation-count/machine-hour measures (JSONB, §3). This rule prevents taxonomy explosion.
3. **Machine as master data** (a Machine registry; contribution lines referencing machine_id via attributes) — deferred until machine stages are real. No scheduling/capacity engine — out of scope for this platform's horizon (revisit only on demonstrated need).
4. Costing: machine stages choose per_operation/per_hour units via §4's additive path; amortization deferred.

---

## 10) Owner decisions — ALL LOCKED 2026-06-10

| # | Decision | Recommendation |
|---|---|---|
| D-R1.1 | Lock the **archetype map** (§1) + invariants I1-I10 (§0) as the stage-agnostic foundation | LOCK |
| D-R1.2 | Lock the **output-contract rules** (§2): typed-record/snapshot reads only; I3 grain mandatory for piece-producing stages; handler-local handover gates | LOCK |
| D-R1.3 | Lock the **per-archetype contribution patterns** (§3) + JSONB-on-first-consumer | LOCK |
| D-R1.4 | Lock **costing-unit extensibility + cost≠earning separation** (§4) | LOCK |
| D-R1.5 | Lock the **traceability ladder + piece-truth-begins-at-identification** (§5) + incident anchor duality (§6.1/§7.1) | LOCK |
| D-R1.6 | Lock **rework-is-normal-work** (§7.3 — AlterCase links ordinary tasks; no parallel labor pipeline) | LOCK |
| D-R1.7 | Settle **P4.2 D3+D2** (§8): barcode models stay in tracking; tracking below production → **P4.2 unparked** | LOCK |
| D-R1.8 | Confirm **machine sub-stage trigger rule + parent-FK shape** (§9) | LOCK |
| D-R1.9 | Lock the **formal nine-field Stage Contract** (§2A) as the stable foundation beneath any future taxonomy (archetype defaults table = the template) | LOCK |
| D-R1.10 | Lock **expected-piece vs identified-piece truth separation** (§5A — Missing/Alter and money never depend on barcode existence) + the **barcode integration seam** (§8A — scanning = data-driven stage capability, not an archetype; lifecycle deferred to a future Barcode/Traceability review) | LOCK |
| — | Stage NAMES / final taxonomy / which stages split or merge / whether identification stays a visible stage / concrete Missing+Alter models / barcode lifecycle, genealogy, scan rules | **EXPLICITLY DEFERRED** (by owner instruction + by design — these decisions now have fixed shapes to land in) |

**After R1 closes:** roadmap resumes P2 (pt.2b/2c worker report UI — schema-driven, now archetype-validated) → P3 (V2-1d, preconditions locked) → P4 (V2-2 per ADR 0007) → P5 (V2-3) → P6 (Missing/Alter modules instantiating §6/§7 contracts). P4.2 schedulable any time after its characterization tests.

**⏹ No UI designed, no code written, no stage names finalized, no barcode lifecycle designed. Owner review requested on D-R1.1…D-R1.10.**
