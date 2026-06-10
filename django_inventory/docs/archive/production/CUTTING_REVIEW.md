# Cutting Workflow — Master Prompt Coverage Report

**Status:** Comprehensive review against the user-provided master prompt.
**Last touched:** 2026-05-29
**Companion docs:** [CUTTING_DESIGN.md](CUTTING_DESIGN.md), [LAYERING_STAGE.md](LAYERING_STAGE.md), [TRACKING.md](TRACKING.md), [OVERVIEW.md](OVERVIEW.md)

This doc maps every section of the master prompt to the current implementation. Each row marks ✅ done, ⚠️ partial, or ✘ missing. Gaps fixed in PR13 noted inline.

---

## 1. Overall Manufacturing Workflow

```
Raw Cloth
    ↓
Layering Stage              ✅ (layering_service.py)
    ↓
Cutting Pattern Stage       ✅ (cutting_pattern_service.py + PR2 validations)
    ↓
Cutting Stage               ✅ (cutting_service.py — workspace + draft + complete)
    ↓
Bundle Generation           ✅ (CuttingBundle + CuttingBundleItem; PR8-PR12)
    ↓
Barcode Generation          ✅ (BarcodeBatch ranges + lazy BatchBarcode; PR6 + PR11 bundle FK)
    ↓
Future Manufacturing Stages — foundation ready (BarcodeBatch.bundle FK + BatchBarcode FKs)
```

Workflow advances via `production.services.adda_service.advance_to_next_stage`. Each stage stamps `AddaStageRecord.completed_at` + `completed_by`; the Adda's `current_stage` FK points to the next `WorkflowStage`.

---

## 2. Architecture Rules

| Rule | Status | Where |
|---|---|---|
| Service-layer only | ✅ | All writes go through `production.services.*` and `tracking.services.*`. Views never call `.objects.create` for stage-typed rows. |
| No business logic in views | ✅ | Views parse POST, call service, redirect. See [stage_views.py](../../config/production/views/stage_views.py). |
| `@transaction.atomic` on multi-row writes | ✅ | Every service write (`add_pieces_to_bundle`, `create_bundle_with_pieces`, `complete_cutting`, `reopen_cutting`, etc.) wraps in `@transaction.atomic`. |
| Reuse Adda workflow flow | ✅ | `advance_to_next_stage(adda, user)` shared by all stage-complete services. |
| Reuse history/audit services | ✅ | `tracking.services.log_adda` called on STAGE_REOPENED + via `advance_to_next_stage`. |
| Reuse RBAC/access services | ✅ | `_ensure_cutting_skill`, `_ensure_can_complete_cutting` use `user_has_skill` + `user_has_role` from `inventory.services`. |
| Reuse stage progression | ✅ | `advance_to_next_stage` shared. |
| Reuse iframe stage structure | ✅ | StagePanelView routes `stage_type=cutting` → `_build_cutting_context`. Embedded mode honored throughout templates. |
| Reuse ProductPattern architecture | ✅ | `ProductPatternAssignment` validation in `add_bundle_item` + `add_pieces_to_bundle`. |
| No duplicate logic | ✅ | `add_bundle_item`/`add_item_to_bundle`/`add_pieces_to_bundle`/`create_bundle_with_pieces` form a layered API; each builds on the last. |
| No bypass of history logging | ✅ | Reopen calls `log_adda`; advance calls history via adda_service. |
| No bypass of Adda lifecycle | ✅ | All completes go through advance_to_next_stage; all reopens go through service. |

---

## 3. Code Quality

| Requirement | Status |
|---|---|
| Hinglish comments on important logic | ✅ Throughout cutting_service.py, models.py, templates |
| Beginner-friendly explanations | ✅ Service docstrings explain "why" + Django primitive on first touch |
| Imports commented | ✅ See top of [cutting_service.py](../../config/production/services/cutting_service.py) |
| Models commented | ✅ Each new model has docstring + field-level comments |
| Validation commented | ✅ Complete-stage validation chain documented inline |

---

## 4. UI/UX Requirements (Cutting Stage screen)

