> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# OWNER ACCEPTANCE VALIDATION PLAN
(2026-07-07 · prepared post Phase-6 freeze · SPECIFICATION ONLY)

**This is NOT Phase 7. NOT development. Nothing here is implemented.**
It is the final owner acceptance process before real production data
enters the system. Code, architecture, service contracts, models and
roadmap remain FROZEN. The validation uses **ONLY the owner's existing
real T-Shirt product**. No new demo products. No synthetic validation
product. **DEV-TEE stays an internal engineering reference and is never
touched during acceptance.**

---

## 1. Validation Objectives

1. Prove the complete production workflow on a REAL garment: Product →
   Pattern Designs (per size) → confirmed Geometry → Marker Generation →
   Manual + AI Optimization → Save → Approve → Production Layout
   Summary → PDF / Print / SVG.
2. Prove every honest-refusal path: nothing silent, every blocker named
   exactly, every warning visible before Generate.
3. Prove the collect-once philosophy: after the Hub says
   **Production Ready ✅**, no page ever asks for product data again.
4. Prove the optional-piece law on a real garment (required vs optional
   pattern types) — including the owner clarifications in §8, with the
   as-built mapping in §8.3.
5. Prove size-grain truth: every size owns its own Pattern Design and
   geometry; mixed ratios pull exactly the right per-size outlines.
6. Prove immutability + audit: saved layouts never change; the ★
   designation moves only by the explicit audited Approve act; replaced
   layouts stay reachable.
7. Prove exports are production-usable: true-scale (tape-verified
   100 mm bar), summary-stamped, assembly-numbered.
8. Prove the mobile experience on a real phone (not just an emulated
   viewport).
9. Produce a signed pass/fail record (§12) — the gate before the owner
   uploads real production patterns.

## 2. Prerequisites

- [ ] Phase-6 freeze intact: no code/schema/service changes since
      `PHASE6_COMPLETION_REPORT.md` (owner checkpoint commit made, or
      diff reviewed).
- [ ] The owner identifies the REAL T-Shirt product by code
      (the production T-Shirt with the real 16-operation flow —
      referred to below as **TSHIRT**). Written into §12 header.
- [ ] TSHIRT has the full size chart active in production → Sizes:
      **XS · S · M · L · XL · XXL** (create missing sizes there first —
      this is normal product setup, not patterns_ai work).
- [ ] A commissioned calibration mat (Gate-1 healthy: residual ≤ 1 mm,
      self-check ≤ 2 mm) OR the decision to enter geometry via DXF /
      the geometry editor for this round (both are built paths).
- [ ] Management login (owner) + one worker login (negative tests).
- [ ] Phone (real Android device) + desktop browser + printer with
      "print at 100%" capability + measuring tape.
- [ ] Reference images collected per §9 (license-safe) — optional but
      recommended before starting.
- [ ] Compute runtime healthy (`runtime_available` true; one Generate
      smoke on any existing data).

## 3. Preparation Checklist

- [ ] Read `PRODUCT_INTEGRATION_DESIGN.md` §§1–5 once (the locked
      rules A–N are the behaviour being accepted).
- [ ] Decide the REAL fabric numbers for TSHIRT: cuttable width (mm),
      default layer length, piece spacing, fabric type, GSM, lay mode —
      these go into the Fabric Defaults panel (Scenario A-6).
- [ ] Decide the piece list (§5/§6): which pattern types TSHIRT really
      has, which are Required, which Optional.
- [ ] Decide the geometry entry route per piece: photo-on-mat capture ·
      DXF import · geometry editor. (All three are accepted paths;
      photo capture requires the mat gate to pass — its refusal is
      itself a validation scenario, H-2.)
- [ ] Prepare realistic outlines per §10 (curves, not rectangles).
- [ ] Empty test print of one A4 tile to confirm the printer respects
      100% scale (measure the 10 cm bar) BEFORE the real export test.
- [ ] Block 2–3 hours; scenarios are sequential (A → H).

## 4. Complete Product Setup Checklist (TSHIRT)

