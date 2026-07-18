---
id: confirmed-findings-ledger
type: evidence-cert
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# CONFIRMED FINDINGS LEDGER — Campaign Phase 4 (the permanent implementation record)

> Created at **FIX-0 (2026-07-13)** per the frozen contract
> [campaign_contracts/PHASE_04_CONFIRMED_FINDINGS.md](campaign_contracts/PHASE_04_CONFIRMED_FINDINGS.md)
> (§7 FIX-0). **APPEND-ONLY** — closed rows/blocks are never edited; corrections are dated
> appendices. Hierarchy: status file wins on state · contract wins on procedure · this ledger
> wins on what Phase 4 actually did. Fix-evidence blocks for any Phase-4 work items will be
> appended below §8 as they execute (§6.5 loop).
>
> **FIX-0 preconditions verified 2026-07-13:** Phase 2 CLOSED-CERTIFIED (OWN-H) ✓ · Phase 3
> CLOSED-CERTIFIED (OFF-D) ✓ · git HEAD `49404001` = status file ✓ · porcelain 312 = OFF-D
> close count ✓ · battery **entry baseline 1530/1530** (status dashboard, contract §13 rule —
> NOT the authoring-time 1526) ✓ · this file did not previously exist ✓. NO code changed at
> FIX-0; battery not run (0-code sub-phase rule §13).

## 1. Intake sources + completeness census (§2.2 — all six read)

