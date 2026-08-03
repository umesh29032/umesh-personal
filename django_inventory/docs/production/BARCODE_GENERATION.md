---
id: production-barcode-generation
type: topic-canonical
status: active
owner: handwritten
scope: production subsystem
anchors: —
verified: 2026-07-13
---

# Barcode Generation Stage

Stage 4 of production flow (optional per-product).
Shipped: PR-A → PR-E, 2026-05-29.

---

## Why a Separate Stage

Pre 2026-05-29: cutting completion inline-generated barcodes. That coupled
two unrelated responsibilities into one step:

1. **Verify cutting output** (manufacturing truth)
2. **Generate barcode sequences** (label printing prep)

Extracted because:

- Some products skip barcode generation entirely (NIKKAR-style simple flows)
- Cutting can complete + freeze breakdown; barcode stage runs later when vendor is ready
- Reopen semantics differ — cutting reopen ≠ barcode reopen
- Future label-tracking stages depend on bg completion, not cutting completion
- Audit trail benefits from explicit stage boundary

---

## Flow

```
Cutting complete
    │  materializes AddaProductSizeColorPieceBreakdown rows
    │  (size × color × verified_piece_count)
    ▼
Adda advances to barcode_generation (if in product workflow)
    │
    ├── start_barcode_generation       mgmt assigns workers
    │       └─→ creates AddaStageRecord + BarcodeGenerationRecord
    │
    ├── generate_barcodes              cutting_master / helper triggers
    │       └─→ reads breakdown rows
    │       └─→ bulk_creates BarcodeBatch rows (one per size×color combo)
    │       └─→ sets BarcodeGenerationRecord.generated_at + total_barcodes
    │
    └── complete_barcode_generation    helper / super_admin
            └─→ validates SUM(BarcodeBatch.total_pieces) == breakdown total
            └─→ stamps sr.completed_at + completed_by
            └─→ advance_to_next_stage (or COMPLETED if last)
```

Per-product workflow: if `barcode_generation` is NOT in product's
`WorkflowStage` list, cutting completion inline-generates barcodes (legacy
back-compat). Admin opts in via per-product flow editor.

---

## Model Layer

| Model | Purpose |
|-------|---------|
| `AddaProductSizeColorPieceBreakdown` | Frozen per-(size, color) verified pieces. Source of truth for downstream stages. |
| `BarcodeGenerationRecord` | OneToOne `AddaStageRecord` — typed record for this stage. Denorm `total_barcodes` + `generated_at`. |
| `tracking.BarcodeBatch` | Range header — one row per (size, color) combo. Sequence range `start_seq..end_seq`. |
| `tracking.BatchBarcode` | Lazy per-piece scan state — only created on first scan. |

ER diagram:

```
CuttingRecord
    │
    │ 1:N (CASCADE on cutting reopen)
    ▼
AddaProductSizeColorPieceBreakdown ─── (size, color, verified_piece_count)
                                          │
                                          │ frozen at cutting complete
                                          ▼
BarcodeGenerationRecord (OneToOne AddaStageRecord)
    │
    │ produces (one-shot per stage)
    ▼
BarcodeBatch (range header)
    │
    │ 1:N lazy on scan
    ▼
BatchBarcode (per-piece scan state)
```

---

## Validation Rules

### `generate_barcodes`

- Adda must be at `barcode_generation` stage
- Stage record must exist (start_barcode_generation called)
- Stage not yet completed
- `BarcodeGenerationRecord.generated_at` must be NULL (one-shot)
- `BarcodeBatch` rows must not already exist for this Adda (DB-level guard)
- Permission: cutting_master OR cutting_master_helper skill (mgmt bypass)

### `complete_barcode_generation`

- Stage record + BarcodeGenerationRecord exist
- `generated_at` is set (generate ran successfully)
- `SUM(BarcodeBatch.total_pieces) == SUM(breakdown.verified_piece_count)`
- `SUM(BarcodeBatch.total_pieces) == BarcodeGenerationRecord.total_barcodes` (denorm consistency)
- Permission: cutting_master_helper OR super_admin

### `reopen_barcode_generation`

Refused if:
- Any `BatchBarcode` row exists (lazy-create on scan → scan happened)
- Any `BarcodeExportBatch` row exists for this Adda (vendor already has exported labels)

On reopen:
- `sr.completed_at` + `completed_by` cleared
- Adda `current_stage` → bg wf, `status` → IN_PROGRESS
- All `BarcodeBatch` rows deleted (one-shot rule)
- `BarcodeGenerationRecord.generated_at` + `total_barcodes` reset to NULL / 0
- `AddaHistory.STAGE_REOPENED` audit log

Permission: MANAGEMENT_ROLES.

---

## Barcode Value Format

`{ADDA_CODE}-{PIECE_SEQ:04d}` — e.g. `T-SHIRT-001-0042`.

Sequence is contiguous across all batches in an Adda. Allocation key:
`(size.display_order, size.code, color.name)`. Deterministic — reruns
produce identical ranges (verified by golden-path test).

---

## URL Surface

```
GET   /production/addas/<code>/barcode-gen/             workspace (full page)
POST  /production/addas/<code>/barcode-gen/start/       assign workers
POST  /production/addas/<code>/barcode-gen/generate/    one-shot generate
POST  /production/addas/<code>/barcode-gen/complete/    validate + advance
POST  /production/addas/<code>/barcode-gen/reopen/      mgmt unlock
```

Embedded panel: `/production/addas/<code>/stage/barcode_generation/?embedded=1`
(iframe-safe; auto-resize via postMessage).

---

## Where Code Lives

| File | Role |
|------|------|
| `config/production/services/barcode_generation_service.py` | Service layer — all mutating writes |
| `config/production/views/barcode_gen_views.py` | Views + start form |
| `config/production/templates/production/barcode_gen_workspace.html` | Standalone workspace |
| `config/production/templates/production/_stage_panel_barcode_gen.html` | Embedded panel (5 sections + export) |
| `config/tracking/services/barcode_service.py` | `generate_from_breakdown` — new canonical generator |
| `config/production/migrations/0020-0023` | Schema + seed + backfill |
| `config/tracking/migrations/0009` | BarcodeExportBatch model |

---

## Tests

- `production/tests/test_barcode_stage_models.py` — 18 model + seed tests
- `production/tests/test_cutting_breakdown_materialization.py` — 12 cutting refactor tests
- `production/tests/test_barcode_generation_workflow.py` — 12 workflow tests

Full suite: 196/196 as of 2026-05-29.

---

## See Also

- [BARCODE_STAGE_PLAN.md](../archive/production/BARCODE_STAGE_PLAN.md) — design decisions D1-D5 *(archived)*
- [../tracking/EXPORTS.md](../tracking/EXPORTS.md) — export flow + LabelPrintQueue stub
- [OVERVIEW.md](OVERVIEW.md) — stage list snapshot
