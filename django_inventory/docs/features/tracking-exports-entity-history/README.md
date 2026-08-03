---
id: feature-tracking-exports-entity-history
type: feature-doc
status: generated
owner: generated
scope: feature — tracking-exports-entity-history
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Tracking exports + entity history (CSV · XLSX · PDF · re-download)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `tracking-exports-entity-history` |
| Label | Tracking exports + entity history (CSV · XLSX · PDF · re-download) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `tracking:adda-history` | `/tracking/history/adda/<str:adda_code>/` | `AddaHistoryView` | [adda-history.md](adda-history.md) |
| `tracking:export-csv` | `/tracking/exports/<str:adda_code>/csv/` | `ExportCSVView` | [export-csv.md](export-csv.md) |
| `tracking:export-download` | `/tracking/exports/<str:export_code>/download/` | `ReDownloadView` | [export-download.md](export-download.md) |
| `tracking:export-list` | `/tracking/exports/` | `ExportListView` | [export-list.md](export-list.md) |
| `tracking:export-pdf` | `/tracking/exports/<str:adda_code>/pdf/` | `ExportPDFView` | [export-pdf.md](export-pdf.md) |
| `tracking:export-xlsx` | `/tracking/exports/<str:adda_code>/xlsx/` | `ExportXLSXView` | [export-xlsx.md](export-xlsx.md) |
| `tracking:roll-history` | `/tracking/history/roll/<int:roll_pk>/` | `RollHistoryView` | [roll-history.md](roll-history.md) |

## Member models

No machine-provable member models (`belongs_to_feature` model edges: 0).

## Apps touched

- `inventory` — [config/inventory/README.md](../../../config/inventory/README.md) · [docs/apps/inventory/GUIDE.md](../../apps/inventory/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
