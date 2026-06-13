# accounts — REQUEST_MAP (`/app/`)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

| URL | View | Service | Writes |
|---|---|---|---|
| login / verify-otp / resend-otp | Login/VerifyOTP/ResendOTP | auth_service (OTP) | session |
| login/password | PasswordLoginView | Django auth + rate limit | session |
| signup/* | Signup* | auth_service (pre-provisioned) | User activate |
| forgot/reset | ForgotPassword/ResetVerify | auth_service | password |
| users/* | User CRUD | user_service | User |
| skills/*, user-types/* | Skill/UserType CRUD | permission_service | Role/Skill/UserType |
Gate: super-admin for management; auth+rate-limit for auth flows.

---
*Depth: [config/accounts/README.md](../../../../config/accounts/README.md) (business) ·
[docs/apps/accounts/GUIDE.md](../../../apps/accounts/GUIDE.md) (file-by-file). This = navigation/flow only.*
