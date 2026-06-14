# S4 Design Correction Addendum (2026-06-14)

Resolves the blockers from the [M-1…M-4 re-review](M1_M4_REVIEW_2026_06_14.md) **before**
any S4 code. Extends [PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md) — where they
conflict, THIS doc wins for S4. **Design + decision record only. No models, no migrations,
no implementation plan, no code.** Entities below are described by responsibility /
lifecycle / relationships, not by field DDL.

---

## C1 — `AddaProductSizeColorPieceBreakdown` (APSCPB) has live barcode consumers

**Fact (verified).** APSCPB is Cutting-specific (FK `cutting_record`, CASCADE), written by
`cutting/service` (`get_or_create` per `(size,color)`), and **read at runtime** by
`barcode_generation/assembly.generate_from_breakdown` (BarcodeBatch ranges) +
`preview_barcode_counts`. The PRE_S1 addendum's "dead snapshot, 0 consumers, generalize it"
premise is **false**.

### Decision: `StagePoolSnapshot` is a COMPLETELY NEW table. APSCPB is left untouched.
**Recommendation + rationale:**
- **Different purpose.** APSCPB answers "what cut pieces exist per (size,color) so barcode
  ranges can be generated." `StagePoolSnapshot` answers "how much good is available to
  allocate to the next stage's workers, at that stage's grain." Merging two purposes into
  one table couples barcode generation to allocation — a coupling we'd spend later sprints
  regretting.
- **Different anchor.** APSCPB is keyed to `cutting_record` (a Cutting-only artifact);
  `StagePoolSnapshot` must be keyed to `AddaStageRecord` (every stage). Not the same row.
- **Zero blast radius.** Leaving the live, shipped, tested barcode path alone = zero
  regression risk. "Generalize the snapshot" trades real regression risk for a DRY win that
  isn't even true (the two snapshots hold different things).
- **They coexist as siblings at Cutting.** At the Cutting stage, `StagePoolSnapshot.good`
  per `(color,size)` is derivable from the same `WorkerStageContribution.good` that APSCPB's
  pieces are cut from — but the pool reads **contribution good**, not APSCPB (see D3). No
  dependency between the two tables.
- **No barcode migration.** Explicitly out of scope. If a true unification is ever wanted,
  it is a separate, independently-reviewed refactor — never a precondition for S4.

---

## C2 — `WorkerStageAllocation` (WSA) as production-truth; relationship to `StageWorkAssignment` (SWA)

**Fact (verified).** SWA is the **settlement earning line** — born at **finalize**
(settlement-first), carries money (`earning_rate_snapshot`, `earning_amount_snapshot`,
`adda_settlement` FK). `allocate_stage_work` **refuses** under the live default
`LEDGER_CREDIT_AT_ALLOCATION=False`. So **no allocation row exists before settlement** —
M-2's pool draw-down "at complete" had nothing to draw into.

### Decision: `WorkerStageAllocation` is a NEW production-truth entity, distinct from SWA.
**It carries NO money.** It records *who is allocated how much of a stage's available work,
at the stage's grain* — a capacity/assignment fact, not an earning. It lives in the
**production** app (alongside `WorkerStageContribution` + `StagePoolSnapshot`); expense
never gains a new writer. This preserves settlement-first (no money/ledger until finalize)
and the production-truth↔settlement separation.

### Lifecycle (creation → settlement)
1. **Allocate** (manager action; Strict model — Open deferred). Manager allocates a worker a
   slice of a stage's *available* pool → a WSA row is created → `StagePoolSnapshot.available`
   for those `(color,size)` dims **draws down** (under the D2 lock). Pre-work. No money.
2. **Report.** Worker submits `WorkerStageContribution` (good/alter/missing). Soft over-
   allocation **warning** at draft; the **hard** bound `Σ(good+alter+missing) ≤ Σ allocated`
   for that `(worker, dims)` is enforced at **complete** (the crystallization point — PRE_S1
   M decision, unchanged).
3. **Complete.** Contribution good/alter/missing crystallize, bounded by the worker's WSA.
   The pool draw-down already happened at allocate; complete only validates the bound.
4. **Reallocate / correct** (production-truth correction). Never edit/hard-delete: **void**
   the WSA (`voided_at`), which **credits the pool back** (`available += voided allocation`),
   then create a fresh WSA. Append-only, audited (owner data-history rule).
5. **Settlement (finalize).** Unchanged from today: `adda_settlement_service` creates the
   SWA earning line from the contribution's `settlement_quantity` (= good) × frozen rate.
   WSA is the **production provenance** that bounded the good; SWA is its **money
   realization**.