Run entirely from the production Product pages + the Pattern Design Hub
— the collect-once surface. Done when the Hub dashboard reads
**Production Ready ✅** with zero blockers.

- [ ] Product exists, active, correct code/name.
- [ ] Sizes XS–XXL active with correct display order.
- [ ] Pattern library: every pattern type in §6 assigned to TSHIRT with
      the correct pieces-count per Adda (production → Product Patterns).
- [ ] Every piece registered in the Hub (§5) with correct flags
      (pair / fold / optional).
- [ ] Geometry confirmed for every REQUIRED piece × every size
      (36 = 6 pieces × 6 sizes if using the §6 default required set).
- [ ] Optional pieces: geometry confirmed for the sizes the owner
      intends to produce (deliberately leave ONE optional piece
      incomplete — needed by scenarios C-6/C-7).
- [ ] Reference image on every piece (display-only; §9 sources).
- [ ] Fabric Defaults saved (real numbers from §3).
- [ ] Hub dashboard: 100% (or the honest % if optional gaps were left
      deliberately) — screenshot for the record.

## 5. Pattern Piece Setup Checklist (per piece — the Hub's Rule-K ladder)

For EVERY pattern type, in this order (one piece fully finished before
the next — the piece card's "Next:" hint should agree at every step):

1. [ ] Register the piece (correct pattern type name from §6; flags:
       `pair` for sleeves if cut mirrored, `optional` where §6 says so;
       `on fold` only if truly cut on fold — note: fold pieces block
       generation by design, scenario H-4).
2. [ ] Enter geometry for EVERY size (XS–XXL), one of:
       photo-on-mat wizard (gate must pass) · DXF-AAMA import ·
       geometry editor. Realistic outline per §10.
3. [ ] Confirm each size's geometry (grain is mandatory at confirm —
       the system refuses without it; tape-measure acceptance where the
       wizard asks).
4. [ ] Attach the reference image (display-only; zoom to verify).
5. [ ] Piece card shows **Ready ✓**; matrix row fully green.

## 6. Industry-standard Pattern Piece naming

Standard knit-tee nomenclature (garment-industry usage; see §9 sources).
Names below are the recommended pattern-type names for TSHIRT.

**Required (structural — garment cannot be sewn without them):**

