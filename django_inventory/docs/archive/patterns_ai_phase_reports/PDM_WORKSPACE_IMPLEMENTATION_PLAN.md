> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PRODUCT PATTERN WORKSPACE — Implementation Plan (PDM stage)
(2026-07-07 · plan for approval — NO code yet. Workspace ONLY; no
Cutting Table work. Hierarchy frozen per PATTERN_HIERARCHY_FREEZE_
REVIEW §7 + owner's six acceptances. Zero schema changes anywhere in
this plan.)

---

## 0. Business-principle review (owner's gate — answered first)

**Principle: the business is centered on Product Sizes, not Pattern
Pieces. UI always size-first. Each design row = the complete source of
truth. The Workspace owns product knowledge; the Cutting Table only
composes.**

Review of the approved design against it — **CONFORMS. No stop
needed.** Three honest notes, folded into the plan as requirements:

1. **The edit surface is the one deliberate exception.** Reading is
   size-first everywhere; but Edit deep-links land on the per-piece
   version page (the grading FAMILY — the frozen §3 grain). That page
   showing all sizes of one piece is CORRECT there (confirm covers the
   family). The Workspace remains the only size-first knowledge
   surface; the version page is the focused edit room. (W2 requirement:
   Edit links carry the size so the target row is highlighted —
   size-first even inside the exception.)
2. **Piece-level actions must say so.** `optional`/`pair`/`fold` badges
   and the reference image live on the PIECE (frozen). Shown on every
   size row, an operator could think "optional for S only". W2
   requirement: piece-level controls are labeled "applies to all sizes
   of <piece>" wherever they act.
3. **The matrix stays a secondary lens.** Piece-first grid demoted to
   `[matrix view]` — power-user gap-scan, never the primary reading.
   Conforms to "always size-first" as long as it never becomes the
   landing view (W2 requirement).

CT knowledge boundary: the plan builds the read-only design facade as
the Workspace's data supplier — the CT will later consume the SAME
facade, so product knowledge has exactly one home by construction.

### 0b. Owner clarifications locked into the facade design (approval note, 2026-07-07)
1. **The facade prepares the CANONICAL Product Design Library** whose
   intended consumer is the future Cutting Table. The current Generate
   page is a TEMPORARY consumer — the facade must never shape itself
   around it.
2. **A Design Row is a complete business object**, not a table line:
   one confirmed Pattern Design for one Product Size, owning piece ·
   size · preview · reference image · measured dimensions · version ·
   status · geometry · metadata · edit entry point. The Workspace (and
   every consumer) thinks in Design Rows, never scattered fields.
3. **The Workspace IS the Product Design Library** — the single home of
   design knowledge. The CT will consume Design Rows exactly as
   presented and never becomes a second knowledge home.
4. **The row contract must already support the CT lifecycle**
   (Available → Selected → Placed) without any Workspace redesign:
   stable `design_key` identity + self-contained facts (incl. outline
   geometry for palette previews/composition). Direction only — ZERO
   Cutting Table functionality is built in this stage.

## 1. What gets built (scope fence)

IN: read-only design facade · the Workspace page (evolved Hub — same
URL, same POST actions) · production button relabel · General-size
shortcut (production-side) · tests · browser + mobile validation ·
docs. OUT: Cutting Table anything · schema · new writers · engines ·
exports · redirect-priority changes.

## 2. Milestones (STOP after each, owner approves before the next)

### W1 — The design facade (backend only, zero UI change)
- **Objective:** one read-only supplier for all design knowledge:
  `services/pattern_design_facade.py` —
  `product_design_library(product)` returning: product summary
  (readiness %, ready flag, checklist, blockers, warnings, counts,
  fabric profile) · per-size sections · per-design rows (piece,
  size, version_no + draft-in-progress flag, status, dims W×H + trust
  label, preview payload ref, reference-image id, badges) · ghost
  entries for missing designs.
  READ-ONLY module: imports models + existing derivations; exposes NO
  writers; the current `_hub_readiness` logic moves in here (the view
  keeps a thin wrapper so nothing regresses); the Generate-page matrix
  reroutes to the same facade.
- Explicitly sanctioned: the owner froze "CT consumes confirmed
  Designs only through the read-only facade" — this milestone creates
  that facade with the Workspace as consumer #1.
- **Tests (~10):** facade returns exactly the acceptance-run truths on
  seeded fixtures (sections per size · row facts match version-page
  truth · draft chip logic (§3 display law) · ghost rows for missing ·
  dims honesty label (MEASURED vs unverified) · readiness identical to
  today's `_hub_readiness` output (parity test) · zero writes
  (assertNumQueries-style write guard) · sizeless product → empty-with-
  reason payload).
- **Regression:** hub/generate pages byte-identical behaviour (parity);
  full battery.
- Browser: N/A (backend).

