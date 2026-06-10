# Production Tracking — Overview

**Status:** 4 stages live (Layering · Cutting Pattern · Cutting · Barcode Generation [optional]) + **stage costing** + **worker payroll** (`expense` app). 292 tests green. `manage.py check` clean. Last touched 2026-06-02.

End-to-end factory tracking subsystem for Kapil Enterprises: raw cloth intake → batch (Adda) production → layering → cutting-pattern design → cutting → barcode generation → export to vendor. Each priced stage freezes a `processing_cost` on advance (`cost_service`); worker earnings flow to the `expense` app's ledger. Replaces the gutted batch/cloth code in the old `inventory` app (which now owns RBAC + dashboard + the Access Control hub).

## Three-app split

| App | Responsibility | Owns |
|---|---|---|
| `raw_materials` | Cloth inventory + master data | `ClothType`, `ClothColor`, `StorageLocation`, `ClothRoll` |
| `production` | Products, patterns, sizes, stages, workflows, stage records | `Product`, `ProductPattern`, `ProductPatternAssignment`, `ProductSize`, `Stage`, `WorkflowStage`, `Adda`, `AddaStageRecord`, `LayeringRecord`, `LayeringRollEntry`, `RemainingClothOfClothRoll`, `CuttingPatternRecord`, `CuttingPatternPhoto`, `CuttingPatternVerification`, `CuttingPatternSizeAllocation`, `CuttingRecord`, `CuttingPieceBreakup`, `CuttingBundle`, `CuttingBundleItem`, **`AddaProductSizeColorPieceBreakdown`**, **`BarcodeGenerationRecord`**, **`LabelPrintQueue`** (stub) |
| `tracking` | Barcodes + exports + per-domain audit history | `BarcodeBatch`, `BatchBarcode`, **`BarcodeExportBatch`**, `ClothRollHistory`, `AddaHistory`, `ProductHistory` |
| `expense` | Worker payroll: earnings ledger, advances, settlement | `StageWorkAssignment` (standalone FK allocation — NOT an M2M `through`), `WorkerLedgerEntry` (append-only), `WorkerAdvance`, `WorkerProfile`, `PayrollSettlement`, `PayrollSettlementItem`. `AddaStageRecord.workers` stays a bare M2M (roster); earnings tracked on `StageWorkAssignment`. |

**Boundary rule**: cross-app FKs point downstream only.
- `raw_materials.ClothRoll.adda → 'production.Adda'` (string FK, no import cycle)
- `tracking.*` references both upstream apps
- `raw_materials` imports nothing from `production` or `tracking`

## Stage library (DB-managed)

`production.Stage` rows are admin-managed at `/production/stages/`. Each row owns:
- `code` (slug, LOCKED on update — services hardcode these in `production/constants.py`)
- `name`, `description`, `is_active`
- `access_by_skill` M2M (Skill)
- `access_by_role` M2M (Role)

Four well-known codes:
- `STAGE_LAYERING = 'layering'`
- `STAGE_CUTTING_PATTERN = 'cutting_pattern'`
- `STAGE_CUTTING = 'cutting'`
- `STAGE_BARCODE_GENERATION = 'barcode_generation'`  ← NEW 2026-05-29 (optional per-product)

Super Admin + Manager bypass per-stage access via `MANAGEMENT_ROLES` in `production.services.access_service`.

Stage CRUD is perm-gated:
- `production.view_stage` to land on the page
- `production.add_stage / change_stage / delete_stage` for write actions
- ROLE_SUPER_ADMIN bypasses every perm via `permission_service.user_has_perm`

## Hybrid workflow model

```
Product (T-SHIRT) ── has ──▶ WorkflowStage(order=1, stage→Stage[layering])
                       has ──▶ WorkflowStage(order=2, stage→Stage[cutting_pattern])
                       has ──▶ WorkflowStage(order=3, stage→Stage[cutting])

Adda(product=T-SHIRT, current_stage=WorkflowStage[order=1])
  └── AddaStageRecord(adda, workflow_stage, workers M2M, completed_at, completed_by)
        ├── LayeringRecord (OneToOne) + LayeringRollEntry[]
        ├── CuttingPatternRecord (OneToOne) + CuttingPatternPhoto[]
        └── CuttingRecord (OneToOne)
```

`Adda.current_stage` advances **explicitly** via service call (`complete_layering`, `complete_pattern_stage`, `complete_cutting`) — never auto on save.

## Per-product flow editor

`/production/products/<pk>/flow/` lets admin add/reorder/remove stages in a product's workflow. Service: `production.services.flow_service`. Refuses removal if any Adda in-use; refuses last-stage removal; reorder uses parking-slot swap because `(product, order)` is unique_together.

