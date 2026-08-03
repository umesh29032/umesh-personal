# P19A — Production Readiness Functional Audit (Business Acceptance Audit)

**Date:** 2026-07-20 · **Trigger:** owner order (deployment PAUSED) after live 500 on
`POST /production/addas/XFB-002/layering/start/` · **Mode:** audit-only — no code, docs, or
deployment artifacts were modified. This report file is the sole new artifact.

**Verdict up front: NOT production-ready. 2 CRITICAL runtime defects block every
manufacturing scenario. Both are regressions introduced by the `erp-v1.0.0` release commit
(`90c1f2f3`, streams redesign). Deployment stays blocked until C-1/C-2 are fixed and the
scenario battery is re-run end-to-end.**

---

## 1. Executive Summary

- The reported crash is real, root-caused, and worse than a 500: **`start_layering` lost its
  `@transaction.atomic`** (a helper was inserted between the decorator and the function in
  commit `90c1f2f3`). Every layering worker-assignment POST now crashes with
  `TransactionManagementError` **after committing partial writes** (stage record + frozen
  rate snapshot, no roster, no history event). Layering is stage 1 of every product flow →
  **no Adda can start work. Scenarios A, B and C are all blocked at step 1.**
- A second CRITICAL was found by runtime smoke: the **worker report page 500s
  (`MultipleObjectsReturned`) on every multi-lane Adda** — the stage-record lookup is not
  lane-scoped. This kills Scenario B (Three-Patti / cross-fabric class) worker reporting on
  GET and POST, for all roles, and it crashes *before* the permission check.
- **Why the test suite is green while production 500s:** Django `TestCase` wraps every test
  in a transaction, so "select_for_update outside a transaction" can never fire in tests.
  This bug class is structurally invisible to the current battery (systemic finding H-2).
- Everything else is in materially good shape: a **precise repo-wide sweep found exactly one
  transaction-hijack instance (C-1)**; the expense app has **zero** instances of the bug
  class; single-writer discipline (ledger/history) **PASSES**; settlement lifecycle armor
  (locks, finalize/reopen guards, advisory-lock ordering) **PASSES**; URL/role walls hold in
  live probes (workers get 403 on all management surfaces, no money figures leak to worker
  pages).
- **Deployment gap independent of bugs:** a fresh production database gets only 4 stages,
  2 skills and 1 machine type from migrations. The other 18 operational stages, 8 operator
  skills, 4 machine types and all stage-access M2Ms exist **only as hand-made dev-DB rows**
  — there is no idempotent seed path (H-1). A seed plan is in §13/§14.
- Local DB is 100% test data (18 Addas, ~45 of 46 users) — fine for dev, but it means
  production must start from a fresh seeded DB, never from this one (§15).

**Coverage honesty (owner rule):** 2 of 5 audit sub-agents died on a session limit
(access-control deep audit; secondary-apps POST audit). Their scopes were re-covered in the
main thread in condensed form (live role probes, gate greps, service atomicity checks) —
recorded in §4/§19. Full runtime execution of every POST as every role was **not** possible:
C-1 blocks all flows at stage 1, and exhaustive POST replay would mutate the dev DB. The
scenario battery must be re-run after C-1/C-2 are fixed (§16).

---

## 2. Business Workflow Review (Scenarios A / B / C)

| Scenario | Status | Blocking finding |
|---|---|---|
| **A — Normal product, single layering/body/bundle** | ❌ BLOCKED at "assign workers → start Layering" | C-1 (all products) |
| **B — Three-Patti: multi-layering, panel lanes, merge, settlement** | ❌ BLOCKED twice | C-1 + C-2 (worker report 500 on any multi-lane Adda: layering / pattern / cutting lanes) |
| **C — Nikkar** | ❌ BLOCKED | C-1 (DEV-NICKAR-001 completed 2026-07-11 proves the flow worked pre-regression) |

Historical proof the flows are sound when the code works: settled journeys ₹801 (3-PATTI-009),
₹344.25 (LOWER-001), ₹633 (T-SHIRT-001), finalized settlements for SHA-001/GLDN-001/XFB-001,
and 9 completed Addas — all executed before the streams-redesign regressions. The workflow
design is not the problem; the v1.0.0 release commit's layering/report code paths are.

Static walk-through of the full lifecycle (create → layering → pattern → cutting → bundles →
barcode → generic stitching/finishing stages → complete → settle) found the rest of the chain
transaction-safe and permission-gated (per-URL table evidence in §3): all `complete_*`,
`reopen_*`, bundle, allocation, pool and settlement writers are `@transaction.atomic` with
correct lock ordering; the reopen skeleton IS lane-aware (contrast C-2).

