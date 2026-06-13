> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/production/OVERVIEW.md](../../production/OVERVIEW.md) (2026-05-19 brainstorm log).

# Decision Log — Production Tracking Brainstorm

Brainstorm session: 2026-05-19. Owner: Umesh. Facilitator: Claude (brainstorming skill).

| # | Decision | Rationale | Alternatives rejected |
|---|---|---|---|
| 1 | Three-app split: `raw_materials`, `production`, `tracking` | Maximum modularity per user request; allows isolated migration/test/repo split later | one-app `manufacturing` (too coarse); two-app `raw_materials` + `production` (tracking concerns leak into production) |
| 2 | Hybrid workflow: `Product → WorkflowStage` ordered rows + typed stage records (`LayeringRecord`, `CuttingRecord`) | Per-product flexibility + rich typed data per stage; matches user's explicit future plan for per-stage models | flat enum on Adda (no per-product variance); fully dynamic JSONField (loses typing/queryability) |
| 3 | Roll ID = `CR-NNNNNN` zero-padded global sequence | Human-readable, scannable, sortable, fits on labels | date-coded (couples to user-editable date); UUID (unprintable) |
| 4 | Adda code = `{PRODUCT_CODE}-NNN` per-product counter | Self-describing IDs ("Bedsheet 12"); user explicit preference | global ADDA-NNNN (loses product context); date+seq (long, awkward) |
| 5 | `StorageLocation` single flat model, soft-delete via `is_active` + `on_delete=PROTECT` | Covers stated "configurable & extendable" need; minimal schema | two-level Factory+Zone (over-engineering); enum (contradicts configurability) |
| 6 | (REVISED) Whole-roll FK now; weight + width recorded at assignment; services named for future partial-use M2M migration | User clarified weight measured at use-time, ~10–15 rolls/Adda, full consumption; M2M was over-engineered | partial-use M2M now (premature); whole-roll FK with no future seam (lock-in) |
| 7 | New role `ROLE_ACCOUNTANT = 'accountant'`, view + edit Supplier & Cost Per KG; Super Admin universal view preserved | User explicit pick for finance persona; layered defense across form/service/template | role check on ROLE_SUPER_ADMIN only (no accountant persona); named perm `view_cloth_financials` (no edit story) |
| 8 | Per-domain history tables: `ClothRollHistory`, `AddaHistory`, `ProductHistory`, all written via `history_service.log_*` only | User explicit pick; typed columns per domain queryable; assignment events live in ClothRoll fields | generic `AuditLog` with JSON metadata (JSON spelunking); two-layer typed ledger + generic |
| 9 | `BatchBarcode.value = {ADDA_CODE}-{PIECE_SEQ:04d}`; QR-format on sticker, payload = full scan URL | Phone-camera-native scan, no app required; sticker still readable as text fallback | Code 128 (needs scanner app, no native URL); short opaque base32 (no batch hint) |
| 10 | Soft-delete via `is_active` + `on_delete=PROTECT` on all master data (ClothType, ClothColor, StorageLocation, Product) | Preserves historical references; hard delete only when usage_count==0 | PROTECT-only (stale dropdowns forever); CASCADE (data-loss catastrophe) |
| 11 | NFR baseline: ~5k rolls/yr, 50 Addas/mo, 10 users, bulk ≤200 rolls/<5s, daily pg_dump, no SLA, supplier/cost role-gated | User confirmed | — |
| 12 | Bulk roll intake form: ClothType + (color, qty) breakup rows; weight + width entered at use-time (not intake) | User clarified weight comes from weighbridge at consumption | per-roll grid at intake (200 weight inputs); same-weight assumption per breakup row |
| OQ-1 | `Width` lives on `ClothRoll` (per-roll, IntegerField 36..44) | Matches spec; allows mixed widths within one ClothType | width on ClothType (forces duplicate types per width) |
| OQ-2 | Explicit "Advance to next stage" button via `AddaStageService.complete_current_stage` | Allows edits/partial work; manager controls when stage closes | auto-advance on record save (no in-progress state) |
| OQ-3 | Hardcode `[layering, cutting]` workflow in data migration for v1; WorkflowStage CRUD UI deferred | YAGNI — schema supports CRUD, UI ships when 2nd workflow shape is real | ship WorkflowStage CRUD UI now (premature) |
| Extra-a | `LayeringRecord` extended: `lay_count`, `total_colors`, `duration_minutes`, `rolls_used` M2M | User requested; M2M (not JSON snapshot) for queryability + history preservation | JSON snapshot on the record |
| Extra-b | `workers` M2M lifted to `AddaStageRecord` (parent) | Every stage type tracks workers uniformly; future expense.StageWorkAssignment slots in as `through=` | put workers on each typed record (duplicate columns) |
| Extra-c | New `expense` app placeholder for future worker-payment ledger | User future plan; schema seam ready via M2M | model now (out of scope this phase) |