## ProductPattern library (NEW 2026-05-28)

`ProductPattern` is a reusable design shape (e.g. Front Panel, Back Panel, Sleeve). `Product.patterns` M2M via `ProductPatternAssignment` through-model with `pieces_count` (e.g. T-Shirt = 1 Front + 1 Back + 2 Sleeve).

- Admin CRUD: `/production/patterns/`
- Per-product assignment editor: `/production/products/<pk>/patterns/`
- Sidebar: Production → Product Patterns (perm-gated `production.view_productpattern`)
- Cutting-pattern stage reads `Product.pattern_assignments` to render the checklist

## Identifier formats

| Entity | Format | Example |
|---|---|---|
| Roll ID | `CR-NNNNNN` (global Postgres sequence) | `CR-000142` |
| Adda code | `{PRODUCT_CODE}-NNN` (per-product counter, race-safe) | `T-SHIRT-001` |
| Piece barcode | `{ADDA_CODE}-{PIECE_SEQ:04d}` | `T-SHIRT-001-0042` |

## RBAC roles

| Role | Source | Scope |
|---|---|---|
| `super_admin` | existing | universal access (implicit bypass everywhere) |
| `manager` | existing | production CRUD |
| `worker` | existing (was `karigar`) | floor worker, scoped views |
| `accountant` | seeded by `inventory/0013` | view + edit Supplier + Cost Per KG |
| `listing_team` | existing | storefront CRUD |

`PRODUCTION_ROLES = {super_admin, manager, worker}`
`MANAGEMENT_ROLES = {super_admin, manager}`
`FINANCIAL_ROLES = {super_admin, accountant}`

