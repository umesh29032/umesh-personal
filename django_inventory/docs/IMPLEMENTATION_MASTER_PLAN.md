---
id: docs-implementation-master-plan
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Implementation Master Plan — Kapil Enterprises ERP

**Status:** governing execution plan. Replaces the audit process (Phases A–I complete). Foundation design is **LOCKED** — not re-opened here. No implementation in this document.

**Inputs:** Phases [A](audit_phases/PHASE_A_core_manufacturing_flow.md)–[I](audit_phases/PHASE_I_edge_cases_integrity.md), [FOUNDATION_LOCKED](PRODUCTION_TRUTH_FOUNDATION_LOCKED.md), [FOUNDATION_ROADMAP](PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md).

**Locked (treat as given):** AddaStageRoleRate · WorkerStageAllocation · Strict mode only (Open deferred) · good/alter/missing · allocation-bounded reporting · `Good + Recovered-Alter − allocated` pool · Adda-level rate snapshots · settlement-first · existing financial architecture.

---

## Recommendation up front (the final question)

**B — Ship the current system to staging after the P0 fixes, THEN build the Foundation.** Justification (audit evidence only) is in the last section. Short form: the money engine **reconciles and is hardened** (Phase B + I), the one HIGH production-truth risk (over-report) is **process-mitigatable + already visible** during staging, the foundation is a **multi-sprint** effort whose worker-facing UX is **better designed after observing real usage**, and staging exists to produce exactly that feedback. P0 is small.

---

## Finding classification (every A–I finding, one bucket each)

### P0 — Must fix before staging (defects / security / integrity / deploy blockers)

| ID | Source | Summary | Why P0 | Effort | Deps |
|----|--------|---------|--------|--------|------|
| P0-1 | A-2 | `GET /expense/settlements/start/<pk>/` → 500 (POST-only TemplateView, no template) | Real crash, trivially hit (bookmark/refresh); #1 likely breakage | S | — |
| P0-2 | G-SEC-1 | DEBUG off in staging/prod + register `handler403/404/500` | Info-disclosure on any 500; deploy blocker | S | — |
| P0-3 | E-2 | Align `LEDGER_CREDIT_AT_ALLOCATION` getattr fallbacks to `False` (allocation_service:66 is `True`) | Latent money split-brain vs documented settlement-first default | S | — |
| P0-4 | E (state) | Apply/confirm `tracking 0014` migration; verify schema head == running | Running schema ≠ migrated head; surfaces at deploy | S | — |
| P0-5 | I-2 | `complete_worker_task`: `select_for_update(task)` + re-check status | Stage-complete race can strand worker pay (unpaid) / resurrect cancelled task; **foundation precursor** | S | — |

### P1 — High ROI before foundation (small, no foundation conflict)

| ID | Source | Summary | Reason | Effort | Deps |
|----|--------|---------|--------|--------|------|
| P1-1 | C-1, H-4 | Role-based landing → owner/manager to operational dashboard + a **morning digest** (stalled + due-to-settle + yesterday output + pending payable) | Owner's 30-sec pulse; today they land on an empty worker view | M | — |
| P1-2 | C-2, C-3, C-4, D-3 | Sidebar: move Production under Main, dedupe the two "Dashboard" items, add Payroll/Settlements entries (also fixes mobile drawer depth) | Core flow buried; finance pages URL-only | S–M | — |
| P1-3 | C-5, G-UX-1 | One branded denial (use the `handler403` from P0-2) instead of bare 403 | Consistent denial UX | S | P0-2 |
| P1-4 | D-1 | Buttonize per-card actions ("Settle" etc.) ≥44px | Mis-tap risk on the money action | S | — |
| P1-5 | G-AUTH-1 | Isolate history routes to assigned Addas (or management-only) | Worker can read any Adda's history by URL | S–M | — |
| P1-6 | H-2 | **Stalled-Adda alert** (Adda/stage idle > threshold) | Highest-ROI report; built on existing timestamps | M | — |
| P1-7 | H-7 | Advance-exposure overview (total + top debtors) | Cash-flow control; today's data | S–M | — |
| P1-8 | H-6, F-3 | "Who hasn't reported" queue per active stage | Chase work before stages auto-cancel; today's data | M | — |
| P1-9 | A-1, I-4 | Guard non-numeric quantity → ValidationError (contained by atomic; UX only) | Stops a 500 on odd input | S | — |
| P1-10 | A-3 | Friendly "stage not started" page instead of raw 404 | Stale-link UX | S | — |
| P1-11 | I-3 | DB partial-unique `(adda, status=draft)` backstop | Defense-in-depth beyond the PG advisory lock | S | — |
| P1-12 | E-1 | Correct ARCHITECTURE_V2 §5/§6 (variance does NOT reduce payable today) | Doc tells the truth about factory_absorbs | S | — |
| P1-13 | B-4, I-5 | (optional) populate `WorkerLedgerEntry.settlement` FK | Direct "ledger for settlement X" query | S | — |

### P2 — Foundation work (S1 → S5)

