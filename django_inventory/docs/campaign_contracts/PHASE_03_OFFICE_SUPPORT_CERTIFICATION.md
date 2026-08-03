---
id: docs-campaign-contracts-phase-03-office-support-certification
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 3 Execution Contract — Office / Support Role Certification

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) — this contract only adds phase specifics and tightenings.
> Certifies the two remaining non-management operational roles: **`accountant`**
> (FINANCIAL_ROLES member) and **`listing_team`** (STOREFRONT_ROLES member). Completes the
> role lattice: worker (certified, deny-focused) → manager (certified, deny+function) → owner
> (Phase 2, allow-focused) → **specialist roles (this phase: smallest designed surfaces)**.
> Method precedent: [../MANAGEMENT_ROLE_CERTIFICATION.md](../MANAGEMENT_ROLE_CERTIFICATION.md)
> and [PHASE_02_OWNER_VISIBILITY.md](PHASE_02_OWNER_VISIBILITY.md). Evidence doc (created at
> OFF-0): `docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md`.
> Every §2.2 code fact below was derived from the repository 2026-07-12 (file:line cited);
> DB-resident facts are marked and re-verified at OFF-0. Where design INTENT is not decidable
> from the repository, the item is routed to the Design Record (Appendix A) — never invented.

## 1. Phase objective

Certify the `accountant` and `listing_team` roles across the entire ERP on three axes (§3-axis
definition, §6.1): each role is BLOCKED everywhere outside its designed surface, ALLOWED +
FUNCTIONAL on its designed surface, and every universal wall + prior-certification fix holds
with these roles driving. Novelty this phase must resolve: **the accountant role's designed
grant (financial fields on cloth rolls) is unreachable through the role's own page gates per
current code** (§2.2.1) — the certification delivers an evidence-based verdict on this
structural contradiction under the owner's ratified deployment model (Design Record D1),
instead of assuming either "bug" or "by design".

## 2. Scope

### 2.1 In / out

**In:** all 9 URL-bearing apps + django-admin `/admin/` + SidebarAccessMiddleware overlay,
probed AS `accountant` (pure and, if D1 ratifies, composite) and AS `listing_team`; cross-role
interaction audit (accountant↔manager, listing↔manager, listing↔owner); meta-audit with fresh
instruments. **Out:** any refactor; backlog #1/#3/#4 (infra/polish), #6 (doc drift — KOS
phase 7), #7/#8/#9 unless upgraded to a confirmed in-mandate defect; `/media/<path>` login-tier
(owner Option 1); OTP-send POSTs (real-SMTP risk, MGT-F disclosure precedent); KOS/docs work;
Phase-2 OWN-* work (paused separately); changing any Role/SidebarItemRule row except inside
rollback-wrapped probes.

### 2.2 Role-surface facts derived from code (2026-07-12 — re-verify §17.4)

#### 2.2.1 Accountant

