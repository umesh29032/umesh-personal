> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PRODUCT PATTERN WORKSPACE — Design (PDM stage)
(2026-07-07 · DESIGN document — no code yet. The architecture is
FROZEN per the owner's direction lock; this document designs the
operator experience only. Rib / stages / accessories / fabric groups /
D-7 approval history: postponed by owner, not mentioned again.)

**Locked foundations this design builds on:** hierarchy Product →
Sizes → Pattern Design Library → Cutting Table → Saved Layouts →
Production Layout → Export · Option A (the Hub EVOLVES into this
Workspace) · the Cutting Table only CONSUMES the library · four-state
composition (designed later, at CT stage) · AI = assistant.

---

## 1. Identity & entry

- **Name everywhere: "Product Pattern Workspace"** (short: the
  Workspace). The word "workspace" is retired from the layout editor's
  visible language (the editor becomes "Cutting Table" vocabulary at CT
  stage; until then its title stays "Layout editor").
- Entry stays Option-A-shaped: the production page
  `/production/products/<id>/patterns/` keeps pattern ASSIGNMENTS
  (production truth) and carries one prominent button — **"🧵 Open
  Pattern Workspace"** — into the evolved Hub (product-pinned, Rule C).
  The smart redirect's incomplete-setup branches also land here.
- One product = one Workspace. No product switcher inside (Rule C);
  the no-product URL keeps the existing chooser.

## 2. Page architecture — the owner's vertical flow, made concrete

```
┌─ PRODUCT SUMMARY ────────────────────────────────────────────────┐
│ T-Shirt (T-SHIRT)                      92% · In preparation ⚠    │
│ 4 sizes · 8 pattern types · 30/32 designs confirmed              │
│ Fabric defaults: 1700 mm · jersey · 3.0 mm   [edit defaults]     │
│ ▸ details (readiness checklist · blockers · warnings)            │
│                                   [🪡 Open Cutting Table]        │
└──────────────────────────────────────────────────────────────────┘
┌─ SIZES ──────────────────────────────────────────────────────────┐
│  [S 8/8 ✓] [M 8/8 ✓] [L 7/8 ⚠] [XL 7/8 ⚠]        [matrix view]  │
└──────────────────────────────────────────────────────────────────┘
┌─ PATTERN DESIGNS · S ── 8/8 confirmed ✓ ────────────── collapse ─┐
│ ┌────────┬────────┬──────────────────────────────────────────┐   │
│ │[shape] │[photo] │ Front Panel · S        v1 · Confirmed ✓  │   │
│ │preview │ ref    │ 480 × 660 mm (tape-accepted)   [Edit →]  │   │
│ ├────────┼────────┼──────────────────────────────────────────┤   │
│ │[shape] │[photo] │ Neck Rib · S   optional  v1 · Confirmed ✓│   │
│ │        │        │ 420 × 70 mm                    [Edit →]  │   │
│ └────────┴────────┴──────────────────────────────────────────┘   │
├─ PATTERN DESIGNS · L ── 7/8 · 1 missing ⚠ ───────────────────────┤
│ │[ghost] │  —    │ Care Label · L      NO DESIGN YET          │  │
│ │ dashed │       │ required for L markers   [+ Add geometry]  │  │
└──────────────────────────────────────────────────────────────────┘
┌─ LAYOUTS ────────────────────────────────────────────────────────┐
│ ★ Production: Layout #22 · 1700 mm · 4006 mm · 75.1%  [open]     │
│ Saved: #21 · #20 · #19 … (grouped, collapsible)      [all →]     │
└──────────────────────────────────────────────────────────────────┘
   Register piece · Calibration mats                      (footer)
```

### 2.1 Product Summary (the owner's first glance)
- Name/code · readiness % + Ready/In-preparation badge · counts
  (sizes · pattern types · designs confirmed/total) · fabric defaults
  one-liner with edit.
- The Rule-J checklist and the blockers/warnings panels are NOT lost —
  they live under the "▸ details" expander (summary-first; the % and
  badge carry the headline, the expander carries the proof).
