# RBAC — Production Tracking Roles & Gating

Reuses existing `inventory.services.permission_service` (CLAUDE.md rule #6). No raw `is_superuser` checks anywhere.

## Role additions

```python
# inventory/services/permission_service.py — additive
ROLE_ACCOUNTANT = 'accountant'

ADMIN_ROLES      = {ROLE_SUPER_ADMIN}
MANAGEMENT_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER}
FINANCIAL_ROLES  = {ROLE_SUPER_ADMIN, ROLE_ACCOUNTANT}   # view + edit Supplier, Cost Per KG
PRODUCTION_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER}  # ROLE_WORKER == 'worker' (renamed from ROLE_KARIGAR/'karigar' 2026-06-02)
```

Super Admin keeps universal visibility — every role set includes `ROLE_SUPER_ADMIN`.

## What each role can do

| Role | Cloth dashboard | Roll bulk add | Adda CRUD | Stage advance | Supplier / Cost per KG | Product CRUD |
|---|---|---|---|---|---|---|
| `super_admin` | view | yes | yes | yes | view + edit | yes |
| `manager` | view | yes | yes | yes | hidden | yes |
| `karigar` | view | yes | view + assign rolls | yes (own task) | hidden | view |
| `accountant` | view (no costs) | no | view | no | view + edit | no |

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

All three layers must agree. Removing one creates a hole.

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
