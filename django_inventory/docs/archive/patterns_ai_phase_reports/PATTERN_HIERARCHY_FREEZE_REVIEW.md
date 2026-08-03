> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PATTERN HIERARCHY FREEZE REVIEW — Piece vs Design
(2026-07-07 · review ONLY, no redesign, no code. Question: is the
explicit Pattern Piece level cleaner than treating Pattern Design
directly as Piece × Size — and what should freeze?)

---

## 0. Verdict up front

**The explicit Pattern Piece level ALREADY EXISTS as a first-class
concept in the built model — the owner's hierarchy is not a change, it
is the correct DESCRIPTION of what is built**, with two precise
clarifications to freeze alongside it (versioning grain §3, reference-
image home §4). No new level, no new table, no migration is needed or
recommended. The perceived "mixing" of Piece and Design was a
VOCABULARY problem (pages and docs sometimes said "piece" when showing
a design row), and the Workspace design already fixes it by making the
design row the visual atom.

## 1. Owner's hierarchy → built model, term by term

| Owner concept | Built truth | Verdict |
|---|---|---|
| Pattern Piece (logical garment component: Front Panel…) | `PatternPiece` — product-scoped identity row; owns flags (optional · pair · fold), the reference image, the library link | ✅ exists, first-class, size-independent — exactly the owner's definition |
| Pattern Design (versioned design of ONE piece for ONE size) | the **confirmed (piece-version × size) geometry row** — geometry · preview (derived) · measured dims + tape · DXF in/out · metadata · trust status; reachable as "piece P, size S, version vN" | ✅ exists as a precise composite; the resolver and every layout's provenance ALREADY treat exactly this tuple as the atom |
| Product → Size → Piece → Design (the order) | storage is a GRID (piece identity × size), which is what lets the Workspace show it size-first AND the matrix show it piece-first from one derivation | ✅ freeze it as the NAVIGATION hierarchy; the grid underneath is what makes both lenses cheap — do not reorder storage |

## 2. So is anything actually mixed? — What was, and what fixed it

Historically the Hub's cards were PIECE-level (flags, one status), and
designs were only visible deeper. That is the mixing the owner felt.
The approved Workspace design already resolves it: **the design row
(Piece × Size) is the atom the operator sees; the piece appears as the
row's identity + badges; sizes are the grouping.** Nothing in the data
needed to change for this — only the projection.

## 3. The ONE real semantic decision hiding in the owner's sentence
("a Pattern Design is a VERSIONED design … for ONE size")

Two possible version grains:

- **Built: versions belong to the PIECE** (append-only chain per
  piece; one version carries geometry rows for its sizes; copy-forward
  starts v(n+1) from v(n); confirming supersedes at the piece level).
- Owner's sentence could be read as: **independent version chains per
  (piece, size)** — "Front Panel L v3 while Front Panel S stays v1".

**Review verdict: the built (per-piece) grain is the cleaner one, for
factory reasons, and the owner's per-design version VIEW should be a
display truth on top of it:**
1. **Factory reasoning:** a shape change re-grades the FAMILY. When
   the front neck curve changes, S–XXL all change together (grading).
   Per-piece versioning makes the grading family one auditable unit;
   per-size chains invite drift (L cut to new logic, S still old —
   physically inconsistent garments in one marker).
2. **Provenance reasoning:** layouts already snapshot the exact
   (version, geometry-row) per design — per-piece versions keep one
   confirm act per family = one truth boundary; per-size chains would
   multiply confirm acts and superseding edges for zero layout-side
   gain.
3. **Editing reasoning:** editing only L today = copy-forward v(n+1),
   edit L's row, confirm — the other sizes ride along unchanged. One
   extra implicit step, but it PRESERVES the family audit. This is a
   feature, not friction.
4. **Display resolution (what the Workspace does):** every design row
   shows ITS version number and status ("v2 · Confirmed ✓", "v3 draft
   in progress") — the operator experiences per-design versioning; the
   system keeps family integrity underneath. Both mental models
   satisfied, no schema change.

**Freeze recommendation: version chain = per Piece (as built), version
DISPLAY = per Design row (as designed).**

## 4. The second clarification: where the Reference Image lives

Owner's list puts the reference image inside Pattern Design (per
size). Built: reference image is **per PIECE**.
- A Front Panel's illustrative photo does not vary by size; per-size
  references would mean 4–6 near-identical uploads per piece
  (30+ photos for the real T-SHIRT) for almost no information.
- The per-size SHAPE truth already exists as the geometry preview on
  every design row — the thing a per-size reference would try to show.
- The Workspace design already displays the piece's reference on EVERY
  design row of that piece, so the operator's experience matches the
  owner's list anyway.

**Freeze recommendation: reference image = per Piece, displayed per
Design row.** (Future-compatible note, decision not needed now: an
optional per-design override could be added later without disturbing
anything — the piece-level image simply becomes the fallback. Only
worth it if size-specific construction photos ever matter.)

## 5. Would reifying "PatternDesign" as its own table be cleaner? NO.

Tested against the three concerns the owner named:
- **Versioning** — per-piece chain is the better grain (§3); a Design
  table would either duplicate the version chain per size (drift risk)
  or still point at the piece chain (then it adds nothing).
- **Future editing** — per-size draft editing ALREADY targets exactly
  one (version, size) row; a new table adds no capability.
- **Cutting Table composition** — the resolver already emits design
  atoms as (piece, size, version, geometry-row) tuples, and layout
  provenance already stores them; the CT palette consumes these as-is.
  A Design table would be a second name for the same tuple.
Cost side: new table + backfill + provenance/migration churn against
frozen, populated data — for a synonym. **Equivalent-or-worse.
Do not reify.**

## 6. Cutting Table relationship — restated against this hierarchy

CT consumes **confirmed Pattern Designs** (the tuples above) through
the read-only facade; layouts copy geometry into their immutable
payload (never referencing live rows for display); CT never writes any
piece/version/geometry table. Already law (I-1 wall + immutable
payloads); the hierarchy freeze changes nothing here — it names it.

## 7. The freeze (what to write into the design contract)

```
NAVIGATION HIERARCHY (frozen):   Product → Size → Pattern Piece → Pattern Design
DATA GRAIN (frozen, as built):   PatternPiece (identity + flags + reference image)
                                 └ versions: append-only chain PER PIECE
                                     └ geometry rows: one per (version × size)
"PATTERN DESIGN" (frozen term):  the confirmed (piece, size) design =
                                 latest confirmed version's row for that size
                                 — owns geometry · preview · dims+tape · DXF ·
                                 metadata · status; displays ITS version
REFERENCE IMAGE (frozen home):   per Piece, shown on every design row
CUTTING TABLE (frozen relation): consumes confirmed Designs read-only, never owns/edits
```

**STOPPED — review delivered. If the owner accepts §3 (per-piece
version chain, per-design version display) and §4 (per-piece reference,
per-row display), the hierarchy is FROZEN exactly as the owner wrote it
— with zero schema change — and the Workspace implementation plan can
be drafted next. If the owner instead wants per-(piece,size) version
chains or per-design reference images, say so explicitly — both are
schema decisions that must be taken BEFORE the Workspace build.**
