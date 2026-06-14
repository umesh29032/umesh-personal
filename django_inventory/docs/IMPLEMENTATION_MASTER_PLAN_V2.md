# Implementation Master Plan V2 — Kapil Enterprises ERP

**Supersedes** [IMPLEMENTATION_MASTER_PLAN.md](IMPLEMENTATION_MASTER_PLAN.md). Incorporates the accepted risk-review corrections RC-1…RC-8 + mandatory gates MT-1…MT-8 from [IMPLEMENTATION_RISK_REVIEW.md](IMPLEMENTATION_RISK_REVIEW.md). Governing execution plan. **No implementation in this document.**

**Locked (not reopened):** AddaStageRoleRate · WorkerStageAllocation · Strict-only (Open deferred) · good/alter/missing · allocation-bounded reporting · `Good + Recovered-Alter − allocated` pool · Adda rate snapshots · settlement-first · existing financial architecture.

---

## 0. Resolved decisions (the V2 deltas)

### RC-1 — Staging-data lifecycle: **DISPOSABLE.**
- **Staging data is throwaway. It is NEVER promoted to production.** Production starts from a **clean database** once the foundation is built + validated.
- **Foundation migrations + backfills must still be designed and tested for production-scale datasets** (batched, idempotent, scale-tested on a synthetic prod-size fixture). We do not write throwaway migration code.
- **The "safe because only ~4 rows" justification is removed everywhere.** Migration safety now derives from: additive design + tested backfills + a pre-migration backup (MT-1) + soak windows — **not** from data smallness. (Resolves the V1 contradiction: B is now internally consistent because staging data never becomes the thing the migrations run against in prod.)

### RC-2 — Foundation S5 split into S5 + S6.
- **S5 = allocation-bounded reporting ENFORCEMENT only** (feature-flagged, forward-only, reversible by flag-off).
- **S6 = `reported_quantity` retirement + column DROP.** Separate, late step. Requires: MT-1 backup, a production **soak period** after S5 is proven, an explicit **rollback review**, and **production validation** that nothing reads `reported_quantity`. **Not flag-reversible** — treated as a one-way migration with backup as the only rollback.

### RC-3 — Constraint sequencing (S3), no insert can fail on legacy constraints.
- In **S3**, when adding `good_quantity`/`alter_quantity`/`missing_quantity` + the new check (`each ≥ 0 AND sum > 0`): **drop the legacy `wsc_reported_quantity_positive` constraint in the same migration**, and **dual-write `reported_quantity = good_quantity`** on every new write until S6.
- Result: `reported_quantity` stays populated + valid through S3→S5 (legacy reads keep working), and no allocation-era insert can fail on a stale `reported_quantity > 0` / NOT-NULL constraint. The column is only emptied of meaning at S6 (drop).

### MT-1…MT-8 — mandatory execution gates (cannot skip)
| Gate | Requirement | Applies to |
|------|-------------|-----------|
| MT-1 | **DB backup** taken + restore-tested before the migration runs | every migration (S1,S2,S3,S4,S6) |
| MT-2 | Staging-data lifecycle = **disposable** (RC-1) — declared, enforced | one-time, up front ✅ resolved |
| MT-3 | **Prod-config checklist** green: `DEBUG=False`, `ALLOWED_HOSTS`, `collectstatic`/static serving, 403/404/500 templates render, correct settings module | staging-deploy gate |
| MT-4 | **Migration 0014 verified non-destructive** on populated `addahistory` (no row reject/loss) | P0-4 |
| MT-5 | **Staging DB engine == prod (PostgreSQL)** confirmed | staging-deploy gate |
| MT-6 | **Realistic multi-worker concurrency/load test** of allocation draw-down passes | S5 gate (before enforce) |
| MT-7 | **PKALS `canonical_manifest` / CHANGE_IMPACT_MATRIX regenerated** + DOCS-SYNC applied | every sprint |
| MT-8 | **Un-reviewed flagged-rate Adda cannot settle** (default gate) | S2 |

### RC-4 — AddaStageRoleRate backfill tie-break (folded into S2)
- Per `(stage_record, role)` may map to multiple frozen `expected_rate`s (drift). Backfill rule: **pick the most-recent completed contribution's rate; if rates conflict within a (stage_record, role), flag the Adda for owner review** and apply MT-8 (no settle until reviewed).

### Items NOT changed in V2 (out of the accepted RC-1…RC-8 set)
- P0-3 stays **P0** (RC-10 reclassify not accepted).
- `settlement_quantity` resolver stays in S1 (RC-9 acknowledged as deliberate forward-investment).
- RC-11 (physical bundle reveals count) + RC-12 (retrain twice) — acknowledged operational notes, no plan change; see Remaining Risks.

---

