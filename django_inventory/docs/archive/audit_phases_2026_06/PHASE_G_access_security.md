> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase G — Access Control & Security

**Method:** permission-probe matrices (worker3 / manager1) + code verification of the security core — `SidebarAccessMiddleware`, `permission_service` (roles), `StageViewAccessMixin`, `_ManagementOnly`, `_ProductionRoleMixin`, object-level checks. Findings separated into **Security risk / Authorization-design / UX inconsistency** as requested. Evidence-backed only.

---

## Verdict
**Authorization posture is genuinely strong.** No privilege-escalation path found; object-level isolation guards the money/work-critical surfaces; super-admin bypass is unified; login is rate-limited; the middleware closes the "hidden-menu-but-reachable-URL" gap. The real issues are **one missing object-isolation on history routes**, **one separation-of-duties design question**, and **denial-UX inconsistency** (two unrelated-looking denial paths). The only true *security* risk is deployment-config (DEBUG/tracebacks), not auth.

---

## 1. SECURITY RISK

**G-SEC-1 — DEBUG=True exposes full tracebacks (info disclosure if it reaches staging/prod).** *deployment / info-disclosure* · confidence HIGH
- Evidence: the settlement-start GET 500 (A-2) rendered a full Django debug page — stack trace, file paths, local frames. If `DEBUG` is ever True outside local, any 500 leaks internals.
- Fix: ensure staging/prod run `config.settings.production` (DEBUG off) + register `handler500/404/403`. Effort: **S** (deploy config + handlers). Cross-ref A-2, and G-UX-1 below.

**No auth-bypass / escalation found (verified):**
- Worker **cannot** set `verified_quantity` (management-gated in `AddaReportReviewView._gate`), **cannot** complete another worker's task (worker-report resolves the requester's own task or 403), **cannot** reach management pages (gated). Super-admin power is **unified** (`is_superuser` OR `super_admin` role — `user_service` removed the prior is_superuser/role divergence). No path to elevate role/skill from a worker session.

---

## 2. AUTHORIZATION / DESIGN ISSUE

**G-AUTH-1 — History routes lack object-level isolation (inconsistent with the dashboard).** *authorization* · confidence HIGH
- `AddaHistoryView` and `RollHistoryView` are gated by `_ProductionRoleMixin` = PRODUCTION_ROLES `{super_admin, manager, worker}` — a **role check with no "assigned-to-me" object check** ([tracking_history.py:34](config/inventory/views/tracking_history.py#L34)). Adda codes are predictable (`3-PATTI-001`…), so **any worker can view any Adda's / any roll's full history by URL**.
- Inconsistency: the dashboard explicitly isolates ("a worker sees ONLY Addas they're actively assigned to" — [dashboard.py:48](config/inventory/views/dashboard.py#L48)); the history route bypasses that principle.
- Exposure is **operational, not financial**: the template renders event type + actor email + timestamps + stage/roll details — **no settlement amounts** (verified: template has no `expected_total`/₹). So it leaks who-did-what + staff emails across Addas a worker isn't on, not money.
- Fix: apply the dashboard's assigned-Adda isolation to history (or make history management-only). Effort: **S–M**.

**G-AUTH-2 — Financial authority = management; the Accountant role can't touch settlements (separation-of-duties).** *authorization-design* · confidence HIGH
- All money pages (Payroll, Settlements, Advances, Worker-settle) gate on `_ManagementOnly` = `MANAGEMENT_ROLES {super_admin, manager}`. The **Accountant** role is NOT in MANAGEMENT_ROLES; `FINANCIAL_ROLES {super_admin, accountant}` gates only **cloth-roll supplier/cost_per_kg** fields ([permission_service.py:38](config/accounts/services/permission_service.py#L38), used in raw_materials). 
- Implications: (a) a **Manager has full payment authority** (settle + record advances + finalize) — no separation between operational management and money-out; (b) an **Accountant cannot access settlements/payroll** at all — its real scope is narrow (raw-material costing). So provisioning an "accountant" will NOT give them settlement access — likely contrary to the name's expectation.
- Confirm intended. For a small factory, management-settles may be fine; flag so the owner isn't surprised. Effort: **S** (decision) / **M** (if a finance-settlement role is wanted).

**G-AUTH-3 — Management bypasses the stage skill-gate (intended; confirm).** *authorization-design* · confidence HIGH
- `StageViewAccessMixin`: super-admin bypasses; skill/stage-role holders pass; **management (super_admin+manager) bypasses both the skill gate AND the per-stage assignment gate** ([mixins.py:37-39](config/production/views/mixins.py#L37)). This is why manager1 reached `cutting/workspace` (200) without the cutting_master skill — **by design** (managers oversee all stages), not a leak. Confirm this matches intent. No fix needed if intended.

---

## 3. UX INCONSISTENCY

**G-UX-1 — Two denial paths look completely different to the user.** *UX / consistency* · confidence HIGH (probe + code)
- Path A — `SidebarAccessMiddleware` (managed page URLs with a `SidebarItemRule`): denial → flash "You don't have access" + **redirect to the user's dashboard** (AJAX → clean JSON 403). Good UX, no loops. (Manager probe: `access`, `roles`, `stages`, `storefront` → redirect-to-dashboard.)
- Path B — view mixins (`_ManagementOnly`, `StageViewAccessMixin`, `_ProductionRoleMixin` via `UserPassesTestMixin`): denial → **bare unstyled Django "403 Forbidden"** (no app shell, no nav, no message) because **no `handler403` is registered**. (Manager probe: `products/add`, `stages/add`, `user-types`, `rolls/bulk-add` → bare 403.)
- Same user, same kind of action, two unrelated-looking denials. Plus the settlement-start **GET → 500** (A-2) is a third denial-adjacent failure mode.
- Fix: register a branded `handler403` (+ 404/500), or route view-mixin denials through the same flash+redirect as the middleware. Effort: **S–M**.

---

## Verified WORKS-WELL (security strengths — keep)
- **Object-level isolation** on the two critical surfaces: worker-report (own task or 403) and payroll detail ("You can only view your own payroll" unless management).
- **Unified super-admin** (`is_superuser` OR `super_admin` role) — prior divergence fixed in `user_service`.
- **`SidebarAccessMiddleware`** closes the hidden-menu-but-reachable-URL gap (defense-in-depth): exempts dashboards (no loops), super-admin allow, AJAX→403, page URLs re-checked.
- **Stage access** is skill-gated AND assignment-gated for non-management.
- **Login rate-limited per IP+email** (verified live — it throttled the audit twice). Strong brute-force control. Logout is POST-only.

---

## Net Phase G
Security is a strength — no escalation, good isolation on money/work, unified admin, rate limiting. Before staging: **G-SEC-1** (DEBUG off + error handlers) and **G-AUTH-1** (isolate history routes) are worth doing; **G-AUTH-2** (financial separation of duties) is an owner decision; **G-UX-1** (one consistent, branded denial) ties up the bare-403 loose end (and rides on the same `handler403` work as G-SEC-1).
