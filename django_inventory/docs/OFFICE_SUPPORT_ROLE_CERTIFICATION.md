---
id: office-support-role-certification
type: evidence-cert
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Office / Support Role Certification — Campaign Phase 3

> Pre-deployment campaign, opened 2026-07-13 (OFF-0). Sibling of
> [WORKER_ROLE_CERTIFICATION.md](WORKER_ROLE_CERTIFICATION.md) (CLOSED),
> [MANAGEMENT_ROLE_CERTIFICATION.md](MANAGEMENT_ROLE_CERTIFICATION.md) (CLOSED, CERTIFIED) and
> [OWNER_VISIBILITY_CERTIFICATION.md](OWNER_VISIBILITY_CERTIFICATION.md) (CLOSED, CERTIFIED).
> Campaign resume anchor: [DEPLOYMENT_CAMPAIGN_STATUS.md](DEPLOYMENT_CAMPAIGN_STATUS.md).
> Engine FROZEN — fix ONLY confirmed bugs, pins only for fixes, battery rerun only on code change
> (baseline **1530/1530**, sequential fresh-DB canonical).
> **Execution contract: [campaign_contracts/PHASE_03_OFFICE_SUPPORT_CERTIFICATION.md](campaign_contracts/PHASE_03_OFFICE_SUPPORT_CERTIFICATION.md)
> (🔒 frozen; its Appendix A Design Record was filled by the owner at OFF-0, below).**

## What this certifies (three axes, per contract §6.1)

The two remaining specialist roles: **`accountant`** (FINANCIAL_ROLES member) and
**`listing_team`** (STOREFRONT_ROLES member) — the smallest designed surfaces in the system.
Phase 3 is dominated by negative space plus a small functional core never exercised before:

1. **BLOCKED (hostile-negative):** each role refused on every surface outside its designed set —
   dispatch mixins, middleware overlay, service re-gates, CSRF-valid escalation POSTs,
   hand-crafted POSTs, AJAX forks, enumeration/garbage-pk fail-closed.
2. **ALLOWED + FUNCTIONAL:** the designed surface works end-to-end with the specialist driving —
   listing: full storefront CRUD lifecycle; accountant: financial-field read AND write landing in
   DB + history **under the D1-ratified identity shape (composite — see Design Record)**.
   200-GET is not functional proof; the write must LAND (then roll back or be disclosed).
3. **UNIVERSAL WALLS + prior fixes:** S2 signup-closed + S3 email-shadow hold for these
   identities; POST-only endpoints 405 on GET; SA-only levers refuse them; prior-fix guard list
   (contract §14) holds with these roles driving.

Headline novelty resolved at OFF-0: the **pure-accountant reachability contradiction**
(contract §2.2.1 — the role's own financial-field grant sits on pages that dispatch-403 a pure
accountant) is ruled **BY DESIGN under D1 = add-on deployment model** (see Design Record);
OFF-A certifies composite-functional + pure-blocked.

## Certification identities (cast, verified/created at OFF-0)

| Identity | pk | Shape (verified read-only 2026-07-13) | Purpose |
|---|---|---|---|
| `dev.accountant@test.local` | 61 | active · role=accountant · extra=[] · no flags — PURE (D3: reused, password reset to Dev@12345 at OFF-0) | pure-accountant lane |
| `dev.acct.mgr@test.local` | 76 | active · role=manager · extra=[accountant] · no flags — **created at OFF-0 per D2** (Dev@12345; retained permanently as documented DEV identity, owner order) | composite lane (D1=(a)) |
| `dev.listing@test.local` | 62 | active · role=listing_team · extra=[] · no flags — PURE | listing lane (Dev@12345 pattern per framework README; verify at OFF-B login) |
| `dev.mgr@test.local` | 52 | active · pure manager | negative control (Phase-1 regression) |
| `dev.ow.a@test.local` | 46 | active · pure worker | negative control (Phase-W regression) |
| `umesh29mar@gmail.com` | 1 | SA (su+staff, all aligned) | positive control (owner supplies password per session) |

Login `/app/login/password/` — rate-limited per IP+email, ONE careful attempt per identity
(lockout = contract §16.6 stop).

## Method (locked, per sub-phase — the 10-step loop, unchanged from Phases 1/2)

1. Read app docs + urls.py. 2. Gate-map audit per URL for THIS role (mixin → DB rule → service →
template). 3. Shell probes (GET matrix, then rollback-wrapped writes). 4. Browser on :8003 (real
login, real forms, CSRF-valid POSTs, DEV-marked data). 5. Fix ONLY confirmed bugs (smallest
change; U14 stop). 6. Pins only for fixes. 7. Battery per U5 only if code changed. 8. Docs-sync.
9. Status file + memory. 10. STOP — next sub-phase owner-gated.

## Evidence standard (contract §5 — Phase-1/2 lineage + Phase-3 additions)

Per-URL status matrix, shell AND browser, PER IDENTITY · exact flash/error/JSON quotes ·
CSRF-valid POSTs with DB re-check · rollback-wrapped shell writes, byte-identical recounts ·
SA + manager + worker controls on every probed surface. Phase-3 additions:
**two-sided financial-leak proof** (same roll: accountant-positive AND manager/worker-negative in
one evidence block) · **expectation-matrix accounting** (every observed outcome reconciled vs the
matrix below; any mismatch = finding) · **middleware-fork proof** (≥1 managed-blocked URL per
identity: non-AJAX flash+302 AND AJAX JSON 403 quoted) · sub-agent findings supplemental (U7);
money-adjacent probes + all verdicts main-thread.

## Expectation matrix (contract §6.2 copy — certified baseline as amended by the Design Record)

Legend: ✅ allowed+functional · ❌403 view-mixin refusal · ❌302/JSON middleware refusal · SELF
self-scoped only. Composite column ACTIVE (D1=(a), D2=yes). D4=NO ⇒ the payroll door row is
certified CLOSED.

| Surface | Pure accountant | Composite (mgr+acct extra) | listing_team |
|---|---|---|---|
| Main: my_dashboard, my-earnings | ✅ (SELF, exempt landings) | ✅ | ✅ (SELF) |
| Production (all) | ❌ | manager-lane (Phase-1 matrix) | ❌ |
| Raw materials: dashboards, roll list/detail, masters lists | ❌403 (ProductionRoleMixin) — BY DESIGN per D1=(a) | ✅ pages + ✅ financial columns/history/write | ❌ |
| Raw materials: roll edit/damage/assign, masters CRUD | ❌403 (ManagementRoleMixin) | ✅ + financial fields present in forms | ❌ |
| Raw materials: bulk-add | ❌403 (SuperAdminOnly) | ❌403 (composite is NOT SA) | ❌ |
| Financial FIELDS (supplier/cost_per_kg) | service-level grant exists; UI-unreachable BY DESIGN (D1) | ✅ view+edit, service accepts, history rows written | ❌ stripped/refused |
| Expense: payroll/settlements/advances/factory-expenses/profile | ❌403 (_ManagementOnly) | manager-lane (4 SA-only levers still refused) | ❌ |
| Expense: /my/, /workers/<own_pk>/ | ✅ SELF (empty) | ✅ | ✅ SELF |
| Expense: /workers/<other_pk>/ | ❌ (can_view_worker; **D4=NO — door certified CLOSED**) | ✅ (management lane) | ❌ |
| Tracking: all 12 routes | ❌ (PRODUCTION/MANAGEMENT gates) | manager-lane ✅ | ❌ |
| Storefront: 8 management CBVs | ❌403 (ListingTeamMixin) | ❌403 (manager ∉ STOREFRONT_ROLES — MGT-F regression) | ✅ full CRUD |
| Storefront: public homepage `/` | ✅ (anonymous surface) | ✅ | ✅ |
| Accounts: own login/logout/password flows | ✅ | ✅ | ✅ |
| Accounts: users/skills/user-types CRUD | ❌ (SA-only) | ❌ | ❌ |
| Accounts: S2 signup, S3 email management | ❌ walls hold | ❌ | ❌ |
| Inventory Administration | ❌ (SA-only + double gate) | ❌ | ❌ |
| machines, patterns_ai | ❌ (management-gated) | manager-lane ✅ | ❌ |
| `/admin/` | ❌ staff wall (302→admin login) | ❌ | ❌ |
| Sidebar render | Main only (seeded) | manager sidebar (Phase-1 baseline 19 links) | Main + Storefront (3 seeded rules) |

