# Kapil Enterprises Inventory — Project Architecture

**Stack:** Django 5.2 + PostgreSQL 14+
**Status:** Production tracking (Stage 1 Layering shipped end-to-end). 74 tests green. `manage.py check` clean.

End-to-end factory tracking app: cloth intake → Adda (production batch) → Layering → Cutting → barcode generation → future packing/dispatch.

---

## App layout

| App | Owns | Imports | Exports |
|---|---|---|---|
| `accounts` | `User` (email login), `Skill`, signals | `inventory.Role` | auth, skill helpers |
| `inventory` | `Role`, `Permission` constants, RBAC service, sidebar registry, dashboard view | `accounts` | `permission_service`, `user_dashboard` |
| `raw_materials` | `ClothType`, `ClothColor`, `StorageLocation`, `ClothRoll` | `inventory.services` (RBAC) | roll services, master CRUD |
| `production` | `Product`, `WorkflowStage`, `Adda`, `AddaStageRecord`, `LayeringRecord`, `LayeringRollEntry`, `RemainingClothOfClothRoll`, `CuttingRecord` | `accounts.skills`, `inventory.services`, `raw_materials.*` | adda + stage services, activity timeline |
| `tracking` | `BatchBarcode`, `ClothRollHistory`, `AddaHistory`, `ProductHistory` | upstream apps | barcode generator, history loggers |
| `storefront` | featured products, categories | `inventory` (roles) | listing CRUD |

**Cross-app FK direction:** downstream only.
- `raw_materials.ClothRoll.adda → 'production.Adda'` (string FK, no import cycle)
- `production.RemainingClothOfClothRoll → raw_materials.ClothRoll + production.Adda`
- `tracking.*` references upstream apps
- `raw_materials` imports **nothing** from `production` or `tracking`

---

## Per-stage isolation (Phase 6 refactor)

Stages live in their own files. New stages drop in without touching siblings.

```
production/
├── forms/
│   ├── _shared.py          # widgets, querysets, label helpers
│   ├── layering.py         # Stage 1 forms (Start, AttachRoll, Edit, RemainingCloth, Complete)
│   ├── cutting.py          # Stage 2 forms
│   ├── product_forms.py    # non-stage CRUD
│   └── adda_forms.py       # non-stage CRUD
├── services/
│   ├── _shared.py          # auth helpers shared across stages
│   ├── layering_service.py # Stage 1 state transitions
│   ├── cutting_service.py  # Stage 2 state transitions
│   ├── adda_service.py     # Adda lifecycle (create + advance)
│   ├── product_service.py  # Product CRUD
│   ├── activity_service.py # activity timeline derivation
│   └── stage_service.py    # back-compat shim (re-exports)
├── templates/production/
│   ├── _stage_panel_layering.html  # Stage 1 reusable partial (used in iframe + standalone)
│   ├── _stage_panel_cutting.html
│   ├── _stage_card_layering.html   # tab summary on Adda Detail
│   ├── _stage_card_cutting.html
│   ├── stage_panel_embedded.html   # chromeless wrapper for iframe
│   ├── stage_panel_standalone.html # full-page wrapper for standalone view
│   └── adda_detail.html            # tab UI (iframes per stage)
├── views/
│   ├── stage_views.py      # all stage views (per-stage class clusters)
│   ├── adda_views.py
│   ├── product_views.py
│   └── dashboard.py
└── urls.py
```

Add new stage = `forms/<stage>.py` + `services/<stage>_service.py` + `_stage_panel_<stage>.html` + `_stage_card_<stage>.html` + register `WorkflowStage.StageType.<NEW>` + dispatch in `StagePanelView`.

---

## Identifier formats

| Entity | Format | Example | Allocator |
|---|---|---|---|
| Roll ID | `CR-NNNNNN` | `CR-000142` | Postgres `cloth_roll_seq` sequence |
| Adda code | `{PRODUCT_CODE}-NNN` | `T-SHIRT-001` | per-product counter w/ `SELECT FOR UPDATE` |
| Piece barcode | `{ADDA_CODE}-{PIECE_SEQ:04d}` | `T-SHIRT-001-0042` | bulk_create per Cutting completion |

---

## RBAC + skills

### Roles
| Role | Scope |
|---|---|
| `super_admin` | universal escape hatch |
| `manager` | production CRUD, worker assignment |
| `karigar` | floor worker (scoped views) |
| `accountant` | view + edit financial fields (supplier, cost_per_kg) |
| `listing_team` | storefront only |

Convenience sets:
- `MANAGEMENT_ROLES = {super_admin, manager}`
- `PRODUCTION_ROLES = {super_admin, manager, karigar}`
- `FINANCIAL_ROLES = {super_admin, accountant}`

### Skills (independent axis from role)
| Skill | Role in workflow |
|---|---|
| `cutting_master` | guides Layering setup, can attach rolls |
| `cutting_master_helper` | executes layering + can complete Layering → Cutting transition |
| `dhage_katne_wala`, `embroidery`, `tailoring`, `other` | future stages |

Skill checks via `accounts.skills.user_has_skill(user, names)`. Auth gates layered:
- `_ensure_can_manage` → PRODUCTION_ROLES
- `_ensure_management` → MANAGEMENT_ROLES
- `_ensure_assigned_worker` → on stage_record.workers M2M OR management bypass
- `_ensure_layering_skill` → cutting_master / helper OR management bypass
- `_ensure_can_complete_layering` → helper skill OR super_admin (strict)

---

## Adda lifecycle (high level)

