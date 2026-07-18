---
id: docs-ai-pattern-intelligence-product-integration-design
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PRODUCT INTEGRATION DESIGN — permanent (owner clarification, 2026-07-07)

**🔒 Permanent product-ownership ruling: Pattern Intelligence is NOT an
independent product. It is a helper tool of the Product Pattern Design
workflow. The Product remains the source of truth.**

## 1. The owning workflow

```
Product
  → Pattern Designs (production owns this)
    → Geometry            (created ONCE, in the layout tool)
      → Marker Generation (the tool)
        → Manual + AI Layout Optimization (the tool)
          → Save Marker   (the tool; verified, immutable)
            → Pattern Design Stage uses that saved marker (production)
              → Production
```

Pattern Intelligence only helps create and edit markers. It never owns
manufacturing state, never writes production tables, never runs its own
workflow. (This has been structurally true since ADR-H; it is now also
the PRODUCT framing.)

## 2. One entry point → straight into the editor (UX-simplified, 2026-07-07)

**The landing page is DROPPED** (owner UX review): the daily workflow is

```
Product → Pattern Design → [🧵 Open Layout Tool] → Layout Editor
```

- **The button** (production's Product Pattern Design page, management-
  gated, template-level URL composition — the ADR-H-safe pattern) points
  at **`/patterns/tool/<product>/`**, which is a SMART REDIRECT, not a
  page. **Deterministic priority (🔒 owner-locked, 2026-07-07):**
  | # | If … | Open … |
  |---|---|---|
  | 1 | an **Approved Production Layout** exists | that layout in the editor |
  | 2 | any saved layout exists | the latest saved layout in the editor |
  | 3 | confirmed geometry exists | the Generate Layout form (product pre-selected) |
  | 4 | pattern pieces exist | the Pattern Library (product-scoped) |
  | 5 | nothing yet | Register Pattern Piece |
  ("Approved Production Layout" = the ONE saved layout marked for
  production use — the Pattern Design Stage consumes it. Phase 6 defines
  the marking as a single "Approve for production" act on a saved
  layout, mapped onto the existing Marker container with its legacy
  benchmark gate simplified away — per the Legacy Code Report chain.)
- **Inside the editor**, one compact toolbar addition — a **"Layout ▾"
  switcher** ordered **by ROLE, not recency (🔒 owner-locked)**:
  1. the **current production layout** (when one exists, marked ★),
  2. the other saved layouts (drafts),
  3. **"＋ Generate New Layout"**.
  A select and a link — not tabs, not sections, not panels.
- **Geometry stays on its own pages** (library/capture/verify): it is a
  once-per-piece task and does not belong inside the daily editor;
  embedding it as tabs would bloat the editor for something done rarely.

Why this beats the landing page: the landing inserted a stop between the
button and the canvas for the most common case, and its three sections
merely duplicated pages that already exist. State-based routing does the
same job invisibly; the switcher covers moving between layouts without
leaving the canvas. The user never re-enters product/pieces/geometry —
**the Product supplies Product, Pattern Pieces, existing Geometry and
existing saved Markers**; the tool supplies editing and optimization.

## 2b. 🔒 Navigation rules C/D/E (owner-locked pre-M4, 2026-07-07)

**Rule C — Product Context Lock.** Opening the Layout Tool from a
Product LOCKS the product context. Inside the tool there is NEVER a
Product selector; everything belongs to ONE product. The user may
switch layouts / runs / drafts / the approved layout — never the
Product. Changing product = leave the tool, open another Product from
Production. (Compliance today: the editor is candidate-scoped with no
selector; the smart redirect is product-pinned. The shared
Generate/Library pages keep their standalone product filter ONLY for
entry via the tool's own home nav — they become context-locked as M5
reworks Generate prefills and M6 rebuilds the library into the Hub.)

**Rule D — Product Name Everywhere.** The editor header always shows
read-only context labels: **Product name · Current layout (★ when it is
the production layout) · Size ratio · Fabric width**. The user never
wonders which product is open. (Facts + derived-at-read only — no
schema.)

**Rule E — Smart Redirect Audit.** Every redirect decision is logged:
product, destination, reason (approved layout / latest layout /
generate / library / register), timestamp. Implementation = the
application log (`logger.info`, timestamped log records) — NOT a table:
no analytics, no reporting, nothing to prune, and the "M2 is the ONE
Phase-6 migration" promise stays intact. Grep the log to answer "why
did this product open here?".

