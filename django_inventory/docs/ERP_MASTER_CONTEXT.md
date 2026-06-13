# ERP_MASTER_CONTEXT.md

## Garment Manufacturing ERP — Master Project Context

**Regenerated 2026-06-10 (R0 reconciliation)** — supersedes the previous version; status and precision corrections only, no principle changes. Verified against repo `new_flask_app` (417 tests green, migrations through production 0033) and locked docs. Corrections log: `docs/archive/reviews/R0_RECONCILIATION.md` · full review: `docs/archive/reviews/ERP_MASTER_CONTEXT_REVIEW.md`.

This document is the durable reference context for future chats, architecture reviews, and implementation planning. It captures long-term requirements, locked decisions, preferred design principles, and the open areas intentionally not final yet.

---

## 1) Project Overview

A **garment manufacturing ERP** around an **Adda-centric production model**. An **Adda** is the primary production batch/job unit; it moves through stages and eventually reaches settlement.

Designed for: long-term maintainability, auditability, scalability, future microservice extraction, open-closed stage architecture, manufacturing traceability, financial correctness, incremental migration safety, review-first architectural decisions.

Not a generic SaaS, not a traditional payroll app. A production-tracking and Adda-settlement system.

---

## 2) Core Architectural Principles

### 2.1 Production Truth ≠ Financial Truth (most important principle)

**Production Layer** stores operational reality: who worked, on what, when, which stage, color/size/dimension breakdown, reported quantities, missing pieces, alter/rework, audit trail, history.

**Financial Layer** stores economic reality: expected earning snapshots, advances, settlement decisions, recovery, ledger entries, final payable, payment records.

Production data must not automatically become final financial truth. Settlement finalizes financial truth later.

> **Status:** locked (ADR 0005) and partially live. The V2 worker-tracking layer that embodies this (tasks + contributions + frozen `expected_*`, booking no money) is BUILT. The **live money path is still the pre-V2 transitional model**: ledger credits at allocation time. The move to settlement-time crediting happens at V2-2/V2-3 under **ADR 0007 (Option A — coexist)**: historical allocation-era credits remain untouched; AddaSettlement credits only not-yet-credited lines; symmetric cross-era double-credit guard; `LEDGER_CREDIT_AT_ALLOCATION` flag as rollback lever; no synthetic settlements, no retroactive rewrites, no worker balance churn.

### 2.2 Adda-Centric Architecture

Everything interpreted through the Adda; Adda-centric reporting preferred over worker-centric payroll as the primary domain view. The Adda is the root for stage records, worker contributions, missing-piece tracking, alter/rework, costing, settlement, audit history, profitability.

### 2.3 Open-Closed Stage Engine

Future stages addable without schema redesign or hardcoded branching. Stage taxonomy may evolve (layering, pattern, cutting, stitching machine sub-stages, thread cutting, finishing, QC, packing, dispatch, machine-specific, rework stages…). Current stage definitions are NOT final — reference implementations only.

> **Status:** engine framework BUILT — `StageHandler` ABC + self-registering registry + `autodiscover()`, 4 handlers, data-driven `WorkflowStage.credits_workers`, open-closed proof test. **Known debt:** ~30 hardcoded stage-key sites (4 template elif chains, per-stage view modules, layering-only auto-start) — open-closed in framework, partial in practice. Rule until the stage-domain review: new code routes through the registry only.

### 2.4 Assignment-Based Access Control

Worker access is object-level, not just role-level. A worker sees only assigned Addas/stages, their tasks/contributions, their own earnings/advances/settlement history. Managers/admins see broader data by role. Assignment isolation is a security requirement.

> **Status: BUILT (V2-1c-iv).** `StageViewAccessMixin` = skill gate + active-assignment gate (management bypass); dashboards scoped by `worker_tasks__worker`; service-layer `_ensure_assigned_worker`; payroll self-scoped (`can_view_worker`); money screens management-only.

### 2.5 Append-Only / Immutable History

