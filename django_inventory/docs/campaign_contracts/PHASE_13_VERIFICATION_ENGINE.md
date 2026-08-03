---
id: docs-campaign-contracts-phase-13-verification-engine
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 13 Execution Contract — Verification / Smoke Test Engine

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), **the Phase-11 specification** (`docs/DEV_DATASET_ARCHITECTURE.md`:
> assertion definitions §6.1.7, golden values, DEV-namespace reservation, guard factors) and
> **the Phase-12 contract + its artifacts**
> ([PHASE_12_SEEDER_ENGINE.md](PHASE_12_SEEDER_ENGINE.md): the shared assertions module —
> **the single source of truth this engine imports and NEVER forks** — the seed-manifest
> contract, the guard architecture, the purity-test pattern, and the SEED-D4 battery-growth
> mechanism). None restated; deltas only.
> **Cross-contract reconciliation flagged (VER-D1):** SEED-D6's default placed the shared
> assertions module inside the dev-only `devseed` app — but `devseed` is structurally ABSENT
> under production settings, and `verify_production` must run there. Resolution default: the
> verification app lives in BASE settings (production-present, read-only by construction),
> the shared check library lives IN IT, and `devseed` imports it (dependency: devseed →
> verification). This is a dated amendment proposal to PHASE_12's Design Record, ratified at
> whichever of SEED-0 / VER-0 executes FIRST — never silently diverged.
> **This engine is designated the permanent verification instrument for every future
> deployment** (owner, 2026-07-12): phases 19–21 and post-campaign operations consume it.
> Evidence doc (created at VER-0): `docs/VERIFICATION_ENGINE_LOG.md`.

## 1. Phase objective

Implement the verification engine — **`verify_demo` · `verify_factory` ·
`verify_feature <feature>` · `verify_production` · `verify_all`** — a strictly read-only,
deterministic check-runner that proves a world (seeded DEV world or the production database)
conforms to its certified invariants: spec assertions, golden values, DEV-contamination
absence, configuration truth (enforcement flags, migrations), and data-integrity invariants
already certified by the campaign. At close, "is this system in a known-good state?" is one
command with a machine-readable answer — the standing instrument deployment readiness
(Phase 21) and post-deploy operations will cite.

## 2. Scope

### 2.1 Facts of record (authoring-time; VER-0 re-verifies)

| Fact | Evidence |
|---|---|
| The check substrate exists by contract | Phase-12 `assertions` module (spec §6.1.7 definitions: counts · handle completeness · DEV-marking invariant · referential spot-checks · golden values · flags untouched) + `var/seed_manifests/` machine-readable manifests (scenario, spec version, handle census, counts, assertion results) |
| Certified invariants to codify | manifest `never_modify`/`hard_rules` (single-writer walls, never-edit-money-rows, ADR-0009 no-summing) · the 26+ CheckConstraints record · golden ₹ values (owner business truth) · U10 flag policy (ENFORCE_* stay OFF until R11 — a CONFIG assertion with an owner-declared expected state) · DEV-namespace reservation (P11 DATA-D8: production data may never carry DEV identifiers) |
| Production side-effect hazard | exercising the request cycle writes rows (sessions; potential logs/messages) — therefore production checks are ORM-SELECT/config-only by default (VER-D3); request-cycle smoke belongs to dev modes only |
| Home constraints | foundation-purity + acyclic layering (PHASE_12 §2.1): a domain-reading engine must sit at/above the topmost layer; `devseed` is local-settings-only — verify_production needs a BASE-settings home (→ VER-D1) |
| Battery mechanism | SEED-D4 precedent: a new app's tests join the canonical battery via a dated framework-README amendment |
| Point-in-time trap | MGT-C's 170 rows/₹10880.25 were session baselines, NOT eternal constants — verification checks must encode SELF-CONSISTENCY invariants (items-sum-to-totals, reversals-net, constraint-shaped predicates), never frozen snapshots |

### 2.2 In / out