| ID | Source | Summary | Maps to |
|----|--------|---------|---------|
| P2-1 | (resolver) | `settlement_quantity(c, policy)` abstraction, default = current | S1 |
| P2-2 | A-5 | Adda-start rate copy + first-completion lock + **block finalize on unpriced payable stage** | S2 |
| P2-3 | (fields) | `good_quantity` / `alter_quantity` / `missing_quantity` + constraint loosen | S3 |
| P2-4 | (allocation) | `WorkerStageAllocation` (Strict) + pool fn (`good + recovered(0) − allocated`) + audit history | S4 |
| P2-5 | B-1, I-1, A-4, I-6 | Allocation-bounded reporting ENFORCE (kill the over-report) + retire `reported_quantity` | S5 |
| P2-6 | E-3 | Cross-link ARCHITECTURE_V2 §11 + TM-1 → foundation docs (DOCS-SYNC) | each sprint |

### P3 — Post-foundation (depend on the new data model)

| ID | Source | Summary | Why P3 |
|----|--------|---------|--------|
| P3-1 | H-1 | Stage-by-stage loss/shrinkage report | Needs good/alter/missing (S3) |
| P3-2 | H-9 | Loss-cost rollup (₹ of missing/rejects per Adda/stage/worker) | Needs S3 data |
| P3-3 | H-5 | Worker productivity ranking incl. missing/alter frequency | Needs S3 data |
| P3-4 | B-2 | Standard-vs-actual labor **variance report** (ADR-0009's declared home) | Meaningful once reconciled |
| P3-5 | B-3 | (if chosen) `deduct_rejected` variance policy — only **after** B-1 reconciliation | Trustworthy counts first |
| P3-6 | F-1, F-2 | Cross-Adda assignment monitor + assignment-intent visibility | Allocation rows make intent persistent |

### P4 — Future / defer

| ID | Source | Summary |
|----|--------|---------|
| P4-1 | H-8 | Adda profitability (cost vs sale revenue) — commerce linkage, ADR-0008 |
| P4-2 | G-AUTH-2 | Decide whether a finance-settlement role is wanted (today: management settles) |
| P4-3 | C-7 | Global Adda search/quick-jump (at volume) |
| P4-4 | D-2 | Access-hub matrix mobile view |
| P4-5 | F-4 | Workload-balancing visibility |
| P4-6 | H-10/11/12 | Throughput trend · cloth yield · daily digest push |
| P4-7 | C-6, C-8 | Completed-Adda stage label "—" · filter loading state |
| P4-8 | G-AUTH-3 | (no action — confirm management skill-gate bypass is intended) |

---

## Recommended implementation order

1. **P0 (all 5)** — staging unblock. ~2–3 days.
2. **Staging deploy** + operational discipline: use `review-reports/` to verify quantities before settling (mitigates the over-report window until S5). Collect real worker/manager usage.
3. **P1-1, P1-2, P1-3, P1-4** (landing + nav + denial + tap targets) — the staging-experience wins. ~1 week.
4. **P1-6, P1-7, P1-8** (stalled alert + advance exposure + pending reports) — operational visibility on existing data.
5. **P1-5, P1-9..P1-13** (history isolation + hardening + doc fix).
6. **Foundation Sprints 1→4** (P2), informed by staging usage — see below.
7. **P3** (reports/monitors over the foundation data).
8. **P4** as needed.

---

## Foundation plan (LOCKED roadmap → sprints)

### Foundation Sprint 1 — S1 (settlement resolver) + S2 (AddaStageRoleRate) + P0-5 precursor
- **Migrations:** `production 0037` AddaStageRoleRate `(adda_stage_record, role, rate, locked_at)`; data migration backfill rate from existing `WorkerStageContribution.expected_rate` (completed) / current workflow rate (in-progress, flag for review).
- **Services:** `settlement_quantity(c, policy)` resolver (default = `verified ?? reported`, byte-identical); `adda_service` copies rates at Adda-start; `complete_worker_task` + settlement read the frozen Adda rate (fallback workflow rate if no snapshot); `cost_service.role_rate_for` unchanged (standard cost untouched). **P0-5:** `select_for_update(task)` in `complete_worker_task`.
- **Views:** Adda-start rate review/edit (management); finalize/preview use the resolver.
- **Templates:** Adda-start rate-review screen (mobile-ok).
- **Tests:** golden — ₹225 supersede chain **identical** before/after S1 + S2; rate locks at first completion; backfill correctness; historical settlement numbers unchanged; P0-5 race test (concurrent complete vs stage-complete).
- **Rollout risks:** resolver must be behavior-preserving (golden-gated); rate-source change must not move historical numbers (fallback); in-progress-Adda rate backfill flagged, not invented.

### Foundation Sprint 2 — S3 (good / alter / missing + constraint loosen)
- **Migrations:** add `good_quantity`, `alter_quantity`, `missing_quantity` (nullable, default 0); **swap** `wsc_reported_quantity_positive` → `good/alter/missing ≥ 0 AND sum > 0` (a **loosening** — safe on existing rows); backfill `good_quantity ← reported_quantity`. (Do **not** drop `reported_quantity` yet.)
- **Services:** report/complete write good/alter/missing; `worker_summary` + "pieces" read `good`; earnings = `good × frozen rate`.
- **Views/Templates:** worker self-report form gains Good/Alter/Missing inputs (this is the carved-out screen — designed here, mobile-first, `type=number`+`inputmode`); My Earnings shows the split.
- **Tests:** constraint loosening against a prod-shaped dump; backfill exactness; zero-good+alter>0; all 18 read-sites migrated to `good_quantity`; flag-free (no enforcement yet).
- **Rollout risks:** constraint swap atomicity; read-site sweep completeness; rename semantics (column kept, aliased).

### Foundation Sprint 3 — S4 (WorkerStageAllocation + pool, Strict, no enforcement)
- **Migrations:** `WorkerStageAllocation (stage_record, worker, color, size, allocated_quantity, allocated_by)`; `WorkerStageAllocationHistory` (append-only); index `(stage_record, color, size)`.
- **Services:** allocation service (allocate / reassign / top-up / reduce-≥-reported), audited via `history_service` (single-writer, rule 5); **pool-derivation fn** future-shaped `Σ good + Σ recovered(=0) − Σ allocated`; low-friction **auto-even-split** default; `select_for_update` on allocation rows.
- **Views/Templates:** manager allocation screen (the carved-out assignment screen — designed here; Strict, auto-split then adjust; mobile + desktop).
- **Tests:** pool derivation (incl. recovered term present, =0); `Σ allocations ≤ pool`; reduce-below-reported rejected; re-cut raises pool; reassign moves bound; allocation-history audit; auto-split.
- **Rollout risks:** name `WorkerStageAllocation` deliberately vs `expense.StageWorkAssignment` (truth vs money — document both); pool query cost (indexed); no enforcement yet (safe to populate live).

### Foundation Sprint 4 — S5 (allocation-bounded reporting ENFORCE) + FINAL cleanup
- **Migrations:** feature flag (setting, default off); **FINAL:** drop `reported_quantity` (only after all reads use `good_quantity`, tested, a release later).
- **Services:** report/complete **enforce** `good+alter+missing ≤ allocation` (Strict); color/size taken from the allocation; allocation draw-down `select_for_update` (P0-5 pattern pays off — no double-consume); forward-only (new Addas).
- **Views/Templates:** worker report form bounded — cap **never** sent to client; generic over-limit error.
- **Tests:** over-report rejected; cap not leaked to client; flag-off = exactly old behavior; historical (no-allocation) Addas still settle; concurrency — two reports drawing one allocation can't jointly exceed.
- **Rollout risks:** behavior change (flag = instant kill-switch); worker retraining; the `reported_quantity` drop (last, tested, non-additive — safe pre/early-staging); bimodal old/new Addas.

---

## Final question — A vs B, justified by audit evidence

**Chosen: B — staging after P0, then foundation.**

Evidence for B:
- **Money is safe to run now.** Phase B: every settlement/earning/ledger/reverse calculation **reconciles to the rupee** (₹225 chain across 2 reversals); Phase I: settlement path is **atomic + advisory-locked + ordered row-locks + up-front-validated + double-credit-guarded**, `on_delete=PROTECT` everywhere (no orphan/cascade loss), production truth immutable + append-only audit ("an auditor can reconstruct 6 months later"). Nothing here corrupts under real load.
- **The one HIGH risk is bounded and visible during staging.** The over-report (I-1/B-1, ₹45 on one Adda) is real but: (a) management can catch it with the **existing verification surface** (`review-reports/`, A-4) before settling; (b) the **costing page already surfaces** the standard-vs-actual divergence (₹315 vs ₹360) so it's not hidden; (c) the foundation is **forward-only + backfill-known-facts**, so staging data won't be made un-migratable. It's process-mitigatable for a small-scale staging window.
- **Foundation UX needs real usage first.** The two screens the foundation redesigns (worker self-report, manager allocation) are exactly where observing real worker behavior improves the design. Building them blind, pre-staging, risks rework — the carve-out decision already implies "design these with the foundation," and staging is the cheapest way to learn the allocation friction tolerances (auto-split defaults, Strict ergonomics).
- **Foundation is large (4 sprints); P0 is ~days.** Blocking staging on S1–S5 delays the validation staging exists to provide, for a system that's already financially sound.

Evidence weighed against B (why not A):
- A's only strong argument is "prevent any over-report from ever happening." But the audit shows that risk is **operationally containable + visible + reversible**, not a silent corruption. No Phase A–I finding shows data that staging would make **unrecoverable**. So A's safety premium isn't justified by the evidence.

**Condition on B:** ship only after **all P0**, and run staging with the verification-before-settle discipline until S5 lands. Then build the foundation informed by staging usage, S1→S5 in order, each behind its golden tests / feature flag.

---

## Doc-sync note
When implementation starts, add a CLAUDE.md pointer to this plan + the foundation docs, and apply the per-sprint DOCS-SYNC updates (P2-6). Not done now (planning-only).

**This is the single execution plan. Audit mode closed.**
