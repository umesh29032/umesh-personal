> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/ARCHITECTURE_V2.md](../../ARCHITECTURE_V2.md).

# R0 — Documentation & Architecture Reconciliation (FOR OWNER REVIEW)

**Date:** 2026-06-10 · **Phase:** R0 (docs + decisions only; no code, no migrations) · **Status: ✅ APPLIED + owner-signed.**
Owner decisions: **ADR-0007 = Option A (ACCEPTED)** · **C2-C5 all confirmed as recommended.** Edits A1-A6 applied; ERP_MASTER_CONTEXT regenerated at `docs/ERP_MASTER_CONTEXT.md`; agenda updated with the R0 locked-decision block. A8 docstring fixes remain deferred to their owning code PRs.
Inputs: `docs/ERP_MASTER_CONTEXT_REVIEW.md` (12-section review) + `docs/ERP_MASTER_CONTEXT_REVIEW_STATE.md` (evidence, file:line verified).
Companion: `docs/adr/0007-allocation-era-ledger-cutover.md` (PROPOSED).

Per owner instruction: this document delivers (1) the architecture truth model, (2) the full doc↔code contradiction inventory classified **doc wrong / code wrong / decision not finalized**, (3) the updated decision matrix, and (4) the exact edit list to apply after owner sign-off.

---

## 1) Architecture Truth Model (what is ACTUALLY true today)

### 1.1 System shape
- Django 5.0.1 + PostgreSQL monolith, branch `new_flask_app`, clean tree, **417 tests green** (~134s; suite discovers only from `config/` — root-dir run silently finds 0).
- 8 apps: accounts, core (abstract bases, no tables), inventory, raw_materials, production, tracking, expense, storefront. Service layer owns all writes (ADR 0001); no signals.

### 1.2 Production truth (V2 worker-tracking) — BUILT through V2-1c
- `WorkerStageTask` (5 statuses: assigned / in_progress / completed / **verified [optional, never a gate]** / cancelled-terminal) + `WorkerStageContribution` (multi-line; color/size/qty FKs; frozen `expected_rate`/`expected_earning`; 4 CheckConstraints). Migrations 0031/0032/0033 applied to dev DB. Commits e4953ef9 → cfdb2d26.
- `AddaStageRecord.workers` M2M **still exists and is dual-written** via the single chokepoint `worker_task_service` behind `WORKER_TASK_DUAL_WRITE` (default ON, env kill-switch). All reads repointed to tasks (V2-1b). M2M drop = V2-1d, NOT done (point of no return).
- Stage engine: `StageHandler` ABC + self-registering registry + `autodiscover()`; 4 handlers (layering, cutting_pattern, cutting, barcode_generation); `contribution_schema()` hook built (base qty-only; Cutting override = color+size+qty); data-driven `WorkflowStage.credits_workers`; open-closed proof test exists. **BUT** ~30 hardcoded stage-key sites remain (4 template elif chains, per-stage view modules, layering-only auto-start) — open-closed is true for the framework, partial in practice.
- Stage advance: `adda_service.advance_to_next_stage` derives next stage from `WorkflowStage.order`; `AddaStageRecord` lifecycle is timestamp-derived (no status column); `cost_billed_at` lives on WorkflowStage; frozen cost snapshots on the record. `CuttingPatternVerification` **is a hard completion gate** for the cutting_pattern stage (per-worker task `verified` is the thing that never gates).
- Worker reporting: draft (stage-level drafts + `is_draft`/`save_draft_contributions` replace-semantics) vs Submit&Complete (freezes expected_*, books **no** ledger entry). Report/draft/complete services have **zero view/UI callers yet** (pt.2b pending).