**In:** the verification app (VER-D1 home, BASE settings) · the five commands + shared check
registry · guard polarity per command (§6.3) · the read-only purity proof · report generation
(stdout + machine-readable) · determinism proofs · the engine's test suite + battery
integration · docs + handoffs.
**Out:** ANY write to ANY database by engine code, ever (tests mutate their own test DBs
freely — the ENGINE writes nothing) · fixing anything a check finds (findings route per U12 /
Phase-4 protocol / U8 stop — a verifier that repairs is a corrupter) · new invariants
(§6.4 law: checks CODIFY certified invariants; wanting a new one = owner/ADR territory) ·
seeding (Phase 12's job; verify commands may REQUIRE a manifest, never create one) ·
CI/scheduling infrastructure (VER-D9 records the owner's cadence intent; cron/CI wiring is
out) · knowledge_sync's docs-drift domain (Phase 14) · schema changes (no models expected;
needing one = stop) · deployment wiring itself (Phase 19 consumes the handoff).

## 3. Success criteria

Phase 13 is DONE when ALL hold:
1. The five commands exist in the VER-D1 home, present under BOTH dev and production settings;
   guard polarity proven per command (§6.3 matrix — each cell negatively tested).
2. **Read-only proven:** the purity test pins zero ORM writes (save/create/update/delete/raw
   write SQL) from the verification package — in the battery forever; additionally a runtime
   proof: a full `verify_all` run against a seeded scratch world leaves its row counts
   byte-identical.
3. **Single-source honored:** every seed-world check imports the shared assertions module;
   zero duplicated check logic (structural proof: the engine defines only registry/reporting/
   production-check code, and the SEED-D6 reconciliation is applied on whichever side runs
   first).
4. **Check-registry completeness:** every certified-invariant source (§2.1 row 2) is either
   codified as a check with its citation, or registered deferred-with-reason — counted, not
   asserted.
5. **Category coverage proven on scratch worlds:** smoke (dev modes) · regression/golden
   (byte-match) · production-safety (flags/migrations/config) · DEV-contamination (a planted
   DEV-handle row in a scratch "prod-like" DB is caught; clean DB passes) · self-consistency
   integrity checks — each demonstrated with a passing AND a failing case (failing cases
   constructed in test DBs via designed paths).
6. **Determinism proven:** same world + same engine version ⇒ byte-identical machine reports
   (modulo the report's own run-timestamp field, which lives in the envelope, not the body —
   body hash stable).
7. `verify_all` composes correctly per environment (manifest-driven in dev; production-safe
   subset in prod; aggregate report; run-all-then-report per VER-D7).
8. Battery green at the new baseline (entry + the verification suite; framework-README
   amendment per VER-D6 recorded); primary dev DB untouched throughout (census proof —
   scratch-DB law inherited).
9. Docs synced (U6 — new app README/GUIDE/index rows); Phase-14/15/19 handoffs written;
   status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + P11/P12 inheritance)

- **Read-only is architectural, not behavioral:** the engine holds no code path that writes —
  enforced by the purity test from VER-A onward (before any check logic lands, mirroring
  guards-before-features).
- **Checks codify, never legislate (§6.4):** every check names the certified invariant it
  implements (manifest rule id / spec § / ADR / golden value / CheckConstraint class). A
  check without a citation does not merge.
- **A red check never triggers a fix from this phase:** finding → report → route (U12
  backlog / Phase-4 ledger / U8 STOP if money-adjacent / dated P11-P12 amendment if
  spec-vs-engine). The engine's exit code is its whole authority.
- **Production humility:** verify_production runs SELECT + settings/migration introspection
  only; no request cycle, no logins, no cache/session churn; bounded query cost (large-table
  checks use aggregate queries, not row scans, where the invariant allows — noted per check).
- **Scratch-DB law inherited** (SEED-D5): all dev-mode proofs on allowlisted scratch worlds;
  the primary dev DB is never a proof target this phase.
- One check-category wave at a time (serial discipline); the shared-module reconciliation
  (VER-D1) is applied as ONE coordinated change with its own battery run, whichever phase
  executes first.

## 5. Evidence standard

Per wave: command outputs quoted (pass AND constructed-fail cases) · check-registry table
(check id · invariant citation · category · env applicability · status) · purity + read-only
runtime proofs (pre/post row-count identity) · determinism body-hash pairs · guard-polarity
matrix results · battery arithmetic per wave · primary-dev-DB untouched census. Report
samples: one machine-readable report per command class archived into the log (quoted, since
`var/` is runtime territory). Sub-agent scaffolding sweeps supplemental (U7); check-registry
citations, production-check design, money-adjacent integrity checks, and certification =
main-thread.

