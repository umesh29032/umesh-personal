---
id: docs-campaign-contracts-phase-12-seeder-engine
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 12 Execution Contract — Seeder Engine

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md) and **the entire Phase-11 specification**
> ([PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md](PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md)
> → `docs/DEV_DATASET_ARCHITECTURE.md`, frozen at DSA-C): the service-path seeding law, the
> 11-layer dependency order, the scenario taxonomy with golden values, the reserved-handle
> registry, reset semantics, and the 4-factor production guard — **none restated here; this
> contract is implementation deltas only. The spec wins on WHAT; this contract owns HOW.**
> A spec gap discovered during implementation = a dated Phase-11 amendment, never silent
> divergence (P11 §6.6 rule).
> **This is the campaign's first NEW-CODE implementation phase** (the documented-not-implemented
> charter reaching its turn): management commands + their tests are created; the battery grows.
> Evidence doc (created at SEED-0): `docs/SEEDER_ENGINE_LOG.md`.

## 1. Phase objective

Implement the four seeder commands the master index charters — **`seed_demo` · `seed_factory` ·
`seed_feature <feature>` · `reset_demo`** — as a spec-faithful orchestration engine: guards
first, services only, idempotent by natural key, transactional per world, self-asserting after
every seed, structurally incapable of running in production, and proven by its own test suite
inside the battery. At close, any agent can produce a deterministic DEV world with one command,
and Phase 13 has a live assertion substrate to verify.

## 2. Scope

### 2.1 Facts of record (authoring-time, verified 2026-07-12; SEED-0 re-verifies)

| Fact | Evidence |
|---|---|
| Import boundaries | `config/.importlinter`: foundation-purity = core+accounts import NO domain app (ALSO test-enforced: `core/tests.py::FoundationPurityTests` — a seeder in core/accounts goes battery-red by construction); acyclic layering tops out at the sibling row `storefront : expense : inventory : machines : patterns_ai` over production over tracking over raw_materials over accounts over core |
| Settings structure | `config/config/settings/{base,local,production}.py`; INSTALLED_APPS in base; `local.py` = dev overrides (DEBUG=True), the manage.py DEFAULT — a dev-only app registered in local.py is importable for runserver AND the battery, and absent under production settings |
| Command precedent | management commands exist per-app (e.g. `preview_allocation_bound`, S5 rollout cmd); no cross-domain orchestration command exists anywhere — the seeder is the first |
| Purity-test precedent | `patterns_ai/test_purity.py` — a test suite that PINS an app's structural non-interference; the model for the seeder's no-direct-guarded-writes purity test |
| Battery definition | framework README env facts: 9-app suite + patterns_ai as separate runs, sequential fresh-DB — adding the seeder app's tests = a framework-README battery-definition amendment (owner-gated, SEED-D4) |
| U8 posture | the seeder calls the approved single-writer services; it is NOT a new money-write path — PROVEN, not asserted, by the purity test (zero direct ORM writes to guarded tables) |
| Dev-DB fragility | the primary dev DB is single-copy evidence (Phase-0 OPEN) — seeder DEVELOPMENT must never touch it (SEED-D5 scratch-DB rule) |
| No migrations expected | the engine seeds the EXISTING schema via services; the seeder app ships with no models ⇒ no migrations (U14 stays untriggered; a migration need = stop condition) |

### 2.2 In / out

**In:** the dev-only seeder app (SEED-D1 home) · the four commands + shared orchestration
core · the 4-factor guard + structural absence in production settings · scenario registry
implementation (all six spec classes) · post-seed self-assertions · idempotency + determinism
proofs · the purity test + guard tests + scenario tests · battery integration ·
documentation + handoffs.
**Out:** ANY schema change (models/migrations — none; needing one = §16.4) · touching any
existing app's code (the seeder IMPORTS services; it never edits them; a service found
insufficient for seeding = spec-vs-reality finding → Phase-11 amendment + owner, never a
service patch from this phase) · seeding/resetting the PRIMARY dev DB during this phase
(SEED-D5) · production/deployment wiring (Phase 19 explicitly EXCLUDES seeders) · Phase-13
verify commands (only the shared assertion module is built here) · flag changes (U10) ·
teardown of the organic dev worlds (owner-gated elsewhere).

## 3. Success criteria

Phase 12 is DONE when ALL hold:
1. The four commands exist in the SEED-D1 home, registered ONLY in dev settings; under
   production settings the app is absent (proven: command discovery fails — recorded).