| Fact | Evidence |
|---|---|
| Role sets | `FINANCIAL_ROLES = {super_admin, accountant}`; accountant ∉ MANAGEMENT_ROLES ∉ PRODUCTION_ROLES ∉ STOREFRONT_ROLES ∉ ADMIN_ROLES — `config/accounts/services/permission_service.py:29-38` |
| Complete designed grant | exactly TWO fields — `ClothRoll.supplier` + `ClothRoll.cost_per_kg`, view AND edit (one shared predicate; no view-only variant): `permission_service.py:96-103`. Nothing else anywhere keys off FINANCIAL_ROLES |
| The 4-layer financial wall (accountant = the positive side) | (1) form field population `raw_materials/forms/roll_forms.py:75,144` · (2) service check, `PermissionDenied` "Supplier and Cost Per KG require Accountant or Super Admin role" `raw_materials/services/roll_service.py:79,173` · (3) template conditionals `roll_views.py:60,206` → roll_list/roll_detail templates · (4) history-row filter ×4 sites (`roll_views.py:128`, `dashboard.py:82,181`, `inventory/views/tracking_history.py:14,68`) |
| **Reachability contradiction** | every raw_materials view dispatch-gates on ProductionRole/ManagementRole/SuperAdminOnly mixins (`raw_materials/views/mixins.py:15-43`; per-URL census §6.2) — accountant is in NONE of these sets ⇒ a PURE accountant 403s on every page hosting its own designed fields |
| Composition path | `user_role_codes` unions primary role + `extra_roles` M2M (`permission_service.py:65-88`; stacking example `accounts/models.py:195`) — a manager-primary + accountant-extra user passes BOTH the page gates and the financial gates |
| Expense | `_ManagementOnly` on 11 of 13 views (`expense/views.py:60-62` + dispatch list) — accountant 403; reachable: `/expense/my/` (LoginRequired, self-scoped `views.py:75-81`) + `/expense/workers/<own_pk>/` (self via `can_view_worker`, `payroll_service.py:154-166`). The ONLY accountant-capable widening: Django perm `expense.view_all_payroll` honored by `can_view_worker` — granted by NO seed (DB-resident, → D4) |
| Tracking | all 12 routes PRODUCTION/MANAGEMENT-gated (incl. explicit checks `tracking_dashboard.py:143-144`, `tracking_barcodes.py:177,204`) — accountant 403 everywhere; exports contain NO financial columns at all (`tracking_exports.py` — absence verified, not a leak) |
| Seeds | Role row seeded with **zero Django permissions** (`accounts/migrations/0016_seed_default_roles.py:20-21`, docstring: "no migration ever seeded role.permissions"; legacy `inventory/migrations/0013`) · seeded sidebar = ONE rule: `inventory:user_dashboard` shared with worker+listing_team (`accounts/migrations/0017_seed_sidebar_rules.py:15`) — NO raw_materials rule includes accountant |
| Test/fixture state | zero tests exercise the accountant positive surface (financial-wall tests use worker vs super_admin); one test pins an accountant REFUSAL (`production/tests/test_s4_grain.py:102-108`); NO fixture creates an accountant user; `dev.accountant@test.local` exists only in the live dev DB (security.log logins 2026-07-11) |
| Authoring observations (pre-registered; judge in OFF-A, fix only if confirmed in-mandate defect) | (a) dead context flag: `production/views/stage_views.py:324-329,404` computes `can_edit_financials`, consumed by no template (service layer still guards) · (b) view==edit predicate identical — a view-only accountant is inexpressible today |

#### 2.2.2 Listing team

| Fact | Evidence |
|---|---|
| Role sets | `STOREFRONT_ROLES = {super_admin, listing_team}` (`permission_service.py:31`); listing_team ∉ every other set |
| Designed surface | the 8 storefront management CBVs, ALL `LoginRequiredMixin + ListingTeamMixin` at dispatch (`storefront/views/listing_views.py:24-27`): FeaturedProduct list/add/edit/delete + Category list/add/edit/delete; plus sidebar section Storefront (`permission_service.py:316-323`) |
| Service layer | NO gated service: writes via ModelForms; `image_service.process_and_attach` = pure image processing, no permission re-check; deletes = plain DeleteView single-row deletes (ListingService removed as pass-through, `listing_views.py:103-110` comment); public homepage anonymous read-only (ADR-0008); storefront media public (pinned `core/tests.py:362`) |
| Seeds | Role row, zero Django permissions (`accounts/migrations/0016`); sidebar rules ×3: user_dashboard + storefront:product_list + storefront:category_list (`accounts/0017:15-17`) |
| Certification state | worker-cert Phase G proved worker+manager blocked ×8 and listing_team **200-GET ×8** — functional WRITE certification as listing_team has never been done; **zero listing_team tests exist in code**; a listing-team NEGATIVE sweep across the other 8 apps has never been run |
| Authoring observation (pre-registered; judge in OFF-B) | `ListingTeamMixin` hand-builds `{ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM}` instead of importing `STOREFRONT_ROLES` (equivalent membership today; divergence risk if the constant ever changes) |

#### 2.2.3 Middleware overlay (both roles)