## 6. Methodology

### 6.1 Verification philosophy

Verification answers exactly one question per check: "does observed state satisfy a CERTIFIED
invariant?" — with a citation, deterministically, without side effects, in any environment the
check declares. It never explains, never repairs, never re-certifies (certification phases
prove behavior; verification proves state). Reports are for humans AND machines (Phase-21
certificate + Phase-14 conventions). Where verification and certification disagree, the
finding routes to the owner via the conflict rule — the engine is an instrument, not an
authority.

### 6.2 Engine architecture (VER-D1 default)

A NEW app (default name `verification`): no models, no migrations, no URLs — `management/
commands/` (five commands), `checks/` (the registry: one module per category, each check a
pure function over ORM/settings state → CheckResult), `report.py` (envelope + body,
machine-readable JSON + human stdout), `guard.py` (polarity per §6.3). Registered in BASE
settings (present everywhere — its read-only nature is what makes that safe). Import-linter:
topmost layer (alongside/below `devseed`, which imports it after the SEED-D6 reconciliation).
The shared assertions library (spec §6.1.7 implementation) LIVES HERE; `devseed` imports it
for post-seed self-assertions — one implementation, two consumers.

### 6.3 Command responsibilities + guard polarity (VER-D2 default)

| Command | Does | Dev settings | Prod settings |
|---|---|---|---|
| `verify_demo` | full check suite over the seed_demo world (manifest-required) | ✅ | ❌ refuses (needs seeded world + dev-only categories) |
| `verify_factory` | same over the seed_factory world | ✅ | ❌ refuses |
| `verify_feature <slug>` | scenario-scoped checks (slug validated against the spec registry) | ✅ | ❌ refuses |
| `verify_production` | production-safe subset ONLY: DEV-contamination scan · flags-state vs owner-declared expectation · migrations-applied consistency · self-consistency integrity checks · config sanity | ✅ (runs the same subset — useful pre-deploy rehearsal) | ✅ (its purpose) |
| `verify_all` | environment-aware composition: dev = every manifest-present world + verify_production's subset; prod = the production-safe subset only | ✅ | ✅ |

Common flags: `--report <path-or-default>` (machine report; default `var/verification_reports/`)
· `--verbosity` · exit codes: 0 = all green, nonzero = any red (count in the envelope).
Dev-world commands REQUIRE the world's seed manifest (absent manifest = clear refusal naming
`seed_*` as the remedy — the engine never seeds). No flag exists to skip a check silently;
category exclusion is explicit + reported (`--skip <category>` prints what was skipped into
the report).

### 6.4 Check categories + the codify-don't-legislate law

- **Smoke (dev modes only):** app registry loads · URLConf resolves (route-count vs the
  census instrument) · critical pages render 200 via test client AS cast identities on a
  SCRATCH world (request-cycle allowed only here).
- **Regression / golden:** shared-assertion runs on regression worlds; ₹ byte-match.
- **Production safety:** ENFORCE_* flags == owner-declared expected state (U10; the expected
  state is a DECLARED input read from the check registry's config, changed only by owner —
  post-R11 flips update the declaration, not the check) · migrations applied = migration files
  (no unapplied/unknown) · settings sanity (DEBUG False in prod-mode report, secret presence
  not value).
- **DEV-contamination:** scan identifier-bearing columns for the reserved DEV namespace
  (P11 DATA-D8) — any hit in a production-mode run = red.
- **Integrity (self-consistency):** settlement items Σ = settlement totals · ledger reversal
  pairs net correctly · constraint-shaped predicates re-checked in SQL (the CheckConstraints
  record) · single-writer sanity where READ-detectable. All SELECT/aggregate.
Every check carries its citation (§4); the registry is machine-readable (Phase-14 interface).

### 6.5 Reports + determinism (VER-D5 default)

Machine report = JSON: envelope (command, engine version, spec version, environment, run
timestamp, totals) + body (ordered check results: id, citation, status, measured values).
**Determinism = body-stable:** sorted check order, no timestamps/randomness in the body;
body-hash recorded in the envelope — two runs on an unchanged world produce identical bodies.
Reports live in `var/verification_reports/` (gitignored runtime territory); anything binding
is quoted into campaign/deployment records by the humans who cite it.

