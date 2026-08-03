---
id: docs-campaign-contracts-phase-02-owner-visibility
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 2 Execution Contract — Owner Visibility Certification

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) — this contract only adds phase specifics and tightenings.
> Charter + evidence doc: [../OWNER_VISIBILITY_CERTIFICATION.md](../OWNER_VISIBILITY_CERTIFICATION.md)
> (OWN-0 already closed 2026-07-12; this contract governs OWN-A..OWN-H).
> Predecessor method precedent: [../MANAGEMENT_ROLE_CERTIFICATION.md](../MANAGEMENT_ROLE_CERTIFICATION.md).

## 1. Phase objective

Certify the `super_admin` / Owner role across the entire ERP. NOT "can the owner access
everything" — the six real questions: (1) owner reaches every expected surface; (2) no surface
falsely blocks the owner; (3) every owner-ONLY operation actually works end-to-end (these writes
have never been exercised by any prior certification — only 200-GET positive controls); (4) no
manager-only / shared-management assumption accidentally excludes the SA role; (5) hidden
owner-only bugs (the MGT-B-1/#5 class: crashes inside surfaces only one role ever exercises) are
found; (6) every Worker-cert and Management-cert fix still works with the owner driving.

## 2. Scope

**In:** all 9 URL-bearing apps (production, expense, inventory+tracking, raw_materials, machines,
storefront, accounts, patterns_ai) + django-admin `/admin/` — probed AS the owner identity, three
axes (§5 of the charter): zero-false-blocks · SA-only-ops-functional · universal-walls-hold.
Includes the deferred carry-in: **`RoleForm.permissions` queryset vs curated allowlist** (worker-cert
Phase-D INFO, explicitly deferred to this phase; judged in OWN-D).

**Out:** any refactor; backlog items #1/#3/#4 (infra/polish); #6 (doc drift — KOS phase 7);
#7/#8/#9 unless this certification upgrades one to a confirmed owner-workflow defect;
`/media/<path>` login-tier (owner Option 1 accepted); OTP-send POSTs (real-SMTP risk);
KOS/docs work; deployment work.

## 3. Success criteria

Phase 2 is DONE when ALL hold:
1. OWN-A..OWN-H each closed with an appended evidence section in OWNER_VISIBILITY_CERTIFICATION.md
   meeting the evidence standard (§5).
2. Zero unexplained owner blocks: every 403/302/405/500 the owner receives is classified
   BY DESIGN (universal wall) with the design citation, or FIXED with pin + battery.
3. Every SA-only operation on the OWN-A..G target lists proven FUNCTIONAL by a real write
   (rollback-wrapped shell or DEV-marked browser) with DB before/after.
4. The RoleForm.permissions carry-in carries a final evidence-based verdict
   (CONFIRMED-FIXED / BY DESIGN / INFO-with-proof).
5. Negative controls hold: manager AND worker remain blocked on every SA-only surface probed
   (Phase-1/worker-cert regression guard).
6. Battery green at final baseline (1526 + any new pins), sequential fresh-DB, only re-run if
   code changed.
7. OWN-H meta-audit delivers the phase verdict (CERTIFIED or CERTIFIED-WITH-FINDINGS) from fresh
   system-level instruments, not a summary.
8. Status file + backlog + memory synced at every sub-phase close.

## 4. Rules of engagement (deltas beyond U1–U14)

- Fix mandate per sub-phase = ONLY bugs confirmed inside that sub-phase's scope (MGT-E precedent:
  even a pre-confirmed backlog row needs its named sub-phase).
- The owner account (pk=1) is the REAL owner login. Browser probes must not change its password,
  email, role, or flags. Destructive-looking UI flows (deletes, voids, FnF) run rollback-wrapped
  in shell first; browser-drive only DEV-marked, reversible instances.
- FnF and pay-basis probes target DEV workers only (worker-cert cast: `dev.*@test.local`), never
  a real worker row.
- If a needed probe cannot be contained (no rollback path, real side effect), record it as a
  DISCLOSED LIMITATION in the evidence section instead of running it (MGT-F OTP precedent).

