---
id: docs-campaign-contracts-phase-16-monthly-expense-engine
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 16 Execution Contract — Monthly Expense Engine

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md) and the full new-feature lock-set established at
> [PHASE_15_BUSINESS_OPERATING_DASHBOARD.md](PHASE_15_BUSINESS_OPERATING_DASHBOARD.md):
> frozen PDD (charter enters via change-control) · MANUFACTURING_V1_FREEZE · U8/Money-Write
> STOP · U9 · Phase-10 UI canon · P11/P12 dataset mechanics · P13/P14 instruments. Deltas only.
> **The governing truth-lock is ADR-0011** (monthly-salary-factory-level), which RESERVED this
> exact future: FactoryExpense = a factory-level cost record — **NEVER allocated into
> per-Adda manufacturing cost**; `FactoryExpense.worker` FK = audit-only, "must never create a
> ledger or settlement relationship"; any future allocation feature "must not require changing
> production history, settlement history, worker history, or FactoryExpense history"; salary
> entering processing_cost/full-cost/settlement = an ADR violation absent an owner-approved
> revision. **This contract implements the reserved automation WITHOUT touching any of that.**
> Second lock: **`expense_service` is the SOLE FactoryExpense writer** (R5: append-only
> posture, create/void only, "No edit function EXISTS", void = super-admin with mandatory
> reason — MGT-C-certified as one of the 4 SA-only levers).
> **Two campaign firsts this phase must handle:** (a) new MODELS ⇒ migrations ⇒ the U14
> owner-approval procedure runs for real; (b) a new legitimate money-write CALLER ⇒ the
> Money-Write census baseline (R5_HOSTILE_REVIEW Part 2) gets its first sanctioned, dated
> addendum. **Product content (what recurs, amounts, cadence, approval flow) is NOT on
> record** — owner charter at MEE-0, never invented (the PHASE_15 BOD-D1 discipline).
> Evidence doc (created at MEE-0): `docs/MONTHLY_EXPENSE_ENGINE_LOG.md`.

## 1. Phase objective

Automate recurring factory expenses — the monthly salaries and any other owner-chartered
recurring costs — so that each period's FactoryExpense rows are generated from owner-defined
recurrence templates: idempotently (one row per template per period, constraint-backed),
through the existing single writer (`expense_service`), append-only as ever (generated rows
are ordinary FactoryExpense rows: voidable by the SA lever, never edited), management-visible
and management-triggered, with the ledger, settlements, and per-Adda costing untouched by
construction. The engine removes monthly typing, not monthly control.

## 2. Scope

### 2.1 Facts of record (authoring-time; MEE-0 re-verifies)

| Fact | Evidence |
|---|---|
| FactoryExpense today | R5 (docs/R5_EXECUTION_PLAN.md, ACCEPTED): append-only (create/void, no edit function exists); `expense_service` = sole writer (rules 4/5); void = SA-only + mandatory reason; a COST RECORD, never a ledger (ADR-0011); UI = management list + create (MGT-C certified: create=management, void=SA lever) |
| ADR-0011 guardrails | factory-level only; worker FK audit-only; no ledger/settlement relationship ever; future features must not require changing production/settlement/worker/FactoryExpense HISTORY; revisions = owner-approved ADR change first |
| Monthly workers | pay_basis=monthly exists (SA-only flip, payroll_service P-2); monthly workers structurally excluded at `_settleable_lines`; FnF path exists (fnf_service, SA-only); dev cast has a monthly worker — the salary-shaped audience for this engine |
| Money-Write census baseline | R5_HOSTILE_REVIEW_2026_07_05 Part 2 = the approved money-writer census (owner Money-Write STOP rule names it the baseline) — a new caller/function REQUIRES a dated, owner-approved addendum, not a silent extension |
| Scheduler reality | NO celery/queue/cron infrastructure exists in the repo — "automation" cannot mean unattended in-app scheduling (MEE-D4) |
| No recurrence model exists | no template/recurrence/period table anywhere — the engine needs new models ⇒ migrations ⇒ U14 procedure (MEE-D2) |
| Battery | the expense app is ALREADY a battery member — this phase grows an existing suite (NO framework-README amendment needed, unlike phases 12/13/15) |
| Golden truth | settled journeys ₹801.00/₹344.25/₹633.00 + golden ₹225 must remain byte-identical — the engine's do-no-harm proof for the settlement path it never touches |