| Piece | Notes |
|---|---|
| Front Panel (Front Body) | front neck drop curve, shoulder slope, armhole curves |
| Back Panel (Back Body) | shallower back neck curve, shoulder slope, armhole curves |
| Left Sleeve | sleeve cap curve; usually cut as mirrored pair with right |
| Right Sleeve | mirrored twin (or one `pair` piece — owner's choice) |
| Neck Rib (Neckband) | narrow stretched rib strip, cut cross-grain |

**Optional (style/branding — legitimate tees exist with and without):**

| Piece | Notes |
|---|---|
| Pocket (Patch Pocket) | square/pentagon patch, chest |
| Brand Label (Main Label) | small woven label piece |
| Care Label (Wash-care Label) | small strip, usually side-seam |
| Size Label | often combined with brand label |
| Reinforcement Patch | shoulder/back-neck reinforcement |
| Half-Moon Patch | back-neck inside patch (premium tees) |
| Back Neck Tape / Shoulder Tape | narrow stability strips |
| Hem Band / Bottom Rib | ribbed bottom variant |
| Cuff Rib | ribbed sleeve-end variant |
| Decorative Panel | contrast/style block |
| Hood | hooded-tee variant |
| Kangaroo / Extra Pocket | hoodie-style pocket |
| Hang Loop | small folded strip |
| Placket | henley-style front opening |

Pick the set that matches the REAL TSHIRT (typical minimum: the 5
required + Pocket + Brand Label + Care Label). Labels are tiny pieces —
they exercise the nesting of very small parts among large ones, which
is exactly what real markers contain.

## 7. Size Validation

**The grain law under test: every size owns its own Pattern Design;
every Pattern Design owns its own geometry.** The size matrix is
XS · S · M · L · XL · XXL.

| # | Check | How (scenario ref) |
|---|---|---|
| 7.1 | Single-size production | C-1: ratio `M×10` only |
| 7.2 | Mixed-size production | C-2: ratio `S×2 M×3 L×4 XL×1` |
| 7.3 | Large production ratio | C-3: e.g. `XS×5 S×20 M×30 L×30 XL×15 XXL×5` (≈ real cut order; expect the Thorough method / honest timebox behaviour on huge piece counts) |
| 7.4 | Incomplete sizes | C-4: remove/skip one size's design on ONE required piece → Hub blocker names it; Generate refuses with the exact `piece / size` |
| 7.5 | Missing geometry | C-4/H-1: registered piece with no confirmed version blocks by name |
| 7.6 | Geometry updates | D-7: new version via copy-forward → edit → confirm; NEW generations use it |
| 7.7 | Version history | D-7: old saved layouts remain byte-stable (open an old layout after the update — outlines unchanged; §3e law) |

## 8. Optional Pattern Rule (owner clarification — validation of the existing optional-piece architecture)

### 8.1 The owner rule (verbatim intent)
A Product may contain Required and Optional pattern types. Required
always participate — missing required geometry blocks exactly as today.
Optional are never mandatory. Different layouts may legitimately carry
different optional combinations (Layout A body-only · Layout B + Pocket
· Layout C + Pocket + Brand Label — all valid). Approval validates only
the pattern types actually inside the approved layout.

### 8.2 What the frozen system does (as-built truth, for honest testing)
- `is_optional` per piece (Hub toggle / registration checkbox).
- Missing REQUIRED designs **block** generation, naming exactly what is
  missing. Unchanged. ✅ owner point 1.
- Missing OPTIONAL designs **never block** — the piece/size is skipped
  with an honest warning, and the skip is permanently recorded in the
  run (`optional_skipped`). ✅ owner points 2, 8-partial.
- An optional piece **with** confirmed geometry for the requested sizes
  is **automatically included**. Participation is controlled by *which
  geometry exists*, not by a per-run checkbox.
- Approval (Rule A) checks only the layout itself (verified, non-empty,
  belongs to product) — it never demands every optional piece. ✅ owner
  point 6.
- Exactly **ONE current ★ production layout per product** (owner-locked
  §3h, OneToOne). ALL saved layouts remain immutable and reachable in
  the switcher; any of them can become the ★ by an explicit approve.

### 8.3 ⚠️ Mapping owner points → as-built (OWNER DECISION BOX — read before executing suite C)

| Owner point | As-built verdict |
|---|---|
| 1 required block · 2 optional never mandatory · 6 approval validates only included | ✅ exact match — test directly |
| 4 different combos between layouts | ✅ achievable: combos follow from which optional geometry exists at generation time; every saved layout keeps its combo forever |
| 5 multiple approved layouts | ⚠️ interpretation: the system keeps ONE **current** ★ designation (owner-locked in M2/M3). Layouts A/B/C all exist as valid, immutable, approvable layouts; the ★ marks which one production cuts **now**; re-approving switches, history stays. If the owner instead requires several SIMULTANEOUS ★ designations per product, that is an architecture change (unfreeze decision) — NOT assumed here. |
| 3 operator chooses per-run which optional types participate · 7 selected-optional must be complete like required · 8 "missing AND selected" | ⚠️ **GAP: there is no per-run include/exclude selector.** As-built: optional participation = geometry availability (complete optional auto-joins; incomplete optional skips with warning). Two consequences: (a) "available but excluded from this layout" is not expressible per-run; (b) "selected but missing" cannot block — it skips honestly. **Path 1 (default, no code): accept the as-built semantics and validate them precisely — suite C below is written for Path 1.** **Path 2 (owner may order AFTER acceptance review): a scoped per-run optional-piece selection on the Generate form — that is NEW post-freeze work requiring an explicit owner order and its own review; NOT part of this acceptance.** |

### 8.4 Optional scenarios to execute (all documented in suite C)

| Owner-required case | Scenario | As-built expected result |
|---|---|---|
| no optional pieces | C-5a (all optional geometry absent) | body-only layout; warnings list each skipped optional |
| one optional piece | C-5b (Pocket complete, others absent) | Pocket joins; others warn-skip |
| multiple optional | C-5c (Pocket + Brand Label complete) | both join |
| different combinations | C-5 a→c saved as separate layouts | three immutable layouts with three combos; each approvable |
| required-only production | C-5a approved | ★ on the body-only layout; approval never asks about optional pieces |
| optional missing, NOT "selected" | C-6 (ratio avoids the incomplete size) | no warning, not included — silence is correct because nothing was requested for it |
| optional missing AND requested (Path-1 reading of "selected") | C-7 (ratio includes a size the optional lacks) | generation proceeds; warning names `piece / size — skipped (optional…)`; run records `optional_skipped`; run page/flash shows it |
| optional available and requested | C-5b/c | included; NO warning |

## 9. Reference Material Collection (research plan ONLY — nothing implemented)

Purpose: license-safe reference images (documentation ONLY — **never
geometry**; the capture wizard remains the only geometry door and
refuses the reference kind structurally) + realistic outline shapes for
§10.

Approved source classes (public / educational / open-license ONLY):
1. **FreeSewing.org** — open-source parametric garment patterns
   (MIT-licensed code and documentation; includes tee blocks) — best
   single source for realistic knit-tee piece shapes.
2. **Seamly2D / Valentina** open-source pattern-making project files and
   documentation (GPL community patterns).
3. **Wikipedia / Wikimedia Commons / Wikibooks** sewing & pattern-making
   articles and public-domain/CC illustrations (bodice/sleeve drafting
   diagrams).
4. University / vocational **open courseware** on apparel construction
   (textile-engineering OER; government skill-development apparel
   curricula — e.g. public sewing-operator/pattern-maker course PDFs).
5. **Owner's own photographs** of the owner's own cardboard patterns —
   always safe, and the most realistic.
6. Self-rendered outlines drawn from the system's OWN confirmed
   geometry (the engineering method used for DEV-TEE) — license-free by
   construction.

Rules: record source + license per image in a small table before
upload · NO copyrighted commercial manufacturing assets (no scanned
branded patterns, no paywalled blocks, no marker screenshots from
commercial CAD) · images go in ONLY through the Hub's reference-image
slot (kind = display-only) · anything doubtful is excluded.

## 10. Realistic Garment Validation (no rectangles)

Every validated piece must carry real construction curves so the pieces
interlock the way a real lay does:

| Piece | Required realism |
|---|---|
| Front Panel | front-neck scoop (deeper), shoulder slope ~15–25 mm drop, armhole curve, straight side seams or slight shaping |
| Back Panel | shallow back-neck curve, same shoulder slope, armhole curve |
| Sleeves | sleeve-cap curve (front/back asymmetry if drafted), underarm seam taper |
| Neck Rib | long narrow strip (stretch ratio shorter than neck circumference) |
| Pocket | patch shape with angled/pentagon bottom |
| Labels/patches | true small dimensions (e.g. 40×20 mm label) — they must nest into gaps |

Grading between sizes must be real (not one outline scaled): change
widths/lengths per size step (e.g. ~25 mm chest per size, ~15 mm
length) so mixed markers show genuinely different-sized pieces.
Interlock expectation: curved armholes/sleeve caps should visibly nest
(the DEV-TEE engineering run showed curves beating rectangles ~1707 →
1291 mm for one L garment — expect the same qualitative effect on the
real product). Tape-measure honesty: at confirm, enter the true tape
value; the ±2 mm gate must pass (a deliberate wrong tape is scenario
H-2).

## 11. Validation Scenarios

Execution order: A → H. Every scenario records: **objective ·
preparation · exact steps · expected screenshots · expected result ·
failure result · acceptance criteria.** "Fail" anywhere = record §12,
continue where independent, and STOP the acceptance if a money-grade
surface (approve/exports) fails.

Shared failure result (all scenarios): any 500 page, any silent
success/failure, any wrong number, any write occurring on a read step —
automatic FAIL.

---

### Suite A — Product & Pattern Setup (the Hub)

**A-1 Product surfaces in the Hub**
- Objective: TSHIRT reachable, context locked (Rule C).
- Prep: §2 done; logged in as owner.
- Steps: production → Products → TSHIRT → Patterns page → click
  **🧵 Open Layout Tool**; land per redirect (first time: Hub/register).
  Open the Hub directly and pick TSHIRT from the chooser.
- Screenshots: production button row · Hub hero for TSHIRT.
- Expected: Hub shows "Product Setup · <TSHIRT name>"; NO product
  selector inside; chooser only when arriving without a product.
- Acceptance: context lock + hero + chooser behaviour all correct.

**A-2 Register all pieces (Rule-K ladder start)**
- Objective: piece registration incl. flags.
- Prep: §6 list decided.
- Steps: + Register piece for each type; set pair on sleeves, Optional
  checkbox on §6 optional types; verify each card appears with
  "Next: Capture or import geometry".
- Screenshots: registration form with optional checkbox · Hub cards.
- Expected: cards show required/optional badges correctly; readiness
  matrix rows appear all-✗.
- Acceptance: every piece present, correctly flagged, next-step correct.

**A-3 Geometry entry + confirm, per size**
- Objective: the size grain (one design per piece × size).
- Prep: outlines per §10; route per §3.
- Steps: per piece: enter geometry for XS–XXL; confirm each (grain set;
  tape entered honestly); watch the piece card's next-step ladder move
  (Add {size} geometry → Confirm the drawn sizes → Add a reference
  image).
- Screenshots: one wizard/editor pass · matrix mid-way (mixed ✓/◐/✗) ·
  matrix all-green end state.
- Expected: draft cells show ◐ "drawn but not confirmed" (warning, not
  done); confirmed cells ✓; blockers list shrinks piece by piece.
- Acceptance: 6×N matrix truthful at every intermediate step.

**A-4 Reference images (Rule M)**
- Objective: display-only images with zoom/replace/remove.
- Prep: §9 images w/ license table.
- Steps: Add per piece → thumbnail appears → click = zoom lightbox →
  Replace one → Remove + re-add one.
- Screenshots: card with thumb · lightbox open.
- Expected: labeled "display only — never geometry"; replace moves the
  pointer (old asset stays stored); geometry pages unaffected.
- Acceptance: all pieces illustrated; zoom/replace/remove work; no
  geometry side-effects.

**A-5 Completion dashboard truth (Rule J)**
- Objective: derived readiness is honest.
- Prep: A-2..A-4 done except the DELIBERATE gaps (one optional piece
  incomplete per §4).
- Steps: read the dashboard checklist + % + blockers/warnings panels;
  fix a remaining required blocker; watch % move.
- Screenshots: dashboard before/after.
- Expected: exact naming ("<piece> — missing <size> geometry"); %
  changes only via real completions; **Production Ready ✅ only at zero
  blockers**.
- Acceptance: numbers reproducible from the §4 counts by hand.

**A-6 Fabric defaults (Rules G/B)**
- Objective: defaults = prefill only.
- Prep: real numbers from §3.
- Steps: save defaults in the Hub panel; open an EXISTING saved layout
  (any old TSHIRT layout if one exists — else defer re-check to D-6);
  open Generate.
- Screenshots: defaults panel · Generate form prefilled.
- Expected: Generate prefills width/spacing; saved layouts keep their
  OWN stored values; nothing historical changes.
- Acceptance: prefill present + history byte-stable.

### Suite B — Smart Redirect (Rule E audit included)

**B-1 Redirect priority walk**
- Objective: the locked 5-branch table on real data.
- Prep: state before any TSHIRT layout exists, then after each stage.
- Steps: hit `/patterns/tool/<TSHIRT>/` at each lifecycle stage:
  (i) pieces only → Library/Hub; (ii) confirmed geometry → Generate;
  (iii) saved layout exists → latest layout; (iv) after E-1 approve →
  the ★ layout. Worker login: same URL.
- Screenshots: one landing per branch.
- Expected: exact branch each time; worker = 403 page; log lines
  `patterns.tool.redirect … reason="…"` for each (owner may grep).
- Acceptance: 4 live branches + worker 403 + log lines present.

### Suite C — Generation (sizes + optional law)

**C-1 Single size** — ratio `M×10`.
- Steps: Generate with prefills; confirm readiness matrix on the form;
  submit; open run page.
- Expected: verified options; only M-size outlines; lengths plausible;
  each option independently checked.
- Acceptance: options open in editor; piece count = pieces × 10 (pairs
  ×2); no warnings.

**C-2 Mixed ratio** — `S×2 M×3 L×4 XL×1`.
- Expected: per-size outlines genuinely differ (grading visible);
  count = Σ ratio × pieces; no warnings (full coverage).
- Acceptance: spot-measure one S vs one XL piece in the editor.

**C-3 Large production ratio** — real cut-order scale (≈105 garments).
- Expected: EITHER options within the timebox (Thorough method) OR the
  honest give-up message ("ran out of time… use the Thorough method…").
  No hang, no silent partial marker.
- Acceptance: outcome is one of the two honest results; UI stays
  responsive.

**C-4 Incomplete size (required)** — temporarily lacking one size design
  on ONE required piece (use a piece whose vN for that size was never
  confirmed, or add size XXS to the chart w/o designs).
- Expected: Hub blocker + Generate-page matrix ✗ + POST refusal naming
  `<piece> / <size>` exactly. Nothing generated.
- Acceptance: wording exact; after completing the design the same ratio
  generates.

**C-5 Optional combinations (Path 1, §8.3)** — three sub-runs saved as
  three layouts:
  a) no optional geometry present → body-only layout + warnings naming
     every skipped optional; b) complete Pocket only → Pocket included;
  c) Pocket + Brand Label complete → both included.
