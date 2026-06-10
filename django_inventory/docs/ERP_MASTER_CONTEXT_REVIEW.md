# ERP_MASTER_CONTEXT.md — Architecture Review (Final Deliverable)

**Date:** 2026-06-10 · **Reviewed against:** repo `new_flask_app` (clean tree, 417 tests green, dev DB at production migration 0033) + locked docs (ARCHITECTURE_V2, V2_1_REVIEW, V2_FOUNDATION_REVIEW, TARGET_ARCHITECTURE, ADRs 0001-0006, STAGE_DOMAIN_REVIEW_AGENDA).
**Method:** multi-agent map (7 areas) + adversarial verification of every flagged conflict (11 verdicts, all confirmed) + inline RBAC verification. Evidence log: `docs/ERP_MASTER_CONTEXT_REVIEW_STATE.md`.
**Scope:** review only. No code. Implementation starts only after explicit owner approval (Phase Execution Policy).

---

## 1) Architecture Verdict

**SOUND — and the codebase is AHEAD of the master-context document.**

The master-context's principles (Production Truth ≠ Financial Truth, Adda-centric settlement, Option B, Model A, append-only history, assignment isolation, stage-driven contribution schema, migration-safe phases) are not aspirations — they are already locked owner decisions in repo docs, most with shipped code behind them. The document's main defect is **staleness**: it describes V2-1a as "in progress" when V2-1a/1b/1c are built, committed, migrated, and characterization-tested. A handful of claims conflict with shipped reality (see §3 MODIFY rows). No principle in the document needs reversal.

Consistent with ADR 0006's own target: this is an 8.5/10 foundation by design, not a 10/10 — the remaining 1.5 points are deliberately deferred seams, not gaps.

## 2) Risk Matrix

| # | Risk | Sev | Likelihood | Where | Mitigation |
|---|------|-----|------------|-------|------------|
| R1 | **Dual money surface with no cutover policy.** Live ledger credits at allocation (`expense/services/allocation_service.py:110`) coexist with frozen `expected_*` on WorkerStageContribution. V2-2 has no locked plan for allocation-era `WorkerLedgerEntry` rows (void / coexist / map into AddaSettlement). | HIGH | Certain if V2-2 starts unplanned | expense + production | Lock cutover ADR before any V2-2 code (§9.1) |
| R2 | **V2-1d M2M drop = point of no return** taken before task data is proven by real use (pt.2b UI has zero callers yet) or a dual-write reconciliation check. | HIGH | Low (already gated by plan) | production 0034+ | Soak dual-write through pt.2b usage; add M2M↔task parity assertion before drop |
| R3 | **reverse_settlement gap is now load-bearing.** PayrollSettlement conflates settle+pay+recovery atomically; recovery items cannot be compensated — a wrong settlement permanently reduces advance outstanding. | MED | Med (manual ops) | expense | Fold into V2-2 reversal design (draft→finalized→reversed lifecycle already locked); don't patch pre-V2 |
| R4 | **Deployment blockers** (no CACHES → per-process rate limiter; argon2-cffi & gunicorn missing from requirements; SSL-redirect proxy loop; prod media unsolved). | HIGH on deploy day, LOW today | Certain at first deploy | settings/infra | One small pre-deploy PR (§5 checklist); not urgent now |
| R5 | **~30 hardcoded stage-key sites** (4 template elif chains, per-stage view modules, layering-only auto-start) vs pending stage-taxonomy redesign — every new stage shipped on the old pattern raises redesign cost. | MED | Med | production views/templates | Stage-domain review decides target; until then route new code through handler registry only |
| R6 | **Doc-truth drift** — ARCHITECTURE_V2 header "design only" stale; §2 vs §11.3 WorkerAdvance.adda contradiction; SYSTEM_DESIGN scan-flow shows `mark_status` path that has no URL/view (missing status is unsettable from UI); "292 tests" memory vs 417 actual. This review itself tripped on it. | MED | Certain | docs | Phase R0 reconciliation (§7) |
| R7 | Scale: mgmt dashboard lists ALL in-progress Addas unpaginated; costing view builds full-table per-Adda aggregate dicts in memory (rows capped at 200, memory not). Query counts flat (perf baselines locked) but memory/render degrade at 100k Addas. | LOW now | High at 10k+ | inventory/production views | Read-model/pagination seam later (ADR 0006) — document, don't build |
| R8 | Test-discovery footgun: running `manage.py test` from repo root silently discovers 0 tests and exits 0. mypy island report-only with ~242 open violations. | LOW | Sneaky | tooling | Note in docs; ratchet stays advisory |

