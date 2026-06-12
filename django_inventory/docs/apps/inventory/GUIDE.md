# inventory app — file-by-file GUIDE (composition + access glue)

> Business view: [config/inventory/README.md](../../../config/inventory/README.md).
> Zero models (re-export shim). Naam legacy hai; kaam = dashboards + access.

| File | What |
|---|---|
| `middleware.py` | ★ SidebarAccessMiddleware — menu hidden ⇒ URL blocked |
| `context_processors.py` | sidebar data har template ko |
| `views/dashboard.py` | role-aware home (worker badges vs mgmt summary) |
| `views/access_hub_views.py` + `role_views.py` + `sidebar_access_views.py` | Access-Control hub |
| `views/tracking_*.py` (4) | /tracking/ surface (P4.2: views YAHAN, tracking app primitive rahe) |
| `views/mixins.py` | RBAC gates (permission_service delegate) |
| `signals.py` | tombstone — kyon signals BANNED (padhna!) |
| `models.py` | Role/SidebarItemRule re-export (back-compat) |
| `urls.py` + `tracking_urls.py` | headers me route maps |

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