| Screen requirement | Section | Status |
|---|---|---|
| Suggested Piece Breakup | Section 02 | ✅ — `CuttingPieceBreakup` with inventory columns (Count / Consumed / Available) |
| Verified Piece Summary | Section 02 (combined) | ✅ — Cutting master edits + saves count; available_count is the verification result |
| Bundle Creation Section | Section 03 top form (PR12) | ✅ — Size + Bundle Number + Multi-select Pattern × Color picker |
| Bundle Summary | Section 03 bundle cards (PR12) | ✅ — Pattern chips header + Pattern × Color × Count table + Color totals pills |
| Barcode Generation Summary | Section 05 (PR13) | ✅ — Pre-completion preview shows bundle/color/start/end ranges before user clicks Complete |
| Draft / Completion Actions | Section 04 + 05 | ✅ — Save Draft + Mark Complete |
| Sticky CTAs | ✅ Bundle card + complete button | ✅ |
| Mobile responsive | ✅ All tables use `data-label` pattern | ✅ |
| Color-coded validation | ✅ Available count green/stone; Consumed locked indicator | ✅ |
| Workflow indicators | ✅ Panel-state pills (Started / Not Started / Completed) | ✅ |

---

## 5. Existing Stage Logic — reused

| Stage | Models Reused | Services Reused |
|---|---|---|
| Layering | `LayeringRecord` (lay_count + rolls_used) | `layering_service.complete_layering` |
| Cutting Pattern | `CuttingPatternRecord` + `CuttingPatternVerification` + `CuttingPatternSizeAllocation` | `cutting_pattern_service.complete_pattern_stage` |
| ProductPattern | `ProductPattern` + `ProductPatternAssignment` | Validation in `add_bundle_item` |
| Tracking | `BarcodeBatch` + `BatchBarcode` + `AddaHistory` | `tracking.services.generate_for_cutting` + `log_adda` |

---

## 6. Product Size System

- `ProductSize` model (per-Product) — code + label + display_order + is_active
- Numeric (1, 2, 3, 4) or apparel (S, M, L, XL) — admin choice per product
- Editor at `/production/products/<pk>/sizes/`
- Used by: pattern stage allocations, cutting workspace size picker, bundle headers, barcode batch keys
- ✅ Fully wired

---

## 7. Cutting Stage — Core (lifecycle)

| Service | Purpose |
|---|---|
| `start_cutting(adda, worker_ids, user)` | Manager assigns workers |
| `upsert_breakup_row(adda, ..., user)` | Section 02 inventory entry; idempotent per (size, color, pattern); count=0 deletes |
| `delete_breakup_row(adda, row_id, user)` | Remove row (locked if consumed) |
| `create_bundle(adda, size_id, bundle_number, user)` | Bundle header only |
| `create_bundle_with_pieces(adda, size_id, bundle_number, selections, user)` | **PR12** Atomic: header + initial items |
| `add_pieces_to_bundle(adda, bundle_id, selections, user)` | **PR10** Multi-select consume from inventory |
| `add_item_to_bundle(adda, bundle_id, pattern_id, color_id, count, user)` | Single freeform item (back-compat) |
| `delete_bundle_item(adda, item_id, user)` | Restores consumed_count on source breakup |
| `delete_bundle(adda, bundle_id, user)` | Restores consumed_count on all source breakups |
| `save_cutting_draft(adda, notes, user)` | Notes only; no advance |
| `complete_cutting(adda, user)` | Workspace path — strict validation + barcode gen + advance |
| `complete_cutting(adda, user, pieces_cut=N, worker_ids=..., notes=...)` | Legacy single-shot path (NIKKAR-style, no bundles) |
| `reopen_cutting(adda, user)` | Admin unlock; refused if scanned barcode exists |
| `get_cutting_snapshot(adda)` | Read snapshot — state, breakup, bundles, totals |
| `get_suggested_breakup(adda)` | Formula-based pre-fill: `lay_count × pieces × pct / 100` |
| `preview_barcode_batches(adda)` | **PR13** Pre-completion barcode batch preview |

---

## 8. Suggested Piece Breakup (Section 02)

- Read from layering + pattern stage data via `get_suggested_breakup`
- Displayed in Section 02 with columns: Pattern · Size · Color · **Count** · **Consumed** · **Available** · Action
- Cutting master edits Count (verifies physically); save persists to `CuttingPieceBreakup.count`
- Inventory rules locked: Available = Count − Consumed (formula §9)

---

## 9. Inventory Consumption Logic

| Rule | Implementation |
|---|---|
| Every row tracks total/consumed/available | `CuttingPieceBreakup.count`, `consumed_count`, `available_count` property |
| Available = Total − Consumed | `available_count` property on model |
| Pieces consumed via bundle | `add_pieces_to_bundle` increments `consumed_count` |
| Cannot reuse | `take_count <= available_count` check in service (raises if over-take) |
| Cannot delete consumed row | UI locks Remove button when `consumed_count > 0` |
| Restore on bundle/item delete | `_recompute_breakup_consumed(source)` called from `delete_bundle_item` + `delete_bundle` |
| Over-take rejection atomic | `@transaction.atomic` + `select_for_update` on breakup row |

