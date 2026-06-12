# accounts app — file-by-file GUIDE (identity + RBAC foundation)

> Business view: [config/accounts/README.md](../../../config/accounts/README.md).

| File | What |
|---|---|
| `models.py` | custom User (email login) · Role(+extra_roles M2M) · SidebarItemRule (RBAC relocated here 2026-06 — foundation owns access) |
| `services/permission_service.py` | ★ user_has_perm/_has_role + MENU REGISTRY (sidebar declarative; menu+URL ek saath gate) |
| `services/auth_service.py` | OTP issuance |
| `services/user_service.py` | user-provisioning invariants (no signals) |
| `views.py` | FILE MAP at top: OTP login/verify · user CRUD · rate-limited password login · signup(pre-provisioned) · reset |
| `urls.py` | mounted at /app/ |
| templates/accounts/ | base.html ★ (THE design system: tokens, components, money-family canonicals) + auth pages |

Foundation-purity: core+accounts import NO domain app (CI gate 1/4).
Dots: har request → middleware(sidebar rules) → permission_service → view.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