## 5. Evidence standard

Unchanged from Phase 1 (charter §"Evidence standard"): per-URL status matrix shell + browser ·
exact flash/error quotes · CSRF-valid POSTs with DB re-check · rollback-wrapped shell writes with
before/after counts · negative controls (manager + worker) on every SA-only surface · positive
functional proof = the write LANDED (row created/changed) then rolled back or disclosed.
Money sub-phase (OWN-C) additionally: ledger-integrity recount after every rollback-wrapped block
(re-baseline row-count/Σ at sub-phase start — the MGT-C values 170/₹10880.25 are point-in-time,
NOT eternal constants). Sub-agent findings supplemental (U7). Main-thread for money + verdicts.

## 6. Methodology (per sub-phase — the locked 10 steps)

1. Read the app's docs + `urls.py`. 2. Gate-map audit per URL, owner-angle: WHICH check admits SA
(`user_has_role({ROLE_SUPER_ADMIN})` vs `is_superuser` vs Django perm vs `is_staff` vs
SidebarItemRule) — and could any future SA-role account fall between them? 3. Shell probes as
owner via Django test client — GET matrix first, then rollback-wrapped writes (wrap in
`transaction.atomic` + forced rollback; verify post-rollback counts byte-identical). 4. Browser
on :8003 as `umesh29mar@gmail.com` — real navigation, real forms, CSRF-valid POSTs, DEV-marked
data only. 5. Fix ONLY confirmed bugs (smallest change; U14 migration stop). 6. Pins only for
fixes, in the app's existing certification test module. 7. Battery per U5 only if code changed.
8. Docs-sync per §11. 9. Status file + memory per §11/§12. 10. STOP (U3).

## 7. Sub-phase breakdown

Status lives in the status file + charter table; this is the procedure map.

| # | Scope | Probe targets (verify still exist at session start) | Key SA-only functional writes to prove |
|---|---|---|---|
| OWN-A | Production 1/2 — master-data engine | products (18 at Phase-1 close) incl. pk=5; pattern library (60 ProductPattern); stages (23), categories (5), machine-types (5); stage-rates on a completed DEV Adda | product add/edit/archive/sizes; **flow editor save**; pattern CRUD ×4; stage/category/machine-type CRUD; **`rerate_stage_role`** (S1.1: per (stage_record, role) lock, auto-recalc, `RateCorrectionAudit` row) |
| OWN-B | Production 2/2 — stage operations as SA | LOWER-002 (full flow, `elastic_attach` open) + XFB-002 (layering open) — MGT-B targets; re-verify state first | consoles/workspaces render; generic start/complete/reopen (incl. S4-P5 downstream-guard refusal = BY DESIGN when downstream consumed); allocate/void; review-reports GET+POST; worker-report as non-assigned SA (expected: designed refusal, classify); barcode gen ×5; costing |
| OWN-C | Expense — the 4 SA-only money levers | monthly worker pk=25 (pay-basis/FnF; verify basis state first); XFB-001-class unsettled completed Adda for lifecycle; an over-allocated case for a REAL M-6 block (may need DEV construction — if impossible without un-rollbackable state, disclose per §4) | pay-basis flip + audit row; FnF preview→execute (rollback-wrapped); **reconciliation override actually biting on a real M-6 block** (`SettlementReconciliationEvidence.override_reason/overridden_by` stamped); factory-expense void; full settlement lifecycle as SA; ledger recount after every block |
| OWN-D | Inventory Administration + tracking financials | Role table (5 roles at Phase-1 close); SidebarItemRule (21 rules); roll pk=37 (financial history target) | **roles add/edit/delete round-trip incl. THE carry-in** (§2): enumerate `RoleForm.permissions` queryset vs curated allowlist, POST a non-curated perm, check persistence AND whether any gate honors it — judge from evidence; sidebar-access editor M2M write → live middleware behavior change (rollback-wrapped); access hub; SA sees supplier/cost_per_kg history rows; exports |
| OWN-E | Raw materials — financial truth | roll pk=1 CR-000001 (supplier="Validation Supplier", cost=200); masters incl. referenced Cotton(1); roll count baseline (32 at Phase-1) | bulk-add WITH financials (SA-only; rollback-wrapped); roll-edit financials land + history rows written; all 4 financial layers SA-POSITIVE (form fields present · service admits · template renders · history rows visible); masters CRUD/archive/delete; #7 owner-relevance check (garbage-pk archive-confirm as SA) |
| OWN-F | Machines + Storefront-as-SA + Accounts admin | machines (4, EL-001/OL-001/SN-001); FeaturedProduct 1/Category 1; User 47/Skill 10/UserType 5 | machine CRUD/assign/release as SA (MGT-F-1 immutability guard re-proven with SA driving); **storefront editor as SA — first functional cert** (product/category add/edit/delete, rollback-wrapped); users/skills/user-types CRUD; S2 signup-closed + S3 email-shadow hold for SA too; `/admin/` admits owner (is_staff wall from inside) |
| OWN-G | patterns_ai as SA + django-admin sample | MRK-000002; DEV-NICKAR cutting table; blueprint route | blueprint 200 + write path (SA bypass on `production.change_productpattern`); route sweep SA-positive; exports; `/admin/` sampled CRUD on a low-risk model (rollback-wrapped); #9 noted only |
| OWN-H | Meta-audit + close | whole root URLConf (528 routes at MGT-H; re-census) | fresh instruments: SA-perspective census + dynamic sweep with anomaly rules (SA 403 / SA 302-bounce / SA 500 anywhere = anomaly unless enumerated universal wall); rendered sidebar as SA vs matrix; user_has_role-vs-is_superuser-vs-is_staff gate-gap audit (charter flag); carry-in disposition review; FINAL VERDICT |