### 2.2 In / out

**In:** the owner-chartered recurrence catalog (MEE-D1) · recurrence data model + U14-gated
migrations · additive generation function(s) inside the expense service family (single-writer
preserved) · idempotent period generation · management UI (template administration +
period-generation trigger + review) per the certified gating pattern · tests + battery ·
docs/dataset/BOD handoffs · the Money-Write census addendum.
**Out:** ANY per-Adda allocation of factory expenses (ADR-0011 wall — a chartered item
demanding it = owner ADR-revision territory, not this phase) · ledger/settlement interaction
of any kind · editing FactoryExpense rows (append-only stands; a generated-wrong row is
VOIDED via the existing SA lever + regenerated) · changing the void lever, pay-basis lever,
FnF, or any existing money behavior · schedulers/queues/celery/cron-in-repo (external cron
invoking a management command = a post-deploy ops decision, MEE-D4) · payroll/salary
DISBURSEMENT (recording a cost ≠ paying a person; worker payment stays settlement/FnF
territory untouched) · PDD body edits (amendment register entry per change-control) ·
BOD widgets (recorded as a handoff; built under the PHASE_15 ladder later or as this phase's
final owner-gated wave — MEE-D8).

## 3. Success criteria

Phase 16 is DONE when ALL hold:
1. The owner's product charter is recorded via PDD change-control (MEE-D1: the recurring
   catalog — which expense types, amount sources, cadence, who triggers, approval/review
   flow, proration + backdating policy) — BEFORE any model was designed.
2. **U14 honored for real:** the data-model design was presented and each migration
   individually owner-approved BEFORE being written; migrations are minimal, additive, and
   reversible-by-design (documented reverse path), touching NO existing table's schema.
3. **Single-writer preserved, proven:** FactoryExpense rows are created ONLY by
   `expense_service`-family code; the generation function lives inside that family; the
   engine's UI/command layers hold zero write logic (purity test: no ORM writes to
   FactoryExpense — or any guarded table — outside the service module); the Money-Write
   census addendum is recorded, dated, owner-approved.
4. **ADR-0011 compliance proven:** generated rows are factory-level (no Adda linkage
   anywhere in the new schema or queries); worker FK (if the charter uses it for salary
   rows) remains audit-only — a grep+schema proof that no ledger/settlement/costing path
   references the new tables or the generated rows beyond the existing FactoryExpense
   surfaces; per-Adda cost pages byte-identical on a seeded world before/after generation.
5. **Idempotency proven:** one row per (template, period) constraint-backed; re-running
   generation for a covered period creates zero rows and reports why; a voided row's period
   can be regenerated ONLY per the chartered policy (MEE-D5).
6. **Append-only honored:** no edit path exists for templates' GENERATED rows (template
   changes affect FUTURE periods only, per the chartered proration policy); template rows
   themselves follow soft-state discipline (deactivate, never delete — U13/data-principles).
7. **Money do-no-harm proven:** ledger row-count/Σ byte-identical around every probe wave;
   golden journeys byte-identical; settlement lifecycle regression spot-run green;
   existing FactoryExpense create/void behavior unchanged (MGT-C pins still green).
8. **Permissions certified** (certification-grade, per MEE-D6 matrix): template
   administration + generation trigger gated per charter; void stays the SA lever; all-identity
   matrices + double-gate + negative controls; mobile-first UI per Phase-10 canon.
9. Battery green at the new baseline (entry + expense-suite growth; arithmetic per wave);
   knowledge_sync diff-mode clean at close; U6 docs complete (expense README/GUIDE are the
   owning docs); `seed_feature monthly-expense` recorded as a dated P11 amendment; BOD-widget
   handoff written; status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inherited locks)

