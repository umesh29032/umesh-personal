---
id: feature-user-role-admin
type: feature-doc
status: generated
owner: generated
scope: feature — user-role-admin
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — User/role admin

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `user-role-admin` |
| Label | User/role admin |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `accounts:skill_add` | `/app/skills/add/` | `SkillCreateView` | [skill_add.md](skill_add.md) |
| `accounts:skill_delete` | `/app/skills/<int:pk>/delete/` | `SkillDeleteView` | [skill_delete.md](skill_delete.md) |
| `accounts:skill_edit` | `/app/skills/<int:pk>/edit/` | `SkillUpdateView` | [skill_edit.md](skill_edit.md) |
| `accounts:skill_list` | `/app/skills/` | `SkillListView` | [skill_list.md](skill_list.md) |
| `accounts:user_add` | `/app/users/add/` | `UserCreateView` | [user_add.md](user_add.md) |
| `accounts:user_delete` | `/app/users/<int:pk>/delete/` | `UserDeleteView` | [user_delete.md](user_delete.md) |
| `accounts:user_edit` | `/app/users/<int:pk>/edit/` | `UserUpdateView` | [user_edit.md](user_edit.md) |
| `accounts:user_list` | `/app/users/` | `UserListView` | [user_list.md](user_list.md) |
| `accounts:usertype_add` | `/app/user-types/add/` | `UserTypeCreateView` | [usertype_add.md](usertype_add.md) |
| `accounts:usertype_delete` | `/app/user-types/<int:pk>/delete/` | `UserTypeDeleteView` | [usertype_delete.md](usertype_delete.md) |
| `accounts:usertype_edit` | `/app/user-types/<int:pk>/edit/` | `UserTypeUpdateView` | [usertype_edit.md](usertype_edit.md) |
| `accounts:usertype_list` | `/app/user-types/` | `UserTypeListView` | [usertype_list.md](usertype_list.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `accounts.Role` | `accounts_role` | not machine-known |
| `accounts.User` | `accounts_user` | not machine-known |

## Apps touched

- `accounts` — [config/accounts/README.md](../../../config/accounts/README.md) · [docs/apps/accounts/GUIDE.md](../../apps/accounts/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
