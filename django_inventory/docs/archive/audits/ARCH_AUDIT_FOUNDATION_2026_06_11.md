> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [ADR-0009](../../adr/0009-cost-truth.md) + [ADR-0010](../../adr/0010-growth-and-identity-policy.md) (its lock-now items became these ADRs + C-1).

# Final Foundation Audit — manufacturing ERP vs the next 3–5 years (2026-06-11)

Owner-requested, post-V2-3, pre-deployment. Architecture only — not code quality.
Locked facts assumed (WST=participation, WSC=production truth, AddaSettlement=
financial closing, ledger=financial truth, settlement-first, ADR-0007/0008,
Tracking Mode, mobile-first, deploy stack). Evidence: multi-agent code audit
(costing area, file:line-grounded) + inline verification of load-bearing
constraints. Optimized for preventing future regret, not positivity.

---

## Part 1 — The ten areas

### 1) MissingPiece module
- **Clean support?** YES. Anchors exist at every grain a case needs: Adda,
  AddaStageRecord, ClothColor, ProductSize FKs all live; expected-piece
  denominators exist (CuttingPieceBreakup per size, CuttingBundle/items per
  color+pattern, WSC sums per color/size); the §11.10 variance seam means
  settlement consumes counts without owning the workflow; R1 §5A guarantees
  barcode-independence.
- **Embedded assumptions:** variance counts at settlement are MANUAL today and
  frozen into AddaSettlementItem; "missing" currently exists ONLY as those
  frozen settlement counts — there is no Adda-level operational record between
  discovery and settlement.
- **Retrofit risks:** LOW overall. One real one (MED): if cases launch AFTER
  months of production, historical "missing" exists only inside frozen
  settlement snapshots — backfillable as known facts, but cases and snapshot
  counts will never reconcile 1:1 for old Addas. Accept and label.
- **Lock NOW:** the case lifecycle principle (already implied by owner rules,
  state it): MissingPieceCase = append-only lifecycle (open→resolved/found/
  written-off), found-later = new lifecycle event, NEVER edits settlement
  snapshots or WSC. Zero schema today.
- **Wait:** the module itself, responsibility attribution (needs barcode for
  identified-piece blame), any auto-deduction policy (factory_absorbs locked).

### 2) Alter/Rework module
- **Clean support?** MOSTLY — with ONE verified structural blocker.
- **Embedded assumption (verified inline):** `WorkerStageTask` has a partial
  unique constraint `(stage_record, worker)` excluding only CANCELLED
  (worker_task.py:75-79). A worker with a COMPLETED task on a stage can NEVER
  get a second task on that stage record. One AddaStageRecord exists per
  (adda, workflow_stage). **Rework round = same worker redoing the same stage
  is unrepresentable.** The architecture assumes each worker passes each stage
  at most once per Adda.
- **Retrofit risks:** HIGH if ignored — Alter/Rework's core flow (piece goes
  back, possibly to the same worker, possibly paid again or not) collides with
  the constraint. Options when the module is designed: (a) AlterCase carries
  its own work records (rework never re-enters WST/WSC — cleanest, keeps
  first-pass production truth pure); (b) add a `round`/`case` dimension to WST
  (constraint swap; cheap migration but pollutes first-pass truth). Settlement
  side is already fine: partial settlements are legal, a second settlement on
  the same Adda can pay rework.
- **Lock NOW:** the DECISION PRINCIPLE only — "first-pass production truth
  (WSC) is never diluted by rework rows; rework work is case-scoped" (direction
  (a)). One paragraph. Cheap now; after the module ships wrong, repairing mixed
  first-pass/rework quantities inside WSC would corrupt every yield report.
- **Wait:** the module, pay policy for rework, alterations workflow UI.

### 3) Material costing (G1) — fleet-audited, file:line grounded
- **Clean support?** Better than expected. ClothRoll.cost_per_kg exists
  (audited edits); consumption grain per (roll, Adda) is enforced — attach
  weight required, per-roll leftover weight MANDATORY at layering completion;
  net consumed kg derivable retroactively. ADR-0008 already locks the margin
  formula consuming it.
- **Embedded assumptions:** material = CLOTH ONLY, entering ONLY at Layering
  (service hard-rejects other stages); one roll → one Adda forever (FK, not
  through-table); valuation unit = kg only (no per-meter price, no GSM
  conversion anywhere).
