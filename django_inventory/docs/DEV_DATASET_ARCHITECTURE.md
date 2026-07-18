---
id: dev-dataset-architecture
type: topic-canonical
status: frozen-v1
owner: handwritten
scope: development dataset — the frozen architecture spec (layers · service-path seeding law · handles · scenarios · reset/safety) that Phase 12 implements and Phase 13 verifies
anchors: docs/campaign_contracts/PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md, docs/FACTORY_OPERATIONS_MASTER.md, docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json
verified: 2026-07-17
---

# DEVELOPMENT DATASET ARCHITECTURE — specification (v1.0.0, 🔒 `frozen-v1`)

> **Status: 🔒 `frozen-v1` — owner-accepted + frozen at DSA-C 2026-07-17** (pre-freeze
> consistency pass ALL GREEN: zero obsolete-world references · golden values source-verified ·
> 13/13 register · zero provenance violations — evidence: PHASE_11 contract §DSA-C).
> Changes henceforth = dated amendments in §12 under DOC_STANDARDS §20 discipline.
> Phase 12 implements THIS document exactly.
> Authored at Phase-11 DSA-B under the ratified Design Record DATA-D1..DATA-D9 (all ACCEPT
> 2026-07-17; D6 performance volume targets DEFERRED) + dated amendment A1 (world truth =
> [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md) §12) + the DSA-A census
> ([PHASE_11 contract evidence](campaign_contracts/PHASE_11_DEVELOPMENT_DATASET_ARCHITECTURE.md)).
> **Provenance discipline:** every rule is labeled `[REPO <evidence>]` (transcribes certified
> reality) or `[PROPOSED→DATA-D#]` (ratified design). Zero unlabeled invention.
> **This is a DESIGN document.** Phase 12 (Seeder Engine) implements it exactly; Phase 13
> (Verification Engine) consumes §7; spec gaps found later = dated amendments here (§10),
> never silent divergence.

## 1. Philosophy `[REPO conventions + PROPOSED→DATA-D1..D9 ratified]`

Development-only (§6 guard is a hard precondition of every seeder run) · **deterministic**
(same spec version + same scenario ⇒ same world: identical natural identifiers, counts,
relationships, monetary outcomes; **auto-PKs are explicitly NOT part of the contract** —
nothing may reference them `[REPO: the pk-drift weakness class, PHASE_02/03 re-verify
warnings]`) · **reproducible from zero** (empty DB + migrations + seed = the world — the
structural fix for single-copy-dev-DB fragility; does NOT replace the Phase-0 snapshot
decision `[DATA-D9]`) · **resettable** (§8) · **idempotent** (re-running a seed converges by
natural-key upsert; zero duplicates) · **production-safe** (§6) · **never mixes with
production data** (DEV-marking invariants §4; disjoint identifier namespaces).

## 2. Layers + dependency order `[REPO structure · order DATA-D2 ratified]`

Seeding order = dependency order. Each layer names its owning app + creating path.

| # | Layer | Owning app · creating path | Census anchor (DSA-A) |
|---|---|---|---|
| 1 | **Migration baseline** — PRE-EXISTING, consumed NEVER created | accounts migrations 0016/0017 (Roles ×5, SidebarItemRule ×21) `[REPO]` | roles 5 · SIR 21 verified |
| 2 | Cast (users + roles + skills + compositions) | accounts `user_service`/UI; `extra_roles` compositions per PHASE_03 D1 | 33 `dev.*@test.local` + owner/utest/mgmt1 |
| 3 | Core master data | raw_materials masters UI/ORM (cloth types/colors/storage) · production stage library/categories/machine types (UI) | 6/15/3 · stages 23 · cats 5 · mtypes 5 |
| 4 | Products + flows | production `product_service`/`flow_service`/flow-editor UI (workflow stages incl. tracking modes, rates via `stage_rate_service`) | products 18 · WorkflowStage 73 (T-SHIRT 16-op, LOWER 13-op `[REPO FOM §9/§10]`) |
| 5 | Machines | machines `machine_service` | OL/FL/SN/EL-001 |
| 6 | Raw materials (rolls incl. financial fields) | raw_materials bulk-add service path; financial fields ONLY via the FINANCIAL_ROLES path `[REPO OWN-E 4-layer wall]` | 32 rolls (`roll_id` CR-*/GLDN-R1..6) |
| 7 | Production truth (Addas, tasks, contributions, allocations) | production `adda_service` · `worker_task_service` · `pool_service` chokepoints ONLY | Addas 18 · WST 150 · WSC 153 · WSA 84 · SPS 88 |
| 8 | Expenses + money | expense single-writers ONLY: `adda_settlement_service` · `ledger_service` (rows only ever as service OUTCOMES) · `advance_service` · `expense_service` (FactoryExpense) · `fnf_service` | ledger 170/₹10,880.25 · ADST-0001..0010 |
| 9 | Storefront | storefront listing service path (+`image_service`) | Category/FP "3 Patti" |
| 10 | AI pattern data | patterns_ai services (`pattern_design_facade`/`marker_service`/`calibration_service`/`layout_usage_service` …) | MRK-000001..3 + DEV-NICKAR chain |
| 11 | Reporting/history examples | **as SERVICE OUTCOMES of layers 2–10 only** — history tables are single-writer (`history_service`), never direct rows `[REPO U13]` | BarcodeExportBatch 6 |

