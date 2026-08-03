---
id: apps-accounts-guide
type: app-guide
status: active
owner: handwritten
scope: accounts
anchors: config/accounts/
verified: 2026-07-13
---

# accounts app — file-by-file GUIDE (identity + RBAC foundation)

> Business view: [config/accounts/README.md](../../../config/accounts/README.md).

| File | What |
|---|---|
| `models.py` | custom User (email login) · Role(+extra_roles M2M) · SidebarItemRule (RBAC relocated here 2026-06 — foundation owns access) |
| `services/permission_service.py` | ★ user_has_perm/_has_role + MENU REGISTRY (sidebar declarative; menu+URL ek saath gate) |
| `services/auth_service.py` | OTP issuance |
| `services/user_service.py` | user-provisioning invariants (no signals)  **C-1 2026-07-05: retro-tag/sync_user_skills REMOVED — zero production imports (COUP-5 resolved)** |
| `views.py` | FILE MAP at top: OTP login/verify · user CRUD · rate-limited password login · signup(pre-provisioned) · reset · `EmailManagementDisabledView` (**S3 fix 2026-07-12**: shadows allauth `/accounts/email/` so workers can't self-service their login identity — add/make-primary once synced into `User.email`; pins `tests.py EmailManagementDisabledTests`) · **`HomeView` D9 landing override (BOD-E 2026-07-18, owner charter): super_admin → `bod:dashboard`; manager → Operations (P1-1, unchanged); others → My Dashboard; auth flow untouched (matrix pinned in `bod/tests/test_certification.py` + P1-1 tests)** |
| `allauth_adapters.py` | pre-provisioned-only gate, BOTH halves: `RestrictedSocialAccountAdapter` (Google — link existing, refuse strangers) + `RestrictedAccountAdapter` (**S2 fix 2026-07-12**: closes allauth `/accounts/signup/`; before this, anonymous email+password signup created live active Users — worker-cert Phase H finding). Wired via `ACCOUNT_ADAPTER`/`SOCIALACCOUNT_ADAPTER` in settings/base.py. Pins: `tests.py SignupDisabledTests` + `AllauthAdapterTests` |
| `urls.py` | mounted at /app/ (allauth mounted separately at /accounts/ in root urls.py — Google OAuth; allauth email mgmt at `/accounts/email/` is shadowed by `EmailManagementDisabledView` in root urls.py, **S3 fix**) |
| templates/accounts/ | base.html ★ (THE design system: tokens + shared JS components incl. `fancy-select` & `fancy-date` calendar — vocab in [UI_COMPONENTS.md](../../../UI_COMPONENTS.md) — + money-family canonicals) + auth pages (`user_form.html` = edit user). **UI-audit 2026-07-20: `.td-actions` (mobile) + `.sticky-bar` ab `flex-wrap: wrap` — `justify-content: flex-end` + nowrap ka overflow LEFT jata hai (first button viewport ke bahar, unreachable); 5-button product rows + 3-button settlement bar clip karte the** |
| `templates/accounts/login.html` + shared/_auth_shell.html | OTP login (split shell, `body.auth-login` skin). **2026-07-20 UI polish, ALL gated under `.auth-login` (OTP/reset/password pages inert):** aurora breathing on brand glows · living-thread accent animation · submit shine sweep · `.auth-mobile-brand` strip ≤860px (brand identity back on phones) · "Back to Storefront" `.auth-back` link → `public_home` · **round-2 (same day): brand-panel particle canvas (`storefront/js/ke-particles.js`, self-guards reduced-motion + no-ops when panel hidden ≤860px) · copper shimmer on heading `em` · cursor-spotlight on card (fine pointers) · cross-document View Transition opt-in via `auth_extra_head` (login page ONLY — OTP/reset don't opt in, so they navigate plain; monogram carries `view-transition-name: ke-brand`, breakpoint-gated so exactly one element per page has it)**. Shell stays the ONE `.auth-*` CSS owner; login.html carries markup + presentation-only JS (form/CSRF untouched) |

Foundation-purity: core+accounts import NO domain app (CI gate 1/4).
Dots: har request → middleware(sidebar rules) → permission_service → view.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
