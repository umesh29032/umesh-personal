---
id: app-inventory-models
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Why is inventory/models.py only 15 lines — and where did Role and SidebarItemRule actually go?"
related: [app-inventory, feature-rbac-access]
---

# inventory — model knowledge (a shim, and the lesson inside it)

> 📂 [inventory app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Models = **database ke tables**
>
> Yeh file batati hai is app mein **kaunsi cheezein store hoti hain** aur har cheez ke kaunse column hain. Socho Excel ki sheets ki list — kaunsi sheet, aur usme kaunse columns. Code mein ek `class` = ek table.
>
> *(`inventory` app ka kaam: admin ka hissa — roles, sidebar access, dashboards.)*

## The whole file (15 lines)

`config/inventory/models.py` = a **re-export shim**:

```python
from accounts.models import Role, SidebarItemRule  # noqa: F401
__all__ = ['Role', 'SidebarItemRule']
```

## Why (the 2026-06 relocation — worth understanding, it's an interview story)

`Role` + `SidebarItemRule` began life here because the ADMIN UI lives here.
But identity + access control is a FOUNDATION — every app depends on it,
and it must depend on nothing domain-specific. Living in inventory created
an upward dependency (domain apps importing the UI-shell app). Fix:
**models moved to `accounts`** (the true foundation layer), while inventory
kept what it genuinely owns — the admin SURFACES (role editor, sidebar
editor, hub), the middleware, the context processor. The shim keeps every
old `from inventory.models import Role` call-site working unchanged —
rename-not-break, the same staging discipline as
[migrations](../../concepts/django/migrations.md) rename-not-drop.

## Where the real models live

| Model | Home | What it is |
|---|---|---|
| `Role` | `config/accounts/models.py` | the Role FK = RBAC source of truth (super_admin bypass; curated editor here in inventory) |
| `SidebarItemRule` | `config/accounts/models.py` (~line 260) | ONE row per managed url_name: which roles/skills see the menu item AND may hit the URL — the pair |

Writers: `sidebar_service.save_sidebar_rules` (rules) ·
role views (Role CRUD, SA). Readers: the middleware + context processor on
EVERY request — keep these queries lean.

## The lesson to keep

When a model's OWNER app and its UI app differ, the model belongs with the
foundation, the UI stays where users find it, and a shim buys you a
zero-break migration. *(Model neenv ke saath, UI darwaze ke saath, shim
purani chaabiyon ke liye.)*

## Evolution Timeline (the relocation, explicitly)

Originally: `Role` + `SidebarItemRule` born in inventory (the admin UI was
here) → *problem discovered:* domain apps importing the UI-shell app —
an upward dependency; identity/access is FOUNDATION → *refactor (2026-06):*
models → `accounts`; inventory keeps surfaces + middleware + processor;
15-line re-export shim keeps every old import alive → *current:* clean
downward dependencies; shim still standing (harmless) → *future:* the shim
retires whenever a sweep updates the last old-style import — zero urgency,
zero risk.

## Required Knowledge (this page)

- [ ] App-dependency direction / layering → [system-map](../../project/system-map.md)
- [ ] Rename-not-break staging → [migrations](../../concepts/django/migrations.md)

## Learning Graph

**Before:** [README](README.md) why-separate. **After:**
[services.md](services.md) — the machinery that consumes these models on
every request.
