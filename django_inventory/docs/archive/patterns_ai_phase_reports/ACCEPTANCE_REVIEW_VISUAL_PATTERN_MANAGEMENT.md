> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# ACCEPTANCE REVIEW — Visual Pattern Management
(2026-07-07 · supplementary acceptance-validation review · REVIEW ONLY —
zero code/DB/UI changes; freeze intact)

Walked as a factory operator on the REAL `T-SHIRT` product (8 pieces ·
30 confirmed designs · layouts #16–#22 · ★ #22). Evidence:
`av_V_piece_detail.png`, `av_V_version_grid.png`, `av_V_run13.png` +
the suite-A/E screenshots.

---

## 1. The Product → Piece → Size → Version → Status → Reference → Preview chain

What the operator actually gets today, page by page:

| Level | Where | What is visible | Verdict |
|---|---|---|---|
| Product | Hub | dashboard %, blockers/warnings, matrix, piece cards w/ size chips + reference thumb + next-step | **Strong** |
| Piece | Hub card | required/optional badge, per-size status chips, reference thumb, ONE next step | **Strong** |
| Piece → versions | piece-detail page | version timeline (v#, status, size codes as text) — **no shapes, no dims, no reference** | **Weak middle link** |
| Version → sizes | version-detail page | per-size cards: **inline geometry preview SVG with grain arrow**, trust badge (Measured tape-accepted), tape W×H mm + Δ, per-size SVG/DXF/Gate-1 print | **Excellent — the best page in the system** |
| Layout | candidate page | viz + totals + Production Layout Summary | good totals, weak per-design breakdown (§5) |

**Chain verdict: ends are strong, the middle is thin.** The Hub answers
"is the product ready"; the version page answers "is THIS design right"
— beautifully (see screenshot: S/M/L/XL shape previews side by side
with measured dimensions). The piece-detail page between them is a
text-only timeline that shows neither shapes nor dimensions nor the
reference image, so the operator hops straight through it.

## 2. Size visibility

- Which sizes exist / missing / confirmed: **immediately visible** —
  Hub matrix (✓/◐/✗ per piece × size) + per-card size chips. One page.
- Which sizes still require work: **yes** — blockers/warnings name
  exact `piece / size`, and each card carries a single "Next:" step.
- Which sizes have NEWER versions in progress: **partially** — a new
  draft shows as ◐ "drawn but not confirmed" (warning). That says
  *work in progress*, but not *"L is at v2-draft while production truth
  is v1"*. Version-awareness lives only on the piece/version pages.
- Hop count for "does Front Panel L exist, confirmed, right size?":
  exists+confirmed = 1 page (Hub). Actual dimensions = 3 pages
  (Hub → piece → version). See §4.

**Verdict: readiness-level size visibility is genuinely one-page.
Version-level size visibility is not — acceptable, but the v1-vs-v2
question will grow with real usage.**

## 3. Visual preview (thumbnails)

- Geometry **shape** previews exist ONLY on the version-detail page
  (inline SVG per size — excellent there).
- The Hub cards show the **reference image** thumb (a photo/illustration)
  — helpful, but it is documentation, not the confirmed shape.
- The piece list/timeline and the run/layout option cards show **no
  shapes at all**; the run page's options are text cards until opened.
- The owner's instinct is confirmed by this walk: operators recognise
  Front-vs-Back by the neck-scoop depth in a heartbeat, and by text
  label only slowly. Today that recognition works on exactly one page.

**Verdict: shape thumbnails are currently a deep-page feature. Making
small geometry thumbnails first-class (Hub cards · piece timeline ·
run option cards) is the single highest-leverage visual improvement
this review found. The rendering primitive already exists
(`geometry-svg` endpoint + inline SVG on the version page) — this is a
surfacing question, not a capability question. DOCUMENTED ONLY.**

## 4. Dimension visibility

- Width × Height per design: **version page only** (tape `480.0×660.0
  mm (Δ 0.0/0.0)` + grain + tolerance — exactly right, where confirm
  happens).
- Hub cards/matrix: no dimensions (deliberate minimalism — fine).
- piece-detail: **zero mm anywhere** (measured: 0 "mm" mentions) —
  the page most needing a dims column has none.
- Bounding box: never shown as such; tape W×H is the de-facto bbox at
  MEASURED grade — sufficient, but only after confirm and only 3 hops
  deep.

**Verdict: everything important IS captured and displayed once —
but only at depth 3. "Size · version · W×H · status · reference ·
preview" never appears together on one row anywhere.**

## 5. Layout review — who is IN this marker?

- The layout page gives honest totals (`45 pieces · 6 garment(s)`,
  ratio `S×1 M×2 L×2 XL×1`) and the Production Layout Summary.
- Per-design participation ("Front Panel S ×1, … Left Sleeve XL ×1")
  exists ONLY as hover-titles on the viz polygons — nothing readable
  as a list, nothing printable.
- **The skip record is invisible after generation.** The run persists
  `optional_skipped` (validated in suite C: `Care Label / L, / XL —
  skipped…`) but neither the run page nor the layout page displays it —
  the only "skip" string on both pages is the accessibility link
  (verified). The operator learns skips from the Hub BEFORE generating,
  then the information disappears from view while remaining in the
  database.

**Verdict: this is the clearest operator-understanding gap found.
An Included/Skipped block (piece × size × count + the persisted skip
lines) on run + layout pages would answer the owner's exact question;
the data already exists on both objects. DOCUMENTED ONLY.**

## 6. Reference image vs verified geometry

- Distinction holds everywhere it matters: Hub labels the slot
  "Reference image · display only — never geometry"; upload path
  forces the display-only kind; extraction refuses it structurally
  (M2-pinned); the version page shows GEOMETRY previews with
  trust/tape/grain — visually unmistakable from the photo thumb.
- One nuance: reference images are per-PIECE, while the owner's ask
  ("realistic garment-shaped reference images for every Size") is
  per-size. Since the per-size geometry preview already shows the true
  per-size shape, a per-size reference photo would duplicate it — the
  current split (one reference per piece + real previews per size) is
  arguably the better design. Noted for the discussion rather than as
  a gap.

**Verdict: no confusion risk found. PASS.**

## 7. Summary — the owner's seven questions

| Question | Answer |
|---|---|
| What already works well | Hub readiness (matrix, chips, next-steps, honest warnings); the version page's per-size shape previews w/ measured dims — best-in-system; reference/geometry separation; approve summary |
| What feels confusing | Nothing *confusing* found; the weak spots are *invisible* things, not misleading ones |
| Excessive navigation | Dims + previews live at depth 3 (Hub → piece → version); the piece-detail middle page adds a hop while showing the least |
| What would improve operator understanding | (a) Included/Skipped block on run + layout pages (data already persisted); (b) small geometry thumbnails on Hub cards / piece timeline / option cards; (c) a dims (tape W×H) column wherever a size row appears |
| Should visual thumbnails become first-class | **Yes — evidence says operators read shapes faster than labels, and the renderer already exists.** Decision is the owner's; nothing implemented |
| Is size-wise visibility sufficient | For readiness: yes, genuinely one-page. For version-level truth (v1 vs v2-draft per size): thin — grows in importance with real iteration |
| Does Product → Pattern → Size navigation feel natural | Yes — the ladder (Hub card → Geometry → version) matches the mental model; it is the *information density per hop* that lags, not the path |

## Findings register (additions to the acceptance record — REVIEW ONLY)

| ID | Severity | Finding |
|---|---|---|
| V-1 | MEDIUM | Persisted `optional_skipped` never displayed post-generation (run/layout pages) — participation invisible after the fact |
| V-2 | MEDIUM | No per-design Included list on layouts (hover-titles only; not readable/printable) |
| V-3 | MEDIUM | Geometry shape thumbnails exist only at depth 3; Hub/piece/option surfaces are text-only |
| V-4 | LOW | piece-detail page shows no dims/preview/reference — thinnest page on the busiest path |
| V-5 | LOW | Per-size "newer version in progress" only inferable from the ◐ warning; no v-number at Hub level |
| V-6 | INFO | Reference-per-piece vs owner's reference-per-size: current split looks right because per-size geometry previews exist — discuss, don't change |

**Nothing was implemented. Nothing was changed. All findings are
discussion inputs for the owner review, alongside F-A1..F-A4 and the
§3.8 cutting-scope evidence in the main acceptance report.**

**STOPPED.**