## Post-design decisions (during/after implementation)

| # | Decision | Rationale |
|---|---|---|
| Post-1 | Sidebar active-tab uses longest-substring match in `build_menu_for(user, path)`; template renders `{% if item.is_active %}` | Substring match in template made multiple items light up simultaneously |
| Post-2 | Bulk roll form uses inert `<template>` for new rows | `cloneNode(true)` from live `<select>` preserved `<option selected>` attr → 2nd row showed row 1's color and felt "disabled" |
| Post-3 | `/raw-materials/` is overall raw-material index; `/raw-materials/cloth/` is the cloth-specific dashboard | User asked for placeholder tiles (Elastic, Rib, Sui, Dhaga, Button, Tag) at top level |
| Post-4 | Bulk roll intake gated to `ROLE_SUPER_ADMIN` only | User said "for only one role" |
| Post-5 | Added `updated_at` to `tracking.TimeStampedModel` (migration 0003) | User wanted timestamps on every model uniformly |
| Post-6 | Date-range filter on cloth/Adda/barcode/roll-list via `?from=&to=` | User explicit ask |
| Post-7 | Roll list shows latest 50 cloth-roll movements at bottom | User explicit ask for "time logs" panel |
| Post-8 | Active-filter chips strip on roll list with per-chip remove URLs | User explicit ask — "show filter info if any filter applied" |
| Post-9 | Color filter (4th dropdown) on roll list | User explicit ask |
| Post-10 | QR print sheet uses ECC level Q (25% damage tolerance) + 3 density modes | Industrial shop-floor standard |
| Post-11 | All templates rebuilt to global classes (`.kpis`/`.tbl`/`.card`/`.btn-*`) + mobile `data-label` + form shell | User: "new html pages are not mobile friendly, check my frontend feedback md" |
| Post-12 | Hinglish docstrings + inline why-comments across all new `.py` + `.html` files | User: "you dont follow the comment rule" — matches existing project style |
| Post-13 | Time-log panels converted to collapsible `<details>/<summary>` accordion + applied to 5 dashboards | User: "add time logs section same as in cloth dashboard, accordian collapse/expand, where needed" |

## Open items (deferred, not blocking)

- Workflow CRUD UI (deferred to phase 2 once 2nd product needs different stages).
- Barcode scan flow beyond opening detail page (status updates via scan, status workflow rules).
- `expense` app modelling (worker hours, rates, payouts).
- Cost reports + financial dashboards for ROLE_ACCOUNTANT.
- Multi-factory permission scoping (currently single-factory).

## Memory anchors

- `feedback_ui_polish` — every create/edit page uses form-shell (hero + numbered panels + sticky CTA).
- `project_form_shell` — exact CSS contract for the shell.
- `project_rbac_state` — `Role` FK is single source of truth; sidebar gated by `build_menu_for`.
- CLAUDE.md rule #4 — service layer owns all multi-row writes; no signals.
- CLAUDE.md rule #5 — single-writer ledger discipline (re-applied as `history_service.log_*` for new app).
- CLAUDE.md rule #6 — permission_service primitives, no raw `is_superuser`.
