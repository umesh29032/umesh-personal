# Page — Access Control hub

The unified RBAC overview page mandated by the master spec. This file is the
exemplar for the per-page doc template (see `docs/PAGES/README.md`).

## Purpose
Give a super-admin ONE place to see the whole access picture — who sees which
sidebar pages, which skills/roles unlock which production stages, and what every
user is granted — surfacing the cross-functional relationships that no single
editor showed. Read-only; it routes to the existing editors for changes.

## Route
- URL: `/inventory/access/`
- Name: `inventory:access-control`
- View: `inventory/views/access_hub_views.py::AccessControlHubView` (TemplateView)
- Template: `templates/inventory/access_control.html`
- Sidebar: Administration → "Access Control" (first item).

## Permissions
- `LoginRequiredMixin` + `SuperAdminOnlyMixin` (`inventory/views/mixins.py`).
- Direct-URL safe: a non-super-admin who types the URL gets **403** (verified by
  `inventory.tests.AccessControlHubTests` + live browser test). Not sidebar-hidden only.

## Role access
- Super Admin only. Manager / Karigar / Listing Team / Accountant → 403.

## Skill access
- None. Skills do not gate this page (this is an access-admin surface, not a
  production stage). The page *displays* skill→stage mappings but is role-gated.

## Form behavior
- None — the page is **read-only**. Every panel has an "Edit →" link to its
  dedicated CRUD page:
  - Roles × Pages → `inventory:sidebar-access`
  - Stages × access → `production:stage-list`
  - Users → `accounts:user_list`
  - Roles → `inventory:role_list`

## Data shown (no writes)
- **Roles × Sidebar Pages**: walks the in-code `permission_service.SIDEBAR`
  registry, joins each item to its `SidebarItemRule` (DB). Items with no rule are
  marked `code` (gated by the in-code predicate) so coverage gaps are visible.
- **Production Stages × Access**: `Stage.access_by_skill` + `Stage.access_by_role`
  per stage; note super_admin/manager are always allowed (built-in).
- **Users roster**: `user_type` (display), primary `role`, `extra_roles`,
  `skills`, `is_superuser` flag.
- **Roles summary**: per-role permission count; super_admin shown as "all (bypass)".

## Edge cases
- Super Admin is always-visible at the service layer, so it is intentionally
  NOT a column in the Roles × Pages matrix (can't lock yourself out).
- A brand-new sidebar item with no `SidebarItemRule` row shows as `code`-gated —
  this is the rbac-3 coverage gap made visible, not an error.
- Empty stage/user tables render a friendly "none" row.

## Mobile behavior
- Legend cards stack to 1 column < 820px. The roster / stages / roles tables use
  `.stack` (rows collapse to label:value pairs). The Roles × Pages matrix (dynamic
  role columns) stays a horizontally-scrollable table inside `.table-scroll`.
- Verified @375: no page-level horizontal overflow.

## Risks
- Read-only by design — low risk. If future inline-edit is added, each cell write
  must re-check super-admin server-side (never trust the matrix UI).
- The matrix reflects `SidebarItemRule` DB state, which may lag the in-code
  `SIDEBAR` for un-ruled items; the `code` badge signals that.