## 8. Deliverables

- 8 evidence sections (OWN-A..H) appended to OWNER_VISIBILITY_CERTIFICATION.md, each with
  close-out (bugs/pins/battery/next).
- Final verdict in OWN-H (phase 2 certified or not, with grounds).
- Updated charter sub-phase table (status ticks only — never rewrite closed text).
- Backlog rows for any new INFO findings (U12).
- If fixes: pins in the app's certification test module + updated battery number.
- Status file + memory updates per sub-phase (§11/§12).

## 9. Files expected to change

**Always (docs):** `docs/OWNER_VISIBILITY_CERTIFICATION.md` · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md`
· `docs/DEPLOYMENT_BACKLOG.md` (only if new INFO) · memory files (if agent has memory).

**Only if a bug is CONFIRMED in-scope (code):** the single smallest app file(s) owning the defect
(views/services/forms/templates of the app under audit) · that app's existing certification test
module (`config/production/tests/test_management_role_certification.py` pattern — create
`test_owner_visibility_certification.py` siblings only if no suitable module exists) · the app's
GUIDE/README (U6) · `docs/DOCUMENTATION_INDEX.md` if a new file is created.

## 10. Files that must never change (touching one = STOP + report)

- Migrations (existing or new — new requires owner pre-approval, U14).
- `config/config/settings/*` (incl. enforcement flags, U10) — exception: none foreseen; a
  confirmed bug whose fix lives in settings = STOP + owner decision.
- Money single-writer services beyond a confirmed in-scope bug: `ledger_service`,
  `settlement_service`, `adda_settlement_service`, `payroll_service`, `fnf_service`,
  `expense_service`, `advance_service` — any change here triggers U8 review in the report.
- Frozen-foundation modules (U9) absent a confirmed in-scope defect.
- Anything in `docs/adr/`, the PDD, ARCHITECTURE_V2, freeze packages.
- `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) append evidence section to
OWNER_VISIBILITY_CERTIFICATION.md (never edit closed sections; corrections are appended, dated);
(b) update status-file Phase-2 sub-phase table + dashboard (battery, docs-sync, memory-sync,
carry-overs) + "Next action"; (c) backlog row per new INFO (U12); (d) if code changed: app
GUIDE/README + any doc the CHANGE_IMPACT_MATRIX maps (U6); (e) if a new file was created:
DOCUMENTATION_INDEX row.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (description +
Phase-2 bullet) and the MEMORY.md index line at each sub-phase close. Agents without memory: skip
— §11's on-disk updates are the complete binding record; nothing may exist ONLY in memory.

## 13. Battery policy

Sequential fresh-DB canonical (U5). Baseline entering OWN-A: **1526/1526** (9-app 998 +
patterns_ai 528). Expected count after any fix = previous baseline + new pins; record the
arithmetic in the close-out (MGT precedent: 1519→1522→1524→1526). Re-run ONLY when code changed;
a 0-bug sub-phase states "battery NOT re-run (baseline stands)". Never `--parallel`, never
`--keepdb` across suites.

## 14. Regression policy

- Every SA-only surface probe pairs with manager + worker negative controls (they must stay
  blocked — silent Phase-1/worker-cert regression detection).
- Prior-fix guard list (re-proven with owner driving where the surface is touched): BUG-1
  (legacy cutting complete gate) · BUG-2 (layering draft scope) · BUG-3 (alloc ₹ ctx) · BUG-E1
  (master CRUD roles) · S2 (signup closed) · S3 (email shadow) · MGT-B-1 (lane refusal flash,
  not 500) · #5 (delete-confirm renders) · MGT-F-1 (machine-code immutability).
- Pins only for NEW fixes (U4); prior pins already guard prior fixes.

## 15. Rollback policy

- Shell writes: wrap in one `transaction.atomic` block per probe cluster; force rollback
  (raise inside the block or `transaction.set_rollback(True)`); verify post-rollback counts
  byte-identical to the pre-probe baseline captured in the same session.
- Browser writes: DEV-marked data only; prefer create→verify→delete round-trips (MGT-E
  `MGTE-BROWSER-DEL` precedent); append-only tables (history, manifests, possession windows)
  cannot be unrolled from the browser → run those rollback-wrapped in shell, or disclose the
  artifact row explicitly in the evidence section (U13; MGT-D EXP-2026-006 precedent).
- State leak (probe row survives unexpectedly): record exactly what leaked, restore via the
  designed reverse path if one exists (void/archive/restore), otherwise disclose; NEVER raw-SQL
  delete.
- Session crash mid-probe: next session re-baselines counts FIRST and reconciles any orphan
  probe rows before continuing (worker-cert Phase-B lesson: evidence lost to a crash forces
  owner-attestation — capture evidence into the doc incrementally, not at the end).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. Money-write anomaly (U8).
3. Fix requires a migration (U14) or a settings change (§10).
4. Fix touches a frozen-foundation module or single-writer service beyond the confirmed defect.
5. Owner account (pk=1) state accidentally modified (password/email/role/flags) — report before
   ANY remediation.
6. Login rate-limit lockout of any probe identity.
7. Evidence contradicts a CLOSED certification (worker/management regression found) — report;
   do not reopen closed phases unilaterally.
8. Probe leaks non-DEV data or un-rollbackable state beyond disclosed-artifact class.
9. Battery goes red on anything other than the just-added pins' target behavior.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → confirm Phase 2 active + which OWN-* is next.
2. Read `docs/campaign_contracts/README.md` (universal invariants + environment) → this contract.
3. Read `docs/OWNER_VISIBILITY_CERTIFICATION.md` — charter + ALL closed evidence sections
   (carry-forward findings, disclosed artifacts, battery arithmetic).
4. Verify preconditions: git HEAD unchanged since last close (currently `49404001` + working
   tree); battery baseline number from the status dashboard; probe identities exist + active
   (read-only shell check); probe targets for the next sub-phase still in expected state
   (§7 targets are point-in-time — re-verify, re-anchor if drifted, and note the drift in the
   evidence section).
5. Obtain the owner password from the owner (or memory `test-credentials` for Claude sessions).
6. Execute exactly ONE sub-phase per §6. STOP per §16.
7. If anything read in steps 1–4 is internally inconsistent, report the inconsistency and stop
   before probing (framework conflict rule).