`SidebarAccessMiddleware` (`inventory/middleware.py:50-85`): managed url_name + no role/skill
overlap → AJAX (`X-Requested-With`) = JSON 403 `{"detail": "You don't have the access to this
page."}`; non-AJAX = same flash + 302 to accessible same-host referer else
`inventory:my_dashboard`; unmanaged url_names pass through to the view's own mixin (defense in
depth); exempt landings: my_dashboard + 2 legacy twins. DB rules can WIDEN menu/URL passage for
managed items but the view mixin still decides (double gate) — a widened rule with a blocking
mixin yields "menu visible, page 403": that combination is a FINDING if observed.

### 2.3 DB-resident facts (code cannot decide — verified at OFF-0, never assumed)

Live SidebarItemRule rows (21 at MGT-H; runtime edits possible) · accountant/listing Role rows'
runtime-granted Django permissions (seeds grant none; `expense.view_all_payroll` is the
sensitive one → D4) · existence/purity/credentials of `dev.accountant@test.local` and
`dev.listing` · any user stacking these roles via `extra_roles`.

## 3. Success criteria

Phase 3 is DONE when ALL hold:
1. OFF-0..OFF-D each closed with an appended evidence section in
   OFFICE_SUPPORT_ROLE_CERTIFICATION.md meeting §5.
2. Design Record D1–D4 answered by the owner BEFORE OFF-A probing begins.
3. **Accountant verdict delivered:** under the D1-ratified deployment model, the financial-field
   grant is proven FUNCTIONAL end-to-end for the ratified identity shape (write lands in DB +
   history rows, then rolled back/disclosed), AND the pure-accountant reality (whatever D1 makes
   it) is proven and classified — the §2.2.1 reachability contradiction ends as
   CONFIRMED-BUG-FIXED, BY-DESIGN-with-citation, or OWNER-DEFERRED-with-backlog-row. Silence is
   not an outcome.
4. **Listing verdict delivered:** full storefront CRUD lifecycle proven functional AS
   `dev.listing` (browser + shell, DEV-marked data, round-tripped), and the first comprehensive
   listing-team negative sweep across the other 8 apps + /admin/ shows zero unexplained
   admissions.
5. Cross-role isolation (OFF-C) proven: financial fields invisible/unwritable to manager while
   accountant-positive on the SAME objects; storefront blocked for manager while
   listing-positive on the SAME objects; no listing/accountant admission to any manager/SA
   surface; SA positive controls throughout.
6. Every 403/302/405/500 observed for these roles is classified BY DESIGN (with citation) or
   FIXED with pin + battery; every 200 outside the expectation matrix is treated as a leak
   finding.
7. Negative controls hold (worker + manager stay blocked on the probed specialist surfaces —
   regression guard on Phases W/1).
8. Battery green at final baseline (1526 + any new pins), sequential fresh-DB, re-run only if
   code changed.
9. OFF-D meta-audit delivers the phase verdict from fresh instruments, not a summary.
10. Status file + backlog + memory synced at every sub-phase close.

## 4. Rules of engagement (deltas beyond U1–U14)

- Fix mandate per sub-phase = ONLY bugs confirmed inside that sub-phase's scope (MGT-E
  precedent). The §2.2 authoring observations are INPUTS to judge, not pre-confirmed bugs.
- **No probing before ratification:** OFF-A does not start until D1–D4 carry owner answers.
- Role/SidebarItemRule/permission rows are never durably mutated to "make a probe work". If a
  probe requires a granted perm or widened rule (e.g. D4 exploration), it runs rollback-wrapped
  in shell and the live DB ends byte-identical.
- Identity handling: `dev.accountant@test.local` is DB-resident with unknown provenance —
  OFF-0 verifies it read-only; if unusable (wrong role shape / unknown password), create fresh
  DEV-marked identities instead (owner test-data authorization 2026-07-04); NEVER touch a
  non-DEV user. Composite identity (if D1 ratifies stacking) is created DEV-marked at OFF-0.
- Login attempts are rate-limited per IP+email (~15–30 min lockout) — one careful attempt per
  identity; a lockout is stop condition §16.6.
- Financial-field probes write to `ClothRoll` + append-only `ClothRollHistory` → shell probes
  rollback-wrapped; browser financial edits only on a DEV-marked roll, with the created history
  rows explicitly disclosed (U13; MGT-D EXP-2026-006 precedent).
