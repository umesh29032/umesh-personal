---
id: docs-verification-engine-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# VERIFICATION ENGINE LOG — Campaign Phase 13 (append-only evidence)

> Contract: [campaign_contracts/PHASE_13_VERIFICATION_ENGINE.md](campaign_contracts/PHASE_13_VERIFICATION_ENGINE.md)
> (frozen; Design Record = its Appendix A). Spec inherited: 🔒
> [DEV_DATASET_ARCHITECTURE.md](DEV_DATASET_ARCHITECTURE.md) (v1.0.0 frozen-v1) + the
> Phase-12 artifacts ([SEEDER_ENGINE_LOG.md](SEEDER_ENGINE_LOG.md), 🏁 closed 2026-07-17).
> **Owner designation (2026-07-12): this engine = the PERMANENT deployment-verification
> instrument** (Phases 19–21 + post-campaign operations consume it).

## VER-0 — Charter + gate + ratification — ⏸ DECISION PACK PENDING OWNER (opened 2026-07-17)

### 1. Gate — Phase 12 closed correctly — ✅ PASS (re-verified live this session)

| Gate item | Proof |
|---|---|
| Phase 12 verdict on record | SEEDER_ENGINE_LOG §SEED-F.7: "PHASE 12 COMPLETE — SEEDER ENGINE CERTIFIED" (owner-accepted; SEED-D/E/F all owner-accepted + closed) |
| Assertions module live | `config/devseed/assertions.py` exists (spec §6.1.7 single source; public surface `run_post_seed` + `SeedAssertionError`) |
| Manifests live | `var/seed_manifests/` = 228 machine-readable manifests incl. 6 reset manifests (format = SEEDER_ENGINE_LOG §SEED-F.5.1, the verify input contract) |
| Registry live | `devseed.scenarios.SCENARIOS` — 24 slugs / 6 classes / 22 implemented (pinned by devseed test_guard) |
| Battery entry baseline | **1600/1600** — FINAL Phase-12 baseline (9-app 1002 + patterns_ai 528 + devseed 70), re-verified at SEED-F close this same session |
| Primary-dev-DB census anchor | **Fresh read-only capture at VER-0: ALL 34 anchor counts EXACT + ledger Σ ₹10,880.25** (anchor table = SEEDER_ENGINE_LOG §2b; zero drift) |
| Engine home is VACANT | `verification` appears NOWHERE: `config/config/settings/base.py` 0 hits · `config/.importlinter` 0 hits · no app tree — no naming collision, VER-D1 default buildable |

### 2. SEED-D6 reconciliation state — UNAMBIGUOUS (stop-condition §16.2 satisfied)

**Current state: NOT YET APPLIED.** The shared assertions library lives in
`config/devseed/assertions.py` (dev-only app); `.importlinter` shows `devseed` topmost with
no `verification` layer. Phase 13 is the FIRST executor of the reconciliation → per both
contracts, **VER-A applies it as ONE coordinated battery-run diff** (create `verification`
app in BASE settings → move the shared library into it → `devseed` imports it →
import-linter layer updated → dated amendments recorded in BOTH Design Records, PHASE_12
Appendix A + PHASE_13 Appendix A). Rollback = the same single diff reverted (contract §15).

### 3. Charter enumerations (VER-0 deliverable — read-only, nothing implemented)

#### 3.1 Verification surfaces (what the engine will prove, per §6.4 categories)

1. **Seeded DEV worlds** (allowlisted scratch DBs only): the demo world · the factory
   composite (3 golden worlds + machines slice) · the 20 feature/edge worlds — each
   manifest-required (absent manifest = refusal naming `seed_*` as remedy).
2. **Golden regression truth (byte-match):** ₹344.25 (LOWER/ADST-class) · ₹801.00 (T-SHIRT)
   · ₹633.00 (3-PATTI) + per-worker items · ₹150.00 (feature-settlement, self-derived).
   **₹225 = HISTORICAL only (spec §12 A1)** — never an executable verify target; its living
   guard stays the settlement suite's on-disk goldens.
3. **Production DB state (SELECT/aggregate only):** DEV-contamination absence (spec §4
   namespace: `dev.*@test.local` · `DEV-*` · `dev-*`) · self-consistency integrity
   (settlement items Σ = totals · ledger reversal pairs net · CheckConstraint-shaped
   predicates re-checked in SQL · single-writer sanity where READ-detectable).
4. **Configuration truth:** `ENFORCE_ALLOCATION_BOUND` / `ENFORCE_SETTLEMENT_RECONCILIATION`
   == owner-DECLARED expected state (U10: OFF until R11 — declaration is an input, changed
   only by owner) · migrations applied = migration files · settings sanity (DEBUG False in
   prod-mode report; secret PRESENCE, never value).
5. **Smoke (dev modes only):** app registry loads · URLConf route-count vs the census
   instrument · critical pages render 200 via test client AS cast identities on scratch
   worlds (the ONLY place the request cycle is permitted).

#### 3.2 Assertion sources (every one, with its authority)