2. **Guard proof:** every command refuses unless all four spec guard factors pass
   (settings-module + dev marker + DB-name allowlist + explicit destructive confirmation for
   reset) — each factor negatively tested (simulated wrong settings/DB name → refusal quoted).
3. **Spec fidelity:** every scenario in the spec registry is implemented; layer order matches
   the spec's 11 steps; every seeded row is created via its spec-mapped writer (service or
   plain ORM only where the spec's writer map says no service exists).
4. **Purity proven:** the purity test pins zero direct ORM writes to guarded tables from the
   seeder package (ledger, settlements, WST/WSC, allocations, *History, processing_cost) —
   the U8 compliance proof, in the battery forever.
5. **Idempotency proven:** double-seed of every scenario converges (second run = zero new
   rows, zero duplicates; counts identical) — tested.
6. **Determinism proven:** two seeds of the same scenario into two fresh scratch DBs produce
   identical natural-handle sets, counts, and monetary outcomes.
7. **Golden regression scenarios pass:** the seeded journeys reproduce the spec's embedded
   expected values (₹801.00 / ₹344.25 / ₹633.00 class; ₹225 invariant) byte-for-byte, and the
   post-seed self-assertion pass (§6.5) is green for every scenario.
8. **Battery green** at the new baseline: entry baseline + the seeder suite (arithmetic
   recorded per wave; the framework-README battery amendment ratified at SEED-0 and applied).
9. The primary dev DB is untouched throughout (proven: row-count/mtime census unchanged —
   recorded at SEED-0 and SEED-F).
10. Docs synced (U6: new app → GUIDE + README + DOCUMENTATION_INDEX + CHANGE_IMPACT_MATRIX
    consultation); Phase-13/14 handoffs written; status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + the spec)

- **Guards before features:** no seeding logic lands before the guard module + its negative
  tests are green (SEED-A). A command skeleton that can touch a DB before its guard exists
  never ships even transiently.
- **Scratch-DB law (SEED-D5):** all seeder development, manual runs, and determinism proofs
  use throwaway databases named per the guard allowlist (created/dropped freely); the primary
  dev DB is NEVER a seeder target in Phase 12. (Recommendation carried from P11: executing
  Phase 0's snapshot before this phase further de-risks — owner's call, noted not gated.)