## Resumability

A fresh session continues from **DEPLOYMENT_CAMPAIGN_STATUS.md** + this file + the contract §17.
Each sub-phase appends ONE section below at close; never edit a closed section (corrections
appended, dated).

---

## OFF-0 — Charter + owner Design Record + identity census (2026-07-13) ✅ — NO probing

**Verdict: OFF-0 CLOSED. D1–D4 owner-ratified and recorded verbatim (here + contract Appendix A).
Preconditions verified with ZERO material drift. Two owner-authorized durable identity writes
landed + disclosed. 0 bugs, 0 code changes, battery NOT re-run (1530/1530 stands).**

### Design Record (owner answers, 2026-07-13, recorded verbatim)

| # | Item | Owner answer |
|---|---|---|
| **D1** | Accountant deployment model | **(a) ADD-ON role only** — intended to be stacked via `extra_roles` on top of manager or super admin where financial capabilities are required. No RBAC redesign. ⇒ Certification target: composite FUNCTIONAL + pure-blocked BY DESIGN; the §2.2.1 reachability contradiction is resolved **BY-DESIGN-with-citation** (this record) |
| **D2** | Composite probe identity | **YES** — create `dev.acct.mgr@test.local` (manager primary + accountant extra, Dev@12345); **retain permanently as a documented DEV identity** ⇒ created at OFF-0, pk=76, verified below |
| **D3** | `dev.accountant@test.local` | **REUSE** — do NOT recreate; reset password to Dev@12345 if required ⇒ reset performed at OFF-0 (credentials were unrecorded), pk=61, purity verified below |
| **D4** | `expense.view_all_payroll` | **INTENDED = NO** — not intended for the accountant role; the current zero-holder state IS the intended design ⇒ OFF-A certifies the door CLOSED (matrix row ❌) |

### Preconditions verification (contract §17.4, all read-only)