6. **Reverse settlement.** Voids the SWA (existing armor). The WSA (production allocation) is
   **untouched** — it is production truth, not money. Re-settlement re-derives a new SWA from
   the same (still-valid) good.

### WSA ↔ SWA — the two are different concerns
| | `WorkerStageAllocation` (NEW, S4) | `StageWorkAssignment` (existing) |
|---|---|---|
| Concern | production-truth: capacity / bound / pool draw-down | settlement: the earning line (money) |
| App | production | expense |
| Born at | **allocate** (pre-work, pre-settlement) | **finalize** (settlement) |
| Carries money | **No** | Yes (rate × qty snapshots, ledger credit) |
| Grain | stage's `allocation_dimensions` (color/size or quantity) | per worker (its own size/color/bundle copy) |
| Correction | void → pool credit → re-allocate | void → reverse/supersede settlement |
| Relationship | bounds the good that → feeds → the SWA at finalize | realized from the bounded good |

This **retires** the dead era-A `allocate_stage_work`-writes-SWA concept (the
`LEDGER_CREDIT_AT_ALLOCATION` path, soak-gated for deletion per ADR-0007). Post-S4, SWA is
**purely** the settlement earning line; production allocation is **purely** WSA. The naming
collision flagged as a should-fix is resolved by this clean split.

---

## H1 — Cutting grain: require `color/size`, or support a NULL bucket?

**Fact (verified).** Cutting's `color_id`/`size_id` are `required=False`; the writer does
not enforce them. One Cutting stage can hold both `(Red,M)` and `(NULL,NULL)` rows = mixed
grain at a single stage.

### Option A — require color/size on `color_size`-grain stages (RECOMMENDED)
- A stage declaring `allocation_dimensions = COLOR_SIZE` **requires** both on every
  contribution (enforced in the single-writer `report_contributions`/`save_draft`
  chokepoint; the worker UI already shows the pickers — flip them to required for these
  stages). `QUANTITY`-grain stages keep color/size NULL by declaration.
- **Operational implications:** cutting workers must pick color+size for every line (minor
  added friction; the pickers already exist). Legacy pre-S4 Cutting rows with NULL grain are
  **grandfathered read-tolerantly** (the rule binds new contributions on grain-declared
  stages); an S4 data audit flags any legacy NULL-grain rows on a `COLOR_SIZE` stage for
  manual review (not auto-invented).
- **Why recommended:** M-1's entire premise is "each stage has ONE grain." A NULL bucket
  reintroduces mixed grain → the pool's `filter(color,size)` aggregation + the monotonicity
  check become ambiguous → defeats correct-by-construction. Required grain keeps the pool
  exact.

### Option B — support a `(NULL,NULL)` bucket
- The pool carries a "grain-agnostic" bucket alongside `(color,size)` buckets.
- **Operational implications:** less capture friction, BUT the pool must answer "does a NULL
  allocation satisfy a `(Red,M)` demand?" — there is no non-arbitrary answer. Mixed grain
  propagates downstream; the monotonicity invariant cannot be checked; reconciliation
  (Σ good vs output) becomes per-bucket-ambiguous. This is the exact failure M-1 exists to
  prevent.

**Decision: Option A.** Required `(color,size)` on `COLOR_SIZE` stages, enforced at the
chokepoint; legacy rows grandfathered + audited, never back-invented.

---

## D1 — `allocation_dimensions` + grain monotonicity

- **`allocation_dimensions`** = a per-`WorkflowStage` declaration, enum `{COLOR_SIZE,
  QUANTITY}` (extensible). `COLOR_SIZE` → pool/allocation/contributions tracked per
  `(color,size)`. `QUANTITY` → tracked as a single scalar (color/size NULL).
- **Source + default.** Seeded from the stage's `handler.contribution_schema` (Cutting →
  `COLOR_SIZE`; Layering/Barcode/Pattern → `QUANTITY`), **editable per-product** in the flow
  editor (a product may legitimately track a stage finer or coarser). **Default = `QUANTITY`**
  (the safe coarse grain) for any stage that doesn't declare.
- **Grain monotonicity ("may only coarsen downstream").** Enforced at **flow-edit time**
  (config, before any Adda runs — cheap, declarative). Rule: walking stages in `order`,
  `grain(stage N)` must be **equal-or-coarser** than `grain(stage N−1)`. Concretely
  `COLOR_SIZE → QUANTITY` is allowed (coarsen = aggregate); `QUANTITY → COLOR_SIZE` is
  **rejected** (re-fining would require inventing per-color data). The flow editor refuses to
  save a flow that violates this. Cutting (finest) must be ≥ every downstream stage.