- **Services are read-only dependencies:** the seeder imports and calls; it never monkeypatches,
  never bypasses PermissionDenied paths (it authenticates as seeded cast identities where a
  service demands an actor — the spec's cast layer seeds first for exactly this reason), never
  catches-and-ignores service refusals (a refusal during seeding = a bug in the scenario
  definition or a spec gap → stop and report, not force).
- **One layer/scenario wave at a time** (PHASE_04 serial discipline): implement → test →
  battery → log before the next.
- **Actor integrity:** seeded writes carry TRUE actor stamps from the cast (MGT-G
  true-actor-stamp precedent) — the seeder never writes as a phantom/system user unless the
  spec names one.
- U13 in dev worlds: scenario teardown inside a living world uses designed reverse paths;
  `reset_demo` alone may rebuild a scratch DB wholesale (spec §6.1.8).
- New-code tests are part of implementation (this is a charter build, not a certification —
  U4's pins-only-for-fixes governs CERTIFICATION phases; here the test suite is a deliverable,
  and its membership in the battery is the SEED-D4 amendment).

## 5. Evidence standard

Per wave: the commands run + full output quoted (guard refusals verbatim) · row-count tables
per layer vs spec expectations · handle-registry census (seeded handles vs spec reserved list)
· idempotency double-run diffs · determinism cross-DB comparisons · golden-value assertion
output (₹ matched, byte-form shown) · battery arithmetic (entry + suite growth per wave) ·
primary-dev-DB untouched proof (census unchanged). Test evidence: suite list with what each
test pins. Sub-agent scaffolding sweeps supplemental (U7); guard proofs, money-adjacent waves
(SEED-C), purity verdicts, and certification = main-thread.

## 6. Methodology

### 6.1 Command home + architecture (SEED-D1 default)

A NEW dev-only Django app (default name `devseed`): no models, no migrations, no URLs, no
templates — only `management/commands/` (the four commands), an orchestration core
(`scenarios/` registry + `layers/` seeding steps + `guard.py` + `assertions.py`), and tests.
Registered ONLY in `config/config/settings/local.py` (`INSTALLED_APPS += [...]` override —
the app does not exist under production settings: the structural fifth guard factor).
Import-linter: added as a NEW TOPMOST layer above the sibling row (it imports everything;
nothing imports it) — the `.importlinter` edit is part of SEED-A and battery-covered via
FoundationPurityTests remaining green. Commands are thin CLI shells; ALL logic lives in the
orchestration core (testable without CLI).

### 6.2 CLI interface (SEED-D7 default)

`seed_demo` (no args — the demo world per SEED-D2) · `seed_factory` (the full three-product
factory) · `seed_feature <feature-slug>` (slug validated against the spec scenario registry;
unknown slug lists valid ones and exits nonzero) · `reset_demo [--db <allowlisted-name>]
--i-understand-this-destroys-<dbname>` (exact-name confirmation string — typo-proof
destructive gate). Common flags: `--verbosity` (Django standard) · `--check` (dry-run: print
the plan — scenario, layers, expected counts — write nothing) · `--skip-assertions` does NOT
exist (assertions are not optional). Every run prints the spec version it implements and the
scenario id; exit codes: 0 = seeded+asserted, nonzero otherwise.

### 6.3 Orchestration: layers, services, transactions (SEED-D3 default)

Layer executors follow the spec's 11-step order; each executor declares its writer map row
(service function per entity family) and its natural-key converge rule (get-by-handle →
create-via-service if absent → verify state matches spec else report divergence). **One outer
`transaction.atomic` block per WORLD** (scenario = all-or-nothing; service-internal atomics
nest as savepoints); `reset_demo` is non-transactional by nature (DB drop/recreate → migrate →
optional seed) and therefore carries the strictest confirmation. Failure mid-seed = automatic
rollback of the world + a report naming the layer, entity, and service refusal verbatim.

### 6.4 Idempotency + natural identifiers

Convergence is keyed EXCLUSIVELY on the spec's reserved handles (natural keys); the seeder
never queries by pk, never stores pks in its registry, and its output manifest reports handles
only. Re-run semantics: existing handle + matching state = skip (counted); existing handle +
divergent state = REPORT, never auto-correct (a divergent world is evidence of drift — the
Phase-14 interface — not something a seeder silently paves).

### 6.5 Post-seed self-assertions + logging (SEED-D6/D8 defaults)

The shared `assertions` module implements the spec §6.1.7 definitions (per-scenario counts ·
handle completeness · DEV-marking invariant · referential spot-checks · golden values · flags
untouched) and runs AUTOMATICALLY after every seed — fail = nonzero exit + the world stays
(rolled-back worlds excepted) for forensics. **This module is single-source: Phase 13's
`verify_*` commands import IT** (never fork it — the PHASE_08 validator-extension rule
applied). Logging: human-readable run log to stdout + a machine-readable seed manifest
(scenario, spec version, timestamp, handle census, counts, assertion results) written to a
runtime location OUTSIDE the repo tree (default `var/seed_manifests/` — gitignored territory;
runtime artifacts never enter docs/).

### 6.6 Production safety (spec DATA-D8 + the structural factor)

Five factors, all independent: (1) settings-module check · (2) dev-marker (DEBUG) check ·
(3) DB-name allowlist · (4) exact-string destructive confirmation · (5) STRUCTURAL — the app
is not installed under production settings, so the commands do not exist there (proven in
§3.1). Guard logic is pure + unit-tested first (SEED-A); guard bypass flags do not exist.

### 6.7 Handoffs

**Phase 13 (Verification):** consumes `assertions` as its single-source check library; the
seed manifest format is its input contract; the DEV-namespace reservation check is specified
for `verify_production` (read-only). **Phase 14 (knowledge_sync):** the scenario registry is
machine-readable — spec⇄implementation drift detection (declared vs implemented scenarios,
spec version pinning) handed off as a detector spec (detect-and-notify law). **Phase 15
(BOD):** demos run on `seed_factory` worlds in scratch DBs until the owner blesses a primary-
dev-DB refresh. **Deployment (19):** the runbook states the seeder's exclusion + the
structural absence proof.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery at every
code-wave close** (§13).

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **SEED-0** — Charter + gate + ratification | Gate: Phase 11 closed (spec `frozen-v1`). Owner ratifies SEED-D1..SEED-D9 incl. the battery-definition amendment (D4) + scratch-DB allowlist names (D5). Baselines: battery entry number; primary-dev-DB census (row counts of key tables — the untouched-proof anchor). Log skeleton. **Stop:** gate fails; any SEED-D unanswered. |
| **SEED-A** — App skeleton + guards (battery-bearing) | Create the dev-only app + local.py registration + .importlinter topmost layer; guard module + negative tests FIRST (all five factors); command shells that only guard-check and exit; `--check` plumbing. **Proofs:** production-settings absence; guard refusals verbatim; FoundationPurityTests still green; battery = entry + guard tests. **Stop:** import-linter red; any path by which an unguarded write could occur. |
| **SEED-B** — Foundation layers (cast → masters → products/flows → machines → rolls; battery-bearing) | Layer executors 2–6 per the spec writer map; minimal scenario end-to-end on a scratch DB; idempotency double-run for these layers; handle census vs spec. **Stop:** a service refuses a spec-defined seed (spec gap → P11 amendment); any direct write where a service exists. |
| **SEED-C** — Production truth + money layers (7–8; battery-bearing, U8-hostile) | Chokepoint orchestration (worker_task/pool/settlement/advance/expense services) with TRUE cast actors; the **purity test** lands here (zero direct guarded-table writes — pinned forever); golden regression scenario seeds + ₹-value assertions; ledger-integrity recount around the wave (MGT-C discipline). **Stop:** U8 anomaly (any write path outside the approved services — STOP + report, never silently fix); golden value mismatch (spec-vs-reality → owner). |
| **SEED-D** — Remaining layers + full scenario registry (9–11; battery-bearing) | Storefront, patterns_ai, reporting-as-service-outcomes; `seed_demo`/`seed_factory` complete per SEED-D2; all `seed_feature` slices; edge-case scenarios (over-allocation M-6 world, damaged rolls, monthly worker, composite roles); registry completeness vs spec = counted. **Stop:** an edge-case scenario cannot be built through designed paths (spec/owner). |
| **SEED-E** — reset_demo + idempotency/determinism certification (battery-bearing) | The destructive path LAST: reset on scratch DBs only, exact-string confirmation, allowlist enforcement negative-tested; full idempotency matrix (every scenario double-seeded); determinism cross-DB proof; divergent-world REPORT behavior tested. **Stop:** reset touches anything outside the named DB; confirmation bypass possible. |
| **SEED-F** — Certification + handoffs | Full-suite battery at final arithmetic; primary-dev-DB untouched proof (census vs SEED-0); spec-fidelity checklist (every spec register row → implemented/deferred-with-P11-amendment); §6.7 handoffs written; U6 docs complete (new app GUIDE/README, DOCUMENTATION_INDEX rows, CHANGE_IMPACT_MATRIX); PHASE-12 VERDICT. **Stop:** unaccounted spec row; census drift on the primary dev DB. |

## 8. Deliverables

- The dev-only seeder app: 4 commands, orchestration core, guard module, shared `assertions`
  module, scenario registry — all spec-faithful.
- Its test suite in the battery (guards, purity, idempotency, determinism, golden scenarios)
  + the ratified battery-definition amendment.
- `docs/SEEDER_ENGINE_LOG.md`: ratifications · per-wave evidence · proofs (§3) ·
  certification + handoffs.
- U6 documentation: the app's README + `docs/apps/<app>/GUIDE.md` + index rows.
- Filled Design Record (SEED-D1..SEED-D9); status + memory per sub-phase.

## 9. Files expected to change

**New (code):** the seeder app tree (commands, core, guard, assertions, tests — SEED-D1 home)
· its app README + `docs/apps/<app>/GUIDE.md`. **Updated (code-adjacent):**
`config/config/settings/local.py` (dev-only registration — the ONE settings edit this phase
is licensed for; base.py/production.py untouched) · `config/.importlinter` (topmost layer
row). **Docs:** `docs/SEEDER_ENGINE_LOG.md` (new) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` ·
`docs/DOCUMENTATION_INDEX.md` · framework `campaign_contracts/README.md` (the D4
battery-definition amendment, dated) · this file (Design Record + amendments) · memory files.
**Runtime (gitignored territory):** scratch DBs + `var/seed_manifests/`. Nothing else.

## 10. Files that must never change (touching one = STOP + report)

- EVERY existing app's code: models, services, views, forms, templates, tests, migrations —
  the seeder adapts to services, never the reverse.
- `config/config/settings/base.py` + `production.py` (local.py's registration line is the
  licensed exception) · enforcement flags (U10) · `.env`.
- The PRIMARY dev database (SELECT-census only; never a seed/reset target this phase) · the
  organic dev worlds · non-DEV data anywhere.
- Seed migrations (accounts/0016/0017 class) · `docs/DEV_DATASET_ARCHITECTURE.md` (spec
  changes = dated P11 amendments by their own rules) · `canonical_manifest.json` ·
  `docs/DOC_STANDARDS.md` · T1 truth-locks · closed phase logs.
- `.claude/` tooling · the 2 stashes · `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections append-only,
corrections dated); (b) status-file Phase-12 row + dashboard (battery number updates per wave)
+ "Next action"; (c) **U6 fully applies** (new code): app README + GUIDE created at SEED-A and
kept current per wave; CHANGE_IMPACT_MATRIX consulted per changed file; DOCUMENTATION_INDEX
rows (log at SEED-0; app docs at SEED-A); (d) the framework-README battery-definition
amendment recorded at SEED-0 (dated, owner-approved).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-12
bullet: wave closed, battery arithmetic, scenario coverage, log pointer) + MEMORY.md index
line at each sub-phase close. Agents without memory: skip — the log + status file + the seed
manifests are the complete binding record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (SEED-A..SEED-E) and at
SEED-F final**. Arithmetic: entry baseline (status dashboard at SEED-0) + the seeder suite's
cumulative test count per wave — recorded each run. The suite definition amendment (adding
the seeder app to the canonical battery command list) is SEED-D4, ratified at SEED-0 and
applied to the framework README same session. Golden-scenario integration tests may be the
suite's slowest members — runtime recorded; if the owner rules them out of the default
battery (D9), they run as a named separate proof at every wave instead (never skipped
silently).