- **Charter fidelity (BOD-D1 discipline):** the recurring catalog, amounts, cadence, and
  approval flow are the owner's; nothing is added to the catalog uninvited.
- **U14 procedure (normative, first live use):** at MEE-A the executing agent STOPS after
  presenting the model design + migration plan (tables, columns, constraints, indexes,
  reverse path) and resumes only on the owner's recorded per-migration approval. No migration
  is written speculatively; no existing table is altered.
- **Writer discipline:** new write logic = additive function(s) INSIDE the expense service
  family, hostile-reviewed (money-phase mindset, owner standing rule), with the census
  addendum. The UI/command layers orchestrate and render; they never write. Existing
  `expense_service` functions are NOT modified (additive only; a needed change to an existing
  function = stop → owner).
- **ADR-0011 is load-bearing, not decorative:** every wave's evidence includes the
  no-allocation proof of §3.4's form; a chartered requirement that brushes the wall stops the
  phase for an owner ruling (the requirement changes or the ADR does — by its own process).
- **Generated money is still money:** generation probes run rollback-wrapped in shell first;
  browser generation only on DEV-marked scratch worlds; every landed row disclosed or
  round-tripped via the void lever (U13).
- One wave at a time (serial discipline); the money-write function wave (MEE-B) is
  main-thread, U8-hostile, never delegated wholesale.

## 5. Evidence standard

Per wave: commands/UI actions + outputs quoted · row-count tables (FactoryExpense before/
after/rolled-back) · ledger recount (count/Σ) around every wave · idempotency double-run
proofs · the ADR-0011 no-allocation proof set (schema grep + costing-page byte-compare on a
seeded world) · permissions matrices (shell + browser, all identities) · mobile 3-width
browser evidence after restart · battery arithmetic per wave · golden-journey byte-checks at
MEE-D. The census addendum quoted verbatim with its owner approval. Sub-agent scaffolding
sweeps supplemental (U7); charter recording, migration gates, the service function, money
proofs, and certification = main-thread.

## 6. Methodology

### 6.1 Engine shape (orchestrator over the single writer)

Three thin layers over one heavy rule: **templates** (owner-defined recurrence records:
expense type, amount source, cadence anchor, active window — new models, expense app) →
**generation** (an additive `expense_service`-family function: given a period, resolve due
templates → create FactoryExpense rows via the existing create path → record the
(template, period) coverage — idempotent, constraint-backed, transactional per period) →
**surfaces** (management UI: template administration, "generate period" trigger with preview,
generated-rows review linking into the EXISTING FactoryExpense list; optionally a management
command wrapping the same service function for external cron — MEE-D4). The engine lives in
the expense app (fit-existing-architecture: the owning domain extends, no new app), at the
same layer, importing nothing new upward.

### 6.2 Period + idempotency semantics (MEE-D5 frame; policy content = charter)

A period = the owner-chartered cadence unit (monthly anchor expected). Coverage is recorded
per (template, period) with a DB uniqueness constraint — generation converges: covered
periods produce zero new rows and say so. Template lifecycle: create → active → deactivated
(soft-state; never deleted while referenced); amount/detail changes affect FUTURE periods
only unless the chartered proration/backdating policy says otherwise (MEE-D1/D5 — proration,
mid-month starts, back-periods, and voided-row regeneration are OWNER POLICY, not defaults
this contract invents). Preview-before-write: the trigger shows what WOULD be created
(template, amount, period) before the confirming POST.

### 6.3 What generation may read (and what it may not)

Amount sources per the charter (e.g. a fixed template amount; IF the charter wants salary
amounts read from a worker-profile field, that read is audit-transparent and the worker FK
stays audit-only per ADR-0011). Generation NEVER reads production/settlement state to compute
amounts (a "percentage of output"-style chartered item = ADR-0011-adjacent → owner ruling
first). Generation writes exactly one table family: FactoryExpense + the new coverage/template
tables. Nothing else, provably (purity test scope).