### 1.3 Financial truth — LIVE = PRE-V2 transitional model (acknowledged)
- `WorkerLedgerEntry`: append-only, single writer `ledger_service` (verified sole `objects.create`). **Credits are written at allocation time** (`expense/services/allocation_service.py:110`, cutting workspace) — the locked Option B target (credit only at settlement) is design, not yet runtime.
- `PayrollSettlement` **conflates settle + pay + advance-recovery** in one atomic event (`amount_paid` on header). `AddaSettlement` does not exist in code (V2-2).
- Advances: separate loan pool (no ledger debit on issue), owner-controlled per-advance partial recovery at settlement. `reverse_entry` exists; **`reverse_settlement` (compensating recovery items) unbuilt** — a wrong settlement permanently reduces advance outstanding.
- Net: **two earning surfaces coexist** — SWA→ledger credits (live money) and WSC `expected_*` (visibility). Reconciling them at V2-2 is ADR-0007's subject.
- No variance/deduction engine ('deduction' category has zero writers); factory_absorbs is locked policy, design-only.

### 1.4 Access control — object-level isolation BUILT (V2-1c-iv)
`StageViewAccessMixin` = skill gate + active-assignment gate (management bypass) at `production/views/mixins.py:29-46`; dashboard scoped `worker_tasks__worker=request.user`; service guard `_ensure_assigned_worker`; payroll self-scoped via `can_view_worker`; costing/payroll-overview management-only. Workers see no other worker's money or contributions on built screens.

### 1.5 Missing / Alter
Missing = `BatchBarcode.Status.MISSING` enum + read-only dashboard aggregates ONLY. **`mark_status` has no view/URL caller — missing status cannot be set from the UI.** Nothing in costing/settlement reads missing counts. Alter/rework = zero code. `MissingPieceCase`/`AlterCase` = locked future modules.

### 1.6 Deployment reality
Local/dev only; no deploy infra, no evidence of live production data. Settings split + .env correct; DB sessions; storage via Django Storage API (FileSystem backend). Blockers catalogued for a future pre-deploy PR: no `CACHES` (rate limiter per-process), argon2-cffi + gunicorn missing from requirements.txt, `SECURE_SSL_REDIRECT` without proxy header, prod media unserved, multi-process-unsafe file logging.

### 1.7 Sequencing state
⏸️ Paused at clean checkpoint for the stage-domain review. Agreed resume order: pt.2b → pt.2c → V2-1d → V2-2 → V2-3 → Missing/Alter. P4.2 barcode cycle-break parked.

---

## 2) Contradiction Inventory (every doc↔code conflict found, classified)

### A. DOC WRONG (code/reality is right → edit the doc)