## 3. Ownership — the service-path seeding law + writer map `[REPO — manifest `never_modify` + CLAUDE.md rules 4/5 + chokepoint pages; DATA-D3 ratified]`

**Every seeded row is created through the SAME write path production uses.** Raw
fixtures/SQL/`loaddata` are **FORBIDDEN for guarded tables** — a dataset that bypasses the
chokepoints seeds worlds the invariants never blessed, and every certification proof over
such a world is void. **The seeder (Phase 12) is an ORCHESTRATOR of services, not a data
loader.** Plain ORM is permitted ONLY for tables with no service owner (pure masters,
layer 3). DSA-A verified the existing dev data contains **zero fixture-born rows** — the
organic data already obeys this law.

| Guarded target | Sole writer `[REPO manifest never_modify unless noted]` |
|---|---|
| `WorkerLedgerEntry` | `config/expense/services/ledger_service.py` (CI gate 4) |
| `AddaSettlement` / `AddaSettlementItem` / era-B `StageWorkAssignment` | `config/expense/services/adda_settlement_service.py` (CI gates 4b+4c) |
| `WorkerStageTask` / `WorkerStageContribution` | `config/production/services/worker_task_service.py` (CI gate 4) |
| ALL `*History` rows | `config/tracking/services/history_service.py` |
| `processing_cost` freeze | `config/production/services/cost_service.py` |
| `WorkerStageAllocation` / `StagePoolSnapshot` | `config/production/services/pool_service.py` `[REPO CLAUDE.md S4 + chokepoint page]` |
| `FactoryExpense` | `config/expense/services/expense_service.py` `[REPO R5 sole-writer]` |
| `WorkerAdvance` | `config/expense/services/advance_service.py` `[REPO CLAUDE.md]` |
| FnF settlement legs | `config/expense/services/fnf_service.py` `[REPO OWN-C]` |
| patterns_ai truth (Marker/Usage/Outcome/pieces/layouts) | patterns_ai services (`register_pattern_definition`, usage/outcome/void paths) `[REPO MGT-G/OWN-G]` |
| Storefront Category/FeaturedProduct (+images) | storefront listing service + `image_service` `[REPO OFF-B]` |
| Machines + assignments | `config/machines/services/machine_service.py` `[REPO MGT-F-1 guard]` |
| Users/permissions | `config/accounts/services/user_service.py` / `permission_service` `[REPO rule 6]` |

## 4. Stable identifiers + DEV-marking `[REPO house conventions · DATA-D4 ratified]`

Per-family schemes (the existing house style, formalized):

| Family | Scheme | Examples (census-live) |
|---|---|---|
| Identities | `dev.<role-or-name>@test.local`, cast password `Dev@12345` `[REPO Test-Data rule 2026-07-04]` | `dev.mgr` · `dev.monthly` · `dev.acct.mgr` |
| Worlds (Addas) | `<PRODUCT>-NNN` world codes; DEV-experimental = `DEV-`-prefixed | `3-PATTI-016` · `T-SHIRT-001` · `DEV-NICKAR-001` |
| Products | UPPER house codes; DEV-experimental `DEV-*` | `T-SHIRT` · `LOWER` · `DEV-NICKAR` |
| Rolls | `roll_id` natural key (`CR-NNNNNN` intake; named series like `GLDN-R<n>` for scenario fixtures) | `CR-000001` · `GLDN-R6` |
| Machines | `<TYPE>-NNN` codes (immutable per MGT-F-1) | `OL-001` · `EL-001` |
| Settlements | `ADST-NNNN` references (service-issued) | `ADST-0006` |
| Markers | `MRK-NNNNNN` references (service-issued) | `MRK-000002` |
| Masters/stages | migration-adjacent slug codes | `layering` · `cutting_pattern` |