- **Open Cutting Table** is the section's primary action. Until the CT
  stage ships, this button = today's "Open Layout Tool" behaviour
  (smart entry); the label changes now so operators learn one name.
  If zero confirmed designs exist the button explains itself
  ("no confirmed designs yet — add geometry first") instead of hiding.

### 2.2 Sizes strip
- One chip per active size with per-size completion (`L 7/8 ⚠`).
  Tap = jump to (and expand) that size's section. This strip IS the
  owner's "Sizes" level — always visible, always honest.
- `[matrix view]` keeps the piece×size matrix as the second lens
  (modal/expander) — two lenses, one derivation; the matrix remains
  the fastest gap-scan for power users.

### 2.3 Pattern Designs, grouped by size (the library)
- One section per size, **accordion** (mobile-first): header = size +
  progress + expand. Default: first incomplete size open, complete
  sizes collapsed (desktop may open all).
- **The design row (the atom of the whole system):**
  - geometry **shape preview** (mini SVG from confirmed geometry;
    tap = zoom lightbox) — the operator's fastest recognizer;
  - **reference image** thumb (piece-level truth, shown on every row;
    tap = zoom; visually distinct frame + "ref" tag so documentation
    never reads as geometry);
  - name + size + piece badges (`optional` · `pair` · `fold`);
  - **version**: `v1 · Confirmed ✓`, plus an amber `v2 draft in
    progress` chip when a newer draft exists;
  - **measured dimensions**: tape W × H mm + `tape-accepted` marker
    (MEASURED grade), or the geometry bbox labeled `unverified` for
    non-measured grades — never a number without its honesty label;
  - status chip: Confirmed / Draft (◐) / Missing (✗);
  - **[Edit →]** deep-link into the per-piece ladder focused on that
    size (capture / import / editor / confirm — existing pages).
- **Missing designs appear as ghost rows in place** (dashed preview
  box, "NO DESIGN YET", `[+ Add geometry]`): the library shows what
  SHOULD exist, not only what does — this embeds the matrix's truth
  into the reading flow and gives every gap a one-tap fix path.
- Draft-only designs render their draft preview greyed with the ◐
  status — visible but unmistakably not-yet-truth.
- Scale rule (from the final review): sections collapse + previews
  lazy-load from day one; >10 pieces per section adds an in-section
  name filter.

### 2.4 Layouts section
- **★ Production layout card**: thumb (existing SVG render), width ·
  length · utilization · approved-by/at · [open] [exports].
- **Saved layouts**: compact list, newest first, grouped by month once
  >10, each row: # · saved date · length/util · [open]. (Honest scope
  per the owner's D-7 postponement: this section shows the CURRENT ★
  and all immutable saved layouts — it makes no history claims.)
- Section title: **"Layouts"** with the ★ row pinned first — avoids
  implying an approval-history ledger that is postponed.

