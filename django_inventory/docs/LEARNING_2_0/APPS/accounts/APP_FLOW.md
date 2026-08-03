---
id: l2-apps-accounts-app-flow
type: topic-canonical
status: active
owner: handwritten
scope: accounts
anchors: config/accounts/
verified: 2026-07-13
---

# accounts — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Identity + access. Foundation: core+accounts import NO domain app (CI gate 1/4).
## Flow 1 — Login: email → OTP (or password) → session. Rate-limited per IP+email.
## Flow 2 — Access: every request → permission_service.user_has_perm/_has_role
+ SidebarItemRule (menu hidden ⇒ URL blocked, via inventory middleware).
## Flow 3 — User admin: super-admin creates pre-provisioned users + roles/skills.
No open signup. No signals (writes in services).

---
*Depth: [config/accounts/README.md](../../../../config/accounts/README.md) (business) ·
[docs/apps/accounts/GUIDE.md](../../../apps/accounts/GUIDE.md) (file-by-file). This = navigation/flow only.*
