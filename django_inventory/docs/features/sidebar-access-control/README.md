---
id: feature-sidebar-access-control
type: feature-doc
status: generated
owner: generated
scope: feature — sidebar-access-control
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Sidebar/access control

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `sidebar-access-control` |
| Label | Sidebar/access control |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `inventory:access-control` | `/inventory/access/` | `AccessControlHubView` | [access-control.md](access-control.md) |
| `inventory:role_add` | `/inventory/roles/add/` | `RoleCreateView` | [role_add.md](role_add.md) |
| `inventory:role_delete` | `/inventory/roles/<int:pk>/delete/` | `RoleDeleteView` | [role_delete.md](role_delete.md) |
| `inventory:role_edit` | `/inventory/roles/<int:pk>/edit/` | `RoleUpdateView` | [role_edit.md](role_edit.md) |
| `inventory:role_list` | `/inventory/roles/` | `RoleListView` | [role_list.md](role_list.md) |
| `inventory:sidebar-access` | `/inventory/sidebar-access/` | `SidebarAccessListView` | [sidebar-access.md](sidebar-access.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `accounts.Role` | `accounts_role` | not machine-known |
| `accounts.SidebarItemRule` | `accounts_sidebaritemrule` | not machine-known |

## Apps touched

- `inventory` — [config/inventory/README.md](../../../config/inventory/README.md) · [docs/apps/inventory/GUIDE.md](../../apps/inventory/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