### 6.4 Certified-pattern surfaces

Gating per MEE-D6 (dispatch mixin + SidebarItemRule row via the Access Control UI — no seed
migration + middleware double-gate + AJAX fork); financial amounts on-screen = management
surfaces (this is the expense app's existing posture; FINANCIAL_ROLES is a raw-materials
field wall, not the expense gate — the expense pattern of record is `_ManagementOnly` + SA
levers, and this engine follows it). UI composes from Phase-10 certified owners (forms are a
FROZEN family — the template form uses the existing form-shell canon, no new form system);
mobile summary-first; delete-confirm class pages get the #5-regression watch.

### 6.5 Integration hooks

**Dataset:** `seed_feature monthly-expense` (dated P11 amendment) — templates + a generated
period + a voided example on scratch worlds; the demo/acceptance substrate. **Verification:**
candidate P13 checks (coverage-uniqueness holds; generated rows factory-level — a
no-Adda-linkage predicate) = handoff notes, adopted per P13's own registry law. **Knowledge:**
feature doc + cards via the graph/generation pipeline; knowledge_sync diff-mode per wave
(the P14/P15 discipline). **BOD:** the engine's headline numbers (this month's recurring
total, pending generation state) become BOD widgets ONLY via the PHASE_15 ladder + registry
(MEE-D8: built here as a final owner-gated wave, or handed to a later session — owner's
call). **Phase 17:** raw-material → expense cost integration will sit BESIDE this engine in
the same app; this contract's schema decisions must not paint Phase 17 into a corner
(MEE-D2 asks the owner to see the Phase-17 one-liner when approving the model design).
**Deployment:** migrations join the deploy story (Phase 19 runbook: migrate step ordering);
external-cron wiring = post-deploy ops decision, documented not implemented.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery at every
code-wave close**.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **MEE-0** — Product charter + gate + ratification | Gate: Phase 15 closed (locked order). **Owner supplies the charter** (recurring catalog · amount sources · cadence · trigger/approval flow · proration/backdating/void-regeneration policy) via PDD change-control (amendment-register entry). Owner ratifies MEE-D1..MEE-D9. Baselines: battery entry; ledger count/Σ; FactoryExpense count; golden-journey reference values quoted. **Stop:** charter absent/ambiguous; any MEE-D unanswered. |
| **MEE-A** — Data-model design + U14 gate + migrations (battery-bearing) | Present the model design (templates + coverage; constraints incl. (template, period) uniqueness; soft-state fields; NO existing-table changes; reverse paths) → **STOP for per-migration owner approval (U14)** → write approved models+migrations → migrate scratch worlds → battery. **Stop:** approval absent; any existing-table alteration; a schema element implying Adda linkage. |
| **MEE-B** — Generation service (battery-bearing; U8-hostile, main-thread) | The additive `expense_service`-family generation function: period resolution → preview data → creation via the existing FactoryExpense create path → coverage rows; transactional; idempotent; hostile-review pass (money-phase mindset); the purity test (no guarded-table writes outside the service module); **the Money-Write census addendum recorded with owner approval**; rollback-wrapped shell proofs + ledger recount + ADR-0011 proof set v1. **Stop:** U8 anomaly; any temptation to modify an existing service function; census addendum unapproved. |
| **MEE-C** — Management surfaces (battery-bearing) | Template administration (soft-state lifecycle) + generate-period trigger with preview→confirm + generated-rows review into the existing expense list; sidebar rule via Access Control UI; Phase-10 canon + mobile evidence; #5-class delete/confirm watch. **Stop:** any write outside the service function; gating diverges from the certified pattern. |
| **MEE-D** — Money certification wave | Full do-no-harm set: ledger byte-identical across a generate+void round-trip · golden journeys byte-identical · per-Adda costing pages byte-identical pre/post generation (seeded world) · MGT-C pin behaviors re-proven (create/void unchanged, void stays SA) · all-identity permission matrices + negative controls + AJAX forks · idempotency + voided-period policy proofs per charter. **Stop:** any drift in ledger/golden/costing bytes; a leak or false block. |
| **MEE-E** — Certification + handoffs | knowledge_sync diff-mode dispositioned; U6 docs (expense README/GUIDE = owning docs; CHANGE_IMPACT_MATRIX); `seed_feature monthly-expense` P11 amendment; P13 check handoff notes; BOD-widget disposition per MEE-D8; deployment note (migration ordering for Phase 19); charter-coverage census (every chartered item built/deferred/declined — counted); PHASE-16 VERDICT. **Stop:** unaccounted chartered item. |