| Source | Content | Authority |
|---|---|---|
| `config/devseed/assertions.py` | `run_post_seed(expected_counts, handles, output_handles, dev_prefixes)`: exact filtered row-counts · minted-handle existence + DEV-marking · service-issued output handles existence-only · enforcement-flags-untouched; `SeedAssertionError` | spec §6.1.7 — THE single source; relocates at VER-A (SEED-D6); P13 imports-never-forks |
| Golden constants | registry `expected` fields (344.25/801.00/633.00) · `test_golden_journeys.GOLDEN` + `EXPECTED_ITEMS` (per-worker extracted truth) · `minimal_money` ₹150 self-derived config | owner business truth (spec §7 change-control; mismatch = STOP, never adjust) |
| Spec §7 / §4 / §11 | per-class assertion definitions · DEV-namespace schemes · reserved-handle registry + collision law | 🔒 frozen-v1 spec |
| MANUFACTURING_V1 freeze manifest | `never_modify` / `hard_rules` (single-writer walls · never-edit-money-rows · settlement = only money boundary) | 🔒 freeze package (docs/MANUFACTURING_V1_FREEZE.md) |
| CheckConstraints record | 26+ DB CheckConstraints (DB-Integrity PR1+PR2, 2026-06-06) | migration-encoded; verify re-checks constraint-SHAPED predicates in SQL |
| ADR-0009 / ADR-0011 | cost-truth (no summing worker earnings into product cost) · monthly salary = factory-level, never per-Adda | 🔒 ADRs |
| U10 flag policy | both ENFORCE_* flags owner-declared OFF | campaign framework invariant |
| MGT-C lesson | self-consistency predicates, NEVER point-in-time constants (170/₹10,880.25 = a session baseline, not an eternal truth) | contract §2.1 row 6 |

#### 3.3 Manifest sources

- **`var/seed_manifests/`** (gitignored runtime; 228 today): scenario manifests
  `{scenario, spec_version, database, max_layer, counts, handles, assertions, money|null,
  post|null, ran_at}` · factory composite adds `composite{child: {counts, money,
  assertions}}` · reset manifests `{scenario: "reset-<db>", reset, spec_version, migrated,
  seeded|null, ran_at}`. Format of record: SEEDER_ENGINE_LOG §SEED-F.5.1.
- **Producers:** `devseed.core.seed_scenario` + `devseed.core.run_reset` via the four seed
  commands — the verify engine NEVER produces manifests (it may REQUIRE them).
- **Comparator:** `devseed.core.strip_volatile` (`ran_at` = the only volatile key; cross-DB
  additionally strips DB-identity keys).
- **Version pin:** `devseed.guard.SPEC_VERSION` ("1.0.0") ⇄ spec §10 semver.

#### 3.4 Registry sources

- **Existing (consumed):** `devseed.scenarios.SCENARIOS` — machine-readable, 24 slugs,
  6 classes, implemented/deferred/historical flags + golden values + notes; four-surface
  agreement pinned by devseed tests. `verify_feature <slug>` validates against it;
  non-executable entries must REFUSE in verify too.
- **New (built this phase):** the CHECK registry (`checks/` — one module per §6.4 category;
  each check a pure function → CheckResult carrying its citation) — machine-readable by
  design; it is the Phase-14 interface and the §3.4 completeness-census object (every §3.2
  source row → check or deferred-with-reason).

#### 3.5 Owner decisions required (ALL of them — none assumed)

Exactly the contract's Appendix-A pack: **VER-D1..VER-D9** (presented in §4 below with
binding defaults). No additional decisions identified at charter — one clarifying NOTE
attached to VER-D6 (battery-suite placement) that stays within its default.

#### 3.6 Implementation waves (contract §7 — one session each, STOP after)

| Wave | Builds | Battery-bearing |
|---|---|---|
| VER-A | app skeleton + BASE-settings registration + import-linter layer + guard polarity + **read-only purity test BEFORE any check logic** + command shells + report scaffolding + **the SEED-D6 coordinated move** | ✅ |
| VER-B | dev-world commands (manifest ingestion · shared-assertion invocation · smoke · golden byte-match) + pass/constructed-fail proofs per category | ✅ |
| VER-C | verify_production (contamination scan w/ planted-handle fail proof · flags-vs-declaration · migrations · integrity) + verify_all composition + runtime read-only proof (pre/post row-count identity) | ✅ |
| VER-D | determinism body-hash pairs · report samples archived · `--skip` transparency · exit-code matrix | ✅ (if fixes) |
| VER-E | registry completeness census · handoffs (14/15/19-21) · final battery · primary untouched proof · PHASE-13 VERDICT | final |

#### 3.7 Battery additions (arithmetic plan)

Entry baseline **1600/1600**. Additions land per wave (VER-A guard-polarity + read-only
purity + skeleton tests → VER-B dev-world check tests → VER-C production-subset +
planted-handle tests → VER-D determinism tests); the devseed suite keeps its 70 (SEED-D6
changes an import path, never a count). Suite membership + sequential-run placement =
VER-D6 (framework-README dated amendment on ratification). The engine's commands NEVER
substitute for the battery (state ≠ behavior, contract §13).

#### 3.8 Documentation touchpoints

THIS log (created now, append-only) · app README + `docs/apps/verification/GUIDE.md`
(VER-A, then current per wave) · `DOCUMENTATION_INDEX.md` rows (log row added at VER-0;
app rows at VER-A) · `CHANGE_IMPACT_MATRIX.md` row (VER-A) · framework README battery
amendment (dated, on VER-D6 ratification) · PHASE_12 + PHASE_13 Design Records (dated
SEED-D6 amendment in BOTH when applied at VER-A) · `DEPLOYMENT_CAMPAIGN_STATUS.md` +
campaign memory (every sub-phase close) · SEEDER_ENGINE_LOG untouched (closed; the
amendment lives in the Design Records, not the closed log).

#### 3.9 Phase interfaces

