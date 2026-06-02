# Barcode Exports

Shipped: PR-D, 2026-05-29.

---

## Purpose

After Barcode Generation stage completes, Cutting Master (or Super Admin)
generates exportable files for:

- **Vendor label printing** — CSV / XLSX rows that vendor's printer software consumes
- **Factory sign-off** — PDF summary manifest for paper trail
- **Audit + reorder** — re-download by export code for vendor reprints

Export is **manifest-tracked**. Every export creates a `BarcodeExportBatch`
row. File content is regenerated on-demand from live `BarcodeBatch` data
(not stored on disk).

---

## Flow

```
Barcode Generation stage COMPLETE
    │
    ▼
Cutting Master triggers export (CSV / XLSX / PDF)
    │
    │ Service: generate_csv / generate_xlsx / generate_pdf_summary
    │
    ├─→ Validate barcode_generation stage is complete
    │   (else ValidationError 400)
    │
    ├─→ Compute total_labels (SUM of BarcodeBatch.total_pieces)
    │
    ├─→ Generate next export_code (EXP-YYYY-NNN)
    │
    ├─→ Insert BarcodeExportBatch row (manifest, frozen)
    │
    └─→ Render bytes from live data + return HTTP attachment
    │
    ▼
File downloaded by browser
```

Re-download:

```
GET /tracking/exports/<export_code>/download/
    │
    └─→ Fetch BarcodeExportBatch row
    └─→ Re-render bytes from CURRENT BarcodeBatch state
    └─→ Same Content-Disposition filename as original
```

If barcodes were reopened + regenerated between original export and
re-download, content will differ. Manifest `total_labels` stays frozen
at first export (audit trail).

---

## Per-Row Output Shape

Each row in CSV / XLSX represents one printable label:

| Column | Source |
|--------|--------|
| `barcode` | `BatchBarcode.value` (or `BarcodeBatch.value_for_seq()` for lazy seq) |
| `qr_payload` | Same as barcode (QR encodes value verbatim) |
| `adda` | `Adda.code` |
| `product` | `Product.code` |
| `bundle` | `Bundle-{size_code_upper}` (e.g. `Bundle-M`) |
| `size` | `ProductSize.label` |
| `color` | `ClothColor.name` |
| `piece_seq` | 1-indexed within Adda |

PDF is **NOT per-piece**. PDF renders the manifest:

- Title + Adda + Product + Export timestamp
- Per-batch table: Size | Color | Range | Pieces
- TOTAL row at bottom

---

## Gate Rules

Export refused if:

1. Adda's product workflow has no `barcode_generation` stage
2. Stage record missing (never started)
3. Stage record not completed (`completed_at` is NULL)
4. `BarcodeGenerationRecord` missing
5. No barcodes exist (`SUM(BarcodeBatch.total_pieces) == 0`)

All gates raise `ValidationError`. Views return HTTP 400 with message.

---

## URL Surface

```
GET   /tracking/exports/                         export-list (recent global)
POST  /tracking/exports/<adda_code>/csv/         export-csv
POST  /tracking/exports/<adda_code>/xlsx/        export-xlsx
POST  /tracking/exports/<adda_code>/pdf/         export-pdf
GET   /tracking/exports/<export_code>/download/  export-download (re-download)
```

Legacy `/tracking/barcodes/<adda_code>/export/` still works as a quick CSV
download (no manifest row). Useful pre-completion for diagnostics. The new
manifest-tracked path is preferred for production exports.

---

## Models

`tracking.BarcodeExportBatch`:

| Field | Type | Notes |
|-------|------|-------|
| `export_code` | CharField(24, unique) | `EXP-YYYY-NNN` |
| `adda` | FK Adda (PROTECT) | |
| `product` | FK Product (PROTECT) | denorm |
| `barcode_gen_record` | FK BarcodeGenerationRecord (PROTECT) | source |
| `export_method` | TextChoices | csv / xlsx / pdf |
| `exported_by` | FK User (PROTECT) | |
| `total_labels` | PositiveIntegerField | **frozen at first export** |
| `created_at` / `updated_at` | TimeStampedModel | |

Index: `(adda, -created_at)` + `(-created_at)` for global list.

---

## Where Code Lives

| File | Role |
|------|------|
| `config/tracking/services/barcode_export_service.py` | CSV / XLSX / PDF renderers + manifest write + sequencer |
| `config/tracking/views/export_views.py` | 5 views (3 triggers + redownload + list) |
| `config/tracking/templates/tracking/export_list.html` | Global recent exports table |
| `config/production/templates/production/_stage_panel_barcode_gen.html` | Section 06 — export buttons inside stage panel |

---

## Sequencer

`_next_export_code()`:

1. Compute prefix `EXP-{current_year}-`
2. Fetch latest export code with that prefix (ordered by code)
3. Parse trailing number, add 1
4. Format with 3-digit zero-pad

Race risk: at high throughput, two concurrent exports could collide on
the same number (catch by `unique=True` on `export_code`). For factory
floor scale (few exports/day), acceptable. Future hardening: dedicated
Postgres sequence per year.

---

## Future: Label Print Queue (Stub Only)

`production.LabelPrintQueue` is a **stub model only**. Designed in PR-A
but no service logic yet. Future flow:

```
Export generated
    │
    ▼
LabelPrintQueue row created
    │   status = QUEUED
    │
    ├── status → SENT          (vendor receives file via email / portal)
    │       sent_at stamped
    │
    ├── status → RECEIVED      (vendor delivers labels physically)
    │       received_at stamped
    │
    └── status → PRINTED       (factory printer integration, future)
            printed_at stamped
```

Implementation deferred per user instruction. When real workflow lands:

- Service auto-creates row on export completion
- Status transitions via service methods + AddaHistory audit log
- Factory-printer integration writes `printed_at` directly

---

## Dependencies

- `openpyxl==3.1.2` — XLSX writer
- `reportlab==4.1.0` — PDF generation

Added to `requirements.txt` in PR-D.

---

## Tests

`config/tracking/tests/test_barcode_export.py` — 13 tests:

- Gate (refused before bg complete; refused mid-progress)
- CSV bytes + headers + 20 rows
- XLSX bytes valid via openpyxl reload
- PDF starts with `%PDF-`
- Export code increments
- Re-download identical bytes
- View-layer integration (5 view tests)

Full suite: 196/196 as of 2026-05-29.

---

## See Also

- [../production/BARCODE_GENERATION.md](../production/BARCODE_GENERATION.md) — upstream stage
- [../production/BARCODE_STAGE_PLAN.md](../production/BARCODE_STAGE_PLAN.md) — design decisions
- [../production/OVERVIEW.md](../production/OVERVIEW.md) — production subsystem overview