- **Git:** HEAD `49404001` exact · 311 dirty/untracked paths (stable vs OWN-H's 311) · no git writes.
- **Battery:** status-dashboard baseline **1530/1530** stands (no code change this sub-phase; not
  re-run). **Dated drift note:** contract §13 states "baseline entering OFF-0: 1526/1526" — the
  contract was authored 2026-07-12 before the OWN-C-1/OWN-D-1 pins; arithmetic 1526+2+2=1530 is
  on record (OWN-H §H6); status file wins on state (framework conflict rule). Not §16.10 drift.
- **§2.2 gate facts spot-checked in code — ALL EXACT:** role sets + financial predicate
  (view==edit shared, observation (b) stands) `permission_service.py:29-38,96-103` ·
  `user_role_codes` extra-roles union `:65-88` · `_role_perm_codenames` PRIMARY-FK-only `:106-124`
  (OWN-D fact re-verified) · `user_has_perm` codename split + Django-native fallback `:127-158` ·
  raw_materials mixins exclude accountant (`mixins.py:15-43` — contradiction stands) · expense
  `_ManagementOnly` (`views.py:60-62`) · `can_view_worker` = self ∨ management ∨
  `expense.view_all_payroll` (`payroll_service.py:154-166`) · `ListingTeamMixin` hand-builds
  {SA, listing_team} (`listing_views.py:24-27` — pre-registered duplication observation stands,
  OFF-B judges) · seeds: roles 0-perm (0016 docstring "no migration ever seeded
  role.permissions") + accountant ONE sidebar rule / listing_team three (0017).
- **§7 probe anchors EXACT:** roll pk=1 `CR-000001` supplier='Validation Supplier' /
  cost=200.00 / used · roll count **32** · FeaturedProduct **1** · Category **1**.

### §2.3 DB-resident census (live dev DB, read-only ORM — zero writes in this census)

- **Role-perm census (D4 baseline):** all 5 system roles hold **0 Django permissions**.
- **`expense.view_all_payroll`** = Permission id=237 (expense/workerledgerentry): held by
  **no role, no user_permissions, no group** — zero-holder state, now RATIFIED as intended (D4).
- **SidebarItemRule census: 21 rows** (matches MGT-H/OWN-H). Accountant in exactly ONE rule
  (id=2 `inventory:user_dashboard`, shared worker+listing_team+accountant); listing_team in 3
  (ids 2, 3 `storefront:product_list`, 4 `storefront:category_list`). Live state == seeds — no
  runtime widening for either role.
- **Identity census:** table above. Additional D1 evidence: **zero users carry accountant in
  `extra_roles`; zero users in the entire DB use `extra_roles` at all** — the composition path
  was code-only until D2's composite was created below. `dev.accountant` (pk=61) pre-existed
  PURE (joined 2026-07-10, last_login 2026-07-10 19:30 — matches the security.log provenance in
  contract §2.2.1).

### Identity actions (the ONLY writes of OFF-0 — owner-authorized, durable, disclosed)

1. **D2 create:** `dev.acct.mgr@test.local` pk=**76** — `create_user` + role=manager FK +
   `extra_roles.add(accountant)`, active, no flags. Verified: `check_password('Dev@12345')`=True
   (hash check only — login view/rate-limiter untouched) · `user_role_codes` =
   {accountant, manager} · `user_can_view_financials`/`user_can_edit_financials` = True/True ·
   `user_has_role(MANAGEMENT_ROLES)` = True. Retained permanently (owner order, cast list above).
2. **D3 reset:** pk=61 `set_password('Dev@12345')` (password column only). Verified:
   `check_password`=True; shape unchanged (active, pure accountant).

**Disclosed durable artifacts:** User count 47→**48** (pk=76) · pk gap 62→76 = auto-increment
consumed by prior phases' rollback-wrapped throwaway users (sequences don't roll back) ·
pk=61 password hash replaced (old credential unrecorded, now standardized to the DEV cast
pattern). No other row in any table changed; no login attempts made; no probing performed.

### Observations (reported, not fixed — U12/freeze discipline)

- `docs/DOCUMENTATION_INDEX.md` row for OWNER_VISIBILITY_CERTIFICATION.md still reads "OWN-0
  done, OWN-A..H paused (contract-first mode)" — stale vs Phase-2 CLOSED/CERTIFIED reality.
  Doc-drift class → KOS phases 6/7 venue (same lane as backlog #6); reported to owner here.

### Charter deliverables checklist (contract §7 OFF-0 row)

Charter (this file: 3-axis definition · identities · expectation-matrix copy · evidence
standard) ✅ · filled Design Record (here + contract Appendix A) ✅ · verified identity table ✅ ·
SidebarItemRule census vs seeds ✅ · role-perm census (D4 baseline) ✅ · git/battery baseline ✅ ·
NO probing ✅.

**Next: OFF-A — accountant certification (pure pk=61 + composite pk=76 lanes per D1), owner-gated.**

---

## OFF-A — Accountant certification (2026-07-13) ✅ — ACCOUNTANT VERDICT DELIVERED

**Verdict: The `accountant` role is CERTIFIED under the D1-ratified add-on deployment model.
The §2.2.1 reachability contradiction is resolved BY-DESIGN-WITH-CITATION. 0 confirmed bugs,
0 code changes, battery NOT re-run (1530/1530 stands), 1 new INFO (backlog #13). Every probe
byte-identical after rollback; the two owner-authorized OFF-0 identities are the only DB deltas.**

### §3.3 accountant structural verdict (the headline)

The pure accountant is dispatch-refused from every page hosting its own `supplier`/`cost_per_kg`
grant — **PROVEN and classified BY DESIGN**: owner D1 = the accountant is an ADD-ON role, only
ever stacked via `extra_roles` onto manager/SA. The grant is a *capability* (financial fields =
FINANCIAL_ROLES, role-code union), NOT a *page-access* role (pages = PRODUCTION/MANAGEMENT/SA
mixins). A pure accountant therefore correctly reaches nothing but its own SELF surfaces; the
financial capability becomes reachable only when composed onto a page-bearing role — which is
exactly the ratified model. The capability is proven FUNCTIONAL end-to-end on the composite lane
(financial write lands in DB + history via the single-writer, then rolled back / DEV-roll torn
down). No new page gate was added (contract forbids it without an explicit order; none given).

### Preconditions (§17.4, read-only) — zero material drift

HEAD `49404001`; identities exact (pk=61 pure accountant · pk=76 composite mgr+[accountant] ·
controls pk=52 mgr / pk=46 worker / pk=1 SA / pk=25 `dev.monthly` worker for other-pk). Anchors:
rolls **32**, roll pk=1 `CR-000001` 'Validation Supplier'/200.00/used, roll history **40**,
financial history rows **0**, SidebarItemRule **21** (accountant in 1 rule id=2; live == seeds),
`view_all_payroll` (perm id=237) held by **no role/user/group**. In-stock (`not_used`) rolls: pk=21
NKS-R4, pk=27 SHA-R4 (edit targets).

### Gate-map audit (per surface, both lanes)

Financial grant = one shared predicate `user_can_view_financials == user_can_edit_financials ==
user_has_role(FINANCIAL_ROLES)` (permission_service.py:96-103). raw_materials mixins
(mixins.py:15-43): ProductionRole (dashboards/list/detail) · Management (roll edit/damage/assign +
masters CRUD) · SuperAdminOnly (bulk-add) — **accountant ∈ none**; service re-gate
(roll_service.py:79,173) `PermissionDenied` on financial fields for non-FINANCIAL. expense
`_ManagementOnly` (views.py:60) + `can_view_worker` = self ∨ MANAGEMENT ∨ `view_all_payroll`
(payroll_service.py:154-166). SidebarAccessMiddleware: managed url_name + no role overlap → 302
(non-AJAX) / JSON 403 (AJAX), BEFORE the view mixin.

### PURE ACCOUNTANT lane (pk=61) — shell, real password login (1 attempt, landed my-dashboard)

**GET matrix (every outcome reconciled to §6.2):**
- Main: my_dashboard 200 · expense my-earnings 200 · worker-detail SELF 61 200 — ✅ SELF (exempt).
- raw_materials: 6 MANAGED list URLs (dashboard/cloth-dashboard/roll-list/type-list/color-list/
  storage-list) → **302** to my-dashboard (middleware); all UNMANAGED (roll-detail/edit/damage/
  assign/bulk-add + every masters add/edit/archive/delete) → **403**. Matrix cell says "❌403";
  the 302/403 split is the §2.2.3 double-gate (managed rule fires middleware first) — legend
  admits ❌302 for managed exclusion. **The contradiction surface (roll-detail/edit 403) = BY
  DESIGN.** Enumeration roll-detail 99999 → 403 (mixin before object lookup, fail-closed).
- expense: payroll-overview/settlement/profile/pay-basis/fnf/advance/factory-expense(×2)/
  adda-settlement(list/start/detail) all **403**; **worker-detail OTHER 25 → 403 (D4 door)**;
  worker-detail garbage 99999 → 404.
- tracking ×13: dashboard 302 (managed); barcode-list/print/export/scan/roll-history/adda-history/
  export-list/download **403**; scan-status + export csv/xlsx/pdf **405** (POST-only). No financial
  columns anywhere.
- negative sweeps: production dashboards 302 (managed) / adda-create·product-create·pattern-list·
  costing 403 · machines list+add 403 · patterns_ai home 302 (managed) + dashboard 403 · storefront
  product/category_list 302 (managed) + add 403 · accounts user/skill_list + inventory role_list/
  sidebar-access/access-control 302 (managed roles=[]) · `/admin/` 302→admin-login · home `/` 200.

**Middleware fork (roll-list):** non-AJAX → 302, final /inventory/my-dashboard/ (flash consumed on
landing); AJAX (`X-Requested-With`) → **403** `{"detail": "You don't have the access to this page."}`.

**Sidebar render (my_dashboard):** links = ONLY `/inventory/my-dashboard/` + `/expense/my/`
(Main + self Payroll); Raw Materials / Production / Tracking / Administration absent — matches the
seeded single accountant rule.

**CSRF-valid escalation POSTs (all refused, DB inert):** roll-edit-21 financial (403) · cloth-type-
create (403) · worker-pay-basis-25 (403) · machines-add (403) · storefront category_add (403).
Post: roll21 supplier='' cost=200.00 unchanged; counts rolls/types/machines/cats all baseline.

**S2/S3 walls:** GET /accounts/signup/ → 302 /app/home/; POST → 302, **no user created**; GET
/accounts/email/ → 302 (shadow bounce); POST → 302, **pk61 email unchanged**.

### D4 payroll door — CLOSED proof (rollback-wrapped)

no-grant GET workers/25/ → **403**; grant `view_all_payroll` to the accountant Role on a savepoint
→ GET → **200** (door mechanism is real); savepoint rollback → GET → **403**; role holders back to
**0**. **Certified CLOSED as the intended state (D4=NO); zero grant leaked.**

### COMPOSITE lane (pk=76, manager primary + accountant extra) — shell, real password login (landed /production/)

**GET matrix:** raw_materials all **200** (dashboards/list/detail/edit/assign/masters lists) +
bulk-add **403** (SA-only, composite is not SA); expense manager-lane all **200** (payroll/
worker-detail-25/settlement/fnf/advance/factory-expense/adda-settlement), worker-pay-basis GET
**405** (POST-only); production dashboard/adda-list/product-list/costing **200**, stage-list **302**
(managed roles=[]), product-create **403** (SA-only); tracking dashboard/barcode-list/roll-history/
export-list **200**; machines list **200**; patterns_ai home+dashboard **200**; storefront
product_list **302** (managed listing) + product_add **403** (ListingTeamMixin — **manager ∉
STOREFRONT_ROLES, MGT-F regression holds**); accounts/inventory admin **302** (managed roles=[]);
`/admin/` **302**. Sidebar render: Raw Materials + Production + Tracking + Payroll (+ Machines +
Patterns) present, Administration absent — manager lane.

**FINANCIAL FUNCTIONAL WRITE — the core objective (both paths landed, rollback-wrapped):**
- *Render:* composite roll-detail-1 shows supplier 'Validation Supplier' + cost 200.00; manager
  sees neither (server-side excluded). Composite roll-edit-21 form carries `supplier` +
  `cost_per_kg` fields; manager roll-edit form has **neither** (form pops them, form_forms.py:144).
- *Update-path (view/form):* POST roll-edit-21 (supplier='DEV OFFA Supplier', cost=222.33,
  width=40) → redirect to roll-detail (success), **DB: supplier='DEV OFFA Supplier' cost=222.33** +
  **2 history rows via single-writer** (field=supplier old=''→new, field=cost_per_kg
  old=200.00→222.33, **actor=76**). *(First POST used the roll's stored width=60, outside the
  form's 36-44 choices → form-invalid "Select a valid choice" — probe-payload error, not a defect;
  corrected width=40, write landed. Disclosed.)*
- *Create-path (service, composite actor):* `bulk_create_rolls(pk76, supplier='DEV OFFA SvcCreate',
  cost=111.11)` → roll LANDED with financials + CREATED history **actor=76**.
- *Service acceptance / refusal controls:* manager `bulk_create_rolls` + `update_roll_details` with
  financials → **PermissionDenied "Supplier and Cost Per KG require Accountant or Super Admin role"**
  (both). Manager HACK-injection view POST (supplier+cost+weight) → weight saved, **financials
  inert, 0 financial-history rows** (4-layer wall holds).

**Two-sided leak proof (same roll 21, post-edit, in one transaction):**
| viewer | detail-21 supplier/cost visible | roll-history-21 financial rows | roll-list financial col |
|---|---|---|---|
| composite | **YES** / YES | 200, **visible** | **shown** |
| SA | YES / YES | 200, visible | (control) |
| manager | **NO** / NO (weight ctrl visible) | 200, **hidden** | **not shown** |
| worker | NO / NO | **403** | — |

**bulk-add SA-only wall (composite):** GET 403 · CSRF POST 403 · roll count inert.
**Middleware fork (storefront product_list):** non-AJAX 302→my-dashboard; AJAX 403 JSON.
**S2/S3 (composite):** signup 302 no-create; email 302 no-change; pk76 email unchanged.
**Worker regression spots:** roll-list 302 (managed) · roll-edit-21 403 · payroll-overview 403 ·
my-earnings 200 (self). Zero regression.

### Browser verification (:8003, both identities, real logins)

- **Pure accountant** (pk=61, Dev@12345): landed `/inventory/my-dashboard/`; sidebar = ONLY *My
  Dashboard* + *My Earnings*; roll-list (managed) → bounced to my-dashboard; roll-detail-1
  (unmanaged) → branded **"Access denied — 403"** page.
- **Composite** (pk=76): landed `/production/`; full manager sidebar (RM ×6 + Production + Machines +
  Patterns + Tracking + Payroll ×4; no Administration/Storefront links). On a **DEV-marked roll
  (CR-000019, created via SA service for this proof)**: roll-detail rendered supplier+cost;
  roll-edit form carried both financial fields prefilled; **CSRF-valid Save landed** (redirect to
  detail, new values 'DEV-OFFA-BROWSER-EDITED' / 133.44 render) with history rows stamped
  **actor=76** via the single-writer. Then torn down (roll + 4 history rows deleted) → **zero
  residue** (roll count back to 32, financial-history 0).

### Pre-registered observations judged (contract §2.2.1)

- **(a) dead `can_edit_financials` context flag** (stage_views.py:329 computes, :404 passes, zero
  template consumers — grep-verified) → **INFO, backlog #13**. Dead read-only variable; the service
  guard is the real gate and is independent; the layering page is ProductionRole-gated so the
  accountant never renders it. Not a bug; engine-frozen, fix-when-touched.
- **(b) view==edit shared predicate** (a view-only accountant is inexpressible) → **BY DESIGN**. The
  seeded Role description is "Can view + edit Supplier and Cost Per KG"; D1=(a) grants both as one
  capability; no product requirement for a view-only variant exists. Not a defect.
- *(minor, not raised)* financial history rows carry `change_type='weight_updated'` (RollUpdateView's
  generic field-change type) — pre-existing labeling accepted silently at OWN-E; field_name/old/new/
  actor are all correct; out of scope, no new row.

### Expectation-matrix accounting

Every probed URL for both lanes reconciles to §6.2 (managed exclusions surface as 302, unmanaged as
403 — both are the designed refusal; legend covers it). **Zero unexplained outcomes; zero matrix
mismatches; zero leaks; zero false blocks.** Negative controls (manager + worker) held on every
accountant-exclusive surface; SA positive controls implicit in the two-sided proof.

### Rollback / disclosed artifacts

All shell probes ran inside forced-rollback atomics; post-rollback recount **byte-identical**
(users 48, rolls 32, roll-history 40, financial-history 0, `view_all_payroll` role-holders 0,
roll21 supplier='' cost=200.00). Browser DEV roll created→edited→deleted (zero residue).
**Disclosed durable delta:** `cloth_roll_seq` consumed 3 values (16→19: CR-000017/18 shell-
rollback + CR-000019 browser, all gone — Postgres sequences never roll back); pk=76 retained (D2).
No login rate-limit lockout (1 careful attempt per identity). Money-Write STOP never triggered
(the only financial writes were via the certified single-writer path, all rolled back / torn down).

### Success criteria (§3) — OFF-A slice

3 (accountant verdict delivered, §3.3 = BY-DESIGN-with-citation + composite functional) ✅ · 5
(cross-role isolation preview: financial two-sided proof, manager blocked while composite/SA
positive on the SAME roll) ✅ · 6 (every 403/302/405/404 classified) ✅ · 7 (worker+manager
negative controls held) ✅. Full OFF-B/C/D criteria remain for later sub-phases.

**Next: OFF-B — listing_team certification (owner-gated).**

---

## OFF-B — Listing-team certification (2026-07-13) ✅ — LISTING VERDICT DELIVERED

**Verdict: The `listing_team` role is CERTIFIED. First-ever functional storefront CRUD
certification as `dev.listing` (FeaturedProduct + Category full lifecycles LANDED, browser + shell)
and first-ever comprehensive listing negative census: zero unexplained admissions, zero leaks,
zero false blocks. 0 confirmed bugs, 0 code changes, battery NOT re-run (1530/1530 stands),
1 new INFO (backlog #14). Every probe byte-identical after rollback/teardown; live storefront
rows (pk=1) never touched.**

### Preconditions (§17.4, read-only) — zero material drift

HEAD `49404001`; :8003 serving (200). Identities exact: pk=62 `dev.listing@test.local` PURE
(active · role=listing_team · extra=[] · no flags · 0 user_permissions · 0 groups · role holds
0 Django perms); controls pk=52 mgr / pk=46 worker / pk=1 SA / pk=61+76 OFF-0 cast intact.
Password verified via `check_password('Dev@12345')`=True BEFORE any login (hash check only —
no attempt burned). Anchors EXACT: FeaturedProduct **1** (pk=1 '3 Patti', active) · Category
**1** (pk=1 '3 Patti') · SidebarItemRule **21**, listing_team in exactly ids 2/3/4
(user_dashboard shared + product_list + category_list = seeds, no runtime widening) · rolls 32 ·
users 48 · all 5 roles 0-perm. **Dirty-count note (dated):** porcelain = **312** = OWN-H's 311 +
the OFF-0-created evidence doc (`?? docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md` confirmed);
OFF-A's "311 stable" line was a stale count — all today-modified paths enumerated and every one
is an expected OWN-C/D-fix or campaign-doc artifact; not §16.10 drift.

### Gate-map audit

All 8 storefront management CBVs = `LoginRequiredMixin + ListingTeamMixin` at dispatch
(`listing_views.py:24-27`, hand-built `{ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM}` — §2.2.2
observation judged below). NO service gate: writes via ModelForms (`form.save()` →
`image_service.process_and_attach` = pure Pillow processing, no permission re-check); deletes =
plain single-row DeleteViews (documented non-service exception, `listing_views.py:103-110`).
Middleware overlay: managed set = the 21 rules; listing passes only 2/3/4; Administration rules
15-20 store roles=[]. Public homepage `/` = anonymous read-only composition (ADR-0008).

### PURE LISTING lane (pk=62) — shell, real password login (1 attempt)

Login POST `/app/login/password/` → 302 `/app/home/` → landed `/inventory/my-dashboard/`.

**Positive GET matrix (all reconcile to §6.2):** storefront product_list / category_list /
product_add / category_add **200** ×4 · my_dashboard **200** · expense my-earnings **200** +
worker-detail SELF 62 **200** (SELF, empty) · public `/` **200**.

**Sidebar render:** exactly `/inventory/my-dashboard/` + `/expense/my/` + `/storefront/products/`
+ `/storefront/categories/` — Main + self-payroll + the Storefront section; no other section
(matches seeds; same my-earnings self-link pattern OFF-A recorded for the accountant).

**FUNCTIONAL CRUD LIFECYCLE — the core objective (rollback-wrapped, CSRF-valid, flashes exact):**
- Category CREATE → `Category "DEV OFFB Category" created.` row landed · EDIT → rename persisted
  + `updated.` flash · delete-confirm GET **200** (#5-class watch PASS) · DELETE →
  `Category "DEV OFFB Category v2" deleted.` row gone.
- FeaturedProduct CREATE (category=DEV row, price 99.99, badge new) → `Product "DEV OFFB
  Product" created.` · EDIT → price 88.88 + badge hot persisted + `updated.` · delete-confirm
  GET **200** · DELETE → `deleted.` row gone.
- **Image path via `image_service`:** product CREATE with a real 600×450 PNG upload →
  processed to **400×300** (Pillow crop pipeline proven; saved
  `storefront/products/dev_offb_probe.jpg`) → row deleted in-txn; the disk file (storage writes
  don't roll back) deleted post-run + verified (media dir back to its pre-existing content).
- **Public homepage reflects listing edits (anon, in-txn):** anonymous client GET `/` → 200
  containing both DEV rows while they existed.
- In-txn counts returned to base (FP 1 / Cat 1) BEFORE forced rollback; post-rollback recount
  byte-identical.

**Negative sweep (first-ever comprehensive listing census — every outcome reconciled):**
**17×302** managed-rule middleware bounces (RM ×6 · production dashboard/adda-list/product-list/
stage-list · tracking dashboard · patterns_ai home · access-control/role_list/sidebar-access ·
accounts user_list/skill_list) · **1×301** `/inventory/dashboard/` = legacy-twin permanent
redirect BY DESIGN (middleware-exempt `middleware.py:32-34`; `dashboard_redirect`
`views/dashboard.py:296-300` — OWN-H posture) · **43×403** unmanaged view-mixin refusals
(RM roll-detail/edit/damage/assign/bulk-add/masters-create ×8 + enumeration roll-detail-99999
fail-closed · production adda-create/product-create/pattern-list/costing · patterns_ai
dashboard+blueprint · machines list+add · tracking barcodes/scan/history/export-list/download ×8
· expense payroll-overview/worker-25/settle/profile/pay-basis/fnf/advance/factory-expense ×2/
adda-settlement list+start ×11 · accounts user_add/skill_add/usertype_list · inventory role_add ·
tracking export-csv/xlsx/pdf GET ×3 — see classification below) · **1×404** expense
worker-detail garbage-pk · **1×405** tracking scan-status GET (POST-only) · `/admin/` **302** →
`/admin/login/?next=/admin/` (staff wall).

**Refusal-class classification (code-cited):** tracking export-csv/xlsx/pdf GET → **403** not
405 — they are CBVs (`_BaseExportTriggerView`, `tracking_exports.py:49-53`) where
`ManagerOrAdminMixin` (UserPassesTestMixin) dispatch-refuses BEFORE the `http_method_names`
check; scan-status is a function view whose explicit method check precedes its role gate → 405.
Both are designed refusals; matrix cell (❌ blocked) holds.

**Middleware fork (roll-list):** non-AJAX → 302 → `/inventory/my-dashboard/`; AJAX →
**403** `{"detail": "You don't have the access to this page."}`.

**CSRF-valid escalation POSTs ×6 (rollback-wrapped, all refused 403, DB inert proven):**
roll-edit-21 financial (supplier/cost injection) · cloth-type-create · worker-pay-basis-25 ·
machines-add · accounts user_add · inventory role_add. Post-block: roll21 supplier=''/cost=200.00
unchanged; types 6 / machines 4 / users 48 / roles 5.

**S2/S3 walls:** signup GET → 302 `/app/home/`; signup POST → 302, **no user created**; email
GET → 302 (shadow bounce); email POST → 302, **pk62 email unchanged**.

### Controls (shell `force_login` — no password attempts consumed; method disclosed)

- **Manager pk=52 (MGT-F regression re-proven):** product/category_list **302** (managed,
  listing-only rules) + add/edit-1/delete-1 **403** ×6 (ListingTeamMixin — manager ∉ set) +
  AJAX fork 403 JSON + category_add POST **403** count-inert.
- **Worker pk=46:** lists 302 / adds 403 / product_add POST 403 inert.
- **SA pk=1 positive control:** all 8 storefront URLs **200** (GET-only here; SA storefront
  CRUD-functional already certified at OWN-F).
- **Verification spots (accountant pk=61):** export-csv/xlsx/pdf GET → **403** ×3 ·
  scan-status GET → 405 · manager on export-csv GET → 405 — the basis for the OFF-A
  correction below.

### Browser verification (:8003, pk=62 real login, DEV-marked rows only)

Landed my-dashboard; sidebar = the 4 links above (screenshot on record). Full CRUD driven
through real forms: category `DEV OFFB Browser Cat` created (flash verbatim) → product
`DEV OFFB Browser Prod` created with the category chosen via FancySelect picker (design-system
control live) → **anonymous curl `/` showed both DEV rows** (committed browser writes; 2 category
+ 1 product mentions) → edit landed (price 55.55→44.44, `Product "DEV OFFB Browser Prod"
updated.`) → both delete-confirm pages rendered with warning copy (#5-class PASS; category
confirm shows "Products unlinked ho jaayenge, delete nahi.") → both deleted (flashes verbatim)
→ **anonymous `/` back to zero DEV mentions**, '3 Patti' intact. Refusals cross-checked
in-browser: `/raw-materials/rolls/` → bounced to my-dashboard with "You don't have the access
to this page." flash; `/machines/` → branded **Error 403** page. Signed out (session flushed).
Stray-pk probe categories/2/delete → 404 (fail-closed). Live pk=1 rows never opened for edit.

### Judged observations

- **§2.2.2 mixin-duplication (pre-registered) → INFO, backlog #14.** Grep census:
  `STOREFRONT_ROLES` has **zero functional consumers** — defined (`permission_service.py:31`)
  and re-exported only; BOTH live storefront gates hand-build the identical pair
  (`ListingTeamMixin` `listing_views.py:26-27` AND the sidebar Storefront section
  `permission_service.py:316-323` `_any_role(ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM)`). Membership
  equivalence proven live in both directions this sub-phase (listing+SA admitted; mgr/worker/
  accountant refused). Risk = dead lever: editing the constant changes nothing. Not a confirmed
  in-mandate defect (no wrong behavior; engine frozen; role-set-adjacent edit not licensed) —
  fix-when-touched: make both gates consume `STOREFRONT_ROLES`.
- my-dashboard (universal F-1 exempt landing) renders "New Addas Started" cards (adda code +
  name + date only — no money/quantities) to listing_team, the same render every previously
  certified role sees (worker/manager/accountant all 200 on this page) — consistent, BY DESIGN,
  no new row.

### Dated correction to OFF-A (appended per §11 — closed section not edited)

OFF-A's tracking line read "scan-status + export csv/xlsx/pdf **405** (POST-only)" for the pure
accountant. Re-verified live 2026-07-13: export-csv/xlsx/pdf GET as pure accountant = **403 ×3**
(CBV mixin precedes method check, code-cited above); scan-status = 405 (correct as written);
manager control = 405 on export-csv. **Refusal-class label error only** — the certified
substance (accountant blocked on all tracking exports, matrix ❌) is unchanged; OFF-A verdict
unaffected. Not §16.7 (no closed-cert contradiction on substance).

### Expectation-matrix accounting

Every probed URL for the listing lane + all four control identities reconciles to §6.2 (managed
exclusions 302 / unmanaged 403 / POST-only 405 / staff wall 302 / legacy twin 301-by-design).
**Zero unexplained outcomes; zero matrix mismatches; zero leaks; zero false blocks on the
designed surface.**

### Rollback / disclosed artifacts

Shell probes forced-rollback; browser rows created→verified→deleted same session. Post-run
recounts **byte-identical**: FP 1 (pk=1) · Cat 1 (pk=1) · rolls 32 · users 48 · SIR 21 ·
roles 5 · roll21 ''/200.00 · pk62 shape unchanged · anon homepage zero DEV content.
**Disclosed durable deltas:** `storefront_featuredproduct_id_seq` last_value **5** and
`storefront_category_id_seq` last_value **6** (Postgres sequences never roll back; OFF-B consumed
≤3 product + ≤2 category values across shell-rollback + browser-deleted rows; the remainder =
OWN-F storefront-cert consumption, same disclosed class) · probe media file
`storefront/products/dev_offb_probe.jpg` written then deleted (verified) · security.log
pw_login lines for pk=62 (shell + browser). Sessions signed out both lanes. No login lockout
(one careful attempt per lane). Money-Write STOP never triggered (storefront CMS rows carry no
money; no ledger/settlement table touched).

### Success criteria (§3) — OFF-B slice

4 (listing verdict: full CRUD lifecycle functional AS dev.listing, browser + shell, DEV-marked,
round-tripped; first comprehensive negative sweep = zero unexplained admissions) ✅ · 6 (every
403/302/301/404/405 classified with citation) ✅ · 7 (worker + manager negative controls held;
SA positive control) ✅. OFF-C/D criteria remain.

**Next: OFF-C — cross-role interaction audit (owner-gated).**

---

## OFF-C — Cross-role interaction audit (2026-07-13) ✅ — ISOLATION LATTICE PROVEN

**Verdict: the cross-role isolation lattice HOLDS. All three contract pairs proven in BOTH
directions on SHARED objects; six-identity leakage matrix (financial · storefront · production ·
tracking · administration) shows ZERO privilege leakage; the composite behaves as the EXACT union
{manager ∪ accountant} with zero unexpected inheritance. 0 confirmed bugs, 0 code changes,
battery NOT re-run (1530/1530 stands), 0 new INFO. 119 recorded shell probes + supplemental forks
+ 4-identity browser pass — ZERO 500s anywhere (MGT-B-1-class holds). Every shell probe
rollback-wrapped, post-rollback recount byte-identical; browser DEV rows torn down zero-residue.**

### Preconditions (§17.4, read-only) — zero material drift

HEAD `49404001` · porcelain **312** (== OFF-B) · :8003 serving. Identities exact (pk=61 pure acct ·
pk=76 composite mgr+[accountant] · pk=62 listing · pk=52 mgr · pk=46 worker · pk=1 SA; hashes
`check_password`=True ×5 before any login). Anchors EXACT: rolls 32 · roll-1 CR-000001
'Validation Supplier'/200.00/used · roll-history 40 · fin-history 0 · FP 1 / Cat 1 · users 48 ·
SIR 21 · 5 roles 0-perm · `view_all_payroll` (id=237) zero-holder · ledger 170. §2.2 gate facts
re-verified EXACT in code (role sets + shared financial predicate `permission_service.py:29-38,
96-103` · `user_role_codes` union `:65-88` · raw_materials mixins `mixins.py:15-43` ·
`ListingTeamMixin` hand-built pair `listing_views.py:24-27` · `_ManagementOnly` `views.py:60-62` ·
`can_view_worker` `payroll_service.py:154-166`). Settled-Adda probe target resolved:
**3-PATTI-009 (adda pk=23) / ADST-0001 finalized** (XFB-001-class; detail URL keys on
`reference` string — a garbage numeric reference 404s AFTER the `_ManagementOnly` gate for
management, 403s AT DISPATCH for specialists: fail-closed order proven incidentally).

### Method note

Shell: 61/76/62/52 = REAL password logins on CSRF-enforced test clients (every escalation POST
carried a valid token — refusals are authorization, not CSRF); SA pk=1 + worker pk=46 =
`force_login` controls (disclosed, OFF-B precedent). All writes in ONE outer atomic, forced
rollback, byte-identical recount. Browser: real logins per identity on :8003. A first shell run
crashed on a URL-reverse probe error (settlement-start needs `adda_pk`) INSIDE the atomic —
rolled back cleanly (recount proven), script corrected, full suite re-run.

### Pair 1 — accountant↔manager on a SHARED roll (DEV CR-000021 pk=50, in-txn)

Created via **composite service create-path** (financial stamps + CREATED history actor=76), then
composite **view-POST financial edit LANDED**: supplier 'DEV OFFC Shared'→'DEV OFFC Acct Edit',
cost 150.00→175.25, redirect to detail, **2 single-writer fin-history rows actor=76**. Against the
SAME roll, same transaction:
- **manager (pk=52):** detail 200 — ZERO financial content (leak=False) · edit form 200 —
  supplier/cost fields ABSENT · **CSRF-valid HACK POST** (supplier='HACK MGR', cost=999.99,
  width=42) → width saved, **financials INERT, fin-history still 2** (4-layer wall) · service
  direct → `PermissionDenied` **"Supplier and Cost Per KG require Accountant or Super Admin
  role"** verbatim.
- **worker (pk=46):** detail 200 no-leak · edit 403 · tracking roll-history **403**.
- **pure accountant (pk=61):** detail 403 · edit 403 · POST 403 DB-inert · roll-list 302 →
  my-dashboard · AJAX → **403 `{"detail": "You don't have the access to this page."}`** (D1
  pure-block re-proven on the very object class its capability targets).
- **listing (pk=62):** detail 403 · POST 403 DB-inert (cross-family).
- **tracking history, same roll:** SA **visible** · composite **visible** · manager 200 rows
  **hidden** · worker **403** — the six-identity single-object financial matrix, two-sided proof
  re-driven from both identities per contract.

### Pair 1b — mgmt money surfaces on the settled Adda (MGT-C regression, both directions)

Same objects (ADST-0001 · 3-PATTI-009): accountant **403 ×4** (settlement-detail · adda-detail ·
costing · payroll-overview) + listing **403 ×4** + worker settlement/costing/payroll 403
(adda-detail 200 = BY DESIGN: worker ∈ PRODUCTION_ROLES, worker-cert baseline — production page,
not a money surface); **manager/composite/SA settlement-detail 200 + payroll-overview 200**
(ownership held while specialists refused — the pair in both directions). Lever nuance captured:
accountant pay-basis POST → **403 at dispatch** (page gate); manager pay-basis POST → 302 +
flash **"Only a Super Admin can change a worker's pay basis."** (SA-lever refusal verbatim,
MGT-C/OWN-C regression). Specialist settlement-start POSTs → 403 ×2, **AddaSettlement count +
ledger count inert** (Money-Write STOP never triggered; no specialist path reached any money
writer).

### Pair 2 — listing↔manager on SHARED storefront rows (DEV Cat pk=7 + FP pk=6, in-txn)

Listing CREATE both (flashes verbatim: `Category "DEV OFFC Cat" created.` · `Product "DEV OFFC
Prod" created.`). Against the SAME pks: **manager ×8 = [302, 302, 403, 403, 403, 403, 403, 403]**
(lists managed-bounce; add/edit/delete mixin-403 — MGT-F regression re-proven on shared objects) +
AJAX 403 JSON + **CSRF POST edit → 403, name unchanged**. Worker GET+POST 403 inert · pure
accountant GET+POST 403 inert · **composite product_add 403 + POST edit 403 inert** (manager-lane,
NOT listing). Then **listing re-edit LANDED** (price 77.77→66.66, flash `updated.`) — the object
stays fully listing-operable after five hostile identities failed against it. Anon `/` reflected
both DEV rows in-txn. SA GET edit 200 (positive control).

### Pair 3 — listing↔owner shared-object collision + escalation census

**SA POST edit on listing's row LANDED** (price→55.55) → **listing re-read sees 55.55** → listing
re-edit LANDED (→44.44) → **SA rename of listing's category LANDED** ('DEV OFFC Cat v2') —
collision sanity both directions, last-write-wins, no error, no lock-out of either side. Listing
escalation census: user_add GET+POST **403** (users inert) · role_add GET+POST **403** (roles
inert) · role_list/sidebar-access/access-hub **302** (managed, roles=[]) · `/admin/` **302** staff
wall. **#5-class:** product delete-confirm **200** + category delete-confirm **200**; listing then
deleted the SA-edited rows (full lifecycle on a shared object) — in-txn counts back to 1/1.

### Composite = exact union (D1/D2 design proof)

`user_role_codes` = **{accountant, manager}** · fin view/edit True/True · management True ·
**0 Django user-perms / 0 groups**. Union-positive: manager-lane pages + financial fields (Pair 1).
No unexpected inheritance: bulk-add 403 GET + POST-inert (NOT SA) · user_add 403 · role_list 302 ·
`/admin/` 302 (staff wall) · product_add 403 (NOT listing). Middleware fork proven for composite
(role_list non-AJAX 302→my-dashboard / AJAX 403 JSON) and for all four specialist-session
identities this sub-phase (acct roll-list · mgr product_list · listing role_list · composite
role_list).

### Administration family — six identities, one instrument

role_list/sidebar-access/access-hub: **SA (200,200,200)**; manager, worker, accountant, listing,
composite ALL **(302,302,302)** (managed rules, roles=[]); role_add POST → **403 ×4**
(mgr/acct/listing/comp), Role count + role-perm M2M inert. Zero administration leakage.

### Prior-fix guard list (§14) re-verified live

**S2** signup GET/POST 302 + **no user created** (composite + accountant) · **S3** email GET/POST
302 + **emails unchanged** (pk=76, pk=61) · **BUG-E1** cloth-type-create: acct 403 / listing 403 /
worker 403 / manager 200 (owns), specialist POSTs inert · **#5-class** storefront delete-confirms
200 (shell + browser) · **MGT-B-1-class**: **zero 500s across all 119 recorded probes** + browser
pass · **MGT-F regression** manager ×8 (Pair 2) · MGT-C SA-lever refusal verbatim (Pair 1b).
MGT-F-1 machine-code guard: not re-driven — OFF-C touches no machine object (contract §14 scopes
it "only if OFF-C touches machines as a control"); OWN-F re-proof stands.

### Browser verification (:8003, four real logins, DEV rows torn down)

- **listing (pk=62):** sidebar = exactly 4 links · created **DEV OFFC Browser Cat (pk=8)** +
  **DEV OFFC Browser Prod (pk=7, FancySelect category pick)**, flashes verbatim; anon `/` showed
  3 DEV mentions.
- **manager (pk=52):** landed /production/ · shared product edit → branded **"Error 403 / You
  don't have access"** · product_list → bounce + flash "You don't have the access to this page." ·
  **shared DEV roll CR-000022 (pk=51, SA-service-created for this proof, disclosed):** detail =
  ZERO financial mentions; edit form `supplier`/`cost_per_kg` inputs **absent**, `weight_kg`
  present (live DOM check).
- **composite (pk=76):** roll-51 detail rendered Supplier 'DEV OFFC Browser Base' + ₹120.00 ·
  edit form prefilled both financial fields · **CSRF Save LANDED**: flash `Roll CR-000022
  updated.`, DB 142.42/'DEV-OFFC-BROWSER-EDIT', **2 fin-history rows actor=76** · storefront
  product_add → branded 403 (no listing inheritance, browser-proven).
- **pure accountant (pk=61):** shared roll-51 detail → branded 403 · ADST-0001 settlement →
  branded 403 · roll-list → managed bounce + flash.
- **listing re-login:** re-edit LANDED (price→33.33, `updated.`) after all cross-identity
  traffic → both delete-confirms rendered (#5 PASS) → both deleted (flashes verbatim) → anon `/`
  **zero DEV mentions**, '3 Patti' intact.
- **SA browser lane:** SKIPPED-DISCLOSED — no owner password supplied this session and no
  persisted owner session in the browser profile; SA collision-positive side fully proven in
  shell (force_login) per §6.3. Screenshots captured to the session scratchpad (ephemeral);
  the quoted page text above is the evidence of record.
- Browser incident disclosed: during the first product-create attempt a generic
  `form.submit()` fallback submitted the header Sign-Out form instead → session ended, product
  NOT created (verified FP count 1, no residue); re-login and exact-ref click landed it. Probe
  technique error, not a defect.

### Expectation-matrix accounting

Every probed URL × identity reconciles to §6.2 (managed 302+flash / unmanaged 403 / POST-only
untouched this sub-phase / staff wall 302 / SELF 200). **Zero unexplained outcomes · zero leaks ·
zero false blocks · zero 500s.** Two classifications recorded, neither a finding: worker
adda-detail 200 (PRODUCTION_ROLES membership, worker-cert baseline) · settlement-detail
garbage-reference 404-after-gate for management vs 403-at-dispatch for specialists (fail-closed
both ways).

### Rollback / disclosed artifacts

Shell: outer-atomic forced rollback; recount **byte-identical** (rolls 32 · roll-history 40 ·
fin-history 0 · FP 1 / Cat 1 · users 48 · SIR 21 · roles 5 / 0-perm · ADST 8 · ledger 170 ·
roll-1 anchor exact). Browser rows created→verified→deleted same session; DEV roll 51 + its 3
history rows (CREATED actor=1 + 2 fin rows actor=76) deleted, counts re-proven. **Disclosed
durable deltas:** `cloth_roll_seq` 19→**22** (CR-000020 crashed-run rollback · CR-000021 suite
rollback · CR-000022 browser roll deleted) · `storefront_featuredproduct_id_seq` →**7** ·
`storefront_category_id_seq` →**8** (in-txn + browser rows, all gone) · security.log password
logins (shell ×8 across two runs + browser ×6) · session rows. No login lockout (all attempts
succeeded first-try). Fin-history rows carried `change_type='weight_updated'` — the pre-existing
labeling note accepted at OWN-E/OFF-A, no new row.

### Success criteria (§3) — OFF-C slice

**5 (cross-role isolation): PROVEN** — financial fields invisible/unwritable to manager while
composite-positive on the SAME roll; storefront blocked for manager while listing-positive on the
SAME rows; no listing/accountant admission to any manager/SA surface; SA positive controls
throughout ✅ · 6 (every 403/302/404 classified, zero 500s) ✅ · 7 (worker + manager negative
controls held on every probed specialist surface) ✅. OFF-D criteria remain.

**Next: OFF-D — meta-audit + final phase verdict (owner-gated).**

---

## OFF-D — Meta-audit + FINAL PHASE VERDICT (2026-07-13) ✅ — PHASE 3 CERTIFIED

**Verdict: PHASE 3 — OFFICE / SUPPORT ROLE CERTIFICATION: CERTIFIED. Fresh instruments (not a
summary): 528-route census EXACT (zero route drift vs MGT-H/OWN-H) · 95-route parameterless
dynamic sweep across THREE specialist identities (pure accountant pk=61 · listing pk=62 ·
composite pk=76, real password logins) = ZERO 500s, ZERO leak-200s, ZERO false blocks · sidebars
match matrix (2/4/19 links) · /admin/ staff wall ×3 · AJAX JSON-403 fork ×3 verbatim · refusal
uniformity holds. Phase ledger: 0 confirmed bugs · 0 fixes · 0 regression pins · battery NOT
re-run anywhere in the phase (**1530/1530 = the Phase-3 final baseline**) · 2 new INFO across the
phase (#13, #14 — both re-verified today, stay INFO) · 0 new INFO at OFF-D. Every OFF-A/B/C
finding re-checked; all four dated notes resolved-with-citation; zero unresolved contradictions.**

### Preconditions (§17.4, read-only) — zero material drift

HEAD `49404001` · porcelain **312** (== OFF-B/OFF-C; unchanged after all OFF-D probes) · :8003
serving 200. Identities EXACT (pk=61 pure accountant · pk=76 mgr+[accountant], 0 user-perms/0
groups · pk=62 pure listing · controls 52/46/1), `check_password('Dev@12345')`=True ×3 verified
hash-only BEFORE any login. Anchors EXACT: roll-1 CR-000001 'Validation Supplier'/200.00/used ·
rolls 32 · roll-history 40 · fin-history 0 · FP 1 / Cat 1 · users 48 · SIR 21 · 5 roles 0-perm ·
`view_all_payroll` (id=237) zero-holder · ledger 170 · ADST 8. §2.2 gate facts re-verified EXACT
in code (role sets + shared financial predicate `permission_service.py:29-38,96-103` ·
`user_role_codes` union · raw_materials mixins `mixins.py:15-43` · `_ManagementOnly`
`views.py:60-62` · `can_view_worker` `payroll_service.py:154-166` · `ListingTeamMixin` hand-built
pair `listing_views.py:24-27`). Specialist sidebar rules == seeds (accountant in exactly rule
id=2; listing_team in ids 2/3/4).

### Fresh instrument 1 — 528-route census (MGT-H/OWN-H precedent, re-derived from the live URLConf)

Recursive root-URLConf walk = **528 routes EXACT — zero route drift across Phases 1→2→3.**
Gate-class breakdown, each class mapped to a specialist expectation:

| Class | Count | Accountant / listing expectation |
|---|---|---|
| django-admin (`admin/*`, staff wall) | 274 | ❌ 302→admin-login |
| `_ManagementOnly` (patterns_ai 51 · expense 11 · machines 5 · costing 1) | 68 | ❌ 403/302 |
| `ProductionRoleMixin` | 65 | ❌ 403/302 |
| LoginRequired-CBV (Administration double-gate · SELF `/expense/my/`+`workers/<pk>` · internal-check pages: blueprint, sidebar-access, stage/pattern libs, accounts CRUD) | 37 | ❌ except SELF ✅ |
| Auth-flow/public CBV (app login/OTP/logout · allauth account+social · styleguide login-tier) | 28 | ✅ own-auth flows |
| `ManagementRoleMixin` | 20 | ❌ |
| `SuperAdminOnlyMixin` | 12 | ❌ |
| `ListingTeamMixin` | 8 | acct ❌ / listing ✅ |
| `ManagerOrAdminMixin` (tracking exports) | 5 | ❌ (403 — the OFF-B-corrected class) |
| Function views (public `/` · my-dashboard exempt landing · 2 legacy redirects · google oauth ×3 · tracking scan/export fn ×3 · media ×2 owner-Option-1) | 11 | per class |

Arithmetic: 274+68+65+37+28+20+12+8+5+11 = **528** ✓. No unclassified route; no gate class
admits a specialist outside the §6.2 matrix.

### Fresh instrument 2 — parameterless dynamic sweep, THREE identities (95 routes)

95 parameterless non-admin routes (the ~95 of contract §7), swept as **pure accountant, pure
listing, AND composite** — real password logins on CSRF-enforced test clients (one attempt each,
all landed first-try), one outer `transaction.atomic` + forced rollback. Excluded + disclosed:
`/app/resend-otp/` (OTP-send adjacency, MGT-F disclosure precedent; its GET is
anti-enumeration-redirect per code, not probed). Anomaly rules per contract: specialist-200
outside matrix = leak · any 500 = anomaly · non-200 on designed surface = false block.

| Identity | 200 | 302 | 301 | 403 | 50x | Leaks | False blocks |
|---|---|---|---|---|---|---|---|
| pure accountant (61) | 20 | 29 | 2 | 43 | **0** | **0** | **0** |
| pure listing (62) | 24 | 27 | 2 | 41 | **0** | **0** | **0** |
| composite (76) | 57 | 18 | 2 | 17 | **0** | **0** | **0** |

- **Accountant 200s (all 20 accounted):** SELF (my-dashboard · `/expense/my/`) + public `/` +
  `/inventory/styleguide/` (login-tier design gallery, MGT-H-classified, role-blind, no data) +
  16 own-auth/allauth flow pages (matrix "own login/logout/password flows ✅"). **Zero 200s on
  any role surface.**
- **Listing 200s = accountant's 20 + EXACTLY the 4 designed storefront pages** (product/category
  list+add); its 302/403 columns shrink by exactly those 4 (2 managed→200, 2 unmanaged→200) —
  byte-consistent with the matrix delta.
- **Composite 403s (all 17 enumerated):** bulk-add · storefront add ×2 (manager ∉ STOREFRONT —
  MGT-F regression in the fresh instrument) · blueprint · production master-data SA-only set
  (patterns ×2 · stages/add · stage-categories ×2 · machine-types ×2 · products/add) · accounts
  CRUD ×4 · roles/add. **Zero manager-lane false blocks** (production/costing/RM/expense/
  tracking/machines/patterns all 200).
- **302s classified to a route:** managed-rule middleware bounces → my-dashboard (acct 20 ·
  listing 18 · composite 8) + designed auth redirects (authed login/root/verify-otp · POST-only
  logout GET→home · **S2 signup→/app/home/ and S3 email→/app/home/ re-proven in the fresh
  instrument for acct AND composite** · allauth password/set→change · social signup→login ·
  `/app/home/` role-landing fork: specialists→my-dashboard, composite→/production/).
- **301 ×2 per identity** = the two legacy-twin permanent redirects (BY DESIGN, OWN-H posture).

### Sidebar render + /admin/ wall + middleware fork (per identity, fresh)

- **Sidebar (rendered my-dashboard nav):** accountant = **2 links** (My Dashboard + My Earnings)
  · listing = **4 links** (+ storefront ×2) · composite = **19 links** = the Phase-1 manager
  baseline (RM ×6 · production ×4 · tracking · machines · patterns · expense ×4 · my-dashboard),
  **no Administration, no Storefront** — all three match the §6.2 matrix row exactly.
- **/admin/:** 302 → `/admin/login/?next=/admin/` for all three (staff wall; is_staff only at
  /admin/ = OWN-H gate-gap posture undisturbed).
- **AJAX fork ×3 verbatim:** acct+listing on roll-list, composite on roles →
  `{"detail": "You don't have the access to this page."}` 403 JSON; non-AJAX same URLs = 302 +
  flash (the sweep rows above).

### Cross-app refusal uniformity

One philosophy everywhere, fresh-proven: dispatch mixin → **403** (branded page, OFF-A/B/C
browser record) · managed rule → middleware **302 + flash** (non-AJAX) / **JSON 403** (AJAX) ·
POST-only → **405** on GET (scan-status class) / **403** where a CBV mixin precedes the method
check (export-trio class, OFF-B citation) · staff wall → **302** · fail-closed enumeration
(mixin before object lookup). **ZERO 500s across all 285 recorded probes** (95×3) — the
MGT-B-1 class holds phase-wide (OFF-C's 119 + OFF-D's 285, zero 500s total).

### Phase finding review (every OFF-A/B/C item re-checked)

- **Phase ledger: 0 confirmed bugs · 0 fixes · 0 pins · battery never re-run (no code changed
  in any sub-phase) — 1530/1530 stands as the Phase-3 final baseline.** Arithmetic: baseline
  entering OFF-0 = 1530 (OWN-H final; contract §13's "1526" = dated authoring note, recorded
  OFF-0) + 0 pins = 1530 ✓.
- **INFO #13** (dead `can_edit_financials` ctx flag) — re-verified today: computes :329, passes
  :404, zero template consumers. Stays INFO. **INFO #14** (`STOREFRONT_ROLES` dead lever) —
  re-verified today: defined + re-exported only, both gates still hand-build the pair; live
  equivalence re-proven by this sweep (listing 200 ×4 / acct+composite blocked on the same URLs).
  Stays INFO.
- **Backlog #1–#12 reviewed line-by-line:** none is a specialist-permission issue; #2/#5
  resolved-historical; #7/#8/#9/#10/#11/#12 INFO fix-when-touched, unchanged; #6 doc-drift (KOS
  lane). Nothing upgrades to a confirmed in-mandate defect.
- **Prior-fix guard list in the fresh instrument:** S2 + S3 bounces re-proven (sweep 302s,
  acct + composite; write-inertia halves proven OFF-A/B/C) · BUG-E1-class masters-create 403s
  present in all specialist sweeps · MGT-F manager-∉-storefront re-proven via composite ·
  MGT-B-1-class zero 500s · #5-class + MGT-F-1 stand on OFF-B/C + OWN-F evidence (not re-driven;
  no machine/delete-confirm object touched at OFF-D).
- **Contradiction audit across OFF-A/B/C: ZERO unresolved.** All four dated notes are
  resolved-with-citation and mutually consistent: export-trio 403-not-405 (OFF-B correction;
  confirmed by census class `ManagerOrAdminMixin`) · porcelain 311→312 (OFF-B note; 312 again
  today) · contract-§13 battery 1526 = authoring-time number (OFF-0 note) · sequence-disclosure
  chain continuous (cloth_roll_seq 12→16→19→22 · FP/Cat seqs 5/6→7/8; no gaps, no overlaps).
  Design Record D1–D4 applied uniformly in every section.

### Success criteria (§3) — final accounting

1 evidence sections OFF-0..OFF-D ✅ (this section closes it) · 2 D1–D4 answered before OFF-A ✅ ·
3 accountant verdict = BY-DESIGN-WITH-CITATION + composite functional-proven ✅ · 4 listing
verdict = CRUD functional + zero-admission census ✅ · 5 isolation lattice both directions on
shared objects ✅ · 6 every non-200 classified, every 200 reconciled (OFF-A/B/C + this fresh
sweep) ✅ · 7 worker+manager negative controls held throughout ✅ · 8 battery green at final
baseline 1530/1530 (re-run never triggered — no code change) ✅ · 9 OFF-D verdict from fresh
instruments ✅ · 10 status/backlog/memory synced at every close ✅.

### Rollback / disclosed artifacts

Sweep GET-only inside one forced-rollback atomic; post-rollback anchors **byte-identical**
(rolls 32 · roll-history 40 · fin-history 0 · FP 1 / Cat 1 · users 48 · SIR 21 · roles 5 ·
ledger 170 · ADST 8 · roll-1 exact); porcelain 312 unchanged; **no sequences consumed** (zero
inserts). Disclosed durable artifacts: security.log `pw_login` lines ×3 (pk 61/62/76) + session
rows rolled back with the atomic. No login lockout (3/3 first-try). Money-Write STOP never
triggered (GET-only sweep; no money writer reachable).

---

## FINAL PHASE 3 VERDICT (OFF-D close, 2026-07-13)

**PHASE 3 — OFFICE / SUPPORT ROLE CERTIFICATION: CERTIFIED.**

| Ledger item | Value |
|---|---|
| Confirmed bugs (whole phase) | **0** |
| Fixes applied | **0** |
| Regression pins added | **0** |
| Battery | **1530/1530** (final Phase-3 baseline; never re-run — no code changed in OFF-0..D) |
| New INFO this phase | **2** (backlog #13 OFF-A · #14 OFF-B; both re-verified at OFF-D, stay INFO) |
| INFO backlog residue (campaign-wide) | #6–#14 fix-when-touched (+ #1/#3/#4 infra) |
| Roles certified | `accountant` (add-on model: composite FUNCTIONAL + pure-blocked BY DESIGN, D4 door CLOSED) · `listing_team` (full CRUD functional + zero-admission census) · isolation lattice proven (OFF-C) · meta-audit clean (OFF-D) |

The role lattice is now complete: worker ✅ (V1.1) → manager ✅ (Phase 1) → owner/SA ✅ (Phase 2)
→ **accountant + listing_team + composite ✅ (Phase 3)**.

**Phase 3 CLOSED. Next: Phase 4 — FIX-0 intake (gated on owner F-D1..F-D3 per
PHASE_04_CONFIRMED_FINDINGS.md §17), owner-gated.**