Role editor at `/inventory/roles/<pk>/edit/` is curated section-by-section (Production Flow · Raw Materials · Tracking · Storefront · Administration). Internal join tables hidden. See [project_rbac_state](https://example.com) memory and `permission_service.ROLE_EDITOR_SECTIONS`.

## Seeded master data (migrations)

- 5 Products: `3-PATTI`, `T-SHIRT`, `NIKKAR`, `PAJAMA`, `1-6` — each gets `[layering, cutting]` workflow by default. Admin can insert `cutting_pattern` via the flow editor.
- 4 ClothTypes: Cotton, Polyester, Silk, Linen
- 6 ClothColors: Red, Blue, Green, White, Black, Yellow
- 2 StorageLocations: PACKING, ROHINI
- 3 Stage rows: layering, cutting, **cutting_pattern** (seeded in `production/0013_seed_cutting_pattern_stage.py`, attaches `cutting_master` + `cutting_master_helper` skills)

## URL surface

```
/raw-materials/                              Overall raw-material index
/raw-materials/cloth/                        Cloth dashboard
/raw-materials/rolls/                        Roll list (filter chips + time-log accordion)
/raw-materials/rolls/bulk-add/               Super Admin only — bulk intake form
/raw-materials/rolls/<int:pk>/               Roll detail
/raw-materials/rolls/<int:pk>/assign/        Assign roll to Adda
/raw-materials/{cloth-types,cloth-colors,storage-locations}/ (+CRUD URLs)

/production/                                 Adda dashboard
/production/products/ (+CRUD URLs)           Super Admin only
/production/products/<pk>/flow/              Per-product Stage workflow editor
/production/products/<pk>/patterns/          Per-product ProductPattern assignments
/production/patterns/ (+CRUD URLs)           ProductPattern library
/production/stages/ (+CRUD URLs)             Stage library (perm-gated)
/production/addas/                           Adda list
/production/addas/start/                     Start new Adda
/production/addas/<code>/                    Adda detail (workflow pipeline + iframe panels)
/production/addas/<code>/stage/<type>/       Per-stage embedded panel (iframe-safe)

/production/addas/<code>/layering/                  Layering workspace
/production/addas/<code>/layering/{start,attach-roll,quick-create-roll,full-create-roll,complete}/
/production/addas/<code>/layering/entries/<pk>/{,remove}/
/production/addas/<code>/layering/remaining/<pk>/remove/
/production/addas/<code>/layering/reopen/           Admin reopen (NEW 2026-05-28)

/production/addas/<code>/pattern/                   Cutting-pattern workspace (NEW)
/production/addas/<code>/pattern/{start,save,complete}/
/production/addas/<code>/pattern/photos/{add,<pk>/remove}/

/production/addas/<code>/cutting/                   Cutting complete → barcodes

/tracking/                                   Barcode dashboard
/tracking/barcodes/<adda_code>/{print,export}/
/tracking/scan/<value>/                      QR scan landing
/tracking/history/{roll,adda}/<id>/          Timelines
```

## Iframe + postMessage flow

- Stage panels live at `/production/addas/<code>/stage/<stage_type>/?embedded=1`
- StagePanelView + AddaDetailView both decorated with `@xframe_options_sameorigin`
- On Complete from iframe, view redirects to NEW current stage's embedded URL with `?advanced=1`
- Embedded JS detects `?advanced=1` → postMessages `{type:'stage-advanced'}` to parent
- Parent (`adda_detail.html` + `user_dashboard.html`) listens → `window.location.reload()`
- Iframe auto-resize via `stage-panel-resize` postMessage

## Layering Reopen (NEW 2026-05-28)

Admin-only rollback of completed Layering for corrections. `POST /production/addas/<code>/layering/reopen/`. Service `reopen_layering`:
- Copies `LayeringRecord` header values into `sr.draft_*` BEFORE delete (so form re-renders with prior values pre-filled)
- Deletes LayeringRecord
- Resets `sr.completed_at`, `adda.current_stage` → layering wf, `adda.status` → IN_PROGRESS
- Refuses if any downstream stage has `started_at` set
- Audit via `AddaHistory.ChangeType.STAGE_REOPENED`

Button rendered on completed layering panel for management users. Per-entry `layers_on_roll` + `remaining_pieces` preserved across reopen.

## Cutting-pattern stage (NEW 2026-05-28)

See [CUTTING_PATTERN.md](CUTTING_PATTERN.md) for full details. TL;DR:
- Cutting master draws pattern on layered cloth; uploads **video AND/OR photos** (either suffices at complete-time)
- Photos auto-compressed via Pillow (JPEG q=80, ≤2400px, EXIF-honored)
- Video stored as-is (ffmpeg recompress deferred)
- Storage abstraction = Django `STORAGES['default']`. S3/MinIO swap = settings change only
- Auto-submit on file pick (users were missing the submit-button click step)
- Complete requires helper skill (or super_admin); advances to next stage

## Non-functional baseline

- Scale: ~5k rolls/year, ~50 Addas/month, ~10 concurrent users
- Bulk roll create: up to 200 rolls per submit, <5s
- Daily `pg_dump` backups, single-owner, no SLA
- Postgres-only (Roll ID sequence uses `CREATE SEQUENCE`)
- All multi-row writes via service layer (CLAUDE.md rule #4); no signals
- History tables written exclusively via `tracking.services.history_service.log_*`

## Lazy-load docs

- [RAW_MATERIALS.md](RAW_MATERIALS.md) — cloth inventory app deep dive
- [PRODUCTION_APP.md](PRODUCTION_APP.md) — products, Adda, stages (NOTE: predates Stage model + cutting_pattern; treat structural parts as outdated, code is canonical)
- [TRACKING.md](TRACKING.md) — barcodes + history
- [CUTTING_PATTERN.md](CUTTING_PATTERN.md) — Stage 2 deep dive (NEW 2026-05-28)
- [LAYERING_STAGE.md](LAYERING_STAGE.md) — Stage 1 deep dive
- [RBAC.md](RBAC.md) — `ROLE_ACCOUNTANT` + financial gating
- [MIGRATIONS.md](MIGRATIONS.md) — migration order + seed data
- [TESTS_AND_RISKS.md](TESTS_AND_RISKS.md) — coverage + edge cases
- [DECISION_LOG.md](DECISION_LOG.md) — chronological brainstorm decisions
- [UI_PATTERNS.md](UI_PATTERNS.md) — form shell, mobile rules, filter chips, accordions, QR print
- [CHAT_LOG.md](../archive/production/CHAT_LOG.md) — design evolution log *(archived)*

## How to load this in a fresh session

```
Load docs/production/OVERVIEW.md (this file).
For specific work, load only the relevant sub-doc:
  - models/services on cloth          → RAW_MATERIALS.md
  - Adda/Product/stage logic          → PRODUCTION_APP.md (caveat above)
  - cutting_pattern stage             → CUTTING_PATTERN.md
  - barcodes / history / scan         → TRACKING.md
  - UI / templates / mobile / forms   → UI_PATTERNS.md
  - role gating / accountant rule     → RBAC.md
  - migrations / seed data            → MIGRATIONS.md
  - tests / risks / edge cases        → TESTS_AND_RISKS.md
  - chronological decisions           → DECISION_LOG.md (CHAT_LOG.md archived)
```

## Verify

```bash
cd /home/tech/umesh-personal/django_inventory
env/bin/python config/manage.py check                                                       # clean
env/bin/python config/manage.py test raw_materials production tracking inventory accounts   # 74/74 OK
env/bin/python config/manage.py runserver
```
