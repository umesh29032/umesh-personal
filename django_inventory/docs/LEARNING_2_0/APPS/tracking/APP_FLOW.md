---
id: l2-apps-tracking-app-flow
type: topic-canonical
status: active
owner: handwritten
scope: tracking
anchors: config/tracking/
verified: 2026-07-13
---

# tracking — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Append-only MEMORY + piece IDENTITY. Imports neither production nor expense
> (string FKs) — it's a primitive (ADR-0004).
## Flow 1 — History: koi bhi service important event hone par history_service.log_*
call karti hai → *History row (INSERT only, never edit). Timelines + future G4.
## Flow 2 — Barcode identity: barcode_generation stage → BarcodeBatch ranges per
(adda,color,size). Piece identity = (adda, seq); printed payloads PERMANENT (ADR-0010 §3).
## Flow 3 — Export: barcode CSV/XLSX/PDF (views live in inventory app — P4.2).

---
*Depth: [config/tracking/README.md](../../../../config/tracking/README.md) (business) ·
[docs/apps/tracking/GUIDE.md](../../../apps/tracking/GUIDE.md) (file-by-file). This = navigation/flow only.*
