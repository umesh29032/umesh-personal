# PRODUCTION_AUDIT_STATUS.md — Single Source of Truth

> **Production Readiness Audit** of Kapil Enterprises Inventory (Django 5.0 + PostgreSQL).
> Stabilization & hardening phase. **No new features. No redesign. No speculative work.**
> Goal: FIND BUGS · VERIFY EXISTING BEHAVIOR · FIX VERIFIED ISSUES.
>
> This file is the resume point. A new session running **`CONTINUE AUDIT`** must:
> read this file → find last completed phase → resume at the next unfinished phase → never restart completed work.

---

## CURRENT STATE

| | |
|---|---|
| **Current phase** | PHASE 16 — Performance Audit ✅ COMPLETE (awaiting review; NOT committed) |
| **Next phase** | PHASE 17 — Final Regression Audit (do NOT start without review) |
| **Branch** | `new_flask_app` |
| **Last updated** | 2026-06-15 |
| **Green test baseline** | **700 tests, all passing** (Phase 16 = +4 query-count regression tests; run from `config/`: `../env/bin/python manage.py test --settings=config.settings.local --parallel 4`) |
| **Open blockers** | None. Documented follow-ups: storefront PA-05A-SF1..4 (migration); over-allocation 3-PATTI-001 (pre-foundation dev data, foundation flags off pending soak); stray test-product data (dev-DB cleanup); **PA-16-QUEUE** settlement-queue residual ~4 queries/Adda (structural, bounded by pending-unsettled queue; batching = settlement-logic redesign, out of stabilization scope). |

---

