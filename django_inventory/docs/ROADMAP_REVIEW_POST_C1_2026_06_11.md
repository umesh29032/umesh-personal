# Roadmap Execution Review — post V2-3 + C-1, pre-deployment (2026-06-11)

Owner-requested roadmap-level review. No design, no implementation. Inputs:
locked ADRs 0005–0010, Tracking-Mode requirement lock (D-T1..T5, C-TM),
foundation audit (ARCH_AUDIT_FOUNDATION), V2-3 + C-1 shipped state.
Question to answer: what builds BEFORE deployment, what waits for real-worker
soak, and whether the locked order still holds.

**Headline: nothing remains to build before deployment. C-1 was the last
pre-deploy item. Every remaining phase is safer built AFTER real workers are
on the system — two small exceptions ride ALONGSIDE the soak (G4 thin slice,
TM-1), not before it.**

---

## Phase-by-phase (10 points each)

### MissingPiece
1. **Problem:** pieces vanish between stages; today "missing" exists only as a
   manually-typed frozen count at settlement — no lifecycle, no found-later
   recovery, no per-Adda operational record, no accountability trail.
2. **Data exists:** expected denominators (CuttingPieceBreakup per size,
   bundles per color/pattern, WSC per color/size), frozen variance counts on
   settlement items, AddaHistory timeline, factory_absorbs policy, §11.10
   source-agnostic seam.
3. **New expected:** `MissingPieceCase` (adda, optional stage_record,
   color/size grain, qty, lifecycle open→found/written-off, actor stamps) +
   single-writer case service + history events + settlement-draft pre-fill of
   variance counts from open cases.
4. **Dependencies:** V2-2/V2-3 ✓. Barcode NOT required (§5A locked). No hard
   dep on TM-1.
5. **Screens:** case list + open/resolve (management), per-Adda missing panel,
   settlement-draft pre-fill.
6. **Mobile-worker impact:** none directly (management files cases at launch).
7. **Owner/manager impact:** "where are the 10 pieces" finally answerable;
   recovery tracked as events, not edits.
8. **Cost/settlement impact:** feeds variance counts through the locked seam;
   pay never auto-deducted (factory_absorbs); G3 will value the counts later.
9. **Architecture risk:** LOW-MED — append-only lifecycle, zero money writes;
   the only care point is the settlement pre-fill staying read-suggest, not
   write-coupled.
10. **Order:** first feature phase after deploy + TM-1.

### TM-1 (Tracking Mode: Manual/None)
1. **Problem:** every assigned worker on every stage gets a report task; on
   no-report stages (layering optional, cutting_pattern) completion
   auto-cancels them — roster falsely reads "did not participate" (H1), and
   the owner cannot configure reporting per product flow.
2. **Data exists:** policy home reserved on WorkflowStage (R1 §2A), handler
   capability live (contribution_schema), D-T2/D-T3 decisions locked.
3. **New expected:** ONE additive field (enum or two axes — D-T1 decided at
   build) + flow-editor dropdown + `resolve_stage_tasks_on_complete` change
   (participated-without-report) + two validations (credits_workers ⇒ mode ≠
   none; block mid-flight change). One small additive migration — the only
   migration anywhere in the next two phases.
4. **Dependencies:** none. TM-2 (Barcode/Both) explicitly excluded (D-T4).
5. **Screens:** flow editor extension (management, desktop/tablet); worker
   report screen simply absent for none-mode stages.
6. **Mobile-worker impact:** fewer pointless report prompts; honest dashboard
   badges; lower friction during soak.
7. **Owner/manager impact:** per-product reporting policy without code.
8. **Cost/settlement impact:** none on money paths; H2 validation protects
   payable stages from none-mode.
9. **Architecture risk:** LOW — every decision pre-locked.
10. **Order:** immediately after deploy, alongside early soak — it directly
    removes soak noise (auto-cancel roster pollution) before it accumulates.

### Alter/Rework
1. **Problem:** rejected/alter pieces have no flow — who fixes them, was it
   fixed, does the fixer get paid.
2. **Data exists:** alter/rejected variance counts reserved on settlement
   items; ADR-0010 §4 case-scoping LOCKED; WST uniqueness intentional.
3. **New expected:** `AlterCase` + case-scoped work records (NEVER second
   WST/WSC rows on the original stage — locked), case service, history
   events; optional rework pay as additional settlement lines reading case
   records.
4. **Dependencies:** MissingPiece (shares the case-lifecycle family and UI
   patterns); settlement seam ✓.
5. **Screens:** case board, assign-fix flow, resolution.
6. **Mobile-worker impact:** rework assignments visible/actionable on phone.
7. **Owner/manager impact:** rework cost + quality visibility per Adda/worker.
8. **Cost/settlement impact:** the one open design decision — whether/how
   rework pays (extra settlement on case records vs unpaid). First-pass
   truth untouched by construction.
9. **Architecture risk:** MED — the only phase introducing a parallel
   work-record type; the ADR-0010 fence is exactly why it was locked early.
