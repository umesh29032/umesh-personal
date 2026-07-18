---
id: barcode-architecture-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# BARCODE ARCHITECTURE REVIEW — first principles, real factory
(2026-07-11 · Module 7 opening review · REVIEW ONLY, no code ·
method: production-manager questions answered against the ACTUAL
implementation — tracking/models.py, tracking/services/barcode_service,
production/stages/barcode_generation/{service,assembly}, the module-5/6
browser walks, and the streams proof world DEV-NICKAR-001)

# VERDICT: **NO redesign. The existing barcode architecture is correct
on first principles.** One SMALL implementation gap is real and
justified — born from the streams late-lane semantics — and gets the
one-page readiness (companion doc). Everything else stands as built.

---

## 1 · The first-principles questions, answered

**What is the TRUE purpose of the barcode?**
Identity, nothing else. A barcode is a permanent NAME for one physical
piece so the database can speak about it later. It is not a data
carrier, not a label, not a report.

**What exactly is being identified?**
**One PIECE, scoped to one Adda.** The printed value is
`{ADDA}-{SEQ:04d}` (e.g. `DEV-NICKAR-001-0037`) — Adda code + a
per-Adda sequence number. Not bundle, not size, not color, not worker,
not operation: those are FACTS ABOUT the piece, and facts live in the
database (`BarcodeBatch` rows carry size · color · bundle · range).
Scanning `…-0037` resolves the batch → every dimension arrives
derive-at-read. This is exactly the right split.

**Your Option A vs Option B question — already answered by the build.**
Option A (one simple sequence per Adda) is the printed NUMBER; Option B
(size/color/bundle-aware traceability) is the DATABASE truth behind it.
The current design IS both at once, because it encodes nothing and
derives everything. There is no decision left to make.

**What should NEVER be encoded?** Anything that can change or be
corrected: dimensions, worker, rates, stage, status. The value already
encodes none of these — correcting a wrongly-recorded color is a DB
edit; ten thousand printed stickers stay valid. (Encode-nothing is the
same law as derive-at-read, applied to paper.)

**What should be printed?** The value + its QR (payload = the scan
URL). Human-readable size/color MAY be printed alongside as a
convenience — the export manifest already carries them — but they are
decoration, never identity.

**Which stages actually need scanning?** Today: NONE are required —
and that is correct, not a gap. The count hierarchy (modules 5–6,
browser-proven) is the flow truth: ops stages consume dimension-scoped
COUNTS (allocations → reports → verified-else-good pools). Scanning is
the EXCEPTION channel: `mark_status` per piece (damage, QC holds,
spot-checks) and future dispatch verification. `BatchBarcode` rows are
lazily created ON FIRST SCAN — zero rows for the happy path, a row the
moment reality needs to say something about one specific piece. This is
the cheapest honest design possible; making any stage scan-mandatory
would be redesign-because-it-looks-rigorous, which you forbade.

**What happens when a barcode is damaged (the sticker)?**
Reprint the same value — `BarcodeExportBatch` manifests regenerate
idempotently on download; identity never changes. A damaged PIECE is a
status (`mark_status` → damaged), not a new identity.

**What happens after recutting / additional Cutting Streams?**
⚠️ **The one real gap.** The frozen late-lane semantics
(CUTTING_STREAM_LIFECYCLE §2) promise that a post-join lane's output
"APPENDS to the ops pool" — but barcode generation is one-shot per
Adda (`generate_for_adda` / `generate_for_cutting` raise when any
batch exists). A recut lane's 12 replacement pieces would reach the
pool with NO identities. The fix is small and law-shaped: **append
batches for uncovered breakdown rows, continuing the sequence at
`Max(end_seq)+1`** — sequence numbers are data, never reused, and
history is untouched. This is a real factory workflow (you named
recuts twice), not speculation. → readiness doc.

**Should one Adda have one sequence forever?** Yes — continuous,
append-only, never renumbered. The append fix above preserves exactly
that.

**Can future formats evolve without changing history?** Yes —
`parse_value`/`resolve_value` is the single resolver seam; a future
format is a new pattern the resolver also accepts. Old stickers scan
forever. No change needed now (YAGNI); the seam already exists.

## 2 · Ownership (verified correct as built)

| Concern | Owner | As built |
|---|---|---|
| Generation moment + counts | ERP (production) | barcode stage / at-the-join inline; sourced from the frozen per-lane breakdowns (APSCPB) adda-wide |
| Identity, ranges, values, scan state | Tracking | BarcodeBatch (single writer: the generation assembly) · BatchBarcode lazy rows · barcode_service |
| Printing/export | Tracking | BarcodeExportBatch, idempotent regeneration |
| Consumption as counts | ERP ops stages + Inventory | pools/dashboards read ranges + statuses; never write |
| Pattern Intelligence | **NOTHING** | correct — PI ends at the layout contract; barcodes are floor identity |

Single-writer holds (assembly writes batches; barcode_service writes
piece scan-state; nobody else). Genericity holds (no product knowledge
anywhere near barcode code). Operator authority holds (counts stand;
scans annotate, never overrule).

## 3 · Challenges considered and REJECTED (so they stay rejected)

- **Encode size/color in the value** — breaks correction-safety and
  print permanence for zero factory gain; the DB already answers every
  scan. Rejected.
- **Mandatory scan-in/scan-out per stage** — the floor runs on counts;
  per-piece scanning at 13 stages is a labor tax the owner never asked
  for. The lazy-scan design already supports it LATER per stage with
  zero schema change if a real problem (theft/loss dispute) demands.
  Rejected now.
- **Per-bundle barcodes as primary identity** — bundles are containers;
  pieces outlive bundle membership (recuts, re-bundling). Piece
  identity + bundle-as-DB-fact is strictly more truthful. Rejected.
- **Adda-independent global sequence** — destroys the floor's mental
  model ("piece 37 of this order") and gains nothing. Rejected.

## 4 · What Module 7 (campaign) should verify AFTER this review

The verification module proceeds on the CURRENT architecture: export
manifest download (CSV/XLSX/PDF) · QR scan resolve → correct
size/color/bundle derive-at-read · mark_status lifecycle (scan → status
→ audit) · lazy-row law (no rows before first scan) · reprint
idempotence · the streams world's 1–60 range resolving correctly for
both fabrics — plus the append fix below once approved.

**STOP — review only. No code written. Readiness for the ONE justified
item: BARCODE_IMPLEMENTATION_READINESS.md.**
