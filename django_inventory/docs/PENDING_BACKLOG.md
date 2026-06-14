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
