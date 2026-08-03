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
| `accountant` (**READ TIER**, owner ruling 2026-08-02 — supersedes OFF-A D1 "dispatch-blocked BY DESIGN") | **view** (roll list) | no | **no** | no | **view + edit** — the capability is finally reachable | no |
| `student` (ADD-ON role, 2026-08-02) | **no** | no | **no** | no | hidden | **no** — holds **zero** business permissions; its only reach is `/learn/` |

## The accountant READ TIER (owner ruling 2026-08-02)

**The problem.** Every financial page was `_ManagementOnly` — read AND write behind one
gate. A *pure* `accountant` login therefore had **no reachable page at all**: their
`FINANCIAL_ROLES` capability (view + edit Supplier and Cost Per KG) was unreachable dead
code, and their dashboard showed WORKER copy (*"Jab manager aapko kaam dega"*, *"Pieces
Produced 0"*). This supersedes the earlier OFF-A D1 record of "pure accountant:
dispatch-blocked from rm pages BY DESIGN".

**The principle: reads widened, writes did not move.**

`FINANCIAL_READ_ROLES = MANAGEMENT_ROLES | {accountant}` (permission_service).

| Surface | accountant | why |
|---|---|---|
| Payroll overview · Adda Settlements (list/detail) | ✅ read | reconciliation is the job |
| Factory Expenses (list **+ record**) | ✅ read + **write** | the ONE money-write grant |
| Recurring Expenses **register** | ✅ read | status comes from `generate_monthly_expenses(confirm=False)` — a pure preview |
| Material Spend (cloth ₹/kg) | ✅ read | their core report; previously had **no menu entry at all** |
| Cloth Rolls + supplier/cost-per-kg | ✅ read + edit fields | where the capability is defined |
| Record Advance · settlement start/finalize · pay-basis · FnF | ❌ | money-writes, unchanged |
| **void expense** · template create/amount-change · **generate period** | ❌ | super-admin / management levers, enforced **inside the service** |

### Why this is safe

1. **Two layers, independently.** `_FinancialRead` gates only list/detail/report views;
   `expense_service` and `settlement_service` re-check the actor themselves. `void_expense`
   and the template levers are super-admin-only *in the service*, so even a mis-gated view
   cannot become a money hole.
2. **Settlement is untouched** — still the single money-write boundary.
3. **Append-only bookkeeping.** An accountant can **add** a cost record but never erase or
   rewrite one; corrections stay with the owner. Standard accounting hygiene.
4. **The gate follows the write, not the call.** `generate_monthly_expenses` is two things
   behind one name: `confirm=False` is a pure read (returns the plan before touching
   anything), `confirm=True` writes rows. Gating both as a write made a **read** page 403.
   Now: preview → `FINANCIAL_READ_ROLES`, confirm → `MANAGEMENT_ROLES`.

### Implementation

| Piece | Where |
|---|---|
| `FINANCIAL_READ_ROLES` | `accounts/services/permission_service.py` |
| `_FinancialRead` mixin | `expense/views.py` (read views only) |
| `ProductionOrAccountantMixin` | `raw_materials/views/mixins.py` (roll list only) |
| Accounts dashboard panel | `inventory/views/dashboard.py` — **reuses `payroll_service.payroll_totals()`**, never re-derives money (it already excludes REVERSED recoveries, PA-12-A) |
| Sidebar section `Payroll & Accounts` | `permission_service.SIDEBAR` — reads on `FINANCIAL_READ_ROLES`, `Record Advance` still `MANAGEMENT_ROLES` |
| Access-Control row edit | `accounts/migrations/0021_accountant_read_tier_sidebar.py` — adds accountant to `raw_materials:roll-list`, whose **DB rule overrode the in-code predicate** |

**Pinned by** `expense.tests.test_accountant_read_tier` (16 tests: can-read · cannot-write ·
service refuses at the service layer · menu-offers-only-what-opens · panel figures equal the
canonical aggregate). Browser-verified 37/37 across accountant · worker · manager · mobile.

## The `student` role + the `/learn/` gate (owner ruling 2026-08-02)

**Why.** The course reader shipped **ungated** — every authenticated user saw "Learn",
including factory workers who have no use for SQL/deployment courses. The owner wants
to hand the link to peers (and later, paying students) **without exposing the factory**.

**What changed** (`accounts/migrations/0020_student_role_and_learning_access.py`):

| Thing | Value |
|---|---|
| New role | `student` — "Student", `is_system=True`, **0 permissions** |
| New `SidebarItemRule` | `url_name='learning:index'`, section `Main`, label `Learn` |
| Seeded `allowed_roles` | `student` only |
| `super_admin` | **deliberately not listed** — service-layer bypass means an admin can never lock themselves out |
| `manager` | **not seeded** — tick it in Access Control if the owner wants managers to have courses |

**Who sees Learn now** (verified, `LearningAccessControlTests`):

| Role | menu link | URL access |
|---|---|---|
| `super_admin` | ✅ | ✅ (bypass) |
| `student` | ✅ | ✅ |
| `manager` · `worker` · `accountant` · `listing_team` | ❌ | ❌ |
| role-less user | ❌ | ❌ |

### ⚠️ The hole a sidebar rule alone would leave

`can_access_url_name()` returns **True for any `url_name` with no rule**, and only
`learning:index` carries one. So a rule row by itself hides the menu link **and still
serves `/learn/sql/14-indexes/` to anyone who types it** — the chapter, interview,
revision and search views all have their own url_names.

The fix is `_LearningAccessMixin` in `config/learning/views.py`: **every** learning view
(and every progress POST endpoint) checks `can_access_url_name(user, 'learning:index')`,
so **one** Access-Control checkbox governs the whole section. That is the documented
"the view's own mixin gates it = defense in depth" contract, made real.

Denial mirrors `SidebarAccessMiddleware` exactly — message + redirect to
`inventory:my_dashboard` (302), or a clean **403** for `XMLHttpRequest` callers, since a
redirect would corrupt a `fetch()`. A blocked user must never get a friendly redirect on
one learning URL and a bare 404 on the next.

**Pinned by** `learning.tests.test_learning.LearningAccessControlTests` — including
`test_a_blocked_role_cannot_reach_a_chapter_by_typing_the_url` (the hole above) and
`test_menu_link_and_url_access_never_disagree` (rule 6 invariant across all 5 roles).

**To change who gets courses:** Access Control → Sidebar Access → the **Learn** row →
tick/untick roles. No code change, no deploy.

## Live verification — AUDIT-2, 2026-07-27

Re-proven end-to-end against the running app: **10 identities × 30 surfaces = 300 live probes**
(full matrix + method in
[AUDIT2_PRODUCTION_ACCESS_FINANCIAL_2026_07_27.md](../AUDIT2_PRODUCTION_ACCESS_FINANCIAL_2026_07_27.md)).

| Role | 200 | 403 | 302→my-dashboard | rate/cost tokens in page content |
|---|---|---|---|---|
| `super_admin` | 27 | 3 | 0 | 5 (owns them) |
| `manager` | 20 | 5 | 5 | 1 (costing page) |
| `accountant` (pure) | 2 | 18 | 10 | **0** |
| `listing_team` | 2 | 18 | 10 | **0** |
| `worker` (any of 6 skill profiles) | 3–5 | 15–17 | 10 | **0** |

**Skill-gated stage isolation is exact** — each worker gets `200` on only their own stage's report
and `403` on every other. Verified with deliberate negative controls (`iron_master`,
`sleeve_operator`, and a zero-skill worker): all three get `403` on every report page and stage
panel, and see **zero** money tokens on an Adda detail page where an *assigned* worker correctly
sees their **own** expected earning.

Two nuances worth keeping in mind when reading test output:

- `assertNotContains(resp, 'Stage Rates')` in `test_r1_navigation` currently **fails as a false
  positive** — the string appears only inside a CSS *comment* in the page's `<style>` block. There
  is no link and no rate value in `<main>`, and `/stage-rates/` returns **403** to every worker.
- A `SidebarItemRule` row can outlive its code SIDEBAR-registry entry (`production:my-work`). The
  middleware **still gates the URL** from the rule (workers 200, listing_team/accountant 302), so an
  orphan is a *navigation* defect, not an access hole — but the drift guard rightly fails.

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