Never delete production history; prefer cancellation over deletion; settlement snapshots immutable; historical reports reconstructable. Backfill only known facts — never invent states.

### 2.6 Migration-Safe Incremental Refactors

Reviewed before implementation; small phases; characterization tests; reversible where possible; clone rehearsal; focused PRs. Don't combine model-migration risk with unrelated coupling cleanup.

---

## 3) Current Domain Model Direction

### 3.1 Adda
Primary production job/batch. Root for stage records, worker tasks, contributions, costing, settlement, missing pieces, alter/rework, future piece-level audit.

### 3.2 AddaStageRecord
An Adda moving through a stage; the production container for the stage. **Reality notes:** lifecycle is **timestamp-derived** (no status column — matches derived-not-stored); carries frozen `processing_cost` + cost snapshots; `cost_billed_at` lives on **WorkflowStage**; `adda` FK is PROTECT. The legacy `workers` M2M still exists and is **dual-written** behind `WORKER_TASK_DUAL_WRITE` until the V2-1d drop (point of no return; preconditions locked — see §12).

### 3.3 WorkerStageTask — **BUILT**
Worker assignment + lifecycle + security isolation + readiness input + future traceability anchor.
**FIVE statuses:** `assigned → in_progress → completed → [verified] + cancelled (terminal)`. `verified` is **optional and never a gate** — completion drives readiness; verification is an optional correction workflow.
Assignment is mutable; production history is immutable; un-assign ⇒ task becomes cancelled, never deleted. One ACTIVE task per (stage_record, worker) via partial UniqueConstraint; cancelled workers re-assignable.

### 3.4 WorkerStageContribution — **BUILT**
The dimensional work record, separate from the lifecycle record; multiple lines per task (color + size + quantity today). Frozen `expected_rate`/`expected_earning` at completion (visibility, not money); `reported_quantity` vs `verified_quantity` are separate fields. Stage-specific richer fields come via the locked **`StageHandler.contribution_schema()` pattern (BUILT)** with a nullable `attributes` JSONB added only when a real non-cutting stage needs it — no speculative schema.

### 3.5 Settlement Layer (design locked, NOT built — V2-2)
Settlement is Adda-centric (`AddaSettlement` = reconciliation event producing ledger entries; frozen append-only `AddaSettlementItem` per worker). Settlement ≠ payment (Model A): settlement books expected/variance/recovery/final payable, moves no cash; `PayrollSettlement` narrows to the separate cash event (partial/multiple/later). Advance recovery happens at settlement; payment never re-runs recovery. Lifecycle: draft → finalized → reversed/superseded (corrections never edit). Invariants (§11.9): cross-era double-credit guard (ADR 0007), quantity-freeze at finalize, write-once audit snapshots, finalize lock order. **No per-Adda paid/unpaid flag** (money is fungible at worker level). **`WorkerAdvance.adda` FK: REJECTED.**

### 3.6 Advances
Separate loan pool, independently trackable, never merged into earnings; no ledger debit on issue; owner-controlled per-advance (partial) recovery at settlement. **BUILT and live.**

### 3.7 Missing Pieces (future first-class domain)
Operational incidents, not counters: Adda linkage, detection stage, aging, open/closed/resolved, recovery/write-off history, auditability → future `MissingPieceCase`.
**Reality today:** only a `BatchBarcode.Status.MISSING` enum + read-only dashboard counts; `mark_status` has **no UI caller** (status unsettable from UI). **Locked rule (R0 C4):** no interim status UI; when missing-marking ships, `detection_stage` + `detected_at` + `detected_by` are mandatory at mark time (un-backfillable facts).

### 3.8 Alter / Rework (future first-class domain)
A lifecycle, not a counter → future `AlterCase` (open / in_rework / qc_pending / resolved / rejected / scrapped; originating Adda, stage, color, size, defect type/stage, dates, outcome). **Zero code today** — intentionally.

---

## 4) Production Workflow Direction