---

## 3. Page-by-Page Audit (POST surface)

Full 81-row `/production/` URL inventory and 17-row `/expense/` inventory were produced
(view, POST?, atomic-safe?, gate per row). Summary of non-clean rows — everything not listed
here verified clean:

| URL | Verdict |
|---|---|
| `POST /production/addas/<code>/layering/start/` | **C-1 — guaranteed 500 + partial commits** |
| `GET/POST /production/addas/<code>/report/<stage>/` | **C-2 — 500 on multi-lane Addas** |
| `POST …/pattern/photos/add/`, `…/pattern/verify/`, `…/pattern/sizes/` | M-3 — lazy SR+rate creation runs non-atomic and *before* the skill gate |
| `POST …/layering/quick-create-roll/` | M-2 — rolls persist even when the attach gate then refuses (gate in 2nd transaction) |
| `POST …/report/<stage>/` (checklist mode) | M-4 — multi-transaction sequence; mid-failure leaves photos/verification committed, report unsubmitted |
| `POST /expense/expenses/`, `/expense/templates/`, `/expense/generate/` (+ machines assign, product archive/sizes) | M-6 — tampered non-integer POST ids → ValueError 500 (no money risk) |
| `POST …/review-reports/` bulk verify | L — row-by-row commits; mid-loop error commits earlier rows silently |
| `POST /production/stages/add|edit` | L — object save + M2M save unatomic |
| `…/pattern/photos/<pk>/remove/` | L — direct view write, no service/transaction |
| `create_bundle` / `advance_lane` / barcode SR helper | L — undecorated but all *current* callers atomic (latent C-1 class) |

GET smoke (super admin, 184 URLs): 134×200, 16 redirects, 13×404 (placeholder ids — correct),
17×405 (POST-only — correct), **1×500 = C-2**.

## 4. Role-Based Access Audit

Live probes this session (worker `utest@…`): 403 on adda-create, product-create, costing,
payroll, settlements, advances, machines; 200 on own-earnings and adda-detail (verified: **no
₹/cost/rate values render** for worker); production dashboards redirect. Sidebar middleware
URL wall works. Static: **zero raw `is_superuser` checks in views** (rule 6 holds); every
production/expense URL login-gated + role/skill/perm-gated per inventory tables; worker
report path enforces own-task ∩ live stage-access (C-3 predicate) — correct **except** C-2
crashes before the gate on multi-lane Addas (information-free 500, still wrong).
Signup routes confirmed unrouted (S2 intact). Machines/raw-materials/inventory/storefront
views all carry management/production mixins.
**Not re-verified this session** (agent died; prior V1.1 certification stands as baseline):
full browser matrix for accountant/listing_team/manager on every page. Re-run with the
scenario battery (§16). Data anomaly: **3 active users with `role=None`** (ids 11, 13, 22)
— their effective access should be verified or the accounts deactivated (M-7).

## 5. Multi-Layering Audit (highest-risk feature)

- Lane machinery itself is sound: `add_stream`/`cancel_stream` atomic + management-gated +
  reasons mandatory; per-lane SRs; join predicate (`preproduction_joined`) gates bundling
  (GAP-5); pool draw-down and reopen guards lane-correct; `resolve_stream` refuses ambiguous
  lane references.
- **C-2 is the multi-lane killer:** `WorkerReportView._resolve` uses an unscoped
  `get_object_or_404(AddaStageRecord, adda=…, workflow_stage__stage__code=…)` — 2+ lane SRs →
  `MultipleObjectsReturned` (uncaught) → 500. Dev DB has 15 (adda, stage) pairs with 2–5 SRs
  (NKB-001 ×4 lanes, SHA-001 ×5 cutting SRs, XFB-001/002, NKS-001, SHT-001, DEV-NICKAR-00x,
  LOWER-002) — every one of them 500s the report page today.
- Barcode/generic (post-join) stages correctly use single-SR lookups; reopen skeleton
  correctly branches lane-scoped vs post-join. Only the worker-report resolver missed the
  streams redesign.
- Bundle flow (create/add-pieces/item-delete/bundle-delete/ready-sets/merge-at-join) — all
  atomic, skill+post-join gated, consumed-count resync under row locks. Clean.

## 6. Stage Transition Audit

`advance_to_next_stage`: atomic; PAY-2 worker-credit block, C3 pending-report block with
super-admin-only audited override, cost freeze, F3 task resolution, pool materialization —
all wired. `advance_lane`: undecorated but all 4 callers atomic (L — decorate it).
Reopen: uniform skeleton (management-only, settled-stage refusal, transitive downstream-
consumer guard with actionable error, cost/rate refloat, pool clear). **PASS** apart from the
C-1-adjacent notes.