## 3) Decision Matrix (KEEP / MODIFY / DEFER / REJECT)

### KEEP (verified locked + correct)
| Decision (master-context §) | Evidence |
|---|---|
| Production Truth ≠ Financial Truth; Option B (no ledger until settlement; expected_* = visibility) — §2.1, §6.1-6.2 | ARCHITECTURE_V2 §5, ADR 0005; `expected_*` built+frozen by `complete_worker_task`, books NO ledger (verified) |
| Adda-centric architecture; settlement Adda-rooted — §2.2, §3.5 | §11.0 Model A + WRAP locked |
| Settlement ≠ payment; partial/multiple/later payments; recovery at settlement only — §6.3, §6.5 | §11.0 d1, locked term 1 |
| Advances = separate loan pool, never merged into earnings — §3.6 | Matches built code exactly (no ledger debit on issue; owner-controlled per-advance recovery) |
| Append-only / immutable history; cancel-not-delete — §2.5 | ADR 0004, V2_1 Q2/R3, built (task cancel terminal) |
| Migration-safe increments: backfill-known-facts-only, dual-write flag, reversible-until-drop, clone rehearsal — §2.6, §12 | All five elements owner-locked AND executed in V2-1a (verified) |
| Assignment-based object-level worker access — §2.4, §4.4 | **Already built** (V2-1c-iv): `StageViewAccessMixin` assignment gate (production/views/mixins.py:35-45), dashboard `worker_tasks__worker` scoping, `_ensure_assigned_worker` service guard, payroll `can_view_worker` self-scope, costing management-only |
| Stage-driven contribution schema (`StageHandler.contribution_schema()`); no speculative universal schema; additive JSONB only on real need — §5, §7 | F1 locked AND hook built (handler.py:106 + CuttingHandler override) |
| Draft = operational, Submit = business truth; draft never affects readiness/costing — §4.2 | Built: `is_draft` + `save_draft_contributions` replace-semantics; truth begins at complete |
| Worker report UI: locked read-only after submit, no other-worker progress, no money on worker screens — §7 | D1-D8 owner decisions; money screens verified management-gated |
| factory_absorbs launch variance policy; no premature attribution engine — §6.4 | §11 locked; verified no deduction writer exists |
| Missing/Alter = future first-class lifecycle domains; settlement consumes summaries — §3.7, §3.8, §8 | §11.11 locked; code unconstrained (nothing reads missing counters in money math — verified) |
| Stage engine open-closed as DIRECTION; current stages = reference implementations — §2.3, §15 | Engine framework built + open-closed proof test; taxonomy review agendized |
| Deployment seeds not infrastructure (stateless, storage abstraction, job boundaries, env config) — §17 | Mostly present (§5); remaining items are small fixes, not architecture |
| Domain events as documentation vocabulary, not infra — §19 | Correct posture; *History tables + request-id logs cover audit today |
| Multi-factory: reserve boundary only — §20 | Matches locked `current_factory()` chokepoint seam (TARGET_ARCHITECTURE) |