- Storefront objects are live-site content (public homepage!) — browser CRUD probes use
  DEV-marked FeaturedProduct/Category rows created for the purpose and deleted in the same
  session; never edit pre-existing live rows.

## 5. Evidence standard

Unchanged from Phase 1/2 (charter §"Evidence standard" lineage): per-URL status matrix, shell
(Django test client) AND browser, PER IDENTITY · exact flash/error/JSON quotes · CSRF-valid
POSTs with DB re-check · rollback-wrapped shell writes with byte-identical post-rollback counts
· SA + manager + worker controls on every probed surface. Phase-3 additions:
- **Two-sided financial-leak proof (injected-row pattern, MGT-D precedent):** the same roll
  probed as accountant (sees supplier/cost + history rows, can write) AND as manager/worker
  (sees neither, write refused with the exact service message) in the same evidence block.
- **Expectation-matrix accounting:** every probed URL's observed outcome is reconciled against
  the §6.2 matrix; any mismatch is a finding (leak or false block) — no silent divergence.
- **Middleware-fork proof:** for at least one managed-blocked URL per identity: non-AJAX
  (flash + 302 target recorded) AND AJAX variant (JSON 403 body quoted).
- Sub-agent findings supplemental (U7); money-adjacent probes (payroll perm door D4) and all
  verdicts main-thread.

## 6. Methodology

### 6.1 Certification philosophy + the three axes (this phase's inversion)

Worker cert asked "is the worker blocked?"; management cert asked "blocked + does the job
work?"; owner cert asks "zero false blocks". The specialist roles have the SMALLEST designed
surfaces in the system — so Phase 3 is dominated by negative space, with a small functional
core that has NEVER been exercised:
1. **BLOCKED (hostile-negative):** each role must be refused on every surface outside its
   designed set — dispatch mixins, middleware overlay, service re-gates, CSRF-valid escalation
   POSTs, hand-crafted POSTs, AJAX forks, enumeration/garbage-pk fail-closed behavior.
2. **ALLOWED + FUNCTIONAL (functional-positive):** the designed surface actually works
   end-to-end with the specialist driving — listing: full storefront CRUD lifecycle;
   accountant: financial-field read AND write landing in DB + history (under the D1-ratified
   identity shape). 200-GET is not functional proof; the write must LAND (then roll back or be
   disclosed).
3. **UNIVERSAL WALLS + prior fixes:** S2 signup-closed and S3 email-shadow hold for these
   identities; POST-only endpoints 405 on GET; SA-only levers refuse them; the prior-fix guard
   list (§14) still behaves with these roles driving where their surfaces touch it.

Per sub-phase, the locked 10-step loop (Phase-1/2 method, unchanged): read app docs + urls.py →
gate-map audit per URL (which check refuses/admits THIS role — mixin, DB rule, service,
template) → shell probes (GET matrix, then rollback-wrapped writes) → browser on :8003 (real
login, real forms, CSRF-valid POSTs, DEV-marked data) → fix ONLY confirmed bugs (smallest
change; U14 stop) → pins only for fixes → battery per U5 only if code changed → docs-sync →
status file + memory → STOP.

### 6.2 Expectation matrix (code-derived; the certified baseline unless a Design Record answer amends it)

Legend: ✅ = allowed+functional expected · ❌403 = view-mixin refusal · ❌302/JSON = middleware
refusal expected where a managed rule excludes the role (exact split verified at OFF-0 against
live rules) · SELF = self-scoped only. "Composite" column applies ONLY if D1 ratifies stacking.

