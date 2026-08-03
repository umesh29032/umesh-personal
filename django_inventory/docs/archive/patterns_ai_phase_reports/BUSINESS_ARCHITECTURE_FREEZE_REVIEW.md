> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# BUSINESS ARCHITECTURE FREEZE REVIEW — Product-Size-centric manufacturing
(2026-07-08 · ARCHITECT REVIEW ONLY · no code · grounded in current models,
views, URLs, services — every claim checked against the repo this session)

Supersedes-and-extends: PRODUCT_SIZE_PATTERN_ARCHITECTURE_REVIEW.md (2026-07-08).
Companions: FINAL_ARCHITECTURE_REVIEW_PDM_CUTTING_TABLE.md · PATTERN_HIERARCHY_FREEZE_REVIEW.md.

---

## 0. Verdict

**The proposed architecture is internally consistent and freeze-able — with
one law made explicit, one ambiguity resolved, and six rulings recorded
(§7). No storage change is required. ~90% of the desired flow is already
built and tested (W2R/W2R2).**

The single most important sentence of this review:

> **"Size-first" is the correct BUSINESS and NAVIGATION hierarchy — and it
> must NOT become the STORAGE hierarchy.** Product Size owns its Pattern
> Designs *as a projection* (what the facade and the two PDM pages already
> do), not *as a foreign-key parent*. The moment storage is reorganized
> under ProductSize, the grading-family law breaks (§1). The architecture
> you described is exactly a navigation freeze over the existing storage —
> which is why it is safe.

## 1. The one law: business hierarchy ≠ storage hierarchy

Your hierarchy (Product → Sizes → each Size owns its Designs → Ready →
Cutting Table) is how the OWNER thinks and how every page must be
organized. Storage stays piece-rooted:

```
BUSINESS (navigation, pages, facade)        STORAGE (unchanged, frozen)
Product                                     Product
 └─ ProductSize  ◄— central object           ├─ ProductPatternAssignment (piece SET + counts, size-blind)
     └─ its Pattern Designs                  ├─ ProductSize (size chart)
         (projection: facade section)        └─ PatternPiece (identity, size-blind)
                                                 └─ PatternVersion (chain per PIECE)
                                                     └─ PieceSizeGeometry (× ProductSize)  ◄— "the Design"
```

Why storage must stay piece-rooted (all three already owner-frozen in the
hierarchy review, restated because this proposal tempts reversal):

1. **Grading family.** One version confirm covers the piece across ALL
   sizes (S/M/L/XL graded together — industry reality). If versions hung
   off ProductSize, confirming Front-M v3 while Front-L sits at v2 becomes
   representable — a state your factory never wants. The per-piece chain
   makes it *unrepresentable*.
2. **Provenance.** Approved layouts point at exact geometry rows; those
   chains are immutable. Re-parenting breaks every existing layout/export.
3. **Piece-level facts** (optional flag, pair/fold, reference image) are
   genuinely size-blind. Duplicating them per size = 4× copies + drift.

The facade (`pattern_design_facade.product_design_library`) is precisely
the adapter between the two hierarchies: storage in, size-first sections
out. **That adapter is the architectural centerpiece of your proposal —
and it exists, tested.**

## 2. Concept map — your terms → the models (exact)

