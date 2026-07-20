# Engineering Review — Allocation Engine AE-1 → AE-4 (pre-commit PR review)

**Date:** 2026-07-20 · **Base:** HEAD `ebeec580` (P19A P0) · **Scope:** the uncommitted AE-1→AE-4
diff ONLY (storefront homepage WIP + accounts/inventory GUIDE edits are pre-existing and
excluded). **Review only — no code changed, nothing committed.** Two independent passes
(author + a fresh-eyes adversarial reviewer); findings reconciled below.

**Diff size:** ~387 insertions across 13 Python files + ~966 LOC new (bundle_service 253,
3 templates, 3 test files). Migrations: production 0052, accounts 0019.

---

## 1. Strengths
- **Adapt-not-rebuild was the right call and executed cleanly.** The existing
  `WorkerStageAllocation` quantity-pool is the substrate; whole = `qty=remaining`, partial =
  `qty=n`. **Zero historical-data migration**; money/settlement/cost/extensibility untouched —
  proven by 898/898 tests + byte-identical goldens.
- **Clean layering, verified independently:** `bundle_service` is a genuine read-only projection;
  `pool_service` stays money-free (decoupling contract intact); `worker_task_service.report_bundle`
  still routes creation through the single writer. **No view performs a direct WSC/WSA write** —
  parse→gate→delegate holds in both new views.
- **Stage-genericity preserved** — no stage-name conditionals added; a new stitching stage is
  still config-only. The always-on bound closes the FAT over-report hole, and the **producer-skip
  correctly exempts pool-producing stages** (cutting) at every completion entry point (incl.
  `cutting_pattern/handler.py` checklist path).
- **Migrations additive, reversible, idempotent** (0052 default-partial CharField, no backfill;
  0019 `update_or_create` sidebar with reverse).
- **Tests assert real behavior** — whole/partial/remainder-grab, hard refusals, pair-block,
  single-bundle scoping, isolation fallback, live progress, snapshot↔DB reconciliation — not
  trivial passes.
- Mobile-first UIs, page-scoped CSS, graceful client+server validation.

## 2. Weaknesses
- **Flag-removal debris.** Retiring `ENFORCE_ALLOCATION_BOUND` left one genuinely dead service
  function (still exported + tested), a dead helper, dead CSS, a now-vacuous devseed assertion,
  and ~8 stale comments/help-strings that will actively mislead the next reader (standing rule 14).
- **The hard bound is implemented twice with a divergent field basis** — a real latent-correctness
  debt (S6), not just DRY (detail in §4).
- **Read-model N+1** contradicts AE-4's "bounded" claim — tolerable now, cheap to improve.
- **`total = assigned + available` is a reconstruction**, not true `pool_good`; can mislead on
  multi-component/rework addas (progress could exceed 100%). Verify before AE-5 multi-component.
- Minor: management view living in `worker_report_views.py`; raw mode-string literals; multi-lane
  scoping gap in the per-bundle report.

## 3. Recommended cleanups (all — required + optional consolidated)
See §4 (required before commit) and §5 (optional after). Every required item is a deletion or a
small local refactor — exactly what the "review diff → one clean commit" step is for. No redesign.

## 4. REQUIRED cleanups before the commit  (⇒ No-Go until done)

| # | Item | Location | Why |
|---|---|---|---|
| R1 | **`report_bundle` bound duplication + S6 divergence** — it re-derives the hard bound inline from the FORM dict `reported_quantity + alter + missing + damaged > allocated`, while canonical `check_allocation_bound` reads `good_quantity + …` from the persisted row. `reported_quantity` is the S6-retired column; post-S6 `.get('reported_quantity')`→None→0 and the *per-bundle submit* check silently degrades to `alter+missing+damaged ≤ allocated` (good over-report slips past submit; complete-time still catches it only once ALL bundles are in). **Fix:** `report_bundle` delegates to a shared bound helper reading `good`, not the raw line. | worker_task_service.py:382-399 vs pool_service.py:520-533 | correctness debt (latent) |
| R2 | **Delete dead `bound_soft_warning`** — zero production callers after AE-1 dropped the view call; still defined + exported + 2 unit tests. Design doc §12 said "retire." | pool_service.py:471; __init__.py:90,110; test_s4_bound.py:216,223 | dead code |
| R3 | **Delete dead `_dim_labels`** — no callers after `_pool_section` moved to bundle_service. | views_ctx.py:19 | dead code |
| R4 | **Delete dead CSS `.gsp .alloc-form`** — the `alloc-form` markup was replaced by `.ab-*`. | _stage_panel_generic.html:26-28 | dead code |
| R5 | **Fix stale `ENFORCE_ALLOCATION_BOUND` comments/docstrings/help** (flag is gone; these read as if it still gates behavior) | worker_task_service.py:462,575,587; preview_allocation_bound.py:6,8,18,35; test_s4_bound.py:6 + remove vestigial `@override_settings` at :84; pool_service.py:421,474; worker_report_views.py:68 | rule-14 (misleading docs) |
| R6 | **Fix vacuous test** — `assertFalse(getattr(settings,"ENFORCE_ALLOCATION_BOUND",False))` can never fail (setting removed → always default). Drop or re-point to the surviving flag. | devseed/tests/test_money.py:69 | test integrity |
| R7 | **Remove repo-root residue** `c_ov2.txt`, `ov2iso.html` (stray curl output). | repo root | hygiene |