| Surface | Pure accountant | Composite (mgr+acct extra) | listing_team |
|---|---|---|---|
| Main: my_dashboard, my-earnings | ✅ (SELF, exempt landings) | ✅ | ✅ (SELF) |
| Production (all: dashboards, addas, consoles, products, patterns, stages, machines, patterns_ai) | ❌ | manager-lane expectations (Phase-1 matrix) | ❌ |
| Raw materials: dashboards, roll list/detail, masters lists | ❌403 (ProductionRoleMixin) — the contradiction surface | ✅ pages + ✅ financial columns/history/write | ❌ |
| Raw materials: roll edit/damage/assign, masters CRUD | ❌403 (ManagementRoleMixin) | ✅ + financial fields present in forms | ❌ |
| Raw materials: bulk-add | ❌403 (SuperAdminOnly) | ❌403 (SuperAdminOnly — composite is NOT SA) | ❌ |
| Financial FIELDS (supplier/cost_per_kg) | (unreachable via UI; service-level grant exists) | ✅ view+edit, service accepts, history rows written | ❌ stripped/refused |
| Expense: payroll/settlements/advances/factory-expenses/profile | ❌403 (_ManagementOnly) | manager-lane (incl. 4 SA-only levers still refused in services) | ❌ |
| Expense: /my/, /workers/<own_pk>/ | ✅ SELF (empty) | ✅ | ✅ SELF |
| Expense: /workers/<other_pk>/ | ❌ (can_view_worker) unless D4 grants view_all_payroll | ✅ (management) | ❌ |
| Tracking: all 12 routes (dashboard, barcodes, scan, history, exports) | ❌ (PRODUCTION/MANAGEMENT gates) | manager-lane ✅ | ❌ |
| Storefront: 8 management CBVs | ❌403 (ListingTeamMixin) | ❌403 (manager is NOT in STOREFRONT_ROLES — MGT-F regression) | ✅ full CRUD |
| Storefront: public homepage `/` | ✅ (anonymous surface) | ✅ | ✅ |
| Accounts: own login/logout/password flows | ✅ | ✅ | ✅ |
| Accounts: users/skills/user-types CRUD | ❌ (SA-only) | ❌ | ❌ |
| Accounts: S2 signup, S3 email management | ❌ closed walls hold | ❌ | ❌ |
| Inventory Administration (roles, sidebar-access, access hub) | ❌ (SA-only + double gate) | ❌ | ❌ |
| machines, patterns_ai | ❌ (management-gated) | manager-lane ✅ | ❌ |
| `/admin/` | ❌ staff wall (302→admin login) | ❌ | ❌ |
| Sidebar render | Main only (seeded); anything more = finding vs live rules | manager sidebar (Phase-1 baseline 19 links) | Main + Storefront (3 seeded rules) |

### 6.3 Verification philosophies

- **Shell (first, exhaustive):** Django test client per identity — full GET matrices, CSRF-valid
  escalation POSTs, hand-crafted parameter abuse, enumeration/garbage pks; ALL writes inside
  `transaction.atomic` + forced rollback with byte-identical recounts; both middleware forks
  exercised by header toggling.
- **Browser (second, representative + UX-truth):** real logins on :8003 per identity —
  rendered sidebar vs matrix, absence of financial columns/buttons where stripped, real form
  submissions on DEV-marked data, cross-checking at least one shell-observed refusal and one
  functional write per identity. Browser proves what the USER experiences; shell proves the
  gate lattice. A claim needs the pair.

## 7. Sub-phase breakdown

Status lives in the status file + evidence-doc table; this is the procedure map. Probe-target
counts are point-in-time (Phase-1/2 anchors) — re-verify at session start, note drift.