| # | Source | Findings in | Rows out (this ledger) |
|---|---|---|---|
| 1 | [MANAGEMENT_ROLE_CERTIFICATION.md](MANAGEMENT_ROLE_CERTIFICATION.md) (Phase 1) | 3 confirmed bugs (all fixed in-phase) + 4 INFO/doc-drift rows seeded (#6–#9) + judged observations | CF-07..CF-09 · B-rows #6–#9 · E-rows |
| 2 | [WORKER_ROLE_CERTIFICATION.md](WORKER_ROLE_CERTIFICATION.md) (V1.1 worker cert) | 6 confirmed bugs (all fixed in-phase) + S1 verified-safe + judged observations/limitations | CF-01..CF-06 · E-rows |
| 3 | Phase 2 residue — [OWNER_VISIBILITY_CERTIFICATION.md](OWNER_VISIBILITY_CERTIFICATION.md) | 2 confirmed bugs (all fixed in-phase, incl. THE carry-in) + 3 INFO (#10–#12) + 0 stop-condition deferrals | CF-10..CF-11 · B-rows #10–#12 · §7 |
| 4 | Phase 3 residue — [OFFICE_SUPPORT_ROLE_CERTIFICATION.md](OFFICE_SUPPORT_ROLE_CERTIFICATION.md) + Design Record D1–D4 | 0 confirmed bugs + 2 INFO (#13–#14) + D1–D4 answered (nothing arrives as work) + 0 deferrals | B-rows #13–#14 · D-rows · §7 |
| 5 | Certification stop-condition deferrals (migration/settings/role-set/frozen-module class) | **ZERO** — census §7 | §7 (F-D2 arrives EMPTY) |
| 6 | [DEPLOYMENT_BACKLOG.md](DEPLOYMENT_BACKLOG.md) (+ PENDING_BACKLOG.md read for F-D1 context) | 14 rows: 2 resolved-historical (#2, #5) · 12 open (#1, #3, #4, #6–#14) | §3 table (all 14) |

**Arithmetic: 11 confirmed bugs ever raised by the certification campaign → 11 PRE-CLOSED rows
(§2). 0 open confirmed bugs arrive at Phase 4.** All other raised findings are accounted in
§3–§6 in exactly one terminal state each.

## 2. Ledger A — confirmed bugs (class: confirmed-bug). ALL PRE-CLOSED (fixed in-certification)

Lifecycle for every row below: Confirmed → Fixed → Pinned → Battery → Docs → **CLOSED
(in-phase)**; entered here per §2.2.1/.2 for reconciliation completeness — **no Phase-4 work**.

| id | Finding | Source + evidence | Owning app/file(s) | Approval ref | Pins | Battery delta | Docs | Closed |
|---|---|---|---|---|---|---|---|---|
| CF-01 | **BUG-1** — `complete_cutting_legacy` gate was PRODUCTION roles (name trap): any worker could complete Cutting (stage advance + barcode gen + cost freeze) | WORKER cert Phase A, "Bugs found → fixed (3)" | production — `stages/cutting/service.py` | n/a (in-mandate) | part of 6 pins, `production/tests/test_worker_role_certification.py` | 1499→**1505** (6 pins, all 3 BUG fixes) | evidence §Phase A | 2026-07-12 |
| CF-02 | **BUG-2** — `save_layering_draft`: any production-role worker could tamper layering drafts on any Adda | WORKER cert Phase A (same section) | production — `stages/layering/service.py` | n/a | (same 6-pin set) | (in CF-01 delta) | evidence §Phase A | 2026-07-12 |
| CF-03 | **BUG-3** — `_build_cutting_context` leaked OTHER workers' ₹ earning snapshots (era-A alloc rows) to every viewer | WORKER cert Phase A (same section) | production — `views/stage_views.py` | n/a | (same 6-pin set) | (in CF-01 delta) | evidence §Phase A | 2026-07-12 |
| CF-04 | **BUG-E1** — master write views + `_ensure_can_manage` were ProductionRole (name trap): any worker could create/edit/archive/hard-delete cloth types/colors/locations | WORKER cert Phase E, "Bug found → fixed (1)" | raw_materials — `views/master_views.py` + `services/master_service.py` | n/a | 3 pins, `raw_materials/tests/test_master_gates.py` | 1505→**1508** | evidence §Phase E | 2026-07-12 |
| CF-05 | **S2** — anonymous public signup created live active ERP users (allauth `/accounts/signup/` open) | WORKER cert Phase H (S2 section) | accounts — `allauth_adapters.py` + `config/settings/base.py` (`ACCOUNT_ADAPTER`) | pre-campaign fix (settings line landed with the fix, before the U-invariant regime; recorded as-is) | 6 pins, `accounts/tests.py` (`SignupDisabledTests` + `AllauthAdapterTests`) | 1508→**1514** | evidence §Phase H | 2026-07-12 |
| CF-06 | **S3** — allauth `/accounts/email/` let any signed-in worker add/make-primary an arbitrary email → login-identity takeover class; shadow-route fix | WORKER cert Phase H4 | accounts — `views.py` (`EmailManagementDisabledView`) + `config/urls.py` (shadow mount) | pre-campaign fix (root-URLConf line, recorded as-is) | 5 pins, `accounts/tests.py` `EmailManagementDisabledTests` | 1514→**1519** | evidence §Phase H4 | 2026-07-12 |
| CF-07 | **MGT-B-1** — missing `PermissionDenied` import in `adda_views.py`: every lane-service refusal 500'd (`NameError`) instead of the designed flash | MGT cert MGT-B, "Bug found → FIXED" | production — `views/adda_views.py` (1 import line) | n/a | 3 pins, `production/tests/test_management_role_certification.py` | 1519→**1522** | evidence §MGT-B | 2026-07-12 |
| CF-08 | **backlog #5** — `_MasterDeleteView` missing `title`/`list_url_name` context → delete-confirm GET = `NoReverseMatch` 500, all 3 masters, every allowed role | MGT cert MGT-E (pre-confirmed at worker-cert Phase E as out-of-scope) + backlog row #5 (struck, retained) | raw_materials — `views/master_views.py` (`get_context_data`) | n/a | 2 pins, `raw_materials/tests/test_master_gates.py` | 1522→**1524** | evidence §MGT-E · backlog #5 struck | 2026-07-12 |
| CF-09 | **MGT-F-1** — `machine_service.update_machine` code-immutability guard compared the form-mutated in-memory instance (always False): silent code rename with assignment history + dup-check bypass | MGT cert MGT-F, "Bug → FIXED" | machines — `services/machine_service.py` (guard reads DB row) | n/a | 2 pins, `machines/tests/test_r10a.py` (→17) | 1524→**1526** | evidence §MGT-F | 2026-07-12 |
| CF-10 | **OWN-C-1** — `record_reconciliation_evidence` resolved the evidence FK by stage CODE: multi-lane Addas collapsed N lane-SRs → persisted append-only audit row pointed at the WRONG lane | OWN cert OWN-C, "CONFIRMED BUG OWN-C-1 → FIXED" | expense — `services/reconciliation_service.py` (+`stage_record_id` in recon rows) + `services/adda_settlement_service.py` (direct FK) | U8 review recorded in-block (single-writer family touched strictly within the confirmed defect; money math untouched; golden green) | 2 pins, `expense/tests/test_s5_recon_block.py` `MultiLaneEvidenceTests` | 1526→**1528** | evidence §OWN-C · `config/expense/README.md` M-6 lane note · backlog #11 sibling | 2026-07-13 |
| CF-11 | **OWN-D-1** — THE carry-in: `RoleForm.permissions` queryset = 216 app-level perms vs 80 curated → hand-crafted POST persisted invisible, gate-honored service-model grants | OWN cert OWN-D, "THE CARRY-IN … CONFIRMED DEFECT → FIXED" (carry-in chain: worker-cert Phase D INFO → MGT carry-over → OWN-D verdict) | inventory — `forms/role_forms.py` (queryset ← `permissions_qs_by_app()`) | n/a (form validation only; no role-set constant touched) | 2 pins, `inventory/tests.py` `RolePermissionCurationTests` | 1528→**1530** | evidence §OWN-D · `docs/apps/inventory/GUIDE.md` · `config/inventory/README.md` | 2026-07-13 |

Pin/battery reconciliation: worker-cert 20 pins (6+3+6+5, 1499→1519) · Phase 1 7 pins
(3+2+2, 1519→1526) · Phase 2 4 pins (2+2, 1526→1530) · Phase 3 0 pins. **Entry baseline
1530/1530 ✓** (= status dashboard at FIX-0).

## 3. Ledger B — DEPLOYMENT_BACKLOG rows (all 14 accounted; class per §2.1)

| Row | Class | State/route (terminal unless owner F-D1 selects) |
|---|---|---|
| #1 export-code sequencer contention | infrastructure | Deferred (backlog; venue = future per-year PG sequence, migration-class → would need F-D2 if ever selected) |
| #2 worker tracking-dashboard empty table | resolved-historical | PRE-CLOSED (resolved Worker-cert Phase C by 0018 policy; row retained) |
| #3 export_list.html inline style | backlog INFO (polish) | Deferred (fix-when-touched; tokens-only rule candidate; also Phase-10 territory) |
| #4 patterns_ai not parallel-safe + keepdb Role truncation | infrastructure | Deferred (battery law already canonical SEQUENTIAL FRESH-DB; fix = test refactor, venue noted in row) |
| #5 master delete-confirm 500 | confirmed-bug | PRE-CLOSED = CF-08 (struck in backlog, retained) |
| #6 RBAC.md role-table drift | documentation drift | **Routed to KOS phase 7** (backlog precedent; NEVER Phase 4) |
| #7 master archive-confirm garbage-pk 500 | backlog INFO | Deferred (fix-when-touched = `get_object_or_404`; OWN-E owner-relevance: not owner-UI-reachable either) |
| #8 MachineAssignView worker-param validation | backlog INFO | Deferred (fix-when-touched = picker-queryset re-validation + int-parse; OWN-F dated note) |
| #9 patterns_ai `voided_by`/`retired_by` actor stamps absent | backlog INFO | Deferred (fix-when-touched = additive FK columns + stamps — **migration-class → F-D2 approval required if ever selected**) |
| #10 review-reports string-compare "no changes" flash | backlog INFO | Deferred (fix-when-touched = compare parsed Decimals; proven inert OWN-B) |
| #11 a360 recon badge collapses multi-lane stages | backlog INFO | Deferred (display-only sibling of CF-10; fix-when-touched = per-lane/worst-flag aggregation; recon rows already carry `stage_record_id`) |
| #12 RM index tile lumps damaged into "Used" | backlog INFO | Deferred (fix-when-touched = `used = total - available - damaged`; canonical dashboard correct) |
| #13 dead `can_edit_financials` ctx flag | backlog INFO | Deferred (fix-when-touched = drop 2 dead lines or wire consumer) |
| #14 `STOREFRONT_ROLES` dead lever | backlog INFO | Deferred (fix-when-touched = make both gates consume the constant; **role-set-adjacent → F-D2 approval required if ever selected**) |

## 4. Ledger C — documentation-drift items (route: KOS phases 6–7, never Phase 4)

| id | Item | Source |
|---|---|---|
| DD-1 | Backlog #6 — RBAC.md "What each role can do" table stale | MGT-A (backlog row #6) |
| DD-2 | DOCUMENTATION_INDEX row for OWNER_VISIBILITY_CERTIFICATION.md stale ("OWN-A..H paused") | OFF-0 observation (reported, not fixed) |
| DD-3 | DOCUMENTATION_INDEX row for OFFICE_SUPPORT_ROLE_CERTIFICATION.md now same-class stale (ends at "Next OFF-B"; phase since CLOSED) — noted at FIX-0 intake, same lane as DD-2, routed with it | FIX-0 intake observation (routing note, not a new discovery: the row's staleness is the mechanical consequence of Phase 3 closing after the last index edit) |
| DD-4 | patterns_ai README drift | pre-logged (status dashboard carry-over) |
| DD-5 | Worker-cert meta-audit evidence lives only in memory, not in WORKER_ROLE_CERTIFICATION.md | campaign_contracts/README.md known-risks — **ASSIGNED: Phase 6 discovers/queues (dated amendment, §2.2 seed item 5); Phase 7 materializes** |
| DD-6 | inventory `templates/inventory/dashboard.html` orphan template + `signals.py` tombstone referencing removed StockService | Worker-cert Phase D observations (inert, judged in-phase) |

## 5. Ledger D — design-ambiguity / owner-decision rows (answered, terminal)

| id | Item | Ruling (verbatim record in owning doc) |
|---|---|---|
| OD-1 | PHASE_03 §2.2.1 pure-accountant reachability contradiction | **Resolved BY DESIGN via D1 (owner, OFF-0 2026-07-13)**: accountant = ADD-ON capability role; composite functional + pure-blocked. Does NOT arrive at Phase 4 (the D1 ruling did not name Phase 4 as a venue; no page-gate work authorized) |
| OD-2 | PHASE_03 D4 — `expense.view_all_payroll` zero-holder state | **intended-NO** (door certified CLOSED at OFF-A). No work |
| OD-3 | PHASE_03 D2/D3 — composite pk=76 created (permanent DEV cast) · pk=61 reused+reset | Identity decisions, executed at OFF-0; disclosed durable writes. No work |
| OD-4 | `/media/<path>` login-tier | Owner Option 1 (2026-06-11) — out of certification scope, noted in MGT carry-overs + OWN-H. Stands; no Phase-4 item |
| OD-5 | Worker-cert Phase B (expense) re-audit | Owner DECLINED re-audit (attested close-out; artifacts lost). Superseded in practice by MGT-C + OWN-C certifications of the same surface. No work |
| OD-6 | Enforcement flags stay OFF until R11 · S6 reported_quantity retirement soak-gated | Standing owner rulings (U10; PENDING_BACKLOG) — outside Phase-4 intake by definition; will appear in the Phase-21 open-items register |

## 6. Ledger E — judged observations, verified-safe, dated corrections, disclosed limitations (terminal, no work)

**Verified safe / BY DESIGN (judged inside their named sub-phases):** S1 inactive-user OTP
login inert (worker-cert H3) · MGT-A products-list Edit/Flow links render→403 (template
cosmetics, same class as worker-cert Phase-E roll-detail buttons — both judged INFO-cosmetic,
fails closed, no numbered backlog row by in-phase choice) · MGT-A masters delegation seam BY
DESIGN · MGT-G cross-manager scoping BY DESIGN ABSENT (runtime-proven) · OFF-A obs (b)
view==edit predicate BY DESIGN · OFF-B my-dashboard universal landing BY DESIGN · worker-cert
Phase C/D owner-policy items (scan-any-Adda · timeline actor emails · broadcast rows ·
styleguide open) · Phase D `can_access_url_name` anonymous-True BY DESIGN.

**Dated corrections (all resolved-with-citation; OFF-D contradiction audit = zero
unresolved):** OFF-A export-trio "405" → **403** refusal-class label (corrected OFF-B) ·
OWN-H rule-23 narrative correction (OWN-D blanket line over-broad; functional impact zero) ·
OWN-B narrative-precision note on MGT-B multi-lane funnels · OFF-0 note: contract §13 "1526" =
authoring-time number · OFF-B porcelain 311→312 note · backlog #2 stale-observation
resolution (worker-cert Phase C).

**Disclosed limitations (recorded, not findings):** OTP-send POSTs never probed
(EMAIL_BACKEND may be real SMTP — MGT-F/OWN-H) · worker-cert Phase B attested-not-artifact
close · worker-cert FIX-2/FIX-3 browser leg cut short (shell+pins cover) · Phase C
financial-strip never exercised on live data (pins cover) · Phase C barcode-list/print 403
pin-gap (U4: pins only for fixes) · OFF-C SA browser lane skipped (no owner password) ·
worker-cert Phase C 8-finder sub-agent failure, audit redone main-thread (U7 precedent).

## 7. Stop-condition deferral census (§2.2.5) — F-D2 input

Searched Phase 2 + Phase 3 records (H5/H6 disposition tables, OFF-D phase-finding review,
close-outs): **ZERO fixes were refused/deferred for migration-, settings-, role-set-, or
frozen-module-class reasons.** Both Phase-2 bugs were fixed in-phase; Phase 3 found none.
**F-D2 therefore arrives with an EMPTY item list** — nothing is approval-pending; the table
stays open for any future arrival under the permanence clause (§6.6).

## 8. Work queue (ordered by §7 category) — state at FIX-0

**EMPTY.** 0 open confirmed bugs arrived from phases 1–3 (all 11 pre-closed). Pending owner
F-D1 (backlog selection, contract default = NONE) and F-D2 (empty census). Unless F-D1
upgrades rows, FIX-A/B/C execute as documented no-ops and the phase proceeds to FIX-D (pin
audit) → FIX-E (terminal battery) → FIX-F (docs audit) → FIX-G (reconciliation).

| Queue slot | Category | Items |
|---|---|---|
| FIX-A | permission | — (none) |
| FIX-B | business-logic | — (none) |
| FIX-C | ui-template | — (none) |

## 9. Design Record status (answers live in contract Appendix A when given)

| # | Question | Record shown to owner | Owner answer |
|---|---|---|---|
| F-D1 | Which backlog rows (if any) upgrade to Phase-4 work items? | Open rows: #1 infra · #3 polish · #4 infra · #6 doc-drift (phase-7 route, ineligible by precedent) · #7–#14 INFO each with a written fix-when-touched spec. Contract default: **NONE** | **ANSWERED 2026-07-13, verbatim: "NONE. Do not promote any backlog items into Phase 4. Leave backlog rows #1, #3, #4, #7–#14 deferred exactly as documented. Keep #6 permanently routed to KOS Phase 7."** |
| F-D2 | Per-item approvals for approval-gated deferrals | Census §7: **no items arrived** — nothing to approve unless F-D1 selects a gated row (#9 migration-class · #14 role-set-adjacent · #1 future-fix migration-class) | **ANSWERED 2026-07-13, verbatim: "CONFIRMED EMPTY. No approval-gated items are selected."** |
| F-D3 | Permanence scope confirmation (§6.6: post-phase-22, commit discipline replaces U2; all else stands) | Owner designation recorded 2026-07-12 | **ANSWERED 2026-07-13, verbatim: "CONFIRMED. Adopt §6.6 permanently exactly as written. Post-Phase-22 commit discipline replaces U2. All remaining permanence rules remain unchanged."** |

**F-D1..F-D3 recorded (mirrored in contract Appendix A, dated+attributed) → FIX-0 CLOSED
2026-07-13.** Consequences locked: work queue stays EMPTY for the whole phase (no item can
enter — this phase discovers nothing, §2.3); FIX-A/B/C execute as documented no-op
pass-throughs in the frozen order (no sub-phase skipped); first work-bearing sub-phase =
FIX-D (pin-coverage audit); battery next runs at FIX-E (terminal certification) unless FIX-D
adds gap-filling pins.

## 10. Prior-fix guard list imported (§14 — re-proven wherever Phase-4 changes touch a surface)

BUG-1 · BUG-2 · BUG-3 · BUG-E1 · S2 · S3 · MGT-B-1 · #5 · MGT-F-1 **+ Phase-2 additions:
OWN-C-1 (multi-lane evidence FK) · OWN-D-1 (role-form curation)**. All 11 have green pins at
baseline 1530/1530 (last full run OWN-D close 2026-07-13); FIX-D audits pin↔defect coverage.

## 11. U7 disclosure — FIX-0 method

Main-thread (binding): both backlog files read fully; all six sources' finding/verdict/fix/
pin/battery sections read directly (contract §2.2, §7 FIX-0); censuses cross-checked against
the status-file phase ledgers (arithmetic ✓). Supplemental sweep (Workflow, 5 finders):
worker-cert + backlog finders completed and matched the main-thread census (no missed
finding-class item); **the MGT/OWN/OFF finders FAILED (session token limit) — recorded per
U7; no surface was marked clean on sub-agent silence; those three docs were extracted
main-thread as above.**

---

# Evidence blocks (appended per work item as Phase 4 executes — §6.5 step 7)

## FIX-A — Permission / RBAC findings (2026-07-13) ✅ CLOSED — EMPTY QUEUE, DOCUMENTED NO-OP

- **Queue read (§6.5 step 1):** ledger rows with class=confirmed-bug AND lifecycle≠CLOSED AND
  category=permission → **0 items.** All 11 confirmed bugs (CF-01..CF-11) are PRE-CLOSED
  (fixed+pinned+battery-proven inside their certification phases); F-D1 = NONE (verbatim, §9)
  promoted nothing; F-D2 = CONFIRMED EMPTY. Per §2.3 this phase discovers nothing, so no item
  can enter the queue mid-phase.
- **Work performed:** none possible — no fix, no pins (U4: pins only for fixes), no probes
  (§4 no-new-probing; no source probe exists to re-run because no work item exists).
- **Code changed:** ZERO. Battery per §6.4/§13: **NOT run — 0-code sub-phase, baseline
  1530/1530 stands.**
- **Regression (§14):** N/A — re-proof obligations trigger only "wherever a Phase-4 change
  touches its surface"; no surface touched. Prior-fix guard list (§10, 11 entries) remains
  green at baseline 1530/1530 (last full run OWN-D close 2026-07-13); FIX-D audits coverage
  next per its own mandate.
- **Rollback:** n/a (no probes, no writes beyond this ledger + status/memory sync).
- **Stop conditions (§16):** none triggered; normal U3 stop at sub-phase close.
- **Docs (U6):** no code → app GUIDE/README/CHANGE_IMPACT_MATRIX = N/A; synced this session:
  this ledger + status file + memory. Backlog untouched (§11c: nothing resolved, nothing
  added).
- **Not skipped:** FIX-A executed as a formal pass-through per the frozen §7 order and the
  owner's 2026-07-13 instruction ("Do not skip any sub-phase. Follow the frozen execution
  order."). **Next sub-phase: FIX-B (business-logic) — same empty-queue state, owner-gated.**

## FIX-B — Business-logic findings (2026-07-13) ✅ CLOSED — EMPTY QUEUE, DOCUMENTED NO-OP

- **Preconditions (§17.4, read-only, this session):** git HEAD `49404001` = status file ✓ ·
  porcelain 313 = FIX-0 close count (312 + this ledger) ✓ · battery baseline **1530/1530**
  (dashboard) ✓ · Design Record final (§9: F-D1 "NONE" · F-D2 "CONFIRMED EMPTY" · F-D3
  "CONFIRMED", owner verbatim 2026-07-13) ✓ · owning-file drift check (§16.9) N/A — no work
  item names an owning file.
- **Queue read (§6.5 step 1, from disk):** ledger rows with class=confirmed-bug AND
  lifecycle≠CLOSED AND category=business-logic → **0 items.** All 11 confirmed bugs
  (CF-01..CF-11) PRE-CLOSED in-certification; F-D1=NONE promoted nothing; F-D2 empty; §2.3
  forbids mid-phase discovery, so the queue cannot have grown since FIX-A.
- **Work performed:** none possible — no fix, no pins (U4), no probes (§4 no-new-probing; the
  tightened FIX-B evidence obligations — rollback-wrapped DB proofs, ledger row-count/Σ
  re-baseline, golden ₹225 byte-check — attach to money-adjacent FIXES and are N/A with zero
  work items; probing them without a work item would itself violate §2.3).
- **U8 / money invariants:** no single-writer service, settlement path, or money-write path
  touched (zero writes of any kind beyond this ledger + status/memory sync) — Money-Write
  STOP rule never engaged; golden invariants trivially undisturbed.
- **Code changed:** ZERO. **Battery per §6.4/§13: NOT run — 0-code sub-phase, baseline
  1530/1530 stands.** (The "immediate full battery after any single-writer fix" trigger never
  armed — no fix.)
- **Regression (§14):** N/A — no Phase-4 change touched any prior-fix surface; guard list
  (§10, 11 entries) stands green at baseline.
- **Rollback:** n/a (no probes, no DB access).
- **Stop conditions (§16):** none triggered; normal U3 stop at sub-phase close.
- **Docs (U6):** no code → GUIDE/README/CHANGE_IMPACT_MATRIX N/A; synced this session: this
  ledger + status file + memory. Backlog untouched (§11c).
- **Not skipped:** FIX-B executed as a formal pass-through per the frozen §7 order and the
  owner's explicit 2026-07-13 order. **Next sub-phase: FIX-C (UI/template) — same empty-queue
  state, owner-gated.**

## FIX-C — UI / template findings (2026-07-13) ✅ CLOSED — EMPTY QUEUE, DOCUMENTED NO-OP

- **Owner-ordered re-reads performed from disk before executing:** contract §7 FIX-C row
  re-read verbatim · this ledger re-read (queue table, §9 Design Record, FIX-A/FIX-B evidence
  blocks, Ledger-A row states).
- **Preconditions (§17.4, read-only, from disk):** git HEAD `49404001` = status file ✓ ·
  porcelain 313 (unchanged since FIX-0 close) ✓ · battery baseline **1530/1530** (dashboard) ✓
  · Design Record final (§9: F-D1 "NONE" · F-D2 "CONFIRMED EMPTY" · F-D3 "CONFIRMED", owner
  verbatim) ✓ · owning-file drift check (§16.9) N/A — no work item names an owning file.
- **Queue read (§6.5 step 1, from disk):** ledger rows with class=confirmed-bug AND
  lifecycle≠CLOSED AND category=ui-template → **0 items.** All 11 confirmed bugs (CF-01..CF-11)
  PRE-CLOSED in-certification (11/11 rows verified on disk); F-D1=NONE promoted nothing; F-D2
  empty; §2.3 forbids mid-phase discovery — queue cannot have grown since FIX-B.
- **Work performed:** none possible — no fix, no pins (U4; #5-precedent Python render-crash
  pins attach to fixes only), no probes, no browser session (§4 no-new-probing; the tightened
  FIX-C evidence obligations — :8003 before/after as the affected identity after dev-server
  restart, mobile responsive check, DEV-data round-trip — attach to UI FIXES and are N/A with
  zero work items). No template, CSS, or static file touched; tokens-only + design-frozen
  rules trivially unviolated.
- **Code changed:** ZERO (templates count as code for U5 — none touched). **Battery per
  §6.4/§13: NOT run — 0-code sub-phase, baseline 1530/1530 stands.**
- **Regression (§14):** N/A — no page changed, so no other-identity render/refuse re-proof is
  owed; prior-fix guard list (§10, 11 entries) stands green at baseline.
- **Rollback:** n/a (no browser data created, no DB access).
- **Stop conditions (§16):** none triggered (incl. FIX-C's own design-system-growth stop —
  unreachable with no fix); normal U3 stop at sub-phase close.
- **Docs (U6):** no code → GUIDE/README/CHANGE_IMPACT_MATRIX N/A; synced this session: this
  ledger + status file + memory. Backlog untouched (§11c).
- **Not skipped:** FIX-C executed as a formal pass-through per the frozen §7 order and the
  owner's explicit 2026-07-13 order. **Queue sub-phases FIX-A/B/C now ALL CLOSED as documented
  no-ops. Next sub-phase: FIX-D (regression-pin coverage audit) — the phase's first
  work-bearing sub-phase, owner-gated.**

## FIX-D — Regression-pin coverage audit (2026-07-13) ✅ CLOSED — 31/31 pins verified, 0 gaps, 0 pins added

- **Preconditions (from disk):** git HEAD `49404001` ✓ · contract §7 FIX-D row re-read
  verbatim ✓ · ledger §10 guard list re-read ✓ · all 7 pin-home modules exist on disk ✓ ·
  baseline **1530/1530** ✓.
- **Method (contract-exact):** fail-on-revert verified by READING each pin against its
  defect (never by reverting); presence = disk enumeration (`grep class/def` per module) +
  full pin-body reads; greenness = targeted execution (below) + the 1530/1530 full-battery
  citation (OWN-D close) with the documented docs-only drift chain since (porcelain
  311→312→313, every session 0-code).

### Pin-coverage table (pin↔defect mapping — the §7 FIX-D output)

| CF | Defect (revert condition) | Pin(s) on disk (module · test) | Fails-on-revert reading |
|---|---|---|---|
| CF-01 BUG-1 | cutting-complete gate reverts to PRODUCTION roles | `production/tests/test_worker_role_certification.py` · `LegacyCuttingCompleteGateTests.test_worker_blocked_even_with_cutting_skill` + `test_manager_passes_the_role_gate` | worker call must raise `PermissionDenied('only management…')` — reverted gate lets the skilled worker through → assertRaises fails; companion pins the manager passing the ROLE gate (falls to stage `ValidationError`) |
| CF-02 BUG-2 | layering-draft gate loses assignment/skill/mgmt scoping | same module · `LayeringDraftGateTests.test_unassigned_worker_blocked` + `test_assigned_worker_helper_and_management_allowed` | outsider draft must raise 'not assigned to this stage' AND `draft_notes` stay `''` — reverted gate writes the tamper → both assertions fail; companion proves the three allowed identities still draft |
| CF-03 BUG-3 | `alloc_items` built for non-management viewers again | same module · `CuttingAllocationCtxVisibilityTests.test_worker_gets_zero_allocation_bytes` + `test_management_still_sees_allocation_rows` | worker bundle `alloc_items == []` — reverted ctx carries ₹ rows → equality fails; companion pins management still gets the full rows (allocated/remaining keys) |
| CF-04 BUG-E1 | master write views/service revert to Production gates | `raw_materials/tests/test_master_gates.py` · `MasterWriteGateTests.test_worker_blocked_from_master_write_views` + `test_manager_passes_master_write_views` + `test_service_gate_blocks_worker` | 6 write GETs must 403 for worker + create/archive POST inertia (row absent, flag untouched) — reverted mixin returns 200/302 with writes → fails; manager-positive + service-layer `PermissionDenied` (defence-in-depth) companions |
| CF-05 S2 | signup adapter/setting removed — public signup reopens | `accounts/tests.py` · `SignupDisabledTests.test_allauth_signup_get_is_closed` + `test_allauth_signup_post_creates_no_user` · `AllauthAdapterTests` ×4 (`account_adapter_signup_closed` / `social_adapter_signup_closed` / `google_login_links_pre_provisioned_user` / `google_login_refuses_unprovisioned_user`) | GET must render `account/signup_closed.html` (template-name assert) and POST must leave `User.objects.count()` unchanged — reverted adapter renders the form + creates the user → fails; adapter unit pins nail both `is_open_for_signup()==False` halves + the pre-provisioned-only Google invariant both directions |
| CF-06 S3 | shadow route unmounted — allauth email management reopens | `accounts/tests.py` · `EmailManagementDisabledTests` ×5 (`reverse_resolves` / `get_is_shadowed` / `add_email_post_creates_nothing` / `make_primary_does_not_change_identity` / `anonymous_to_login`) | GET must 302 and NEVER render `account/email.html`; add-POST must create zero `EmailAddress` + leave `User.email` unchanged; make-primary refused even with a second address — reverted mount processes all of it → fails; reverse-pin keeps allauth templates safe |
| CF-07 MGT-B-1 | `PermissionDenied` import removed from adda_views again | `production/tests/test_management_role_certification.py` · `LaneViewsServiceRefusalTests` ×3 | empty add/cancel-lane POST must 200-render with 'reason is required' flash + 0 `CuttingStream` rows — reverted import 500s (`NameError`) → status/contains asserts fail; worker 403-at-dispatch companion |
| CF-08 #5 | `_MasterDeleteView.get_context_data` removed | `raw_materials/tests/test_master_gates.py` · `test_manager_delete_confirm_page_renders` + `test_manager_delete_confirm_then_post_deletes` | confirm GET must 200 with Cancel `href` reversing + title, ALL THREE masters — reverted context 500s (`NoReverseMatch`) → fails; full confirm→POST→row-gone workflow companion |
| CF-09 MGT-F-1 | code-immutability guard compares in-memory instance again | `machines/tests/test_r10a.py` · `MachineViewsTests.test_edit_form_cannot_rename_code_with_history` + `test_edit_form_renames_code_without_history` | POST rename on a machine WITH assignment history must re-render 200 + 'immutable' + DB code unchanged — reverted guard compares mutated instance (always False) and saves → fails; no-history rename still allowed (companion prevents over-tightening) |
| CF-10 OWN-C-1 | evidence FK resolves via stage-CODE dict again | `expense/tests/test_s5_recon_block.py` · `MultiLaneEvidenceTests.test_evidence_fk_points_at_the_over_allocated_lane` + `test_both_lanes_over_get_their_own_evidence_rows` | two-lane world: evidence row must FK the OVER lane's sr (`ev.stage_record_id == sr_b.pk`) with its own quantity pair; both-lanes-over must yield TWO rows each FK'd+paired — reverted CODE-dict collapses to one arbitrary survivor → both fail |
| CF-11 OWN-D-1 | RoleForm queryset reverts to app-level filter | `inventory/tests.py` · `RolePermissionCurationTests.test_queryset_equals_curated_allowlist` + `test_handcrafted_noncurated_perm_rejected` | offered pks must EQUAL curated `permissions_qs_by_app()` set with `change_machinetype` explicitly absent — reverted 216-perm queryset breaks set-equality; hand-crafted POST with the non-curated pk must form-error + persist nothing — reverted queryset validates+persists it → fails |

### Audit findings

- **Presence: 31/31 pins found on disk**, exactly matching every CF row's claimed count
  (6+3+3+2+6+5+2+2+2 per fix = 31). **No missing pins.**
- **No orphan pins:** every pin above maps to exactly one confirmed defect (U4 honored —
  co-resident tests in these modules are certification tests, not pins, and claim no defect).
- **Battery arithmetic internally consistent:** 1499 +6 =1505 +3 =1508 +6 =1514 +5 =**1519**
  (worker-cert) +3 =1522 +2 =1524 +2 =**1526** (Phase 1) +2 =1528 +2 =**1530** (Phase 2);
  Σ pins = 31 = 1530 − 1499 ✓; matches each source doc's per-fix recorded numbers ✓.
- **Green NOW (targeted execution, disclosed as verification — NOT a battery):** one
  sequential fresh-test-DB run of all 7 pin homes
  (`manage.py test production.tests.test_worker_role_certification
  production.tests.test_management_role_certification raw_materials.tests.test_master_gates
  machines.tests.test_r10a expense.tests.test_s5_recon_block
  inventory.tests.RolePermissionCurationTests accounts.tests.SignupDisabledTests
  accounts.tests.AllauthAdapterTests accounts.tests.EmailManagementDisabledTests`) →
  **`Ran 55 tests in 8.249s — OK`** (module co-residents included by module-level targets:
  6+3+5+17+8+2+5+4+5 = 55; all 31 pins inside). Test DB created fresh + destroyed; dev DB
  untouched.
- **Testability stop (§7 FIX-D):** not triggered — every defect was expressible as a pin
  without app-code change (all already exist).
- **Gaps: ZERO → gap-filling pins: ZERO → per §7 "Battery: full run if any pin added" the
  full battery is NOT triggered. Baseline 1530/1530 STANDS.** Code changed this sub-phase:
  ZERO (tests read + executed only).
- **Docs (U6):** no code → GUIDE/README/CHANGE_IMPACT_MATRIX N/A; synced: this ledger +
  status file + memory. Backlog untouched (§11c). **Next sub-phase: FIX-E (terminal
  sequential battery certification) — owner-gated.**

## FIX-E — Terminal sequential battery certification (2026-07-13) ✅ CLOSED — 1530/1530 GREEN

- **Preconditions (from disk):** contract §7 FIX-E row re-read verbatim ✓ · all prior
  sub-phases CLOSED in this ledger (FIX-0 §9 close note · FIX-A/B/C/D evidence blocks) ✓ ·
  git HEAD `49404001` = status file ✓ · porcelain 313 ✓ · entry baseline **1530/1530**
  (status dashboard: 9-app 1002 + patterns_ai 528, OWN-D close) ✓ · expected final =
  **1530** (entry 1530 + Σ 0 pins added in FIX-A..D) ✓.
- **U5 canonical procedure, executed exactly** (sequential · fresh test DBs created and
  destroyed per run · NO `--parallel` · NO `--keepdb` — backlog #4 + MGT-F addendum honored):

| Run | Command line (verbatim) | Result | Timing |
|---|---|---|---|
| 1 | `env/bin/python config/manage.py test accounts core raw_materials production tracking expense storefront inventory machines` | **Ran 1002 tests — OK** | 168.480s |
| 2 | `env/bin/python config/manage.py test patterns_ai` | **Ran 528 tests — OK** | 139.850s |

- **Final count: 1002 + 528 = 1530/1530 GREEN.** Zero failures, zero errors, zero
  unexpected regressions → §16.8 stop NOT triggered. Canonical baseline **re-certified
  unchanged at 1530/1530** (identical composition to the OWN-D-close baseline: 1002+528).
- **Phase-4 battery-history reconciliation (every run this phase listed, §7 output):**

| Sub-phase | Battery activity | Arithmetic |
|---|---|---|
| FIX-0 | NOT run (0-code intake; §13) | baseline 1530 read from dashboard |
| FIX-A | NOT run (0-code no-op) | 1530 stands |
| FIX-B | NOT run (0-code no-op) | 1530 stands |
| FIX-C | NOT run (0-code no-op) | 1530 stands |
| FIX-D | full battery NOT armed (0 pins added); targeted 55-test pin-home run = verification, NOT a battery (disclosed in FIX-D block) | 1530 stands |
| **FIX-E** | **terminal full battery (2 runs above)** | **entry 1530 + Σ 0 pins = 1530 ✓ actual 1530 ✓** |

  Cross-phase chain re-stated: 1499 (V1.1 sprint) + 20 worker-cert pins = 1519 + 7 Phase-1
  pins = 1526 + 4 Phase-2 pins = 1530 + 0 Phase-3 pins + **0 Phase-4 pins = 1530** ✓
  (per-run history verified at FIX-D against every source doc).
- **Code changed this sub-phase: ZERO** (test execution only; test DBs destroyed; dev DB
  untouched — the two runs create/destroy `test_*` databases only).
- **Rollback:** n/a. **Stop conditions (§16):** none triggered; normal U3 stop.
- **Docs (U6):** no code → GUIDE/README/CHANGE_IMPACT_MATRIX N/A; synced: this ledger +
  status file + memory. Backlog untouched (§11c). **Next sub-phase: FIX-F (documentation
  synchronization audit) — owner-gated.**

## FIX-F — Documentation-synchronization audit (2026-07-13) ✅ CLOSED — ZERO OUTSTANDING OBLIGATIONS

- **Preconditions (from disk):** contract §7 FIX-F row re-read verbatim ✓ · ledger re-read
  (FIX-0..E all CLOSED, append-only order intact) ✓ · designated docs re-read ✓ · HEAD
  `49404001` · porcelain 313 ✓. Battery NOT run (no code — §7 FIX-F rule).
- **Phase-4 changed-file set (the §7 "diffs" input):** docs ONLY —
  `docs/CONFIRMED_FINDINGS_LEDGER.md` (new) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` ·
  `docs/DOCUMENTATION_INDEX.md` · `docs/campaign_contracts/PHASE_04_CONFIRMED_FINDINGS.md`
  (Appendix A designated fill) · memory files (outside repo). **Zero app code proof:** mtime
  census — the ONLY 5 `config/**.py` files modified today are the CF-10/CF-11 owning/pin
  files stamped 02:47–03:36 (the Phase-2 OWN-C/OWN-D fix sessions, pre-FIX-0); 0 templates
  today; porcelain 312→313 = exactly this ledger; FIX-E battery green at exact baseline
  composition = behavioral corroboration.

### Docs-sync table (§7 FIX-F output)

| Obligation | Disposition (verified from disk) |
|---|---|
| CHANGE_IMPACT_MATRIX per changed file | Matrix = code-file→docs map; carries NO row for the 4 changed doc files → **N/A-stated**. Nearest row "roadmap/phase change" NOT triggered (execution progress ≠ plan change; ROADMAP/PENDING_BACKLOG untouched by design). The one matrix-mapped file family Phase 4 brushed — `expense/services/adda_settlement_service.py` (CF-10) — was changed in PHASE 2 under its own certified U6 close (evidence-resolution only; money flow/architecture docs unaffected → their matrix rows N/A per that close) |
| New file ⇒ DOCUMENTATION_INDEX row (§11e) | ✓ ledger row present (line 48), added at FIX-0 |
| DEPLOYMENT_BACKLOG rows struck/updated | ✓ NOTHING owed — zero rows resolved this phase (F-D1=NONE); 14 rows intact, #2/#5 remain struck-historical; file byte-untouched by Phase 4 (§11c honored) |
| Status file per sub-phase close (§11b) | ✓ six closes recorded (FIX-0 gate + close, A, B, C, D, E): last-updated chain + master row 4 + sub-phase table + dashboard (battery row re-based at FIX-E) + next-action, each same-session |
| Ledger discipline (§11a) | ✓ append-only held: closed blocks never edited; F-D answers filled the designated §9 pending cells + dated close note; blocks FIX-A→E in §7 order; Dated-amendments section still "(none)" |
| Contract Appendix A | ✓ F-D1/F-D2/F-D3 owner-verbatim + date/attribution line; ONLY the designated fillable section touched — frozen body byte-untouched, no Corrections section needed |
| Memory (§12) | ✓ topic file `project_deployment_campaign_2026_07_12.md` + MEMORY.md index updated at every close (FIX-0/A, B, C, D, E; this close adds F); nothing exists only in memory (ledger + status file carry everything) |
| **Per-CF app-doc trail current (CF-01..11)** | CF-01..03: `docs/apps/production/GUIDE.md` documents the 3 worker-cert fixes (line ~297) ✓ · CF-04/CF-08: `config/raw_materials/README.md` (management-only writes) + `docs/apps/raw_materials/GUIDE.md` (name-trap note + `_MasterDeleteView.get_context_data` #5 note) ✓ · CF-05/CF-06: `docs/apps/accounts/GUIDE.md` rows for `allauth_adapters.py` (S2) + `views.py`/`urls.py` (S3) with pin references ✓ · CF-07: no doc ever claimed the buggy behavior (1-line import); fix-time U6 recorded at MGT-B close; no stale claim found ✓ · CF-09: `config/machines/README.md` documents the MGT-F-1 DB-row guard ✓ · CF-10: `config/expense/README.md` lane-correctness note (line ~135) ✓ · CF-11: `docs/apps/inventory/GUIDE.md` forms row (OWN-D-1, detailed) + `config/inventory/README.md` invariant #4 ✓ — **no stale claim contradicting any fix found anywhere checked** |
| Known doc-drift (NOT Phase-4 obligations) | DD-1..DD-6 remain routed to KOS phases 6–7 (ledger §4) — including DOCUMENTATION_INDEX's stale Phase-2/3 certification rows (DD-2/DD-3): deliberately NOT repaired here (doc-drift repair = phase 7, §2.3/backlog-#6 precedent) |

- **Truth-lock contradiction stop (§7 FIX-F):** NOT triggered — no doc update revealed any
  contradiction with a lock (no PDD/ADR/ARCHITECTURE_V2/freeze content was implicated by a
  docs-only phase).
- **Outstanding documentation obligations: ZERO.**
- **Docs (U6) for this sub-phase itself:** no code → app docs N/A; synced: this ledger +
  status file + memory. Backlog untouched. **Next sub-phase: FIX-G (final verification +
  campaign reconciliation + PHASE-4 VERDICT — the Phase-21 certificate input) — owner-gated.**

## FIX-G — Final verification + campaign reconciliation (2026-07-13) ✅ — PHASE 4 VERDICT: CERTIFIED, CLOSED

**Preconditions (from disk):** contract re-read (§3 criteria + §7 FIX-G row + §16/§17) ✓ ·
this ledger re-read, FIX-0..F blocks all CLOSED in §7 order ✓ · HEAD `49404001` · porcelain
313 ✓ · **zero code since FIX-E** (mtime census 0 .py / 0 .html in the window — §2.3 honored,
FIX-E stands, battery NOT re-run) ✓.

### Reconciliation statement (§3.6 — every certification-campaign finding in EXACTLY ONE terminal state)

**Completeness census — findings in = rows out, per §2.2 source:**

| Source | Findings in | Rows out | Terminal state |
|---|---|---|---|
| §2.2.1 Phase 1 (MGT) | 3 confirmed bugs | CF-07 · CF-08 · CF-09 | PRE-CLOSED (fixed+pinned+battery in-phase) |
| §2.2.2 Worker-cert | 6 confirmed bugs + S1 suspect | CF-01..CF-06 + §6 verified-safe row | PRE-CLOSED ×6 · S1 VERIFIED SAFE |
| §2.2.3 Phase 2 residue | 2 confirmed bugs + 3 INFO + 0 deferrals | CF-10 · CF-11 + B-rows #10/#11/#12 | PRE-CLOSED ×2 · INFO-deferred ×3 |
| §2.2.4 Phase 3 residue | 0 bugs + 2 INFO + D1–D4 | B-rows #13/#14 + OD-1..OD-3 | INFO-deferred ×2 · owner-answered (BY DESIGN, no arrival) |
| §2.2.5 Stop-condition deferrals | **0** | §7 census | F-D2 EMPTY, owner-confirmed verbatim |
| §2.2.6 Backlog | 14 rows | §3 table, all 14 | 2 resolved-historical · 12 open (routed below) |
| (completeness extras) | doc-drift · owner decisions · dated corrections · disclosed limitations | DD-1..6 · OD-1..6 · §6 lists (6 corrections · 7 limitations) | routed phase-6/7 · terminal-answered · resolved-with-citation · recorded |

**Arithmetic: 11 confirmed bugs ever raised = 11 CF rows, ALL CLOSED (9 dated 2026-07-12,
2 dated 2026-07-13 — verified on disk this sub-phase); 0 open defects carried in; 0 carried
out; 0 unaccounted findings discovered (stop §16-FIX-G NOT triggered).** 31 pins protect the
11 fixes (FIX-D 31/31, read-verified + 55-test green) · terminal battery 1530/1530 (FIX-E).

### Backlog line-by-line review (MGT-H precedent — all 14 rows)

#1 export sequencer contention — infra, documented trade-off, fine at factory scale; future
fix = per-year PG sequence (migration-class ⇒ owner approval whenever picked up). Deferred. ·
#2 worker tracking-dashboard — resolved-historical (0018 policy, worker-cert Phase C); row
retained. · #3 export_list inline style — polish, tokens-only candidate; Phase-10 territory.
Deferred. · #4 patterns_ai parallel/keepdb — infra; battery law already canonical
sequential-fresh; fix = test-media isolation refactor. Deferred. · #5 — FIXED (CF-08),
struck-retained. · #6 RBAC.md role table — doc-drift, permanently routed KOS phase 7 (owner
F-D1 verbatim). · #7 archive-confirm garbage-pk 500 — INFO, not UI-reachable (mgr AND owner
censuses), fails closed; fix-when-touched spec on row. · #8 MachineAssignView worker param —
INFO, data-hygiene, hand-crafted-POST-only; spec on row. · #9 voided_by/retired_by stamps —
INFO, audit-hygiene; **additive-migration-class ⇒ U14 owner approval whenever picked up**. ·
#10 review-reports string-compare flash — INFO, proven inert; spec on row. · #11 a360 badge
lane collapse — INFO, display-only sibling of CF-10; mechanical fix spec on row. · #12 RM
index tile damaged-lump — INFO, display-only; spec on row. · #13 dead can_edit_financials
flag — INFO, no consumer; spec on row. · #14 STOREFRONT_ROLES dead lever — INFO, equivalence
certified live; **role-set-adjacent ⇒ owner approval whenever picked up**. **None is, or has
become, a blocking defect; nothing upgrades; no new rows (this phase discovered nothing).**

### Verification check-off (owner objectives + §3 criteria)

- Every finding in exactly one terminal state ✓ (census above) · findings-in = rows-out ✓
- All 11 CF rows remain CLOSED ✓ (disk re-verified) · pins 31/31 green (FIX-D) ✓ · terminal
  battery 1530/1530 (FIX-E) ✓ · docs obligations zero outstanding (FIX-F) ✓
- **Design Record honored throughout:** F-D1 "NONE" → zero promotions occurred (queue empty
  end-to-end) ✓ · F-D2 "CONFIRMED EMPTY" → zero gated work performed ✓ · F-D3 "CONFIRMED" →
  §6.6 stands unamended, permanence intact ✓
- **Frozen order held:** FIX-0→A→B→C→D→E→F→G, one sub-phase per owner order, none skipped,
  none reordered; no contract modification beyond the designated Appendix A fill ✓
- **§3 criteria: 7/7** — (1) ledger exists, append-only, every finding rowed with one class +
  state ✓ (2) work-item lifecycle: zero Phase-4 work items arrived; the 11 pre-closed rows
  carry per-transition evidence via their cited certification sections ✓ (3) every
  non-work-item row carries its route ✓ (4) zero scope creep: phase diff = the §9 always-docs
  set ONLY (ledger · status file · DOCUMENTATION_INDEX · Appendix A · memory), zero app files
  — mtime-census-proven at FIX-F ✓ (5) battery green with reconciled arithmetic: 1530 = entry
  1530 + Σ0 pins, per-run history in FIX-E block ✓ (6) this reconciliation statement ✓
  (7) status file + backlog + memory synced at every close (backlog correctly required zero
  changes) ✓
- **No unresolved Phase-4 work remains.** Dated amendments: none needed (section stays empty).

### Carry-forward list for phases 5–22

1. **INFO fix-when-touched (owner F-D1: stay deferred exactly as documented):** #3 · #7 ·
   #8 · #10 · #11 · #12 · #13 — each with its written fix spec on the backlog row; plus the
   two approval-gated-if-ever-selected rows: **#9 (additive migration ⇒ U14)** and **#14
   (role-set-adjacent ⇒ owner approval)**; any future pickup runs through THIS contract's
   permanent lifecycle (§6.6).
2. **Infrastructure:** #1 (sequencer; future per-year PG sequence, migration-class) · #4
   (patterns_ai test-media isolation refactor; battery stays sequential fresh-DB law).
3. **Doc-drift → phases 6–7:** DD-1 (#6 RBAC.md table, permanently routed per F-D1) · DD-2 +
   DD-3 (DOCUMENTATION_INDEX stale Phase-2/3 certification rows) · DD-4 (patterns_ai README)
   · DD-5 (worker-cert meta-audit memory-only evidence — PHASE_06 §2.2 seed item 5, Phase 7
   materializes) · DD-6 (inventory orphan template + signals tombstone).
4. **Design-Record decisions that travel:** F-D3 permanence — this contract = the campaign's
   permanent implementation protocol; post-Phase-22 commit discipline replaces U2, all else
   unchanged (owner verbatim) · U10 enforcement flags stay OFF until R11 · S6
   reported_quantity retirement stays soak-gated → both belong in the Phase-21 open-items
   register · PHASE_03 D1–D4 recorded in their own contract.
5. **Immediate owner action queued by Phase 0:** snapshot REFRESH now due (post-Phase-4
   milestone, dashboard freshness row).

### Phase-21 readiness-certificate input (sentence form, to be cited verbatim)

> "Phase 4 (Confirmed Findings Implementation) closed 2026-07-13 CERTIFIED: every finding
> ever raised by the certification campaign (worker-cert + phases 1–3) is accounted in
> CONFIRMED_FINDINGS_LEDGER.md in exactly one terminal state; all 11 confirmed defects are
> FIXED + PINNED (31 green regression pins, coverage-audited) + CLOSED; zero open defects
> were carried into or out of the phase; zero backlog rows were promoted (owner F-D1 = NONE)
> and zero approval-gated items existed (owner F-D2 = CONFIRMED EMPTY); the terminal
> sequential fresh-DB battery re-certified the canonical baseline at 1530/1530 (9-app 1002 +
> patterns_ai 528); residual risk = 12 open backlog rows (#1/#4 infra · #3 polish · #6
> doc-drift routed to phase 7 · #7–#14 INFO fix-when-touched), all evidence-judged
> non-exploitable, each carrying a written fix spec."

### PHASE 4 VERDICT

**PHASE 4 — CONFIRMED FINDINGS IMPLEMENTATION: CERTIFIED. The phase is CLOSED.**

| Phase ledger item | Value |
|---|---|
| Findings accounted (all sources) | 100% — findings-in = rows-out, census above |
| Confirmed defects (campaign-wide) | 11 — ALL CLOSED (all pre-closed in-certification; 0 arrived open) |
| Phase-4 fixes / pins added / code changed | 0 / 0 / 0 (docs-only phase; queue empty by owner F-D1/F-D2) |
| Pin coverage | 31/31 verified (FIX-D), 0 gaps, 0 orphans |
| Battery | **1530/1530 GREEN** (FIX-E terminal, preserved through FIX-F/G — no code after FIX-E) |
| Owner Design Record | F-D1 "NONE" · F-D2 "CONFIRMED EMPTY" · F-D3 "CONFIRMED" — all honored |
| Backlog | 14/14 reviewed line-by-line; 2 resolved-historical; 12 open, correctly routed; nothing upgraded; nothing added |
| Protocol permanence | §6.6 in force — this contract remains the campaign's implementation protocol for phases 5–22 and beyond |

**Next campaign step: owner snapshot refresh (post-Phase-4, due now) → Phase 5
(Documentation Foundation) → DOC-0 ratification of R1–R12, owner-gated.**

# Dated amendments

_(none)_
