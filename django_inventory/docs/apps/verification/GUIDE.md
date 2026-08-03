---
id: docs-apps-verification-guide
type: app-guide
status: active
owner: handwritten
scope: verification
anchors: config/verification/
verified: 2026-07-18
---

# verification — app guide (read-only engine, Campaign Phase 13 — 🏁 CERTIFIED at VER-E 2026-07-17)

> The permanent deployment-verification instrument (owner designation 2026-07-12), engine
> v1.0.0 CERTIFIED. Production-PRESENT (BASE settings) · read-only by architecture ·
> contract: 🔒 [PHASE_13_VERIFICATION_ENGINE.md](../../campaign_contracts/PHASE_13_VERIFICATION_ENGINE.md).
> Evidence: [VERIFICATION_ENGINE_LOG.md](../../VERIFICATION_ENGINE_LOG.md) (§VER-E =
> completeness census + Phase 14/15/19/20/21 handoffs incl. the mandatory post-deploy
> `verify_production` gate + the Phase-21 certificate input contract).

| File | Role |
|---|---|
| `apps.py` | AppConfig — no models, no migrations, no URLs, no templates (read-only by shape) |
| `guard.py` (VER-A) | Polarity per command (VER-D2 §6.3): dev-world commands (`verify_demo`/`verify_factory`/`verify_feature`) refuse outside dev; `verify_production`/`verify_all` run everywhere; pure functions + thin gather; no bypass flags |
| `assertions.py` (VER-A, SEED-D6) | **THE shared assertion library** (spec §6.1.7, single implementation — owner ruling VER-D1): counts · handle existence · DEV-marking · flags-untouched; `devseed` imports it (post-seed), `verify_*` consume it (VER-B+) |
| `report.py` (VER-A) | Report scaffolding (VER-D5): `CheckResult` (citation mandatory) · `build_report` (envelope w/ engine+spec versions, totals, body-hash, the ONLY timestamp; deterministic sorted body) · `write_report` → `var/verification_reports/` · `render_stdout` · `exit_code`; `ENGINE_VERSION` + `SPEC_VERSION` pins |
| `checks/__init__.py` (VER-A) | Check-registry scaffold: the 5 §6.4 category names; check modules land VER-B (smoke·golden) / VER-C (production-safety·dev-contamination·integrity) — every check cited (VER-D4) |
| `management/commands/_base.py` | `PolarityCommand` (banner → polarity → wave gate) + `DevWorldVerifyCommand` (VER-B: polarity → manifest-REQUIRED → checks → deterministic report → exit code; red ⇒ CommandError, "the engine never fixes"); common `--report`/`--skip`/`--manifest-dir` flags (skips explicit, never silent) |
| `management/commands/verify_{demo,factory,feature}.py` (VER-B, LIVE) | Dev-world commands: slug-fixed demo/factory + registry-validated `verify_feature <slug>` (post-polarity; non-executable slugs refuse with the registry note) |
| `management/commands/verify_{production,all}.py` (VER-C, LIVE) | `verify_production`: the production-safe subset, env-stamped report (dev run = rehearsal) · `verify_all`: environment-aware composition via `checks/compose.py` |
| `checks/production.py` (VER-C) | The production-safe subset (SELECT/aggregate only, cost noted): DEV-contamination scan (10 columns × spec-§4 namespace; prod-mode red, dev informational) · flags-vs-`OWNER_DECLARED_FLAGS` (U10 — declaration changed only by owner) · migrations-consistent · settings-sanity · integrity self-consistency (items-Σ per finalized settlement · reversal nets · ledger/WSC constraint re-checks · supersession chain); `_plan`/`_violators` injection = constructed-fail tests only |
| `checks/compose.py` (VER-C) | verify_all composition (VER-D7): run-all-then-aggregate, no fail-fast; dev = manifest-present worlds (`world.<slug>.…` ids) + rehearsal; prod = subset only; `all.composition` summary lists verified + manifest-absent worlds |
| `guard.environment()` (VER-C) | Report-env classifier: 'dev' = dev settings + DEBUG; else 'prod' (battery classifies prod → prod-mode checks battery-testable) |
| `manifests.py` (VER-B) | `latest_manifest(slug)` from `var/seed_manifests/` (newest by embedded stamp); `ManifestMissing` refusal names the exact `seed_*` remedy |
| `checks/dev_world.py` (VER-B) | The cited dev-world registry: manifest conformance (spec §10 · SEED-D5 database-match · P12 §6.5 recorded assertions) · LIVE shared-assertion re-run (the SEED-D6 library over devseed content — drift = red) · golden totals + worker items (certified sources only; zero literals, test-pinned) · smoke (app registry · URLConf · cast-identity renders — sanctioned request-cycle, session writes disclosed) · composite-aware (factory children) · `feature_slug_failure` validation |
| `tests/test_purity.py` (7) | **THE PERMANENT READ-ONLY PIN** (landed first): zero ORM writes · zero queryset/instance mutations · zero write-verb raw SQL · zero transaction management · modelless shape · BASE-settings presence |
| `tests/test_guard.py` (9) | The §6.3 polarity matrix cell-by-cell (pure) + command-level dev-world refusals under the test env (everywhere-commands' green runs live in test_production) |
| `tests/test_production.py` (VER-C, 22) | Green prod verification + BOTH commands end-to-end in the battery (prod-classified env) · planted-contamination red + informational rehearsal · flag/migration/sanity/integrity constructed fails · STRICT read-only row-count identity · composition proofs (subset-only prod · manifest-driven dev · absent-worlds listed · no fail-fast) |
| `tests/test_certification.py` (VER-D, 13) | **THE CERTIFIED-SCHEMA TRIPWIRE (engine 1.0.0):** envelope/body key sets · closed status/category sets · sorted duplicate-free body · independent body-hash recompute · determinism pairs per command shape · exit-code matrix (0/N/250-cap) · --skip transparency (envelope+body+stdout) |
| `tests/test_report.py` (6) | Body sorted + timestamp-free · body-hash deterministic/state-sensitive · totals + exit codes · explicit skips · disk round-trip |
| `tests/test_shared_library.py` (5) | SEED-D6 single-implementation proof: library lives here · devseed consumes the SAME object · exactly one `run_post_seed` in the tree · old module gone · spec-version cross-pin |
| `tests/test_dev_world.py` (VER-B, 17) | Green demo/regression/factory runs on REAL seeded worlds · determinism (body-hash ×2) · constructed fails per category (tampered spec-version/database/golden/item · world drift · bad route · missing identity) · manifest refusals + newest-wins · slug validation · single-source pins (zero golden literals static scan · re-run provably calls the shared library) |

Rules of the app: read-only architectural (purity-first) · checks codify certified
invariants only, with citations · a red check never fixes anything · the engine never
seeds · reports deterministic (body-hash stable) · no silent skips.
