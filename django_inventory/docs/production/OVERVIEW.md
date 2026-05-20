# Production Tracking — Overview

**Status:** All 10 phases shipped. 19/19 tests green. `manage.py check` clean.

End-to-end factory tracking subsystem for Kapil Enterprises: raw cloth intake → batch (Adda) production → cutting → barcode generation → future packing/dispatch. Replaces the gutted batch/cloth code in the old `inventory` app (which now only owns RBAC + dashboard).

## Three-app split

| App | Responsibility | Owns |
|---|---|---|
| `raw_materials` | Cloth inventory + master data | `ClothType`, `ClothColor`, `StorageLocation`, `ClothRoll` |
| `production` | Products, batches, workflows, stage records | `Product`, `WorkflowStage`, `Adda`, `AddaStageRecord`, `LayeringRecord`, `CuttingRecord` |
| `tracking` | Barcodes + per-domain audit history | `BatchBarcode`, `ClothRollHistory`, `AddaHistory`, `ProductHistory` |
| `expense` (future) | Worker payment ledger | placeholder only; `AddaStageRecord.workers` M2M migrates to `through='expense.StageWorkAssignment'` later |

**Boundary rule**: cross-app FKs point downstream only.
- `raw_materials.ClothRoll.adda → 'production.Adda'` (string FK, no import cycle)
- `tracking.*` references both upstream apps
- `raw_materials` imports nothing from `production` or `tracking`

## Hybrid workflow model

```
Product (BEDSHEET) ── has ──▶ WorkflowStage(order=1, stage_type=layering)
                       has ──▶ WorkflowStage(order=2, stage_type=cutting)

Adda(product=BEDSHEET, current_stage=WorkflowStage[order=1])
  └── AddaStageRecord(adda, workflow_stage, workers M2M, completed_at, completed_by)
        ├── LayeringRecord (OneToOne to stage_record)
        └── CuttingRecord  (OneToOne to stage_record)
```

`Adda.current_stage` advances **explicitly** via `AddaStageService.complete_current_stage(adda, user)` — never auto on stage record save.

## Identifier formats

| Entity | Format | Example |
|---|---|---|
| Roll ID | `CR-NNNNNN` (global Postgres sequence) | `CR-000142` |
| Adda code | `{PRODUCT_CODE}-NNN` (per-product counter, race-safe) | `T-SHIRT-001` |
| Piece barcode | `{ADDA_CODE}-{PIECE_SEQ:04d}` | `T-SHIRT-001-0042` |

## RBAC roles

| Role | Source | Scope |
|---|---|---|
| `super_admin` | existing | universal access |
| `manager` | existing | production CRUD |
| `karigar` | existing | floor worker, scoped views |
| `accountant` | seeded by `inventory/0013` | view + edit Supplier + Cost Per KG |
| `listing_team` | existing | storefront CRUD |

`PRODUCTION_ROLES = {super_admin, manager, karigar}`
`FINANCIAL_ROLES = {super_admin, accountant}`

## Seeded master data (migrations)

- 5 Products: `3-PATTI`, `T-SHIRT`, `NIKKAR`, `PAJAMA`, `1-6` — each gets `[layering, cutting]` workflow
- 4 ClothTypes: Cotton, Polyester, Silk, Linen
- 6 ClothColors: Red, Blue, Green, White, Black, Yellow
- 2 StorageLocations: PACKING, ROHINI

## URL surface

```
/raw-materials/                              Overall raw-material index (Cloth live + future tiles)
/raw-materials/cloth/                        Cloth dashboard: Type × Color, by-location, filters
/raw-materials/rolls/                        Roll list (filter chips + time log accordion)
/raw-materials/rolls/bulk-add/               Super Admin only — bulk intake form
/raw-materials/rolls/<int:pk>/               Roll detail
/raw-materials/rolls/<int:pk>/assign/        Assign roll to Adda
/raw-materials/cloth-types/ (+CRUD URLs)     Master CRUD
/raw-materials/cloth-colors/ (+CRUD URLs)
/raw-materials/storage-locations/ (+CRUD URLs)

/production/                                 Adda dashboard
/production/products/ (+CRUD URLs)           Super Admin only
/production/addas/                           Adda list
/production/addas/start/                     Start new Adda
/production/addas/<code>/                    Adda detail (workflow pipeline + stage records)
/production/addas/<code>/layering/           Complete Layering stage
/production/addas/<code>/cutting/            Complete Cutting stage → barcodes generated

/tracking/                                   Barcode dashboard
/tracking/barcodes/<adda_code>/              Barcode list per Adda
/tracking/barcodes/<adda_code>/print/        A4 QR print sheet (3 density modes)
/tracking/barcodes/<adda_code>/export/       CSV export
/tracking/scan/<value>/                      QR scan landing (login required)
/tracking/history/roll/<int:roll_pk>/        Roll history timeline
/tracking/history/adda/<str:adda_code>/      Adda history timeline
```

## Non-functional baseline (locked in design)

- Scale: ~5k rolls/year, ~50 Addas/month, ~10 concurrent users
- Bulk roll create: up to 200 rolls per submit, completes in <5s
- Daily `pg_dump` backups, single-owner, no SLA
- Postgres-only (Roll ID sequence uses `CREATE SEQUENCE`)
- All multi-row writes via service layer (CLAUDE.md rule #4); no signals
- History tables written exclusively via `tracking.services.history_service.log_*`

## Lazy-load docs

- [RAW_MATERIALS.md](RAW_MATERIALS.md) — cloth inventory app deep dive
- [PRODUCTION_APP.md](PRODUCTION_APP.md) — products, Adda, stages
- [TRACKING.md](TRACKING.md) — barcodes + history
- [RBAC.md](RBAC.md) — `ROLE_ACCOUNTANT` + financial gating
- [MIGRATIONS.md](MIGRATIONS.md) — migration order + seed data
- [TESTS_AND_RISKS.md](TESTS_AND_RISKS.md) — coverage + edge cases + risks
- [DECISION_LOG.md](DECISION_LOG.md) — chronological brainstorm decisions
- [LAYERING_STAGE.md](LAYERING_STAGE.md) — Stage 1 deep dive (data model, complete handler, permission matrix)
- [UI_PATTERNS.md](UI_PATTERNS.md) — form shell, mobile rules, filter chips, accordions, QR print
- [CHAT_LOG.md](CHAT_LOG.md) — design evolution log (chronological, for new-chat context)

## How to load this in a fresh session

```
Load docs/production/OVERVIEW.md (this file).
For specific work, load only the relevant sub-doc:
  - models/services on cloth          → RAW_MATERIALS.md
  - Adda/Product/stage logic          → PRODUCTION_APP.md
  - barcodes / history / scan         → TRACKING.md
  - UI / templates / mobile / forms   → UI_PATTERNS.md
  - role gating / accountant rule     → RBAC.md
  - migrations / seed data            → MIGRATIONS.md
  - tests / risks / edge cases        → TESTS_AND_RISKS.md
  - chronological decisions           → DECISION_LOG.md, CHAT_LOG.md
```

## Verify

```bash
env/bin/python config/manage.py check                                      # clean
env/bin/python config/manage.py test raw_materials production tracking     # 19/19 OK
env/bin/python config/manage.py runserver
# Login as super_admin → walk /raw-materials/ → /production/ → /tracking/
```