## 1. Buckets (unchanged from V1 except where noted)

**P0 — pre-staging blockers:** P0-1 settlement-start 500 · P0-2 DEBUG-off + handlers (now gated by MT-3) · P0-3 LEDGER fallback align (stays P0) · P0-4 migration 0014 (gated by MT-4) · P0-5 `complete_worker_task` task-lock (foundation precursor).

**P1 — high-ROI before foundation:** P1-1 role landing **→ staging bundle** · P1-2 nav cleanup **→ staging bundle** · P1-3 branded denial · P1-4 tap targets · P1-5 history isolation · P1-7 advance exposure · P1-8 who-hasn't-reported · P1-9 input guard · P1-10 not-started page · P1-11 dup-draft backstop · P1-12 ARCH_V2 doc fix · P1-13 ledger FK (optional).

**P1.5 (was H-2, HIGH) — stalled-Adda alert → staging bundle.**

**P2 — foundation (S1→S6):** resolver · AddaStageRoleRate+unpriced-block · good/alter/missing+constraint-sequence · WorkerStageAllocation+pool · enforce · retire/drop.

**P3 — post-foundation:** stage-loss · loss-cost · productivity · variance report · deduct-rejected (after B-1) · assignment monitor.

**P4 — defer:** profitability · finance-role decision · global search · matrix-mobile · workload · throughput/yield/digest · minor UX.

---

## 2. Recalculated implementation order