10. **Order:** after MissingPiece.

### G4 Adda-360
1. **Problem:** one Adda's story spans 4+ screens; the owner's §10 goal
   (production/operations/financial in one view, truths separated) unmet.
2. **Data exists:** ALL of it — proven by composition in the post-V2-2
   reassessment. Zero schema gaps.
3. **New expected:** one read-model service + one page. No models.
4. **Dependencies:** none. Buildable today.
5. **Screens:** the Adda-360 page (timeline, stage grid, contributions,
   settlement chain, money panel with era labels).
6. **Mobile-worker impact:** none (management page) — still rule-11
   responsive.
7. **Owner/manager impact:** the flagship visibility win; THE soak instrument
   — owner watches real Addas live during soak.
8. **Cost/settlement impact:** read-only; MUST follow ADR-0009 (labor-source
   rule, never-add duality) — first consumer of the new ADR.
9. **Architecture risk:** LOW — read-only; only failure mode is violating
   0009, which is why 0009 exists.
10. **Order:** thin slice DURING soak (locked L6); polish later.

### G1 Material Costing
1. **Problem:** Adda cost = labor only; cloth — the biggest input — invisible.
2. **Data exists:** cost_per_kg (purchase-price semantic locked), enforced
   attach weights, mandatory leftover weigh-ins, `consume_leftover` write
   path (C-1), honest-NULL surfaces already on the dashboard.
3. **New expected:** material read-model (derived, never stored), the
   costing-era stamp (ADR date), leftover-reuse UI (mobile-first), intake
   nudges. No schema beyond possibly nothing.
4. **Dependencies:** C-1 ✓. Independent of MissingPiece but reports get more
   honest after it.
5. **Screens:** costing dashboard material column (SEPARATE from labor —
   0009), leftover-reuse flow, unpriced-rolls worklist.
6. **Mobile-worker impact:** leftover weigh-in/reuse on phone at the rack.
7. **Owner/manager impact:** true cloth cost per Adda; supplier comparison;
   the first half of real margins.
8. **Cost/settlement impact:** none on settlement; full-cost assembled per
   the locked 0009 formula.
9. **Architecture risk:** LOW-MED — read-model + one write UI; valuation
   correctness fenced by 0009.
10. **Order:** after Alter/Rework (or overlapping its tail); before G3.

### G3 Variance Valuation
1. **Problem:** missing/rejected counts have no ₹ value — loss is invisible
   in money terms.
2. **Data exists:** variance counts (settlement + future cases), frozen
   expected_rate (labor component), material cost per piece (after G1).
3. **New expected:** valuation read-model + possibly new VariancePolicy
   choices (schema-reserved, additive). Display-only at launch.
4. **Dependencies:** MissingPiece (real counts) + G1 (material component).
5. **Screens:** loss report inside the costing area.
6. **Mobile-worker impact:** none.
7. **Owner/manager impact:** "missing cost us ₹X this month" answerable;
   informed policy decisions.
8. **Cost/settlement impact:** valuation only; pay deduction remains a future
   explicit policy change (factory_absorbs stays default).
9. **Architecture risk:** LOW.
10. **Order:** after G1 + MissingPiece, whichever lands later.

### G6 Product/SKU master
1. **Problem:** two product identities (production master vs storefront free
   text); nothing sellable exists; commerce impossible without one identity.
2. **Data exists:** production triple (Product, ClothColor, ProductSize);
   storefront free text (no FK = nothing to unwind, only to connect).
3. **New expected:** SKU/variant entity mapping (product, color, size) → one
   sellable unit; storefront re-pointed to it; ADR-0010 §5 fence (no raw
   commerce→production FKs).
4. **Dependencies:** none hard; MUST precede G5/G2 (owner-locked).
5. **Screens:** SKU admin + storefront editor re-point.
6. **Mobile-worker impact:** none.
7. **Owner/manager impact:** one catalog truth; future channel pricing home.
8. **Cost/settlement impact:** none.
9. **Architecture risk:** MED — identity decisions ripple through all
   commerce; cheap now precisely because no commerce data exists yet.
10. **Order:** first commerce-side phase, after the factory-side phases.

### G5 Finished Goods Inventory
1. **Problem:** completed Addas vanish into the physical world; no stock
   truth; the locked Order↔Adda junction doesn't exist.
2. **Data exists:** outputs at every candidate grain (WSC per color/size,
   bundles, barcode ranges); G6 SKU (dependency) gives the identity.
3. **New expected:** FinishedGood/stock model + append-only movement records
   (ledger-discipline: single writer, no edits), birth event (packing stage —
   R1 archetype F — or Adda completion), G5 service.
4. **Dependencies:** G6 hard; packing-stage decision; TM-1 makes its
   reporting configurable; TM-2 scan counts optional later.
5. **Screens:** stock dashboard, receipt/adjustment flows.
6. **Mobile-worker impact:** packing counts entered on phone.
7. **Owner/manager impact:** sellable stock truth; output side of margins.
8. **Cost/settlement impact:** stock valuation can consume full-cost (G1),
   era-labeled; no settlement change.
