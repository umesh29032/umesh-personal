# PENDING BACKLOG — everything still to do, one place (2026-06-12)

> THE consolidated open-items list. Big-picture order lives in
> [ROADMAP_REVIEW_POST_C1_2026_06_11.md](ROADMAP_REVIEW_POST_C1_2026_06_11.md)
> (canonical roadmap); this file gathers EVERY pending item — large and small —
> with its source. Update this file when an item ships; never delete, strike.

## 0) Blocking NOW — deployment decisions (owner)
| Item | Detail | Source |
|---|---|---|
| VPS provider + size | ~2 vCPU/4GB start | deploy/README |
| Domain | Caddy/TLS + ALLOWED_HOSTS | deploy/README |
| Backup provider | Backblaze B2 vs Cloudflare R2 (restic) | deploy/README |
| **DB-init** | **FRESH production DB recommended** — migrating dev carries test Addas + demo ADST settlements into append-only financial history forever | ARCH_READINESS_REVIEW §expensive-after-data |

## 1) Deploy week (with/just after the deploy session)
- P4 runbook entries: worker password-reset procedure; phone session-lifetime
  setting; Hinglish one-page training cards per persona (worker card = 5
  lines). (owner workflow audit)
- Observability bundle live (error reporting — stack has the seams).
- Backup→restore FIRE DRILL on the real VPS (never rehearsed end-to-end).
- Frontend: verify the 6–8 DataTables lists once on real phone hardware.
- **FOUNDATION S4 Phase 4 (complete-time allocation bound) DONE 2026-06-14** ([S4_PHASE4_RECEIPT](S4_PHASE4_RECEIPT_2026_06_14.md)) — Strict bound at `complete_worker_task` (via `pool_service.check_allocation_bound`): **`Σ(good_quantity+alter_quantity+missing_quantity) per REPORTED (worker, stage, colour, size) ≤ Σ active (non-voided) allocated`**. **Per-dimension + independent** (owner: under-consuming an allocated dim passes; a reported-but-unallocated dim → allocated=0 → refused). **🔒 Production-CAPACITY only — reads good/alter/missing + allocated_quantity, NEVER verified/settlement/rate/earning/cost_method** (decoupling proof test: verified_quantity that would flip the result is ignored). **`worker_allocated` = Σ ALL active rows, never a single row** (multiple sum; partial void reduces; reallocation = current active). Gated by **`ENFORCE_ALLOCATION_BOUND` (default False = kill-switch + back-compat)**; pool-participant stages only (NONE never bounded). No schema (setting + logic). 11 tests (incl. both owner examples + decoupling). Golden ₹225 byte-identical; full suite green. **4 independent concerns preserved: allocation / cost_method / earning / settlement.** **STOP for review before Phase 5 (Era-A reopen guard + clear_stage_pool wiring).**
- **FOUNDATION S4 Phase 3 (WorkerStageAllocation + draw-down) DONE 2026-06-14** ([S4_PHASE3_RECEIPT](S4_PHASE3_RECEIPT_2026_06_14.md)) — **`WorkerStageAllocation`** (migration prod **0042**): a worker's allocated slice of a CONSUMING stage's upstream pool; **production-truth, NO money** (no rate/earning/ledger/settlement FK), append-only (`voided_at`, never delete); distinct from settlement `StageWorkAssignment`. Draw-down folded into **`pool_service`** (the piece-pool chokepoint — NOT a 2nd `allocation_service`, which is the legacy expense era-A path): `allocate` (refuse over-allocation — pool integrity, always-on, NOT gated by `ENFORCE_ALLOCATION_BOUND`), `void_allocation` (qty returns), `available` = `pool_good(source)↓grain + recovered − Σ non-voided WSA`; `_upstream_pool_source` (nearest non-NONE; skips pre-piece); grain coarsen-aggregation; `recovered_alter`/`found_missing` M-7 stubs→0. **D2 lock = advisory `(5375, objid(source_sr,color,size))`, two-int namespace disjoint from settlement bigint 5374; never AddaStageRecord.** **🔒 Decoupling verified+locked (owner): WSA ⊥ costing/earning/rate/settlement** (`allocation_dimensions`/`cost_method`/`credits_workers` independent; no-money + import-decoupling tests). New chokepoint doc `pool_service.md`. 9 tests; golden ₹225 held. **Current flow: pool source (cutting) but no consumer → `allocate` unreached live; ready for stitching.** **STOP for review before Phase 4 (complete-time bound enforcement, gated by `ENFORCE_ALLOCATION_BOUND=False`).**
- **FOUNDATION S4 Phase 2 (StagePoolSnapshot) DONE 2026-06-14** ([S4_DESIGN_CORRECTION_ADDENDUM §C1/D2/D3 LOCKED Option B](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md)) — **`StagePoolSnapshot`** model (migration prod **0041**): frozen per-(colour,size) `good` for DOWNSTREAM pool-producing stages; immutable write-once; reopen clears+refreezes. **Cutting gets NO SPS row — its pool good = `AddaProductSizeColorPieceBreakdown` (single source of truth, Option B; never duplicated).** Pool source **handler-dispatched** (`handler.pool_good`/`materialize_pool`; cutting overrides → APSCPB read + materialize no-op; base → SPS) — no stage-name conditionals. `pool_service` (`pool_good`/`materialize_stage_pool`/`clear_stage_pool`). **NEVER `cost_quantity_snapshot`.** Pool-only (orthogonal to settlement/costing). **D2 draw-down lock = advisory by (source_stage_record_id,color_id,size_id), distinct classid from settlement 5374 → domains disjoint** (the lock USE lands Phase 3 draw-down). **Current flow: pool source (cutting) exists but NO consumer → SPS materialises no rows today; foundation ahead of future piece-consuming stages (stitching).** 6 tests; golden ₹225 held. **STOP for review before Phase 3 (WorkerStageAllocation + draw-down).**
- **FOUNDATION S4 Phase 1 (D1) DONE 2026-06-14** (design: [S4_IMPLEMENTATION_RECEIPT](S4_IMPLEMENTATION_RECEIPT_2026_06_14.md); corrected model: [S4_DESIGN_CORRECTION_ADDENDUM §D1](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md)) — `WorkflowStage.allocation_dimensions` (migration prod **0040**), enum `AllocationDimensions` **{NONE, QUANTITY, COLOR_SIZE}**, default NONE. **Owner-locked business truth: the piece-pool starts at CUTTING** — layering/cutting_pattern/barcode = NONE (pre-piece, excluded from SPS + allocation bound), cutting = COLOR_SIZE (pool source). **POOL-ONLY: orthogonal to settlement (`credits_workers`) + costing (`cost_method`)** — a NONE stage still settles + pays per its cost_method. Seeded from each handler's `pool_grain` (data-driven). `flow_service.set_stage_grain` + `_validate_grain_monotonicity` (non-increasing among non-NONE participants only — so layering(NONE)→cutting(COLOR_SIZE) is NOT a violation; checked on set/add/reorder). 13 tests; golden ₹225 held; full suite green. **STOP for review before Phase 2 (StagePoolSnapshot).** S4 = service+tests only (no UI); `ENFORCE_ALLOCATION_BOUND=False` default.
- **FOUNDATION S3 DONE 2026-06-14** (good/alter/missing + RC-3; design: [S3_DESIGN_RECEIPT](S3_DESIGN_RECEIPT_2026_06_14.md)) — thin slice (columns + resolver; worker UI unchanged). `WorkerStageContribution.good_quantity` (NOT NULL, payable) + `alter_quantity`/`missing_quantity` (immutable observations, default 0). **Migration prod 0039** = one-file RC-3: add cols → batched backfill `good=reported` → good NOT NULL → drop `wsc_reported_quantity_positive` → add `wsc_gam_nonneg_sum_positive` (each≥0 ∧ sum>0; good=0 all-defect row now legal). **Dual-write** `reported_quantity=good_quantity` on every write (renamed-not-dropped @S6). Resolver pays `good`; expected_earning + rerate freeze on good; payroll pieces stat + worker display → good. Golden ₹225 byte-identical; NEW non-zero alter/missing golden (claim 120 / good 105 → pays 105, B-1 leak structurally closed) + RC-3 proof (good=0 row legal) + dual-write invariant. **NOT in S3:** allocation bound (S4), finalize BLOCK (S5), reported drop (S6). Owner: good NOT NULL + payroll stat→good confirmed. **Re-review M-1..4 before S4.**
- **FOUNDATION S1.1 DONE 2026-06-14** (hostile-review hardening; review: [S1_HOSTILE_REVIEW_2026_06_14](S1_HOSTILE_REVIEW_2026_06_14.md)) — **H1** M-6 settlement WARN scoped to `over_allocated` only (`SETTLEMENT_WARN_FLAGS`; was all HARD_FLAGS = noise) · **H2** `SettlementReconciliationEvidence` (expense 0010) — append-only persisted variance at finalize (`record_reconciliation_evidence`), soak B-1 metric survives corrections · **M3** dead `reconciliation_warnings` attr removed · **M4** creation-site wiring test (create_adda→snapshots) · **M5** global lock-order doc updated (production-truth domain task→AddaStageRoleRate→WSC, disjoint from settlement order) · **Re-rate override (owner Option 1, keeps M1 per-(stage,role) lock):** `stage_rate_service.rerate_stage_role` — super-admin corrects a stage rate UNTIL settlement (overrides the completion lock), auto-recalcs all completed-but-unsettled expected_rate/expected_earning, refuses once actively settled (reverse first), mandatory `reason`, append-only `RateCorrectionAudit` (production 0038) · thin super-admin UI (`production:stage-rates` + `stage-rate-correct`, mobile-first). Golden ₹225 byte-identical. **M1 ruling: rate immutability is per (stage_record, role), NOT per stage.**
- **FOUNDATION S1 DONE 2026-06-14** — settlement_quantity resolver (`STAGE_GOOD` default = verified??reported; 3 sites; golden ₹225 chain byte-identical) · `cost_service.resolved_payable_rate` (single source) · `AddaStageRoleRate` model+migration (production 0037) — frozen RESOLVED rate per (stage_record, role), snapshot at stage-start, **immutable after first completion** (contract 1, lock order task→rate), live-fallback+WARN only for pre-S2 (contract 2) · `WorkerStageContribution.role_snapshot` (rate reads frozen role, not live) · grouped-member→₹0 preserved · M-6 reconciliation WARN groundwork (`reconcile_stage_pay` surfaced at finalize-log + settlement detail + soak; **BLOCK deferred to S5**). 556/556 green. Governed by [PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md). **Re-review M-1..4 (grain/pool/lock/reopen) before S4.**
- **F-3 DONE 2026-06-14** — pending-reports drill-down (`production:pending-reports`, linked from the digest tile): actionable pending tasks (assigned/in-progress on open stages), oldest-waiting first, mobile-first cards (Adda/stage/worker/status/assigned/age). SINGLE source — `operations_digest.pending_report_tasks()` shared by tile + list (counts reconcile). Management/super_admin see all; **worker sees only their own queue** (existing isolation preserved; dashboard `my_active_stages` untouched). No allocation/settlement/costing/payroll/truth change. Tests: 4 (oldest-first, reconciliation, worker-own-queue, super_admin).
- **H-2B DONE 2026-06-14** — stalled-Adda drill-down (`production:stalled-addas`, linked from the digest tile): mobile-first severity cards (warning / critical=2×threshold), longest-stalled first, code/stage/status/days/stalled-since. SINGLE stalled path — `operations_digest.stalled_stage_records()` shared by the tile + the list (counts always reconcile). Worker isolation preserved. No foundation/settlement/costing touch. **H-2 now fully closed (H-2A tile + H-2B drill-down).** Tests: 5 (sort, severity, reconciliation, worker-isolation, super_admin).
- **G-AUTH-1 DONE 2026-06-14** — object-level isolation on history routes (AddaHistoryView + RollHistoryView): management sees all; a worker only Addas they hold a live WorkerStageTask on (rolls only if they touched such an Adda, via AddaHistory). Same principle as the dashboard. Read-only views only — NO service/model/financial path touched. Tests: 8 (assigned/unassigned/manager/super_admin × Adda + Roll).
- **P1-2 DONE 2026-06-14** — sidebar section reorder (C-2): Main → **Production → Raw Materials → Storefront** → Tracking → Payroll → Administration. Pure `SIDEBAR` tuple reorder — no URL/route/permission/visibility/label changes. Tests: accounts/test_sidebar_order (super_admin full order + manager + worker).
- **P1-1 DONE 2026-06-14** — role-based landing (HomeView: management → Operations dashboard `production:dashboard`, worker → My Dashboard) + management-only **Operations digest** (6 tiles: stalled / pending-reports / active / completed-today / pending-payable / advance-exposure; all foundation-independent) + sidebar dedupe (labels → "My Dashboard" + "Operations"). Stalled threshold = `STALLED_ADDA_DAYS` setting (default 3). Addresses C-1/C-3/H-2/H-4 + summary H-7.
- **P0-2 DONE 2026-06-14** — branded `handler403/404/500` registered + `templates/{403,404,500}.html` (self-contained; 500 needs no DB/context). **MT-3 prod-config verified end-to-end:** `config.settings.production` loads + `check --deploy` = 0 issues; `collectstatic` (CompressedManifestStaticFilesStorage) = 130 copied/386 post-processed OK. **Deploy MUST set env:** `SECRET_KEY`, `REDIS_URL`, `ALLOWED_HOSTS` (CSV), `CSRF_TRUSTED_ORIGINS` (all fail-fast, no defaults) — and **run `collectstatic`** before serving (manifest storage). Nice-to-have: a few duplicate static files shadow-collected (e.g. `accounts/images/kid1.jpeg`, `accounts/css/auth.css`) — dedupe later, non-blocking.