## PHASE LEDGER

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 01 | System Mapping | ✅ COMPLETE | `docs/AUDIT_SYSTEM_MAP.md` written; 151 URLs / 151 views / 31 services / 36 forms / 109 templates mapped + nav/RBAC + infra. Map cross-validated vs actual `urls.py`. |
| 02 | Authentication Audit | ✅ COMPLETE · commit `1dc05424` | 18 candidates → 8 fixed (incl. owner-approved signup disable), 5 documented-no-fix, 5 refuted. Code+browser+DB+live verified. 649 tests green. |
| 03 | RBAC Audit | ✅ COMPLETE · commit `0213aaa7` | Empirical URL×role matrix (7 principals × ~80 no-arg URLs) + adversarial code workflow. 1 real leak fixed (PA-03-1), 1 owner-decision (WONTFIX), 2 documented defense-in-depth. URL-layer RBAC sound. 652 tests green. |
| 04 | Navigation Audit | ✅ COMPLETE · commit `0637337a` | Static dead-link scan (all 390 url names; every template `{% url %}` + py `reverse/redirect` resolves) + adversarial workflow (redirect/cancel/breadcrumb/loop/orphan) + browser mobile-nav. 1 dead-link fixed (PA-04-1, dormant template). Nav integrity clean. 652 green. |
| 05A | CRUD Audit — Master Data | ✅ COMPLETE · commit `9be49e17` | Behavioral C/R/U/D probes (real DB writes, rolled back) on 7 surfaces + delete-in-use probes + adversarial workflow (21 candidates). 5 fixed, 5 refuted, 4 storefront gaps documented. Mobile CRUD PASS. 660 green. |
| 05B | CRUD Audit — Operational | ✅ COMPLETE · commit `15371a08` | Adversarial workflow (38 candidates, 6 money/qty/inventory flows) + code-level verification + live mobile worker-report test. 2 fixed (finalize crash, breakup atomic); rest refuted/documented (money writes are service-locked+atomic+tested). 663 green. |
| 06 | Master Data — Integrity / Config / Seed / **Drift** | ✅ COMPLETE · commit `d75e606f` | Refined scope (a–e incl. owner-added Configuration Drift Audit). Adversarial workflow (16 candidates: DB-integrity/seed/flow-config/WorkerProfile/config-drift) + live DB drift probes + constraint-enforcement probes. 2 fixed (WorkerProfile validation); rest documented/refuted. Constraints enforced; reconcile_denorm clean; no drift on real products. 671 green. |
| 07 | Stage Engine Audit | ✅ COMPLETE · commit `bc008685` | Full lifecycle audit of layering · cutting_pattern · cutting · barcode (create/assign/start/report/draft/complete/reopen/review/settlement/quantity/allocation/transition/race). 7-finder adversarial workflow died on session limit → continued main-thread (full stage engine read). 2 fixed (PA-07-1/2, one root cause: raw-string→`Decimal` 500), 2 refuted (Adda.started_at None; breakup count<consumed). Money/transition/reopen logic = foundation-locked + tested, verified sound. 673 green. |
| 08 | Raw Material Audit | ✅ COMPLETE · commit `666d7274` | Cloth roll lifecycle: inbound (bulk intake) · stock-edit · Adda assignment · leftover consumption. Main-thread audit (subagents still session-limited; not re-run — no added coverage vs manual read of a 5-file app). 2 fixed (PA-08-1/2: negative weight/cost on plain forms.Form → DB CheckConstraint IntegrityError → 500). Refuted: RollEditForm (ModelForm full_clean validates constraint → graceful), dashboard filter parse (guarded), assign-roll race (PA-05B-RACE class), RollBulkCreateView `except PermissionError` mismatch (latent, super-admin-only → unreachable). 677 green. |
| 09 | Inventory Audit | ✅ COMPLETE · commit `63f58fb5` | Inventory as a QUANTITY-TRUTH system (the `inventory` Django app is RBAC-only): roll/leftover · breakup↔bundle↔item · breakdown↔barcode · S4 pool · reopen effects · denorm counters · concurrency · reconcile. 6-finder conservation Workflow ran; **9/10 verifiers died on session limit → main-thread-verified every finder candidate (honesty rule — NOT marked clean on dead verifiers).** 2 fixed (PA-09-1 legacy-cutting double-create SR 500; PA-09-2 mixed manual+breakup add unique-collision 500). Refuted/documented: consume_leftover stale read-cache (benign), reconcile pieces_cut-vs-breakup (by-design, tested contract), reconcile 2-of-5 coverage (enhancement, counters self-heal), manual-no-bound (PA-07-BREAKUP class), total_pieces lost-update (display-only/PA-05B-RACE). 679 green. |
| 10 | Production Audit | ✅ COMPLETE · commit `70a7afca` | Production-truth system: Adda/assignment/contribution lifecycle · draft→complete · reopen→re-complete · rate-freeze · expected_earning · good/alter/missing · settlement-qty derivation · AddaStageRoleRate · locks/atomicity/audit. Finder-only Workflow (all 6 finders survived → 12 candidates; verify stage omitted to dodge the verifier-death pattern) + main-thread-verified EACH. 3 fixed: PA-10-1 (CRITICAL — `ensure_worker_credit` blocked ALL cutting completion in the default flag-off config), PA-10-2 (HIGH — `set_stage_workers` cancelled COMPLETED tasks → orphaned pay), PA-10-3 (LOW — `ensure_stage_role_rates` SR-site coverage). 5 documented-not-fixed (reopen-restale=by-design/use rerate; verified-qty no-audit=by-design; grouped→0 settlement-preview + finalize-vs-verified race = Phase 11; role=None→base rate = benign). Golden ₹225 settlement byte-identical. 685 green. |
| 11 | Settlement Audit | ✅ COMPLETE · commit `111a8a33` | finalize / reverse / supersede chains / AddaSettlement / SWA / ledger / reconciliation evidence / rerate / override / locks / settlement_quantity / double-pay / replay / S5. Finder-only Workflow (all 6 finders survived → 10 candidates) + main-thread-verified each. Money-write/reverse/supersede/ledger-idempotency verified SOUND (5374 serializes; era-A/B guards; reverse fully restores; double-finalize/reverse blocked). 3 fixed: PA-11-1 (MEDIUM — `outstanding_advances` ignored `reversed_at` → reversed recovery hid the restored advance from the recovery UI), PA-11-2 (MEDIUM — grouped→0 not applied at settlement preview/queue [carried PA-10-GROUPED-PREVIEW]), PA-11-3 (MEDIUM — finalize locked AddaStageRecord but not the WSC rows where `verified_quantity` lives [carried PA-10-VERIFY-RACE]; comment falsely claimed protection). Golden ₹225 byte-identical. 687 green. |
| 12 | Payroll Audit | ✅ COMPLETE · commit `c7c50c79` | Money-consumption (read/aggregate/display): generation/aggregation/display/filtering/history/visibility · grouped-worker · settlement integration · reverse/supersede effects · stale values · permissions · advances. Finder-only Workflow (all 4 finders survived → 14 candidates) + main-thread-verified each. 3 fixed (all reversal-netting amount-mismatches; ledger payable was always correct): PA-12-A (`payroll_totals` advance_exposure ignored `reversed_at`), PA-12-B (`PayrollOverviewView` advance_outstanding ignored `reversed_at`), PA-12-C (`PayrollOverviewView` `total_earnings`/`total_settled` didn't net reversals by category → counted CREDIT/REVERSAL as earnings; now mirrors `worker_summary`). Permissions sound (MyEarnings self-scoped; worker-detail `can_view_worker`-gated; overview management-only). No payroll export surface. 688 green. |
| 13 | Reporting + Search + Filter + Export Audit | ✅ COMPLETE · commit `0f0d178a` | MERGED (reporting+search+filter+sort+pagination+exports+aggregations+visibility). Finder-only Workflow (all 4 finders survived → 8 candidates) + main-thread-verified each. 6 fixed: PA-13-1 (HIGH barcode-dashboard cartesian-JOIN inflation), PA-13-2 (HIGH RollListView non-numeric id filter → 500), PA-13-3 (HIGH cost/supplier leak via 3 time-log accordions — PA-03-1 class), PA-13-4 (MEDIUM UserListView non-numeric `?skills` → 500), PA-13-5 (LOW garbage-status chip), PA-13-6 (LOW CSV/XLSX formula-injection). +8 regression tests. Verified sound: all paginated lists ordered, operations_digest single-source, payroll netting (P12). 696 green. |
| 14 | Mobile Responsiveness Audit | ✅ COMPLETE · commit `2b8d1c5e` | Real-browser (headless Chromium) scan at 320/375/390/414px across all priority surfaces (dashboards, lists, workspaces, Adda detail, settlement, payroll, stage-rates, review, forms, worker-report). Automated overflow/clip/touch-target/scroll diagnostics + visual screenshots. **3 fixed:** PA-14-1 (HIGH — settlement-detail money tables clipped off-screen, no scroll), PA-14-2 (MEDIUM — `.filter-card` horizontal-scroll hides filters on 5 dash/list pages), PA-14-3 (MEDIUM — class-less fancy-select triggers = bare 20px line, sub-44px touch target). **UI_COMPONENTS.md updated** (3 reusable rules: bare-table clip, filter-card mobile stacking, fancy-select tag-CSS gotcha + `--bare` fallback). 696 green (UI-only, browser-verified). |
| 15 | UI Consistency Audit | ✅ COMPLETE · commit `bf7dab93` | Real-browser (headless Chromium) audit at 320/375/390/414/desktop. Carry-forward bare-table sweep of all 9 named surfaces + broad list sweep + touch-target + fancy-select + date-input dimensions. **3 fixed:** PA-15-1 (MEDIUM — product_sizes_edit inline-edit table clipped Archive off-screen at ≤340px + 28px mini buttons), PA-15-2 (LOW — product_patterns_edit identical pattern), PA-15-3 (LOW — standalone pattern_workspace breakup-tables had dead `data-label` / no stacking host). **Documented SAFE (verified):** worker_detail/settlement_form `.adv` (text-only, wraps, money cols visible at 320); cutting-panel/costing/adda_settlement_list/payroll_overview (own scoped stacking, browser-confirmed). **CLEAN dimensions:** fancy-select (all class-less selects covered by Phase-14 `--bare` fallback, 44–45px), date inputs (native `type=date` full-width, no clip), touch targets (only sub-44 actionable = page-scoped `.btn-mini`, folded into PA-15-1/2; `.hamburger`/`.btn` = pre-existing app baseline). **UI_COMPONENTS.md updated** (3 reusable rules: data-label-needs-wrapper gotcha · inline-edit vs text table clip · shared-partial responsive ownership). 696 green (UI-only). |
| 16 | Performance Audit | ✅ COMPLETE (awaiting review) | **Measured** (django.db CaptureQueriesContext + assertNumQueries scale tests — no code-reading-only verdicts). Built a 2-scale query-count harness over the heavy read paths: settlement detail/queue/preview, payroll overview/my-earnings/worker-detail, adda detail, cutting snapshot. **2 fixed:** PA-16-1 (HIGH — settlement-detail draft + queue per-line N+1 on `workflow_stage.stage`, missing `select_related` → +4q/line; settlement-detail draft was O(lines)), PA-16-2 (MEDIUM — same page called `outstanding_advances` per worker → +2q/worker). Combined: **settlement-detail draft now O(1) in contribution lines** (a 30-line cutting Adda ≈137q → 15q, measured flat). **1 refuted by measurement** (PA-16-DUP: adda-detail "duplicate stage_records prefetch" — `worker_tasks` prefetch ran ×1, no dup). **Measured-clean (flat, not assumed):** my-earnings, worker-detail, payroll-overview, get_cutting_snapshot. Dashboards/lists/costing/exports already optimized (prior phases). +4 regression tests (assertNumQueries scale-invariance). 700 green. |
| 17 | Final Regression Audit | ⬜ PENDING | full-system retest |

> **Phase-plan revision (owner 2026-06-15):** Phase 13 = merged Reporting+Search+Filter+Export (one user-facing reporting surface, avoids duplicate verification). Mobile moved to 14 (right after Reporting). **Mandatory for Phases 14+15:** every UI-related fix MUST be evaluated for inclusion in `UI_COMPONENTS.md` — if it establishes a reusable rule (responsive/layout/form/table/modal/dropdown/date-input/validation-display/spacing/accessibility), document the standard + reference the component so future pages follow it. No reusable UI knowledge stays trapped in one template.

Legend: ✅ complete · 🔄 in progress · ⬜ pending · ⛔ blocked

---

## ISSUES FOUND

> Format per BUG REPORT below. None are auto-fixed; each fix is verified + regression-checked before status → FIXED.

| BUG ID | Sev | Phase | Module | Status | One-line |
|--------|-----|-------|--------|--------|----------|
| PA-02-1 | HIGH | 02 | accounts/auth | ✅ FIXED | Account enumeration: forgot-password (and OTP-verify step) leaked email existence via "Session expired" vs "Invalid OTP". |
| PA-02-2 | LOW | 02 | accounts/auth | ✅ FIXED | Mixed-case-local email locked out of OTP login/reset (exact lookup vs `normalize_email` keeping local-part case). Latent (0 affected in dev). |
| PA-02-3 | LOW | 02 | accounts/auth | ✅ FIXED | Auth pages cacheable → back-button after logout could redisplay them. Added `@never_cache`. |
| PA-02-4 | MEDIUM | 02 | accounts/templates | ✅ FIXED | Mobile: OTP digit boxes ~30px at 320px (<44px); reset_otp.html also missing the ≤480px shrink rule the others had. |
| PA-02-OPEN-SIGNUP (was [8]/[9]) | HIGH | 02 | accounts/auth | ✅ FIXED | Public `/app/signup/` created real authenticated accounts (contradicting "no open signup"). Owner chose to DISABLE: routes removed, login-page links removed, views kept unrouted (reversible). Verified 404 + Google/admin-create intact. |
| PA-02-XFF (was [2]) | MEDIUM | 02 | accounts/throttle | 📋 DOC (deploy) | IP-throttle bypass via spoofed `X-Forwarded-For` if app exposed without a trusted proxy. Per-email throttle still applies. Fix = deployment/config decision (TRUSTED_PROXIES). |
| PA-02-OTP-REUSE (was [3]) | LOW | 02 | accounts/auth | 📋 DOC (not exploitable) | Reset OTP not cleared after weak-password rejection — but requires a valid OTP (email control); no escalation. Correct UX. |
| PA-02-NEXT (was [4]) | LOW | 02 | accounts/auth | 📋 DOC (intentional) | PasswordLoginView ignores `?next` (always → home). Deliberate anti-open-redirect; minor deep-link UX only. |
| PA-02-403 (was [13]) | LOW | 02 | accounts/auth | 📋 DOC (intentional) | Denial UX inconsistent: managed URLs → 302 redirect+flash; unmanaged action URLs → bare 403. Both deny correctly. |
| PA-02-TIMING (was [10]) | LOW | 02 | accounts/auth | 📋 DOC (impractical) | Timing side-channel on email existence (DB hit + email send). Not practically exploitable; message/redirect oracle (the real one) now closed by PA-02-1. |
| PA-03-1 | MEDIUM | 03 | inventory/tracking-history | ✅ FIXED | Roll-history timeline leaked `supplier`/`cost_per_kg` change values to non-financial users (worker/manager) though roll list/detail hide them. Filtered server-side by `user_can_view_financials`. |
| PA-03-WORKER-SKILL | MEDIUM | 03 | production/worker-report | ✅ WONTFIX (by-design) | `WorkerReportView` POST gates by manager ASSIGNMENT, not stage SKILL. Owner confirmed (2026-06-14) assignment-only is intended (manager authorizes by assigning; skill-gating would block untagged workers). Real lever for future = the assignment UI ("at least one assignee skilled" check). |
| PA-03-2 (workflow [2]) | LOW | 03 | production/stage-actions | 📋 DOC (service holds) | Layering/Cutting action POST views lack `StageViewAccessMixin` (fail-fast), but the service layer (`_ensure_*_skill`) already raises PermissionDenied → write blocked. Defense-in-depth gap, not a bypass. |
| PA-03-3 (workflow [4]) | LOW | 03 | production/layering | 📋 DOC (service holds) | `LayeringFullCreateAndAttachView` accepts financial POST params from a worker, but the service rejects them with PermissionDenied → no write. Defense-in-depth gap, not a bypass. |
| PA-04-1 | LOW | 04 | accounts/templates | ✅ FIXED | Dormant `signup_otp.html` had 2 broken `{% url %}` (`accounts:signup`, `accounts:signup_resend_otp` — removed in Phase 02). Unreachable (no route) so no live 500, but a dead-link landmine. Repointed to `accounts:login`. |
| PA-05A-1 | HIGH | 05A | accounts/skills | ✅ FIXED | `SkillDeleteView` had no guard — deleting a Skill silently cascaded its M2M, stripping the skill (and stage access) from every worker holding it + emptying any SidebarItemRule referencing it. Added in-use guard (mirrors UserTypeDeleteView). |
| PA-05A-2 | MEDIUM | 05A | inventory/roles | ✅ FIXED | `RoleDeleteView` guarded the primary-role FK (`users`) but not the `extra_roles` M2M (`extra_users`) — a role used only as an extra_role could be deleted, silently stripping it. Guard now covers both. (`is_system` already protected.) |
| PA-05A-3 | LOW | 05A | inventory/roles | ✅ FIXED | Role create/update gave no success message (inconsistent with other CRUD). Added `messages.success`. |
| PA-05A-4 | MEDIUM | 05A | production/patterns | ✅ FIXED | `ProductPatternsEditView` did `int(POST['pieces_count'])` — non-numeric/tampered input → ValueError 500. Added `_safe_pieces_count` (clamp ≥1, fall back to 1). |
| PA-05A-5 | MEDIUM | 05A | accounts/users | ✅ FIXED | `UserCreateView` had no IntegrityError handler — a concurrent double-submit of the same email (iexact validation vs case-sensitive DB unique) → 500. Now caught → field error (mirrors SignupVerifyView). |
| PA-05A-SF1 | MEDIUM | 05A | storefront | 📋 DOC (needs migration) | `Category.name` not `unique=True` → duplicate categories possible. 0 dup in dev DB. Fix = unique + migration. |
| PA-05A-SF2 | MEDIUM | 05A | storefront | 📋 DOC (needs migration) | `FeaturedProduct.price`/`original_price` lack `MinValueValidator` → zero/negative accepted. 0 featured products live. Fix = validator + migration. |
| PA-05A-SF3 | MEDIUM | 05A | storefront | 📋 DOC | Image fields have no size/type cap (Pillow validates it's an image; no max size). Admin/listing-team only. Fix = validators (size policy decision). |
| PA-05A-SF4 | LOW | 05A | storefront | 📋 DOC | Updating a Category/FeaturedProduct image leaves the old file on disk (orphan). Ops hygiene, not user-facing. |
| PA-05B-1 | MEDIUM | 05B | expense/settlement | ✅ FIXED | `_parse_finalize_inputs` did `int(worker_id)`/`int(advance_id)` OUTSIDE the try → a tampered finalize key (`var_abc_packed`, `recover_abc`) → unhandled ValueError 500. Now ValidationError → graceful message. Management-only surface, no DB write before the crash. |
| PA-05B-2 | LOW | 05B | production/cutting | ✅ FIXED | `CuttingBreakupSaveView` upserted rows in a loop and returned on the first bad row → earlier rows persisted (partial write). Wrapped the batch in `transaction.atomic()` + raise-on-error → all-or-nothing. Draft-stage, recoverable, but now consistent. |
| PA-05B-ADV | — | 05B | expense/advance | 📋 DOC (not a bug) | "Duplicate advance on refresh / no dedup / no reverse": PRG is present (FormView redirects); duplicate advances are LEGITIMATE (same worker can get ₹500 twice) so dedup would be wrong; "reverse advance" is a missing FEATURE, not a defect (recovery happens at settlement) — not built per no-feature rule. |
| PA-05B-RACE | LOW | 05B | production/expense | 📋 DOC | `report_contributions`/`save_draft`/`assign_roll_to_adda` check status without `select_for_update` → a true concurrent double-submit (same single user) could race. Mitigated by `@transaction.atomic` + status guards; single-actor surfaces; low likelihood. Not touching the locked foundation services for a theoretical race. |
| PA-05B-FND | — | 05B | production/expense | 📋 DOC (foundation-covered) | Allocation "CSRF/idempotency/double-credit/authz": CSRF is global middleware; over-allocation is refused always-on (S4); `LEDGER_CREDIT_AT_ALLOCATION=False` (no money at allocation); service permission-checks. AJAX draft `204` is correct (not a PRG page). reopen view-authz → service guards (= PA-03-2 class). |
| PA-06-1 | HIGH | 06 | expense/WorkerProfile | ✅ FIXED | `opening_advance` (seeds Advance Outstanding = money) had no validator/constraint → negative accepted, corrupting recovery math. Form `min_value=0` (mirrors AdvanceForm). |
| PA-06-2 | MEDIUM | 06 | expense/WorkerProfile | ✅ FIXED | bank_ifsc / bank_account_number / cross-field had no validation → malformed payout details savable. Blank-tolerant IFSC format + numeric account + "account⇒require IFSC+name" clean. |
| PA-06-DRIFT-OVERALLOC | MEDIUM | 06 | expense/reconciliation | 📋 DOC (known, not mutated) | `3-PATTI-001` cutting: 120 allocated vs 105 produced (over_allocated). KNOWN pre-foundation dev data; `reconcile_pay` detects it (tooling works); S4/S5 prevents new ones (flags off pending soak). NOT mutated — voiding it would hide bug evidence (per cleanup rule). Remediation = enable enforcement flags post-soak OR void the 15-pc delta. |
| PA-06-SEED | LOW | 06 | accounts/sidebar | 📋 DOC | 6 SIDEBAR code items have no SidebarItemRule row → fall back to in-code predicates (functionally correct, never silently hidden). Only 4/6 fit the role-rule model (my-earnings is ungated, pattern-list is perm-gated). Governance nicety, not a functional bug. Optional: seed the 4 role-gated rows. |
| PA-06-TESTDATA | LOW | 06 | dev DB | 📋 DOC (dev-data) | Stray test products (CROSS-TEST, TEST-VERIFY, TEST-86f27f0a) with handler-less stages (cross_cutting, verify, verify-86f27f0a) — leaked test fixtures in the dev DB. No production-code impact (real products all have handlers). Recommend dev-DB cleanup. |
| PA-06-FLOW | LOW | 06 | production/flow_service | 📋 DOC (propose, defer) | `add_stage_to_product_flow` doesn't verify the stage has a registered handler → a handler-less stage can be configured (a flow dead-end). Mitigated: worker-report fails **gracefully** (403 "No handler registered", no crash). Smallest fix = `registry.has(stage.code)` guard — DEFERRED (documented-future TM-1 manual stages may legitimately lack a handler; owner call). |
| PA-06-WP-UPI | LOW | 06 | expense/WorkerProfile | 📋 DOC | `upi_id` has no format validation. Left unvalidated (UPI handle format varies; strict regex risks false-positives) — documented as data-quality. |
| PA-07-1 | MEDIUM | 07 | production/worker-report | ✅ FIXED | Worker report: a non-numeric quantity (tampered POST, or a locale-comma `1,5` on a phone) reached `report_contributions` as a raw string → `Decimal()` `InvalidOperation` (not a `ValidationError`) → `WorkerReportView`'s `except ValidationError` missed it → **500**. Service now catches `InvalidOperation` → graceful `ValidationError`. (Same class as PA-05B-1/PA-05A-4.) |
| PA-07-2 | MEDIUM | 07 | production/adda-report-review | ✅ FIXED | Management quantity review: a tampered/non-numeric `verified_<pk>` reached `set_verified_quantity` as a raw string → same `Decimal()` `InvalidOperation` → 500 (`AddaReportReviewView` catches only `(ValidationError, PermissionDenied)`). Same root cause + fix as PA-07-1. |
| PA-07-STARTED-AT | — | 07 | production/layering | 📋 REFUTED | "Layering auto-duration `now − adda.started_at` 500s if `started_at` is None." `Adda.started_at = DateTimeField(auto_now_add=True)` (models/adda.py:45) → never None. Not a bug. |
| PA-07-BREAKUP-COUNT | — | 07 | production/cutting | 📋 REFUTED (benign) | "`upsert_breakup_row` can set a breakup `count` below its `consumed_count` → negative `available`." Breakup is the INFORMATIONAL plan (docstring: bundles drive completion/settlement, not breakup). Negative `available` only blocks further takes in `add_pieces_to_bundle` (`take > available` always rejects) — no crash, no money/qty error. Not fixed (no-speculative rule). |
| PA-08-1 | MEDIUM | 08 | raw_materials/intake | ✅ FIXED | Bulk roll intake: a negative `cost_per_kg` passed `BulkRollForm` (a plain `forms.Form`, no model-constraint validation) → `bulk_create_rolls` → `ClothRoll` INSERT → DB CheckConstraint `rawmat_clothroll_costperkg_nonneg` → **IntegrityError** (RollBulkCreateView catches only `(ValidationError, PermissionError)`) → 500. Reproduced at service level. Fix: `min_value=0` on the form field → graceful field error. (Same class as PA-06-1.) |
| PA-08-2 | MEDIUM | 08 | raw_materials/assign | ✅ FIXED | Roll→Adda assign: a negative `weight_kg` passed `AssignRollForm` (`is_valid()=True`, plain forms.Form) → `assign_roll_to_adda` → roll save → CheckConstraint `rawmat_clothroll_weight_nonneg` → IntegrityError (RollAssignView catches only `(Adda.DoesNotExist, ValidationError)`) → 500. Fix: `min_value=0` on the form field. Mobile-relevant (roll assign is a floor data-entry surface; the number input had no `min`). |
| PA-08-EDITFORM | — | 08 | raw_materials/roll-edit | 📋 REFUTED | "RollEditForm accepts negative weight/cost → 500." It is a **ModelForm**; Django 5 validates the model CheckConstraint in `full_clean()`, so `is_valid()` is False (`__all__` error) → no service call, no 500. Already graceful (message leaks the constraint name — cosmetic, not fixed per no-speculative). |
| PA-08-PERM | LOW | 08 | raw_materials/intake | 📋 DOC (latent, unreachable) | `RollBulkCreateView.form_valid` catches `PermissionError` (Python builtin) but the service raises `django.core.exceptions.PermissionDenied` — wrong type. Latent only: the view is `SuperAdminOnlyMixin`, super-admin always passes `user_can_edit_financials`, so `bulk_create_rolls`' financial gate never fires here → PermissionDenied is unreachable from this view (would 403 anyway, not 500). Not fixed (not reproducible). |
| PA-09-1 | HIGH | 09 | production/cutting (legacy complete) | ✅ FIXED | `complete_cutting_legacy` CREATEs the `AddaStageRecord` unconditionally, but `(adda, workflow_stage)` is `unique_together` and the SR may already exist — `start_cutting`, any bundle/breakup op (`_get_or_create_cutting_stage_record`), or a prior complete+`reopen_cutting` (keeps the SR) all leave one. Second create → **IntegrityError**, uncaught by `CuttingCompleteView` (`except (ValidationError, PermissionDenied)`) → 500. Cleanest repro: legacy-complete → reopen → legacy-complete again. Fix: refuse gracefully if an SR exists (point at the workspace). |
| PA-09-2 | MEDIUM | 09 | production/cutting (bundles) | ✅ FIXED | `CuttingBundleItem` is `unique_together (bundle,pattern,color)` but `add_pieces_to_bundle`'s `get_or_create` keys on `(...,source_breakup)`. A manually-added line (`add_item_to_bundle`, `source_breakup=NULL`) for the same (pattern,color) then a breakup-consume → `get_or_create` can't match it → tries CREATE → unique violation → **IntegrityError** (uncaught by `CuttingBundleAddPiecesView`) → 500. Fix: detect the conflicting line before create → graceful ValidationError. |
| PA-09-CONSUME-LEFTOVER | — | 09 | production/leftover | 📋 REFUTED (benign) | `consume_leftover` sets `is_consumed=True` but never re-syncs the source `ClothRoll.remaining_*` denorm (no `_sync_roll_leftover` call), so a per-roll display column on 3 pages shows a stale leftover. Verified benign: `ClothRoll.remaining_*` is a pure read-cache — NO costing/settlement/barcode/pieces/pool code reads it; double-consume is governed by `is_consumed` (correct, `select_for_update`+recheck); leftover-availability dashboards Sum the PRIMARY `RemainingClothOfClothRoll` rows, not the roll denorm. Display drift only → not fixed. |
| PA-09-RECONCILE-SRC | — | 09 | production/reconcile | 📋 REFUTED (by-design) | `reconcile_denorm` checks `pieces_cut == Σ CuttingPieceBreakup.count`, while the modern workspace path sets `pieces_cut = Σ CuttingBundleItem.count` — so it can report plan≠actual as "drift". This is the DOCUMENTED + TESTED contract (model docstring "pieces_cut = SUM(breakup.count)"; `test_reconcile_denorm` codifies breakup-as-source). In correct usage Σ breakup == Σ items (Phase-06 verified clean on real data); a divergence is a legitimate plan/actual flag, not a false positive. Changing the source = redesign → not changed (no-redesign rule). |
| PA-09-RECONCILE-COV | LOW | 09 | production/reconcile | 📋 DOC (enhancement) | `reconcile_denorm` covers only `pieces_cut` + `total_barcodes`; it does NOT verify `CuttingPieceBreakup.consumed_count`, `CuttingBundle.total_pieces`, or `ClothRoll.remaining_*`. Drift in those would go undetected by the tool. Mitigated: all three are recomputed-from-truth on every write (`_recompute_*` / `_sync_roll_leftover`) so they self-heal; none feeds barcode/settlement truth. Adding checks = enhancement (no-feature rule) → documented, not built. |
| PA-09-TOTALPIECES-RACE | LOW | 09 | production/cutting (bundles) | 📋 DOC (display, race) | `_recompute_bundle_total`/`_recompute_breakup_consumed` re-sum without locking the bundle/items, so two managers concurrently adding items to the SAME bundle could persist a stale `total_pieces`/`consumed_count` (lost update). Display-only impact: `total_pieces` is NOT in the truth path (barcode/breakdown/`pieces_cut` read `Σ items` directly); recomputed correct on the next item op. Single-bundle two-actor concurrency = PA-05B-RACE class (not touching locked services for a theoretical race). |
| PA-10-1 | CRITICAL | 10 | production/credit (PAY-2) | ✅ FIXED | `ensure_worker_credit` (PAY-2) required a non-voided `StageWorkAssignment`, but in the documented-default config (`LEDGER_CREDIT_AT_ALLOCATION=False`) `allocate_stage_work` refuses and the settlement SWA is created at finalize (AFTER completion) → `complete_cutting_from_bundles`→`advance_to_next_stage(enforce=True)`→`ensure_worker_credit` raised → **NO Adda could complete cutting** (all 5 real cutting stages are `credits_workers=True`/self-paid; 0 cutting completions since the V2-3 flip). The code (credit.py:33) had flagged this SWA-read as needing the cutover. Fix: flag-aware — era-A (flag on) keeps the SWA check verbatim; settlement-first (default) requires a COMPLETED/VERIFIED `WorkerStageContribution` (the exact `_settleable_lines` predicate settlement pays). Verified cutting credits via worker self-report (3-PATTI-001 has 3 contributions). |
| PA-10-2 | HIGH | 10 | production/worker_task_service | ✅ FIXED | `set_stage_workers` cancelled a COMPLETED/VERIFIED task when a manager re-edits the roster mid-stage. `complete_worker_task` never stamps `stage_record.completed_at`, so a COMPLETED task sits on an OPEN stage; re-running `start_layering`/`start_cutting` with a reduced roster → the cancel-loop (excludes only CANCELLED) cancels it → its frozen `WorkerStageContribution` vanishes from settlement (`_settleable_lines` filters completed/verified) + the review screen → worker silently unpaid. Fix: never cancel COMPLETED/VERIFIED in the cancel loop (`resolve_stage_tasks_on_complete` already keeps them via `target`, so unaffected). |
| PA-10-3 | LOW | 10 | production/cutting + cutting_pattern | ✅ FIXED | `_get_or_create_cutting_stage_record` + `get_or_create_pattern_stage_record` skipped `ensure_stage_role_rates` (every other SR site calls it — Contract 2). The cutting rate snapshot was late-created at first worker completion with a spurious `snapshot_missing_at_complete` WARNING (the codebase treats that as a bug signal) — which PA-10-1 makes universal for cutting. Fix: snapshot at SR creation (idempotent, callers atomic). |
| PA-10-REOPEN-RATE | — | 10 | production/reopen | 📋 REFUTED (by-design) | "reopen refloats `AddaStageRoleRate` but settlement pays the contribution's stale frozen `expected_rate`." By-design: settlement (`adda_settlement_service:331`) pays each contribution at ITS frozen `expected_rate` = price-at-time-of-completion; the dedicated re-pricing tool is `rerate_stage_role` (recalcs completed-unsettled contributions + writes `RateCorrectionAudit`). `refloat_rates_on_reopen` targets RE-COMPLETIONS; the common reopen (no rate change) is correct. reopen+config-rate-change+re-settle is a footgun → use `rerate`. Not changing reopen (locked foundation, no-redesign). |
| PA-10-VERIFY-AUDIT | LOW | 10 | production/worker_task_service | 📋 DOC (by-design) | `set_verified_quantity` overwrites `verified_quantity` (only the latest survives) with no append-only audit / `AddaHistory` (unlike `rerate_stage_role`'s `RateCorrectionAudit`). By-design (owner model: `reported_quantity` immutable, `verified_quantity` = latest management correction). An audit trail for verified corrections = a future enhancement (no-feature rule). |
| PA-10-GROUPED-PREVIEW | MEDIUM | 10→11 | expense/settlement preview | 📋 DOC (Phase 11) | The grouped→₹0 structural guard (`effective_pay_rate`) is applied at finalize (`adda_settlement_service:331`) but NOT at the settlement PREVIEW/queue surfaces (`settlement_queue:195`, `expense/views.py` `_line_dict`/totals), which use raw `c.expected_rate`. A stage grouped AFTER its workers completed shows ₹(qty×stale_rate) in the approval gate while finalize correctly books ₹0. VISIBILITY divergence only (booked money correct). Defer to Phase 11 (Settlement) — settlement-preview surface + unusual group-after-complete scenario. |
| PA-10-VERIFY-RACE | LOW | 10→11 | expense/settlement | 📋 DOC (Phase 11) | `finalize_adda_settlement` locks `AddaStageRecord` ("freeze quantity inputs") but `verified_quantity` lives on `WorkerStageContribution`, which finalize does NOT lock; `set_verified_quantity` takes neither 5374 nor the AddaStageRecord lock → a verified edit racing an in-flight finalize can be booked on the stale quantity. Two-actor, recoverable via reverse/supersede. Defer to Phase 11 (settlement finalize locking) — PA-05B-RACE-adjacent. |
| PA-10-ROLE-NONE | — | 10 | production/contribution-rate | 📋 REFUTED (benign) | A skilled worker with `User.role=None` completing freezes at the base rate (skips per-role override) + `role_snapshot=None`. Benign: role=None → base rate is the sensible fallback (no role = no override to apply); assignment is skill-gated by design (PA-03-WORKER-SKILL WONTFIX). Not a defect. |
| PA-11-1 | MEDIUM | 11 | expense/payroll_service | ✅ FIXED | `outstanding_advances()` summed `PayrollSettlementItem.amount_recovered` WITHOUT `reversed_at__isnull=True` — unlike its siblings `advance_remaining`/`advance_outstanding`. So after a settlement-with-recovery is REVERSED, the reversed PSI still counted as recovered → the restored advance showed understated remaining (or, if fully-recovered-then-reversed, dropped out at the `remaining>0` gate) → vanished from the settlement recovery UI (`expense/views.py:386`) → owner couldn't re-recover it. Money truth was correct (finalize uses `advance_remaining`); this was a visibility/re-recovery gap. Fix: add `reversed_at__isnull=True` (one line, consistent with siblings). |
| PA-11-2 | MEDIUM | 11 | expense/settlement preview | ✅ FIXED | (carried PA-10-GROUPED-PREVIEW) the grouped→0 structural guard (`effective_pay_rate`) was applied at finalize but NOT at the two settlement-preview surfaces — `settlement_queue` (`adda_settlement_service:195`) + `AddaSettlementDetailView._line_dict` (`expense/views.py:347`, feeding per-worker + `grand_expected`). A stage grouped AFTER completion has a stale non-zero frozen `expected_rate`, so the approval gate showed ₹(qty×stale) while finalize correctly books ₹0. Visibility-only (money correct), but the approver saw a number finalize won't pay. Fix: apply `effective_pay_rate` at both preview sites (mirror finalize; completes the F2 invariant). |
| PA-11-3 | MEDIUM | 11 | expense/adda_settlement_service | ✅ FIXED | (carried PA-10-VERIFY-RACE) `finalize_adda_settlement` locked `AddaStageRecord` ("freeze quantity inputs") but `verified_quantity` lives on `WorkerStageContribution`, which finalize never locked — and `set_verified_quantity` takes neither the 5374 advisory lock nor the SR lock. A verified-quantity correction committing during the finalize window was a lost update → money booked on the stale quantity (the in-code comment falsely claimed the SR lock froze verified edits). Two-actor, recoverable. Fix: finalize now `select_for_update(of=('self',))` the WSC rows of the payable stages (the SAME target `set_verified_quantity` locks) → a racing verify blocks, then sees `settlement_line` stamped and refuses; corrected the comment. No deadlock (every settlement op takes 5374 first; set_verified takes only the WSC row). |
| PA-12-A | MEDIUM | 12 | expense/payroll_service | ✅ FIXED | `payroll_totals()` (operations digest) summed `PayrollSettlementItem.amount_recovered` WITHOUT `reversed_at__isnull=True` → after a settlement reversal the reversed recovery still counted as recovered → factory-wide `advance_exposure` understated. Fix: add the `reversed_at` filter (consistent with `advance_remaining`/`advance_outstanding`/`outstanding_advances`). Ledger payable always correct. |
| PA-12-B | MEDIUM | 12 | expense/PayrollOverviewView | ✅ FIXED | The management payroll overview's `recovered_map` summed recoveries WITHOUT `reversed_at__isnull=True` → the "Advance Out" column + `total_advance_out` understated a worker's outstanding advance after a settlement reversal (disagreed with worker-detail). Fix: add the `reversed_at` filter. |
| PA-12-C | MEDIUM | 12 | expense/PayrollOverviewView | ✅ FIXED | The overview computed `total_earnings = credits − reversals` (all-credits − all-debit-reversals) and `total_settled = settled` (gross). A settlement reversal writes a CREDIT/REVERSAL (undoing the advance-recovery debit), which inflated "Earned"; a reversed payment would inflate "Settled". Both disagreed with `worker_summary`. Fix: the grouped aggregate now nets BY CATEGORY exactly like `worker_summary` — `earned` (EARNING-category credits) − `earned_reversed` (reversals of earnings); `settled` − `settled_reversed`. Overview now matches each worker's own page. Payable (credits−debits) was always correct. |
| PA-12-BREAKDOWN | — | 12 | expense/payroll_service | 📋 DOC (dead code) | `worker_balance_breakdown()` is unwired (no view/template caller); its `debits_by_category` would show gross recovery debits after a reversal. No user-visible figure is wrong. Flagged so a future wiring nets REVERSAL rows. |
| PA-12-GROUPED-BOARD | LOW | 12 | expense/PayrollOverviewView | 📋 DOC (by-design) | A worker who did ONLY grouped/zero-cost stage work (earning 0 → no ledger credit booked) + has no advance is absent from the payroll overview board (`worker_ids = ledger | given | recovered`, not `pieces_map`), so their pieces don't show. By-design: the board scopes to payroll activity (who's owed); a ₹0-payable worker is out of scope and productivity has its own views. Not changed (board-scope is a product decision, no-feature). |
| PA-13-1 | HIGH | 13 | inventory/barcode-dashboard | ✅ FIXED | `BarcodeDashboardView` per-Adda counts used ONE `.annotate()` mixing `Sum('barcode_batches__total_pieces')` (relation A) + `Count('barcodes', …)` (relation B) → cartesian JOIN: `total` inflated ×#barcodes, packed/dispatched/missing inflated ×#batches, the moment a multi-batch Adda had ≥1 scanned piece (repro: 2 batches + 3 scanned → total 300 not 100, packed 4 not 2). The page's KPI cards (separate queries) were correct → page self-contradicted. `.distinct()` doesn't fix join-multiplied aggregates. Fix: compute `total` (BarcodeBatch grouped) + scanned-by-status (BatchBarcode grouped) from SEPARATE per-Adda queries (same approach as the KPIs), attach in Python. `inventory/views/tracking_dashboard.py`. |
| PA-13-2 | HIGH | 13 | raw_materials/roll-list | ✅ FIXED | `RollListView.get_queryset` applied `qs.filter(cloth_type_id=type_id)` (also color/location) from the raw GET string → a non-numeric value (`?cloth_type=abc`, stale/tampered link) raised `ValueError` → **500**, making the whole roll list unreachable. (The chip block caught it; the queryset filter didn't — PA-08 guarded the dashboards, not these list filters.) Fix: `.isdigit()` guard on the three id filters (ignore a non-numeric filter). |
| PA-13-3 | HIGH | 13 | raw_materials reporting | ✅ FIXED | The PA-03-1 financial-leak REOPENED on 3 reporting surfaces: the cloth-roll Time-Logs accordion (`_roll_events_accordion.html` renders `field_name: old → new`) on the **roll list**, the **cloth dashboard**, and the **raw-material dashboard** rendered `ClothRollHistory` `cost_per_kg`/`supplier` CHANGE VALUES to worker/manager (non-financial) — the exact figures the roll table/detail hide. (PA-03-1 only fixed the dedicated roll-history timeline.) Fix: server-side `exclude(field_name__in=('supplier','cost_per_kg'))` for non-financial viewers on all 3 querysets (same as PA-03-1). |
| PA-13-4 | MEDIUM | 13 | accounts/user-list | ✅ FIXED | `UserListView.get_queryset` did `qs.filter(skills__id__in=skills)` from `GET.getlist('skills')` → a non-numeric value (`?skills=abc`) → `ValueError` → 500. Super-admin-only surface (low blast radius). Fix: keep only numeric ids (mirrors the `int()`-guard the context builder already applies to `selected_skills`). |
| PA-13-5 | LOW | 13 | raw_materials/roll-list | ✅ FIXED | `?status=garbage` returned 200 but rendered a misleading "Status: garbage" active-filter chip + a `filtered_count` equal to the FULL list (the filter only applies for valid choices, but the chip showed for any non-empty status). Fix: ignore an invalid status in the context so chip + filtered_count match `get_queryset`. |
| PA-13-6 | LOW | 13 | barcode export | ✅ FIXED | The CSV/XLSX barcode manifest wrote free-text `color`/`size` labels (ClothColor.name/ProductSize.label — no char validator) verbatim → a label starting with `= + - @ tab CR` executes as a formula when a production-role user opens the manifest in Excel/LibreOffice (CSV-injection). No wrong count/total; not financial. Fix: `_csv_safe` prefixes a formula-leading cell with `'` in both CSV + XLSX renderers (`export_service.py`). |
| PA-12-PIECES-SEMANTICS | — | 12 | expense/payroll | 📋 REFUTED (labeling) | The overview "Pieces" (Σ SWA.allocated_quantity = settled qty) and `worker_production_stats.pieces` (Σ good_quantity = production output) measure different things and can differ. No money impact; a labeling/semantics nuance, not a defect. |
| PA-14-1 | HIGH | 14 | expense/settlement-detail | ✅ FIXED | Settlement-detail per-worker tables (incl. **Final payable ₹ / Recovered ₹** money columns) were bare `<table>`s with no `.table-responsive` wrapper. Page content lives in `main.content { overflow-x: hidden }`, so the ~448px table was **clipped with NO horizontal scroll** at 320–414px — the rightmost money columns were invisible + unreachable on a phone. Fix: wrapped all 6 tables in `.table-responsive` + `data-label` on every `<td>` (the documented stacked-card standard) → on mobile each row becomes a label:value card with every column visible. Verified at 320px (Final payable ₹ 225.00 now shown). |
| PA-14-2 | MEDIUM | 14 | filter-card (5 pages) | ✅ FIXED | `.filter-card` (roll-list, adda-list, adda-dashboard, cloth-dashboard, tracking/barcode-dashboard) is `flex-wrap:nowrap; overflow-x:auto` with `min-width:150px` fields → on a phone the filter row scrolled sideways (e.g. roll-list: 6 fields = ~864px on a 320px screen), fields cut mid-field, later filters hidden with no scroll affordance. No page had a mobile-stacking media rule. Fix: added `@media (max-width:600px) { flex-direction:column; align-items:stretch; overflow-x:visible; fields/inputs width:100% }` to all 5 page-scoped definitions → filters stack full-width, all discoverable. |
| PA-14-3 | MEDIUM | 14 | base.html / fancy-select | ✅ FIXED | fancy-select JS swaps `<select>`→`<button class="fancy-select-trigger [copied select classes]">`. A `<select>` styled only by **tag name** (`.expense-form select{}`) loses all box styling because the trigger is a button, not a select → rendered as a bare ~20px UA-grey line (sub-44px touch target, inconsistent with sibling cream inputs). Hit advance-add, settle-create, layering-workspace roll filters (a worker phone surface). Fix: JS now tags a class-less trigger with `.fancy-select-trigger--bare`, defined in base.html as a default cream input box + `min-height:44px`. **Zero regression to classed triggers** (`.sf-input` etc. never receive `--bare`). Verified: triggers now 44px cream boxes; dropdown still opens (7 opts). |
| PA-14-TOPBAR-TITLE | — | 14 | base.html / topbar | 📋 REFUTED (intended) | Mobile topbar page-title (`.topbar-title`) reports scrollWidth>clientWidth on long titles. By design: `white-space:nowrap; overflow:hidden; text-overflow:ellipsis` — intended ellipsis truncation; the full title is also shown in the page hero/H1. Not a clip bug. |
| PA-14-HERO-FLEX | — | 14 | shared `.hero` | 📋 REFUTED (false positive) | The overflow detector flagged `.hero` (scrollWidth ≈ clientWidth+100) as clipped on many pages. Visually clean at 320px (full hero content fits + visible); the excess scrollWidth is a flex min-content artifact, no child rect exceeds the viewport, nothing is cut. Not a bug. |
| PA-11-SOUND | — | 11 | expense/settlement | 📋 VERIFIED SOUND | Finder-verified (main-thread re-checked) with NO defect: finalize money-write (qty=verified-else-good × grouped-guarded rate, ROUND_HALF_UP; era-A/B exclusion; recovery ≤ remaining under lock; tie-out; S5 block rolls back atomically); reverse/supersede (compensating ledger + PSI `reversed_at` + SWA soft-void re-arm; FINALIZED-only guard; multi-level chain isolation); ledger idempotency (double-finalize/double-reverse blocked under 5374; `uniq_one_reversal_per_entry` DB constraint; balance nets reversals to 0); `verified_quantity=0` pays 0; alter/missing never enter the payable; recovery>earning negative balance is by-design (advance pool independent of this Adda's earning). The 5374 advisory lock serializes all finalize/reverse/rerate; lock orders are deadlock-free. |
| PA-15-1 | MEDIUM | 15 | production/product_sizes_edit | ✅ FIXED | Active/Archived Sizes tables were bare `<table>`s whose Label cell holds an inline-edit `<form>` with fixed-width inputs (`input[name=label]{width:140px}` + number input + Save). Fixed-width inputs **can't shrink**, so the table was forced to **351px** and the Actions/Archive column was **clipped off-screen at ≤340px with no scroll** (`main.content overflow-x:hidden`) — could not archive a size on a phone. Browser-confirmed at 320px (rightEdge 384, screenshot). The page-scoped `.btn-mini` Save/Archive were also only **28px** tall (sub-44 touch). Fix: wrapped both tables in `.table-responsive` + `data-label` on every `<td>` + `class="cell-edit"` on the form cell + `class="td-actions"` on the action cell + a `@media(≤600px)` block stacking the edit form full-width and bumping `.btn-mini` to 44px. Verified at 320px (stacks to label:value cards, Archive reachable, buttons 44px) and 1280px (unchanged). |
| PA-15-2 | LOW | 15 | production/product_patterns_edit | ✅ FIXED | Identical inline-edit bare-table pattern as PA-15-1 (sibling config page; Pattern · Pieces/Adda[number input+Save] · Remove). Currently fits at 320px for short data (254px) but shares the clip-prone structure (fixed-shrink inputs) and the 28px `.btn-mini` sub-44 touch target. Fixed together with PA-15-1 (same `.table-responsive`+data-label+cell-edit+td-actions+44px treatment). Verified stacks at 320px, unchanged at 1280px. |
| PA-15-3 | LOW | 15 | production/pattern_workspace | ✅ FIXED | The cutting-pattern panel partial (`_stage_panel_cutting_pattern.html`) is included by TWO hosts: `stage_panel_embedded.html` (scopes `.breakup-table` mobile stacking on the bare element → stacks) and the standalone `pattern_workspace.html` (includes `_form_styles.html`, which scopes stacking under `.form-shell .breakup-table` — but the workspace wrapper is NOT `.form-shell`). So in the standalone path the panel's `data-label` attrs were **dead**: `thead` stayed visible and tables rendered cramped/unstacked on phones (browser-confirmed thead visible at 320px). Fix: added a bare-`.breakup-table` mobile stacking block to `pattern_workspace.html` `extra_head` (mirrors the embedded path) so the same partial stacks identically in both hosts. Verified stacks at 320px, unchanged at 1280px. |
| PA-15-ADV-SAFE | — | 15 | expense/worker_detail · settlement_form | 📋 DOC (verified safe) | The `.adv` money tables (worker_detail: Date·Amount·Recovered·Remaining; settlement_form: Date·Remaining) are bare `<table>`s with `data-label` but no `.table-responsive` wrapper (data-label inert). **Verified NOT a clip bug** (browser, injected+deleted a temp advance): they are **text-only** — cells wrap freely, the table shrinks to fit, all money columns stay visible at 320px (worker_detail 272px, settle 266px). Unlike PA-15-1's inline-edit table (form inputs can't shrink → clips), text tables wrap-and-fit. Left bare per no-speculative rule; residual = a very long advance note only makes the Date cell taller, never wider. |
| PA-15-STACK-SAFE | — | 15 | cutting-panel · costing · adda_settlement_list · payroll_overview | 📋 VERIFIED SOUND | The other carry-forward bare-table surfaces each ship their **own page-scoped stacking** (`.<scope> thead{display:none}` + `td::before{content:attr(data-label)}` at ≤640/720px) instead of `.table-responsive`. Browser-confirmed at 320px: thead hidden, no clip on all four. Functionally equivalent to the canonical wrapper; left as-is (working + tested). |
| PA-15-SELECT-CLEAN | — | 15 | fancy-select | 📋 VERIFIED SOUND | All remaining class-less `<select>` (layering filters, product_flow cost selects, user role, pattern-add) are covered by the Phase-14 `.fancy-select-trigger--bare` fallback. Browser-confirmed 44–45px cream boxes at advance-add + user-add. No migration to explicit `.sf-input`/`.field` classes needed — the fallback already gives a consistent touch-sized control (migration would be cosmetic, no-speculative). |
| PA-15-DATE-CLEAN | — | 15 | date inputs | 📋 VERIFIED SOUND | Native `type=date` inputs (adda/cloth/barcode dashboards via stacked `.filter-card`; advance_date, settlement_date, joining_date; roll purchased_date) render full-width (305–313px) with no clip/overlap at 320/375px; OS calendar picker reachable; 37–44px tall. Clean. |
| PA-15-TOUCH-CLEAN | — | 15 | touch targets | 📋 DOC | Sub-44px actionable elements found: only page-scoped `.btn-mini` (28px → fixed in PA-15-1/2). `.hamburger` (36px) + `.close-btn` (30px) are established sidebar chrome (prior-phase verified, unchanged); the app-wide `.btn` baseline is 38px (global token change = out of stabilization scope); `.worker`/`.ref` (16px) are inline text-link row actions (tappable line). No new regression. |
| PA-16-1 | HIGH | 16 | expense/adda_settlement_service | ✅ FIXED | Settlement-detail DRAFT + settlement queue + preview: `_settleable_lines` select_related'd `task__stage_record` but NOT `__workflow_stage__stage`, yet the consumers (`_line_dict`, `settlement_queue`, `cost_service.effective_pay_rate`) read `c.task.stage_record.workflow_stage.stage.name` **per contribution line** → 2 extra queries (workflow_stage + stage) for EVERY line. **Measured:** settlement-detail draft +4q/line (17q@1 line → 33q@5 lines); queue +5.3q/Adda. A real multi-size/colour cutting Adda (30+ lines) ran ~137 queries on a money-approval page. Fix: add `task__stage_record__workflow_stage__stage` to the select_related (one line; fixes detail + queue + preview + reuses the same join finalize already pays for). After: +2q/line on detail (the rest = PA-16-2); queue +4q/Adda. |
| PA-16-2 | MEDIUM | 16 | expense/views (AddaSettlementDetailView) + payroll_service | ✅ FIXED | Same draft page called `outstanding_advances(worker)` in a loop (`for w in by_worker.values()`) → 2 queries (advances + recovered SUM) **per distinct worker** = an N+1 over workers on the finalize gate. Fix: new `payroll_service.outstanding_advances_bulk(workers)` — same row shape + the SAME `reversed_at__isnull=True` filter (PA-11-1) — computes all workers in **2 queries total**; the view calls it once. **Measured after PA-16-1+2: settlement-detail draft is now FLAT at 15q for 1 and 5 lines (delta/line = 0)** — O(1) in contribution lines. Equivalence regression-tested (bulk rows == per-worker rows). |
| PA-16-DUP | — | 16 | production/adda-detail | 📋 REFUTED (measured) | Hypothesis: `AddaDetailView` evaluates `sr_qs` for `sr_by_type` then `sr_qs.order_by(...)` as `ctx['stage_records']` → a duplicate stage-record fetch + re-run prefetches. **Measured false:** the `worker_tasks` prefetch query ran **×1** (a duplicate full evaluation would re-run it). adda-detail = 25q for a rich K-stage tabbed page (per-stage snapshot + per-stage RBAC); the only repeats are tiny role PK-lookups (×6, bounded by stage count, not data growth). Not a defect; bounded by flow length, not data volume. Not touched (no-speculative rule). |
| PA-16-QUEUE | LOW | 16 | expense/adda_settlement_service | 📋 DOC (measured, deferred) | `settlement_queue` loops Addas calling `_payable_stage_records` + `_settleable_lines` per Adda → after PA-16-1 a residual **~4 queries/Adda** (stage records + contributions + era-A pairs). Measured (6q@1 Adda → 17q@4). STRUCTURAL: inherent to classifying every pending Adda; **bounded by the pending-unsettled queue** (fully-credited Addas drop out → it does NOT grow with all-time Adda count). Batching across Addas = redesigning the locked `_settleable_lines` (shared with finalize) + queue classification — explicitly out of scope ("no redesign of settlement logic to chase speed"). Documented, not chased. |
| PA-16-CLEAN | — | 16 | money + cutting read paths | 📋 VERIFIED SOUND (measured) | Marked clean only after MEASUREMENT (honesty rule), not code-reading: **my-earnings** (34q flat, 1→5 Addas worked), **worker-detail** (39q flat), **payroll-overview** (10q flat, 1→9 workers — pre-aggregated maps), **get_cutting_snapshot** (8q flat, 1→5 bundles — `prefetch_related('items__pattern','items__color')` works). Read-confirmed already-optimized (prior phases, explicit N+1-prevention comments): 5 dashboards (adda/raw-material/cloth/barcode/inventory), costing (10q locked), adda-list (11q locked), roll-list (select_related+paginated), exports (rows computed from batch seq-ranges, no per-label query), barcode list/print, history timelines, worker-report. |

### Issues fixed
Phase 02: PA-02-1, PA-02-2, PA-02-3, PA-02-4, PA-02-OPEN-SIGNUP.
Phase 03: PA-03-1 (financial-history leak).
Phase 04: PA-04-1 (dead signup links).
Phase 05A: PA-05A-1..5 (Skill delete guard, Role extra-role guard, Role messages, pattern int-parse, UserCreate IntegrityError).
Phase 05B: PA-05B-1 (settlement finalize int-parse crash), PA-05B-2 (cutting breakup atomic).
Phase 06: PA-06-1 (WorkerProfile opening_advance ≥ 0), PA-06-2 (WorkerProfile bank-detail validation). All with regression tests (671 green). Full reports below.
Phase 07: PA-07-1 (worker-report non-numeric quantity → 500), PA-07-2 (review verified-qty non-numeric → 500) — one root cause, fixed at the `worker_task_service` writer boundary. +2 regression tests (673 green).
Phase 08: PA-08-1 (bulk-intake negative cost → 500), PA-08-2 (roll-assign negative weight → 500) — `min_value=0` on the two plain-form DecimalFields (DB CheckConstraint mirrored at the form layer). +4 regression tests (677 green).
Phase 09: PA-09-1 (legacy-cutting unconditional SR create → IntegrityError 500), PA-09-2 (mixed manual+breakup bundle add → unique-collision IntegrityError 500) — both converted to graceful ValidationError. +2 regression tests (679 green).
Phase 10: PA-10-1 (CRITICAL — `ensure_worker_credit` blocked all cutting completion in the default flag-off config; made flag-aware → production-truth credit), PA-10-2 (HIGH — `set_stage_workers` cancelled COMPLETED tasks → orphaned pay), PA-10-3 (LOW — `ensure_stage_role_rates` SR-site coverage). +6 regression tests (685 green); golden ₹225 settlement byte-identical.
Phase 11: PA-11-1 (MEDIUM — `outstanding_advances` ignored `reversed_at` → reversed recovery hid the restored advance), PA-11-2 (MEDIUM — grouped→0 not applied at settlement preview/queue), PA-11-3 (MEDIUM — finalize didn't lock the WSC rows holding `verified_quantity`). +2 regression tests (PA-11-3 = structural lock, covered by existing finalize/verify tests). 687 green; golden ₹225 byte-identical.
Phase 12: PA-12-A (MEDIUM — `payroll_totals` advance_exposure ignored `reversed_at`), PA-12-B (MEDIUM — overview advance_outstanding ignored `reversed_at`), PA-12-C (MEDIUM — overview earnings/settled didn't net reversals by category). +1 regression test (asserts overview == worker_summary == ledger after a reverse). 688 green.
Phase 13: PA-13-1 (HIGH barcode-dashboard cartesian-JOIN), PA-13-2 (HIGH roll-list non-numeric filter 500), PA-13-3 (HIGH cost/supplier leak via 3 time-log accordions), PA-13-4 (MEDIUM user-list `?skills` 500), PA-13-5 (LOW garbage-status chip), PA-13-6 (LOW CSV/XLSX formula-injection). +8 regression tests. 696 green.
Phase 14: PA-14-1 (HIGH settlement-detail money tables clipped off-screen → `.table-responsive`+data-label on 6 tables), PA-14-2 (MEDIUM `.filter-card` horizontal-scroll hides filters on 5 dash/list pages → mobile-stack media rule), PA-14-3 (MEDIUM class-less fancy-select trigger = bare 20px line → `.fancy-select-trigger--bare` default box, 44px touch target). UI-only (CSS/template/JS), browser-verified at 320/375/390/414px; 696 green (no unit-test delta). **UI_COMPONENTS.md updated** with 3 reusable rules. 2 refuted (topbar-title ellipsis = intended; `.hero` flex scrollWidth = false positive).
Phase 15: PA-15-1 (MEDIUM product_sizes_edit inline-edit table clipped Archive off-screen + 28px mini buttons), PA-15-2 (LOW product_patterns_edit identical pattern), PA-15-3 (LOW standalone pattern_workspace breakup-tables had dead data-label / no stacking host). UI-only (3 templates: product_sizes_edit, product_patterns_edit, pattern_workspace), browser-verified at 320/375/390/414/1280px; 696 green (no unit-test delta). **UI_COMPONENTS.md updated** with 3 reusable rules (data-label-needs-wrapper · inline-edit-vs-text clip · shared-partial responsive ownership). 5 documented SAFE/CLEAN (worker_detail/settle `.adv` text-wrap; 4 own-stacking surfaces; fancy-select `--bare` fallback; native date inputs; touch targets).
Phase 16: PA-16-1 (HIGH — settlement-detail draft + queue + preview per-line N+1 on `workflow_stage.stage`; `select_related` fix), PA-16-2 (MEDIUM — settlement-detail draft `outstanding_advances` per-worker N+1; new `outstanding_advances_bulk` = 2 queries). **Settlement-detail draft now O(1) in contribution lines** (measured flat 15q at 1 & 5 lines; ~137q→15q on a 30-line Adda). 1 refuted by measurement (PA-16-DUP adda-detail), 1 documented-deferred (PA-16-QUEUE structural per-Adda cost), measured-clean money + cutting read paths (PA-16-CLEAN). Files: `expense/services/adda_settlement_service.py`, `expense/services/payroll_service.py`, `expense/views.py`, `config/expense/README.md`. +4 regression tests (assertNumQueries scale-invariance + bulk equivalence). 700 green.

### Open blockers
- None. (PA-05A-SF1..4 storefront validation gaps documented for a small follow-up — need model+migration; storefront not yet live.)

---

## PHASE 01 — SYSTEM MAPPING · RESULT

**Deliverable:** [docs/AUDIT_SYSTEM_MAP.md](AUDIT_SYSTEM_MAP.md) (complete inventory).

**Coverage (cross-validated against source `urls.py`):**

| App | Prefix | URLs | Views | Services | Forms | Templates |
|-----|--------|-----:|------:|---------:|------:|----------:|
| accounts | `/app/` | 23 | 23 | 3 | 5 | 20 |
| inventory | `/inventory/` | 8 | 8 | 1 | 1 | 12 |
| tracking | `/tracking/` | 12 | 12 | 2 | 0 | 7 |
| production | `/production/` | 68 | 68 | 13 | 16 | 43 |
| raw_materials | `/raw-materials/` | 22 | 22 | 2 | 6 | 11 |
| expense | `/expense/` | 9 | 9 | 9 | 3 | 8 |
| storefront | `/storefront/` | 9¹ | 9 | 1 | 5 | 8 |
| **TOTAL** | | **151** | **151** | **31** | **36** | **109** |

¹ storefront = 8 in `storefront/urls.py` + `public_home` mounted at root `/` (in `config/config/urls.py`).
Plus: `core` (abstract base models, no tables), Django admin `/admin/`, allauth `/accounts/`.

**Key facts captured for downstream phases:**
- **RBAC layers (5):** sidebar visibility (`build_menu_for`) · URL access (`SidebarAccessMiddleware` + `can_access_url_name`) · view perms (role.permissions M2M) · stage-panel access (`access_service.user_can_access_stage`, skill-gated) · financial fields (`FINANCIAL_ROLES`). Super-admin bypasses all (dual: `is_superuser` OR `role.code=='super_admin'`).
- **Roles:** super_admin, manager, worker, listing_team, accountant. `role` (FK) + `extra_roles` (M2M) stack.
- **Middleware stack (11):** custom = `core.observability.RequestIDMiddleware` (#2) + `inventory.middleware.SidebarAccessMiddleware` (#11).
- **Feature flags (defaults):** `LEDGER_CREDIT_AT_ALLOCATION=False`, `ENFORCE_ALLOCATION_BOUND=False`, `ENFORCE_SETTLEMENT_RECONCILIATION=False`, `SETTLEMENT_RECONCILIATION_TOLERANCE=0`, `STALLED_ADDA_DAYS=3`.
- **Auth:** OTP login (email) + password fallback + Google OAuth (pre-provisioned only); Argon2; rate-limited; DB sessions 8h.
- **Mgmt commands:** `reconcile_pay` (expense), `preview_allocation_bound` (production), `reconcile_denorm` (production), `seed_homepage` (storefront).

**Bugs found in Phase 01:** none (mapping phase — no behavioral testing performed).

---

## PHASE 02 — AUTHENTICATION AUDIT · RESULT

**Scope:** login (OTP + password + Google), logout, session, redirects, unauthorized access, signup, password reset, throttle, OTP lifecycle, auth-page mobile rendering.

**Method:** deep code read of `accounts/{views,forms,throttle,utils,allauth_adapters,models}.py` + `auth_service`; adversarial finder workflow (6 lenses → 18 candidates → per-finding verify); independent re-verification at DB level (`manage.py shell`, rolled back), HTTP level (Django test client), and browser level (headless Chromium 320/375/414/1280px). Server: dev runserver on :8000.

**Evidence captured:**
- Anonymous → every protected URL 302→`/app/?next=…` ✓. Logout GET→redirect (no logout, CSRF-safe), POST→logout ✓. Authed hitting login pages → redirect to home ✓.
- Auth pages (login/signup/password): **no horizontal overflow 320–1280px, no console JS errors** (only Google-Fonts CDN requests). Login form DOM verified present + visible.
- role=None self-signup user **contained**: my-dashboard 200 (empty); production/raw-materials/users → 302 redirect; payroll → 403. No privilege escalation.
- DB: `normalize_email('Foo.Bar@Example.COM')` → `Foo.Bar@example.com` (local-part case kept); exact lowercased filter MISSES, `__iexact` matches. Dev DB: 12 users, 0 mixed-case.
- Post-fix browser: OTP box width 320px **30→39px**, 360px **46px**, separator dropped ≤360, no overflow; screenshot `/tmp/audit_otp_320.png`.

### BUG PA-02-1 — Account enumeration via password-reset / OTP-verify step
- **Severity:** HIGH · **Module:** accounts/auth · **URL:** `/app/forgot-password/` + `/app/reset-password/verify/` (and `/app/verify-otp/`) · **Role:** anonymous · **Device:** both
- **Reproduction:** (1) POST forgot-password with a **non-existent** email → redirect to reset-verify. (2) POST reset-verify with any OTP → **"Session expired. Please start again."** + redirect to forgot-password. (3) Repeat with a **real** email → reset-verify POST returns **"Invalid OTP. N remaining"** and stays on the page. Different message/redirect = existence oracle. Same shape at the OTP-verify step for login.
- **Expected:** identical behavior for existent vs non-existent email (the code comments claim anti-enumeration).
- **Actual:** `ForgotPasswordView` set `session['reset_email']` only inside `if email exists`; `LoginView` issued a real OTP only for existing emails, so the verify step diverged.
- **Root cause:** anti-enumeration was implemented at step 1 (redirect) but not step 2 (verify); session/OTP state differed by existence. `config/accounts/views.py` `LoginView.post`, `ForgotPasswordView.post`.
- **Fix:** always set the session email key in both branches **and** stash a **decoy OTP** (random, un-emailed) for non-existent emails, so the verify step returns "Invalid OTP" identically. `accounts/views.py:84-116, 534-560` + import `generate_otp, store_otp_in_session`.
- **Verification:** new tests `test_login_verify_step_unknown_email_same_as_known`, `test_forgot_password_unknown_email_same_as_known`. 646 green. Browser: non-existent email still renders the verify page.
- **Status:** ✅ FIXED

### BUG PA-02-2 — Mixed-case-local email locked out of OTP login / reset
- **Severity:** LOW (latent; 0 affected in dev) · **Module:** accounts/auth · **Device:** both
- **Reproduction:** create a user whose email local part has uppercase (e.g. via `manage.py createsuperuser` with `Foo.Bar@x.com`; `normalize_email` keeps local-part case). Enter `foo.bar@x.com` on OTP login → `User.objects.filter(email=email)` exact match fails → treated as non-existent → no OTP → cannot log in via OTP or reset.
- **Expected:** email identity is case-insensitive (forms already use `email__iexact`).
- **Actual:** OTP/reset views used exact `filter(email=…)` / `get(email=…)` against a fully-lowercased input.
- **Root cause:** inconsistent lookup; `accounts/views.py` lines 102/139/183/544/591.
- **Fix:** switch those five lookups to `email__iexact` (matches the forms; no behavior change for already-lowercase data).
- **Verification:** `test_otp_login_resolves_mixed_case_email_end_to_end` (full OTP flow), `test_forgot_password_recognises_mixed_case_email`. 646 green.
- **Status:** ✅ FIXED · **Residual (documented, LOW):** password login still uses Django's exact `get_by_natural_key`; a mixed-case-local user can log in via password only by typing the exact case. Out of scope (custom backend = redesign).

### BUG PA-02-3 — Auth pages cacheable (back-button after logout)
- **Severity:** LOW · **Module:** accounts/auth · **Device:** both
- **Reproduction:** load an auth page (e.g. `/app/`); response had no `Cache-Control: no-store`, so a browser/bfcache could redisplay it via back button after logout.
- **Root cause:** only `LogoutView` had cache headers; the GET-render auth views did not.
- **Fix:** `@method_decorator(never_cache, name="dispatch")` on `LoginView, VerifyOTPView, PasswordLoginView, SignupView, SignupVerifyView, ForgotPasswordView, ResetPasswordVerifyView`.
- **Verification:** `test_auth_get_pages_set_no_store`. 646 green.
- **Status:** ✅ FIXED

### BUG PA-02-4 — Mobile: OTP digit boxes too narrow + reset_otp inconsistent
- **Severity:** MEDIUM (mobile-priority) · **Module:** accounts/templates · **Device:** mobile ≤375px
- **Reproduction:** open OTP page at 320px → 6 digit boxes computed to ~30px wide (< 44px touch min). Also `reset_otp.html` @media(≤480px) omitted the `.otp-digit{height:52px}` shrink that `otp.html`/`signup_otp.html` had → inconsistent box height.
- **Fix:** added `.otp-digit` shrink to `reset_otp.html` ≤480px rule; added a ≤360px rule to all three OTP templates that drops the decorative `.otp-sep` and tightens the gap + card padding so boxes widen.
- **Verification (browser):** 320px **39px** (was 30), 360px **46px** (≥44), no overflow 320–414px; screenshot `/tmp/audit_otp_320.png`.
- **Status:** ✅ FIXED · **Residual (documented):** true 44px width at 320px isn't achievable with 6 boxes without a layout redesign (out of scope); ~39px tall-box numeric input is usable.

### PA-02-OPEN-SIGNUP (findings [8]/[9]) — RESOLVED (owner: disable native signup)
- **Severity:** HIGH (policy) · **URL:** `/app/signup/` (+ verify), was linked as "Create one →" on both login pages.
- **Verified:** anyone could self-register (email+password+OTP-to-own-email) → a real `User` (role=None). **Contained** (role=None → empty personal dashboard; all management/production/admin URLs 302/403). **No privilege escalation.** Contradicted the documented invariant "pre-provisioned users only (no open signup)".
- **Owner decision (2026-06-14):** disable native signup; align code with the documented internal-ERP invariant. Public signup (invite/allowlist/portals) is future product scope, not an audit fix.
- **Fix applied:**
  - Removed the 3 signup routes from `accounts/urls.py` (+ their imports; left a re-enable note).
  - Removed the "Create one →" links from `login.html` + `login_password.html`.
  - Repointed the only live `redirect("accounts:signup")` (VerifyOTPView not-found) → login with a neutral message.
  - Kept `SignupView/SignupVerifyView/ResendSignupOTPView` + `SignupForm` unrouted in `views.py`/`forms.py` (reversible; banner comment added).
- **Verification (owner-requested regression set):**
  - signup `/app/signup/`, `/signup/verify/`, `/signup/resend-otp/` → **404** (live + test).
  - login + password pages: **no "Create one"** link (live + test); **OTP login** end-to-end ✓; **password login** lockout tests ✓; **Google login** route `/accounts/google/login/` → 200 + button present ✓; **logout** POST ✓; **role-based access** (anonymous→redirect, role=None contained) ✓.
  - New tests: `SignupDisabledTests` (3). 649 tests green.

### Not bugs (refuted on re-verification)
[11] SignupForm DOES call `validate_password` (forms.py:188). [15] OTP attempts feedback is correct. (Plus [3][4][10][13] documented above as intentional/not-exploitable.)

---

## PHASE 03 — RBAC AUDIT · RESULT

**Scope:** URL access · sidebar visibility · view permissions · stage-panel permissions · financial-field visibility · multi-role (role+extra_roles) · super-admin bypass · privilege escalation · direct-URL bypass · hidden-action visibility · POST/action authorization · anonymous access · role=None containment. Every finding verified at 4 layers: **URL / UI-visibility / service-action / DB-impact** (a boundary holds only if all four agree).

**Method:** (1) read the full RBAC stack (`permission_service`, `access_service`, `SidebarAccessMiddleware`, all view mixins). (2) Built an **empirical URL×role access matrix** — `manage.py shell` (rolled back), one user per principal {anon, role=None, worker, listing_team, accountant, manager, super_admin} × every no-arg URL (~80), recording GET status. (3) Adversarial code workflow (6 lenses → 4 findings → per-finding verify). (4) Independent re-verification of every finding against code + matrix.

### Empirical matrix — KEY RESULTS (URL layer)
- **No anonymous bypass:** every protected URL → 302 to login. **No role=None bypass:** role=None reaches only its empty personal dashboard + self-scoped my-earnings; all management/production/admin → 302/403/404.
- **Admin surface super-only:** `user_list/add`, `skill_*`, `role_*`, `usertype_*`, `access-control`, `sidebar-access` → only super_admin 200; others 403 or middleware-redirect. **Django `/admin/` → staff/superuser only** (non-staff 302).
- **Payroll/settlement** (`payroll-overview`, `adda-settlement-list`, `advance-add`) → management only (worker/accountant/listing 403).
- **Storefront** (category/product) → listing_team only. **Financial costing** (`production:costing`) → management only (worker 403).
- **Deliberate (verified vs mixin code, NOT bugs):** worker (PRODUCTION_ROLES) can reach `adda-create`, `cloth-type/color/storage-create`, `pending-reports`, `stalled-addas`, `tracking:export-list`. `ProductionRoleMixin` docstring: *"master CRUD ke liye sufficient hai"*; `SuperAdminOnlyMixin` reserves the irreversible `roll-bulk-create` for super-admin. Factory-floor users are trusted operators by design.
- **No privilege escalation at URL layer:** user/role/skill edit forms (which expose `is_superuser`/`role`/`extra_roles`) are super-admin-only; `self_edit_blockers` prevents self-demotion/lockout.

### BUG PA-03-1 — Financial field-change values leak via roll history
- **Severity:** MEDIUM · **Module:** inventory/tracking-history · **URL:** `tracking:roll-history` · **Role:** worker, manager (non-financial) · **Device:** both
- **4-layer verification:** URL → `RollHistoryView` reachable by PRODUCTION_ROLES + object isolation ✓. **UI-visibility → FAIL:** `roll_history.html` renders `{{ e.field_name }}: {{ e.old_value }} → {{ e.new_value }}` for every event, and `roll_service` logs `supplier`/`cost_per_kg` changes → a worker/manager sees cost values the roll list/detail correctly hide (`user_can_view_financials` = FINANCIAL_ROLES). service/DB → read-only.
- **Root cause:** the financial-field view-gate (`user_can_view_financials`) was applied to the roll list/detail but not to the history timeline. `inventory/views/tracking_history.py`.
- **Fix:** filter the events queryset server-side — `if not user_can_view_financials(user): events = events.exclude(field_name__in=('supplier','cost_per_kg'))`. Values never reach the client.
- **Verification:** `FinancialHistoryLeakTests` (3): worker + manager don't see `123.45`/`cost_per_kg`; super_admin (financial) does. 652 tests green. (Note: AddaHistory checked — its COST_FROZEN metadata is NOT rendered, no leak there.)
- **Status:** ✅ FIXED

### OWNER DECISION — PA-03-WORKER-SKILL (workflow finding #1)
- **Severity:** MEDIUM · **Module:** production/worker-report · **URL:** `production:worker-report` (POST)
- **4-layer:** URL → unmanaged action URL, middleware passes. UI → form renders for the assigned user. **service-action → no SKILL gate** (`WorkerReportView` = `LoginRequiredMixin + View`; `save_draft_contributions`/`report_contributions` check task ownership/assignment, not skill). DB → `WorkerStageContribution` rows persist → flow to settlement.
- **Finding:** an **assigned-but-unskilled** worker can submit production contributions. The stage workspace requires skill+assignment (`StageViewAccessMixin`); the report surface requires assignment only — by documented intent (view comment: *"skill alone is not enough — you report only on stages you are actively assigned to"*).
- **Why not auto-fixed:** the report surface is deliberately ASSIGNMENT-gated (a manager authorizes by assigning). Adding a skill gate is a behavior change that would **block legitimately-assigned workers whose skill M2M isn't tagged** — real production-halt risk in a factory where skills may be sparsely populated. Exploitation needs a manager to deliberately assign an unskilled worker; quantities are management-reviewed before settlement (`AddaReportReviewView`). No privilege escalation / data exposure.
- **Owner decision (2026-06-14): KEEP assignment-only gating → WONTFIX (by-design).** A manager authorizes by assigning; skill-gating the report path would block legitimately-assigned workers whose skill M2M isn't tagged (production-halt risk). The future lever, if ever desired, is the *assignment* UI — `LayeringStartView` currently only checks "at least one assignee has the skill", not all. No code changed.

### Documented, not fixed (defense-in-depth gaps — service layer already blocks)
- **PA-03-2:** Layering/Cutting action POST views (`_LayeringActionBase`, `_CuttingActionBase`) lack `StageViewAccessMixin` (no fail-fast at view), but `_ensure_layering_skill`/`_ensure_cutting_skill` in the service raise PermissionDenied → **write blocked**. Boundary holds at the service layer; adding the mixin is consistency hardening (carries the same skill/assignment interaction as PA-03-WORKER-SKILL).
- **PA-03-3:** `LayeringFullCreateAndAttachView` accepts financial POST params from a worker, but the service rejects them (PermissionDenied) → no write. Same pattern: boundary holds at the service layer.

### Financial-field write-path (verified SAFE)
Cloth-roll `supplier`/`cost_per_kg`: forms **pop** the fields for non-financial users (`BulkRollForm`/`RollEditForm.__init__`), AND `update_roll_details` uses `if x is not None` (None = unchanged → no data loss) PLUS a service-level `user_can_edit_financials` re-check. Mass-assignment + data-loss both refuted — solid defense-in-depth.

---

## PHASE 04 — NAVIGATION AUDIT · RESULT

**Scope:** every sidebar item · dashboard card · action button · breadcrumb · redirect · cancel/back · success/error redirect · CTA · modal action · row-action · cross-module path. 12 requirements incl. dead links, orphans, back/forward, loops, mobile nav, hidden-action-via-direct-URL, breadcrumb-hierarchy.

**Method:** (1) **Static dead-link scan** — extracted every `{% url 'name' %}` from all 116 templates + every `reverse/reverse_lazy/redirect('name')` from all app `.py`, checked each against the 390 resolver-registered names. (2) Adversarial workflow (6 lenses: redirect-targets, cancel/back/CTA, breadcrumbs, loops/orphans, mobile-nav). (3) Browser testing (headless Chromium, super-admin) of mobile nav + live navigation.

### Static dead-link result — CLEAN
- **390** url names registered. **121** distinct template `{% url %}` names + **63** py `reverse/redirect` names checked. **Every reachable reference resolves.** Only broken refs were the **dormant signup cluster** (unrouted since Phase 02) — `signup_otp.html` (fixed, PA-04-1) + internal `reverse()` calls inside the 3 unrouted signup view classes (never execute; restore-on-re-enable). `accounts:<name>` flagged = a docstring placeholder (false positive). Post-fix re-scan: **0 broken template refs.**
- 8 variable `{% url var %}` tags (sidebar/menu) aren't statically checkable; covered by `build_menu_for`'s own `resolved_url() is None → skip` guard + the Phase-03 matrix (all sidebar URLs resolved + RBAC-correct).

### Adversarial workflow — only the 2 dormant signup links (PA-04-1); 4 other lenses CLEAN
- **Redirect targets:** no broken/wrong/looping redirects found. **Cancel/back/CTA:** clean (except dead signup). **Breadcrumbs:** none found to mismatch. **Loops:** `SidebarAccessMiddleware` exempts the dashboards (`_EXEMPT_URL_NAMES`) + re-checks the referer before redirecting to it → no redirect loop. **Orphans:** none flagged as wrongly-unlinked (detail/edit reached via row-actions = intentional).

### Browser — mobile nav + navigation (PASS)
- Mobile drawer (375px): `.sidebar` off-canvas (left:-260) + `.hamburger` toggle → opens (left:0) with `.overlay`; **26 nav items reachable**; overlay-click closes (left:-260). No horizontal overflow at **320 / 414** on `/production/`, `/production/addas/`, `/raw-materials/`, `/expense/payroll/`, `/app/users/`.
- Live: sidebar link (Addas) → `/production/addas/`; browser **back** returns correctly.

### BUG PA-04-1 — Dead `{% url %}` in dormant signup OTP template
- **Severity:** LOW (unreachable; latent) · **Module:** accounts/templates · **File:** `accounts/templates/accounts/signup_otp.html:74,107`
- **Detail:** back-link → `{% url 'accounts:signup' %}` and resend-link → `{% url 'accounts:signup_resend_otp' %}` — both routes removed in Phase 02 (PA-02-OPEN-SIGNUP). Would `NoReverseMatch` (500) **if** the template rendered, but it's unrouted + not `{% include %}`d anywhere → unreachable today.
- **Fix:** repointed both to `{% url 'accounts:login' %}` + a comment noting the re-enable restoration targets. Keeps the dormant cluster reversible without a render-time landmine.
- **Verification:** static scan re-run → 0 broken template refs; 652 tests green (incl. `test_signup_url_names_are_not_reversible`).
- **Status:** ✅ FIXED

**No other navigation issues found.** Nav integrity (links, redirects, mobile, loops, orphans) is clean.

---

## PHASE 05A — CRUD AUDIT (MASTER DATA) · RESULT

**Scope:** master-data CRUD — User, Skill, UserType (accounts) · Role (inventory) · Product, ProductPattern, Stage (production) · ClothType, ClothColor, StorageLocation (raw_materials) · Category, FeaturedProduct (storefront). 21-point checklist incl. DB persistence, validation, dup-prevention, delete guards, transaction safety, RBAC, messages, PRG, mobile 320-414. Operational CRUD (addas/rolls/settlements/payroll) → Phase 05B.

**Method:** (1) **Behavioral probes** — real C/R/U/D via Django test client as super_admin in rolled-back transactions (writes happen + verified, no dev-DB pollution); 7 surfaces × {create-PRG, list-shows, update-single-row, delete, omit-required-validation, duplicate}. (2) **Delete-in-use probes** — create master + a live reference, attempt delete. (3) Adversarial workflow (6 domain lenses → 21 candidates → per-finding verify). (4) Browser mobile (logged-in super_admin) — forms + list tables at 320/375px.

### Behavioral result — master-data CRUD is SOUND
- All 7 surfaces: **Create** redirects (PRG → refresh-safe) + writes the row; **Read** list shows it; **Update** changes only that row; **Delete** removes it; **omit-required** → form re-render, no write; **duplicate** unique field → blocked (200 form error). (Two initial "dup not blocked" flags were probe artifacts — the probe renamed the unique field before the dup check; corrected re-test confirmed `unique=True` blocks both ClothType + ClothColor.)
- **Delete-in-use is graceful:** ClothType (used by a roll), Stage (used by a WorkflowStage), Role (used by a user) → all **blocked with a redirect+message**, no 500, no cascade-wipe, referencing objects intact (FK PROTECT + view guards).
- **Mobile (320/375px):** no page overflow on any create/edit form or list; tables fit or scroll within their responsive wrapper; console clean.

### Fixed (5) — all view-only, no migration, regression-tested
- **PA-05A-1 (HIGH)** `SkillDeleteView` in-use guard (Skill→User + Skill→SidebarItemRule M2M would cascade silently). `accounts/views.py`. Tests: `SkillDeleteGuardTests` (3).
- **PA-05A-2 (MEDIUM)** `RoleDeleteView` now guards `extra_users` (extra_roles M2M) too. `inventory/views/role_views.py`. Tests: `RoleDeleteGuardTests` (3).
- **PA-05A-3 (LOW)** Role create/update success messages.
- **PA-05A-4 (MEDIUM)** `ProductPatternsEditView` `pieces_count` safe-parse (was `int()` → 500 on tampered input). `production/views/pattern_views.py`. Tests: `PatternPiecesCountSafeParseTests` (2).
- **PA-05A-5 (MEDIUM)** `UserCreateView` catches IntegrityError on concurrent same-email → field error instead of 500.

### Refuted (verified NOT bugs)
- Skill/UserType edit-dup → Django `ModelForm.validate_unique` handles it (probe: Role/Stage edit work). Role.clean_code → only guards system-role code immutability; uniqueness via validate_unique. Master-name dup → blocked at form layer (200, not 500); masters hard-delete so no archived-row collision. Storefront `ProductDeleteView`/`CategoryDeleteView` → DO have `ListingTeamMixin` (no RBAC hole). Product create/update "service bypass" → that IS the correct service-owns-writes pattern (CLAUDE rule 4).

### Documented for follow-up (real, but need model+migration; storefront not live)
PA-05A-SF1 Category.name not unique · SF2 FeaturedProduct price/original_price no MinValueValidator · SF3 image fields no size/type cap · SF4 orphaned image files on update. All admin/listing-team-only entry; 0 bad data in dev. Recommended as one small storefront-validation migration PR — not bundled into the surgical 05A view-fix commit.

---

## PHASE 05B — CRUD AUDIT (OPERATIONAL) · RESULT

**Scope:** money / production-qty / inventory / settlement write flows — Adda lifecycle, worker assignment, contribution draft-vs-submit, settlement create/finalize/reverse, advance, payroll, roll ops, reopen workflows. For every such write: DB before/after, history/audit, rollback, permissions, refresh-safety, concurrency, mobile.

**Method:** adversarial workflow (6 flow lenses → 38 candidates → per-finding verify) + code-level verification of every "real" candidate + live mobile worker-report test. NOTE: the settlement/allocation/cost/reopen MATH is locked + heavily tested (Foundation S1–S5) — this phase audited the CRUD SURFACE, not the money math.

### What's already robust (verified, not re-derived)
- **Money/qty services are guarded:** 41 `@transaction.atomic` / `select_for_update` / advisory-lock callsites across the money/qty services (settlement service alone: 15 locks + 4 atomic; worker_task: 5 + 5). Dedicated tests: `test_reopen_voids_pay`, `test_concurrency`, `test_s4_reopen_guard`, `test_v2_3_guards`, `test_s5_recon_block`, `test_worker_report_view`.
- **Settlement actions** (finalize/reverse/supersede/discard) are `_ManagementOnly`-gated, service-locked, atomic, and PRG (redirect after POST).
- **Worker-report double-submit** is guarded — `report_contributions` refuses on COMPLETED/VERIFIED status inside `@transaction.atomic` (a 2nd submit can't duplicate/re-complete); draft is replace-semantics. Tested.
- **Allocation over-allocation** is refused always-on (S4); `LEDGER_CREDIT_AT_ALLOCATION=False` → no money booked at allocation (settlement is the money boundary).

### Mobile — worker reporting (phone-first, HIGHEST priority): PASS
Logged in as the assigned worker, opened `production:worker-report` (live task on `3-PATTI-002`/layering): no horizontal overflow at **320/375/414px**, console clean, hero + numbered panels + cream quantity input + "+ Add another line" + sticky "Submit & Complete"/"Save draft". Exemplary phone-first data entry. Screenshot `/tmp/audit_worker_report_375.png`. Assignment-gating correctly admits the legit worker.

### BUG PA-05B-1 — settlement finalize crashes on tampered input
- **Severity:** MEDIUM · **Module:** expense/settlement · **URL:** `expense:adda-settlement-detail` POST `action=finalize` · **Role:** management · **Device:** both
- **Repro:** POST finalize with `var_abc_packed=5` (or `recover_abc=100`). `_parse_finalize_inputs` (expense/views.py) did `int(wid)`/`int(advance_id)` **outside** the try → unhandled ValueError → **500**. (The variance branch wrapped `int(raw)` but not `int(wid)`; recovery wrapped `Decimal(raw)` but not `int(advance_id)`.)
- **Writes:** none (crash is in form parsing, before any service call/DB write).
- **Fix:** moved both `int()` conversions inside the try → ValidationError (the view's outer handler shows a message + redirects). `expense/views.py`.
- **Verification:** `FinalizeInputParseTests` (3 — malformed var, malformed recover, valid parse). 663 green.
- **Status:** ✅ FIXED

### BUG PA-05B-2 — cutting breakup bulk save is not all-or-nothing
- **Severity:** LOW · **Module:** production/cutting · **URL:** `production:cutting-breakup-save` POST · **Role:** cutting/management · **Device:** both
- **Repro:** POST a multi-row breakup where row 1 is valid and row 2 is incomplete/invalid. The handler upserted row 1, then hit row 2, `messages.error` + `return` — leaving row 1 persisted (partial write).
- **Writes:** production-qty (breakup rows). Draft-stage, recoverable (upsert + retry), caught at cutting-complete — hence LOW.
- **Fix:** wrapped the row loop in `transaction.atomic()` and RAISE on any bad row (instead of mid-loop `return`) so the whole batch rolls back → all-or-nothing. `production/views/stage_views.py`.
- **Verification:** mechanically all-or-nothing (atomic + raise); happy path covered by existing cutting-workflow tests (regression green, 663); dedicated partial-failure integration test deferred (heavy cutting scaffold) — verified by code inspection.
- **Status:** ✅ FIXED

### Documented, not fixed (verified not-a-bug / foundation-covered / missing-feature / LOW race)
- **PA-05B-ADV** advance "duplicate on refresh / no dedup / no reverse": PRG present; duplicate advances are legitimate (dedup would be wrong); advance-reverse is a missing feature (recovery is at settlement) — not built (no-feature rule).
- **PA-05B-RACE** `report_contributions`/`save_draft`/`assign_roll_to_adda` lack `select_for_update` → theoretical concurrent-double-submit race on single-actor surfaces; mitigated by `@atomic` + status guards. Not touching locked foundation services for a theoretical race.
- **PA-05B-FND** allocation CSRF (global middleware) / over-allocation (refused always-on) / double-credit (`LEDGER_CREDIT_AT_ALLOCATION=False`) / AJAX `204` (correct for auto-save) / reopen view-authz (service guards) — all already covered.

**UI_COMPONENTS.md:** no change — both fixes are backend (input parsing, transaction wrapping); no reusable UI rule emerged. The worker-report mobile pattern is exemplary but is existing behavior already covered by the form-shell pattern.

---

## PHASE 06 — MASTER DATA: INTEGRITY / CONFIG / SEED / DRIFT · RESULT

**Boundary (approved):** NOT a re-audit of 05A CRUD or 05B operational flows. Five sub-areas: (a) DB integrity at rest, (b) seed correctness, (c) per-product flow config, (d) WorkerProfile master data, (e) **Configuration Drift Audit** (owner-added) — DB-valid-but-architecture-violating configs. Supplier/Customer = no models (out of scope).

**Method:** adversarial workflow (5 lenses → 16 candidates → verify) + my own live DB drift probes (dumped every WorkflowStage vs architecture invariants) + constraint-enforcement probes + ran `reconcile_denorm`/`reconcile_pay`.

### Verified SOUND
- **Constraints enforced:** CheckConstraint blocks negative `cost_rate` (IntegrityError); FK PROTECT holds (05A delete-in-use probes). **`reconcile_denorm`: ✓ clean** (denormalized counters match source).
- **No config drift on REAL products:** every real `WorkflowStage` satisfies the invariants — registered handler, valid `allocation_dimensions`, pre-piece stages (layering/cutting_pattern/barcode_generation)=NONE, valid/empty `cost_method`, `cost_rate ≥ 0`, unique (product, order).
- **`cost_method=''` on layering = INTENTIONAL** (not drift): migration 0026 sets it; rows are `credits=False`, `cost_billed_at=cutting` (layering cost billed at cutting); `cost_service` handles empty method (`if not method or rate is None`). Refuted.

### Fixed (2) — WorkerProfile master-data validation (form-level, no migration)
- **PA-06-1 (HIGH):** `opening_advance` (seeds Advance Outstanding = money) accepted negative → corrupts recovery math. Form `min_value=0`. Tests: `WorkerProfileFormValidationTests`.
- **PA-06-2 (MEDIUM):** bank IFSC/account/cross-field unvalidated → malformed payout details savable. Blank-tolerant IFSC regex (normalized upper), numeric account (9–18), "account ⇒ require IFSC + name" clean. (Updated 1 existing test that used invalid placeholder bank data.)

### Configuration Drift Audit (e) — findings
- **Over-allocation `3-PATTI-001`** (120 allocated vs 105 produced): real drift, but KNOWN pre-foundation dev data; `reconcile_pay` correctly flags it; S4/S5 foundation prevents new ones (enforcement flags off pending soak). **Not mutated** (voiding it would hide bug evidence). Remediation path documented.
- **Stray test data:** 3 test products with handler-less stages (dev-DB cruft, no production impact) → recommend cleanup.
- **Flow editor** allows configuring a handler-less stage → graceful 403 at report-time (no crash). Guard proposed but DEFERRED (TM-1 manual-stage tension).
- **6 sidebar items unseeded** → functionally-correct in-code fallback; only 4/6 fit the role-rule model → governance nicety, documented.

### UI_COMPONENTS.md
No change — both fixes are backend form validation; no reusable UI rule emerged.

---

## PHASE 07 — STAGE ENGINE AUDIT · RESULT

**Scope:** the 4-stage production workflow end-to-end — **layering · cutting_pattern · cutting · barcode_generation** — across the full lifecycle (create · assign · start · report · draft-save · complete · reopen · review · settlement-impact) and the cross-cutting concerns (quantity integrity · allocation interaction · stage transitions / `advance_to_next_stage` · rollback / reopen guards · race conditions · tampered input · production-truth good/alter/missing + `AddaStageRoleRate` + rate-freeze behavior).

**Method:** (1) deep read of the whole stage engine — `stages/{layering,cutting_pattern,cutting,barcode_generation}/{handler,service}.py`, `stages/base/{handler,registry}.py`, `services/{_shared,worker_task_service,pool_service,cost_service,stage_rate_service,adda_service}.py`, and every stage view (`stage_views.py`, `pattern_stage_views.py`, `barcode_gen_views.py`, `worker_report_views.py`) + forms. (2) A 7-finder adversarial workflow (per-stage + cross-cutting lenses → per-finding adversarial verify) was launched but **all 7 finders died on a session/API limit** (0 findings returned — not a clean result), so the audit was completed **in the main thread** against the already-loaded code. (3) Every candidate verified against the actual code + the existing `production/tests/` suite (≈400 production tests) before flag/refute.

### What's robust (verified, not re-derived)
- **Money / transitions / reopen are foundation-locked + tested.** `reopen_stage_record` (the shared Template Method) enforces, in order: settled-stage refuse → `_downstream_consumer_guard` (transitive, names the furthest blocker) → stage `guard` → `teardown` → clear frozen cost → re-float rate snapshot → void era-A allocations → clear pool → reset Adda → log `STAGE_REOPENED`. All four stages wire it consistently. `advance_to_next_stage` freezes cost before advancing, handles last-stage (`current_stage=None`, COMPLETED), and runs the PAY-2 worker-credit gate before mutating.
- **Stage completes are race-safe** — each `complete_*` does `select_for_update` on the `AddaStageRecord` + re-checks `completed_at` (WF-4). `complete_worker_task` locks the task row + re-reads DB status (P0-5).
- **Piece-count integrity holds** — `add_pieces_to_bundle` locks the breakup row + refuses over-take; delete/void recompute `consumed_count`; allocated bundle items are PROTECT-guarded against delete (graceful `ValidationError`, no `ProtectedError` 500). Barcode generate is one-shot (guarded), and complete validates `batch_total == breakdown_total == denorm`.
- **View input parsing is hardened** — every `int()` on POST in the stage views (`pattern_stage_views`, cutting bundle/breakup/allocate views, layering layer-save) is wrapped → graceful message (prior-phase discipline). Attach/edit-roll paths use Django Forms (`cleaned_data` = typed). `record_remaining_cloth` / `save_layering_breakup` have no raw-POST caller.

### BUG PA-07-1 — worker-report non-numeric quantity → 500
- **Severity:** MEDIUM · **Module:** production/worker-report · **URL:** `production:worker-report` POST · **Role:** assigned worker · **Device:** both (mobile-relevant)
- **Reproduction:** as the assigned worker, POST a contribution line with `line-0-reported_quantity=abc` (or a locale-comma `1,5`, or `1.2.3`). `WorkerReportView._parse_lines` int-guards `choice` fields but stores the **quantity field as a raw string** (no numeric check). `save_draft_contributions → report_contributions` does `Decimal(str(line['reported_quantity']))` → `decimal.InvalidOperation`. The view's `except ValidationError` does NOT catch it (`InvalidOperation` ⊄ `ValidationError`) → **500**.
- **Why mobile-real (not pure tamper):** the input is `type=number inputmode=decimal`, but a phone keyboard / locale that emits a comma decimal (`1,5`) submits a value `Decimal()` rejects.
- **Root cause:** untrusted string reaches `Decimal()` in the single-writer service, whose only numeric guard was `qty <= 0`. `worker_task_service.report_contributions`.
- **Fix:** wrap the `Decimal(...)` in `try/except InvalidOperation → raise ValidationError("Quantity must be a number.")`. Imported `InvalidOperation`. `config/production/services/worker_task_service.py`.
- **Verification:** `test_report_non_numeric_qty_rejected_gracefully` (`'abc'`,`'1,5'`,`'1.2.3'` → `ValidationError`). Note transactional safety: `save_draft_contributions` is `@transaction.atomic`, so the delete-then-recreate rolls back on the bad line (no draft loss). 673 green.
- **Status:** ✅ FIXED

### BUG PA-07-2 — review verified-quantity non-numeric → 500
- **Severity:** MEDIUM · **Module:** production/adda-report-review · **URL:** `production:adda-report-review` POST · **Role:** management · **Device:** both
- **Reproduction:** on the pre-settlement quantity review, POST a tampered `verified_<pk>=abc`. `AddaReportReviewView` passes the raw string to `set_verified_quantity`, which does `Decimal(str(quantity))` → `InvalidOperation`. The view catches only `(ValidationError, PermissionDenied)` → **500**.
- **Root cause:** identical to PA-07-1 (untrusted string → `Decimal()` in the writer). `worker_task_service.set_verified_quantity`.
- **Fix:** same `try/except InvalidOperation → ValidationError("Verified quantity must be a number.")`. `config/production/services/worker_task_service.py`.
- **Verification:** `test_verify_non_numeric_rejected_gracefully` (`test_c1_hardening.PreDeploySafetyTests`). 673 green.
- **Status:** ✅ FIXED

### Refuted on re-verification
- **PA-07-STARTED-AT:** Layering auto-duration `now − adda.started_at` — `Adda.started_at` is `auto_now_add=True` (never None). No crash.
- **PA-07-BREAKUP-COUNT:** `upsert_breakup_row` can drop a breakup `count` below its `consumed_count` → negative `available`, but the breakup is the *informational plan* (bundles drive completion/settlement) and negative `available` only blocks further takes — no crash, no money/qty error. Not fixed (no-speculative rule).
- **Foundation behaviors verified, not re-flagged:** over-allocation refused always-on (S4 `pool_service`); `LEDGER_CREDIT_AT_ALLOCATION=False` (no money at allocation); single-actor `select_for_update` races (documented PA-05B-RACE); handler-less stage = graceful 403 (PA-06-FLOW); assignment-not-skill report gating (PA-03-WORKER-SKILL); good/alter/missing dual-write + `AddaStageRoleRate` rate-freeze (S1/S3).

### Production-truth verification (good/alter/missing · rate freeze · reopen · allocation · settlement)
- `report_contributions` dual-writes `good_quantity = reported_quantity` (alter/missing default 0); `complete_worker_task` freezes `expected_earning = good × frozen rate` from the `AddaStageRoleRate` snapshot (live fallback only for pre-S2 records, warned); grouped-member→0 structural guard holds. Reopen voids era-A allocations + re-floats the rate; settled stages refuse reopen. All consistent with the locked foundation — verified, not redesigned.

### Mobile (highest priority)
Both fixes are **backend-only** (`worker_task_service`) — **no template / CSS / markup change**, so the rendered stage surfaces are byte-identical and carry no new mobile risk. The touched surface (worker-report) was browser-verified PASS at 320/375/414px in Phase 05B (phone-first hero + numbered panels + cream quantity input + sticky submit; screenshot on file). No fresh mobile regression introduced.

### UI_COMPONENTS.md
No change — both fixes are backend input validation in the writer service; no reusable UI rule emerged.

---

## PHASE 08 — RAW MATERIAL AUDIT · RESULT

**Scope:** the cloth-roll lifecycle in the `raw_materials` app — **inbound** (bulk intake), **stock** edit, Adda **assignment**, leftover **consumption** ("adjustments" = the width/weight/location stock edits; there is no separate stock-count surface). Models: ClothType / ClothColor / StorageLocation (master, audited in 05A — not re-audited) + ClothRoll. Files: `services/roll_service.py`, `views/{roll,assign,dashboard,master}_views.py`, `forms/roll_forms.py`, `models.py`.

**Method:** main-thread deep read of the whole app (5 core files) + a live shell repro of the suspected 500s (negative numeric → DB CheckConstraint `IntegrityError`) + tmp-row cleanup verified. **Sub-agents were NOT re-run** — still session-limited, and a 5-file app gains no coverage over a complete manual read (per the Phase-07 finder-honesty rule). RBAC + master-data CRUD already covered in Phases 03/05A — not re-audited.

### What's robust (verified)
- **Money/measure write paths are service-owned + atomic.** `bulk_create_rolls` (financial gate + per-row qty `int()` guarded in `BulkRollForm.clean`), `update_roll_details` (field-level diff + history + `refresh_from_db` to survive ModelForm instance mutation + USED-roll block), `consume_leftover` (`select_for_update` + re-check + same-Adda guard, C-1/ADR-0009). Roll FKs PROTECT; CheckConstraints (`cost_per_kg/weight/remaining_* >= 0`) enforced at the DB.
- **Filter parsing is guarded** — `RollListView` chip lookups `try/except (DoesNotExist, ValueError)`; dashboard `color_id` gated by `.isdigit()`; `_parse_date` `try/except ValueError → None`. No GET-param 500s.
- **`assign_roll_to_adda`** guards roll status + Adda in-progress + Layering-stage; the missing `select_for_update` is the already-documented single-actor race (PA-05B-RACE), not re-flagged.

### BUG PA-08-1 — bulk intake: negative cost_per_kg → 500
- **Severity:** MEDIUM · **Module:** raw_materials/intake · **URL:** `raw_materials:roll-bulk-create` POST · **Role:** super_admin (financial) · **Device:** both
- **Reproduction:** submit a valid color/qty breakup with `cost_per_kg = -2`. `BulkRollForm` is a plain `forms.Form` (NOT a ModelForm) so it runs no model-constraint validation — the negative passes `is_valid()`. `bulk_create_rolls` builds `ClothRoll(cost_per_kg=-2)` → `bulk_create` → DB CheckConstraint `rawmat_clothroll_costperkg_nonneg` → **IntegrityError**, which `RollBulkCreateView.form_valid` does not catch (`except (ValidationError, PermissionError)`) → 500.
- **Verification of repro:** shell — `bulk_create_rolls(..., cost_per_kg=Decimal('-2'))` raised `IntegrityError: ... violates check constraint "rawmat_clothroll_costperkg_nonneg"`. (tmp master rows cleaned up.)
- **Root cause:** the non-negative rule lived only at the DB; the plain form had no `min_value`. `raw_materials/forms/roll_forms.py` `BulkRollForm.cost_per_kg`.
- **Fix:** `min_value=0` on the field (+ `min='0'` on the widget) → graceful field error before any INSERT. Mirrors PA-06-1.
- **Status:** ✅ FIXED · test `RollFormNonNegativeTests.test_bulk_form_rejects_negative_cost` (+ positive control).

### BUG PA-08-2 — roll→Adda assign: negative weight_kg → 500
- **Severity:** MEDIUM · **Module:** raw_materials/assign · **URL:** `raw_materials:roll-assign` POST · **Role:** production (worker/manager) · **Device:** both (mobile floor surface — the number input had no `min`)
- **Reproduction:** on the assign form, enter `weight_kg = -5`. `AssignRollForm` (plain forms.Form) returns `is_valid()=True` (shell-verified). `assign_roll_to_adda` saves `weight_kg=-5` → CheckConstraint `rawmat_clothroll_weight_nonneg` → IntegrityError, not caught by `RollAssignView.form_valid` (`except (Adda.DoesNotExist, ValidationError)`) → 500.
- **Root cause + fix:** same as PA-08-1 — `min_value=0` on `AssignRollForm.weight_kg`.
- **Status:** ✅ FIXED · test `RollFormNonNegativeTests.test_assign_form_rejects_negative_weight` (+ positive control).

### Refuted / documented
- **PA-08-EDITFORM (refuted):** `RollEditForm` is a **ModelForm** → Django 5 validates the CheckConstraint in `full_clean()`, so a negative weight/cost makes `is_valid()` False (graceful `__all__` error, no service call, no 500). Shell-confirmed. (The message leaks the constraint name — cosmetic, not fixed.)
- **PA-08-PERM (doc, latent):** `RollBulkCreateView` catches `PermissionError` (builtin) not `PermissionDenied` (Django) — but the view is super-admin-only so the service's financial gate never raises here. Unreachable → not fixed.
- **Sequence gaps on validation failure:** `_next_roll_id()` advances the Postgres sequence before the late `is_active` checks; a rejected intake leaves CR-ID gaps. Inherent to Postgres sequences (rollback never reclaims `nextval`) — cosmetic, not a bug.

### Mobile (highest priority)
Both fixes are **form-validation-only** (one kwarg + a widget `min` attr) — no template/layout change. The assign surface (PA-08-2) is a floor data-entry form; adding `min='0'` to its number input is a small mobile-correctness improvement (prevents an invalid negative at the keyboard). No layout/overflow impact.

### UI_COMPONENTS.md
No change — backend form-field validation; no reusable visual/layout rule emerged. (The `min='0'` on numeric inputs is a sensible convention but does not rise to a documented component rule.)

---

## PHASE 09 — INVENTORY AUDIT · RESULT

**Scope (quantity-truth, not CRUD):** the `inventory` Django app is RBAC-only (no stock model), so "inventory" = the STOCK QUANTITY-TRUTH subsystem across raw_materials + production + tracking. Audited stock conservation, movement correctness, negative-stock prevention, quantity drift, denormalized counters, reconciliation, orphaned records, concurrency (double-consume / double-assign / lost-update / lock coverage), and reopen/reversal effects — with DB-truth ⟷ service-truth ⟷ UI-truth consistency as the bar.

**Method:** a 6-finder quantity-conservation Workflow (roll-leftover · breakup-bundle · breakdown-barcode · S4 pool · reopen-reversal · concurrency-reconcile) + adversarial per-finding verify. **The finders ran and surfaced 10 candidates, but 9 of 10 VERIFIERS died on a session/API limit** (only the `consume_leftover` verifier completed). Per the honesty rule, "0 confirmed" was NOT treated as clean — **every finder candidate was main-thread-verified against the actual code + tests.** Two were also independently found main-thread before the workflow returned.

### What's robust (verified)
- **Conservation chain holds:** breakup(plan) → bundle items(actual) → `_materialize_breakdown` (Σ items by size,color) → `pieces_cut`(=Σ items) → BarcodeBatch; `complete_barcode_generation` enforces `batch_total == breakdown_total == total_barcodes`. Barcode count == pieces actually bundled.
- **Negative/over:** all counts are `PositiveIntegerField` (DB rejects negative); `available_count = max(count−consumed,0)` clamps; `add_pieces_to_bundle` locks the breakup + refuses over-take; CheckConstraints on roll cost/weight/remaining + BarcodeBatch `total_pieces>0` / `total_pieces == end−start+1`.
- **Double-consume guarded:** leftover `consume_leftover` = `select_for_update` + `is_consumed` recheck + same-Adda guard; allocated bundle items / settled lines PROTECT against delete.
- **Denorm self-heals:** `_recompute_bundle_total` / `_recompute_breakup_consumed` / `_sync_roll_leftover` recompute-from-truth on every write.
- **Reopen resets stock:** cutting reopen deletes breakdown + BarcodeBatch (incl. inline) + clears pool; barcode reopen deletes batches + resets `total_barcodes`/`generated_at`; the transitive downstream-consumer guard blocks reopening a stage whose output is consumed.

### BUG PA-09-1 — legacy cutting completion double-creates the stage record → 500
- **Severity:** HIGH · **Module:** production/cutting · **URL:** `production:cutting-complete` POST · **Role:** management · **Device:** both
- **Reproduction:** (1) start cutting (or add any bundle/breakup, or complete-then-reopen) so an `AddaStageRecord(adda, cutting)` exists. (2) POST the legacy cutting form (`/production/addas/<code>/cutting/`). `complete_cutting_legacy` runs `AddaStageRecord.objects.create(adda=, workflow_stage=)` **unconditionally**, but `(adda, workflow_stage)` is `unique_together` → **IntegrityError**, which `CuttingCompleteView` (`except (ValidationError, PermissionDenied)`) doesn't catch → 500. Cleanest path: legacy-complete → `reopen_cutting` (keeps the SR) → legacy-complete again.
- **Root cause:** the single-form path assumes a fresh stage; it never checks for an existing SR. `config/production/stages/cutting/service.py` `complete_cutting_legacy`.
- **Fix:** refuse gracefully (`ValidationError`) if an SR already exists, directing to the cutting workspace (which handles an existing SR). Pure-legacy first-completion (no SR) is unchanged.
- **Verification:** `StartCuttingTests.test_legacy_complete_after_start_refused_gracefully` (asserts `ValidationError`, exactly one SR, not completed). 679 green.
- **Status:** ✅ FIXED

### BUG PA-09-2 — mixed manual + breakup bundle-add collides → 500
- **Severity:** MEDIUM · **Module:** production/cutting · **URL:** `production:cutting-bundle-add-pieces` POST · **Role:** cutting/management · **Device:** both
- **Reproduction:** in a bundle, add a line manually for Front/Red (`add_item_to_bundle` → `source_breakup=NULL`), then consume the Front/Red breakup into the same bundle (`add_pieces_to_bundle`). Its `get_or_create(bundle,pattern,color,source_breakup=breakup)` can't match the manual row (different `source_breakup`), tries to CREATE, and trips `unique_together (bundle,pattern,color)` → **IntegrityError** (uncaught by `CuttingBundleAddPiecesView`) → 500.
- **Root cause:** the unique key and the get_or_create key differ. `config/production/stages/cutting/service.py` `add_pieces_to_bundle`.
- **Fix:** before create, detect a conflicting line for `(bundle,pattern,color)` not sourced from this breakup → graceful `ValidationError` ("edit that line instead"). Consumes nothing on refusal (atomic).
- **Verification:** `AddPiecesToBundleTests.test_manual_item_then_breakup_consume_refused_gracefully`. 679 green.
- **Status:** ✅ FIXED

### Refuted / documented (main-thread verified — verifiers had died)
- **PA-09-CONSUME-LEFTOVER (refuted, benign):** `consume_leftover` leaves `ClothRoll.remaining_*` denorm stale, but that field is a pure read-cache (no costing/settlement/barcode/pool reader); `is_consumed` (correct, locked) governs double-consume; availability dashboards Sum the primary leftover rows. Display drift only.
- **PA-09-RECONCILE-SRC (refuted, by-design):** `reconcile_denorm` checks `pieces_cut` against `Σ breakup.count` — the documented + `test_reconcile_denorm`-codified contract (breakup is the source-of-truth for pieces_cut). Changing it to Σ items = redesign (forbidden). In correct usage they're equal (Phase-06 clean on real data).
- **PA-09-RECONCILE-COV (doc, enhancement):** reconcile covers only 2 of the denorm counters; the other three self-heal on write and don't feed barcode/settlement truth. Adding checks = feature (not built).
- **manual-no-bound (refuted):** `add_item_to_bundle` overwriting a breakup-sourced count can push `consumed_count>count`, but breakup is the informational plan (PA-07-BREAKUP) and the manual count IS the actual barcoded truth — no downstream corruption.
- **PA-09-TOTALPIECES-RACE (doc):** `_recompute_*` re-sum without locking the bundle → a two-manager concurrent add to the same bundle could persist a stale `total_pieces`; display-only (not in the barcode/breakdown/pieces_cut truth path), self-heals next op. PA-05B-RACE class.

### Mobile (highest priority)
Both fixes are **backend service guards** (turn an `IntegrityError` 500 into a graceful `ValidationError` the existing views already surface as a message) — no template/markup/CSS change, so no mobile-render delta. The cutting workspace + legacy form render unchanged.

### UI_COMPONENTS.md
No change — backend quantity-truth guards; no reusable visual/layout rule emerged.

---

## PHASE 10 — PRODUCTION AUDIT · RESULT

**Scope (production-truth, not CRUD):** Adda lifecycle · worker assignment · `WorkerStageTask`/`WorkerStageContribution` lifecycle · draft→complete · reopen→re-complete · quantity truth · good/alter/missing · settlement_quantity derivation · `AddaStageRoleRate` · `expected_rate` freeze · `expected_earning` · replay/refresh · stale-after-reopen · duplicate completion · locks/atomicity · audit/history. DB-truth ⟷ service-truth ⟷ UI-truth consistency as the bar.

**Method:** I deep-read the full production-truth core (worker_task_service, stage_rate_service, cost_service, adda_service, _shared reopen, credit.py, the settlement resolver + finalize) then ran a **FINDER-ONLY** Workflow (6 finders, verify stage deliberately omitted — the prior two phases' verifiers died on the session limit and burned ~1M tokens; finders survive). **All 6 finders survived → 12 candidates**, and **every candidate was main-thread-verified** against the code + the dev DB (honesty rule: no candidate accepted or dismissed on agent say-so).

### BUG PA-10-1 — payable-stage completion blocked in the documented-default config (CRITICAL)
- **Module:** production/credit (PAY-2) · **Trigger:** any Adda, cutting stage, default `LEDGER_CREDIT_AT_ALLOCATION=False` · **Role:** management · **Device:** both
- **Reproduction:** all 5 real cutting `WorkflowStage`s are `credits_workers=True` + self-paid (migration 0030). Start cutting + report work + build bundles, then `CuttingWorkspaceCompleteView` → `complete_cutting_from_bundles` → `advance_to_next_stage(enforce_worker_credit=True)` → `ensure_worker_credit`. With the flag off, `allocate_stage_work` refuses (so no era-A SWA) and the settlement SWA is only created at finalize (AFTER completion) → `ensure_worker_credit` finds zero non-voided SWA → `ValidationError` → **the Adda can never advance past cutting via the workspace path in the default config.** Dev-DB evidence: 0 cutting completions since the 2026-06-11 V2-3 flip (only 3-PATTI-001, completed pre-flip when allocation worked).
- **Root cause:** `ensure_worker_credit` read the transitional `StageWorkAssignment`; V2-3 moved crediting to settlement but never re-pointed this guard (its own comment, credit.py:33, flagged the SWA-read as needing the cutover).
- **Fix:** flag-aware credit source — flag ON (era-A rollback lever) keeps the SWA check + message verbatim; flag OFF (default) requires a COMPLETED/VERIFIED `WorkerStageContribution` (the exact `_settleable_lines` predicate settlement pays). Same gate intent; truth-source moved from the transitional SWA to production truth. Verified cutting credits via worker self-report (3-PATTI-001 has 3 contributions; resolver is stage-agnostic).
- **Verification:** new `StageCreditSettlementFirstTest` (4 tests, default flag): blocked without a completed contribution, passes with one, advance both ways. `test_stage_credit` (flag-on) unchanged + green. **Golden ₹225 settlement chain byte-identical.** 685 green.
- **Status:** ✅ FIXED

### BUG PA-10-2 — roster edit cancels a COMPLETED worker task, orphaning payable truth (HIGH)
- **Module:** production/worker_task_service · **URL:** `production:layering-start` / `cutting` start POST · **Role:** management · **Device:** both
- **Reproduction:** assign [A,B]; B reports + completes (B's `WorkerStageTask`=COMPLETED, contribution frozen) — `complete_worker_task` never stamps `stage_record.completed_at`, so the STAGE stays OPEN. Manager re-submits the roster as [A] (drop B). `set_stage_workers` builds `active` excluding only CANCELLED (so B's COMPLETED task is in it) and cancels it. B's frozen `WorkerStageContribution` is now on a CANCELLED task → excluded from settlement (`_settleable_lines` filters completed/verified) + the review screen → B silently unpaid, production truth stranded.
- **Root cause:** the cancel loop had no guard for COMPLETED/VERIFIED tasks (only `resolve_stage_tasks_on_complete` protected them, via `target`).
- **Fix:** the cancel loop now skips COMPLETED/VERIFIED tasks (never cancel frozen truth). `resolve_stage_tasks_on_complete` already passes them in `target` → behaviour there unchanged.
- **Verification:** `test_set_never_cancels_a_completed_task_on_roster_edit` (completed task survives a roster drop + contribution intact; an ASSIGNED worker dropped in the same call is still cancelled). 685 green.
- **Status:** ✅ FIXED

### BUG PA-10-3 — two SR-creation sites skipped the rate-snapshot contract (LOW)
- **Module:** production/cutting + cutting_pattern · **Reproduction:** `_get_or_create_cutting_stage_record` / `get_or_create_pattern_stage_record` created an `AddaStageRecord` without `ensure_stage_role_rates` (every other site calls it — Contract 2). The cutting `AddaStageRoleRate` was then late-created at first worker completion with a spurious `snapshot_missing_at_complete` WARNING (codebase: "on a fresh DB any warning = a bug") — which PA-10-1 makes universal for cutting.
- **Fix:** snapshot at SR creation (idempotent; callers atomic). **Verification:** `test_start_snapshots_stage_role_rates`. 685 green.
- **Status:** ✅ FIXED

### Verified-but-not-fixed (main-thread verified — verify stage was omitted by design)
- **PA-10-REOPEN-RATE (refuted, by-design):** 3 finders flagged "reopen refloats the rate but settlement pays the stale `c.expected_rate`." Settlement pays each contribution at ITS frozen rate (price-at-time-of-completion); the dedicated re-pricing tool is `rerate_stage_role` (recalcs completed-unsettled + audits). `refloat` targets re-completions; the common reopen (no rate change) is correct. reopen+config-rate-change+re-settle is a footgun → use `rerate`. Not changing reopen (locked foundation).
- **PA-10-VERIFY-AUDIT (doc, by-design):** `set_verified_quantity` has no append-only audit (unlike `rerate`). Owner model: `reported` immutable, `verified` = latest correction. Audit trail = future enhancement.
- **PA-10-GROUPED-PREVIEW (Phase 11):** grouped→₹0 applied at finalize but not at the settlement preview/queue → preview overstates a grouped-after-complete member (money correct). Settlement-preview surface → Phase 11.
- **PA-10-VERIFY-RACE (Phase 11):** finalize locks `AddaStageRecord` but not the `WorkerStageContribution` rows where `verified_quantity` lives → a two-actor verified-edit-vs-finalize window. Recoverable; settlement-finalize locking → Phase 11.
- **PA-10-ROLE-NONE (refuted, benign):** a role=None skilled worker freezes at the base rate — sensible (no role = no override); assignment is skill-gated by design.

### Mobile (highest priority)
All three fixes are **backend service guards** (turn a blocked/orphaning/warning path into correct behaviour) — no template/markup/CSS change, no mobile-render delta.

### UI_COMPONENTS.md
No change — backend production-truth guards; no reusable visual/layout rule emerged.

---

## PHASE 11 — SETTLEMENT AUDIT · RESULT

**Scope:** the money boundary — `finalize_adda_settlement` · `reverse_adda_settlement` · supersede chains · `AddaSettlement`/`AddaSettlementItem` · `StageWorkAssignment` earning lines · `WorkerLedgerEntry` creation · `SettlementReconciliationEvidence` · `rerate` interaction · super-admin override · settlement locks (5374) · `settlement_quantity` derivation · double-payment prevention · replay/idempotency · race conditions · reversal recovery · S5 enforcement.

**Method:** deep-read the whole settlement stack (adda_settlement_service, settlement_resolver, ledger_service, reconciliation_service, payroll_service, expense/views.py) + a **FINDER-ONLY** Workflow (6 finders, verify stage omitted — the prior pattern). **All 6 finders survived → 10 candidates**, each **main-thread-verified** against code + tests. Most candidates were clean-area confirmations (the money-write, reverse/supersede, ledger idempotency, qty-parity are sound). Three real defects fixed.

### What's verified SOUND (not re-derived)
- **finalize money-write:** per-line `amount = settlement_quantity(verified-else-good) × effective_pay_rate(grouped→0)`, ROUND_HALF_UP; era-A (non-settlement SWA) + era-B (settlement_line) exclusion prevents double-credit across drafts/supersede chains; recovery validated ≤ `advance_remaining` under the WorkerAdvance row lock; tie-out `Σ items == expected_total`; the S5 over-allocation block raises inside the atomic → full rollback.
- **reverse/supersede:** every stage-earning credit compensated, every recovery PSI compensated + `reversed_at` stamped, every SWA soft-voided (re-arms era-B); FINALIZED-only guard blocks re-reverse/re-finalize; multi-level chains reverse only their own lines (isolated).
- **ledger/idempotency:** double-finalize / double-reverse blocked by the DRAFT/FINALIZED status check under advisory lock 5374; `reverse_entry` double-reversal guarded by app check + the `uniq_one_reversal_per_entry` DB constraint; `worker_balance` nets reversals to 0.
- **5374** serializes all finalize/reverse/rerate; lock orders (finalize 5374→ADST→SR→WSC→profile→advance; reverse 5374→ADST→SWA→PSI; rerate 5374→AddaStageRoleRate→WSC) all take 5374 first → deadlock-free. Recovery-over-concurrent-settlement is closed by 5374.

### BUG PA-11-1 — reversed recovery hides the restored advance (MEDIUM)
- **Module:** expense/payroll_service · **Reproduction:** finalize a settlement that fully recovers advance #A, then reverse it. `advance_remaining`/`advance_outstanding` correctly restore #A (they filter `reversed_at__isnull=True`), but `outstanding_advances()` (the source for the settlement recovery table, `expense/views.py:386`) summed `amount_recovered` WITHOUT that filter → the reversed PSI still counted → remaining computed to 0 → #A dropped out → the owner can't re-recover it.
- **Root cause:** `outstanding_advances` (payroll_service.py:77) diverged from its two siblings. **Fix:** add `reversed_at__isnull=True`. **Verification:** `test_outstanding_advances_excludes_reversed_recovery` (fully-recover → reverse → advance reappears with full remaining). 687 green. **Status:** ✅ FIXED

### BUG PA-11-2 — grouped→0 not applied at the settlement preview (MEDIUM, carried from Phase 10)
- **Module:** expense/settlement preview · **Reproduction:** group a payable stage AFTER its workers completed (frozen `expected_rate` stays non-zero). `settlement_queue` (`adda_settlement_service:195`) + `_line_dict` (`expense/views.py:347`, feeding per-worker + `grand_expected`) computed `qty × c.expected_rate` (raw), so the approval gate showed ₹(qty×stale) while finalize correctly books ₹0 (`effective_pay_rate` grouped→0). Visibility divergence (money correct) — the approver sees a number finalize won't pay.
- **Root cause:** the F2 structural guard (apply `effective_pay_rate` ANYWHERE `expected_*` is recomputed) was missing at the two preview surfaces. **Fix:** apply `effective_pay_rate` at both (mirror finalize). **Verification:** `test_grouped_after_complete_preview_matches_finalize_zero` (queue `expected == 0 == finalize expected_total`). 687 green. **Status:** ✅ FIXED

### BUG PA-11-3 — finalize locks the wrong table to freeze the settled quantity (MEDIUM, carried from Phase 10)
- **Module:** expense/adda_settlement_service · **Reproduction:** finalize locks `AddaStageRecord` rows ("freeze quantity inputs") but `settlement_quantity` resolves from `WorkerStageContribution.verified_quantity`, which finalize never locked; `set_verified_quantity` takes neither 5374 nor the SR lock. A verified-quantity correction committing during the finalize window (after finalize reads the lines, before it stamps `settlement_line`) is a lost update → money books on the stale quantity. The in-code comment falsely claimed the SR lock froze verified edits.
- **Root cause:** lock-domain mismatch. **Fix:** finalize now `select_for_update(of=('self',))` the WSC rows of the payable stages (the same target `set_verified_quantity` locks) so a racing verify blocks → then sees `settlement_line` set → refuses; corrected the comment. No deadlock (every settlement op takes 5374 first; set_verified takes only the WSC row). **Verification:** structural lock — a true two-actor READ-COMMITTED lost-update isn't reproducible in a single-threaded `TestCase`; covered by no-regression on the full finalize/reverse suite + the existing verified-after-finalize refusal test. 687 green. **Status:** ✅ FIXED

### Verified-but-not-fixed
- **PA-11-SOUND:** the finalize/reverse/supersede/ledger areas were examined in depth with no defect (recorded per the honesty rule — area covered, not silently "clean"). `verified_quantity=0` correctly pays 0; alter/missing never enter the payable; recovery>earning negative balance is by-design.

### Mobile (highest priority)
All three fixes are backend (a query filter, a rate-guard mirror on read-only preview helpers, a row lock) — no template/markup/CSS change, no mobile-render delta. (The preview numbers now match finalize, which is a correctness improvement to the management settlement screen, not a layout change.)

### UI_COMPONENTS.md
No change — backend settlement-truth + preview-parity guards; no reusable visual/layout rule emerged.

---

## PHASE 12 — PAYROLL AUDIT · RESULT

**Scope:** payroll as a money-consumption (read/aggregate/display) system — generation/aggregation/display/filtering/history/visibility · grouped-worker · settlement integration · reverse/supersede effects · stale values · duplicate records · permissions · audit trail. Verified DB ⟷ service ⟷ UI consistency. Looked specifically for amount mismatches, stale cached values, missing reversals, double counting, hidden records, permission leaks, export inconsistencies.

**Method:** deep-read `payroll_service.py` + the three payroll views + a FINDER-ONLY Workflow (4 finders, verify omitted). **All 4 finders survived → 14 candidates**, each main-thread-verified. Three real reversal-netting mismatches fixed (found main-thread before the finders returned; the finders — running against the working tree — confirmed them fixed + tests passing, and surfaced no new fixable defect).

### Theme: payroll figures must net reversals consistently
Balances are derived live from the ledger (never stored) and `pending_payable = Σcredits − Σdebits` was always correct (a reversal writes one opposite entry, so it nets). The bugs were in the DERIVED display figures that aggregate by category and must exclude reversed rows — three sites had drifted from the canonical `worker_summary`/advance helpers.

- **PA-12-A (MEDIUM):** `payroll_totals().advance_exposure` summed recoveries without `reversed_at__isnull=True` → factory-wide exposure understated after a reversal. Fix: add the filter.
- **PA-12-B (MEDIUM):** `PayrollOverviewView` `recovered_map` likewise → the "Advance Out" column + factory total understated after a reversal (disagreed with worker-detail). Fix: add the filter.
- **PA-12-C (MEDIUM):** `PayrollOverviewView` computed `total_earnings = credits − reversals` and `total_settled = settled` (gross). A settlement reversal writes a CREDIT/REVERSAL (undoing the advance-recovery debit) that inflated "Earned"; a payment reversal would inflate "Settled". Fix: the grouped aggregate now nets by category exactly like `worker_summary` (`earned − earned_reversed`, `settled − settled_reversed`). Overview == each worker's own page == ledger.

**Verification:** `Phase12PayrollAuditTests.test_advance_exposure_and_earnings_correct_after_reverse` — finalize-with-recovery → reverse, then assert `payroll_totals`, `worker_summary`, AND the live `PayrollOverviewView` context all agree (advance restored to ₹100, earnings netted to ₹0). Full suite 687 → 688, OK.

### Verified SOUND / documented-not-fixed
- **Permissions:** `MyEarningsView` self-scoped (no worker_id param); `WorkerPayrollDetailView` gated by `can_view_worker` (worker → self only, tested via URL-tamper in `test_views`); `PayrollOverviewView` `_ManagementOnly`. No leak.
- **No payroll export surface** exists (no CSV/HttpResponse view) → the "exports" lens is N/A (recorded, not assumed clean).
- **Reverse/supersede self-heal:** `worker_stage_earnings`/`worker_adda_earnings`/`unsettled_expected` read non-voided SWA + re-arm correctly after a reversal; era-A/era-B can't double-count (the `_settleable_lines` skip).
- **PA-12-BREAKDOWN:** `worker_balance_breakdown` is unwired dead code (no caller) — its post-reversal `debits_by_category` would read oddly but is never displayed.
- **PA-12-GROUPED-BOARD (LOW, by-design):** a worker who did ONLY grouped/zero-cost work (₹0 payable, no ledger credit) is absent from the payroll board — by design (the board scopes to payroll activity; productivity has its own views).
- **PA-12-PIECES-SEMANTICS (refuted):** overview "Pieces" (settled qty) vs `worker_production_stats` (production output) measure different things — labeling nuance, no money impact.

### Mobile (highest priority)
All three fixes are backend aggregate-query filters — no template/markup/CSS change, no mobile-render delta. (The displayed numbers are now correct, a data-truth fix to the management overview, not a layout change.)

### UI_COMPONENTS.md
No change — backend aggregation-netting fixes; no reusable visual/layout rule emerged.

---

## PHASE 13 — REPORTING + SEARCH + FILTER + EXPORT AUDIT · RESULT

**Scope (merged 13+14):** the user-facing reporting surface — dashboard totals/aggregations · list filters · search · sort · pagination · CSV/XLSX/PDF exports · date-range filters · stale data · reporting visibility/RBAC.

**Method:** mapped the surface (exports = barcode manifests; dashboards = production/raw_materials/inventory/expense; lists = Adda/Roll/User/Settlement/Export) + a FINDER-ONLY Workflow (4 finders, verify omitted). **All 4 finders survived → 8 candidates** (deduped to 6 distinct bugs), each main-thread-verified. Three HIGH.

### What's verified SOUND
- **Pagination:** every paginated ListView has a stable `order_by` (the "vanishing records on pagination" class is closed — incl. the documented `UserListView` `-date_joined,email` fix).
- **Digest/aggregation reconciliation:** `operations_digest` is single-source for stalled/pending (drill-downs reconcile) + reuses the (P12-fixed) `payroll_totals`. `adda_cost_summary` honest-NULL + cost-duality respected.
- Filter parse-guards on the audited dashboards (PA-08 `.isdigit()`/`_parse_date`) hold.

### BUG PA-13-1 — barcode dashboard cross-join inflation (HIGH)
- **Module:** inventory/barcode-dashboard (`/tracking/`) · **Reproduction:** a multi-batch Adda with ≥1 scanned piece → the single `.annotate()` joining `Sum(barcode_batches.total_pieces)` × `Count(barcodes)` cross-joins: per-Adda `total` ×#barcodes, `packed`/`dispatched`/`missing` ×#batches (verified: 2 batches + 3 scanned → total 300 vs 100, packed 4 vs 2, pending 294 vs 97). KPI cards (separate queries) stayed correct → the page contradicted itself.
- **Fix:** compute total + scanned-by-status from SEPARATE per-Adda grouped queries (the KPI approach), attach in Python — no cross-join. **Test:** `BarcodeDashboardCountTests` (asserts per-row == real == KPI). **Status:** ✅ FIXED

### BUG PA-13-2 — roll-list 500 on non-numeric id filter (HIGH)
- **Module:** raw_materials/roll-list · **Reproduction:** `GET /raw-materials/rolls/?cloth_type=abc` (or color/location) → integer FK lookup `ValueError` → 500 → list unreachable. **Fix:** `.isdigit()` guard. **Test:** `RollListReportingTests.test_non_numeric_id_filters_do_not_500`. **Status:** ✅ FIXED

### BUG PA-13-3 — cost/supplier leak via Time-Logs accordions (HIGH)
- **Module:** raw_materials reporting (roll list + cloth dashboard + raw-material dashboard) · **Reproduction:** edit a roll's cost/supplier (writes `ClothRollHistory`), then view any of the 3 surfaces as a worker/manager — the accordion renders `cost_per_kg`/`supplier` change values that the roll table/detail hide. The PA-03-1 class, on 3 surfaces its fix didn't cover.
- **Fix:** server-side `exclude(field_name__in=('supplier','cost_per_kg'))` for non-financial viewers on all 3. **Test:** `RollListReportingTests` (worker hidden, financial shown). **Status:** ✅ FIXED

### Lower-severity (fixed)
- **PA-13-4 (MEDIUM):** `UserListView` 500 on non-numeric `?skills` → keep-numeric guard. Super-admin-only. Test: `UserListFilterParamTests`.
- **PA-13-5 (LOW):** roll-list rendered a misleading "Status: garbage" chip + full `filtered_count` for an invalid status → ignore invalid status in context. Test: `test_garbage_status_shows_no_status_chip`.
- **PA-13-6 (LOW):** CSV/XLSX barcode manifest didn't neutralize spreadsheet formula injection in free-text color/size labels → `_csv_safe` prefixes formula-leading cells with `'`. Tests: `FormulaInjectionTests`.

### Mobile (highest priority)
All six fixes are backend (aggregate queries, filter guards, a server-side exclude, an export cell-sanitizer) — no template/markup/CSS change, no mobile-render delta. (PA-13-1/PA-13-3 make the rendered numbers correct + close a leak — data-truth/security fixes, not layout.)

### UI_COMPONENTS.md
No change — all fixes are backend (query/visibility/export). No reusable visual/layout/component rule emerged. (Mobile + UI-consistency rule-harvesting begins in Phases 14–15 per the owner rule.)

---

## PHASE 14 — MOBILE RESPONSIVENESS AUDIT · RESULT

**Scope:** every priority user-facing surface at **320 / 375 / 390 / 414px** — worker reporting, layering/cutting/pattern/barcode workspaces, Adda detail + list, settlement (list/detail/create), payroll (overview/worker-detail), roll management, dashboards (production/raw-material/cloth/tracking/barcode), stage-rate correction, report-review, and all major CRUD forms (user/role/adda/roll-bulk/advance/worker-profile).

**Method:** real headless-Chromium (gstack browse), logged in as super-admin. For each surface, at each width: an injected diagnostic measured (a) true horizontal overflow accounting for `body{overflow-x:hidden}` masking — flagging elements whose content is **clipped by an `overflow-x:hidden` ancestor** (the masking trap that hides real overflow from a naive `scrollWidth==innerWidth` check), (b) overflow-x:auto scroll containers, (c) sub-36px touch targets on buttons/links/inputs. Visual screenshots confirmed every candidate (the detector's clip heuristic produces flex false-positives — each was screenshot-verified before accepting or refuting). **Note (process):** the dev `runserver` caches templates in-process — server MUST be restarted after each template edit for changes to render (caught a stale-verify early; re-verified post-restart).

**Result:** 3 real defects fixed, 2 refuted. No console errors on any surface. Forms (user-create, roll-bulk, worker-report, worker-profile, barcode-dashboard) verified genuinely clean (`overflow-x:visible`, no clip). The worker-report phone surface remains exemplary (Phase 05B).

### BUG PA-14-1 — Settlement-detail money tables clipped off-screen on mobile
- **Severity:** HIGH · **Module:** expense/settlement-detail · **Page:** `expense:adda-settlement-detail` · **Device:** mobile (320/375/390/414) · **Role:** management
- **Reproduction:** open a finalized settlement (`/expense/settlements/ADST-0003/`) at 320px → the per-worker snapshot table shows only Worker / Expected ₹ / Advance before ₹ + a sliver of "Rec…"; **Recovered ₹ and Final payable ₹ are off the right edge with no way to scroll to them.**
- **Root cause:** 6 bare `<table>`s (no `.table-responsive` wrapper). Content sits in `main.content { overflow-x: hidden }` (and `.main`/`.shell` likewise), so a 448px table on a 320px viewport is clipped, not scrollable. `width:100%` can't shrink a table below the sum of its column min-widths.
- **Files:** `config/expense/templates/expense/adda_settlement_detail.html` (6 tables).
- **Fix:** wrapped each table in `<div class="table-responsive">` + added `data-label` to every `<td>`. The global `.table-responsive` rule gives desktop h-scroll and, at ≤600px, switches each row to a stacked label:value card — every column (incl. money) visible.
- **Verification:** 320px screenshot — per-worker card shows Expected/Advance before/Recovered/**Final payable ₹ 225.00**; diagnostic clip count 0; last `<td>` right=292 < vw 320. 696 tests green.
- **Status:** ✅ FIXED

### BUG PA-14-2 — `.filter-card` filters scroll off-screen on mobile (no stacking)
- **Severity:** MEDIUM · **Module:** filter-card (roll-list, adda-list, adda-dashboard, cloth-dashboard, tracking/barcode-dashboard) · **Device:** mobile · **Role:** all
- **Reproduction:** `/raw-materials/rolls/` at 320px → the filter bar (6 fields ≈ 864px) scrolls horizontally; "Cloth Type" is cut mid-field and Location/Color/Apply/Reset are hidden with no visible scroll affordance.
- **Root cause:** page-scoped `.filter-card` is `display:flex; flex-wrap:nowrap; overflow-x:auto` with `flex-shrink:0` + `min-width:150px` fields; no page had a mobile media rule to stack them.
- **Files:** roll_list.html, adda_list.html, adda_dashboard.html, cloth_dashboard.html, barcode_dashboard.html.
- **Fix:** `@media (max-width:600px) { .filter-card { flex-direction:column; align-items:stretch; overflow-x:visible } .field{width:100%} input,select{width:100%; min-width:0} }` on all 5.
- **Verification:** all 5 at 320px → `overflow-x:visible`, scrollWidth==clientWidth, fields full-width (262–270px); roll-list screenshot shows all filters stacked + visible.
- **Status:** ✅ FIXED

### BUG PA-14-3 — Class-less fancy-select renders as a bare ~20px line (touch target + consistency)
- **Severity:** MEDIUM · **Module:** base.html fancy-select · **Page:** advance-add, settle-create, layering-workspace roll filters · **Device:** mobile (also desktop) · **Role:** worker + management
- **Reproduction:** `/expense/advances/add/` at 375px → the "Worker" dropdown is a thin ~20px underlined grey line, visually unlike the cream Amount/Date/Notes inputs and too short to tap; same on the settlement payment-method select and the layering "Colour/Type/Width" roll filters (a worker phone surface).
- **Root cause:** fancy-select JS replaces `<select>` with `<button class="fancy-select-trigger " + select.className>`. Pages that style selects **by tag** (`.expense-form select{}`) can't reach the button → a class-less select yields an unstyled UA button (h=20, padding 0, grey). Pages that put a class on the select (`sf-input`) render correctly (the class is copied to the trigger).
- **Files:** `config/accounts/templates/accounts/base.html` (fancy-select JS class assignment + new `.fancy-select-trigger--bare` CSS).
- **Fix:** when `select.className` is empty, the JS tags the trigger `.fancy-select-trigger--bare`, styled as a default cream input box (`padding:11px 13px; min-height:44px; border; border-radius; cream bg`). Classed triggers never get `--bare` → zero regression. Touch target now ≥44px.
- **Verification:** advance/settle/layering triggers now 44px cream boxes (was 20px); dropdown still opens (7 options); screenshot confirms visual parity with sibling inputs. 696 green.
- **Status:** ✅ FIXED

### Refuted
- **PA-14-TOPBAR-TITLE:** mobile topbar title clip = intended `text-overflow:ellipsis` (full title in hero). Not a bug.
- **PA-14-HERO-FLEX:** `.hero` scrollWidth≈clientWidth+100 = flex min-content artifact; screenshot-verified fully visible at 320px, no child exceeds viewport. False positive.

### UI_COMPONENTS.md
**UI_COMPONENTS.md updated** — 3 reusable rules captured: (1) Tables — never ship a bare `<table>`; wrap in `.table-responsive` + `data-label` (the `main.content{overflow-x:hidden}` clip applies to detail/money tables, not just DataTables lists). (2) New `.filter-card` mobile-stacking standard (media rule). (3) Selects — corrected the stale "tag CSS auto-applies" claim; documented that tag-only `select{}` rules don't reach the `<button>` trigger + the new `.fancy-select-trigger--bare` fallback.

---

## PHASE 15 — UI CONSISTENCY AUDIT · RESULT

**Scope:** design-system consistency + mobile-first UI standard across the app, with the 4 explicit carry-forward watch items: (1) latent bare-table risk on the 9 named surfaces (`_stage_panel_cutting`, `_stage_panel_cutting_pattern`, `adda_settlement_list`, `payroll_overview`, `worker_detail`, `settlement_form`, `product_sizes_edit`, `costing`, `product_patterns_edit`); (2) touch targets (buttons/icon-buttons/row-actions/pills/links vs 44px); (3) fancy-select consistency (class-less selects on the Phase-14 fallback); (4) date-input audit.

**Method:** real headless-Chromium (gstack browse), super-admin, at **320 / 375 / 390 / 414 / 1280px**. Per surface an injected diagnostic measured: table `scrollWidth` vs viewport AND the nearest `overflow-x` ancestor (to catch the `main.content{overflow-x:hidden}` clip trap), `thead` display (is mobile stacking actually active), per-element bounding boxes for sub-44px touch targets, and date-input width/clip. Static grep mapped every `<table>` (wrapper + `data-label` presence) and every class-less `<select>`/`type=date` first; browser confirmed each candidate (screenshots for the real defects). **Process:** dev `runserver` caches templates in-process → server restarted after the template edits before re-verifying (Phase-14 gotcha). **Data gap handled honestly:** `worker_detail`/`settlement_form` `.adv` tables don't render with 0 advances in dev — injected one temp `WorkerAdvance`, browser-verified, then **deleted it** (DB restored to 0); recorded the method rather than marking clean on absent data.

**Result:** 3 real defects fixed (all the inline-edit-form table family), 5 surfaces/dimensions documented SAFE/CLEAN with browser evidence. No console errors. The key root-cause distinction: **a table cell holding a `<form>` with fixed-width inputs cannot shrink and clips; a text-only table wraps and fits.** That separates the 3 bugs (inline-edit tables) from the safe `.adv` money tables (text-only). The 4 already-stacking surfaces (cutting panel / costing / adda_settlement_list / payroll_overview) ship their own page-scoped stacking and were browser-confirmed.

### BUG PA-15-1 — product_sizes_edit inline-edit table clips Archive off-screen + sub-44 mini buttons
- **Severity:** MEDIUM · **Module:** production/product_sizes_edit · **Page:** `production:product-sizes` · **Device:** mobile (≤340px) · **Role:** management
- **Reproduction:** `/production/products/1/sizes/` at 320px → the Active Sizes table is 351px wide; ORDER is the last fully-visible column and the **Actions/Archive button is clipped off the right edge with no scroll** (screenshot). Cannot archive a size on a phone. Save/Archive `.btn-mini` measured 28px tall.
- **Root cause:** bare `<table>` with `.ps-edit input[name=label]{width:140px}` + `input[type=number]{width:80px}` in the Label cell's inline-edit form. Fixed-width inputs can't shrink, forcing the table past the 320px viewport; `main.content{overflow-x:hidden}` clips it with no scroll. `data-label` was absent so the canonical stacking couldn't engage.
- **Files:** `config/production/templates/production/product_sizes_edit.html` (both tables + extra_head).
- **Fix:** wrapped both tables in `.table-responsive`; added `data-label` to every `<td>`; `class="cell-edit"` on the form cell, `class="td-actions"` on the action cell; `@media(≤600px)` block: edit form column-stacks full-width, `.btn-mini` → `min-height:44px`.
- **Verification:** 320px — table 254px, `thead` hidden (stacked cards), Archive in its own full-width actions row + reachable, `.btn-mini` all 44px (screenshot). 1280px — `thead` visible, normal table, no clip. 696 green.
- **Status:** ✅ FIXED

### BUG PA-15-2 — product_patterns_edit: identical inline-edit bare-table pattern
- **Severity:** LOW · **Module:** production/product_patterns_edit · **Page:** `production:product-patterns` · **Device:** mobile · **Role:** management
- **Reproduction:** `/production/products/1/patterns/` — same Pattern · Pieces/Adda[number input + Save] · Remove inline-edit table; fits at 320px for short data (254px) but shares the fixed-shrink-input clip risk, and `.btn-mini` Save/Remove were 28px.
- **Root cause / Fix:** identical to PA-15-1 (sibling config page, same author/pattern). Fixed together: `.table-responsive` + `data-label` + `cell-edit`/`td-actions` + `@media(≤600px)` stacking + 44px `.btn-mini`.
- **Files:** `config/production/templates/production/product_patterns_edit.html`.
- **Verification:** 320px stacks (thead hidden), 1280px unchanged. 696 green.
- **Status:** ✅ FIXED

### BUG PA-15-3 — standalone pattern_workspace breakup-tables don't stack (dead data-label)
- **Severity:** LOW · **Module:** production/pattern_workspace · **Page:** `production:pattern-workspace` · **Device:** mobile · **Role:** cutting-master/management
- **Reproduction:** `/production/addas/3-PATTI-001/pattern/` at 320px → the `.breakup-table` / `.cp-verify-table` carry `data-label` attrs (author intended stacking) but render with `thead` visible, unstacked + cramped; the same partial stacks correctly inside the embedded stage panel.
- **Root cause:** `_stage_panel_cutting_pattern.html` is included by two hosts. `stage_panel_embedded.html` scopes `.breakup-table` mobile stacking on the **bare element** → works. The standalone `pattern_workspace.html` pulls `_form_styles.html`, which scopes stacking under **`.form-shell .breakup-table`** — but the workspace wrapper is not `.form-shell`, so the rule never matched and `data-label` was inert.
- **Files:** `config/production/templates/production/pattern_workspace.html` (extra_head).
- **Fix:** added a bare-`.breakup-table` `@media(≤600px)` stacking block to the workspace head (mirrors the embedded path) so the shared partial stacks identically in both hosts. Chose this over adding `class="form-shell"` to the wrapper (would restyle the whole page — regression risk).
- **Verification:** 320px — both tables `thead` hidden, no clip; 1280px unchanged. 696 green.
- **Status:** ✅ FIXED

### Documented SAFE / CLEAN (verified, not fixed)
- **PA-15-ADV-SAFE** — `worker_detail` (4-col) + `settlement_form` (2-col) `.adv` money tables are bare but **text-only**: cells wrap, table shrinks to fit, all money columns visible at 320px (272px / 266px, browser-verified with an injected+deleted temp advance). Not a clip bug; left bare per no-speculative.
- **PA-15-STACK-SAFE** — cutting panel / costing / adda_settlement_list / payroll_overview ship their own page-scoped stacking; browser-confirmed `thead` hidden + no clip at 320px.
- **PA-15-SELECT-CLEAN** — all class-less `<select>` covered by the Phase-14 `.fancy-select-trigger--bare` fallback (44–45px, browser-confirmed). No migration needed.
- **PA-15-DATE-CLEAN** — native `type=date` inputs render full-width (305–313px), no clip/overlap, picker reachable at 320/375px.
- **PA-15-TOUCH-CLEAN** — only sub-44 actionable = `.btn-mini` (fixed in PA-15-1/2); `.hamburger`/`.close-btn`/`.btn`(38px)/inline text-links are pre-existing app baseline, not regressions.

### UI_COMPONENTS.md
**UI_COMPONENTS.md updated** — 3 reusable rules captured under Tables: (1) **`data-label` is inert without a `.table-responsive` ancestor** — the ≤600px stacking media query keys every rule on the wrapper; data-label alone does nothing (found dead in several templates). (2) **Inline-edit tables clip worse than text tables** — form cells with fixed-width inputs can't shrink → MUST use `.table-responsive` + `data-label` + `cell-edit`/`td-actions` + the mobile stacking/44px snippet; text-only tables wrap and are safe to leave bare (document why). (3) **Shared table partials must own their responsive CSS** — scope stacking to the bare element (not a host-only class like `.form-shell`) so every include path gets it.

---

## PHASE 16 — PERFORMANCE AUDIT · RESULT

**Scope:** real performance defects (not micro-optimizations) — N+1 query patterns, missing `select_related`/`prefetch_related`, unbounded querysets, heavy per-request aggregation, duplicate/redundant queries, large template loops triggering lazy queries, export query/memory cost, and any endpoint that degrades as data grows. Focus surfaces: lists, dashboards, detail pages, settlement/payroll aggregations, exports.

**Method (MEASURED, not code-read):** a 2-data-scale query-count harness using `django.test.utils.CaptureQueriesContext` + the test `Client`/`RequestFactory`. For each candidate, query counts captured at two data sizes (e.g. 1 vs 5 contribution lines, 1 vs 4 Addas, 1 vs 9 workers) so a count that **grows with N proves an N+1** (and a flat count proves clean) — no surface marked clean on code-reading alone (audit honesty rule). Repeated-SQL attribution (normalized SQL `Counter`) pinned each N+1 to its exact relation access. The dev DB is tiny (5 Addas), so scaling tests (not absolute counts) were the oracle. Fixes re-measured before/after; the temp harness was converted into 4 permanent `assertNumQueries` scale-invariance regression tests.

**Result:** 2 real defects fixed (1 HIGH, 1 MEDIUM, both on the settlement money-approval page), 1 candidate refuted by measurement, 1 structural cost documented-deferred, 4 read paths measured-clean. 700 tests green (+4 regression).

### BUG PA-16-1 — Settlement-detail draft + queue: per-line N+1 on `workflow_stage.stage`
- **Severity:** HIGH · **Module:** expense/adda_settlement_service · **Surfaces:** `AddaSettlementDetailView` (draft), `settlement_queue` (AddaSettlementListView), `preview_lines` · **Role:** management
- **Reproduction (measured):** open a DRAFT settlement at increasing line counts → settlement-detail draft = 17q @ 1 line, 33q @ 5 lines (**+4 queries per contribution line**); settlement queue = 6q @ 1 Adda, 22q @ 4 Addas. Repeated-SQL attribution: `production_workflowstage` ×N + `production_stage` ×N (one pair per line).
- **Root cause:** `_settleable_lines` select_related'd `task__stage_record` but **not** `__workflow_stage__stage`, while every consumer (`_line_dict`, `settlement_queue`, `cost_service.effective_pay_rate`) reads `c.task.stage_record.workflow_stage.stage.name` **per line** → 2 lazy queries each. On a real multi-size/colour cutting Adda (30+ lines) the money-approval page issued ~137 queries.
- **Files:** `config/expense/services/adda_settlement_service.py` (`_settleable_lines` select_related, +1 line).
- **Fix:** added `task__stage_record__workflow_stage__stage` to the select_related — covers `.workflow_stage` and `.stage` in the existing join (the same join finalize already traverses). Pure fetch change, no result change.
- **Verification (measured after):** settlement-detail draft +2q/line (remainder = PA-16-2); queue +4q/Adda (remainder = PA-16-QUEUE structural). Full suite green.
- **Status:** ✅ FIXED

### BUG PA-16-2 — Settlement-detail draft: `outstanding_advances` called per worker (N+1)
- **Severity:** MEDIUM · **Module:** expense/views (`AddaSettlementDetailView`) + payroll_service · **Role:** management
- **Reproduction (measured):** after PA-16-1 the draft still grew +2q/line; attribution = `expense_workeradvance` ×N + `expense_payrollsettlementitem` SUM ×N — the `for w in by_worker.values(): w['advances'] = outstanding_advances(w['worker'])` loop = 2 queries per distinct worker.
- **Root cause:** `outstanding_advances(worker)` is per-worker; the finalize gate renders every worker's outstanding advances (per-advance recovery inputs), so it ran once per worker.
- **Files:** `config/expense/services/payroll_service.py` (new `outstanding_advances_bulk`), `config/expense/views.py` (draft branch calls it once).
- **Fix:** `outstanding_advances_bulk(workers)` returns `{worker_id: [rows]}` with the **identical row shape + the same `reversed_at__isnull=True` filter (PA-11-1)** in **2 queries total** regardless of worker count; the view replaces the loop with one call.
- **Verification (measured after):** **settlement-detail draft now FLAT — 15q at both 1 and 5 lines (delta/line = 0)**, i.e. O(1) in contribution lines (≈137q → 15q on a 30-line Adda). Regression test asserts bulk rows == per-worker rows (semantics preserved on a money page) + the 2-query bound + empty-input 0-query.
- **Status:** ✅ FIXED

### Refuted (by measurement)
- **PA-16-DUP** (adda-detail "duplicate stage_records prefetch"): hypothesis was that `sr_qs` (iterated for `sr_by_type`) plus `sr_qs.order_by(...)` (ctx `stage_records`) re-fetches + re-runs prefetches. **Measured false** — the `worker_tasks` prefetch ran **×1** (a second full evaluation would re-run it). adda-detail = 25q for a rich K-stage tabbed page (per-stage snapshot + per-stage RBAC); only repeats are tiny role PK-lookups (×6), bounded by stage count (flow length), not data growth. Not a defect.

### Documented (measured, deferred — out of stabilization scope)
- **PA-16-QUEUE** (LOW): `settlement_queue` residual ~4 queries/Adda after PA-16-1 (`_payable_stage_records` + `_settleable_lines` contributions + era-A pairs, per Adda; 6q@1 → 17q@4). STRUCTURAL — inherent to classifying every pending Adda and **bounded by the pending-unsettled queue** (fully-credited Addas drop out; does not grow with all-time Adda count). Batching across Addas would redesign the locked `_settleable_lines` (shared with finalize) + queue classification — forbidden by the audit rule "no redesign of settlement logic to chase speed." Left as-is.

### Measured-clean (flat — confirmed by measurement, not assumption)
- **my-earnings** 34q flat (1→5 Addas worked) · **worker-detail** 39q flat · **payroll-overview** 10q flat (1→9 workers; pre-aggregated grouped maps) · **get_cutting_snapshot** 8q flat (1→5 bundles; `prefetch_related('items__pattern','items__color')` works).
- Read-confirmed already-optimized (prior phases, explicit N+1-prevention comments + locked baselines): 5 dashboards (adda / raw-material / cloth / barcode-tracking / inventory), costing (`COSTING_QUERIES=10` locked), adda-list (`ADDA_LIST_QUERIES=11` locked), roll-list (select_related + paginate_by=50), barcode export (rows computed from `BarcodeBatch` seq-ranges — no per-label query), barcode list/print (one scanned-state prefetch + Python expand), history timelines (select_related, single-entity bounded), worker-report (single-task form, select_related).

### Regression coverage
`config/expense/tests/test_perf_settlement.py` (+4 tests, mirrors `production/tests/test_perf_baseline.py`): (1) settlement-detail draft query count **flat** at 2 vs 6 lines (catches a re-introduced per-line N+1 without hardcoding an absolute); (2) `outstanding_advances_bulk` == 2 queries for any worker count; (3) bulk rows **equal** per-worker `outstanding_advances` rows (semantic equivalence on a money page); (4) empty input = 0 queries. **Note:** not committed — awaiting review (working tree holds the Phase-16 changes + this status update).

### Docs-sync
`config/expense/README.md` — added a PA-16 perf note under `payroll_service` (settlement-detail read path is O(1) in lines; `outstanding_advances_bulk` is the batched sibling of `outstanding_advances`, same filter).

---

## AUDIT METHODOLOGY (per page)

A page passes only when ALL hold: A loads · B RBAC · C navigation · D mobile render · E desktop render · F CRUD · G validation · H error handling · I persistence · J visibility · K search/filter · L actions · M no console errors · N no server errors · O no broken links · P no hidden overflow · Q no layout break · R no inaccessible controls · S no permission bypass · T no stale data.

**Mobile (highest priority):** test 320 / 375 / 390 / 414px — overflow, clipping, dropdown/date-picker visibility, modal usability, table usability, form usability, button accessibility, keyboard overlap, scrolling. Any mobile issue = HIGH.

**Every issue must be reproducible** and carry: reproduction steps · root cause · affected files · fix · regression verification.

---

## BUG REPORT FORMAT

```
BUG ID:        PA-<phase>-<n>
Severity:      CRITICAL | HIGH | MEDIUM | LOW | COSMETIC
Module:
Page:
URL:
Role:
Device:        desktop | mobile <width> | both
Reproduction:  numbered steps
Expected:
Actual:
Root Cause:
Files:         path:line
Fix:           what changed
Verification:  test added/run + manual recheck + regression (641 baseline)
Status:        OPEN | FIXED | WONTFIX(reason) | DEFERRED(reason)
```

---

## HOW TO RUN TESTS (regression gate)

Tests are discovered only from the `config/` working directory:

```bash
cd config && ../env/bin/python manage.py test --settings=config.settings.local --parallel 4
```

Baseline at audit start: **641 tests, OK**. Every fix must keep this green (or add tests, raising the count).
Dev login creds for browser testing: see memory `project_test_credentials`.

---

## WORK RULES (do not violate)

1. No feature development · 2. No architecture redesign · 3. No speculative improvements · 4. No future roadmap work · 5. No refactor unless required to fix a verified issue · 6. Every issue reproducible · 7. Full bug report each · 8. One phase at a time · 9. Update THIS file after every phase · **STOP after each completed phase and wait for review.**
