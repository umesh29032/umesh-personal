---
id: docs-campaign-contracts-phase-11-development-dataset-architecture
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 11 Execution Contract — Development Dataset Architecture

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md); Standard-bound (the spec artifact obeys `docs/DOC_STANDARDS.md`
> typology/metadata/ownership). **This is a DESIGN phase (documented-not-implemented charter —
> status file: "Phases 12/13/14 are documented-not-implemented until their turn"): its sole
> build artifact is an architecture specification.** No Python, no fixtures, no datasets, no
> commands, no DB writes are produced by Phase 11 — Phase 12 (Seeder Engine) implements the
> spec; Phase 13 (Verification Engine) consumes its assertions.
> Governing owner rules wired in: **Test-Data Authorization 2026-07-04** (freely create
> DEV-marked temp data; never a future-phase dependency unless documented) · **Factory-Driven
> Development** (validate on DEV-NICKAR + T-SHIRT + Lower; real factory problems) ·
> **Data/History principles 2026-06-09** (append-only history; soft-state over delete) ·
> U8 single-writer discipline · U10 flags stay OFF.
> Evidence sections append to THIS contract (small design phase — PHASE_00/PHASE_05 pattern);
> the deliverable spec = `docs/DEV_DATASET_ARCHITECTURE.md` (created at execution, NOT now).

## 1. Phase objective

Design the project's development dataset as an architecture: deterministic, reproducible,
resettable, idempotent, production-safe, DEV-marked data — layered, scenario-organized,
stably-identified, versioned, and validated — formalizing what today exists only as an
organically-grown dev database (the 3-PATTI worlds, the Dev@12345 cast, DEV-NICKAR, the three
settled golden journeys), so that Phase 12 can implement `seed_demo` / `seed_factory` /
`reset_demo` / `seed_feature <x>` against a frozen spec instead of folklore, and Phase 13 can
verify seeded worlds against embedded expected values.

## 2. Scope

### 2.1 Facts of record (authoring-time; DSA-A re-verifies + completes the census)

| Fact | Evidence |
|---|---|
| An organic dev dataset EXISTS | dev worlds 3-PATTI-011/013/014/015 (owner-declared evidence worlds; teardown of 013/014/015 was owner-gated at Phase-3 config) · DEV-NICKAR cutting table · T-SHIRT 16-op + Lower 13-op REAL flows (Phase-3 config pass 1) · cast `dev.ow.a-d`/`sw.a-b`/`piece`/`monthly`/`mgr` all Dev@12345 + `dev.listing` + `dev.accountant@test.local` (DB-resident, no fixture — PHASE_03 §2.2) — none of it created by any committed fixture/command |
| Golden monetary outcomes | three settled journeys with owner-verified totals: T-SHIRT **₹801.00** · LOWER **₹344.25** · 3-PATTI **₹633.00** (FACTORY_OPERATIONS_MASTER §8–§12) + the golden **₹225** byte-identical settlement invariant (S-series) — ready-made regression-dataset expected values |
| System rows are migration-owned | Roles + SidebarItemRule baselines seeded by migrations (accounts/0016/0017) — the dataset layers ON TOP of the migration baseline and NEVER duplicates/edits it |
| Single-writer walls | WorkerLedgerEntry → ledger_service · AddaSettlement* → adda_settlement_service · WST/WSC → worker_task_service · *History → history_service · processing_cost → cost_service (manifest never_modify + U8) — seeding money/history/production-truth rows via raw fixtures would bypass every certified invariant |
| DEV-marking conventions in use | `DEV-` / `3-PATTI-` style entity codes · `dev.*@test.local` identities · "DEV-marked" = the owner's own test-data vocabulary (rule 2026-07-04) |
| Known weakness this architecture cures | campaign contracts reference point-in-time PKs (worker pk=25, roll pk=1, rule counts) that drift per DB rebuild — PHASE_02/03 carry re-verify warnings for exactly this reason; stable natural handles remove the class |
| Dev DB fragility | the live dev DB is single-copy (Phase-0 §2.2: capturable only via pg_dump) — a reproducible dataset architecture is the structural fix; it does NOT replace the Phase-0 snapshot decision (DATA-D9) |
| What does NOT exist | no seeder commands, no dataset fixtures, no scenario registry, no reset tooling, no production guard — all Phase-12 implementation surface |

### 2.2 In / out

**In:** census of the existing organic dev data (read-only) · the architecture spec: dataset
philosophy, layers + dependency order, ownership, referential integrity, stable identifiers,
versioning, scenario taxonomy (minimal / full demo / feature / performance / regression /
edge-case), validation assertions, reset semantics, safety rules, phase interfaces · owner
ratification + freeze + handoffs.
**Out:** ANY implementation (Python, management commands, fixtures, JSON/SQL datasets,
scripts, tests, migrations — all Phase 12+) · any DB write (census is read-only) · seeding or
resetting anything · teardown of existing dev worlds (owner-gated separately; 3-PATTI teardown
already awaits owner per Phase-3 record) · changing seed migrations · production/deployment
work · the Phase-0 snapshot decision (noted, not decided here).

## 3. Success criteria

Phase 11 is DONE when ALL hold:
1. `docs/DEV_DATASET_ARCHITECTURE.md` exists, Standard-compliant (frontmatter, T2 canonical,
   `handwritten` class), complete against the §6.2 required-content register — every row
   checked off in evidence.
2. The existing-data census (DSA-A) is complete: every DEV entity family referenced by the
   certifications/contracts/operations-master is inventoried with its natural identifier,
   creating-path (service/UI/shell), and spec disposition (formalized-into-scenario /
   grandfathered / owner-teardown-listed).
3. Every spec rule carries provenance (`[REPO <evidence>]` or `[PROPOSED→DATA-D#]` — the
   PHASE_05 §5 provenance discipline reused); zero unlabeled invention.
4. The **service-path seeding law** (§6.1.3) is stated with its per-table writer map — no
   guarded table may ever be seeded by raw fixture/SQL.
5. The scenario taxonomy is defined with the regression scenarios carrying their embedded
   expected values (₹801.00 / ₹344.25 / ₹633.00 / ₹225 class) and their owner-change-control
   rule.
6. The stable-identifier registry scheme is defined and the reserved-handle seed list drafted
   from the census.
