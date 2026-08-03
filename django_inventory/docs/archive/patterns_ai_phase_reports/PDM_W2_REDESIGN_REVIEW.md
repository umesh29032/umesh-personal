> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DESIGN REVIEW — From Design Viewer to Product Pattern Design MANAGER
(2026-07-08 · review ONLY, nothing implemented. Cutting Table out of
scope except where its GATE touches this page.)

The owner used W2 and named the gap precisely: **the page displays
designs; the business needs the page that PREPARES the product.** The
question the page must answer, per size, is:
**"Is Size S completely ready for Cutting?"** — then M, L, XL.
Hierarchy frozen by the owner: **Product → Sizes → Pattern Designs for
that Size → Cutting Table.** Not "Product → Pieces → Layouts".

---

## 1. Honest diagnosis — why W2 still reads as a Viewer

| Symptom in W2 | Why it's viewer-thinking |
|---|---|
| The page LEADS with the product-level 100% | the operator's unit of work is a SIZE; the product number answers management's question, not the preparer's |
| Size sections show counts (`7/8`) but no VERDICT | "7/8" is data; "NOT ready — Pocket missing" is management |
| Rows show 9 facts + one Edit link | facts without in-place actions = a catalogue; management means the fix lives where the problem shows |
| Piece-settings bar at the bottom (optional/reference/remove) | piece-first appendix, detached from the size context where the operator actually is |
| **Layouts section on the page** | composer-domain content on the preparation page — exactly the "Product → Pieces → Layouts" shape the owner rejected |
| Open Cutting Table always enabled (tooltip only) | a gate that doesn't gate; preparation page must HOLD the door until required designs are ready |
| No "+ Add Size", no per-size "Edit Pattern Designs" mode | the two most basic manager acts aren't on the manager's page |

The data layer is NOT the problem: the W1 facade + Design-Row atom
already carry everything a manager needs. This is a PRESENTATION and
INTERACTION redesign — zero schema, zero writers, facade gains only
additive read-only fields.

## 2. The target — the owner's sketch, made precise

```
T-SHIRT · Product Pattern Workspace
─────────────────────────────────────────────
SIZES   [S ✓ Ready] [M ✓ Ready] [L ⚠ 7/8] [XL ⚠ 7/8]   [+ Add Size]
─────────────────────────────────────────────
S ····································· READY FOR CUTTING ✓ · 8/8
  ✓ Front Panel   ✓ Back Panel   ✓ Left Sleeve   ✓ Right Sleeve
  ✓ Neck Rib      ✓ Pocket       ✓ Brand Label   ✓ Care Label
                                        [ Edit Pattern Designs ]
─────────────────────────────────────────────
L ····································· NOT READY ⚠ · 7/8
  ⚠ Care Label — no design yet (optional)          [+ Add geometry]
  ✓ Front Panel  ✓ Back Panel  … (issues float to the top)
                                        [ Edit Pattern Designs ]
─────────────────────────────────────────────
🪡 OPEN CUTTING TABLE      — enabled per gate (§4); disabled state
                             names exactly what is missing
```

Per-size section = a WORK UNIT with three layers:
1. **The verdict line** (always visible, even collapsed):
   `READY FOR CUTTING ✓` or `NOT READY — Front Panel missing` +
   the 7/8 progress. This IS the page's answer to the owner's question.
2. **The design checklist** — the Design-Row atom re-skinned
   checklist-first: leading status glyph (✓/◐/⚠/✗), name, then the
   facts (dims · version · preview/ref thumbs) — issues SORT TO THE
   TOP of the section.
3. **Manage-in-place** — every row carries its contextual primary
   action (`+ Add geometry` when missing · `Confirm` when drafted ·
   `Edit` when done), and `[Edit Pattern Designs]` flips the section
   into manage density (piece-level controls — optional toggle,
   reference add/replace — appear ON the rows they belong to, each
   still labeled "applies to all sizes of ⟨piece⟩"; the detached
   bottom piece-settings bar DIES).

## 3. What must change (the redesign register — design-level)

- **R-W2-1 · Per-size verdict becomes the primary object.** Facade
  gains additive per-section fields: `ready` (required designs
  confirmed for this size), `required_missing` names,
  `issues_first` ordering. (Read-only, contract-additive — the atom
  and design_key untouched.)
- **R-W2-2 · Product summary demotes** to a compact header strip
  (product · overall % · settings). The hero paragraph goes; the
  checklist/blockers/warnings stay one tap away (settings/details
  sheet).
- **R-W2-3 · Rows become actionable** (contextual primary action per
  status; manage-mode reveals the piece-level controls in place).
- **R-W2-4 · Piece-settings bar removed** (its actions move into
  manage-mode rows; "Register piece" becomes `+ Add Pattern Design`
  inside manage-mode, clearly marked product-wide).