- **Retrofit risks:**
  - **HIGH — leftover re-consumption is digitally unwritable today.** Fields
    exist (is_consumed, consumed_in_adda) but NO service sets them. Leftovers
    accumulate at every layering completion NOW; every physical reuse is
    off-book and unrecoverable later (violates the backfill-known-facts rule).
  - **HIGH — cost_per_kg is nullable AND mutable with no consumption-time
    snapshot.** The price-at-time-of-order pattern protecting every labor
    number was NOT applied to material. If anyone "updates" a price, history
    silently revalues.
  - MED — no material-costing-era stamp (labor has structural era markers;
    material has none).
- **Lock NOW (all cheap):** (1) cost_per_kg = PURCHASE price semantic, one ADR
  line; (2) require/flag price at roll intake + "unpriced rolls" honest-NULL
  surface; (3) leftover-consumption WRITE semantics (single service,
  whole-piece, valued at source roll's price) even if UI waits; (4) the
  labelability rule — material cost NULL ≠ 0, mirror of processing_cost.
- **Wait:** AddaMaterialCost snapshot tables, per_meter cost methods, non-cloth
  materials (label reports "cloth cost" honestly), leftover-reuse UI.

### 4) Adda-360 (G4)
- **Clean support?** YES — proven by construction: section 3 of the post-V2-2
  reassessment composed the full story read-only from existing data. AddaHistory
  (JSON metadata) renders a timeline; WST carries started/completed/verified
  timestamps; settlement chain + ledger provenance all reachable via FKs.
- **Embedded assumptions:** timeline queries are per-Adda (indexed adequately);
  metadata stays display-grade JSON (fine until someone wants to FILTER on it).
- **Retrofit risks:** LOW. Worst case: JSON metadata promotion to columns if
  filtered reporting is ever needed — additive.
- **Lock NOW:** nothing schema. Build the thin slice EARLY (already locked L6)
  so the page becomes the soak instrument.
- **Wait:** full G4 polish, cross-Adda comparative dashboards.

### 5) Finished-goods inventory (G5)
- **Clean support?** Seam is clean BECAUSE nothing pretends to be inventory.
  Birth-grain candidates all exist: WSC totals per (color, size), bundles,
  BarcodeBatch ranges per (adda, color, size). No model holds sellable stock;
  no price exists anywhere in production models (correct).
- **Embedded assumptions:** ADR-0008 G5 = the Order↔Adda junction; MTO = MTS
  with zero dwell; finished goods read completion/packing truth.
- **Retrofit risks:** MED, and it is NOT in G5 itself — it is G6: there is no
  SKU/variant concept anywhere. Production identity = (Product, ClothColor,
  ProductSize); storefront identity = free text. FinishedGood must be born
  with an identity commerce can sell — building it on production's triple and
  bolting SKU on later = the classic two-identity trap.
- **Lock NOW:** G6 BEFORE G5 (already owner-locked); plus one decision: the
  future sellable identity is a DEDICATED SKU/variant entity mapping to
  (product, color, size) — never raw FKs from commerce into production tables
  (ADR-0008 boundary in schema form).
- **Wait:** the FinishedGood model itself — until a packing/dispatch stage
  (archetype F) or G5 phase defines the birth event.

### 6) Commerce / Orders
- **Clean support?** The boundary is the cleanest part: revenue appears
  nowhere in manufacturing; no Order model exists, so no premature shape.
  ADR-0008's gap registry is honest.
- **Embedded assumptions:** storefront is marketing-only (verified: 7 models,
  all display config; FeaturedProduct free text, no production FK).
- **Retrofit risks:** MED — the standing temptation: when Orders arrive, an
  Order→Adda FK "just for traceability." The locked route is through G5
  inventory. Second: pricing — if a "price" field ever lands on
  production.Product instead of the commerce side, the boundary dies quietly.
- **Lock NOW:** one sentence in ADR-0008's enforcement section: production
  models may NEVER grow price/revenue fields; commerce references manufacturing
  identity only via the G6 SKU entity. (Make the import-linter contract cover
  storefront→production model imports when commerce work starts.)
- **Wait:** orders, carts, payments, channel pricing — all of it.

### 7) Multi-factory growth
- **Clean support?** NO — and that is the honest, correct state for a
  single-factory business. Verified global assumptions: Adda.code globally
  unique; ADST-XXXX one global sequence under one global advisory-lock key
  (5374); SETL refs global; roll IDs one sequence; one User table (workers/
  skills/roles global — fine, people move between sites); StorageLocation has
  no site dimension; settlement queue scans ALL Addas; RBAC principal cache
  keyed per user globally; single Postgres/Redis.
- **Embedded assumptions:** exactly one operational tempo. None of this is
  wrong today; all of it becomes a coordinated migration if factory #2 arrives
  unplanned.
- **Retrofit risks:** HIGH **only under one specific failure mode**: the fork
  — standing up a second deployment for factory #2. Two databases = two ledgers
  = consolidation becomes ETL forever, and reference collisions (ADST-0042
  twice) poison any later merge. In-schema retrofit (a `site` FK on Adda +
  scoped queues) is a MEDIUM, bounded migration — IF references stayed
  globally unique.
- **Lock NOW (policy only, zero schema):** (1) **references are globally
  unique forever** — a second factory gets the SAME sequences, never its own
  ADST-0001; (2) **multi-factory = one database, a site dimension on Adda**,
  never a second deployment. Two sentences in an ADR. That converts a
  potential rewrite into a bounded future migration.
- **Wait:** the site field itself, per-site RBAC, per-site queues — until a
  second factory is real.

### 8) Barcode traceability
- **Clean support?** The seam is genuinely good. Verified: BarcodeBatch =
  contiguous sequence RANGE per (adda, color, size) with start_seq/end_seq +
  range indexes — meaning **per-piece identity is already DERIVABLE: (adda,
  seq) resolves to exactly one (color, size, bundle) without any Piece table
  existing.** Tracking references production via string FKs (dependency-clean,
  R1 I8 holds). C-TM convergence locks scan-derived lines into the same WSC
  chokepoint; the F1 `attributes` JSONB escape hatch covers scan extras.
- **Embedded assumptions:** identity is issued at the barcode_generation stage
  (archetype E), batch-granular; no scan-event model yet (correct — deferred).
- **Retrofit risks:** MED — exactly one: if the future Barcode review invents
  a NEW per-piece numbering scheme instead of materializing pieces FROM the
  existing (adda, seq) ranges, the printed history (physical garments already
  carrying today's barcodes) orphans. Physical labels are the one thing no
  migration can rewrite.
- **Lock NOW:** payload/derivability rule — **the printed barcode payload is
  permanent: piece identity = (adda, seq); any future Piece model must be
  born FROM existing ranges, never renumbered.** One ADR line.
- **Wait:** Piece model, ScanEvent model, TM-2 modes, H3 hybrid reconciliation,
  H5 scanner attribution — all inside the dedicated Barcode/Traceability review.

### 9) Worker performance analytics
- **Clean support?** YES for the data, MOSTLY for the queries. Production
  truth (WSC) + participation (WST with started/completed/verified stamps) +
  verified-vs-reported deltas (quality signal) + earnings ladder all exist.
  V2-3 PR-C already repointed productivity to production truth.
- **Embedded assumptions (verified):** there is NO "work date" distinct from
  row timestamps — analytics will use task completed_at as the work-date
  proxy; late reporting skews daily stats. WST indexes are (stage_record) and
  (worker, status) — time-windowed worker queries will eventually want
  (worker, completed_at).
- **Retrofit risks:** LOW. Indexes are additive any day. The work-date proxy
  is the only semantic gap; if real backdating is ever needed, an additive
  nullable `work_date` on WSC follows the entry_date precedent in the ledger.
- **Lock NOW:** nothing schema. One sentence: "completed_at is the work-date
  proxy until a real need shows" — so reports label it honestly.
- **Wait:** materialized views, reporting schema, any aggregation infra —
  cliffs start far beyond one factory's volume (~50k contributions/yr is fine
  on indexed SUM/GROUP BY).

### 10) Full manufacturing-cost visibility per Adda — fleet-audited
- **Clean support?** All three components have homes or seams: actual labor
  (settled SWA/ledger, both eras), standard processing cost (frozen
  per-stage), material (derivable per §3). BUT —
- **THE COST DUALITY (CRITICAL, undeclared):** `processing_cost` (ws.cost_rate
  × handler quantity, role-independent) and settled worker earnings
  (verified-else-reported × role-aware rate) are **two measurements of the
  SAME money** for payable stages — standard cost vs actual pay. They diverge
  legitimately (role rates, quantity basis, non-payable coverage, grouping),
  and the costing dashboard already shows them side by side. Nothing anywhere
  states "never add them." The first full-cost report that sums material +
  processing_cost + settled labor double-counts labor — an owner-facing money
  error that becomes politically locked once it drives pricing.
- **Verified consequences:**
  - ADR-0008's LOCKED margin formula ("settled labor + material + variance")
    OMITS processing_cost of non-payable priced stages (outsourced/machine
    work) — implemented literally, margins overstate profit. The ADR needs a
    clause, cheaper now than after reports ship.
  - **Grouped-member role-rate leak (HIGH, real double-pay):** role rates
    survive cost-grouping untouched and the expected-rate freeze never checks
    cost_billed_at — a WorkflowStageRoleRate on a grouped member with
    credits_workers=True freezes a nonzero rate, settlement pays the member's
    workers WHILE the payer stage's grouped rate already covers them. Era-A
    allocation refuses grouped stages; the settlement path has NO equivalent
    guard. Append-only consequences.
  - No quantity reconciliation between the two truths (workers reporting
    1,200 pcs on a 1,000-pc stage is paid silently; verified_quantity is the
    lever but nothing demands it) — the future standard-vs-actual variance
    report is the declared home; name it so ad-hoc checks don't sprout.
- **Lock NOW:** (1) the duality declaration + "full Adda cost = material +
  ACTUAL settled labor + processing_cost of NON-payable stages only + future
  overhead; standard-vs-actual = variance report, never a sum" — ADR
  paragraph; (2) ADR-0008 margin clause amendment; (3) **the grouped-member
  guard (2-line code fix + test — this is PR-A-family money armor and should
  ship pre-deploy)**; (4) labor-source rule: per-Adda actual labor = Σ
  non-voided SWA snapshots (both eras), never WSC.expected_*, never Σ
  settlement totals.
- **Wait:** overhead modeling (no seam needed yet, but stamp the era when it
  arrives), stored full-cost columns (derived-never-stored is locked), the
  variance report itself, splitting cost_rate into standard-vs-pay fields.

---

## Part 2 — Rollups

### A. Top 10 architectural strengths
1. Append-only financial truth with single-writer enforcement in CI (gates
   4/4b/4c) — the property everything else leans on.
2. Production truth ≠ financial truth, joined only at an explicit closing
   event with frozen approval snapshots — the hardest ERP separation, done.
3. Corrections as first-class events (reverse/supersede chains) — "fix
   yesterday without editing it" works for money today and generalizes to
   Missing/Alter.
4. Open-closed stage engine with declared capability vs per-product policy
   (contribution_schema / WorkflowStage) — new stages and Tracking Mode are
   data, not code.
5. Honest-NULL discipline (unpriced ≠ zero) — already saving the costing
   domain from silent lies; extensible to material.
6. Era markers are structural, not inferential (SWA.adda_settlement,
   settlement_line provenance, frozen *_at stamps).
7. The variance seam (§11.10): settlement consumes counts, never owns
   workflows — Missing/Alter/barcode can evolve without touching money code.
8. Material consumption captured at valuable grain BEFORE costing exists
   (roll↔Adda binding, mandatory weights, leftover provenance).
9. Barcode identity derivable from ranges — per-piece traceability possible
   without a piece table or a renumbering event.
10. ADR + gap-registry discipline — G1-G7 are named debts with owners, not
    surprises; locked decisions are written where the next developer reads.

### B. Top 10 remaining architectural risks (ranked)
1. **CRITICAL — undeclared cost duality** (§10): first full-cost report
   double-counts labor.
2. **HIGH — grouped-member role-rate leak**: real double-pay through the
   settlement path, append-only consequences.
3. **HIGH — leftover re-consumption unwritable**: consumption history being
   lost NOW, unbackfillable by owner's own rule.
4. **HIGH — cost_per_kg mutable/nullable, no consumption snapshot**: material
   history revalues silently; coverage decays roll by roll.
5. **HIGH — multi-factory fork temptation**: a second deployment would split
   the ledger forever; preventable with a two-sentence policy.
6. **MED — ADR-0008 margin formula omits non-payable processing cost**:
   locked formula, wrong when implemented literally.
7. **MED — rework round blocked by WST uniqueness**: Alter/Rework design must
   decide case-scoped work records first or it will dilute WSC truth.
8. **MED — no SKU/variant identity**: G5/commerce on raw production triples =
   the two-identity trap; G6 ordering already locked, identity decision isn't.
9. **MED — barcode payload permanence unstated**: a renumbering "clean start"
   in the future barcode module would orphan printed garments.
10. **MED — zero production usage** (carried risk): every invariant above is
    developer-proven, none factory-proven; soak still dominates.

### C. Domains still under-designed
- **Overhead** — no concept, no seam, no allocation basis. Fine to wait;
  NOT fine to ship Costing-2 reports without declaring its absence and era.
- **Non-cloth materials** (trims/thread/packaging/dyes) — structurally out of
  scope of G1; reports must say "cloth cost" until modeled.
- **Sellable identity (SKU/variant)** — the G6 gap is named but the entity
  shape is undesigned; it is the keystone of G5/G2.
- **Rework rounds** — one paragraph of design (case-scoped work) missing.
- **Period/fiscal boundaries** — ledger has entry_date and in-period netting;
  no period-close concept. Acceptable for years; named so reports don't invent
  ad-hoc month logic.
- **Data retention/archival** — append-only forever is the right default; no
  policy exists for what "forever" means operationally (dump sizes, history
  table growth). Deploy-era concern, not schema.

### D. Future requirements that would force painful rewrites (if unguarded)
1. A full-cost/pricing report built on processing_cost + settled labor
   (prevent: duality declaration NOW).
2. Factory #2 as a second deployment (prevent: one-DB/site-dimension policy
   NOW).