## 2c. 🔒 Editor rules F/G/H/I (owner-locked pre-M5, 2026-07-07)

**Rule F — Layout switcher = version history, not navigation.** Order
always: **★ Approved Production Layout → drafts (newest first) →
＋ Generate New Layout**. Selecting a layout opens it immediately; the
ONLY confirmation is the document-editor prompt when unsaved editor
changes exist: *"Discard changes and open another layout?"*. Dirty =
any layout operation since load (history depth > 1) or an edited
width/height field.

**Rule G — Product defaults are only defaults.** The fabric profile
PREFILLS values for NEW work (the Generate form) and nothing else.
Opening a saved layout ALWAYS displays the values stored inside that
layout; changing the profile never modifies old layouts, approved
layouts, exports or generation history (Rule B made this structural;
Rule G adds the display law). Consequence: the editor's width/height
NEVER prefill from the profile — they are the layout's own facts. (This
consciously supersedes the execution plan's "prefill the editor" line.)

**Rule H — Editor always wins.** Generation produces a STARTING layout;
afterwards the editor is the source of truth. Width, spacing, moving,
rotating, locking stay manually editable; the tool NEVER auto-
regenerates — engines run only on the explicit Generate / Optimize
actions. The user is always in control.

**Rule I — No hidden work.** Switching layouts triggers NOTHING —
no generation, no optimization, no verification, no approval. Opening
another layout is a plain GET that loads another immutable saved
layout. (The switcher is literally a list of links.)

## 2d. 🔒 Hub rules J/K/L/M/N (owner-locked pre-M6, 2026-07-07)

**Primary goal:** the Pattern Design Hub = the SINGLE place a Product is
prepared before production. After M6 nobody asks "did I forget
something?" — the Hub answers it automatically.

**Rule J — Completion Dashboard.** One summary card on top: the
checklist (Sizes · Pattern Types · Required Pieces · Geometry ·
Confirmed · Grain · Fold Rules · Reference Images · Optional Pieces)
plus **Overall Readiness %** or **Production Ready ✅**. DERIVED ONLY —
readiness is never stored (F6).

**Rule K — Piece-first workflow.** The Hub guides: Piece → Size →
Geometry → Confirmation → Reference Image → Ready. Every piece card
carries its single NEXT STEP; the UI encourages finishing one piece
completely instead of hopping between pages.