### W2 — The Workspace page (the big one: UI)
- **Objective:** `piece_list.html` becomes the Product Pattern
  Workspace per the approved design: Product Summary (％ + badge +
  counts + defaults one-liner + ▸details expander w/ checklist/
  blockers/warnings + **[🪡 Open Cutting Table]** w/ honest disabled
  reason) → Sizes strip (per-size chips, tap-jump; `[matrix view]`
  overlay = the existing matrix partial) → per-size accordions of
  **design rows** (all 9 facts: preview SVG · ref thumb ("ref"-tag) ·
  piece name · size · version + draft chip · status chip · dims +
  honesty label · badges · Edit→ deep-link w/ size focus) → ghost rows
  with `[+ Add geometry]` → Layouts section (★ card + saved list,
  title "Layouts") → footer (Register piece · Mats).
  Production template button text → "🧵 Open Pattern Workspace".
  Page title/vocabulary per the locked table.
- Mobile-first per design §3: sticky mini-header, card rows, 44 px,
  accordion one-open, tap-zoom lightbox (existing), matrix as
  full-screen overlay, no h-scroll.
- Preview rendering: inline mini SVGs from the facade's geometry
  payloads (simplified outlines); sections render collapsed —
  measured, and if row count > ~60 the closed sections defer render
  (progressive enhancement, page still correct without JS).
- **Tests (~16):** page renders all sections for the real fixture
  shape · 9 facts per row asserted · ghost rows + fix links · draft
  chip · piece-level action labeling ("applies to all sizes") ·
  Edit href carries size focus · sizes strip counts · summary expander
  keeps checklist/blockers/warnings (nothing regresses) · layouts
  section ★-first · CT button honest disabled state · worker 403 ·
  zero writes on GET · production button relabel · matrix overlay
  reachable · mobile template hooks (data-labels/cards) present.
- **Browser (desktop + 390px):** walkthroughs 1–3 + 5 from the design
  §4 on the REAL T-SHIRT (understand → fix-gap path → version chip →
  CT button), screenshots; no-h-scroll check; lightbox zooms.
- **Regression:** full battery; Hub POST actions unchanged
  (optional toggle · reference add/replace/remove · defaults).

### W3 — Flows, polish, PDM acceptance
- **Objective:** the General-size shortcut — production-side, boundary-
  clean: the production Sizes page gains a one-click
  "create default 'General' size" action (production-owned code; no
  patterns_ai import), and the Workspace's sizeless state links to it
  with the honest prompt from design §4.4. Plus: perf pass at scale
  (synthetic 160-row product in a test — render budget), final
  vocabulary sweep (no visible "hub"/"library page"/"workspace-editor"
  strays), any W2 review nits.
- **Tests (~8):** sizeless product → prompt + link · production
  quick-create makes exactly one active 'General' size (idempotent) ·
  Workspace picks it up · scale fixture renders within budget ·
  vocabulary greps (no stray names in templates).
- **Browser:** brand-new sizeless DEV product walk (register → General
  prompt → size appears → ghost rows → one design end-to-end) — this
  is walkthrough §4.4 proven live; mobile pass repeat on the final
  page.
- **Close:** PDM acceptance against the design §7 ten-point bar
  (mini acceptance run on the real T-SHIRT, evidence table) →
  PDM_WORKSPACE_COMPLETION_REPORT → stage freeze → STOP (Cutting Table
  stage remains owner-gated).

## 3. Files touched (complete list)

| File | Milestone | Change |
|---|---|---|
| `patterns_ai/services/pattern_design_facade.py` | W1 | NEW read-only module |
| `patterns_ai/views.py` | W1, W2 | `_hub_readiness` → facade wrapper; workspace context from facade |
| `patterns_ai/templates/patterns_ai/piece_list.html` | W2 | becomes the Workspace |
| `patterns_ai/templates/patterns_ai/_design_row.html` (+ small partials) | W2 | NEW row/ghost partials |
| `patterns_ai/templates/patterns_ai/_readiness_matrix.html` | W2 | reused as the overlay lens |
| `production/templates/production/product_patterns_edit.html` | W2 | button text only |
| `production` sizes view/template | W3 | quick-create 'General' (production-owned) |
| `patterns_ai/tests/test_pdm_w1/2/3.py` | each | NEW suites |
| docs: design doc as-built notes + milestone reports | each | docs-sync |

No migrations. No new writers. No frozen-service changes.

## 4. Risks & honesty

- Template rework of the busiest page → W2 keeps every POST action and
  URL identical; parity tests + full battery guard regressions.
- Inline preview weight → measured in W2, budget enforced in W3's
  scale test.
- `piece_list.html` name vs "Workspace" — internal names stay (churn
  rule); visible vocabulary is what freezes.
- The ONE cross-app touch (General quick-create) is production-owned
  by design — the boundary stays clean; if the owner prefers, W3 can
  downgrade to link-only (owner choice at W3 review).

**STOP — plan delivered, no code written. On approval: begin W1 only.**