- **R-W2-5 · Layouts section REMOVED from the Workspace.** The page
  prepares; the Cutting Table (later) owns layout lists. Saved/★
  layouts remain reachable exactly as today via the CT entry/redirect
  and their own pages — nothing is orphaned. (Owner's hierarchy made
  literal.)
- **R-W2-6 · Cutting Table gate.** The button renders DISABLED with
  the honest reason until the gate passes (rule = decision PD-1, §4).
- **R-W2-7 · `+ Add Size` on the page.** Sizes are production-owned:
  v1 = a clearly-labeled hand-off ("opens Product Sizes") preserving
  the boundary; optional later: a production-owned slide-over (same
  pattern as W3's planned General quick-create). Decision PD-2.
- **R-W2-8 · Vocabulary/visual truth:** section verdict wording is the
  law's wording — required missing = NOT READY (red/amber); optional
  gaps = Ready-with-warnings (never block a size).

## 4. Decisions needed (small, before the redo)

| # | Decision | Recommendation |
|---|---|---|
| PD-1 | CT gate rule | **Enabled when ≥1 size is Ready** (you can cut S while XL is unfinished); disabled state lists per-size verdicts. Alternative (stricter): all sizes ready — rejected: real factories cut ready sizes first. |
| PD-2 | + Add Size mechanism | v1 hand-off link to production Sizes (boundary-clean); revisit slide-over with W3's General work |
| PD-3 | Layouts leave the page | confirm removal (they live behind the CT entry; pages unchanged) |
| PD-4 | Manage-mode scope | per-SECTION toggle (recommended) vs page-wide edit switch |

## 5. UI direction — "tech-giant grade", concretely (not vibes)

Principles to build against (Linear/Stripe-admin class, adapted to the
existing Craft&Thread tokens — no new design system, rule-of-canon):
1. **One question per screen region.** Header answers "which product,
   how far"; each size card answers "ready or not, and what's next".
   Nothing else competes.
2. **Verdict-first typography.** The size letter + verdict = the
   largest elements after the product name; facts are quiet; numbers
   right-aligned, tabular.
3. **Status is a system, not decoration.** Exactly four glyph/colors
   (✓ confirmed · ◐ draft · ⚠ optional-gap · ✗ required-gap) used
   identically in chips, rows, strip and gate — never a fifth.
4. **Issues float up.** Within a section, ✗ then ◐ then ⚠ then ✓ —
   the operator reads only the top until it's green.
5. **Progressive disclosure.** Collapsed section = verdict line only.
   Open = checklist. Manage = controls. Three densities, one page, no
   navigation.
6. **Contextual single primary action** per row and per section — the
   next step is always the visually loudest thing in its container.
7. **8-pt spacing grid · existing tokens only** (--card-bg,
   --border-card, shadows) · restrained motion (accordion + sheet
   transitions only) · no new colors beyond the status system.
8. **Mobile is the primary layout**: size cards stack full-width;
   horizontal size chips stay sticky under the app bar; a bottom
   sticky bar carries THE next action ("Fix Care Label · L" → jumps);
   rows = thumb-first cards (status glyph left, action right, 44 px);
   previews tap-to-zoom; manage-mode = a bottom sheet per row rather
   than inline forms.
9. **Empty/edge states designed, not defaulted**: no sizes → the
   Add-Size hand-off card; no pieces → "start by adding the pattern
   designs Size S needs"; sizeless product → General prompt (W3).
10. **Latency honesty**: previews lazy-load with skeletons; the
    verdict line renders first (server-computed, no JS required).

## 6. What survives untouched (so the redo is cheap)

The W1 facade + Design-Row **atom** (this is exactly why it exists —
re-skin, same business object) · honesty labels · Rule C · size-focus
edit anchors · matrix overlay (kept as the power lens) · all POST
actions/writers · zero schema. The redo is: facade +3 additive section
fields, one template rework, CSS/JS pass, tests updated consciously.

## 7. Acceptance bar for the redo (replaces design-§7 items 1–4)

1. Collapsed page answers "is each size ready?" with ZERO taps.
2. Any size's full picture = ONE tap (open section); any fix = the
   row's primary action; understanding one size NEVER leaves the page.
3. CT button honestly gated per PD-1.
4. No Layouts content on the page.
5. Product summary reachable but never competing.
6. Mobile: the §5.8 behaviors, no h-scroll, one-thumb operable.
7. Everything else from the original ten-point bar still holds
   (ghosts, version chips, zero-writes, worker 403, 160-row budget).

**STOPPED — review only. On the owner's PD-1..PD-4 rulings: W2R (the
Workspace redo) plan/implementation, milestone discipline as always.
Cutting Table remains out of scope.**