## 2) During soak (riding alongside)
- **G4 Adda-360 thin slice** — read-only page; THE soak instrument; first
  consumer of ADR-0009 read rules. (locked L6)
- **TM-1 Tracking Mode (Manual/None)** — week 1–2; D-T1 storage decision at
  build; H1/H2/H4 rules; **TM-1×P2 interaction: make
  `pending_report_workers` tracking-mode-aware** (readiness review §3).
- SOAK_TRACKER.md evidence log (feeds the two soak gates below).
- During-soak UI friction list (collect real, don't pre-polish): size-hint
  after product create · settlement-queue→workspace nav link · settlement
  detail snapshot table on phone (pre-existing side-scroll) · login-page
  first-render flash.

## 3) Soak-GATED (forbidden before soak passes)
- **ADR-0007 deletion PR**: remove `LEDGER_CREDIT_AT_ALLOCATION` lever +
  era-A allocation path + un-pin the 8 lever-regression test classes.
- MissingPiece settlement **pre-fill** (observe real variance patterns before
  automating their entry; the module itself isn't gated).

## 4) Feature phases (locked order — details per phase sheet in the roadmap)
1. **MissingPiece** (+case lifecycle principle locked; barcode-free §5A)
2. **Alter/Rework** — design OPENS with the rework-pay decision; work records
   case-scoped (ADR-0010 §4); WST uniqueness stays
3. **G1 material costing** — material read-model (derived) + **costing-era
   stamp** + leftover-reuse UI (mobile-first) + unpriced-roll worklist
4. **G3 variance valuation** (needs MissingPiece + G1)
5. **G6 product/SKU master** — BEFORE any G5/G2 (owner-locked); SKU entity
   decision is the keystone
6. **G5 finished-goods stock** — ledger-discipline from birth; packing stage
   (archetype F) decision
7. **G2 orders/revenue** — commerce side only; Order→Adda FK banned forever
8. **Reporting (full)** — after lifecycle modules; era labels mandatory
9. **G7 planning/MRP-lite** — last
- **TM-2 (Barcode/Both)** — ONLY via the dedicated Barcode/Traceability
  review: piece model born FROM (adda,seq) ranges (ADR-0010 §3), H3 hybrid
  reconciliation, H5 scan attribution.

## 5) Parked tech debt (touch-time / scheduled)
| Item | When | Source |
|---|---|---|
| F7 assignable pool (= Stage.access_by_skill ∪ management, active) | direction LOCKED; build when access work next opens | validation F7 |
| D-T5 workspace visibility (masters vs helpers see planned qty) | F7 family | TM requirement §9 |
| mypy ratchet drift (257 errs) | next services-touching PR | readiness review |
| Frontend B-scope: legacy-page CSS migration, button-NAME unification, DataTables→data-label conversions | post-soak / touch-time | consolidation review (archived) |
| Stage-panel partial splits + JS→static extraction | when next forced; pairs with WhiteNoise work | frontend audit Phase 9 |
| REMEDIATION_PLAN phases 4–13 (god-files, M4 cycle-break, logging) | parked; import-linter: restate WSC.settlement_line as NAMED exemption | REMEDIATION_PLAN |
| docs/PAGES skeletons | fill per-page as screens are touched (docs/FLOWS archived 2026-06-13 — flows live in LEARNING_2_0/DATA_FLOWS + REQUEST_JOURNEYS) | doc audit gap list |
| ARCH_READINESS_REVIEW → archive | after soak passes | doc audit |
| Per-worker cross-Adda verified-qty rollup screen | only if asked; data derivable | readiness §1 |
| Period-close concept · retention policy for append-only tables | named, far | foundation audit §C |

## 6) Standing rules that travel with ALL of the above
Mobile-first (rule 11, every UI review documents 360/768/1280) · honest-NULL ·
backfill known facts only · append-only corrections · single-writer gates must
stay green · every new phase opens by reading its locks (ADR 0008/0009/0010,
R1, TM requirement).
