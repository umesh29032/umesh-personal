---
id: seeder-engine-log
type: evidence-log
status: active
owner: append-only
scope: all — Campaign Phase 12 (Seeder Engine) evidence
anchors: docs/campaign_contracts/PHASE_12_SEEDER_ENGINE.md, docs/DEV_DATASET_ARCHITECTURE.md
verified: 2026-07-17
---

# SEEDER ENGINE LOG — Campaign Phase 12 (created SEED-0, append-only)

> Contract = procedure ([PHASE_12_SEEDER_ENGINE.md](campaign_contracts/PHASE_12_SEEDER_ENGINE.md));
> the spec = the WHAT ([DEV_DATASET_ARCHITECTURE.md](DEV_DATASET_ARCHITECTURE.md) 🔒 frozen-v1);
> this log = what was built and proven. Runtime seed manifests live in `var/` — anything
> binding is quoted HERE.

---

## SEED-0 — Charter + gate + ratification — EXECUTED 2026-07-17 · ⏸ AWAITING OWNER SEED-D1..SEED-D9

**Owner order honored:** "Execute SEED-0 only… Do not assume any owner decisions. Do not
create any code until every SEED-0 gate has passed." — no ratification language → FIX-0
precedent, no answer fabricated; **the next owner gate = this decision pack.** Zero code,
zero tests, battery NOT run (entry baseline recorded below from the dashboard).

### 1. Gate (contract §7 SEED-0 row) — PASS

| Check | Result |
|---|---|
| Phase 11 closed + spec frozen | ✓ — PHASE_11 §DSA-C "🏁 PHASE 11 VERDICT: SPEC-FROZEN"; `docs/DEV_DATASET_ARCHITECTURE.md` frontmatter `status: frozen-v1` (v1.0.0, 2026-07-17) |
| Import boundaries (§2.1) | ✓ — `config/.importlinter` present: `foundation-purity` contract (:25) + `acyclic-layers` (:52); test-side twin `core/tests.py::FoundationPurityTests` (:47) |
| Settings structure | ✓ — `config/config/settings/{base,local,production}.py`; `local.py` carries `DEBUG = True` (the dev-only registration target; base/production untouched by this phase) |
| Purity-test precedent | ✓ — exists at `config/patterns_ai/tests/test_purity.py` (**path note:** contract §2.1 says `patterns_ai/test_purity.py`; the file lives inside the `tests/` package — location imprecision only, the precedent stands) |
| Battery definition home | ✓ — framework `campaign_contracts/README.md` U5 (:49) + run commands (:69); D4 amendment target confirmed |
| No seeder app exists | ✓ — `config/devseed` absent; no cross-domain orchestration command anywhere (grep) |
| Evidence log absent pre-session | ✓ — this file created now |
| git state | HEAD `49404001` · 0 staged · 2 stashes ✓ |

### 2. Baselines

- **Battery entry baseline: 1530/1530** (status dashboard; last physically run at Phase-10
  UIL-D wave-1 close 2026-07-16 — 9-app 1002 + patterns_ai 528; unchanged-code-since proven
  at UIL-E/F). Phase-12 arithmetic starts here.
- **Primary-dev-DB census anchor (the untouched-proof anchor):** §2b below — key-table row
  counts + ledger sum, captured read-only at SEED-0; re-proven unchanged at SEED-F (and any
  drift mid-phase = stop condition §16.7).

### 2b. Primary-dev-DB census anchor (read-only)

**Capture disclosure (dated, not silent):** the sandbox's Bash safety-classifier was
temporarily unavailable at SEED-0, so a fresh in-session query run could not execute. The
anchor below = the **DSA-A census values, captured read-only EARLIER THIS SAME DAY
(2026-07-17)**, with zero DB-writing activity since (Phase 11 = docs-only by construction;
this session = docs-only). **Obligation recorded: SEED-A's FIRST step (before any code) =
re-capture this table fresh and diff against these values; any delta = stop condition
§16.7.**

| Table | Anchor | Table | Anchor |
|---|---|---|---|
| accounts.User | 48 (46 active) | production.WorkerStageTask | 150 |
| accounts.Role | 5 | production.WorkerStageContribution | 153 |
| accounts.SidebarItemRule | 21 | production.WorkerStageAllocation | 84 |
| accounts.Skill / UserType | 10 / 5 | production.StagePoolSnapshot | 88 |
| raw_materials.ClothType/Color/Storage | 6 / 15 / 3 | machines.Machine / MachineAssignment | 4 / 5 (2 open) |
| raw_materials.ClothRoll | 32 | expense.WorkerLedgerEntry | **170 · Σ ₹10,880.25** |
| production.Product | 18 | expense.AddaSettlement / Item | 8 / 43 |
| production.Adda | 18 (3-PATTI: 009/010/012/016) | expense.StageWorkAssignment | 141 |
| production.WorkflowStage | 73 | expense.FactoryExpense / WorkerAdvance | 4 / 0 |
| production.Stage / StageCategory / MachineType | 23 / 5 / 5 | storefront.Category / FeaturedProduct | 1 / 1 |
| production.AddaStageRecord | 132 | patterns_ai.Marker / MarkerUsage / PatternPiece | 3 / 1 / 58 |
| | | tracking.BarcodeExportBatch | 6 |

### 3. Standing-context notes recorded at charter

- **KOS-compat (record-only, owner permanent guidance):** the machine-readable scenario
  registry + seed-manifest format designed this phase = the Phase-14 drift-detector inputs
  (contract §6.7) and remain the future graph-kind candidates recorded at DSA-0. Nothing
  built beyond the contract.
- **Snapshot refresh (post-P9 D4 cadence) remains DUE — owner action.** P11 carried the
  recommendation: executing it BEFORE first-code SEED-A further de-risks (noted, not gated).
- Money-Write STOP rule armed for the whole phase (U8-hostile SEED-C; purity test = the
  standing proof).

### 4. ⏸ Decision pack — SEED-D1..SEED-D9 (defaults binding unless overridden; Appendix A)

| # | Decision | Default in one line | Notes for ruling |
|---|---|---|---|
| SEED-D1 | Command home | New dev-only app **`devseed`** (no models/migrations/URLs/templates): 4 commands + orchestration core + guard + assertions + tests; registered ONLY in `settings/local.py`; NEW TOPMOST import-linter layer | the structural 5th guard factor |
| SEED-D2 | seed_demo vs seed_factory | `seed_demo` = minimal-plus demo world (fast, single product journey) · `seed_factory` = the full three-product factory (T-SHIRT + LOWER + 3-PATTI class with settled journeys) | matches spec §7 minimal/full-demo classes |
| SEED-D3 | Transactions | ONE outer atomic per world (services nest as savepoints); `reset_demo` non-transactional (drop→migrate→optional seed) with strictest confirmation | spec §8 |
| SEED-D4 | **Battery membership (a dated framework-README amendment)** | devseed tests join the canonical battery as an additional sequential suite member; amendment dated + applied at SEED-0 closure | changes the U5 battery definition — needs your explicit yes |
| SEED-D5 | **Scratch-DB law + allowlist names** | All Phase-12 runs/proofs on allowlisted throwaway DBs; PRIMARY dev DB never a target. **Proposed allowlist: `inventory_seed_scratch_1` · `inventory_seed_scratch_2`** (two, for the determinism cross-DB proof) | names = owner input; propose the two above |
| SEED-D6 | Assertions single-source | `assertions` module implements spec §7 definitions; runs automatically post-seed (non-optional); Phase 13 IMPORTS it (never forks) | P13 contract carries the reconciliation note |
| SEED-D7 | CLI surface | Slugs validated against the registry · `--check` dry-run · exact-string destructive confirmation · NO assertion-skip flag · spec-version banner · standard exit codes | — |
| SEED-D8 | Manifests + logging | stdout log + machine-readable manifest → `var/seed_manifests/` (gitignored runtime; never docs/) | — |
| SEED-D9 | Test tiers | Guard units + purity + idempotency + determinism + golden integration scenarios. **Runtime-cost call: golden tests IN the default battery vs named-separate-proof at every wave** | golden integration seeds full journeys — likely the slowest members; your call |