7. Phase-12/13/14/15/deployment interfaces written (§6.6), each as concrete obligations.
8. Owner ratified DATA-D1..DATA-D9 BEFORE spec authoring, and accepted + froze the spec at
   close (design → `frozen-v1`, its own amendment section governing changes).
9. Zero code/DB/dataset changes; battery untouched and NOT re-run; status file + memory
   synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Design-only, tighter than U1:** no code-change branch exists in this phase at all
  (PHASE_00/05 wording). The census is read-only (Django shell SELECTs / doc reads); zero
  writes to any DB.
- **Formalize, don't fictionalize:** the spec describes the dataset the FACTORY needs
  (Factory-Driven Development: real problems, real flows) — scenario content derives from the
  certified journeys and probe needs already on record, not from imagined demo scenery.
- **Migration-baseline respect:** anything a migration seeds (Roles, sidebar rules) is OUT of
  dataset scope forever — the spec depends on it, never re-creates it.
- **No new future-phase dependency without documentation** (owner rule 2026-07-04 verbatim):
  every scenario a later phase will rely on is named in the spec, or it may not be relied on.
- Existing dev worlds are sacred during this phase: censused, never mutated; their teardown
  remains the separately owner-gated item it already is.
- Unknowables (e.g. exact volume targets for performance datasets) = Design Record items,
  never guessed.

## 5. Evidence standard

- Census: per-family tables (entity family · natural ids in use · creating path · referenced
  by which certification/contract/doc · disposition), with the read-only queries/commands
  quoted; counts reconciled against the source documents' own numbers.
- Spec completeness: the §6.2 register reproduced with every row → satisfying spec section.
- Provenance census: counts of `[REPO]` vs `[PROPOSED]` rules; every `[PROPOSED]` mapped to
  its DATA-D item.
- Golden values: quoted from FACTORY_OPERATIONS_MASTER with section anchors (never from
  memory).
- Sub-agent census sweeps supplemental (U7); dispositions, the seeding-law writer map, and
  the freeze = main-thread.

## 6. Methodology — the architecture this phase materializes

§6.1 defines binding defaults (the PHASE_05 pattern): DSA-B transcribes them into the spec as
amended by the DSA-0 Design Record.

### 6.1 The architecture

#### 6.1.1 Philosophy `[REPO + PROPOSED]`

Development-only (a production guard is a hard precondition of every future seeder run —
§6.1.9) · deterministic (same spec version + same scenario ⇒ the same world: identical natural
identifiers, counts, relationships, and monetary outcomes; auto-PKs explicitly NOT part of the
contract — nothing may reference them) · reproducible from zero (empty DB + migrations +
seed = the world; kills the single-copy-dev-DB fragility class) · resettable (§6.1.8) ·
idempotent (re-running a seed converges by natural-key upsert; zero duplicates) ·
production-safe (§6.1.9) · never mixes with production data (DEV-marking invariants §6.1.4;
disjoint identifier namespaces; the guard refuses non-dev environments).

#### 6.1.2 Layers + dependency order `[REPO structure; order PROPOSED→DATA-D2]`

Seeding order = dependency order; each layer names its owning app + creating services:
1. migration baseline (PRE-EXISTING: roles, sidebar rules — consumed, never created) →
2. authentication users + permissions (the cast; extra_roles compositions per PHASE_03 D1) →
3. core master data (cloth types/colors/storage; stage library, categories, machine types) →
4. products + flows (products, patterns, workflow stages incl. tracking modes, rates) →
5. machines →
6. raw materials (rolls incl. financial fields via the FINANCIAL_ROLES path) →
7. workers' production truth (Addas, assignments, contributions, allocations — via
   worker_task_service/pool_service chokepoints) →
8. expenses + money (advances, settlements, FnF cases, factory expenses — via their
   single-writer services; LEDGER rows only ever as service outcomes) →
9. storefront (categories, featured products) →
10. AI pattern data (patterns_ai: markers, usage, calibration — via its services) →
11. reporting/historical examples (exports, history — as SERVICE OUTCOMES of the above, never
    direct rows: history tables are single-writer, U13).

#### 6.1.3 Data ownership + the service-path seeding law `[REPO — U8/rule 4; normative]`

**Every seeded row is created through the SAME write path production uses:** the owning
service for any table with a service owner; plain ORM only where no service exists (pure
masters). Raw fixtures/SQL/loaddata are FORBIDDEN for guarded tables (ledger, settlements,
WST/WSC, allocations, *History, processing_cost) — a dataset that bypasses the chokepoints
seeds worlds the invariants never blessed, and every certification proof over such a world is
void. Consequence: the seeder (Phase 12) is an ORCHESTRATOR of services, not a data loader.
The spec carries the full table→writer map (from the manifest never_modify + chokepoint pages).

#### 6.1.4 Stable identifiers + DEV-marking `[REPO conventions; scheme PROPOSED→DATA-D4]`

Every seeded entity carries a stable natural identifier in the existing house style
(`DEV-`-prefixed codes, `3-PATTI-NNN`-style world codes, `dev.<role>@test.local` identities,
Dev@12345 cast password) — the spec defines per-family schemes + a **reserved-handle
registry** (seeded from the census) so scenarios, contracts, and probes reference handles,
never PKs. DEV-marking is an invariant, not a convention: every dataset-created row is
identifiable as dataset-born by its identifier alone (mixing-detection = a validation check).

#### 6.1.5 Referential integrity `[REPO — DB constraints + service invariants]`

Integrity is inherited, not asserted: because seeding drives services (§6.1.3), the 26+
CheckConstraints and service invariants hold by construction. The spec adds dataset-level
rules: no dangling handle references between scenario layers; cross-scenario isolation
(feature scenarios never reference another scenario's handles unless declared as a
composition); teardown obeys soft-state-over-delete inside a live world (full reset = DB
rebuild, §6.1.8).

#### 6.1.6 Scenario taxonomy `[REPO journeys + PROPOSED→DATA-D5]`

- **minimal** — smoke world: 1 product + 1 flow + minimal cast + 1 roll + 1 Adda; fastest
  seed; the default for quick dev.
- **full demo (`seed_demo`/`seed_factory` class)** — the factory: T-SHIRT + LOWER + 3-PATTI
  worlds with flows, cast, machines, rolls, and at least one settled journey each.
- **feature-specific (`seed_feature <x>`)** — per-feature slices (allocation, settlement,
  FnF, machines, patterns_ai, storefront, tracking-exports…), each self-contained + named in
  the registry.
