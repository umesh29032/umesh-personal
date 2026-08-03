---
id: app-accounts-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "permission_service, auth_service, user_service, throttle — the decision brain everyone consults."
related: [app-accounts, concept-auth-hardening]
---

# accounts — service knowledge (the decision brain)

> 📂 [accounts app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`accounts` app ka kaam: log-in, users, roles aur **skills** — kaun andar aa sakta hai aur kaun kaunsa kaam kar sakta hai.)*

## `permission_service.py` — THE authorization brain 🔒

Owns: role constants + ROLE SETS (`ADMIN_ROLES`, `MANAGEMENT_ROLES`,
`FINANCIAL_ROLES`, `PRODUCTION_ROLES`) · `user_has_role` / `user_has_perm`
· `can_access_url_name` (the sidebar-pair decision the middleware
enforces) · financial-visibility helpers.
**Callers:** EVERY app (house rule 6: no raw `is_superuser` in views).
**The design:** decisions computed fresh per request — no caching layer,
so a role edit applies on the next click (correctness over micro-perf;
the queries are lean by design).
**Change protocol:** adding a role to a SET = code review + re-run the
certification mindset (role matrices).

## `auth_service.py` — OTP issuance

`issue_otp(request, email, prefix, subject)` — throttle-checked, hashed,
single-use, expiring; uniform behavior regardless of account existence.
Used by login + reset + (historically) signup flows.

## `user_service.py` — identity lifecycle verbs

User create/update plumbing for the superuser CRUD (role+skills
assignment in one place — the birthplace verbs).

## `throttle.py` — the cache-backed rate limiter (no external deps)

Counter-with-TTL keys per (action, IP) AND (action, email) — dual keys
close both the botnet and the single-target bypass. Self-lockout
protection: recovery lanes keep working. Backed by LocMem in dev, Redis in
prod ([tech-stack](../../project/tech-stack.md)) — losing it loses only
counters. DSA note: the simplest limiter (fixed window) is the RIGHT one
for auth ([auth-hardening §10](../../concepts/security/auth-hardening.md)).

## Support modules

`utils.py` (OTP generate/hash/session helpers, email send) · `forms.py`
(auth forms; strip-don't-trust) · `allauth_adapters.py` (the locked
adapter — no auto-signup; the S2 fix's second half) · `skills.py` (skill
helpers).

## Adding/changing here — the checklist

Any auth-flow change → the 37-test suite grows (attack-as-test) · any
role-set change → grep consumers → uniform-response review → kos-sync
(this app + people-and-roles + rbac-access).

## Required Knowledge (this page)

- [ ] Three-surface hardening → [auth-hardening](../../concepts/security/auth-hardening.md)
- [ ] Where enforcement lives (inventory trio) → [inventory services](../inventory/services.md)

## Learning Graph

**Before:** [models.md](models.md). **After:**
[rbac-access](../../features/rbac-access.md) → the access playbook →
open `permission_service.py` (the most-consulted file in the repo).
