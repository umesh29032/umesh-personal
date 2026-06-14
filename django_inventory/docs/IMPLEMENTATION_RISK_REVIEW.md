# Implementation Risk Review — adversarial pass on IMPLEMENTATION_MASTER_PLAN.md

**Stance:** challenge, not agree. Reviewing [MASTER_PLAN](IMPLEMENTATION_MASTER_PLAN.md) + [FOUNDATION_LOCKED](PRODUCTION_TRUTH_FOUNDATION_LOCKED.md) + [FOUNDATION_ROADMAP](PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md) for execution / migration / operational / deployment risk only. Locked decisions not reopened. No implementation.

**Headline:** the *direction* is sound, but the execution plan has **one genuine internal contradiction**, **one irreversible step mislabeled as reversible**, and several **missing deploy/migration prerequisites**. Fix those before executing.

---

## Critical Risks

**RC-1 — Recommendation B (staging-first) contradicts the foundation's own migration-safety premise.**
- The roadmap + LOCKED doc justify the destructive parts (drop `reported_quantity`, constraint swap, backfills) as safe **"because pre-staging — no production consumers, ~4 rows"** (LOCKED §D2; ROADMAP §2/§8.6).
- But the master plan chooses **B: ship to staging FIRST, then build the foundation.** Under B, every foundation migration runs on a **populated, in-use staging system** that has been accumulating Addas/contributions/settlements — *not* the 4-row pre-staging dataset the safety claims assume.
- Net: the foundation's "safe/additive/drop-safe" guarantees were derived under foundation-first; **choosing B invalidates the premise they rest on.** This is a real contradiction between the two governing docs.
- Resolve before executing: either (a) declare staging data **throwaway** (wiped before prod; foundation effectively still builds pre-prod) — and say so explicitly, or (b) **re-derive** each foundation migration's safety for real data volume (backfill correctness, drop, constraint swap on thousands of rows). Until one is chosen, the plan is internally inconsistent.

**RC-2 — The `reported_quantity` DROP is irreversible but is bundled into S5 and described under "flag-off rollback."**
- ROADMAP §2: "S5 enforcement rolls back by flag off — the flag is the primary kill-switch." S5 ALSO contains "FINAL: drop `reported_quantity`."
- A column **drop is not flag-reversible** — once dropped, you cannot roll back to any earlier code version that reads `reported_quantity` (and there will be deployed history that does). Conflating "enforcement flag off" (reversible) with "drop the column" (irreversible) is a rollback-safety error.
- Correction: the drop must be a **separate, late step after S5 has soaked in production**, gated by a DB backup — never inside the behavior-change slice. (See Roadmap Corrections.)

---

## Medium Risks

**RC-3 — Dual-column constraint trap during S3→S5.** While `good_quantity` and `reported_quantity` coexist, the **old** `wsc_reported_quantity_positive` (`reported_quantity > 0`, implicitly NOT NULL) is still active. New allocation-era rows that populate only `good_quantity` would leave `reported_quantity` NULL → violate the old constraint → **INSERT fails**. The roadmap says "keep `reported_quantity`" but never sequences its constraint. Must explicitly: drop the old constraint in S3, or dual-write `reported_quantity` until the drop.

**RC-4 — `AddaStageRoleRate` backfill fidelity.** The new table is per-`(stage_record, role)`, but `expected_rate` is frozen per-**contribution**. If two workers of the same role on one stage completed at different times with a drifted workflow rate (the exact drift A-5/§1 flagged), there are **two `expected_rate`s for one (stage_record, role)** → backfill must define a deterministic pick (latest? most-common?) and **flag conflicts**, or it silently loses fidelity / picks wrong.

**RC-5 — Strict-only assumes pre-allocation discipline the floor may not have.** With Open deferred, a worker **cannot report without a prior allocation**. If the real floor is "workers grab bundles ad-hoc," managers will rubber-stamp large allocations to everyone — **defeating the control** the foundation exists for. Auto-even-split mitigates, but this assumption must be **validated during staging** (does the manager actually pre-allocate per color/size?). The deferred Open mode was the relief valve; removing it raises this operational risk.

**RC-6 — B's over-report mitigation relies on the discipline whose absence caused the bug.** The plan mitigates the staging over-report window with "verify-before-settle discipline (`review-reports/`)." But B-1 happened **because** verification is optional and was skipped. Trusting the same human discipline during staging means **real workers may receive wrong pay** — trust damage with the exact people being onboarded.

**RC-7 — DEBUG-off (P0-2) is under-scoped.** Turning `DEBUG=False` surfaces a cluster of prod-config requirements not enumerated: `ALLOWED_HOSTS`, static-file serving (`collectstatic` + whitenoise/nginx), and **working** 403/404/500 templates (a 500 handler that itself errors, or missing static, is worse than DEBUG-on). P0-2 as written ("DEBUG off + register handlers") understates the readiness work.

**RC-8 — Nav/landing fixes ordered AFTER the staging deploy.** Master-plan order: P0 → **staging deploy** → P1 (landing C-1, nav C-2/3/4, denial, stalled-alert). So staging evaluators (owner + workers) hit the **known-bad** UX: owner lands on an empty worker dashboard, Production buried below Storefront, two "Dashboard" items, bare 403s. That undercuts the staging evaluation. P1-1, P1-2, and H-2 should ship **with** the staging bundle, not after.