3. Commerce pricing fields creeping onto production.Product (prevent:
   ADR-0008 enforcement line + future import contract).
4. A new piece-numbering scheme in the barcode module (prevent: payload
   permanence lock NOW).
5. Rework rows mixed into first-pass WSC (prevent: case-scoped principle NOW).
6. Off-book leftover reuse and unpriced rolls for another year (prevent:
   intake rule + write-service NOW — this one is losing data TODAY).

### E. Recommended roadmap order after V2-3
1. **C-1 "money-truth hardening" micro-PR (pre-deploy, ~half session):**
   grouped-member settlement guard + cost-duality ADR paragraph + ADR-0008
   margin clause + cost_per_kg intake flag + leftover-consumption service stub
   + the five one-line policy locks (references-global, one-DB multi-factory,
   barcode payload permanence, rework case-scoping, labor-source rule).
   Everything in it is either a 2-line guard or a paragraph.
2. **Deploy + true soak** (the binding gate; G4 thin slice ships WITH it as
   the soak instrument — locked L6).
3. **MissingPiece** (+TM-1 tracking-mode config as companion).
4. **Alter/Rework** (design opens with the rework-round decision).
5. **G1 Costing-2** (material rollup + costing-era stamp + variance report
   home) → **G3** variance valuation.
6. **G6 product master/SKU** → **G5 finished goods** → **G2 revenue/orders**.
7. **Reporting (full)** → **G7 planning** → Barcode/Traceability review (TM-2)
   whenever traceability pain or commerce demands it.