**Rule L — Validation before Generation.** Every blocker appears BEFORE
Generate, named exactly ("Front Panel — missing XL geometry" · "Back
Panel — not confirmed" · "Pocket — missing reference image (warning)").
Blockers and warnings are visually distinct; Generate's honest refusal
stays as the backstop.

**Rule M — Reference Images.** Documentation only, displayed
beautifully: large preview, zoom, replace, remove. Never confused with
geometry capture — labeled display-only; the capture wizard stays the
only geometry door (extraction refuses the kind structurally).

**Rule N — Product Setup Experience.** A manager prepares a brand-new
product with zero training: the page itself is the guide (next steps,
exact missing lists, one collect-once surface).

**DEV-TEE = the permanent golden demo product**: every field populated
(all pieces, all sizes, reference images, optional Pocket, fabric
profile) — the standing regression dataset.

## 3. "Available back inside the Product page" — the honest boundary

Production pages cannot QUERY patterns_ai data (that would require a
reverse python import — permanently forbidden, test-walled). The
integration therefore works as: the Product page carries the ENTRY
BUTTON; everything marker-related lives one click behind it (usually the
editor itself), always product-scoped, always current. Saving a layout returns
the user to the saved layout inside the tool; the Product page's button
reaches it immediately. This is the permanent shape: **Product page =
the main source; Pattern Intelligence = the advanced editor behind one
button.**

## 3b. 🔒 The data grain: Pattern Designs = Product + Size (owner rule, 2026-07-07)

**The rule:** a Pattern Design never maps to a Product alone — it maps to
Product + Size. Every Pattern Type (Front Panel, Back Panel, Left
Sleeve…) carries its own Size-specific Pattern Design; geometry is
size-specific.

**Design review verdict: the built model ALREADY has this grain**
(ADR-D2, decided at Phase-1 entry and frozen since):

| Owner term | Built model |
|---|---|
| Pattern Type | `PatternPiece` (product-scoped identity: Front Panel of THIS product) |
| Pattern Design (per size) | a confirmed **`PieceSizeGeometry` row = (piece version × `ProductSize`)** — one canonical geometry per size, trust-graded |
| Product's size set | `production.ProductSize` (the per-product size chart — the FK target) |

**No schema change is required.** The rules that follow from the grain
are also already law: generation loads size-specific geometry
automatically from the ratio (`{Size: count}`), **never guesses a
missing design, never lets the user hand-pick pieces**, and refuses with
the exact missing list ("Front Panel / L — no geometry for this size").
Mixed production scenarios (single size · any subset · custom mix like
S×20 M×15 L×40 …) are the existing ratio input.

**One Phase-6 addition (design-level, from this rule):** the Generate
page shows a **readiness matrix** — Pattern Types × Sizes with
✓ confirmed / ✗ missing — so incompleteness is visible BEFORE the
Generate click (the click itself keeps its honest refusal as the
backstop). The smart redirect keeps its priority order; the matrix lives
where generation lives.

## 3c. 🔒 Collect-once law: the Pattern Design Hub (owner ruling, 2026-07-07)

**The Layout Tool never asks for product information. Everything the
tool will ever need is collected while defining the Product's Pattern
Designs — once.** The Layout Editor and Generate pages are pure
consumers.

**Where "the Product Pattern Design page" lives (boundary-honest):**
production python can never query patterns_ai (ADR-H, test-walled), so
the collection experience is the tool's own product-scoped **Pattern
Design Hub** — the existing pattern-library page upgraded — sitting ONE
click behind the production page's entry button (the smart redirect
already lands there whenever setup is incomplete). Two faces, one tool:
**Hub = collect once · Editor = consume only.**

**Field-by-field status vs the built model:**

| Owner field | Status | Home |
|---|---|---|
| Pattern Type | ✅ built | `PatternPiece` (product-scoped identity) |
| Size | ✅ built | `ProductSize` grain (ADR-D2) |
| Geometry | ✅ built | confirmed `PieceSizeGeometry` per size |
| Pattern Photos | ✅ built | mat-gated capture wizard |
| DXF | ✅ built | DXF-AAMA import per size |
| Grain Direction | ✅ built | mandatory at confirm (`features.grain`); invalid grain impossible |
| Fold information | ✅ built | `on_fold` flag (generation refuses honestly) |
| Mirror information | ✅ built | `is_pair` flag |
| Fabric Direction | ✅ built | the 0°/180° grain-along-lay law |
| Measurement Status | ✅ built | trust grades (measured / photo-calibrated / uncalibrated) |
| Geometry Status | ✅ built | version status + per-size rows |
| **Required / Optional** | ❌ **GAP** | Phase 6: `PatternPiece.is_optional` — optional pieces join a layout only when their designs exist for the requested sizes; missing OPTIONAL designs never block generation (they skip with an honest note); missing REQUIRED designs always block. (The DEV-TEE demo exposed this: Pocket blocked generation because today every piece is required.) |
| **Reference Images** | ❌ **GAP** | Phase 6: reference image per piece — display-only illustration (new `CaptureAsset.Kind.REFERENCE_IMAGE`, product-homed, piece-linked, NEVER a geometry source, no mat required, clearly labeled) |
| **Validation Status** | 🟡 partial | Phase 6: the readiness matrix grows into the Hub's **validation checklist** (below) + a product-level "Pattern Designs complete" banner |

**Hub validation checklist (§4 rules — detected BEFORE the editor):**
per piece × size: required pattern missing · geometry missing ·
geometry unconfirmed · DXF/photo source absent · reference image missing
(warning, not blocker) · wrong size mapping (structurally impossible —
FK to the product's own size chart) · invalid grain (structurally
impossible — confirm refuses without grain) · incomplete pattern set
(any required piece lacking any requested size). Blockers block
generation; warnings show honestly.

## 3d. Default Fabric Profile (owner §5 — Phase 6)