## 7. Bundle Flow Audit — PASS (see §5; all writers atomic + gated, counts resync locked).

## 8. Settlement Audit — PASS with one policy flag

Draft→finalize→reverse/supersede lifecycle: advisory lock 5374 → status re-check under
`select_for_update` → documented lock ladder (ADST → SR → WSC → WorkerProfile → WorkerAdvance,
workers sorted) — followed in code. Frozen items immutable; S5 reconciliation BLOCK behind
`ENFORCE_SETTLEMENT_RECONCILIATION` (default OFF per plan) with ADMIN-only audited override.
No silent post-finalize mutation path exists.
**M-1 (owner decision):** all money writes (advances, settlements, finalize, **reverse of a
FINALIZED settlement**, expenses) are gated `MANAGEMENT_ROLES = {super_admin, manager}` — a
plain manager can reverse finalized money; `accountant` can write nothing. Docs say this is
by design; the audit brief expected SA/accountant gating. Decide and record.

## 9. Payment / Payroll Audit — PASS

Single-writer discipline verified: `WorkerLedgerEntry.objects.create` exists in exactly one
place (`ledger_service.py:42`); reversal guards present; `*History` writes only via
`history_service`; SWA/PayrollSettlement/AddaSettlement/WorkerAdvance creates only inside
their documented writers. SA-only levers (pay-basis, F&F, write-offs, void expense, rerate,
reconciliation override) enforced **in the services**, not just views. Low: `update_payout_profile`
has no in-service gate (view-only protection).

## 10. Dashboard Audit

Production/worker/admin dashboards, A360, costing, stalled, pending-reports all 200 on smoke
with role-correct gating. `ON_HOLD`/`CANCELLED` tiles can never be non-zero (dead statuses,
M-5). Dashboard *data correctness* under live flow could not be re-verified end-to-end
(blocked by C-1) — include in post-fix battery.

## 11. POST Request Failure Register

| # | Endpoint | Failure | Confirmed |
|---|---|---|---|
| 1 | `POST /production/addas/<any>/layering/start/` | `TransactionManagementError` 500, partial commits | Live (owner) + static-certain |
| 2 | `GET/POST /production/addas/<multi-lane>/report/layering|cutting|cutting_pattern/` | `MultipleObjectsReturned` 500 | Live (this audit, GET; POST shares `_resolve`) |
| 3 | Tampered non-int ids on expense/machines/product POSTs | `ValueError` 500 | Static-certain (M-6) |

## 12. Runtime Exception Register

1. `TransactionManagementError: select_for_update cannot be used outside of a transaction` —
   `worker_task_service.py:68` via `start_layering` (C-1).
2. `production.models.AddaStageRecord.MultipleObjectsReturned: get() returned more than one
   AddaStageRecord -- it returned 2!` — `worker_report_views.py:170` (C-2), reproduced on
   XFB-002 as super admin and worker.

## 13. Database Seed Recommendations

Fresh-DB migration output today: 4 stages (layering, cutting, cutting_pattern,
barcode_generation), 2 skills, 5 roles, 1 machine type, 4 categories, 21 sidebar rules,
raw-material masters. **Missing (dev-DB-only, hand-created):** 18 stitching/finishing/dispatch
stages (ids 19–48), 8 operator skills, 4 machine types (Overlock/Flatlock/Single-Needle/
Elastic), "Printing" category, all `access_by_skill`/`access_by_role` M2Ms for the 18 generic
stages. **Exclude from any seed:** junk stages `verify`, `verify-86f27f0a`, `cross_cutting`
(ids 5/6/11, inactive, 0 usage). Physical `machines.Machine` rows (OL-001 …) are per-factory
assets — do NOT seed. Per-product `WorkflowStage` flows + rates are factory configuration —
do NOT seed (document as day-1 setup instead).

## 14. Master Data Synchronization Plan (design only — no code written)

One management command, `sync_master_data` (or `sync_stage_library`):
- **Source:** a versioned JSON/py manifest in-repo (exported once from dev DB minus junk):
  StageCategory → MachineType → Skill → Stage (natural key = `code`/`name`) → stage access
  M2Ms (by skill/role code) → SidebarItemRule deltas.
- **Idempotency:** `update_or_create` on natural keys; M2Ms via `.set()`; never delete rows
  it didn't create; report created/updated/unchanged counts. Safe to run every deploy
  (runbook step), same contract as `accounts/0016/0017` seed migrations.
