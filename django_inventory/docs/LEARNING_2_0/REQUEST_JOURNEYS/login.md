---
id: l2-request-journeys-login
type: request-journey
status: active
owner: handwritten
scope: login (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Login (OTP / password)

## TL;DR (1 min)
Email → OTP (or password). Rate-limited per IP+email. Pre-provisioned users only.

**URL** `accounts:login` (`/app/`) → step1 email; `accounts:verify_otp`; or
`accounts:login_password`. **View** `accounts/views.py:LoginView/VerifyOTPView/
PasswordLoginView`. **Forms** login/OTP forms (`accounts/forms.py`). **Service**
`auth_service` (OTP issue/verify). **Models read** User. **Models written**
session (+ OTP attempt counters in cache). **Tx** n/a (session). **RBAC** public,
RATE-LIMITED. **ADRs** — (security baseline). **Tables** — django_session; cache
(not DB) for rate limit. **Payload** `username=a@b.com` then `otp=123456`.
**Before→after** anonymous → authenticated session.

### How would I debug this in production?
- **First file:** `accounts/views.py` (LoginView/PasswordLoginView) + `auth_service.py`.
- **First breakpoint:** OTP verify / password `authenticate`.
- **First query/check:** cache rate-limit key per IP+email; `SELECT is_active FROM accounts_user WHERE email=…`.
- **First log:** the dedicated security log (auth events).
- **Failure modes:** "too many attempts" = rate limit (per IP+email); login refused = user not pre-provisioned / inactive; OTP expired.
- **Recovery:** owner resets password / re-provisions; rate-limit clears on TTL.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (accounts/urls.py routes, views.py classes). Auth internals: **Derived understanding** (read headers, not every line). Tests: accounts auth tests.