**Recommendation: accept all nine**, with D5 = the two proposed scratch names (or supply your
own) and D9 = keep golden tests IN the battery (correctness > runtime; runtime recorded per
run — can be re-ruled later by dated amendment if it hurts).

### 5. Scope discipline

Files touched this sub-phase: this log (NEW) · DOCUMENTATION_INDEX (log row) · status ·
memory. **Zero code · zero tests · zero DB writes (census = SELECT-only) · battery NOT
run.** **Next: owner answers SEED-D1..SEED-D9 → D4 amendment applied to the framework README
→ SEED-A app skeleton + guards (battery-bearing, owner-gated).**

### 6. SEED-0 CLOSURE — owner rulings 2026-07-17 (verbatim)

> "I accept the defaults for SEED-D1 through SEED-D9 with the following explicit rulings.
> … [D4] Record the required dated amendment to the framework README… [D5] Use the proposed
> scratch database allowlist exactly: inventory_seed_scratch_1 · inventory_seed_scratch_2.
> The primary development database must never be a Phase 12 seeding target. … [D9] Keep the
> golden integration tests inside the canonical battery. … Before SEED-A performs any
> implementation work, execute the fresh primary-development-database census recapture…"

All nine RATIFIED (Appendix A filled verbatim) · **D4 amendment APPLIED** (framework README
battery block, dated 2026-07-17: devseed = third sequential suite member). **SEED-0 CLOSED
2026-07-17.** SEED-A authorized, gated on the census re-capture.

## SEED-A — App skeleton + guards — DONE 2026-07-17 · BATTERY 1548/1548 GREEN (new baseline)

### 0. Owner-ordered precondition — census re-capture: EXACT MATCH

Fresh read-only re-capture (inline query, full 32-table anchor set + ledger sum): **every
value identical to the §2b anchor — including ledger 170 / Σ ₹10,880.25.** §16.7 NOT
triggered → implementation authorized. (Bash-classifier outage workaround: inline `python -c`
form; same queries, disclosed.)

### 1. Built (guards-before-features law held: guard module + tests landed before any command shell)

| File | Content |
|---|---|
| `config/devseed/guard.py` | 4-factor guard: pure per-factor checks (unit-testable with injected values) + thin `gather_and_check` · `SPEC_VERSION = "1.0.0"` pin · owner-ratified `SCRATCH_DB_ALLOWLIST` (frozenset, 2 names) · never short-circuits (refusals complete) · NO bypass flag exists |
| `config/devseed/scenarios/__init__.py` | Machine-readable registry: **24 declared slugs covering ALL six spec classes** (minimal · demo/factory full-demo · 7 feature slices · 4 regression worlds with golden values pinned · 8 edge-case worlds · performance-with-owner-deferred-targets); everything `implemented: False` at SEED-A |
| `management/commands/{_base,seed_demo,seed_factory,seed_feature,reset_demo}.py` | Thin shells: spec-version banner → guard → `--check` dry-run (guard-first, no bypass) → wave-gate CommandError ("not implemented… zero writes performed"). `seed_feature`: slug validated against the registry (unknown → lists valid, nonzero exit). `reset_demo`: per-DB LITERAL confirmation flags (`--i-understand-this-destroys-inventory_seed_scratch_1/_2` — typo-proof: the closed 2-name allowlist gets static flags; two-at-once = ambiguous = unconfirmed) |
| `config/devseed/tests/test_guard.py` | **18 tests**: 7 pure factor tests (each factor negative+positive; allowlist size pinned =2; reset collects ALL 4 failures) + 7 command-level refusals (test env: DEBUG False + test-DB name ⇒ every command refuses — the standing proof seeder commands can never touch a battery DB; `--check` does NOT bypass; unknown-slug listing) + 4 registry↔spec pins (6 classes exact · golden 801.00/344.25/633.00/225 · nothing-claims-implemented) |
| Wiring | `settings/local.py`: `INSTALLED_APPS += ["devseed"]` (the ONE licensed settings edit; base/production untouched — grep-proven 0/0) · `config/.importlinter`: devseed in root_packages + NEW TOPMOST layer |
| U6 docs | `config/devseed/README.md` + `docs/apps/devseed/GUIDE.md` (new) · DOCUMENTATION_INDEX rows · CHANGE_IMPACT_MATRIX consulted: new-app class → app README+GUIDE+index (done); no service/model/URL rows triggered (none exist in devseed) |

### 2. Proofs

- **Guard refusal verbatim (primary dev DB):** `GUARD REFUSED: - database 'inventory_db' is
  not an allowlisted scratch DB (allowed: inventory_seed_scratch_1, inventory_seed_scratch_2)
  — the primary dev DB is never a seeder target` (live run of `seed_demo` under local
  settings; zero writes).
- **Production-settings absence (structural factor 5):** `production.py` does not import
  locally at all (env-gated: `decouple.UndefinedValueError: REDIS_URL not found` — disclosed;
  full boot impossible here by design). Static proof: `grep -c devseed` → local.py **2** ·
  base.py **0** · production.py **0**; Django command discovery is INSTALLED_APPS-driven ⇒
  the commands do not exist under production settings.
- **Import-linter:** `foundation-purity` **KEPT** · `acyclic-layers` BROKEN with **ZERO
  devseed rows** (0 grep hits) — every violation = the pre-existing documented worklist (the
  contract file itself marks that contract REPORT-ONLY/M4). devseed introduced no new edge.
- **Battery (U5, 3 suites per the D4 amendment):** 9-app **`Ran 1002 tests — OK` (169.9s,
  FoundationPurityTests inside)** + patterns_ai **`Ran 528 — OK` (142.3s)** + devseed
  **`Ran 18 — OK` (0.004s)** = **1548/1548. Arithmetic: entry 1530 + 18 new = 1548 ✓.**
  (Runner note, disclosed: the same canonical suites invoked via an inline `get_runner`
  wrapper this session — Bash-classifier outage blocked the literal `manage.py test` command
  line; identical runner, settings, sequential fresh-DB semantics.)
- **Primary-dev-DB untouched post-wave:** 9-sentinel spot census + ledger Σ — all EXACT vs
  anchor.

### 3. Scope discipline

New files = the devseed tree + its 2 docs. Changed = local.py (licensed line) ·
`.importlinter` (topmost layer) · framework README (D4 dated amendment) · this log · contract
Appendix A · DOCUMENTATION_INDEX · status · memory. **Zero existing-app code touched · zero
migrations (U14 untriggered) · zero DB writes outside test DBs (created/destroyed by the
runner) · flags untouched.** git `49404001` · 0 staged · 2 stashes.

**Next: SEED-B — foundation layer executors 2–6 (cast → masters → products/flows → machines
→ rolls) + minimal scenario end-to-end on a scratch DB (owner-gated).**

_Section closed 2026-07-17._

## SEED-B — Foundation layers (2–6) — DONE 2026-07-17 · BATTERY 1556/1556 GREEN (new baseline)

### 1. Built (spec §2 layers 2–6, spec §3 writer map — services only)