---

## 10. Correct Bundle Logic

| Spec | Implementation |
|---|---|
| Bundle = combination of multiple pattern pieces | `CuttingBundleItem` rows inside `CuttingBundle` |
| Bundle belongs to one size | `CuttingBundle.size` FK + `unique_together(cutting_record, size)` |
| Inside bundle: multiple patterns + colors | Items collection — each row = (pattern, color, count) |
| Bundle creation = combine pattern pieces | `create_bundle_with_pieces` atomically takes Pattern×Color×Take selections |
| Pieces consumed at bundle creation | `consumed_count` incremented per source breakup row |
| Physical tied manufacturing group | Bundle = one rope-tied group (logically) |

---

## 11. Bundle as Manufacturing Unit

- Primary tracking unit for future stages
- `BarcodeBatch.bundle` FK (PR11) links each barcode range to its source bundle
- Future stages can query `bundle.barcode_batches.all()` directly
- Item.source_breakup preserves audit trail back to inventory row

---

## 12. Bundle Creation Workflow

```
Step 1: User selects available pieces from Section 02 inventory
        (multi-select picker in top "Create Bundle" form)
Step 2: User chooses bundle size (size dropdown)
Step 3: User enters bundle_number label (optional)
Step 4: System combines pattern pieces into bundle items
        (CuttingBundleItem rows with source_breakup FK)
Step 5: Inventory consumed automatically
        (CuttingPieceBreakup.consumed_count incremented)
Step 6: Bundle saved + total_pieces denormalized
```

Multiple bundles per size NOT allowed (`unique_together(cutting_record, size)`).
Multiple colors per bundle: ✅ (items can have different colors).
Multiple patterns per bundle: ✅ (items can have different patterns).

---

## 13-14. Size-Based Bundle Mapping + Color Distribution

- Bundle = per-size header
- Items inside hold (pattern, color, count)
- Color summary in UI: `color_summary` list on bundle (computed in snapshot)
- Barcode generation aggregates by (bundle, size, color) → one BarcodeBatch per group

---

## 15. Final User Verification

- Suggested counts populated from `get_suggested_breakup` formula
- Cutting master edits Count column in Section 02 (final verification)
- `complete_cutting` requires at least one bundle with items (bundles = manual user output)
- Bundle creation requires user multi-select (no auto-create from suggestion)
- Final verified counts = `cutting_record.pieces_cut = SUM(bundle.items.count)`

---

## 16. Barcode Generation System

| Rule | Implementation |
|---|---|
| Generation starts after bundle + verification + stage completion | `generate_for_cutting(cr)` called inside `_complete_cutting_from_breakup` after validation passes |
| One barcode = one physical piece | `BarcodeBatch.total_pieces` = sum of items; `BatchBarcode` lazy per scan |
| Barcode quantity = final verified piece count | `BarcodeBatch.total_pieces` sum across batches = `cutting_record.pieces_cut` |

---

## 17. Barcode Metadata Requirements

| Field | Storage |
|---|---|
| Adda | `BarcodeBatch.adda` FK ✅ |
| Product | `BarcodeBatch.product` FK ✅ (denorm) |
| Bundle | `BarcodeBatch.bundle` FK ✅ (PR11) |
| Size | `BarcodeBatch.size` FK ✅ |
| Color | `BarcodeBatch.color` FK ✅ |
| Pattern Group | Indirect via `bundle.items` — patterns collapsed at batch level (per spec §11) but recoverable |
| Piece Sequence | `BarcodeBatch.start_seq` + `end_seq`; per-piece `BatchBarcode.piece_seq` |

