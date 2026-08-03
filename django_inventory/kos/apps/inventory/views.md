---
id: app-inventory-views
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Which inventory view module do I open — including the middleware that runs on EVERY request?"
related: [app-inventory, app-inventory-urls]
---

# inventory — handler knowledge (8 view modules + the middleware)

> 📂 [inventory app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Views = **reception counter**
>
> Browser se request aati hai to sabse pehle yahin aati hai. View ka kaam sirf teen cheezein hai: **request padho → permission check karo → service ko bhej do**. View khud database mein likhta **nahi** — isiliye yeh files patli hoti hain. Moti view = design ki galti.
>
> *(`inventory` app ka kaam: admin ka hissa — roles, sidebar access, dashboards.)*

## Handler groups at a glance

- **READ:** dashboards (user_dashboard + tracking BarcodeDashboardView) · AccessControlHubView (matrices) · barcode list/print · Roll/Adda history · ExportListView
- **WRITE:** SidebarAccessListView (rules save) · Role Create/Update · scan_piece + update_piece_status · 3 export triggers (POST, manifest rows)
- **ADMIN (SA):** everything under roles/ + sidebar-access/ + access/ (SuperAdminOnly mixins)
- **DELETE:** RoleDeleteView only (guarded; roles in use protected)
- **ASYNC:** none (scan endpoints return JSON but are synchronous views)

## THE component that runs on every request — `middleware.py` (85 lines, read it)

`SidebarAccessMiddleware`: resolves `url_name` → if a `SidebarItemRule`
exists, enforce the SAME decision the menu used
(`accounts.can_access_url_name`). Denied → flash + redirect back (JSON
requests get a JSON 403). Pass-through: anonymous (LoginRequired's job) ·
unmanaged url_names (view mixins gate) · super admin · exempt dashboards
(loop prevention). **Additive defense: it never replaces view mixins.**
Debugging any access issue starts by classifying which lane a URL is in —
[access playbook](../../debugging/access-denied-or-invisible.md).

## Module map

| Module | Classes | Owns |
|---|---|---|
| `dashboard.py` | fns + ctx builders (~300 lines) | `user_dashboard` (role-aware home) + `dashboard_redirect`; worker badges via bulk queries |
| `mixins.py` | 3 | SuperAdminOnly / ManagerOrAdmin gates used across modules |
| `role_views.py` | 4 | Role CRUD (SA) — curated editor, generic CBVs |
| `sidebar_access_views.py` | 2 | `_SuperAdminOnly` + the rules editor (POST → sidebar_service) |
| `access_hub_views.py` | 1 | read-only RBAC matrices |
| `tracking_dashboard.py` | 1 + `barcode_export_csv` fn | scan overview + quick CSV |
| `tracking_barcodes.py` | 2 + 2 fns | list/print views · `scan_piece`/`update_piece_status` |
| `tracking_history.py` | 2 | Roll/Adda timelines (financial CHANGE rows stripped for workers) |
| `tracking_exports.py` | 6 | `_BaseExportTriggerView` → CSV/XLSX/PDF triggers · ReDownload · list (all ManagerOrAdmin; service refuses pre-barcode-gen) |

## Handler rules of thumb (this app)

1. Dashboard = every user's landing — changes here get seen by EVERYONE
   tomorrow morning; mobile-first check is non-negotiable.
2. The exempt-dashboard list in middleware exists to prevent redirect
   loops — extend it only for true landing pages.
3. Scan endpoints are phone-first + JSON-aware — keep responses tiny.
4. Export views share `_BaseExportTriggerView` — new formats subclass it,
   never fork the flow.
5. History views strip by audience — never "simplify" the strip away
   (wall #4, certified).

## Required Knowledge (this page)

- [ ] Middleware lifecycle → [request-through-stack](../../flows/request-through-stack.md)
- [ ] The pair + ONE-predicate laws → [rbac-access](../../features/rbac-access.md)
- [ ] Template-cache + N+1 dashboard lanes → [page-slow playbook](../../debugging/page-slow-or-erroring.md)

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [services.md](services.md) (the
trio) → open `middleware.py` — 85 lines, the best security read in the repo.