### 6.6 Handoffs

**Phase 14 (knowledge_sync):** the machine-readable check registry + report format = shared
conventions; boundary stated: 13 verifies DATA/CONFIG state, 14 detects CODE⇄DOCS⇄GRAPH
drift — no overlap, same detect-and-notify law. **Phase 15 (BOD):** the dashboard may DISPLAY
latest verification results (read var/ artifacts) — it never runs checks inline; any such
feature = Phase-15 contract work. **Phase 19–21 (deployment):** the runbook gains a mandatory
post-deploy `verify_production` step + a pre-deploy rehearsal note; the Phase-21 readiness
certificate CITES a green `verify_production` report (envelope + body-hash quoted) as a
required input — this engine is the permanent deployment-verification instrument (owner
designation, header).

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery at every
code-wave close**.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **VER-0** — Charter + gate + ratification | Gate: Phase 12 closed (assertions module + manifests live). Owner ratifies VER-D1..VER-D9 incl. the SEED-D6 reconciliation state (already applied at SEED execution, or applied here as the coordinated change) + the battery amendment (VER-D6). Baselines: battery entry; primary-dev-DB census anchor. **Stop:** gate fails; any VER-D unanswered; reconciliation state ambiguous. |
| **VER-A** — App skeleton + guards + read-only purity (battery-bearing) | Create the `verification` app + BASE-settings registration + import-linter layer; guard polarity module + negative tests; **the read-only purity test lands BEFORE any check logic**; command shells guard-check and exit; report envelope/body scaffolding. **Proofs:** polarity matrix; purity green; FoundationPurityTests green; battery = entry + new tests. **Stop:** any conceivable engine write path. |
| **VER-B** — Dev-world verification (battery-bearing) | `verify_demo`/`verify_factory`/`verify_feature`: manifest ingestion, shared-assertion invocation, smoke category (test-client renders on scratch worlds), golden byte-match; pass + constructed-fail proofs per category. **Stop:** any check logic duplicating the shared module (single-source breach); manifest-format mismatch (→ dated P12 amendment). |
| **VER-C** — verify_production + verify_all (battery-bearing) | Production-safe subset: contamination scan (planted-handle fail proof on a scratch DB), flags-vs-declaration, migrations consistency, integrity self-consistency checks (SELECT/aggregate only, cost noted per check); verify_all composition both environments; runtime read-only proof (pre/post row-count identity on a full run). **Stop:** a production check needs the request cycle or unbounded scans; an integrity check wants a NEW invariant (owner/ADR). |
| **VER-D** — Determinism + report certification (battery-bearing if fixes) | Body-hash determinism pairs per command; report samples archived into the log; `--skip` transparency proof; exit-code matrix. **Stop:** nondeterministic check that survives one fix attempt. |
| **VER-E** — Certification + handoffs | Registry completeness census (every §2.1 invariant source → check or deferred row); full battery final arithmetic; primary-dev-DB untouched proof; §6.6 handoffs written (incl. the runbook step spec + certificate input format for Phase 19/21); U6 docs complete; PHASE-13 VERDICT. **Stop:** unaccounted invariant source. |

## 8. Deliverables

- The `verification` app: 5 commands, check registry (cited checks), shared assertion library
  (post-reconciliation single source), guards, reports — read-only proven.
- Its test suite in the battery (+ the ratified battery amendment).
- `docs/VERIFICATION_ENGINE_LOG.md`: ratifications · per-wave evidence · registry census ·
  report samples · certification + handoffs.
- U6 docs: app README + `docs/apps/<app>/GUIDE.md` + index rows.
- Filled Design Record (VER-D1..VER-D9) + the SEED-D6 reconciliation record.

## 9. Files expected to change