### MODIFY (claim wrong or stale — corrections verified)
| # | Claim | Correction | Risk of keeping as-is | Migration impact | Implementation impact | Long-term benefit |
|---|---|---|---|---|---|---|
| M1 | §11/§12: "V2-1a in progress", contribution deferred | V2-1a/1b/1c BUILT+COMMITTED (e4953ef9…cfdb2d26; migrations 0031-0033 applied; 417 green). Pending: pt.2b/2c UI, V2-1d, V2-2, V2-3, Missing/Alter | Future reviews re-decide already-shipped things; wasted cycles (happened in this review) | None | Doc edits only | Accurate baseline for every future chat |
| M2 | §3.3: task lifecycle = 4 statuses | FIVE: assigned/in_progress/completed/**verified**/cancelled; `verified` optional, never a gate (worker_task.py:32-39) | Future code written against 4-status enum breaks invariants | None | Doc edit | Schema truth |
| M3 | §3.4-adjacent + "WorkerStageTask/Contribution replace SWA" implication | SWA **RETAINED** (locked §11.4): repurposed at finalize as the settlement-written earning line backing every `WorkerLedgerEntry.assignment` PROTECT credit; no removal migration | Someone deletes/deprecates SWA → breaks locked ledger traceability design | Avoids one (no SWA drop migration) | V2-3 = repurpose, not removal | Zero ledger schema churn |
| M4 | §4.3: "Stage advance should not depend on verification today" | Two different "verifications": per-worker task `verified` status — correct, never gates. But **CuttingPatternVerification IS a hard completion gate** for the cutting_pattern stage (complete_pattern_stage requires all pattern assignments verified) — shipped, owner-built behavior | Blanket rule applied literally would rip out a deliberate quality gate | None now | Reword: task-level verification never gates; stage-specific completion validations MAY (stage-domain review owns the final rule) | Keeps open-closed: gates live in stage handlers, not core |
| M5 | §3.2: AddaStageRecord "tracks stage lifecycle" (implies status field) + costing placement assumptions | Lifecycle is timestamp-derived (no status column — matches derived-not-stored principle); `cost_billed_at` lives on WorkflowStage, frozen cost snapshots on the record | Wrong field assumptions in future designs | None | Doc edit | Accurate ER baseline |
| M6 | §12 framing "dual-write can be feature-flagged" (future tense) | Flag exists and is ON (`WORKER_TASK_DUAL_WRITE`, base.py:177, env kill-switch); M2M still authoritative until V2-1d | Mis-sequenced V2-1d planning | None | Doc edit + add reconciliation check before drop (§9.2) | Safe drop |

### DEFER (master-context already defers — confirm correct)
Stage taxonomy + machine sub-stage hierarchy (STAGE_DOMAIN_REVIEW_AGENDA owns it) · MissingPieceCase/AlterCase schemas (capture-seams exist; dimensions backfillable, lifecycle facts intentionally not) · barcode ownership (P4.2 parked — relocation not data migration; barcode models stay in tracking per D3) · piece-level traceability strategy · final RBAC refinement beyond shipped isolation · microservice boundaries (ADR 0006: seams only) · attributes JSONB column · read models/materialized views · job-queue infrastructure (boundaries identified in §5; build nothing) · multi-site columns.

### REJECT
Nothing in the master-context needs outright rejection. One adjacent item to kill in DOCS: **ARCHITECTURE_V2 §2/§10 "add WorkerAdvance.adda FK"** — already explicitly REJECTED by locked §11.3 ("Do not add it"); §2/§10 were never reconciled. Fix in Phase R0 so nobody builds it from the stale section.

## 4) Foundation Gaps (real, evidence-backed)

1. **Ledger cutover policy missing (R1)** — the single biggest unlocked decision. Options to decide: (a) leave allocation-era ledger rows untouched, AddaSettlement only for new Addas after cutover date; (b) void-and-rebook via compensating entries; (c) retro-map old rows to synthetic AddaSettlements. §11.9's double-credit invariant must be defined over historical rows too.
2. **reverse_settlement unbuilt** while PayrollSettlement conflates settle+pay+recovery (R3). Documented as deferred; now blocking-adjacent for V2-2 design.
3. **Missing-piece flow is dead in UI**: `mark_status` has zero view/URL callers — MISSING status is display-only plumbing; SYSTEM_DESIGN.md:260 scan-flow diagram documents a path that doesn't exist. When the UI lands, capture detection-stage + detection-date at mark time (owner backfill rule: facts not captured now can never be backfilled).
4. **Open-closed partial in practice**: framework genuinely open-closed (registry + autodiscover + proof test) but ~30 hardcoded stage-key sites, 4 template elif chains, per-stage view modules, layering-only auto-start in adda_service. Contain: new stages/views go through the registry; cleanup priced into stage-domain review.
5. **Contribution pipeline has no UI caller** (pt.2b) — production-truth path is built but unexercised by real users; V2-1d must wait for usage soak.
6. **No dual-write reconciliation assertion** (M2M set == active task set) and kill-switch mid-flight semantics undefined — needed before V2-1d.

## 5) Deployment Readiness Review

**Seams (already correct):** settings split base/local/production + python-decouple (.env for SECRET_KEY/DB/hosts/email/OAuth; no hardcoded secrets found); DB-backed sessions; RBAC caches request-scoped (deployment-safe); uploads via Django Storage API; whitenoise for static; request-id-correlated logs + dedicated security.log; no sqlite; no process-global business state found.

