---
id: feature-login
type: feature-doc
status: generated
owner: generated
scope: feature — login
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Login (OTP/password)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `login` |
| Label | Login (OTP/password) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `accounts:forgot_password` | `/app/forgot-password/` | `ForgotPasswordView` | [forgot_password.md](forgot_password.md) |
| `accounts:home` | `/app/home/` | `HomeView` | [home.md](home.md) |
| `accounts:login` | `/app/` | `LoginView` | [login.md](login.md) |
| `accounts:login_password` | `/app/login/password/` | `PasswordLoginView` | [login_password.md](login_password.md) |
| `accounts:logout` | `/app/logout/` | `LogoutView` | [logout.md](logout.md) |
| `accounts:resend_otp` | `/app/resend-otp/` | `ResendOTPView` | [resend_otp.md](resend_otp.md) |
| `accounts:reset_password_verify` | `/app/reset-password/verify/` | `ResetPasswordVerifyView` | [reset_password_verify.md](reset_password_verify.md) |
| `accounts:verify_otp` | `/app/verify-otp/` | `VerifyOTPView` | [verify_otp.md](verify_otp.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `accounts.User` | `accounts_user` | not machine-known |

## Apps touched

- `accounts` — [config/accounts/README.md](../../../config/accounts/README.md) · [docs/apps/accounts/GUIDE.md](../../apps/accounts/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