## 14. Regression policy

- FoundationPurityTests + the full existing battery green at every wave = the do-no-harm
  proof (the seeder must not perturb any existing app's tests).
- The purity test (SEED-C) permanently pins U8 compliance; guard negative tests permanently
  pin production safety.
- Golden values are owner-truth: a mismatch is NEVER fixed by adjusting the expected value
  (that's a P11-spec owner decision) nor by patching a service (§2.2 out) — mismatch = stop.
- Prior-fix guard list untouched surfaces — not re-proven here (no existing-code changes);
  any incidental discovery of an app defect while seeding = observation → U12 backlog
  (+U8 stop if money), never fixed inline.
- Pins-for-fixes (U4) applies to any CONFIRMED defect fixed under the Phase-4 protocol
  (cross-logged) — distinct from the engine's own feature tests.

## 15. Rollback policy

- Failed world-seed: the outer atomic rolls back (proven behavior, tested); the report names
  layer/entity/refusal.
- A bad wave: revert the wave's diff (the app tree is additive and file-scoped; local.py +
  .importlinter lines revert cleanly); battery to green; report.
- Scratch DBs are disposable by definition; `reset_demo` misfire risk is bounded by the
  allowlist + exact-string confirmation (negative-tested before the command ever runs
  outside tests).
- The log + Design Record are append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests FIRST, reconciles the log,
  completes or reverts the half-done executor before new work; scratch worlds are re-seeded,
  never forensically nursed.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. SEED-0 gate fails (Phase 11 not closed / spec not frozen) or any SEED-D1..D9 unanswered.
3. U8 anomaly: any write path to a guarded table outside its approved service — in seeder
   code, in a test, anywhere (STOP + report, never silently fix).
4. A migration, an existing-app code change, or a base/production settings change becomes
   "necessary" (misfiled work → owner / P11 amendment / Phase-4 protocol).
5. A service refuses a spec-defined seed, or a golden value mismatches (spec-vs-reality →
   dated P11 amendment + owner; the seeder never forces).
6. Guard hole: any conceived path by which a command could execute under production settings
   or against a non-allowlisted DB.
7. The primary dev DB's census drifts (anything touched it — this phase or otherwise).
8. Battery red on anything other than the wave's own new tests' target behavior.
9. Identity/lockout issues with cast actors during service-path seeding (rate-limit rules
   apply to seeded logins only if the seeder authenticates via the auth stack — if it uses
   direct actor objects, N/A; either way, no production identity is ever used).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-12 row: which SEED-* is next; battery
   baseline + suite arithmetic so far.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment + any D4 battery amendment)
   → `docs/DEV_DATASET_ARCHITECTURE.md` (the spec — the WHAT) →
   [PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md](PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md)
   (Design Record answers) → this contract → `docs/SEEDER_ENGINE_LOG.md` if it exists
   (absent ⇒ next = SEED-0).
