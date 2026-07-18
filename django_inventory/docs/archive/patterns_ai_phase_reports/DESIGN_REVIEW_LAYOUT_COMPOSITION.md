> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DESIGN REVIEW — Layout Composition & Operator Control
(2026-07-07 · acceptance-validation discussion document · REVIEW ONLY —
nothing implemented; freeze intact. Scope strictly: Product → Size →
Pattern Design → Layout Tool. Production stages / rib / accessories:
intentionally NOT discussed here.)

Evidence base: the executed acceptance run on the real `T-SHIRT`
product (runs 11–16, layouts #16–#22, ★ #22), the H-6 multiset probe,
and the Visual Pattern Management review (V-1..V-6).

---

## 1. The hierarchy under review — verdict: SOUND

```
Product ──▶ Product Size ──▶ Pattern Piece
                                 │
                    Pattern Design = Piece × Size
                    (geometry · reference image · dimensions · version)
                                 │
                             Layout Tool
```

Validated end-to-end on real data: every size owns its own Pattern
Design; every design owns its own confirmed geometry (MEASURED, tape-
gated); mixed ratios pulled exactly the right per-size outlines
(grading visibly different S vs XL). **The hierarchy is correct and
nothing in this review questions it.**

## 2. How composition ACTUALLY works today (as-built truth)

The operator's control over "which Pattern Designs participate" exists
at exactly ONE moment, with exactly ONE lever:

| Phase | Control | Granularity |
|---|---|---|
| Generate | the size RATIO (`S×1 M×2 …`) | garments per size — never per design |
| (implicit) | data availability | a design participates iff its geometry is confirmed for a requested size; incomplete OPTIONAL designs skip with a recorded note; incomplete REQUIRED designs block |
| Editor | NONE over composition | arrange-only: move / rotate 180° / lock; the save door **refuses any add or remove** ("the layout must contain exactly the source candidate's pieces" — verified live, H-6) |
| Undo | transforms only | there is nothing compositional to undo |

This is not an accident — it is the immutability chain doing its job:
composition fixed at generation ⇒ every layout is reproducible from
its run's provenance spine ⇒ one verifier covers everything ⇒ saved
layouts are evidence-grade. The trade-off it buys is exactly the gap
the owner is now probing.

## 3. The owner's five operator questions, answered against as-built

| Operator should understand… | Today | Where/why |
|---|---|---|
| which Pattern Designs are AVAILABLE | ✅ before the tool (Hub matrix, Generate-page readiness matrix) · ❌ inside the editor | availability is a Hub concept; the editor never shows it |
| which are ALREADY IN the layout | 🟡 the canvas itself + hover titles; ratio chip in the strip | no readable list (V-2); counts per piece×size not shown anywhere |
| which are NOT part of the layout | ❌ | skipped-optional record persists in the run but is displayed nowhere post-generation (V-1); available-but-not-included is not even derivable on the layout pages |
| how composition CHANGES while editing | N/A — composition CANNOT change while editing (by design, multiset law) | the honest answer to give an operator is "it doesn't — arrange only"; today nothing on screen says that |
| does undo move items back to an available list | N/A — no composition ops, so undo correctly covers transforms only | if composition ops ever exist, undo MUST cover them (design note DN-1) |

**Summary: the owner's mental model is an interactive composition
palette ("available designs ⇄ layout"). The built tool is a two-phase
model ("compose by ratio at Generate → arrange in the editor").** The
two agree on outcomes only when the ratio+availability lever happens to
express the operator's intent — the acceptance run proved that staging
data availability can emulate intent (Markers A/B/C), and also proved
how unnatural that emulation is once data is complete.

## 4. Visual validation — the 7 per-design facts, in the layout context

For a design sitting inside a layout, can the operator immediately see:

| Fact | In the editor | Notes |
|---|---|---|
| Product | ✅ context strip (Rule D) | |
| Size | 🟡 hover title only (`Front Panel·l #2`) | no size legend/colour key; no filter "show all L pieces" |
| Pattern Piece | 🟡 hover title only | print/PDF tiles DO print centroid labels; the editor has no persistent-label toggle |
| Geometry preview | ✅ the canvas IS the true shape | |
| Reference image | ❌ | lives in the Hub only (per piece) |
| Dimensions | ❌ | tape W×H lives at version depth (V-4); editor shows only live layout metrics |
| Confirmation status | ✅ *by construction* | a placed design is ALWAYS confirmed geometry (provenance law) — displaying a status in-editor would be noise; worth stating in UI copy, not adding a badge |

## 5. Workflow gaps (WG register — discussion inputs)

- **WG-1 (central).** No per-design participation control at layout
  level. The ratio is the only lever, and it is garment-grained.
  "Make this marker without Pocket" (while Pocket geometry exists) is
  inexpressible. Same root as acceptance §8.3 Path-2 — now framed
  in-scope as *layout-tool composition control*.
- **WG-2.** Composition is invisible after generation: no
  Included/Skipped/Available-not-included view on run, layout or
  editor surfaces (V-1, V-2). The data for all three already exists or
  is derivable read-only.
- **WG-3.** No composition ops in the editor: cannot add one more
  `Pocket·M` instance to fill a visible gap, cannot drop one `XL`
  garment's pieces — the only path is regenerate-with-new-ratio, which
  discards manual arrangement work.
- **WG-4.** Ratio is garment-level only: piece-level quantities
  ("2 extra M Front Panels for re-cut allowance") cannot be requested.
  Fine for standard garment markers; blocks fill/remnant markers.
- **WG-5 / DN-1 (design note).** Undo today = transforms only —
  correct. Any future composition ops must enter the same undo stack
  and the same verifier, or the editor's honesty rules break.

## 6. UX gaps (UX register — layout-tool specific; V-1..V-6 incorporated)

- UX-1: editor lacks a **layout-contents list** (piece × size × count)
  — the single change that would answer three of the owner's five
  questions at once (read-only, derivable from placements).
- UX-2: **skipped record invisible** post-generation (V-1) — surfacing
  the already-persisted `optional_skipped` on run + layout pages
  closes it.
- UX-3: no size legend / per-size highlight in the editor; colours are
  per-key but never explained.
- UX-4: no persistent piece labels in the editor (hover-only); the
  exports already print labels — inconsistency between screen and
  paper.
- UX-5: dims/reference/status at depth (V-3/V-4) — a hover card or
  side panel per selected piece (tape W×H · version · ref thumb) would
  bring the version page's excellence into the tool.
- UX-6: nothing tells the operator "this editor arranges; composition
  was decided at Generate" — one sentence of UI copy prevents the
  wrong mental model from forming.

## 7. Missing validation scenarios (to add to the acceptance plan when the owner decides)

- MV-1 (runnable today): "composition change = regenerate" workaround
  path as an explicit scenario — adjust ratio → regenerate → compare
  layouts; assert manual-arrangement loss is understood.
- MV-2 (runnable today): layout-contents cross-check — placements
  grouped by piece×size must equal ratio × pieces-count (this run
  validated it by hand; make it a scripted assertion).
- MV-3 (blocked until a decision): available ⇄ layout add/remove/undo
  cycles — cannot be validated because the capability does not exist;
  listed so the gap is explicit, not forgotten.
- MV-4 (blocked): per-design include/exclude at Generate — Path-2
  scenarios from the acceptance plan §8.4 (selected-but-missing,
  excluded-though-available).

## 8. Improvements — ONLY within Product → Size → Pattern Design → Layout Tool (design-only, owner decides)

Ordered smallest-first; each subsumes nothing above it.

- **S-1 · Layout Composition Panel (read-only).** On editor + layout +
  run pages: **Included** (piece × size × count, from placements) ·
  **Skipped** (the persisted record) · **Available but not included**
  (derived from confirmed designs vs placements). Zero architecture
  change, zero writes, freeze-compatible in spirit — answers owner
  bullets 1–3 and V-1/V-2/UX-1/UX-2/UX-6.
- **S-2 · Composition preview at Generate.** The same list BEFORE the
  run (a dry resolver read): "this ratio will include … / skip …" —
  turns the post-hoc record into a pre-decision view.
- **S-3 · Per-run participation control at Generate.** Checkboxes over
  the product's OPTIONAL pieces (required pieces not deselectable —
  keeps the required-blocks law intact). This is the §8.3 Path-2
  decision expressed inside the current tool; implications if chosen:
  resolver gains a participation argument, the run's provenance
  records the selection, refusal/skip wording extends. Smallest change
  that gives the operator real intent-level control.
- **S-4 · Editor composition ops (add/remove design instances).** The
  full palette model (available ⇄ layout, undo-aware). HEAVY: breaks
  the exactly-the-source-pieces law, so save-verification, provenance
  and undo semantics all extend. Recommendation: only if factory
  evidence AFTER S-1..S-3 shows arrangement-preserving composition
  edits are truly needed.
- **S-5 · Editor visibility niceties.** Size legend + highlight-by-
  size, persistent-label toggle, selected-piece info card (dims ·
  version · reference thumb). Pure display (UX-3/4/5, V-3/V-4).

**Recommended decision order: S-1 + S-2 (pure display) → S-3 (the real
operator-control question) → S-5 → S-4 only with evidence.** No
recommendation here is an implementation request.

## 9. What is already RIGHT and must not be lost

Whatever the owner decides, these validated properties are the tool's
spine and every option above was framed to preserve them: immutable
saved layouts · composition provenance in the run · one verifier ·
required-designs-block law · honest named skips · approve = explicit
audited pointer move · derived-at-read metrics.

**STOPPED — design review only. Nothing implemented, nothing changed.
Awaiting the owner's decisions on S-1…S-5 (and the standing acceptance
sign-off).**