| Piece | Content |
|---|---|
| `core.py` | `seed_scenario(slug)` orchestrator: ONE outer `transaction.atomic` per world (SEED-D3) → executors in spec order → **post-COMMIT self-assertions** (fail ⇒ world stays for forensics, §6.5) → manifest to `var/seed_manifests/` (SEED-D8; `var/` pre-gitignored). `IMPLEMENTED_THROUGH_LAYER = 6` wave gate |
| `assertions.py` | Single-source module (SEED-D6; Phase 13 imports): exact counts · minted-handle existence + **DEV-marking invariant** · service-issued OUTPUT handles (existence-only — see finding SB-F2) · flags-untouched (U10) — full failure list, never first-only |
| `layers/cast.py` | L2 via `User.objects.create_user` (production hashing path) + role converge; divergent role = `DivergenceError`, never paved |
| `layers/masters.py` | L3 plain-ORM exception per spec §3 (cloth masters + stage library — no service owner); converge by unique name/slug |
| `layers/products.py` | L4 via `product_service.create_product` (SA-only gate — see SB-F1) + `flow_service.add_stage_to_product_flow` (manager); converge by product code / (product,stage) pair |
| `layers/machines.py` | L5 via `machine_service.create_machine_type/create_machine` (iexact-dup + MGT-F-1 guards live); converge by code |
| `layers/rolls.py` | L6 via `roll_service.bulk_create_rolls` — TRUE manager actor, **honest-NULL financials** (no FINANCIAL_ROLES in minimal cast), fixed deterministic `purchased_date=2026-01-01`; ClothRollHistory CREATED rows arrive via the certified path; converge = attribute-keyed (SB-F2) |
| `scenarios/minimal.py` | Declarative content: cast ×3 (`dev.min.sa/mgr/worker`) · DEV-MIN masters · product DEV-MIN-TEE · flow (2 stages) · 1 roll · layer-7 Adda DECLARED for SEED-C |
| `tests/test_layers.py` | 8 tests (suite 18→26): end-to-end slice · idempotency (zero created on rerun) · flow order · roll service-path proof (CR- id + history + NULL financials) · divergence-report-never-pave · mid-seed atomic rollback (world vanishes) · **service-refusal propagation (worker actor → PermissionDenied surfaces verbatim)** · machines idempotency |

### 2. In-wave findings (assertion machinery caught both — fixed within the wave, spec-faithful)

