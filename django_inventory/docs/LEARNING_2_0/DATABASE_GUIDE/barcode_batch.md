---
id: l2-database-guide-barcode-batch
type: database-guide
status: active
owner: handwritten
scope: barcode_batch (model)
anchors: —
verified: 2026-07-13
---

# DB: BarcodeBatch — piece identity ranges

## TL;DR
What: contiguous seq range per (adda,color,size). Why: per-piece identity =
(adda, seq) WITHOUT a per-piece table; printed payload PERMANENT. Writes:
barcode_service (at generation). Reads: print sheets, scan resolve, future
traceability. Breaks if removed: no piece identity. ADRs: 0004/0010 §3. File:
`config/tracking/models.py`.

## Fields (key)
adda FK, product FK, bundle FK, color FK, size FK, **start_seq / end_seq**
(PositiveInt), total_pieces (denormalized = end−start+1). unique_together(adda,color,size).
Indexes (adda,start_seq) + (adda,end_seq) for range lookup.

## Example
`3-PATTI-001, Red, Size-1, start_seq=1, end_seq=60, total_pieces=60`. Garment #37 = (3-PATTI-001, 37).

## FK chain
`BarcodeBatch → Adda` + Product/Bundle/Color/Size. Piece resolve:
`WHERE adda=? AND start_seq<=seq<=end_seq`.

## How data reaches / leaves
IN: barcode generation (one-shot, ranges). OUT: reopen deletes batches (regenerate).
NEVER renumber existing printed payloads.

## SQL
```sql
SELECT color_id,size_id,start_seq,end_seq,total_pieces FROM tracking_barcodebatch WHERE adda_id=<id>;
-- resolve a scanned piece:
SELECT * FROM tracking_barcodebatch WHERE adda_id=<id> AND start_seq<=37 AND end_seq>=37;
```

## Debug in production
Count mismatch → reconciliation_service (BarcodeGenerationRecord.total vs Σ batch).
Gap/overlap in ranges = generation bug. Query by adda_id.

### Verification Sources
tracking/models.py (BarcodeBatch+, start/end_seq, unique_together, indexes). **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** ADR-0010 §3.