- Expected: three immutable saved layouts with three different
  combinations; run pages record the skips permanently.
- Acceptance: Layout A/B/C exist per §8.1 example; each is approvable.

**C-6 Optional missing but NOT requested** — ratio restricted to sizes
  the incomplete optional DOES have (or optional has zero designs and
  expectation = plain skip warning listing it once).
- Expected: honest, minimal messaging; no block.

**C-7 Optional missing AND requested** — ratio includes a size the
  optional piece lacks.
- Expected (as-built Path 1): generation proceeds; warning
  `<piece> / <size> — skipped (optional…)`; recorded in the run.
- Acceptance: warning wording + persistence verified (revisit the run
  page later — the note is still there).

### Suite D — Layout editor

**D-1 Manual editing** — open a C-2 option: pan/zoom/fit; drag pieces;
  guides + snap; live length/utilization/waste update; plain click
  never nudges a piece.
**D-2 Rotate** — R / button = 180° only (grain law); no free rotation
  anywhere.
**D-3 Lock / Unlock** — L toggles; locked = dashed + undraggable;
  survives save/reload (D-5 re-check).
**D-4 AI Optimization** — select-none vs selection; locked pieces never
  move; strip shows Current + options with honest deltas incl. "Worse
  than Current" when true; Return restores exactly; Keep applies; undo
  history: preview = zero entries, Keep = one.