### 4.1 Worker Reporting
Save draft → Submit & Complete → locked for the worker; manager/admin can correct later (via `verified_quantity`, never edits to the worker's report). Worker UI never reveals other workers' progress. **Backend BUILT (report/draft/complete-freeze services); UI = pt.2b, pending** (mockup approved, D1-D8 decisions locked).

### 4.2 Draft vs Submit
Draft = operational convenience (task-not-completed + replace-semantics draft lines); Submit & Complete = business truth. Draft data never affects readiness, costing, settlement, expected earnings, payroll, or reporting.

### 4.3 Readiness
Stage advance is derived, not stored (assigned/in-progress/completed/cancelled, readiness %, ready-for-review/advance — service-computed, no table).
**Verification semantics (locked, R0 C3):** task-level `verified` NEVER gates progression. Stage-level completion validations are stage-handler-owned and MAY gate that stage's completion — e.g. `CuttingPatternVerification` is today a hard gate for completing cutting_pattern (shipped, deliberate). Their final shape belongs to the stage-domain review. Advance gate for payability = all active tasks completed.

### 4.4 Worker Visibility
Workers see only their own tasks, contributions, earnings/advances, relevant Adda data. Never: other workers' contributions/earnings, factory-wide totals, unassigned Addas, management-only detail. Management bypasses. **BUILT** (see §2.4).

---

## 5) Stage Engine / Contribution Schema

Stage-driven, open-closed. The report UI and contribution handling must not hardcode a universal color/size/quantity schema — those fit Cutting (the reference implementation). Future stages may need roll weight, fabric length, bundle count, machine hours, operation count, defect count, piece type, custom data.

**`StageHandler.contribution_schema(adda)` is BUILT** (base = qty-only; CuttingHandler override = color+size+qty). Rendering is stage-definition-driven. Additive extension seam (`attributes` JSONB) only on demonstrated need — no speculative schema.

---

## 6) Financial Philosophy

### 6.1 Expected Earning Snapshot
Contribution completion freezes an expected earning snapshot (`expected_rate`/`expected_earning`) — operational visibility. Not a ledger entry, not final payable, not settlement. **BUILT.**

### 6.2 Ledger
Ledger contains only financial truth; single writer (`ledger_service`, ADR 0002); append-only. Target: no provisional/pre-settlement credits. **Transitional reality:** credits currently book at allocation (pre-V2 model) — ends at V2-2/V2-3 per ADR 0007; allocation-era credits remain valid history (never rewritten).

### 6.3 Settlement
Final money truth established at settlement:
Contribution → Expected Snapshot → Settlement → Variance/Missing/Alter adjustments → Advance Recovery → Final Payable → Ledger Entry → Payment. Settlement Adda-centric; payment separate.

### 6.4 Variance Policy
Launch default **factory_absorbs**: missing/rejected/shortfall tracked and reported, payable NOT auto-reduced. Variance visible and auditable; deduction policy configurable later; no attribution engine prematurely. Variance entry at finalize is **manual and source-agnostic** (future Missing/Alter modules feed the same seam with no settlement schema change).

### 6.5 Payment
Settlement books what is owed; payment is a separate cash event — immediate/partial/multiple/delayed; advance recovery never conflated with the pay event. **Transitional reality:** today's `PayrollSettlement` conflates settle+pay+recover; it narrows to payment-only at V2-2. `reverse_settlement` is designed inside V2-2's reversal lifecycle (R0 C5) — until then, manual-ops caution on settlements.

---

## 7) Worker Report UI Direction

Mockup approved (editable draft + submitted/locked states, chip color/size pickers, qty input, Save Draft, Submit & Complete, Submitted-At in locked state). Stage-specific EXAMPLE, not the universal form — rendering comes from `contribution_schema()`. Worker-friendly, mobile-friendly, no other workers' progress, **no financial truth on the worker reporting screen** (payment shown separately). Locked decisions D1-D8 (both routes; worker cannot reopen completed; dashboard badges; stage-driven fields; locked state; manager-correction UI deferred — `verified_quantity` suffices; chips kept; no other-worker visibility). **Build = pt.2b/2c, pending.**

---

## 8) Missing Pieces and Alter/Rework — Future Seams

Never collapse into counts forever. Future `MissingPieceCase` + `AlterCase` are operational lifecycle entities; settlement consumes their **summaries**, never owns their workflow. Capture-seams verified: dimensions (adda/color/size/qty) backfillable from existing models; lifecycle facts (detection stage/date) intentionally NOT fabricated — captured live from day one of the module (§3.7 rule).

---

## 9) Performance and Scalability

Concerns: dashboard N+1, per-Adda query explosion, stage summaries, settlement reporting. Prefer derived summaries, query flattening, prefetch/select_related, read models when necessary, audit-preserving optimization. Design for 10 → 100k Addas.

> **Status:** hot paths query-flat with locked perf-baseline tests (dashboard worker=14/mgmt=20 queries, adda list=11, costing=9, layering snapshots flat at 5). Known cliffs for later: unpaginated mgmt dashboard; costing view's in-memory full-table aggregates. Suite footgun: run tests from `config/` (root-dir run silently discovers 0).

---

## 10) Future Microservice Boundaries

Possible later: Production, Settlement, Costing, Missing Pieces, Alter/Rework, Identity/Permissions services. Current architecture must not block extraction — and must not implement it (ADR 0006: architect for scale, do NOT implement; target 8.5-9/10, seams not features). Known coupling on the books: production↔tracking cycle (P4.2, parked — relocation-class fix), expense allocation writer retiring at V2-3, production→expense one-way facade in exactly one file (target).

---

## 11) Current Review / Implementation State (corrected 2026-06-10)

### Built + committed (`new_flask_app`, migrations 0029-0033, 417 tests green)
- V2-1a: `WorkerStageTask` + reversible backfill + dual-write chokepoint (`worker_task_service`, sole M2M writer, check.sh gate) behind `WORKER_TASK_DUAL_WRITE`.
- V2-1b: all readers flipped to tasks (M2M still dual-written).
- V2-1c: `WorkerStageContribution` + self-report/draft/complete-freeze services + `contribution_schema()` hook + assignment-isolation gate (V2-1c-iv).
- Stage engine (handlers/registry), stage costing + frozen snapshots, expense app (ledger/advances/PayrollSettlement), RBAC three-concept model + object-level isolation, tracking/barcodes, perf baselines.

### Locked design, not built
- §11 settlement: `AddaSettlement`/`Item` (V2-2), SWA repurpose as settlement earning line (V2-3 — SWA is **retained**, not replaced), PayrollSettlement narrowing, reversal lifecycle incl. reverse_settlement.
- ADR 0007 cutover (accepted; implemented inside V2-2).
- Missing/Alter modules; worker report UI (pt.2b/2c).

### Locked decisions (headline set)
Open-closed stage engine · WorkerStageTask = lifecycle foundation (5 statuses) · WorkerStageContribution = dimensional truth · settlement ≠ payment · expected snapshot = visibility · advances separate · Missing/Alter future first-class · assignment isolation · immutable history / backfill-known-facts-only · draft vs submit · stage-driven contribution schema · factory_absorbs · frozen AddaSettlementItem · no per-Adda paid flag · WorkerAdvance.adda rejected · double-credit + quantity-freeze invariants · finalize lock order · derived-never-stored progress/balances · Stage.code = immutable identity vs Stage.name = display · WorkflowStage flat (sub-stages via additive parent FK later) · credits_workers permanently on WorkflowStage · ADR 0006 seams-not-features · ADRs 0001-0007.

### Still intentionally open / future review
Complete stage taxonomy · machine-stage hierarchy · final missing-piece architecture · final alter/rework architecture · barcode ownership (P4.2 parked) · piece-level traceability · final RBAC refinement · microservice boundaries · stage-specific contribution schemas for future stages.

---

## 12) V2-1 Migration / Foundation State (corrected)

Executed so far exactly per plan: backfill used known facts only (`assigned`/`completed`, never fabricated `in_progress`); unassign cancels, never deletes; dual-write feature-flagged (ON, env kill-switch); M2M/Task coexistence reversible; clone-rehearsed.

**Remaining point of no return = V2-1d (drop the M2M).** Preconditions LOCKED (R0 C2):
1. M2M↔active-task parity assertion in the suite/check.sh;
2. kill-switch semantics documented (flag OFF ⇒ tasks go stale ⇒ re-backfill before re-enable);
3. soak: pt.2b worker UI exercised on real data through ≥1 full Adda cycle;
4. clone rehearsal of the drop migration.

---

## 13) Architecture Style Preferences

Staff/Principal/Domain-Architect thinking; challenge assumptions; separate hidden coupling from real requirements; don't over-engineer speculative problems; don't under-design future-proof seams; validate foundation first; current stages = reference implementations; avoid hardcoding the present into the future.

## 14) Communication Preferences

English for technical/system design; Hindi OK conversationally; no Urdu wording/script by default. Concise, architecture-rich prompts. Preferred response structure: decision → why it fits → what to defer → what to review next. Frequent asks: response crafting, review prompts, decision selection, phased planning, migration risk reviews, foundation-first review.

## 15) Current Working Mental Model

Long-lived manufacturing platform: Adda-based production, future stage redesign, worker contributions, missing-piece + alter tracking, settlement/payment separation, audit & dispute resolution, future machine workflows, future cost/reporting refinement. Today's Cutting implementation must not become the permanent shape of the system.

## 16) How to Use This File in Future Chats

Attach this file (or a subset). When asking for review, clarify whether the question is about: foundation · current stage implementation · settlement · future domain expansion · migration safety. **Process docs in-repo:** `docs/archive/reviews/ERP_MASTER_CONTEXT_REVIEW.md` (12-section review) · `docs/archive/reviews/R0_RECONCILIATION.md` (truth model + contradiction inventory) · `docs/archive/reviews/STAGE_DOMAIN_REVIEW_AGENDA.md` (next review's backlog + resume order).

## 17) Deployment & Runtime Architecture Seeds

Monolith today; goal is NOT Kubernetes/microservices now. Keep deployment possible without rewrites: stateless web layer (state in PostgreSQL/Redis/storage), storage abstraction (Django Storage API — held), background-job boundaries (long work behind service functions — held), environment-based config (held: base/local/production + .env), View → Service → Domain layering (held), read-model readiness, path Monolith → Docker → multi-container → K8s reserved.

> **Known pre-deploy blockers (catalogued, fix in one PR before first real deploy — not now):** no `CACHES` setting (auth rate limiter per-process under multi-worker), `argon2-cffi` + WSGI server missing from requirements.txt, `SECURE_SSL_REDIRECT` without `SECURE_PROXY_SSL_HEADER` (proxy loop), production media serving unsolved, file-based logging multi-process unsafe.

## 18) Observability & Operational Readiness

Future: structured logging, error/job monitoring, request tracing, settlement audit tracing. Today: request-id-correlated rotating logs + dedicated security.log + `*History` tables; business events logged (advance issuance missing a log line — minor). Traceable events target list unchanged (Adda created, stage completed, settlement created, advance issued, missing opened, alter opened).

## 19) Domain Event Vocabulary (documentation concepts, not infrastructure)

WorkerTaskAssigned · WorkerTaskCompleted · ContributionSubmitted · AddaAdvanced · SettlementCreated · SettlementFinalized · AdvanceIssued · MissingPieceOpened/Resolved · AlterCaseOpened/Resolved.

## 20) Factory / Multi-Site Direction

Single factory now; possible multi-factory later. Build no multi-site infrastructure today; the reserved seam is the `current_factory()` chokepoint with NO factory columns now (half-scoping = leak risk).