9. **Architecture risk:** MED-HIGH — the first new TRUTH domain since the
   ledger; must replicate the same discipline (single writer, append-only,
   honest-NULL) from birth.
10. **Order:** after G6.

### G2 Orders/Commerce
1. **Problem:** revenue side absent; no order capture, fulfillment, or real
   profitability.
2. **Data exists:** ADR-0008 boundary + gap registry; G5 stock + G6 SKU
   (dependencies).
3. **New expected:** Order/OrderLine, fulfillment-from-stock, revenue records
   (commerce side only), customer basics.
4. **Dependencies:** G5 + G6 hard. Order→Adda FK permanently banned (0008/0010).
5. **Screens:** order entry/board, fulfillment, customer view.
6. **Mobile-worker impact:** none initially (dispatch confirmation later).
7. **Owner/manager impact:** revenue truth; derived margins finally complete
   (output valuation − the 0009 cost formula).
8. **Cost/settlement impact:** zero on manufacturing (the boundary's whole
   point).
9. **Architecture risk:** MED — greenfield domain, but every fence it needs
   is already locked.
10. **Order:** after G5.

### Reporting (full)
1. **Problem:** cross-Adda, cross-period, cross-worker analytics beyond the
   operational dashboards.
2. **Data exists:** everything, append-only with provenance — the hard part
   of reporting was pre-paid; V2-3 PR-C already repointed stats to production
   truth.
3. **New expected:** report read-models; materialized views only if volume
   ever demands.
4. **Dependencies:** after lifecycle modules (variance provenance must be
   real, not typed) and ideally G1 (cost reports).
5. **Screens:** report center (period/worker/product cuts).
6. **Mobile-worker impact:** possible own-history views.
7. **Owner/manager impact:** trends, period summaries, worker analytics.
8. **Cost/settlement impact:** read-only; 0009 rules are the correctness
   fence; era labels mandatory on mixed-regime windows.
9. **Architecture risk:** LOW.
10. **Order:** late, as locked — after the truths it reports on exist.

### G7 Planning/MRP-lite
1. **Problem:** no demand→capacity→material planning; production is reactive.
2. **Data exists:** stage durations (auto), rates, consumption history; stock
   (G5) and demand (G2) once built.
3. **New expected:** plan/draft models (plans are NOT truth — no append-only
   ceremony needed), capacity heuristics.
4. **Dependencies:** G2 + G5 + reporting maturity; real historical data from
   soak onward is its fuel.
5. **Screens:** planning board.
6. **Mobile-worker impact:** none.
7. **Owner/manager impact:** "can we take this order / when / what cloth to
   buy."
8. **Cost/settlement impact:** none.
9. **Architecture risk:** LOW architecturally; HIGH product uncertainty —
   exactly why it is last.
10. **Order:** last.

---

## Reassessment after V2-3 + C-1

**Does the locked order change? One promotion, zero reorderings.**

- **TM-1 is promoted** from "candidate alongside MissingPiece" to an explicit
  slot immediately after deploy. Reason discovered in the Tracking-Mode review
  (H1): during soak, every no-report stage completion auto-cancels roster
  tasks, polluting participation truth daily. TM-1 is the cheapest phase on
  the board (one additive field + a chokepoint tweak, all decisions
  pre-locked) and it cleans the data the soak is supposed to produce.
- **G4 thin slice formally rides the soak** (was already L6) — it is the
  instrument the owner watches the soak THROUGH, and the first consumer of
  ADR-0009's read rules.
- Everything else: order unchanged and re-validated. MissingPiece before
  Alter (counts before rework), G1 before G3 (valuation needs material),
  G6 before G5 before G2 (identity → stock → revenue, owner-locked),
  Reporting after lifecycle modules, G7 last.

**Pre-deploy build list: EMPTY.** C-1 closed the final pre-deploy item (money
truth cannot be silently corrupted by reports, grouping, or material drift).
Building anything more before deployment inverts the risk ranking — the #1
standing risk is zero production usage, and every pre-soak feature adds
surface the soak must then validate.

**Post-deploy sequence (locked, with soak gates):**
```
DEPLOY ──► soak starts (current worker flow, settlement-first default)
  ├─ alongside: G4 thin slice (read-only soak instrument)
  ├─ week 1-2:  TM-1 (kills auto-cancel roster noise)
  ├─ then:      MissingPiece → Alter/Rework
  ├─ then:      G1 → G3
  ├─ soak gate: ADR-0007 deletion PR (lever + era-A path removed)
  ├─ commerce:  G6 → G5 → G2
  └─ tail:      Reporting (full) → G7
```
Soak evidence feeds two explicit gates: the ADR-0007 deletion PR (real workers
settled successfully) and the MissingPiece variance pre-fill (real variance
patterns observed before automating their entry).

**Money-touching changes (MissingPiece pre-fill, Alter pay, G1 valuation in
reports) all land AFTER the soak proves settlement-first with real workers —
none before.**