- **performance** — volume-scaled variants (row-count targets = DATA-D6 owner input; never
  guessed).
- **regression** — the golden journeys WITH embedded expected values (₹801.00 / ₹344.25 /
  ₹633.00 settled totals; ₹225 settlement invariant): seed → run the flow → totals must match
  byte-for-byte. Expected values encode business truth: they change ONLY by owner approval
  (DATA-D6).
- **edge-case** — the certified hard cases as reproducible worlds: over-allocation (a REAL
  M-6 block — PHASE_02 OWN-C needs one) · damaged/restored rolls · monthly worker (pk-25
  class, by handle) · inactive users · reopen-guard chains · composite-role identities
  (PHASE_03 D1) · rate-correction cases.

#### 6.1.7 Dataset validation `[PROPOSED→DATA-D5/D6; Phase-13 input]`

Per scenario, the spec defines post-seed assertions: row counts per layer · handle-registry
completeness · DEV-marking invariant (zero unmarked rows created) · referential spot-checks ·
golden-value assertions for regression scenarios · flags-state assertion (enforcement flags
untouched — U10). These assertion definitions ARE the Phase-13 `verify_*` input spec.

#### 6.1.8 Reset philosophy `[PROPOSED→DATA-D7; data-principles-compatible]`

Two distinct operations, never conflated: **full reset** (`reset_demo` class) = rebuild the
dev DATABASE (drop/recreate → migrate → seed) — legitimate because it replaces the whole
world, not history within one; **in-world teardown** = only via the app's designed reverse
paths (void/archive/reverse) — append-only history is never raw-deleted inside a living world
(U13 even in dev). Resets never touch: the production DB (guard), media files unless
scenario-declared, the migration baseline.

#### 6.1.9 Safety rules `[PROPOSED→DATA-D8]`

The production guard (Phase-12 implements; spec defines): seeder/reset commands refuse unless
(a) the settings module is the dev one, (b) DEBUG or an equivalent dev marker holds, (c) the
database name matches a dev allowlist, (d) an explicit `--yes-i-know` style confirmation for
destructive resets. Plus: seeders never appear in any deployment runbook path (Phase-19
exclusion); dataset artifacts never ship in a production image; the DEV identifier namespace
is reserved (production data may never legitimately carry it — gives Phase 13 a
cross-contamination check).

### 6.2 Required-content register for the spec

philosophy (§6.1.1) · layers+order (§6.1.2) · ownership + service-path law + writer map
(§6.1.3) · identifiers + registry + DEV-marking (§6.1.4) · referential integrity (§6.1.5) ·
scenario taxonomy with all six classes + composition rules (§6.1.6) · validation assertions
per scenario (§6.1.7) · reset semantics (§6.1.8) · safety rules (§6.1.9) · versioning +
change control (DATA-D6) · the census-derived reserved-handle seed list · phase interfaces
(§6.6) · its own metadata block + amendment section.

### 6.6 Phase interfaces

| Phase | Interface |
|---|---|
| 12 Seeder Engine | Implements the spec EXACTLY: the four command classes, the guard, natural-key idempotency, service-path orchestration; commands = code ⇒ Phase 12 is battery-bearing with tests + pins per its own contract; spec gaps found there = dated Phase-11 amendments, never silent divergence |
| 13 Verification Engine | Consumes §6.1.7 assertion definitions as the `verify_*` spec; regression golden values = its pass/fail truth; `verify_production` additionally uses the DEV-namespace reservation as a contamination check (read-only in prod) |
| 14 Knowledge Sync | May check spec⇄seeder drift (declared scenarios vs implemented commands) — detect-and-notify; scenario registry is sync-readable (structured section) |
| 15 Business Dashboard | Demos + acceptance run on the full-demo scenario; BOD feature work may request new scenarios ONLY via dated spec amendments (owner rule: no undocumented future-phase dependency) |
| Deployment (19–21) | Seeders excluded from every production path (runbook states it); Phase-0 note: a reproducible dataset REDUCES dev-DB preciousness but does NOT replace the snapshot decision (DATA-D9) — the organic dev DB remains evidence until the owner rules otherwise |

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence appended to this contract; battery
NEVER runs (no code is touchable, §10).