Per product, OPTIONAL defaults, collected in the Hub, editable
everywhere they prefill: **default fabric width · default layer length
(fabric height) · default piece spacing · default grain direction
(display: fixed 0°/180° law)**. New small patterns_ai-side model
(`ProductFabricProfile`, OneToOne → production Product — patterns_ai
owns it; production schema untouched; model pin 15→16, conscious).
Prefills the Generate form and the editor's width/height/spacing —
always editable at use.

## 3e. 🔒 Pattern-version ownership of layouts (review verdict: ALREADY GUARANTEED — documented)

Saved layouts are permanently tied to the exact Pattern Versions that
produced them, twice over:

1. **The layout carries its own geometry.** A saved layout stores the
   placed pieces as absolute polygon outlines inside its immutable
   payload — it never re-reads geometry at display/export time. A later
   Pattern Design version can never move a single point of an existing
   layout.
2. **The provenance spine names the exact sources.** Every layout's
   generation record snapshots the precise `geometry_row_id` +
   `version_id` per piece × size (and manual saves chain to their source
   layout), so any layout is reproducible and auditable down to the
   exact confirmed rows — which are themselves immutable (confirmed
   geometry can never be edited or deleted; PROTECT FKs).

New geometry versions therefore affect only FUTURE generations. Existing
layouts remain byte-stable forever. **No design change required.**

## 3f. Production Layout Summary (review addition — Phase 6, no schema)

When a layout is Approved for Production, Production must know its
numbers without manual calculation. All of them already exist as facts
or standing derivations:

| Value | Source |
|---|---|
| Fabric Width | the layout's stored width (fact) |
| Required Layer Length | the layout's verified length (fact) |
| Utilization / Waste | derived at read from the stored outlines (F6 — never stored) |
| Pattern Count | derived (pieces in the layout) |
| Size Ratio | the layout's stored ratio (fact) |