**D-5 Save draft** — Save → NEW immutable layout ("Layout saved (… mm,
  verified)"); reload keeps locks; ★ designation UNTOUCHED (§3g law —
  verify on the layout page).
**D-6 Switcher + unsaved-change protection** — order ★ → drafts
  newest-first → ＋ Generate New; clean switch instant; dirty switch
  asks exactly "Discard changes and open another layout?"; cancel
  stays, accept discards.
**D-7 Geometry update + version history (7.6/7.7)** — new version of
  one piece (copy-forward → edit → confirm). Old layouts byte-stable
  (open one: outlines unchanged); NEW generation uses the new outline
  (visible difference).
- Each D scenario: screenshot before/after; acceptance = the exact
  behaviours above, nothing extra triggered (Rule I: switching loads
  only).

### Suite E — Approval + Summary

**E-1 Approve with summary-before-approve** — pick the C-5c layout:
  layout page summary block (width/length/util/waste/pieces/ratio) →
  "★ Approve for production…" → review page repeats the summary + names
  the consequence → explicit POST → ★ banner + audit line (owner, time).
**E-2 Re-approve + replace** — re-approve same = "already… nothing
  changed" (audit preserved). Approve C-5a instead: review names the
  replaced layout; after: ★ moved, old layout intact in switcher,
  redirect follows.
