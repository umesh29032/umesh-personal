# Requirement Review — Stage Reporting, Tracking Mode, and Settlement Truth

Status: REVIEW ONLY — no implementation, no redesign. Date: 2026-06-11.
Owner requirement: per-stage configurable reporting (Manual / Barcode / Both /
None) on the Product-Flow screen; worker-reports-own-work; reports = permanent
production truth; settlement = separate financial decision; missing pieces
belong to the Adda; worker visibility restricted during reporting.

Reviewed against: Stage Engine (registry + StageHandler), R1 Stage Contracts
(docs/R1_STAGE_DOMAIN_REVIEW.md, D-R1.1–D-R1.10 locked), WorkerStageTask/
Contribution, AddaSettlement (V2-2), ADR-0007, ADR-0008, G1–G7.

---

## 0) Headline verdict

**No architectural conflict. This requirement is ~90% a business-language
restatement of architecture that is already locked and largely already built.**
The R1 review anticipated almost every clause:

| Owner clause | Already locked as |
|---|---|
| Reporting differs per stage | `StageHandler.contribution_schema(adda)` — live (base = qty-only; Cutting overrides with colour+size) |
| Tracking method per product-flow stage, configurable, no code change | R1 §2A contract: "policy fields = **WorkflowStage** data (cost_method, cost_rate, credits_workers, **future scan_policy §8A**)" |
| Barcode reporting | R1 §8A locked seam: scanning = stage **capability**, not archetype; future additive `WorkflowStage.scan_policy {none, optional, required}` + handler `validate_scan` hook; scan events live in the tracking primitive |
| Manual + barcode must not collide | R1 I8/I9: tracking owns identity + scan history; production owns quantity truth; Missing/Alter read both, never depend on barcode (§5A) |
| Worker reports own work, only where assigned | V2-1c-iv isolation rule, enforced in `worker_report_views._resolve` — skill alone insufficient, task assignment required |
| Report = permanent production truth | WSC append-once at submit; `reported_quantity` never overwritten; management correction = separate `verified_quantity` field (both preserved) |
| Settlement never modifies production truth | `finalize_adda_settlement` READS contributions; its only WSC write is the `settlement_line` provenance stamp (metadata, not truth) — verified in code |
| Missing pieces belong to Adda; no auto-deduction | `factory_absorbs` policy (locked); §11.10 source-agnostic variance seam; MissingPieceCase = roadmapped module; "found later → added back" = future case lifecycle |
| Owner opens any Adda and sees both truths separately | = the G4 Adda-360 requirement statement, verbatim |

What is genuinely NEW in this requirement: **(a)** an owner-facing Tracking
Mode selector on the flow editor, **(b)** the "None" reporting mode as an
explicit configuration, **(c)** the worker-visibility rule stated as policy.
All three fit existing seams; none requires redesign.

---

## 1) Architectural conflicts found

**None hard. One real tension:**

**T1 — §5 visibility vs the stage workspace.** The worker REPORT screen is
already clean: `_resolve` hands the template only the worker's own task, own
saved lines, own total — no previous-stage quantities, no targets (verified in
worker_report_views.py:130-180). BUT stage workspaces (e.g. cutting) are
gated skill∧assignment, and an assigned helper who opens the cutting workspace
sees the piece breakup — i.e. planned per-colour/size quantities they could
copy into their report. Nuance: for the cutting MASTER that breakup is the
work instruction (they cannot do the job without it); the leak only concerns
non-master helpers assigned to the same stage. This is an access-granularity
question (same family as parked F7: assignable pool / role granularity), not a
schema problem. **Disposition: record as policy decision D-T5 (below); do not
redesign now.**

## 2) Hidden future problems (named now, so they cannot ambush later)

| # | Problem | Disposition |
|---|---|---|
| H1 | **None-mode × F3/F8 auto-cancel.** Today every assigned worker gets a task; stage completion auto-cancels unreported tasks. Under tracking_mode=none, ALL roster tasks would auto-cancel — the roster would falsely read "did not participate" (contradicts the owner's locked "roster = workers who actually participated"). None-mode stages need tasks resolved as participation-without-report (e.g. complete-without-contributions), not cancelled. | Must be solved in the Tracking-Mode build; small chokepoint change in `resolve_stage_tasks_on_complete` |
| H2 | **None-mode × credits_workers=True is incoherent.** A payable stage with no reporting produces no production truth → settlement finds nothing to settle. | Validation rule at flow-editor save: `credits_workers ⇒ tracking_mode ≠ none`. (A future flat-rate earning basis would be a new, separate decision.) |
| H3 | **Hybrid double-count.** Manual lines + scan-derived lines for the same pieces would double production truth. A reconciliation rule (scan-authoritative for scanned dimensions? manual blocked where scans exist?) is undefined. | Defer to the Barcode/Traceability review (R1 already deferred scan lifecycle there). Named here so "Both" mode does not ship without it |
| H4 | **Mid-flight mode change.** The flow editor edits WorkflowStage live; flipping tracking_mode while an Adda is mid-stage could orphan draft reports or suddenly demand scans. | Guard at save (block change while in-flight stage records exist), same family as the PR-3 costing guards |
| H5 | **Scan attribution.** Barcode-derived contributions must attribute to the scanning worker's TASK (assignment truth) — requires scanner identity (login/device). | Barcode review scope; the seam (scan event → derive lines → `report_contributions` chokepoint) already supports it |
| H6 | **"Packed count" has no home yet.** The owner's 1000-reported/990-packed example: today the packed side exists only as manual variance entry at settlement. The true source arrives with a packing/dispatch stage (R1 archetype F) feeding the same §11.10 seam. | Already-known gap; no new risk |

## 3) Q3 — Where does Tracking Mode belong?

**On `WorkflowStage` — i.e. exactly the Product-Flow editor screen the owner
named (`ProductFlowEditView` + product_flow.html), and R1 already reserved the
spot:** "policy fields = WorkflowStage data (… future scan_policy §8A)". The
owner's per-product examples (Product A Cutting=Manual, Product B
Cutting=Barcode) confirm it is per-product policy, NOT a Stage-library or
handler property.

