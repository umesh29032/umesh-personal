> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# REVIEW — Workflow split: Product Sizes page → per-Size Design Library
(2026-07-08 · review ONLY. Question: is Product → Sizes →
Manage-Pattern-Designs(one size) → Cutting Table cleaner than one
expanding Workspace page?)

## Verdict: YES — cleaner, and I recommend adopting it as-is.

This is not a tie-breaker judgment; the split wins on every axis that
has bitten us so far:

1. **It matches the operator's question order.** "What sizes exist,
   which are ready?" is a DECISION page; "fix Size L" is a WORK page.
   One page per question = the factory-software law the owner stated
   (simple pages → simple decisions → simple actions). The W2R
   single-page plan juggled three densities to fake this; the split
   just... has two pages.
2. **Cognitive load matches the real prep loop.** A cutting master
   prepares ONE size at a time and returns. The size-library page puts
   exactly one size's designs in front of them — nothing else exists.
3. **It scales structurally, not by discipline.** 20 pieces × 8 sizes
   never lands on one page again: the overview is always ≤ a dozen
   cards; the library is always ≤ the piece count. The 160-row budget
   problem dissolves instead of being managed.
4. **Mobile becomes trivially right.** Overview = stacked verdict
   cards (perfect phone page). Library = one focused list. No
   accordion mega-page, no three-density juggling, no bottom-sheet
   complexity — most of redesign-§5.8's cleverness becomes
   unnecessary, which is the best sign.
5. **The Cutting Table inherits the same grouping for free**: its
   Available palette is "the size-library pages, read-only, grouped" —
   conceptual continuity from preparation to composition.

## Honest trade-offs (named, all acceptable)

- **One extra tap** to see any design (overview → size). That tap IS
  the workflow — it buys the empty-headed overview.
- **Cross-size questions** ("is Pocket confirmed everywhere?") don't
  fit either page — the matrix overlay stays on the overview as the
  power lens. Answered, not lost.
- **Piece-level acts** (optional toggle, reference image) happen on a
  SIZE page while affecting all sizes — the "applies to all sizes of
  ⟨piece⟩" label carries over verbatim; acceptable because the frozen
  truth is piece-level and the label is honest.
- The product-level summary (%, checklist, defaults) compresses into
  the overview header + a details/settings sheet — nothing lost,
  nothing competing.

## Why implementation is CHEAP (no new architecture)

- Same view, param-scoped: `?product=2` = the Sizes overview;
  `?product=2&size=l` = the Size-L Design Library. Rule C intact, one
  URL family, no routing invention.
- The W1 facade already sections per size — the library page renders
  ONE section; the overview renders per-section VERDICTS (the same +3
  additive fields from R-W2-1: `ready`, `required_missing`, ordering).
- The Design-Row atom is reused untouched on the library page (this is
  the reuse it was built for). Ghost rows, honesty labels, size-focus
  edit anchors, matrix overlay, POST actions, writers: all unchanged.
- Zero schema. Zero service changes.

## Decisions — mostly self-resolved by the owner's own text

| # | Status |
|---|---|
| PD-1 CT gate | **RESOLVED by owner:** "only when at least one Size is ready" — enabled at ≥1 Ready size; disabled state lists per-size verdicts |
| PD-3 Layouts off the page | **RESOLVED:** the sketch contains no layouts; they live behind the CT entry |
| PD-4 manage-mode | **DISSOLVED:** the size-library page IS the manage surface; no mode toggle needed |
| PD-2 + Add Size | remains: v1 = clean hand-off to production Sizes (boundary); slide-over later if wanted |

## The locked workflow (supersedes the W2R single-page shape)

```
/production/products/<id>/patterns/  (production: assignments + button)
        │  🧵 Open Pattern Manager
        ▼
PRODUCT PATTERN MANAGER (?product=N) — sizes only:
   product header (name · overall % · settings sheet)
   [S · Ready ✓ · 8/8]  [M · Ready ✓ · 8/8]
   [L · Needs attention ⚠ · 7/8 · Missing: Care Label]
   each card → [Manage Pattern Designs]        [+ Add Size]
   [🪡 Open Cutting Table] — enabled at ≥1 Ready size, else the reason
        │
        ▼
SIZE DESIGN LIBRARY (?product=N&size=l) — ONE size's designs:
   the Design-Row atoms (preview · ref · version · dims · status ·
   contextual action: Add geometry / Confirm / Edit) · ghosts in place
   · piece-level acts labeled all-sizes · ← back to sizes
        │
        ▼   (later, separate)
CUTTING TABLE — consumes; never manages.
```

## Endorsing the owner's final recommendation

Agreed completely: **this is the last design round.** The remaining
insights (selection, placement, optimize feel) will come from USING
the software on the real T-SHIRT, not from more documents. Proposed
close-out: lock this workflow → implement it as **W2R (two pages,
one milestone)** → W3 as planned (General-size, perf, vocabulary, PDM
acceptance on the real product) → then the Cutting Table stage,
informed by real use.

**STOPPED — review only. On approval: implement W2R exactly as the
locked workflow above (no further design documents).**