| Your concept | Model(s) today | Size-aware? | Verdict |
|---|---|---|---|
| **Pattern Definition** (which pieces exist) | THREE entities: `ProductPattern` (global piece library) + `ProductPatternAssignment` (product ↔ pattern + `pieces_count`) + `patterns_ai.PatternPiece` (product-scoped identity + optional/pair/fold flags + reference) | ❌ size-blind | ✅ Correctly size-blind. Survives unchanged. The 3-way split is the messiest seam in the system — see ruling R1/R5 (§7). |
| **Pattern Design** (actual geometry) | `PieceSizeGeometry` (piece-version × `ProductSize`), status draft/confirmed | ✅ per-size | ✅ Already IS your "each Size owns its Designs". Zero change. |
| **Product Size** | `production.ProductSize` (code/label/display_order/is_active, unique (product,code)) | — | ✅ Central business object — as NAVIGATION KEY. Ownership unchanged (§3.4). |
| **Size Ready** | facade verdict: ALL REQUIRED pieces confirmed for that size (optional never blocks) | per-size | ✅ Built + tested (W2R law). |
| **Product Ready** | — (does not exist as a stored state) | — | 🟡 Ambiguous in your flow — resolved in §5. |
| **Pattern Manager / Preparing Size** | `piece_list.html` / `size_library.html` (W2R/W2R2) | — | ✅ Built exactly as described. |
| **Cutting Table** | future stage (4-state model locked) | — | Consumes the same facade. Unchanged by this proposal. |
| **Approved Layout** | `ProductionLayout` (★ designation, immutable saved layouts, provenance to designs) | per-ratio | ✅ Exists. Multi-Adda question deferred (§6). |

**Your "do NOT merge the two concepts" instruction is already satisfied by
the schema.** Definition = assignment+piece (size-blind). Design =
geometry (per-size). Nothing in the codebase confuses them; the only
place they *visually* mix is the old `ProductPatternsEditView` page —
a UI problem (§3, "what moves"), not a data problem.

## 3. Direct answers

### 3.1 What SURVIVES (unchanged)
- All storage: `Product`, `ProductSize`, `ProductPattern`,
  `ProductPatternAssignment`, `PatternPiece`, versions,
  `PieceSizeGeometry`, `ProductFabricProfile`, `ProductionLayout`,
  saved layouts/exports, `CuttingPatternRecord`/`SizeAllocation`/
  `Verification`, `AddaProductSizeColorPieceBreakdown`.
- All frozen single-writer services + the read-only facade + ADR-H wall
  (production never imports patterns_ai; URL-only hand-offs).
- Edit / Flow / Sizes / Archive actions — exactly as you specified.
- The two PDM pages (Manager, Preparing Size), verdict law, CT gate,
  Design-Row atom, buckets, checks.

### 3.2 What CHANGES (UI/navigation only)
- **Patterns action** = Product Pattern Manager as its primary surface
  (today: one hand-off button on the old assignment page — one hop too
  many for "Patterns IS the Manager").
- The assignment/counts editor **moves INTO the Manager** as a small
  product-level "Pattern Definition" section (which pieces + counts) —
  the split becomes visible page structure: definition at top
  (product-level), size cards below (per-size design prep). One entry,
  two honest layers.
- Universal-size convention (§4) — one service rule + one guard.

### 3.3 What becomes OBSOLETE
- `ProductPatternsEditView` as a **standalone destination** (its content
  moves; the view/route can stay during transition). Nothing else. No
  model, no service, no migration becomes obsolete. The standalone
  Generate page was already declared temporary (pre-W1 clarification) —
  unchanged by this.

### 3.4 The five specific questions

**ProductPatternAssignment — survives? YES, unconditionally (for now).**
Verified consumers today:
1. **Marker generation** — `marker_generation_service.py:95`:
   `qty = int(count) * (2 if piece.is_pair else 1)` — `pieces_count` is
   the "how many of this piece per garment" truth the nest engine cuts by.
   Delete it and generation breaks.
2. **Adda cutting checklist** — `CuttingPatternVerification` is one-per-
   assignment (unique (record, assignment)). Historic verifications FK it.
3. **Registration gate** — `create_piece` requires the assignment.

Long-term (post-Adda-refactor, your own future direction) its checklist
role transfers to Approved Layouts, but the **per-garment count** truth
has no other home. Verdict: survives; role narrows; revisit ONLY at the
Adda refactor; **never make it per-size** (an S and an XL t-shirt need
the same 1 Front + 1 Back + 2 Sleeves — only shape differs; per-size
counts = 4× duplication + drift; a "pocket only on L/XL" case is the
OPTIONAL flag + per-size geometry presence, already supported).

