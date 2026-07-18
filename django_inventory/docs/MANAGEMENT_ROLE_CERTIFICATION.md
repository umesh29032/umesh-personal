---
id: management-role-certification
type: evidence-cert
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Management Role Certification — Campaign Phase 1

> Pre-deployment campaign, opened 2026-07-12 (MGT-0). Sibling of
> [WORKER_ROLE_CERTIFICATION.md](WORKER_ROLE_CERTIFICATION.md) (CLOSED, 9 apps + meta-audit).
> Campaign resume anchor: [DEPLOYMENT_CAMPAIGN_STATUS.md](DEPLOYMENT_CAMPAIGN_STATUS.md).
> Engine FROZEN — fix ONLY confirmed bugs, pins only for fixes, battery rerun only on code change.

## What this certifies (three questions, per app)

The `manager` role (MANAGEMENT_ROLES = {super_admin, manager}) is certified on THREE axes —
worker certification asked only "is the worker blocked?"; management certification also asks
"does the manager's job actually work?":

1. **BLOCKED where required** — manager must NOT reach:
   - Administration surfaces: roles CRUD · sidebar-access · access hub · Team Members · User Skills
     (super-admin-only, double-gated: SuperAdminOnlyMixin + empty SidebarItemRule role-sets — Phase D law)
   - Storefront editor (STOREFRONT_ROLES = super_admin + listing_team; manager excluded by design, Phase G proven)
   - Financial fields `supplier` / `cost_per_kg` — view AND edit (FINANCIAL_ROLES = super_admin + accountant;
     manager sees NEITHER, at all 4 layers: form / service / template / history strip)
   - Super-admin-only actions: roll bulk-add (SuperAdminOnlyMixin) · `rerate_stage_role` rate correction ·
     settlement reconciliation override (S5) · `PatternBlueprintView` perm gate (unless perm granted)
2. **ALLOWED where required** — every MANAGEMENT_ROLES surface reachable; no false 403/302.
3. **FUNCTIONAL when allowed** — allowed pages render (no 500s) and mgmt writes work.
   Precedent: DEPLOYMENT_BACKLOG #5 (master delete-confirm 500, reproduced AS MANAGER) = this class,
   already CONFIRMED → scheduled fix in MGT-E.

## Certification identity

- **`dev.mgr@test.local` / Dev@12345** — verified 2026-07-12 (MGT-0): exists, active,
  primary_role=manager, extra_roles=[], is_superuser=False, skills=0 (clean pure-manager probe identity).
- Cross-check identities: super_admin `umesh29mar@gmail.com` (positive control) ·
  worker `dev.ow.a@test.local` (regression spot-checks).
- Login via `/app/login/password/` (bypasses OTP). Rate-limited per IP+email — type carefully.
- 4 other manager accounts exist (manager1@test.local, mgmt1@test, mgmt2@test, dev.manager@test.local —
  the latter does NOT use Dev@12345); not used unless a scenario needs a second manager.

## Method (locked, per sub-phase — the 10 steps)

