---
id: docs-campaign-contracts-phase-04-confirmed-findings
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 4 Execution Contract — Confirmed Findings Implementation

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) — this contract only adds phase specifics and tightenings.
> **This phase discovers NOTHING.** It is the campaign's implementation protocol: it executes
> ONLY findings already CONFIRMED with evidence by the certification phases (1–3), plus backlog
> rows the owner explicitly selects. Every rule below is derived from the campaign's own
> operating record — the U-invariants, the Phase-1 fix precedents (MGT-B-1 · backlog #5 ·
> MGT-F-1), the worker-cert fix precedents (BUG-1/2/3 · BUG-E1 · S2 · S3), and the
> [DEPLOYMENT_BACKLOG.md](../DEPLOYMENT_BACKLOG.md) taxonomy — with citations. Where the record
> does not decide something, it is a Design Record item (Appendix A), never an invention.
> **Owner designation (2026-07-12): this contract is the campaign's PERMANENT implementation
> protocol** — later phases (and, adapted per §6.6, post-campaign fix work) implement confirmed
> findings under these rules; their contracts state only deltas.

## 1. Phase objective

Implement, pin, battery-verify, document, and close every finding that phases 1–3 confirmed
but did not (or could not) fix inside its certification mandate — and ONLY those. Deliver a
reconciliation in which every finding ever raised by the certification campaign is accounted
for in exactly one terminal state: FIXED+PINNED+CLOSED · INFO-deferred (backlog row with
fix-when-touched spec) · design-ambiguity (Design Record, owner-answered) · doc-drift (routed
to KOS phases 6–7) · infrastructure (backlog, venue named) · owner-declined (recorded). After
this phase, the campaign carries zero unaccounted findings into the documentation and
deployment phases.

## 2. Scope

### 2.1 The finding classification (normative taxonomy)

Derived from the campaign's practiced vocabulary; every intake item gets exactly ONE class:

