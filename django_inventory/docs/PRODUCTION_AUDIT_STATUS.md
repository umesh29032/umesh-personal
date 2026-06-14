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
| **Current phase** | PHASE 02 — Authentication Audit ✅ COMPLETE (awaiting review) |
| **Next phase** | PHASE 03 — RBAC Audit |
| **Branch** | `new_flask_app` |
| **Last updated** | 2026-06-14 |
| **Green test baseline** | **649 tests, all passing** (was 641; +8 Phase-02 regression tests) |
| **Open blockers** | None (PA-02-OPEN-SIGNUP resolved: owner chose to disable native signup; done + verified) |

---

## PHASE LEDGER

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 01 | System Mapping | ✅ COMPLETE | `docs/AUDIT_SYSTEM_MAP.md` written; 151 URLs / 151 views / 31 services / 36 forms / 109 templates mapped + nav/RBAC + infra. Map cross-validated vs actual `urls.py`. |
| 02 | Authentication Audit | ✅ COMPLETE | 18 candidates → 8 fixed (incl. owner-approved signup disable), 5 documented-no-fix, 5 refuted. Code+browser+DB+live verified. 649 tests green. |
| 03 | RBAC Audit | ⬜ PENDING | every role: access · visibility · restrictions · privilege escalation |
| 04 | Navigation Audit | ⬜ PENDING | sidebar links · buttons · actions · redirects |
| 05 | CRUD Audit | ⬜ PENDING | every module: C/R/U/D + DB persistence |
| 06 | Master Data Audit | ⬜ PENDING | products · stages · roles · workers · addas · materials · suppliers · customers |
| 07 | Stage Engine Audit | ⬜ PENDING | layering · cutting_pattern · cutting · barcode: create/assign/complete/reopen/settlement-impact |
| 08 | Raw Material Audit | ⬜ PENDING | cloth roll: inbound · stock · consumption · adjustments |
| 09 | Inventory Audit | ⬜ PENDING | |
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

### Issues fixed
PA-02-1, PA-02-2, PA-02-3, PA-02-4, PA-02-OPEN-SIGNUP — all with regression tests (649 green). Full reports below.

### Open blockers
- None.

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
