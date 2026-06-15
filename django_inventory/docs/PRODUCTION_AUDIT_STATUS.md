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
| **Current phase** | PHASE 09 — Inventory Audit ✅ COMPLETE (awaiting review) |
| **Next phase** | PHASE 10 — Production Audit |
| **Branch** | `new_flask_app` |
| **Last updated** | 2026-06-15 |
| **Green test baseline** | **679 tests, all passing** (was 641; +38 audit regression tests) |
| **Open blockers** | None. Documented follow-ups: storefront PA-05A-SF1..4 (migration); over-allocation 3-PATTI-001 (pre-foundation dev data, foundation flags off pending soak); stray test-product data (dev-DB cleanup). |

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
| 09 | Inventory Audit | ✅ COMPLETE · commit `PENDING` | Inventory as a QUANTITY-TRUTH system (the `inventory` Django app is RBAC-only): roll/leftover · breakup↔bundle↔item · breakdown↔barcode · S4 pool · reopen effects · denorm counters · concurrency · reconcile. 6-finder conservation Workflow ran; **9/10 verifiers died on session limit → main-thread-verified every finder candidate (honesty rule — NOT marked clean on dead verifiers).** 2 fixed (PA-09-1 legacy-cutting double-create SR 500; PA-09-2 mixed manual+breakup add unique-collision 500). Refuted/documented: consume_leftover stale read-cache (benign), reconcile pieces_cut-vs-breakup (by-design, tested contract), reconcile 2-of-5 coverage (enhancement, counters self-heal), manual-no-bound (PA-07-BREAKUP class), total_pieces lost-update (display-only/PA-05B-RACE). 679 green. |
| 10 | Production Audit | ⬜ PENDING | |
| 11 | Settlement Audit | ⬜ PENDING | |
| 12 | Payroll Audit | ⬜ PENDING | |
| 13 | Reporting Audit | ⬜ PENDING | |
| 14 | Search/Filter/Export Audit | ⬜ PENDING | |
| 15 | Mobile Responsiveness Audit | ⬜ PENDING | **HIGHEST PRIORITY** — 320/375/390/414px |
| 16 | UI Consistency Audit | ⬜ PENDING | spacing · alignment · typography · buttons · dropdowns · date inputs |
| 17 | Performance Audit | ⬜ PENDING | |
| 18 | Regression Audit | ⬜ PENDING | full-system retest |

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
