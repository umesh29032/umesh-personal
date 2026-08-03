---
id: docs-apps-devseed-guide
type: app-guide
status: active
owner: handwritten
scope: devseed
anchors: config/devseed/
verified: 2026-07-18
---

# devseed — app guide (dev-only, Campaign Phase 12 — 🏁 CERTIFIED at SEED-F 2026-07-17)

> Dev-only seeder engine, PHASE-12 CERTIFIED (25/27 registry scenarios executable — 22/24 at certification + `feature-bod` (A2, Phase-15) + `feature-monthly-expense` (A3, Phase-16) + `feature-rm-expense` (A4, Phase-17 RMX-F 2026-07-18); 2 refuse
> by owner ruling). NOT installed under production settings (local.py-only registration —
> structural guard; proven live at SEED-F). Spec of record: 🔒
> [DEV_DATASET_ARCHITECTURE.md](../../DEV_DATASET_ARCHITECTURE.md) (v1.0.0 frozen-v1).
> Evidence: [SEEDER_ENGINE_LOG.md](../../SEEDER_ENGINE_LOG.md) (§SEED-F = certification +
> Phase 13/14/15/19 handoffs).

| File | Role |
|---|---|
| `apps.py` | AppConfig (no models, no migrations, no URLs, no templates) |
| `guard.py` | The 4-factor production guard (pure checks + thin gather); `SPEC_VERSION` pin; owner-ratified scratch-DB allowlist |
| `scenarios/__init__.py` | Machine-readable scenario registry (spec §7 taxonomy: 27 declared slugs across all six classes — 24 at certification + `feature-bod` [A2] + `feature-monthly-expense` [A3] + `feature-rm-expense` [A4]; `implemented` flags per wave; the Phase-14 drift-detection surface) |
| `management/commands/_base.py` | Shared thin-CLI shell (banner · guard · `--check` dry-run · implemented-gate → `core.seed_scenario` dispatch + manifest summary; non-executable slugs refuse with their registry note — SEED-D) |
| `management/commands/seed_demo.py` | Demo world (minimal-plus, SEED-D2) |
| `management/commands/seed_factory.py` | Full three-product factory (SEED-D2) |
| `management/commands/seed_feature.py` | Registry-validated feature slices |
| `management/commands/reset_demo.py` (SEED-E) | DESTRUCTIVE scratch-DB rebuild — per-DB literal confirmation flags → `core.run_reset` (drop → recreate → migrate → optional `--seed <slug>`, validated before any DDL) → reset manifest; no bypass flags; `inventory_db` has no flag even in the parser |
| `tests/test_guard.py` | 18 tests: every guard factor negative-tested · command-level refusals (incl. --check no-bypass) · registry↔spec pins (golden values 801.00/344.25/633.00/225; implemented-set = all but the two owner-ruled-out) |
| `core.py` (SEED-B → SEED-D) | The orchestration engine: `seed_scenario(slug)` — one outer atomic per world · post-commit self-assertions · manifest writer (`DEFAULT_MANIFEST_DIR` = repo-root `var/seed_manifests/`) · composite worlds (factory) · optional product · grain-list config · sizes/patterns · storefront · post-step dispatch · `IMPLEMENTED_THROUGH_LAYER = 11` |
| ~~`assertions.py`~~ → `verification/assertions.py` (SEED-D6 applied at P13 VER-A 2026-07-17) | The SINGLE-SOURCE post-seed assertion library RELOCATED to the production-present `verification` app (owner VER-D1 ruling: exactly one implementation); devseed IMPORTS it (`core.py`, `tests/test_reset.py`); pinned by `verification.tests.test_shared_library` |
| `layers/` (SEED-B) | Executors 2–6: `cast` (create_user + role converge) · `masters` (plain-ORM exception: cloth masters + stage library) · `products` (product_service SA-gate + flow_service; layering auto-attaches as mandatory first stage) · `machines` (machine_service) · `rolls` (roll_service.bulk_create_rolls, honest-NULL financials, attribute-keyed converge — roll_id = service-issued output handle) · `DivergenceError` = report-never-pave |
| `scenarios/minimal.py` (SEED-B) | Declarative minimal-world content (dev.min.* cast incl. SA product-actor · DEV-MIN masters/product/flow/roll · layer-7 Adda declared for SEED-C) |
| `tests/test_layers.py` (SEED-B) | 8 tests: end-to-end foundation slice · idempotency double-seed (zero created on rerun) · flow order (layering first) · service-path roll proof (CR- id, history rows, NULL financials) · divergence report-never-pave · mid-seed atomic rollback · service-refusal propagation · machines executor idempotency |
| `layers/production_truth.py` (SEED-C w1) | Layer 7: full journey via chokepoints — create_adda → layering (start/attach/breakup/complete, skilled worker + SA completer) → cutting legacy single-shot → generic stages (set_stage_workers → report good → complete_worker_task → advance); SR creation snapshots role rates (contract 2); COMPLETED-adda converge, partial = DivergenceError |
| `layers/money.py` (SEED-C w1) | Layer 8: settle_adda (create_draft → finalize via adda_settlement_service, golden byte-assert, ledger recount before/after) · seed_advance (advance_service) · seed_factory_expense (expense_service) |
| `scenarios/minimal_money.py` (SEED-C w1) | `feature-settlement` = THE deterministic money world: flow layering→cutting→dev-min-stitching (₹3/pc, credits) · 50 good → **golden ₹150.00** computed from its own config |
| `tests/test_purity.py` (SEED-C w1, +storefront pin SEED-D) | **THE PERMANENT U8 PIN**: static source scan — zero direct ORM writes/saves/deletes in devseed outside the TWO audited exceptions (masters · storefront); guarded-model write receivers = battery-red forever |
| `tests/test_money.py` (SEED-C w1) | 6 tests: journey completes adda + WSC service-outcomes · journey idempotent · golden ₹150.00 finalized · ledger recount delta fully explained + worker balance · money-world idempotent (zero new ledger rows) · flags never touched |
| `scenarios/recipes.py` (SEED-C w2) | THE three golden-journey recipes, extracted read-only from ADST-0004/0005/0006 + FOM §9/§10/§12: full flows/rates/rosters/dim-lines/APSCPB breakdowns/completion modes. Goldens = ASSERTION targets only. Carries the owner-approved **W2-F5 replay-only adjustment** (credits=False on cutting/cutting_pattern — documented in the module docstring) |
| `layers/journeys.py` (SEED-C w2) | The recipe replay engine: multi-roll layering modes (full/advance) · workspace cutting (`upsert_breakup_row` + `complete_cutting_from_bundles`) · blind advances (never-opened trio stages) · dim-line reports (color×size + alter/missing) · verified-qty overrides · settle |
| `tests/test_golden_journeys.py` (SEED-C w2) | 4 tests: **₹344.25 / ₹801.00 / ₹633.00 emerge byte-identically** + per-worker items byte-matched vs extracted truth + ledger delta + journey idempotency |
| `scenarios/extras.py` (SEED-D) | The 16 remaining scenario contents (demo · factory composite · 6 feature slices · 8 edge worlds) — per-tag `_world()` clones of the money world + 12 idempotent post-step functions (certified services only: pool_service.allocate · fnf_execute w/ DEDICATED leaver · machine_service.assign · roll damage/restore · set_pay_basis · rerate_stage_role · reverse+supersede+finalize · reopen/over-allocation refusal captures) |
| `layers/storefront.py` (SEED-D) | Layer 9 — Category/FeaturedProduct: the SECOND audited plain-ORM exception (no service owner; purity test pins the module to exactly these two models) |
| `tests/test_registry_complete.py` (SEED-D) | 17 tests: whole-registry-on-one-DB ×2 (shared-scratch simulation) + per-world targeted asserts (allocation draw-down · refusals verbatim · leaver-only deactivation · possession window · patterns/sizes · storefront · inline barcodes · damaged round-trip · MONTHLY basis · composite roles · rerate recalc+audit · supersession chain) |
| `core.run_reset` + `strip_volatile` (SEED-E) | Destructive orchestration (allowlist belt-check → psycopg2 DROP+CREATE via maintenance connection → connection switch + migrate → optional seed w/ assertions → `reset-<db>` manifest; NON-transactional DDL). `strip_volatile` = the determinism comparison surface (`ran_at` = the only permitted runtime identifier). Injection points `_dropper/_migrator/_seeder` exist ONLY for failure-propagation tests |
| `tests/test_reset.py` (SEED-E, 12 tests) | Command wall (confirmation/mismatch/inventory_db/unknown-DB refusals, validation-before-DDL) + orchestration contract (belt refusal · migrate/assertion failure propagation w/ no-manifest-on-failure · manifest shape · repeated-reset + cross-DB determinism surfaces · re-seed convergence) |

