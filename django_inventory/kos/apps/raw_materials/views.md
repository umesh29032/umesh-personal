---
id: app-raw-materials-views
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "raw_materials' 31 view classes in 5 modules — which file, which gates?"
related: [app-raw-materials, app-raw-materials-urls]
---

# raw_materials — handler knowledge (5 modules, 31 classes)

> 📂 [raw_materials app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## Handler groups at a glance

- **READ:** dashboard.py (2 boards) · list/detail views per family
- **WRITE:** roll_views.py (bulk-create 🔐SA, edit, damage) · assign_views.py (THE reservation) · master_views.py (3 CRUD families)
- **ADMIN:** bulk-add SA-only (MGT-A) · financial-field lanes (FINANCIAL_ROLES via form-strip + service re-gate)
- **DELETE:** masters only, PROTECT-guarded · **ASYNC:** none

## Module map

| Module | Owns |
|---|---|
| `mixins.py` | shared gates (management; SA where locked) |
| `dashboard.py` | the two derived-only boards |
| `roll_views.py` | registry, intake, edit (wall-in-action), damage |
| `assign_views.py` | the reservation POST — thin wrapper on the service's guards |
| `master_views.py` | types/colors/storage archive-first CRUD |

## The handlers that matter

**`RollAssignView`** — parses roll/adda/weight/width, everything else is
service law ([urls §8](urls.md)). **`RollUpdateView`** — the certified
financial-strip exemplar. **`RollDamageView`** — status + mandatory reason.
**`RollBulkCreateView`** — SA gate; row-wise validation.

## Handler rules of thumb

1. Status transitions never happen in views — verbs only.
2. Financial columns: template-hide is politeness; the strip + re-gate are
   the walls (don't "simplify").
3. Master CRUD: archive-first; deletes exist for the never-used case only.

## Required Knowledge (this page)

- [ ] The walls → [rbac-access](../../features/rbac-access.md)
- [ ] active-manager pickers → [orm-and-managers](../../concepts/django/orm-and-managers.md)

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [services.md](services.md) →
open `roll_service.py` with the reservation section beside it.
