---
id: worker-role-certification
type: evidence-cert
status: active
owner: append-only
scope: worker role — all 9 URL-bearing apps
anchors: config/accounts/services/permission_service.py, config/inventory/middleware.py
verified: 2026-07-12
---

# Worker Role Certification — Phase A: Production · Phase B: Expense · Phase C: Tracking · Phase D: Inventory · Phase E: Raw Materials · Phase F: Machines · Phase E: Raw Materials

> V1.1 sprint, 2026-07-12. One app per phase (scope discipline).
> **Phase A = production app** (`production/urls.py`, `production/views/*`,
> `production/templates/production/*`, permission-bearing
> `production/services` + `production/stages/*/service.py`).
> **Phase B = expense app** · **Phase C = tracking surface** ·
> **Phase D = inventory app** (sections below).
> Raw-Materials / Machines / Storefront /
> Accounts / Patterns-AI = future certification phases — NOT covered here.
> Engine FROZEN; only found bugs were fixed, zero refactoring.

## Method

1. URL enumeration from `production/urls.py` → per-view gate-chain code audit
   (mixin → service gate → template ctx).
2. Suspicious writes probed in shell (rollback-wrapped, real dev DB).
3. 3 confirmed bugs fixed, gates re-probed (worker / manager / helper).
4. Browser verification as the real worker `dev.ow.a@test.local` on :8003.
5. Permission tests + full sequential battery.

## Worker-visible surfaces — verdicts

| # | Surface | Verdict | Evidence |
|---|---------|---------|----------|
| 1 | Worker dashboard (`/inventory/my-dashboard/`) | ALLOWED | Login lands here; sidebar = **Main only** (My Dashboard, My Earnings) — OP-1 lockdown holds |
| 2 | My assigned Addas (adda-detail) | ALLOWED, own-data-only | Browser leak check on NKS-001: settlement-mentions 0 · stage-rates links 0 · A360 markers 0 · My-Work panel 1 · only own ₹ ("Qty 45 · Expected ₹45.00") |
| 3 | Stage workspace (panels/consoles) | ALLOWED, lane-scoped | GAP-4 `_scope_console_lanes`: foreign lane → `PermissionDenied` ("That lane isn't assigned to you") |
| 4 | Stage reporting | ALLOWED, own task only | Own-task check + C-3 live-access check (revoked access ⇒ 403, frozen-foundation rule) |
| 5 | Lane isolation | BLOCKED cross-lane | Same GAP-4 law on layering + cutting consoles |
| 6 | Stage actions (complete/reopen) | BLOCKED for workers | Reopens mgmt-only; generic complete = mgmt or assigned∧live-access; legacy cutting complete was **BUG-1** (fixed) |
| 7 | Bundle pages (cutting workspace) | ALLOWED view; ₹ rows mgmt-only | Allocation ₹ ctx was **BUG-3** (fixed) |
| 8 | Barcode Generation pages | ALLOWED (production roles) | List/print/scan stay production-role; exports were tightened to management in V1.1 Item 3 (tracking phase) |
| 9 | Pool / readiness pages | BLOCKED (management) | Bundle-sets POST + Add-lane lifecycle = management views; service re-enforces post-join gate |
| 10 | JSON/AJAX (production) | BLOCKED / own-scope | Covered by the 13-URL probe below + per-view audit |

## Forbidden-URL probe (browser, as `dev.ow.a`)

13 management URLs probed logged-in as the worker — **all denied**
(redirect to My-Dashboard or in-page denial), except two that are
**worker-scoped by design**:

- Denied: `/production/` · `/production/addas/` · `/production/products/` ·
  `/production/stages/` · `/production/addas/start/` · `/production/costing/` ·
  `/production/patterns/` · `/production/addas/NKS-001/review-reports/` ·
  `/production/addas/NKS-001/stage-rates/` · `/production/stage-categories/` ·
  `/production/machine-types/`