**E-3 Approval validates only included pieces (owner point 6)** —
  approving the body-only layout (C-5a) while optional geometry gaps
  exist product-wide MUST succeed.
**E-4 Unverified never approvable** — if any unverified layout exists
  (or skip if none): no approve button + POST refused.
- Acceptance: audit fields correct; exactly one current ★; history
  reachable; §3g law re-verified live.

### Suite F — Exports (production documents)

**F-1 PDF** — on the ★ layout: download; page 1 = Production Layout
  Summary incl. ★ audit line + assembly instructions; tiles numbered
  C{col}-R{row}; **print ONE tile at 100% and tape-measure the 10 cm
  bar (must be 100 ± 1 mm)**; measure one printed piece edge against
  its confirmed dimension.
**F-2 Print page** — tile count = cols × rows; browser print preview =
  one tile per sheet + summary sheet; dashed overlap lines align when
  two adjacent printed tiles are physically overlapped.
**F-3 SVG** — download; `<desc>` + summary metadata block present incl.
  `"production": true`; opens in a viewer; outlines match the editor.
**F-4 Export safety** — worker: all three URLs = 403. Unverified layout
  (if any): PDF/print refuse honestly.
- Acceptance: true-scale proven by TAPE, summary stamped everywhere,
  gates hold.

