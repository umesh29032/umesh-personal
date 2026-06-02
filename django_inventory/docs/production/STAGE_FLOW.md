# Production App — Stage Flow & Model Connections

> Focused reference: **what each stage creates** + **how every model wires into the end-to-end flow**.
> Verified against live code at commit `4fd746d2` (2026-06-01). 196/196 tests green.
> Companion to [OVERVIEW.md](OVERVIEW.md). For whole-project scope see `/SYSTEM_DESIGN.md`.

The `production` app is a **4-stage factory pipeline**. It rests on one polymorphic spine
(`Adda` → `AddaStageRecord`); each stage hangs a typed `OneToOne` record off that spine and
writes its own child rows. Every write goes through the service layer (CLAUDE rule #4) —
views never write multi-row state directly, and there are no signals.

```
Stage flow (per product workflow; stages 2 & 4 optional):

  ┌──────────┐   ┌─────────────────┐   ┌─────────┐   ┌────────────────────┐
  │ LAYERING │ → │ CUTTING PATTERN │ → │ CUTTING │ → │ BARCODE GENERATION │ → export
  └──────────┘   └─────────────────┘   └─────────┘   └────────────────────┘
   stage 1          stage 2 (opt)        stage 3        stage 4 (opt)
```

`Adda.current_stage` advances **explicitly** via a service call (`complete_layering`,
`complete_pattern_stage`, `complete_cutting`, `complete_barcode_generation`) → never on `save()`.
When the last `WorkflowStage` completes, `current_stage` = NULL and `Adda.status` = `COMPLETED`.

---

## 0. Backbone — created at Adda START (before any stage)

Service: `adda_service.create_adda` → `config/production/services/adda_service.py:96`

| Model | Count | Note |
|---|---|---|
| `Adda` | ×1 | the batch. Code `T-SHIRT-001`. `current_stage` → first `WorkflowStage`. Race-safe counter (`SELECT FOR UPDATE` on `Product`). |
| `AddaStageRecord` | ×1 | auto-created **only if** first stage = layering; other first-stages create it at their own `start_*`. |
| `tracking.AddaHistory` | ×1 | audit row `CREATED` (written via `history_service`). |

**`AddaStageRecord` is the polymorphic parent.** One row per `(adda, workflow_stage)`
(`unique_together`). The `workers` M2M lives here — common shape across all stages, future
`expense.StageWorkAssignment` through-model converts it. Every typed stage record below is a
`OneToOne` back to this parent.

---

## Stage 1 — LAYERING

Service: `config/production/services/layering_service.py`

| Model | Created when | Count |
|---|---|---|
| `AddaStageRecord` | `start_layering` (or reused from `create_adda`) | ×1 |
| `LayeringRollEntry` | `attach_roll_to_layering` — each roll attached | ×N rolls |
| `RemainingClothOfClothRoll` | `save_layering_breakup` — leftover cloth per roll | ×N rolls |
| `LayeringRecord` | `complete_layering` | ×1 (`OneToOne`) |

- `LayeringRollEntry` → FK `raw_materials.ClothRoll` (PROTECT). Per-roll width/weight verify + `layers_on_roll`.
- `LayeringRecord` freezes the `rolls_used` M2M snapshot → `ClothRoll`. This is the **raw-cloth → production** join.
- `RemainingClothOfClothRoll` = leftover tracker; future Addas may consume it (`is_consumed`).
- **Reopen** (`reopen_layering`): copies header into `sr.draft_*`, deletes `LayeringRecord`, resets stage. Refuses if any downstream stage already `started_at`.

---

## Stage 2 — CUTTING PATTERN  *(optional per product)*

Service: `config/production/services/cutting_pattern_service.py`

| Model | Created when | Count |
|---|---|---|
| `AddaStageRecord` | `start_pattern_stage` | ×1 |
| `CuttingPatternRecord` | first `save_pattern_record` / `attach_photo` | ×1 (`OneToOne`) |
| `CuttingPatternPhoto` | `attach_photo` — each photo (Pillow-compressed JPEG q=80, ≤2400px) | ×N |
| `CuttingPatternVerification` | per pattern physically verified | ×N = `ProductPatternAssignment` count |
| `CuttingPatternSizeAllocation` | per size, `proportion_pct` (must sum 100) | ×N = `ProductSize` count |

- `CuttingPatternRecord` holds optional `video` + `notes`.
- `CuttingPatternVerification` → FK `ProductPatternAssignment` (proves each required pattern shape).
- `CuttingPatternSizeAllocation` → FK `ProductSize` (this batch's size mix).
- **Complete gate** (`complete_pattern_stage`): `verifications.count == product.pattern_assignments.count` AND size proportions sum 100 AND video-OR-photo present.

---

## Stage 3 — CUTTING

Service: `config/production/services/cutting_service.py`

| Model | Created when | Count |
|---|---|---|
| `AddaStageRecord` | `start_cutting` | ×1 |
| `CuttingRecord` | `complete_cutting` | ×1 (`OneToOne`) |
| `CuttingPieceBreakup` | verified plan entry | ×N per (size, color, pattern) |
| `CuttingBundle` | bundle build | ×N — **one per size** |
| `CuttingBundleItem` | line item inside bundle | ×N per (pattern, color) |
| `AddaProductSizeColorPieceBreakdown` | **`complete_cutting` → `_materialize_breakdown`** | ×N per (size, color) |

- `CuttingPieceBreakup` = informational verified plan; tracks `consumed_count` / `available_count`.
- `CuttingBundle` (per size) → holds `CuttingBundleItem` rows (pattern × color × count). `total_pieces` denormalized.
- `_materialize_breakdown` (`cutting_service.py:143`): aggregates `SUM(CuttingBundleItem.count) GROUP BY (size, color)` → freezes `AddaProductSizeColorPieceBreakdown`.
- **This frozen breakdown is the handoff boundary.** Barcode generation + future Stitching/Packing consume it; they never recompute upstream cutting data.
- **Reopen** (`reopen_cutting`): deletes `AddaProductSizeColorPieceBreakdown` rows (re-materialized on next complete).

---

## Stage 4 — BARCODE GENERATION  *(optional per product)*

Services: `config/production/services/barcode_generation_service.py` + `config/tracking/services/barcode_service.py`

| Model | Created when | Count |
|---|---|---|
| `AddaStageRecord` | `start_barcode_generation` | ×1 |
| `BarcodeGenerationRecord` | first record touch | ×1 (`OneToOne`) |
| `tracking.BarcodeBatch` | `generate_barcodes` → `generate_from_breakdown` (bulk) | ×N per (size, color) range |
| `tracking.BatchBarcode` | **LAZY — on first QR scan** (`get_or_create_piece`) | 0 at gen; 1 per scanned piece |

- `generate_from_breakdown` reads `AddaProductSizeColorPieceBreakdown` → `BarcodeBatch` range headers (contiguous seq allocation).
- Per-piece `BatchBarcode` rows are **not** created upfront — born lazily on scan to save rows at ~5k pieces/yr scale.
- `BarcodeGenerationRecord.total_barcodes` = denorm `SUM(BarcodeBatch.total_pieces)`. Generation one-shot/idempotent.
- **Reopen** (`reopen_barcode_generation`): cleared only if no scans + no exports exist.

### Post-stage — Export (tracking app)

Service: `config/tracking/services/barcode_export_service.py`

| Model | Created when | Count |
|---|---|---|
| `tracking.BarcodeExportBatch` | `generate_csv` / `generate_xlsx` / `generate_pdf_summary` | ×1 per export |
| `production.LabelPrintQueue` | **STUB — no service logic yet** | — |

---

## Full FK spine (how every model connects)

```
Product ──<WorkflowStage>── Stage              admin config: per-product flow + per-stage RBAC
  │                                             (Stage.access_by_role / access_by_skill M2M)
  └──< Adda (current_stage → WorkflowStage)
        └──< AddaStageRecord  ◄══ POLYMORPHIC PARENT  (workers M2M lives here)
              │   one row per (adda, workflow_stage)
              │
              ├─1:1 LayeringRecord ──M2M→ raw_materials.ClothRoll
              │       ╞ LayeringRollEntry ──FK→ ClothRoll
              │       ╘ RemainingClothOfClothRoll ──FK→ ClothRoll
              │
              ├─1:1 CuttingPatternRecord
              │       ╞ CuttingPatternPhoto
              │       ╞ CuttingPatternVerification ──FK→ ProductPatternAssignment
              │       ╘ CuttingPatternSizeAllocation ──FK→ ProductSize
              │
              ├─1:1 CuttingRecord
              │       ╞ CuttingPieceBreakup (size · color · pattern)
              │       ╞ CuttingBundle (per size) ──< CuttingBundleItem (pattern · color)
              │       ╘ AddaProductSizeColorPieceBreakdown  ◄══ FROZEN HANDOFF (size · color)
              │
              └─1:1 BarcodeGenerationRecord
                      ╘ tracking.BarcodeBatch ──< tracking.BatchBarcode (lazy on scan)
                                                      ╘ tracking.BarcodeExportBatch
                                                            ╘ production.LabelPrintQueue (stub)

Audit (parallel, every mutation):  tracking.AddaHistory / ClothRollHistory / ProductHistory
                                    written exclusively via tracking.services.history_service
```

---

## Lifecycle trace — one T-SHIRT Adda (start → export)

Assume T-SHIRT flow = `[layering, cutting_pattern, cutting, barcode_generation]`,
3 patterns (Front×1, Back×1, Sleeve×2), 4 sizes (S/M/L/XL), 2 colors (Red, Blue), 5 rolls used.

| Step | Service call | Rows created |
|---|---|---|
| 1. Start Adda | `create_adda` | `Adda` ×1, `AddaStageRecord`(layering) ×1, `AddaHistory` ×1 |
| 2. Attach 5 rolls | `attach_roll_to_layering` ×5 | `LayeringRollEntry` ×5 |
| 3. Breakup + leftover | `save_layering_breakup` | `RemainingClothOfClothRoll` ×5 |
| 4. Complete layering | `complete_layering` | `LayeringRecord` ×1 (+ `rolls_used` M2M ×5), advance |
| 5. Start pattern | `start_pattern_stage` | `AddaStageRecord`(pattern) ×1 |
| 6. Save + photos | `save_pattern_record`, `attach_photo` | `CuttingPatternRecord` ×1, `CuttingPatternPhoto` ×k |
| 7. Verify + sizes | (verify) | `CuttingPatternVerification` ×3, `CuttingPatternSizeAllocation` ×4 |
| 8. Complete pattern | `complete_pattern_stage` | advance |
| 9. Start cutting | `start_cutting` | `AddaStageRecord`(cutting) ×1 |
| 10. Bundles | `add_bundle_item` etc. | `CuttingBundle` ×4 (per size), `CuttingBundleItem` ×(pattern·color), `CuttingPieceBreakup` ×N |
| 11. Complete cutting | `complete_cutting` → `_materialize_breakdown` | `CuttingRecord` ×1, `AddaProductSizeColorPieceBreakdown` ×8 (4 sizes × 2 colors), advance |
| 12. Start barcode | `start_barcode_generation` | `AddaStageRecord`(barcode) ×1, `BarcodeGenerationRecord` ×1 |
| 13. Generate | `generate_barcodes` → `generate_from_breakdown` | `tracking.BarcodeBatch` ×8 (one per breakdown row); `BatchBarcode` = 0 |
| 14. Complete barcode | `complete_barcode_generation` | advance → `current_stage` NULL, status `COMPLETED` |
| 15. Export CSV | `barcode_export_service.generate_csv` | `tracking.BarcodeExportBatch` ×1 |
| 16. Scan a QR | `barcode_service.get_or_create_piece` | `tracking.BatchBarcode` ×1 (lazy, on demand) |

---

## Design rules that hold it together

1. **Polymorphic spine.** `AddaStageRecord` is the shared parent; each stage = one typed `OneToOne` child. Adding a new stage = new typed record model + new `Stage` row; the spine never changes.
2. **Explicit advance.** `complete_*` services call `advance_to_next_stage`. Never auto on `save()`. No signals.
3. **Frozen handoff between stages.** Each stage feeds the next via a materialized snapshot (rolls → size proportions → bundles → `AddaProductSizeColorPieceBreakdown` → barcode batches). Downstream reads frozen data; never recomputes upstream.
4. **Service layer owns all multi-row writes** (CLAUDE rule #4). Views call services.
5. **Cross-app FK downstream only:** `raw_materials` ← `production` ← `tracking`. `raw_materials` imports nothing upstream.
6. **Lazy per-piece barcodes.** `BatchBarcode` rows are created on scan, not at generation — keeps row counts low.

---

## Config / master models (NOT created per-stage)

Admin- or seed-managed, referenced by the flow but not produced by it:
`Product`, `Stage`, `WorkflowStage`, `ProductPattern`, `ProductPatternAssignment`, `ProductSize`.
