---
id: apps-tracking-guide
type: app-guide
status: active
owner: handwritten
scope: tracking
anchors: config/tracking/
verified: 2026-07-13
---

# tracking app — file-by-file GUIDE (append-only memory + identity)

> Business view: [config/tracking/README.md](../../../config/tracking/README.md).
> PRIMITIVE app: imports neither production nor expense (string FKs).

| File | What |
|---|---|
| `models.py` | AddaHistory/ClothRollHistory/ProductHistory (append-only, JSONB metadata) · ★ BarcodeBatch (seq RANGES per adda+color+size — piece identity (adda,seq), payload PERMANENT ADR-0010) · BatchBarcode · ExportBatch |
| `services/history_service.py` | ★ SOLE *History writer (rule 5) — "YEH FILE KYU HAI" header padho |
| `services/barcode_service.py` | scan-state + QR primitive |
| (views?) | NAHI — P4.2: tracking ke views inventory/views/tracking_*.py me (URL namespace preserved) |

Dots: har service apne events yahan log karti hai; timelines + future G4 isi se.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
