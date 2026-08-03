> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# REVIEW — Product → Sizes → Patterns architecture + Adda pattern-stage dependency
(2026-07-08 · REVIEW ONLY, no code. Grounded in the CURRENT models.)

## 0. The one finding that matters

Your product already has **two different "pattern" representations**, and
they disagree about the size dimension. Your sentence "each product size
has its own product pattern" is **already true for ONE of them and
should NOT become true for the other.** Untangling this is the whole
review.

| Concept | Model (today) | Size-aware? | Should it be per-size? |
|---|---|---|---|
| **Pattern SET + counts** — which pieces a garment needs, how many each | `ProductPatternAssignment` (product ↔ ProductPattern, `pieces_count`) — drives the cutting checklist | ❌ size-blind | **NO** — an S t-shirt and an XL t-shirt both need 1 Front + 1 Back + 2 Sleeve. Only the SHAPE differs by size, not the count. |
| **Pattern DESIGN / geometry** — the actual outline of each piece for each size | `patterns_ai.PieceSizeGeometry` (piece-version × `ProductSize`) — the "Pattern Design" the whole PDM is built on | ✅ per-size | **YES — already is.** |

So the "each size has its own pattern" you see on screen = the
**DESIGN** (geometry), which the PDM already does right (S Front ≠ XL
Front, per-size confirmed geometry). The **counts** are product-level
and duplicating them per size would copy identical data 4× and invite
drift. **Keep counts product-level; keep designs per-size.** They are
different questions, not one.

## 1. What exists today (ground truth)

```
Product
├── patterns  (M2M through ProductPatternAssignment: pattern + pieces_count)   ← SIZE-BLIND set/counts
├── sizes     (ProductSize: code · label · display_order · is_active)          ← per-product chart, exists
└── (patterns_ai) PatternPiece → versions → PieceSizeGeometry(× ProductSize)   ← per-size DESIGNS (PDM)
```

Product-list row actions (`/production/products/`):
- **Edit** → `product-update` (name/description; code locked once Addas exist).
- **Flow** → `product-flow` (workflow stages — untouched, keep).
- **Patterns** → `product-patterns` = `ProductPatternsEditView` — the
  **size-blind assignment editor** (add pattern + pieces_count).
- **Sizes** → `product-sizes` = `ProductSizesEditView` (super-admin) —
  the size chart CRUD (already exists).
- **Archive** → soft archive (`is_active`).

Adda pattern-design stage (the downstream consumer, refactor deferred):
`cutting_pattern` stage → `CuttingPatternRecord` →
`CuttingPatternSizeAllocation` (operator sets proportion % per size,
sum=100) + `CuttingPatternVerification` (one per
`ProductPatternAssignment` — the checklist). Then cutting →
`AddaProductSizeColorPieceBreakdown` (verified per-(size,color) counts).
**The stage reads the size-blind assignment checklist today; it does
NOT read the per-size PDM designs at all.** That gap is §4.

## 2. Your requested changes → mapped to as-built (what's real work vs already-there)

| Your ask | Verdict |
|---|---|
| CRUD to add Product Sizes | ✅ EXISTS (`product-sizes` / `ProductSizesEditView`). Needs only UX polish, not new architecture. |
| product → sizes → "each size has its own patterns" | 🟡 As DESIGNS: already exists (PDM per-size geometry). As a size-tabbed VIEW on the Patterns page: NEW UI over existing data (the PDM Manager I just built is exactly this — size cards → per-size library). |
| Patterns page = size tabs + CRUD of pattern details | 🟡 The **PDM Manager/Library** (just built) IS this, sitting in patterns_ai. Decision needed: does the production **Patterns** button open the assignment editor (counts) or hand off to the PDM (designs)? — §3. |
| Universal default size when a product has none | 🟢 NEW small convention: a real `ProductSize(code='universal')` auto-created at first need. This is the "General" convention from the earlier hierarchy review — same idea. Uses existing `is_active` to archive it. |
| Archive Universal, then add real sizes | ✅ `ProductSize.is_active` soft-archive already supports it (one guard needed: §3 rule). |
| Patterns → Pattern Management → Cutting Table buttons | ✅ chain already built (production Patterns button → Pattern Manager → gated Open Cutting Table). |
| Flow unchanged | ✅ leave `product-flow` alone. |

**Net: almost nothing here is new data architecture. It is (a) a UI
rework of the Patterns entry to be size-first, (b) the Universal-size
convention, (c) one decision about counts-vs-designs ownership.**