| `knowledge/` (Phase-14 KS-A) | The knowledge_sync detector core (charter widened to "dev tooling", SYNC-D1): `__init__` (Finding · SEVERITIES · the 8-domain inventory w/ the A-1 re-scoped domain 5 · VENUES) · `report.py` (P13-convention deterministic reports; THE single write site → `var/knowledge_sync_reports/`; threshold=BLOCKER) · `acceptance.py` (visible dated owner-attributed; exit-exempt only) · `gitio.py` (read-only git verb allow-list + porcelain fingerprint) |
| `management/commands/knowledge_sync.py` (KS-B: 9 detectors LIVE) | `--diff`/`--deep`/`--report`/`--skip`; registry = code-docs.{change-impact,route-map,model-map} + ownership.{matrix,metadata,lifecycle} + manifest.{paths,coverage,consistency}; graph domains land KS-C, registries KS-D; no `--fix` exists by law |
| `knowledge/d1_code_docs.py` (KS-B) | Domain 1: matrix routing (diff) + dead matrix refs (sweep) + route/model-map vs the graph — censuses/ids IMPORTED from the Phase-8 builder (extend-never-fork) |
| `knowledge/d6_ownership_metadata.py` (KS-B) | Domain 6: OWNERSHIP_MATRIX family-row coverage · §13 R2 frontmatter (7 fields; valid statuses incl. frozen-vN + generated) · §12 supersession banners; census = the builder's doc_boundary() |
| `knowledge/d5_manifest.py` (KS-B) | Domain 5 — THE A-1 OWNER SCOPE ONLY: path validation (dead path = BLOCKER, the CI-guarded class) · topic coverage vs graph · consistency; regenerate-compare DOES NOT EXIST |
| `knowledge/d2_graph.py` (KS-C) | Domain 2: Phase-8 validator IMPORTED + re-run (FATAL→BLOCKER) **with its write-bearing repro subprocess NO-OP'D (§16.3 incident KS-C-I1 — disclosed as a standing INFO every run)** · `--deep` builder dry-run w/ the file-write captured in memory → hash compare |
| `knowledge/d3_graph_census.py` (KS-C) | Domain 3: census counts (builder's own walkers) · disk→graph completeness · graph self-integrity via the P9 `load_graph()` gate (BLOCKER on refusal) |
| `knowledge/d4_generated.py` (KS-C) | Domain 4 (P9 stale-output contract): stamped-hash-vs-current (WARN w/ the file's own regeneration remedy) · banner corruption (BLOCKER) · corpus-wide fence pairing (code-block examples stripped) · `--deep` in-memory render-compare hand-edit detection (`write()` never called) · **`_HANDWRITTEN` exclusion (2026-08-01):** `HUMAN_GUIDE.md` is a hand-written KOS satellite living inside `docs/features/`, so scanning it for a generated banner produced a permanent false BLOCKER that stopped `knowledge_sync` from ever exiting clean. Excluded **by exact filename, never by `owner: handwritten`** — that field is editable, so trusting it would let a hand-edited card opt out of detection |
| `tests/test_knowledge_purity.py` (8) + `test_knowledge_report.py` (5) | **Pure-detector permanent pins:** single-write-site · zero destructive fs · read-only git (static + runtime refusal) · no-`--fix` pin · **sweep leaves porcelain-hash + every model count byte-identical** (with LIVE detectors) · report determinism/threshold/acceptance mechanics |
| `tests/test_knowledge_docs_domains.py` (KS-B, 14) | The constructed-drift matrix: every ordered failure class planted-and-caught via injected inputs (matrix routing/dead-ref · route/model drift both directions · unowned · metadata ×3 · bannerless supersession · manifest dead-path/unreadable BLOCKERs · coverage · consistency) + finding-shape + registry pins |
| `tests/test_knowledge_graph_domains.py` (KS-C, 17) | Domains 2/3/4 constructed matrix (validator propagation/crash · deep-rebuild both ways · census/completeness/graph-hash · stale/banner/fence/hand-edit/orphan/diff-scope) + **the 2 §16.3 incident pins** (real-validator no-write + repro-neutralized disclosure) + deep-gating transparency |
| `knowledge/d7_dataset_spec.py` (KS-D) | Domain 7 (SEED-F handoff): registry shape/implemented-state/completeness vs `SCENARIOS`⇄`CONTENT` · three-way SPEC_VERSION pin (guard ⇄ report ⇄ spec §10) · golden-vs-spec agreement |
| `knowledge/d8_verification_registry.py` (KS-D) | Domain 8 (VER-E handoff): live check census (static extraction) vs the certified 19-id baseline · VER-D4 citation presence + file-level resolution · VER-D certified report-schema dependency (P19/20/21) |
| `tests/test_knowledge_registry_domains.py` (KS-D, 18) | Domains 7/8 constructed matrix (11 ordered classes) + severity-engine certification (threshold · accepted-BLOCKER exempt-but-printed · stale-acceptance surfacing) + the eight-domain completeness meta-pin + live-clean pins (registries/citations/schema green today) |
| `tests/test_knowledge_guards.py` (KS-E, 4) | **THE SYNC-D4 PERMANENT GUARD SUBSET (build-red forever):** dead-manifest-path · fence-corruption · graph-invariant FATALs · hand-edited-graph — live detector runs, the PkalsNavigationGuardTests extension pattern |

Rules of the app: guards before features · services only (no direct guarded-table writes —
the permanent purity pin) · natural handles, never pks · primary dev DB never a target ·
world isolation (per-tag namespaces; shared identities never mutated destructively —
FnF gets its own leaver) · **knowledge_sync is a PURE DETECTOR (detect/classify/route,
never repair; single write site = its own var/ reports).**
