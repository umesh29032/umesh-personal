# S1 Hostile Architecture Review (2026-06-14)

Adversarial review of the SHIPPED S1 (commit `99ab7935`) — trying to prove it flawed / incomplete / debt-creating, not defend it. Tests assumed incomplete. Verdict in §D.

## A. Findings by severity

### HIGH
**H1 — M-6 WARN fires on ALL `HARD_FLAGS`, not just the B-1 leak → noise that defeats D-β "actionable".**
S1 surfaces `[r for r in reconcile_stage_pay(adda) if r['flag'] in HARD_FLAGS]`. But `HARD_FLAGS = {over_allocated, grouped_paid, unpriced_paid, no_output_qty}` — only **over_allocated** is the paid-more-than-produced leak M-6 targets. Break: a flow with any stage whose `cost_quantity_snapshot` is None (fixed-cost / no-handler-qty stage) flags **`no_output_qty` on EVERY settlement** of that Adda → the detail banner + finalize log cry wolf → managers learn to ignore the banner → the real `over_allocated` gets ignored too. Worse, this is the basis for the S5 BLOCK — you **cannot block** a settlement for `no_output_qty` (the stage legitimately has no measurable output). **Scope the M-6 signal to `over_allocated` (the B-1 leak) before S5;** treat the other flags as a separate integrity report.

**H2 — M-6 WARN is ephemeral (log + live recompute); no persisted variance → the soak's B-1-frequency/trend metric is blind to past-then-fixed leaks.**
The WARN logs at finalize and the detail view recomputes `reconcile_stage_pay` live. Nothing PERSISTS "settlement ADST-X over-allocated stage Y by Δ." Break: a settlement over-allocates, the soak observer isn't watching that hour, the contribution is later verified-corrected or the settlement reversed → `reconcile_stage_pay` now returns clean → the historical leak is **invisible** to the weekly B-1-frequency metric (STAGING_OBSERVATION_FRAMEWORK §5), which is the headline evidence for sizing the foundation. The framework assumed a queryable variance; S1 gives it only log-scraping. **Persist the variance at finalize (a small append-only row), or explicitly downgrade the soak metric to log-derived + document it.**

### MEDIUM
**M1 — First-completion lock is PER-(stage, role); a stage is NOT frozen after the first worker completes.**
`complete` locks only the completing worker's role row (`frozen_rate_for(sr, role, lock=True)` + `mark_locked` on that one row). Break: worker A (role=worker) completes → worker-rate locked; owner then edits the **manager**-rate row (still unlocked) up; a manager later completes the same stage → paid the post-hoc-edited rate. This matches the addendum's literal predicate ("locks once ANY contribution on that (stage_record, role) completes") — but "first completion freezes the stage" is the intuitive reading, and the per-role window allows editing a not-yet-completed role's rate **after** production on the stage has started/been paid for another role. Confirm this is intended; document loudly (it's a money-edit window people won't expect).

**M2 — Rate edits are per-(stage, role) rows; a stage-level rate correction = N edits.**
`edit_until_lock(stage_record, role, rate)` touches one row. A flat-rate stage has 3 role snapshots (super_admin/manager/worker) at the same value; fixing "the cutting rate" pre-lock requires 3 separate calls. No "set the stage's rate" affordance. Operational friction (and a partial-edit hazard: edit worker but forget manager).

**M3 — Dead transient attribute: `settlement.reconciliation_warnings` set in `finalize` is never read.**
`finalize` does `settlement.reconciliation_warnings = [...]` then returns; the view redirects (doesn't render the return), and the detail view **recomputes** independently. So the assignment is write-only dead code — misleading (implies the caller consumes it). The WARN **log** is the real artifact. Remove the attribute (or actually consume it in the post-finalize flash).

**M4 — Test gap: the 4 creation-site WIRINGS aren't tested; only `ensure_stage_role_rates` is.**
`test_s1_foundation` calls `ensure_stage_role_rates(sr)` directly. Nothing asserts that **`create_adda` / cutting-start / layering-start / barcode-start actually CALL it.** Break: a refactor removes the call at one site → that stage's records ship with no snapshot → silent live-fallback (the WARN is the only signal, and on a fresh DB it'd be everywhere). Add an integration test: `create_adda(...)` → snapshots exist on the layering SR.

**M5 — Global lock-order doc (addendum M-3) not updated to include `AddaStageRoleRate`.**
`complete` locks task → AddaStageRoleRate (correct local order). Today this is deadlock-free because `finalize` locks a DISJOINT set (AddaStageRecord/WorkerProfile/WorkerAdvance) and never touches the task or rate rows. But M-3 mandated documenting the global order; it wasn't amended. S4 (allocation/pool locks) WILL interleave — the doc must be authoritative before then.

### LOW
- **L1** — `role_snapshot` is captured at COMPLETE, not at report; a role change between report and complete picks the complete-time role. Minor/defensible.
- **L2** — the resolver references `reported_quantity` literally; S3 must change it to `good_quantity` AND add a golden fixture WITH non-zero alter/missing (challenge #12). The `STAGE_GOOD` named seam is in place; this is a planned S3 step, not an S1 defect.
- **L3** — snapshots are created only for `PRODUCTION_ROLES`; an off-roster role completing hits live-fallback+WARN even on an S1 record. Surfaced, acceptable.
- **L4** — `payroll_service` "pieces produced" = `Σ reported_quantity` is not routed through any abstraction; S3's reported→good rename must update it (coupled change, not S1's job).

