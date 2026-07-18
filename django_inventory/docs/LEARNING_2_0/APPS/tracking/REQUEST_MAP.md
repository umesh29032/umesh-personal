---
id: l2-apps-tracking-request-map
type: topic-canonical
status: active
owner: handwritten
scope: tracking
anchors: config/tracking/
verified: 2026-07-13
---

# tracking — REQUEST_MAP

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

> Tracking has NO own views (P4.2: /tracking/ URLs served by inventory/views/tracking_*).
| Capability | Writer | Models |
|---|---|---|
| log Adda/roll/product event | history_service.log_adda/log_roll/log_product (SOLE writer, rule 5) | AddaHistory, ClothRollHistory, ProductHistory |
| barcode ranges | barcode_service | BarcodeBatch, BatchBarcode |
| exports | barcode_service + inventory tracking views | BarcodeExportBatch |

---
*Depth: [config/tracking/README.md](../../../../config/tracking/README.md) (business) ·
[docs/apps/tracking/GUIDE.md](../../../apps/tracking/GUIDE.md) (file-by-file). This = navigation/flow only.*
