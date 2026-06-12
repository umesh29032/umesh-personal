> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/R1_STAGE_DOMAIN_REVIEW.md](../../R1_STAGE_DOMAIN_REVIEW.md) (the executed review).

# Manufacturing Stage-Domain Review — FUTURE backlog + live reminder log

> Set 2026-06-10. The V2 **foundation is LOCKED + signed off** ([V2_FOUNDATION_REVIEW.md](V2_FOUNDATION_REVIEW.md)).
> **This is now the LIVING future-reminder backlog** (owner decision 2026-06-10): remediation + V2 work
> proceeds **against the current stage flow now** — we do NOT block on this review. Every stage-coupled touch
> point in the code carries an inline **`# FUTURE-STAGE-REDESIGN: …`** comment pointing here, so when stages
> are added/renamed/refactored later, this doc + a `grep -rn "FUTURE-STAGE-REDESIGN"` give the full checklist.
> Cutting today = a REFERENCE implementation, NOT the final stage definition.
>
> **Convention:** stage-coupled code uses `# FUTURE-STAGE-REDESIGN: <what to revisit when stages change>`.
> Accumulate notable markers under "§ Logged reminders" at the bottom as they're added.

## PRESERVE — locked foundation, do NOT revisit in this review (it's correct + built)
- `WorkerStageTask` (lifecycle + assignment) + `WorkerStageContribution` (qty + frozen `expected_*`) — built.
- `StageHandler.contribution_schema()` open-closed hook — built (base qty-only; Cutting reference).
- Settlement architecture §11 — Option B (no ledger until settlement), Model A (settlement ≠ payment;
  recovery at settlement), WRAP (AddaSettlement event + PayrollSettlement payment), frozen AddaSettlementItem.
- Immutable single-writer ledger; production-truth ≠ financial-truth; dual-write chokepoint; assignment
  isolation (Skill ∧ Assignment); draft = task-not-completed.
- Extensibility seams (all additive, no rewrite): contribution `attributes` JSONB (deferred), WorkflowStage
  `parent` FK for sub-stages (deferred), Missing/Alter as future first-class domains, stage rename via
  stable `Stage.code` ≠ display `name`.