**New (code):** the verification app tree (commands, checks, report, guard, tests) · its app
README + GUIDE. **Updated (code-adjacent):** `config/config/settings/base.py` (the ONE
base-settings edit this phase is licensed for: the app registration line — production.py and
local.py untouched unless the SEED-D6 reconciliation moves an import) · `config/.importlinter`
(layer row) · `devseed`'s assertion import IF the reconciliation lands here (the coordinated
change, own battery run). **Docs:** `docs/VERIFICATION_ENGINE_LOG.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DOCUMENTATION_INDEX.md` · framework README
(VER-D6 battery amendment, dated) · PHASE_12's Design Record (the dated SEED-D6 amendment, per
its own rules) · this file (Design Record + amendments) · memory files. **Runtime:** scratch
DBs + `var/verification_reports/`. Nothing else.

## 10. Files that must never change (touching one = STOP + report)

- EVERY existing domain app's code (models/services/views/forms/templates/tests/migrations) —
  a check that needs an app change is reporting a finding, not requesting a feature.
- Enforcement flags + their settings (U10) — the engine READS the declaration, never sets
  state; `production.py` entirely; `.env`.
- The PRIMARY dev database (census only) · the organic dev worlds · ANY production data
  (verify_production is SELECT-only by architecture — proven, §3.2).
- The Phase-12 seeder beyond the single coordinated SEED-D6 reconciliation import move.
- `docs/DEV_DATASET_ARCHITECTURE.md` (dated P11 amendments only) · `canonical_manifest.json`
  · `docs/DOC_STANDARDS.md` · T1 truth-locks · closed phase logs.
