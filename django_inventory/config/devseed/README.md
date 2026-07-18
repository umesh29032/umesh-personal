---
id: config-devseed-readme
type: app-readme
status: active
owner: handwritten
scope: devseed
anchors: config/devseed/
verified: 2026-07-18
---

# devseed — dev-only DEV TOOLING: Seeder Engine (Phase 12) + knowledge_sync (Phase 14)

**Charter widened at Phase-14 KS-0 (SYNC-D1, owner-ratified 2026-07-17):** devseed = the
dev-only TOOLING home. It hosts (a) the four seeder commands — `seed_demo` · `seed_factory`
· `seed_feature <slug>` · `reset_demo` — implementing the frozen spec
[docs/DEV_DATASET_ARCHITECTURE.md](../../docs/DEV_DATASET_ARCHITECTURE.md) (v1.0.0); the
seeder is an ORCHESTRATOR of the app's single-writer services, never a data loader (raw
fixtures/SQL forbidden for guarded tables, spec §3); and (b) **`manage.py knowledge_sync`**
— the PURE drift DETECTOR (Phase 14; `knowledge/` core): detects · classifies · reports ·
names the owning repair venue; it never repairs and a `--fix` flag will never exist.
**🏁 PHASE 14 CLOSED at KS-E (2026-07-17) — KNOWLEDGE SYNC CERTIFIED: 23 detectors · 8
domains · full-sweep/`--diff`/`--deep` · deterministic reports · threshold = any unaccepted
BLOCKER · every finding names its repair venue.** The SYNC-D4 guard subset (dead-manifest-
path · fence-corruption · graph-invariant · hand-edited-graph) = build-red battery tests
forever. Incident KS-C-I1 (the validator's repro subprocess rewrote the graph) disclosed →
neutralized → owner-disposed (new certified baseline `203547859d65…`) → pinned unforgeable
(the artifact-identity-by-hash battery pin). With this close the PHASE_05 Documentation
Foundation family (5→6→7→8→9→14) is COMPLETE. Post-close usage: `--diff` after feature
waves (P15–18 U6 queue) · pre-deploy sweep (P19 readiness input) · mandatory `--deep`
pre-checkpoint sweep (P22).
Evidence: [docs/KNOWLEDGE_SYNC_LOG.md](../../docs/KNOWLEDGE_SYNC_LOG.md).

**Where it exists:** registered ONLY in `config/config/settings/local.py` — under production
settings the app (and therefore every command) does not exist (structural guard factor 5).
Topmost import-linter layer: devseed imports the world; nothing imports devseed.

**The guard (all factors must pass; no bypass flags exist):**
1. settings module == `config.settings.local`
2. `DEBUG` is True
3. target DB ∈ scratch allowlist `inventory_seed_scratch_1` / `_2` (owner-ratified SEED-D5 —
   **the primary dev DB `inventory_db` is deliberately NOT allowlisted**)
4. `reset_demo` additionally requires the literal per-DB flag
   `--i-understand-this-destroys-<dbname>`

**State (🏁 PHASE 12 CLOSED at SEED-F, 2026-07-17 — SEEDER ENGINE CERTIFIED):**
engine + reset OPERATIONALLY CERTIFIED — **22 of 24 registry
scenarios executable** via the real commands (demo · factory composite · minimal ·
feature-settlement · 3 golden regressions · 6 feature slices · 8 edge worlds), each
deterministic + idempotent + manifest-emitting + self-asserting, proven ×2 runs on BOTH
allowlisted scratch DBs with identical final census (ledger 89 / Σ 2,978.25). The two
non-executable stay by owner ruling and refuse at the command: `regression-settlement-225`
(spec §12 A1 — historical evidence) · `performance` (DATA-D6 — targets deferred).
**`reset_demo` is REAL (SEED-E):** guard + literal per-DB flag → drop → recreate → migrate →
optional `--seed <slug>` (slug validated BEFORE any DDL) → reset manifest; certified ×2
cycles ×2 scratch DBs — state and manifests identical across resets (minus `ran_at`) and
across databases. NON-transactional (DDL); `inventory_db` has no confirmation flag even in
the parser; zero bypass flags.

**Purity (permanent):** zero direct guarded-table writes; TWO audited plain-ORM exceptions
only — `layers/masters.py` (5 service-less masters) and `layers/storefront.py`
(Category/FeaturedProduct, no service owner) — both module-pinned by `tests/test_purity.py`.

**Tests:** `devseed` suite = the third sequential battery member (SEED-D4 dated amendment,
framework README). Run: `env/bin/python config/manage.py test devseed`.

**Evidence:** [docs/SEEDER_ENGINE_LOG.md](../../docs/SEEDER_ENGINE_LOG.md).
