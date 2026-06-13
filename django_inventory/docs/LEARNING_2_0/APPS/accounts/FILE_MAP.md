# accounts — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — **User** (custom, email login, AUTH_USER_MODEL), **Role**(+extra_roles M2M),
**SidebarItemRule** (RBAC relocated here 2026-06 so identity+access = one foundation).
## services/ — `permission_service.py` ★ (user_has_perm/_has_role + MENU REGISTRY,
ROLE_SUPER_ADMIN bypass) · `auth_service.py` (OTP issuance) · `user_service.py`
(provisioning invariants, no signals).
## views.py — FILE MAP at top: auth (OTP login/verify/logout), user CRUD,
rate-limited password login, pre-provisioned signup, OTP reset.
## forms.py — login/signup/user/reset forms. urls.py — mounted /app/. admin.py — 2 admins.
## templates/accounts/ — **base.html ★** (THE design system: tokens, components,
money-family canonicals, stacked-table CSS) + auth pages.
## tx/security — Argon2 hasher; cache rate-limit per IP+email on every auth endpoint;
self-lockout protection; allauth restricted to pre-provisioned.

---
*Depth: [config/accounts/README.md](../../../../config/accounts/README.md) (business) ·
[docs/apps/accounts/GUIDE.md](../../../apps/accounts/GUIDE.md) (file-by-file). This = navigation/flow only.*