**Blockers (fix in ONE small PR before any real deploy — not now):**
1. `CACHES` unset → LocMemCache → **auth rate limiter broken multi-worker** (per-process counters). Add Redis cache backend + redis dep.
2. `argon2-cffi` not in requirements.txt (venv-only) → clean deploy cannot verify any password.
3. `SECURE_SSL_REDIRECT=True` without `SECURE_PROXY_SSL_HEADER` → redirect loop behind any proxy/PaaS.
4. Production media unsolved (`/media/` only when DEBUG) → uploaded images 404 in prod. Whitenoise covers static only.
5. No WSGI server pinned (gunicorn). RotatingFileHandler multi-process unsafe → ship logs to stdout in prod config.

**Job-queue candidates (boundaries only, build later):** barcode print-sheet (one QR PNG per piece per request), CSV/XLSX/PDF exports (full piece expansion), future settlement finalize. All already behind service functions = clean future Celery/Dramatiq seam.

**Path Monolith→Docker→multi-container:** nothing architectural blocks it once the 5 items above land. Do not start Docker/K8s work now (matches §17).

## 6) Phased Roadmap (review-first; each phase ends with re-review)

| Phase | Content | Type | Gate to pass first |
|---|---|---|---|
| **R0** | **Doc-truth reconciliation + cutover decision lock** (details in §7) | docs + 1 ADR | none |
| **R1** | Stage-domain review (already agendized): taxonomy, responsibilities, machine sub-stages, missing/alter lifecycles, costing implications | review | R0 (clean baseline) |
| **P2** | pt.2b worker report UI + pt.2c dashboard badges (design + mockup already approved, D1-D8 locked) | build | R1 outcome confirms contribution shape |
| **P3** | V2-1d: drop `AddaStageRecord.workers` M2M (**point of no return**) | build/migration | dual-write soak through P2 usage + reconciliation assertion green + clone rehearsal |
| **P4** | V2-2: AddaSettlement build (incl. reversal lifecycle, §11.9 invariants, finalize lock order) | build | R0's cutover ADR locked; reverse-design covers R3 |
| **P5** | V2-3: SWA repurpose (settlement-written earning line) + retire allocation-time crediting | build | P4 live |
| **P6** | MissingPieceCase + AlterCase modules; wire `mark_status` UI with detection metadata; settlement consumes summaries | build | P4/P5 + R1 lifecycle designs |
| **PD** | Deploy-blocker PR (§5 items 1-5) — slot ANY time before first real deployment, independent of P2-P6 | build (small) | none |

P4.2 barcode cycle-break: stays PARKED until after R1 (per owner decision; code relocation, not data migration).

## 7) Recommended First Phase: R0 — Doc-Truth Reconciliation + Cutover Decision Lock

**Content (docs only, zero migration, zero behavior change):**
1. Fix ARCHITECTURE_V2.md line-3 header (worker-tracking BUILT through V2-1c; §11 settlement design-only).
2. Reconcile §2/§10 vs §11.3 WorkerAdvance.adda contradiction (delete the "add adda FK" lines; §11 wins).
3. Update V2_1_REVIEW §10 "NOT committed" note; CLAUDE.md "In progress (V2-1a)"; stale test counts.
4. Fix SYSTEM_DESIGN.md:260 scan-flow (mark_status has no UI path today) + UI_PATTERNS "reprint flow" caveat.
5. Regenerate ERP_MASTER_CONTEXT.md with this review's corrections (M1-M6) so the master baseline is true.
6. **Write ADR 0007: allocation-era ledger cutover policy for V2-2** — owner picks (a) coexist-with-cutover-date / (b) void-and-rebook / (c) retro-map. Define §11.9 double-credit invariant over historical rows. This is the one genuinely unlocked decision blocking future build phases.
7. Define V2-1d preconditions in the ADR/agenda: reconciliation assertion (M2M == active tasks), kill-switch semantics, soak criteria.