| # | Scope | Probe targets | Key proofs |
|---|---|---|---|
| OFF-0 | Charter: create evidence doc skeleton · owner answers D1–D4 → Design Record · identity census read-only (dev.accountant@test.local shape/credentials; dev.listing purity; create DEV composite identity if D1 says so; SA/mgr/worker controls exist) · live SidebarItemRule census vs seeds (21 rules at MGT-H) · role-perm census (accountant/listing Django perms — expect zero; view_all_payroll state → D4 baseline) · git/battery baseline check | live DB read-only | charter + filled Design Record + verified identity table + rule/perm census; NO probing |
| OFF-A | Accountant certification: raw_materials full matrix (pure + composite per D1) · financial-field functional write (create-path AND update-path: form field presence, service acceptance, DB value change, history rows) + two-sided leak proof on the same roll (mgr/worker negative) · expense matrix incl. SELF pages + D4 door state · tracking matrix ×12 · production/machines/patterns_ai/storefront/accounts/admin negative sweeps · S2/S3 walls · middleware forks · judge §2.2.1 contradiction + pre-registered observations (a)(b) | roll pk=1 CR-000001 (supplier="Validation Supplier", cost=200 at Phase-1 close) or a DEV roll; roll count baseline (32); dev worker pk=25 for other-pk probes | the accountant VERDICT (§3.3) with citations; financial write landed + rolled back/disclosed |
| OFF-B | Listing certification: storefront functional CRUD lifecycle as dev.listing (product add→edit→delete round-trip + category add→edit→delete, browser + shell, DEV-marked; image upload through image_service; delete-confirm pages render — #5-class regression watch) · public homepage reflects listing edits (anon check) · negative sweep: production/raw_materials/tracking/expense/machines/patterns_ai/accounts/admin + SA-only surfaces (first-ever comprehensive listing negative census) · S2/S3 · middleware forks · judge mixin-duplication observation | FeaturedProduct (1 at Phase-1 close) + Category (1) as anchors — CREATE new DEV rows, don't edit live ones | listing functional-positive proof + zero-admission negative census |
| OFF-C | Cross-role interaction audit: accountant↔manager (same-roll two-sided financial proof re-driven from both identities; accountant blocked on mgmt money surfaces while manager owns them — MGT-C regression; both blocked from each other's exclusive lanes) · listing↔manager (same-object storefront proof: listing edits, manager 403 ×8 re-proven — MGT-F regression; listing blocked on manager lanes) · listing↔owner (SA edits the same DEV storefront rows — shared-surface collision sanity; SA positive controls; no listing escalation to SA-only accounts/admin surfaces) | DEV rows created in OFF-A/B; XFB-001-class settled Adda for accountant money-negative spot | isolation lattice: every pair proven in BOTH directions on SHARED objects |
| OFF-D | Meta-audit + close: route census re-run (528-route instrument, MGT-H precedent) classified for accountant + listing · parameterless dual-identity dynamic sweep (~95 routes) with anomaly rules: specialist-200 on any surface outside matrix = leak anomaly; specialist-500 anywhere = anomaly; false-403 on designed surface = anomaly · rendered sidebar per identity vs matrix · /admin/ wall · cross-app refusal uniformity (mixin 403 vs middleware 302/flash vs AJAX JSON) · backlog review · FINAL VERDICT | whole root URLConf | CERTIFIED / CERTIFIED-WITH-FINDINGS from fresh instruments |

## 8. Deliverables

- `docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md` (NEW at OFF-0): charter (3-axis definition,
  identities, expectation matrix copy, evidence standard) + 5 appended evidence sections.
- Filled Design Record (Appendix A) — D1–D4 verbatim.
- The accountant structural verdict + the listing functional-positive record.
- Backlog rows for any new INFO findings (U12).
- If fixes: pins in the owning app's existing certification test module (create
  `test_office_role_certification.py` sibling only if no suitable module exists) + battery
  arithmetic.
- Status file + memory updates per sub-phase.

## 9. Files expected to change

**Always (docs):** `docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DEPLOYMENT_BACKLOG.md` (only if new INFO) ·
this file (Design Record + corrections only) · memory files (if agent has memory).
**Only if a bug is CONFIRMED in-scope (code):** the single smallest app file(s) owning the
defect (raw_materials / storefront / expense / inventory views·services·forms·templates) ·
that app's certification test module · the app's GUIDE/README (U6) ·
`docs/DOCUMENTATION_INDEX.md` if a new file is created.
**DEV data (execution, disclosed):** DEV-marked identities (composite user if D1), DEV
FeaturedProduct/Category/roll rows — created and round-tripped/disclosed per §4.

## 10. Files that must never change (touching one = STOP + report)

- Migrations (existing or new — new requires owner pre-approval, U14) — including the Role /
  SidebarItemRule seed migrations §2.2 cites.
- `config/config/settings/*` (U10). A confirmed bug whose fix lives in settings = STOP.
- Money single-writer services beyond a confirmed in-scope defect: `ledger_service`,
  `settlement_service`, `adda_settlement_service`, `payroll_service`, `fnf_service`,
  `expense_service`, `advance_service` (U8 review on any touch).
- `permission_service.py` role-set constants — changing FINANCIAL/STOREFRONT/MANAGEMENT/
  PRODUCTION membership is an RBAC architecture change: owner decision, never a "fix".
- Frozen-foundation modules (U9); `docs/adr/`, PDD, ARCHITECTURE_V2, freeze packages.
- Non-DEV user rows (incl. pk=1) — read-only; `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) append the evidence section (never edit closed
sections; corrections appended, dated); (b) status-file Phase-3 sub-phase table + dashboard
(battery, docs-sync, memory-sync, carry-overs) + "Next action"; (c) backlog row per new INFO
(U12); (d) if code changed: app GUIDE/README + CHANGE_IMPACT_MATRIX-mapped docs (U6); (e) new
file ⇒ DOCUMENTATION_INDEX row (the evidence doc gets its row at OFF-0).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-3
bullet) + MEMORY.md index line at each sub-phase close. Agents without memory: skip — §11's
on-disk records are the complete binding record; nothing may exist ONLY in memory.

## 13. Battery policy

Sequential fresh-DB canonical (U5). Baseline entering OFF-0: **1526/1526** (9-app 998 +
patterns_ai 528). Expected count after any fix = previous baseline + new pins; record the
arithmetic (MGT precedent 1519→1522→1524→1526). Re-run ONLY when code changed; a 0-bug
sub-phase states "battery NOT re-run (baseline stands)". Never `--parallel`, never `--keepdb`
across suites (backlog #4 + MGT-F addendum).

## 14. Regression policy

- Every specialist probe pairs with negative controls: worker AND manager must stay blocked on
  specialist-exclusive surfaces; SA positive control on every surface (no false lock-out).
- Prior-fix guard list (re-proven where these roles' surfaces touch it): BUG-E1 (master CRUD =
  ManagementRole — accountant/listing must also be refused) · #5 (delete-confirm renders — the
  storefront DeleteView confirm pages get the same watch in OFF-B) · S2 (signup closed for
  these identities) · S3 (email management neutralized) · MGT-F-1 (machine-code guard — only if
  OFF-C touches machines as a control) · MGT-B-1-class (refusals must flash, never 500).
- MGT-C/D/E financial+storefront negative results for manager are the FIXED baseline OFF-C
  re-proves from the specialist side — a divergence reopens nothing unilaterally (§16.7).
- Pins only for NEW fixes (U4).

## 15. Rollback policy

- Shell writes: one `transaction.atomic` block per probe cluster; force rollback; verify
  post-rollback counts byte-identical (roll count, ClothRollHistory count, FeaturedProduct/
  Category counts, User count, SidebarItemRule count, Role-perm M2M count).
- Browser writes: DEV-marked rows only; create→verify→delete round-trips; append-only artifacts
  that cannot be unrolled (ClothRollHistory rows from a browser financial edit, security-log
  lines) are DISCLOSED in the evidence section with identifiers (U13).
- Identity artifacts: DEV identities created for this phase are retained + documented in the
  evidence doc (cast-list precedent), never silently deleted.
- State leak → record exactly what leaked, restore via the designed reverse path if one exists,
  else disclose; NEVER raw-SQL delete.
- Session crash mid-probe → next session re-baselines counts FIRST (worker-cert Phase-B lesson:
  capture evidence into the doc incrementally, not at session end).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. D1–D4 unanswered/ambiguous at OFF-A start (probing without a ratified deployment model
   would certify against an invented expectation).
3. Money-write anomaly (U8) — e.g. any accountant-driven path that creates/mutates a ledger,
   settlement, or FactoryExpense row.
4. Fix requires a migration (U14), a settings change, or a `permission_service` role-set
   change (§10) — owner decision, not a fix.
5. A probe would durably mutate a Role/SidebarItemRule/permission row or any non-DEV user.
6. Login rate-limit lockout of any probe identity.
7. Evidence contradicts a CLOSED certification (worker/management regression) — report; never
   reopen closed phases unilaterally.
8. Probe leaks non-DEV data or un-rollbackable state beyond the disclosed-artifact class.
9. Battery goes red on anything other than the just-added pins' target behavior.
10. §2.2 facts materially drifted at re-verification (gate mixins changed, role sets changed,
    seed state differs) — re-derive before certifying against a stale matrix.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → confirm Phase 3 active + which OFF-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → this contract FULLY,
   including the §6.2 matrix and Appendix A.
3. If OFF-0 is closed: read `docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md` charter + all closed
   evidence sections (carry-forward findings, disclosed artifacts, battery arithmetic,
   identity cast list).
4. Verify preconditions read-only: git HEAD (was `49404001` + working tree at authoring);
   battery baseline from the status dashboard; probe identities exist + active; §2.2 gate facts
   still true (spot-check the mixin files cited); §7 probe targets in expected state — re-anchor
   and note drift in evidence if moved.
5. Obtain passwords: manager/worker/listing = Dev@12345 pattern per framework README env facts
   (verify, don't assume); accountant + composite per the OFF-0 identity table; owner (SA
   control) supplied by owner at session start.
6. Execute exactly ONE sub-phase per §6. STOP per §16.
7. Anything internally inconsistent across status file / this contract / evidence doc / Design
   Record → report before probing (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (OFF-0)

| # | Item | What the repository shows (facts, §2.2) | Decision needed | Owner answer |
|---|---|---|---|---|
| D1 | **Accountant deployment model** | grant = 2 roll fields, but every hosting page dispatch-403s a pure accountant; composition via `extra_roles` passes both gates; seeds give Main-only sidebar | Is `accountant` (a) an ADD-ON role stacked onto manager/SA via extra_roles, (b) a standalone role whose page access is INTENDED and currently missing (⇒ confirmed design gap → owner decides fix venue: this phase vs backlog vs PDD change), or (c) intentionally dormant until a future finance surface? Certification target per answer: (a) certify composite functional + pure-blocked; (b) report gap, owner picks venue — this contract does NOT authorize new page gates without an explicit order; (c) certify pure-blocked as BY DESIGN | **(a) ADD-ON role only** — intended to be stacked via `extra_roles` on top of manager or super admin where financial capabilities are required; "Do not redesign the RBAC architecture." ⇒ certify composite functional + pure-blocked BY DESIGN; §2.2.1 contradiction resolved BY-DESIGN-with-citation (this record) |
| D2 | Composite probe identity | no fixture creates one; extra_roles path exists in code | If D1=(a): approve creation of DEV-marked `dev.acct.mgr@test.local` (manager primary + accountant extra, Dev@12345)? | **YES** — "Retain it permanently as a documented DEV identity." ⇒ created at OFF-0: pk=76, shape verified (role codes {accountant, manager}; financial view/edit True; management gate True; password check True) |
| D3 | `dev.accountant@test.local` | exists only in live dev DB (security.log 2026-07-11); no fixture; credentials unrecorded | Reuse it (owner supplies/along-resets password on this DEV account) or retire-and-recreate `dev.acct@test.local` fresh? | **REUSE — do NOT recreate**; reset password to Dev@12345 if required ⇒ reset performed at OFF-0 (credentials were unrecorded); pk=61 purity verified (active, role=accountant, extra=[], no flags) |
| D4 | `expense.view_all_payroll` | honored by `can_view_worker` (payroll_service.py:154-166); granted by no seed; live grant state = DB-resident | Is the accountant INTENDED to hold this perm (payroll read door)? Certification proves the ratified state; if intended-yes and absent, granting it is an owner action recorded here, not an agent fix | **INTENDED = NO** — "The current zero-holder state is the intended design." OFF-0 census: Permission id=237 held by no role / no user_permissions / no group ⇒ OFF-A certifies the door CLOSED |

Date · answered by: **2026-07-13 · owner (Umesh), answers recorded verbatim at OFF-0; evidence + census in [../OFFICE_SUPPORT_ROLE_CERTIFICATION.md](../OFFICE_SUPPORT_ROLE_CERTIFICATION.md) §OFF-0**

## Dated amendments

_(none)_

# Evidence note

Evidence sections live in `docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md` (created at OFF-0), not
in this contract — mirror of the Phase-1/2 pattern (contract = procedure, evidence doc = what
happened).
