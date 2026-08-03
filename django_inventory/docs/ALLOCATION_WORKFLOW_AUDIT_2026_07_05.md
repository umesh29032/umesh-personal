---
id: allocation-workflow-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Allocation Workflow Audit — 2026-07-05 · ✅ COMPLETE (findings at bottom, awaiting owner approval)

> Owner order: business-workflow validation of the OP-1 multi-worker engine —
> browser-proven evidence, findings grouped Critical/High/Medium/Low, root
> cause + smallest architecture-preserving fix, **NO implementation until
> owner approves**. This doc = the resume anchor for a fresh session.

## Audit world (already built — do NOT rebuild)

- **Sleeve Join stage** created VIA UI (config-only re-proof): `sleeve_join`,
  work_type=machine, machine_type=**Overlock Machine** (MachineType-reuse
  proof), category=Stitching, skill `sleeve_operator`. In 3-PATTI flow
  order 6, per_piece ₹3, pays workers, split=Colour+Size.
- **3-PATTI flow now:** 1 layering(none·10·no-pay) · 2 cutting_pattern(none·500·pays)
  · 3 cutting(color_size·100·pays) · 4 barcode(none) · 5 overlock(color_size·5·pays)
  · 6 sleeve_join(color_size·3·pays). (Layering was briefly mis-edited by a wrong
  form match during setup; restored exactly — verify no drift if suspicious.)
- **DEV workers** (password all `Dev@12345`, role worker):
  dev.ow.a/b/c@test.local (skill overlock_operator) · dev.sw.a/b@test.local
  (skill sleeve_operator). Overlock stage skills = cutting_master + overlock_operator.
- **Fixture Adda `3-PATTI-013`** (ORM fixture, DEV-marked): stages 1-4 completed
  rows, CuttingRecord pieces_cut=50, **APSCPB Red·Size 1 = 50** (owner's exact
  example), overlock SR started, OW-A/B/C rostered. current_stage=overlock.
- Server: `env/bin/python config/manage.py runserver 8003` (MINE; owner's 8000
  never touched). Browser CLI: `$HOME/.claude/skills/gstack/browse/dist/browse`
  (syntax: `fill <sel> <val>`, `viewport 390x844`; `type` = focused-element only;
  NEVER `querySelector('form')` — grabs the sidebar logout form).
- Flag state: `ENFORCE_ALLOCATION_BOUND` env-driven (config/settings/base.py:190),
  currently **OFF** (default). ON-phase = restart server with
  `ENFORCE_ALLOCATION_BOUND=True` env var.

## Evidence so far (flag OFF = current dev truth)

| Q | Scenario | Result | Verdict |
|---|---|---|---|
| P1-6 (alloc ceiling) | Manager allocates 55 vs snapshot 50 | **REFUSED** "Cannot allocate 55: only 50 available" | ✅ SAFE (always-on) |
| P1-6 cumulative | 20(OW-A)+25(OW-B) ok → next 10 | **REFUSED** "only 5.00 available" | ✅ SAFE — Σ allocations can never exceed cutting snapshot. Screenshot `audit_q8_ceiling.png` (scratchpad) |
| P1-2 (report > allocation) | OW-A allocated 20, reports 25 | **ACCEPTED** + soft warning "Allowed now, but refused once allocation enforcement is on" | 🔴 HOLE while flag OFF |
| P1-3 (report > snapshot) | OW-B allocated 25, reports 55 (>50 cut) | **ACCEPTED** + same warning | 🔴 HOLE while flag OFF |
| P1-3 combined | Board total 25+55+5 = 85 vs snapshot 50 | accepted | 🔴 same root |
| P1-1 (report w/o allocation, UI) | OW-C (rostered, 0 allocation) report page | Chips empty + "Nothing assigned to you yet — ask your manager"; submit → "Line 1: Colour is required" | ✅ UI structurally blocks on COLOR_SIZE stages |
| P1-1 (report w/o allocation, FORGED POST) | OW-C posts `line-0-color_id=1&size_id=4&reported_quantity=5` via fetch | **ACCEPTED — task COMPLETED, contribution (Red,S1,5.00) written** | 🔴🔴 **CRITICAL**: `_parse_lines` int()s choice values but never validates membership in schema options; with flag OFF nothing else stops it |

**Root causes identified so far:**
1. `ENFORCE_ALLOCATION_BOUND=False` = the designed rollout state, but OP-1
   shipped the allocation UI — the ramp is over; flag should turn ON (that one
   flip closes P1-1/2/3/4 at `complete_worker_task`, always at the single
   chokepoint). Smallest fix: set env True in dev + runbook step, keep flag as
   emergency-off lever.