## 3. Recommended target — WITHOUT breaking the size-blind/per-size split

```
Product
 ├── Edit    → product details (unchanged)
 ├── Flow    → workflow stages (unchanged)
 ├── Sizes   → ProductSize CRUD  ← the size chart lives here (source of truth for sizes)
 └── Patterns→ TWO honest layers, not one page pretending to be both:
        (A) Pattern SET   — which pieces + pieces_count   (ProductPatternAssignment; product-level)
        (B) Pattern DESIGNS — per-size geometry per piece  (the PDM Manager, size-first)
```

- **Patterns button** should open the **PDM Pattern Manager** (the
  size-first page just built) as the primary surface — because that's
  where the operator thinks "prepare each size". The pattern SET/counts
  editor (A) becomes a small section INSIDE it ("which pieces this
  product has") rather than a separate competing page. One entry, two
  honest layers.
- **Universal size rule (the one new invariant):** a product with zero
  active sizes is treated as having a single implicit **Universal**
  size; the first time designs/patterns are prepared, materialize a
  real `ProductSize(code='universal', label='Universal')`. When the
  owner adds real sizes, they may archive Universal — **guard:** refuse
  archiving Universal while it still holds confirmed designs AND no
  other active size has them (else the product silently loses its only
  design set). Offer "copy Universal designs into the new sizes" as the
  honest migration, or block with the reason.
- **Sizes CRUD stays the source of truth for the size set**; the
  Patterns page consumes it (size tabs = the active ProductSizes). "+
  Add Size" on the Manager already hands off here — keep that boundary.

This keeps: counts product-level (no duplication), designs per-size
(already right), sizes owned in one place (ProductSize), and the PDM as
the single design-truth surface (the frozen boundary).

## 4. Dependency on the Adda pattern-design stage (the refactor you flagged for later)

Today the `cutting_pattern` Adda stage reads the **size-blind
assignment checklist** (`ProductPatternAssignment` →
`CuttingPatternVerification`) and the operator hand-enters a per-size
**proportion %** (`CuttingPatternSizeAllocation`). It never sees the
per-size PDM designs.

Once product patterns are canonical (this review's target), the Adda
stage SHOULD change so that:
- its checklist = "the confirmed Pattern DESIGNS for the sizes in this
  Adda's size allocation" (consume PDM `PieceSizeGeometry`), not a bare
  size-blind list;
- verification means "these confirmed designs are what we cut" — richer
  than the current tick-per-assignment;
- `AddaProductSizeColorPieceBreakdown` (already per-size) becomes the
  natural join point — the Adda's verified per-size counts line up with
  the per-size designs.

**But that Adda-stage refactor is downstream and correctly deferred**
until this product-side architecture is fixed and frozen — exactly your
sequencing. It also crosses the ADR-H boundary (production reading
patterns_ai is forbidden), so the Adda stage would consume PDM designs
through the same **read-only facade** the Cutting Table uses (the facade
already exists — built in PDM W1). That is the clean seam; nothing about
it needs deciding now beyond noting it.

## 5. Risks / cautions if you build the target

- **Do NOT make `pieces_count` per-size.** It is the one tempting wrong
  move — it duplicates identical data per size and desyncs the moment a
  count changes. If a real product ever needs different piece counts per
  size (rare — e.g. a pocket only on L/XL), model that as the piece's
  **optional/required per size** (the PDM already has `is_optional` +
  per-size geometry presence), not as per-size counts.
- **Universal archiving** must be guarded (§3) or a product loses its
  designs silently.
- **Two edit surfaces for "patterns"** (assignment counts vs PDM
  designs) will confuse operators if both stay top-level — fold counts
  INTO the Manager (§3).
- **ADR-H**: any production page showing PDM data does it via template
  URL + the read-only facade, never a python import (the wall is
  test-enforced).

## 6. Answer to "you write the code?"

Your message opened with "you write the code??" but closed with
"review only … read current and what I want to improve." **I treated
this as review-only and wrote nothing.** If you want implementation
next, the smallest correct first step (no new data model) is: **point
the production Patterns button at the PDM Pattern Manager, fold the
assignment/counts editor into it as a section, and add the Universal-
size convention + its archive guard.** Say the word and I'll turn that
into a milestone plan (same discipline: plan → approve → build one →
stop). The Adda pattern-stage refactor stays a separate later stage.

**STOPPED — review delivered. No code written. Awaiting your call:
approve this target + Universal rule, or adjust, before any plan.**