## 8. Deliverables

- The engine in the expense app: template + coverage models (U14-approved migrations),
  the additive generation service function (census-addended), management surfaces —
  single-writer, append-only, ADR-0011-clean, idempotent, certified.
- Expense-suite test growth (models/constraints/idempotency/purity/permission pins) in the
  battery; the Money-Write census dated addendum; the PDD amendment-register entry.
- `docs/MONTHLY_EXPENSE_ENGINE_LOG.md`: charter record · U14 approvals · per-wave evidence ·
  money proofs · certification + handoffs.
- U6 docs (expense README/GUIDE updated, index rows); the P11 spec amendment; filled Design
  Record (MEE-D1..MEE-D9).

## 9. Files expected to change

**Code (expense app, gated as stated):** new models file/section + U14-approved migrations ·
the additive service function (inside the expense service family) · new views/templates/URLs
for the surfaces · the app's tests. **Code-adjacent:** none expected (no settings, no
importlinter — same app, same layer). **Docs:** `docs/MONTHLY_EXPENSE_ENGINE_LOG.md` (new) ·
`config/expense/README.md` + `docs/apps/expense/GUIDE.md` (U6, owning docs) · status file ·
DOCUMENTATION_INDEX · the PDD amendment register · the Money-Write census baseline doc
(dated addendum) · `docs/DEV_DATASET_ARCHITECTURE.md` (dated amendment) · this file (Design
Record + amendments) · memory. **Runtime:** scratch worlds. NOTE: no framework-README battery
amendment (expense is already a member).

## 10. Files that must never change (touching one = STOP + report)

- Existing `expense_service` FUNCTIONS (additive-only rule) · `ledger_service` ·
  `settlement_service` / `adda_settlement_service` · `payroll_service` (incl. the pay-basis
  lever) · `fnf_service` · `advance_service` — the engine adds beside them, never inside them.
- Any existing table's schema (migrations are additive-new-tables only) · any existing
  FactoryExpense row (append-only; void is the only state change, via the existing lever).
- ADR-0011 and every truth-lock (a chartered conflict = owner ADR process, not an edit) ·
  PDD body · MANUFACTURING_V1_FREEZE · enforcement flags (U10) · settings (base/local/
  production) · `.env`.
- Per-Adda costing surfaces, settlement lifecycle, worker payroll/earnings pages — untouched
  and byte-proven (§3.4/§3.7).
- The PRIMARY dev DB (scratch worlds only) · non-DEV data · the 2 stashes · `.git` (U2 — the
  approved migrations sit uncommitted in the working tree like all campaign work).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-16 row + dashboard (battery per wave)
+ "Next action"; (c) **U6 fully applies**: expense README/GUIDE current per wave (new files
→ GUIDE rows), CHANGE_IMPACT_MATRIX per changed file, DOCUMENTATION_INDEX rows; (d) the PDD
amendment entry (MEE-0), the census addendum (MEE-B), and the P11 amendment (MEE-E) recorded
at their owning documents per those documents' own rules; (e) knowledge_sync findings
dispositioned per wave.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-16
bullet: wave closed, U14 approvals, census-addendum state, battery arithmetic, log pointer)
+ MEMORY.md index line at each sub-phase close. Agents without memory: skip — the log +
status file + the owning registers (PDD/census/spec) are the complete binding record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (MEE-A..MEE-C, and any MEE-D
fix wave)**. Arithmetic: entry baseline (status dashboard at MEE-0) + expense-suite growth
per wave — **no framework amendment needed** (expense is an existing battery member; the
canonical command list is unchanged). Migration waves additionally prove clean
migrate-forward on a fresh scratch DB and the documented reverse path on a disposable copy.