```
create_adda(user, product)
  → AddaStageRecord(layering) auto-created
    + workers M2M auto-populated from skilled users
    + ClothRoll inventory check (must have ≥1 skilled user)
  → status=IN_PROGRESS
  → current_stage=WorkflowStage[layering]
  → AddaHistory.CREATED logged

[per-roll workflow on Layering stage]
  attach_roll_to_layering   → LayeringRollEntry created, ClothRoll.status=USED
  save_layering_breakup     → upsert layers + leftover per row + denorm to ClothRoll
  save_layering_draft       → bulk + header (draft_*) fields on stage_record

complete_layering(adda, ...)
  → validates per-row (layers + leftover)
  → LayeringRecord created (lay_count, total_colors, layer_length, duration)
  → ClothRoll.layers_on_roll + layer_length_meters copied (inventory-level lookup)
  → AddaStageRecord.completed_at + completed_by set
  → drafts cleared
  → advance_to_next_stage → current_stage=cutting
  → AddaHistory.STAGE_ADVANCED logged

complete_cutting(adda, pieces_cut, ...)
  → CuttingRecord(pieces_cut)
  → generate_for_cutting → N BatchBarcode rows
  → advance_to_next_stage → COMPLETED
  → AddaHistory.COMPLETED logged
```

---

## Adda Detail UI (tabs)

```
┌──────────────────────────────────────────────┐
│ Hero — Adda code + status + product           │
├──────────────────────────────────────────────┤
│ Tab bar — [Layering] [Cutting] [future...]    │
├──────────────────────────────────────────────┤
│ Tab pane (iframe → /stage/<type>/?embedded=1) │
│   ✓ live edit/save inside iframe              │
│   ✓ postMessage auto-resize iframe to content │
│   ✓ "Open in new window" deep link            │
├──────────────────────────────────────────────┤
│ Activity feed (chronological, all users)      │
└──────────────────────────────────────────────┘
```

Same per-stage partial is reused on User Dashboard accordions for skilled users (mobile-first iframe).

---

## Dashboard routing (unified Phase 4)

`/inventory/dashboard/` (admin) and `/inventory/my-dashboard/` (non-admin) render the same template.

Both show:
- **Active Addas** — list of in-progress Addas with stage pipeline
  - Skilled users (cutting_master / helper / management) → accordion with iframe to live stage panel
  - Non-skilled → status-only card
- **My Active Stages** — assigned stage records
- **Helper Stats** (cutting_master_helper only) — completed count, active count, total layers, total minutes
- **My Recent Activity** — cross-Adda timeline

---

## Activity tracking

Derived (no event table). `production/services/activity_service.py` UNIONs:
- `tracking.AddaHistory` (stage transitions, roll assigns)
- `tracking.ClothRollHistory` (roll status changes, scoped to adda)
- `production.LayeringRollEntry` (attach events with verified width/weight)
- `production.AddaStageRecord` (stage completion events)

Returns sorted `ActivityEvent(at, actor, verb, adda_code, target, note)` tuples.

Two entry points:
- `adda_activity(adda, user=None)` — Adda Detail timeline
- `user_activity_across_addas(user, limit=30)` — User Dashboard timeline

---

## Discipline (rule recap, see CLAUDE.md)

1. Service layer owns all multi-row writes. Views call services.
2. History tables written ONLY via `tracking.services.history_service.log_*`.
3. Permissions via `permission_service` + skill helpers. No raw `is_superuser` in views.
4. `on_delete=PROTECT` on master FKs; soft archive via `is_active`.
5. Postgres-only (sequence + SELECT FOR UPDATE).
6. Race-safe per-product counter for Adda codes.
7. ClothRoll.adda FK + ClothRoll.status flipped USED only via `raw_materials.assign_roll_to_adda`.
8. ModelForm `_post_clean()` mutates instance before service runs — services must `refresh_from_db()` if comparing pre/post values.

---

## Test surface

74 tests across 7 files. All exercise production behavior. None are throwaway.

| File | Coverage |
|---|---|
| `production/tests/test_layering_workflow.py` | Start/attach/update/detach/complete + breakup + leftover (LayerMetricsAndLeftoverTests) |
| `production/tests/test_phase4.py` | create_adda auto-tag, retro-tag signal, activity timeline |
| `production/tests/test_golden_path.py` | end-to-end bulk→Adda→Layering→Cutting→barcodes |
| `production/tests/test_adda_service.py` | Per-product counter atomicity |
| `tracking/tests/test_barcode_service.py` | Barcode generation per Cutting |
| `inventory/tests.py` | Dashboard helper section (UserDashboardHelperTests) |
| `raw_materials/tests/test_roll_service.py` | Sequence, bulk_create_rolls, **UpdateRollDetailsTests** (regression for ModelForm mutation) |

---

## Doc map

- **`docs/ARCHITECTURE.md`** (this file) — top-level project arch
- **`docs/production/LAYERING_STAGE.md`** — Stage 1 deep dive
- `docs/production/OVERVIEW.md` — older 3-app split overview
- `docs/production/PRODUCTION_APP.md` — Product/Adda/Stage model details
- `docs/production/RAW_MATERIALS.md` — cloth + master CRUD
- `docs/production/TRACKING.md` — barcodes + history
- `docs/production/RBAC.md` — role + skill matrix
- `docs/production/MIGRATIONS.md` — migration order
- `docs/production/UI_PATTERNS.md` — form shell, mobile, filter chips
- `docs/production/TESTS_AND_RISKS.md` — coverage + risks
- `docs/production/DECISION_LOG.md` — historical decisions
- `docs/production/CHAT_LOG.md` — chronological design log