3. Verify read-only: spec version vs the version the code claims (a drifted spec = dated-
   amendment trail to reconcile first); guard tests green before ANY manual command run;
   scratch-DB allowlist names from the Design Record; primary-dev-DB census vs the SEED-0
   anchor.
4. Never run a seeder command before its guard suite passes in THIS working tree.
5. Battery environment per framework env facts; manual runs on scratch DBs only.
6. Execute exactly ONE sub-phase per §7, waves strictly serial. STOP per §16.
7. Anything inconsistent across status file / spec / Design Record / log / this contract →
   report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (SEED-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| SEED-D1 | Command home | New dev-only app `devseed` (no models/migrations/URLs): commands + orchestration core + guard + assertions + tests; registered ONLY in settings/local.py; added as NEW TOPMOST import-linter layer | **ACCEPT** (owner 2026-07-17, verbatim; no override) |
| SEED-D2 | seed_demo vs seed_factory semantics | `seed_demo` = the minimal-plus demo world (fast, single product journey); `seed_factory` = the full three-product factory (T-SHIRT + LOWER + 3-PATTI class worlds with settled journeys) | **ACCEPT** |
| SEED-D3 | Transaction boundaries | One outer atomic per world (services nest as savepoints); reset_demo non-transactional (drop→migrate→optional seed) with the strictest confirmation | **ACCEPT** |
| SEED-D4 | Battery membership | The seeder app's tests join the canonical battery as an additional sequential suite member; framework-README env-facts amendment dated + applied at SEED-0 | **ACCEPT + owner verbatim: "Record the required dated amendment to the framework README so the devseed test suite becomes an official sequential member of the canonical battery from Phase 12 onward."** → amendment applied same session |
| SEED-D5 | Scratch-DB law | All Phase-12 runs/proofs on allowlisted throwaway DBs (names ratified here); the PRIMARY dev DB is never a target this phase; Phase-0 snapshot before execution = recommended, owner's call | **ACCEPT + owner verbatim allowlist: `inventory_seed_scratch_1` · `inventory_seed_scratch_2`. "The primary development database must never be a Phase 12 seeding target."** |
| SEED-D6 | Assertion module single-source | `assertions` implements spec §6.1.7; runs automatically post-seed (non-optional); Phase 13 imports it, never forks | **ACCEPT** |
| SEED-D7 | CLI surface | §6.2: slugs validated against the registry, `--check` dry-run, exact-string destructive confirmation, no assertion-skip flag, spec-version banner, standard exit codes | **ACCEPT** |
| SEED-D8 | Manifests + logging | stdout run log + machine-readable manifest to `var/seed_manifests/` (gitignored runtime territory; never docs/) | **ACCEPT** |
| SEED-D9 | Test tiers | Guard unit tests + purity test + idempotency tests + determinism proof + golden integration scenarios; golden tests' battery membership vs named-separate-proof = owner's runtime-cost call here | **ACCEPT + owner verbatim: golden integration tests STAY INSIDE the canonical battery ("Correctness and regression protection take priority over runtime"); runtimes recorded per run; revisit only via dated amendment** |

Date · answered by: **2026-07-17 · owner, verbatim ("I accept the defaults for SEED-D1 through SEED-D9 with the following explicit rulings…") — SEED-0 CLOSED; SEED-A authorized same order, gated on the fresh dev-DB census re-capture matching the SEED-0 anchor (§16.7 on any delta).**

## Dated amendments

- **2026-07-17 — SEED-D6 reconciliation APPLIED (by Phase 13 VER-A, the first executor, per
  the owner's VER-D1 ratification: "Apply the SEED-D6 reconciliation as ONE coordinated
  change… The assertion library must have exactly one implementation after the move"):** the
  shared assertion library relocated `devseed/assertions.py` → `verification/assertions.py`
  (the BASE-settings read-only `verification` app). `devseed` now IMPORTS it (three sites:
  `core.py` ×2, `tests/test_reset.py`); the old module is DELETED (no shim — single
  implementation, pinned by `verification.tests.test_shared_library`). Import-linter:
  `verification` layered directly below `devseed`. One coordinated diff, own battery run
  (devseed 70/70 + verification 28/28 green post-move). Mirror record: PHASE_13 Appendix A.

# Evidence note

All implementation evidence lives in `docs/SEEDER_ENGINE_LOG.md` (created at SEED-0) —
contract = procedure, log = what was built and proven (framework hierarchy rule). Runtime
seed manifests are operational artifacts (`var/`), never campaign records; anything binding
they contain is quoted into the log.