---

## Part 3 — The 3–5 year regret question

**"If this ERP runs successfully for 3–5 years and grows into manufacturing +
inventory + commerce, what will we most likely regret — and what can still be
prevented today?"**

The regrets will NOT be the ones this project already armored against. Money
provenance, correction lifecycles, era coexistence, stage extensibility —
those are solved better than most commercial ERPs. The likely regrets, in
order of probability × pain:

1. **"Our cost numbers were subtly wrong for two years."** The cost duality is
   undeclared, the margin formula has a hole, and the grouped-member leak can
   double-pay through the append-only ledger. Wrong money that LOOKS precise
   is the worst ERP failure mode because it drives pricing, wages, and trust.
   **Fully preventable today** — one guard, two ADR paragraphs (C-1).
2. **"We can't reconstruct material history."** Leftovers are being created
   mandatorily and reused physically with no digital write path; rolls enter
   unpriced. Unlike every other regret, this one is **destroying data right
   now** — each off-book reuse is unrecoverable under your own
   backfill-known-facts rule. **Preventable today**, and only today.
3. **"Factory #2 split our books."** If growth arrives as a cloned deployment,
   the ledger — the system's crown jewel — becomes two ledgers, and no future
   migration can unsplit ADST-0042 existing twice. **Preventable with two
   sentences of policy** locked before anyone is in a hurry.
4. **"We sell things the factory can't recognize."** The SKU gap. Commerce
   built on free text or raw production triples means every order needs a
   human translator. Already mitigated by the locked G6-first ordering;
   finish it by locking the SKU-entity decision.
5. **"We renumbered the pieces."** Thousands of garments will physically carry
   today's (adda, seq) barcodes. Any future module that mints new identity
   instead of deriving from ranges orphans the physical world. **Preventable
   with one ADR line.**
6. **"Rework polluted our production truth."** Yield, productivity, and
   missing-piece math all assume WSC = first-pass truth. One wrong modeling
   decision in the Alter module breaks three other domains. **Preventable with
   one design principle locked now.**
7. **What is NOT preventable and must be accepted:** era heterogeneity (era-A
   rows, pre-G1 material-blind Addas, pre-overhead costing) — permanent,
   correctly handled by labeling, never by rewriting; the Django-monolith
   ceiling — irrelevant at factory scale for this horizon; and the
   single-brain risk — the owner is the architecture's only fluent reader,
   which docs mitigate but only succession planning solves.

Everything in regrets 1–6 fits in the C-1 micro-PR plus existing locked
ordering. The architecture has no rewrite-class flaw left; what remains is a
short list of cheap declarations whose price never gets lower than today.