## B. New technical debt introduced by S1
1. **M-6 WARN coupled to `reconcile_stage_pay`'s multi-purpose `HARD_FLAGS`** (H1) — if that check's flags evolve, M-6's settlement-WARN semantics drift silently.
2. **Dead `reconciliation_warnings` attribute** (M3).
3. **Two role-rate tables** (`WorkflowStageRoleRate` template + `AddaStageRoleRate` frozen) — acknowledged in the addendum, but now real surface a maintainer must keep straight.
4. **Resolver hard-references a field (`reported_quantity`) scheduled to be renamed** — a known, named seam (low debt, but a cross-sprint coupling).
5. **No persisted reconciliation evidence** (H2) — the soak metric leans on logs.

## C. Fix before S3
- **H1** — scope the M-6 WARN to `over_allocated` (decide `no_output_qty`/grouped/unpriced handling separately; they can't be S5 BLOCK criteria). *Small.*
- **M3** — remove the dead `reconciliation_warnings` finalize attribute (or consume it). *Trivial.*
- **M4** — add the `create_adda → snapshot exists` wiring test (+ ideally one per creation site). *Small.*
- **M5** — amend the documented global lock order in `adda_settlement_service` to include `AddaStageRoleRate`. *Trivial (doc).*
- **M1** — get an explicit owner ruling on per-role-vs-whole-stage lock; document it. *Decision, not code.*
- **H2** — decide: persist the variance now (small append row) vs accept log-derived soak metric + document. *Owner call.*
- **L2** is an S3 task (resolver→good + alter/missing golden), not an S1 fix.

## D. Verdict: **GO-WITH-CHANGES** for S3
S1's core is **sound**: the frozen rate is correct (resolved == old live logic; golden ₹225 byte-identical), the resolver extraction is genuinely behavior-preserving, the locks are deterministic (edit/complete serialize on the same row; complete/finalize lock disjoint sets — no deadlock today), grouped→₹0 holds, role-change-after-lock doesn't re-price (tested). **No Critical** — nothing corrupts money or blocks S3 conceptually.

But ship these before S3 (all small, mostly): **H1** (WARN noise — the one that quietly defeats the soak's purpose), **M3** (dead code), **M4** (wiring test), **M5** (lock-order doc); and get owner rulings on **M1** (per-role lock semantics) and **H2** (persist variance). S3 (good/alter/missing) is largely independent of these, so they don't *block* it — but H1's noise + H2's gap degrade the very staging evidence the foundation sequencing depends on, so fixing them now (not "later") is the right call.

**Recommend:** a tiny **S1.1 hardening pass** (H1 + M3 + M4 + M5, ~1 sitting) + the two owner rulings, then S3.

---

## E. RESOLUTION — S1.1 SHIPPED 2026-06-14 (572/572 green, golden ₹225 byte-identical)

Owner rulings: **M1** = keep per-(stage_record, role) lock (NOT whole-stage). **H2** = persist evidence. Plus a new owner requirement — super-admin rate correction until settlement (Option 1: keep M1 for normal edits + add a super-admin override).

| Item | Resolution |
|---|---|
| **H1** | `reconciliation_service.SETTLEMENT_WARN_FLAGS = {over_allocated}`; finalize + detail both filter on it. `no_output_qty`/grouped/unpriced stay in `reconcile_pay`'s full report only. |
| **H2** | `expense.SettlementReconciliationEvidence` (migration 0010) — append-only, written at finalize by `record_reconciliation_evidence`; soak B-1 metric now queryable + survives later corrections. |
| **M1** | Confirmed per-(stage_record, role); documented in `AddaStageRoleRate` docstring + lock-order docs. |
| **M3** | Dead `settlement.reconciliation_warnings` attribute removed (replaced by the persisted write). |
| **M4** | `CreationSiteWiringTests.test_create_adda_snapshots_first_stage` — asserts the creation path snapshots (not just the helper). |
| **M5** | `adda_settlement_service` docstring now documents the production-truth lock domain (task → AddaStageRoleRate → WorkerStageContribution) as DISJOINT from the settlement order — no deadlock. |
| **Rate-correction req** | `stage_rate_service.rerate_stage_role` (super-admin, until-settlement, auto-recalc of completed-but-unsettled expected_*, refuse-if-settled, mandatory `reason`, append-only `RateCorrectionAudit` migration 0038) + thin super-admin UI (`production:stage-rates`/`stage-rate-correct`, mobile-first). M1 preserved: normal `edit_until_lock` still locks at completion; rerate is the explicit owner override. |
| **L2** | Deferred to S3 as planned (resolver `reported_quantity`→`good_quantity` + alter/missing golden fixture). |

**Verdict upgraded: GO for S3.** All Critical/High/Medium resolved or explicitly deferred (L2→S3). The mandatory **M-1…M-4 re-review still gates S4** (grain/pool/lock/reopen).