| # | Location | Says | Truth | Proposed fix |
|---|----------|------|-------|--------------|
| A1 | `docs/ARCHITECTURE_V2.md:2` | "Status: PROPOSED 2026-06-09 (design only, not yet built)" | Worker-tracking layer (V2-1a/1b/1c) built+committed; only §11 settlement design-only | Reword header: "Worker-tracking BUILT (V2-1a→1c, migrations 0031-0033); §11 settlement LOCKED design, not yet built" |
| A2 | `docs/ARCHITECTURE_V2.md:84` (§2) + `:222` (§10 "Added" list) | "WorkerAdvance (existing) **+ add adda FK**" | Locked §11.3 explicitly REJECTS `WorkerAdvance.adda` ("Do not add it"); §11.12 confirms not added | Strike "+ add adda FK" from §2; strike `WorkerAdvance.adda` from §10's Added list; add pointer "→ rejected, see §11.3" |
| A3 | `docs/V2_1_REVIEW.md:243-250` (§10 header) | "uncommitted… **NOT committed** (owner approval pending)"; "Full suite 366 OK" | Committed (e4953ef9, adddec97, bf9bfff3, 77d5d773, 5e4b4516, 2580a7d6, cfdb2d26); suite 417 | Update status line + test count; keep history note |
| A4 | `CLAUDE.md:8` | "**In progress (V2-1a).**" | Built through V2-1c-iii pt.2a + 1c-iv; paused for stage-domain review | Replace with "V2-1a→1c BUILT; paused pre-stage-domain-review; pending pt.2b/2c, V2-1d, V2-2, V2-3" |
| A5 | `SYSTEM_DESIGN.md:258-260` | Scan flow diagram: "scan → … → mark_status (pending/packed/dispatched/missing)" | `scan_piece` never calls `mark_status`; no view/URL exposes it — status unsettable from UI | Correct diagram (scan = resolve + get_or_create only); add note: "`mark_status` service exists, no UI caller — wiring deferred (see ADR-0007 §open / Missing module)" |
| A6 | `docs/production/UI_PATTERNS.md:181` | `?status=missing` filter described as part of working "reprint flow" | Filter works, but nothing can set MISSING → flow not exercisable end-to-end | Add one-line caveat |
| A7 | `ERP_MASTER_CONTEXT.md` (owner's master doc) | §11/§12 status ("V2-1a in progress"); 4-status task lifecycle; SWA "replaced"; "stage advance should not depend on verification today" (unqualified) | See review M1-M6: built through V2-1c; 5 statuses; SWA retained-repurposed (§11.4); CuttingPatternVerification IS a stage-completion gate (task-level `verified` is what never gates) | Regenerate master-context with corrections (§4 below) |
| A8 | `config/production/models/worker_task.py:14` (docstring) + `adda.py:89-92` (docstring) | "WorkerStageContribution… deferred to V2-1c" / stale M2M Hinglish note | Delivered in same tree / M2M drop scheduled V2-1d | **Docstring edits = code files → NOT touched in R0.** Logged here; fold into the V2-1d PR (adda.py one is already on V2_1_REVIEW:218's list) |
| A9 | Stale counts in older memory/doc mentions ("292 tests", "366 OK") | — | 417 green | Covered by A3/A4 edits |

### B. CODE WRONG / CODE BEHIND THE LOCKED DECISION (doc is right → code catches up in planned phases; nothing to do in R0)

| # | Location | Locked decision | Live code | Catches up at |
|---|----------|----------------|-----------|---------------|
| B1 | `expense/services/allocation_service.py:110` | Option B: ledger credit only at settlement (§5, §11, ADR 0005) | Credits at allocation time | V2-2/V2-3 (per ADR-0007) — explicitly acknowledged in PAYROLL_ARCHITECTURE banner; not a bug |
| B2 | `expense/services/settlement_service.py` (`create_settlement`) | Model A: settlement ≠ payment | One atomic settle+pay+recover event | V2-2 (PayrollSettlement narrows to cash-only) |
| B3 | reverse path | Settlement lifecycle draft→finalized→reversed/superseded (§11) | `reverse_settlement` unbuilt; recovery items irreversible | V2-2 reversal design (recommendation: do NOT patch the pre-V2 model) |

### C. DECISION NOT FINALIZED (neither doc nor code can be "right" yet → owner decisions)

| # | Question | Options / recommendation | Decided where |
|---|----------|--------------------------|---------------|
| C1 | **Allocation-era ledger cutover** for V2-2 | ADR-0007 options A/B/C; recommendation = A (coexist + boundary + extended double-credit guard) | **ADR-0007 — owner must pick** |
| C2 | **V2-1d preconditions** | Proposed: (i) M2M↔active-task parity assertion added to suite/check.sh, (ii) kill-switch semantics documented (flag OFF = M2M-only writes → tasks stale → re-backfill required before re-enable), (iii) soak = pt.2b worker UI used on real data through ≥1 full Adda cycle, (iv) clone rehearsal of the drop migration | Owner confirms list (then it gets appended to V2_1_REVIEW §6) |
| C3 | **Verification-gate wording** | Recommend: "Task-level `verified` never gates anything. Stage-level completion validations (e.g. CuttingPatternVerification) are stage-handler-owned and MAY gate that stage's completion; the stage-domain review owns their final shape." Master-context §4.3 rewritten accordingly | Owner confirms wording → applied in A7 |
| C4 | **mark_status / missing marking** | Recommend: do NOT wire interim UI now; wait for MissingPieceCase (R1/P6). One rule locked now: when ANY missing-marking UI ships, it must capture detection-stage + detection-date + actor at mark time (un-backfillable facts) | Owner confirms → noted in SYSTEM_DESIGN fix (A5) + agenda |
| C5 | **reverse_settlement placement** | Recommend: fold into V2-2 reversal lifecycle; accept the gap until then (manual ops caution) | Owner confirms → noted in FLOWS/README + agenda |

---

## 3) Updated Decision Matrix (delta vs the review's §3)

All KEEP rows from `ERP_MASTER_CONTEXT_REVIEW.md §3` stand unchanged. MODIFY rows M1-M6 are now concretized as edits A1-A7 above. DEFER list unchanged. REJECT: only the doc-level `WorkerAdvance.adda` remnant (A2). New since review: C2-C5 promoted to explicit owner decisions (review §9 items, now with concrete recommendations).

---

## 4) ERP_MASTER_CONTEXT regeneration plan (A7)

Corrections to weave in when regenerating the owner's master doc (no principle changes — status + precision only):
1. §3.3: five task statuses; `verified` optional/non-gating.
2. §3.2: AddaStageRecord lifecycle = timestamp-derived; cost fields = frozen snapshots on record, `cost_billed_at` on WorkflowStage.
3. §3.4: WorkerStageContribution BUILT (not future); attributes-JSONB deferred-additive.
4. SWA: transitional-RETAINED → settlement earning line (§11.4), not replaced.
5. §4.3: verification wording per C3.
6. §11/§12: status block rewritten — built: V2-1a/1b/1c + contribution_schema hook + isolation gate; pending: pt.2b/2c, V2-1d, V2-2, V2-3, Missing/Alter; locked-decision list extended with the ~15 omissions (factory_absorbs, frozen AddaSettlementItem, no per-Adda paid flag, §11.9 invariants, finalize lock order, derived-never-stored, Stage.code identity, credits_workers placement, ADR 0006, parked P4.2…).
7. New §: ADR-0007 cutover decision (once owner picks).

---

## 5) What R0 will NOT touch
No models, no migrations, no services, no views, no templates, no settings. Docstring fixes (A8) deferred to their owning code PRs. Deployment blockers stay catalogued (review §5) for a separate PD PR.

## 6) Apply checklist (execute only after owner sign-off)
1. Owner picks ADR-0007 option (A/B/C) + confirms C2-C5.
2. Apply edits A1-A6 to repo docs.
3. Regenerate ERP_MASTER_CONTEXT.md (A7 + §4 plan) — delivered back to owner as the new attachable baseline.
4. Mark ADR-0007 ACCEPTED; append V2-1d preconditions to V2_1_REVIEW §6; update STAGE_DOMAIN_REVIEW_AGENDA pointers.
5. Re-run doc-accuracy guard + test suite (no behavior change expected); commit as `docs(R0)` per commit conventions.
6. Owner reviews → decide next phase: **V2-1d vs Stage-Domain Review** (note: recommended C2 soak criterion implies pt.2b/R1 BEFORE V2-1d — surface this trade-off at that decision point).

---

## 7) Pre-existing finding surfaced during R0 verification (NOT fixed — out of R0 scope)
`scripts/check.sh` blocking gate **[1/4] foundation-purity FAILS on HEAD** (pre-dates R0; confirmed by stashing R0's doc changes): `accounts.tests -> inventory.models` (accounts/tests, l.265) violates "core + accounts import no domain app". Tests (417), coverage (69%), and the M2M single-writer gate are green. Fix belongs to a small code PR (move/indirect the test import); candidate for whichever code phase runs next.