Note: barcodes aggregate **pattern across bundle** (per user's PR11 spec — "barcode batch identity = bundle + color"). Pattern info lives one hop away on `BarcodeBatch.bundle.items.filter(color=...)`.

---

## 18. Barcode Allocation Logic

```
Bundle Size M (total 75)
  ├ Red:   25 pieces  → BarcodeBatch range  1..25
  ├ Blue:  25 pieces  → BarcodeBatch range 26..50
  └ Green: 25 pieces  → BarcodeBatch range 51..75
```

- Each color → one `BarcodeBatch` row with start_seq / end_seq / total_pieces
- Sequential `seq` per Adda across all bundles
- Sort order: (size.display_order, size.code, color.name) for determinism
- Per-piece `BatchBarcode` lazy-created on scan with size + color + pattern + bundle FKs populated

---

## 19. Save Draft

- `save_cutting_draft(adda, notes, user)` — notes only; no validation, no advance, no barcode gen
- Bundle adds + breakup edits are themselves drafts (persisted but no advance)
- UI: explicit "Save Draft" button in Section 04 (Notes)
- ✅

---

## 20. Architecture Models — final shape

```
CuttingRecord (typed stage record)
    └── CuttingPieceBreakup (Section 02 inventory; per pattern×size×color)
    │     • count, consumed_count
    │     • available_count = count - consumed_count
    │
    └── CuttingBundle (per size header)
          • total_pieces (denormalized SUM of items.count)
          • bundle_number (optional label)
          │
          └── CuttingBundleItem (pattern × color × count)
                • source_breakup FK → CuttingPieceBreakup (for restore-on-delete)

BarcodeBatch (per bundle × color)
    • adda, product, bundle, size, color FKs
    • start_seq, end_seq, total_pieces
    • value format: {ADDA}-{seq:04d}
        │
        └── BatchBarcode (lazy per-piece scan state)
              • status, last_scanned_at, last_scanned_by
              • size, color, pattern, roll FKs
```

No unnecessary complexity. CuttingPieceInventory + BundleColorDistribution requirements satisfied by existing models + computed properties (no extra tables).

---

## 21. Review Report

This document IS the review report. Sections:
- Existing functionality: §1-§9 (all green)
- Missing functionality: §17 (Pattern field on barcode is one-hop indirect — accepted per spec)
- Reusable services/models: §5
- RBAC integration: §2
- Risks: see [TESTS_AND_RISKS.md](TESTS_AND_RISKS.md)

---

## 22. Documentation Touched (PR13)

- This file (`CUTTING_REVIEW.md`) — coverage report
- [CUTTING_DESIGN.md](CUTTING_DESIGN.md) — schema + service contracts
- [TRACKING.md](TRACKING.md) — barcode batch storage
- [OVERVIEW.md](OVERVIEW.md) — production app overview
- [production/README.md](../../config/production/README.md) — production app walkthrough

---

## 23. Final Deliverables — checklist

- ✅ Review report (this doc)
- ✅ Gap analysis (mapped per section)
- ✅ Architecture plan (§20)
- ✅ UI improvement (PR12 + PR13)
- ✅ Database/model updates (PR6 → PR12)
- ✅ Service-layer implementation (cutting_service.py + barcode_service.py)
- ✅ Validation implementation (over-take, missing-bundle, size-not-allowed)
- ✅ Bundle workflow (Sections 02-03)
- ✅ Barcode generation (`generate_for_cutting` iterates bundle items, aggregates by size+color)
- ✅ Draft system (`save_cutting_draft`)
- ✅ Responsive UI (data-label tables, mobile chip pickers)
- ✅ Documentation (this + companion docs)
- ✅ Beginner Hinglish comments
- ✅ Test suggestions (in [TESTS_AND_RISKS.md](TESTS_AND_RISKS.md))
- ✅ Edge-case handling (over-take rollback, atomic restore on delete, reopen scan-guard)

---

## PR timeline

| PR | Scope | Files |
|---|---|---|
| PR1-PR5 | Initial cutting pattern validation + cutting workspace skeleton + ProductSize | ~15 |
| PR6 | BarcodeBatch range storage + lazy BatchBarcode | ~10 |
| PR7 | CuttingBundle (PR7 schema — flat row per pattern+size+color) | ~9 |
| PR8 | Bundle restructure: per-size header + CuttingBundleItem | ~10 |
| PR9 | Two-step create_bundle + add_item_to_bundle | ~6 |
| PR10 | Inventory consumption: consumed_count + add_pieces_to_bundle multi-select + restore-on-delete | ~10 |
| PR11 | Bundle display by color + BarcodeBatch.bundle FK | ~6 |
| PR12 | Atomic create_bundle_with_pieces + restore pattern visibility | ~5 |
| PR13 | Barcode preview + docs + review report | ~4 |

**Tests**: 127 passing (started baseline 74; net +53 across PR1-PR12).

---

## Open future work (out of scope)

- Machine tracking — `BarcodeBatch.bundle` FK enables this
- Worker scanning — per-piece `BatchBarcode.last_scanned_by` exists
- Movement tracking — needs new `PieceMovement` model
- Real-time dashboards — needs telemetry layer
- Stitching/Finishing/Packing stages — new Stage rows + per-stage services

Foundation in place. Future stages plug into `BarcodeBatch.bundle` for lookup.
