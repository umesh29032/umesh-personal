---
id: app-accounts-views
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "accounts' ~26 view classes in one file — which handles what, and which are deliberately dead?"
related: [app-accounts, app-accounts-urls]
---

# accounts — handler knowledge (`config/accounts/views.py`, one file)

> 📂 [accounts app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## Handler groups at a glance

- **AUTH FLOWS (public, throttled):** LoginView (76) · ResendOTPView (128) ·
  VerifyOTPView (159) · PasswordLoginView (422) · ForgotPasswordView (598) ·
  ResetPasswordVerifyView (637) · LogoutView (218, POST-only) · HomeView (263)
- **ADMIN CRUD (superuser):** User ×4 (286–421) · Skill ×4 (707–765) ·
  UserType ×4 (766–806) — all via `SuperuserRequiredMixin` (280)
- **DELIBERATELY DEAD (teach-from-absence):** SignupView + SignupVerifyView +
  ResendSignupOTPView (467–597, S2 — unrouted) · EmailManagementDisabledView
  (234, S3 — the disabled stub)
- **DELETE:** guarded CRUD deletes only · **ASYNC:** none

## The handlers that matter most

**`LoginView` / `VerifyOTPView`** — the OTP pair: throttle-first, uniform
responses, hashed single-use codes via `utils.py`. Every branch is a pinned
behavior (37 tests) — read the tests as the spec.

**`PasswordLoginView`** — extends Django's LoginView with throttle +
normalized-email lockout keys (the mixed-case scar).

**`LogoutView`** — POST-only; the one-line lesson about CSRF-able GETs.

**`UserCreateView`** — the ONLY birthplace of accounts (S2). Role + skills
assigned here; everything downstream trusts this moment.

**The dead trio + stub** — do NOT delete them: they're executable history
of S2/S3, and the adapter (`allauth_adapters.py`) leans on their absence
from urls.py.

## Handler rules of thumb (this app)

1. Every public handler: throttle → uniform message → no-cache. No exceptions.
2. Never branch messages on account-existence — the oracle is the difference.
3. Admin CRUD gates by Django superuser HERE (predates role-set gating for
   these lanes) — consistent with SA-bypass; don't "modernize" casually.
4. New identity-touching view = the S2/S3 checklist in README first.

## Required Knowledge (this page)

- [ ] The three-surface hardening model → [auth-hardening](../../concepts/security/auth-hardening.md)
- [ ] Throttle design → [services.md](services.md)

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [services.md](services.md) →
`config/accounts/tests.py` (the 37 attacks).
