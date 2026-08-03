---
id: app-accounts-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Any accounts URL — login, OTP, reset, users, skills, user-types — plus the two routes that are FAMOUSLY absent."
related: [app-accounts]
---

# accounts — URL Learning Pages (all 20, individually — plus 2 absences)

> 📂 [accounts app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Source: `config/accounts/urls.py` (74 lines). Every auth endpoint is
> RATE-LIMITED; responses are UNIFORM (anti-enumeration). Admin lanes are
> Django-superuser gated (`SuperuserRequiredMixin`).

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`accounts` app ka kaam: log-in, users, roles aur **skills** — kaun andar aa sakta hai aur kaun kaunsa kaam kar sakta hai.)*

**Reading Strategy** — *Beginner:* §§1–5 (the login story in order).
*Intermediate:* §§6–7 (reset pair) → §§8–11 (user admin). *Senior:* the two
**absences** at the bottom — the S2/S3 security stories.

## The login story (§§1–5)

### 1. `/accounts/` — `login`
**Purpose:** step 1 of OTP-first login — email entry.
**Why OTP-first:** factory reality — shared devices, no password reuse
risk, inbox = existing root of trust ([auth-hardening §5](../../concepts/security/auth-hardening.md)).
**Method:** GET form / POST email → `LoginView` (`views.py:76`).
**Guards:** `otp_send` throttle (per-IP + per-email) · uniform response
whether the email exists or not (no oracle) · no-cache headers.
**Journey:** POST → throttle check → (if user exists) hashed OTP stored +
emailed (dev: printed to console) → EITHER WAY "check your email" → §2.
**Failure modes:** throttled (429-class message) — same message shape regardless.
**Tests:** throttle + anti-enum pins in the 37.

### 2. `verify-otp/` — `verify_otp`
**Purpose:** step 2 — the 6-digit code.
**Method:** GET/POST → `VerifyOTPView` (:159).
**Guards:** verify-throttle (10⁶ space needs attempt limits) · single-use ·
expiry · session-bound (the email from step 1).
**Failure modes:** wrong/expired code (uniform wording) · too many attempts.
**Why simple-looking, hard-earned:** every guard here is an attack that
works elsewhere.

### 3. `resend-otp/` — `resend_otp`
**Purpose:** resend without restarting. **Method:** POST → `ResendOTPView` (:128).
**Guard:** its own throttle key (resend-abuse = its own budget).
**Why separate from §1:** separate budgets — restarting login shouldn't
reset resend limits (throttle-key design lesson).

### 4. `login/password/` — `login_password`
**Purpose:** the password FALLBACK lane (Argon2-verified).
**Method:** GET/POST → `PasswordLoginView` (:422, extends Django's LoginView).
**Guards:** login throttle · Argon2-first hashers (transparent upgrades) ·
mixed-case email lesson applied (lockout keys normalized).
**Misconception guard:** this is the fallback; OTP is primary.

### 5. `home/` — `home` · and `logout/` — `logout`
**`home`:** post-login bounce → inventory dashboard (`HomeView` :263) —
one-line view; the dashboard question belongs to inventory.
**`logout`:** **POST-only** (`LogoutView` :218) — GET logout = CSRF-able
logout (a real attack class). Learn from the method restriction.

## The reset pair (§§6–7)

### 6. `forgot-password/` — `forgot_password`
**Method:** GET/POST → `ForgotPasswordView` (:598). Same anti-enum law:
the response NEVER reveals whether the account exists (the certified
enumeration probe class). Throttled.

### 7. `reset-password/verify/` — `reset_password_verify`
**Method:** GET/POST → `ResetPasswordVerifyView` (:637). Token/OTP-verified
reset; single-use; then Argon2 re-hash.
**Together §§6–7 teach:** the reset lane must be as hardened as login —
attackers pick the SOFTEST identity path (the S3 principle).

## User admin (§§8–11, superuser-only)

### 8. `users/` — `user_list` · 9. `users/add/` — `user_add` · 10. `users/<pk>/edit/` — `user_edit` · 11. `users/<pk>/delete/` — `user_delete`
**Shared context:** `SuperuserRequiredMixin` CRUD (`views.py:286–421`);
**§9 is THE ONLY way users come into existence** (S2 closed public signup).
Each individually:
- **§8 list** — census view; roles/skills visible.
- **§9 add** — creates identity: email + role + skills; the birthplace of
  every account. Failure modes: duplicate email (uniform-ish admin context).
- **§10 edit** — role/skill changes ripple to every gate on next request
  (no decision caching, deliberate).
- **§11 delete** — guarded: users anchoring money/history rows are
  PROTECTed — deactivate, don't delete ([orm-and-managers](../../concepts/django/orm-and-managers.md) soft-archive thinking).

## Skills + user types (§§12–20, superuser-only masters)

*Skills — the SKILL axis of the three-concept model; a skill edit changes
STAGE VISIBILITY across production ([rbac-access](../../features/rbac-access.md)).
All superuser CRUD, `views.py:707–765`. Each route:*

### 12. `skills/` — `skill_list`
GET → `SkillListView` (:707). The capability census.

### 13. `skills/add/` — `skill_add`
GET+POST → `SkillCreateView` (:714). New skill → assignable to users AND
selectable on Stage access rules — two consumers per row.

### 14. `skills/<pk>/edit/` — `skill_edit`
GET+POST → `SkillUpdateView` (:725). Rename ripples everywhere (referenced,
never copied).

### 15. `skills/<pk>/delete/` — `skill_delete`
POST → `SkillDeleteView` (:736). Guarded when referenced by stages/users —
retire by un-assigning first.

*User types — classification master, rows-not-code
([pattern](../../concepts/patterns/configuration-over-code.md)); `views.py:766–806`:*

### 16. `user-types/` — `usertype_list`
GET → `UserTypeListView` (:766).

### 17. `user-types/add/` — `usertype_add`
GET+POST → `UserTypeCreateView` (:773).

### 18. `user-types/<pk>/edit/` — `usertype_edit`
GET+POST → `UserTypeUpdateView` (:784).

### 19. `user-types/<pk>/delete/` — `usertype_delete`
POST → `UserTypeDeleteView` (:795). Guarded delete, same law as every master.

## THE TWO ABSENCES (the best security teaching in this app)

### ∅ No public signup route
`SignupView`/`SignupVerifyView`/`ResendSignupOTPView` EXIST in views.py
(:467–597) but **no urls.py row points at them** — S2: public allauth
signup was creating live users; the route was removed, the views kept as
history + the adapter locked. **Learn:** closing a door = removing the
ROUTE and pinning the refusal (tests assert 404), not hiding the link.

### ∅ No email-change route
`EmailManagementDisabledView` (:234) exists as a deliberate DISABLED stub —
S3: the email-change path allowed identifier takeover. **Learn:** every
writer of a security-critical field gets the full guard set or gets
REMOVED; the stub documents the decision in code.

## Learning Graph (this page)

**Before:** README Mental Model. **After:** [views.md](views.md) →
[services.md](services.md) → the 37 tests (`config/accounts/tests.py`) —
each one is an attack that now fails.
