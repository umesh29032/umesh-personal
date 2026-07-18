---
id: owner-visibility-certification
type: evidence-cert
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Owner Visibility Certification — Campaign Phase 2

> Pre-deployment campaign, opened 2026-07-12 (OWN-0). Sibling of
> [WORKER_ROLE_CERTIFICATION.md](WORKER_ROLE_CERTIFICATION.md) (CLOSED, 9 apps + meta-audit) and
> [MANAGEMENT_ROLE_CERTIFICATION.md](MANAGEMENT_ROLE_CERTIFICATION.md) (CLOSED, MGT-0..H, CERTIFIED).
> Campaign resume anchor: [DEPLOYMENT_CAMPAIGN_STATUS.md](DEPLOYMENT_CAMPAIGN_STATUS.md).
> Engine FROZEN — fix ONLY confirmed bugs, pins only for fixes, battery rerun only on code change
> (baseline **1526/1526**, sequential fresh-DB canonical).
> **Execution contract (2026-07-12, contract-first mode): [campaign_contracts/PHASE_02_OWNER_VISIBILITY.md](campaign_contracts/PHASE_02_OWNER_VISIBILITY.md)
> — OWN-A..H execution is PAUSED until the owner orders it against that contract.**

## What this certifies (three questions, per app)

The `super_admin` / Owner role. Worker cert asked "is the worker blocked?"; management cert asked
"blocked + does the job work?". Owner certification INVERTS the emphasis — the owner is expected to
reach everything, so the certification hunts for the opposite failure classes:

1. **ALLOWED everywhere expected — zero false blocks.** No 403, no 302-to-dashboard, no middleware
   bounce, no perm-seam accident on ANY surface the owner is designed to reach (which is every
   project surface except the enumerated universal walls, axis 3). Special attention to gates that
   check `user_has_role` vs `is_superuser` vs Django perms vs `is_staff` — a manager-only or
   shared-management assumption that accidentally excludes the SA role is a Phase-2 bug even
   if no manager or worker ever hits it.
2. **FUNCTIONAL — every owner-only operation actually WORKS end-to-end.** Prior certifications
   only proved these return 200 as a positive control; nobody has ever certified the WRITES:
   product CRUD + flow editor · pattern/stage/category/machine-type library CRUD ·
   `rerate_stage_role` · roles editor + sidebar-access editor + access hub · Team Members /
   User Skills / User Types CRUD · roll bulk-add with financials · financial fields
   (supplier/cost_per_kg) view AND edit · the 4 SA-only money levers (pay-basis · FnF ·
   reconciliation override · expense void) · storefront editor (SA ∈ STOREFRONT_ROLES) ·
   blueprint · django-admin. Hidden owner-only 500s live here — the MGT-B-1/#5 bug class
   (crash inside a surface only ONE role ever exercises).