**PatternPiece ownership — changes? NO.** Stays product-scoped,
size-blind. It IS your "Pattern Definition" leaf on the PDM side.
Piece-level flags + reference stay piece-level (shown per row — frozen
hierarchy rule). Re-parenting under ProductSize would break §1.

**PieceSizeGeometry — changes? NO.** It already IS the per-size Pattern
Design. Bonus already in place: `size` FK is `on_delete=PROTECT`
(ADR-D2) — a size holding designs can never be hard-deleted at DB level.

**ProductSize ownership — changes? NO.** production owns it (it predates
patterns_ai: cutting allocations + APSCPB already FK it). Sizes CRUD
(`ProductSizesEditView`) stays the ONLY write surface for the size set;
patterns_ai only reads + FKs. The "+ Add Size" hand-off boundary is
already correct. Making ProductSize "central" = navigation centrality,
not ownership transfer.

**Adda Pattern Stage — how affected?** Your three-layer target
(prepare → compose → manufacture) is consistent and the seams for it
already exist:
- Approved layouts are immutable with provenance to confirmed designs ✓
- The facade is the ADR-H-legal read path for any future production
  consumer ✓
- `AddaProductSizeColorPieceBreakdown` is already per-size — the natural
  join between "designs per size" and "verified pieces per size" ✓

