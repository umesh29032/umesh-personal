---
id: l2-request-journeys-barcode-flow
type: request-journey
status: active
owner: handwritten
scope: barcode_flow (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Barcode Generation

## TL;DR (1 min)
After cutting, generate contiguous barcode ranges per (adda,color,size). Piece
identity = (adda, seq); printed payload is PERMANENT.

**URL** `production:barcode-gen-*` (workspace/start/generate/complete/reopen).
**View** `production/views/barcode_gen_views.py:BarcodeGen*View`. **Service**
`production.services.generate_barcodes` + barcode_generation stage service +
`tracking.barcode_service`. **Models read** CuttingBundle/breakup (piece counts),
BarcodeGenerationRecord. **Models written** BarcodeGenerationRecord, BarcodeBatch
(ranges), AddaHistory (BARCODES_GENERATED). **Tx** atomic (one-shot generate).
**RBAC** skill/management. **ADRs** 0004 (tracking primitive), 0010 §3 (payload permanence).
**Tables** production_barcodegenerationrecord, tracking_barcodebatch, tracking_addahistory.

### How would I debug this in production?
- **First file:** `production/stages/barcode_generation/service.py` + `tracking/services/barcode_service.py`.
- **First query:** `SELECT adda_id,color_id,size_id,start_seq,end_seq,total_pieces FROM tracking_barcodebatch WHERE adda_id=<id>;`
- **First log:** barcode generate + `BARCODES_GENERATED` history.
- **Failure modes:** count mismatch (BarcodeGenerationRecord.total vs Σ BarcodeBatch.total_pieces — reconciliation_service checks); reopen deletes batches.
- **Expected DB state:** contiguous seq ranges, no gaps/overlaps per (adda,color,size).
- **Recovery:** reopen → batches deleted → regenerate. NEVER renumber existing printed payloads.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (urls/views barcode_gen; service __init__ exports generate_barcodes). Internals: **Derived understanding** (read structure + handler, not every line). Tests: barcode/stage tests.