## 14. Regression policy

- Full battery green every wave = frozen-engine do-no-harm; MGT-C's certified expense
  behaviors (create=management, void=SA+reason, 4-lever walls) re-proven at MEE-D with the
  engine present.
- Ledger count/Σ + golden journeys + per-Adda costing byte-checks = the money regression
  instruments, run at every money-adjacent wave.
- The purity test + (template,period) constraint tests + permission pins = this phase's
  permanent pins.
- Prior-fix guard list surfaces touched by new templates/pages (#5 delete-confirm class,
  MGT-B-1 flash class) re-proven in browser waves.
- Incidental defects = observations → U12 (+U8 stop if money); fixes via the Phase-4
  protocol (cross-logged).

## 15. Rollback policy

- Pre-migration waves revert file-scoped. Post-migration: the documented reverse path
  (additive-new-tables ⇒ reverse = drop the new tables; proven on a disposable copy at
  MEE-A) — but under U2's no-commit regime a landed migration is treated as
  semi-irreversible: reverting it after later waves = owner decision, never unilateral.
- Generated rows in probe worlds: void-lever round-trips or world disposal (scratch);
  landed disclosed artifacts per U13.
- The log + Design Record append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests + re-baselines ledger/counts
  FIRST, reconciles the log, completes or reverts before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. MEE-0 charter absent/ambiguous, or any MEE-D1..D9 unanswered.
3. **U14:** any migration need beyond the approved plan, or approval absent at MEE-A's gate.
4. **U8:** any FactoryExpense (or other guarded-table) write path outside the expense-service
   family; the census addendum missing/unapproved; any ledger/settlement interaction from
   engine code.
5. **ADR-0011:** any chartered requirement or design element implying per-Adda allocation,
   ledger linkage, or worker-payment semantics — owner ruling territory.
6. An existing service function/table/row would be modified (additive-only breach; append-only
   breach; edit-path temptation on generated rows).
7. Money byte-drift: ledger/golden/costing checks fail at any wave.
8. Permissions leak/false-block; gating pattern divergence.
9. Battery red beyond the wave's own new tests' target behavior; knowledge_sync BLOCKER at
   a wave close.
10. Scope creep toward disbursement, payroll integration, allocation, or scheduling
    infrastructure.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-16 row: which MEE-* is next; battery
   arithmetic; ledger/golden baselines.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env) → **ADR-0011 + the R5 record +
   `config/expense/README.md`** (the owning truths) → this contract FULLY (charter + U14
   approvals + census-addendum state in the Design Record/log) →
   `docs/MONTHLY_EXPENSE_ENGINE_LOG.md` if it exists (absent ⇒ next = MEE-0).
3. Verify read-only: migration state on a scratch world matches the log; purity tests green
   in THIS tree; ledger count/Σ + FactoryExpense count vs the last wave's baseline; golden
   references unchanged.
4. Money waves (MEE-B/D) = main-thread, hostile-review mindset, ledger recount discipline —
   never delegated wholesale (owner standing rule).