Division of labor (honors the locked R1 contract):
- **Handler declares CAPABILITY** (open-closed): what fields are manually
  reportable (`contribution_schema`), whether the stage can consume scans
  (future `validate_scan`).
- **WorkflowStage stores POLICY**: the owner's choice among the modes the
  handler supports.
- **Flow editor validates** policy against capability (can't pick Barcode on a
  stage whose handler has no scan support; can't pick None on a payable stage — H2).

Recommended storage shape (decision D-T1 below): the owner-facing dropdown is
ONE field ("Tracking Mode: Manual / Barcode / Both / None"), and it maps onto
the R1-locked axes — manual entry (on/off) × scan_policy (none/optional/
required). Manual = entry-on + scan none · Barcode = entry-off + scan required
(quantities derived) · Both = entry-on + scan optional · None = entry-off +
scan none. Whether to store one enum or the two axes is an implementation
detail to settle at build time; the LOCK here is: per-WorkflowStage, owner-
configurable, validated against handler capability.

## 4) Q4 — Does this stay open-closed for future stage types?

**Yes, strengthened.** A new stage type = new handler declaring its schema +
capabilities; its tracking mode is then pure data on the flow editor — zero
worker-UI edits (the report renderer is already schema-driven). The only
additive extension barcode needs in the report layer is a new schema `kind`
('scan') beside today's 'choice'/'quantity' — one renderer addition, used by
every scan-capable stage forever. The F1-locked `attributes` JSONB remains the
escape hatch for stage-specific measures (roll weight, machine hours). Nothing
in this requirement introduces a stage-name conditional anywhere.

## 5) Q5 — Can barcode and manual coexist cleanly?

**Yes, by the already-locked boundary (R1 I8/I9):** tracking owns piece
identity + scan events; production owns quantity truth. Scan-derived reporting
= scan events (tracking) → derived lines → the SAME single-writer chokepoint
(`report_contributions` / `complete_worker_task`) that manual entry uses. WSC
stays the one production truth regardless of entry method; settlement
(verified-else-reported) is entry-method-blind; expected_* freeze is
entry-method-blind; Missing/Alter stay barcode-independent (§5A). The ONLY
unsolved piece is H3 (hybrid reconciliation rule) — deferred with a name to
the Barcode/Traceability review, which R1 already scheduled.

## 6) Compatibility sweep (requested checklist)

- **Stage Engine** — compatible; Tracking Mode is data + one future schema kind.
- **R1 Stage Contracts** — this requirement IS the contract's fields 5/6/7
  restated; archetype table already says layering=native-unit qty,
  cutting_pattern=usually none, cutting=colour+size+qty, future
  packing=scan-derived. No contract change needed.
- **WorkerStageTask** — assignment truth untouched; H1 adjustment to
  auto-cancel semantics for none-mode is a resolution-rule tweak, not a model
  change.
- **WorkerStageContribution** — production truth untouched; barcode mode only
  changes who TYPES the lines, not what they are.
- **AddaSettlement** — untouched; reads contributions, stamps provenance,
  never writes quantities (verified). The owner's §9 is a description of V2-2
  as built.
- **ADR-0007** — orthogonal. Tracking mode concerns how production truth is
  CAPTURED; 0007 concerns when money books. No interaction.
- **ADR-0008** — orthogonal; nothing here touches commerce. G5's future
  finished-goods inflow would READ packing-stage truth — cleaner with scan
  counts, not dependent on them.
- **G1–G7** — G4 gets its requirement statement (§10 of the owner doc);
  G1/G3 consume the same settlement-side numbers; no seam moves.

## 7) Decision points for the owner (lock before the build, no code yet)

- **D-T1 — Storage shape:** one `tracking_mode` enum vs two axes
  (manual_entry + scan_policy) under a one-dropdown UI. Recommendation: decide
  at build time; both honor R1; the UI is identical.
- **D-T2 — None-mode task resolution (H1):** on stage completion, none-mode
  roster tasks resolve as participated-without-report (recommended) — never
  auto-cancelled.
- **D-T3 — Validation rules (H2/H4):** credits_workers ⇒ mode ≠ none; mode
  changes blocked while the stage is in-flight on any Adda. Recommended both.
- **D-T4 — Delivery split:** TM-1 = Manual/None config (field + flow editor +
  H1/H2/H4 rules) — small, no barcode dependency, natural companion to the
  MissingPiece phase or earlier. TM-2 = Barcode/Both — ONLY via the full
  Barcode/Traceability review R1 deferred (scan model, attribution H5,
  reconciliation H3). Recommendation: do not let TM-2 ride into TM-1.
- **D-T5 — Workspace visibility (T1):** policy decision on non-master helpers
  seeing planned quantities in stage workspaces (cutting breakup = work
  instruction for the master). Options: accept for cutting + enforce §5 for
  report-only stages (recommended, zero change now) / per-stage worker-console
  split (future, F7 family). Not a V2-3 item.

## 8) Sequencing statement

Nothing in this requirement changes the locked next step: **V2-3 proceeds as
reviewed** (settlement-primary cutover + the two integrity guards). Tracking
Mode lands after, per D-T4 — TM-1 cheap and early, TM-2 behind the Barcode/
Traceability review. This document is the requirements lock for both.