## REVIEW + (re)design in this phase — the manufacturing domain
1. **Stage taxonomy** — the real set of stages (names, boundaries); which to rename / split / merge.
2. **Stage responsibilities** — what each stage owns (inputs, outputs, who acts, what's measured).
3. **Worker interaction patterns** — per-stage report shapes (the `contribution_schema` per stage).
4. **Machine-based stages** — machine sub-stages, machine hours, operation counts; hierarchy needs
   (→ may trigger the deferred `WorkflowStage.parent` seam).
5. **Missing-Piece lifecycle** — first-class domain: detection stage, aging, recovery/resolution/write-off,
   reporting, audit (→ `MissingPieceCase` design; settlement consumes its summary).
6. **Alter/Rework lifecycle** — first-class domain: defect type/stage, rework/reject/scrap, dates, outcomes,
   analytics (→ `AlterCase` design; settlement consumes its summary).
7. **Settlement implications** — how the finalized stage taxonomy + missing/alter feed AddaSettlement.
8. **Costing implications** — per-stage cost methods/rates; piece-rate vs time-rate vs fixed (the F2 note:
   keep earning computation swappable per stage).
9. **Future reporting requirements** — adda/worker/stage/colour/size + missing/alter/defect-stage + cost +
   settlement + advance analyses; confirm the grain captured today supports them.

## Output of this phase (before resuming build)
- A locked stage taxonomy + per-stage responsibility map + per-stage `contribution_schema`.
- `MissingPieceCase` + `AlterCase` domain designs (models + lifecycle + the settlement summary seam).
- Decisions on machine sub-stages (flat vs `parent` FK), costing/pay models per stage.
- THEN resume: V2-1c-iii pt.2b (worker report UI, schema-driven) → pt.2c (dashboard badges) → V2-1d (drop
  M2M) → V2-2 (AddaSettlement build) → V2-3 (SWA repurpose) → Missing/Alter modules.

## § Logged reminders (`# FUTURE-STAGE-REDESIGN:` markers added during remediation)
> Appended as stage-coupled code is touched. `grep -rn "FUTURE-STAGE-REDESIGN" config` for the live set.
- **SWA-transitional → V2-2 settlement (Phase 6, P2.7):** the `production → expense`
  StageWorkAssignment reads are tagged at `stages/base/credit.py` (PAY-2 guard),
  `services/_shared.py` (reopen void), `views/stage_views.py` (allocation UI),
  `views/costing_views.py` (earnings column). When V2-2 (Adda settlement, Option B)
  books earnings at settlement, repoint/retire these + break the production↔expense
  cycle. See ARCHITECTURE_V2 §11 + V2_1_REVIEW.

## § R1 — Manufacturing stage-domain review 🔒 LOCKED 2026-06-10
**[R1_STAGE_DOMAIN_REVIEW.md](R1_STAGE_DOMAIN_REVIEW.md) — D-R1.1…D-R1.10 all owner-locked.** Resolves this agenda's items 2-8 at the ARCHITECTURE level (item 1 stage names/taxonomy + item 9 reporting grain confirmation remain open by design):
- Archetype map (A-F) + invariants I1-I10; nine-field **Stage Contract** (§2A) = stable foundation beneath any taxonomy.
- Output grain (adda, stage, color, size, qty) = expected-piece truth, **independent of barcodes** (§5A); Missing/Alter anchor on it, barcode refs = optional enrichment.
- Contribution patterns per archetype; JSONB on first consumer. Cost-unit extensibility + cost≠earning separation.
- Missing/Alter integration contracts (anchor duality, §11.10 variance seam, **rework = ordinary WorkerStageTasks** linked from AlterCase).
- **P4.2 settled + UNPARKED**: barcode models stay in tracking (D3=NO move), tracking BELOW production (D2), assembly relocates to production; views = D1 at execution.
- **Scan seam (§8A):** scanning = stage capability (not archetype); future additive `WorkflowStage.scan_policy {none,optional,required}` + handler `validate_scan` hook; scan events in tracking primitive; lifecycle/genealogy deferred to a future **Barcode/Traceability review**.
- Machine sub-stages: parent-FK shape + trigger rule (different workers/rates OR independent progress; else one stage with operation measures).
**Still open (deliberate):** final stage names/taxonomy (lands when real stages onboard, instantiating Stage Contracts) · concrete MissingPieceCase/AlterCase models (P6) · barcode lifecycle (future review).

## § R0 reconciliation — owner decisions locked 2026-06-10
- **ADR 0007 ACCEPTED (Option A):** allocation-era ledger credits coexist untouched; AddaSettlement credits only uncredited (worker, stage_record) lines; symmetric cross-era double-credit guard; `LEDGER_CREDIT_AT_ALLOCATION` flag = rollback lever; no synthetic settlements. V2-2 build requirements + edge-case tests listed in the ADR.
- **C2 — V2-1d preconditions** locked (see V2_1_REVIEW §10 header): parity assertion · kill-switch semantics · pt.2b soak ≥1 full Adda cycle · clone rehearsal.
- **C3 — verification semantics:** task-level `verified` NEVER gates progression (optional correction workflow; completion drives readiness). Stage-level completion validations (e.g. CuttingPatternVerification) are stage-handler-owned and MAY gate that stage; their final shape belongs to THIS review.
- **C4 — missing marking:** no interim `mark_status` UI; ships with MissingPieceCase; `detection_stage`/`detected_at`/`detected_by` mandatory at mark time from day one.
- **C5 — reverse_settlement:** designed inside V2-2's reversal lifecycle (draft→finalized→reversed/superseded), covering AddaSettlement + narrowed payment; no isolated pre-V2 patch. Until then: manual-ops caution on settlements.
- Full inventory + truth model: `docs/R0_RECONCILIATION.md`; review: `docs/ERP_MASTER_CONTEXT_REVIEW.md`.

## Checkpoint state at pause (2026-06-10)
Branch `new_flask_app`, working tree clean, **389 tests green**. V2 commits this run:
`e5ad1445 docs · e4953ef9 V2-1a · adddec97 V2-1b · bf9bfff3 V2-1c-i · 77d5d773 V2-1c-ii ·
5e4b4516 V2-1c-iv · 2580a7d6 draft+mockup · ea3d3527 mockup-review · cfdb2d26 contribution_schema`.
Dev DB migrated through `0033`. Nothing uncommitted.