5. Battery environment per framework env facts; browser on :8003 with restart after template
   edits; scratch worlds only.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / charter / ADR-0011 / census baseline / log /
   this contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (MEE-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| MEE-D1 | **Product charter** | OWNER-SUPPLIED: the recurring catalog (which expense types — salaries? rent? utilities?), amount source per type (fixed template amount vs a profile-field read), cadence + period anchor, who triggers generation, approval/review flow, proration + backdating + voided-period-regeneration policy — via PDD change-control. No default exists; unanswered = phase blocked | **APPROVED 2026-07-18** ("The MEE-0 Design Review is approved… Approve the refined MEE-D1 charter"). Charter = PDD amendment-register **entry 7**; full record MONTHLY_EXPENSE_ENGINE_LOG §0.12. Headlines: V1 MONTHLY only, frequency-general schema; fixed template amounts (User.salary stays informational — L-3/F4); preview→confirm; M-3-respecting salary skip; void→regenerate supersession w/ reason; month-end clamp; boundaries re-affirmed (RM purchasing · payroll · settlement · BOD · supplier mgmt all OUT) |
| MEE-D2 | Data model + U14 gate | New ADDITIVE tables only (recurrence template + period coverage), (template, period) uniqueness, soft-state lifecycle fields; per-migration owner approval BEFORE writing; reverse path documented + proven on a disposable copy; owner sees the Phase-17 charter line when approving (no schema corner-painting) | **ACCEPTED as default 2026-07-18** |
| MEE-D3 | Writer discipline + census addendum | FactoryExpense writer stays the expense-service family; generation = additive function inside it; UI/command layers write nothing; dated owner-approved addendum to the R5 Part-2 Money-Write census | **ACCEPTED as default 2026-07-18** |
| MEE-D4 | Trigger mechanism | Management-triggered generation with preview→confirm (UI) + a management command wrapping the same service function; NO in-repo scheduler; external cron = post-deploy ops decision, documented only | **ACCEPTED as default 2026-07-18** |
| MEE-D5 | Period/idempotency semantics | One row per (template, period), constraint-backed, converging re-runs; template changes affect future periods only; proration/backdating/void-regeneration = per the D1 charter (no invented defaults) | **ACCEPTED as default 2026-07-18** (charter fills the policy content: no proration V1 — templates start at their start_date period; backdating = generation allowed for any period within the active window; void-regeneration = explicit + reasoned + supersession-chained) |
| MEE-D6 | Permissions | Template administration = SA-only default (templates encode salary amounts); generation trigger = management default; void unchanged (SA lever); certified double-gate pattern; ratify the split | **ACCEPTED as default 2026-07-18** |
| MEE-D7 | Tests + battery | Expense-suite growth (constraints, idempotency, purity, permissions, ADR-0011 predicates); NO framework amendment (existing member); golden byte-checks in MEE-D | **ACCEPTED as default 2026-07-18** |
| MEE-D8 | BOD widgets | Engine KPIs enter the BOD ONLY via the PHASE_15 ladder + registry — built as this phase's final owner-gated wave OR handed to a later session (owner's call here) | **RULED 2026-07-18: "BOD changes remain outside this phase"** → handoff to a later session via the PHASE_15 ladder + registry (recorded at MEE-E) |
| MEE-D9 | Monthly-worker relationship | If salary templates reference workers: FK stays audit-only (ADR-0011); pay-basis flips and FnF remain untouched SA levers; engine behavior on a worker's exit/FnF (stop template? owner action?) = charter policy, not engine invention | **RULED 2026-07-18 (Q13):** worker inactive ⇒ future salary generation stops AUTOMATICALLY (generation-time worker-active check — no FnF/payroll coupling); existing generated rows unchanged; history never modified; Final Settlement stays Payroll's; MEE performs NO FnF calculations. **+ Template-amount ruling: NOT immutable — identity stable, amount changes allowed + historically traceable, generated months never change (evaluation → MEE-A package)** |

Date · answered by: **2026-07-18 · owner (MEE-D1 charter message + MEE-A authorization message), recorded same session**

## Dated amendments

_(none)_

# Evidence note

All build evidence lives in `docs/MONTHLY_EXPENSE_ENGINE_LOG.md` (created at MEE-0) —
contract = procedure, log = what was chartered, approved (U14 + census addendum), built, and
proven (framework hierarchy rule). The product truth lives in the PDD amendment register; the
money truth stays exactly where ADR-0011 and the R5 census put it.
