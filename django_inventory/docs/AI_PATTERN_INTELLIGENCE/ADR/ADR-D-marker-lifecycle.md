---
id: docs-ai-pattern-intelligence-adr-adr-d-marker-lifecycle
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-D — Marker Immutability, Lineage, Statuses & Promotion

**Status: DRAFT (Phase 1) — owner sign-off pending.**

## Problem
Markers are knowledge assets the owner keeps forever (V2 principle: manual
markers first-class; nothing overwritten). They reference geometry that itself
evolves; they can be born from a Product library, a manual chalk photo, an
import, or an Adda-temporary generation that may later be promoted. Without a
precise lifecycle, immutability and the owner's promotion vision collide.

## Decision
1. **Markers are immutable after creation.** Placements are never edited;
   "changing a marker" = creating a new one with `supersedes` lineage.
   Regeneration is a new `MarkerRun` + new Marker.
2. **Origins:** `manual_photo | generated | imported | adda_temporary`.
   Manual markers (photo + declared width/ratio/repeats, placements optional)
   are permanent first-class citizens — the library's founding population and
   the baselines every generated marker must beat (`benchmarked_against` FK).
3. **Status machine (complete, F5):**
   `candidate → validated → promoted → superseded | retired(reason) |
   rejected(reason)`. Every transition records actor + timestamp; negative
   transitions REQUIRE a reason (F2). Nothing is ever deleted; `retired`/
   `rejected` stay queryable in the biography.
4. **Adda-temporary carve-out (D11):** `origin=adda_temporary` markers carry a
   nullable Adda FK and MAY pin **draft** geometry; they render with an
   UNVERIFIED badge and are excluded from recommendations. **Promotion =
   human-confirming the pinned geometry rows + one audited status flip** — no
   copying; PROTECT pins already point at the right rows; full history travels.
5. **Single-writer:** every marker mutation (creation, transition, usage)
   passes through `marker_service`; import/backfill tooling uses the same
   chokepoint — raw-ORM writes are a review-reject (I-1).
6. **Reproducibility contract (C16):** stored placements ARE the artifact;
   re-RENDER always; re-RUN best-effort (seed/engine pinned for audit only).
7. **References:** globally-unique `MRK-000001` via the shared
   `next_reference` discipline (C14); `usable_width_band` stamped at creation
   (C10).

## Alternatives considered
- **Editable draft markers** — rejected: mutating knowledge; drafts are cheap
  to regenerate instead.
- **Copy-on-promotion** — rejected: duplicates rows, severs lineage, breaks
  "complete history travels with it".
- **Hard-deleting rejected candidates** — rejected: rejections are knowledge
  (F2/F5); a reasoned `rejected` state is the asset.
- **Marker versions as mutable head + history table** — rejected: two truths;
  immutable rows + lineage FKs are simpler and match V1's append-only style.

## Tradeoffs
Many similar immutable rows accumulate (cheap; biography + supersedes chains
keep them navigable; UNVERIFIED/retired tiers keep pickers clean). Promotion
requires geometry confirmation first — deliberate friction: the human gate IS
the feature.

## Consequences
The marker library is a true append-only knowledge base: every layout the
factory ever cut or considered, with reasons, evidence, and lineage. The
confidence system (V2 §5) reads facts without special cases.

## Future evolution
New origins (e.g. `plotter_native`), new strategies, new validation gate types
= additive enum/event values. Cross-product marker cloning (if ever wanted) =
new marker with lineage to the source — no schema change.

## Why it respects Manufacturing V1
MarkerUsage FKs INTO production (Adda) — the allowed direction; no production
writes; the audited-void/append-only philosophy mirrors V1's settlement armor
(reasons on negative paths = the same discipline as void_submitted_report).

## Why it respects Blueprint V3
Implements C2/C4/C6/C14/C16, F2 (decision spine), F5 (status sets + never
delete), and the owner's promotion vision verbatim; keeps the simplicity
principle (one table, one service, lineage FKs — no parallel version store).