**Design ruling:** the Approve act surfaces these as the **Production
Layout Summary** — shown on the approved layout page AND baked into the
export package (the SVG/PDF/print artifacts carry a summary block, like
the Gate-1 print's header). Exports are derived artifacts, so printing
derived numbers into them is constitutional; the database still stores
only facts. Folded into Phase-6 items 4 (Approve) and the export items.

## 3g. 🔒 Production-layout safety (review verdict: ALREADY GUARANTEED — one detail locked)

A Production Layout can never silently change, structurally:

- **Every saved layout is immutable** (save/delete guards; editing NEVER
  mutates — the editor's Save always creates a NEW immutable layout).
- The owner's mandated flow is exactly what the pieces already do:
  `Production Layout → Open → Edit → Save (a new draft layout) →
  [explicit] Approve for Production → designation moves`.
- **Locked detail:** *Approve is its own explicit act, never bundled
  into Save.* Saving a draft NEVER touches the production designation;
  moving the designation is a separate click, audited (who/when), and
  the replaced production layout remains intact and reachable in the
  Layout switcher's saved list — full history, zero silent replacement.

## 3h. 🔒 Storage architecture — two models, locked (owner, 2026-07-07)

```
Product
├── ProductFabricProfile        (long-lived defaults ONLY)
│     default_width_mm · default_length_mm · default_spacing_mm ·
│     fabric_type · gsm · lay_mode
├── ProductionLayout            (the CURRENT designation ONLY)
│     approved_layout (PROTECT FK → immutable saved layout) ·
│     approved_by · approved_at
└── Saved Layouts               (immutable, append-only — unchanged)
```

Locked rules:
- **ProductFabricProfile NEVER references any layout.** Nothing
  layout-specific, approval-specific, or derived lives there.
- **ProductionLayout NEVER contains fabric defaults.** It owns only the
  designation; OneToOne(product) makes exactly-one structural.
- Replacing the approved layout **changes only the pointer** — no layout
  row is ever modified.
- **Approval history = the immutable saved layouts + the audit fields**,
  never layout mutation.
- One additive migration · no production data migration · fully
  reversible.

## 3i. 🔒 M3 frozen service contract (owner-approved review F-1..F-6 + Rules A/B, 2026-07-07)

**The single-writer API — FROZEN after M3 (no further architectural
changes without an approved review):**

```python
# fabric_profile_service.py — sole ProductFabricProfile writer
set_fabric_profile(*, user, product, default_width_mm=None,
                   default_length_mm=None, default_spacing_mm=None,
                   fabric_type='', gsm=None, lay_mode='') -> ProductFabricProfile

# production_layout_service.py — sole ProductionLayout writer
approve_production_layout(*, user, product, layout) -> ProductionLayout

# pattern_geometry_service.py — the existing PatternPiece writer gains
set_piece_optional(*, user, piece, is_optional) -> PatternPiece
set_reference_image(*, user, piece, asset) -> PatternPiece   # None clears

# marker_generation_service.py — RENAMED (frozen name):
resolve_generation_geometry(product, ratio) -> (payload, sources, warnings)
#   (was collect_confirmed_geometry — it resolves required validation,
#    optional skipping and warnings, not just collection)
```

**Rule A — approval eligibility (owner-locked).** Eligible = ALL of:
belongs to the supplied product · immutable saved layout (persisted
row) · `verification.ok == true` · exportable (non-empty placements).
No deleted/void state exists on saved layouts (append-only, never
deleted) — nothing to check there. Approval NEVER performs verification
itself; it validates eligibility and moves the pointer, nothing else.
Same-layout re-approve = strict no-op (first-approval audit preserved,
F-3); a different layout moves the pointer with fresh approved_by/at.

**Rule B — profile semantics (owner-locked).** Defaults ONLY, used to
prefill generation/editor values for NEW work. Changing the profile
never modifies existing layouts, approved layouts, generation runs,
saved markers or historical exports — historical data stays
byte-identical forever (test-asserted). Structural walls: the profile
module imports nothing layout-side; layouts/runs are immutable at the
model layer.

**Optional-piece law (rule 6, F-4).** Missing REQUIRED designs block
generation naming exactly what's missing (unchanged). Missing OPTIONAL
designs skip per **(piece, size)** with an honest warning line; warnings
return to the caller AND persist in `run.params['optional_skipped']`
(additive key; absent = nothing skipped) — a skip is never silent, even
historically. `on_fold` blocks regardless of optional (fold ≠ missing
design). All writers management-gated.

## 4. Geometry once, markers reused (workflow philosophy)

- Geometry is captured and confirmed ONCE per piece (new versions only
  for real shape changes — the copy-forward path already exists).
- Saved markers are REUSED; the normal daily flow never regenerates
  anything.
- Only when the user wants improvement do they reopen the layout editor
  (edit the saved layout, or generate fresh options and compare —
  Current Layout stays the honest baseline).
- The smart entry makes this the path of least resistance: the latest
  saved marker first, generation only when needed, geometry rarely.

## 5. What Phase 6 implements from this design

Per ROADMAP_V2 Phase 6 (Export & Production Ready) PLUS this ruling:
1. The **smart-redirect entry** `/patterns/tool/<product>/` (one thin
   view, no template) + the single button on the Product Pattern Design
   page (template-level, `is_management`-gated).
2. The **"Layout ▾" switcher + "＋ New options…" link** in the editor
   toolbar.
3. The Phase-6 export items (PDF · full-marker true-scale print · final
   validation) so the saved marker is production-usable.
4. The **"Approve for production" act** (one click on a saved layout;
   exactly one approved per product; explicit act separate from Save —
   §3g; surfaces the **Production Layout Summary** and stamps it into
   exports — §3f).
5. The **Pattern Design Hub** (§3c): library page upgraded into the
   collect-once surface — readiness/validation checklist (Types × Sizes),
   required/optional flag, reference images, completeness banner.
6. **`PatternPiece.is_optional`** + generation's optional-skip semantics
   (honest note when an optional piece is skipped).
7. **Reference images** (display-only kind, piece-linked, never geometry).
8. **`ProductFabricProfile`** defaults prefilling Generate + editor (§3d).
9. **BLF internal timebox** (demo finding F1) + documented engine
   envelope.
Nothing else. No landing page, no production-side data display, no
second entry points, no workflow ownership.

## 6. 🔒 Finality (owner ruling, 2026-07-07)

**Phase 6 is the FINAL implementation phase of PRODUCT_VISION_V2.**
After Phase 6: no Phase 7, no new roadmap, no future feature proposals,
no "next improvements", no AI expansion, no additional optimization
roadmap. The project is COMPLETE after Phase 6 unless the owner
explicitly requests new functionality later.