3. **Universal walls hold even for the owner** — designed everyone-blocks stay closed: S2 signup
   closed · S3 email management neutralized · own-task surfaces behave sanely for a non-assigned
   SA · POST-only endpoints still 405 on GET. Plus: every Worker/Management-cert fix (BUG-1/2/3,
   BUG-E1, S2, S3, MGT-B-1, #5, MGT-F-1) must remain functional WITH the owner driving.

## Certification identity

- **`umesh29mar@gmail.com` / pk=1 — THE owner account**, verified read-only 2026-07-12 (OWN-0):
  active, `primary_role=Super Admin`, `extra_roles=[]`, `is_superuser=True`, `is_staff=True`,
  password verified. Login via `/app/login/password/` (bypasses OTP; rate-limited per IP+email —
  type carefully).
- **Flag-alignment census (OWN-0):** exactly ONE account in the DB carries any owner-class flag,
  and all three align on it (role=Super Admin ∧ is_superuser ∧ is_staff). The
  "SA-role-without-is_superuser" divergence class is EMPTY in data — but gates are still audited
  at code level per sub-phase (a future second admin must not fall into a gap between
  `user_has_role({ROLE_SUPER_ADMIN})`, `is_superuser` bypasses, and the `/admin/` staff wall).
- Cross-check identities: manager `dev.mgr@test.local` (negative control — SA-only writes must
  stay manager-blocked, regression on Phase-1) · worker `dev.ow.a@test.local` (regression spots) ·
  listing_team `dev.listing` (storefront comparison).

## Method (locked, per sub-phase — the 10 steps, unchanged from Phase 1)

1. Read app docs + urls.py. 2. Gate-map audit per URL (mixin → SidebarItemRule → service gate →
template ctx), owner-angle: which check admits SA, and could it ever not? 3. Shell probe as owner
(test client; POSTs rollback-wrapped; manager/worker negative cross-checks). 4. Browser as
`umesh29mar` on :8003 (real navigation + CSRF-valid POSTs; DEV-marked data only; destructive
writes rollback-wrapped in shell, browser-driven only where reversible or DEV-marked).
5. Fix ONLY confirmed bugs. 6. Regression pins ONLY for fixes. 7. Sequential fresh-DB battery ONLY
if code changed (baseline **1526/1526**). 8. Docs-sync (this file's section + app GUIDE/README if
code touched). 9. Update DEPLOYMENT_CAMPAIGN_STATUS.md + memory. 10. STOP — next sub-phase is
owner-gated.

## Evidence standard (artifact-backed, unchanged)

Every verdict carries its probe: per-URL status matrix (shell + browser) · exact flash/error
quotes · CSRF-valid POST with DB re-check · rollback-wrapped shell writes · negative controls
(manager AND worker must stay blocked on SA-only surfaces — Phase-1 regression guard).
"Looks correct in code" is never a verdict. Sub-agent findings are supplemental — no surface is
marked clean on sub-agent silence (audit-honesty rule); finder failures are recorded.
Money probes: golden invariant = ledger row-count/Σ must survive every rollback-wrapped probe
(Money-Write STOP rule applies — a new money-write path outside approved single-writer services
⇒ STOP + report, never silently fix).

## Resumability

A fresh session continues from **DEPLOYMENT_CAMPAIGN_STATUS.md** (sub-phase checklist + next
action) plus this file (evidence so far). No chat history required. Each sub-phase appends ONE
section below at close; never edit a closed section (append corrections).

## Sub-phases

| # | Scope | Size driver | Status |
|---|-------|-------------|--------|
| OWN-0 | Charter: identity + flag census verified · skeleton + status file · methodology locked | tiny | ✅ DONE 2026-07-12 |
| OWN-A | Production 1/2 — the SA-only master-data engine, FUNCTIONAL for the first time: products add/edit/archive/sizes + **flow editor** (never write-certified) · pattern library ×4 (SA bypass on `_PatternPermissionRequired`) · stage library + stage-categories + machine-types (`_StagePermissionRequired` SA bypass) · stage-rates + **`rerate_stage_role`** (S1.1 SA-only, auto-recalc + `RateCorrectionAudit`) | largest never-exercised SA write surface | ✅ DONE 2026-07-13 — 0 bugs, 0 code changes |
| OWN-B | Production 2/2 — stage operations as SA: consoles/workspaces/panels · generic ops start/complete/reopen (incl. S4-P5 downstream-guard interplay when SA drives) · allocate/void · review-reports · worker-report as non-assigned SA · barcode generation ×5 · costing + dashboards | second half; SA path through service gates | ✅ DONE 2026-07-13 — 0 bugs, 0 code changes, 1 INFO → backlog #10 |
| OWN-C | Expense — the 4 SA-only money levers FUNCTIONAL end-to-end (pay-basis flip + audit row · FnF preview→execute · reconciliation override **with a real M-6 block** · factory-expense void) + full settlement lifecycle driven by SA + advances + ledger-integrity recount after every rollback | highest stakes; hostile mindset; Money-Write STOP rule | ✅ DONE 2026-07-13 — **1 bug FIXED (OWN-C-1 evidence-FK lane collapse) + 2 pins, battery 1528/1528**; 1 INFO → backlog #11 |
| OWN-D | Inventory Administration — **roles CRUD incl. THE carry-in: RoleForm.permissions queryset vs curated allowlist (judge from evidence)** · sidebar-access editor (M2M writes → live middleware behavior) · access hub · tracking: financial history rows VISIBLE to SA + exports | the deferred owner item lives here | ✅ DONE 2026-07-13 — **carry-in CONFIRMED → FIXED (OWN-D-1) + 2 pins, battery 1530/1530**; 0 false owner blocks |
| OWN-E | Raw materials — roll bulk-add WITH financials (SA-only, functional) · roll edit financials at all 4 layers (SA-positive: form fields present, service admits, template renders, history rows visible) · masters CRUD/archive/delete (#7 relevance check) · damage/restore/assign | financial-truth surface | ✅ DONE 2026-07-13 — 0 bugs, 0 code changes, battery NOT re-run; #7 stays INFO (not owner-UI-reachable, all-3-masters census); 1 INFO → backlog #12 |
| OWN-F | Machines (SA positive incl. assign/release) + **Storefront as SA (SA ∈ STOREFRONT_ROLES — first functional certification of the editor for the owner)** + Accounts: Team Members / User Skills / User Types CRUD functional · S2 signup-closed + S3 email-shadow hold for SA too · login/logout/OTP flows · `/admin/` staff wall admits the owner | three small surfaces + admin entry | ✅ DONE 2026-07-13 — 0 bugs, 0 code changes, battery NOT re-run; MGT-F-1 re-proven SA-driving; storefront editor FIRST functional cert; owner self-guards verbatim; /admin/ 200; #8 stays INFO |
| OWN-G | patterns_ai as SA — blueprint perm gate (SA 200 + write path) · full route sweep SA-positive · django-admin `/admin/` sampled surface (owner reaches it; is_staff=True) | one gate law + admin sample | ✅ DONE 2026-07-13 — 0 bugs, 0 code changes, battery NOT re-run; blueprint write LANDED; usage→outcome→void chain landed w/ owner stamps; admin Skill CRUD sampled; #9 stays INFO |
| OWN-H | Meta-audit + close: SA-perspective route census (anomaly rules: SA 403/302-bounce/500 anywhere = anomaly) · rendered sidebar as SA vs matrix (owner sees everything gated-visible) · cross-app uniformity of SA admission · carry-in disposition review · final verdict · docs+memory sync | mirrors MGT-H | ✅ DONE 2026-07-13 — 528-route census zero drift; 96-route SA sweep ZERO 403/500; sidebar 28/28; gate-gap audit clean; **PHASE 2 VERDICT: CERTIFIED — CLOSED** |

## Carry-ins into this certification

| Item | Disposition plan |
|---|---|
| **Worker-cert Phase-D INFO — `RoleForm.permissions` queryset wider than curated allowlist** (explicitly deferred to Phase 2; the reason this phase exists in the order) | **PRIMARY MANDATE → OWN-D.** Judge from evidence: what the form offers vs what the curated Roles editor intends vs what a POST actually persists; escalation impact (can the owner grant a perm the editor never curated, and does any gate honor it?). Fix ONLY if confirmed defect; else classify BY DESIGN / INFO with proof |
| Backlog #6 — RBAC.md role-table drift | Doc-only; NOT fixed here (KOS phase 7); consulted as (unreliable) expectation input only |
| Backlog #7 — `_MasterArchiveView` garbage-pk 500 | Owner-relevance check in OWN-E (SA hits same 500); stays INFO unless certification proves UI-reachable for owner |
| Backlog #8 — MachineAssignView worker-param validation | OWN-F touches assign as SA; stays INFO unless owner workflow confirms a defect |
| Backlog #9 — patterns_ai voided_by/retired_by stamps | OWN-G notes only; audit-hygiene, fix-when-touched |
| `/media/<path>` login-tier (owner Option 1) | out of scope, noted only |
| OTP-send POSTs | NOT probed (EMAIL_BACKEND may be real SMTP — external side effect); same disclosure as MGT-F |

---

# Evidence sections (one per sub-phase, appended at close)

## OWN-0 — Charter (2026-07-12) ✅

- Git state verified: HEAD 49404001 (2026-07-04), **306 dirty/untracked paths** = 303 at Phase-1
  close + exactly the 3 Phase-1 files (MANAGEMENT_ROLE_CERTIFICATION.md ·
  test_management_role_certification.py · DEPLOYMENT_CAMPAIGN_STATUS.md) — no drift.
  Battery baseline **1526/1526** stands (no code change since MGT-F; not re-run per method rule 7).
- Owner identity verified read-only (Django shell): `umesh29mar@gmail.com` pk=1, active,
  role=Super Admin, extra_roles=[], is_superuser=True, is_staff=True, password verified.
- Flag-alignment census: **exactly one owner-class account exists**; role/is_superuser/is_staff
  all align on pk=1; zero staff-non-superuser or SA-role-divergent users (re-confirms the worker
  meta-audit census, now from the owner side).
- Created this skeleton; DEPLOYMENT_CAMPAIGN_STATUS.md Phase-2 section added;
  DOCUMENTATION_INDEX row added; memory synced.
- **No certification performed. No code touched. No fix applied.**

## OWN-A — Production 1/2: the SA master-data engine, FUNCTIONAL for the first time (2026-07-13) ✅

**Verdict: 0 bugs · 0 false owner blocks · 0 code changes · battery NOT re-run (1526/1526 stands).**

**Preconditions (§17.4):** identities verified (pk=1 SA active · dev.mgr pk=52 · dev.ow.a
pk=46); every §7 probe anchor EXACT — Products 18 (pk=5 = "1-6"), ProductPatterns 60,
Stages 23, StageCategories 5, MachineTypes 5 — zero target drift. Rerate targets selected:
DEV-NICKAR-001 (completed, unsettled, DEV world) + XFB-001 sr=161 (completed, unsettled,
real-rate rows). Owner password per §17.5 (memory `test-credentials`); never recorded here.

**Gate-map audit (owner-angle, step 2):** product CRUD/sizes/flow/archive + stage-rates/
correct = `SuperAdminOnlyMixin` (`user_has_role([ROLE_SUPER_ADMIN])`, mixins.py:92 — role-code
path, admits any SA-role account regardless of is_superuser) · patterns = `_PatternPermission
Required` + stages/categories/machine-types = `_StagePermissionRequired` (Django perms with
the DOUBLE SA bypass inside `user_has_perm`: is_superuser branch AND role.code branch — both
admit pk=1; a future SA-role-without-is_superuser also passes). **No gate gap on any OWN-A
surface for the SA class.**

**Shell GET matrix as owner (Django test client, 22 URLs):** 21× **200** (product list/create/
update(5)/flow(5)/sizes(5)/archive(5) · pattern list/add/edit/delete · stage list/add/edit/
delete · category list/add/edit · machine-type list/add/edit · stage-rates DEV-NICKAR-001) ·
1× **302 = `product-patterns` → `patterns_ai:dashboard?product=5` — BY DESIGN**, citation =
the view's own docstring (`ProductPatternsEntryView`, pattern_views.py:147: "Login-only by
design (Phase-1 D-2)... Redirect by URL name only — no patterns_ai import (ADR-H wall)").

**Functional writes — ALL LANDED, all rollback-wrapped (one outer atomic + per-cluster
savepoints; post-rollback counts byte-identical; sessions rolled back too):**
- **Products:** create `DEV-OWNA-P1` (count 18→19, row verified) → edit (name change landed)
  → archive (`is_active` → False, soft-state) — rollback → 18 ✓.
- **Sizes:** add (code=zz, label) → row landed → update label → archive `is_active=False` —
  rollback ✓. (First attempt used a wrong field name — `name` vs `label` — producing a
  redirect + no row: PROBE ERROR, not a defect; corrected probe fully passed.)
- **Flow editor (first-ever write certification):** `action=add` (WorkflowStage row created)
  → `action=set_cost` (cost_rate 9.50 landed + `credits_workers=True` toggle landed) —
  service-path (`add_stage_to_product_flow`/`set_stage_cost`) — rollback ✓.
- **Patterns ×4:** create `DEV-OWNA-PT1` (60→61) → edit → delete (row gone) — rollback → 60 ✓.
- **Stage/category/machine-type:** StageForm required = [code, name, work_type]; create/edit/
  delete stage + create category + create machine-type all landed — rollback ✓ (23/5/5).
- **`rerate_stage_role` (S1.1) — FULL FUNCTIONAL PROOF** on XFB-001 sr=161 role=3:
  POST new_rate=0.75 + mandatory reason + confirm → **rate 0.5000→0.7500, auto-recalc fired
  (WSC expected_earning 6.00→9.00), `RateCorrectionAudit` +1 {old 0.5000, new 0.7500,
  actor=umesh29mar, reason recorded}**; service log: `stage_rate.rerate sr=161 role=3
  0.5000->0.75 recalc=1 by=1` — rollback restored rate/earning/audit-count byte-identically.
  (An earlier probe on DEV-NICKAR-001 changed 0→0 WITH a valid audit row — explained: that
  DEV world carries placeholder-0 rates; the service ran and audited correctly there too.)

**Negative controls:** dev.mgr AND dev.ow.a → **403 ×10** (product-create, product-flow(5),
pattern-add, stage-rates, machine-type-add — each identity) — Phase-1/worker walls hold.

**Browser as `umesh29mar` on :8003 (real login, one attempt):** landing = `/production/`
(Operations) · **sidebar census: ALL sections render for SA** — Main, Production, Raw
Materials, Storefront, Tracking, Payroll, **Administration incl. Access Control / Team
Members / Roles & Permissions / Stages / Sidebar Access** (SA-sees-everything predicate live)
· products page renders (39 Edit/Flow actions) · **flow editor pk=5 renders** · **stage-rates
XFB-001 renders** with the S1.1 explainer ("Super-admin: correct a stage's payable rate
before settlement… Settled rows require a reversal first") + Correct actions · **CSRF-valid
write round-trip:** pattern `DEV-OWNA-B1` created (flash "Pattern … created.", row in list)
→ **delete-confirm page rendered correctly (#5-class regression watch PASS with owner
driving)** → deleted (flash "… deleted."), **DB residue zero (60/60)**. Screenshots in
session scratchpad (owna_products/owna_flow/owna_rates.png).

**Prior-fix guards touched:** #5 delete-confirm class (pattern delete-confirm rendered) ✓.
**Disclosed artifacts (U13):** browser login session row for pk=1 (a normal owner login);
auto-increment pk gaps from rolled-back/deleted probe rows (e.g. ProductPattern pk=63
consumed) — zero data rows remain; pk=1 password/email/role/flags untouched (§16.5 clean).

**Close-out:** 0 confirmed bugs → 0 fixes → 0 pins (U4) → battery NOT re-run (method rule 7;
baseline 1526/1526 stands). Docs-sync: this section + status file + memory. **Next: OWN-B**
(Production 2/2 — stage operations as SA; targets LOWER-002 + XFB-002, re-verify state first).

## OWN-B — Production 2/2: stage operations as SA (2026-07-13) ✅

**Verdict: 0 bugs · 0 false owner blocks · 0 code changes · battery NOT re-run (1526/1526
stands) · 1 new INFO → backlog #10.**

**Preconditions (§17.4):** HEAD `49404001` exact; 308 dirty/untracked paths (status file records
"303+"; growth = campaign doc files from Phase-0/OWN-A closes — no code drift class). Identities
verified read-only (pk=1 SA active/su · dev.mgr pk=52 · dev.ow.a pk=46). **Probe targets EXACT
vs OWN-A census — zero drift:** LOWER-002 `in_progress`, current=`elastic_attach` (sr=108 open),
7 SRs (103/104/105/113/106/107 completed; two cutting-lane SRs = lanes 1+2, both `cut complete`);
XFB-002 `in_progress`, layering open (2 lane SRs 163/164 + cutting sr=165 started). Owner password
never used — browser reused the persisted OWN-A daemon session, identity verified in-page
(`umesh29mar@gmail.com` rendered in navbar); zero fresh login attempts, zero rate-limit exposure.

**Gate-map audit (owner-angle, step 2):** `user_role_code` (permission_service.py:43) checks
`is_superuser` FIRST → `super_admin`, else `role.code` — pk=1 admitted by BOTH paths
independently. All stage-op dispatch gates = role-code sets containing SA:
`ManagementRoleMixin`/`ProductionRoleMixin` (production/views/mixins.py:84/77) ·
`StageViewAccessMixin` skill gate → `user_can_access_stage` (access_service.py:35: management
always-True before any skill/stage lookup) · assignment gate bypasses MANAGEMENT_ROLES
(mixins.py:63). Service re-gates all admit SA: reopen skeleton step-1 mgmt gate
(`_shared.reopen_stage_record`) · `pool_service.allocate`:353 / `void_allocation`:521 =
MANAGEMENT_ROLES · lane writers `add_stream`:500 / `cancel_stream`:542 = MANAGEMENT_ROLES ·
review-reports `_gate` = MANAGEMENT_ROLES on GET **and** POST · the four per-stage
completion-skill gates (`_ensure_can_complete_layering/cutting/pattern/barcode`) = explicit
`{ROLE_SUPER_ADMIN}` bypass OR helper skill · C3 pending-override (adda_service.py:420) =
**SA-only lever**. **The ONE designed SA refusal** = worker-report own-task resolution
(worker_report_views.py:180 — no management bypass by design; owner decision D6: management
corrects via review-reports). A read-only sweep sub-agent independently corroborated (32-gate
table, zero SA-exclusion) — supplemental only per U7; every cited gate re-verified main-thread.

**Shell GET matrix as owner (Django test client): 17× 200** (dashboard · stalled ·
pending-reports · costing · layering-ws LOWER + XFB · pattern-ws · cutting-ws · cutting-legacy ·
barcode-ws · stage-panel elastic_attach + side_seam_close · review-reports · stage-advanced ·
add-lane form · adda-detail LOWER + XFB) **+ 1× 403 BY DESIGN** (worker-report as non-assigned
SA — exact refusal `PermissionDenied("You are not assigned to this stage.")`, POST also 403;
classification: D6 own-task-only surface; the SA correction path = review-reports, proven
functional below). **POST-only proof: 14× 405** on GET (generic start/complete/reopen/allocate/
alloc-void · layering-complete/reopen · cutting-reopen · barcode start/generate/complete/reopen ·
cancel-lane · bundle-sets).

**Functional writes — ALL LANDED, all rollback-wrapped** (technique of record: outer atomic +
savepoints + Sentinel; three probe runs; post-rollback baselines byte-identical every run —
run 2 exited via an in-probe script exception and the next session-start recount proved the
outer atomic rolled back byte-identically, §15.4 discipline):
- **Generic reopen → re-complete (side_seam_close sr=107):** reopen flipped DONE→OPEN, Adda
  pointer reset to side_seam_close, service chain logged as user=1 (`cost.clear` ·
  `stage_rate.refloat_on_reopen rows=3` · `pool.clear rows=2` · `stage.reopen`); re-complete
  restored DONE (`cost.freeze …processing_cost=170.00` · `pool.materialize rows=2` ·
  `adda.advance stage_to=elastic_attach`). Flashes: "Stage reopened — make corrections then
  Complete again." / "Stage complete. Advanced to Elastic Attach."
- **Allocate + void (OP-1, elastic_attach sr=108):** allocate 1.00 (color=1,size=14) to
  DEV-EL-A → WSA row LANDED (0→1, `pool.allocate … by=1`) → void → `voided_at` set, "quantity
  returned to the pool." **Over-allocation refusal always-on with SA driving:** qty=99999 →
  "Cannot allocate 99999: only 29.00 available in the pool for these dimensions."
- **Review-reports POST (P1 correction):** `verified_162: 29` (good=30.00) → value LANDED,
  "1 quantity correction(s) saved."; `void_report` with garbage task_id → designed "Invalid
  report reference." (no 500 — the MGT-B-1 crash class absent here).
- **Generic start:** added a 2nd worker → "Workers assigned.", WorkerStageTask 1→2
  (`worker_task.set sr=108 members=[46, 56]`).
- **Lanes (GAP-4):** empty-reason POST → "A reason is required to add a cutting lane."
  (**MGT-B-1 prior-fix guard re-proven with SA — flash, not 500**, shell AND live browser);
  valid add → **lane LANDED** ("Lane added: body (lane 3)…", CuttingStream 2→3, seq=3,
  `adda.stream_added … by=1`); **cancel-if-empty LANDED** on the new lane (`cancelled_at` +
  reason stamped, "it stays on the record, greyed"); guard quotes captured: seq-1 lane → "A
  derived lane can never be cancelled…" · unknown fabric group → "'A' is not one of this
  Adda's fabric groups — a new group is a Blueprint change…".
- **C3 pending-override — the SA-ONLY stage-ops lever, FULL FUNCTIONAL PROOF (first ever):**
  transitional semantics documented from evidence — an assigned-but-never-started task does
  NOT block (completion auto-cancels it; observed run 2), a STARTED-not-submitted task BLOCKS:
  with DEV-OW-A holding a draft (in_progress) and DEV-EL-A submitted, SA complete WITHOUT
  override → **"Cannot complete Elastic Attach: 1 worker(s) have STARTED work but not
  submitted: DEV-OW-A. Wait for their reports, have them submit, or (Super Admin) override
  with a reason."** (sr stays open); **manager WITH override+reason → "Only a Super Admin can
  override pending worker reports."** (blocked — SA-only negative control); SA WITH
  override+reason → **stage completed, pending task cancelled, `COMPLETION_OVERRIDE`
  AddaHistory event landed audit-complete** {stage: Elastic Attach, reason, pending_count: 1,
  pending_workers: [DEV-OW-A]} actor=umesh29mar + service WARNING `stage.completion_override
  … by=1`, then cost_frozen + stage_advanced events. All rolled back byte-identically.
- **Designed refusals classified (fail-closed, state proven unchanged):** barcode-gen
  start/generate/complete on the completed stage → "Adda is not at the barcode_generation
  stage."; **barcode-gen reopen → the S4-P5 downstream-consumer guard VERBATIM, actionable:**
  "Cannot reopen Barcode Generation: downstream stage 'Side Seam Close' still has active
  worker allocations and completed production (good/alter/missing) that depend on this
  stage's output. Reverse-first — reverse any settlement on 'Side Seam Close', void its
  allocations, then reopen 'Side Seam Close'; work back toward 'Barcode Generation'.";
  bundle-sets → "This product has a single component — bundle from the cutting rows directly."
- **Multi-lane funnel refusals (observation):** cutting-reopen + layering-reopen (LOWER-002)
  and layering-complete (XFB-002) all refuse with "…has multiple cutting lanes — specify
  which lane." (streams-redesign `resolve_stream` fires before any stage guard; SRs
  unchanged). NOTE: MGT-B's close-out narrative attributed the cutting-reopen refusal to the
  S4-P5 guard; today's exact quote shows the lane-resolution refusal fires first on this
  2-lane Adda. Not a regression (reopen refused + state protected both times; S4-P5 guard
  itself proven verbatim above) — recorded as a narrative-precision observation, MGT-B
  section stays closed.

**New INFO → backlog #10:** review-reports "No changes." detection compares strings
(worker_report_views.py:347) — re-POSTing an equal value formatted differently (`29` vs stored
`29.00`) flashes "1 quantity correction(s) saved." though nothing changed. Proven inert:
verified value byte-identical AND `VERIFIED_QTY_CORRECTED` history count unchanged (4→4; the
service stays honest — view message/counter only). Fix-when-touched: Decimal compare.

**Negative controls:** worker (dev.ow.a) → 403 ×4 at dispatch (add-lane POST · cancel-lane
POST · review-reports GET+POST) + service denials with zero writes (generic reopen → "only
super_admin or manager can reopen the Side Seam Close stage", SR stayed DONE; allocate →
"Only management can allocate stage work.", WSA count unchanged); manager (dev.mgr) →
review-reports 200 + layering-ws 200 (Phase-1 positives hold) but BLOCKED on the SA-only
override lever (quote above). No Phase-1/worker-cert regression.

**Browser as owner on :8003 (persisted session, identity verified in-page):** sidebar = ALL
sections incl. **Administration ×6 links** (Access Control · Team Members · User Skills ·
Roles & Permissions · Stages · Sidebar Access — OWN-A listed 5, User Skills present then too;
census-precision note only); live renders: Layering Workspace — LOWER-002 · LOWER-002 ·
Cutting · Barcode Generation · stage-panel Elastic Attach · Review worker reports (correction
inputs + VOID REPORT actions visible, values match DB 30.00/29.00 · 38.00/38.00) ·
Manufacturing Costing; worker-report → **branded 403 page** ("This page is restricted to
other roles…"); **CSRF-valid live write probe:** add-lane submit with empty reason → refusal
flash banner rendered on the re-served form (screenshot), lanes DB re-checked unchanged
(2 rows, none cancelled). Screenshots in session scratchpad (ownb_lane_flash / ownb_review /
ownb_layering .png).

**Prior-fix guards touched:** MGT-B-1 (lane service refusal = flash, not 500) re-proven with
SA driving, shell + browser ✓.
**Disclosed artifacts (U13):** none in data — all writes rolled back byte-identically (proven
by recount after each of 3 runs); auto-increment pk gaps consumed by rolled-back rows (WSA 108,
CuttingStream 46, WorkerStageTask 232+, WSC/AddaHistory ids); no new login session row (browser
session reuse); pk=1 password/email/role/flags untouched (§16.5 clean).

**Close-out:** 0 confirmed bugs → 0 fixes → 0 pins (U4) → battery NOT re-run (method rule 7;
baseline 1526/1526 stands). Docs-sync: this section + status file + backlog #10 + memory.
**Next: OWN-C** (Expense — the 4 SA-only money levers; hostile mindset, Money-Write STOP rule,
ledger re-baseline at sub-phase start; owner-gated).

## OWN-C — Expense: the 4 SA-only money levers, end-to-end (2026-07-13) ✅ — 1 bug FIXED

**Verdict: 1 confirmed bug FIXED (OWN-C-1, evidence-FK lane collapse) + 2 pins → battery
1528/1528 · 0 false owner blocks · 1 new INFO → backlog #11 · ledger byte-identical after
every probe block.**

**Preconditions (§17.4) + ledger re-baseline (§5):** HEAD `49404001`; identities verified;
**OWN-C ledger baseline = 170 rows / Σ₹10880.25** (freshly recounted this session — numerically
equal to MGT-C's values, i.e. zero ledger drift since; still re-anchored per contract, never
assumed). ADST 8 (6 finalized + 2 superseded) · advances 0 · FactoryExpense 4 (2 voided) ·
recon-evidence rows 0. Targets verified: **worker pk=25 = `dev.monthly@test.local`** (DEV per
§4, active, `pay_basis=monthly`, 1 prior audit row — basis state verified first per §7) ·
unsettled completed Addas = XFB-001 + DEV-NICKAR-001/-A1 + DEV-P8B-A1 · runtime flag proof:
`ENFORCE_SETTLEMENT_RECONCILIATION=False`, `TOLERANCE=0`, `LEDGER_CREDIT_AT_ALLOCATION=False`
(U10 posture intact — settings files untouched all session).

**Gate-map audit (owner-angle):** every expense view = LoginRequired + `_ManagementOnly`
(MANAGEMENT_ROLES, views.py:60) except MyEarnings (self-view) — SA admitted at dispatch
everywhere. The 4 SA-only levers gate in the SERVICE on `{ROLE_SUPER_ADMIN}` role-code checks
(all admit pk=1 via both is_superuser-first resolution AND role FK): `payroll_service.
set_pay_basis`:387 · `fnf_service._ensure_super_admin`:36 (guards preview AND execute) ·
`adda_settlement_service.finalize`:490 override (`ADMIN_ROLES`) · `expense_service.
void_expense`:88. No gate gap for the SA class on any expense surface.

**GET matrix as SA: 11× 200 + 2× 405** (pay-basis + adst-start are POST-only — correct).
Zero 500s.

**Lever 1 — pay-basis (rollback-wrapped):** SA flip monthly→piece_rate → **landed** (flash
"Pay basis … changed to Piece Rate.", `WorkerPayBasisAudit` 1→2, actor=pk-1, service log
`pay_basis.change worker=25 monthly->piece_rate by=1 unsettled=2` — the R4 unsettled-lines
confirm path exercised with `confirm_unsettled=1`). Manager flip → "Only a Super Admin can
change a worker's pay basis.", basis + audit count unchanged. Worker POST → 403. Recount ✓.

**Lever 2 — FnF preview→execute (rollback-wrapped, DEV workers only per §4):**
- worker 25 (zero-balance monthly): preview ready; manager execute → "Only a Super Admin can
  run a Full & Final settlement." (worker stays active); **SA execute LANDED** — "Full & Final
  complete … 0 settlement(s), ₹0.00 paid, 0 advance write-off(s). Account deactivated —
  history preserved.", `is_active` flipped False. Worker GET → 403.
- **Money legs on `dev.hlp.nkb` (pk=66, DEV — holds XFB-001 uncredited ₹10.50 + an open
  XFB-002 task):** execute with the open task → designed guard verbatim: "Cannot run F&F:
  1 open task(s) — XFB-002/Cutting. Resolve them first (submit the report or cancel the
  assignment)." (still active); designed resolution via `set_stage_workers(sr165, [],
  cancel_note=…)`; preview then ready_addas=[XFB-001 ₹10.50]; **SA execute LANDED with real
  money: "1 settlement(s), ₹10.50 paid", ledger 170→173 (Σ→10901.25: 2 stage-earning credits
  6.00+4.50 via `ledger_service` + settlement payment), ADST-0011 finalized (leaver-scoped
  `only_worker`), account deactivated.** Recount after rollback ✓ 170/₹10880.25.

**SA-driven full settlement lifecycle (XFB-001, rollback-wrapped):** start → draft ADST-0011 ·
detail GET 200 with **`reconciliation_override` field rendered for SA** (S5 UI; MGT-C proved
it absent for manager) · finalize → status=finalized, `settled_by=1`, **ledger 170→172
(+₹10.50)**, expected_total 10.50, evidence rows 0 (clean adda) · reverse → status=reversed,
`reversed_by=1`, **ledger 172→174 (append-only proven — rows only ever added; ADR-0002
honored)**, flash "ADST-0011 reversed — ledger restored." Recount ✓.

**Lever 3 — reconciliation override on a REAL M-6 block (the never-done proof):** the block
exists only under `ENFORCE_SETTLEMENT_RECONCILIATION=True` (U10 keeps it OFF) — probe used a
**test-scoped `override_settings` context manager**, the exact technique of the pinned
`test_s5_recon_block` battery suite; settings files/env untouched, runtime flag re-verified
False before + after. Over-allocation constructed rollback-wrapped on XFB-001 (sr161
`cost_quantity_snapshot` 12.00→10.00 — probe-state construction mirroring the pinned test's
canonical fixture; contract §7 explicitly licenses DEV construction here). Results:
- SA finalize NO override → **exact block**: "Cannot finalize ADST-0011: settled more than
  produced — 'cutting' settled 12.00 but produced 10.00 (over by 2.00). Tolerance 0. Correct
  the verified quantity (Review Reports), void the over-allocation, or finalize with a
  super-admin override (reason required)." — status stays draft, **ledger unchanged (atomic
  finalize rolled back, nothing booked)**.
- MANAGER finalize WITH override text → "Only a super admin can override a settlement-
  reconciliation block ('cutting' settled 12.00 but produced 10.00 (over by 2.00))." —
  draft + ledger unchanged (SA-only negative control).
- **SA finalize WITH override+reason → FINALIZED + `SettlementReconciliationEvidence` row
  stamped audit-complete: (flag=over_allocated, allocated 12.00, output 10.00,
  `override_reason='DEV OWN-C M-6 override probe'`, `overridden_by=pk-1`).** Recount ✓.

**🐛 CONFIRMED BUG OWN-C-1 → FIXED (in-scope: the lever's own evidence stamping):**
`record_reconciliation_evidence` resolved the evidence FK via a dict keyed by stage CODE
([adda_settlement_service.py](../config/expense/services/adda_settlement_service.py)) — on a
multi-lane Adda, N same-code lane SRs collapsed to an arbitrary survivor, so **the persisted
append-only audit row pointed at the WRONG lane's stage record** while carrying the
over-allocated lane's quantities. Probe proof: over-allocation constructed on sr=161 (holds
the 12.00 contribution) → evidence row carried sr161's numbers (12.00/10.00) but
`stage_record_id=162` (the clean 9/9 lane). Evidence rows persist on EVERY finalize (WARN
record-only mode included) → the B-1 soak metric that S5 gates on would mis-attribute lanes.
Lane-era (GAP-4 streams) regression of a one-SR-per-stage-code assumption. **Fix (smallest):**
`reconcile_stage_pay` rows now carry `stage_record_id` (additive key,
[reconciliation_service.py](../config/expense/services/reconciliation_service.py)) and the
evidence bulk_create uses it directly (the old code's completed-SR filter was redundant —
recon already filters completed SRs). Money math untouched — block/override/tolerance logic
reads quantities, not the FK. **U8 review (§10 disclosure): the fix touches
`adda_settlement_service` (single-writer family) strictly within the confirmed defect — no
money-write path added or altered; `ledger_service` untouched; golden values unaffected
(battery green incl. ₹225 chain).** **Pins ×2** (`test_s5_recon_block.MultiLaneEvidenceTests`):
evidence FK = the over-allocated lane's SR (clean+over two-lane world) · both-lanes-over →
2 rows, each FK'd + quantity-paired to its own SR. **Post-fix live re-proof:** identical
rollback-wrapped M-6 probe → evidence now stamps sr=161 with the override + correct pairs.
Related display-only observation (NOT fixed, smallest-change rule): a360's
`recon_by_stage` badge collapses the same way → **INFO backlog #11**.

**Lever 4 — factory-expense void (rollback-wrapped):** SA create (rent ₹11, service-path
actor=pk-1) → SA void NO reason → "A reason is required to void an expense." → manager void →
"Only a Super Admin can void a factory expense." (`voided_at` still None) → **SA void WITH
reason → landed: `voided_at` set, `voided_by=1`, reason recorded** → SA re-void → "This
expense is already voided." Recount ✓.

**Advances (rollback-wrapped):** SA advance to worker 25 (monthly) → **designed refusal**:
"Advances are not available for monthly-salary workers yet — there is no recovery path (their
pay never flows through settlement)…" — zero rows (R4 monthly exclusion, classified BY
DESIGN); SA advance ₹100 to `dev.ow.a` (piece-rate) → **landed** (WorkerAdvance row created,
"Advance recorded", **ledger delta ZERO — loan pool by design, V2**). Recount ✓.

**Negative controls:** worker → my-earnings 200 (own view) + **403 ×8** (payroll · adst-list ·
adst-detail · advance-add · exp-list · fnf · worker-detail-25 · pay-basis POST); manager →
payroll/adst-list 200 (Phase-1 positives hold) but blocked on ALL 4 levers with exact denial
quotes (above). Zero Phase-1/worker-cert regression.

**Browser as owner on :8003:** persisted session had EXPIRED (bounced to sign-in — earlier
selector checks discarded as void); fresh password login, ONE attempt, landing /production/.
Render-proofs (SA sees what the manager provably doesn't, MGT-C contrast): worker-25 profile
→ **pay-basis form rendered** (`[name=pay_basis]` present) · worker-detail → FnF link present ·
FnF page → **full Execute panel rendered** ("Run Full & Final" button + confirm checkbox +
"Money position ₹0.00" + honest "monthly workers never settle (salary via Factory Expenses)";
`write_off_reason` input correctly ABSENT — worker 25 has 0 advances, reason is demanded only
when residuals exist) · expenses list → **2 void_reason inputs + 2 Void buttons rendered** ·
ADST-0010 (finalized) → Reverse / Reverse-&-settle-again actions. **Zero-write CSRF probe with
owner driving:** Record-Advance form (FancySelect worker=dev.monthly, amount 50) → submit →
**designed refusal flash banner rendered live** + advance rows 0 (DB re-checked). Screenshots:
ownc_profile / ownc_fnf / ownc_advance_refusal .png (session scratchpad).

**Battery (U5, code changed):** sequential fresh-DB — 9-app **1000/1000 OK** (170.2s) +
patterns_ai **528/528 OK** (143.0s) = **1528/1528 GREEN**; arithmetic 1526 + 2 pins = 1528 ✓.
(Disclosure: the 9-app suite was run twice — once for the OK verdict, once re-emitting the
count line; both green.)

**Money-Write STOP review (U8):** no new money-write path found anywhere in OWN-C probing;
all landed writes flowed through the approved single writers (`ledger_service` credits at
finalize · settlement services · `payroll_service` audit · `expense_service` void ·
`advance_service` pool). The one code fix altered an audit-FK resolution inside the approved
writer, not a money write. No STOP event.

**Disclosed artifacts (U13):** all probe writes rolled back byte-identically (per-block ledger
recounts + final all-state recount, incl. after two mid-development probe-script crashes whose
outer atomics rolled back — verified by recount before continuing); auto-increment pk gaps
consumed (ADST-0011 references, ledger entries 214+, WorkerAdvance pk 4, FactoryExpense pk 6,
evidence rows); one fresh owner login session row (normal login; the OWN-A browser session had
expired); pk=1 state untouched (§16.5 clean). sr161 snapshot verified restored 12.00.

**Close-out:** 1 confirmed bug (OWN-C-1) → FIXED (2 files: reconciliation_service.py +
adda_settlement_service.py, evidence-resolution only) → 2 pins (U4) → **battery 1528/1528**
(new canonical baseline). Docs-sync: this section + status file + backlog #11 +
config/expense/README.md (M-6 lane-correctness note) + memory. **Next: OWN-D** (Inventory
Administration — roles CRUD incl. THE `RoleForm.permissions` carry-in · sidebar-access editor
· access hub · tracking financials/exports; owner-gated).

## OWN-D — Inventory Administration: roles CRUD + THE carry-in, sidebar-access live-flip, hub, tracking financials/exports (2026-07-13) ✅ — carry-in CONFIRMED → FIXED

**Verdict: THE `RoleForm.permissions` carry-in = CONFIRMED DEFECT → FIXED (OWN-D-1) + 2 pins →
battery 1530/1530 · 0 false owner blocks · 0 new INFO · every probe rolled back byte-identically.**

**Preconditions (§17.4):** HEAD `49404001` exact; 309 dirty/untracked paths (308 at OWN-C close +
campaign-doc growth; no code-drift class). Identities verified read-only (pk=1 SA
active/su/staff · dev.mgr pk=52 · dev.ow.a pk=46). **Probe anchors EXACT:** Role table **5 rows**
(accountant/listing_team/manager/super_admin/worker — ALL `is_system=True`, all holding **0
permissions**) · SidebarItemRule **21 rows** (ids 1–20+23; census captured: 6 Administration rules
all `roles=[]` = SA-implicit-only; Main 2 / Production 4 / Raw Materials 6 / Storefront 2 /
Tracking 1) · roll pk=37 = `GLDN-R6` (supplier EMPTY, cost_per_kg 195.00, status=used, **1 history
row**; DB-wide census: ZERO ClothRollHistory rows with `field_name ∈ {supplier, cost_per_kg}` —
financial-visibility proof therefore used a constructed row via the single-writer, below). Owner
password per §17.5 (memory `test-credentials`); never recorded here.

**Gate-map audit (owner-angle, step 2):** roles CRUD ×4 + access hub = `SuperAdminOnlyMixin`
(`user_has_role({ROLE_SUPER_ADMIN})`, inventory/views/mixins.py — role-code path; pk=1 admitted
via is_superuser-first resolution AND role FK independently) · sidebar-access GET+POST =
`_SuperAdminOnly` (same predicate, sidebar_access_views.py:29) · middleware overlay
(`SidebarAccessMiddleware` → `can_access_url_name`, permission_service.py:513): SA always-True
BEFORE any rule lookup; the editor's POST handler force-excludes super_admin from `allowed_roles`
(`.exclude(code=ROLE_SUPER_ADMIN)`, :92) — the owner can never lock themselves out, DB-proven
(no rule row stores super_admin) · tracking: dashboard/barcode-list/print/scan =
`ProductionRoleMixin` (SA ∈ PRODUCTION_ROLES) · roll/adda history = ProductionRole + G-AUTH-1
helpers (management always) + **the financial-row filter `user_can_view_financials` (FINANCIAL_
ROLES = {super_admin, accountant}) — SA admitted** · exports list/trigger/re-download =
`ManagerOrAdminMixin` (MANAGEMENT_ROLES — by design NOT SA-only) · quick-CSV + scan fns =
in-body role checks admitting SA. **No gate gap for the SA class on any OWN-D surface.**
django-admin cross-check: `accounts/admin.py` registers Skill + User only — Role has NO admin
surface, so the curated Roles editor is the ONLY Role-permissions write path (relevant to the
carry-in verdict; /admin/ itself = OWN-G scope).

**Shell GET matrix as owner (Django test client): 17× 200 + 4× 405** — roles list/add/edit(3)/
delete-confirm(3) · sidebar-access · access hub · my-dashboard · styleguide (login-only by
design) · tracking dashboard · barcode-list/print LOWER-002 · quick-CSV (text/csv) ·
roll-37 history · adda-history LOWER-002 · export-list · EXP-2026-006 re-download (text/csv) ·
scan SHA-001-0361; 405 = export csv/xlsx/pdf triggers + scan-status (POST-only, correct).
**Zero 500s, zero false owner blocks.** (Whole matrix ran inside one forced-rollback atomic —
scan GET stamps `last_scanned_at/by` by design; nothing persisted.)

**THE CARRY-IN — judged from evidence → CONFIRMED DEFECT → FIXED (OWN-D-1):**
- **Enumeration:** `RoleForm.permissions` queryset = **216 perms** (filter =
  `app_label ∈ ROLE_EDITABLE_APPS`, 5 apps; the old `ROLE_EDITABLE_MODELS_EXCLUDED` guard is an
  EMPTY legacy alias since the positive-allowlist refactor). Curated editor
  (`ROLE_EDITOR_SECTIONS` → `permissions_qs_by_app()` → template `perm_sections`) renders
  **80 perms** (20 content types × 4). **DELTA = 136 perms across 34 service-only/internal
  models** the editor deliberately hides (WorkerStageContribution, StagePoolSnapshot,
  RateCorrectionAudit, accounts.User, *History …).
- **Persistence proof (pre-fix, rollback-wrapped):** hand-crafted owner POST to role_edit with
  `production.change_machinetype` (in-app, non-curated) → form VALID → **persisted**
  (`['change_machinetype', 'view_stage']`), invisible on the edit page (template renders curated
  sections only), visible only as the hub's perm_count.
- **Gate honoring proof (the escalation question, rollback-wrapped):** throwaway user with the
  probe role as PRIMARY role → `production:machine-type-list` **200** and
  `machine-type-edit` **200** (previously 403) — `user_has_perm` step 4 matches the persisted
  codename (codename-only, app-label ignored: `split('.')[-1]`, permission_service.py:155), and
  the `_StagePermissionRequired`-family views at access_views.py:224/287 honor it.
  machine-type-add stayed 403 (add_machinetype not granted — grant-precise). Control: same user
  without the role → 403. (extra_roles note: `_role_perm_codenames` reads the PRIMARY role FK
  only, so an extra_roles stack does NOT carry perm grants — primary-role proof is the decisive
  one.)
- **Boundary held:** POST with `expense.view_all_payroll` (app NOT in the editable set) →
  form error **"Select a valid choice. 237 is not one of the available choices."** — money/
  payroll perms were never POST-able; the hole was in-app service-model perms only.
- **Self-healing observed:** a subsequent normal editor save (curated ticks only) silently WIPES
  hidden grants (M2M set from POST) — the breach was real but unstable, another reason the
  curated abstraction must be enforced at the validator.
- **Existing-data safety:** all 5 live roles hold 0 perms → narrowing the queryset can strip
  nothing in production data.
- **Verdict: CONFIRMED-FIXED.** The form's validation queryset (the ONLY Role-perm write
  surface, per the admin cross-check) contradicted the curated editor's own documented intent
  ("sirf un models ko expose karte hain jo non-developer admin grant kare") and produced
  honored, invisible grants. **Fix (smallest):** [role_forms.py](../config/inventory/forms/role_forms.py)
  `__init__` now builds the queryset from `permissions_qs_by_app()` — the SAME curated source the
  rendered checkboxes use (offered == validatable; 1 code file). **Post-fix live re-proof:**
  queryset = exactly 80 = curated (delta 0); identical machinetype POST now REJECTED ("Select a
  valid choice. 297 is not one of the available choices."), nothing persisted; curated create
  still lands; rendered sections byte-same (5 sections / 80 boxes, browser-confirmed). **Pins ×2**
  (`inventory.tests.RolePermissionCurationTests`): queryset ≡ curated allowlist (+ machinetype
  explicitly absent) · hand-crafted non-curated POST → form error + zero persistence.

**Roles CRUD round-trip + guard quotes (rollback-wrapped, owner driving):** create `DEV OWND R1`
(5→6, flash "Role 'DEV OWND R1' created.", curated perm landed) → edit (name change landed) →
delete-confirm GET 200 → delete POST → row GONE → count 5 ✓. Guards verbatim:
delete-while-assigned (extra_roles) → **"'DEV OWND R1' is still assigned to users (primary or
extra role). Reassign them first."** (PA-05A-2 extra_users guard re-proven) · system-role delete →
**"Cannot delete system role 'Worker'."** · system-role code change → form error **"Cannot change
the code of a system role."** (code stayed `worker`). Negatives: manager AND worker role_add POST
→ 403, zero rows.

**Sidebar-access editor — M2M write → LIVE middleware flip (rollback-wrapped):** baseline worker
GET /tracking/ → **302** → my-dashboard + `can_access_url_name=False` (rule 14 roles=[manager]).
Owner POST (full 21-rule bulk-upsert payload rebuilt from DB state + worker added to
`tracking:dashboard`) → flash "Sidebar access rules saved.", rule now [manager, worker] → fresh
worker client GET /tracking/ → **200** + `can_access=True` — **the menu rule changed URL
enforcement live, no restart, no cache invalidation** (middleware re-reads rules per request).
Post-rollback: rule 14 = [manager] byte-identical. SA-implicit invariant held throughout
(no rule ever stores super_admin; SA bypass precedes rule lookup).

**Access hub (read-only):** GET 200 with all four matrices materialized — 7 page-sections
(SIDEBAR registry join, db-vs-code governance flagged per row) · 23 stage rows · 47 user rows ·
role_summary perm-counts (probe role's hidden grant surfaced here as count=2 pre-fix — the ONLY
surface that betrayed it). TemplateView = no POST path.

**Roll #37 financial history SA-POSITIVE (constructed rows via the single-writer,
rollback-wrapped):** DB held zero financial history rows anywhere, so two rows were written
through `history_service.log_roll` (rule-5 single writer; cost_per_kg 195.00→210.00 + supplier
''→'DEV Supplier') on roll 37, then: **SA GET → events contain `['cost_per_kg', 'status',
'supplier']` — both financial rows VISIBLE; manager GET → `['status']` only** (server-side
`.exclude(field_name__in=('supplier','cost_per_kg'))`, tracking_history.py:69 — value never
reaches the template for non-FINANCIAL_ROLES). Worker GET roll-37 → 403
**"You can only view history for rolls on Addas you're assigned to."** (G-AUTH-1 sibling;
same worker gets adda-history LOWER-002 200 = assignment-scoped, by design). Rollback → roll-37
history back to exactly 1 row.

**Exports as SA (rollback-wrapped):** POST export-csv LOWER-002 → **200 text/csv, 5366 bytes,
BarcodeExportBatch 6→7 (manifest row landed)** → rollback → 6. Re-download EXP-2026-006 → 200
text/csv. Quick-CSV GET → 200 text/csv. Worker POST → 403. (Manager 200 = MANAGEMENT_ROLES by
design, MGT-D certified — export is management-wide, not SA-only; classified, not a finding.)

**Negative controls (Phase-1/worker-cert regression guard):** manager — Administration page URLs
roles-list/sidebar-access/access-hub → **302 + "You don't have the access to this page."**
(middleware, rules 18/20/15 roles=[]) and action URLs roles add/edit/delete → **403** (mixin —
the two-layer defense visible in one matrix); tracking surfaces stay manager-positive
(MGT-D holds); financial history rows manager-EXCLUDED (above). Worker — everything
Administration-blocked (302/403 same split), export surfaces 403 ×5, roll-37 history 403;
barcode list/print/scan 200 = PRODUCTION_ROLES worker-cert posture unchanged. Manager + worker
role_add POSTs inert. **Zero regression on any closed certification.**

**Browser as owner on :8003 (fresh password login, ONE attempt — prior daemon session expired;
identity verified in navbar):** sidebar renders ALL sections incl. **Administration ×6**
(Access Control · Team Members · User Skills · Roles & Permissions · Stages · Sidebar Access);
roles list renders all 5 roles; **role form renders exactly 5 curated sections / 80 checkboxes
(post-fix UI live)**; **CSRF-valid write round-trip: role `DEV OWND Browser` created via the
real form (row in list + DB row pk=16 with the ticked curated perm `view_product`) →
delete-confirm page rendered (#5-class regression watch PASS) → deleted → DB residue ZERO
(5/5 roles)**; Sidebar Access page renders the 21-rule grid (294 role/skill checkboxes) with the
SA-implicit explainer ("Super Admin sees every sidebar item… can never lock themselves out");
Access hub renders the Roles × Pages matrix + three-concept explainer; roll-37 history renders
(GLDN-R6); exports page renders all 6 manifest rows. Screenshots: ownd_roles / ownd_sidebar_
access / ownd_access_hub / ownd_role_delete_confirm / ownd_exports .png (session scratchpad).
**Deliberate containment (§4):** the Sidebar-Access SAVE button was NOT clicked in the browser —
it bulk-upserts the LIVE 21-rule M2M table with no reverse path; the write path was fully proven
rollback-wrapped in shell instead (live-flip block above). Probe-error disclosure: one blind
`form.submit()` hit the navbar LOGOUT form (form[0]) and ended the owner session — re-login
performed (second login of the session); subsequent probes scoped to the role form (form[1]).

**Battery (U5, code changed):** sequential fresh-DB — 9-app **1002/1002 OK** (170.7s) +
patterns_ai **528/528 OK** = **1530/1530 GREEN**; arithmetic 1528 + 2 pins (OWN-D-1) = 1530 ✓.

**Prior-fix guards touched:** #5-class delete-confirm (role delete-confirm rendered, shell +
browser) ✓ · BUG-E1-class master-CRUD roles untouched here · middleware flash-redirect behavior
(worker-cert Phase-D posture) re-proven from the owner/manager/worker sides.

**Disclosed artifacts (U13):** all probe writes rolled back byte-identically (Role 5 ·
SidebarItemRule 21 with rule-14 roles=[manager] · roll-37 history 1 · BarcodeExportBatch 6 —
recounted after every block); auto-increment pk gaps consumed by rolled-back/deleted rows (Role
pks 12–16 consumed incl. browser round-trip pk=16 create+delete; ClothRollHistory, BarcodeExport
Batch ids); TWO fresh owner login session rows (initial + post-logout-mishap re-login — both
normal logins); pk=1 password/email/role/flags untouched (§16.5 clean).

**Close-out:** 1 confirmed defect (OWN-D-1 = THE carry-in, verdict CONFIRMED-FIXED) → FIXED
(1 code file: inventory/forms/role_forms.py, validation-queryset-only — no view/service/model/
migration change) → 2 pins (U4) → **battery 1530/1530 (new canonical baseline)**. Docs-sync:
this section + status file + docs/apps/inventory/GUIDE.md (forms row) + config/inventory/
README.md + memory; no new backlog row (0 INFO). **Next: OWN-E** (Raw materials — bulk-add +
financial fields SA-positive 4 layers · masters · #7 relevance check; owner-gated).

## OWN-E — Raw materials: financial truth SA-POSITIVE at all 4 layers, bulk-add functional, masters CRUD, #7 owner-relevance (2026-07-13) ✅

**Verdict: 0 bugs · 0 false owner blocks · 0 code changes · battery NOT re-run (1530/1530
stands) · 1 new INFO → backlog #12 · #7 stays INFO (owner-relevance proven ABSENT) · every
probe rolled back byte-identically.**

**Preconditions (§17.4):** HEAD `49404001` exact; 311 dirty/untracked paths (309 at OWN-D close +
campaign-doc growth only — verified doc-class via porcelain grep, no code drift). Identities
verified read-only (pk=1 SA active/su/staff · dev.mgr pk=52 · dev.ow.a pk=46). **Probe anchors
EXACT:** roll pk=1 `CR-000001` (supplier='Validation Supplier', cost_per_kg=200.00, status=used,
weight=25.00) · roll count **32** · Cotton pk=1 active + referenced (29 rolls) · masters census
6 types / 15 colors / 3 locations · DB-wide financial ClothRollHistory rows = **0** (OWN-D
constructed-row rollback held) · total ClothRollHistory 40. Roll-op targets re-anchored: pk=21
`NKS-R4` NOT_USED (edit/damage target) · pk=36 `GLDN-R5` DAMAGED (restore target) · 3 in-progress
Addas with an open Layering lane (XFB-002 · DEV-NICKAR-002 · 3-PATTI-010) for the assign proof.

**Gate-map audit (owner-angle, step 2):** dashboards ×2 + roll-list + roll-detail + 3 master
lists = LoginRequired + `ProductionRoleMixin` (SA ∈ PRODUCTION_ROLES) + SidebarItemRule ×6
managed (SA-implicit bypass precedes rule lookup, OWN-D-proven) · roll-bulk-create =
**`SuperAdminOnlyMixin`** (`user_has_role([ROLE_SUPER_ADMIN])` — the ONLY SA-only surface in the
app) · roll-edit/assign/damage = `ManagementRoleMixin` + service re-gates (`update_roll_details`/
`mark_roll_damaged`/`restore_damaged_roll` re-check MANAGEMENT + mandatory reason) · master
create/update = `ManagementRoleMixin` + ModelForm; archive/delete route through
`master_service._ensure_can_manage` (MANAGEMENT) · **financial fields supplier/cost_per_kg =
4 layers** (form `fields.pop` unless `user_can_edit_financials` · service `PermissionDenied`
re-check in `bulk_create_rolls`+`update_roll_details` · template `can_view_financials` branches ·
history strip `.exclude(field_name__in=('supplier','cost_per_kg'))` on the 3 time-log surfaces
roll-list/rm-dashboard/cloth-dashboard, PA-13-3) — FINANCIAL_ROLES={super_admin, accountant},
**SA admitted at every layer**. All gates route through `user_has_role` (is_superuser-first
resolution + role FK independently, OWN-D lineage). **No gate gap for the SA class on any
raw_materials surface.**

**Shell GET matrix as owner (Django test client): 22× 200 + 1× 405** — dashboards ×2 ·
roll list/bulk-add/detail-1/edit-21/assign-21 · masters list/add/edit/archive-confirm/
delete-confirm ×3 models; 405 = roll-damage (POST-only, correct). **Zero 500s, zero false owner
blocks.** (Matrix ran inside one forced-rollback atomic; counts byte-identical after.)

**Financial truth — all 4 layers SA-POSITIVE with landed writes (rollback-wrapped):**
- **Layer 1 (form):** SA `BulkRollForm` fields = {cloth_type, storage_location, purchased_date,
  **supplier, cost_per_kg**}; SA `RollEditForm` = 6 fields incl. both financials. Manager control:
  both fields ABSENT from both forms. Browser: live bulk-add form as owner renders both fields
  (forms-census + screenshot).
- **Layer 2 (service):** SA view-path bulk-add POST → flash **"3 cloth rolls created."** —
  CR-000013/14/15 (2× color Red + 1× Blue breakup) ALL stamped supplier='DEV OWNE Supplier' +
  cost_per_kg=123.45, status=not_used, count 32→35, **3 ClothRollHistory CREATED rows actor=1
  note='Bulk intake'**; SA service-direct `bulk_create_rolls` with financials also landed
  (CR-000016, cost=77.10). Manager service-direct with cost → **PermissionDenied "Supplier and
  Cost Per KG require Accountant or Super Admin role"** (and same quote on `update_roll_details`
  with supplier).
- **Roll-edit financials LAND + history rows WRITTEN:** SA POST roll-21 edit (supplier
  'DEV OWNE Sup2', cost 250.00, weight 11.50) → flash **"Roll NKS-R4 updated."**, all three
  landed, **2 financial history rows written via the single-writer** (`('supplier','','DEV OWNE
  Sup2',actor=1)` + `('cost_per_kg','200.00','250.00',actor=1)`) + weight control row
  ('10.00'→'11.50').
- **Layer 3 (template):** SA roll-detail-21 renders new supplier + 250.00; SA roll-list renders
  Supplier column + values. Manager GETs same pages: both ABSENT (server-side, in-transaction).
- **Layer 4 (history strips):** SA sees the supplier-change event on ALL THREE time-log surfaces
  (roll-list · rm-dashboard · cloth-dashboard); manager sees NONE of them ×3 while the weight
  control event IS visible ×3 (exclude-filter precision, not a blanket hide).
- **Manager injection control (MGT-E re-proof, owner phase):** manager roll-edit POST with
  `supplier=HACK-SUPPLIER&cost_per_kg=999.99` → weight change SAVED, financials UNCHANGED,
  **0 financial history rows** (form popped the fields).
- **USED-roll guard holds for the owner too (BY DESIGN):** SA edit POST on roll-1 → refusal
  rendered ("Roll CR-000001 is in use. Detach from its Adda before editing." + service sibling
  "already in use"), roll-1 untouched. Classified: immutability-of-consumed-stock design
  (verified width/weight live on LayeringRollEntry), not an owner block.
- Post-rollback: roll-21 byte-identical (supplier='' cost=200.00 weight=10.00), history 40/0.

**Masters CRUD as SA (rollback-wrapped, flash quotes verbatim):** ClothType full round-trip —
create 'DEV OWNE Type' ("Cloth Type created.", 6→7) → rename ("Cloth Type updated.") → archive
POST ("DEV OWNE Type R archived.", is_active=False) → second archive POST restores ("… restored.",
is_active=True) → delete-confirm GET **200 (#5-class regression watch PASS)** → delete POST
("… deleted.", row gone, 6) · referenced-delete guard on Cotton(1) → **"Cannot delete — this
record is still referenced by other rows. Archive it instead."** + row survives
(ProtectedError→ValidationError path) · ClothColor + StorageLocation create→delete round-trips
landed ("Cloth Color created."/"Storage Location created." + "… deleted."). Post-rollback 6/15/3.

**Roll ops as SA (rollback-wrapped):** damage-21 → **"Roll NKS-R4 marked DAMAGED — out of
available stock; reason on the roll's history."** + status=damaged + history row
(status not_used→damaged, note "damaged: DEV OWNE damage probe") · restore-21 → "… restored to
available stock …" + not_used · no-reason POST → **"A reason is required to mark a roll
damaged."** (state unchanged) · damage USED roll-1 → **"This roll is already consumed by
production — record damage on the affected pieces/reports, not the roll."** · restore
non-damaged → **"Only a damaged roll can be restored."** · restore the real DAMAGED roll-36 →
landed (GLDN-R5 → not_used; rolled back to damaged). **Assign functional:** garbage adda code →
200 + form error "Adda matching query does not exist." rendered, ZERO writes; real assign
roll-21 → XFB-002 → **"Roll NKS-R4 assigned to XFB-002."** — status=used, adda=43, weight/width
stamped, used_by=1, **ClothRollHistory STATUS_CHANGED ('not_used'→'used', note "assigned to
XFB-002") + AddaHistory ROLL_ASSIGNED (adda 43, actor 1)** — both single-writer rows; rolled back
(roll-21 not_used/adda=None, AddaHistory 400 byte-identical).

**#7 owner-relevance check (charter carry-in) — VERDICT: stays INFO, owner-relevance ABSENT:**
as SA, archive-confirm GET with garbage pk → **500 on ALL THREE masters** (cloth-types/
cloth-colors/storage-locations 99999 — broadened census vs MGT-E's single-master repro; same
uncaught `DoesNotExist` in `_MasterArchiveView.get`); edit/delete siblings → 404 ×2; roll-detail
99999 → 404. **NOT owner-UI-reachable:** href census on the live ct-list page = archive links
render ONLY real pks ({1,2,3,4,17,18} exact match to table). Fails closed (no write, no leak).
Fix-when-touched spec unchanged (`get_object_or_404`); dated evidence note appended to backlog #7.

**Negative controls (Phase-1/worker-cert regression guard):** manager — bulk-add GET **403** +
POST **403** with roll count 32→32 (dispatch inertia); financial layers 1-4 manager-blocked
(above, in-transaction). Worker — 6 managed URLs (dashboards/roll-list/3 master lists) →
**302→my-dashboard ×6** (middleware) · bulk-add/roll-edit/roll-assign/ct-add/ct-delete →
**403 ×5** (mixin — two-layer defense visible in one matrix) · roll-detail-1 → **200 with ZERO
financial leak** (production-floor read, by design; 'Validation Supplier' absent from body) ·
POST ct-add → 403 zero rows · POST damage-21 → 403 state unchanged. **Zero regression on any
closed certification.**

**Browser as owner on :8003 (persisted OWN-D session verified live — navbar
`umesh29mar@gmail.com`; no fresh login needed, zero rate-limit exposure):** sidebar renders Raw
Materials ×6 + Administration ×6; rm-dashboard renders with the SA-only "+ Add Cloth Rolls" CTA;
cloth dashboard splits **32 total / 2 available / 29 used / 1 damaged** (V1.1 damage-visibility
posture intact); roll-list renders Supplier + Cost/KG columns with values; roll-detail CR-000001
renders SUPPLIER 'Validation Supplier' + COST/KG ₹200.00 (screenshot); bulk-add form renders
supplier + cost_per_kg inputs (forms census: 8 fields incl. both + csrfmiddlewaretoken;
screenshot); **CSRF-valid master write round-trip via real forms: ClothType 'DEV OWNE Browser'
created ("Cloth Type created.", DB pk=25) → delete-confirm page renders "Permanently delete DEV
OWNE Browser?" + Cancel + Delete Permanently (#5-class watch PASS) → deleted ("DEV OWNE Browser
deleted.") → DB residue ZERO, count 6.** Screenshots: owne_bulkadd / owne_delete_confirm /
owne_roll1_financials .png (session scratchpad). **Deliberate containment (§4):** bulk-add SAVE
and roll-edit SAVE not clicked in the browser — bulk intake has NO reverse path from the UI
(rolls + sequence + CREATED history are permanent by design) and roll-edit financials would need
a manual counter-edit; both write paths fully proven rollback-wrapped in shell instead
(MGT-D/OWN-D containment precedent).

**New INFO → backlog #12:** rm-dashboard index tile lumps DAMAGED into "Used" (tile arithmetic =
`total - available` → shows "30 Used" while truth is 29 used + 1 damaged; browser-proven).
Display-only, zero permission/money impact; the canonical cloth dashboard one click deeper splits
damaged correctly (V1.1 item-1 posture intact). Out of OWN-E fix mandate (no confirmed
owner-visibility/functional defect).

**Prior-fix guards touched:** #5-class delete-confirm (rendered ×3 masters shell + browser
round-trip) ✓ · BUG-E1-class master-write role gates re-proven (worker 403s + manager positives
implicit in MGT-E, SA positives here) ✓ · M9 roll-edit lineage (ManagementRoleMixin + service
re-gate) re-proven with SA driving ✓.

**Disclosed artifacts (U13):** all probe writes rolled back byte-identically (rolls 32 · types 6 ·
colors 15 · locations 3 · ClothRollHistory 40 · AddaHistory 400 · roll-1/21/36 field-exact;
DB-wide financial history rows back to 0; DEV OWNE residue 0); **`cloth_roll_seq` advanced
12→16** (Postgres sequences don't roll back — 4 roll_ids CR-000013…16 consumed, same class as
pk-gap disclosure) + master/roll pk auto-increment gaps consumed by rolled-back/deleted rows
(incl. browser round-trip ClothType pk=25 create+delete); browser probes reused the persisted
owner session (no new login rows); pk=1 password/email/role/flags untouched (§16.5 clean).

**Close-out:** 0 confirmed bugs → 0 fixes → 0 pins → **battery NOT re-run (canonical baseline
1530/1530 stands)**. Docs-sync: this section + status file + backlog (#12 new row + #7 dated
evidence note) + memory; app GUIDE/README untouched (no code change — U6 N/A). **Next: OWN-F**
(Machines + Storefront-as-SA first functional cert + Accounts admin CRUD + /admin/ staff wall;
owner-gated).

## OWN-F — Machines + Storefront-as-SA (first functional cert) + Accounts admin CRUD + /admin/ staff wall (2026-07-13) ✅

**Verdict: 0 bugs · 0 false owner blocks · 0 code changes · battery NOT re-run (1530/1530
stands) · 0 new INFO (#8 re-noted, stays INFO) · every probe rolled back byte-identically ·
pk=1 byte-identical after every self-guard probe (§16.5 clean).**

**Preconditions (§17.4):** HEAD `49404001` exact; 311 dirty paths (stable vs OWN-E close).
Identities verified read-only (pk=1 SA active/su/staff · dev.mgr 52 · dev.ow.a 46 ·
dev.listing 62). **Probe anchors:** machines **4** (OL-001/FL-001/SN-001/EL-001, all active) ·
MachineAssignment **5 total / 2 open** (FL-001→dev.flat.a · OL-001→dev.ow.a; +1 vs the MGT-F
"4" baseline = the DISCLOSED MGT-F browser artifact — closed EL-001→dev.ow.a possession window,
drift explained, re-anchored) · FeaturedProduct **1** / Category **1** · User **47** / Skill
**10** / UserType **5** / Role **5** — all exact. EL-001 + SN-001 free (assign targets).

**Gate-map audit (owner-angle, step 2):** machines ×5 = `_ManagementOnly`
(`user_has_role(MANAGEMENT_ROLES)` — SA admitted by role-code + is_superuser independently;
assign/release POST-only `View`) · storefront ×8 = `ListingTeamMixin`
(`user_has_role({ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM})` — **SA is a designed member of
STOREFRONT_ROLES**; the 2 list URLs additionally managed SidebarItemRule roles=[Listing Team] —
SA-implicit middleware bypass precedes rule lookup, OWN-D lineage) · accounts admin trio ×12 =
`SuperuserRequiredMixin` (`user_has_role({ROLE_SUPER_ADMIN})` — role-code path, NOT raw
is_superuser; charter gate-gap flag satisfied: both resolution paths admit pk=1) + Administration
double-gate on the 2 managed lists · S2 = `RestrictedAccountAdapter.is_open_for_signup=False`
(all users) · S3 = `EmailManagementDisabledView` shadow-mounted before allauth (urls.py:28, all
users) · `/admin/` = Django staff wall (`is_staff` — pk=1 True). **No gate gap for the SA class
on any OWN-F surface.**

**Shell GET matrix as owner: 25× 200 + 2× 405 + designed 302s.** 200s: machines
list/add/edit-1 · storefront products+categories list/add/edit-1/delete-confirm-1 ×2 models ·
accounts users/skills/user-types list/add/edit/delete-confirm ×3 models · forgot-password ·
**`/admin/` → 200 (owner INSIDE the staff wall)**. 405s: assign/release GETs (POST-only,
correct). Designed 302s (classified, not blocks): login + login-password → /app/home/
(`redirect_authenticated_user`) · home → /production/ (P1-1 landing) · signup → /app/home/
(allauth redirects an AUTHENTICATED user before the closed page; anon control below) ·
email-mgmt → /app/home/ (S3 wall). **Zero 500s, zero false owner blocks.**

**Machines as SA (rollback-wrapped, flash quotes verbatim):** create → **"Machine DEV-OWNF-M1
created."** (4→5) · duplicate code EL-001 → form error "already exists.", no row ·
**MGT-F-1 re-proven with the owner driving**: rename OL-001 (3 assignment-history rows) →
**"Machine code is immutable once the machine has assignment history (floor labels reference
it). Create a new machine instead."** + DB code unchanged; lowercase dup `el-001` → "already
exists." (iexact live); no-history rename → landed ("Machine DEV-OWNF-M2 updated.") · assign
EL-001→dev.ow.a → **"EL-001 assigned to DEV-OW-A."** (open window created) · double-assign →
**"EL-001 is currently with DEV-OW-A (since 13 Jul 04:18). Release it first."**, zero rows ·
release → "EL-001 released." + end_at set · re-release → **404** (fails closed) · assign on
MAINTENANCE machine → **"DEV-OWNF-M2 is Maintenance — set it Active before assigning."**, zero
rows. **#8 owner-relevance note:** garbage `worker=abc` hand-crafted POST as SA → same 500
(uncaught ValueError) — identical to the MGT-F facet, no new owner-workflow defect, **stays
INFO** (dated note on backlog row #8). Post-rollback 4/5/5 + OL-001 exact.

**Storefront as SA — FIRST functional certification of the editor (rollback-wrapped):**
category create → **'Category "DEV OWNF Cat" created.'** (1→2, no image — blank=True, zero
media artifacts) · edit → '… updated.' (name+subtitle landed) · product create with FK to the
new category → **'Product "DEV OWNF Product" created.'** (badge=new, price=99.00) · edit →
'… updated.' (price 120.50, badge=hot landed) · delete-confirm GETs **200 ×2** (#5-class watch
PASS) · deletes → '… deleted.' ×2, rows gone · existing pk=1 FeaturedProduct/Category intact.
Post-rollback 1/1. **The owner can run the storefront end-to-end — SA ∈ STOREFRONT_ROLES is
FUNCTIONAL, not just a 200.**

**Accounts admin CRUD as SA (rollback-wrapped):** user create → **"User dev.ownf.probe@test.local
created."** (47→48, role=worker, active) · duplicate email case-insensitive
(`DEV.OWNF.PROBE@…`) → "already exists.", no row · edit → "User updated successfully."
(first_name landed) · delete-confirm GET 200 · delete → "User deleted successfully." (row gone,
47). **Owner self-guards, live with pk=1 (guards refuse BEFORE save; §16.5 clean):**
self-delete → **"You cannot delete your own account."** · self-deactivate →
**"Refused: you cannot deactivate your own account while editing your own profile. Ask another
Super Admin to do it."** · self-demote-superuser → **"Refused: you cannot revoke your own
superuser flag while editing your own profile. Ask another Super Admin to do it."** — pk=1
byte-identical after all three (email/flags/role/password compared). Last-admin delete refusal
("only active Super Admin") NOT live-triggerable while pk=1 is the sole active admin (the guard's
own precondition) — covered by existing accounts pins (tests.py `delete_user`/`self_edit_blockers`
suite), classified, not skipped silently. Skill CRUD → "Skill added."/"Skill updated."/"Skill
deleted." (round-trip, 10→11→10) · UserType CRUD → "User type 'OWNF UT' created."/updated/
deleted (5→6→5).

**S2 + S3 hold for the owner too (universal walls):** S2 — **anon GET /accounts/signup/ → 200
closed page** + anon POST → user delta 0; authenticated-SA GET → 302 home (allauth authed
redirect, classified BY DESIGN) + SA POST → 302, **user delta 0** (no creation path for anyone).
S3 — SA GET /accounts/email/ → bounced to /production/ + flash **"Your email address is managed
by your administrator."**; SA POST action_add `evil-ownf@example.com` → 302, **pk=1 email
unchanged, zero EmailAddress rows** — the wall holds even for the owner, exactly as designed.

**/admin/ staff wall from inside:** owner GET /admin/ → **200 "Django administration / Site
administration"** (shell + browser) · manager + worker → **302 /admin/login/?next=/admin/ ×2**
(wall intact from outside). Sampled admin CRUD deliberately deferred to OWN-G per §7 (django-admin
sample = OWN-G scope).

**Negative controls (regression guard):** manager — machines list **200 = BY DESIGN**
(management surface, MGT-F certified) · storefront list 302→my-dashboard + add 403 · users
302 + user-types 403 + user-add 403 · POSTs skill-add/category-add → 403 ×2 inert. Worker —
machines 403 · storefront 302/403 · accounts 302/403 ×4 · POSTs user-add/machine-assign → 403 ×2
inert. Listing-team — storefront products **200 (positive control holds)** · machines **403**.
All deltas zero. **Zero regression on any closed certification.**

**Browser as owner on :8003 (persisted session verified in navbar; zero login attempts):**
machines register renders (counts strip Total 4 / Active 4 / Maintenance 0 / Assigned now 2;
EL-001 + SN-001 "— free", FL-001/OL-001 holder chips; screenshot ownf_machines.png) ·
storefront Featured Products + Categories pages render with the sidebar showing the Storefront
section (SA sees it; manager never does — MGT-F) · Team Members renders · **/admin/ renders
"Django administration / Site administration" live** · **CSRF-valid storefront write round-trip
via real forms: category 'DEV OWNF Browser Cat' created ('Category "DEV OWNF Browser Cat"
created.', DB pk=4) → delete-confirm renders "Delete this category? … permanently delete: DEV
OWNF Browser Cat" (screenshot ownf_sf_delete_confirm.png) → "Yes, Delete Category" → deleted,
DB residue ZERO (count 1)**. Deliberate containment (§4): machines assign/release + accounts
user-create NOT browser-driven (possession windows are append-only history; user rows carry
credentials) — both fully proven rollback-wrapped in shell (MGT-F browser precedent already
covers the assign widget itself).

**Prior-fix guards touched:** MGT-F-1 machine-code immutability re-proven with SA driving
(exact error + DB unchanged) ✓ · S2 signup-closed (anon + SA, POST-inert both) ✓ · S3
email-shadow (SA bounced + POST-inert) ✓ · #5-class delete-confirm pages render across
storefront ×2 + accounts ×3 surfaces (shell) + browser category confirm ✓.

**Disclosed artifacts (U13):** all probe writes rolled back byte-identically (User 47 · Skill 10 ·
UserType 5 · Role 5 · FeaturedProduct 1 · Category 1 · Machine 4 · MachineAssignment 5/2-open ·
pk=1 field-exact · zero OWNF residue, recounted after every block); auto-increment pk gaps
consumed by rolled-back/deleted rows (User 75 · Skill 14 · UserType 9 · Category 3-4 incl.
browser round-trip create+delete · FeaturedProduct 2 · Machine 10 · MachineAssignment 19);
browser reused the persisted owner session (no new login rows); anchor drift MA 4→5 documented
above (MGT-F disclosed artifact, not this session's).

**Close-out:** 0 confirmed bugs → 0 fixes → 0 pins → **battery NOT re-run (canonical baseline
1530/1530 stands)**. Docs-sync: this section + status file + backlog #8 dated note + memory;
app GUIDEs/READMEs untouched (no code change — U6 N/A). **Next: OWN-G** (patterns_ai as SA —
blueprint perm gate + write path · route sweep SA-positive · exports · django-admin sampled CRUD
on a low-risk model rollback-wrapped · #9 noted only; owner-gated).

## OWN-G — patterns_ai as SA: blueprint gate + write path, route sweep, exports, django-admin sample (2026-07-13) ✅

**Verdict: 0 bugs · 0 false owner blocks · 0 code changes · battery NOT re-run (1530/1530
stands) · 0 new INFO (#9 re-noted, evidence unchanged, stays INFO) · every probe rolled back
byte-identically.**

**Preconditions (§17.4):** HEAD `49404001` exact. Identities verified read-only (pk=1 SA ·
dev.mgr 52 · dev.ow.a 46). **Probe anchors EXACT vs the MGT-G baseline:** MRK-000002 exists
(markers 3) · MarkerUsage **1 (unvoided)** · MarkerOutcome **1** · CalibrationMat **2**
(MAT-DEV-01/02 active) · pieces 58 / versions 36 / runs 23 / candidates 28 / geometry
extractions 11 · DEV-NICKAR product pk=23 (cutting-table anchor re-found; the similarly-named
'DEV Nickar Big' NKB = pk 24 is a DIFFERENT product — both probed below).

**Gate-map audit (owner-angle, step 2 — MGT-G G0 law re-read):** every route
`LoginRequiredMixin + _ManagementOnly` (MANAGEMENT_ROLES — SA admitted) · ONE stricter gate =
`PatternBlueprintView` (`user_has_perm('production.change_productpattern')` — **SA bypass step 1
of user_has_perm**; manager with 0 Django perms blocked) · services re-gate writes
(`_ensure_management`/`_gate`) · `patterns_ai:home` = managed SidebarItemRule roles=[Manager,
Super Admin] · per-manager ownership DOES NOT EXIST BY DESIGN (product-anchored factory memory,
PLATFORM_STATUS §3 frozen). **No gate gap for the SA class on any patterns_ai route.**

**Shell route sweep as owner: 25× 200 + 2 designed 302s, zero 500s, zero false blocks** — home ·
dashboard · blueprint picker + ?product=24 · studio · studio-work(piece 1 × size 14) ·
studio-evidence-count · marker-list · yield-board · manual-marker-new · marker-detail MRK-000002 ·
usage-new form · outcome-new form · mat-list/new/detail-1 · piece-list/detail · version-detail ·
generate · run-detail-23 · candidate-detail-28 · advisor · insights · workspace(candidate).
302s classified: `tool/24` → studio (M4 smart-redirect, docstring-cited BY DESIGN) ·
`table/24` → dashboard with honest flash **"Digital Cutting Table is locked — no size is ready
yet. Finish the required designs of at least one size."** (designed ready-gate; NOT a block —
positive control: **cutting-table 200 as SA on READY products pk=18 Classic Crew Neck T-Shirt
AND pk=23 DEV-NICKAR — the exact MGT-G anchor re-proven**).

**Exports as SA (content-type proven ×6):** candidate-svg `image/svg+xml` · candidate-pdf
`application/pdf` · candidate-print `text/html` · geometry-svg `image/svg+xml` · geometry-dxf
`application/dxf` · geometry-print `text/html` — all 200.

**Blueprint gate + WRITE PATH (the OWN-G headline, rollback-wrapped):** manager GET → **403** ·
manager add-POST → **403** (piece count unchanged) · SA GET → 200 (picker + per-product view) ·
**SA write LANDED:** POST `action=add` product=24 → flash **'"DEV OWNG Piece" added to the
Blueprint.'** — PatternPiece 58→59 + ProductPattern assignment 60→61 created through
`register_pattern_definition` (the single writer, parse→gate→delegate). Post-rollback 58/60.

**SA functional write chain (rollback-wrapped, owner stamps verified):** fresh usage on
MRK-000002 × LOWER-002 → **"Usage recorded for MRK-000002 on LOWER-002."** (pk=3,
`confirmed_by=umesh29mar` — TRUE-actor stamp, plies=10; first probe with a non-product Adda →
**404 BY DESIGN**, D11 own-adda rule `get_object_or_404(Adda, product=m.product)`) → outcome on
the fresh usage → **"Outcome recorded — 31.00 m per 100 garments (derived, not stored)."**
(`recorded_by=umesh29mar`) → void → **"Usage voided — kept in history."** (voided_at set).
Designed refusals verbatim: second outcome on usage-1 → **"An outcome already exists for this
usage — facts never change; void the usage and re-record if it was wrong."** (OneToOne law) ·
void of usage-1 → landed + reason stored + original confirmed_by preserved (append-only F2).
Mat lifecycle: register `mat-dev-owng` → **"Mat mat-dev-owng registered — commission it before
first use."** (`created_by=umesh29mar`, status=uncommissioned) → retire → **"Mat mat-dev-owng
retired."** (status=retired + reason). **#9 re-noted, evidence UNCHANGED: `voided_by` column
still absent on MarkerUsage, retire actor still uncaptured — both paths functional and
reason-mandatory; stays INFO (no material change, no re-evaluation trigger).**

**django-admin sampled CRUD (low-risk model = accounts.Skill, rollback-wrapped):** changelist
GET 200 · add form GET 200 · **add POST → row landed (pk=15, 10→11)** · change POST → label
renamed · delete POST (confirm `post=yes`) → row gone, count 10. The owner can operate the raw
Django admin end-to-end (is_staff wall from inside, functional — extends the OWN-F 200-render
proof to writes).

**Negative controls:** worker — home → 302→my-dashboard (managed rule) · marker-list/
marker-detail/mat-detail/candidate-svg/candidate-pdf → **403 ×5** · void + mat-new POSTs →
**403 ×2, zero writes**. Manager — blueprint GET+POST 403 ×2 (the perm seam holds; everything
else manager-positive = MGT-G certified, unchanged). **Zero regression.**

**Browser as owner on :8003 (persisted session, navbar-verified, zero logins):** Pattern
Blueprint renders the product picker ("Pick a product to define its garment structure" — 1-6 ·
3-PATTI · DEV-HUB · DEV-NICKAR · LOWER …; screenshot owng_blueprint.png) — the SA-only surface
live (manager gets the branded 403, MGT-G browser evidence) · Pattern Dashboard renders ·
`/admin/accounts/skill/` changelist renders inside Django administration. Deliberate containment
(§4): blueprint add + usage/mat writes NOT browser-driven (knowledge rows have no UI delete
path — append-only design); all write paths shell-proven rollback-wrapped above.

**Prior-fix/wall guards touched:** blueprint perm-split (mgr 403 / SA 200) re-proven both ways ✓ ·
MGT-G enumeration fail-closed posture unchanged (D11 404 observed) ✓ · worker wall ×8 class ✓.

**Disclosed artifacts (U13):** all probe writes rolled back byte-identically (usages 1/unvoided 1 ·
outcomes 1 · mats 2 · pieces 58 · assignments 60 · skills 10 — recounted); zero OWNG residue;
auto-increment pk gaps consumed (MarkerUsage 3 · MarkerOutcome 2 · CalibrationMat 4 ·
PatternPiece 59 · Skill 15); browser reused the persisted owner session (no new login rows);
pk=1 untouched (§16.5 clean).

**Close-out:** 0 confirmed bugs → 0 fixes → 0 pins → **battery NOT re-run (canonical baseline
1530/1530 stands)**. Docs-sync: this section + status file + memory; backlog untouched (#9 note
lives here — no material change); app README untouched (no code change — U6 N/A; patterns_ai
README drift already pre-logged for KOS phases 6-7). **Next: OWN-H** (meta-audit + close:
SA-perspective route census with anomaly rules · rendered sidebar vs matrix · gate-gap audit ·
carry-in disposition review · FINAL PHASE VERDICT; owner-gated).

## OWN-H — Meta-audit + close (2026-07-13) ✅ — PHASE 2 VERDICT: CERTIFIED

> Not a summary of OWN-A..G — fresh system-level instruments: full-root-URLConf SA-perspective
> census, a dynamic owner sweep with anomaly rules, the rendered-sidebar-vs-matrix check, the
> charter's gate-gap audit, and the carry-in disposition review. 0 code changes; sweep
> rollback-wrapped.

**Preconditions:** HEAD `49404001` exact · 311 dirty paths (stable since OWN-E) · battery
**1530/1530** stands (no code change since OWN-D) · identities verified read-only.

### H1 — SA-perspective static census (whole root URLConf)

Programmatic walk of `get_resolver().url_patterns`: **528 total routes — EXACTLY the MGT-H
number; zero routes added/removed by the entire Phase 2** (the two Phase-2 fixes were
validation-queryset/service-internal — no URL surface change). Every route classified by
strongest dispatch gate (CBV MRO scan): SuperAdminOnly 12 · SuperuserRequired 12 ·
_SuperAdminOnly 2 · _StagePermissionRequired 10 · _PatternPermissionRequired 4 · blueprint
UserPassesTestMixin 1 · _ManagementOnly 68 · ManagementRoleMixin 20 · ManagerOrAdmin 5 ·
ProductionRole 65 · ListingTeam 8 · LoginRequired-only 7 + auth-flow CBVs 9 + function-views 9
(inventory redirects/scan/public_home) · django-admin 274 (+ admin auth 3 counted in the walk)
· allauth 22. **Every gate class admits the SA role** (role-code sets containing SA, Django-perm
seams with the double SA path, or staff wall pk=1 passes) — no unknown/unclassified gate exists.
SidebarItemRule join: 21 rows, 6 Administration rules roles=[] (double-gate posture intact).

**Census correction (narrative precision, MGT-G-corroborated):** rule pk=23 (`patterns_ai:home`,
updated 2026-07-06 — freeze era) stores roles **[manager, super_admin]**. MGT-G documented
exactly this ("managed SidebarItemRule roles=[Manager, Super Admin]"); OWN-D's blanket line
"no rule row stores super_admin" was over-broad (its own numeric census — 6 Administration rules
roles=[] — was correct; the OWN-D bulk-POST probe would have stripped rule 23's SA via the
editor's force-exclude, and that write was rolled back to the seeded state). **Functional impact
ZERO:** `can_access_url_name` returns True for SA BEFORE any rule lookup, so a stored super_admin
is inert redundancy; the lockout-proof design (bypass precedes lookup + editor strips SA on
save) is unaffected; the OWN-D live-flip/rollback/fix proofs stand. Dated correction recorded
here per the append-only evidence rule; reported to the owner in the OWN-H close report.

### H2 — dynamic owner sweep (anomaly rules: SA 403 / SA 302-bounce / SA 500 = anomaly)

All **96 no-arg non-admin routes** GET as the owner inside one forced-rollback atomic:
**82× 200 · 8× enumerated designed 302** (authed login/login-password redirects · home role
landing · verify-otp no-session bounce · logout POST-only law · S3 email shadow · S2
authed-signup redirect · inventory dashboard hop) · **6× additional 302s ALL classified benign
redirect hops** (allauth login→home / password-set→change / social-signup→login ·
resend-otp→login no-session · inventory legacy my-dashboard hop ×2) · **ZERO 403 · ZERO 500 ·
ZERO unexplained bounce.** django-admin sampled as owner: index + skill/user changelists 200 ·
admin login → 302 index (already-authed staff) · admin logout GET 405 (POST-only, correct).
Arg-bearing routes: covered by the OWN-A..G per-app matrices (100+ URL probes with live pks
across production/expense/inventory/tracking/raw_materials/machines/storefront/accounts/
patterns_ai); enumerated designed arg-route non-200s for SA: worker-report 403 (D6 own-task) ·
product-patterns entry 302 (Phase-1 D-2) · tool smart-redirect · cutting-table ready-gate ·
barcode/stage designed refusals — every one carries its design citation in its sub-phase section.

### H3 — rendered sidebar as SA vs matrix

Live sidebar as owner (shell parse + browser screenshot ownh_sidebar_sa.png): **28 distinct
links across ALL sections** — Main 2 · Production 7 (incl. Machines + Pattern Intelligence) ·
Raw Materials 6 · Storefront 2 · Tracking 1 · Payroll 4 · **Administration 6** — and **28/28
fetch 200 as SA** (SA-sees-everything predicate live; manager sees 19 links and no
Administration/Storefront — MGT-H baseline unchanged). Matrix join: 19/21 managed rules render
as menu items; the 2 non-rendered rules (`inventory:inventory_dashboard` ·
`inventory:user_dashboard` legacy) are REDIRECT-stub rules not rendered for ANY role (both 302
to my-dashboard; MGT-H's manager count 19/19-visible implies the same posture) — **BY DESIGN**,
not an SA-visibility gap.

### H4 — gate-gap audit: user_has_role vs is_superuser vs is_staff (charter flag)

- **Zero raw `is_superuser` gates in views** (grep-proven; hits = an access-hub display column,
  comments citing rule 6, and the UserEditForm field name). Rule 6 holds project-wide.
- **Zero `is_staff` checks outside django-admin** — the AdminSite staff wall is the ONLY
  is_staff-gated surface.
- Resolution law: `user_role_code` = is_superuser-first → role.code; `user_has_perm` = superuser
  grant-all + role-codename path; `user_service._is_admin` = is_superuser OR SA-role
  (deliberately dual — admin-set invariants can't diverge; race-safe advisory lock).
- **Seam analysis for a FUTURE second admin:** an SA-role account WITHOUT is_superuser is
  admitted by every project gate (role-code path) and by user_has_perm (role-codename branch) —
  it would lack ONLY `/admin/` (Django's own is_staff wall — set is_staff when provisioning) and
  the Django built-in grant-all (perm-seam views still admit via the role branch, OWN-A/D-proven).
  An is_superuser account without the SA role resolves to super_admin at step 1 everywhere.
  **No project surface falls between the three flag systems.**
- **Flag-alignment census re-run at close:** exactly ONE owner-class account in data (pk=1,
  active, role=super_admin ∧ is_superuser ∧ is_staff — all aligned); the divergence class
  remains EMPTY.

### H5 — carry-in disposition review (charter table, final)

| Carry-in | Final disposition |
|---|---|
| **RoleForm.permissions queryset (PRIMARY MANDATE)** | **JUDGED OWN-D: CONFIRMED DEFECT → FIXED (OWN-D-1)** — queryset ← curated `permissions_qs_by_app()`; 2 pins; battery 1530. CLOSED |
| Backlog #6 RBAC.md role-table drift | Consulted as unreliable-expectation input only; unchanged; **stays with KOS phase 7** |
| Backlog #7 archive-confirm garbage-pk 500 | **OWN-E: owner-relevance ABSENT** (SA 500 all-3-masters; href census = not owner-UI-reachable) — stays INFO, dated note on row |
| Backlog #8 MachineAssignView worker param | **OWN-F: same 500 as SA, no new owner-workflow facet** — stays INFO, dated note on row |
| Backlog #9 patterns_ai actor stamps | **OWN-G: evidence unchanged** (columns still absent, paths functional, reason-mandatory) — stays INFO |
| /media/<path> login-tier | Out of scope (owner Option 1) — untouched |
| OTP-send POSTs | NOT probed (EMAIL_BACKEND may be real SMTP) — **disclosed limitation**, same as MGT-F; gates covered by renders + throttle pins |

### H6 — Phase-2 findings cross-check (OWN-A..G ledger)

| Sub-phase | Bugs | Fixes | Pins | Battery | INFO |
|---|---|---|---|---|---|
| OWN-A | 0 | 0 | 0 | 1526 stands | — |
| OWN-B | 0 | 0 | 0 | 1526 stands | #10 (string-compare flash, proven inert) |
| OWN-C | **1 (OWN-C-1** recon-evidence FK lane collapse**)** | 1 | 2 | **1528/1528** | #11 (a360 badge collapse, display-only) |
| OWN-D | **1 (OWN-D-1** = THE carry-in**)** | 1 | 2 | **1530/1530** | — |
| OWN-E | 0 | 0 | 0 | stands | #12 (index tile damaged-lump, display-only) |
| OWN-F | 0 | 0 | 0 | stands | — (#8 dated note) |
| OWN-G | 0 | 0 | 0 | stands | — (#9 re-note) |
| OWN-H | 0 | 0 | 0 | stands | — (rule-23 narrative correction, functional impact zero) |

Arithmetic verified: 1526 + 2 (OWN-C-1) + 2 (OWN-D-1) = **1530** ✓. Prior-fix guard list (§14)
fully touched with the owner driving: BUG-1/2/3 surfaces (OWN-B workspaces/allocation) · BUG-E1
(OWN-E masters) · S2 + S3 (OWN-F, anon + SA) · MGT-B-1 (OWN-B, shell + browser) · #5-class
delete-confirm (OWN-A/D/E/F, shell + browser ×4 apps) · MGT-F-1 (OWN-F, SA driving). Money
probes: ledger integrity re-proven after every OWN-C block (Money-Write STOP rule never
triggered; the one single-writer touch = the confirmed OWN-C-1 defect, U8-reviewed in place).

### H7 — success criteria (§3) verified

1. OWN-A..H evidence sections appended ✓ · 2. **Zero unexplained owner blocks** — every
403/302/405/500 classified BY DESIGN with citation or FIXED with pins ✓ · 3. Every §7 SA-only
operation proven FUNCTIONAL by a landed write ✓ (flow editor · rerate · C3 override · 4 money
levers incl. a real M-6 recon-override · roles + sidebar editors · bulk-add financials ·
storefront editor · machines lifecycle · accounts CRUD · blueprint · django-admin CRUD) ·
4. Carry-in verdict = CONFIRMED-FIXED ✓ · 5. Manager + worker negative controls held on every
SA-only surface ✓ · 6. Battery green at final baseline (1526 + 4 pins = 1530, sequential
fresh-DB; re-run only when code changed) ✓ · 7. OWN-H verdict from fresh instruments ✓ ·
8. Status/backlog/memory synced at every close ✓.

### FINAL VERDICT

**PHASE 2 — OWNER VISIBILITY CERTIFICATION: CERTIFIED. The phase is CLOSED.**
The owner reaches every designed surface with zero false blocks; every owner-only operation is
functional end-to-end (proven by landed writes, not renders); the universal walls hold even for
the owner; both confirmed defects found by the phase are fixed and pinned; battery
**1530/1530 GREEN**. Remaining INFO residue: backlog #6 (doc drift → KOS phase 7) · #7 · #8 ·
#9 · #10 · #11 · #12 — all evidence-judged non-exploitable, fix-when-touched.
**Next: Phase 3 — Office/Support Role Certification (OFF-0 charter, gated on owner Design
Record D1–D4 per its contract §17).**
