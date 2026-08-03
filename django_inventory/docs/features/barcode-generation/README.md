---
id: feature-barcode-generation
type: feature-doc
status: generated
owner: generated
scope: feature — barcode-generation
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Barcode generation

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `barcode-generation` |
| Label | Barcode generation |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:barcode-gen-complete` | `/production/addas/<str:code>/barcode-gen/complete/` | `BarcodeGenCompleteView` | [barcode-gen-complete.md](barcode-gen-complete.md) |
| `production:barcode-gen-generate` | `/production/addas/<str:code>/barcode-gen/generate/` | `BarcodeGenGenerateView` | [barcode-gen-generate.md](barcode-gen-generate.md) |
| `production:barcode-gen-reopen` | `/production/addas/<str:code>/barcode-gen/reopen/` | `BarcodeGenReopenView` | [barcode-gen-reopen.md](barcode-gen-reopen.md) |
| `production:barcode-gen-start` | `/production/addas/<str:code>/barcode-gen/start/` | `BarcodeGenStartView` | [barcode-gen-start.md](barcode-gen-start.md) |
| `production:barcode-gen-workspace` | `/production/addas/<str:code>/barcode-gen/` | `BarcodeGenWorkspaceView` | [barcode-gen-workspace.md](barcode-gen-workspace.md) |
| `tracking:barcode-export` | `/tracking/barcodes/<str:adda_code>/export/` | `barcode_export_csv` | [barcode-export.md](barcode-export.md) |
| `tracking:barcode-list` | `/tracking/barcodes/<str:adda_code>/` | `BarcodeListForAddaView` | [barcode-list.md](barcode-list.md) |
| `tracking:barcode-print` | `/tracking/barcodes/<str:adda_code>/print/` | `BarcodePrintSheetView` | [barcode-print.md](barcode-print.md) |
| `tracking:dashboard` | `/tracking/` | `BarcodeDashboardView` | [dashboard.md](dashboard.md) |
| `tracking:scan` | `/tracking/scan/<str:value>/` | `scan_piece` | [scan.md](scan.md) |
| `tracking:scan-status` | `/tracking/scan/<str:value>/status/` | `update_piece_status` | [scan-status.md](scan-status.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.BarcodeGenerationRecord` | `production_barcodegenerationrecord` | not machine-known |
| `tracking.BarcodeBatch` | `tracking_barcodebatch` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)
- `inventory` — [config/inventory/README.md](../../../config/inventory/README.md) · [docs/apps/inventory/GUIDE.md](../../apps/inventory/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