**Reserved-handle registry** `[census-derived — §11]`: scenarios, contracts, and probes
reference HANDLES, never PKs. Existing pk-references in closed contracts are FLAGGED for
future dated amendments at those docs' own gates (DSA-A §4 report), never rewritten by this
spec. **DEV-marking is an invariant, not a convention:** every dataset-created row is
identifiable as dataset-born by its identifier alone; the DEV namespace
(`dev.*@test.local` / `DEV-*` / the reserved handle list) is RESERVED — production data may
never legitimately carry it (→ the Phase-13 contamination check, §9).

## 5. Referential integrity `[REPO — DB CheckConstraints + service invariants]`

Integrity is **inherited, not asserted**: because seeding drives services (§3), the 26+
CheckConstraints `[REPO DB-integrity PR1/PR2]` and service invariants hold by construction.
Dataset-level additions `[PROPOSED→DATA-D2/D5 ratified]`: no dangling handle references
between scenario layers · cross-scenario isolation (a feature scenario never references
another scenario's handles unless declared as a composition in the registry) · in-world
teardown obeys soft-state-over-delete `[REPO Data/History principles 2026-06-09]`; full
reset = DB rebuild (§8).

## 6. Safety rules — the production guard `[PROPOSED→DATA-D8 ratified]`

Seeder/reset commands REFUSE unless **all four** hold: (a) settings module = the dev one ·
(b) DEBUG or an equivalent dev marker · (c) database name matches a dev allowlist ·
(d) explicit `--yes-i-know`-style confirmation for destructive resets. Plus: seeders never
appear in any deployment runbook path (Phase-19 exclusion) · dataset artifacts never ship in
a production image · the DEV identifier namespace is reserved (§4). Enforcement flags are
NEVER touched by seeding (`ENFORCE_ALLOCATION_BOUND` / `ENFORCE_SETTLEMENT_RECONCILIATION`
stay OFF — U10 `[REPO]`).

## 7. Scenario taxonomy `[REPO journeys · DATA-D5 ratified]` + validation assertions `[→ Phase-13 input]`

Six classes. Every scenario is registry-listed (name · layers used · handles created ·
assertions). Composition rule: scenarios compose only via declared registry references.

| Class | Content | Post-seed assertions (Phase-13 `verify_*` input) |
|---|---|---|
| **minimal** | 1 product + 1 flow + minimal cast + 1 roll + 1 Adda — fastest seed, default for quick dev | layer row-counts · handle completeness · DEV-marking (zero unmarked rows) · flags-OFF |
| **full demo** (`seed_demo`/`seed_factory`) | THE FACTORY: T-SHIRT + LOWER + 3-PATTI worlds with real flows (16-op/13-op `[REPO FOM §9/§10]`), cast, machines, rolls, ≥1 settled journey each | minimal-class asserts + settled-journey presence + referential spot-checks |
| **feature** (`seed_feature <x>`) | per-feature slices, each self-contained + registry-named: allocation · settlement · FnF (leaver cast `[REPO OWN-C dev.hlp.nkb]`) · machines · patterns_ai (DEV-NICKAR chain `[REPO MGT-G/OWN-G]`) · storefront · tracking-exports · **bod (amendment A2)** · **monthly-expense (amendment A3)** · **rm-expense (amendment A4)** | per-slice row-counts + handle registry + DEV-marking |
| **performance** | volume-scaled variants — **row-count targets OWNER-DEFERRED (DATA-D6 ruling 2026-07-17: "Do not invent any target sizes"); supplying them = a dated amendment here** | deferred with the targets |
| **regression** | the golden journeys WITH embedded expected values: **T-SHIRT settled ₹801.00 `[REPO FOM §10 · DB ADST-0005]` · LOWER ₹344.25 `[REPO FOM §9 · ADST-0004]` · 3-PATTI ₹633.00 `[REPO FOM §12 · ADST-0006 · amendment A1]` · the ₹225 byte-identical settlement invariant `[REPO S-series/MANUFACTURING_V1_FREEZE]`**. Seed → run the flow → totals match byte-for-byte | golden-value byte-asserts (the Phase-13 pass/fail truth) + all minimal-class asserts |
| **edge-case** | certified hard cases as reproducible worlds: over-allocation → a REAL M-6 block `[REPO OWN-C]` · damaged/restored rolls `[REPO OWN-E]` · monthly worker (`dev.monthly` handle, the pk-25 class) · inactive users · reopen-guard chains `[REPO S4-P5]` · composite-role identity (`dev.acct.mgr` `[REPO PHASE_03 D1]`) · rate-correction (`rerate_stage_role` `[REPO OWN-A]`) · settlement supersession chain (`ADST-0007→0008` class `[REPO census]`) | per-case: the certified refusal/block/outcome reproduces verbatim |

**Golden-value change control `[DATA-D6 ratified]`:** the embedded expected values encode
business truth — they change ONLY by owner approval, as dated amendments here.

## 8. Reset semantics `[PROPOSED→DATA-D7 ratified · Data/History-compatible]`

Two distinct operations, never conflated: **full reset** (`reset_demo` class) = rebuild the
dev DATABASE (drop → recreate → migrate → seed) — legitimate because it replaces the whole
world, not history within one. **In-world teardown** = ONLY via the app's designed reverse
paths (void / archive / reverse / FnF) — append-only history is never raw-deleted inside a
living world (U13 holds even in dev `[REPO]`). Resets never touch: the production DB (§6
guard) · media files unless scenario-declared · the migration baseline (layer 1).

## 9. Phase interfaces `[REPO contract §6.6 — concrete obligations]`

| Phase | Obligation |
|---|---|
| **12 Seeder Engine** | Implements THIS spec exactly: 4 command classes (`seed_demo`/`seed_factory`/`reset_demo`/`seed_feature <x>`) · the §6 four-factor guard · natural-key idempotency · §3 service-path orchestration (purity test pins zero direct guarded-table writes). Spec gaps = dated amendments here, never silent divergence. Battery-bearing per its own contract. |
| **13 Verification Engine** | Consumes §7 assertion definitions as the `verify_*` spec; regression golden values = pass/fail truth; `verify_production` uses the §4 DEV-namespace reservation as a read-only contamination check in prod. |
| **14 Knowledge Sync** | May check spec⇄seeder drift (declared scenarios vs implemented commands) — detect-and-notify; **the §11 registry + §7 scenario table are the sync-readable structured sections** (also the future graph-kind candidates recorded at DSA-0 — KOS-compat, record-only). |
| **15 BOD** | Demos/acceptance run on the full-demo scenario; new scenarios ONLY via dated amendments here (owner rule 2026-07-04: no undocumented future-phase dependency). |
| **Deployment 19–21** | Seeders excluded from every production path (runbook states it); the reproducible dataset REDUCES dev-DB preciousness but does NOT replace the Phase-0 snapshot decision `[DATA-D9]` — the organic dev DB remains grandfathered evidence. |

## 10. Versioning + change control `[DATA-D6 ratified]`

Spec semver — this document = **v1.0.0 / `frozen-v1`** (frozen at DSA-C 2026-07-17).
Scenario additions/changes = dated amendments in §12. Regression expected values =
owner-approval-only (§7). Performance volume targets = owner-deferred; their arrival = a
dated amendment. DOC_STANDARDS §20 discipline applies.

## 11. Reserved-handle registry (census-derived seed list — the DATA-D4 registry v1)

**Identities (36):** the 33 `dev.*@test.local` cast (DSA-A census list is normative:
`dev.ow.a-d` · `dev.sw.a-b` · `dev.mgr` · `dev.manager` · `dev.piece` · `dev.monthly` ·
`dev.monthly2` · `dev.leaver` · `dev.helper` · `dev.hlp.nkb` · `dev.accountant` ·
`dev.listing` · `dev.acct.mgr` · `dev.aud.{chk,cm1,cm2,cm3,hlp,sw}` · `dev.cm.a-c` ·
`dev.{el,flat,sn,chk,iron,fin}.*` skill cast) + `umesh29mar@gmail.com` (owner) +
`utest@gmail.com` (cutting master) + `mgmt1@test` (Manager-B, MGT-G).
**Worlds:** `T-SHIRT-001` · `LOWER-001` · `LOWER-002` · `3-PATTI-016` (canonical settled
real-flow world, A1) · `3-PATTI-009` (ADST-0001 history) · `DEV-NICKAR-A1/001/002`.
**Products:** `T-SHIRT` · `LOWER` · `3-PATTI` · `DEV-NICKAR` · `NKB` · `NKS`.
**Rolls:** `CR-000001` · `GLDN-R1..R6`. **Machines:** `OL-001` · `FL-001` · `SN-001` ·
`EL-001`. **Money:** `ADST-0001` (₹1,500) · `ADST-0004` (**₹344.25**) · `ADST-0005`
(**₹801.00**) · `ADST-0006` (**₹633.00**) + the **₹225** S-series invariant.
**Patterns:** `MRK-000001..3`. **Stage library:** the 23 slug codes (`layering`,
`cutting`, `cutting_pattern`, …).
Registry law: Phase-12 scenarios may only mint NEW handles in the §4 schemes; collisions
with reserved handles = seed failure, never auto-suffix.

## 12. Amendments

- **A1 (2026-07-17, SEED-C C-SEED-1 disposition — owner option (b) verbatim: "Do NOT invent
  the ₹225 executable recipe… The historical ₹225 statement remains historical evidence. The
  executable regression set is derived only from recipes that are fully reconstructable from
  the repository and database."):** §7's regression row is amended: the **executable** golden
  set = **₹801.00 · ₹344.25 · ₹633.00** (recipes reconstructable from the certified primary
  DB + FOM receipts). **The ₹225 invariant is HISTORICAL EVIDENCE** (S-series receipts assert
  it; no executable recipe exists on disk — SEEDER_ENGINE_LOG §SEED-C.1) and **is no longer a
  standalone executable regression until an authoritative recipe exists** (its living guard =
  the settlement suite's on-disk goldens, battery-permanent). §11's money row and the
  registry's `regression-settlement-225` entry re-scope accordingly. No history rewritten;
  no certification record modified.

- **A2 (2026-07-18, Phase-15 BOD-F — the §15 BOD interface row exercised as written:
  "new scenarios ONLY via dated amendments here"; ratified owner Design Record BOD-D8):**
  §7's feature row gains **`feature-bod`** — the Business Operating Dashboard demo world:
  the deterministic settled money world (per-tag DEV-BOD clone; layers 2,3,4,6,7,8 —
  ledger credits light the Outstanding-Payments tile) plus ONE DEV-noted factory expense
  via the certified `expense_service.record_expense` writer (lights the This-Month's-
  Expenses/Categories tiles); the post step re-runs the board's OWNING services
  (`operations_digest` · `monthly_totals`) as the world's evidence — the BOD itself owns
  nothing, so the world is proven at the services. Standard feature-class assertions;
  idempotent (note-probed skip); no new architecture, no new layers, no golden values.

- **A3 (2026-07-18, Phase-16 MEE-E — the §15-class interface rule exercised again;
  chartered at PHASE_16 §6.5, owner-approved with the MEE-D1 charter):** §7's feature row
  gains **`feature-monthly-expense`** — the Monthly Expense Engine world: DEV-MEE rent +
  salary templates created through the census-ADDENDUM-1 writers
  (`create_expense_template`), the 2026-07 period generated via
  `generate_monthly_expenses` (the sole path: preview=confirm code), and ONE voided
  example via the existing `void_expense` lever. Layers (2,3) only; converging
  (sub-steps probe their own end-state); standard feature-class assertions; no new
  architecture, no golden values.

- **A4 (2026-07-18, Phase-17 RMX-F — chartered at PHASE_17 §6.5/RMX-D8, owner-approved
  with the RMX charter):** §7's feature row gains **`feature-rm-expense`** — the
  Phase-17 material-money proof world: a DEV-RME settled journey whose consumed roll
  stays UNPRICED (the honest-NULL banner world), a PRICED-but-unconsumed roll (the
  purchases fixture, priced via `update_roll_details`), a DAMAGED roll (purchases-only
  fixture, via `mark_roll_damaged`), and the journey's REAL 2.5kg leftover
  `consume_leftover`'d into a second adda (the one-rupee-once reuse chain) — every step
  a certified writer; converging. The straddle-month/exact-value reconciliation
  fixtures live in the battery suites (`test_rmx_read_paths` / `test_rmx_certification`)
  — the world provides the LIVE demo/verification substrate; no golden values.

## 13. Phase-12 implementation checklist — FINALIZED (DSA-C 2026-07-17)

1. Dev-only app (default `devseed`) registered ONLY in dev settings; import-linter layer.
2. Four-factor guard (§6) FIRST, negative-tested, before any seeding feature.
3. Command classes: `seed_demo` · `seed_factory` · `reset_demo` (exact-string confirm) ·
   `seed_feature <x>` (registry-driven).
4. Service-path orchestration per §3 writer map; purity test = zero direct guarded-table
   writes; TRUE cast actors on every service call.
5. Natural-key idempotent converge per §4; divergent world = REPORT, never auto-pave.
6. Scenario registry = §7 table + §11 handles, machine-readable.
7. Assertions module per §7 (single source, shared with Phase 13 per that contract's
   reconciliation note).
8. Golden regression scenarios reproduce ₹801.00/₹344.25/₹633.00/₹225 byte-for-byte.
9. Scratch-DB law: the primary dev DB is never a seeder target in Phase 12.
10. Battery + pins per PHASE_12's own contract; docs per U6.