### Suite G — Mobile (real phone)

**G-1 Hub on phone** — dashboard stacks, matrix scrolls horizontally
  inside its card, cards usable, upload reference image FROM THE PHONE
  CAMERA/gallery.
**G-2 Editor on phone** — open ★ layout: pan/zoom usable, context strip
  wraps, switcher menu touch-friendly, no horizontal page scroll.
**G-3 Approve on phone** — full E-1 flow on the phone (review page
  readable, buttons ≥ thumb size).
- Screenshots: phone screenshots attached to §12.
- Acceptance: every step completable one-handed; no dead zones.

### Suite H — Failure cases & honest refusals

**H-1 Missing required geometry** — Generate refusal names piece/size
  (re-run of C-4 wording check).
**H-2 Capture gate refusal** — photograph a piece with the mat mostly
  covered (<50% corners) → wizard refuses with the gate reason; retake
  passes. (If using DXF-only: substitute a deliberately wrong tape
  value at confirm → refusal.)
**H-3 Fabric too narrow** — Generate with width smaller than the widest
  piece → every engine refuses; message names the numbers; nothing
  saved.
**H-4 On-fold piece** — mark a spare piece on-fold → Hub blocker +
  generation refusal listing it; unmark → clears.
**H-5 Tampered URLs** — logged in as owner: nonexistent product/layout
  ids → 404 pages (no 500); worker: tool/Hub/approve/exports → 403.
**H-6 Editor refusals** — save with an overlap (drag two pieces
  together) → refusal with mm² numbers; move a piece outside width →
  refusal names the escape.
- Acceptance: every refusal is specific, actionable, and writes nothing.

## 12. Acceptance record (fill during execution)

Header: date · TSHIRT product code · executed by · app git commit.

| Scenario | Pass/Fail | Evidence (screenshot/file) | Notes |
|---|---|---|---|
| A-1 … H-6 | | | |

Sign-off: **Owner acceptance granted / withheld** — signature + date.
Withheld ⇒ list blocking findings; fixes are owner-ordered separately
(the freeze stays until then).

## 13. Non-goals (hard)

No code, no schema, no service, no architecture changes. No new demo or
synthetic products. DEV-TEE untouched (engineering reference only).
Path-2 of §8.3 (per-run optional selection) is NOT authorized by this
document. This plan itself is the only deliverable of this step.