| Class | Definition (with campaign precedent) | Route |
|---|---|---|
| **Confirmed bug** | Defect reproduced with probe artifacts + root-caused, inside a certification mandate (MGT-B-1: NameError 500 on lane refusals; #5: NoReverseMatch 500; MGT-F-1: guard compared mutated instance) | **Phase-4 eligible** (unless already fixed in-certification — then recorded pre-closed) |
| **Candidate observation** | Noted during authoring/probing, NOT yet judged (PHASE_03 §2.2 pre-registered observations; MGT-A "edit buttons render for manager" pre-judgment) | Judged inside its NAMED certification sub-phase; never fixed from candidate state |
| **Backlog INFO** | Judged non-blocking, fails closed, out-of-mandate — recorded with where-found · what · why-deferred · fix-when-touched spec (#7, #8, #9) | DEPLOYMENT_BACKLOG row; enters Phase 4 ONLY via owner selection (F-D1) |
| **Design ambiguity** | Intent not decidable from the repository (PHASE_03 D1 accountant deployment model; PHASE_00 D1–D5) | Design Record item in the owning contract; the owner's answer may reclassify it |
| **Owner decision** | A recorded ruling that authorizes or declines work (U14 migration approvals; enforcement-flags-stay-OFF; C-4 owner-gated) | Recorded verbatim in the owning Design Record; an authorization converts the item into a Phase-4 work item with an approval reference |
| **Documentation drift** | Docs wrong, code certified correct (#6 RBAC.md role table; PHASE_05 Appendix B.3 register) | KOS phases 6–7 — **never Phase 4** (backlog #6 precedent) |
| **Infrastructure issue** | Test-infra / tooling / scale trade-off, zero product-code defect (#1 export sequencer contention; #4 patterns_ai parallel/keepdb flakiness) | Backlog row with venue note; Phase 4 only via owner selection |

Only the first class is implementable here. A dispute about an item's class = stop condition
§16.3 (owner arbitrates), never a silent upgrade.

### 2.2 Intake sources (FIX-0 reads these; nothing else)

1. **Phase 1 record** — [MANAGEMENT_ROLE_CERTIFICATION.md](../MANAGEMENT_ROLE_CERTIFICATION.md):
   all 3 confirmed bugs already fixed+pinned in-phase (battery 1519→1526) → enter the ledger
   PRE-CLOSED (reconciliation completeness, no work).
2. **Worker-cert record** — [WORKER_ROLE_CERTIFICATION.md](../WORKER_ROLE_CERTIFICATION.md):
   BUG-1/2/3, BUG-E1, S2, S3 fixed in-phase → PRE-CLOSED rows.
3. **Phase 2 execution residue** — OWNER_VISIBILITY_CERTIFICATION.md evidence sections + its
   carry-in verdict (RoleForm.permissions, judged OWN-D): any finding confirmed but deferred
   under a Phase-2 stop condition (migration-class, settings-class, frozen-module-class).
4. **Phase 3 execution residue** — OFFICE_SUPPORT_ROLE_CERTIFICATION.md evidence + Design
   Record D1–D4 outcomes: notably, if D1 rules the accountant reachability contradiction a
   confirmed design gap AND the owner names Phase 4 as the venue, it arrives here WITH that
   ruling attached (PHASE_03 D1 explicitly does not authorize new page gates without it).
5. **Certification stop-condition deferrals** — any fix a phase refused because it required a
   migration (U14), a settings change, a `permission_service` role-set change, or a
   frozen-module/single-writer edit (PHASE_02 §16.3-4, PHASE_03 §16.4): each arrives
   "confirmed + deferred pending owner decision" and is workable ONLY with the owner's
   recorded per-item approval (F-D2).
6. **Owner-selected backlog rows** — from [DEPLOYMENT_BACKLOG.md](../DEPLOYMENT_BACKLOG.md)
   (open at authoring: #1 infra · #3 polish · #4 infra · #6 doc-drift[→phase 7] · #7 · #8 · #9
   INFO) and, if the owner reaches for it, PENDING_BACKLOG.md — selection is F-D1; nothing
   auto-promotes.

**Ordering precondition:** FIX-0 runs only after Phase 2 AND Phase 3 deliver final verdicts
(their residue IS the input). The owner may order a reduced-scope early run (backlog-only);
that order is recorded in the Design Record and the ledger marks the intake PARTIAL.

### 2.3 In / out

**In:** intake + classification ledger; implementing confirmed bugs (categories §7); pins;
battery; docs-sync; reconciliation. **Out:** ANY new probing/discovery (a new defect noticed
mid-fix is a finding for the backlog or a certification phase — not this phase's work);
doc-drift repair (phase 7); KOS work; enforcement-flag changes (U10); performance/refactor work
(U1); anything the ledger does not carry as an approved work item.

## 3. Success criteria

Phase 4 is DONE when ALL hold:
1. `docs/CONFIRMED_FINDINGS_LEDGER.md` exists (FIX-0), append-only, one row per finding from
   every §2.2 source, each carrying exactly one §2.1 class and a lifecycle state.
2. Every ledger work item reached a terminal state via the §6.1 lifecycle
   (Confirmed → Fixed → Pinned → Battery → Docs → Closed), with per-transition evidence.
3. Every non-work-item row carries its route: PRE-CLOSED / INFO+backlog-row / Design-Record ref
   / phase-7 route / owner-declined (verbatim).
4. Zero scope creep: the diff of this phase = exactly the owning files of closed work items +
   their pins + their docs (§9); nothing else changed.
5. Battery green at final state with reconciled arithmetic: final count = FIX-0 entry baseline
   + Σ pins added this phase (per-fix arithmetic recorded; entry baseline read from the status
   dashboard at FIX-0 — 1526/1526 at authoring, NOT assumed then).
6. FIX-G reconciliation statement written: every phase-1–3 finding accounted, backlog reviewed
   line-by-line (MGT-H precedent), a carry-forward list for phases 5–22, and the input
   statement the Phase-21 readiness certificate will cite.
7. Status file + backlog + memory synced at every sub-phase close.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Single-fix-at-a-time.** Within a sub-phase, work items execute strictly serially: item N is
  Fixed → Pinned → (targeted verification, §6.4) → evidence written BEFORE item N+1 starts.
  No interleaved diffs; each fix is independently attributable and revertable.
- **Smallest-change philosophy** (Phase-1 practice, now normative): the fix is the smallest
  change inside the single owning file(s) that removes the confirmed defect — precedents:
  MGT-B-1 = one import line; #5 = one `get_context_data` mirroring siblings; MGT-F-1 = one
  guard reads the DB row. A fix wanting to touch a second concern, refactor, or "improve
  nearby code" has left its mandate (stop condition §16.5). New files only when no owning file
  exists (test-module sibling rule, §6.3).
- **No new probing.** Reproduction uses the EXACT probe recorded in the source evidence
  (re-run pre-fix to prove the defect still exists, re-run post-fix to prove it is gone) —
  hostile exploration belongs to certification phases.
- **Approval-gated classes.** U14-migration items, settings items, role-set items,
  frozen-module/single-writer items: work starts only with the per-item owner approval
  reference in the ledger row (F-D2). Absent reference = untouchable.
- Money-adjacent fixes (anything within U8's single-writer list, even approved): golden
  invariants re-proven around the fix — ledger row-count/Σ re-baselined same session (MGT-C
  precedent: point-in-time values, never eternal constants) and golden ₹225 byte-identical
  where the settlement path is touched (S-series precedent).
- DEV-data rules, identity rules, rate-limit caution: as PHASE_03 §4 (unchanged).

## 5. Evidence standard

Per WORK ITEM (the MGT-E/F fix-evidence pattern, normative):
1. **Pre-fix reproduction** — the source probe re-run, exact error/flash/status quoted
   (MGT-E precedent: "re-reproduced pre-fix as manager AND super-admin ×6, exact
   'NoReverseMatch: Reverse for '' not found'").
2. **Root cause** — one paragraph naming the defective mechanism (not the symptom).
3. **The diff** — files + a summary of the smallest change; owning-file justification.
4. **Post-fix proof** — same probe passes; for permission fixes, the multi-identity lattice on
   the changed surface (§7 FIX-A).
5. **Negative control** — whoever must STILL be blocked/refused on that surface, re-proven.
6. **Pins** — list of added tests, module, and what each pins.
7. **Battery arithmetic** — expected = prior + new pins; actual; both quoted.
8. **Docs** — U6 lookup results (GUIDE/README/CHANGE_IMPACT_MATRIX rows updated or N/A-stated).
Sub-agent findings supplemental (U7); reproduction, fixes, money proofs, and verdicts =
main-thread. "Looks fixed in code" is never a closure (U11).

## 6. Methodology

### 6.1 Bug lifecycle (normative)

`Confirmed → Fixed → Pinned → Battery → Docs → Closed`
- **Confirmed**: ledger row exists with source-evidence link + class=confirmed-bug + (if
  approval-gated) the owner approval reference. Entry gate to any code edit.
- **Fixed**: smallest change landed in owning file(s); pre/post reproduction evidence written.
- **Pinned**: regression pins authored in the owning app's existing certification module
  (U4 — pins only for fixes, authored AT fix time; FIX-D audits, §7).
- **Battery**: the run whose arithmetic covers this fix's pins is green (§6.4 timing).
- **Docs**: U6 same-session sync done (app GUIDE/README + CHANGE_IMPACT_MATRIX-mapped docs).
- **Closed**: ledger row terminal; status file + memory updated.
A failed transition rolls the item back one state with the failure recorded — never deleted.

### 6.2 Backlog lifecycle (normative)

`Observation → INFO → Deferred` — an observation is judged inside a NAMED certification
sub-phase (never in Phase 4); judged non-blocking ⇒ INFO row in DEPLOYMENT_BACKLOG with the
four-part format (where found · what · why deferred · fix-when-touched spec — #7/#8/#9 are the
template); it stays Deferred until a later phase with a named mandate (or owner F-D1 selection)
picks it up; resolution strikes through but RETAINS the row for history (#2/#5 precedent).

### 6.3 Ownership rules (where a fix and its pins may land)

- Fix: the single smallest app file(s) owning the defect — views/services/forms/templates of
  the app under work (PHASE_02 §9 wording, normative here).
- Pins: the app's existing certification/regression module — precedents:
  `config/production/tests/test_management_role_certification.py`,
  `config/raw_materials/.../test_master_gates.py`, machines `test_r10a`. Create a sibling
  (`test_confirmed_findings.py` naming pattern) ONLY if no suitable module exists.
- Untouchable regardless of approval state: `permission_service` role-set constants (PHASE_03
  §10 rule — RBAC architecture, owner decision, never a "fix"), enforcement flags (U10),
  `.git` (U2). Migrations/settings/single-writers/frozen modules: only WITH the F-D2 per-item
  approval reference.

### 6.4 Battery timing (U5-derived; contracts may only tighten)

- Targeted verification per fix: the owning app's cert/test module runs immediately after
  pinning (cheap serial check between items).
- **Full sequential fresh-DB battery at every sub-phase close where code changed** (U5
  canonical — Phase-1 precedent ran the full battery in the same sub-phase as each fix; this
  contract keeps that and FIX-E is IN ADDITION, not instead).
- Immediate full battery (not deferred to sub-phase close) when a fix touched any U8
  single-writer or money path.
- FIX-E = the terminal certification run over the final aggregate state + arithmetic
  reconciliation of every run this phase.

### 6.5 The per-item execution loop (locked)

1. Read the ledger row + its source evidence section. 2. Verify preconditions (class, approval
ref if gated, owning file unchanged since confirmation — drift ⇒ §16.9). 3. Reproduce pre-fix
(§5.1). 4. Fix (smallest change). 5. Pin. 6. Targeted module run. 7. Evidence block appended to
the ledger. 8. Next item (or sub-phase close: full battery if code changed → docs-sync →
status/memory → STOP per U3).

### 6.6 Permanence clause (owner designation)

This protocol survives the campaign as the implementation protocol for confirmed-finding work:
phases 5–22 route any confirmed defect they surface through this lifecycle (their contracts
state deltas only). Post-phase-22 adaptation: U2's no-commit rule ends at the First Git
Checkpoint — thereafter "Closed" additionally requires the fix committed under normal git
discipline; every other rule stands unchanged. (Recorded as owner order 2026-07-12; scope
questions → F-D3.)

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); status lives in the status file + ledger.

| # | Scope · Inputs · Outputs · specifics |
|---|---|
| **FIX-0** — Campaign intake + confirmed-findings ledger | **Scope:** build `docs/CONFIRMED_FINDINGS_LEDGER.md`; NO code. **Inputs:** the six §2.2 sources, read completely; owner answers F-D1 (backlog selection) + F-D2 (approval-gated items) + F-D3 (permanence scope). **Outputs:** ledger (columns: id · source+evidence link · class · lifecycle state · owning app/file · approval ref · pins · battery delta · docs · closed date) with EVERY finding rowed, work-queue ordered by category; Design Record filled. **Evidence:** per-row source citation; intake-completeness census (each source doc's findings counted vs rows). **Rollback:** docs-only. **Regression:** none possible. **Battery:** never runs. **Stop:** owner absent for F-D1/2; upstream phase 2 or 3 not closed (unless recorded reduced-scope order); source docs internally inconsistent (conflict rule). |
| **FIX-A** — Permission / RBAC findings | **Scope:** confirmed bugs whose defect is a gate (mixin/middleware/service-gate/perm-seam). **Inputs:** ledger queue, class=confirmed-bug, category=permission. **Outputs:** fixes+pins+evidence per §6.5. **Evidence (tightened):** post-fix multi-identity lattice on the changed surface — SA + manager + worker (+ accountant/listing where the surface touches them) each re-proven allowed/blocked per the owning certification's expectation matrix; middleware AJAX fork re-checked where relevant. **Rollback:** shell probes transaction-wrapped; no durable Role/rule mutation (PHASE_03 §4). **Regression:** prior-fix guard list (§14) rows touching gates re-run. **Battery:** full at close if code changed (§6.4). **Stop:** fix wants a role-set/settings/migration change (§16.4); identity lockout. |
| **FIX-B** — Business-logic findings | **Scope:** confirmed bugs in service-layer behavior (money-adjacent likely). **Inputs:** ledger queue, category=business-logic; approval refs for any single-writer touch. **Outputs:** fixes+pins+evidence. **Evidence (tightened):** rollback-wrapped before/after DB proofs; ledger row-count/Σ re-baseline around every money-adjacent fix; golden ₹225 byte-identical if settlement path touched. **Rollback:** one atomic block per probe cluster, byte-identical recounts; append-only artifacts disclosed (U13). **Regression:** the owning flow's canonical lifecycle re-run (stage_earnings/fnf flow docs as the script). **Battery:** immediate full run after any single-writer fix (§6.4). **Stop:** U8 anomaly; approval ref missing; golden invariant drifts. |
| **FIX-C** — UI / template findings | **Scope:** confirmed bugs in templates/static UI behavior (500-on-render class like #5, leaks-by-render, broken affordances). **Inputs:** ledger queue, category=ui-template. **Outputs:** fixes+pins+evidence. **Evidence (tightened):** browser before/after on :8003 as the affected identity **after dev-server restart** (production-audit lesson: runserver caches templates); mobile responsive check where layout touched (owner rule 11); tokens-only + design-frozen rules bind (no new CSS outside the rules). **Rollback:** DEV-marked browser data round-tripped. **Regression:** the page's other identities still render/refuse correctly. **Battery:** full at close if code changed (template-only changes still count as code for U5 purposes — pins for render-crash fixes are Python tests per #5 precedent). **Stop:** fix grows into design-system change (frozen 2026-06-18 — owner decision). |
| **FIX-D** — Regression-pin audit | **Scope:** pin COVERAGE verification — pins are authored at fix time (§6.1); this sub-phase audits: every closed work item has pins that fail on revert (spot-verify by reading the pin against the defect, not by reverting); every prior-phase fix (§14 guard list) still has its pins present and green; gaps filled. **Inputs:** ledger + test modules. **Outputs:** pin-coverage table appended to ledger; any gap-filling pins. **Evidence:** pin↔defect mapping per item. **Rollback:** n/a (tests only). **Regression:** this IS the regression audit. **Battery:** full run if any pin added. **Stop:** a pin cannot express the defect without app-code change (report — that's a testability finding, not a license to refactor). |
| **FIX-E** — Sequential battery certification | **Scope:** terminal full battery over the final aggregate state. **Inputs:** all prior sub-phases closed. **Outputs:** final count + reconciled arithmetic (entry baseline + Σ pins per sub-phase = final; every intermediate run listed). **Evidence:** command lines + counts + timing, per U5 canonical procedure (9-app suite then patterns_ai, fresh DBs, sequential). **Rollback:** n/a. **Regression:** any red = §16.8. **Battery:** this is it. **Stop:** red beyond just-added pins' target behavior. |
| **FIX-F** — Documentation synchronization | **Scope:** sweep-verify U6 completeness for the whole phase (each fix already synced same-session; this audits): every closed item's app GUIDE/README rows current; CHANGE_IMPACT_MATRIX consulted per changed file with each mapped doc updated or N/A-stated; DEPLOYMENT_BACKLOG rows struck/updated; DOCUMENTATION_INDEX rows for any new files. **Inputs:** ledger + diffs. **Outputs:** docs-sync table appended to ledger. **Evidence:** per-file matrix-row disposition. **Rollback:** docs-only. **Battery:** not run (no code). **Stop:** a doc update reveals a truth-lock contradiction (report, framework conflict rule). |
| **FIX-G** — Final verification + campaign reconciliation | **Scope:** the accounting close. **Inputs:** everything above. **Outputs:** reconciliation statement in the ledger: every phase-1–3 finding in exactly one terminal state; backlog line-by-line review (MGT-H precedent); carry-forward list for phases 5–22 (INFO rows, Design-Record answers, doc-drift items routed to 6–7); the sentence-form input for the Phase-21 readiness certificate; PHASE-4 VERDICT. **Evidence:** completeness census with arithmetic (findings in = rows out). **Battery:** not re-run (FIX-E stands unless code changed after it — which §2.3 forbids). **Stop:** unaccounted finding discovered ⇒ back to FIX-0 intake as an amendment, dated. |

## 8. Deliverables

- `docs/CONFIRMED_FINDINGS_LEDGER.md` (NEW at FIX-0; append-only; the phase's evidence doc —
  fix-evidence blocks live in it, mirroring how certification phases append evidence sections).
- Filled Design Record (Appendix A): F-D1 selections, F-D2 per-item approvals, F-D3 scope.
- Fixes + pins per closed work item; final battery number with reconciled arithmetic.
- Updated DEPLOYMENT_BACKLOG (struck/annotated rows), status file, memory per sub-phase.
- FIX-G reconciliation statement (Phase-21 input).

## 9. Files expected to change

**Always (docs):** `docs/CONFIRMED_FINDINGS_LEDGER.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DEPLOYMENT_BACKLOG.md` ·
`docs/DOCUMENTATION_INDEX.md` (ledger row at FIX-0; plus any new files) · this file (Design
Record + dated amendments only) · memory files (if agent has memory).
**Per closed work item (code):** the item's owning app file(s) · the app's certification test
module (or `test_confirmed_findings.py` sibling per §6.3) · the app's GUIDE/README +
CHANGE_IMPACT_MATRIX-mapped docs (U6). Nothing outside the ledger's approved work items.

## 10. Files that must never change (touching one = STOP + report)

- Anything not owned by an approved ledger work item (the §3.4 zero-scope-creep criterion made
  file-concrete).
- Migrations, `config/config/settings/*`, `permission_service` role-set constants,
  enforcement flags — except a specific item carrying its F-D2 owner approval reference, and
  then ONLY the approved change.
- Money single-writer services beyond an approved item's confirmed defect (U8 review mandatory
  in the evidence block).
- Frozen-foundation modules (U9), `docs/adr/`, PDD, ARCHITECTURE_V2, freeze packages absent an
  approved item.
- Non-DEV user rows; the 2 pre-existing stashes; `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) ledger updated (rows + evidence blocks — closed
blocks never edited, corrections appended dated); (b) status-file Phase-4 sub-phase table +
dashboard (battery, docs-sync, memory-sync, carry-overs) + "Next action"; (c) backlog row
updates (strike resolved with pointer, add none — this phase discovers nothing); (d) per
closed item: U6 docs same session (not deferred to FIX-F — FIX-F audits); (e) new file ⇒
DOCUMENTATION_INDEX row.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-4
bullet: items closed, battery number, ledger pointer) + MEMORY.md index line at each sub-phase
close. Agents without memory: skip — the ledger + status file are the complete binding record;
nothing may exist ONLY in memory.

## 13. Battery policy

Sequential fresh-DB canonical (U5): 9-app suite then patterns_ai, never `--parallel`, never
`--keepdb` across suites (backlog #4 + MGT-F addendum). Entry baseline = the status-dashboard
number AT FIX-0 (1526/1526 at authoring — phases 2/3 execution may raise it first; never
assume). Expected after any fix = prior + new pins, arithmetic recorded per run (precedent
chain 1519→1522→1524→1526). Timing per §6.4. A 0-code sub-phase states "battery NOT re-run
(baseline stands)".

## 14. Regression policy

- Prior-fix guard list (re-proven wherever a Phase-4 change touches its surface): BUG-1
  (cutting complete gate) · BUG-2 (layering draft scope) · BUG-3 (alloc ₹ ctx) · BUG-E1
  (master CRUD roles) · S2 (signup closed) · S3 (email shadow) · MGT-B-1 (refusals flash,
  never 500) · #5 (delete-confirm renders) · MGT-F-1 (machine-code immutability) — plus any
  fixes phases 2/3 add before FIX-0 (the ledger imports their guard entries).
- Every permission fix re-proves its surface's full identity lattice (FIX-A tightening).
- Certified-phase verdicts are never reopened by this phase; evidence contradicting a CLOSED
  certification = §16.7 report.
- Pins only for fixes (U4); FIX-D audits coverage, it does not speculate.

## 15. Rollback policy

- Code: single-fix-at-a-time makes every fix independently revertable — an aborted item's diff
  is reverted whole (file-scoped), its ledger row steps back one lifecycle state with the
  failure recorded; never half-landed.
- Shell probes: one `transaction.atomic` block per cluster, forced rollback, byte-identical
  recounts (counts named per category in §7).
- Browser: DEV-marked rows, create→verify→delete round-trips; un-unrollable append-only
  artifacts disclosed in the evidence block (U13).
- Ledger/Design Record: append-only; a changed owner decision is a dated amendment row.
- Session crash mid-item: next session re-baselines counts FIRST, reconciles any orphan state
  against the item's evidence block, and resumes the item at its recorded lifecycle state
  (worker-cert Phase-B lesson: evidence is written incrementally, not at session end).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. FIX-0 preconditions unmet: phase 2 or 3 not closed (and no recorded reduced-scope order),
   or F-D1/F-D2 unanswered.
3. Classification dispute — an intake item fits no class or two classes (owner arbitrates;
   no silent upgrade to confirmed-bug).
4. A fix requires a migration (U14), settings change, role-set change, or frozen-module edit
   WITHOUT its F-D2 approval reference.
5. Scope growth mid-fix — the smallest change wants a second file/concern, or a "nearby
   improvement" tempts (U1); also: a NEW defect discovered mid-fix (it is recorded as an
   observation for the backlog/certification, and if it blocks the current fix, the item
   rolls back and the session stops).
6. Money-write anomaly (U8) or golden-invariant drift (₹225 / ledger Σ).
7. Evidence contradicts a CLOSED certification.
8. Battery red on anything other than the just-added pins' target behavior.
9. Owning-file drift: the file to be fixed changed since the finding was confirmed
   (re-confirmation belongs to a certification phase, not here).
10. Identity lockout (rate limit) during reproduction probes.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-4 row: which FIX-* is next; battery
   baseline; carry-overs.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → this contract FULLY.
3. Read `docs/CONFIRMED_FINDINGS_LEDGER.md` if it exists (absent ⇒ next work = FIX-0): row
   states, evidence blocks, Design Record answers. The ledger, not memory, is the work queue.
4. Verify preconditions read-only: git HEAD vs status file; battery baseline; for the next
   work item — its owning file unchanged since confirmation (§16.9), its approval ref if
   gated, its source evidence section reachable.
5. Identities/passwords per the owning certification's cast list (framework README env facts;
   owner supplies SA password at session start).
6. Execute exactly ONE sub-phase per §7 (within it, items strictly serial per §6.5). STOP per
   §16.
7. Anything internally inconsistent across status file / ledger / this contract / source
   evidence docs → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (FIX-0)

| # | Item | What the record shows | Decision needed | Owner answer |
|---|---|---|---|---|
| F-D1 | Backlog selection | Open rows at authoring: #1 (infra, sequencer) · #3 (polish, inline style) · #4 (infra, test isolation) · #6 (doc-drift → phase 7 by precedent) · #7/#8/#9 (INFO, fix-when-touched, each with a written fix spec) | Which rows (if any) upgrade into Phase-4 work items? Default: NONE — all stay Deferred per their why-deferred column | **"NONE. Do not promote any backlog items into Phase 4. Leave backlog rows #1, #3, #4, #7–#14 deferred exactly as documented. Keep #6 permanently routed to KOS Phase 7."** (owner verbatim, 2026-07-13; rows #10–#14 had joined the backlog after authoring — the answer covers the full open set at FIX-0) |
| F-D2 | Approval-gated deferrals | Certification phases stop on migration/settings/role-set/frozen-module fixes; those arrive "confirmed + deferred" | Per-item approval (verbatim, one row each as they arrive from phases 2/3) — an item without a row here is untouchable | **"CONFIRMED EMPTY. No approval-gated items are selected."** (owner verbatim, 2026-07-13 — matches the FIX-0 §2.2.5 census: zero deferrals arrived from phases 2/3) |
| F-D3 | Permanence scope | Owner designated this contract the campaign's permanent implementation protocol (2026-07-12, recorded §6.6) | Confirm post-phase-22 adaptation (§6.6: commit discipline replaces U2; all else stands), or amend | **"CONFIRMED. Adopt §6.6 permanently exactly as written. Post-Phase-22 commit discipline replaces U2. All remaining permanence rules remain unchanged."** (owner verbatim, 2026-07-13) |

Date · answered by: **2026-07-13 · Owner (Umesh), recorded verbatim at FIX-0 close (evidence: CONFIRMED_FINDINGS_LEDGER.md §9)**

## Dated amendments

_(none)_

# Evidence note

Per-item fix evidence lives in `docs/CONFIRMED_FINDINGS_LEDGER.md` (created at FIX-0), not in
this contract — the contract is procedure; the ledger is what happened (framework hierarchy
rule).
