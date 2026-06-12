# `inventory` app — Dashboards, Access Hub & Glue (no tables of its own)

> Dual-register guide. RBAC truth: [docs/production/RBAC.md](../../docs/production/RBAC.md) ·
> [ADR-0003](../../docs/adr/0003-three-concept-rbac-skill-gated-stages.md).

## Purpose & business responsibility

Historical naam "inventory" hai, par aaj yeh app **composition + access** ka
ghar hai: dashboards (owner/manager/worker views), the Access Control hub,
role editor, sidebar gating middleware, and the tracking-section views.
**Zero models** — `Role`/`SidebarItemRule` relocated to `accounts` (2026-06);
`inventory/models.py` sirf re-export karta hai taaki purane imports na tootein.

## What tables are created

None. (Re-exports only.) `signals.py` is an intentional tombstone explaining
WHY signals are banned (ADR-0001) — padho, samajh aa jayega.

## How data flows through this app

```
request → SidebarAccessMiddleware (menu item hidden ⇒ its URL ALSO blocked)
        → view (dashboard/access-hub/tracking section)
        → reads via services (permission_service, payroll_service, models' read helpers)
        → renders. WRITES: none of its own — role edits call accounts services.
```

**Why this design:** menu and URL gating share ONE rule source
(`SidebarItemRule`) — "dikh nahi raha to khul bhi nahi sakta." Worker
dashboard isolation: own active stages via
`filter(worker_tasks__worker=user, status__in=ACTIVE)` — assignment truth,
skill alone is not enough (V2-1c-iv).

**What breaks if bypassed:** a view added without a sidebar rule is reachable
by URL while invisible in menus — the whitelist bug class (fixed 2026-06-02);
always register the rule.

## Views (the interesting ones)

`views/dashboard.py` — role-aware home (worker: active Addas + report badges;
management: ops summary) · `views/access_hub_views.py` + `role_views.py` —
Access Control hub (roles, skills, per-user) · `views/sidebar_access_views.py`
— menu/URL rules · `views/tracking_*` — barcode dashboard/export/history
sections · `middleware.py` — the URL-enforcement half of the sidebar.

## Common mistakes

1. No raw `is_superuser` checks — `permission_service` only (rule 6).
2. New menu item without `SidebarItemRule` = unprotected URL.
3. Don't resurrect signals here; the tombstone stays.

## Django Learning Notes

- **Middleware**: ek hi jagah pe har request ka gate — yahan sidebar rules
  URL-enforcement bante hain.
- **Context processors** (`context_processors.sidebar`): har template ko
  menu data automatically — views ko repeat nahi karna padta.
- **Re-export shim** (`inventory/models.py`): refactor ke baad backward
  compatibility ka sasta tareeka — imports kaam karte rehte hain jab tak
  call-sites migrate na ho jayein.

## Related ADRs: 0001 (no signals) · 0003 (RBAC).

## Real factory example

Worker Two login karta hai → middleware sidebar rules check → usse sirf
Dashboard + My Earnings dikhta hai → dashboard pe "● Report needed" badge
(uske ACTIVE task se) → tap → report screen. Manager wahi URL kholta hai to
poora ops view — same app, role-aware composition.
