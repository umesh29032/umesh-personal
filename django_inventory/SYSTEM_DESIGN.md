# Kapil Enterprises Inventory — System Design & Architecture

> **Single source of truth for the CURRENTLY-BUILT system.** Generated 2026-06-01 by deep code dig.
> Stack: **Django 5.0.1 + PostgreSQL** (use `CheckConstraint(check=...)`). Branch `new_flask_app`.
>
> ⚠️ **LOCKED REDESIGN IN PROGRESS — read [docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) (§11 🔒LOCKED)
> + [docs/V2_1_REVIEW.md](docs/V2_1_REVIEW.md).** The worker-tracking + settlement layer is being
> rebuilt: per-worker `WorkerStageTask`/`WorkerStageContribution` (replacing the bare
> `AddaStageRecord.workers` M2M), **Option B** (no ledger entry until settlement; `expected_*` frozen at
> complete = visibility only), and an **Adda-centric `AddaSettlement`** that books earnings + advance
> recovery (settlement ≠ payment). What this doc describes below = the *pre-V2 built state*; where it
> conflicts with ARCHITECTURE_V2, V2 wins for the redesigned area.

This document is the exhaustive reference for the whole project: every app, every model
(with all fields, `on_delete` rules, indexes, and the *why*), every service-layer function,
the full URL/view surface, the production stage pattern, RBAC, reopen semantics, denormalised
counters, and the diagrams that connect them. Built as the **pre-change baseline** before the
upcoming stage-system redesign.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Seven-App Architecture & Boundary Rules](#2-seven-app-architecture--boundary-rules)
3. [Entity-Relationship Map](#3-entity-relationship-map)
4. [Production Flow (End-to-End)](#4-production-flow-end-to-end)
5. [The Repeating Stage Pattern](#5-the-repeating-stage-pattern)
6. [Model Reference (every model, every field)](#6-model-reference)
   - 6.1 accounts · 6.2 inventory · 6.3 raw_materials · 6.4 production · 6.5 tracking · 6.6 storefront · 6.7 expense
7. [Service Layer Reference](#7-service-layer-reference)
8. [Single-Writer Discipline](#8-single-writer-discipline)
9. [URL & View Surface](#9-url--view-surface)
10. [RBAC & Permissions](#10-rbac--permissions)
11. [Reopen Semantics Matrix](#11-reopen-semantics-matrix)
12. [Denormalised Counters & Invariants](#12-denormalised-counters--invariants)
13. [Identifier Formats](#13-identifier-formats)
14. [Iframe + postMessage Stage Embedding](#14-iframe--postmessage-stage-embedding)
15. [Settings, Dependencies, Seed Data](#15-settings-dependencies-seed-data)
16. [Known Gaps & Where to Extend Stages](#16-known-gaps--where-to-extend-stages)

---

## 1. System Overview

End-to-end factory tracking for a kids-garment manufacturer (Kapil Enterprises). The system
follows cloth from **raw intake → batch (Adda) production → layering → cutting-pattern design →
cutting → barcode generation → export to vendor**, with per-piece QR barcodes and full audit history.

| Property | Value |
|---|---|
| Framework | Django 5.2 |
| Database | PostgreSQL (hard requirement — uses `CREATE SEQUENCE` + `SELECT FOR UPDATE`) |
| Auth | Custom `accounts.User` (email login), django-allauth, OTP + password fallback |
| Apps | 6 (`accounts`, `inventory`, `raw_materials`, `production`, `tracking`, `storefront`) |
| Concrete domain models | ~43 (49 incl. abstract bases + managers + Django auth) |
| Service modules | 18 |
| Live stages | 4 (Layering · Cutting Pattern · Cutting · Barcode Generation) |
| Tests | 196 green |
| Settings | split: `config/settings/{base,local,production}.py` |
| Scale target | ~5k rolls/yr, ~50 Addas/mo, ~10 concurrent users |

### Core architectural laws (from CLAUDE.md, verified enforced)

1. **Service layer owns ALL multi-row writes.** Views are thin POST parsers. Zero ORM writes in views.
2. **No Django signals.** No `save()` overrides for business logic. State changes are explicit service calls.
3. **`permission_service` is the only RBAC gate.** No raw `is_superuser` checks in views.
4. **History tables written only via `history_service.log_*`.**
5. **Cross-app FKs point downstream only** (string FKs avoid import cycles).
6. **PROTECT on master FKs; soft-archive via `is_active` + `.active` manager** — real DELETE is rare.
7. **IDs are service-generated** (`editable=False`): roll IDs from a PG sequence, Adda codes from a per-product counter under row lock.

> ⚠️ **Doc drift to fix:** CLAUDE.md rule #5 names `StockService.log → StockLedger` as the single ledger writer. That model/service is **dead** (exists only in old migrations `inventory/0002`, `0012`). The live single-writer for audit is `tracking.services.history_service`.

---

## 2. Seven-App Architecture & Boundary Rules

```
┌─────────────┐     ┌─────────────┐
│  accounts   │     │  inventory  │      BASE LAYER (no upstream deps)
│ User, Skill │     │ Role,       │
│             │     │ SidebarRule,│
│             │     │ permission_ │
│             │     │ service     │
└──────┬──────┘     └──────┬──────┘
       │ AUTH_USER_MODEL   │ Role / Skill FKs
       ▼                   ▼
┌──────────────────────────────────────────────┐
│ raw_materials   ──string FK──▶  production     │
│ ClothType,ClothColor,           Product,Stage, │
│ StorageLocation,ClothRoll       Adda, 20 more  │
│      ▲                              │          │
│      └────────── string FK ─────────┘          │
└──────────────────────┬─────────────────────────┘
                       ▼
              ┌─────────────────┐
              │    tracking     │   references BOTH upstream apps
              │ BarcodeBatch,   │
              │ BatchBarcode,   │
              │ *History,       │
              │ ExportBatch     │
              └─────────────────┘
                       │ string FK (AddaStageRecord, bundles) + worker User
                       ▼
              ┌─────────────────┐
              │    expense      │   DOWNSTREAM — worker payroll. Reads
              │ StageWork-      │   production + accounts; NEVER writes them.
              │ Assignment,     │   Allocation-driven immutable earnings
              │ WorkerLedger-   │   ledger (balance always derived, never
              │ Entry, Advance, │   stored).
              │ Settlement      │
              └─────────────────┘

┌─────────────┐
│ storefront  │   INDEPENDENT — public marketing CMS, no production FKs
└─────────────┘
```

**Boundary rule (strict):** `raw_materials` imports nothing from `production`/`tracking`.
`production` references `raw_materials` via string FK (`'raw_materials.ClothColor'`).
`tracking` references both upstream apps via string FK; `expense` is downstream of both
`production` and `accounts` and writes neither. This keeps the dependency graph acyclic
so migrations and app loading never deadlock.

**`core` (infra app, not shown above):** holds shared **abstract** base models —
`TimeStampedModel` (created_at/updated_at) and `ActiveManager` (the `.active` soft-archive
manager). Abstract = no tables, no migrations. Every domain app imports from `core` instead
of redefining these (they used to be copy-pasted in 4 apps).

| App | Responsibility | Owns |
|---|---|---|
| `accounts` | Identity + skills | `User` (custom, email login), `Skill` |
| `inventory` | RBAC core + dashboards | `Role`, `SidebarItemRule`, `permission_service` |
| `raw_materials` | Cloth inventory + master data | `ClothType`, `ClothColor`, `StorageLocation`, `ClothRoll` |
| `production` | Products, patterns, sizes, stages, workflows, **all stage records** | `Product`, `ProductPattern`, `ProductPatternAssignment`, `ProductSize`, `Stage`, `WorkflowStage`, `Adda`, `AddaStageRecord`, + 4 typed stage records + cutting breakup/bundle/breakdown + `LabelPrintQueue` (stub) |
| `tracking` | Barcodes + exports + audit history | `BarcodeBatch`, `BatchBarcode`, `BarcodeExportBatch`, `ClothRollHistory`, `AddaHistory`, `ProductHistory` |
| `storefront` | Public marketing site CMS | `HomePageConfig`, `Category`, `FeaturedProduct`, `HeroShowcaseCard`, `WhyUsCard`, `FooterLink`, `NavLink` |
| `expense` | Worker payroll: earnings ledger, advances, settlements | `StageWorkAssignment` (standalone FK allocation — NOT an M2M `through`), `WorkerLedgerEntry`, `WorkerAdvance`, `WorkerProfile`, `PayrollSettlement`, `PayrollSettlementItem`. `AddaStageRecord.workers` stays a bare M2M (roster only); earnings are tracked separately on `StageWorkAssignment`. |

---

## 3. Entity-Relationship Map

```
                          accounts.User ◀── role (FK SET_NULL) ── inventory.Role ──M2M── auth.Permission
                             │  │                                       ▲
                  skills M2M │  │ extra_roles M2M ──────────────────────┘
                             ▼
                       accounts.Skill ──M2M── production.Stage.access_by_skill
                                       └─M2M── inventory.SidebarItemRule.allowed_skills

 raw_materials                                production
 ─────────────                                ──────────
 ClothType ◀─PROTECT─┐                         Product ◀──── adda_counter (race-safe)
 ClothColor ◀PROTECT─┤                           │  ▲
 StorageLocation ◀───┤                           │  │ M2M (through ProductPatternAssignment, pieces_count)
                     │                           │  └────────────── ProductPattern
              ClothRoll ──adda FK (PROTECT)──▶  Adda ◀────────────── ProductSize (per product)
                 ▲   ▲                            │
                 │   │                            │ current_stage FK ─▶ WorkflowStage ──stage FK─▶ Stage
        rolls_used│   │layering_entries           │                      (order, product unique)
                 │   │                            │
   LayeringRecord│   │LayeringRollEntry           ▼
        (1:1)    │   │   (FK)              AddaStageRecord  (adda × workflow_stage unique)
                 │   │   │                  │  workers M2M ─▶ User
                 │   │   │                  │
                 │   │   │  ┌───────────────┼────────────────┬──────────────────┐
                 │   │   │  ▼ (OneToOne)     ▼ (OneToOne)      ▼ (OneToOne)        ▼ (OneToOne)
                 │   │   │ LayeringRecord  CuttingPattern   CuttingRecord     BarcodeGeneration
                 │   │   │                  Record            │                 Record
                 │   │   │                   │                │                  │
                 │   │   │              ┌────┴─────┐    ┌──────┴────────┐         │
                 │   │   │           Photo×N   Verification CuttingPieceBreakup   │
                 │   │   │                     SizeAllocation   │ consumed_count   │
                 │   │   │                                CuttingBundle           │
                 │   │   │                                  └ CuttingBundleItem    │
                 │   │   │                                      │ source_breakup FK │
                 │   │   │                                      ▼                   │
                 │   │   │            AddaProductSizeColorPieceBreakdown ◀──────────┘
                 │   │   │              (FROZEN manufacturing truth)        feeds
                 │   │   └─ RemainingClothOfClothRoll (leftover tracker)      │
                 │   │                                                        ▼
 tracking                                                          BarcodeBatch (range header)
 ────────                                                            │  per (adda, size, color)
 BarcodeBatch ──adda/product/bundle/size/color FK──────────────────  │
   └─ BatchBarcode (lazy per-piece scan state; value "{ADDA}-{SEQ:04d}")
 BarcodeExportBatch ──barcode_gen_record FK──▶ BarcodeGenerationRecord
   └─ LabelPrintQueue (stub) ──export_batch FK──┘
 ClothRollHistory / AddaHistory / ProductHistory  (append-only; history_service only)
```

---

## 4. Production Flow (End-to-End)

```
ClothRoll(s)  [raw_materials]  status: not_used
   │
   │  AddaService.create_adda(product)  ── SELECT FOR UPDATE on Product row ──▶ code "{PRODUCT}-NNN"
   ▼
Adda(product, current_stage=WorkflowStage[order=1], status=IN_PROGRESS)
   │   flow = ordered WorkflowStage rows (per-product, from Stage library)
   │
   ├─ STAGE 1: LAYERING ───────────────────────────────────────────────
   │    start_layering → workers assigned
   │    attach_roll_to_layering → roll flips to USED, LayeringRollEntry created
   │    save_layering_breakup → per-roll layers + leftover
   │    complete_layering → LayeringRecord (1:1) + rolls_used M2M snapshot
   │                        validates: ≥1 entry, per-entry layers, leftover per roll
   │                        ── advance_to_next_stage ──▶
   │
   ├─ STAGE 2: CUTTING_PATTERN ────────────────────────────────────────
   │    start_pattern_stage → workers
   │    save_pattern_record (video) / attach_photo (Pillow-compressed)
   │    verify_pattern (per ProductPatternAssignment)
   │    set_size_allocation (proportion_pct per size, Σ=100 at complete)
   │    complete_pattern_stage → validates video|photo + all assignments verified
   │                            + Σ allocation == 100 ── advance ──▶
   │
   ├─ STAGE 3: CUTTING ────────────────────────────────────────────────
   │    start_cutting → workers
   │    upsert_breakup_row → CuttingPieceBreakup per (size,color,pattern)
   │    create_bundle / add_pieces_to_bundle → CuttingBundle + CuttingBundleItem
   │                         (consumes breakup.available_count, SELECT FOR UPDATE)
   │    complete_cutting → CuttingRecord.pieces_cut = Σ items
   │                     → _materialize_breakdown ── FREEZES ──▶
   │                       AddaProductSizeColorPieceBreakdown × (size,color)
   │                       ◀═══ MANUFACTURING TRUTH (downstream consumes this) ═══
   │                     → if product has NO barcode_gen stage: inline generate_for_cutting
   │                     → advance ──▶
   │
   └─ STAGE 4: BARCODE_GENERATION  [OPTIONAL per-product] ──────────────
        start_barcode_generation → workers
        generate_barcodes → tracking.generate_from_breakdown(record)
                          → BarcodeBatch range rows per (size,color), one-shot
                          → BarcodeGenerationRecord.total_barcodes + generated_at
        complete_barcode_generation → validates Σbatch == Σbreakdown == total
                                    → advance (last stage → Adda COMPLETED) ──▶
   ▼
EXPORT (post barcode-gen complete)
   generate_csv / generate_xlsx / generate_pdf_summary → BarcodeExportBatch (EXP-YYYY-NNN)
   re-download by export_code (regenerated from live data)
   ▼
(future) vendor labels printed / factory printer → LabelPrintQueue
   ▼
SCAN (lazy)
   /tracking/scan/{value}/ → resolve_value → get_or_create_piece (BatchBarcode row born here)
                           → mark_status (pending/packed/dispatched/missing)
```

**The golden rule:** `Adda.current_stage` only ever moves inside `adda_service.advance_to_next_stage`,
which every `complete_*` calls. Nothing else mutates it. When `advance` finds no next stage,
it sets `status=COMPLETED`, `completed_at=now`, `current_stage=None`.

---

## 5. The Repeating Stage Pattern

**This is the most important section for the upcoming redesign.** Every stage in the flow is
built from the same 7 layers. Adding a new stage means copying this pattern — **no core changes**.

```
1. Stage (DB row)            production.Stage — admin CRUD at /production/stages/
   ├ code (slug, LOCKED on edit — services hardcode it in production/constants.py)
   ├ name, description, is_active
   ├ access_by_skill  M2M(Skill)   ─┐  OR-semantics access gate
   └ access_by_role   M2M(Role)    ─┘

2. WorkflowStage (join)      per-product, order-indexed
   unique_together (product, order) AND (product, stage)

3. AddaStageRecord (parent)  polymorphic; one row per (adda, workflow_stage)
   ├ workers M2M(User)
   ├ started_at / completed_at / completed_by
   └ draft_* fields (generic across all stages — leave/return support)

4. Typed child (OneToOne → AddaStageRecord)   stage-specific data:
   ├ LayeringRecord          (layer_length_meters, lay_count, duration, rolls_used M2M)
   ├ CuttingPatternRecord    (video, notes)
   ├ CuttingRecord           (pieces_cut)
   └ BarcodeGenerationRecord (total_barcodes, generated_at)

5. Service  production/services/<stage>_service.py
   ├ _ensure_<stage>_skill(user)          skill gate
   ├ _ensure_can_complete_<stage>(user)   stricter gate to advance
   ├ get_or_create_<stage>_stage_record(adda, user)
   ├ start_<stage>(adda, worker_ids, user)
   ├ <stage-specific mutations>
   ├ complete_<stage>(adda, user)         validate + advance_to_next_stage
   └ reopen_<stage>(adda, user)           mgmt-only, refused if downstream started

6. Views  production/views/<stage>_views.py (or stage_views.py)
   ├ <Stage>WorkspaceView (TemplateView, full page)
   ├ <Stage>StartView / <action>View / CompleteView / ReopenView (POST)
   └ iframe-safe redirect via ?embedded=1 + ?advanced=1 postMessage

7. Templates
   ├ <stage>_workspace.html        standalone, extends base
   └ _stage_panel_<stage>.html     shared partial (workspace + embedded iframe)
       routed by StagePanelView on the <stage_type> URL kwarg
```

Four well-known stage codes (in `production/constants.py`):
`STAGE_LAYERING='layering'`, `STAGE_CUTTING_PATTERN='cutting_pattern'`,
`STAGE_CUTTING='cutting'`, `STAGE_BARCODE_GENERATION='barcode_generation'`.

---

## 6. Model Reference

Legend: **PK** primary key · **FK** foreign key · **O2O** OneToOne · **M2M** ManyToMany ·
`PROTECT`/`CASCADE`/`SET_NULL` = `on_delete` · *abstract* `TimeStampedModel` adds
`created_at` (auto_now_add) + `updated_at` (auto_now) to most models.

### 6.1 `accounts`

#### `User` (extends `AbstractUser`, `AUTH_USER_MODEL`)
Custom user; **email is the login field** (`username` dropped). Two identity concepts:
`user_type` is a display label; `role` is the RBAC source of truth — **never gate on `user_type`**.

| Field | Type | Notes |
|---|---|---|
| email | EmailField unique | `USERNAME_FIELD` |
| user_type | Char choices | admin/manager/karigar/helper/normal — display only |
| first_name, last_name | Char(30) | |
| is_active, is_staff, is_superuser | Bool | |
| date_joined, created_at, updated_at | DateTime | |
| phone_number | Char(15), validated | regex `+?1?\d{9,15}` |
| birth_date, bio, profile_picture, salary | mixed | profile_picture→`profile_pics/`; salary Decimal(10,2) ≥0 |
| **skills** | M2M(Skill) | factory-floor capability gate |
| **role** | FK(inventory.Role) SET_NULL null | primary RBAC role |
| **extra_roles** | M2M(inventory.Role) | stacks additional access on top |

#### `Skill`
| Field | Type | Notes |
|---|---|---|
| name | Char choices unique | cutting_master, **cutting_master_helper**, dhage_katne_wala, embroidery, tailoring, other |

`cutting_master_helper` is special: only this skill (or super_admin) can **complete & advance** stages.

### 6.2 `inventory`

#### `Role`
| Field | Type | Notes |
|---|---|---|
| name | Char(64) unique | |
| code | Slug(32) unique | stable identifier used in `permission_service` constants |
| description | Text | |
| is_system | Bool | system roles (admin/manager/karigar) cannot be deleted |
| permissions | M2M(auth.Permission) | the actual grant set |

Seeded: Super Admin, Manager, Karigar (+ Accountant via `inventory/0013`, Listing Team).

#### `SidebarItemRule`
DB-driven per-menu-item visibility (admin-editable at `/inventory/sidebar-access/`).
| Field | Type | Notes |
|---|---|---|
| url_name | Char(128) unique | Django URL name, e.g. `raw_materials:roll-list` |
| section, label | Char(64) | denormalized for self-contained admin display |
| allowed_roles | M2M(Role) | |
| allowed_skills | M2M(accounts.Skill) | skill holders also see the item |

Super Admin is hardcoded-always-visible at the service layer (cannot lock self out).

### 6.3 `raw_materials`

All three master models carry `is_active` + dual managers: `objects` (all) and `active` (is_active=True).

#### `ClothType` / `ClothColor` / `StorageLocation`
| Model | Fields |
|---|---|
| ClothType | name (unique), is_active |
| ClothColor | name (unique), hex_code (blank), is_active |
| StorageLocation | name (unique), code (unique), is_active |

#### `ClothRoll` — one physical roll
Roll ID from Postgres `cloth_roll_seq` via `roll_service._next_roll_id()` only. Weight/width set at
**Adda assignment time**, not intake — hence nullable.

| Field | Type | Notes |
|---|---|---|
| roll_id | Char(20) unique, `editable=False` | `CR-000142` |
| purchased_date | Date | |
| cloth_type | FK(ClothType) PROTECT | |
| cloth_color | FK(ClothColor) PROTECT | |
| width_inch | Int choices 36–44, null | |
| weight_kg | Decimal(8,2) null | |
| supplier | Char, blank | **financial field** (role-gated in form) |
| cost_per_kg | Decimal(10,2) null | **financial field** |
| storage_location | FK(StorageLocation) PROTECT | |
| status | Char choices | not_used / used |
| adda | FK('production.Adda') PROTECT null | string FK (no cycle) |
| used_at, used_by | DateTime, FK(User) PROTECT `+` | |
| layers_on_roll | PosInt null | denorm at Layering complete |
| layer_length_meters | Decimal null | denorm |
| remaining_length_meters, remaining_weight_kg | Decimal null | denorm leftover (synced from `RemainingClothOfClothRoll`) |

Indexes: `status`; `(cloth_type, cloth_color)`; `(storage_location, status)`; `(adda, status)`.
Property `display_summary` → `"CR-000142 · Cotton · Red - 42 inch"`.

### 6.4 `production` (23 models — the heart)

#### `Product`
| Field | Type | Notes |
|---|---|---|
| code | Char(30) unique | short slug; drives Adda codes + barcodes |
| name, description, is_active | | |
| adda_counter | PosInt default 0 | per-product Adda numbering; **only** `create_adda` increments under row lock |
| patterns | M2M(ProductPattern) through `ProductPatternAssignment` | |

#### `Stage` (the library)
`objects` + `active` managers. `code` slug locked on edit.
Fields: code (slug32 unique), name, description, is_active, **access_by_skill** M2M(Skill),
**access_by_role** M2M(inventory.Role).

#### `WorkflowStage` (per-product flow)
| Field | Type | Notes |
|---|---|---|
| product | FK(Product) CASCADE | |
| order | PosInt | |
| stage | FK(Stage) PROTECT | |

`unique_together`: `(product, order)`, `(product, stage)`. Back-compat shims:
`.stage_type` → `stage.code`, `.get_stage_type_display()` → `stage.name`.

#### `Adda` (one production batch)
| Field | Type | Notes |
|---|---|---|
| code | Char(40) unique, `editable=False` | `T-SHIRT-001` |
| product | FK(Product) PROTECT | |
| current_stage | FK(WorkflowStage) PROTECT null `+` | NULL when COMPLETED |
| status | Char choices | in_progress / on_hold / completed / cancelled |
| started_at | DateTime auto_now_add | |
| completed_at | DateTime null | |
| created_by | FK(User) PROTECT null `+` | |

Indexes: `status`, `(product, status)`, `current_stage`. Property `total_pieces` = Σ barcode_batches.total_pieces.

#### `AddaStageRecord` (polymorphic stage parent)
| Field | Type | Notes |
|---|---|---|
| adda | FK(Adda) CASCADE | |
| workflow_stage | FK(WorkflowStage) PROTECT `+` | |
| workers | M2M(User) | roster only (visibility). Earnings tracked separately on `expense.StageWorkAssignment` (standalone FK), NOT via a `through`. |
| started_at, completed_at | DateTime null | |
| draft_layer_length_meters | Decimal(8,2) null | generic draft state |
| draft_duration_minutes | PosInt null | |
| draft_notes | Text | |
| completed_by | FK(User) PROTECT null `+` | |

`unique_together (adda, workflow_stage)`. Indexes `(adda, -started_at)`, `(workflow_stage, completed_at)`.
Property `is_active` = started but not completed.

#### Typed stage records (OneToOne → AddaStageRecord, CASCADE)
| Model | Key fields |
|---|---|
| `LayeringRecord` | lay_count, total_colors, duration_minutes, layer_length_meters (null), **rolls_used** M2M(ClothRoll), notes. Props: `total_fabric_used_meters` (lay_count × layer_length), `stage_started_at` |
| `CuttingPatternRecord` | video (FileField, per-Adda path), notes |
| `CuttingRecord` | pieces_cut (denorm = Σ bundle items), notes |
| `BarcodeGenerationRecord` | total_barcodes (denorm), notes, generated_at (null until generate) |

#### Layering support models
| Model | Key fields |
|---|---|
| `LayeringRollEntry` | stage_record FK CASCADE, roll FK(ClothRoll) PROTECT, width_verified_inch, weight_verified_kg, **layers_on_roll**, notes, attached_by, attached_at. `unique_together (stage_record, roll)` |
| `RemainingClothOfClothRoll` | roll FK PROTECT, source_adda FK(Adda) PROTECT, layering_entry FK SET_NULL, remaining_weight_kg, remaining_length_meters, is_consumed, consumed_in_adda FK, consumed_at, notes, created_by. Leftover-cloth tracker (Phase 6) |

#### Pattern library
| Model | Key fields |
|---|---|
| `ProductPattern` | code (slug48 unique), name, description, reference_image, is_active. `objects` + `active` managers |
| `ProductPatternAssignment` | product FK CASCADE, pattern FK PROTECT, **pieces_count** (PosSmallInt default 1), notes. `unique_together (product, pattern)` — e.g. T-Shirt = 1 Front + 1 Back + 2 Sleeve |
| `ProductSize` | product FK CASCADE, code (slug16), label, display_order, is_active. `unique_together (product, code)` — per-product size chart |

#### Cutting-pattern stage detail
| Model | Key fields |
|---|---|
| `CuttingPatternPhoto` | record FK CASCADE, image (Pillow-compressed q80 ≤2400px), caption, uploaded_by |
| `CuttingPatternVerification` | record FK CASCADE, assignment FK PROTECT, verified_by, verified_at, photo FK SET_NULL, note. `unique_together (record, assignment)` |
| `CuttingPatternSizeAllocation` | record FK CASCADE, size FK PROTECT, proportion_pct (PosSmallInt). `unique_together (record, size)`; Σ=100 enforced at complete |

#### Cutting stage detail
| Model | Key fields |
|---|---|
| `CuttingPieceBreakup` | cutting_record FK CASCADE, size/color/pattern FK PROTECT, count, **consumed_count** (denorm), roll FK null. `unique_together (cutting_record, size, color, pattern)`. Prop `available_count = count − consumed_count` |
| `CuttingBundle` | cutting_record FK CASCADE, size FK PROTECT, **total_pieces** (denorm = Σ items), bundle_number. `unique_together (cutting_record, size)` — one bundle per size |
| `CuttingBundleItem` | bundle FK CASCADE, pattern/color FK PROTECT, count, **source_breakup** FK(CuttingPieceBreakup) PROTECT null. `unique_together (bundle, pattern, color)` |

#### Frozen output + stub
| Model | Key fields |
|---|---|
| `AddaProductSizeColorPieceBreakdown` | adda FK PROTECT, product FK PROTECT, cutting_record FK CASCADE, bundle FK SET_NULL, size/color FK PROTECT null, **verified_piece_count**, created_by. `unique_together (cutting_record, size, color)`. **Manufacturing truth — frozen at cutting complete, deleted on cutting reopen** |
| `LabelPrintQueue` | **STUB** — export_batch FK(tracking.BarcodeExportBatch) PROTECT, status (queued/sent/received/printed/cancelled), vendor_name, sent/received/printed_at, notes. No service logic yet |

### 6.5 `tracking`

#### `BarcodeBatch` — contiguous seq range per (Adda, color, size)
Stores ranges, not rows: a 500-piece Adda = ~5 batch rows, not 500.
| Field | Type | Notes |
|---|---|---|
| adda | FK(Adda) PROTECT | |
| product | FK(Product) PROTECT `+` | denorm for fast filter |
| bundle | FK(CuttingBundle) PROTECT null | source link |
| color | FK(ClothColor) PROTECT null `+` | null for legacy single-batch |
| size | FK(ProductSize) PROTECT null `+` | |
| start_seq, end_seq | PosInt | 1-indexed, inclusive |
| total_pieces | PosInt | denorm = end−start+1 |

`unique_together (adda, color, size)`. Indexes `(adda, start_seq)`, `(adda, end_seq)`.
Props: `start_value`, `end_value`, `value_for_seq(seq)`.

#### `BatchBarcode` — lazy per-piece scan state
Born only on first scan/status touch. Value `{ADDA_CODE}-{PIECE_SEQ:04d}`.
| Field | Type | Notes |
|---|---|---|
| adda | FK(Adda) PROTECT | |
| batch | FK(BarcodeBatch) PROTECT null | |
| piece_seq | PosInt | 1..N within Adda |
| value | Char(60) unique | QR payload |
| status | Char choices | pending / packed / dispatched / missing |
| last_scanned_at, last_scanned_by | DateTime, FK(User) `+` | |
| size, color, pattern, roll | FK PROTECT null `+` | metadata (new barcodes populate all four) |

`unique_together (adda, piece_seq)`. Indexes `(adda, status)`, `status`, `(size, color, status)`.

#### History tables (append-only; `history_service.log_*` only)
| Model | change_type choices | extra fields |
|---|---|---|
| `ClothRollHistory` | created / status_changed / location_moved / weight_updated / archived | roll FK, actor, field_name, old/new_value, note |
| `AddaHistory` | created / stage_advanced / stage_reopened / status_changed / roll_assigned / completed | adda FK, actor, stage_from/to FK, roll FK, note |
| `ProductHistory` | created / updated / archived | product FK, actor, field_name, old/new_value |

All indexed `(entity, -created_at)`.

#### `BarcodeExportBatch` — export manifest
| Field | Type | Notes |
|---|---|---|
| export_code | Char(24) unique | `EXP-2026-001` (service counter) |
| adda | FK(Adda) PROTECT | |
| product | FK(Product) PROTECT `+` | denorm |
| barcode_gen_record | FK(BarcodeGenerationRecord) PROTECT | source; must be complete |
| export_method | Char choices | csv / xlsx / pdf |
| exported_by | FK(User) PROTECT `+` | |
| total_labels | PosInt | frozen Σ at export time |

File content is **regenerated on download** (not stored) — storage stays lean; re-download by `export_code`.

### 6.6 `storefront` (public marketing CMS, independent)

| Model | Purpose |
|---|---|
| `HomePageConfig` | **Singleton** (save() enforces one active row) — hero, stats, CTA banner, section headings, images, footer |
| `Category` | Homepage category grid (name, subtitle, image/icon_svg, display_order, is_active) |
| `FeaturedProduct` | Showcased products (name, category FK SET_NULL, price/original_price, sizes CSV, badge, image). Props `size_list`, `display_category`, `badge_css_class` |
| `HeroShowcaseCard` | Hero right-side cards |
| `WhyUsCard` | "Why choose us" feature cards |
| `FooterLink` | Footer links grouped by column (products/company/access) |
| `NavLink` | Public navbar links |

---

### 6.7 `expense` (6 models — worker payroll, downstream of production)

> Added 2026-06-02. Full field-level design lives in
> [docs/production/PAYROLL_ARCHITECTURE.md](docs/production/PAYROLL_ARCHITECTURE.md) +
> [docs/production/SETTLEMENT_ARCHITECTURE.md](docs/production/SETTLEMENT_ARCHITECTURE.md).
> Settlement-based (NOT monthly). Balance is ALWAYS derived, never stored.

| Model | Purpose |
|---|---|
| `StageWorkAssignment` | A worker's allocated slice of a stage's work. Standalone FK row (NOT an M2M `through`). `earning = allocated_quantity × earning_rate_snapshot`, frozen at allocation. |
| `WorkerLedgerEntry` | Append-only, immutable money ledger — the financial source of truth. `amount` always positive; direction = `entry_type` (credit/debit). Payable = SUM(credit) − SUM(debit). |
| `WorkerAdvance` | Cash given before earnings — a SEPARATE loan pool. Does NOT post to the payable ledger; recovered at settlement by owner's choice. |
| `PayrollSettlement` | On-demand payout event. Clears (part of) payable + recovers (part of) advances. Snapshots state for audit; balances still derived live. |
| `PayrollSettlementItem` | One per-advance recovery line of a settlement (owner-controlled). |
| `WorkerProfile` | Per-worker payroll metadata (bank/UPI, opening_advance). No stored totals. |

---

## 7. Service Layer Reference

18 service modules. Views call services; services own all multi-row writes and transactions.

### `inventory/services/permission_service.py` — RBAC engine (read-only)
- `user_role_code(user)` / `user_role_codes(user)` — primary + extra_roles
- `user_has_role(user, codes)` — any-overlap
- `user_has_perm(user, 'app.codename')` — **canonical check**; order: not-auth→False → `is_superuser`→True → `role.code=='super_admin'`→True → `role.permissions.exists()` → Django fallback
- `user_can_view_financials` / `user_can_edit_financials` — gate on `FINANCIAL_ROLES`
- `build_menu_for(user, path)` — sidebar; super_admin→all, else `SidebarItemRule` DB rows, else hardcoded predicates
- `permissions_sectioned_for_role_editor` — curated role editor (hides service-only join tables)
- Constants: role codes, `MANAGEMENT_ROLES={super_admin,manager}`, `PRODUCTION_ROLES={…,karigar}`, `FINANCIAL_ROLES={super_admin,accountant}`, `STOREFRONT_ROLES`, the `SIDEBAR` registry

### `raw_materials/services/roll_service.py`
- `_next_roll_id()` — **sole** roll-ID allocator (`nextval('cloth_roll_seq')`)
- `bulk_create_rolls(...)` — *atomic*; N rolls + history; financial-field gate; up to 200/submit
- `update_roll_details(...)` — *atomic*; field-level update (NOT_USED only) + per-field history
- `assign_roll_to_adda(...)` — *atomic*; roll→USED, history; called by layering

### `raw_materials/services/master_service.py`
- `archive_master` / `restore_master` / `hard_delete_master` — *atomic*; soft-archive default, `ProtectedError`→ValidationError

### `production/services/_shared.py` — auth gates (no writes)
`_ensure_can_manage` (PRODUCTION_ROLES), `_ensure_management` (MANAGEMENT_ROLES), `_ensure_assigned_worker`, `_ensure_layering_skill`, `_ensure_can_complete_layering` (helper-only).

### `production/services/adda_service.py`
- `create_adda(user, *, product)` — *atomic*; **`Product.objects.select_for_update()`** → `adda_counter += 1` → create Adda; pre-checks skilled-pool + ≥1 workflow stage; auto-creates layering AddaStageRecord; logs CREATED
- `advance_to_next_stage(adda, user)` — *atomic*; **the only mover of current_stage/status**; logs STAGE_ADVANCED / COMPLETED

### `production/services/layering_service.py` — Stage 1
`get_layering_snapshot`, `start_layering`, `attach_roll_to_layering`, `update_layering_roll_entry`,
`detach_roll_from_layering`, `save_layering_breakup`, `save_layering_draft`, `record_remaining_cloth`,
`remove_remaining_cloth`, `complete_layering` (→ LayeringRecord + advance),
`reopen_layering` (*select_for_update*; refused if downstream started; refills draft_* before delete).

### `production/services/cutting_pattern_service.py` — Stage 2
`start_pattern_stage`, `ensure_pattern_record`, `attach_photo` (Pillow compress), `save_pattern_record`,
`verify_pattern` / `unverify_pattern`, `set_size_allocation` (full-replace),
`complete_pattern_stage` (9-step validation: video|photo, all assignments verified, Σ alloc=100),
`reopen_pattern_stage` (*select_for_update*; record+photos kept).

### `production/services/cutting_service.py` — Stage 3 (largest)
`preview_barcode_batches`, `get_cutting_snapshot`, `get_suggested_breakup`,
`_materialize_breakdown` (**sole writer of AddaProductSizeColorPieceBreakdown**),
`start_cutting`, `create_bundle`, `create_bundle_with_pieces`,
`add_pieces_to_bundle` (*select_for_update* on breakup; consumes available_count),
`add_item_to_bundle` / `add_bundle_item`, `delete_bundle_item` / `delete_bundle` (restore consumed_count),
`upsert_breakup_row` / `delete_breakup_row`, `save_cutting_draft`,
`complete_cutting` (dual path: legacy `pieces_cut` vs `_complete_cutting_from_breakup`; inline barcode gen if no bg-stage),
`reopen_cutting` (*select_for_update*; 3 blockers; deletes breakdown + BarcodeBatch).

### `production/services/barcode_generation_service.py` — Stage 4
`preview_barcode_counts`, `get_barcode_snapshot`, `start_barcode_generation`,
`generate_barcodes` (→ tracking.generate_from_breakdown; one-shot guard),
`complete_barcode_generation` (Σbatch == Σbreakdown == total validation),
`reopen_barcode_generation` (*select_for_update*; blocked on scan/export; deletes BarcodeBatch).

### `production/services/{product,product_size,flow,access,activity,stage}_service.py`
- `product_service` — Product CRUD (super_admin), auto-seeds Layering WorkflowStage, ProductHistory
- `product_size_service` — ProductSize CRUD (super_admin)
- `flow_service` — `add_stage_to_product_flow`, `remove_…` (blocked: last stage / Adda on it / record exists), `move_…` (parking-slot swap)
- `access_service` — `user_can_access_stage` (mgmt bypass → role → skill, fail-closed), `stage_access_map`
- `activity_service` — derived timeline (UNION of 4 FK sources), read-only
- `stage_service` — back-compat re-export shim

### `tracking/services/barcode_service.py` — sole writer of BarcodeBatch + BatchBarcode
- `generate_for_cutting(cutting_record)` — *atomic*; range allocation from **live** CuttingBundleItem; one-shot (IntegrityError if batches exist)
- `generate_from_breakdown(record)` — *atomic*; **canonical** path; same algorithm from **frozen** breakdown rows
- `parse_value` / `resolve_value` — parse + range-containment lookup
- `get_or_create_piece(batch, seq)` — *atomic*; **lazy-creates** BatchBarcode on first scan
- `qr_data_uri(...)` — QR PNG; `mark_status(user, value, status)` — *atomic*

### `tracking/services/barcode_export_service.py` — sole writer of BarcodeExportBatch
`generate_csv` / `generate_xlsx` (openpyxl) / `generate_pdf_summary` (reportlab) — each *atomic*, gate
requires barcode-gen complete; `_next_export_code` (`EXP-YYYY-NNN`); `regenerate_for_export` (live re-render); `list_exports`.

### `tracking/services/history_service.py` — sole writer of all 3 history tables
`log_roll`, `log_adda`, `log_product`. No signals, no save overrides. Callers wrap in their own atomic.

### `storefront/services/listing_service.py`
`ListingService` static class — Category + FeaturedProduct CRUD; `reorder_products` (*atomic* bulk update).

---

## 8. Single-Writer Discipline

| Table / value | Sole writer |
|---|---|
| `Adda.code` + `Product.adda_counter` | `adda_service.create_adda` (SELECT FOR UPDATE) |
| `Adda.current_stage` / `status` transitions | `adda_service.advance_to_next_stage` |
| `ClothRoll.roll_id` allocation | `roll_service._next_roll_id` (PG sequence) |
| `BarcodeBatch`, `BatchBarcode` | `tracking/barcode_service.py` |
| `AddaProductSizeColorPieceBreakdown` | `cutting_service._materialize_breakdown` |
| `BarcodeExportBatch` | `tracking/barcode_export_service.py` |
| `ClothRollHistory` / `AddaHistory` / `ProductHistory` | `tracking/history_service.log_*` |

No Django signals exist; `signals.py` is tombstoned with rationale. Counter drift is caught by `test_counter_invariants.py`.

---

## 9. URL & View Surface

Root mounts (`config/config/urls.py`): `/admin/`, `/` (public home), `/app/` (accounts),
`/accounts/` (allauth), `/inventory/`, `/storefront/`, `/raw-materials/`, `/production/`, `/tracking/`.

**~122 views total (~117 CBV, ~5 FBV).** All require login; gated by mixins
(`ProductionRoleMixin`, `SuperAdminOnlyMixin`, perm/skill mixins).

### accounts (`/app/`)
Auth: `login`, `verify_otp`, `resend_otp`, `login_password`, `signup`(+verify/resend),
`forgot_password`, `reset_password_verify`, `home`, `logout`.
Admin (super_admin): users CRUD (`user_list/add/edit/delete`), skills CRUD.

### inventory (`/inventory/`)
`dashboard` (FBV, PRODUCTION_ROLES), `my-dashboard` (FBV, any user),
roles CRUD (super_admin), `sidebar-access` (super_admin).

### raw_materials (`/raw-materials/`)
`dashboard`, `cloth-dashboard`; rolls: `roll-list`, `roll-bulk-create` (financial editor),
`roll-detail`, `roll-edit` (financial), `roll-assign` (layering master);
masters (cloth-types/colors/storage-locations): list (all) + create/edit/archive/delete (super_admin).

### production (`/production/`) — 63+ views
- Dashboard: `dashboard` (Adda KPIs)
- Products (super_admin write): `product-list/create/update/archive`, `product-flow`, `product-patterns`, `product-sizes`
- Pattern library (perm-gated `productpattern`): `pattern-list/add/edit/delete`
- Stage library (super_admin): `stage-list/add/edit/delete`
- Addas: `adda-list`, `adda-create`, `adda-detail` (tabbed pipeline), `stage-panel` (embedded)
- **Layering** `/addas/<code>/layering/`: workspace, start, attach-roll, quick-create-roll, full-create-roll, entries/<pk>/(update,remove), remaining/<pk>/remove, complete, reopen
- **Cutting Pattern** `/addas/<code>/pattern/`: workspace, start, save, photos/(add,<pk>/remove), verify, unverify, sizes, complete, reopen
- **Cutting** `/addas/<code>/cutting/`: complete(legacy), workspace, start, breakup/(save,<pk>/delete), bundle/(create,<pk>/add-item,<pk>/add-pieces,item/save,item/<pk>/delete,<pk>/delete), draft, workspace/complete, reopen
- **Barcode Gen** `/addas/<code>/barcode-gen/`: workspace, start, generate, complete, reopen

Pattern per stage: `*-workspace` (GET) · `*-start` (POST mgmt) · `*-<action>` (POST worker) · `*-complete` (POST helper) · `*-reopen` (POST mgmt).

### tracking (`/tracking/`)
`dashboard`, `barcode-list`, `barcode-print` (QR sheet), `barcode-export` (legacy CSV FBV),
`scan` (FBV — `resolve_value` + `get_or_create_piece`), `roll-history`, `adda-history`,
exports: `export-list`, `export-csv/xlsx/pdf` (POST), `export-download` (re-download by code).

### storefront (`/storefront/`)
`public_home` (FBV, public); listing_team CRUD: products + categories list/add/edit/delete.

---

## 10. RBAC & Permissions

**3-layer defense for stage access:**
1. `MANAGEMENT_ROLES` (super_admin + manager) — hardcoded bypass in `access_service`
2. `Stage.access_by_role` M2M — DB-driven
3. `Stage.access_by_skill` M2M — skill-gated (floor workers); fail-closed if none match

**Roles:** `super_admin` (universal bypass), `manager` (production CRUD), `karigar` (floor),
`accountant` (financial fields), `listing_team` (storefront).

| Action | Who |
|---|---|
| Start a stage | MANAGEMENT_ROLES |
| Mutate stage (rolls, photos, breakup, bundles, generate) | cutting_master OR helper skill (mgmt bypass) |
| **Complete + advance** | cutting_master_helper OR super_admin |
| Reopen stage | MANAGEMENT_ROLES |
| Export barcodes | PRODUCTION_ROLES + service gate (bg-stage complete) |
| Stage CRUD | `production.{view,add,change,delete}_stage` (super_admin bypass) |
| Product / size / role editor | super_admin only |
| Financial fields (supplier, cost_per_kg) | FINANCIAL_ROLES |
| Storefront listings | super_admin OR listing_team |

`user_has_perm` short-circuits on ROLE_SUPER_ADMIN — bootstrap-safe. No raw `is_superuser` in views.

---

## 11. Reopen Semantics Matrix

All four reopens are mgmt-only and lock the stage record with `select_for_update()`.

| Stage | Refused when | On reopen |
|---|---|---|
| **Layering** | any downstream stage `started_at` set | copy LayeringRecord header → `draft_*`, delete LayeringRecord, clear completed, current_stage→layering, status→IN_PROGRESS (per-entry layers + leftovers preserved) |
| **Cutting Pattern** | any downstream started | clear sr completed; record + photos kept |
| **Cutting** | (1) any BatchBarcode scanned · (2) barcode_gen stage started · (3) any BarcodeExportBatch exists | delete AddaProductSizeColorPieceBreakdown + delete BarcodeBatch, clear completed |
| **Barcode Generation** | (1) any BatchBarcode scanned · (2) any BarcodeExportBatch exists | delete BarcodeBatch, reset `generated_at`=None + `total_barcodes`=0, clear completed |

Every reopen logs `AddaHistory.STAGE_REOPENED`.

---

## 12. Denormalised Counters & Invariants

No DB triggers (no-signals rule). Services recompute; `test_counter_invariants.py` catches drift.

| Field | Source of truth | Recompute path |
|---|---|---|
| `Product.adda_counter` | next Adda code | SELECT FOR UPDATE in `create_adda` |
| `CuttingRecord.pieces_cut` | Σ CuttingBundleItem.count | `_complete_cutting_from_breakup` |
| `CuttingBundle.total_pieces` | Σ items.count | `_recompute_bundle_total` on mutation |
| `CuttingPieceBreakup.consumed_count` | Σ items where source=row | `_recompute_breakup_consumed` |
| `BarcodeGenerationRecord.total_barcodes` | Σ BarcodeBatch.total_pieces | `generate_barcodes` |
| `BarcodeBatch.total_pieces` | end−start+1 | immutable after create |
| `ClothRoll.remaining_*` | primary leftover row | denorm at Layering complete + leftover edit |
| `AddaProductSizeColorPieceBreakdown.verified_piece_count` | Σ CuttingBundleItem by (size,color) | materialised at cutting complete, frozen until reopen |

---

## 13. Identifier Formats

| Entity | Format | Example | Generator |
|---|---|---|---|
| Roll ID | `CR-NNNNNN` | `CR-000142` | Postgres `cloth_roll_seq` (`_next_roll_id`) |
| Adda code | `{PRODUCT}-NNN` | `T-SHIRT-001` | per-product counter under row lock |
| Barcode value | `{ADDA}-{SEQ:04d}` | `T-SHIRT-001-0042` | barcode range layout |
| Export code | `EXP-YYYY-NNN` | `EXP-2026-001` | `_next_export_code` |

QR payload = `{BASE_URL}/tracking/scan/{value}/` — phone camera scans natively.

---

## 14. Iframe + postMessage Stage Embedding

- Embedded panels at `/production/addas/<code>/stage/<stage_type>/?embedded=1`
- `StagePanelView` + `AddaDetailView` decorated `@xframe_options_sameorigin` (defeats default DENY)
- After `complete_*` from iframe → redirect to NEW current stage's embedded URL `?advanced=1`
- Embedded JS detects `?advanced=1` → `postMessage {type:'stage-advanced'}` to parent
- Parent (`adda_detail.html`, `user_dashboard.html`) listens → `window.location.reload()`
- Auto-resize via `ResizeObserver` + `postMessage {type:'stage-panel-resize', height, code, stage}`

---

## 15. Settings, Dependencies, Seed Data

**Settings:** `config/settings/base.py` + `local.py` + `production.py`. Local run:
```bash
env/bin/python config/manage.py <cmd>   # settings: config.settings.local
```

**Dependencies (`requirements.txt`):** Django 5.2, psycopg2-binary, django-allauth 0.61.1,
python-decouple, dj-database-url, Pillow 10.2, whitenoise, qrcode[pil] 7.4.2,
openpyxl 3.1.2 (XLSX), reportlab 4.1.0 (PDF).

**Migrations:** accounts 10 · inventory 17 · raw_materials 9 · production 23 · tracking 9 · storefront 2.

**Seed data:** 5 Products (3-PATTI, T-SHIRT, NIKKAR, PAJAMA, 1-6) each get `[layering, cutting]` by default;
4 ClothTypes; 6 ClothColors; 2 StorageLocations (PACKING, ROHINI); 3 Stage rows
(layering, cutting, cutting_pattern with cutting_master + helper skills attached).

**Sanity:**
```bash
env/bin/python config/manage.py check
env/bin/python config/manage.py makemigrations --dry-run   # → No changes detected
env/bin/python config/manage.py test production tracking accounts   # 196/196
```

---

## 16. Known Gaps & Where to Extend Stages

**To add a new stage (e.g. Stitching, Packing, Dispatch):**
1. Create the `Stage` row (admin or seed migration) with `code` + access M2Ms.
2. Add a typed record model (OneToOne → `AddaStageRecord`) if it carries stage-specific data.
3. Write `production/services/<stage>_service.py` following the `start_ → mutate → complete_ → reopen_` shape.
   `complete_*` **must** call `advance_to_next_stage`.
4. Add views (workspace + action POSTs) + URL patterns; route the panel in `StagePanelView`.
5. Add `<stage>_workspace.html` + `_stage_panel_<stage>.html`.
6. Attach the stage to products via the flow editor (`/production/products/<pk>/flow/`).
**No core/model changes to `Adda`, `WorkflowStage`, or `AddaStageRecord` are needed.**

**Open follow-ups (from AUDIT_2026_05_29.md):**
- CLAUDE.md rule #5 references dead `StockService`/`StockLedger` — should be corrected.
- `LabelPrintQueue` is a stub (no service logic).
- 5 forms still lack the mandatory form-shell; 19 templates have inline empty-state rows.
- Dashboard perf unprofiled under 40-user load; sidebar build not cached.
- Storefront has zero test coverage; legacy `barcode_export_csv` view untested.
- ffmpeg video recompression for cutting_pattern uploads deferred.
- Future-arch scaffolds (feature flags, machine tracking) not started. (The `expense`
  payroll app SHIPPED 2026-06-02 — see docs/production/PAYROLL_ARCHITECTURE.md +
  SETTLEMENT_ARCHITECTURE.md; it is not yet detailed in §6 below.)

---

*Generated from a full code dig on 2026-06-01. Cross-check against `docs/production/OVERVIEW.md`,
`ARCHITECTURE.md`, and `AUDIT_2026_05_29.md` for sub-system deep dives.*