- By-design 200s (self-scoped, no leak):
  - `/production/pending-reports/` — "Your assigned work"; renders the
    worker's own queue (browser: "All caught up 🎉").
  - `/production/stalled/` — `StalledAddaListView` docstring + code: non-management
    see only stalled Addas they hold a live task on
    ([dashboard.py:112](../config/production/views/dashboard.py#L112)).

SUSPECT-1 (adda-detail vs RBAC doc wording) resolved: template ctx leaks
nothing management-grade to workers (evidence row 2 above).

## Bugs found → fixed (3)

| Bug | Where | What leaked | Fix | Proof |
|-----|-------|-------------|-----|-------|
| **BUG-1** | `complete_cutting_legacy` ([cutting/service.py:1237](../config/production/stages/cutting/service.py#L1237)) | Docstring said MANAGEMENT but the gate was `_ensure_can_manage` = PRODUCTION roles (name trap, same class as the M3 AddaCreate bug) — **any worker could complete Cutting**: stage advance + barcode generation + cost freeze | `user_has_role(user, MANAGEMENT_ROLES)` else `PermissionDenied("only management can complete the cutting stage (legacy path)")` | **Browser-proven**: worker POSTed the real NKS-001 cutting form → error banner with the exact message, no side effects; manager passes the role gate (falls to stage validation) |
| **BUG-2** | `save_layering_draft` ([layering/service.py:563](../config/production/stages/layering/service.py#L563)) | Production role alone let ANY worker tamper layering drafts on any Adda | Draft = write surface → assigned worker (`sr.is_worker_assigned`) OR `cutting_master_helper` skill (the Complete path drafts first) OR management | Shell re-probe: worker BLOCKED "not assigned to this stage"; assigned/helper/manager pass (draft path completed, rolled back) |
| **BUG-3** | `_build_cutting_context` ([stage_views.py:1231](../config/production/views/stage_views.py#L1231)) | Per-bundle-item allocation rows carry OTHER workers' ₹ earning snapshots (era-A) — built for every viewer | `alloc_items` built only `if is_management` (same law as A360: workers never receive a byte; V2-3 visibility = own money only) | Ctx probe on single-lane era-A Adda: manager `alloc_items=3`, cutting-worker `alloc_items=0` |

No other fixes pending — the audit's remaining verdicts were ALLOWED/BLOCKED
as designed and left untouched (scope discipline).

## Tests

[test_worker_role_certification.py](../config/production/tests/test_worker_role_certification.py)
— 6 pins, all green:

- FIX-1: worker (even with cutting skill) → `PermissionDenied`; manager passes the role gate.
- FIX-2: unassigned worker BLOCKED + nothing written; assigned / helper / management all draft successfully.
- FIX-3: assigned cutting worker gets `alloc_items == []` on a bundle-bearing
  workspace; management still gets the full allocation rows.

## Battery

Sequential (canonical — see DEPLOYMENT_BACKLOG #4):

- 9-app battery (`accounts core raw_materials production tracking expense
  storefront inventory machines`): **977/977 OK** (167.8s) — includes the
  6 new certification pins (pre-item-4 total 971).
- `patterns_ai` (sequential): **528/528 OK**.
- Sprint baseline 1499 + 6 new pins = **1505/1505 green**.

## Honest caveats

- FIX-1 is browser-proven end-to-end. FIX-2/FIX-3 are shell-probe +
  test-pinned; the browser draft-tamper POST was cut short by the prior
  session's crash (baseline was captured, gate already probed at service
  level — the layer the bug lived in).
- `/production/stalled/` and `/production/pending-reports/` render for
  workers **by design** (self-scoped). If the owner wants them hidden
  entirely, that is a Sidebar-Access decision, not a permission bug.

## Verdict

**Production app worker surface: CERTIFIED** (3 bugs fixed, gates pinned,
no other leak found in scope). Next phases (owner-gated): ~~Expense~~
(→ Phase B below) → Tracking → remaining apps.

---

# Phase B — Expense app (close-out 2026-07-12)

> Audited in a previous session — **B1 code audit + B2 browser
> verification** — which ended before this close-out landed on disk
> (docs-sync interrupted). This section is the completion record, written
> 2026-07-12 from **owner attestation**. No per-surface evidence artifacts
> (probe logs / browser transcript) survived to disk — see Provenance.

## Scope

`expense/urls.py` · `expense/views.py` · `expense/templates/expense/*` ·
permission-bearing `expense/services/*` (adda_settlement_service ·
ledger_service · settlement_service · fnf_service · allocation_service ·
payroll_service `set_pay_basis` · advance_service · expense_service ·
`_shared` auth gates) — the money-URL surface: my/ · payroll/ · settle/ ·
advances/ · settlements lifecycle · workers/<pk>/pay-basis/ ·
workers/<pk>/fnf/ · expenses/.

## Result (owner-attested)

- **No bugs found.**
- **No implementation changes** — zero code modified for Phase B.
- **No new tests** — existing money-gate pins stand as-is
  (test_v2_3_guards · test_adda_settlement_* · test_r4_monthly_basis ·
  test_r5_factory_expense/hostile_fixes · test_r7_fnf · test_reopen_voids_pay).
- **No battery change** — sequential baseline **1505/1505** from the
  Phase A close-out still current; no rerun was required (nothing changed).

## Provenance & honest caveats

- Close-out written from **owner attestation (2026-07-12)**, not from
  on-disk session artifacts; the auditing session's probe logs and browser
  transcript were lost with that session.
- Certification strength: **attested** — weaker than Phase A's
  artifact-backed record (Phase A carries per-URL probe results, ctx
  probes, exact browser error quotes). Re-audit was explicitly declined
  by the owner (scope discipline, engine frozen).
- If future doubt arises on any expense surface, re-run the Phase-A
  method (URL enum → gate-chain audit → shell probe → browser as
  `dev.ow.a`) on that surface only.

## Verdict

**Expense app worker surface: CERTIFIED (owner-attested).** No bugs, no
code/test/battery change. Next phase (owner-gated): ~~C — Tracking~~
(→ Phase C below) → remaining apps.

---

# Phase C — Tracking surface (2026-07-12)

> Scope: the `/tracking/` URL surface — **13 URLs** in
> [inventory/tracking_urls.py](../config/inventory/tracking_urls.py) (the ONLY
> mount, `config/urls.py:27`; `config/tracking/views/` is empty — P4.2 moved
> views to inventory, tracking app keeps primitives). Audited layers: 4 view
> modules (`tracking_dashboard/barcodes/exports/history`), `tracking/services`
> (barcode_service single-writer + history_service), `tracking/models`,
> all 7 `tracking/templates/tracking/*` (+ shared `_adda_events_accordion`),
> `export_service` backstop, `SidebarAccessMiddleware` + SidebarItemRule data,
> role-set definitions, existing test pins.
>
> Method note (audit-honesty rule): an 8-finder sub-agent Workflow was
> launched for C1 and **all 8 finders failed** (session limit). The entire
> audit was redone **100% main-thread**; no area was marked clean on
> sub-agent silence.

## C1 — code audit (gate map)

| # | URL | Gate chain | Verdict |
|---|-----|-----------|---------|
| 1 | `/tracking/` dashboard | ProductionRoleMixin + **SidebarAccessMiddleware DB rule** (0017 seeded manager+worker; [0018](../config/accounts/migrations/0018_worker_sidebar_lockdown.py) stripped worker → live rule = manager-only) | worker BLOCKED (redirect+flash); pin [test_op1_hardening H-3](../config/production/tests/test_op1_hardening.py) |
| 2–3 | barcode list / print sheet | ProductionRole (unmanaged url_name) | ALLOWED by design ("workers legitimately scan", V1.1-3); no money; export buttons `is_management`-gated |
| 4 | legacy quick-CSV | MANAGEMENT check in view | worker 403; pin `test_worker_quick_csv_403` |
| 5–6 | scan / scan-status | PRODUCTION_ROLES; status POST → `mark_status` single-writer (choice-validated, writes `BatchBarcode.status` only) | non-production 403 pinned (test_rbac_matrix); no money writes |
| 7 | roll history | ProductionRole + mgmt-or-assigned + **financial row strip** (supplier/cost_per_kg = the ONLY money field_names ever logged — verified against every `log_roll` callsite) | pins: G-AUTH-1 ×4 + FinancialHistoryLeak ×3 |
| 8 | adda history | ProductionRole + G-AUTH-1 assigned-only | template renders note/stage/roll/actor; **`metadata` jsonb (COST_FROZEN `{method,rate,qty,cost}`, SETTLEMENT `expected_total`) is NEVER rendered**; every `log_adda` `note=` callsite swept — names/quantities/reasons, zero ₹ |
| 9–13 | exports ×5 (list/csv/xlsx/pdf/re-download) | ManagerOrAdminMixin + `_ensure_management_role` first-line in all 4 service fns; `_render_csv_bytes` callers all post-gate | worker-403 pins ×5 |

C1 verdict: **zero confirmed bugs**. Money never reaches tracking templates
(metadata-only, never rendered); exports double-gated; history double-gated +
financially stripped.

## C2 — browser evidence (worker `dev.ow.a@test.local`, :8003)

1. **Backlog-#2 discrepancy resolved:** `GET /tracking/` → **302** to
   My-Dashboard + flash "You don't have the access to this page." — worker
   never renders the dashboard (no global Adda table / global timeline /
   money). The old "worker got 200" observation is **stale**.
2. **Barcode surfaces:** list (assigned LOWER-002 + foreign DEV-NICKAR-001),
   print sheet (82 QRs), scan, scan-status POST round-trip
   (Packed → verified message → restored Pending, DB re-checked) — all 200,
   zero financial content (only money-regex hit = the worker's own
   "My Earnings" sidebar link); export buttons absent everywhere.
3. **History scoping:** assigned adda NKS-001 → 200, Cost Frozen rows =
   label+stage+actor only (`has_rupee:false`, no rate/qty/method — matches
   C1's "metadata never rendered"); foreign adda → **403 branded**; assigned
   roll (pk 20) → 200 clean; foreign roll (pk 37) → **403 branded**.
4. **Export wall (V1.1-3 regression check):** all 6 endpoints denied —
   `GET exports/`, `GET download/`, legacy CSV = 403; `POST csv|xlsx|pdf`
   **with valid CSRF** = 403/403/403, zero CSV bytes. No regression.

DB footprint: 2 lazy `BatchBarcode` scan rows stamped by the worker, both
left `pending` — normal floor-scan writes (test-data authorization).

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| Dashboard global `adda_events` + all-Adda table | **VERIFIED SAFE** — worker blocked pre-render; viewers are management-grade |
| Backlog #2 "worker 200 on `/tracking/`" | **STALE** — does not reproduce (blocked via redirect+flash) |
| Worker-block is DB data (SidebarItemRule), not code | **OWNER POLICY** — 0018 panel-driven design, owner-approved |
| Worker scans / status-writes ANY Adda's pieces | **OWNER POLICY** — documented V1.1-3 "workers legitimately scan" |
| Assigned worker sees actor emails + event labels on adda timeline | **OWNER POLICY** — G-AUTH-1 documented scope; zero money rendered |

## Honest caveats

- Dev DB holds zero supplier/cost_per_kg roll-history rows, so the
  financial-row strip was not exercised on live browser data — covered by
  the `FinancialHistoryLeakTests` ×3 pins + C1 code read.
- barcode-list/print have no non-production-role 403 test pin (scan has
  one; identical mixin) — INFO test gap, not a bug; left untouched (scope
  discipline: pins are added only for fixed bugs).

## Verdict

**Tracking worker surface: CERTIFIED.** No bugs found, **no implementation
changes, no new tests, no battery change** (sequential baseline
**1505/1505** from Phase A stands — nothing changed). Certification
strength: artifact-backed (per-URL statuses, exact flash/error quotes, DB
re-checks). Next phase (owner-gated): ~~D — Inventory~~ (→ Phase D below)
→ remaining apps.

---

# Phase D — Inventory app (2026-07-12)

> Scope: the `/inventory/` URL surface — **10 URLs** in
> [inventory/urls.py](../config/inventory/urls.py) (dashboards ×3, styleguide,
> roles CRUD ×4, sidebar-access, access hub). `/tracking/` lives in
> `inventory/tracking_urls.py` but was certified as **Phase C** — not re-audited.
> Audited layers: `urls.py` · 4 non-tracking view modules
> (`dashboard/role_views/sidebar_access_views/access_hub_views`) · `mixins.py` ·
> `SidebarAccessMiddleware` (full read) · `context_processors.py` ·
> `forms/role_forms.py` · `models.py`/`services/__init__.py` (re-export shims) ·
> `signals.py` (comment tombstone, dead) · the whole RBAC core it delegates to
> (`accounts/services/permission_service.py`: `user_has_role` / `user_has_perm` /
> `user_principal` / `build_menu_for` / `can_access_url_name` / SIDEBAR registry) ·
> live `SidebarItemRule` DB rows · all 4 worker-reachable/denied templates.
> 100% main-thread (no sub-agents).

## D1 — code audit (gate map, all 10 URLs)

| # | URL | Gate chain | Worker verdict |
|---|-----|-----------|---------|
| 1 | `my-dashboard/` | `login_required`; middleware-EXEMPT landing (no-loop rule); **internal isolation**: non-mgmt Adda list filtered to active `WorkerStageTask` assignment; accordion/OPEN links = ONE live `stage_access_map` predicate (access ∩ assignment, C-2); `expense_month` built ONLY for `is_admin_view` AND template re-guards it; broadcast rows = code/product/date only (PDD §27-D6) | ALLOWED, own-data-only |
| 2–3 | `dashboard/` + `my-dashboard/legacy/` | `login_required` → 301 to my-dashboard (F-1 twins) | ALLOWED (redirect only, no content) |
| 4 | `styleguide/` | `login_required` TemplateView, static component gallery; the only ₹ on it is a hardcoded demo value ("₹360") — zero DB reads | ALLOWED **by design** (documented in urls.py) |
| 5 | `roles/` | LoginRequired + `SuperAdminOnlyMixin` **+ DB rule `inventory:role_list` with roles=[]** → middleware denies everyone but super-admin (even managers) | BLOCKED (302+flash) |
| 6–8 | `roles/add/` · `roles/<pk>/edit/` · `roles/<pk>/delete/` | LoginRequired + `SuperAdminOnlyMixin` (unmanaged url_names → mixin is the gate; authenticated failure ⇒ `PermissionDenied` ⇒ branded 403); delete additionally guards system roles + in-use roles (primary AND extra_roles, PA-05A-2) | BLOCKED (403) |
| 9 | `sidebar-access/` | LoginRequired + super-admin `UserPassesTestMixin` (dispatch gates GET **and POST**) + DB rule roles=[]; POST upsert excludes `super_admin` role from being granted via form | BLOCKED (302; POST inert) |
| 10 | `access/` | LoginRequired + `SuperAdminOnlyMixin` + DB rule roles=[]; read-only matrices (existing pins: manager + worker denied) | BLOCKED (302+flash) |

Middleware bypass hunt (all clean):
- **AJAX branch**: `X-Requested-With` denial returns JSON 403 `{"detail": "You don't have the access to this page."}` — no redirect corruption, no data.
- **Referer redirect**: same-host check + resolve + re-`can_access_url_name` on the referer → no open redirect, no loop.
- **Exempt set**: exactly the 3 dashboard url_names (landing pages) — nothing privileged.
- **Unmanaged url_names pass middleware by design** → every inventory admin view carries its own SuperAdmin mixin (defense in depth holds even if a DB rule row were mis-edited, and vice-versa: Administration rules have empty role sets, so managers are middleware-blocked too).
- **`can_access_url_name` anonymous→True** is intentional (LoginRequired owns that case).

Hidden-endpoint sweep: **no JSON, no download, no export endpoints** exist under `/inventory/` (the only JSON emitter is the middleware's own denial). The only POST surfaces are roles add/edit/delete + sidebar-access — all super-admin-gated at dispatch.

Sidebar-bypass check (`build_menu_for` precedence): hidden registry twins render for NOBODY (checked before the super-admin bypass); DB-managed items obey `SidebarItemRule`; unmanaged items fall back to in-code predicates (`Administration` section + its items = super-admin/perm-gated) → worker menu = **Main only** (0018 lockdown), and every hidden link's URL is independently gated (middleware or mixin).

D1 verdict: **zero confirmed bugs.**

## D2 — probes (shell + browser, worker `dev.ow.a@test.local`, :8003)

Shell (Django test client, POSTs rollback-wrapped; **manager probed too**):

- Worker GET: my-dashboard **200** · dashboard/legacy **301** · styleguide **200** ·
  roles/ **302→my-dashboard** · roles/add **403** · roles/1/edit **403** ·
  sidebar-access **302** · access **302**.
- **Manager GET** (super-admin surfaces): roles/ **302** · roles/add **403** ·
  roles/1/edit **403** · sidebar-access **302** · access **302** — managers blocked too, as designed.
- Worker POST (rolled back): roles/add **403** (no role created) ·
  roles/1/delete **403** (role survives) · sidebar-access **302** (rule unchanged `[] → []`).

Browser (same worker, live session):

1. Sidebar = **Main only** (My Dashboard, My Earnings) — OP-1/0018 lockdown holds.
2. All 6 admin URLs fetch-probed logged-in: roles/ · sidebar-access/ · access/
   land on my-dashboard; roles/add|edit|delete = branded **403**.
3. Real navigation to `/inventory/access/` → bounced to my-dashboard with flash
   **"You don't have the access to this page."** (exact quote).
4. AJAX probe (`X-Requested-With`) → **JSON 403**, exact body above — middleware
   AJAX branch browser-proven.
5. `POST /inventory/sidebar-access/` **with valid CSRF cookie** → bounced, DB
   re-checked: `inventory:role_list` rule roles still `[]`, no `HACK` role exists.
6. Worker dashboard content sweep: **zero ₹ values** on the page, zero management
   strings (no "Expenses ·"/Payroll/Settlements/Access Control/Roles &
   Permissions/Team Members) — expense digest + admin links never reach a worker.
7. Styleguide renders (by-design 200) — static demo data only.

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| `styleguide/` open to any authed user | **BY DESIGN** — documented in urls.py ("login-only; no business logic"); static gallery, hardcoded demo values, zero DB reads |
| `templates/inventory/dashboard.html` | **ORPHAN** — no view renders it (only `user_dashboard.html` is live); unreachable, left untouched (frozen rules) |
| `RoleForm.permissions` queryset = app-level filter, wider than the curated `ROLE_EDITOR_SECTIONS` allowlist the page displays | **INFO, not a worker bug** — surface is super-admin-only (mixin-proven); a super-admin hand-crafting a POST can only grant perms he already fully controls. Logged for a future admin-hardening pass, untouched (scope discipline) |
| Access hub deep-links to `accounts:user_list` / `skill_list` (user management) | **OUT OF PHASE** — gates live in the accounts app (future phase); the hub page itself is super-admin-only |
| Worker sees all in-progress Adda codes via dashboard broadcast | **OWNER POLICY** — PDD §27-D6 (R1), read-only code/product/date, no link, no money |
| Managers blocked from Administration pages (empty DB rule role-sets) | **AS DESIGNED** — Administration = super-admin-only; double-gated (rule + mixin) |

## Honest caveats

- `signals.py` is a comment-only tombstone (its text references the removed
  `StockService` — historical, inert; not touched).
- `/media/<path>` login-required tier (root `config/urls.py`, owner-approved
  Option 1, 2026-06-11) means any authed user who knows an exact file path can
  fetch non-storefront media — **root-URLConf scope, not inventory**; noted for
  the future accounts/global phase, not a Phase D finding.
- Role edit/delete gate probed on pk=1 (`super_admin` role) — GET gate only;
  the delete POST proof used the same pk and was refused at the mixin (403)
  before any object logic ran.

## Verdict

**Inventory worker surface: CERTIFIED.** No bugs found, **no implementation
changes, no new tests, no battery change** (sequential baseline **1505/1505**
stands — nothing changed). Certification strength: artifact-backed (per-URL
shell+browser statuses, exact flash/JSON quotes, DB re-checks, POST-inertia
proofs, manager cross-checks). Next phase (owner-gated): ~~E — remaining apps~~
(→ Phase E below covers raw_materials; machines / storefront / accounts /
patterns_ai remain).

---

# Phase E — Raw Materials app (2026-07-12)

> Scope: the `/raw-materials/` URL surface — **22 URLs** in
> [raw_materials/urls.py](../config/raw_materials/urls.py) (dashboards ×2,
> rolls ×6, cloth-types ×5, cloth-colors ×5, storage-locations ×5). Audited
> layers: all 4 view modules (`dashboard/roll_views/master_views/assign_views`)
> · [mixins.py](../config/raw_materials/views/mixins.py) · both services
> (`roll_service` incl. damage/restore/leftover · `master_service`) ·
> `forms/` (role-popped price fields) · live `SidebarItemRule` rows · the 5
> worker-relevant templates. 100% main-thread (no sub-agents). Method =
> Phase A's (URL enum → gate-chain audit → shell probe → browser as
> `dev.ow.a` → fix → pins → battery).

## E1 — code audit (gate map, all 22 URLs)

| # | URL group | Gate chain | Worker verdict |
|---|-----------|-----------|---------|
| 1–2 | `/` + `cloth/` dashboards | ProductionRoleMixin + **DB rule Manager-only** (`raw_materials:dashboard`/`cloth-dashboard`) | BLOCKED (302+flash) |
| 3 | `rolls/` list | ProductionRoleMixin + DB rule Manager-only (`roll-list`); financial columns + time-log server-side stripped (`user_can_view_financials`, PA-13-3) | BLOCKED (302+flash) |
| 4 | `rolls/bulk-add/` | SuperAdminOnlyMixin; service re-gates supplier/cost (`user_can_edit_financials`) | BLOCKED (403) |
| 5 | `rolls/<pk>/` detail | ProductionRoleMixin (unmanaged url_name) | ALLOWED **by design** — financials `can_view_financials`-gated in ctx+template; browser-proven zero supplier/cost with cost=₹200 in DB |
| 6 | `rolls/<pk>/edit/` | **ManagementRoleMixin** (M9 fix) + service NOT_USED guard + financial-field gate | BLOCKED (403); pinned test_m9_roll_gates |
| 7 | `rolls/<pk>/damage/` | POST-only, ManagementRoleMixin + service mgmt/reason/used-refusal guards (V1.1-1) | BLOCKED (403) |
| 8 | `rolls/<pk>/assign/` | ManagementRoleMixin (M9) + service layering-stage guards | BLOCKED (403) |
| 9–22 | masters ×3 models: list / add / edit / archive / delete | Lists: ProductionRole + DB rule Manager-only. **Writes: were ProductionRoleMixin + `master_service` PRODUCTION_ROLES → BUG-E1 (fixed)** — now ManagementRoleMixin + MANAGEMENT_ROLES service gate | list BLOCKED (302) · writes BLOCKED (403, was 200) |

Hidden-endpoint sweep: **no JSON/AJAX, no download, no export endpoints** under
`/raw-materials/` (only HTML views; leftover re-issue = service-only
`consume_leftover`, management-gated + row-locked, no URL). Inventory-valuation
leakage: `cost_per_kg`/`supplier` gated at every surface — list columns,
detail panel, both dashboards' time-logs (server-side `.exclude(field_name__in=
('supplier','cost_per_kg'))`), forms (fields POPPED for non-financial), service
writes (`user_can_edit_financials` re-check).

## Bug found → fixed (1)

| Bug | Where | What leaked | Fix | Proof |
|-----|-------|-------------|-----|-------|
| **BUG-E1** | master write views ([master_views.py](../config/raw_materials/views/master_views.py)) + `_ensure_can_manage` ([master_service.py:21](../config/raw_materials/services/master_service.py#L21)) | ProductionRoleMixin + PRODUCTION_ROLES service gate (name trap, same class as BUG-1/M9) — **any worker could create/edit/archive/hard-delete cloth types, colors, storage locations**; middleware blocks only the LIST url_names, writes were unmanaged → mixin was the sole gate. Shell-proven pre-fix: worker POST created + archived a ClothType (real rows, cleaned) | 4 write base views (`_MasterCreateView/_MasterUpdateView/_MasterArchiveView/_MasterDeleteView`) → `ManagementRoleMixin`; `master_service._ensure_can_manage` → `MANAGEMENT_ROLES` ("Only management can modify master data."). Lists untouched (read-only, DB-rule-blocked) | Shell: all 8 write GETs 403, create-POST 403 + row inert; manager 200/200. **Browser (live worker `dev.ow.a`)**: all 15 probed URLs denied; **CSRF-valid POST** `cloth-types/add` → 403, DB re-checked no row |

## E2 — browser evidence (worker `dev.ow.a@test.local`, :8003, live session)

1. Sidebar = **Main only** — no raw-materials entry (0018 lockdown holds).
2. 15-URL fetch probe logged-in: dashboards + all 4 lists → redirect to
   My-Dashboard; bulk-add / roll-edit / roll-assign / all 9 master writes → 403.
3. Real navigation `cloth-types/add/` → branded 403 ("Access denied — Kapil
   Enterprises"); `rolls/` → bounced to my-dashboard with flash **"You don't
   have the access to this page."** (exact quote).
4. POST with valid CSRF cookie → 403, `ClothType` row count unchanged.
5. Roll detail pk=20 (by-design 200): supplier clean · cost clean (DB holds
   cost_per_kg=200.00) · no edit/assign buttons rendered (roll USED); page's
   only ₹ match = a base-stylesheet CSS comment, not data.

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| Roll detail worker-reachable (unmanaged url_name) | **BY DESIGN** — read-only stock fact; financials double-gated (ctx flag + template), browser-proven clean |
| Master lists mixin = ProductionRole (worker) | **DEFENSE-IN-DEPTH OK** — live DB rule = Manager-only blocks workers at middleware; mixin stays second layer; read-only, no money |
| Roll detail Edit/Assign buttons gated by `can_edit` (status-only, not role) | **INFO, template cosmetics** — a worker on a NOT_USED roll would see buttons whose targets 403 (M9 mixin). No leak, no write. Untouched (scope discipline) |
| Master delete-confirm GET = **500 NoReverseMatch** (`{% url list_url_name %}` — DeleteView never injects `list_url_name` into ctx, [master_confirm_delete.html:24](../config/raw_materials/templates/raw_materials/master_confirm_delete.html#L24)) | **OUT-OF-SCOPE DEFECT (management-side)** — reproduced for MANAGER too, pre-existing; fails closed (500, no data/write; the delete POST path itself works). Post-fix a worker gets 403 before the template. Not a worker-permission bug → logged for owner, untouched |
| `consume_leftover` (remnant re-issue) has no URL | **AS DESIGNED** — service-only single writer (C-1/ADR-0009), management-gated, row-locked; V1.1-2 tests stand |

## Tests

[test_master_gates.py](../config/raw_materials/tests/test_master_gates.py)
— 3 pins, all green: worker 403 on 6 representative write URLs + POST
inertia (no row created, archive flag untouched); manager passes (200/302 +
archive lands); service-level `PermissionDenied` for worker on archive +
hard-delete (defence in depth). Existing 38 raw_materials tests unaffected.

## Battery

Sequential (canonical):

- 9-app battery (`accounts core raw_materials production tracking expense
  storefront inventory machines`): **980/980 OK** (169.5s) — includes the
  3 new master-gate pins (Phase-A/D baseline was 977).
- `patterns_ai` (sequential): **528/528 OK** (142.3s).
- Sprint baseline 1505 + 3 new pins = **1508/1508 green**.

## Verdict

**Raw-materials worker surface: CERTIFIED** (1 bug fixed — BUG-E1 master-CRUD
name-trap; gates pinned; no other worker leak in scope). Certification
strength: artifact-backed (shell + live-browser statuses, exact flash/403
quotes, CSRF-POST inertia, DB re-checks, manager cross-checks, pre-fix
exploit proof). Next phases (owner-gated): ~~machines~~ (→ Phase F below) /
**storefront / accounts / patterns_ai**.

---

# Phase F — Machines app (2026-07-12)

> Scope: the `/machines/` URL surface — **5 URLs** in
> [machines/urls.py](../config/machines/urls.py) (list · add · edit ·
> assign · release; mounted mgmt-only per R10-A). Audited layers:
> [views.py](../config/machines/views.py) (the single view module, incl.
> `_ManagementOnly` mixin + `MachineForm`) ·
> [services/machine_service.py](../config/machines/services/machine_service.py)
> (sole writer of Machine + MachineAssignment) ·
> [templatetags/machines_tags.py](../config/machines/templatetags/machines_tags.py)
> (the ops-dashboard tile — the ONLY machines surface rendered outside
> `/machines/`) · all 3 templates (`machine_list/machine_form/_ops_tile`) ·
> models · sidebar registry entry · live `SidebarItemRule` rows · existing
> test pins ([test_r10a.py](../config/machines/tests/test_r10a.py)).
> 100% main-thread (no sub-agents). Method = Phase A's.

## F1 — code audit (gate map, all 5 URLs)

| # | URL | Gate chain | Worker verdict |
|---|-----|-----------|---------|
| 1 | `/machines/` list | `LoginRequiredMixin` + `_ManagementOnly` (`user_has_role(user, MANAGEMENT_ROLES)` = super_admin+manager, dispatch-level `UserPassesTestMixin`) | BLOCKED (403) |
| 2 | `add/` GET+POST | same mixin pair; POST delegates to `machine_service.create_machine`/`create_machine_type` | BLOCKED (403) |
| 3 | `<pk>/edit/` GET+POST | same mixin pair; service adds code-immutable-after-history + status-choice guards | BLOCKED (403) |
| 4 | `<pk>/assign/` POST-only (`View` → GET 405) | same mixin pair → `machine_service.assign` (active-machine + one-open-window + IntegrityError race backstop) | BLOCKED (403) |
| 5 | `assignments/<pk>/release/` POST-only | same mixin pair → `machine_service.release` (already-released + end<start guards) | BLOCKED (403) |

Cross-checks (all clean):

- **No hidden surfaces**: no archive/delete URL (status field via edit = the
  maintenance path), no AJAX/JSON, no downloads/exports, no machine-type CRUD
  URL (type creation only via the mgmt-gated add/edit forms). Assign/release
  forms live inside `machine_list.html` — a page the worker can never render.
- **Middleware**: `SidebarItemRule` rows for machines = **0** (unmanaged
  url_names) → middleware passes by design and the `_ManagementOnly` mixin is
  the gate on every view (Phase-D law: unmanaged ⇒ view carries own mixin ✓).
- **Sidebar**: `Machines` MenuItem predicate = `MANAGEMENT_ROLES`
  ([permission_service.py:289](../config/accounts/services/permission_service.py#L289));
  worker menu = Main only (0018) regardless.
- **Ops tile** (`machines_ops_tile` on the production dashboard): gated INSIDE
  the tag (`user_has_role(user, MANAGEMENT_ROLES)` → `{'show': False}`), and its
  host page (`production:dashboard`) is itself worker-blocked.
- **Service layer**: single-writer holds; zero money (grep-pinned
  `test_money_isolation_grep` — machines never imports expense/cost/rate
  modules); no template/middleware-only protection anywhere; NO
  ProductionRoleMixin-guarding-writes name-trap (the BUG-1/M9/BUG-E1 class)
  — every view is management-gated.

F1 verdict: **zero confirmed bugs.**

## F2 — probes (shell + browser, worker `dev.ow.a@test.local`, :8003)

Shell (Django test client, POSTs rollback-wrapped; manager cross-checked):

- Worker GET list / add / edit → **403 / 403 / 403**.
- Worker POST add (HACK machine + new HackType) / edit (name tamper) /
  assign (self) / release → **403 ×4**; DB inert: 0 machines created,
  name untampered, no open assignment gained.
- Manager GET `/machines/` → **200**.

Browser (live session as the worker):

1. Sidebar = **Main only** — no Machines entry.
2. Fetch probe: list / add / edit GET → 403 ×3; **CSRF-valid POSTs** to
   assign / release / add → **403 ×3**.
3. Real navigation `/machines/` → branded 403 ("Access denied — Kapil
   Enterprises · KE ERROR 403 You don't have access").
4. AJAX probe (`X-Requested-With`) → 403.
5. DB re-checked after all probes: 0 `HACK*` machines, 0 `HackType`
   MachineType, release target untouched; the worker's one open assignment
   (OL-001, pk 6) **predates the probes** (created 2026-07-06, R10 build —
   manager-assigned dev data, not probe fallout).

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| Worker appears in the assign picker / holds assignments | **BY DESIGN** — workers are the assignment SUBJECT (possession windows), never the actor; only management opens/closes windows |
| `MachineAssignView` accepts any user pk as `worker` (no active/production-role filter on POST despite the filtered picker) | **INFO, management-side data validation** — actor must already be management; no worker-permission impact. Untouched (scope discipline) |
| Ops tile on production dashboard | **VERIFIED SAFE** — double-gated (tag-internal mgmt check + host page worker-blocked) |
| No SidebarItemRule rows for machines url_names | **AS DESIGNED** — unmanaged ⇒ mixin is the gate (all 5 views carry it); consistent with Phase-D law |

## Honest caveats

- Existing pin `test_worker_403_everywhere` covers list+add GET only;
  edit/assign/release worker-403 are shell+browser-proven this phase but
  carry no test pin — **INFO test gap, not a bug**; pins are added only for
  fixed bugs (scope discipline, same posture as Phase C).
- Assignment-history visibility to workers: none exists — no worker-facing
  page renders MachineAssignment anywhere (checked: the only templates are
  the three above, all mgmt-only).

## Verdict

**Machines worker surface: CERTIFIED.** No bugs found, **no implementation
changes, no new tests, no battery change** (sequential baseline **1508/1508**
from Phase E stands — nothing changed). Certification strength:
artifact-backed (shell + live-browser statuses, branded-403 quote,
CSRF-POST + AJAX inertia, DB re-checks, manager cross-check). Next phases
(owner-gated): ~~storefront~~ (→ Phase G below) / **accounts / patterns_ai**.

---

# Phase G — Storefront app (2026-07-12)

> Scope: `config/storefront/` ONLY — **8 authenticated URLs** in
> [storefront/urls.py](../config/storefront/urls.py) (product list/add/edit/
> delete + category list/add/edit/delete, mounted at `/storefront/`) plus the
> anonymous public homepage (`public_home` mounted at `/` by root urlconf).
> Audited layers: [listing_views.py](../config/storefront/views/listing_views.py)
> (all 8 CBVs + `ListingTeamMixin`) ·
> [public_views.py](../config/storefront/views/public_views.py) ·
> [forms.py](../config/storefront/forms.py) ·
> [services/image_service.py](../config/storefront/services/image_service.py) +
> `processors.py` + `widgets.py` (image pipeline — no permission logic, by
> design view-gated) · models · admin.py · both template dirs · sidebar
> registry (`STOREFRONT_ROLES`) · live `SidebarItemRule` rows · existing tests.
> 100% main-thread (no sub-agents). Method = Phase A's.

## G1 — code audit (gate map)

| # | URL | Gate chain | Worker verdict |
|---|-----|-----------|---------|
| 1 | `products/` list | `LoginRequiredMixin` + `ListingTeamMixin` (`user_has_role(user, {ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM})`, dispatch-level `UserPassesTestMixin`) **+ DB rule `storefront:product_list` roles=[listing_team]** → middleware redirects everyone else (super-admin bypass is service-hardcoded) | BLOCKED (302+flash) |
| 2–4 | `products/add\|edit\|delete` | same mixin pair (unmanaged url_names → mixin is the gate; authenticated failure ⇒ `PermissionDenied` ⇒ branded 403) | BLOCKED (403) |
| 5 | `categories/` list | mixin pair + DB rule `storefront:category_list` roles=[listing_team] | BLOCKED (302+flash) |
| 6–8 | `categories/add\|edit\|delete` | same mixin pair, unmanaged | BLOCKED (403) |
| — | `/` public homepage | **no auth BY DESIGN** (ADR-0008 public face); renders only storefront display models — marketing price/MRP, never production money/quantities | ALLOWED (anonymous) |

Specific hunts (all clean):

- **ProductionRoleMixin protecting writes / missing STOREFRONT_ROLES**: the
  name-trap class (BUG-1/M9/BUG-E1) does NOT exist here — every one of the 8
  views carries `ListingTeamMixin`, which IS the `STOREFRONT_ROLES` set
  (`{super_admin, listing_team}`, [permission_service.py:31](../config/accounts/services/permission_service.py#L31)).
  No ProductionRoleMixin import anywhere in the app.
- **Middleware-only / template-only protection**: none — lists are
  double-gated (DB rule + mixin), writes mixin-gated at dispatch; no raw
  `is_staff`/`is_superuser` checks, no `request.user` logic in templates.
- **Hidden POST / AJAX / downloads**: none exist — 8 URLs + public GET `/`
  are the entire surface; only JSON emitter anywhere is the middleware's own
  denial. Image upload is NOT a separate endpoint — it rides the add/edit
  POSTs (forms → `image_service.process_and_attach`, pure Pillow, no perms
  needed beyond the view gate).
- **Service-layer permission mistakes**: `image_service` is the only service
  (the old ListingService pass-through was removed); it holds no permission
  logic by design — single-row CMS CRUD is CBV-owned, gate lives at dispatch.
- **manager access**: managers are NOT in `STOREFRONT_ROLES` → blocked
  everywhere (probed, below) — as designed, listing_team is the editor role.
- **Money boundary (ADR-0008)**: `FeaturedProduct.price/original_price` =
  public marketing display values on the anonymous homepage, not production
  money; no FK/import touches production/expense; anon homepage grep =
  zero payroll/settlement/adda strings.
- **Django admin registrations** (admin.py): `/admin/` root-scope
  (`is_staff` gate, Django-owned) — same posture as Phase D's media caveat,
  out of app scope.

G1 verdict: **zero confirmed bugs.**

## G2 — probes (shell + browser, worker `dev.ow.a@test.local`, :8003)

Shell (Django test client; worker + manager + listing_team):

- Worker GET: lists **302→my-dashboard** ×2; add/edit/delete **403** ×6.
- Manager GET: identical — **302 ×2, 403 ×6** (not a storefront role).
- listing_team (`dev.listing@test.local`) GET: **200 ×8** — editor works.
- Worker + manager POST (add product `HACK`, delete product 1, add category
  `HACKCAT`, delete category 1) → **403 ×8**; DB inert: counts unchanged,
  no HACK rows, both pk-1 rows survive.

Browser (live session as the worker, identity re-verified on-page):

1. Sidebar = **Main only** — no Storefront section (predicate =
   `STOREFRONT_ROLES`; 0018 lockdown regardless).
2. Real navigation to both lists → bounced to my-dashboard.
3. Fetch probe: all 6 write URLs GET → **403 ×6**.
4. **CSRF-valid POSTs** (real csrftoken cookie) to product-add +
   category-1-delete → **403/403**; DB re-checked: no `HACK-BROWSER`
   product, category pk 1 survives.
5. Anonymous `/` → **200**, zero production-domain strings
   (payroll/settlement/adda grep empty).

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| Public homepage shows prices with no auth | **BY DESIGN** — ADR-0008 commerce face; marketing display price on FeaturedProduct, zero production money |
| Managers blocked from storefront editor | **AS DESIGNED** — `STOREFRONT_ROLES` = super_admin + listing_team only |
| `fields = '__all__'` on storefront forms | **INFO, not a bug** — models are pure display-config rows (no perms/role/money fields to mass-assign); surface is listing_team-gated at dispatch |
| HomePageConfig / HeroShowcaseCard / WhyUsCard / Foot-NavLink have no front-end CRUD | **AS DESIGNED** — Django-admin-only (root `is_staff` scope), no storefront URL exposes them |
| `/media/storefront/*` public serve | **BY DESIGN** — homepage assets for the anonymous storefront (documented in root urls.py); root-URLConf scope, not this app |

## Honest caveats

- No test pin exists for the storefront view gates (`storefront/tests.py` =
  image-pipeline tests only) — **INFO test gap, not a bug**; worker/manager
  403s are shell+browser-proven this phase; pins are added only for fixed
  bugs (scope discipline, same posture as Phases C/F).
- `dev.listing@test.local` proven via shell force-login (200 ×8); the
  browser pass used the worker only — the listing_team browser path was not
  separately driven (nothing changed that would need it).

## Verdict

**Storefront worker surface: CERTIFIED.** No bugs found, **no implementation
changes, no new tests, no battery change** (sequential baseline **1508/1508**
from Phase E stands — nothing changed). Certification strength:
artifact-backed (shell 3-role matrix, live-browser statuses, CSRF-POST
inertia, DB re-checks, anonymous-homepage leak scan). Next phases
(owner-gated): **accounts / patterns_ai** — then, per owner direction, one
final meta-audit closes the campaign (no new work directly after Phase I).

---

# Phase H — Accounts app (2026-07-12; S2+S3 fixed, S1 verified safe — see H3/H4)

> H1 code audit (prior session) surfaced 3 suspects: **S1** inactive-user
> login via custom OTP flow · **S2** public signup via `/accounts/signup/` ·
> **S3** worker email-change via `/accounts/email/`. Owner ordered:
> H2A/H2B browser-verify S2 → S2 confirmed → **freeze rest of Phase H**
> (S1/S3 NOT tested, S2 = only active item). This section records S2 only.

## H2A/H2B — browser confirmation (anonymous, :8003)

- H2A: `GET /accounts/signup/` → **200**, full signup form
  (`email`/`password1`/`password2`, action=`/accounts/signup/`), no login wall.
- H2B: one CSRF-valid anonymous POST (`dev.h2b.temp@test.local`) →
  **302 → `/app/home/`** (auto-login, no OTP step); DB check:
  `accounts.User` pk=73 **created, `is_active=True`** + linked
  `account.EmailAddress`. Cleanup: both rows deleted, count restored 48→47.

**S2 = CONFIRMED BUG**: anonymous public signup created a live active ERP
user — direct violation of the owner invariant "Internal ERP =
pre-provisioned users only" (PA-02-OPEN-SIGNUP).

## Root cause

PA-02 closed only the **native** signup: `/app/signup*` routes removed
(`accounts/urls.py`), login pages stripped of signup links — all pinned by
`SignupDisabledTests`. But root `config/urls.py` mounts **allauth wholesale**
at `/accounts/` (needed for Google OAuth), which exposes `account_signup`.
The social half was gated (`SOCIALACCOUNT_ADAPTER =
RestrictedSocialAccountAdapter`, `is_open_for_signup=False` +
`pre_social_login` pre-provision check), but **`ACCOUNT_ADAPTER` was never
set** → allauth's `DefaultAccountAdapter.is_open_for_signup() == True` →
local email+password signup stayed open. (tests.py's module docstring even
claimed adapter coverage that didn't exist — docstring drift, now real.)

## Fix (smallest possible — 1 adapter class + 1 settings line)

| File | Change |
|------|--------|
| [allauth_adapters.py](../config/accounts/allauth_adapters.py) | new `RestrictedAccountAdapter(DefaultAccountAdapter)` — `is_open_for_signup() → False`; everything else (login, reset emails) stays default |
| [settings/base.py](../config/config/settings/base.py) | `ACCOUNT_ADAPTER = "accounts.allauth_adapters.RestrictedAccountAdapter"` next to the social twin |

allauth's `CloseableSignupMixin` then renders `account/signup_closed.html`
on **both GET and POST** — form never processed, no User possible.
Untouched: password login, OTP login, password reset, Google OAuth
(social adapter path). `/accounts/email/` (S3) was frozen at the time of
this S2 section; it is now fixed — see **Phase H4** below.

## Browser proof after fix

- `GET /accounts/signup/` → 200 **"Sign Up Closed"**, `<form>` count = 0.
- Exact H2B replay (CSRF-valid POST, `dev.s2fix.temp@test.local`) →
  **200 "Sign Up Closed"**, no redirect, `EXISTS: False`, user count 47.
- No-CSRF POST → 403 (closed page issues no token).
- `/app/` login 200 · Google button (`/accounts/google/login/`) present + 200.

## Tests (6 new pins, [tests.py](../config/accounts/tests.py))

- `SignupDisabledTests.test_allauth_signup_get_is_closed` — closed template, not a form.
- `SignupDisabledTests.test_allauth_signup_post_creates_no_user` — POST inert, zero Users.
- `AllauthAdapterTests` ×4 — both adapters closed for signup; Google
  pre-provisioned email auto-links (`SocialAccount` created); unprovisioned
  Google email refused (redirect → login, no User) — first REAL pins for the
  social adapter (previously docstring-only).

## Battery

Sequential canonical: 9-app **986/986** (171.4s) + patterns_ai **528/528**
(141.3s) = **1514/1514** (baseline 1508 + 6 new pins).

## Honest caveats

- **This S2 section was written before S1/S3 were resolved.** S1 and S3 were
  since verified in their own owner-gated turns — **Phase H3** (S1 = safe) and
  **Phase H4** (S3 = fixed) below. Full accounts certification still needs a
  sweep of the wider `/app/` + `/accounts/` surface beyond the three suspects.
- Google OAuth proven at adapter level (unit pins) + endpoint/button
  liveness; a full live Google handshake was not driven (needs real Google
  creds — same posture as before the fix, no regression path exists since
  the social adapter is untouched).

## Verdict

**S2 FIXED + pinned (this section).** S1 and S3 resolved in later
owner-gated turns — see **Phase H3** and **Phase H4** below.

---

# Phase H3 — S1 inactive-user OTP login (2026-07-12, VERIFIED SAFE)

> Scope: S1 ONLY. Question: can an `is_active=False` user complete the custom
> OTP login (`/app/` → `/app/verify-otp/`) and gain access?

## Answer: NO — inactive account is inert (no fix needed)

Browser-proven as `dev.leaver@test.local` (is_active=False) on :8003:

- `/app/` → submit email → redirect to `/app/verify-otp/` (OTP send succeeded;
  dev has live SMTP, so the code went to an inbox we can't read — the only step
  the browser can't finish unaided).
- Smallest probe: seeded a known OTP (`123456`) into that **live server
  session** (substituted only the undeliverable code; verify → `login()` →
  next-request all ran for real over HTTP).
- Entered `123456` → **landed on `/app/?next=/app/home/`** (the login page, not
  the app). Direct nav while "logged in": `GET /app/home/` → bounced to
  `/app/?next=/app/home/`; `/inventory/my-dashboard/` → bounced likewise;
  authed-content check `false`.

**Why safe (mechanism):** [`VerifyOTPView.post`](../config/accounts/views.py#L167)
calls `login()` with no `is_active` guard, so `login()` *does* write the session
(`_auth_user_id`, backend=`ModelBackend`). But every protected view is
`@login_required`/`LoginRequiredMixin`, and on each request
`AuthenticationMiddleware` → `auth.get_user()` → `ModelBackend.get_user()` →
`user_can_authenticate()` returns `None` when `is_active=False` → request user =
**AnonymousUser**. Server-side proof on the post-login session: `_auth_user_id`
set to the inactive user, yet `get_user(request) -> AnonymousUser`. No leak in
the login request itself (the POST returns a redirect before any protected
content renders). Stock Django 5.0.1 backstop; the missing view-level check is
cosmetic, not exploitable.

**No code / test / doc change** (NO-branch: verified safe, engine frozen).
Transient seeded sessions cleaned up; inactive users untouched.

---

# Phase H4 — S3 worker email self-service (2026-07-12, CONFIRMED + FIXED)

> Scope: S3 ONLY. Question: can a normal worker use allauth's email-management
> page (`/accounts/email/`) to change their primary email — violating the
> "pre-provisioned users only" invariant?

## Answer: YES — real violation (now fixed)

**Browser-proven** as worker `dev.ow.a@test.local` (non-management, is_active=True):

1. `GET /accounts/email/` → **200**, full allauth email page: **Add Email**,
   **Make Primary**, **Re-send Verification**, **Remove**.
2. Added a self-chosen address `worker-selfchosen@evil.local` → "Confirmation
   email sent", address listed (Unverified).
3. Selected it, **Make Primary** → "Primary email address set."
4. DB check: allauth synced primary into **`User.email = worker-selfchosen@evil.local`**;
   the provisioned `dev.ow.a@test.local` **no longer resolved** the user. Since
   the OTP login does `User.objects.filter(email__iexact=email)`, the worker had
   just repointed their own login identity to an arbitrary, **unverified**,
   self-chosen address — with no admin involvement. Breaks pre-provisioned-only
   (PA-02), same class as the S2 signup hole.

## Root cause

Root `config/urls.py` mounts **allauth wholesale** (`include("allauth.urls")`).
S2 closed signup via the adapter, but allauth's `EmailView` (`account_email` at
`/accounts/email/`, the sole email-management route in allauth 0.61.1 — handles
add / remove / make-primary) stayed open to any signed-in user. allauth 0.61.1
has **no adapter hook** for "is email management open," so the fix shadows the
route.

## Fix (2 files, surgical)

| File | Change |
|------|--------|
| [accounts/views.py](../config/accounts/views.py) | new `EmailManagementDisabledView(LoginRequiredMixin, View)` — GET bounces to `accounts:home` with an info flash; POST refuses + logs `email_selfservice_blocked` to the security channel. No allauth logic runs. |
| [config/urls.py](../config/config/urls.py) | `path("accounts/email/", EmailManagementDisabledView.as_view())` mounted **BEFORE** `include("allauth.urls")` → top-down resolution stops here for both GET and POST. Same path string ⇒ `reverse("account_email")` still resolves (allauth templates safe). Google OAuth, password reset, confirm-email routes untouched. |

## Browser proof after fix

- Worker `GET /accounts/email/` → **302 → `/inventory/my-dashboard/`** (allauth
  email page gone; `account/email.html` never rendered).
- Worker `POST /accounts/email/` `action_add` with valid CSRF → **302 →
  `/app/home/`**; DB re-checked: **zero** `EmailAddress` created, `User.email`
  still `dev.ow.a@test.local`.

Mutated dev worker fully restored before/after; no residual data.

## Tests (5 new pins, [tests.py](../config/accounts/tests.py) `EmailManagementDisabledTests`)

- `test_reverse_account_email_still_resolves` — reverse kept at `/accounts/email/`.
- `test_worker_get_email_page_is_shadowed` — 302, `account/email.html` never used.
- `test_worker_add_email_post_creates_nothing` — POST refused, zero `EmailAddress`, identity unchanged.
- `test_worker_make_primary_post_does_not_change_identity` — make-primary refused even with a pre-existing second address; `User.email` unchanged.
- `test_anonymous_is_sent_to_login` — anonymous hit → login page (`login_url`).

## Battery

Sequential canonical: 9-app **991/991** (167.6s) + patterns_ai **528/528**
(143.1s) = **1519/1519** (baseline 1514 + 5 new pins).

## Phase H status

- **S2 FIXED** (allauth signup closed) · **S3 FIXED** (email management shadowed)
  · **S1 VERIFIED SAFE** (inactive login inert, no fix).
- Remaining before full accounts certification: broader `/app/` + `/accounts/`
  surface sweep beyond the three suspects (owner-gated, not in H3/H4 scope).

---

# Phase I — patterns_ai app (2026-07-12, CERTIFIED — 0 bugs, 0 changes)

> Scope: the `/patterns/` URL surface — **55 routes** in
> [patterns_ai/urls.py](../config/patterns_ai/urls.py) → **52 view classes** in
> [patterns_ai/views.py](../config/patterns_ai/views.py). Audited layers:
> every view class + its gate mixin, the `_ManagementOnly` mixin, the one
> perm-gated view (`PatternBlueprintView`), the live `patterns_ai:home`
> SidebarItemRule + MENU REGISTRY entry, `can_access_url_name` behavior for
> managed vs unmanaged routes, and the existing worker-403 test pins.
> 100% main-thread (audit-honesty rule; no sub-agents).

## I1 — code audit (gate map)

**One gate law, applied to every route.** 51 of 52 view classes are
`LoginRequiredMixin + _ManagementOnly`; the lone exception is
`PatternBlueprintView` (a stricter perm gate). No route is ungated (grep:
every `class …View(` signature line carries `LoginRequiredMixin`).

| Layer | Rule | Worker outcome |
|-------|------|----------------|
| `_ManagementOnly` ([views.py:28](../config/patterns_ai/views.py#L28)) | `user_has_role(user, MANAGEMENT_ROLES)`; Django `handle_no_permission` **raises PermissionDenied when the user is authenticated** ⇒ branded 403 (anon ⇒ login) | 403 on 51 routes (GET **and** POST — dispatch-level) |
| `PatternBlueprintView` ([views.py:649](../config/patterns_ai/views.py#L649)) | `user_has_perm(user, 'production.change_productpattern')` + super-admin bypass — by design, structure edits are admin-level (stricter than management) | 403 (worker holds no such perm) |
| Middleware | `patterns_ai:home` is the **only** managed url_name (SidebarItemRule roles=`{manager, super_admin}`); the other 54 routes are unmanaged ⇒ `can_access_url_name → True`, so the **view mixin is the gate** (identical defense-in-depth to Phase D inventory admin) | home → 302 redirect; rest → view-mixin 403 |
| Sidebar | MENU REGISTRY 'Pattern Intelligence' → `patterns_ai:home`, section Production, gated by the same rule | worker menu = **Main only**, no Pattern link |

I1 verdict: **zero confirmed bugs.** No name-trap (the gate is `MANAGEMENT_ROLES`
directly, not a mislabeled PRODUCTION `_ensure_can_manage` — the BUG-1 / BUG-E1
class is absent). Services are all behind the dispatch gate; management commands
are CLI-only.

## I2 — probes (shell + browser, worker `dev.ow.a@test.local`, :8003)

**Shell (test client, all 55 routes):** reversed every route with dummy ids
(mixin runs at dispatch, before object lookup) → **50× 403 + 1× 302** (`home`,
middleware redirect); the one mismatch was a probe-arg typo (`outcome-new` takes
`pk`, re-probed → **403**). 8 representative write POSTs
(`manual-marker-new`, `generate`, `table-save`, `candidate-approve`,
`usage-void`, `mat-new`, `version-confirm`, `pattern-capture`) → **all 403**;
DB re-checked, **no `Marker` created**.

**Browser (fresh worker session):**
- Sidebar = **Main only** (My Dashboard, My Earnings); "Pattern Intelligence"
  absent.
- Direct nav: `/patterns/` → 302 to my-dashboard + flash "You don't have the
  access to this page."; `/patterns/studio/`, `/generate/`, `/dashboard/`,
  `/blueprint/`, `/insights/` → stay on-URL, render the **branded "Error 403 —
  You don't have access"** page (title `Access denied — Kapil Enterprises`),
  zero business content.

## Suspect classification

| Suspect | Verdict |
|---------|---------|
| Unmanaged patterns routes → `can_access_url_name` returns True | **BY DESIGN** — Phase-D law; the per-view `_ManagementOnly` mixin is the gate, proven 403 on all 51 |
| `PatternBlueprintView` uses a perm gate, not `_ManagementOnly` | **BY DESIGN** — stricter (admin-level structure edits); still excludes workers (no `change_productpattern`), 403 proven |
| Pattern media (capture photos / SVG / PDF) served to workers | Thumb/SVG/DXF/PDF/print views are all `_ManagementOnly` (403 proven). Raw `/media/<path>` login-tier fetch = **root-URLConf carry-over** (Phase-D caveat, owner-approved Option 1), NOT a patterns_ai finding |

## Existing coverage (no new pins — nothing was fixed)

Worker-block is already pinned across the app, e.g.
`test_phase2_blueprint.test_worker_403_and_get_writes_nothing`,
`test_block3b_workflow.test_worker_forbidden_get_and_post`,
`test_p4_advisor.test_worker_cannot_post_decisions`,
`test_phase6_m6/m7.test_worker_403`,
`test_services_block2b.test_gate_management_only`,
`test_phase3_universal.test_dashboard_carries_button_and_worker_403`.

## Honest caveats

- No code changed ⇒ **battery not re-run** (methodology: rerun only on code
  change). Current patterns_ai sequential baseline **528/528** stands (from the
  Phase H4 run this session).
- Cross-*manager* object scoping (which manager sees which Adda's patterns) was
  not audited — out of scope for **worker**-role certification (workers reach
  nothing here).

## Verdict

**patterns_ai worker surface: CERTIFIED.** No bugs found, **no implementation
changes, no new tests, no battery change.** Certification strength:
artifact-backed (55-route shell status matrix, write-POST inertia + DB re-check,
browser sidebar + branded-403 quotes). Every `/patterns/` route is
worker-blocked at the view layer; the app is management/admin-only by
construction.


---

## FINAL META-AUDIT — evidence section (memory-recovered 2026-07-13, Phase-7 Q-A3)

> **Provenance (honest):** this meta-audit ran 2026-07-12 and closed the certification
> campaign, but its detail survived ONLY in agent memory (framework README risk #2; PHASE_06
> Campaign-Approval amendment, seed 5; discovery finding F-A-06). Recovered onto disk
> 2026-07-13 verbatim from `project_v11_sprint_2026_07_12.md`. Provenance class =
> memory-recovered (weaker than the per-phase artifact-backed sections above — no separate
> on-disk probe artifacts exist for the meta-audit itself; the per-phase evidence it
> aggregates IS on disk above). Nothing here was newly authored.

**VERDICT (2026-07-12): ERP WORKER-PERMISSION MODEL CERTIFIED COMPLETE — cross-phase, 0
global issues, 0 code changes.** The eleven global verifications (main-thread):

1. Coverage = 10 non-vendor apps; 9 URL-bearing all certified; `core` = infra, no URLs.
2. All 12 root-URLConf includes accounted for — `/admin/` staff-gated (worker
   `is_staff=False` → bounces to `/admin/login/`; ZERO staff-non-superuser users exist);
   `/media/<path>` = login-tier carry-over (owner Option 1); allauth plumbing self-scoped.
3. Root URLConf consistent (S3 email-shadow route correctly precedes the allauth include;
   explicit error handlers; 2-tier media).
4. MIDDLEWARE order correct (`SidebarAccessMiddleware` LAST, post-AuthenticationMiddleware).
5. `permission_service` = SINGLE source for role-sets (MANAGEMENT={sa,mgr} ·
   STOREFRONT={sa,listing} · PRODUCTION={sa,mgr,worker}); no divergent local definitions; no
   raw `is_superuser` GATES (grep hits = comments/read-only display/user-CRUD form only).
6. `SidebarAccessMiddleware` sound: exempt = 3 dashboards; anon-pass; unmanaged →
   `can_access_url_name` True → view-mixin gates; AJAX → JSON 403; same-host referer
   re-check = no open redirect/loop.
7. Auth boundaries: `LOGIN_URL=/app/`.
8. **Cross-app worker isolation UNIFORM** — every management URL across all 9 apps → 302
   (managed url_name, middleware) or 403 (unmanaged, view mixin); ZERO 200 leaks; worker
   sidebar = Main only.
9. Certification doc: 9 phase headers; battery chain converges 1499→1505→1508→1514→1519; no
   stale contradictions.
10. MEMORY/GUIDE/DOCUMENTATION_INDEX synced; no stale strings.
11. DEPLOYMENT_BACKLOG all 5 then-entries valid (#2 resolved-Phase-C · #1/#3/#4 non-permission
    polish/infra · #5 management-side delete-confirm 500 fails closed, correctly out of
    worker scope) — NONE are worker-permission bugs.

**Systemic risk class identified:** management-write mis-gated as PRODUCTION_ROLES (the
BUG-1/BUG-E1 name-trap); the campaign found and fixed the known instances. **Genuine
remaining worker-permission issues: NONE.** Two documented non-worker carry-overs for future
phases: media exact-path fetch by any authenticated user; deeper allauth hardening (e.g.
password-reset enumeration). Campaign closed 2026-07-12; no commits (owner checkpoint
policy).