- `.claude/` tooling · the 2 stashes · `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections append-only,
corrections dated); (b) status-file Phase-13 row + dashboard (battery per wave) + "Next
action"; (c) **U6 fully applies** (new code): app README + GUIDE at VER-A, current per wave;
CHANGE_IMPACT_MATRIX per changed file; DOCUMENTATION_INDEX rows; (d) framework-README battery
amendment at VER-0; (e) the PHASE_12 SEED-D6 dated amendment recorded in BOTH Design Records
when applied.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-13
bullet: wave closed, registry counts, battery arithmetic, log pointer) + MEMORY.md index line
at each sub-phase close. Agents without memory: skip — the log + status file + machine
reports (quoted into the log where binding) are the complete record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (VER-A..VER-D) and VER-E
final**. Arithmetic: entry baseline (status dashboard at VER-0) + the verification suite's
cumulative count per wave. Suite membership = the VER-D6 framework amendment (SEED-D4
mechanism). The engine's own commands NEVER substitute for the battery (verification proves
state; the battery proves behavior — both run, neither excuses the other).

## 14. Regression policy

- Full existing battery + FoundationPurityTests green every wave = do-no-harm proof.
- The read-only purity test + guard-polarity tests are permanent pins of this phase's two
  safety properties.
- Golden values remain owner-truth (P12 §14 rule carried): a mismatch stops, never adjusts.
- Constructed-fail proofs (§3.5) guard against a verifier that can only say yes — every
  category must demonstrably catch its failure class before certification.
- Incidental app defects discovered by checks = observations → U12 backlog (+U8 stop if
  money), never fixed inline; pins-for-fixes only via the Phase-4 protocol (cross-logged).

## 15. Rollback policy

- The engine is additive + read-only: a bad wave reverts file-scoped (app tree + the two
  config lines); battery to green; report.
- Reports/scratch worlds are disposable runtime artifacts.
- The SEED-D6 reconciliation is ONE revertable coordinated diff with its own battery run on
  both sides (apply → green, or revert → green; never half-moved).
- The log + Design Record are append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests FIRST, reconciles the log,
  completes or reverts before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. VER-0 gate fails (Phase 12 not closed) or any VER-D1..D9 unanswered; SEED-D6
   reconciliation state ambiguous.
3. Any engine-code write path to any database (read-only breach — the phase's cardinal sin).
4. A check requires a new invariant, an app-code change, a migration, or a flag change
   (owner/ADR/Phase-4 territory — record, stop if pressed).
5. U8 anomaly: any money-adjacent check found WRITING (even "just normalizing") — STOP +
   report.
6. A production check's cost is unbounded or side-effectful with no SELECT-only formulation
   (defer the check with reason; owner decides).
7. Golden/spec mismatch (→ owner via dated amendments; the engine never forces).
8. Battery red beyond the wave's own new tests' target behavior; primary-dev-DB census drift.
9. Guard-polarity hole: any dev-world command executable under production settings.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-13 row: which VER-* is next; battery
   arithmetic.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env + battery amendments) →
   `docs/DEV_DATASET_ARCHITECTURE.md` (spec) → [PHASE_12_SEEDER_ENGINE.md](PHASE_12_SEEDER_ENGINE.md)
   + its log (assertions module home + manifest contract + SEED-D6 amendment state) → this
   contract → `docs/VERIFICATION_ENGINE_LOG.md` if it exists (absent ⇒ next = VER-0).
3. Verify read-only: the assertions module's actual home matches the reconciliation record;
   guard + purity tests green in THIS tree before any manual command run; scratch-DB
   allowlist; primary-dev-DB census vs anchor.
4. Never run a verify command against production-like targets until VER-C's proofs are
   closed; never against the primary dev DB at all this phase.
5. Battery environment per framework env facts; manual proofs on scratch DBs only.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / spec / P12 record / log / this contract →
   report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (VER-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| VER-D1 | Engine home + SEED-D6 reconciliation | New app `verification` in BASE settings (production-present, read-only by construction), topmost import-linter layer; the shared assertion library lives here; `devseed` imports it (dated PHASE_12 SEED-D6 amendment, applied by whichever phase executes first as one coordinated battery-run diff) | _(pending)_ |
| VER-D2 | Command/guard polarity matrix | §6.3 exactly: dev-world commands refuse prod; verify_production + verify_all run everywhere with environment-aware composition | _(pending)_ |
| VER-D3 | Production check depth | SELECT/aggregate + settings/migration introspection ONLY; no request cycle, no sessions, no logins; per-check cost noted; unbounded checks deferred | _(pending)_ |
| VER-D4 | Check-registry law | Every check cites its certified invariant (manifest rule / spec § / ADR / golden value / CheckConstraint class); uncited checks don't merge; new invariants = owner/ADR | _(pending)_ |
| VER-D5 | Report format | JSON envelope (command, versions, environment, timestamp, totals, body-hash) + deterministic sorted body; stdout human view; `var/verification_reports/`; no silent skips | _(pending)_ |
| VER-D6 | Battery membership | The verification suite joins the canonical battery (framework-README dated amendment, SEED-D4 mechanism) | _(pending)_ |
| VER-D7 | verify_all composition | Run-all-then-aggregate (no fail-fast); dev = manifest-driven worlds + production-safe subset; prod = production-safe subset only | _(pending)_ |
| VER-D8 | Deployment integration | Runbook: pre-deploy rehearsal (dev-mode verify_production) + mandatory post-deploy verify_production; Phase-21 certificate cites a green report (envelope + body-hash) as required input | _(pending)_ |
| VER-D9 | Cadence | On-demand + mandatory post-deploy; periodic/cron scheduling explicitly OUT (future owner decision; no CI wiring this phase) | **ACCEPTED (default)** |

Date · answered by: **2026-07-17 · owner, verbatim ("I accept the defaults for VER-D1
through VER-D9 exactly as proposed.") with specific rulings: VER-D1 approved exactly as
written · SEED-D6 applied as ONE coordinated change · dated amendments in BOTH Design
Records · the assertion library has exactly ONE implementation after the move · VER-D2..D9
accepted without modification. VER-0 accepted and closed; VER-A authorized same order.**
(VER-D1..D8 column values: **ACCEPTED (default)** — table cells left as authored; this
note is the answer of record.)

## Dated amendments

- **2026-07-17 — SEED-D6 reconciliation applied at VER-A** (the coordinated move per
  VER-D1): shared assertion library now lives at `verification/assertions.py`;
  `devseed` imports it; old module deleted; single-implementation + spec-version cross-pin
  enforced by `verification.tests.test_shared_library`. Mirror record: PHASE_12 Appendix A.
- **2026-07-17 — VER-D6 battery amendment recorded** in the framework README:
  `verification` = the FOURTH sequential canonical-battery member.

# Evidence note

All implementation evidence lives in `docs/VERIFICATION_ENGINE_LOG.md` (created at VER-0) —
contract = procedure, log = what was built and proven (framework hierarchy rule). Machine
reports are runtime artifacts (`var/`); binding results are quoted into the log or the
deployment records that cite them.
