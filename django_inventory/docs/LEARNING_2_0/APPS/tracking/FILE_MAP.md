---
id: l2-apps-tracking-file-map
type: topic-canonical
status: active
owner: handwritten
scope: tracking
anchors: config/tracking/
verified: 2026-07-13
---

# tracking — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — **AddaHistory/ClothRollHistory/ProductHistory** (append-only;
change_type, actor, `metadata` JSONB, timestamp). **BarcodeBatch** ★
((adda,color,size)+start_seq/end_seq = identity ranges). BatchBarcode, BarcodeExportBatch.
## services/ — `history_service.py` ★ (sole *History writer — read its
"YEH FILE KYU HAI" header) · `barcode_service.py` (scan-state + QR render primitive).
## NO views/urls here (inventory owns the /tracking/ surface). admin.py — 5 admins.
## templates/tracking/ — barcode dashboard/list/print sheet/export/history/scan.
## DB behaviour (junior): history rows are SAVED whenever a service does something
worth remembering — never updated, never deleted. A "fix" = a NEW row. Barcode
batches saved once at generation; the printed number on a garment is forever (adda,seq).

---
*Depth: [config/tracking/README.md](../../../../config/tracking/README.md) (business) ·
[docs/apps/tracking/GUIDE.md](../../../apps/tracking/GUIDE.md) (file-by-file). This = navigation/flow only.*