2. Choice-membership gap: worker report accepts ANY int for `color_id`/`size_id`
   regardless of schema options (worker_report_views `_parse_lines`). Smallest
   fix: validate `raw in {o['value']}` per choice field at parse time (view-level,
   schema-driven, no service change). Independent of the flag (defence-in-depth +
   correct dims even when allocation isn't the gate, e.g. cutting).
3. (code-read, to browser-prove) `set_verified_quantity` has NO ceiling vs
   allocation/pool — manager can verify 100 on a 20-allocation; settlement pays
   verified-else-good. Candidate: WARN (not block) at Report Review + reconciliation
   already catches over_allocated at settlement finalize (S1.1 evidence + S5 gate).

## Remaining steps (resume here)

1. **Flag-ON phase**: restart 8003 with `ENFORCE_ALLOCATION_BOUND=True`; fresh
   worker (create dev.ow.d or void/reuse OW-C? OW-C task now COMPLETED via forged
   post — use a NEW worker): prove P1-1 refusal (0 allocation → submit refused),
   P1-2 (12 vs 10 refused), P1-4 (good8+alter2+missing1=11 vs 10 refused; exactly
   10 passes). NOTE: flag-ON check runs at complete (submit), evaluated per
   reported dim incl. alter+missing.
2. **P1-5 reopen/verify limits**: browser-prove reopen of cutting on 013 →
   REFUSED by downstream-consumer guard (allocations exist on overlock);
   reopen overlock after complete → allowed, SPS cleared+refrozen on re-complete;
   verify-edit 100 via Report Review → accepted (finding #3 evidence) + settled-line
   refusal (already gate-tested, cite test).
3. **Part 2 visibility matrix**: per worker (OW-A assigned · OW-C skilled-unassigned
   after his task cancelled? note his forged COMPLETED task = assigned →
   sees overlock; document) · SW-A/B see NOTHING until sleeve assigned; assign
   SW-A mid-audit → appears; revoke sleeve_operator from SW-A → dashboard/menus/
   panel/report all gone immediately (one live predicate). Also: workers never see
   cutting quantities / other workers / mgmt pages (spot URLs: /production/costing/,
   payroll, machines, A360, report-review).
4. **Part 3 manager board**: 013 overlock board answers who-working/finished/pending
   (statuses + G/A/M + allocated + verified + expected ₹). Screenshot.
5. **Part 4 traceability**: follow Red·S1 story — cutting breakdown (APSCPB) →
   allocations → contributions (dims) → verification → SPS → processing_cost →
   settlement lines (use 3-PATTI-011 for a real settled story; 013 money story after
   corrections). Machine linkage = derivable only (MachineAssignment window vs
   WSC.created_at; no stamp on WSC) — candidate Low/Medium finding.
6. **Part 5 mobile UX @390**: worker dashboard/panel/report — one-question test;
   improvement list (recommendations only).
7. **Findings doc**: this file → final form, severity-grouped, root causes, smallest
   fixes. **STOP for owner approval. No code changes.**

## Constraints in force
Frozen architecture (6 rules) · no new money paths · single-writer services ·
audit-first (no fixes without approval) · 3-PATTI only · owner's 8000 servers
untouched · checkpoint policy (tree stays uncommitted).

---

# ✅ AUDIT COMPLETE — FINDINGS (2026-07-05) · STOP for owner approval

**Method:** every claim below is browser-proven on 8003 (super-admin + 6 DEV
workers) with DB confirmation, plus a 2-agent read-only code census (single-calc
path + correction/race paths). No app code changed. Test world = Adda
`3-PATTI-013`, Overlock stage (Colour+Size grain, ₹5/pc, good-only pay), cutting
snapshot Red·Size 1 = **50**.

## Answers to your 8 questions

| # | Question | Answer | Proof |
|---|---|---|---|
| 1 | Report without an allocation? | **Flag OFF: YES** (forged POST writes a COMPLETED contribution). **Flag ON: NO** (refused "only 0 allocated"). | prior OW-C forge; this run OW-D forge @flag-ON refused |
| 2 | Report more than allocated? | **Flag OFF: YES** (+soft-warn). **Flag ON: NO** (good 12 vs 10 refused). | OW-D 12>10 refused |
| 3 | Good+Alter+Missing exceed allocation? | **Flag OFF: YES**. **Flag ON: NO** — the bound sums good+alter+missing (8+2+1=11>10 refused; 8+1+1=10 passes, pays ₹40 good-only). | OW-D boundary run |
| 4 | Multiple workers exceed the Cutting snapshot? | **NO for allocations** (always-on ceiling). **YES for reports when flag OFF** (Σ reported 93 vs 50 cut). | Σ alloc 45≤50; reports 25/55/5/8 all accepted flag-OFF |
| 5 | Allocations exceed the snapshot? | **NO — always safe** (advisory-locked, flag-independent). | 55>50 refused; cumulative "only 5 available"; concurrent race |
| 6 | Reopen / verify / correction bypass limits? | **Reopen: NO** (downstream guard). **Verify: YES — unbounded** (High). **Void-after-report: YES — strands** (High). | below |
| 7 | Race / double-submit break limits? | **Allocate race: NO** (advisory lock). **Report save_draft: partial GAP** (writes unbounded rows; clobber window). | below |
| 8 | One calculation path? | **YES** — census maps a single chain; the only other writers are a documented rerate mirror + read-only previews. | census |

## Severity-grouped findings

### 🔴 CRITICAL

**C-1 — Both integrity flags ship OFF; in the default config nothing enforces the
allocation ceiling or settlement reconciliation.**
`ENFORCE_ALLOCATION_BOUND=False` (base.py:190) and
`ENFORCE_SETTLEMENT_RECONCILIATION=False` (base.py:197). With the shipped
defaults: every over-report is accepted (Q1–Q4 flag-OFF), and at finalize the
over_allocated reconciliation only **WARNs** — it does not block
(adda_settlement_service.py:487 gated on the flag). Net proven on ONE dimension:
Red·S1 was cut **50**, yet the current payable state settles to **₹840**
(=₹500+₹275+₹25+₹40) — 3.4× the ₹250 ceiling — with only a soft warning.
*Root cause:* the S4/S5 deploy-OFF→soak→enable ramp was designed but never
completed; OP-1 shipped the allocation UI on top of the still-OFF flags.
*Smallest fix:* flip both flags ON in dev+staging now; run the existing
ENFORCEMENT_ROLLOUT_RUNBOOK to production. Keep the flags as emergency-off levers.
No code change — this is the one flip that closes Q1/Q2/Q3/Q4 at the
`complete_worker_task` chokepoint.

**C-2 — Choice-value membership is never validated (`_parse_lines`).**
worker_report_views.py:56-61 `int()`s `color_id`/`size_id` but never checks the
value is in the stage schema's options or the worker's allocation. Flag-OFF this
let unallocated OW-C forge a completed (Red,S1) contribution. Flag-ON masks it for
pool-stage allocated dims (bound refuses allocated=0), but the parse layer itself
still trusts any real PK — defense-in-depth is absent and the shipped default is
flag-OFF. *Root cause:* view parse trusts client-supplied PKs.
*Smallest fix:* in `_parse_lines`, reject a choice `raw` not present in that
field's `options` (schema-driven, view-level, no service change). Independent of
the flag; also gives correct dims on NONE/legacy stages.

### 🟠 HIGH

**H-1 — Verification quantity is unbounded and bypasses the flag entirely.**
`set_verified_quantity` (worker_task_service.py:337-413) has the settled-line
guard but **no ceiling** vs allocation / pool / snapshot / good. Proven: manager
set OW-A verified = **100** on a 20-allocation / 25-report; settlement pays
verified-else-good = 100×₹5 = **₹500**. `ENFORCE_ALLOCATION_BOUND` runs only at
report-complete, so verification is a post-complete money path that the flag never
touches. *Smallest fix:* bound verified ≤ Σ active allocated for the dim (or ≤
good, WARN above) in `set_verified_quantity`, at the same chokepoint.

**H-2 — Voiding an allocation after the worker reported strands reported>allocated;
nothing re-checks, and the worker still gets paid.**
`void_allocation` (pool_service.py:342-364) checks only mgmt + idempotency; no
comparison to already-reported quantities. Proven: voided OW-B's 25-allocation →
OW-B now shows Allocated **0**, report **55** intact, board Expected **₹275**,
settles ₹275. The only reported-vs-allocated check (`check_allocation_bound`) runs
at complete and never re-runs on void. *Smallest fix:* `void_allocation` refuses
(or hard-warns) when the worker has completed contributions on the stage whose
reported qty exceeds the remaining allocation for those dims.

### 🟡 MEDIUM

**M-1 — Manager board "Expected ₹" ignores the verified override → understates the
real payout.** The Output board reads the frozen `expected_earning` (good×rate),
not `settlement_quantity`. Proven: OW-A board shows **₹125** while settlement will
pay **₹500** (verified 100). A manager reviewing the board cannot see what a
verify-correction actually pays. *Smallest fix:* board Expected column =
settlement_quantity × rate (verified-else-good), matching the settlement funnel.

**M-2 — `save_draft` writes unbounded rows and is not serialized by the task lock.**
Two effects: (a) a *refused* submit still commits the draft — proven: the refused
8+2+1=11 attempt left WSC good 8/alter 2/missing 1 (expected None) in the DB, so
the "refused" message is cosmetic for the row (money-safe only because complete
didn't freeze it); (b) census B2: because the view runs `save_draft` then
`complete` as two txns with `save_draft` trusting stale in-memory task status
(no row lock/refresh, worker_report_views.py:141-144), a double-submit can delete
a concurrently-frozen task's contributions and leave a COMPLETED task with NULL
expected. *Smallest fix:* run the bound inside `save_draft` too, and/or wrap
`post()` in one atomic txn and `select_for_update` the task in `save_draft`.

### 🟢 LOW

**L-1 — No upper sanity ceiling on rate/qty corrections.** `rerate_stage_role`
and `set_verified_quantity` accept any value ≥ 0 (census A4/A1). Admin-only +
audited, so low risk; a typo (e.g. rate 500 not 5) has no guardrail.

**L-2 — Machine linkage is derivable-only.** No machine stamp on
`WorkerStageContribution`; tracing which physical machine produced a piece relies
on matching `MachineAssignment` windows to `WSC.created_at`. Traceability gap, no
money impact.

## Proven SAFE (no action)

- **Allocation ceiling (Q4/Q5):** Σ non-voided allocations ≤ cutting snapshot,
  always-on, advisory-locked — flag-independent. (55>50 refused; cumulative
  "only 5"; concurrent 15+15 → one refused, Σ=45≤50.)
- **Reopen guard (Q6):** downstream-consumer guard refused reopening cutting
  while Overlock holds live allocations + completed production, with an actionable
  "reverse-first" message; cutting `completed_at` unchanged.
- **Concurrency (Q7):** pool lock `pg_advisory_xact_lock(5375,objid)` and
  settlement lock `5374` are disjoint (different arity + namespace); allocate race
  proven safe; finalize/verify/reopen serialize on the WSC/SR row locks (census B4/B5).
- **Single calc path (Q8):** cutting APSCPB → pool_service → report_contributions
  → complete freeze (good×rate) → verify → cost freeze → settlement funnel
  (settlement_quantity×rate) → ledger → payroll. Only extra writers = the
  documented rerate mirror and read-only previews; no template money math.
- **Visibility (Part 2):** worker mgmt URLs (costing/payroll/settlements/machines/
  review-reports) all **403**; worker report blind (own allocated dims only, no
  quantities, no other workers); dashboard leaks no cutting quantities; live
  revocation of the skill flipped report access **200→403** immediately (one
  predicate, fail-closed).
- **Mobile (Part 5):** worker report + manager panel/board no horizontal overflow
  @390; board tables use data-label card strategy.

## Recommended fix order (on approval)
1. **C-1** flip both flags ON (dev→staging→prod via runbook) — closes Q1–Q4 at the
   chokepoint. 2. **H-1** bound verified. 3. **C-2** membership validation. 4. **H-2**
   void-vs-reported guard. 5. **M-1** board Expected uses settlement qty. 6. **M-2**
   atomic report post + bounded draft. L-1/L-2 optional.

## Evidence artifacts (scratchpad)
`audit_q1_flagon_refused.png` · `audit_q3_manager_board.png` ·
`audit_q5_worker_report_390.png` · `audit_q5_mgr_panel_390.png`. Full census
transcripts in the task outputs (Q8 calc-path; Q6/Q7 correction+race).

## Dev-state left on 3-PATTI-013 (for owner teardown batch)
Overlock: OW-A alloc 20 / report 25 / **verified 100** (H-1 evidence — will pay
₹500 if settled) · OW-B alloc **VOIDED** / report 55 (H-2 evidence) · OW-C alloc
15 / report 5 · OW-D alloc 10 / report good8+alter1+missing1 (boundary pass, ₹40)
· OW-D worker created this session; skill revoked+restored (net unchanged).
`ENFORCE_ALLOCATION_BOUND=True` currently set on the 8003 process only (dev env
var; base.py default still False).

**STATUS: audit complete, awaiting owner approval. No fixes applied.**

---

# 🔁 RE-AUDIT 2026-07-06 — "impossible to misuse" pass (owner-ordered)

**Owner frame:** think like a factory owner preventing production fraud, mistakes,
and confusing worker UX — not a developer adding features. Fresh browser proof on
a CLEAN fixture, BOTH flag states. Audit-only, no code changed.

**Clean fixture built:** Adda `3-PATTI-014`, cutting complete, multi-dim snapshot
**Red·S1=50 · Red·S2=30 · Blue·S1=40** (total 120). Cast: dev.ow.a/b/c/d
(overlock), dev.sw.a/b (sleeve), dev.piece (overlock, piece-rate), dev.monthly
(monthly), dev.mgr (manager). Server tested at `ENFORCE_ALLOCATION_BOUND=True`
(pid confirmed) then restarted at the **shipped default (flag OFF)**.

## Part 1 — allocation engine, re-verified on clean 014 (both flag states)

| # (owner) | Test | Flag ON (proven) | Flag OFF = shipped default (proven) |
|---|---|---|---|
| 1 report w/o allocation | OW-C 0-alloc report | **REFUSED** "only 0 allocated" | **ACCEPTED → task completed, good 10, pays ₹50** |
| 2 report > allocation | OW-A alloc 30 → 35 / OW-B alloc 20 → 52 | **REFUSED** (35>30) | **ACCEPTED** (52>20) + soft-warn |
| 3 report > snapshot | OW-B report 55 vs snapshot 50 | blocked earlier by alloc bound | **ACCEPTED** (55>50) |
| 4 combined > snapshot | Red·S1: OW-A 28 + OW-B 52 + OW-C 10 = **90** vs 50 | impossible (report≤alloc≤snapshot) | **ACCEPTED — Σ90 pays ₹450 vs ₹250 ceiling** |
| 5 good+alter+missing > allocation | OW-A 33+2+1=36 / boundary 28+1+1=30 | **REFUSED** (36>30); 30 passes | **ACCEPTED** (52+2+1=55>20) |
| 6 reopen breaks limits | reopen cutting w/ overlock allocations live | **REFUSED** — names Overlock, "reverse-first"; cutting untouched | same (guard flag-independent) |
| 7 verification breaks limits | set OW-A verified **99** on alloc 30 / good 28 | **ACCEPTED — pays ₹495**, board still shows ₹140 | same (verify has no flag, no ceiling) |
| 8 allocation > snapshot | allocate Red·S1: OW-A 30 ok, OW-B 25 **refused** "only 20", 20 ok | **REFUSED always** | **REFUSED always** (advisory-locked, flag-independent) |

**One-line verdict:** the allocation *ceiling* (Q8) and *reopen guard* (Q6) are
genuinely misuse-proof and flag-independent. Everything else in Part 1 (Q1-Q5) is
enforced **only when `ENFORCE_ALLOCATION_BOUND` is ON** — and it ships **OFF**.
Verification (Q7) breaks the limits **regardless of the flag**.

## Part 2 — worker access matrix (predicate = access ∩ assignment)

Proved all four quadrants on the Overlock report path + live revocation:

| Worker | Has stage access? | Assigned (rostered)? | Result | 
|---|---|---|---|
| OW-A / OW-D | ✅ overlock skill | ✅ | report **200**, dashboard card shown |
| dev.piece | ✅ overlock skill | ❌ not rostered | report **403**, POST blocked at GET (no form/CSRF), dashboard empty |
| OW-A / OW-D after skill revoked | ❌ (cleared live) | ✅ still rostered | report **200→403**, dashboard card **disappears** — same request |
| SW-A | ❌ (sleeve only) | ❌ | report **403** |

**Verdict:** the stage-visibility predicate is ONE live predicate (access ∩
assignment), fail-closed, updates instantly on revocation — **clean**. Management
URLs (costing/payroll/settlements/machines/review-reports) all **403** for workers.

**🟠 NEW FINDING (Part 2/3) — worker sidebar + non-stage pages are NOT gated.**
Logged in as an overlock worker, the sidebar shows 11 items and these all render
**HTTP 200**: `/production/` (Operations), `/production/addas/` (lists **all 6
Addas**), `/raw-materials/` , `/raw-materials/rolls/` ("Inventory of every cloth
roll"), `/raw-materials/cloth-colors/`, `/tracking/`. A floor worker can browse
factory raw-material inventory, the full Adda list, and tracking. This directly
violates the owner rule "worker sees only their assigned work — no management
information." (This is the still-open F-9 from the 2026-07-05 end-to-end audit; the
STAGE predicate is clean, but the *menu/route* gating for non-stage pages is not.)
*Root cause:* the `worker` role's `SidebarItemRule` / permission set grants read
access to raw-materials + production-list + tracking. *Smallest fix:* add Sidebar
Access rules restricting the worker role to My Dashboard + My Earnings (menu+URL
gated together by `SidebarAccessMiddleware`, CLAUDE.md rule 6) — config, not code.

## Part 3 — mobile worker UX (@390)

The report screen itself is good: no horizontal overflow, blind (own allocated
dims only, no quantities, no other workers), clear GOOD/ALTER/MISSING inputs, good
empty-state ("Nothing assigned to you yet — ask your manager").

Against the owner's "answer ONE question — what work do I finish right now?":

| Owner's question | Answered on worker screen? |
|---|---|
| Which Adda? | ✅ "ADDA · 3-PATTI-014" |
| Which operation? | ✅ "Overlock" |
| Which machine? | ❌ **not shown to the worker** (machine appears only on the manager panel) |
| Which colour / size? | ✅ chips (own allocation) |
| What to report? | ✅ Good / Alter / Missing |
| Nothing else? | ❌ full raw-materials/tracking/operations sidebar; "NEW ADDAS STARTED" broadcast lists Addas the worker has no work on |

**🟡 UX findings (improvement proposals, architecture-preserving):**
- **U-1** Trim the worker sidebar to their world (My Dashboard, My Earnings) — same
  Sidebar Access fix as the Part-2 finding. HIGH-value, config-only.
- **U-2** Show the worker their **machine** on the report screen (owner wants it).
  Data exists (`MachineAssignment` open window for the Adda+type). Display-only,
  read through the existing service — no new model. MEDIUM.
- **U-3** The dashboard "NEW ADDAS STARTED" broadcast shows every new Adda to every
  worker (D6 by design, code+name only). Consider scoping it to Addas the worker is
  rostered on, to honour "only my work." LOW.

## Part 4 — traceability (cutting → last operation)

Per finished piece/dimension, what an admin can reconstruct today:

| Attribute | Captured? | Where |
|---|---|---|
| Colour / Size | ✅ | `WorkerStageContribution.color/size` |
| Operation / stage | ✅ | WSC → task → stage_record → workflow_stage → stage |
| Worker | ✅ | `WorkerStageTask.worker` |
| Good / Alter / Missing | ✅ | WSC fields (append-only, immutable — nothing lost) |
| Who verified + when | ⚠️ derivable | NOT on the WSC (no `verified_by`/`verified_at`); captured in the `AddaHistory` activity log (`VERIFIED_QTY_CORRECTED`, actor + old/new + contribution id) — proven live |
| Manufacturing cost | ✅ (stage-level) | `AddaStageRecord.processing_cost` |
| Settlement | ✅ | `WSC.settlement_line` → `StageWorkAssignment` → `WorkerLedgerEntry` |
| **Which machine produced it** | ❌ **NOT CAPTURED** | no machine ref on WSC or WorkerStageTask; only `MachineAssignment` open windows (machines app) matched to `WSC.created_at` heuristically — imprecise when >1 machine/operator open |

**🟡 FINDING (Part 4) — machine linkage is the one broken traceability leg.** The
owner's "which machine made this piece?" is **not reliably answerable**: production
records carry no machine stamp; the only link is a time-window guess against
`MachineAssignment`. *Smallest fix (on approval):* stamp the operating
`MachineAssignment` (or machine id) onto `WorkerStageContribution` at report time
through the existing single-writer (`report_contributions`) — one nullable FK, no
new money path, no new source of truth. History preservation itself is sound
(WSC rows immutable + append-only; reopen never deletes them).

## Consolidated findings (re-audit) — grouped

**🔴 CRITICAL**
- **C-1** Integrity flags ship OFF (`ENFORCE_ALLOCATION_BOUND`,
  `ENFORCE_SETTLEMENT_RECONCILIATION` both default False) → in the shipped config
  Q1-Q5 are all bypassable and settlement pays it with only a soft warning.
  Re-proven on clean 014: Red·S1 cut 50 → Σ reports 90 → pays ₹450. *Fix:* flip
  both ON (dev→staging→prod via existing runbook); no code.
- **C-2** `_parse_lines` never validates choice-value membership → unallocated /
  forged report writes a completed, payable contribution (flag-OFF; re-proven OW-C
  → ₹50). *Fix:* schema-membership check at parse.

**🟠 HIGH**
- **H-1** `set_verified_quantity` unbounded + flag-independent → verified 99 on a
  30-allocation pays ₹495 (re-proven). *Fix:* bound verified ≤ Σ allocated at the
  chokepoint.
- **H-2** `void_allocation` after a report strands reported>allocated, still pays
  (proven 2026-07-05: OW-B voided→0 alloc, pays ₹275). *Fix:* void refuses/warns
  when completed contributions exceed remaining allocation.
- **H-3 (NEW)** Worker sidebar + non-stage pages ungated → floor worker sees cloth
  rolls, all Addas, tracking, operations (all HTTP 200). *Fix:* Sidebar Access
  rules for the worker role (config).

**🟡 MEDIUM**
- **M-1** Manager board "Expected ₹" ignores the verified override (shows ₹140,
  pays ₹495). *Fix:* board Expected = settlement_quantity × rate.
- **M-2** `save_draft` writes unbounded rows + not serialized by the task lock
  (refused submit leaves an over-limit draft; double-submit clobber). *Fix:* bound
  in save_draft and/or atomic post + lock.
- **M-3 (NEW)** Machine linkage not captured on the production record → "which
  machine?" unanswerable. *Fix:* nullable machine FK stamped at report.
- **M-4 (NEW, UX)** Worker report screen doesn't show the machine (owner wants it).

**🟢 LOW**
- **L-1** No rate/qty sanity ceiling on corrections (admin-only, audited).
- **L-2** Verifier identity lives in the activity log, not on the piece/board.
- **L-3 (UX)** Worker "NEW ADDAS STARTED" broadcast shows unrelated Addas.

## Proven misuse-PROOF (no action)
Allocation ceiling (Q8, always-on, race-tested) · reopen downstream guard (Q6) ·
concurrency (pool lock 5375 ⟂ settlement 5374) · single calculation path (Q8
census) · stage-visibility predicate access ∩ assignment (all 4 quadrants + live
revocation) · management URLs 403 for workers · production history append-only /
immutable (nothing lost).

## Recommended fix order (unchanged core + new)
1. **C-1** flip both flags (closes Q1-Q5 at the chokepoint). 2. **H-1** bound
verified. 3. **C-2** membership validation. 4. **H-2** void guard. 5. **H-3 + U-1**
worker sidebar lockdown (one config change). 6. **M-1** board expected. 7. **M-3 +
U-2** machine stamp + show on report. 8. **M-2** atomic draft. L-1..L-3 optional.

## Dev-state (for owner teardown)
`3-PATTI-014` = re-audit evidence: OW-A verified 99 (H-1), OW-B report 55 (Q2/3),
OW-C forged 10 (Q1 flag-OFF), OW-D Blue·S1 12/2/1 (clean line). `3-PATTI-013` =
prior-audit evidence. Server currently running at the **shipped default
(ENFORCE_ALLOCATION_BOUND OFF)**. Cast users all `Dev@12345`.

**STATUS: re-audit complete. No code changed. Awaiting owner approval on the fix
list + order.**

---

# OWNER DECISIONS 2026-07-06 (post re-audit)

- **Flags stay OFF** during remaining operation development — rollout policy, by
  design. Enable permanently in the production-hardening phase AFTER all
  operations (Overlock → Sleeve → …) are built. C-1 = policy, not a bug fix now.
- **4 fixes APPROVED (architecture correctness), implementation DEFERRED until
  after the business-journey audit:**
  1. C-2 membership validation (never submit a colour/size not allocated to you)
  2. H-1 verified ≤ allocated (verification reduces/confirms, never creates)
  3. H-2 void-after-production requires explicit correction workflow
  4. H-3/U-1 worker visibility lockdown (only access∩assignment stages + own work;
     remove Operations/Tracking/Raw-Materials/All-Addas from worker experience)
- **NEXT: BUSINESS-JOURNEY AUDIT** (this session): simulate real factory — one
  Adda, cutting → 5 colours → 5 workers → verify → sleeve → settle; three lenses
  (worker/manager/owner) at every step; focus = natural/simple/scalable, not
  validation. Audit-first; no implementation until owner approves.

---

# 🏭 BUSINESS-JOURNEY AUDIT 2026-07-06 (owner-ordered, flags OFF, audit-only)

Simulated one real Adda end-to-end. **Fixture 3-PATTI-015**: cutting done, 5
colours × 50 (Red/Blue/Green/Yellow/Black = 250 pieces). Cast: 5 overlock workers
(one colour each), 2 sleeve workers (multi-colour), 1 manager, machine OL-001.
Flags left OFF per owner. Followed the full chain and looked through 3 lenses.

## The journey (proven, DB + browser)

| Step | What happened | Result |
|---|---|---|
| Cutting snapshot | Red/Blue/Green/Yellow/Black = 50 each | pool available correct |
| Manager allocates | A→Red B→Blue C→Green D→Yellow Piece→Black, 50 each | split table drained to 0; over-allocation refused |
| Machine | OL-001 → OW-A on 015 | holder chip on manager panel |
| 5 workers report | independently, blind (own colour only) | G/A/M per worker; Σ good 239, Σ expected ₹1195 |
| Manager verifies | OW-C green 45 → **44** (1 defective) | audited (AddaHistory actor=mgr, 45→44) |
| Complete Overlock → advance | cost froze ₹1195 (good); sleeve pool materialized | **pool = 239 GOOD (Green 45), NOT verified 44** ⚠️ |
| Sleeve: 2 workers, multi-colour | SW-A Red+Blue+Green, SW-B Yellow+Black | reported; Σ expected ₹708 |
| Complete Sleeve | adda status = completed; sleeve cost ₹708 | last operation done |
| Settlement ADST-0003 | finalized | expected_total **₹1898**; Green overlock line = 44 ✓ (verified applied) |
| Money flow | SWA ₹1898 = ledger credit ₹1898 | per worker: A240 B250 **C220** D235 Piece245 SW-A423 SW-B285 |
| My Earnings (OW-C) | ₹220 pending/earned | verified reduction reached pay (44×5, not 45) |
| Costing (owner) | **Std ₹1903 · Settled ₹1898 · Variance ₹5** | variance = exactly the 1 verified piece × ₹5 |
| A360 (owner hub) | cost duality + workers + timeline | coherent, "never added (ADR-0009)" |

**Headline: every number flows and every money surface agrees.** Cutting → report
→ verify → settlement ₹1898 → ledger ₹1898 → My Earnings → costing/A360. The
standard-vs-actual duality is visible and self-explaining (variance ₹5 = the
verification). The workflow feels natural and is internally consistent.

## Three lenses × owner's questions

- **Worker sees:** own Adda, own operation, own colour/size, own numbers, empty-
  state when nothing assigned. **Does NOT see** the cut total (250), other colours,
  other workers, or an allocation ceiling. Blind rule holds through the whole
  journey. ✅ (caveat J-4 sidebar).
- **Manager sees:** split table (available per dim), allocation chips + void, board
  (Allocated/Good/Alter/Missing/Verified/Expected ₹), machine holder, roster,
  Report Review. Everything needed to run the floor. ✅
- **Owner sees:** costing duality + variance, A360 hub, settlement lines (verified
  marked ✓), payroll/ledger, all agreeing. ✅
- **Only what they should?** Workers: yes for stages; **no** for the global sidebar
  (J-4 / re-audit H-3). Manager/owner: yes.
- **Numbers flow to next operation?** Money: yes. Production capacity: **good flows,
  verified does not** (J-1).
- **Confusing on mobile?** No overflow anywhere @390. Multi-colour report has
  friction (J-2).
- **Can UI be simpler?** Yes — J-1/J-2/J-3/J-4 below.

## Journey findings

**🟡 J-1 (MEDIUM — business decision, not clearly a bug) — verification corrects PAY
but does NOT flow to the next operation.** Manager verified OW-C green 45→44; the
sleeve pool still received **45**. Settlement paid 44 (correct); the downstream
operation can work 45 (the 1 caught piece still counts as capacity). Owner rule
was "next operation receives only completed quantities." *Root cause:*
`pool_service` materializes/reads `good_quantity`, never verified-else-good.
*Decision needed:* should a manager's verified reduction shrink the downstream
pool? (For alter/missing, good-only flow is right — they aren't finished pieces.
The open question is specifically the verified correction.) *Smallest fix if yes:*
materialize `verified-else-good` in `pool_service` — one read change, no new model,
no money path (money already uses verified).

**🟡 J-2 (MEDIUM — worker UX, owner-invited improvement) — multi-colour reporting is
harder than single-colour.** A worker with 3 allocated colours (SW-A) sees ONE
blank line + a colour dropdown and must click "Add another work line" per colour;
a single-colour worker (OW-A) got a ready-filled line. Low-literacy workers may
skip a colour. *Fix:* pre-render one ready-filled line per active allocated
dimension (allocations already known); worker only types quantities. Display-only,
architecture-preserving.

**🟢 J-3 (LOW — polish) — stage shows the raw identifier "Sleeve_join"** (underscore,
lowercase) as the panel title/heading, while the button correctly says "Start
Sleeve Join". The human display name isn't used in every place. Cosmetic.

**🟢 J-4 (LOW — already logged) — worker global sidebar clutter** (Operations,
Addas, Raw Materials, Tracking) still present on worker pages incl. My Earnings.
Same item as re-audit **H-3 / U-1** (Sidebar Access config).

## Verdict
The production workflow is **natural, internally consistent, and money-correct
end-to-end**. It is **not yet "impossible to misuse"** only because the four
approved-deferred guards (C-2/H-1/H-2/H-3) are intentionally off during rollout.
The journey surfaced one genuine business question (**J-1 verified→pool**) and
three UX simplifications (**J-2/J-3/J-4**). None require redesigning accepted
architecture. **Audit-only — no code changed. Awaiting owner decision on J-1 and
approval to implement the deferred fixes + J-2/J-3/J-4.**

## Dev-state
3-PATTI-015 = full clean journey (settled ADST-0003 ₹1898). 013/014 = prior audit
evidence. Server at shipped default (flags OFF). Cast all `Dev@12345`.

---

# IMPLEMENTED 2026-07-06 — 8 owner-approved fixes + Operation Independence Audit

**Gate PASS 875** (864→875, +11 `test_op1_hardening`), golden ₹225 byte-identical,
single-writer gates 4/4b/4c green, coverage 78%. Flags stay OFF (owner rollout
policy). Browser-verified on 3-PATTI-014/015.

## Fixes shipped (all in shared/base code — future operations inherit them)

| # | Fix | Where | Proof |
|---|-----|-------|-------|
| J-1 | Downstream pool consumes **verified-else-good** (verification = final truth) | `stages/base/handler.materialize_pool` (`Coalesce(verified,good)`) | unit (pool red 46) + live 014 (Blue pool **16** = OW-D 12 good + dev.piece **4 verified**, not 17) |
| C-2 | Report choice value must be a member of the worker's schema options | `worker_report_views._parse_lines` | unit + live (forged Green → "not in your assigned work", 0 written) |
| H-1 | Verified ≤ good (never create) AND ≤ allocation where one exists | `worker_task_service.set_verified_quantity` | unit (31>30 refused; 22>20-alloc refused; unsplit still usable) |
| H-2 | Void refused once submitted production no longer fits post-void allocation | `pool_service.void_allocation` | unit (void after 18 produced refused; partial void OK; pre-report void free) |
| H-3/J-4 | Worker sidebar+URL locked to their own world | migration `accounts/0018` | unit + live (worker sidebar = "My Dashboard · My Earnings" only; cloth-rolls/all-addas/tracking gone) |
| J-2 | Prefill one report row per allocated colour+size pair | `generic_stage.contribution_schema` `initial_lines` + view | unit + live (dev.piece 2 rows: Blue·S1, Red·S2, chips pre-selected) |
| J-3 | Panel titles use `Stage.name`, never the url slug | `stage_views.StagePanelView` + templates | live ("3-PATTI-015 — Overlock", not "overlock") |

3 legacy pins re-pinned to the lockdown truth (sidebar order = Main only; roll-list
filter pins run as admin). No new money path; verified-else-good reuses the settlement
resolver rule independently in the pool (capacity) — one truth, two concerns.

## Operation Independence Audit — VERDICT: PASS (1 known deferred gap)

| Check | Result | Evidence |
|-------|--------|----------|
| Stages renamed safely | ✅ | `Stage.code` disabled on edit (`access_views.py:144`); `name` free; everything FKs to Stage — rename propagates as a live label |
| Categories renamed safely | ✅ | `StageCategory` is pure data; **zero** literal `category__code`/code reads in engine/money/access (R10-A fence); rename = display only |
| Machine types reused safely | ✅ | `MachineType` is metadata, FK by pk, machine never earns; sleeve_join reused "Overlock Machine" live |
| Order changes don't corrupt history | ✅ | `move_stage_in_product_flow` REFUSES while any Adda is in-flight (F3 fix) → active pool source stays stable; `remove` refuses if any AddaStageRecord references it; money frozen on WSC/SWA regardless of order |
| Rates never change historical settlements | ✅ | `expected_rate` frozen at complete; SWA `earning_amount_snapshot` frozen at finalize; `rerate` refuses settled lines; `cost_rate` edits affect only future freezes |
| Activate/deactivate safely | ✅ | `Stage.is_active` (ActiveManager) hides from pickers only; PROTECT FK keeps history label; `remove` guarded |
| Historical reports immutable | ✅ | `good/alter/missing` are write-only-at-create (`worker_task_service.py:206-208`); NO update path anywhere; only `verified_quantity` is a separate management field |
| Traceability complete | ⚠️ | colour/size/operation/worker/G-A-M/verifier(AddaHistory log)/cost/settlement all traceable — **EXCEPT machine linkage — M-3 CLOSED 2026-07-06 by pre-Phase-3 B: `WSC.machine_code` stamp, migration prod 0048** |
| Every future operation config-only | ✅ | new stage = Stage row + WorkflowStage config + rate, no code (Overlock/Sleeve proven); all 8 fixes live in base/generic/shared code, so future stages inherit them automatically |

**No new corruption vector introduced by the 8 fixes.** The one open item is the
pre-existing **M-3 machine linkage** — since CLOSED 2026-07-06 (pre-Phase-3 B: `WSC.machine_code` stamped at report time, migration prod 0048).

**Minor observation (not a blocker):** `StageCategory`/`MachineType` `code` is editable on
edit while `Stage.code` is locked. Harmless today (nothing reads those codes as literals),
but locking them for symmetry would make the masters uniformly rename-safe.

**STATUS: implemented + gated + audited. Production engine = allocation-hardened,
verified-as-truth, worker-scoped, config-only. Ready to configure remaining operations
(no more infrastructure) once owner accepts.**