---

## Low Risks

**RC-9 — `settlement_quantity` resolver (S1) is an abstraction with one consumer.** Its only caller uses the default policy; the alternate policies (packed/hybrid) are P4/maybe-never. Building the indirection in S1 is forward-investment with no current second use case (mild YAGNI debt). Acceptable if deliberate; otherwise defer to the first real policy need.

**RC-10 — P0-3 (LEDGER fallback align) is latent-only.** Harmless today (setting is defined `=False`, fallback never fires). Not a true staging blocker — fits P1 better than P0. Keep the fix; reclassify priority.

**RC-11 — "Worker never sees the cap" is partly illusory.** The cap = the allocation; a worker handed a physical bundle of 10 can count it. Server-side rejection still holds, but don't oversell the anti-gaming premise — physical work often reveals the number.

**RC-12 — Workers retrained twice.** Staging teaches the old free-pick report flow; S5 changes it (bounded, color/size locked, cap hidden). Plan for the change-management cost of re-teaching the same workers.

---

## Missing Tasks

- **MT-1 — DB backup before each foundation migration** (especially the constraint swap and the `reported_quantity` drop). Not mentioned anywhere; "rollback = drop column" is not a backup.
- **MT-2 — Staging-data lifecycle decision** (throwaway vs promote-to-prod). Gates RC-1; currently unstated.
- **MT-3 — Production-config readiness checklist** for DEBUG-off: `ALLOWED_HOSTS`, `collectstatic`/static serving, error templates exist + render, correct settings module (RC-7).
- **MT-4 — Verify migration `0014` is non-destructive** on populated `addahistory` before applying (P0-4 assumes safe; `alter_*_change_type` can reject/lose rows if it narrows choices).
- **MT-5 — Confirm staging DB engine == prod (PostgreSQL).** Settlement money-armor (advisory locks) + dup-draft protection (I-3) are PG-only; a different staging engine silently weakens them.
- **MT-6 — Realistic multi-worker concurrency/load test** for the allocation draw-down before enabling S5 (the new race surface; single-test ≠ load).
- **MT-7 — PKALS `canonical_manifest` / CHANGE_IMPACT_MATRIX regeneration** as a per-sprint gate (foundation touches many canonical files; DOCS-SYNC is a project hard rule).
- **MT-8 — Default/gate for un-reviewed flagged in-progress Addas** (RC-4): a flagged-rate Adda must not settle on an unreviewed backfilled rate.

---

## Roadmap Corrections

1. **Split the `reported_quantity` drop out of S5** into a separate post-soak cleanup step ("S6"), gated by MT-1 backup + a proven-in-prod soak window (RC-2).
2. **Resolve the staging-data question (MT-2) before committing to B** — declare throwaway, or re-derive migration safety for real volume (RC-1).
3. **Pull P1-1 (role landing), P1-2 (nav), H-2 (stalled alert) into the staging deploy bundle**, before evaluators use it (RC-8).
4. **Sequence the `reported_quantity` constraint** in S3 (drop old constraint or dual-write) to avoid the INSERT trap (RC-3).
5. **Add MT-1..MT-8 as explicit gates** in the relevant sprints.
6. **Reclassify P0-3 → P1** (latent, not a blocker) (RC-10).
7. **Define the AddaStageRoleRate backfill tie-break + conflict flag** (RC-4).

---

## Final Confidence Score: **6.5 / 10**

Direction and analysis are strong (audit evidence solid, foundation design coherent, P0 correctly small). Score held down by: one real cross-doc contradiction (RC-1), one irreversible-step mislabel (RC-2), an INSERT-blocking constraint sequencing gap (RC-3), and missing deploy/migration prerequisites (MT-1..MT-5). These are **execution-plan defects, not design defects** — fixable without reopening any locked decision.

---

## Would I execute IMPLEMENTATION_MASTER_PLAN.md exactly as written?

**NO — execute it with the corrections above (effectively "YES WITH CHANGES," but the changes are blocking, so: NO to *exactly as written*).**

Justification (evidence only):
- **RC-1 is blocking:** the plan's chosen strategy (B) and the foundation's migration-safety claims are derived from **contradictory data-volume assumptions**. Executing as written means running "safe-because-4-rows" migrations on a populated staging DB. Must resolve MT-2 first.
- **RC-2 is blocking:** the plan would drop `reported_quantity` inside a slice it calls flag-reversible. A column drop is not reversible by a flag; executing as written creates a false rollback guarantee on a money-truth table.
- **RC-3 is blocking:** as sequenced, allocation-era inserts can fail the retained old constraint.
- Everything else (RC-4..RC-12, MT-1..MT-8) is fixable in-flight, but RC-1/RC-2/RC-3 must be corrected **before** the first foundation migration.

With the 7 roadmap corrections + 8 missing tasks applied, I would execute confidently (confidence would rise to ~8.5). The bones are right; the execution plan needs these guardrails first.

*Stop. No implementation.*