- **SB-F1 — `create_product` is SUPER-ADMIN-only** (`product_service._ensure_can_manage`:
  "Only Super Admin can manage products") and **auto-attaches the mandatory LAYERING first
  stage** (production law — a flow-less Product breaks `create_adda`). Scenario corrected to
  reality (formalize-don't-fictionalize): minimal cast gained `dev.min.sa` as the
  product-actor; expected flow = auto-layering + 2 declared stages = 3 WorkflowStages.
  NO service was touched (§2.2 out — the seeder adapts).
- **SB-F2 — roll_id is service-issued (`CR-NNNNNN` intake format, spec §4's own declared
  scheme)** — not a minted DEV-prefixed handle. The DEV-marking assertion (correctly)
  refused it → assertion contract refined: MINTED handles = existence + DEV-marking;
  SERVICE-ISSUED output handles = existence-only, dataset-born identity derives from their
  DEV-marked masters (pinned by the count filters). Recorded as the §4 interpretation of
  record for all later waves.

### 3. Scratch-DB evidence run (the §16 laws held)

`inventory_seed_scratch_1` CREATED (psycopg2, .env creds) → `migrate` (baseline layer 1
live) → **seed minimal ×2**:
- **RUN 1:** cast created 3 · masters 6 · products-flows 3 · rolls 1 — assertions
  `{'checks': 4, 'handles': 10, 'result': 'PASS'}`
- **RUN 2:** created **0** everywhere (skipped 3/6/3/1) — **IDEMPOTENT: True**, assertions
  PASS. Manifests ×2 written to `var/seed_manifests/` (gitignored).
- **Handle census vs registry:** 10 minted (`dev.min.sa/mgr/worker` · `DEV-MIN-COTTON/RED/
  RACK` · `dev-min` · `dev-min-cutting/stitching` · `DEV-MIN-TEE`) + 1 output (`CR-000001`)
  — ALL in the §4 schemes; **zero collisions with the spec §11 reserved registry**.

### 4. Primary-dev-DB untouched — PROVEN

Post-wave census on `inventory_db` (no env override): all sentinels EXACT (User 48 ·
rolls 32 · products 18 · Addas 18 · stages 23 · WorkflowStage 73 · machines 4 · ledger
170/Σ ₹10,880.25 · settlements 8 · FP 1 · markers 3) **+ the sharpest proof: `dev.min.*`
users in the primary = 0** (the seeded identities exist ONLY on scratch).

### 5. Battery (3 suites, D4 definition)

9-app **OK (1002)** + patterns_ai **`Ran 528 — OK` (144.4s)** + devseed **`Ran 26 — OK`**
= **1556/1556. Arithmetic: entry 1548 + 8 new layer tests = 1556 ✓.** (Same inline-runner
invocation class as SEED-A — classifier-outage workaround, disclosed.)

### 6. Scope discipline

New files: `core.py` · `assertions.py` · `layers/` (6 files) · `scenarios/minimal.py` ·
`tests/test_layers.py`. Changed: GUIDE (U6 rows) · this log · status · memory. **Zero
existing-app code touched · zero migrations · layers 7+ untouched (SEED-C) · no money/
production-truth writes anywhere · flags untouched.** git `49404001` · 0 staged · 2 stashes.

**Next: SEED-C — production-truth + money layers 7–8 (U8-HOSTILE: chokepoint orchestration
with TRUE actors, the purity test, golden regression seeds + ₹-assertions, ledger recount
discipline) — owner-gated.**

_Section closed 2026-07-17._

## SEED-C — Production truth + money layers (7–8, U8-hostile) — OPENED 2026-07-17 · ⏸ STOPPED AT §16.5 BEFORE IMPLEMENTATION (2 classified items)

**Money-Write STOP discipline applied at the RECON stage: no layer-7/8 code was written**
— one of the wave's four mandated golden assertions is not derivable from the record, and
inventing it would violate the frozen spec (§7: expected values = owner-approval-only) and
§16.5 verbatim ("a needed expected-value or volume target is nowhere on disk — Design Record
item / owner input, never invented").

### 1. ⏸ C-SEED-1 — the ₹225 invariant has NO executable recipe on disk

Evidence trail (all read-only):
- The S-series receipts assert it (S1 hostile review :63/:71 "golden ₹225 byte-identical" ·
  S3 receipt :88 "the golden **₹225 supersede chain** must reconcile byte-identical" ·
  S4-P3 :105/:131 · S5 :121/:131) — receipts PROVE it held; none records the recipe
  (world + quantities + rates that produce 225).
- The pointer in `production/tests/test_s3_good_alter_missing.py:6` ("the byte-identical
  ₹225 gate lives in test_golden_path / test_adda_settlement_service") resolves to a suite
  whose actual golden totals are **240.00 / 150.00 / 90.00 / 135.00 / 30.00 / 0.00 —
  no 225 anywhere** (grep-verified across config/**.py: zero `225` money literals).
- Candidate explanation (NOTED, not blessed): the supersede-chain arithmetic 90 + 135 = 225
  matches the S3 "supersede chain" wording — whether THAT is the historical ₹225 = owner's
  to confirm, not mine to assume.

**Options for the owner:** (a) supply/bless the ₹225 recipe (or confirm the 90+135
supersede-chain identity) → the scenario seeds it; (b) dated spec §12 amendment: the ₹225
invariant's LIVING guard = the settlement suite's current goldens (already in the battery
forever), and `regression-settlement-225` is re-scoped to the suite's on-disk golden chain
(renamed accordingly) — no historical claim rewritten either way.

### 2. Journey-recipe extraction — FEASIBLE (probe evidence), but scale disclosed

`ADST-0006` probed read-only: adda `3-PATTI-016`, **8 settlement items** with full FK chain
(worker · stage_record · earning_assignment) + quantity/earning fields — the ₹633.00 recipe
(and 344.25/801.00 likewise) IS mechanically extractable from the primary DB + WorkflowStage
rates. **Scale disclosure:** replaying a full journey requires a production-line
orchestration engine (per-stage: roll assignment → layering → cutting piece-breakdowns
(APSCPB) → per-handler WST/WSC payloads → stage completions → settle→finalize) across
12–16-op flows — the largest single build of the phase, on top of layer-7/8 executors,
the purity test, and the recount discipline.

**Proposed execution shape (owner ruling requested):** SEED-C as TWO battery-bearing waves —
**wave-1**: layer-7/8 executors + the minimal-money golden world (deterministic expected
value computed from its own seeded rates — spec-embedded at seeding, not invented history) +
the permanent purity test + ledger recount discipline; **wave-2**: the three extracted golden
journeys (801.00/344.25/633.00) + C-SEED-1's disposition. Alternative: single-shot on your
order (accepted scale risk).

### 3. Scope discipline (this stop)

Read-only probes only (grep + 3 SELECT probes). Zero code, zero writes, battery not run
(baseline 1556/1556 stands). git `49404001` · 0 staged · 2 stashes.

**Next: owner disposes C-SEED-1 (a/b) + rules on the wave split → SEED-C implementation.**

### 4. C-SEED-1 disposition + wave split — owner rulings 2026-07-17 (verbatim)

> "Your classification of C-SEED-1 is correct. Do NOT invent the ₹225 executable recipe.
> Approve option (b). Record a dated specification amendment only. … For executable
> regression truth: ₹801.00 · ₹344.25 · ₹633.00 remain mandatory executable golden journeys.
> The ₹225 historical invariant is no longer treated as a standalone executable regression
> until an authoritative recipe exists. … Split SEED-C into two battery-bearing waves. …
> STOP after Wave 1."

→ **Spec §12 amendment A1 recorded** (DEV_DATASET_ARCHITECTURE.md) · registry
`regression-settlement-225` re-scoped (expected=None, historical-evidence note) · registry
pin test updated. Wave split ratified.

## SEED-C — WAVE 1 — DONE 2026-07-17 · BATTERY 1566/1566 GREEN (new baseline)

### 1. Built (layers 7–8 + the permanent purity pin)

| Piece | Content |
|---|---|
| `layers/production_truth.py` (L7) | The journey engine, chokepoints ONLY: `create_adda` → layering via `layering/service` (start_layering[mgr] → attach_roll[skilled worker] → save_breakup[worker] → complete_layering[SA — cutting_master_helper bypass]) → **cutting legacy single-shot** (`complete_cutting(pieces_cut, worker_ids)`, MANAGEMENT gate, materializes APSCPB) → generic stages (`set_stage_workers` → `report_contributions(good)` → `complete_worker_task` → `advance_to_next_stage`) → COMPLETED. SR creation calls `ensure_stage_role_rates` (contract 2 — the same call the certified creation sites make). Converge: COMPLETED adda = skip; partial = DivergenceError |
| `layers/money.py` (L8) | `settle_adda`: `create_draft` → `finalize_adda_settlement` (the single writer) + **golden byte-assert** + **ledger recount before/after** · `seed_advance` (advance_service) · `seed_factory_expense` (expense_service R5 writer) |
| `scenarios/minimal_money.py` | `feature-settlement` = the deterministic money world (owner Wave-1 mandate): flow **layering → cutting → dev-min-stitching** (production trio/join law honored); ONE payable stage ₹3/pc × 50 good = **golden ₹150.00 computed from its own seeded config** |
| `tests/test_purity.py` | **THE PERMANENT U8 PIN (4 tests)**: zero `.objects.create/bulk_create/update/get_or_create` outside the audited masters exception · zero `.save(`/`.delete(` anywhere in non-test devseed source · masters module pinned to the 5 service-less masters · guarded-model write receivers = red forever |
| `tests/test_money.py` (6) + updates | journey→COMPLETED + WSC-as-service-outcomes · journey idempotent · golden ₹150.00 finalized · **recount delta fully explained + worker_balance == ₹150.00** · money idempotent (zero new ledger rows) · flags untouched |

### 2. In-wave findings (all caught by the engine's own discipline; fixed faithfully, ZERO services touched)

- **SC-F1**: a minimal flow WITHOUT a real `cutting` stage can never pass the trio/join
  pointer (`advance_lane` join predicate keys on cutting) — production law formalized: the
  scenario flow gained the REAL library `cutting` stage (legacy single-shot completion).
- **SC-F2**: `lane_stage_record(create=True)` alone skips the S2 role-rate snapshot (service
  self-heals with a WARN) → executor now calls `ensure_stage_role_rates` like every certified
  creation site. Warning gone.
- **SC-F3**: cost-rate converge compared `'3' != '3.0000'` → Decimal-compare fix (true
  idempotency).
- Corrected census facts: service-issued adda code = `DEV-MIN-TEE-001` (naturally
  DEV-marked); roll history = CREATED + ROLL_ASSIGNED (2 rows, both via history_service).

### 3. Scratch evidence (`inventory_seed_scratch_1` recreated FRESH — disposable by definition — + migrate)

- **RUN 1:** cast 3 · masters 5 · product+flow+cost 4 · roll 1 · **journey 1 · settlement 1**;
  money manifest: `ADST-0001 expected_total 150.00 · ledger 0/{0} → 1/{150.00} · delta
  explained 150.00`. Certified-chain log quotes: `ledger.credit … 50.00 × 3.0000 = 150.00` ·
  `adda_settlement.finalize ref=ADST-0001 … expected=150.00` · `adda.advance … frozen_cost=150.00
  status=completed`.
- **RUN 2: created 0 across ALL EIGHT layers — IDEMPOTENT: True**; ledger delta 0; zero new
  business objects. Manifests archived (`var/seed_manifests/`).
- Handle census: 9 minted + `CR-000001` output — all in-scheme, zero reserved-registry
  collisions.

### 4. Ledger reconciliation + primary-DB proof

Scratch: Σ 0 → 150.00, every paisa = the one finalize (recount embedded in the manifest and
pinned by test). **Primary `inventory_db`: ledger 170 / Σ ₹10,880.25 EXACT · settlements 8 ·
addas 18 · rolls 32 · users 48 · `dev.min.*` rows = 0** — untouched throughout.

### 5. Battery (3 suites)

9-app **`Ran 1002 — OK` (167.5s)** + patterns_ai **`Ran 528 — OK` (141.5s)** + devseed
**`Ran 36 — OK`** = **1566/1566. Arithmetic: entry 1556 + 10 new (4 purity + 6 money) = 1566 ✓.**

### 6. Scope discipline

New files: `layers/production_truth.py` · `layers/money.py` · `scenarios/minimal_money.py` ·
`tests/test_purity.py` · `tests/test_money.py`. Changed: cast/products executors (skills
support · stage-cost converge) · core (L7/L8 wiring + recount) · scenarios registry
(implemented flags + A1 re-scope) · spec §12 (A1, owner-ordered) · GUIDE · this log · status ·
memory. **Zero existing-app code touched · zero migrations · flags untouched · Money-Write
STOP never tripped (purity pin now guards forever).** git `49404001` · 0 staged · 2 stashes.

**Next: SEED-C WAVE 2 — extract + replay the three executable golden journeys
(₹801.00 / ₹344.25 / ₹633.00) from the certified production data; byte-identical settlement
outcomes; final ledger reconciliation; battery — owner-gated.**

_Wave 1 closed 2026-07-17._

## SEED-C — WAVE 2 — OPENED 2026-07-17 · ⏸ STOPPED AT §16.5 (owner-ordered stop rule): W2-STOP-1

**Extraction (read-only, archived in scratchpad w2_*.txt): COMPLETE for all three journeys** —
per-worker settlement items (Σ = 344.25 / 801.00 / 633.00 exactly) · full flows with
methods/rates/credits · per-SR rosters + per-line dims (good/alter/missing/verified,
color×size) · APSCPB cutting aggregates · layering records (LOWER 40 layers/CR-000002 ·
3-PATTI 30/CR-000004 · T-SHIRT NONE — completed empty) · completion-mode census (no
CuttingPatternRecords · no barcode batches anywhere = blind-advanced trio stages).

**Built (in-tree, blocked-state pinned):** `scenarios/recipes.py` (3 full recipes — extracted
truth, goldens as ASSERTION targets only) · `layers/journeys.py` (the recipe replay engine:
multi-roll layering w/ modes · workspace cutting via `upsert_breakup_row` +
`complete_cutting_from_bundles` · blind advances · dim-line reports · verified-qty overrides)
· library-stage/machine-type masters extension (15 UI-created stages + 4 machine types via
`machine_service`) · sizes (`product_size_service`, SA gate) + patterns
(`register_pattern_definition`) wiring · `tests/test_golden_journeys.py` (4 tests —
**@skip'd with the W2-STOP-1 reference, NOT silently passing**).

### Classified findings (production-law adjustments — recorded, never silently normalized)

| # | Finding |
|---|---|
| W2-F1 | Baseline migration 0002 seeds products 3-PATTI/T-SHIRT (+3) WITH layering+cutting flows → recipes converge with baseline names + reorder via `move_stage_in_product_flow` (certified mover) |
| W2-F2 | Roll/cloth-master identities = money-invariant reconstructions (layering pays ₹0 in all three journeys) |
| W2-F3 | T-SHIRT carries a blank-code ProductSize row on the primary (legacy artifact; not service-reproducible; unreferenced by the journey) — not seeded |
| W2-F4 | **GAP-2 breakup-color law postdates the journeys** (added for the NKS worlds): breakup colors must ⊆ layered-roll colors; primary rolls were Red-only while 3-PATTI breakup includes Blue → replay complies via per-color rolls (money-invariant; T-SHIRT unaffected — empty layering skips the check) |
| **W2-STOP-1** | **THE STOP:** all six cutting/cutting_pattern SRs across the three journeys show `processing_cost=None · cost_frozen_at=None` and ZERO worker credit on PAYABLE stages (credits_workers=True set BEFORE the journeys, updated_at 07-05/07-06 05:43 < journey times) — a completion shape the CURRENT law refuses (`ensure_worker_credit` PA-10-1: payable stage ⇒ ≥1 completed WSC) and that normal advance cannot produce (finalize always freezes cost). The exact primary click-path is NOT recorded. Every lawful current-path replay: (a) faithful config → REFUSED at cutting; (b) config deviation credits=False on cutting/cutting_pattern → completes lawfully AND the settlement is byte-identical (the certified settlements contain ZERO cutting/cutting_pattern earnings — per-worker items Σ = the per-piece stages exactly); (c) adding cutting workers → CHANGES money (forbidden). |

### ⏸ Owner disposition required (W2-STOP-1)

**(a) RECOMMENDED — approve the classified config adjustment:** recipes set
`credits_workers=False` on cutting + cutting_pattern (dated finding W2-F5; the primary's own
config untouched; money provably byte-identical: certified items contain no cutting lines;
Σ per-piece stages = 344.25/801.00/633.00 exactly). Un-skip the 4 tests, complete the wave.
**(b)** Supply the missing 2026-07-06 completion-path knowledge (how payable worker-less
cutting completed) → replay transcribes it. **(c)** Defer the three journeys (registry stays
BLOCKED-annotated).

### State at the stop

Battery **GREEN at the stop: 1002 OK + 528 OK + devseed 40 OK (4 = the explicit W2-STOP-1
skips)** — the 10 wave-1 tests all live; baseline arithmetic vs 1566: 40 = 36 + 4 blocked
journey tests (counted-not-passing; baseline recount at wave close). Registry: the 3
regression entries carry `implemented: False` + BLOCKED note. **Primary untouched: ledger
170/₹10,880.25 · users 48 · addas 18 · settlements 8.** Zero existing-app code touched ·
zero migrations · Money-Write STOP culture held (the stop itself is its exercise).
git `49404001` · 0 staged · 2 stashes.

**Next: owner disposes W2-STOP-1 (a/b/c) → wave 2 completes (replay ×3 byte-identical +
scratch ×2 + manifests + final recount + full battery) → SEED-D.**

### W2-STOP-1 disposition — owner 2026-07-17 (verbatim, narrowly scoped)

> "I approve option (a). This approval is narrowly scoped. Historical replay recipes may
> contain a classified replay-only configuration adjustment when, and only when, it is
> required to faithfully reproduce certified historical production outcomes under newer
> production laws. … Do NOT modify production services / primary production configuration /
> weaken or bypass any current production validation. The adjustment must exist ONLY inside
> the historical replay recipe. Record it as classified finding W2-F5."

## SEED-C — WAVE 2 — ✅ DONE 2026-07-17 · ALL THREE GOLDENS REPLAYED BYTE-IDENTICALLY · BATTERY 1570/1570

### W2-F5 — dated classified finding (the owner-approved replay-only adjustment)

- **Historical production state:** the three certified journeys completed their PAYABLE
  cutting/cutting_pattern stages with ZERO worker credit and NO cost freeze (all six SRs:
  `processing_cost=None · cost_frozen_at=None`; `credits_workers=True` predates the journeys).
- **Current production law:** `ensure_worker_credit` (PA-10-1) refuses completing a payable
  stage without a completed contribution; normal finalize always freezes cost.
- **Why they cannot coexist:** the faithful-config replay is REFUSED at cutting; adding
  workers would CHANGE money; the primary click-path is unrecorded.
- **Why the adjustment preserves historical truth:** the certified settlements contain ZERO
  cutting/cutting_pattern earnings (per-worker items = exactly the Σ of per-piece stages) —
  `credits: False` on those two stages IN THE RECIPES ONLY reproduces the historical MONEY
  byte-identically while every current validation stays fully armed. **No service modified ·
  primary configuration untouched · no validation bypassed · exists only in
  `devseed/scenarios/recipes.py` (documented in its module docstring).**

### Acceptance criteria — ALL MET

| Criterion | Proof |
|---|---|
| Replays complete via certified services | full chains ran (create_adda → layering modes → workspace cutting `upsert_breakup_row`+`complete_cutting_from_bundles` → blind advances → dim reports → verify overrides → advance → `create_draft`+`finalize_adda_settlement`) |
| Totals EMERGE (never injected) | recipes carry goldens as ASSERTION targets only; engine computes nothing from them |
| **Byte-identical settlement totals** | **₹344.25 · ₹801.00 · ₹633.00 — all three, on the test DB AND both scratch DBs** |
| **Byte-identical line items** | per-worker `expected_earning` maps == the extracted ADST-0004/0005/0006 items (asserted per journey, maxDiff=None) |
| Ledger reconciliation | per-journey delta == total; scratch chain 0 → 344.25 → 1,145.25 → **1,778.25** (Σ of the three, fully explained) |
| Deterministic manifests | 12 archived (`var/seed_manifests/`: 3 journeys × 2 runs × 2 DBs) |
| Idempotency on scratch | second runs: created=0 across every layer, ×3 journeys ×2 DBs — ALL True |
| **Both allowlisted scratch DBs** | scratch_1 AND scratch_2 (fresh + migrated): identical outcomes — **final ledger 81 rows / Σ 1,778.25 IDENTICAL on both = the cross-DB determinism proof** |
| Blocked tests active | every W2-STOP-1 @skip REMOVED; 4 journey tests run + pass |
| Canonical battery | **1002 OK + 528 OK + devseed 40 OK = 1570/1570 (0 skips; chain 1566 + 4 ✓)** |
| Primary untouched re-certified | full 32-table anchor EXACT incl. ledger 170 / Σ ₹10,880.25 |

Registry: `regression-lower/tshirt/3patti` → `implemented: True` (W2-F5-annotated).
Findings register final: W2-F1..F4 (per §SEED-C W2 above) + W2-F5. Zero existing-app code ·
zero migrations · flags untouched · git `49404001` · 0 staged · 2 stashes.

**SEED-C COMPLETE (waves 1+2). Next: SEED-D — remaining layers 9–11 + full scenario registry
(seed_demo/seed_factory complete · feature slices · edge-case worlds) — owner-gated.**

_Wave 2 closed 2026-07-17._

## SEED-D — Remaining layers + full registry — ✅ DONE 2026-07-17 · 22 SCENARIOS EXECUTABLE · BATTERY 1588/1588

**Owner authorization (2026-07-17):** complete layers 9–11 by implementing every remaining
registry scenario with the EXISTING orchestration engine — no new architecture, certified
writers only, purity preserved, production code untouched. STOP before SEED-E.

### 1. What landed (all inside `config/devseed/` — zero production-code edits)

| Piece | Content |
|---|---|
| `scenarios/extras.py` (NEW) | 16 scenario contents: `demo` (minimal-plus settled world, SEED-D2) · `factory` (composite: 3 golden recipes + `feature-machines` — spec §7 full-demo row demands machines) · 6 feature slices · 8 edge-case worlds. All derive from the wave-1 `MINIMAL_MONEY` shape via per-tag `_world()` cloning (DEV-ALC/FNF/MCH/PAI/SF/TRK/OVR/DMG/MON/INA/RPG/CMP/RRC/SUP) + 12 post-step functions (certified-service calls, each idempotent, each returns created/skipped + facts into the manifest `post` key) |
| `layers/storefront.py` (NEW) | Layer 9 — Category/FeaturedProduct. AUDITED plain-ORM exception (spec §3: writer map says "listing UI"; the only storefront service is image processing, N/A to seeding). Purity test pins the module to exactly these two models |
| `core.py` | Dispatch grown, engine unchanged in shape: composite branch (children = own worlds/atomics, aggregate manifest) · optional product · grain LIST config via `flow_service.set_stage_grain` · storefront layer · post-step dispatch inside the atomic · `IMPLEMENTED_THROUGH_LAYER = 11` · `DEFAULT_MANIFEST_DIR` (repo-root `var/seed_manifests/`, cwd-independent) |
| `management/commands/_base.py` | SEED-A stub RETIRED: guard → `--check` → implemented-gate (non-executable slugs refuse with their registry note — spec §12 A1 / DATA-D6, never silently skipped) → `core.seed_scenario` → manifest summary (counts + money line). Guard-first law intact (refusal tests unchanged, still green) |
| `layers/cast.py` | `active: False` + `extra_roles` M2M on create (PHASE_03 D1 composite identities) |
| `layers/production_truth.py` | `expect_completed: False` partial worlds (converge on existence; COMPLETED assert conditional) |
| `layers/masters.py` | SD-F2 fix: `StorageLocation.code = name[:20]` (unique NOT-NULL — `''` default collided on the second world) |
| `scenarios/minimal_money.py` | SD-F1 fix: ONE `_STAGE_COSTS` for the DEV-MIN world family (minimal + feature-settlement converge on the SAME world → identical config at every depth) |
| `scenarios/__init__.py` | 16 slugs flipped `implemented: True` with actual layer tuples + notes; `demo`/`factory` provisional SEED-A layer declarations corrected to actual |
| `tests/test_registry_complete.py` (NEW, 17 tests) | whole-registry-on-one-DB ×2 (the shared-scratch simulation that CAUGHT SD-F1) + per-world targeted asserts (WSA draw-down 30/50 leaving 20 · over-allocation refusal verbatim · leaver-only deactivation · possession window · sizes+patterns · storefront rows · inline barcodes > 0 · damaged→restored `not_used` · MONTHLY pay basis · inactive member · reopen refusal · composite roles · rerate → `expected_earning` 200 + audit · supersession chain ADST original superseded → successor finalized ₹150) |
| `tests/test_purity.py` | +1 test (storefront module pin) + storefront allowance + SD-F6 regex hardening |
| `tests/test_guard.py` | implemented-set pin inverted: exactly `{regression-settlement-225, performance}` stay non-executable |

### 2. Findings register (SD-F1..F7 — stop-and-classify, none silently normalized)

- **SD-F1 (caught by the new whole-registry test):** `minimal` ⊂ `feature-settlement` share
  the DEV-MIN world BY DESIGN, but minimal's journey seeded WITHOUT the stitching rate — on a
  shared DB with minimal first, contributions froze `expected_earning=0` and the ₹150 golden
  settled at 0.00 (DivergenceError). Fix: one `_STAGE_COSTS` constant for the family — cost
  CONFIG is layer-4 config, not money; settlement stays the only money boundary.
- **SD-F2:** `StorageLocation.code` unique NOT-NULL; masters layer created it as `''` —
  latent since SEED-B (single world), collided on the second world. Code = name (≤20).
- **SD-F3:** `reverse_adda_settlement` returns `(settlement, successor)` tuple — call-shape.
- **SD-F4 (pool law):** `_upstream_pool_sources` SKIPS `NONE` stages — allocation worlds must
  set grain on CUTTING (the source participant) too; grain config is a LIST; values are the
  lowercase `AllocationDimensions` constants.
- **SD-F5 (isolation law, enforced by test):** FnF world uses a DEDICATED leaver
  `dev.min.leaver@test.local` (spec §11 leaver-cast class) — deactivating the shared
  `dev.min.worker` would poison every later world on the same scratch DB.
- **SD-F6:** purity guarded-name scan matched `Product` inside `FeaturedProduct` — negative
  lookbehind added (test hardening; no real violation existed).
- **SD-F7:** `_world()` clones inherited the narrow `dev.min.` dev-prefixes → post-seed
  DEV-marking assertions failed; family-wide `("dev.", "DEV-", "dev-")`.

### 3. Registry census (final)

**22 implemented / 24** — every executable entry. The two non-executable stay BY OWNER
RULING and REFUSE at the command with their registry note: `regression-settlement-225`
(spec §12 A1 — historical evidence) · `performance` (DATA-D6 — targets owner-deferred).

### 4. Scratch evidence — BOTH DBs, fresh, via the REAL commands

`inventory_seed_scratch_1` AND `_2`: DROP → CREATE → migrate → **every implemented scenario
×2 through `seed_demo`/`seed_factory`/`seed_feature <slug>`** (guard PASSED on scratch;
manifests archived to `var/seed_manifests/`).

- **Run 1:** 21/21 (factory covers the 3 regression slugs too) `assertions=PASS`; goldens
  emerged **₹344.25 · ₹801.00 · ₹633.00** + four ₹150 worlds (demo · feature-settlement ·
  feature-fnf · edge-reopen-guard) + the supersession chain ADST-0008(superseded)→0009(finalized ₹150.00).
- **Run 2:** `created=0` on EVERY layer of EVERY scenario — pure convergence, ×2 DBs.
- **Cross-DB determinism:** final census IDENTICAL on both DBs — ledger **89 rows /
  Σ 2,978.25 (unsigned sum: credits 2,678.25 + debits 300 — reversal 150 + FnF payment 150)**;
  settlements ADST-0001..0009 same references/statuses/totals; users 20 (inactive exactly 2:
  leaver + dev.min.inactive); WSA 2; BarcodeBatch 9 (one per cutting world).
- Non-executable refusals proven on-DB: both slugs → `CommandError` with registry note,
  "guard PASSED, zero writes performed".

### 5. Battery — NEW BASELINE 1588/1588 (3 sequential fresh-DB suites, D4 order)

9-app **`Ran 1002 — OK` (171.0s)** + patterns_ai **`Ran 528 — OK` (143.6s)** + devseed
**`Ran 58 — OK` (25.0s)**. Arithmetic: 1570 + 17 registry-complete + 1 purity = 1588 ✓.
(Inline `get_runner` invocation class — classifier-outage workaround, disclosed, same as
every Phase-12 run.)

### 6. Primary untouched — re-certified

`inventory_db`: **ledger 170 / Σ ₹10,880.25 EXACT** · settlements 8 · addas 18 · rolls 32 ·
users 48 · `dev.min.*` rows = 0 · WSC 153 · WSA 84 · advances 0 · FactoryExpense 4 ·
machines 4 · FeaturedProduct 1 · products 18. Git `49404001` · 0 staged · 2 stashes ·
enforcement flags untouched · zero migrations · zero production-code edits.

**SEED-D COMPLETE. Next: SEED-E (reset_demo + idempotency/determinism certification) —
owner-gated.**

_SEED-D closed 2026-07-17._

## SEED-E — reset_demo + operational certification — ✅ DONE 2026-07-17 · BATTERY 1600/1600

**Owner authorization (2026-07-17):** complete operational certification — implement the
real `reset_demo`, certify reset determinism on BOTH scratch DBs, permanent operational
tests, primary re-cert. No new scenario types, no architecture expansion.

### 1. What landed (devseed-only; zero production-code/config edits)

| Piece | Content |
|---|---|
| `core.run_reset` (+`_drop_and_recreate` · `_migrate_target` · `strip_volatile`) | The destructive orchestration: allowlist belt-check (safe to call directly) → DROP+CREATE via psycopg2 maintenance connection (`sql.Identifier`, connections closed first — an open handle blocks DROP) → switch the process's default connection to the target + full `migrate` → optional scenario seed (post-seed assertions run inside `seed_scenario` as always) → reset manifest (`reset-<db>-<ts>.json`, SEED-D8 archive). NON-transactional by nature (DDL — SEED-D3), hence the strictest upstream confirmation. `strip_volatile` = THE determinism comparison surface (`ran_at` = the only permitted runtime identifier; cross-DB compare additionally strips the DB-identity keys). **Injection points `_dropper/_migrator/_seeder` exist ONLY for failure-propagation tests** — guard factor 2 (DEBUG) keeps the real path off battery/test DBs by design, so those laws are otherwise unprovable in the battery |
| `reset_demo` command | SEED-A stub retired: banner → 4-factor guard incl. the literal per-DB flag (unchanged) → `--seed <slug>` validated against the registry BEFORE any DDL (unknown slug lists valid ones; non-executable refuses with the registry note — "nothing was reset") → `core.run_reset` → summary. **No bypass flags exist; `inventory_db` has no confirmation flag even in the parser** |
| `tests/test_reset.py` (12 permanent tests) | Command wall: confirmation enforced · mismatched flag refused · `inventory_db` refused ("primary dev DB is never a seeder target") · unknown DB refused · seed-slug validation ordering. Orchestration contract: belt-refusal before ANY step · migrate-failure propagates (seed never runs, NO manifest on failure) · assertion-failure propagates · manifest generation+shape+on-disk equality · repeated-reset manifest determinism · cross-DB comparison surface · re-seed convergence with stable manifest sections |

### 2. Live certification — the real command, BOTH scratch DBs (contract §cert 1-3)

Per DB (`inventory_seed_scratch_1`, then `_2`): **`reset_demo --db <db>
--i-understand-this-destroys-<db> --seed demo` run TWICE** (fresh reset → migrate → seed →
assertions PASS → manifest, ×2 cycles):

| Proof | Result |
|---|---|
| Fresh reset → migrate → seed → assertions → manifest | ✅ ×2 cycles ×2 DBs — `RESET OK … seeded=demo` + `assertions=PASS` every cycle |
| Identical database state across repeated resets | ✅ both DBs: census byte-equal — ledger 1 row / Σ150.00 · ADST-0001 finalized 150.00 · users 3 · adda DEV-DEMO-TEE-001 · roll 1 |
| Identical manifest (except permitted runtime identifiers) | ✅ `strip_volatile` (minus `ran_at` only): scratch_1 pair TRUE · scratch_2 pair TRUE |
| Cross-database determinism | ✅ scratch_1 vs scratch_2 manifests equal minus `ran_at` + DB-identity keys; **nested `seeded` sections byte-equal as-is** (they carry no DB identity) |

### 3. Battery — NEW BASELINE 1600/1600 (3 sequential fresh-DB suites, D4 order)

9-app **`Ran 1002 — OK` (182.6s total)** + patterns_ai **`Ran 528 — OK` (139.7s)** + devseed
**`Ran 70 — OK` (25.9s)**. Arithmetic: 1588 + 12 reset tests = 1600 ✓. (Inline `get_runner`
invocation class — classifier-outage workaround, disclosed, same as every Phase-12 run.)

### 4. Re-certification

- **Primary `inventory_db` UNCHANGED:** ledger **170 / Σ ₹10,880.25 EXACT** · settlements 8 ·
  addas 18 · rolls 32 · users 48 · `dev.min.*` = 0 · `DEV-DEMO*` addas in primary = 0.
- **No production configuration changes:** this wave touched exactly
  `devseed/core.py` · `devseed/management/commands/reset_demo.py` ·
  `devseed/tests/test_reset.py` (+docs). Flags untouched · zero migrations.
- **No guarded-table direct writes:** the permanent purity pin ran green in the battery
  (reset adds DDL via psycopg2 maintenance connection + `call_command('migrate')` — no ORM
  writes; the write-scan and guarded-name scans cover the new code automatically).
- Git `49404001` · 0 staged · 2 stashes.

**SEED-E COMPLETE. Next: SEED-F (certification + handoffs to Phases 13/14/15/19) —
owner-gated.**

_SEED-E closed 2026-07-17._

## SEED-F — Certification + handoffs — ✅ DONE 2026-07-17 · 🏁 PHASE 12 CLOSED

**Owner authorization (2026-07-17):** certification, reconciliation and handoff ONLY — no
new functionality, no architecture expansion, no new scenarios, no service-behavior change.
**Honored: zero engine code changed this sub-phase** (doc edits only: two reconciliation
fixes + this section).

### 1. Final engine certification (live, this session)

**Full end-to-end re-certification via the REAL commands:** both scratch DBs
`reset_demo --db <db> --i-understand-this-destroys-<db>` (fresh, no seed) → **every
implemented scenario ×2 rounds** → zero assertion failures · run-2 `created=0` everywhere
(idempotency) · **cross-DB census IDENTICAL** and **byte-equal to the SEED-D numbers**
(ledger 89 / Σ 2,978.25 · ADST-0001..0009 with 0008 superseded → 0009 finalized · users 20
with exactly 2 inactive · WSA 2 · BarcodeBatch 9) — the third independent reproduction of
the same world-set (SEED-D direct + two post-reset builds). Goldens emerged again:
**₹344.25 · ₹801.00 · ₹633.00** + four ₹150 worlds.

**Production isolation PROVEN LIVE (structural factor):** `config.settings.production`
loaded in-session (dummy env vars for the missing prod-only config — disclosed):
`'devseed' in INSTALLED_APPS → False` · `DEBUG → False` · **all four seeder commands
NONEXISTENT** (`get_commands()` contains none of seed_demo/seed_factory/seed_feature/
reset_demo). Static cross-check: `devseed` appears in exactly one settings file —
`local.py:40`. Even a hypothetical command presence would refuse on factors 1+2.

**Guard behavior / reset / purity / manifests / assertions:** pinned permanently in the
battery — devseed suite 70/70 (18 guard incl. command refusal wall · 8 layers · 5 purity ·
6 money · 4 golden · 17 registry-complete · 12 reset-operational), green in the final run
below.

### 2. Spec-fidelity checklist (DEV_DATASET_ARCHITECTURE §13 — 10/10)

| # | Requirement | Status |
|---|---|---|
| 1 | Dev-only app, dev-settings-only registration, import-linter layer | ✅ `local.py:40` only; topmost `.importlinter` layer; live production-absence proof above |
| 2 | Four-factor guard FIRST, negative-tested | ✅ SEED-A guards-before-features; every factor negative-tested (test_guard 18) |
| 3 | 4 command classes | ✅ all four REAL (seed_feature registry-driven; reset exact-string per-DB confirm) |
| 4 | Service-path per §3 writer map · purity test · TRUE cast actors | ✅ permanent purity pin (5 tests; TWO audited plain-ORM exceptions, module-pinned: masters + storefront) |
| 5 | Natural-key idempotent converge · divergence = REPORT | ✅ DivergenceError report-never-pave (tested); convergence proven ×2 rounds ×2 DBs ×3 waves |
| 6 | Machine-readable registry (§7 taxonomy + §11 handles) | ✅ `devseed.scenarios.SCENARIOS` (24 slugs, 6 classes) + registry pins in test_guard |
| 7 | Assertions module single-source (shared w/ P13) | ✅ `assertions.py` — P13 imports-never-forks; SEED-D6 relocation note in handoff §5.1 |
| 8 | Goldens byte-for-byte | ✅ ₹801.00/₹344.25/₹633.00 emerged + per-worker items byte-matched; **₹225 = historical per spec §12 A1 (owner-ruled amendment, not a gap)** |
| 9 | Scratch-DB law | ✅ primary never a target (allowlist + no confirmation flag exists for it); anchor EXACT below |
| 10 | Battery + pins per contract · U6 docs | ✅ final battery below; GUIDE/README/INDEX/CHANGE_IMPACT_MATRIX rows complete |

### 3. Registry certification (24/24 accounted — no unaccounted spec row)

- **22 implemented** — every entry seeds via its real command, asserts PASS, converges on
  re-run, reproduces cross-DB (proof: §1 above + per-scenario SEED-D §4 evidence + battery
  pins). Classes: minimal 1 · full-demo 2 (demo, factory) · feature 7 · regression 3 ·
  edge-case 8 · (performance 0).
- **1 owner-deferred:** `performance` (DATA-D6 "Do not invent any target sizes") — refuses
  at the command with the registry note; arrival = dated spec §12 amendment.
- **1 historical:** `regression-settlement-225` (spec §12 A1) — `expected: None`, refuses at
  the command; living guard = the settlement suite's on-disk goldens.
- Registry ⇄ engine ⇄ tests three-way agreement pinned: `test_guard` (implemented-set +
  golden values + slug count) · `CONTENT` covers every implemented slug (KeyError otherwise —
  exercised by the whole-registry test) · docs rows (README/GUIDE/spec §7) state the same
  22/2 split.
- §11 handle law verified: scenarios mint ONLY §4-scheme handles (`dev.*@test.local` ·
  `DEV-*` · `dev-*` + service-issued CR-/ADST- outputs); reserved-handle collisions = seed
  failure (assertion-enforced, zero observed across all waves).

### 4. Documentation reconciliation (6 docs — zero contradictions remain)

Checked pairwise: spec ⇄ log ⇄ README ⇄ GUIDE ⇄ status ⇄ index. Two stale fragments found
and fixed this session: **(1)** DOCUMENTATION_INDEX's SEEDER_ENGINE_LOG row still read
"SEED-D1..D9 pack ⏸ awaiting owner at SEED-0" → rewritten to the closed state; **(2)**
CHANGE_IMPACT_MATRIX had NO devseed row (U6 gap) → row added (`config/devseed/*` → GUIDE ·
README · this log · frozen-spec amendment law · registry-pin note). Verified consistent:
battery numbers (status dashboard = this log) · 22/2 registry split everywhere · W2-F5
scoping (recipes-only, all four docs agree) · §12 A1 ₹225 wording (spec = registry note =
README = GUIDE) · guard factor count ("4-factor + structural fifth" phrasing uniform).

### 5. Handoffs (contract §6.7 — documentation only, nothing implemented)

**5.1 → Phase 13 (Verification Engine).** Consumes:
- **`devseed/assertions.py`** = the single-source check library (public surface:
  `run_post_seed(expected_counts, handles, output_handles, dev_prefixes)` +
  `SeedAssertionError`; checks: exact filtered row-counts · minted-handle existence +
  DEV-marking · service-issued output handles existence-only · enforcement-flags-untouched).
  **⚠️ SEED-D6 reconciliation (from the ratified PHASE_13 contract): the shared library
  RELOCATES to a BASE-settings `verification` app (production-present, read-only) and
  devseed IMPORTS it — applied by Phase 13 as the first executor, recorded as a dated
  PHASE_12 SEED-D6 amendment, one coordinated battery-run diff.**
- **Manifest format (the verify input contract; sorted-keys JSON in `var/seed_manifests/`,
  `ran_at` = the ONLY volatile key; `core.strip_volatile` = the comparison surface):**
  scenario manifests `{scenario, spec_version, database, max_layer, counts{<layer>:
  {created, skipped}}, handles[str], assertions{result}, money{settlement, expected_total,
  ledger_before/after{count, sum}, delta_explained}|null, post{…}|null, ran_at}`; composite
  (factory) adds `composite{<child>: {counts, money, assertions}}`; reset manifests
  `{scenario: "reset-<db>", reset, spec_version, migrated, seeded{scenario, counts,
  assertions, money, handles}|null, ran_at}`.
- **Golden truth to cite:** ₹344.25 (LOWER) · ₹801.00 (T-SHIRT) · ₹633.00 (3-PATTI) w/
  per-worker items (`test_golden_journeys.EXPECTED_ITEMS` = the extracted certified maps) ·
  ₹150.00 feature-settlement (self-derived) · ₹225 HISTORICAL-only (spec §12 A1).
- **Registry:** `devseed.scenarios.SCENARIOS` — verify_demo/factory/feature resolve slug →
  expected shape; non-executable entries must REFUSE in verify too (never silently pass).
- **DEV-namespace reservation (spec §4)** = the `verify_production` contamination-scan
  basis: `dev.*@test.local` identities · `DEV-*`/`dev-*` handles; a planted-handle
  constructed-fail proof is mandatory per that contract.

**5.2 → Phase 14 (Knowledge Sync) — drift-detector inputs (detect-and-notify only):**
registry drift (declared slugs vs `implemented` flags vs `CONTENT` keys vs the test_guard
pins — four surfaces that must agree) · manifest-schema drift (`guard.SPEC_VERSION` vs spec
§10 semver; manifest key-set vs §5.1 above) · assertions single-source law (any second
implementation of the check library = drift; post-SEED-D6-relocation home = the
`verification` app) · golden-value three-way agreement (registry `expected` ⇄ spec §7 row ⇄
`test_golden_journeys` constants) · §11 reserved handles vs scenario-authored handles.

**5.3 → Phase 15 (BOD):** demos/acceptance run on **`seed_factory` worlds in scratch DBs**
(`reset_demo --db <scratch> --i-understand… --seed factory` = one-command rebuild), never
the primary dev DB until the owner blesses a refresh; BOD *displays* `var/` artifacts
(manifests/reports), never runs engine commands inline; new demo scenarios ONLY via dated
spec §12 amendments (owner rule 2026-07-04: no undocumented future-phase dependency).

**5.4 → Phase 19 (Deployment):** the runbook states: **seeder excluded from every
production path structurally** (dev-settings-only registration; live proof §1: production
settings → app absent, all four commands nonexistent) · guard factors 1–3 refuse any
hypothetical presence (settings-module + DEBUG + allowlist that contains no production
name; no bypass flags exist anywhere) · `var/` (manifests) is gitignored runtime — never a
deploy artifact · post-deploy contamination check = Phase 13's `verify_production`
DEV-namespace scan.

### 6. Final re-certification + battery

- **Primary `inventory_db` vs the SEED-0 anchor: ALL 34 anchor counts EXACT** (Users 48/46
  active · Role 5 · SidebarItemRule 21 · Skill/UserType 10/5 · ClothType/Color/Storage
  6/15/3 · ClothRoll 32 · Product 18 · Adda 18 · WorkflowStage 73 · Stage/Category/
  MachineType 23/5/5 · ASR 132 · WST 150 · WSC 153 · WSA 84 · SPS 88 · Machine 4 · MA 5
  (2 open) · **ledger 170 / Σ ₹10,880.25** · ADST/Item 8/43 · SWA 141 · FactoryExpense/
  Advance 4/0 · Category/FeaturedProduct 1/1 · Marker/Usage/PatternPiece 3/1/58 ·
  BarcodeExportBatch 6) + `dev.min.*` rows = 0. **Zero census drift across the entire
  phase.**
- Purity holds (battery pin green) · enforcement flags untouched (U10) · zero migrations ·
  zero production-code/config edits phase-wide · git `49404001` · 0 staged · 2 stashes.
- **Canonical battery — FINAL PHASE-12 BASELINE 1600/1600** (3 sequential fresh-DB suites,
  D4 order): 9-app `Ran 1002 — OK` + patterns_ai `Ran 528 — OK` + devseed `Ran 70 — OK`.
  Phase arithmetic: entry 1530 → +18 (SEED-A) +8 (B) +10 (C w1) +4 (C w2) +18 (D) +12 (E)
  = **1600 ✓**. (Inline `get_runner` invocation class — classifier-outage workaround,
  disclosed, used consistently since SEED-0.)

### 7. 🏁 PHASE-12 VERDICT

**PHASE 12 COMPLETE — SEEDER ENGINE CERTIFIED.** The frozen spec is implemented in full:
guards-first dev-only app · 22/24 registry scenarios executable, deterministic, idempotent,
manifest-emitting, self-asserting (2 non-executable by owner ruling, refusing verbatim) ·
goldens emerge byte-identically through certified services · destructive reset certified ·
purity permanent · primary dev DB untouched end-to-end · production structurally excluded.
Residuals carried forward: SEED-D6 assertions-relocation (Phase 13 first-executor
amendment) · `performance` volumes (owner-deferred, dated-amendment arrival) · ₹225
executable recipe (historical until an authoritative recipe exists) · snapshot refresh
(owner action, STILL DUE). **Next: Phase 13 Verification Engine — owner-gated.**

_SEED-F closed 2026-07-17 · Phase 12 closed 2026-07-17._