- **Guard:** refuses to touch rows whose natural key exists with conflicting identity unless
  `--force`; `--dry-run` prints the diff.
- Roles/sidebar already migration-seeded — the command only tops up the operational library.
- Alternative (data migration) rejected: library will keep evolving; a re-runnable command
  beats a migration chain.

## 15. Test Data Cleanup Recommendations (nothing deleted; recommendations only)

- **All 18 Addas are dev/test** (3-PATTI-0xx experiments, DEV-*, XFB, GLDN, SHT, SHA, NKB,
  NKS, LOWER-00x, T-SHIRT-001). All 15 products likewise dev-flavoured. 9 settlements,
  170 ledger rows = the pinned dev sentinel (Σ₹10,880.25) — keep for dev verification.
- **Users:** 1 real (owner). Junk to deactivate: `verify-test@test`, `verify-86f27f0a@test`,
  `nexttest@t.com`, `testuser@t.com`, `w1@test`, `test_worker@test.com`, `worker_direct@…`
  (ids 6,7,9,11,12,13,22). **Fix or deactivate the 3 role=None users (11/13/22).**
- Junk stage rows 5/6/11 — archive-only today; exclude from seed.
- **Primary recommendation: production = fresh DB + migrations + `sync_master_data` + day-1
  factory setup. Never promote this dev DB.** Dev DB cleanup is then optional hygiene.

## 16. Deployment Blockers

1. **C-1** layering start (fix + regression test).
2. **C-2** worker report on multi-lane (fix + regression test).
3. **H-1** master-data seed path (§14) — without it a fresh production DB cannot run the factory.
4. **H-2** add non-`TestCase` coverage: at minimum one `TransactionTestCase`/live-server smoke
   that POSTs every `*-start`/`*-complete`/report endpoint (would have caught C-1 and C-2).
5. Re-run Scenarios A/B/C end-to-end (all roles, mobile+desktop) after 1–4 — this audit could
   not runtime-certify past stage 1.
6. Owner decision on M-1 (money-write gate level) recorded before go-live.

## 17. Recommended Fix Priority

| Priority | Items |
|---|---|
| **P0 (before anything)** | C-1 (move `@transaction.atomic` to `start_layering`; fix stale "all 6 callers" contract comment), C-2 (lane-scope `_resolve` via `lane_stage_record`/stream param), then full scenario re-run |
| **P1 (pre-deploy)** | H-1 seed command, H-2 transaction-real test tier, M-7 role=None users |
| **P2 (pre-deploy, small)** | M-2 quick-create-roll gate order, M-3 pattern lazy-SR (atomic + gate-first), M-6 int-parse POST ids, M-1 owner ruling |
| **P3 (post-deploy hygiene)** | M-4 checklist sequence, M-5 dead statuses / pause-resume-cancel decision, L-cluster (advance_lane/create_bundle decorators, stage M2M txn, photo-remove service, review-loop UX, payout-profile service gate, admin delete-permission, junk rows/users) |

---

## 18. Finding Register (consolidated)

| ID | Sev | Where | Defect |
|---|---|---|---|
| C-1 | Critical | `production/stages/layering/service.py:247–260` | `@transaction.atomic` hijacked onto `_layering_workflow_stage`; `start_layering` autocommits → TME 500 + committed partial writes (SR, rates; possible stray `CuttingStream`). Regression in `90c1f2f3` (erp-v1.0.0). |
| C-2 | Critical | `production/views/worker_report_views.py:170-172` | SR lookup not lane-scoped → `MultipleObjectsReturned` 500 on multi-lane Addas, GET+POST, pre-permission. |
| H-1 | High | deployment | No idempotent seed for operational stage library / skills / machine types / access M2Ms. |
| H-2 | High | test architecture | `TestCase`-only battery cannot detect missing-transaction class; no live-request POST tier. |
| M-1 | Medium | expense services | Money writes manager-gated (incl. reverse of finalized settlement); accountant write-less. Design-vs-brief — owner call. |
| M-2 | Medium | `stage_views.py:655-733` | quick-create-roll: rolls persist when attach gate refuses (gate in 2nd txn). |
| M-3 | Medium | `cutting_pattern/service.py:136` + 3 views | Lazy SR+rate creation non-atomic and before skill gate (photos/verify/sizes). |
| M-4 | Medium | `cutting_pattern/handler.py:104-147` | Checklist submit = txn sequence; mid-fail leaves partial committed state. |
| M-5 | Medium | adda lifecycle | ~~No pause/resume/cancel writers; ON_HOLD/CANCELLED dead; no delete path (PROTECT-safe — good); AddaAdmin delete → ProtectedError 500.~~ **RESOLVED 2026-07-22 (ADR-0012):** super_admin `cancel_adda` (writes CANCELLED) + `delete_adda` (pristine-only, money-guarded) shipped; AddaAdmin delete disabled (no more ProtectedError 500). `test_adda_delete` 19/19. |
| M-6 | Medium | expense views 449/544/631, machines assign, product_views 95/99/121 | Non-int POST ids → ValueError 500. |
| M-7 | Medium | accounts data | 3 active users with role=None; junk test accounts active. |
| L-1..L-11 | Low | various | `advance_lane`/`create_bundle`/barcode-SR-helper undecorated (latent C-1 class); `_ensure_bundling_open` displaced decorator; Stage M2M unatomic; pattern-photo-remove direct write; review bulk-loop partial-commit UX; `update_payout_profile` ungated in service; stale contract comment `worker_task_service.py:21`; junk stage rows 5/6/11; `collar_attach` unused; fnf multi-txn (documented design). |

