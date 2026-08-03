---
id: app-accounts
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm touching identity, login, roles, skills, or permissions — what does accounts own and where do I go?"
related: [concept-auth-hardening, project-people-and-roles, feature-rbac-access]
---

# accounts — the complete app map (the foundation layer)

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*

## Mental Model — read this before anything

> **The passport office + the gate policy.** It issues identity (users,
> OTP login), stamps capabilities (roles, skills), and WRITES the policy
> everyone else enforces (permission_service, SidebarItemRule). It guards
> its own front door ferociously (throttles, uniform answers) — because
> every other wall in the system assumes THIS office told the truth.
> *(Pehchaan yahan banti hai; baaki sab isi par bharosa karte hain.)*

## Common Misconceptions

- **"Anyone can sign up."** NO public signup route exists — S2 closed it;
  users exist only via superuser creation ([urls.md](urls.md) §absence).
- **"Email change is a profile edit."** The email-change route was REMOVED
  (S3: identifier takeover) — `EmailManagementDisabledView` is a deliberate
  stub. Identifier changes = guarded admin lane only.
- **"Roles/permissions logic is scattered."** ONE brain: `permission_service`
  (role sets, `user_has_role`, `can_access_url_name`) — every app consults it.
- **"OTP is a fallback."** OTP is the PRIMARY login; password is the fallback lane.
- **"Skills are permissions."** Skills gate production STAGES
  (access_service uses them); permissions/roles gate everything else —
  three concepts ([people-and-roles](../../project/people-and-roles.md)).

## Real Engineering Questions

**PM: "Lock accounts after 5 failed logins."**
Chain: throttle already counts per-IP+email (`throttle.py`) → lockout
semantics live in auth flows → self-lockout protection is a REQUIREMENT
(recovery lane) → uniform responses preserved (no oracle) → 37-test suite
extends. → [auth-hardening](../../concepts/security/auth-hardening.md).

**PM: "Add Google login for managers."**
allauth adapter exists (`allauth_adapters.py`) — the S2 lesson applies:
any new identity path gets the FULL guard set (throttle, uniform, no
auto-signup) + refusal pins before it ships.

**PM: "Why can't I change my email?"**
The S3 story — read [urls.md](urls.md) §email-absence; the answer is a
security decision with a receipt, not a missing feature.

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §§1–5 (the login story) →
  [auth-hardening](../../concepts/security/auth-hardening.md).
- **Intermediate:** §§8–20 (admin CRUD lanes) → [services.md](services.md).
- **Senior:** the two ABSENCES (§signup, §email) → throttle design →
  [models.md](models.md) Role/SidebarItemRule custody.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Change login/OTP behavior | [urls.md](urls.md) §§1–4 → `views.py` flows + `utils.py` OTP helpers |
| Adjust rate limits | [services.md](services.md) §throttle (cache-backed, per-IP+email) |
| Add/edit roles, role sets | [services.md](services.md) `permission_service` (SETS ARE CODE) + role UI in [inventory §5](../inventory/urls.md) |
| User admin | [urls.md](urls.md) §§8–11 (superuser-only CRUD) |
| Skills / user types | §§12–20 masters |
| Debug a 403/visibility issue | [access playbook](../../debugging/access-denied-or-invisible.md) |
| Security review anything here | [auth-hardening](../../concepts/security/auth-hardening.md) + the 37-test suite (`tests.py`) |

## What this app owns

Identity (custom user flows, OTP login, password fallback, reset) ·
authorization POLICY (`permission_service` role sets + URL policy,
`Role` + `SidebarItemRule` models — custody since 2026-06) · skills +
user-type masters · auth hardening (throttle, uniform responses, no-cache)
· the allauth adapter (locked down).

## What it does NOT own

ENFORCEMENT surfaces — inventory's middleware/menus enforce what this app
decides · stage-level access (production's access_service composes skills
∩ assignment) · role admin UI (inventory hosts it; models live here).

## The census

- **URLs:** 20 (`config/accounts/urls.py`, 74 lines) — every one in [urls.md](urls.md)
- **Views:** ~26 classes in one `views.py` (auth flows + superuser CRUD) — [views.md](views.md)
- **Models:** custom user domain + `Role` + `SidebarItemRule` + skills/user-types — [models.md](models.md)
- **Services:** `permission_service` · `auth_service` · `user_service` (+ `throttle.py`, `utils.py`, `forms.py`, `allauth_adapters.py`) — [services.md](services.md)
- **Tests:** 37 security tests in `tests.py` (argon2, throttle, lockout, anti-enum, email-case, no-cache…)

## The laws to carry in

1. **No new identity paths without the full guard set** (S2/S3 scars):
   throttle + uniform answers + no-cache + refusal pins.
2. **Role sets are CODE constants** in permission_service — adding a role
   to a SET is a reviewed code change, not a row edit.
3. Uniform responses everywhere — the oracle is the DIFFERENCE.

## Engineering Checklist — pre-flight

- [ ] New/changed route touching identity? Full guard set + a refusal pin (the 37 grow, never shrink)
- [ ] Response messages IDENTICAL for exists/doesn't-exist lanes
- [ ] Throttle keys cover the new path (per-IP AND per-email)
- [ ] Role-set change? grep every `user_has_role` consumer first
- [ ] Superuser-only lanes: `SuperuserRequiredMixin` here (NOTE: this app
      predates permission_service's role sets for its own CRUD — it gates by
      Django superuser; consistent with SA-bypass, but know the difference)
- [ ] kos-sync: this app + people-and-roles/rbac-access if the model changed

## Change Impact — touching this app affects

**Everything.** Login = every user's entry; permission_service = every
gate in every app; SidebarItemRule = every menu + managed URL; skills =
production stage visibility. Plus: certifications (role matrices),
middleware behavior, the 37-pin suite. Treat this app like the ledger —
smallest possible diffs, hostile review mindset.

## Learning Graph

**Before:** [people-and-roles](../../project/people-and-roles.md) →
[auth-hardening](../../concepts/security/auth-hardening.md).
**After:** [rbac-access](../../features/rbac-access.md) (enforcement) →
[inventory's trio](../inventory/services.md) → the access playbook.