| # | Scope · Inputs · Outputs · Evidence · Stop deltas |
|---|---|
| **DSA-0** — Charter + gate + ratification | Gate: Phase 10 closed (locked master order — no technical dependency claimed, the order is the owner's). Owner ratifies DATA-D1..DATA-D9. Verify census sources (FACTORY_OPERATIONS_MASTER §8–12, certification cast lists, PHASE_02/03 probe-target tables, manifest never_modify). **Stop:** gate fails; any DATA-D unanswered. |
| **DSA-A** — Existing-DEV-data census (read-only) | Inventory every DEV entity family per §5: worlds, cast, masters, flows, rolls, machines, money artifacts, patterns_ai objects; natural ids + creating paths + which records reference them; draft the reserved-handle registry; list pk-referenced probe targets whose contracts deserve handle-based amendments (report only). Read-only shell queries permitted; ZERO writes. **Stop:** census contradicts a certification record (conflict rule); any write temptation. |
| **DSA-B** — Author the spec | Write `docs/DEV_DATASET_ARCHITECTURE.md` = §6.1 as amended by the Design Record + the census registry; provenance labels throughout; §6.2 register check + link proofs; spec status `draft`. **Stop:** a spec need contradicts a ratified DATA-D answer or an owner standing rule (dated amendment → owner). |
| **DSA-C** — Owner acceptance + freeze + handoff | Owner reads the spec; corrections applied (dated); status → `frozen-v1`; DOCUMENTATION_INDEX + START_HERE routing rows; §6.6 handoffs finalized (incl. the Phase-12 implementation checklist derived from the spec); PHASE-11 VERDICT. **Stop:** owner absent (spec stays `draft`, normal stop). |

## 8. Deliverables

- **`docs/DEV_DATASET_ARCHITECTURE.md`** — the frozen spec (T2 canonical, `handwritten`,
  Standard-compliant), incl. the table→writer map, scenario registry, reserved-handle
  registry, assertion definitions, and the Phase-12 implementation checklist.
- The existing-data census (evidence section of this contract).
- Filled Design Record (DATA-D1..DATA-D9).
- Updated status file, DOCUMENTATION_INDEX, memory per sub-phase.

## 9. Files expected to change

**Docs only:** `docs/DEV_DATASET_ARCHITECTURE.md` (NEW at DSA-B — the phase's only new file) ·
`docs/DOCUMENTATION_INDEX.md` + `docs/START_HERE.md` (routing rows, DSA-C) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · this file (Design Record + evidence appendices) ·
memory files. **Scratchpad:** census query outputs. Nothing else.

## 10. Files that must never change (touching one = STOP + report)

- ANY application file: code, tests, migrations, templates, settings, fixtures, media, `.env`.
- ANY database row (dev or otherwise — the census is SELECT-only; no seeding, no teardown,
  no "tidying" of dev worlds).
- Seed migrations (accounts/0016/0017 class) — the baseline the spec depends on.
- `canonical_manifest.json` · `docs/DOC_STANDARDS.md` · knowledge-graph artifacts · T1
  truth-locks · closed phase logs (dated amendments per their own rules).
- The existing dev worlds' owner-gated teardown status (3-PATTI-013/014/015 stay pending the
  owner's separate decision).
- `.claude/` tooling · the 2 stashes · `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) evidence section appended to THIS contract
(closed sections append-only, corrections dated); (b) status-file Phase-11 row + dashboard
(battery row untouched — no code) + "Next action"; (c) DOCUMENTATION_INDEX: spec row at
DSA-B (status `draft`) updated to `frozen-v1` at DSA-C; (d) U6 app-doc lookups N/A throughout
(no code changes — stated once).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-11
bullet: sub-phase closed, census headline counts, spec status) + MEMORY.md index line at each
sub-phase close. Agents without memory: skip — this contract + the spec are the complete
binding record; the reserved-handle registry lives in the spec, never only in memory.

## 13. Battery policy

**Never runs in this phase.** No code change is possible under §10; nothing to test. Baseline
(status-dashboard value; 1526/1526 at authoring) untouched and NOT re-verified here. The
battery enters this workstream at Phase 12 (commands + tests + pins per its own contract).

## 14. Regression policy

- The only regressions possible: contradicting an existing record (guarded by the census
  conflict rule + provenance discipline) and dev-world mutation (guarded by §10 SELECT-only).
- Certified journeys/values are quoted from their docs of record, never recomputed here.
- No pins, no tests (U4 vacuously satisfied).

## 15. Rollback policy

- DSA-B aborts cleanly: delete the draft spec (its own creation, only while `draft`), revert
  index rows. Nothing else was touched by construction.
- Design Record + evidence sections are append-only (dated amendments).
- Session crash: next session re-reads this contract's evidence state; the census is
  re-runnable read-only (idempotent by nature).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. DSA-0 gate fails or any DATA-D1..D9 unanswered at DSA-B start.
3. Census–record contradiction (a dev entity's state contradicts a certification/operations
   record — framework conflict rule; report, never reconcile unilaterally).
4. Any write to any database or any §10 file would occur (incl. "harmless" dev-world tidying).
5. A spec requirement would demand changing a seed migration, a service, or a flag — that is
   implementation-phase (12+) or owner territory; record as interface obligation, stop if
   pressed.
6. Scenario content cannot be derived from the record (a needed expected-value or volume
   target is nowhere on disk) — Design Record item / owner input, never invented.
7. The spec would create an undocumented future-phase dependency (owner rule 2026-07-04).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-11 row: which DSA-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → this contract FULLY
   (incl. evidence sections + Design Record state) → `docs/DOC_STANDARDS.md` (spec compliance
   target) → `docs/DEV_DATASET_ARCHITECTURE.md` if it exists (status: `draft` ⇒ next =
   finish DSA-B or DSA-C per evidence; `frozen-v1` ⇒ phase done).
3. Census sources: FACTORY_OPERATIONS_MASTER §8–§12 · WORKER/MANAGEMENT/OWNER certification
   cast lists · PHASE_02/PHASE_03 probe-target tables · canonical_manifest never_modify ·
   CHOKEPOINTS pages.
4. Verify read-only: git HEAD vs status file; spec presence/status; no dev-world teardown
   happened meanwhile (world codes still resolve — drift → note + owner).
5. Read-only `manage.py shell` for census queries only (framework env facts for venv path);
   no logins, no writes, no battery environment needed.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / this contract / the spec / source records →
   report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (DSA-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| DATA-D1 | Spec artifact | `docs/DEV_DATASET_ARCHITECTURE.md`, T2 canonical, `handwritten` class, Standard frontmatter, own amendment section; no parallel doc | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D2 | Layers + seeding order | The 11-step dependency order of §6.1.2 (migration baseline consumed, never created) | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D3 | Service-path seeding law | ALL writes via the owning service where one exists; plain ORM only for tables with no service owner; raw fixtures/SQL/loaddata FORBIDDEN for guarded tables — the seeder is an orchestrator, not a loader | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D4 | Identifier scheme + registry | House-style natural keys (`DEV-`/world-code/`dev.*@test.local`/Dev@12345 cast) per family + a reserved-handle registry in the spec; contracts/probes reference handles, never PKs (existing pk-references flagged for future amendment, not rewritten now) | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D5 | Scenario taxonomy | The six classes of §6.1.6 incl. regression scenarios embedding the golden values (₹801.00 / ₹344.25 / ₹633.00 / ₹225) and edge-case worlds from the certified hard cases | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D6 | Versioning + change control | Spec semver; scenario changes = dated spec amendments; regression expected values change ONLY by owner approval (they encode business truth); performance-scenario volume targets = owner-supplied here or deferred | **ACCEPT + owner verbatim: "Defer the performance dataset volume targets. … Do not invent any target sizes."** → volume targets = DEFERRED (spec will carry the performance-scenario class with targets marked owner-deferred; supplying them later = a dated spec amendment) |
| DATA-D7 | Reset semantics | Full reset = DB rebuild (drop→migrate→seed); in-world teardown = designed reverse paths only (append-only respected even in dev); the two never conflated | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D8 | Production-safety guard | Settings-module + dev-marker + DB-name allowlist + explicit destructive-confirmation, all four required; seeders excluded from all deployment paths; DEV namespace reserved (contamination check for Phase 13) | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |
| DATA-D9 | Existing dev DB + Phase-0 relation | The organic dev DB is GRANDFATHERED evidence (censused, formalized where scenarios adopt it, never silently replaced); its pg_dump/snapshot question remains the open Phase-0 owner decision; 3-PATTI-013/014/015 teardown stays its own owner gate | **ACCEPT** (owner 2026-07-17, verbatim \"I accept the defaults for DATA-D1 through DATA-D9\"; no override) |

Date · answered by: **2026-07-17 · owner, verbatim — all nine defaults ratified; D6 performance volume targets DEFERRED by owner order (no sizes invented). DSA-0 CLOSED; DSA-A authorized same order.**

## Dated amendments

- **A1 (2026-07-17, C-DSA-1 disposition — owner-approved verbatim; corrects §2.1 "An organic
  dev dataset EXISTS" row, §2.2/§10 pending-teardown clauses, and the DATA-D9 teardown
  clause):** **FACTORY_OPERATIONS_MASTER §12 is adopted as the authoritative world truth for
  the Phase-11 specification.** Of record: (1) **3-PATTI-011/013/014/015 were already torn
  down as part of the owner-approved real-flow transition** (FOM §12, 2026-07-06 — before
  this contract's authoring); (2) **3-PATTI-016 is the canonical settled real-flow world**
  corresponding to the **₹633.00** regression journey (DB: `ADST-0006` finalized ₹633.00 —
  DSA-A census); (3) the previous pending-teardown wording in the authoring-time contract is
  a **historical authoring artifact only, superseded by this dated amendment** — no history
  rewritten, no certification record modified, no implementation or database touched. The
  DSA-B spec carries the true world list (3-PATTI worlds on disk: 009/010/012/016).

# Evidence sections (DSA-0, DSA-A, DSA-B, DSA-C — appended at close)

## DSA-0 — Charter + gate + ratification — EXECUTED 2026-07-16 · ⏸ AWAITING OWNER DATA-D1..DATA-D9

**Owner order honored:** "Begin with DSA-0 only… Do not assume owner decisions." — no
ratification language for DATA-D1..D9 in the order → FIX-0 precedent, no answer fabricated;
Decision half stays pending; **the next owner gate = this decision pack.** Zero census work
(DSA-A's job), zero DB reads/writes, zero code; battery never runs this phase (dashboard
baseline 1530/1530 stands untouched).

### 1. Gate (contract §7 DSA-0 row) — PASS

| Check | Result |
|---|---|
| Phase 10 closed | ✓ — [UI_COMPONENT_LIBRARY_LOG.md](../UI_COMPONENT_LIBRARY_LOG.md) §UIL-F "🏁 PHASE 10 VERDICT: LIBRARY-CERTIFIED-WITH-REGISTERED-RESIDUALS — PHASE COMPLETE"; owner acceptance verbatim 2026-07-16 ("Phase 10 is accepted.") |
| Census sources present | ✓ ALL: FACTORY_OPERATIONS_MASTER (§8 config receipt · §9 LOWER **₹344.25**/ADST-0004 · §10 T-SHIRT **₹801.00** · §12 3-PATTI real-flow — golden-value anchors verified on disk, not from memory) · WORKER/MANAGEMENT/OWNER/OFFICE certification docs (cast lists) · PHASE_02/PHASE_03 contracts (probe-target tables) · canonical_manifest `never_modify` (5 entries = the single-writer wall for the §6.1.3 writer map) · CHOKEPOINTS 7 pages |
| Spec absent pre-session | ✓ — `docs/DEV_DATASET_ARCHITECTURE.md` does not exist (created only at DSA-B) |
| git state | HEAD `49404001` · 0 staged · 2 stashes ✓ |
| Battery | never runs (design phase, §13); baseline 1530/1530 stands |

### 2. Standing-context notes recorded at charter

- **KOS-compat (record-only, owner permanent guidance 2026-07-16 — no scope change):** two
  spec artifacts this phase designs are natural future knowledge-graph inputs — the
  **scenario registry** (§6.1.6, sync-readable structured section per the §6.6 P14 row) and
  the **reserved-handle registry** (§6.1.4). Both = additive-minor graph-kind CANDIDATES
  (dataset knowledge) for a future KG Design-Record amendment; recorded here as observations,
  nothing built, no new registers created.
- Post-Phase-9 snapshot refresh (Phase-0 D4 cadence) remains DUE — owner action, not a gate.
- 3-PATTI-013/014/015 teardown stays its own owner gate (§10) — untouched by this phase.

### 3. ⏸ Decision pack — DATA-D1..DATA-D9 (defaults binding unless overridden; Appendix A)

The nine defaults are quoted verbatim in Appendix A. Summary for ruling:

| # | Decision | Default in one line |
|---|---|---|
| DATA-D1 | Spec artifact | `docs/DEV_DATASET_ARCHITECTURE.md`, T2 canonical, handwritten, own amendment section — no parallel doc |
| DATA-D2 | Layers + order | The 11-step dependency order (§6.1.2); migration baseline consumed, never created |
| DATA-D3 | Service-path law | All writes via owning services; plain ORM only where no owner; fixtures/SQL/loaddata FORBIDDEN for guarded tables — seeder = orchestrator |
| DATA-D4 | Identifiers | House-style natural handles per family + reserved-handle registry; handles-never-PKs; existing pk-references flagged, not rewritten |
| DATA-D5 | Scenarios | Six classes (§6.1.6) incl. regression scenarios embedding ₹801.00/₹344.25/₹633.00/₹225 + certified edge-case worlds |
| DATA-D6 | Versioning | Spec semver; scenario changes = dated amendments; golden values change ONLY by owner approval; performance volume targets = owner-supplied or deferred |
| DATA-D7 | Reset semantics | Full reset = DB rebuild; in-world teardown = designed reverse paths only; never conflated |
| DATA-D8 | Production guard | Four factors ALL required (settings + dev-marker + DB-name allowlist + explicit confirmation); seeders excluded from deployment paths; DEV namespace reserved |
| DATA-D9 | Existing dev DB | GRANDFATHERED evidence; pg_dump/snapshot question stays Phase-0's; 3-PATTI teardown stays its own gate |

**Recommendation: accept all nine.** They transcribe the certified reality (single-writer
walls, house identifier style, golden journeys, append-only principles) — the only invented
parts are the registry/guard shapes, each marked `[PROPOSED→DATA-D#]` for exactly this
ruling. One open input inside D6: performance-scenario volume targets (owner-supplied now or
explicitly deferred — deferral is the default's built-in option and blocks nothing).

### 4. Scope discipline

Files touched this sub-phase: this contract (evidence section) · status file · memory.
Zero census/DB/code work; zero new files. **Next: owner answers DATA-D1..DATA-D9 →
DSA-A existing-DEV-data census (read-only, owner-gated).**

### 5. DSA-0 CLOSURE — owner rulings 2026-07-17 (verbatim)

> "I accept the defaults for DATA-D1 through DATA-D9. For DATA-D6: Defer the performance
> dataset volume targets. Record the deferment exactly as allowed by the contract. Do not
> invent any target sizes."

All nine RATIFIED (Appendix A filled; D6 deferment recorded in its row). **DSA-0 CLOSED
2026-07-17.** DSA-A authorized by the same order.

## DSA-A — Existing-DEV-data census (read-only) — DONE 2026-07-17 · ⏸ 1 CLASSIFIED FINDING (C-DSA-1)

**Method:** read-only Django ORM SELECTs (`config.settings.local`; queries + raw output
archived in scratchpad `dsa_a_census.txt`); zero writes of any kind; source-document numbers
quoted for reconciliation. Battery never (design phase).

### 1. Headline reconciliation vs certified numbers — EXACT across the board

| Census fact | Measured | Certified source | Match |
|---|---|---|---|
| Users total/active | 48 / 46 | OFF-0 census 48 | ✅ |
| Roles (all system, 0-perm) | 5 (`accountant/listing_team/manager/super_admin/worker`) | OWN-D | ✅ |
| SidebarItemRule (accounts app) | 21 | OWN-D 21-rule grid | ✅ |
| Skills / UserTypes | 10 / 5 | OWN-F | ✅ |
| Cloth masters (type/color/storage) | 6 / 15 / 3 | OWN-E | ✅ |
| Cloth rolls | 32 (`roll_id` = `CR-000001…` + `GLDN-R1..R6` class) | OWN-E 32 | ✅ |
| Machines / assignments | 4 (`OL-001/FL-001/SN-001/EL-001`) / 5 (2 open) | OWN-F re-based 4 · 5/2-open | ✅ |
| **Ledger** | **170 rows · Σ ₹10,880.25** | MGT-C/OWN-C baseline 170/₹10880.25 | ✅ EXACT |
| **Golden settlements IN DB** | `ADST-0004` **₹344.25** finalized · `ADST-0005` **₹801.00** finalized · `ADST-0006` **₹633.00** finalized | FOM §9/§10/§12 anchors | ✅ byte-exact |
| Settlement lifecycle artifacts | 8 AddaSettlements + 43 items; supersession chains `0007→0008` (₹1,254.75) · `0009→0010` (₹1,279.25); `ADST-0001` ₹1,500 finalized | reverse/re-settle receipts + MGT-C target | ✅ |
| Storefront | 1 Category + 1 FeaturedProduct ("3 Patti", pk=1 rows) | MGT-F/OWN-F | ✅ |
| Markers | `MRK-000001..3` (MRK-000002 = the cert target) | MGT-G/OWN-G | ✅ |
| Export batches | 6 (`tracking.BarcodeExportBatch`; latest = the MGT-D artifact EXP-2026-006; OWN-D's 7th was rollback-scoped) | MGT-D/OWN-D | ✅ explained |
| Production truth volumes | WST 150 · WSC 153 · WSA 84 · SPS 88 · APSCPB 53 · SWA 141 · AddaStageRecord 132 · WorkflowStage 73 | magnitude-consistent with journeys; no cert states exact totals | ✅ (no conflict) |
| Empty-by-design | PayrollSettlement 0 (pre-V2 legacy) · WorkerAdvance 0 (loan pool clear) · SettlementReconciliationEvidence 0 | V2 design + rollback-wrapped probes | ✅ |

### 2. Per-family census (entity · natural ids · creating path · referenced-by · disposition)

| Family | Natural ids in use | Creating path | Referenced by | Disposition |
|---|---|---|---|---|
| Cast (33 `dev.*@test.local`) | `dev.ow.a-d` 46-51 · `dev.sw.a-b` 49-50 · `dev.mgr` 52 · `dev.piece` 53 · `dev.monthly` **25** · `dev.monthly2` 43 · `dev.leaver` 42 · `dev.helper` 44 · `dev.hlp.nkb` 66 · `dev.accountant` **61** · `dev.listing` **62** · `dev.acct.mgr` **76** · `dev.aud.*` ×6 (67-72) · `dev.cm.a-c` 63-65 · skill-cast (`dev.el/flat/sn/chk/iron/fin.*`) 54-60 · `dev.manager` 26 | accounts UI + shell (PHASE_03 D2/D3 documented) | all four certifications + FOM | **FORMALIZE** (the canonical cast layer-2) |
| Legacy/junk identities | `worker@test.com` 10 · `worker2/3@test.local` 3/4 · `test_worker` 9 · `testuser` 13 · `verify-*` 6/7 · `nexttest` 11 · `w1@test` 22 · `manager1` 5 · `mgmt1/2@test` 20/21 · `utest` 2 (cutting master, cert-referenced) · owner pk=1 | organic (pre-campaign) | mgmt1 = MGT-G Manager-B; utest = browser-test cred; rest unreferenced | owner+utest+mgmt1 **FORMALIZE**; rest **GRANDFATHERED** (cleanup-candidate flag, owner decision — NOT torn down here) |
| Worlds (Addas, 18) | golden: `T-SHIRT-001` · `LOWER-001/002` · `3-PATTI-016` (settled ₹633) · historical: `3-PATTI-009` (ADST-0001) `/010/012` · DEV: `DEV-NICKAR-A1/001/002` · `DEV-P8B-A1` · post-freeze: `NKB-001` `NKS-001` `SHT-001` | production UI (Phase-3 config real flows) + services | FOM §8-§12 · certs | golden+DEV-NICKAR **FORMALIZE** (regression + feature scenarios) · historical **GRANDFATHERED** |
| Products (18) | `T-SHIRT` `LOWER` `3-PATTI` `NIKKAR` `PAJAMA` `1-6` · `DEV-TEE/HUB/P3A/P3B/P8B/NICKAR` · `NKB` `NKS` (24='NKB' = the "DEV Nickar Big" pk-24 cert mention) | production UI + flow editor | FOM 100-product verdict (READY 18) · MGT-G/OWN-G | real trio + DEV-NICKAR **FORMALIZE**; rest **GRANDFATHERED** |
| Stage library | 23 stages (`layering/cutting/cutting_pattern/…`) · 5 categories · 5 machine types · 73 WorkflowStage rows (per-product flows: T-SHIRT 16-op, LOWER 13-op per FOM) | production UI (stage library + flow editor) | FOM · OWN-A/B | **FORMALIZE** (layer-3/4) |
| Rolls (32) | `CR-000001..` + `GLDN-R1..R6` + NKS-class (`roll_id` natural key) | bulk-add UI/service (financial fields via FINANCIAL_ROLES path) | OWN-E (roll pk=1=CR-000001) · GLDN-R6=roll-37 (OWN-D) | golden/GLDN **FORMALIZE**; consumed historical **GRANDFATHERED** |
| Machines | `OL-001` `FL-001` `SN-001` `EL-001` + 5 assignments (2 open) | machines UI (R10-A) | MGT-F/OWN-F (el-001 iexact case) | **FORMALIZE** (layer-5) |
| Money artifacts | `ADST-0001..0010` (refs above) · ledger 170/₹10,880.25 · FactoryExpense 4 · WorkerAdvance 0 | single-writer services ONLY (adda_settlement_service · ledger_service) — zero fixture rows exist | FOM · MGT-C · OWN-C | golden three + ADST-0001 **FORMALIZE as regression expected-values**; chains 0007-0010 **GRANDFATHERED** (reverse-path receipts) |
| patterns_ai (21 models) | `MRK-000001..3` · PatternPiece 58 (incl. OWN-G "DEV OWNG Piece") · CalibrationMat 2 · ApprovedLayout 5 · CaptureAsset 20 · GeneratedMarkerCandidate 28 · PieceSizeGeometry 115 … | patterns_ai services/UI (register_pattern_definition etc.) | MGT-G/OWN-G · DEV-NICKAR pipeline | DEV-NICKAR chain **FORMALIZE** (feature scenario); volumes **GRANDFATHERED** |
| Storefront | Category "3 Patti" pk=1 · FeaturedProduct "3 Patti" pk=1 | listing UI (image_service) | MGT-F/OWN-F/OFF-B | **FORMALIZE** (layer-9 minimal) |
| Exports | 6 BarcodeExportBatch (EXP-2026-006 = MGT-D artifact) | export UI (service outcome) | MGT-D/OWN-D | **GRANDFATHERED** (history = service outcomes, layer-11 class) |

### 3. Reserved-handle registry — DRAFT (the DATA-D4 seed list; spec-resident at DSA-B)

Identities: the 33 `dev.*@test.local` + `umesh29mar@gmail.com` (owner) + `utest@gmail.com` +
`mgmt1@test` · cast password `Dev@12345` (owner-authorized DEV cred). Worlds:
`T-SHIRT-001 · LOWER-001 · LOWER-002 · 3-PATTI-016 · 3-PATTI-009 · DEV-NICKAR-A1/001/002`.
Products: `T-SHIRT · LOWER · 3-PATTI · DEV-NICKAR · NKB · NKS`. Rolls: `CR-000001 ·
GLDN-R1..R6`. Machines: `OL-001 · FL-001 · SN-001 · EL-001`. Money: `ADST-0001 · ADST-0004
(₹344.25) · ADST-0005 (₹801.00) · ADST-0006 (₹633.00)` + the ₹225 S-series invariant.
Patterns: `MRK-000001..3`. Stage-library codes (`layering` etc.) = migration-adjacent master
handles.

### 4. pk-referenced probe targets deserving future handle-based amendments (REPORT ONLY — nothing rewritten)

worker pk=25 → `dev.monthly@test.local` · pk=61/62/76 → `dev.accountant`/`dev.listing`/
`dev.acct.mgr` · roll pk=1 → `CR-000001` · roll-37 → `GLDN-R6` · product pk=23/24 →
`DEV-NICKAR`/`NKB` · sr=161/162 (XFB-class stage records — per-rebuild volatile, need
world+stage handles) · "rule counts 21/23" → rule-set version handle. Carrying contracts:
PHASE_02/PHASE_03 (already carry re-verify warnings) + certification docs. Disposition =
future dated amendments at those docs' own gates; the spec's registry makes it possible.

### 5. ⏸ C-DSA-1 — CLASSIFIED census-vs-record discrepancy (owner disposition required before DSA-B)

**Finding:** this contract's authoring-time facts (§2.1 "dev worlds 3-PATTI-011/013/014/015"
· §10 "3-PATTI-013/014/015 stay pending the owner's separate decision" · DATA-D9's teardown
clause) assume those four worlds still exist. **The DB contains NONE of them** (3-PATTI set
present: 009/010/012/016). The DB AGREES with the certified operations record:
FACTORY_OPERATIONS_MASTER §12 — "3-PATTI REAL-FLOW JOURNEY RECEIPT (2026-07-06 — teardown →
real flow → settled)" — the teardown already happened, owner-driven, before this contract was
authored (2026-07-12); `3-PATTI-016` is the settled real-flow world (₹633.00 = ADST-0006 ✓).
**Classification: stale authoring-time fact in the frozen contract — NOT a data-integrity
violation, no certification proof invalidated** (FOM §12 + DB are mutually consistent).
Per §16.3 reported, never reconciled unilaterally. **Proposed disposition (owner's):** dated
Appendix-A amendment acknowledging FOM §12 as the world truth (011/013/014/015 =
already-torn-down 2026-07-06; the DATA-D9 teardown clause is MOOT — no pending teardown
exists); DSA-B spec then carries the true world list. Blocks nothing else in the census.

### 6. Scope discipline

Read-only throughout (ORM SELECTs only; zero DB writes; zero dev-world mutation). Files
touched: this contract (Appendix A D-answers + this section) · status · memory. Battery
never (1530/1530 stands). git HEAD `49404001` · 0 staged · 2 stashes.

**Next: owner disposes C-DSA-1 → DSA-B spec authoring (owner-gated).**

### 7. DSA-A CLOSURE — C-DSA-1 owner disposition 2026-07-17 (verbatim)

> "C-DSA-1 disposition approved. I agree with your classification. Record it as a dated
> Appendix-A amendment only. Adopt FACTORY_OPERATIONS_MASTER §12 as the authoritative world
> truth… Do not rewrite history. Do not modify any certification records."

→ **Amendment A1 recorded** (Appendix A). DSA-A CLOSED; DSA-B authorized same order.

## DSA-B — Author the spec — DONE 2026-07-17 · spec `draft`, ⏸ AWAITING OWNER REVIEW

**Deliverable:** [docs/DEV_DATASET_ARCHITECTURE.md](../DEV_DATASET_ARCHITECTURE.md) —
**v0.1.0, status `draft`** (T2 topic-canonical, `handwritten`, 7-field frontmatter, own
amendment section §12). 203 lines; design-only (zero code/fixtures/commands/DB writes).

### 1. §6.2 required-content register check — 13/13

| Register row | Spec section |
|---|---|
| philosophy | §1 |
| layers + order (11-step, D2) | §2 (census anchors per layer) |
| ownership + service-path law + writer map | §3 (14-row writer map: manifest never_modify 5 verbatim + CLAUDE.md/chokepoint/cert-grounded rows) |
| identifiers + registry + DEV-marking | §4 |
| referential integrity | §5 |
| scenario taxonomy (all six classes + composition rule) | §7 (performance targets marked OWNER-DEFERRED per D6 ruling) |
| validation assertions per scenario | §7 assertions column (= the Phase-13 input) |
| reset semantics | §8 |
| safety rules (4-factor guard) | §6 |
| versioning + change control | §10 (semver v0.1.0; golden values owner-approval-only) |
| census-derived reserved-handle seed list | §11 (registry v1 + no-collision law) |
| phase interfaces | §9 (12/13/14/15/deploy — concrete obligations) |
| metadata block + amendment section | frontmatter + §12 (+ §13 draft Phase-12 checklist, finalized at DSA-C) |

### 2. Proofs

Links 2/2 resolve · provenance labels: **40 `[REPO]` + 12 ratified-design (`[PROPOSED→DATA-D#]`/D-ratified)** — zero unlabeled invention · golden anchors ₹801.00/₹344.25/₹633.00/₹225 present, quoted with FOM section anchors (§9/§10/§12) + DB references (ADST-0004/5/6, DSA-A) · frontmatter line-1 ✓ · **A1 world truth carried** (§7 regression row + §11: `3-PATTI-016` = canonical settled world; no torn-down world referenced anywhere in the spec).

### 3. Scope discipline

Files: the spec (NEW — the phase's only new file, per §9) · this contract (A1 + evidence) ·
DOCUMENTATION_INDEX (spec row, `draft`) · status · memory. Zero code/DB writes; battery
never (1530/1530 stands). git HEAD `49404001` · 0 staged · 2 stashes.

**Next: owner reviews the draft → DSA-C acceptance + freeze (`frozen-v1`) + routing +
handoffs + PHASE-11 VERDICT (owner-gated).**

## DSA-C — Owner acceptance + freeze + handoff — DONE 2026-07-17 → 🏁 PHASE 11 VERDICT

**Owner order (verbatim):** "I approve the draft specification as the Phase 11 architecture
baseline. Before freezing, perform one final read-only consistency pass… If everything
passes, proceed with DSA-C only."

### 1. Pre-freeze consistency pass — ALL GREEN (read-only)

| Check | Result |
|---|---|
| Contract ↔ census ↔ A1 ↔ spec consistency | ✅ — A1 present in Appendix A; spec carries the A1 world truth; census golden refs (ADST-0004/5/6) match spec §7/§11 |
| Obsolete-world references in the spec | ✅ **0** (`3-PATTI-011/013/014/015` absent; spec mentions only `3-PATTI-016` ×2 + `3-PATTI-009` ×1, both census-live) |
| Golden values vs sources | ✅ verified at source line-level: FOM :394 (`ADST-0004 finalized ₹344.25`) · :420 (`settled ₹801.00`) · :474 (`3-PATTI-016 … ADST-0006 ₹633.00`) · MANUFACTURING_V1_FREEZE :86 (`golden ₹225`) — each ×3 in the spec, consistent with the DSA-A DB census |
| §6.2 register | ✅ 13/13 section headers, mapping table (§DSA-B.1) stands |
| Provenance | ✅ 43 label lines; zero unlabeled rule sections (DSA-B proof: 40 `[REPO]` + 12 ratified-design) |

### 2. Freeze + routing executed

Spec → **v1.0.0 / 🔒 `frozen-v1`** (frontmatter + banner + §10 + §12; §13 Phase-12
implementation checklist **FINALIZED**). DOCUMENTATION_INDEX row → frozen-v1 wording ·
START_HERE row-A routing line added · status file + memory synced. §6.6 handoffs stand as
written in spec §9 (concrete obligations for 12/13/14/15/deploy; the §11 registry + §7
scenario table = the sync-readable sections + recorded KOS-compat candidates).

### 3. Success criteria walk (§3) — 9/9

1 spec exists, Standard-compliant, 13/13 register ✅ · 2 census complete w/ dispositions ✅
(DSA-A) · 3 provenance zero-unlabeled ✅ · 4 seeding law + writer map stated ✅ (spec §3,
14 rows) · 5 taxonomy w/ embedded golden values + owner change-control ✅ (spec §7) ·
6 identifier scheme + reserved-handle registry drafted-from-census ✅ (spec §4+§11) ·
7 interfaces written as obligations ✅ (spec §9) · 8 owner ratified D1..D9 BEFORE authoring +
accepted & froze at close ✅ · 9 zero code/DB changes, battery untouched, status+memory
synced every sub-phase ✅.

### 🏁 PHASE 11 VERDICT: **SPEC-FROZEN — PHASE COMPLETE.**

The development dataset is now an owner-frozen architecture (`frozen-v1`), formalized from
the certified organic reality with zero invention: Phase 12 implements it exactly (§13
checklist), Phase 13 verifies against its embedded truth, and no guarded table can ever be
legitimately seeded outside its certified writer. Phase-wide ledger: 0 code · 0 DB writes ·
0 pins · battery NEVER ran (1530/1530 stands) · 1 dated amendment (A1) · 1 classified
finding (C-DSA-1, disposed). git HEAD `49404001` · 0 staged · 2 stashes.

_Phase 11 closed 2026-07-17. Next: Phase 12 Seeder Engine — SEED-0 (owner-gated; the
campaign's first NEW-CODE phase)._