### 2.5 Footer utilities
Register piece · Calibration mats. (Register also reachable from any
ghost row's Add path when the piece itself is missing.)

## 3. Mobile design (the Workspace is mobile-FIRST; functional rule)

- Sticky mini-header after scroll: product code + % + Ready badge +
  [Cutting Table] icon button.
- Everything stacks: summary card → sizes strip (horizontal scroll
  chips) → accordions (one open at a time) → layouts.
- Design rows become **cards**: previews side-by-side on top (shape |
  ref), facts below, full-width Edit button ≥44 px.
- Previews tap-to-zoom (existing lightbox pattern); no hover-dependent
  information anywhere (hover = desktop bonus only).
- Reference-image ADD from the phone camera/gallery stays a first-class
  flow (validated in acceptance G-1).
- No horizontal page scroll ever; the matrix lens opens as a
  full-screen scrollable overlay on phones.

## 4. Operator walkthroughs (the workflows this page must make trivial)

1. **"Is this product ready?"** — open Workspace → % + badge; if ⚠,
   the sizes strip shows WHERE, the open accordion shows WHICH design,
   the ghost row shows the fix action. Zero extra pages to understand.
2. **"Fix the gap"** — tap ghost row `[+ Add geometry]` → per-piece
   ladder (capture/import) → confirm → back: row materializes, chip
   flips, % rises.
3. **"Update a shape"** — row `[Edit →]` → new version (copy-forward)
   → row shows `v2 draft in progress` until confirmed → then
   `v2 · Confirmed ✓` (old layouts untouched — spine).
4. **"Brand-new product"** — production page → assign patterns →
   Workspace shows all ghost rows grouped under its sizes → work top
   to bottom. **No sizes yet? The first Register-piece action offers:
   "This product has no sizes — create the 'General' size now?" →
   creates the real ProductSize row → identical hierarchy.** (The
   convention made visible exactly once, at the only moment it
   matters.)
5. **"Cut something"** — [Open Cutting Table] → (CT stage: size
   selection → library palette). Until then: today's smart entry.

## 5. What the Workspace deliberately does NOT do (boundaries)

- Never composes layouts (Cutting Table's job — it only launches it).
- Never edits geometry inline (rows deep-link to the focused pages;
  one-stop UNDERSTANDING, one-hop ACTION).
- Never writes on GET; all writes remain the frozen single-writer
  services behind the existing POST actions (defaults, optional
  toggle, reference images).
- Never shows a product switcher (Rule C).
- Internal note (final review §6): the workspace's row facts should be
  supplied by the same read-only design facade the Cutting Table will
  consume — one supplier, two consumers.

## 6. Vocabulary (locked)

Product Pattern Workspace (the page) · Pattern Design Library (the
per-size design collection) · Pattern Design = Piece × Size ·
Confirmed (design truth) · Saved Layout (immutable) · ★ Production
layout (approved) · Cutting Table (the composer, next stage) ·
Available/Selected/Placed (CT stage states).

## 7. "Perfect" — the acceptance bar for this design

1. Every fact of the owner's list (reference image · geometry ·
   preview · dimensions · status · version · edit) visible per design
   row with ZERO navigation.
2. Any gap in any size discoverable in ≤2 taps from page open, each
   with its one-tap fix entry.
3. Version truth per row (confirmed v# + draft-in-progress marker).
4. Readiness %, checklist, blockers/warnings all preserved (expander).
5. Ghost rows make the library show what SHOULD exist.
6. General-size flow: sizeless product reaches the identical hierarchy
   with one honest prompt.
7. Mobile: all of the above one-handed, no h-scroll, previews zoomable,
   camera upload works.
8. Zero writes on view; worker 403; context locked to one product.
9. The old Hub's every capability still reachable (nothing regresses:
   matrix lens, optional toggle, reference add/replace/remove, fabric
   defaults, register piece, mats).
10. Page stays fast at 160 rows (collapse + lazy previews).

## 8. Delta vs today's Hub (what "evolve" means concretely)

| Today (Hub) | Workspace |
|---|---|
| piece-first cards, size chips inside | **size-first sections**, piece rows inside (matrix stays as second lens) |
| no geometry previews on cards | **shape preview per design row** |
| no dims on cards | **tape W×H + honesty label per row** |
| version invisible at this level | **v# + draft-in-progress chip per row** |
| gaps shown in matrix + warnings | **ghost rows in place** + matrix + warnings |
| layouts not on this page | **Layouts section (★ first + saved)** |
| dashboard card on top | Product Summary (same data, summary-first + expander) |
| "＋ Register piece" header CTA | footer utility + ghost-row path |

Everything else (chooser, warnings wording, lightbox, POST actions,
readiness derivation) carries over unchanged in behaviour.

**STOP. Design delivered — no code, no tasks, no phases. Next step
when the owner approves this design: the implementation plan for the
Workspace (milestone discipline as always). Corrections to any section
above are cheap now — mark up anything that doesn't match the factory
picture.**