## 19. Audit Method & Coverage Record (honesty log)

- Main thread: root-cause + regression blame (git `-L`); precise repo-wide decorator-hijack
  scanner (1 hit); select_for_update × atomic call-chain verification across production/
  expense/pool/rate/worker-task/raw-materials/barcode services; 184-URL GET smoke (super
  admin) + 16-URL role probe (worker); read-only DB census (Addas, users, roles, skills,
  stage library, SR duplicates, settlements); worker money-leak page check.
- Sub-agents: production POST surface (81-URL inventory) ✅; expense/settlement audit ✅;
  stage-library + Adda-lifecycle + seed census ✅; **access-control deep agent ❌ FAILED
  (session limit)**; **secondary-apps POST agent ❌ FAILED (session limit)** — both scopes
  re-covered main-thread in condensed form (§4, machines/raw/inventory/accounts/storefront
  gate + atomicity checks). No area is marked clean on agent silence; per-URL claims trace
  to file:line evidence read in-thread or in completed agent reports.
- **Not done (needs post-fix battery):** runtime POST execution of full flows (blocked by
  C-1), per-role browser matrix re-run, mobile/tablet layout re-verification, dashboard
  number reconciliation under live flow.

---
---

# P19A-2 ADDENDUM — Exhaustive Runtime Pass (same day, owner-ordered "everything, 100%")

Second pass closed the §19 gaps. Method: **1005-URL real-object-id GET sweep × 5 roles
(≈5,025 authenticated requests)** · live login probes for 9 accounts · **POST battery with
real (autocommit) requests against a full DB copy in `inventory_seed_scratch_1`** (scratch
law respected; copy dropped after) · **paisa-level money recompute on the real dev DB
(read-only)** · mobile/tablet/desktop screenshot verification of the worker report surface.
Dev DB was not mutated at any point; the only writes happened on the scratch copy.

## A. Runtime 500 census — COMPLETE

