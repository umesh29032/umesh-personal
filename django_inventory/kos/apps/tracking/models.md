---
id: app-tracking-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "tracking's 6 models — identity, state, memory: who writes each, and what's permanent?"
related: [app-tracking]
---

# tracking — model knowledge (`config/tracking/models.py`, 410 lines · 6 models)

> 📂 [tracking app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## Identity (2)

**`BarcodeBatch` (line 21)** — a contiguous seq RANGE per (adda, color,
size). Ranges, not rows-per-piece (storage win). Writer: production's
barcode-gen handler. **Printed payloads PERMANENT** (ADR-0010) — ranges may
append, never rewrite.

**`BatchBarcode` (130)** — per-PIECE scan state, **lazily created on first
scan** (untouched pieces cost nothing). FSM: pending→packed→dispatched.
Writer: `barcode_service.mark_status` (+ `get_or_create_piece`).
DSA: create-on-demand + a tiny FSM ([stage-tracking §DSA](../../features/stage-tracking.md) mindset).

## Memory (3) — the system's timelines

**`ClothRollHistory` (212)** · **`AddaHistory` (237)** · **`ProductHistory`
(326)** — append-only event rows (actor, change_type, field diffs via
`FieldChangeMixin`, per-domain extras like stage_from/to). Base:
`core.AbstractHistoryEntry`. **Sole writer: `history_service`** (ADR-0002).
Wall #4 lives on READS: financial CHANGE rows stripped for workers
(certified). Never UPDATE/DELETE — correcting events follow wrong events.

## Manifest (1)

**`BarcodeExportBatch` (358)** — the tracked-export manifest row (what was
exported, when, re-download by code). Pattern canon:
[tracked-export](../../concepts/patterns/tracked-export.md).

## Cross-model laws

Append-only citizenship everywhere · identity permanence · lazy piece
materialization · PROTECT-grade anchors. Model docstrings are teaching-grade.

## Required Knowledge (this page)

- [ ] Append-only + evidence-vs-state → [append-only-tables](../../concepts/database-design/append-only-tables.md)
- [ ] Identity policy → ADR-0010 via [reading-the-docs](../../project/reading-the-docs.md)

## Learning Graph

**Before:** [production Part 4](../production/urls-cutting-barcode.md).
**After:** [services.md](services.md) — the two monopolies that write these.
