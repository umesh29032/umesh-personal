# Fixes Applied — QA 2026-06-02

All surgical, no migration, no data mutation. 270 tests green after.
**Uncommitted** (whole stack pending owner approval — do not commit yet).

## #1 — Settlement over-pay race → per-worker lock
`config/expense/services/settlement_service.py`
- Import `WorkerProfile`.
- In `create_settlement`, after `_ensure_management`, take a serializing lock
  on a stable per-worker row before reading `payable_before`:
  ```python
  profile, _ = WorkerProfile.objects.get_or_create(user=worker)
  WorkerProfile.objects.select_for_update().get(pk=profile.pk)
  ```
  Now two concurrent settlements for a worker serialize; the second re-reads the
  reduced payable. (Cross-worker reference race #6 still open — low.)

## #3 — Delete bundle/item with allocation → friendly guard
`config/production/services/cutting_service.py`
- `delete_bundle_item`: refuse with `ValidationError` if
  `item.work_assignments.exists()` (any allocation, incl. voided — they're
  immutable and PROTECT the item).
- `delete_bundle`: same guard across the bundle's items.
- Converts a 500 `ProtectedError` into a clear message; preserves the pay
  audit trail.
- Tests: `expense/tests/test_allocation_ui.py` —
  `test_delete_item_with_live_allocation_refused_not_crash`,
  `test_delete_item_still_refused_after_void`.

## #2 (mitigation) — money models read-only in Django admin
`config/expense/admin.py`
- New `_MoneyReadOnlyAdmin` (no add/change/delete) applied to
  `StageWorkAssignment`, `WorkerLedgerEntry`, `WorkerAdvance`,
  `PayrollSettlement`. Stops admin from orphaning PROTECT'd ledger rows (the
  exact path that stranded SETL-0001's advance_recovery live). `WorkerProfile`
  stays editable (metadata). Matches the sole-writer rule (rule 4/5).
- Does NOT fix the full reverse-settlement gap (#2) — see bugs_found.md.

## #7 — Mobile costing "unpriced" note stacks
`config/production/templates/production/costing.html`
- In the `max-width:720px` block: `td { flex-wrap: wrap }` +
  `td .unpriced { flex-basis: 100%; text-align: right }`. Note drops below the
  cost. Verified @375 (no overflow).

## Deferred (owner decision / feature scope)
- **#2 full fix**: add a `reverse_settlement` service that reverses both ledger
  debits AND writes compensating `PayrollSettlementItem` rows (or a recovery
  reversal the advance pool subtracts) before any settlement-undo is exposed.
- **#4**: net reversed settlement payments out of `total_settled`.
- **#5**: restrict cost methods per stage type, or define a quantity source for
  pattern/custom stages.
- **#6**: lock/retry on `_next_reference` for cross-worker concurrency.

## Live-data note (not a code change)
wa-audit (pk17) carries orphaned ledger debits (`settlement_payment ₹20` +
`advance_recovery ₹30`, settlement=None) from the owner deleting SETL-0001
mid-audit → `advance_outstanding` overstated by ₹30. Owner's test data; not
auto-fixed. Reconcile by reversing those two debits via `ledger_service` if the
recovery is meant to be undone, or re-create the settlement.
A temp dev password was set on `wa-audit@test` (`Audit@1234`) to test the
karigar view.

---

# Stage A Re-Audit Follow-up — 2026-06-02 (second pass)

Master-spec sweep (7-domain reader + adversarial verify, see
`STAGE_A_REAUDIT_2026_06_02.md`). All surgical, **uncommitted**, 276 tests green
(was 270; +6 regression tests). Closes prior-deferred #4 and #6.

## #6 (closed) — settlement cross-worker reference race
`config/expense/services/settlement_service.py`
- `create_settlement` now takes a transaction-scoped Postgres advisory lock
  (`pg_advisory_xact_lock`) before `_next_reference`, serializing reference
  allocation across ALL workers (the per-worker `WorkerProfile` lock didn't).
  Vendor-guarded (`connection.vendor == 'postgresql'`). Auto-released on commit.
- Test: `test_settlement_references_unique_across_workers`.

## #4 (closed) — `total_settled` / `total_earnings` ignore reversals
`config/expense/services/payroll_service.py`
- `worker_summary` now nets reversals **by the category of the reversed entry**
  (`reverses__category`): a reversed settlement payment nets out of
  `total_settled`; earnings count only `STAGE_EARNING`/`PRODUCTION_EARNING`
  credits so a settlement-reversal CREDIT can't inflate `total_earnings`.
- `pending_payable` unchanged (still Σcredit−Σdebit; correct regardless).
- Test: `test_settlement_reversal_nets_settled_not_earnings`.

## NEW — settlement-item admin mutable (db-integrity-1)
`config/expense/admin.py`
- `PayrollSettlementItemInline` got `has_add/change/delete_permission → False`.
  The parent admin was read-only but the inline defaulted to editable → an admin
  could change `amount_recovered` and break
  `advance_deducted == Σ amount_recovered`.

## NEW — cutting consumed_count clobber
`config/production/services/cutting_service.py`
- `add_item_to_bundle` / `add_bundle_item` `update_or_create` keyed on
  `(bundle,pattern,color)` could overwrite the `count` of a row originally
  created WITH a `source_breakup` (via `add_pieces_to_bundle`) without re-syncing
  that breakup → stale `consumed_count` (drift, never negative). Now recompute
  the source breakup after the update when `item.source_breakup_id` is set.
- Test: `test_manual_add_resyncs_source_consumed_count`.

## NEW — unified Access Control hub (master-spec RBAC ask)
- `config/inventory/views/access_hub_views.py` + `urls.py` + template
  `templates/inventory/access_control.html` + sidebar entry. Super-admin-only,
  read-only matrices (Roles×Pages, Stages×skills/roles, Users roster, Roles
  summary) with deep-links to the existing editors. See
  `docs/PAGES/ACCESS_CONTROL.md`.
- Tests: `inventory.tests.AccessControlHubTests` (renders for super_admin;
  manager + karigar → 403 on direct URL).
- Browser-verified live on :8000 (super_admin renders, 0 console errors,
  desktop + mobile no overflow; manager direct-URL → 403).

## Still deferred (owner decision)
- **#2** full `reverse_settlement` service (compensating items) — still needed
  before any settlement-undo is exposed; admin-delete path stays blocked.
- **#5** priced non-producing stage freezes cost=NULL.

---

# RBAC Refactor Review — 2026-06-02 (3rd pass)

Review of the Access Control hub + RBAC architecture. 282 tests green. Migration
0018 applied to dev DB. Browser 4-persona matrix verified live.

## #10 — `/production/products/` reachable by Worker (karigar)
- `production/views/product_views.py`: `ProductListView` mixin
  `ProductionRoleMixin` → `ManagementRoleMixin` (new, super_admin+manager).
- `production/views/mixins.py`: added `ManagementRoleMixin`.
- `inventory/services/permission_service.py`: Products MenuItem gets
  `predicate=_any_role(*MANAGEMENT_ROLES)`.
- `inventory/migrations/0018_*`: drop `karigar` from the `production:product-list`
  `SidebarItemRule`; also seed the `inventory:access-control` rule.
- Test: `production/tests/test_rbac_matrix.py::ProductsAccessMatrixTests`
  (super 200, manager 200, karigar 403, no-role 403).

## #11 — `scan_piece` missing role gate
- `tracking/views/barcode_views.py`: `scan_piece` now `raise PermissionDenied`
  unless `user_has_role(user, PRODUCTION_ROLES)` (mutates audit fields).
- Test: `ScanPieceAccessTests` (no-role 403, karigar passes gate → 404 on bad value).

## Doc fix
- `production/views/adda_views.py`: corrected a stale comment that named the
  deleted `StageAccessRule` table as the live per-stage gate (it is the `Stage`
  model, skill-driven).

## #12 — Stage workspace/panel VIEWS not skill-gated (4th pass)
Full route-enforcement audit (Django URL-resolver introspection) found every app
CBV gated, but stage workspace/panel VIEWS used `ProductionRoleMixin` only — skill
was enforced on ACTIONS (service layer) not on VIEWING. A karigar could direct-URL
into any stage workspace and see its data/UI. Inconsistent with `AddaDetailView`
(which uses `stage_access_map`) and the spec ("skills control stage visibility").
- `production/views/mixins.py`: new `StageViewAccessMixin` (reuses
  `access_service.user_can_access_stage`; management bypass; skill OR stage-role).
- Applied to `LayeringWorkspaceView`, `StagePanelView` (stage_type kwarg),
  `CuttingWorkspaceView`, `PatternWorkspaceView`, `BarcodeGenWorkspaceView`.
- Tests: `production/tests/test_rbac_matrix.py::StageViewSkillGateTests`.
- Browser-verified live: no-skill karigar → layering 403, barcode-gen 403, cutting
  200 (cutting Stage grants karigar via `access_by_role` — OR-semantics intact);
  super_admin → 200 (bypass). 285 tests green.

## #13 — Edit-user form swallowed validation errors (silent fail)
`accounts/templates/accounts/user_form.html`
- Symptom: admin sets a new password (or hits any field-validation error) on Edit
  User → form silently re-renders, no save, NO message → looks "not working."
- Root cause: template rendered only `form.non_field_errors`. Password rejections
  (too short / too common / too similar — `validate_password`) are FIELD errors on
  `new_password`, which were never displayed. (Pre-existing UX gap, not from the
  user_type/role rename — backend always worked: strong password → 302 saves.)
- Fix: added a top-of-form summary listing ALL errors (field + non-field) + an
  inline error under the password field. Weak password now shows "too short / too
  common"; strong password saves (verified 302 + check_password). create template
  already showed password errors.
- Note: forgot-password flow verified working (GET 200, POST 302 → verify); data
  clean (no invalid user_type, role codes = manager/super_admin/worker).

## #14 — Sidebar Access panel hid the menu but NOT the URL
Removing a role from a menu item in the Access-Control / Sidebar Access page
(`SidebarItemRule`) hid the sidebar link but the URL stayed reachable (views were
gated by role mixins, disconnected from the panel). Sidebar hiding ≠ security.
- Fix: `permission_service.can_access_url_name(user, url_name)` (same decision the
  sidebar uses) + NEW `inventory/middleware.py::SidebarAccessMiddleware` (registered
  after auth+messages). For any request whose resolved url_name HAS a SidebarItemRule,
  it enforces the rule: super_admin bypass; role/skill overlap allows; else
  flash "You don't have the access to this page." + redirect to the previous page
  (resolved + re-checked to prevent loops) or the user's dashboard. AJAX → 403 JSON.
  Unmanaged url_names pass through (view mixin still gates them = defense in depth);
  dashboards exempt (landing, no loop).
- Effect: managed-page denials now REDIRECT (302) instead of bare 403 (the
  requested UX). Updated ProductsAccessMatrixTests + AccessControlHubTests
  assertions 403→302 accordingly; scan (unmanaged) stays 403.
- Tests: `SidebarRuleUrlEnforcementTests` (worker blocked 302, manager 200,
  super_admin bypass). Browser-verified: worker → `/production/` → redirect to
  dashboard + message; allowed pages still load. 288 tests green.

## IDOR / object-level audit (OWASP A01) — 2026-06-02
Outcome: **CLEAN, no fix needed.** Audited every per-worker (private/financial)
data path. All payroll service fns (worker_summary/ledger/earnings/settlements/
advances/...) are called ONLY from expense/views.py. The 3 views taking a User
`pk` are each gated: worker-detail → `can_view_worker` (self-or-management),
settlement-create + worker-profile → `_ManagementOnly`. No per-object detail
routes (no /settlement/<id>/ etc.) to leak. Other `pk` views (Product, ClothRoll)
are SHARED org resources, role-gated by design — not per-user-private, so not IDOR
(single-tenant). 
Hardening (test lock): `expense/tests/test_views.py::PayrollDataIsolationTests` —
two workers with REAL earnings; asserts a worker cannot READ another's detail
(403), my-earnings is self-scoped (A sees ₹20 not B's ₹14), and cannot WRITE
(settle / record-advance) for another (no row created). 292 tests green.

## Reported, NOT auto-fixed (load-bearing / design)
- No `supplier`/`worker` user-type (`USER_TYPE_CHOICES = admin/manager/karigar/
  helper/normal`). Spec lists supplier — not implemented.
- Legacy `user_type`→role fallback (`user_role_code` legacy_map) + `is_superuser`
  bypass are **load-bearing**: 10+ live users have `role=None` (incl. the
  super-admin login `umesh29mar` via `is_superuser`, and `skeshav15april`
  type=manager→manager via the fallback). Removing either locks out real users.
  Recommend a data migration to assign explicit roles BEFORE deprecating.
- `Stage.access_by_role` (role path on stages, OR with `access_by_skill`) is a
  mild skill/role mix — documented OR semantics + management bypass; left as-is.
</content>
