# inventory — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Composition + access glue. ZERO models (legacy name). Dashboards, Access hub,
> sidebar gating, /tracking/ surface.
## Flow 1 — Sidebar gate: request → SidebarAccessMiddleware → menu item hidden ⇒
its URL ALSO blocked (one rule source: SidebarItemRule).
## Flow 2 — Dashboard: role-aware home (worker: active stages + report badges;
management: ops summary). Worker isolation = own active tasks only.
## Flow 3 — Access Control hub: super-admin edits roles/skills/per-user + sidebar rules.

---
*Depth: [config/inventory/README.md](../../../../config/inventory/README.md) (business) ·
[docs/apps/inventory/GUIDE.md](../../../apps/inventory/GUIDE.md) (file-by-file). This = navigation/flow only.*