**Step 1 — Staging bundle** (must clear MT-3, MT-4, MT-5 before deploy):
1. P0-1 settlement-start 500
2. P0-2 DEBUG-off + handler403/404/500 *(gate MT-3)*
3. P0-3 LEDGER fallback align
4. P0-4 apply migration 0014 *(gate MT-4)*
5. P0-5 `complete_worker_task` task-lock
6. **P1-1 role-based landing** (pulled in — owner sees an operational view, not an empty worker dashboard)
7. **P1-2 nav cleanup** (Production-under-Main, dedupe Dashboard, add Payroll/Settlements)
8. **H-2 stalled-Adda alert** (pulled in — owner's #1 morning signal)

**Step 2 — Staging deploy** (DB = PostgreSQL per MT-5; data **disposable** per RC-1). Operate with **verify-before-settle discipline** (`review-reports/`) for the over-report window (RC-6 caveat). Objectives: validate the real workflow + **validate RC-5** (do managers actually pre-allocate per color/size, or is Strict too rigid for the floor?).

**Step 3 — Remaining P1** (post-staging, parallel to early foundation): P1-3, P1-4, P1-5, P1-7, P1-8, P1-9..P1-13.

**Step 4 — Foundation Sprints** (each gated by MT-1 backup + MT-7 docs/manifest; all migrations **prod-scale-designed** per RC-1):
- **Sprint 1 = S1 + S2** (+ P0-5 already done as precursor)
- **Sprint 2 = S3**
- **Sprint 3 = S4**
- **Sprint 4 = S5** (enforce; gate MT-6 load test)
- **Sprint 5 = S6** (retire/drop; backup + soak + rollback review + prod validation)

**Step 5 — P3** reports/monitors over the foundation data.
**Step 6 — P4** as needed.
**Step 7 — Production cutover** from a clean DB (staging data discarded).

---

## 3. Foundation sprints (V2 — with gates + prod-scale design)

### Sprint 1 — S1 (resolver) + S2 (AddaStageRoleRate) · gates: MT-1, MT-7, MT-8
- **Migrations:** `AddaStageRoleRate (adda_stage_record, role, rate, locked_at)`; **prod-scale batched** backfill (most-recent completed `expected_rate` per (stage_record, role); **conflict → flag Adda for review**, RC-4).
- **Services:** `settlement_quantity(c, policy)` (default = current, byte-identical); Adda-start rate copy; `complete_worker_task`/settlement read frozen rate (fallback workflow rate if no snapshot); **MT-8 gate** (flagged Adda can't settle unreviewed). P0-5 task-lock already landed.
- **Views/Templates:** Adda-start rate review/edit.
- **Tests:** golden ₹225 chain identical before/after; rate-lock at first completion; backfill on a **prod-scale synthetic fixture**; conflict-flag path; MT-8 gate.
- **Rollout risks:** resolver must be behavior-preserving (golden-gated); rate-source change must not move historical numbers; backfill conflict handling.

### Sprint 2 — S3 (good/alter/missing + constraint sequencing) · gates: MT-1, MT-7
- **Migrations:** add `good_quantity`/`alter_quantity`/`missing_quantity`; **drop legacy `wsc_reported_quantity_positive`** + add new `sum>0, each≥0` constraint **in the same migration** (RC-3); batched backfill `good ← reported`.
- **Services:** write good/alter/missing; **dual-write `reported_quantity = good_quantity`** (RC-3) until S6; reads → `good_quantity`.
- **Views/Templates:** worker self-report form gains Good/Alter/Missing (carved-out screen; mobile-first).
- **Tests:** constraint swap on prod-scale dump (no failure); allocation-era insert with only good set **succeeds** (RC-3 proof); 18 read-sites migrated; dual-write invariant.
- **Rollout risks:** constraint sequencing (the RC-3 proof test is mandatory); read-site sweep completeness.

### Sprint 3 — S4 (WorkerStageAllocation + pool, Strict, no enforcement) · gates: MT-1, MT-7
- **Migrations:** `WorkerStageAllocation (stage_record, worker, color, size, allocated_quantity, allocated_by)` + `WorkerStageAllocationHistory`; index `(stage_record, color, size)`.
- **Services:** allocation service (allocate/reassign/top-up/reduce-≥-reported) audited via `history_service`; pool fn `Σ good + Σ recovered(=0) − Σ allocated`; auto-even-split default; `select_for_update` on allocations.
- **Views/Templates:** manager allocation screen (carved-out; Strict; auto-split-then-adjust).
- **Tests:** pool derivation; `Σ alloc ≤ pool`; reduce-below-reported rejected; re-cut raises pool; history audit; auto-split.
- **Rollout risks:** naming vs `expense.StageWorkAssignment`; pool query cost (indexed); no enforcement yet.

### Sprint 4 — S5 (enforcement only) · gates: MT-1, MT-6, MT-7
- **Migrations:** feature flag (setting, default off). **No drop.**
- **Services:** enforce `good+alter+missing ≤ allocation` (Strict); color/size from allocation; allocation draw-down `select_for_update` (P0-5 pattern); forward-only.
- **Views/Templates:** bounded report form (cap never sent to client).
- **Tests:** over-report rejected; cap not leaked; flag-off = exactly old behavior; historical Addas still settle; **MT-6 multi-worker load test** (no joint over-pool).
- **Rollout risks:** behavior change (flag = kill switch); RC-5 floor discipline (validated in staging); worker retraining (RC-12).

### Sprint 5 — S6 (reported_quantity retirement + drop) · gates: MT-1, soak, rollback review, prod validation
- **Prereq:** S5 enforcement **proven in production through a soak window**; confirm **zero** readers of `reported_quantity` remain; MT-1 backup.
- **Migrations:** stop the dual-write; **drop `reported_quantity`** (one-way; backup = only rollback).
- **Tests:** full suite green with the column gone; golden settlement reconciliation unaffected.
- **Rollout risks:** **irreversible** (RC-2) — backup + soak + rollback review are mandatory; schedule in a low-traffic window.

---

## 4. Updated confidence score: **8.5 / 10**

RC-1 (now resolved: disposable staging + prod-scale migration design), RC-2 (S5/S6 split, drop is no longer mislabeled), and RC-3 (constraint sequencing with a mandatory proof test) are the three former blockers — all addressed. MT-1…MT-8 are now explicit gates. The remaining 1.5 points reflect residual **operational** uncertainty (RC-5 floor discipline, RC-6 verify discipline) that can only be retired by real staging usage — by design, not a doc fix.

## 5. Updated ship-to-staging recommendation: **B — staging-first, CONFIRMED and now internally consistent.**
Ship to staging after the **Step-1 staging bundle** (P0 + role-landing + nav + stalled-alert), with **disposable data** (never promoted) and **verify-before-settle discipline**. This is now consistent: the foundation builds on a clean prod DB, its migrations are prod-scale-designed, and staging exists to validate the workflow + the one open operational assumption (RC-5). Evidence basis unchanged from V1 §final (money engine reconciles + is hardened; over-report is mitigatable + visible + forward-only-fixable; foundation UX benefits from real usage).

## 6. Remaining blocking risks: **NONE (code/migration).**
With RC-1/RC-2/RC-3 resolved + MT-1…MT-8 gated, there are **no remaining blocking code or migration risks**. Two **residual operational risks to validate during staging** (not blockers, but monitor):
- **RC-5** — does the floor tolerate Strict pre-allocation? If managers rubber-stamp blanket allocations, the control is weakened → may justify revisiting Open mode (a future ADR, not now). **Staging must measure this.**
- **RC-6** — the over-report mitigation depends on management actually verifying before settle. **Staging must confirm the discipline holds**, or accept some wrong pay during the window. The S5 enforcement permanently retires this risk.

Minor acknowledged (no plan change): RC-9 (resolver forward-investment), RC-11 (physical bundle reveals count — server rejection still authoritative), RC-12 (two-phase worker retraining — plan change-management).

---

*Governing plan. Stop. No implementation.*