## 5. OPTIONAL cleanups after commit
- **O1 N+1 hoist:** `available()` recomputes `_mandatory_pattern_needs(adda)` per dim; `bundles_for_stage`/`worker_bundles`/`stage_snapshot` issue per-row contribution queries; `AddaSnapshotView` nests `stage_snapshot` in stage×lane loops. Cheap win: hoist `_mandatory_pattern_needs` out of the per-dim loop. (Fine at factory scale.)
- **O2 `total` reconstruction:** `assigned + available` diverges from true `pool_good` when the garment set-cap or `recovered_alter` binds → snapshot Total / progress can mislead (>100% possible). Verify before AE-5 multi-component addas.
- **O3 View cohesion:** move management-only `AddaSnapshotView` (and `AddaReportReviewView`) into a `production_snapshot_views.py`; `worker_report_views.py` header claims "ONLY worker-facing write surface."
- **O4 Enum over strings:** bundle_service + templates compare `mode == 'whole'/'partial'` as bare strings; use `WorkerStageAllocation.Mode` to avoid silent drift.
- **O5 `allocate_whole` doubled work:** acquires the pool lock + computes `available()`, then `allocate()` re-acquires + recomputes. Safe (re-entrant advisory lock) but a private `_allocate_locked` avoids it.
- **O6 Panel JS nits:** `_stage_panel_generic.html` has a dead `document.currentScript.previousElementSibling` line, and `document.querySelector('.alloc-bundles')` is unscoped (two generic panels on one page → only the first wired — multi-lane latent).
- **O7 Internal dup:** "Σ good for (worker,dims)" is copy-pasted 3× in bundle_service — extract a helper (folds into R1's shared helper).

## 6. Coverage of the 15 requested areas
| Area | Verdict |
|---|---|
| 1 Architecture consistency | Strong — read-model/writer discipline holds |
| 2 Code duplication | R1 (bound) + O7 (Σgood) |
| 3 Dead code | R2 bound_soft_warning, R3 _dim_labels, R4 CSS |
| 4 Obsolete allocation logic | Old alloc-form template/JS removed cleanly; no stale `pool.rows/allocations` refs; legacy `expense.allocation_service` era-A still flag-disabled (out of AE scope) |
| 5 Unused helpers | R3 (_dim_labels), R2 (bound_soft_warning) |
| 6 Naming | O4 mode literals; `CuttingBundle`(size) vs "Manufacturing Bundle"(colour+size) collision — future rename, flagged (ADD §4) |
| 7 Service boundaries | Clean — pool_service money-free, bundle_service read-only, single-writer preserved |
| 8 View responsibilities | O3 (management view placement); no business logic in views |
| 9 Template organization | Scoped CSS ok; R4 dead CSS |
| 10 Migration quality | Clean (additive, reversible, idempotent) |
| 11 Test quality | New tests real; R6 one vacuous devseed assertion; modified op1/s4 still meaningful |
| 12 Regression coverage | Gaps: multi-lane/stream scoping test, w2-opens-w1's-allocated-pair isolation, void→reallocate-whole — add before AE-5 |
| 13 Performance | O1 N+1 (tolerable now) |
| 14 Maintainability | R5 stale comments (main drag) |
| 15 Readability | Good; helped by cleanup |

## 7. Overall engineering score & Go/No-Go
**Score: 8.5 / 10.** Architecturally the right shape and cleaner than expected — the money path
is provably untouched, migrations are safe, tests are real, and the design principle (adapt the
existing pool, stay stage-generic) was honored. Points off only for flag-removal debris and the
`report_bundle` bound duplication (a real S6 latent divergence).

**Go / No-Go: NO-GO for an as-is commit → GO after the §4 REQUIRED block.** All seven required
items are deletions, comment fixes, or one small shared-helper refactor (R1). None require
redesign. Recommended sequence: R1 (dedup the bound onto a shared `good`-based helper) → R2–R7
(dead-code + stale-comment + residue sweep) → re-run the focused battery → then the single clean
AE-1→AE-4 implementation commit → resume FAT at AE-5.

**Before AE-5 (not blocking the commit):** verify multi-lane bundle scoping (§5 O-multi-lane) and
the `total` reconstruction on a multi-component cert adda (O2), since AE-5's fresh cert adda may
be multi-lane / multi-component.