1. Read app docs + urls.py. 2. Gate-map audit per URL (mixin → SidebarItemRule → service gate → template ctx).
3. Shell probe as manager (test client; POSTs rollback-wrapped; super_admin cross-check; worker spot-check).
4. Browser as `dev.mgr` on :8003 (real navigation + CSRF-valid POSTs; DEV-marked data only).
5. Fix ONLY confirmed bugs. 6. Regression pins ONLY for fixes. 7. Sequential battery ONLY if code changed
(baseline **1519/1519**). 8. Docs-sync (this file's section + app GUIDE/README if code touched).
9. Update DEPLOYMENT_CAMPAIGN_STATUS.md + memory. 10. STOP — next sub-phase is owner-gated.

## Evidence standard (artifact-backed, Phase-B lesson)

Every verdict carries its probe: per-URL status matrix (shell + browser) · exact flash/error quotes ·
CSRF-valid POST inertia with DB re-check · rollback-wrapped shell writes · positive-control (super_admin)
and regression (worker) cross-checks. "Looks correct in code" is never a verdict. Owner-attested
close-outs are a fallback only, and marked as such. Sub-agent findings are supplemental —
no surface is marked clean on sub-agent silence (audit-honesty rule); finder failures are recorded.

## Resumability

A fresh session continues from **DEPLOYMENT_CAMPAIGN_STATUS.md** (sub-phase checklist + next action)
plus this file (evidence so far). No chat history required. Each sub-phase appends ONE section below
at close; never edit a closed section (append corrections).

## Sub-phases

| # | Scope | Size driver | Status |
|---|-------|-------------|--------|
| MGT-0 | Charter: identity verified · skeleton + status file · methodology locked | tiny | ✅ DONE 2026-07-12 |
| MGT-A | Production 1/2 — mgmt CRUD: dashboards, Adda list/detail/start, products, patterns, stage library, flow editor, costing, stage-rates (**rerate = super-admin-only → manager BLOCKED probe**) | production = 85 URLs, split | ✅ 2026-07-12 — 0 bugs, 0 code changes |
| MGT-B | Production 2/2 — stage operations: start/assign/complete/reopen, layering+cutting consoles, pools, bundle-sets, review-reports, barcode generation (stalled/pending-reports were certified in MGT-A) | second half | ✅ 2026-07-12 — **1 bug FIXED (MGT-B-1 lane 500s)**, 3 pins, battery 1522/1522 |
| MGT-C | Expense (money core, 13 URLs): payroll, settlement lifecycle, advances, pay-basis, FnF, factory expenses. Manager CAN operate money; super-admin-only override BLOCKED. Money-Write STOP rule + hostile mindset | highest stakes | ✅ 2026-07-12 — 0 bugs, 0 code changes; 4 SA-splits proven; ledger integrity intact |
| MGT-D | Tracking (13: dashboard + exports = manager-ALLOWED; history financial-strip applies to manager) + Inventory (10: Administration negative re-confirm, dashboards positive) | two small apps | ✅ 2026-07-12 — 0 bugs, 0 code changes; Phase-D law + financial-strip proven live |
| MGT-E | Raw Materials (23): masters/rolls positive · bulk-add negative · supplier/cost hidden at ALL 4 layers · **FIX DEPLOYMENT_BACKLOG #5** (delete-confirm 500; fix spec in backlog) + pin + battery | one app + one pre-confirmed fix | ✅ 2026-07-12 — **backlog #5 FIXED** (delete-confirm 500 ×3 masters), 2 pins, battery **1524/1524**; 1 new INFO → backlog #7 |
| MGT-F | Machines (5, positive incl. assign/release; judge INFO: assign accepts any user-pk) + Storefront (8, manager-blocked regression spot) + Accounts (20: Team Members/Skills super-admin-only → manager blocked; manager login works) | three small surfaces | ✅ 2026-07-12 — **1 bug FIXED (MGT-F-1** machine-code immutability guard bypassed via edit form**)**, 2 pins; any-user-pk carry-over JUDGED → INFO → backlog #8; storefront + accounts 0 bugs, S2/S3 hold |
| MGT-G | patterns_ai (52 routes): manager-positive sample-render + write probes · blueprint perm-gate · **cross-manager object scoping** (Phase-I logged caveat, first audit) | one gate law, big count; split fallback | ✅ 2026-07-12 — **0 bugs, 0 code changes**; cross-manager isolation JUDGED = **BY DESIGN ABSENT (shared management workspace over product-anchored factory knowledge)**, runtime-proven B→A chains with actor-stamp integrity; 1 INFO → backlog #9 (void/retire actor stamps); battery NOT re-run (1526/1526 stands) |
| MGT-H | Meta-audit: manager sidebar vs matrix · SidebarItemRule sweep · cross-app uniformity (no 200-leaks into admin surfaces, no false 403s) · final verdict · battery status · docs+memory sync | mirrors worker meta-audit | ✅ 2026-07-12 — **0 bugs, 0 code changes**; 528-route census + 95-route dual-identity sweep ZERO anomalies; sidebar 19/19 reachable; **PHASE 1 VERDICT: MANAGEMENT PERMISSION MODEL CERTIFIED** |

## Prior manager evidence (reused, spot-confirmed only — not redone)

- Worker-cert Phase D: manager blocked on all 5 Administration URLs (302/403) ✓
- Phase E: manager passes master writes (200/302 + archive lands) ✓
- Phase F: manager GET /machines/ = 200 ✓
- Phase G: manager blocked on all 8 storefront URLs (302 ×2, 403 ×6) ✓

## Carry-overs into this certification

| Item | Disposition |
|---|---|
| DEPLOYMENT_BACKLOG #5 — master delete-confirm 500 (manager + super-admin repro) | CONFIRMED → fix in MGT-E |
| Phase F INFO — MachineAssignView accepts any user pk as worker | JUDGED in MGT-F 2026-07-12: **INFO → DEPLOYMENT_BACKLOG #8** — probes proved assignment rows created to a listing_team AND an inactive user (hand-crafted POST only; picker offers active production-role users); zero money/permission consequence; non-int pk = 500 folded into the same row |
| Phase E INFO — roll-detail Edit/Assign buttons status-gated, not role-gated | JUDGED in MGT-E 2026-07-12: INFO, untouched — fails closed (worker roll-detail 200 renders buttons, targets 403 ×2 probe-proven; same class as MGT-A products-list links) |
| Phase I caveat — cross-manager pattern scoping never audited | RESOLVED in MGT-G 2026-07-12: **per-manager scoping does not exist BY DESIGN** — pattern knowledge = product-anchored factory memory (model help_texts "Owning product — the permanent home (owner vision)"; PLATFORM_STATUS §3 ownership = PI-vs-ERP module boundary only); shared-management-workspace behavior runtime-proven with actor-stamp integrity (evidence section below) |
| Phase D INFO — RoleForm.permissions queryset wider than curated allowlist | DEFERRED to Phase 2 (Owner Visibility) — super-admin surface |
| /media/<path> login-tier (root URLConf, owner-approved Option 1) | out of scope, noted only |

---

# Evidence sections (one per sub-phase, appended at close)

## MGT-0 — Charter (2026-07-12) ✅

- Git state verified: HEAD 49404001 (2026-07-04), 303 dirty/untracked paths — matches worker-cert
  close-out state; no drift. Battery baseline **1519/1519** stands (no code change since; not re-run
  per method rule 7).
- Manager identity verified read-only (Django shell): `dev.mgr@test.local` active, pure manager,
  `check_password('Dev@12345') = True`. `dev.manager@test.local` does NOT accept Dev@12345 (noted).
- Created this skeleton + [DEPLOYMENT_CAMPAIGN_STATUS.md](DEPLOYMENT_CAMPAIGN_STATUS.md);
  DOCUMENTATION_INDEX rows added; memory synced.
- **No certification performed. No code touched. No fix applied.**

## MGT-A — Production 1/2: management CRUD (2026-07-12) ✅ CERTIFIED, 0 bugs

> Scope: 31 URLs — dashboards ×3 (`dashboard`/`stalled`/`pending-reports`) · `costing` ·
> products ×8 (list/add/edit/archive/flow/sizes + 2 patterns_ai redirects) · pattern library ×4 ·
> addas ×3 (list/start/detail) · stage-rates ×2 · stage library ×4 · stage-categories ×3 ·
> machine-types ×3. Stage OPERATIONS (consoles/actions/pools/barcodes/review-reports) = MGT-B.

### A1 — gate map (code audit)

| Surface | Gate chain | Manager verdict |
|---|---|---|
| dashboard | ProductionRoleMixin + DB rule roles=[manager] | ALLOWED |
| stalled / pending-reports | ProductionRoleMixin (unmanaged; self-scoping inside for non-mgmt) | ALLOWED |
| costing | `_ManagementOnly` (MANAGEMENT_ROLES) | ALLOWED |
| product-list | ManagementRoleMixin + DB rule roles=[manager] | ALLOWED (read) |
| product add/edit/archive/sizes | **SuperAdminOnlyMixin** | BLOCKED 403 |
| product-flow (flow editor) | `_SuperAdminOnly` | BLOCKED 403 |
| product-patterns / blueprint | LoginRequired **redirect-only** → patterns_ai `_ManagementOnly` gates at target | ALLOWED (302; no content at this hop) |
| pattern library ×4 | `_PatternPermissionRequired` (view/change/add/delete_productpattern; SA bypass) — **manager role holds 0 Django perms** | BLOCKED 403 |
| adda-list / adda-detail | ProductionRoleMixin + DB rule roles=[manager] (list) | ALLOWED |
| adda-create | ManagementRoleMixin (M3-fixed lineage) | ALLOWED |
| stage-rates / stage-rate-correct | **SuperAdminOnlyMixin** (S1.1 law: rerate = super-admin) | BLOCKED 403 ✓ |
| stage-list | DB rule **roles=[]** → middleware denies all but SA | BLOCKED 302→my-dashboard |
| stage add/edit/delete · stage-categories ×3 · machine-types ×3 | `_StagePermissionRequired` (Django perms, SA bypass, delegable via Roles editor — docstring-documented RBAC seam) | BLOCKED 403 |

### A2 — shell probes (test client)

- **Manager GET ×31:** 8 ALLOWED all **200** (zero 500s — functional axis clean) · 2 redirects
  (patterns_ai hops) · 20 BLOCKED (19× 403, stage-list 302→my-dashboard). Matrix matches gate map 1:1.
- **Manager blocked-write POSTs ×7** (product-create, product-archive, stage-add, stage-cat-add,
  mt-add, pattern-add, stage-rate-correct): **403 ×7**; row counts before/after identical
  (Product 18 · Stage 23 · StageCategory 5 · MachineType 5 · ProductPattern 60); product pk=5 still active.
- **Super-admin positive control ×9** (every blocked-for-manager surface + costing/adda-create): **200 ×9**.
- **Worker regression spots ×4:** dashboard/product-list 302→my-dashboard · costing/adda-create 403 — worker cert holds.

### A3 — browser evidence (live :8003, `dev.mgr@test.local`)

1. Password login → **lands on `/production/` Operations dashboard** (P1-1 management landing ✓).
2. Sidebar sections: **Main · Production · Raw Materials · Tracking · Payroll** — no Administration,
   no Storefront. Production items: Operations, Machines, Pattern Intelligence, Manufacturing
   Costing, Addas, Products — **no Product Patterns, no Stages** (perm predicates hold).
3. Positives (same session, fetch): costing/products/addas/adda-start/stalled/pending-reports = **200 ×6**;
   adda-detail GLDN-001 real-nav renders full page (code present in body).
4. Negatives (fetch): products add/edit/flow · patterns · stage-rates · stage-categories ·
   machine-types = **403 ×7**. Real nav `/production/stages/` → **bounced to /inventory/my-dashboard/**;
   real nav `/production/products/add/` → **branded "Access denied — Kapil Enterprises"** 403 page.
5. **CSRF-valid POST** product-create (real csrftoken) → **403**; DB re-checked: 0 HACK rows, count 18 unchanged.

### Suspect classification

| Suspect | Verdict |
|---|---|
| RBAC.md "What each role can do" table says manager Product CRUD = "yes"; code = SuperAdminOnly (products, flow, sizes) | **DOC DRIFT, not a permission bug** — table predates the PDD-era master-data lockdown. Logged → DEPLOYMENT_BACKLOG #6; fix in KOS content-cleanup phase |
| Manager blocked from stage-categories / machine-types masters | **BY DESIGN** — `_StagePermissionRequired` is the documented delegation seam (grant via Roles editor without super-admin); manager also has a sanctioned inline path for machine types via the machines app mgmt form. INFO for owner: delegable by config if managers should curate masters |
| Products list renders 18 Edit + 18 Flow links to manager whose targets 403 (no Add button though) | **INFO, template cosmetics** — same class as Phase-E roll-detail buttons: fails closed (branded 403), no leak, no write. Untouched (scope discipline) |
| product-patterns/blueprint redirects gated by LoginRequired only | **VERIFIED SAFE** — redirect hop carries no content; targets are patterns_ai `_ManagementOnly` (Phase-I certified) |

### Close-out

**Zero confirmed bugs → no fixes, no pins, battery NOT re-run (baseline 1519/1519 stands).**
Certification strength: artifact-backed (31-URL shell matrix · 7 POST-inertia probes with row-count
proofs · SA/worker cross-checks · live-browser statuses incl. CSRF-valid POST + DB re-check ·
branded-403/redirect quotes). Next: MGT-B (owner-gated).

## MGT-B — Production 2/2: stage operations (2026-07-12) ✅ CERTIFIED — 1 bug FIXED

> Scope: the 54 operational URLs — lanes ×2 · bundle-sets · stage-panel · stage-advanced ·
> generic ops ×5 (start/complete/reopen/allocate/alloc-void) · worker-report · review-reports ·
> layering ×11 · pattern ×10 · cutting ×16 · barcode-gen ×5. Probe targets: **LOWER-002**
> (full flow, ops mid-stream, `elastic_attach` open) + **XFB-002** (layering open).

### B1 — gate map (code audit)

| Surface | Gate chain | Manager verdict |
|---|---|---|
| add-lane / cancel-lane / bundle-sets | **ManagementRoleMixin** at dispatch | ALLOWED |
| review-reports | LoginRequired + in-view `_gate` = MANAGEMENT_ROLES (GET **and** POST) | ALLOWED |
| worker-report | LoginRequired + **own-task resolution** — docstring: managers correct via verified_quantity/review-reports (owner decision D6), they don't use this surface | BLOCKED 403 **by design** |
| all workspaces + stage-panel + action bases (layering/pattern/cutting/barcode/generic) | ProductionRoleMixin at view; **real law = service gates**: reopen skeleton step 1 = management-role gate (`_shared.reopen_stage_record`) · `pool_service.allocate` = MANAGEMENT_ROLES · action views catch ValidationError/PermissionDenied → error flash + redirect (fail-closed) | ALLOWED (mgmt passes every service gate) |
| stage-advanced | LoginRequired bounce page (data-free) | ALLOWED (trivial) |

### B2 — shell probes (test client, rollback-wrapped)

- **Manager GETs ×11** (5 workspaces incl. legacy cutting form, 2 stage-panels, review-reports,
  stage-advanced, open-layering XFB-002): **200 ×10, zero 500s**; worker-report GET **403 by design**.
- **POST-only proof:** 7 action URLs GET → **405 ×7**; add-lane GET → 200 (it's the management
  form page, DetailView — correct).
- **Manager POST probes ×15** (rollback-wrapped, empty/garbage payloads): 14× **302 with designed
  refusal/redirect** — no gate blocked a manager anywhere. In-transaction state proofs:
  **generic-reopen(side_seam_close) actually flipped DONE→OPEN** (positive functional proof of a
  management reopen, rolled back); cutting-reopen **refused, state unchanged** (S4-P5
  downstream-consumer guard correctly protects completed downstream ops); alloc-void on garbage id → 404
  (fails closed). **1× 500 → BUG MGT-B-1 (below).**
- **Worker regression ×7:** lane add/cancel + review-reports GET/POST = **403 ×4** (dispatch);
  generic-reopen / layering-reopen / allocate = fail-closed flash+redirect with **zero writes**
  (in-transaction proofs: stage records stayed DONE, WSA count unchanged). Exact service denials
  captured: reopen → `PermissionDenied("only super_admin or manager can reopen the Side Seam Close
  stage")` · allocate → `PermissionDenied("Only management can allocate stage work.")`.
- Media-writing POSTs (pattern save-video / photos-add) not POST-probed (non-rollbackable file
  writes); gated by the same `_PatternActionBase` + service pair proven on 4 siblings — disclosed.

### Bug found → FIXED (1)

| Bug | Where | What broke | Fix | Proof |
|-----|-------|-----------|-----|-------|
| **MGT-B-1** | [adda_views.py](../config/production/views/adda_views.py) — `AddaAddLaneView.post` + `AddaCancelLaneView.post` | Both catch `except (ValidationError, PermissionDenied)` but the module **never imported PermissionDenied** → every service refusal on the two lane management surfaces crashed **500 via `NameError: name 'PermissionDenied' is not defined`** instead of the designed error flash. **UI-reachable:** manager submits the Add-lane form without a reason → `add_stream` raises "A reason is required to add a cutting lane." → 500. Fails closed (atomic, no write) but breaks the GAP-4 lane workflow — certification axis 3 | one line: `from django.core.exceptions import PermissionDenied, ValidationError` | Shell: exact NameError traceback captured pre-fix; post-fix empty POSTs → 302 + zero lanes created. **Browser (live dev.mgr, CSRF-valid):** exact repro POST → **200 on add-lane page with "reason is required" flash rendered**, DB re-checked lanes unchanged (2) |

### Tests (3 pins, [test_management_role_certification.py](../config/production/tests/test_management_role_certification.py))

- manager add-lane empty POST → 200 rendered + "reason is required" flashed + 0 lanes created
- manager cancel-lane empty POST → 200 rendered + flashed refusal
- worker POST on both lane views → 403 at dispatch (ManagementRoleMixin regression guard)

### B3 — browser evidence (live :8003, `dev.mgr@test.local`)

1. Workspaces live: layering (LOWER-002 + open XFB-002), pattern, cutting, barcode-gen,
   stage-panel(elastic_attach), review-reports → **200 ×7**; worker-report → **403** (matches design).
2. Add-lane form page renders ("Add cutting lane — LOWER-002", form present).
3. **MGT-B-1 fix proof** (above): CSRF-valid empty-reason POST → flash, not 500.

### Suspect classification

| Suspect | Verdict |
|---|---|
| Manager 403 on worker-report | **BY DESIGN** — own-task-only surface (owner decision D6); management correction path = review-reports (200 for manager, worker-403 both methods proven) |
| Worker gets 302-flash (not 403) on service-gated actions | **BY DESIGN, fail-closed** — action views convert PermissionDenied to error flash + redirect; zero-write proven in-transaction; denial texts quoted above |
| Manager cutting-reopen refused on LOWER-002 | **CORRECT GUARD** — S4-P5 downstream-consumer guard (completed ops downstream); reopen gate itself proven open to management via side_seam_close flip |
| urls.py comments call layering/pattern reopen "Admin-only" | **STALE COMMENT** — law is management (reopen skeleton step 1; probe-proven). Cosmetic; noted for KOS cleanup, untouched |

### Close-out

**1 confirmed bug (MGT-B-1) FIXED + 3 pins. Sequential battery re-run (code changed):
9-app 994/994 OK (166.9s) + patterns_ai 528/528 OK (140.4s) = 1522/1522 GREEN**
(baseline 1519 + 3 new pins). Certification strength: artifact-backed (GET/405 matrices ·
15 rollback-wrapped POST probes with in-transaction state proofs · exact denial quotes ·
pre-fix NameError traceback · live-browser fix repro with CSRF + DB re-check).
Next: MGT-C — Expense money core (owner-gated).

## MGT-C — Expense money core (2026-07-12) ✅ CERTIFIED — 0 bugs, hostile-reviewed

> Scope: all 13 expense URLs + every money writer (ledger_service · settlement_service ·
> adda_settlement_service · payroll_service · advance_service · expense_service · fnf_service ·
> `_shared` gates). Highest-risk module — every write treated as dangerous until proven; every
> POST rollback-wrapped; **golden invariant = ledger 170 rows / Σ₹10880.25 must survive every probe.**
> Probe identities: manager `dev.mgr` · SA `umesh29mar` (positive control) · worker `dev.ow.a`
> (regression) · monthly worker pk=25 (pay-basis/FnF target). 100% main-thread (money + audit-honesty).

### C1 — gate map + the Manager/Super-Admin split (the critical boundary)

Every view carries LoginRequired + `_ManagementOnly` (MANAGEMENT_ROLES) at dispatch, EXCEPT MyEarnings
(worker self-view) and WorkerPayrollDetail (login + internal management flag). **Four actions are
super-admin-only, enforced in the SERVICE (not just hidden in template) — the escalation boundary:**

| SA-only action | Service gate | Manager result |
|---|---|---|
| pay-basis change | `payroll_service.set_pay_basis` → `if not user_has_role(actor, {ROLE_SUPER_ADMIN})` (owner P-2) | BLOCKED |
| Full & Final | `fnf_service._ensure_super_admin` (P-4) | BLOCKED |
| settlement reconciliation override | `adda_settlement_service.finalize` → "Only a super admin can override" (S5) | BLOCKED |
| factory-expense **void** | `expense_service.void_expense` → "Only a Super Admin can void" | BLOCKED |

Manager OWNS: payroll board, worker detail, cash-settle, advances, factory-expense create,
the full Adda-settlement lifecycle (start → finalize → reverse/supersede → discard). Import check:
views import `PermissionDenied` correctly (no MGT-B-1 repeat; 10 uses, imported line 30).

### C2 — shell probes (rollback-wrapped; hostile)

**Manager GET ×13:** 11× **200** (my, payroll, worker-detail, settle-cash, profile, fnf, advance-add,
exp-list, exp-add, adst-list, adst-detail) · pay-basis + adst-start = **405** (POST-only, correct).
Zero 500s — functional axis clean.

**SA-split escalation attempts (manager, rollback-wrapped) — all held:**
- pay-basis POST `piece_rate` → **200, basis UNCHANGED, no audit row written, SA-denial flash shown**.
- FnF POST `write_off_reason=hack` → **200, worker still active, 0 new PayrollSettlement, SA-denial shown**.
- finalize with `reconciliation_override=hack-esc` → override text **ignored** (settlement finalized on
  its own merit; `SettlementReconciliationEvidence` = no override stamped, `overridden_by=None`) — the
  override only bites when an M-6 block exists AND actor is SA (pinned: `test_s5_recon_block
  .test_non_super_admin_override_still_blocked`).
- factory-expense void POST (manager) → **200, expense still live, "Super Admin" denial shown**.

**Manager legitimate money writes (ALLOWED + FUNCTIONAL, rollback-wrapped):**
- advance-add → **302→payroll, WorkerAdvance row created** (advance = loan pool, no ledger entry at
  creation — delta 0, correct per V2 design).
- factory-expense create → **302, FactoryExpense row created**.
- **full settlement lifecycle on XFB-001** (completed, unsettled): start → **draft ADST created** →
  finalize → **status=finalized, +2 ledger rows booked** → reverse → **status=reversed, net ledger
  delta 4** (2 credit + 2 reversing rows, append-only, nothing deleted — ADR-0002 honored).
- cash-settle garbage (`amount=-1`) → **200, no PayrollSettlement created** (validation held).

**Super-admin positive control:** pay-basis change → **200, basis flipped monthly→piece_rate, audit
row added**; FnF GET → **200, preview rendered**; expense void (correct `void_reason`) → **voided**;
payroll/adst-detail → 200. Every SA-only action WORKS for SA = no false lock-out.

**Worker regression ×9:** my-earnings **200** (own self-view, correct) · payroll/adst-list/adst-detail/
advance-add/exp-list/fnf/worker-detail-other **403 ×7** · pay-basis POST **403**. Worker cert holds.

**Ledger integrity:** after EVERY rollback-wrapped block → **170 rows / Σ₹10880.25, ADST count 8,
0 advances, 4 factory-exp — byte-identical to baseline.** No probe leaked a real money row.

### C3 — browser evidence (live :8003, `dev.mgr@test.local`)

1. All 9 money surfaces fetch **200** (payroll, settlements, adst-detail, advance-add, expenses,
   expenses/add, worker-detail, fnf, my).
2. ADST-0010 (finalized) detail: **no `reconciliation_override` field rendered** for manager (`status=Finalized`).
3. Worker-25 profile: **no pay-basis form, no pay_basis input, no FnF link** rendered to manager
   (SA-only controls hidden). FnF page renders shell but **no execute form** (`write_off_reason` absent).
4. **CSRF-valid manager pay-basis escalation POST** (`piece_rate&confirm_unsettled=1`) → **200,
   redirected to profile, SA-denial flash rendered**; DB re-checked: worker-25 `pay_basis=monthly`
   unchanged, audit rows still 1 (the earlier SA change). Escalation structurally impossible.

### Suspect classification

| Suspect | Verdict |
|---|---|
| finalize view forwards `reconciliation_override` from POST for any role | **VERIFIED SAFE** — service ignores it unless an M-6 over-allocation block exists AND actor is SA; manager override text = no-op (proven: finalized with no evidence stamp). Pinned. |
| Manager can reverse/supersede a finalized settlement | **BY DESIGN** — reversal is management-grade (append-only, ledger restored; golden ₹225 chain is a reverse-heavy test). Not SA-gated by owner decision. |
| advance-add books no ledger row | **BY DESIGN** — advance = separate loan pool; recovery happens at settlement (V2-2). Row created in WorkerAdvance, not WorkerLedgerEntry. |
| MyEarnings + WorkerPayrollDetail not `_ManagementOnly` | **BY DESIGN** — my = worker self-view; detail = login+internal mgmt flag (worker-403 proven on the detail of another worker). |

### Honest caveats

- Settlement lifecycle proven on **XFB-001** (real unsettled completed Adda) end-to-end; the finalize
  booked 2 ledger rows (small real Adda). Golden ₹225 supersede chain is separately battery-pinned;
  not re-driven here (no code changed).
- pay-basis/FnF browser proof used the monthly worker (pk=25); shell proved the DB-write path for both.

### Close-out

**0 confirmed bugs → no fixes, no pins, battery NOT re-run (baseline 1522/1522 stands).**
Certification strength: artifact-backed + hostile (13-URL matrix · 4 SA-split escalation attempts with
DB proofs · full lifecycle start→finalize→reverse with ledger deltas · SA positive controls · worker
9-way regression · live-browser CSRF escalation + DB re-check · ledger integrity recount after every
rollback). **Manager money authority = correct: operates the full lifecycle, escalates to none of the
4 SA-only levers, receives zero false 403.** Next: MGT-D (owner-gated).

## MGT-D — Tracking + Inventory (2026-07-12) ✅ CERTIFIED — 0 bugs

> Scope: Tracking 13 URLs ([inventory/tracking_urls.py](../config/inventory/tracking_urls.py)) —
> dashboard · barcode list/print · legacy CSV export · scan/scan-status · roll/adda history ·
> exports ×5 (list/csv/xlsx/pdf/re-download). Inventory 10 URLs ([inventory/urls.py](../config/inventory/urls.py)) —
> my-dashboard + 2 permanent redirects + styleguide · roles ×4 · sidebar-access · access hub.
> Probe targets: LOWER-002 (barcode_generation COMPLETE → exports must work) · SHA-001 (bcgen
> incomplete → designed refusal) · EXP-2026-005 (re-download) · GLDN-001-0001 (virtual barcode) ·
> roll pk=37 (financial-strip). Main-thread throughout.

### D1 — gate map (code audit)

| Surface | Gate chain | Manager verdict |
|---|---|---|
| tracking:dashboard | LoginRequired + ProductionRoleMixin + **DB rule roles=[manager]** (middleware) | ALLOWED |
| barcode-list / barcode-print | LoginRequired + ProductionRoleMixin (unmanaged) | ALLOWED |
| barcode-export (legacy CSV) | @login_required + inline `user_has_role(MANAGEMENT_ROLES)` → bare 403 (V1.1 Item 3) | ALLOWED (mgr IS mgmt) |
| scan / scan-status | @login_required + PRODUCTION_ROLES + @transaction.atomic; scan-status POST-only → single-writer `tracking.services.mark_status` | ALLOWED |
| roll-history / adda-history | LoginRequired + ProductionRoleMixin + G-AUTH-1 in-view gate (mgmt = all; worker = assigned-only) + **PA-03-1 financial strip: rows `field_name in (supplier, cost_per_kg)` excluded server-side unless FINANCIAL_ROLES = {super_admin, accountant}** — manager EXCLUDED from financials by design | ALLOWED (minus financial rows) |
| export-list / export-csv/xlsx/pdf (POST-only) / export-download | LoginRequired + **ManagerOrAdminMixin** + service backstop `_ensure_management_role` (defense-in-depth) + bcgen-completion gate; `regenerate_for_export` = read-only render | ALLOWED |
| my_dashboard / redirects / styleguide | @login_required only (role-aware content; redirects 301; middleware-exempt landing) | ALLOWED |
| roles list · sidebar-access · access hub | **Double gate (Phase-D law): SuperAdminOnlyMixin/_SuperAdminOnly in view + Administration SidebarItemRule roles=[] skills=[] → middleware denies pre-view (302 + flash; AJAX → 403 JSON)** | BLOCKED 302 |
| roles add/edit/delete | SuperAdminOnlyMixin (unmanaged action URLs — middleware docstring: "unmanaged + action URLs keep their existing view mixins") | BLOCKED 403 |

Import check (MGT-B-1 class): tracking_history imports `PermissionDenied` at module top (line 9);
scan views import it locally before raise; export views rely on service-raised PermissionDenied →
Django 403. No NameError class present.

### D2 — shell probes (test client)

- **Manager GET ×23:** 12 ALLOWED = **200 ×12** (tracking dashboard, barcode list/print, legacy CSV
  `attachment; filename="LOWER-002-barcodes.csv"`, roll-history 37, adda-history GLDN-001,
  export-list, re-download `EXP-2026-005-LOWER-002.csv`, my-dashboard, styleguide) + **301 ×2**
  (legacy dashboard twins → /inventory/my-dashboard/) · POST-only GETs = **405 ×4** (csv/xlsx/pdf/scan-status)
  · BLOCKED = **302→my-dashboard ×3** (roles list, sidebar-access, access hub — managed empty-role rules)
  + **403 ×3** (roles add/edit/delete — mixin). **Zero 500s, zero false 403s — matrix matches gate map 1:1.**
- **AJAX branch:** manager GET /inventory/roles/ with `X-Requested-With: XMLHttpRequest` →
  **403 JSON `{"detail": "You don't have the access to this page."}`** (middleware AJAX fork proven).
- **Manager functional writes (rollback-wrapped):** scan GET GLDN-001-0001 → **200, BatchBarcode
  lazy-created 5→6, stamped_by=dev.mgr** (rolled back, post-check row gone) · scan-status POST
  `dispatched` on SHA-001-0361 → **302, row packed→dispatched** (rolled back → packed); garbage status →
  302 + error flash, row unchanged · **export csv/xlsx/pdf POST LOWER-002 → 200 ×3, manifest row
  created 5→6 each (`EXP-2026-006-LOWER-002.*`), rolled back → 5** · export POST SHA-001 → **400
  designed refusal: "Exports require the barcode_generation stage in this product's workflow."**
- **Manager blocked-write POSTs:** roles/add (name=HACK…) → **403, Role count 5→5** · roles/5/delete →
  **403, count 5→5** · sidebar-access POST (roles_N=1,2,3) → **302 intercepted PRE-VIEW by middleware,
  role_list allowed_roles 0→0** (no M2M write).
- **404 negatives (fail-closed, no 500):** garbage scan value → 404 · unknown adda barcode-list → 404 ·
  unknown export re-download → 404.
- **Financial strip (rollback-injected rows, roll 37):** created `cost_per_kg 100.00→123.45`,
  `supplier OldSup→SecretSupplierX`, + non-financial `weight_kg` row → **manager GET: 200, cost row
  NOT rendered, supplier row NOT rendered, weight_kg row rendered; SA GET: 200, BOTH financial rows
  rendered.** Rolled back (0 probe rows remain). FINANCIAL_ROLES={super_admin, accountant} — manager
  exclusion proven at runtime, not just in code.
- **Super-admin positive control ×8:** roles/ + roles/add + sidebar-access + access + tracking
  dashboard + export-list + re-download = **200 ×7**; export csv POST → **200** manifest row (rolled
  back). No false lock-out.
- **Worker regression ×13:** tracking dashboard → **302** (rule roles=[manager]) · export-list /
  re-download / legacy CSV → **403 ×3** · export POST → **403, manifest 5→5** · roll-history 37 +
  adda-history GLDN-001 (unassigned) → **403 ×2** with exact quotes "You can only view history for
  rolls on Addas you're assigned to." / "…for Addas you're assigned to." · roles/ + sidebar-access +
  access → **302 ×3** · roles/add → **403** · my-dashboard → **200** · scan GET SHA-001-0361 → **200**
  (production floor keeps scanning — worker-cert holds).

### D3 — browser evidence (live :8003, `dev.mgr@test.local` — identity re-verified in-session)

1. Sidebar: Main · Production · Raw Materials · **Tracking (Barcode Dashboard)** · Payroll — **no
   Administration section, no Roles/Sidebar Access/Access Control links.**
2. Positives real-nav: /tracking/ renders "Barcode Dashboard" with **10 Export + 10 Print actions
   visible** (is_management ctx holds) · barcode list LOWER-002 (6 export controls) · print sheet
   **82 QR data-URI images** · roll-history 37 (**no "supplier"/"cost per kg" text anywhere in body**) ·
   adda-history GLDN-001 · exports list (5 rows incl. EXP-2026-005).
3. Negatives real-nav: /inventory/roles/, /inventory/sidebar-access/, /inventory/access/ → **all
   bounced to /inventory/my-dashboard/** with flash rendered: **"You don't have the access to this
   page."** · /inventory/roles/add/ → **branded "KE Error 403 — You don't have access… ask your
   administrator"** page.
4. AJAX fetch /inventory/roles/ (XMLHttpRequest header) → **403 `{"detail": "You don't have the
   access to this page."}`**.
5. **CSRF-valid escalation POST** /inventory/roles/add/ (real csrftoken) → **403**; DB re-checked:
   0 HACK roles, Role count 5 unchanged.
6. **CSRF-valid functional POST** /tracking/exports/LOWER-002/csv/ → **200,
   `attachment; filename="EXP-2026-006-LOWER-002.csv"`, text/csv**; DB re-checked: manifest row
   **EXP-2026-006 · LOWER-002 · csv · exported_by=dev.mgr · 82 labels** created. *Disclosed live
   artifact:* this is a REAL export by the manager on DEV data — the manifest row is the designed
   append-only audit record of an export that genuinely happened; retained per data/history principles.

### Suspect classification

| Suspect | Verdict |
|---|---|
| Worker 302 on tracking:dashboard while view mixin (ProductionRoleMixin) would allow | **BY DESIGN / KNOWN** — SidebarItemRule roles=[manager] is the stricter live gate (menu+URL gated together, rule 6); scan/list/print stay unmanaged + PRODUCTION_ROLES so the floor keeps scanning (worker scan 200 proven) |
| roles add/edit/delete have NO SidebarItemRule (single runtime gate = SuperAdminOnlyMixin) | **BY DESIGN** — middleware docstring: action URLs keep view mixins; list/hub URLs carry the double gate; all three action URLs 403-proven for manager AND worker. INFO only |
| Legacy barcode-export returns bare `HttpResponse(status=403)` (no branded page) | **INFO, cosmetic** — file-download endpoint, fails closed; same class as prior bare-403 INFOs; untouched (scope discipline) |
| Manager (not just SA) can trigger/re-download exports + change piece status | **BY DESIGN** — exports are MANAGEMENT_ROLES (V1.1 Item 3 owner decision); scan-status is PRODUCTION_ROLES via single-writer `mark_status` |
| Browser export POST left manifest row EXP-2026-006 | **DISCLOSED ARTIFACT, not a bug** — append-only audit of a real DEV export (see D3.6) |

### Close-out

**Zero confirmed bugs → no fixes, no pins, battery NOT re-run (baseline 1522/1522 stands).**
Certification strength: artifact-backed (23-URL shell matrix · AJAX-fork proof · 5 rollback-wrapped
functional writes with DB before/after · 3 blocked-write inertia proofs · injected-row financial-strip
proof manager-vs-SA · 3 fail-closed 404s · SA ×8 positive control · worker ×13 regression with exact
denial quotes · live-browser real-nav + flash/branded-403 quotes + CSRF escalation AND functional
POSTs with DB re-checks). **Phase-D law re-confirmed: Administration stays super-admin-only for the
manager (double gate live at both layers). Manager tracking authority = correct: full dashboard/
exports/history access, zero false 403/500, financials invisible.** Next: MGT-E (owner-gated).

## MGT-E — Raw Materials (2026-07-12) ✅ CERTIFIED — backlog #5 FIXED

> Scope: all 23 raw_materials URLs ([raw_materials/urls.py](../config/raw_materials/urls.py)) —
> dashboards ×2 · rolls ×6 (list/bulk-add/detail/edit/damage/assign) · cloth-types ×5 ·
> cloth-colors ×5 · storage-locations ×5. Special mandate: **fix DEPLOYMENT_BACKLOG #5**
> (master delete-confirm 500, pre-confirmed Phase E). Probe targets: roll pk=21 NKS-R4
> (NOT_USED, cost=200 set) · pk=36 GLDN-R5 (DAMAGED) · pk=1 CR-000001 (USED,
> supplier="Validation Supplier", cost=200 — financial-visibility target) · masters:
> unreferenced Linen(4)/Blue(2)/Rohini Factory(2), referenced Cotton(1). Main-thread throughout.

### E1 — gate map (code audit)

| Surface | Gate chain | Manager verdict |
|---|---|---|
| dashboard · cloth-dashboard · roll-list · 3 master lists | LoginRequired + ProductionRoleMixin + **SidebarItemRule roles=[manager] ×6** (managed: dashboard/cloth-dashboard/roll-list/type/color/storage lists) | ALLOWED |
| roll-detail | LoginRequired + ProductionRoleMixin (unmanaged); financials via `can_view_financials` ctx | ALLOWED (minus financials) |
| roll-bulk-create | **SuperAdminOnlyMixin** ("sensitive irreversible event") | BLOCKED 403 |
| roll-edit · roll-assign · roll-damage (POST-only) | **ManagementRoleMixin** (M9 lineage) + service guards (`update_roll_details`, `mark_roll_damaged`/`restore_damaged_roll` re-gate MANAGEMENT + mandatory reason) | ALLOWED |
| master create/update/archive/delete ×9 | **ManagementRoleMixin** (Phase-E fix lineage) + `master_service._ensure_can_manage` (MANAGEMENT) | ALLOWED |
| **Financial fields supplier/cost_per_kg** | 4 layers: form `fields.pop` unless `user_can_edit_financials` (BulkRollForm+RollEditForm) · service `PermissionDenied` re-check (bulk_create_rolls + update_roll_details) · template `can_view_financials` branches (roll_detail/roll_list) · history strip `exclude(field_name__in=(supplier,cost_per_kg))` on all 3 time-log surfaces (PA-13-3). FINANCIAL_ROLES={super_admin, accountant} — **manager excluded** | BLOCKED all 4 layers |

Import check (MGT-B-1 class): roll_views imports `PermissionDenied` at module top (line 15);
master_views catches only ValidationError (service raises it); no NameError class present.

### E2 — shell probes (test client)

- **Manager GET ×23 (PRE-fix):** 19× **200** · bulk-add **403** (correct SA-only) · roll-damage
  **405** (POST-only) · **500 ×3 = ALL THREE delete-confirm pages** (bug #5, see below).
  Zero false 403s; matrix matches gate map 1:1.
- **Manager master writes (rollback-wrapped, all six proven functional):** create POST → 302 +
  row + "Cloth Type created." · update POST → 302 + rename · archive POST → 302 + is_active flip ·
  2nd archive POST → restore flip ("restored.") · delete POST unreferenced temp row → 302 + row
  gone + "deleted." · delete POST referenced Cotton → **302 + "Cannot delete — … Archive it
  instead." + row survives** (ProtectedError→ValidationError path works).
- **Manager roll ops (rollback-wrapped):** damage mark pk21 → 302, status→damaged, +1 history row ·
  restore pk36-class → status→not_used · no-reason POST → refused "reason is required", state
  unchanged · damage on USED pk1 → refused "already consumed by production" · roll-edit weight
  33.33 → 302 + saved · **roll-assign garbage adda → 200 form error, zero writes**.
- **Financial injection (layer 1+2 proof):** manager roll-edit POST with `supplier=HACK-SUPPLIER&
  cost_per_kg=999.99` injected → **weight saved, supplier stayed '', cost stayed 200.00, 0
  financial history rows** (form popped the fields). Service direct: `update_roll_details(mgr,
  supplier=…)` and `bulk_create_rolls(mgr, cost_per_kg=…)` → **PermissionDenied "Supplier and
  Cost Per KG require Accountant or Super Admin role"** ×2.
- **Layer 3 (templates):** manager roll-detail pk1 → "Validation Supplier"/"Cost/KG"/"Supplier"
  ALL absent; roll-list → no Supplier/Cost columns. SA sees all of it (positive control).
- **Layer 4 (history strip, injected-row probe):** in-transaction ClothRollHistory rows
  `cost_per_kg→987.65`, `supplier→SecretSupplierZ`, control `weight_kg→77.77` → manager GET
  rm-dashboard + cloth-dashboard + roll-list: **secrets absent ×3, control visible ×3; SA: secrets
  present ×3.** Rolled back (0 probe rows remain).
- **Manager bulk-add POST → 403, roll count 32→32** (dispatch inertia).
- **SA positive control ×9 + forms:** all 200; SA bulk-add + roll-edit forms contain
  supplier/cost fields (manager's roll-edit form: both ABSENT); SA bulk-create POST with
  financials → 2 rolls + cost stamped + 2 history rows (rolled back). SA delete-confirm GET
  pre-fix = **500 too** (backlog's "manager AND super-admin repro" re-confirmed).
- **Worker regression ×14:** 6 managed URLs → **302→my-dashboard ×6** · roll-edit/assign/bulk-add/
  ct-add/ct-delete → **403 ×5** · roll-detail 21 → **200** (production floor, by design; financials
  hidden by the same 4 layers) · damage POST + ct-create POST → **403 ×2, zero writes**.
- **Garbage-pk (fail-closed):** roll-detail/roll-edit/ct-edit/ct-delete 99999 → **404 ×4**;
  ct-archive 99999 → **500** (uncaught DoesNotExist) → INFO, backlog #7 (not UI-reachable, no fix — scope rule).

### Bug → FIXED (1, the pre-confirmed backlog #5)

| Bug | Where | What broke | Fix | Proof |
|-----|-------|-----------|-----|-------|
| **#5** | [master_views.py](../config/raw_materials/views/master_views.py) `_MasterDeleteView` | Django `DeleteView` context = object+form only; shared template [master_confirm_delete.html:24](../config/raw_materials/templates/raw_materials/master_confirm_delete.html) does `{% url list_url_name %}` → var empty → **`NoReverseMatch: Reverse for '' not found` = 500 on the delete-confirm GET for EVERY allowed role, all THREE masters** (UI-reachable: list page → Delete button). Delete POST itself always worked | `get_context_data` on `_MasterDeleteView` supplying `title` + `list_url_name` (mirrors create/update/archive siblings) | Pre-fix: 500 ×3 as manager + 500 as SA, exact NoReverseMatch captured. Post-fix shell: **200 ×6** (mgr+SA × 3 masters), cancel-link reverses, title renders; full confirm→POST workflow deletes temp row + flash. **Browser (live dev.mgr, real forms):** create `MGTE-BROWSER-DEL` → confirm page renders "Delete Cloth Type / Permanently delete MGTE-BROWSER-DEL?" + DESTRUCTIVE chip → Delete Permanently → "deleted." flash, row gone from table, **DB re-check 0 MGTE rows, ClothType count back to 6** |

### Tests (2 pins, [test_master_gates.py](../config/raw_materials/tests/test_master_gates.py))

- `test_manager_delete_confirm_page_renders` — GET all 3 masters' delete-confirm → 200 + Cancel
  href reverses to list + title rendered
- `test_manager_delete_confirm_then_post_deletes` — full workflow confirm→POST→row gone→redirect

### E3 — browser evidence (live :8003, `dev.mgr@test.local`, real password login)

1. Login → lands `/production/` (mgmt landing ✓). Sidebar: Main · Production · **Raw Materials
   (all 6 items: Raw Material Dashboard, Cloth Dashboard, Cloth Rolls, Cloth Types, Cloth Colors,
   Storage Locations)** · Tracking · Payroll — no Administration, no Storefront.
2. In-session fetch matrix: dashboards/rolls/lists/roll-detail/roll-edit + **delete-confirm ×3 =
   200** (fix live) · bulk-add **403**.
3. Real-nav bulk-add → **branded "Access denied — Kapil Enterprises"** 403 page.
4. Financial invisibility live: roll-detail pk1 → no "Validation Supplier"/"Cost/KG"/"Supplier"
   anywhere in body; roll-list → no Supplier/Cost/KG columns.
5. **Full CSRF-valid workflow** (the #5 fix, real forms): create → confirm → delete (row above).
6. **CSRF-valid escalation POST** bulk-add (real csrftoken) → **403**, roll count 32 unchanged.

### Suspect classification

| Suspect | Verdict |
|---|---|
| Master archive-confirm GET garbage pk → 500 (uncaught `DoesNotExist` in `_MasterArchiveView.get`) | **INFO → DEPLOYMENT_BACKLOG #7** — not UI-reachable (lists only link real pks; edit/delete siblings 404), fails closed, no write/leak. NOT fixed (fix-only-#5 mandate) |
| Roll-detail Edit/Assign buttons status-gated, not role-gated (Phase-E carry-over) | **INFO, untouched** — worker roll-detail 200 renders buttons, targets 403 ×2 (probe-proven); fails closed; same class as MGT-A products-list links |
| Worker roll-detail = 200 | **BY DESIGN** — production floor sees roll facts; financials hidden by the same 4 certified layers; write paths all 403 |
| Manager can hard-delete masters (not SA-only) | **BY DESIGN** — masters = management data (Phase-E law); PROTECT FK + service ValidationError guard referenced rows; destructive-confirm page + archive-first guidance |
| Roll bulk intake SA-only (manager blocked) | **BY DESIGN** — documented "sensitive irreversible event" (mixin docstring); SA positive control works |

### Close-out

**1 confirmed bug (backlog #5) FIXED + 2 pins. Sequential battery re-run (code changed):
9-app 996/996 OK (166.6s) + patterns_ai 528/528 OK (139.5s) = 1524/1524 GREEN**
(baseline 1522 + 2 new pins). Certification strength: artifact-backed (23-URL pre/post-fix
matrices · 10+ rollback-wrapped POST probes with DB before/after · 4-layer financial proofs incl.
injected-row history probe + service-direct PermissionDenied quotes · SA ×9 positive control ·
worker ×14 regression · live-browser real-form workflow + CSRF escalation + DB re-checks).
**Manager raw-materials authority = correct: full master CRUD + roll stock ops work, bulk intake
and financials stay walled, zero false 403, zero remaining 500 on any reachable surface.**
Next: MGT-F (owner-gated).

## MGT-F — Machines + Storefront + Accounts (2026-07-12) ✅ CERTIFIED — 1 bug FIXED

> Scope: Machines 5 URLs ([machines/urls.py](../config/machines/urls.py) — list/add/edit/assign/release,
> manager-POSITIVE incl. the two possession actions; special mandate: judge the Phase-F carry-over
> "MachineAssignView accepts any user pk") · Storefront 8 URLs (manager-BLOCKED regression vs Phase G)
> · Accounts 20 URLs (auth flows manager-positive; Team Members / User Skills / User Types
> super-admin-only → manager blocked; S2 signup-closed + S3 email-self-service regressions).
> Probe identities: manager `dev.mgr` (pk 52) · SA `umesh29mar` · worker `dev.ow.a` (pk 46) ·
> listing_team `dev.listing` (pk 62) · inactive `dev.leaver` (pk 42). All shell probes inside ONE
> outer transaction rolled back at the end (post-rollback recount byte-identical incl. sessions).
> Main-thread throughout. OTP-SEND POSTs deliberately NOT probed (EMAIL_BACKEND may be real SMTP —
> external non-rollbackable side effect); gates covered by GET renders + code audit + existing pins.

### F1 — gate map (code audit)

| Surface | Gate chain | Manager verdict |
|---|---|---|
| machines list/add/edit | LoginRequired + `_ManagementOnly` (MANAGEMENT_ROLES); unmanaged by SidebarItemRule (no machines rule exists — sidebar link is the mgmt-only register itself) | ALLOWED |
| machines assign/release | same mixin; POST-only (`View` with only `post`) → GET 405; ALL writes via `machine_service` (sole writer, zero-₹ grep-pinned) | ALLOWED |
| storefront product_list/category_list | LoginRequired + ListingTeamMixin (STOREFRONT_ROLES = SA+listing_team) + **managed SidebarItemRule roles=[Listing Team]** → middleware denies manager PRE-VIEW | BLOCKED 302 |
| storefront add/edit/delete ×6 | LoginRequired + ListingTeamMixin (unmanaged action URLs) | BLOCKED 403 |
| /app/ auth flows (login, verify-otp, resend, password, forgot, reset, home, logout) | public or LoginRequired; throttled (per-IP + per-email); HomeView = role landing (P1-1) | ALLOWED |
| accounts:user_list / skill_list | `SuperuserRequiredMixin` (role-based, `user_has_role({ROLE_SUPER_ADMIN})` — NOT raw is_superuser) + **Administration SidebarItemRule roles=[] (double gate, Phase-D law)** | BLOCKED 302 |
| users/skills/user-types add/edit/delete ×9 + usertype_list | `SuperuserRequiredMixin` (unmanaged → mixin 403) | BLOCKED 403 |
| /accounts/signup/ (allauth) | S2: `RestrictedAccountAdapter.is_open_for_signup=False` (base.py:300) | CLOSED (all users) |
| /accounts/email/ | S3: `EmailManagementDisabledView` shadow-mounted BEFORE allauth include (urls.py:28) | NEUTRALIZED (all users) |

Import check (MGT-B-1 class): machines/storefront views raise via mixins (no local PermissionDenied
catch); accounts views import what they use. No NameError class present.

### F2 — shell probes (test client; ONE outer transaction, rolled back; post-rollback verify: Machine 4 · MachineAssignment 4/2 open · FeaturedProduct 1 · Category 1 · User 47 · Skill 10 · UserType 5 · Role 5 — byte-identical to baseline)

**Machines — manager positive (the certification's functional axis):**
- GET list/add/edit = **200 ×3**; assign/release GET = **405 ×2** (POST-only proven).
- create `MGTF-M1` → **302 + row** · duplicate code `EL-001` → **200 form error "already exists", no row** ·
  edit rename → **302 + saved** · assign EL-001→dev.ow.a with adda XFB-002 → **302 + open window,
  holder + adda stamped** · second assign while held → **200 + exact flash "…currently with … Release
  it first.", zero rows** · release → **302 + end_at set** · release AGAIN → **404** (already-released
  fails closed) · assign on MAINTENANCE machine → **"set it Active" flash, zero rows** · release on
  never-open assignment pk → 404 by queryset (`end_at__isnull=True`).
- **BUG FOUND → MGT-F-1 (below):** edit machine WITH assignment history to a new code → **302, code
  silently renamed OL-001→OL-999** (F1-immutability guard bypassed). Case-insensitive dup via the
  same hole (form dup-check is case-sensitive; service iexact check also skipped).
- **Any-user-pk judgment (the carry-over, with evidence):** manager POST assign with worker=62
  (listing_team) → **302, assignment CREATED** (holder dev.listing) · worker=42 (INACTIVE dev.leaver)
  → **302, CREATED** · worker=1 (SA) → **302, CREATED** (SA is in PRODUCTION_ROLES → also in the UI
  picker, by design) · worker=99999 → **404** · worker=''/'abc', adda='abc' (hand-crafted) → **500 ×3**
  (uncaught ValueError; zero rows — "open on EL-001 after garbage probes: 0"). Picker (template)
  offers ONLY active production-role users + `required` attr → inactive/listing_team need a
  hand-crafted POST. **Verdict: INFO → DEPLOYMENT_BACKLOG #8, NOT fixed (scope rule)** — no money
  (zero-₹ grep pin), no permission consequence (possession row grants nothing), fails closed on
  garbage; data-hygiene only.
- SA positive control: list 200, assign SN-001 → row created. Worker regression: GET ×3 → **403**,
  assign/release POSTs → **403**, assignment count delta 0, open window pk 7 untouched.

**Storefront — manager blocked everywhere (Phase-G regression re-proven):**
- Manager GET ×8: product_list + category_list → **302→my-dashboard** (middleware, managed
  Listing-Team-only rules) · add/edit/delete ×6 → **403** (mixin). AJAX product_list →
  **403 JSON `{"detail": "You don't have the access to this page."}`**.
- Manager POSTs product_add/category_add/product_delete → **403 ×3**; FeaturedProduct 1→1,
  Category 1→1, product pk=1 survives.
- Positive controls: listing_team GET lists **200 ×2** · SA **200**. Worker: list **302**, add **403**.
  Middleware + mixin + (no storefront services touched) + template layer all consistent — manager
  remains excluded by design (STOREFRONT_ROLES unchanged).

**Accounts:**
- Anon: login 200 · password-login 200 · forgot 200 · reset-verify 200 · verify-otp **302→/app/**
  (no pending session) · home/users **302→login?next=…** · logout GET 302.
- **Real credential login (ONE attempt, throttle-safe): POST /app/login/password/ dev.mgr →
  302→/app/home/ → 302→/production/** (P1-1 management landing). Login page while authed →
  302 home. Logout POST → 302 login; logout GET → 302 home (POST-only law holds).
- Manager blocked ×12: user_list + skill_list → **302→my-dashboard** (Administration double gate) ·
  usertype_list + 9 action URLs → **403**. AJAX /app/users/ → **403 JSON** (same middleware fork).
- Manager blocked POSTs: users/add + skills/add + user-types/add + users/46/delete → **403 ×4**;
  User 47→47, Skill 10→10, UserType 5→5, dev.ow.a still active, no hack row.
- **S3 holds:** manager GET /accounts/email/ → **302→/app/home/**; POST action_add
  `evil-mgtf@example.com` → **302, User.email unchanged (dev.mgr@test.local), EmailAddress delta 0**.
- **S2 holds:** anon GET /accounts/signup/ → **200 "Sign Up Closed" page**; POST
  `s2probe-mgtf@example.com` → **200, user NOT created, User delta 0**.
- SA positive ×5 (users/users-add/skills/skills-add/user-types) → **200 ×5**. Worker regression:
  user_list/skill_list **302 ×2**, usertype_list + users/add **403 ×2**, users/add POST → 403 + no row.

### Bug → FIXED (1)

| Bug | Where | What broke | Fix | Proof |
|-----|-------|-----------|-----|-------|
| **MGT-F-1** | [machine_service.py](../config/machines/services/machine_service.py) `update_machine` | Guard read `code.strip() != machine.code` — but `MachineForm(request.POST, instance=machine)` **mutates `machine.code` in memory during `is_valid()`** (Django `construct_instance`), so the guard compared new-vs-new → always False → skipped. Edit form could silently rename a machine code WITH assignment history (F1-immutability broken — printed floor labels reference the code) AND bypass the case-insensitive dup check. Existing pin passed because it calls the service directly with a fresh instance. UI-reachable: register → Edit → change Code → Save | Guard now compares against the **DB row** (`Machine.objects.only('code').get(pk=…)`), not the in-memory instance | Root cause isolated in shell (before-bind `OL-001` → after-`is_valid()` `OL-999`, comparison False). Post-fix shell: history-machine rename → **200 + "immutable" form error + DB code unchanged**; no-history rename → **302 + saved**; lowercase-dup `el-001` → **200 "already exists"**. **Browser (live dev.mgr, real form):** OL-001 edit → code `OL-999` → Save → exact error rendered "Machine code is immutable once the machine has assignment history (floor labels reference it). Create a new machine instead.", DB re-check `pk1 code: OL-001` |

### Tests (2 pins, [test_r10a.py](../config/machines/tests/test_r10a.py) → 17 total)

- `test_edit_form_cannot_rename_code_with_history` — view-path POST rename on a machine with an
  assignment → 200 re-render + "immutable" + DB code unchanged
- `test_edit_form_renames_code_without_history` — no history → rename still allowed (302 + saved)

### F3 — browser evidence (live :8003, `dev.mgr@test.local`, fresh real password login)

1. Sign-out of stale session → password login → **lands /production/**. Sidebar sections:
   Main · Production (incl. **Machines**) · Raw Materials · Tracking · Payroll — **no Administration,
   no Storefront**.
2. Machines register renders (counts strip Total 4 / Active 4 / Assigned now 2, summary cards).
   **Real assign workflow:** EL-001 card → FancySelect worker picker (options = active
   production-role users incl. managers/SA per role-based-picker design) → DEV-OW-A → Assign →
   flash **"EL-001 assigned to DEV-OW-A."** → Release (confirm dialog accepted) → flash
   **"EL-001 released."** DB re-check: assignment pk 18 created by the real form and end-dated.
   *Disclosed artifact:* one CLOSED possession window (EL-001 → dev.ow.a, 33s) — append-only DEV
   history row, retained per data/history principles.
3. **MGT-F-1 fix live in browser** (row above): exact immutable-error rendered, DB unchanged.
4. Negatives real-nav: /storefront/products/ + /app/users/ → **bounced to my-dashboard** with flash
   "You don't have the access to this page." · /storefront/products/add/ + /app/user-types/ →
   **branded 403** pages · /accounts/email/ → **bounced to /production/** with flash "Your email
   address is managed by your administrator." (S3 live).
5. **CSRF-valid escalation POST** /app/skills/add/ (real csrftoken, fetch) → **403 ×2**; DB
   re-checked: Skill count 10 unchanged, no HACKSKILL row.

### Suspect classification

| Suspect | Verdict |
|---|---|
| MachineAssignView accepts any existing user pk (carry-over) | **INFO → DEPLOYMENT_BACKLOG #8** (evidence-judged, facets (a)+(b) above; not BY DESIGN — README documents the picker filter, not server acceptance; not a confirmed bug — zero money/permission impact, hand-crafted-POST-only) |
| Assign picker lists managers + SA | **BY DESIGN** — role-based picker = PRODUCTION_ROLES (machines README: "deliberately not eligible_stage_workers"); managers/SA are production roles |
| Storefront manager 302 (not 403) on the two list URLs | **BY DESIGN / KNOWN** — managed SidebarItemRule roles=[Listing Team]; middleware menu+URL law (rule 6); action URLs stay mixin-403 |
| accounts user-types trio has NO SidebarItemRule (mixin-only gate) | **BY DESIGN / KNOWN** — same class as roles add/edit/delete (MGT-D verdict): action/unmanaged URLs keep view mixins; 403-proven for manager AND worker |
| verify-otp GET → 302 /app/ | **BY DESIGN** — no pending OTP session → bounce to email step |
| OTP-send POSTs not probed | **DISCLOSED LIMITATION** — EMAIL_BACKEND env-configurable to real SMTP (.env unreadable by probe policy); send paths are throttle-pinned in accounts tests; GET renders + throttle module audited |

### Close-out

**1 confirmed bug (MGT-F-1) FIXED + 2 pins. Sequential battery re-run (code changed):
9-app 998/998 OK (162.7s) + patterns_ai 528/528 OK (142.4s) = 1526/1526 GREEN**
(baseline 1524 + 2 new pins; fresh test DBs). *Disclosed battery incident:* a first patterns_ai
attempt on a `--keepdb` DB errored ×2 (`Role.DoesNotExist` in test setup) — kept-DB pollution, NOT a
code regression: `TransactionTestCase` classes in the 9-app run truncate migration-seeded Role rows
and `--keepdb` carries the emptied table into the next process; fresh-DB reruns of BOTH halves are
the green numbers above. Battery procedure note appended to DEPLOYMENT_BACKLOG #4
(canonical battery = fresh test DBs, never `--keepdb` across suites).
Certification strength: artifact-backed (36-URL shell matrix incl. 405s · rollback-wrapped POST
probes with row-count/holder proofs · any-user-pk judgment probes ×6 · root-cause isolation script ·
S2/S3 regression probes with DB deltas · SA ×7 + listing_team positive controls · worker regression
across all three apps · live-browser real login + real assign/release forms + fix repro + CSRF
escalation with DB re-checks). **Manager machines authority = correct and now guard-safe; storefront
stays fully walled; accounts admin surfaces stay super-admin-only; S2/S3 security fixes hold.**
Next: MGT-G (owner-gated).

## MGT-G — patterns_ai + cross-manager isolation (2026-07-12) ✅ CERTIFIED — 0 bugs

> Scope: all patterns_ai routes ([patterns_ai/urls.py](../config/patterns_ai/urls.py)) on the three
> axes PLUS the primary mandate: **first-ever cross-manager data-isolation audit** (Phase-I caveat).
> Identities: Manager A = `dev.mgr` (pk 52) · **Manager B = `mgmt1@test` (pk 20, verified pure
> manager: role=manager, is_superuser=False, 0 perms, 0 groups)** · SA `umesh29mar` · worker
> `dev.ow.a`. All shell probes in ONE outer transaction rolled back at the end (post-rollback:
> MarkerUsage 1 · MarkerOutcome 1 · CalibrationMat 2, usage-1 unvoided — byte-identical).
> Browser probes artifact-free (no real writes). Main-thread throughout.

### G0 — the ownership model (gate-map + design-of-record audit)

**Per-manager object ownership DOES NOT EXIST in patterns_ai — by design.** Evidence chain:
- **Code:** zero `filter(created_by=…)` / `owner=` anywhere in views.py or all 27 services;
  `created_by`/`confirmed_by`/`recorded_by`/`checked_by` are PROTECT audit stamps, never filters.
- **Design of record:** PLATFORM_STATUS §3 "DATA OWNERSHIP (permanently frozen, owner ruling)"
  defines ownership as the **PI-vs-ERP module boundary** — no per-manager concept exists;
  model help_texts: "Owning product — the permanent home (owner vision)" (PatternPiece, Marker).
  Pattern knowledge = product-anchored FACTORY memory, shared by all management.
- **Gate law (Phase-I re-confirmed):** every route `LoginRequiredMixin + _ManagementOnly`
  (MANAGEMENT_ROLES) at dispatch; ONE stricter gate = `PatternBlueprintView`
  (`production.change_productpattern`, SA bypass); services re-gate writes
  (`_ensure_management`/`_gate`); `patterns_ai:home` = managed SidebarItemRule roles=[Manager,
  Super Admin]; `_int_or_404` guards non-int query ids (P1 review lineage).

### G1 — manager-ALLOWED sweep (A, shell)

23 GETs across every station = **200 ×22 + tool-redirect 302→cutting-table, ZERO 500s, zero false
403s**: home · dashboard · studio · marker-list · yield · manual-new · marker-detail · usage-new ·
mat-list/new/detail · piece-list/detail · version-detail · generate · run-detail · candidate-detail ·
advisor · insights · workspace(candidate) · cutting-table(DEV-NICKAR) · studio-work(piece×size).
**Blueprint: manager (0 Django perms) → 403; SA → 200** — the one stricter gate holds both ways.
**Exports as A on artifacts created by other users: candidate-svg `image/svg+xml` · candidate-pdf
`application/pdf` `attachment; filename="layout_28_production.pdf"` · candidate-print 200 ·
geometry svg/dxf/print 200 ×3 with correct content-types.**

### G2 — cross-manager probes (the mandate; B creates → A operates; rollback-wrapped)

| Owner question | Probe | Result | Verdict |
|---|---|---|---|
| A access B's objects? | B GET SA-created MRK-000002 → 200; A GET B-created usage page + B-created mat detail → 200 ×2 | full mutual access | **BY DESIGN** (shared factory knowledge) |
| A edit B's objects? | A POST outcome on B's usage → row created, **`recorded_by=dev.mgr` (the TRUE actor, not B)** | works, honest stamp | **BY DESIGN + stamp integrity** |
| A execute B's workflows? | A POST void on B's usage (reason) → `voided_at` set, reason stored, original `confirmed_by=mgmt1` preserved · A POST retire on B's mat → `status=retired` + reason | works | **BY DESIGN** (append-only F2 semantics hold) |
| A export B's artifacts? | export matrix above (creators = SA/dev.mgr mix) → 200 ×6 | works | **BY DESIGN** (management-gated) |
| Enumerate via predictable URLs? | IDs are sequential BUT reachable only by MANAGEMENT_ROLES; garbage probes ×10 (mats/markers-str/versions/candidates-svg/table/workspace/runs/pieces/void-POST/studio-work-size) → **404 ×10, zero 500s** | fail-closed | **BY DESIGN** (enumeration inside management = the shared workspace; outside = dispatch-blocked) |
| Ownership enforced in services/querysets/middleware/templates? | no per-manager rules exist to enforce; ROLE gates proven at all four layers (dispatch mixin ×55 · managed home rule · service `_ensure_management`/`_gate` · blueprint perm) | n/a | **BY DESIGN** |
| Phase-I documented boundaries? | `_ManagementOnly` everywhere ✓ · blueprint stricter perm ✓ (mgr 403 / SA 200) · worker wall ✓ (below) | all hold | verified |

B-creation proofs: B usage on MRK-000002/LOWER-002 → **`confirmed_by=mgmt1` (pk 20)** · B mat
`mgtg-b-mat` → **`created_by=mgmt1@test`**.

### G3 — worker regression + SA control

Worker: home → **302→my-dashboard** (managed rule) · marker-list/detail, mat-detail, candidate-svg,
candidate-pdf → **403 ×5** · usage-new + mat-new POSTs → **403 ×2, zero writes** (deltas 0).
SA: marker-list/dashboard/candidate-svg → **200 ×3**. No false lock-out.

### G4 — browser evidence (live :8003, `dev.mgr`, artifact-free)

1. `/patterns/dashboard/` renders "Pattern Dashboard"; **SA-created MRK-000002 detail opens for
   dev.mgr** (cross-user read live). `/patterns/blueprint/` → **branded "Error 403"** page.
2. **CSRF-valid POSTs (fetch, real csrftoken):** void garbage-pk → **404** (fail-closed) ·
   mat-new with invalid slug (`bad code with spaces`) → **200 form error** · candidate-pdf →
   **200 application/pdf**. DB re-checked: mats 2 (no bad-code row), usage-1 unvoided —
   **zero artifacts left by this phase.**

### Suspect classification

| Suspect | Verdict |
|---|---|
| Any manager can see/edit/void/export any pattern object | **BY DESIGN** — shared management workspace over product-anchored factory knowledge (G0 evidence chain); actor stamps carry the true actor where stamp fields exist |
| `MarkerUsage` void has no `voided_by` column (actor only in app log) · `retire_mat` captures actor nowhere | **INFO → DEPLOYMENT_BACKLOG #9** — management-gated, F2 reason-mandatory, append-only; audit-hygiene only, NOT fixed (0-confirmed-bugs mandate) |
| Sequential integer IDs guessable | **BY DESIGN / fail-closed** — reachable only by management (the shared workspace); ×10 garbage probes 404; non-management dispatch-blocked |
| patterns_ai README says "P1 Block 1 — foundation only" | **KNOWN DOC DRIFT** (pre-logged: campaign doc-audit "3 drifted app READMEs"); doc-only, KOS phases 6-7 scope; untouched (no code changed this phase) |

### Close-out

**0 confirmed bugs → no fixes, no pins, battery NOT re-run (1526/1526 stands).**
Certification strength: artifact-backed (23-GET ALLOWED matrix · 6-export content-type proofs ·
B→A cross-manager chains with DB stamp verification · ×10 fail-closed enumeration · worker ×8 +
SA ×3 cross-checks · live-browser cross-user read + branded-403 + 3 CSRF-valid artifact-free POSTs
with DB re-checks · one-transaction rollback with byte-identical recount). **The Phase-I caveat is
closed: cross-manager isolation is not a missing wall — it is the designed shape of the module;
role walls (management vs everyone) and actor-stamp honesty are what the design requires, and both
are proven live.** Next: MGT-H meta-audit (owner-gated).

## MGT-H — Meta-audit + close (2026-07-12) ✅ — PHASE 1 VERDICT: CERTIFIED

> Not a summary of MGT-A..G — a fresh system-level instrument pass: programmatic census of the
> ENTIRE root URLConf, a dual-identity dynamic sweep, the rendered-sidebar-vs-matrix check, and a
> line-by-line backlog review. 0 code changes; sweep rollback-wrapped (read-only GETs).

### H1 — URL census (static instrument, whole root URLConf)

Programmatic walk of `get_resolver().url_patterns`: **528 total routes.** Every route classified by
its strongest dispatch gate (CBV MRO scan) and joined against the live `SidebarItemRule` table:

| Gate class | Routes | Disposition |
|---|---|---|
| `_ManagementOnly` (68) · `ManagementRoleMixin` (20) · `ManagerOrAdminMixin` (5) | 93 | manager-ALLOWED surfaces — certified MGT-A..G |
| `ProductionRoleMixin` (65) | 65 | production surfaces; real law = service gates + managed rules (MGT-B/D) |
| `SuperAdminOnlyMixin` (12) · `SuperuserRequiredMixin` (12) · `_SuperAdminOnly` (2) | 26 | SA-only walls — manager-blocked proven (MGT-A/D/E/F) |
| `_StagePermissionRequired` (10) · `_PatternPermissionRequired` (4) · blueprint `UserPassesTestMixin` (1) | 15 | Django-perm delegation seams — pure manager holds 0 perms → blocked (MGT-A/G) |
| `ListingTeamMixin` (8) | 8 | storefront wall — manager-blocked (MGT-F) |
| `LoginRequiredMixin`-only (8) | 8 | ALL previously judged by-design: S3 email-shadow · my-earnings self-view · worker-detail (internal mgmt flag) · worker-report (own-task, D6) · review-reports (in-view mgmt `_gate`) · stage-advanced bounce · 2 patterns redirect hops |
| No project gate (313) | 313 | django-admin 277 (AdminSite staff wall) · allauth 21 (S2 adapter-closed signup; auth-only, no management data) · accounts auth flows 8 (public by design) · inventory 6 (dashboard redirects, my-dashboard, scan pair + legacy export with certified in-view gates) · public_home 1 |

**No unmanaged or forgotten manager-accessible route exists** — every project route lands in a
certified gate class or an enumerated, previously-judged login-tier/public class. `SidebarItemRule`
join reproduces exactly the 21 known rules (6 Administration empty-role double-gates; no drift).

### H2 — dynamic sweep (fresh probes, manager + worker in parallel)

All **95 parameterless project+allauth routes** GET-probed as `dev.mgr` AND `dev.ow.a` in one
rollback-wrapped pass, with automatic anomaly rules (mgr 500 · mgr 200-on-SA-only/listing ·
mgr false-403 on mgmt GET · worker 200-leak on mgmt/SA route · worker 500): **ZERO anomalies.**
Spot rows: managed lists → mgr 200 / wkr 302 pre-view (/patterns/, /production/, /tracking/) ·
SA-only → both blocked (302 managed / 403 mixin, e.g. /app/users/ 302·302, roles/add 403·403) ·
mgmt surfaces → mgr 200 / wkr 403 (×13: machines, payroll, settlements, expenses, advances…) ·
self-view /expense/my/ 200·200 · public / 200·200 — all by design. **`/admin/` as manager →
302→/admin/login/ (staff wall holds).**

### H3 — rendered sidebar vs certified matrix (live browser, dev.mgr)

Sidebar renders **19 links; every one fetched in-session → 200 ×19** (My Dashboard · My Earnings ·
Operations · Machines · Pattern Intelligence · Costing · Addas · Products · 6 raw-materials ·
Barcode Dashboard · Payroll · Settlements · Record Advance · Factory Expenses). **Zero
visible-but-forbidden items; zero hidden-but-needed items** (every certified manager job surface is
reachable from the menu or its parent pages). Administration, Storefront, Product Patterns, Stages
absent — and their URLs independently re-proven blocked in H2 (hidden ⇒ unreachable, rule-6 law).

### H4 — cross-app consistency (the philosophy check)

One philosophy everywhere, no exceptions found: **dispatch gate (or managed empty-role rule) →
service re-gate → fail-closed designed refusal.** Managed-denied = 302+flash (AJAX 403 JSON,
proven MGT-D/F) · unmanaged action = mixin 403 (branded page) · service refusals = error flash +
zero writes (MGT-B/C/E) · money SA-splits enforced in services not templates (MGT-C ×4) ·
financial fields walled at 4 layers (MGT-D/E) · no template-only hiding anywhere certified (every
cosmetic render-but-403 case enumerated as INFO with fail-closed proof). The two import-class 500
bugs this philosophy produced (MGT-B-1, MGT-F-1) were fixed + pinned during certification.

### H5 — backlog review (all 9 rows, line-by-line)

#1 export-code contention (perf infra) · #2 RESOLVED · #3 inline-style polish · #4 test-infra
(parallel + fresh-DB laws) · #5 FIXED · #6 RBAC.md doc drift (certification evidence supersedes;
KOS phase 7) · #7 archive-confirm garbage-pk 500 (hand-typed URL, fails closed) · #8 machine-assign
worker-param (data hygiene, management-only) · #9 patterns_ai actor stamps (audit hygiene).
**None is, or has become, a management-permission issue. Nothing fixed (INFO rule). No new rows.**

### H6 — FINAL VERDICT

**THE MANAGEMENT PERMISSION MODEL IS CERTIFIED.** Grounds:
1. Coverage: MGT-A..G certified every app on all three axes (BLOCKED/ALLOWED/FUNCTIONAL) with
   artifact-backed probes; H1/H2 close the completeness gap system-wide (528-route census, zero
   unaccounted routes; 95-route dual-identity sweep, zero anomalies).
2. Boundaries hold at every layer: middleware double-gates (Administration) · dispatch mixins ·
   Django-perm seams · service gates (money SA-splits, financial fields) · staff wall (/admin/).
3. Functional axis: zero false 403s, zero 500s on any reachable manager surface after the 3 fixes
   (MGT-B-1 lane import · backlog #5 delete-confirm · MGT-F-1 code-guard bypass), each fixed +
   pinned + battery-proven (**1526/1526 GREEN, sequential fresh-DB canonical**).
4. Cross-manager isolation judged BY DESIGN ABSENT with runtime proof (MGT-G).
5. Residual risk = 4 open INFO rows (#6-#9), all non-exploitable, all recorded with fix-when-touched
   specs.

**Phase 1 (Management Role Certification) is COMPLETE.** Next campaign phase: Owner Visibility
Certification (phase 2, owner-gated).