| Phase | Interface |
|---|---|
| 12 (closed) | consumes: assertions module (relocating) · manifest contract · scenario registry · scratch-DB law · DEV-namespace schemes; the ONE licensed devseed touch = the SEED-D6 import move |
| 14 knowledge_sync | the machine-readable CHECK registry + report format = shared conventions; boundary: 13 verifies DATA/CONFIG state, 14 detects CODE⇄DOCS⇄GRAPH drift — no overlap, same detect-and-notify law |
| 15 BOD | dashboard DISPLAYS latest `var/verification_reports/` artifacts; never runs checks inline |
| 19–21 deployment | runbook: pre-deploy rehearsal (dev-mode verify_production) + MANDATORY post-deploy verify_production; Phase-21 readiness certificate CITES a green report (envelope + body-hash) as required input — permanent-instrument designation |
| U10 owner declaration | the flags-expected-state input the production-safety check reads (owner-changed only) |

### 4. ⏸ Decision pack — VER-D1..VER-D9 (defaults binding unless overridden; → contract Appendix A)

| # | Decision | Default in one line | Charter notes |
|---|---|---|---|
| VER-D1 | Engine home + SEED-D6 reconciliation | New app **`verification`** in BASE settings (production-present, read-only by construction), topmost import-linter layer; shared assertion library LIVES here; `devseed` imports it — applied at VER-A as ONE coordinated battery-run diff + dated amendments in both Design Records | reconciliation state verified unambiguous (§2: not yet applied; P13 = first executor). The ONE base.py edit this phase is licensed for |
| VER-D2 | Command/guard polarity | §6.3 exactly: dev-world commands refuse prod; `verify_production`/`verify_all` run everywhere, environment-aware | inverse polarity vs devseed factor 5 — needs its OWN guard module (structural absence can't protect a production-present app) |
| VER-D3 | Production check depth | SELECT/aggregate + settings/migration introspection ONLY; no request cycle/sessions/logins; per-check cost noted; unbounded checks deferred-with-reason | sessions are writes — the §2.1 hazard row |
| VER-D4 | Check-registry law | every check cites its certified invariant (manifest rule · spec § · ADR · golden value · CheckConstraint class); uncited ⇒ no merge; new invariant = owner/ADR | citation sources enumerated §3.2 |
| VER-D5 | Report format | JSON envelope (command, versions, environment, timestamp, totals, body-hash) + deterministic sorted body; stdout human view; `var/verification_reports/`; no silent skips (`--skip` prints into the report) | body-stable determinism = the VER-D wave proof |
| VER-D6 | Battery membership | verification suite joins the canonical battery via a dated framework-README amendment (SEED-D4 mechanism) | NOTE (within default): placement = 4th sequential fresh-DB member (9-app → patterns_ai → devseed → verification), mirroring the D4 precedent |
| VER-D7 | verify_all composition | run-all-then-aggregate (no fail-fast); dev = every manifest-present world + the production-safe subset; prod = production-safe subset only | |
| VER-D8 | Deployment integration | runbook pre-deploy rehearsal + MANDATORY post-deploy verify_production; Phase-21 certificate cites a green report (envelope + body-hash) as required input | the permanent-instrument designation (owner 2026-07-12) |
| VER-D9 | Cadence | on-demand + mandatory post-deploy; periodic/cron scheduling explicitly OUT (future owner decision; no CI wiring) | |

**Rulings requested. On ratification:** answers land in the contract's Appendix A (dated),
the VER-D6 framework-README amendment is recorded, and VER-A is authorized (next session,
owner-gated).

### 5. VER-0 accounting

Zero code written · zero production/devseed files touched · primary-dev-DB read-only census
only · battery NOT re-run (no code change; entry baseline = the SEED-F final 1600/1600,
same session) · git `49404001` · 0 staged · 2 stashes.

## VER-0 ratification — owner 2026-07-17 (verbatim)

> "I accept the defaults for VER-D1 through VER-D9 exactly as proposed." Specific rulings:
> VER-D1 approved exactly as written · SEED-D6 applied as ONE coordinated change · dated
> amendments in BOTH Design Records · **"The assertion library must have exactly one
> implementation after the move."** · VER-D2..D9 accepted without modification. VER-0
> accepted and closed; VER-A authorized.

Recorded: PHASE_13 Appendix A (decision half filled, dated) · VER-D6 battery amendment →
framework README (verification = 4th sequential member).

## VER-A — Skeleton + guards + read-only purity + SEED-D6 move — ✅ DONE 2026-07-17 · BATTERY 1628/1628

### 1. What landed

| Piece | Content |
|---|---|
| `config/verification/` (NEW app) | `apps.py` (modelless/migrationless/URL-less) · `guard.py` (VER-D2 polarity: pure functions + gather; dev-world commands refuse outside `config.settings.local`+DEBUG; everywhere-commands never environment-refuse) · `report.py` (VER-D5 scaffolding: `CheckResult` w/ mandatory citation · envelope[engine 0.1.0 · spec 1.0.0 · totals · body-hash · the ONLY timestamp] + deterministic sorted body · writer → `var/verification_reports/` · stdout renderer · exit-code law) · `checks/__init__.py` (registry scaffold, 5 §6.4 categories — NO check logic by design) |
| 5 command skeletons | `PolarityCommand` base (banner → polarity → wave gate "not implemented until VER-B/C, zero checks run, zero writes possible") + common `--report`/`--skip` flags; `verify_feature` validates its slug lazily against the devseed registry AFTER polarity (devseed absent in prod, where it refuses anyway) |
| **Read-only purity suite — LANDED FIRST** | 7 permanent tests: zero ORM writes · zero queryset/instance mutations · zero write-verb raw SQL · **zero transaction management** (a read-only engine needs none — stricter than devseed's service-path purity) · modelless shape pin · BASE-settings presence pin |
| Polarity tests | 11: the §6.3 matrix cell-by-cell (incl. whole-wall never-short-circuit + disjoint-and-complete class pins) + command-level: dev-world commands REFUSE under the test env (DEBUG False = the standing can't-touch-battery-DBs proof); `verify_production`/`verify_all` pass polarity → wave gate |
| Report tests | 6: body sorted + timestamp-free · body-hash deterministic across runs / sensitive to measured state · totals + exit codes (0 green, N reds) · explicit-skip envelope · disk round-trip |
| **SEED-D6 coordinated move** | `devseed/assertions.py` → `verification/assertions.py` (content behavior-identical, docstring re-homed); 3 devseed import sites updated (`core.py` ×2 · `tests/test_reset.py`); **old module DELETED — no shim** (owner: exactly one implementation); pinned by 5 `test_shared_library` tests (library home · devseed consumes the SAME object (`core.run_post_seed is verification.assertions.run_post_seed`) · exactly one `def run_post_seed` in the whole config tree · old module gone · SPEC_VERSION cross-pin verification⇄devseed) |
| Licensed config edits (the only two) | `config/config/settings/base.py`: +`'verification'` in INSTALLED_APPS · `config/.importlinter`: +root package, +layer directly below devseed, +4 sanctioned ignore rules (test-only single-implementation proof edges + verify_feature's function-level lazy registry read — the R10 sanctioned-function-level precedent) |
| Amendments recorded | framework README (VER-D6, dated, 4th battery member) · PHASE_12 Appendix A (SEED-D6 applied, dated) · PHASE_13 Appendix A (decision half filled + 2 dated amendments) |

### 2. Proofs

- **Suites first-run green post-move:** verification 28/28 + devseed 70/70 (one combined
  run, 98/98) — the coordinated diff proven on both sides in one battery pass.
- **Import-linter:** foundation-purity KEPT; acyclic-layers = the identical PRE-EXISTING
  report-only worklist (raw_materials→tracking · production.tests→inventory), **zero
  verification/devseed rows** after the 4 sanctioned ignores.
- **Single implementation:** `devseed/assertions.py` gone; `grep def run_post_seed` →
  exactly `verification/assertions.py` (test-pinned forever).
- **Canonical battery — NEW BASELINE 1628/1628** (4 sequential fresh-DB suites, first run
  of the VER-D6 shape): 9-app `Ran 1002 — OK` (187.1s) + patterns_ai `Ran 528 — OK`
  (141.5s) + devseed `Ran 70 — OK` (26.9s) + verification `Ran 28 — OK` (0.04s).
  Arithmetic: 1600 + 28 ✓. (Inline `get_runner` invocation class — disclosed, same as
  every Phase-12/13 run.)
- **Primary untouched:** ledger 170 / Σ ₹10,880.25 · settlements 8 · addas 18 · rolls 32 ·
  users 48 · `dev.min.*` = 0. Git `49404001` · 0 staged · 2 stashes.
- Zero domain-app code touched · zero migrations · flags untouched · devseed touched ONLY
  at the three licensed import sites + module deletion (the coordinated diff).

**Next: VER-B — dev-world verification (manifest ingestion · shared-assertion invocation ·
smoke · golden byte-match · pass/constructed-fail proofs) — owner-gated.**

_VER-A closed 2026-07-17._

## VER-B — Dev-world verification — ✅ DONE 2026-07-17 · BATTERY 1645/1645

**Owner authorization (2026-07-17):** dev-world layer only — no production verification, no
production-code/devseed edits. Honored: devseed untouched; engine v0.1.0 → **0.2.0**.

### 1. What landed

| Piece | Content |
|---|---|
| `manifests.py` | Manifest ingestion: `latest_manifest(slug)` (newest by embedded UTC stamp) from repo-root `var/seed_manifests/`; `ManifestMissing` refusal names the exact seeder remedy ("run `manage.py seed_demo` … the verification engine never seeds") |
| `checks/dev_world.py` | The dev-world check registry (every check CITED, VER-D4). **golden category:** manifest spec-version pin (spec §10) · database-match (SEED-D5 — verify THE world the manifest describes) · recorded post-seed assertions (P12 §6.5) · **LIVE shared-assertion re-run** (`verification.assertions.run_post_seed` — the SEED-D6 single implementation — over `devseed.core.expected_counts/scenario_handles`, drift-since-seed = red) · **golden settlement totals** (certified sources ONLY: registry `expected` → scenario config → recipe `journey.golden`; ZERO literals in the engine, test-pinned) · **certified worker-item truth** (single source: the extracted SEED-C W2 maps). **smoke category (dev-only):** app registry · URLConf (critical routes reverse) · critical renders 200 (anon public/login + dashboard AS the world's SA cast identity — the contract-sanctioned request-cycle territory; writes session rows on the TARGET world, disclosed). Composite-aware (factory → per-child checks, `dev.child.<slug>.…` ids). `feature_slug_failure` = registry validation (unknown → lists; non-executable → registry note) |
| Commands | `DevWorldVerifyCommand` (in `_base`): polarity → manifest-REQUIRED → checks → deterministic report (`build/write/render`) → exit code (0 green; red ⇒ CommandError, count in envelope, "the engine never fixes"). `verify_demo`/`verify_factory` = slug-fixed; `verify_feature <slug>` validates post-polarity. New `--manifest-dir` flag (ops/test override, documented) |
| `.importlinter` | +5 sanctioned function-level/test-only edges (checks.dev_world → devseed.core/scenarios/tests.test_golden_journeys · test_dev_world → devseed) — dev-only checks; polarity refuses wherever devseed is absent |
| Tests (+17 → verification suite 45) | green demo run (all pass · citations present · exit 0 · golden consumed FROM `MINIMAL_MONEY` config) · determinism (body-hash equal ×2) · explicit-skip proof · **constructed fails per category** (tampered spec-version · database mismatch · world drift caught by the assertion re-run [renamed master] · tampered golden total 151.00 → red + nonzero exit · unresolvable route · missing cast identity) · regression world (₹633.00 + items green; tampered item 999.00 → red) · **factory composite (all three goldens + items + child re-runs green in one pass)** · manifest refusals (remedy names seeder ×3 shapes; newest-wins) · slug validation · **single-source pins** (zero golden literals in engine source [static] · re-run check provably calls the SEED-D6 library) |

### 2. Live command proofs (the real commands, scratch worlds — the P12 pattern)

- **Green (scratch_2, the SEED-F full-registry world):** `verify_demo` → `totals: pass=8
  fail=0 skip=0` · `verify_factory` → `pass=19 fail=0` (3 goldens + 3 item-maps + 4 child
  assertion re-runs + machines child) · `verify_feature feature-settlement` → `pass=8
  fail=0`. Exit 0 each.
- **Read-only runtime proof:** full model row-count census before/after the 3 runs —
  **byte-identical EXCEPT `sessions.Session` 0→3** (one per smoke force-login render; the
  §6.4-sanctioned dev-mode request cycle, disclosed; scratch-world-only).
- **Determinism live:** `verify_demo` ×2 on the unchanged world → **identical body_hash**
  (`3bc1825a745e886e…`).
- **Refusals live:** `verify_feature regression-settlement-225` → "not executable/verifiable:
  historical-evidence-only…" · missing manifest (`--manifest-dir` empty) → "MANIFEST
  REQUIRED… run `manage.py seed_demo`… the verification engine never seeds."
- **Constructed fail live (no mutation needed):** `verify_demo` against scratch_1 (whose
  world ≠ the latest manifest's DB) → exactly `dev.manifest.database-match` FAIL (SEED-D5
  citation) + nonzero exit — the wrong-target wall works verbatim.

### 3. Certification

- Import-linter: foundation KEPT · acyclic = pre-existing report-only worklist · zero
  verification rows.
- **Battery — NEW BASELINE 1645/1645** (4 sequential fresh-DB suites): 9-app 1002 (187.6s)
  + patterns_ai 528 (159.1s runner-total) + devseed 70 + verification 45 (28.0s).
  Arithmetic: 1628 + 17 ✓. Purity pins green (the read-only suite runs unchanged).
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · settlements 8 · addas 18 · rolls 32 ·
  users 48 · dev.min 0. Git `49404001` · 0 staged · 2 stashes · devseed/production code
  untouched · zero migrations.

**Next: VER-C — verify_production + verify_all (contamination scan w/ planted-handle proof ·
flags-vs-declaration · migrations · integrity self-consistency · composition · runtime
read-only proof) — owner-gated.**

_VER-B closed 2026-07-17._

## VER-C — verify_production + verify_all — ✅ DONE 2026-07-17 · BATTERY 1665/1665

**Owner authorization (2026-07-17):** production verification only — no VER-D, no
production-service/devseed edits. Honored. Engine v0.2.0 → **0.3.0**.

### 1. What landed

| Piece | Content |
|---|---|
| `checks/production.py` | The production-safe subset (VER-D3: SELECT/aggregate + settings/migration introspection ONLY; cost noted per check — bounded COUNT/SUM aggregates). **dev-contamination:** 10 identifier-bearing columns × the spec-§4 reserved namespace (`dev.*`/`@test.local` emails · `DEV-`/`dev-` codes/names across production/raw_materials/machines/storefront); red in prod-mode, informational-with-counts in dev rehearsal. **production-safety:** flags-vs-OWNER-DECLARATION (U10 — `OWNER_DECLARED_FLAGS` both False; post-R11 flips update the DECLARATION, never the check) · migrations-consistent (no unapplied via executor plan; no applied-but-unknown vs disk) · settings-sanity (DEBUG off in prod-mode; secret PRESENCE never value). **integrity (self-consistency, NEVER point-in-time constants — the MGT-C law):** Σ(items.expected_earning)==expected_total per finalized settlement (ARCHITECTURE_V2 §11) · ledger reversal pairs net (amount == reversed amount, §11.5) · CheckConstraint-shaped re-checks in SQL (ledger amount>0 · WSC gam nonneg, prod 0039) · supersession-chain (superseded ⇒ successor). `_plan`/`_violators` injection = constructed-fail-only (a live DB refuses violating rows — the run_reset precedent) |
| `checks/compose.py` | verify_all composition (VER-D7, run-all-then-aggregate, NO fail-fast): dev = every MANIFEST-PRESENT implemented world (ids `world.<slug>.…`) + the production-safe rehearsal; prod = subset only; `all.composition` summary result lists verified AND manifest-absent worlds — nothing silent |
| `guard.environment()` | The report-environment classifier: 'dev' = dev settings module + DEBUG; anything else 'prod' (battery classifies prod — exactly what makes prod-mode checks testable there) |
| Commands LIVE | `verify_production` (subset → report env-stamped → exit code) · `verify_all` (compose → aggregate report; `--manifest-dir` pass-through). Both refuse-free everywhere (polarity §6.3) |
| Tests (+22, −2 reworked wave-gate pins → suite 65) | green prod verification on a clean DB (+ command-level green for BOTH commands — the battery env classifies prod, so these run END-TO-END in the battery) · **planted `dev.planted@test.local` → contamination red + whole-command CommandError; dev rehearsal reports the same hits informationally** · flag mismatch (`override_settings` True → red) · migration mismatch (injected unapplied + unknown → red; live consistency green) · settings-sanity red on DEBUG-in-prod-mode · integrity: items-sum tamper 151.00 → red (green on the real world) · reversal/constraint fails via injection · supersession-chain green on the superseded world · **runtime read-only proof: STRICT full-model row-count identity around the subset (both env modes — this subset never touches the request cycle)** · composition: prod = subset-only ids · dev = manifest-driven (one manifest ⇒ exactly that world verified; absent worlds LISTED) · no-fail-fast (red aggregates, summary still present) |

### 2. Live proofs (scratch worlds; primary never a target)

- **DEV-clean prod-mode integrity/contamination/migrations (fresh reset scratch_1):**
  contamination 0-hit pass · migrations pass · integrity ×5 pass · **STRICT read-only
  row-count identity TRUE** · the one red = `prod.safety.settings-sanity` — correctly
  REFUSING a DEBUG-on environment posing as 'prod' (a live constructed-fail of the sanity
  check working as designed; true prod-mode green is battery-proven where DEBUG is off).
- **Dev rehearsal (scratch_2, real command):** `verify_production` → **`pass=9 fail=0`**,
  contamination PASS-informational over the DEV-full world.
- **verify_all dev (scratch_2, real command):** **`pass=180 fail=0`** — all 21
  manifest-present worlds + the rehearsal subset + the composition summary in ONE
  aggregate; row-census identical except `sessions.Session` +21 (one smoke render per
  world — the §6.4-sanctioned request cycle, disclosed).
- **Prod-mode contamination catch at scale (scratch_2):** forced prod-mode scan over the
  DEV-full world → **FAIL with hits across all 10 scanned columns** (Users 20 · Products 11
  · Addas 9 · Stage 1 · ClothType/Color 19/19 · Storage 17 · Machine 1 · storefront 1/1) —
  the planted-scan works at scale, not just on a single planted row.

### 3. Certification

- Import-linter: +2 sanctioned edges (compose → registry, function-level dev-only ·
  test fixture) — zero verification rows in the report-only worklist; foundation KEPT.
- **Battery — NEW BASELINE 1665/1665** (4 sequential fresh-DB suites): 9-app 1002 (188.3s)
  + patterns_ai 528 (157.5s) + devseed 70 (44.0s) + verification 65 (12.6s). Arithmetic:
  1645 − 2 (reworked VER-A wave-gate pins) + 22 = 1665 ✓. Read-only purity pins green.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0. Git `49404001` ·
  0 staged · 2 stashes · production services + devseed untouched · zero migrations.

**Next: VER-D — determinism + report certification (body-hash pairs per command · report
samples archived · `--skip` transparency · exit-code matrix) — owner-gated.**

_VER-C closed 2026-07-17._

## VER-D — Determinism + report certification — ✅ DONE 2026-07-17 · ENGINE 1.0.0 · BATTERY 1678/1678

**Owner authorization (2026-07-17):** certification only — no new capabilities, no
production-service/devseed edits, checks untouched (none required changes — zero
nondeterminism found). **Engine version certifies to 1.0.0** (the report schema is now
CERTIFIED: changing any certified key set = a new engine version + a dated Design-Record
amendment — `tests/test_certification.py` is the permanent tripwire).

### 1. What landed (tests + the version stamp ONLY)

`tests/test_certification.py` (+13 → suite 78):
- **Report schema certification:** envelope keys exactly `{command, engine_version,
  spec_version, environment, totals, skipped_categories, body_hash, ran_at}` · body rows
  exactly `{id, citation, category, status, measured}` · statuses/categories = closed sets ·
  body sorted + duplicate-free · citation non-empty on every row · **body-hash recomputed
  INDEPENDENTLY of the engine** (sha256 over compact sorted-keys body JSON) · the only
  timestamp lives in the envelope · totals arithmetic — certified across all three report
  shapes (production subset · dev world · composition).
- **Determinism pairs per command shape:** demo · factory · feature-settlement ·
  production (both env modes) · compose (both modes) — body-hash equal ×2 each.
- **Exit-code matrix:** 0 green · 1→1 · 7→7 · 300→250 (shell-safe cap) · command-level:
  green completes, planted red raises with the count.
- **--skip transparency:** command-level `--skip integrity` → envelope records it, body
  carries zero integrity rows, stdout prints "skipped categories (explicit)"; no silent
  skip mechanism exists; on-disk report content-identical to the built report.

### 2. Live certification — the five real commands, ×2 each (scratch_2, unchanged world)

| Command | totals | body_hash pair | Note |
|---|---|---|---|
| verify_demo | pass=8 fail=0 | `3bc1825a745e886e…` ×2 ✅ | same hash as the VER-B session — **cross-session determinism** |
| verify_factory | pass=19 fail=0 | `05489fea4f14b274…` ×2 ✅ | cross-session identical |
| verify_feature feature-settlement | pass=8 fail=0 | `f7f01ee60efba6e4…` ×2 ✅ | cross-session identical |
| verify_production (dev rehearsal) | pass=9 fail=0 | `df2ae5a2d2c97c5a…` ×2 ✅ | cross-session identical |
| verify_all (dev) | pass=180 fail=0 | `41aa7d3acd1d2d46…` ×2 ✅ | 21 worlds + rehearsal + summary |

The body hash excludes the envelope (engine version bump 0.3.0→1.0.0 did not move any
body hash) — exactly the certified design: determinism lives in the MEASURED STATE.

### 3. Archived canonical report samples (quoted; `var/` stays runtime)

**verify_demo — full body ids (8):** `dev.assertions.rerun · dev.golden.settlement-total ·
dev.manifest.assertions-recorded · dev.manifest.database-match · dev.manifest.spec-version ·
dev.smoke.app-registry · dev.smoke.render-critical · dev.smoke.urlconf` — envelope:
```json
{"body_hash": "3bc1825a745e886e6de9626d33c06a658c889373a0c79bbabf1c49e366fbcf69",
 "command": "verify_demo", "engine_version": "1.0.0", "environment": "dev",
 "ran_at": "<runtime>", "skipped_categories": [], "spec_version": "1.0.0",
 "totals": {"fail": 0, "pass": 8, "skip": 0}}
```
**verify_production — full body (9, all pass):** `prod.contamination.dev-namespace ·
prod.integrity.constraint-ledger-amount-positive · prod.integrity.constraint-wsc-gam-nonneg ·
prod.integrity.ledger-reversals-net · prod.integrity.settlement-items-sum ·
prod.integrity.supersession-chain · prod.safety.flags-vs-declaration ·
prod.safety.migrations-consistent · prod.safety.settings-sanity` — envelope:
```json
{"body_hash": "df2ae5a2d2c97c5ac37498776546c4bbf9a26801361b173b016770243e762c9a",
 "command": "verify_production", "engine_version": "1.0.0", "environment": "dev",
 "ran_at": "<runtime>", "skipped_categories": [], "spec_version": "1.0.0",
 "totals": {"fail": 0, "pass": 9, "skip": 0}}
```
**verify_factory:** totals pass=19 · `05489fea4f14b2741a94e39592629ca21134b7051340f7a6c8fc0793d89246bb`.
**verify_feature feature-settlement:** totals pass=8 · `f7f01ee60efba6e47bef594f332474c97e90f1e4761a25db5506330db409dae8`.
**verify_all (dev):** totals pass=180 · `41aa7d3acd1d2d4644a66d795a066ca345da169a659eb9bd23b8c8b1e32e1b6f`;
`all.composition.worlds_verified` = the 21 implemented slugs (registry order), absent = [].

### 4. Certification

- **Battery — NEW BASELINE 1678/1678** (4 sequential fresh-DB suites): 9-app 1002 (183.9s)
  + patterns_ai 528 (159.3s) + devseed 70 (42.7s) + verification 78 (21.0s). Arithmetic:
  1665 + 13 ✓. Read-only purity suite green (unchanged).
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0.
- **Production services unchanged this phase:** the wave's edit list = `report.py`
  version stamp + `tests/test_certification.py` (+docs) — no check logic, no domain app,
  no devseed, zero migrations. Git `49404001` · 0 staged · 2 stashes.

**Next: VER-E — certification + handoffs (registry completeness census · §6.6 handoffs
incl. the Phase-19 runbook step + Phase-21 certificate input format · U6 docs · PHASE-13
VERDICT) — owner-gated.**

_VER-D closed 2026-07-17._

## VER-E — Certification + handoffs — ✅ DONE 2026-07-17 · 🏁 PHASE 13 CLOSED

**Owner authorization (2026-07-17):** close-out only — no new functionality/checks/report
changes, no production/devseed edits. Honored: this wave's engine edits = THREE stale-
docstring reconciliations + one dead-attribute removal (zero behavior change; the safety-net
refusal in the command base reworded honestly; suites re-proven green below).

### 1. Registry completeness census (contract §3.4 — counted, not asserted)

**19 check ids** across the 5 §6.4 categories (dev-world 9: 6 golden-class + 3 smoke ·
production 9: 1 contamination + 3 safety + 5 integrity · composition summary 1). Every
§2.1 certified-invariant source accounted:

| Invariant source | Codified as | Status |
|---|---|---|
| Spec §7 golden ₹ values (150.00 · 344.25 · 633.00 · 801.00 + worker items) | `dev.golden.settlement-total` + `dev.golden.worker-items` (values from certified sources; zero literals) | ✅ codified |
| ₹225 invariant | — | ⏸ HISTORICAL by owner ruling (spec §12 A1); living guard = the settlement suite's on-disk goldens; `verify_feature` refuses the slug |
| Spec §6.1.7 assertion definitions (counts · handles · DEV-marking · flags) | `dev.assertions.rerun` via the SEED-D6 single library | ✅ codified |
| Seed-manifest contract (SEED-F.5.1) | `dev.manifest.spec-version` / `database-match` / `assertions-recorded` | ✅ codified |
| U10 flag policy | `prod.safety.flags-vs-declaration` (OWNER_DECLARED_FLAGS = the input) + the flags-untouched leg of the shared assertions | ✅ codified |
| DEV-namespace reservation (spec §4 / DATA-D8) | `prod.contamination.dev-namespace` (10 columns) + the DEV-marking leg of the shared assertions | ✅ codified |
| Freeze-manifest settlement math (§11: items Σ = totals; settlement = only money boundary) | `prod.integrity.settlement-items-sum` | ✅ codified |
| Correction truth (§11.5 never-edit → reverse/supersede) | `prod.integrity.ledger-reversals-net` + `prod.integrity.supersession-chain` | ✅ codified |
| 26+ CheckConstraints record (PR1+PR2) | 2 representative SQL re-checks (`ledger-amount-positive` · `wsc-gam-nonneg`) | ✅ codified (2) + **24 deferred-with-reason:** PG enforces every CHECK constraint continuously on every write; a bypass (superuser raw SQL) defeats all 26 equally, so the representatives prove the re-check MECHANISM without unbounded per-table cost (VER-D3) |
| Single-writer walls (rule 5 / freeze hard_rules) | — | ⏸ deferred-with-reason: writer IDENTITY is not present in data (not READ-detectable as state); the walls are BEHAVIOR, enforced by the canonical battery's service pins — verification proves state, the battery proves behavior (contract §13 boundary) |
| ADR-0009 no-summing (cost truth) | — | ⏸ deferred-with-reason: a computation law, not a state predicate — frozen `processing_cost` and worker earnings are structurally separate by design; a state check would require DEFINING a new invariant = owner/ADR territory (§6.4 law) |
| Migrations/config sanity (§6.4) | `prod.safety.migrations-consistent` + `settings-sanity` | ✅ codified |
| Smoke (§6.4, dev-only) | `dev.smoke.app-registry` / `urlconf` / `render-critical` | ✅ codified |

**No unaccounted source** (the VER-E stop condition never fired).

### 2. Documentation reconciliation

Cross-checked: log ⇄ contract ⇄ app README ⇄ GUIDE ⇄ status ⇄ index ⇄ CHANGE_IMPACT_MATRIX.
Three stale fragments found + fixed (all in engine docstrings, zero behavior): `checks/
__init__` still claimed "VER-A state: no check logic"; `_base` claimed "wave-gated to
VER-C" and carried the dead `implemented_wave` attribute + a wave-gate message that no
command could reach — reworded to the honest safety-net refusal. No contradictions remain.

### 3. Handoffs (§6.6 + owner-ordered interfaces)

**3.1 → Phase 14 (knowledge_sync).** Shared conventions: the CERTIFIED report schema
(envelope/body key sets, engine 1.0.0 — `test_certification.py` = the tripwire) · the
19-check-id census above (machine-readable via `verification.checks`) · the citation law
(every check names its invariant — an uncited check is drift by definition) · the
SPEC_VERSION cross-pin (verification ⇄ devseed). **Boundary stated:** Phase 13 verifies
DATA/CONFIG state; Phase 14 detects CODE⇄DOCS⇄GRAPH drift — no overlap, same
detect-and-notify law (neither ever fixes).

**3.2 → Phase 15 (BOD).** The dashboard may DISPLAY the latest
`var/verification_reports/` artifacts (read the JSON: envelope totals + body_hash + per-row
status) — it NEVER runs checks inline; any run-button feature = Phase-15 contract work,
owner-gated. Freshness = the envelope `ran_at` (the only timestamp).

**3.3 → Phase 19 (deployment runbook interface).** The runbook gains: **(a) pre-deploy
rehearsal** — dev-mode `manage.py verify_production` (env-stamped `dev`; contamination
informational over the dev cast; exit 0 expected); **(b) MANDATORY post-deploy step** —
`manage.py verify_production --report var/verification_reports/` on the production target
(env-stamped `prod`; contamination is RED there by design; exit 0 = the gate). Structural
facts for the runbook: the app is production-PRESENT (proven live at SEED-F/VER-A); no
bypass flags exist; `verify_all` in prod composes the identical subset (either command
satisfies the step; the runbook names `verify_production`).

**3.4 → Phase 20 (verification interface).** Execution is runbook-VERBATIM: run the exact
post-deploy command; **GO/NO-GO = the exit code** (0 = proceed; nonzero = STOP — the count
is in the envelope; findings route per the campaign protocol/U8, NEVER fixed inline by the
executor); archive the report file path + stdout into the execution record.

**3.5 → Phase 21 (certificate input contract).** The readiness certificate CITES a green
production report as a REQUIRED input, quoting: `command` (verify_production) ·
`engine_version` (1.0.0) · `spec_version` (1.0.0) · `environment` (**"prod"**) · `totals`
(**fail=0**) · `body_hash` · `ran_at` · body row-count. **Verify-never-trust:** the
certificate author independently recomputes the hash — sha256 over the body serialized as
compact sorted-keys JSON (`json.dumps(body, sort_keys=True, separators=(",", ":"))`) — and
states the match. A report whose environment ≠ "prod" or totals.fail ≠ 0 is not a
certificate input.

### 4. Final re-certification + battery

- **Primary vs the anchor: ALL 34 counts EXACT + ledger Σ ₹10,880.25** (fresh read-only
  capture this session) — zero census drift across the entire phase.
- **Final canonical battery 1678/1678** (4 sequential fresh-DB suites): 9-app
  `Ran 1002 — OK` + patterns_ai `Ran 528 — OK` + devseed `Ran 70 — OK` + verification
  `Ran 78 — OK` (re-proven green after the docstring reconciliation). Phase arithmetic:
  entry 1600 → +28 (A) +17 (B) +20 (C: −2+22) +13 (D) = **1678 ✓**.
- Read-only purity pins green · production services + devseed untouched phase-wide (the
  ONE devseed touch = the owner-ratified SEED-D6 import move at VER-A) · git `49404001` ·
  0 staged · 2 stashes · zero migrations · flags untouched.

### 5. 🏁 PHASE-13 VERDICT

**PHASE 13 COMPLETE — VERIFICATION ENGINE CERTIFIED (engine 1.0.0).** All nine §3 success
criteria hold: five commands live under both settings polarities (each cell negative-
tested) · read-only proven architecturally (purity pins) AND at runtime (strict row-count
identity) · single-source honored (SEED-D6 library, one implementation, zero duplicated
logic/goldens) · check-registry completeness counted (19 codified; every deferral
reasoned) · every category proven with pass AND constructed-fail cases · determinism
certified (body-hash pairs ×5 commands, cross-session identical) · verify_all composes
per environment (run-all-then-aggregate) · battery green at 1678 with the primary
untouched · docs + handoffs complete. **The permanent deployment-verification instrument
is operational.** Residuals: none owned by this phase (₹225 historical + performance
volumes remain Phase-11/12 spec residuals; snapshot refresh remains the owner's).
**Next: Phase 14 Knowledge Sync — owner-gated.**

_VER-E closed 2026-07-17 · Phase 13 closed 2026-07-17._
