---
id: apps-inventory-guide
type: app-guide
status: active
owner: handwritten
scope: inventory
anchors: config/inventory/
verified: 2026-07-13
---

# inventory app — file-by-file GUIDE (composition + access glue)

> Business view: [config/inventory/README.md](../../../config/inventory/README.md).
> Zero models (re-export shim). Naam legacy hai; kaam = dashboards + access.

| File | What |
|---|---|
| `middleware.py` | ★ SidebarAccessMiddleware — menu hidden ⇒ URL blocked |
| `context_processors.py` | sidebar data har template ko |
| `views/dashboard.py` | role-aware home (worker badges vs mgmt summary); R1 2026-07-04: worker-only "new Adda started" broadcast rows (read-only, no link — PDD §27-D6); R5 2026-07-05: management-only "Expenses · month" digest (1 aggregate via `expense_service.monthly_totals`, perf baseline 21 — PDD §21/§23, ADR-0011); **F-1 polish 2026-07-05: ONE live view `user_dashboard` (canonical url_name `inventory:my_dashboard`); old twin `dashboard()` → `dashboard_redirect` (301); both legacy url_names redirect there**; **C-2 freeze closeout 2026-07-05: ALL worker-facing visibility via ONE live `stage_access_map` call (access ∩ assignment) — accordions/`current_can_open`/MY-ACTIVE-STAGES filter/layering board; zero hardcoded skill constants; board assignment-scoped for non-mgmt** |
| `views/access_hub_views.py` + `role_views.py` + `sidebar_access_views.py` | Access-Control hub. **Worker-cert Phase D 2026-07-12: poora `/inventory/` surface (10 URLs) CERTIFIED, 0 bugs, 0 code changes — roles CRUD / sidebar-access / access hub sab SuperAdminOnly (mixin) + Administration `SidebarItemRule` rows roles=[] (manager bhi middleware-blocked); worker POSTs (role add/delete, sidebar-access save with valid CSRF) browser-proven inert; dashboard sweep zero-₹. Evidence: [docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md) Phase D** **Owner-cert OWN-D 2026-07-13: SA-side FUNCTIONAL cert — roles CRUD round-trip + guard quotes, sidebar-access M2M write → LIVE middleware flip proven (worker 302→200, rollback-wrapped), hub matrices render; SA-implicit invariant (POST handler excludes super_admin; `can_access_url_name` SA bypass) DB-proven. Evidence: [docs/OWNER_VISIBILITY_CERTIFICATION.md](../../OWNER_VISIBILITY_CERTIFICATION.md) §OWN-D** **RCP-1A F1 2026-07-18: POST ab parse-only — bulk M2M write `services/sidebar_service.save_sidebar_rules` mein (Law 4); behaviour byte-same (SA write-time exclusion preserved); pins `SidebarAccessSaveTests` ×3** |
| `services/sidebar_service.py` | ★ RCP-1A F1 (2026-07-18): THE SidebarItemRule role/skill-assignment writer — `save_sidebar_rules({rule_id: (role_ids, skill_ids)})`, service-owned `@transaction.atomic`, super_admin excluded at write (read-time wall `build_menu_for` mein bhi) |
| `forms/role_forms.py` | RoleForm — Roles editor ka form; `clean_code` = system-role code immutable. **⚠️ OWN-D-1 fix 2026-07-13: `permissions` field ka queryset ab `permissions_qs_by_app()` se (curated `ROLE_EDITOR_SECTIONS` content-type allowlist, 80 perms) — pehle app-level filter tha (216 perms) jisse hand-crafted POST service-only models ke grants (e.g. `production.change_machinetype`) persist kar sakta tha aur live gates unhe honor karte the (`user_has_perm` codename-match). Ab offered == validatable. Pins: `inventory.tests.RolePermissionCurationTests` ×2** |
| `views/tracking_*.py` (4) | /tracking/ surface (P4.2: views YAHAN, tracking app primitive rahe). **V1.1 Item 3 2026-07-12: exports (list/csv/xlsx/pdf/re-download in `tracking_exports.py` + legacy quick-CSV in `tracking_dashboard.py`) = `ManagerOrAdminMixin`/MANAGEMENT_ROLES — worker 403; list/print/scan PRODUCTION_ROLES rahe. Canonical: [docs/tracking/EXPORTS.md](../../tracking/EXPORTS.md).** **Worker-cert Phase C 2026-07-12: 13-URL tracking surface CERTIFIED (0 bugs, 0 code changes) — dashboard worker-blocked via SidebarAccessMiddleware+0018 (redirect+flash, browser-proven); history G-AUTH-1 + financial-strip hold; money metadata kabhi render nahi hota. Evidence: [docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md) Phase C** |
| `views/mixins.py` | RBAC gates (permission_service delegate) |
| `signals.py` | tombstone — kyon signals BANNED (padhna!) |
| `models.py` | Role/SidebarItemRule re-export (back-compat) |
| `urls.py` + `tracking_urls.py` | headers me route maps |

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