- **Why it matters:** monotonicity guarantees the pool composition (D3) is **always
  definable** — coarsening is summation; you never need to split a scalar back into colors
  (= invented data, the thing the whole foundation forbids).

## D2 — `StagePoolSnapshot` lock predicate (the one M-3 discipline)

- **Keying.** `StagePoolSnapshot` is keyed `(stage_record, [color, size])` at the stage's
  grain (color/size NULL for `QUANTITY` stages).
- **Lock predicate (THE rule):** the allocation draw-down locks the SPS row via
  `select_for_update().get(stage_record_id=<in-memory id>, color=…, size=…)` — it locks the
  **SPS row by its own key** and **NEVER locks `AddaStageRecord`.** The in-memory
  `stage_record_id` is trusted (a stage record's identity is stable within a transaction; the
  SPS row itself is the anchor). This is the addendum's option (a), explicitly **not** option
  (b) "lock the stage record."
- **Why this keeps the two domains disjoint (no deadlock):** the **settlement** domain locks
  `AddaSettlement → AddaStageRecord → WorkerProfile → WorkerAdvance`. The **production-
  allocation** domain locks `WorkerStageTask → AddaStageRoleRate → StagePoolSnapshot →
  WorkerStageAllocation → WorkerStageContribution`. The two share **no row** (SPS ≠
  AddaStageRecord), so neither ever waits on the other. **Finalize never touches SPS/WSA** —
  it reads the already-frozen `good` + `expected_rate` (the bound was applied at complete).
- **Correction to PRE_S1 M-3.** The PRE_S1 addendum listed SPS inside a *single* global lock
  order that included the settlement entities. That conflated two domains. **Corrected:**
  SPS + WSA exist **only** in the production-allocation domain; the settlement order is
  unchanged and contains **no** SPS. There is no single global order — there are two disjoint
  orders that never interleave.
- **Intra-domain multi-row.** When one `complete`/`allocate` touches several `(color,size)`
  SPS rows, lock them in a **deterministic order** (`color_id`, then `size_id`) so two
  concurrent draw-downs on the same stage can't deadlock each other.
- **Missing-row case.** If the SPS row doesn't exist yet (snapshot not materialized), the
  draw-down does not silently create it — allocation against an unmaterialized pool is an
  invariant violation surfaced (the producing stage must have completed + materialized first).

## D3 — coarse-stage "good" source

- **`StagePoolSnapshot.good` = `Σ WorkerStageContribution.good_quantity` at the producing
  stage's grain**, materialized **write-once at that stage's complete** (immutable; reopen
  clears + refreezes per the existing reopen discipline).
  - `COLOR_SIZE` stage: `Σ good` grouped by `(color,size)`.
  - `QUANTITY` stage: `Σ good` as a scalar.
- **NOT `cost_quantity_snapshot`.** `cost_quantity_snapshot` is the **handler output** (e.g.
  `CuttingRecord.pieces_cut`, lay count) = the standard-cost basis (ADR-0009) — a *different*
  number from the workers' summed good. (Their divergence is exactly the B-1 reconciliation
  signal: `cost_quantity_snapshot` vs `Σ good`.) The pool must use the **workers' good** (the
  payable production truth), never the handler number.
- **Pool composition (downstream).** The pool *available to allocate at* stage N is the
  **upstream** producing stage's good, aggregated to N's (never-finer, by D1) grain:
  `available(N, dims) = snapshot(N−1).good[dims] + recovered_alter(N−1, dims) − Σ non-voided
  WSA(N, dims)`. `recovered_alter` / `found_missing` are the stable accessors (PRE_S1 M-7),
  returning **0** until the Rework/Missing modules ship. Coarsening aggregates `snapshot
  (N−1).good` down to N's grain (sum over the finer dims).

---

## Era-A reopen guard contract (must ship WITH `WorkerStageAllocation`)