What the refactor will change (later, not now): checklist source
(assignment → the chosen approved layout's designs), verification
meaning ("these confirmed designs are what we cut"), and size
proportions (see §6 — the layout's ratio should become the truth
`CuttingPatternSizeAllocation` derives from, not a second hand-entry).
Correctly sequenced AFTER product-side freeze. Nothing decided today
constrains it badly.

**Scales for future manufacturing? YES.** Sizes per product stay ≤ ~dozen
(cards page never explodes); library page = piece count for one size
(bounded); the facade is one supplier for Manager/Library/CT/future Adda
(one contract to maintain); multi-factory/growth locks (ADR-0010)
untouched; money boundary untouched (nothing here writes money). Layout
volume growth (many ratios × products) is a CT-stage listing concern,
already noted there.

## 4. Universal size — ruling on your rule

**Architecturally correct**, with three precisions:

1. **Universal = a real `ProductSize` row** (`code='universal'`), not a
   nullable-size special case. Every FK (geometry, allocations, APSCPB)
   keeps working; zero schema change. Nullable-size would fork every
   consumer with `if size is None` — reject.
2. **Materialize lazily** at first pattern-prep need, not at product
   create. Recommended because: (a) no backfill data-migration over
   existing products; (b) products that never use PDM don't grow a
   phantom size; (c) the invariant becomes "a product entering pattern
   preparation always has ≥1 active size" — which is the statement your
   business needs. (Alternative — create at product-create + backfill
   all — is defensible but pays migration cost for no operator benefit.)
3. **Archive guard is mandatory and must be service-level.** DB PROTECT
   only blocks hard DELETE; `is_active=False` soft-archive has no
   backstop. Rule: refuse archiving ANY size (Universal included) while
   it holds confirmed designs and no other active size has confirmed
   designs — else the product's only design set silently vanishes from
   every surface. Honest paths: block-with-reason, or offer copy-to-new-
   sizes as explicit migration.

## 5. The one internal inconsistency found (resolve before freeze)

Your flow reads: *"Each Size becomes Ready → Product becomes Ready →
Cutting Table."* Read literally = ALL sizes must be Ready before the CT
opens. But your own locked rule (W2R, tested) = **CT gate enables at
≥1 Ready size** — and that is the correct one (a factory cuts Size M
markers while XL designs are still in prep; all-sizes gating would block
real work for no safety gain).

**Resolution to write into the freeze:** CT gate = ≥1 Ready size
(unchanged, locked). "Product Ready" = ALL active sizes Ready — a
**reporting badge** (product list / Manager header), never a gate.
Two different statements; the flow diagram should show the badge as a
side-fact, not a step.

## 6. Deferred-consciously (freeze must restate, not resolve)

- **Single-★ vs multi-Adda:** one product has exactly ONE ★ production
  layout (Phase-6 lock), but different Addas may need different
  ratios/layouts. The Adda refactor will need "Adda chooses which
  approved layout" — which reopens D-7 (approval history) and possibly
  the exactly-one-★ rule. Biggest known future decision. Correctly NOT
  decided now; must be first item on the Adda-refactor agenda.
- **`proportion_pct` duplication:** today the operator hand-enters size
  proportions at the Adda stage; an approved layout already encodes a
  ratio. Post-refactor, one of them must become derived — else two
  places state the size mix. Flagged, deferred.
- **S6** (reported_quantity retirement) and all frozen-foundation locks —
  untouched by this proposal.

## 7. Rulings needed to freeze (the "still missing" list)

| # | Ruling | Recommendation |
|---|---|---|
| **R1** | **Definition-count convention.** Nothing enforces `pieces_count` ↔ PatternPiece identities agree. "Sleeve" can be: assignment ×2 + one piece `is_pair=True`, or ×1+×1 as Left/Right pieces (real T-SHIRT uses Left/Right). Both work; MIXING them within one product makes generation qty and checklists lie. | Freeze ONE canonical convention for new products — recommend **pair-piece (`is_pair=True`, count 1)** for mirror pairs, separate pieces only when left≠right geometry truly differs — and show a reconciliation line in the Manager's definition section ("definition says N pieces/garment; designs registered: M"). |
| **R2** | **Patterns action destination.** | Points at Pattern Manager; counts editor folds in as the product-level "Pattern Definition" section (§3.2). Old page retires as standalone. |
| **R3** | **Universal materialization moment.** | Lazy, at first pattern-prep need (§4). |
| **R4** | **"Product Ready" semantics.** | Badge = all active sizes Ready; gate stays ≥1 (§5). |
| **R5** | **Registration friction.** Adding one new piece today = 3 writes (library `ProductPattern` → assignment → `create_piece`). Architecture is fine; operator experience is not. | Bless ONE "Add Pattern Definition" action performing all three atomically (service composition — no schema change). Implementation detail, but freeze should name it so nobody "fixes" it by merging models instead. |
| **R6** | **Deferred register.** | Freeze text restates §6 items as OPEN, owned by the Adda-refactor stage. |

## 8. Freeze statement (draft — becomes binding on your confirmation)

1. Product Size = the central BUSINESS object; all pattern navigation is
   size-first. Storage stays piece-rooted; the read-only facade is the
   sole adapter between the two hierarchies.
2. Pattern Definition (size-blind: ProductPattern + assignment + piece)
   and Pattern Design (per-size: confirmed geometry) are permanently
   separate concepts. `pieces_count` never becomes per-size.
3. Product actions: Edit (details) · Flow (unchanged) · Sizes (the ONLY
   size-set write surface) · Patterns (= Pattern Manager: definition
   section + size verdict cards) · Archive.
4. Preparing Size ⟨X⟩ = complete source of truth for that size's designs
   (rows: geometry/reference/dims/area/preview/version/status/DXF/
   checks/actions).
5. Every product entering pattern preparation has ≥1 active size;
   Universal materializes lazily; size-archive guard protects the last
   design-holding size.
6. CT gate = ≥1 Ready size; Product-Ready = all-sizes badge, reporting
   only.
7. Manager prepares · Cutting Table composes · Adda Stage manufactures —
   three layers; Adda's future input = Approved Layouts via the facade,
   never `ProductPatternAssignment` directly and never a python import
   across ADR-H.
8. Open items (single-★/multi-Adda, proportion derivation, D-7) belong
   to the Adda-refactor stage — R6 register.

---
**STOPPED — review only, no code. Awaiting: your rulings on R1–R6 (or
accept recommendations as written), then the freeze becomes permanent
and implementation planning can begin on request.**