**Why first:** every later phase (R1 review, P2-P6 builds) reasons from these documents; this review itself burned cycles on the stale/contradictory baseline. Cheapest possible phase, removes the highest-frequency risk (R6), and unblocks V2-2 planning (R1's biggest dependency) without writing any code. Honors review-first: it is pure decision/record work.

**Risks:** near-zero. Only risk = mis-stating a decision while reconciling — mitigated because every correction here is adversarially verified with file:line evidence (see STATE file).

**Dependencies:** none. All inputs exist in-repo.

**Success criteria:** doc-accuracy guard green; no doc contradicts code or another locked doc; ADR 0007 signed by owner; V2-1d precondition list agreed; master-context regenerated and re-attachable to future chats as a true baseline.

**⏹ STOP.** Implementation (even R0's doc edits) begins only after explicit owner approval.

## 8) Risks To Avoid

- Building V2-2 before the cutover ADR (R1 risk realizes immediately).
- Dropping the M2M (V2-1d) before pt.2b real-usage soak + reconciliation assertion.
- Patching reverse_settlement on the pre-V2 model instead of folding reversal into V2-2's locked lifecycle.
- Adding the attributes JSONB, deduction engine, factory columns, or job queue speculatively (ADR 0006: seams, not features).
- Shipping any new stage via copy-paste view module + template elif (raises taxonomy-redesign cost).
- Deploying with LocMem rate limiter / venv-only argon2 (silent security failure).
- Trusting a root-dir `manage.py test` run (0 tests, exit 0).

## 9) Decisions That Must Be Locked BEFORE Coding (per phase)

1. **ADR 0007 ledger cutover** (before any V2-2 code) — §4.1.
2. **V2-1d preconditions** (before the drop migration): reconciliation check, kill-switch semantics, soak window.
3. **Verification-gate wording** (before R1 closes): task-level `verified` never gates; stage-level completion validations may — confirm or change CuttingPatternVerification's hard gate.
4. **reverse_settlement placement**: confirmed as part of V2-2 reversal design (not a pre-V2 patch).
5. **Missing detection metadata** (before mark_status UI ships): detection stage + date + actor captured at mark time.

## 10) Decisions That Should REMAIN Deferred

Stage taxonomy + machine sub-stages (R1 owns) · MissingPieceCase/AlterCase schemas · attributes JSONB · barcode ownership / P4.2 · piece-level traceability · RBAC refinement beyond shipped isolation · microservice boundaries · multi-factory columns · read models / dashboards pagination strategy · background-job infrastructure · Docker/K8s.

## 11) Long-Term Rewrite Risks

1. **Stage-key hardcoding compounds**: each stage shipped on the bespoke-view + template-elif pattern multiplies R1 redesign cost. Contain now via registry-only rule for new code.
2. **Settle/pay conflation lives until P4**: every PayrollSettlement created meanwhile is history that V2-2 must re-home (nullable `adda_settlement` FK already planned — adequate seam, but volume grows with time).
3. **Un-capturable facts**: missing-piece lifecycle facts (detection stage/date) not recorded today can never be backfilled under the owner's known-facts-only rule. Risk crystallizes the day Missing module ships; cheap to pre-empt in mark_status UI.
4. **Scale cliffs** (R7): unpaginated mgmt dashboard + costing's in-memory full-table aggregates — query-flat but memory-bound; needs read-model seam around 10k+ Addas.
5. **mypy ratchet decay**: 242 island violations, report-only — if never ratcheted, the typed island erodes into documentation.

## 12) Microservice Extraction Readiness

**Posture: correctly boundary-shaped monolith. Extraction later is plausible; nothing should be extracted now.**

Working in favor: service layer owns all writes (ADR 0001); single-writer per ledger/history table (ADR 0002); tracking = append-only history primitive (ADR 0004); planned production→expense one-way facade in exactly one file (TARGET_ARCHITECTURE); env-based config; DB sessions; request-scoped auth caches; domain-event vocabulary documented.

Blocking extraction today (known + parked deliberately): production↔tracking import cycle (P4.2 — relocation-class fix); expense's `allocation_service` writing money from production workflow (dies at V2-3); dashboard queries joining across app boundaries (read-model seam later); LocMem cache (PD phase).

Most extractable first (post-V2): **Settlement service** (Adda-keyed, ledger-mediated) and **Missing/Alter modules** (designed as modules from day one). Hardest: identity/RBAC (sidebar middleware + skill gates woven through views).

Verdict: matches §10/§17 of the master-context — keep reserving seams, extract nothing.

---

*Evidence and per-claim verdicts: `docs/ERP_MASTER_CONTEXT_REVIEW_STATE.md`. Review conducted per the Existing Decisions Policy (no redesign of locked decisions) and Phase Execution Policy (STOP before implementation).*