`reopen_stage_record(stage S)` must **REFUSE** when **any downstream stage of the Adda** has
a live consumer of S's good:
1. a **non-voided `WorkerStageAllocation`** (downstream work was allocated against S's pool), OR
2. a **completed `WorkerStageContribution`** with good/alter/missing (downstream production
   truth exists), OR
3. (future) an **`AlterCase`** on a downstream stage.

- **Why:** reopening S changes S's good → invalidates the `StagePoolSnapshot` that downstream
  allocations drew against → orphans/strands downstream truth. **Reverse-first:** to fix S,
  the operator must first reverse the downstream consumers (void downstream allocations /
  reverse downstream settlements) — explicit, audited — then reopen S.
- **Unify the boundary.** This uses the **same "reverse-first" discipline** already enforced
  by the settled-block in `reopen`, by `set_verified_quantity` (settled-refuse), and by
  `rerate_stage_role` (settled-refuse). A stage is "locked from upstream edits" exactly when a
  downstream consumer exists — allocation OR settlement OR good-alter-missing.
- **Fix the inter-stage inconsistency (M-4-3).** Replace the ad-hoc per-stage
  `downstream_started_guard` with a **uniform** downstream-consumer guard applied to all
  stages.
- **Atomicity of delivery.** Ship conditions (1)+(2)+(3-stub) **together, in the same sprint
  that adds `WorkerStageAllocation`** — do not partially add condition (2) now (avoid a half-
  contract). Until then the current risk is low (nothing consumes the upstream→downstream good
  relationship pre-pool); document the era boundary in `reopen_stage_record`.

---

## Hostile review of THIS corrected design

Adversarial pass on the corrections above (trying to break them):

- **C1 — two snapshots (APSCPB + SPS) = drift risk?** They hold different things (cut-piece
  ranges vs allocatable good) and SPS never reads APSCPB → no shared state to drift. The only
  shared *upstream* is `WorkerStageContribution.good`, which both ultimately derive from — a
  single source. **Holds.**
- **C2 — WSA + SWA = double source of truth for "how much a worker did"?** No: WSA = the
  *bound* (allocated), contribution.good = the *actual*, SWA = the *money*. Three distinct
  facts. The only invariant is `good ≤ allocated` (enforced at complete). Settlement still
  derives money from good, not from WSA → settlement-first intact. **Holds.** Residual: WSA
  voids must credit the pool back atomically with the void (else pool leaks) — a D2-lock
  concern, flagged for the S4 build.
- **C2 — does WSA reintroduce allocation-era money?** No — WSA carries no rate/earning/ledger.
  Money still appears only at finalize. **Holds.**
- **H1 — required color/size breaks legacy?** Grandfathering + audit (not back-invention)
  handles pre-S4 rows; the rule binds new contributions only. Residual: the audit must run on
  the real dump before the chokepoint flips to required (a migration-time check). Flagged.
- **D1 — monotonicity at flow-edit can't see runtime mixed grain.** True — flow-edit enforces
  *declared* grain; H1's required-grain enforcement is what guarantees *runtime* rows match
  the declaration. The two together close it; neither alone does. **Holds only if H1 ships
  with D1** — noted as a hard coupling.
- **D2 — `get()` on a missing SPS row throws.** Intended: allocation against an unmaterialized
  pool is an invariant violation, surfaced loudly, not silently created. **Holds.** Residual:
  the producing-stage-complete materialization must be guaranteed before any downstream
  allocate — an ordering the S4 build must enforce.
- **D2 — trusting in-memory `stage_record_id` without locking SR: race?** The SPS row is the
  lock anchor; SR identity is immutable within the txn; SR deletion is PROTECT-guarded by its
  records. No race that the SPS-row lock doesn't already serialize. **Holds.**
- **D3 — pool uses Σ good, but good can be corrected (verified_quantity / rerate) after
  snapshot freeze.** The snapshot is write-once at complete; later good corrections →
  reconciliation surfaces the variance (the recon evidence, S1.1 H2) and a reopen (reverse-
  first) is the correction path. The pool is **not** silently mutated. **Holds**, consistent
  with reopen contract.
- **Reopen guard — downstream scan cost.** Scanning all downstream stages on every reopen is
  O(stages); Addas have few stages → negligible. **Holds.**

**No new contradictions introduced.** Two hard couplings to honor in the S4 build: **H1 must
ship with D1** (declared grain ⇒ enforced grain), and **producing-stage materialization must
precede downstream allocate** (D2/D3).

## Final decision for S4: **GO**
With this addendum, C1 + C2 are resolved (design-level), H1 is decided, D1/D2/D3 are fully
specified, and the Era-A reopen contract is defined. No remaining contradiction between the
shipped S1+S3 foundation and the S4 design. The two hard couplings (H1⇄D1; materialize-before-
allocate) are **build-time acceptance criteria**, not design gaps. S4 may proceed to its
normal gated implementation (design receipt → approval → code), starting with D1
(`allocation_dimensions` + monotonicity) as the foundation the rest builds on.