| Class | Count | Verdict |
|---|---|---|
| C-2 worker-report `MultipleObjectsReturned` | 20 URLs deterministic, ALL roles, GET+POST (reproduced live + on scratch POST). Worst case 6 SRs (GLDN-001 layering). Crashes BEFORE the permission gate — even accountant/listing get 500 instead of 403. | The **only** deterministic 500 left in the app |
| **NEW H-3** — Postgres connection exhaustion | Transient 500s under sustained browsing: `FATAL: sorry, too many clients already`. Root cause: `CONN_MAX_AGE=600` ([base.py:172](../config/config/settings/base.py#L172)) + dev `runserver` thread-per-request leaks connections (48 idle observed) until `max_connections=100` saturates. **This explains the owner's "random" 500s during manual testing.** Production is bounded (3 sync gunicorn workers = 3 connections) — safe as certified, but any threaded serving (gthread, extra daemons) reopens it. Recommend: `CONN_MAX_AGE=0` in dev settings + runbook note. | High (dev), documented-risk (prod) |
| C-1 layering start | Reproduced with a real POST on the scratch copy: `TransactionManagementError`, exactly as live. | Confirmed |
| M-6 tampered ids | Reproduced live on scratch: `ValueError: Field 'id' expected a number but got 'abc'` → 500. | Confirmed |

Everything else in 5,025 probes: clean. Non-200s fully accounted (403 walls, 404 unstarted
stages/absent rows, 405 POST-only, legit redirects).

## B. Access-control matrix — CLOSED (was agent-failure gap in §19)

- **No unauthorized 200 anywhere** across super-admin/manager/accountant/listing/worker on
  1005 URLs. Manager's 403 set = exactly the SA-only surface (product config, stage-rates,
  user/skill/role admin, BOD). Worker sidebar shows only My Dashboard/My Earnings.
- Worker positives verified live: assigned worker 200 on own report; unassigned worker 403
  (two different accounts); adda history visible ONLY for addas the worker worked
  (assignment-scoped isolation ✓); roll pages render zero ₹/price data to workers ✓.
- **NEW M-8 (High, business)** — the everyday "assigned users" trap: management can assign a
  worker who LACKS the stage's access skill (`set_stage_workers`/`start_generic_stage` have
  no skill check — verified by live POST: unskilled worker accepted onto NKS-001
  side_seam_close). The worker then gets **403 on their own assigned task** (predicate =
  access ∩ assignment). One live mismatch exists in dev DB (dev.cm.b → NKB-001
  side_seam_close). Fix direction (owner call): enforce stage-access at the roster write, or
  filter assignable workers everywhere the roster UI offers them (layering start already
  enforces cutting_master; generic stages don't).
- **M-1 sharpened:** accountant is a functionally dead role — 23 of 1005 pages (own pages
  only); every expense/payroll/settlement surface is `_ManagementOnly`. Decide its intended
  surface before deploy.
- `/inventory/styleguide/` renders for every role incl. worker (Low — dev page, gate it).

## C. Everyday worker chain — PASS end-to-end (real POSTs, scratch copy)

`manager allocate (color/size) → worker sees exactly his allocated dims (Black/Free Size,
labels only — blind reporting ✓) → draft → submit → task COMPLETED → WSC good=3 alter=1
(S3 dual-write reported=good ✓) → manager review sets verified_quantity=3 ✓`.
Also PASS with real POSTs: adda create (3-PATTI-013 on scratch), machine assign/release,
generic stage start, **settlement finalize** (XFB-001 draft → finalized; ledger wrote
12.00×0.5=6.00 + 9.00×0.5=4.50, expected 10.50 — arithmetic correct to the paisa).
UX note (not a bug, is the OP-1 design): on pool stages an assigned-but-unallocated worker
sees "Nothing assigned to you yet — ask your manager" and CANNOT report until the manager
allocates. Two management steps (assign + allocate) — train supervisors on this, it looks
like a bug on the floor.

## D. Worker report surface, mobile/tablet/desktop — PASS (rule-11 certification evidence)

Screenshots at 360×740 / 768×1024 / 1440×900 (assigned worker, live dev server): hero +
numbered panel + card-style work lines + sticky Submit/Save-Draft bar on all three;
`scrollWidth == clientWidth` at 360px (no horizontal scroll); viewport meta present;
33 data-label/responsive markers. Desktop shows correct minimal worker sidebar.

## E. Money accuracy — 100% PASS (read-only recompute, real dev DB)

| Check | Result |
|---|---|
| Ledger sentinel | 170 entries, Σ₹10,880.25 — **exact** (credits 8,346.25 / debits 2,534.00) |
| SWA internal math (`amount = qty × rate`) | 141/141 rows **exact** |
| Every finalized settlement: Σ active lines == Σ ledger credits | 6/6 **exact** (1,500.00 · 344.25 · 801.00 · 633.00 · 1,254.75 · 1,279.25) |
| Supersede armor | Superseded settlements: all lines voided (active Σ=0); their 2,534.00 of credits exactly offset by 2,534.00 reversal debits — **net payable ₹5,812.25 = Σ finalized, balances to the paisa** |
| Golden journeys | LOWER-001 = ₹344.25 ✓ · T-SHIRT-001 = ₹801.00 ✓ · 3-PATTI-016 = ₹633.00 ✓ (all exact) |
| Era-B guard | 0 stage-earning credits exist without a settlement — settlement is provably the only money boundary |
| Manufacturing cost freezes | per_piece `rate × qty == frozen processing_cost` — 0 mismatches across all completed stages; per-adda Σ computed (e.g. T-SHIRT-001 ₹801.75, 3-PATTI-016 ₹633.75, SHA-001 ₹1,265.00) |
| Worker-stage cross-check | Σ SWA allocated per (worker, stage) == Σ WSC good (e.g. LOWER-001 19+17=36 ✓) |

## F. Register updates

- Add **H-3** (connection exhaustion — dev fix + prod runbook note) and **M-8**
  (assign-without-skill = dead assignment) to §18.
- POST Failure Register: C-1, C-2(POST), M-6 now runtime-CONFIRMED; everyday chain,
  settlement finalize, machines, adda create runtime-PASS.
- §16 blockers unchanged: C-1, C-2, H-1, H-2 (+ M-8 strongly recommended pre-deploy —
  it manufactures floor confusion daily); M-1/accountant decision for owner.
- §19 coverage gaps from the failed agents: **now closed by this pass.**

---
---

# P19A-R1 FIX LOG (2026-07-20, same day — owner hit C-1 live again and ordered the fix)

Audit-only phase ended when the owner re-reported the layering-start 500 during live
roster updates. P0 applied:

| Finding | Fix | File |
|---|---|---|
| **C-1** | `@transaction.atomic` re-bound to `start_layering` (helper had hijacked it); stale "all 6 callers" contract comment corrected | [layering/service.py](../config/production/stages/layering/service.py) · [worker_task_service.py](../config/production/services/worker_task_service.py) |
| **C-2** | `WorkerReportView._resolve` lane-aware: worker's own non-cancelled tasks pick the SR (open task preferred), optional `?stream=<id>` narrows, no-SR → 404, no-task → 403. Single-lane byte-identical | [worker_report_views.py](../config/production/views/worker_report_views.py) |
| **H-3 (dev)** | `CONN_MAX_AGE = 0` dev-only override (production untouched — 3 sync workers stay on base 600) | [settings/local.py](../config/config/settings/local.py) |

**Regression tests (the H-2 tier begins):** [production/tests/test_p19a_regressions.py](../config/production/tests/test_p19a_regressions.py)
— `LayeringStartTransactionTest` (TransactionTestCase + REAL POST: the only shape that can
see the C-1 class) + `MultiLaneWorkerReportTest` (2-lane world: assigned 200 on own lane,
stream narrowing isolated, unassigned/management 403 not 500, unstarted 404). 6/6 green.

**Verification:** focused battery 84/84 green (streams, layering workflow+handler, unified
tracking, worker-role certification, dispatch parity, OP-1 ops+hardening, golden path,
R10-B generic, P19A). Live on dev server: `POST /production/addas/XFB-002/layering/start/`
(stream 36, the owner's exact failing case) → **302, task row written, WORKERS_ASSIGNED
history logged**; all 20 formerly-500 report URLs → 403/200 correctly; assigned worker on
NKB-001 cutting → **200**; full **1005-URL re-sweep: ZERO 500s** (789×200, rest =
correct 403/404/405/redirects).

Docs-sync: this log + `docs/apps/production/GUIDE.md` (worker_task_service + views rows) +
kos `debugging/page-slow-or-erroring.md` case file. Still open from the audit: H-1 seed
command, M-8 assignment-skill enforcement (owner call on direction), M-6 id-parse
hardening, M-1/accountant decision, remaining M/L hygiene.

---
---

# P19A-E2E — Live Browser Business Run (2026-07-20, owner-ordered: new Nikkar + 3-Patti addas, full money flow, all dashboards)

Everything below executed IN THE BROWSER on the live dev server, as the real roles
(manager `dev.mgr`, workers `utest`/`dev.cm.b`/`dev.cm.a`, super admin), on freshly
created DEV data. Evidence screenshots in the session scratchpad.

## What WORKS end-to-end (browser-verified)

1. **Flow config UI (SA):** NIKKAR cutting rate set to ₹5/pc via the flow editor
   ("Updated cost for 'Cutting'" + DB verified).
2. **Adda creation UI (manager):** NIKKAR-001 and 3-PATTI-013 created from the Start
   Adda form.
3. **The fixed C-1 button live:** "Update workers" on layering — assigns roster,
   writes tasks + history ("Layering stage started — workers assigned"), twice.
4. **Worker layering flow (utest):** roll picker → attach SHA-R4 (weight auto-fills)
   → phone-style report (10 layers) → submit → breakup + leftover validation message
   ("Fill the breakup for every roll… Missing — layer count / leftover") → complete
   → auto-advance to Cutting. Layering cost correctly ₹0 (grouped into cutting).
5. **Legacy cutting console:** 40 pieces + worker + complete → adda COMPLETED, cost
   frozen ₹200 (40×5), 40 barcodes auto-generated, View/Print QR pages live.
6. **Parallel worker reporting (3-PATTI-013):** utest submits 6 layers, dev.cm.b
   submits 4 layers from separate sessions — two independent contribution rows, both
   visible in DB and on the manager's workspace roster.
7. **Manager review UI (SHT-001):** reported-vs-verified inputs + VOID REPORT door
   render per line (screenshot); saving a verified qty works (earlier battery).
8. **Advance UI:** ₹50 advances recorded for utest and dev.cm.a.
9. **Settlement lifecycle UI:** queue → draft ADST-0012 (per-worker lines 180×0.50 +
   2×0.50 = ₹91; 91×0.50 = ₹45.50; total ₹136.50) → **Recover-advances section lists
   dev.cm.a's ₹50 with a per-advance recover box** → recovered ₹30 → finalize →
   "earnings booked": ledger credits 90+1+45.50 AND debit advance_recovery 30. Wrong
   draft discard also tested (ADST-0012 SHT draft discarded cleanly first).
10. **Worker money view (dev.cm.a, mobile+desktop):** Payable ₹61 (91−30), Expected
    ₹595 (unsettled), Earned ₹91, **Advance Outstanding ₹20**, Paid ₹0 — every state
    exact.
11. **Cash payment UI:** workers/…/settle prefills payable ₹61, explains "advance
    recovery happens at Adda settlement, not here", pays SETL-0001 ₹61 → Paid ₹61.
12. **Expenses:** electricity ₹1,800 + rent ₹12,000 recorded; recurring template
    (Internet ₹999/monthly) created → Generate July = 1 row → re-run says "Nothing
    to create" (idempotent, as designed).
13. **Dashboards all LIVE (SA):**
    - **BOD:** month expenses ₹25,299 with category split (Rent 12,000 · Salary 9,000
      · Electricity 3,300 · Other 999) — exactly the recorded entries; **Outstanding
      Worker Payments ₹5,857.75** (= 5,812.25 + 136.50 − 61 paid − 30 recovered,
      paisa-exact); **Outstanding Advances ₹70** (50+20, exact); Expected Payouts
      ₹10.50 (XFB-001 ready); Active Addas 11; Work-by-Stage includes the new addas;
      roll stock dropped to 1 after the attach.
    - **Ops dashboard:** NIKKAR-001 + 3-PATTI-013 listed live.
    - **Material spend:** ₹110,173.50 net cloth consumed this month at purchase-price
      truth, with an honest "4 rolls without purchase price — never counted as ₹0" warning.
    - **Costing:** Σ frozen stage cost ₹9,012.75 — matches independent hand-sum;
      NIKKAR's ₹200 correctly UN-froze when cutting was reopened.
    - **Payroll:** Total Pending Payable ₹5,857.75 (matches BOD).

## NEW FINDINGS from the live run

| ID | Sev | Finding |
|---|---|---|
| **E2E-1** | **High (money)** | **Legacy cutting console pays nobody and there is NO UI recovery.** On patternless products (Nikkar class), "Complete Cutting → Generate Barcodes" freezes the OWNER cost (₹200) and marks checked workers' tasks completed — but creates **zero WorkerStageContribution**. Consequences, each verified live: settlement draft says "No settleable lines"; worker's report page shows "submitted, 0 lines, LOCKED"; manager's review page says "No submitted reports" (the void-report door only renders for rows WITH lines); reopen unfreezes cost but the born-completed task stays locked. Worker earns ₹0 silently, unfixable outside DB surgery. Certified products avoid this via the workspace/report path; Nikkar-class daily work hits it head-on. Fix direction: legacy complete must route worker credit through contributions (or be retired for a workspace path on patternless products). |
| E2E-2 | Medium | `WIDTH_CHOICES = 36–44"` ([raw_materials/models.py:99](../config/raw_materials/models.py#L99)) but stock contains 60" rolls — layering width-verify cannot state the true width (had to record 44"). Intake and verify disagree on the width domain. |
| E2E-3 | Low | Completed-adda cutting panel (legacy branch) hides the Reopen button — reopen URL works but has no UI door from that state. |
| E2E-4 | Low | Flow editor: saving a rate on a GROUPED stage 302s with no visible error/success — silent no-op confused this test twice; surface the refusal. |
| E2E-5 | Info | Settlement queue simply omits addas with no settleable lines — correct, but the adda-page "Start Settlement" button then opens an empty draft; queue could say why. |
| E2E-6 | Info | C3 pending-report confirm dialog fired correctly at layering complete (warned about DEV-CM-A's unsubmitted report). |

Test data created (all DEV, kept for owner inspection): NIKKAR-001 (reopened at cutting),
3-PATTI-013 (layering, 2 reports), ADST-0012 finalized ₹136.50, SETL-0001 ₹61 payment,
advances utest ₹50 / dev.cm.a ₹50 (₹20 outstanding), expenses elec ₹1,800 + rent ₹12,000 +
recurring Internet ₹999, roll SHA-R4 consumed.
