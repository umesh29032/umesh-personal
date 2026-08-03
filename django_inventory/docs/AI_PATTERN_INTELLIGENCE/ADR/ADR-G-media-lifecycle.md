---
id: docs-ai-pattern-intelligence-adr-adr-g-media-lifecycle
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-G — Media & Asset Lifecycle

**Status: DRAFT (Phase 1) — owner sign-off pending.**

## Problem
"Store ALL originals forever" (owner vision) meets a single factory server:
capture originals, marker renders, and overlay prints accumulate for years.
Without a lifecycle, either disks fill, backups slow past tolerance, or —
worse — someone "cleans up" the company's pattern IP.

## Decision
1. **Three storage classes mirroring the V3 deletion policy (F5):**
   - **KNOWLEDGE (never deleted):** capture ORIGINALS (byte-immutable, sha256
     recorded on the row at upload), confirmed-geometry exports of record.
     Superseded originals move to a **cold/archive tier — never removed**.
   - **REGENERABLE (freely deletable):** thumbnails, rectified previews,
     masks, marker render caches — rebuildable from knowledge + pinned
     pipelines; excluded from forever-retention and from backups where
     rebuild is cheaper.
   - **DEV-marked:** deletable only via owner-sanctioned teardown (the
     Manufacturing V1 precedent).
2. **Layout:** `media/patterns_ai/<product>/…` with class-separated subtrees
   (`originals/`, `derived/`), so retention/backup policy is a path rule.
3. **Integrity job:** periodic sweep comparing DB rows ↔ files ↔ checksums,
   with a report row (append-only) — bit-rot and manual-deletion detection.
4. **Growth budget + switch point:** local disk first; the S3/MinIO switch
   point, backup inclusion rules, and a restore-time target are declared in
   the deploy runbook AT P1 (numbers, not intentions). Model weights live in
   the ADR-F artifact store, never under `/media`.
5. Serving: originals never served raw to browsers (size); derived renditions
   serve the UI.

## Alternatives considered
- **Database blobs** — rejected: backup bloat, no partial restore, Postgres
  is not an object store.
- **Delete-on-supersede** — rejected: violates F5 and the owner's permanence
  lock; superseded ≠ worthless (reprocessing source).
- **S3 from day one** — rejected: network dependency contradicts local-first
  factory reality; the switch point is designed in instead.
- **Deduplicating store (content-addressed)** — deferred: sha256 already
  recorded, so dedup can be layered later without schema change.

## Tradeoffs
Cold tier + integrity job = modest operational surface (one cron, one report).
Keeping originals forever costs disk (bounded by capture volume; photos not
video); the class split keeps backups proportional to knowledge, not caches.

## Consequences
The pattern library is restorable end-to-end: knowledge class + repo (ADR-F)
reproduce everything else. "How big is our pattern IP and is it intact?" is a
report, not archaeology.

## Future evolution
S3/MinIO migration = storage-backend swap behind Django storage API (paths
stable); per-site media roots slot under the same classes for multi-factory;
content-addressed dedup optional later.

## Why it respects Manufacturing V1
Separate media tree — never touches `CuttingPatternPhoto` or its
compress-in-place pipeline; backup runbook extends the existing deploy
documentation rather than replacing it.

## Why it respects Blueprint V3
Implements F5's three classes and C13's custody expectations at the storage
layer; permanence lock honored with an honest cost model; simplicity (path
rules + cron, no new services beyond the sweep).
