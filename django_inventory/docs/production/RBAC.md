---
id: production-rbac
type: topic-canonical
status: active
owner: handwritten
scope: access control — roles, skills, sidebar/URL enforcement, visibility law
anchors: config/accounts/services/permission_service.py, config/inventory/middleware.py
verified: 2026-07-13
---

# RBAC — Production Tracking Roles & Gating

Reuses existing `accounts.services.permission_service` (CLAUDE.md rule #6; auth family consolidated into accounts). No raw `is_superuser` checks anywhere.

## Role additions

```python
# accounts/services/permission_service.py — additive
ROLE_ACCOUNTANT = 'accountant'

ADMIN_ROLES      = {ROLE_SUPER_ADMIN}
MANAGEMENT_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER}
FINANCIAL_ROLES  = {ROLE_SUPER_ADMIN, ROLE_ACCOUNTANT}   # view + edit Supplier, Cost Per KG
PRODUCTION_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER}  # ROLE_WORKER == 'worker' (renamed from ROLE_KARIGAR/'karigar' 2026-06-02)
```

Super Admin keeps universal visibility — every role set includes `ROLE_SUPER_ADMIN`.

## What each role can do

> Table rebuilt 2026-07-13 (Phase-7 Q-A8, backlog #6) from the CERTIFIED gate matrix:
> [MANAGEMENT_ROLE_CERTIFICATION](../MANAGEMENT_ROLE_CERTIFICATION.md) MGT-A/E ·
> [WORKER_ROLE_CERTIFICATION](../WORKER_ROLE_CERTIFICATION.md) (incl. final meta-audit) ·
> [OFFICE_SUPPORT_ROLE_CERTIFICATION](../OFFICE_SUPPORT_ROLE_CERTIFICATION.md) OFF-A (D1
> add-on model). The old table predated the master-data lockdown (product CRUD + roll
> bulk-add are SuperAdmin-only in code).

| Role | Cloth dashboard | Roll bulk add | Adda CRUD | Stage advance | Supplier / Cost per KG | Product CRUD |
|---|---|---|---|---|---|---|
| `super_admin` | view | **yes (SA-only)** | yes | yes | view + edit | **yes (SA-only)** |
| `manager` | view | **no** (SuperAdminOnly, MGT-A) | yes | yes | hidden (service re-gate proven, OFF-C) | **no** (SuperAdminOnlyMixin: add/edit/archive/sizes/flow, MGT-A) |
| `worker` (was `karigar`) | **no** (sidebar = Main only; mgmt URLs 302/403, worker-cert meta-audit §8) | **no** | **no** — own assigned stage reporting only | yes (own task, single-writer path) | hidden | **no** (management list pages blocked) |
| `accountant` (ADD-ON role, OFF-A D1) | pure: **dispatch-blocked** from rm pages BY DESIGN; composite (+manager): view | no | pure: no · composite: as manager | no | **capability holder** — functions only where a page-role admits (composite lane view+edit proven) | no |

## Helpers

```python
def user_can_view_financials(user):
    return user_has_role(user, FINANCIAL_ROLES)

def user_can_edit_financials(user):
    return user_has_role(user, FINANCIAL_ROLES)
```

## Layered defense — Supplier + Cost Per KG

### Form layer — strip fields the user cannot edit

```python
# raw_materials/forms/roll_forms.py
class BulkRollForm(forms.Form):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        if not user_can_edit_financials(user):
            self.fields.pop('supplier', None)
            self.fields.pop('cost_per_kg', None)
```

### Service layer — reject restricted writes

```python
# raw_materials/services/roll_service.py
@transaction.atomic
def bulk_create_rolls(user, *, supplier=None, cost_per_kg=None, **rest):
    if (supplier or cost_per_kg is not None) and not user_can_edit_financials(user):
        raise PermissionDenied("supplier / cost_per_kg restricted")
    ...
```

### Template layer — hide values from rendered HTML

```django
{% load permissions %}
{% if request.user|has_role:'super_admin,accountant' %}
  <td>{{ roll.supplier }}</td>
  <td>₹{{ roll.cost_per_kg }}</td>
{% endif %}
```

### History/audit layer — strip financial CHANGE rows (Production Audit PA-03-1, 2026-06-14)

The roll **history timeline** logs every field change, including `supplier` and
`cost_per_kg` (old → new). Showing those rows to a non-financial user leaks the
same values the list/detail hide. Filter them server-side in the view so the
values never reach the client:

```python
# inventory/views/tracking_history.py — RollHistoryView.get_context_data
events = ClothRollHistory.objects.filter(roll=roll).select_related('actor')...
if not user_can_view_financials(self.request.user):
    events = events.exclude(field_name__in=('supplier', 'cost_per_kg'))
```

All four layers (form · service · template · history) must agree. Removing one creates a hole. Any NEW surface that renders a financial value or its audit trail must apply `user_can_view_financials` too.

## View-level gating — `RoleRequiredMixin`

Existing mixin in `inventory/views/mixins.py`. Reused across all new views.

```python
class RollBulkCreateView(LoginRequiredMixin, RoleRequiredMixin, FormView):
    required_roles = PRODUCTION_ROLES
    ...
```

For finance-only screens (future):

```python
class CostReportView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    required_roles = FINANCIAL_ROLES
```

## Sidebar menu spec

F-1 polish (2026-07-05): "My Dashboard" is ONE ungated MenuItem for every role
(`inventory:my_dashboard`, live at `/inventory/my-dashboard/`); the historical
management/worker URL twins (`inventory_dashboard` / `user_dashboard`) are
permanent redirects, kept in the registry as `hidden=True` entries so their
SidebarItemRule rows aren't orphaned (P3.4 drift guard) — `hidden` items render
for NOBODY, super admin included. Owner may delete those two rules via Sidebar
Access and then remove the hidden entries.

Stage worker PICKERS (F-4, same date): every stage start/assign form gets its
options from `production.services.eligible_stage_workers(stage_code)` = active
users ∩ `Stage.access_by_skill` — the exact population `user_can_access_stage`
admits, so a picker can never offer a worker the gate would 403.

## Visibility vs Action capability (owner decision V-1, 2026-07-05 — INTENTIONAL split)

Two DIFFERENT questions, two owners, both by design:

1. **VISIBILITY / entry — "may this user see & open this stage surface?"**
   Owner: `production.services.access_service` reading the LIVE
   `Stage.access_by_skill` / `access_by_role` rows (Access-Control hub edits
   apply instantly, no cache). Composed rule for worker-facing surfaces:
   `user_can_access_stage(user, stage)` **AND** (management OR an active
   `WorkerStageTask` on that stage record) — exactly `StageViewAccessMixin`.
   Since the C-2/C-3 freeze closeout this ONE predicate drives: stage panels,
   the Adda-page tabs (`can_open` → iframe or Restricted/Not-assigned card),
   every worker-dashboard accordion/board/row, the worker report view, and
   the assignment pickers. No worker-facing surface may hardcode skill names.

   **Worker sidebar lockdown (H-3/J-4, owner-approved 2026-07-06):** the NON-stage
   navigation for the `worker` role is stripped to its own world. Migration
   `accounts/0018_worker_sidebar_lockdown` removes `worker` from the SidebarItemRule
   rows for the raw-materials suite (`raw_materials:*`), Operations
   (`production:dashboard`), all-Addas (`production:adda-list`), and Tracking
   (`tracking:dashboard`). Because `SidebarItemRule` gates the menu link AND the URL
   together (`SidebarAccessMiddleware` → `can_access_url_name`), a worker can neither
   see nor open those pages. A worker keeps: My Dashboard (exempt landing), My Earnings
   (unmanaged, worker-predicate), and their own stage report/workspace URLs (unmanaged
   action URLs gated by the access ∩ assignment predicate above). Net worker sidebar =
   the "Main" section only.

2. **ACTION capability — "may this user perform this business action?"**
   (e.g. *only cutting_master_helper completes a stage*, *≥1 cutting_master
   must be on a layering roster*.) Owner: the stage SERVICES' explicit guards
   (`_ensure_can_complete_*`, `_ensure_cutting_skill`, …) — business rules
   expressed in code, super-admin/management bypass built in. These are
   **deliberately NOT hub-editable**: editing who can *see* a stage never
   silently changes who can *complete* it. If action permissions should
   become configurable, that is its own dedicated phase (post-R10, owner-
   gated) — a per-stage action-skill config on the Stage model.

Rule of thumb: hub edit = visibility, instantly, everywhere. Code change
(reviewed) = business capability.

Updated entries for `build_menu_for(user)`:

```python
register_section('raw_materials', predicate=_any_role(*PRODUCTION_ROLES), items=[
    MenuItem('Cloth Dashboard', 'raw_materials:dashboard'),
    MenuItem('Rolls',           'raw_materials:roll-list'),
    MenuItem('Cloth Types',     'raw_materials:cloth-type-list'),
    MenuItem('Cloth Colors',    'raw_materials:cloth-color-list'),
    MenuItem('Storage',         'raw_materials:storage-list'),
])
register_section('production', predicate=_any_role(*PRODUCTION_ROLES), items=[
    MenuItem('Products',        'production:product-list'),
    MenuItem('Addas',           'production:adda-list'),
    MenuItem('Active Stages',   'production:dashboard'),
])
register_section('tracking', predicate=_any_role(*PRODUCTION_ROLES), items=[
    MenuItem('Barcodes',        'tracking:barcode-list-root'),
    MenuItem('History',         'tracking:history-root'),
])
register_section('finance', predicate=_any_role(*FINANCIAL_ROLES), items=[
    MenuItem('Supplier Costs',  'raw_materials:roll-list?with_costs=1'),
    # Cost reports + payouts come with expense app
])
```

## ROLE_ACCOUNTANT seed migration

```python
# inventory/migrations/000N_add_accountant_role.py
def forwards(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.get_or_create(
        code='accountant',
        defaults={'name': 'Accountant', 'description': 'Financial view + edit on cloth rolls'},
    )

def reverse(apps, schema_editor):
    apps.get_model('inventory', 'Role').objects.filter(code='accountant').delete()
```

Additive, reversible, no FK reshuffle.

## Access Control hub (`/inventory/access/`)

A super-admin-only, **read-only** overview that consolidates the whole RBAC
picture in one page: Roles × Sidebar Pages, Production Stages × skills/roles,
Users roster, and a Roles summary — each deep-linking to its editor (Sidebar
Access / Stages / Team Members / Roles). It does NOT replace those editors; it's
the single landing surface the master spec asked for. The three concepts stay
separate and are labelled on the page:

- **User Type** — 1:1, display/baseline only, never gates access.
- **Roles** (M2M) — grant module/page/admin/sidebar access.
- **Skills** (M2M) — grant production-stage work capability.

Full page contract: `docs/PAGES/ACCESS_CONTROL.md`.
