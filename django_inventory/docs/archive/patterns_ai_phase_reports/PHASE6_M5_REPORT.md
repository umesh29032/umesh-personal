> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M5 REPORT — Layout switcher + profile prefills (Rules F/G/H/I)
(2026-07-07)

**Status: ✅ M5 COMPLETE — STOPPED. M6 will not start without approval.**

Rules F/G/H/I conflict-checked against the frozen architecture — **no
conflicts** — locked into INTEGRATION_DESIGN **§2c** before coding. One
conscious supersession recorded: the execution plan's "profile prefills
the editor width/height/spacing" line is DEAD under Rule G (saved
layouts always display their own stored values) — prefills apply to the
Generate form only. Plan carries the as-built amendment.

## What was built
- **Layout ▾ switcher** (editor toolbar, first control): a custom
  dropdown menu — deliberately NOT a `<select>` (keeps the FancySelect
  auto-upgrade out of navigation, allows separators/★/links). Markup
  order = Rule F structurally: **★ Production → drafts newest-first →
  ＋ Generate New Layout** (production layout never duplicated in the
  drafts section; current layout highlighted).
- **Rule I structurally:** every menu item is a plain `<a href>` to a
  workspace page (or the Generate form) — no forms, no POST, no side
  effects; opening a layout is the same GET it always was.
- **Unsaved-change protection** (document-editor semantics): dirty =
  any layout operation since load (undo-history depth > 1) OR an edited
  width/height field. Dirty ⇒ `"Discard changes and open another
  layout?"`; cancel stays put, accept navigates. Clean ⇒ instant open,
  zero prompts.
- **Rule G prefills:** Generate form's width/spacing prefill from
  `ProductFabricProfile` when the product has one (always editable);
  no profile ⇒ previous defaults (empty + 3).
- **Rule H:** nothing new needed — verified: no auto-regeneration
  exists anywhere; engines run only on explicit Generate/Optimize;
  width/spacing/move/rotate/lock stay manual. Asserted, not built.

## Switcher ordering verification
- Unit: with a designation → items exactly
  `[★ Production · #A, Draft · #newest…, ＋ Generate New Layout]`,
  drafts strictly newest-first, no duplication; without a designation →
  drafts + Generate only, no ★.
- Browser (DEV-TEE, real data): menu showed
  `★ Production · #11 ~ Draft · #12 ~ #10 ~ #9 ~ #8 ~ #7 ~ ＋ Generate
  New Layout` (screenshot `m5_switcher_open.png`).

## Unsaved-change walkthrough (browser, 8003, fresh server)
1. On ★ #11, clean state → clicked `Draft · #12` → **instant navigation,
   no dialog** (`/patterns/workspace/12/`).
2. On #12, edited Width to 1200 (unsaved) → clicked ★ Production →
   confirm fired with EXACTLY `Discard changes and open another
   layout?` → **cancel ⇒ stayed on #12**.
3. Same dirty state, accepted → navigated to #11; editor shows #11's own
   990 mm (the 1200 edit discarded, as promised).

## ProductFabricProfile verification (Rule G — browser-tested explicitly)
- Set DEV-TEE profile via the M3 single-writer: width **1500**, length
  2500, spacing **5.0**, jersey/180/face-up (real dev data).
- Opened saved layout #11: context strip + Width input still **990 mm**
  — the layout's own stored value; 1500 leaked nowhere (screenshot
  `m5_ruleG_layout990.png`).
- Opened Generate `?product=18`: width prefilled **1500**, spacing
  **5.0**, both editable (screenshot `m5_ruleG_generate_prefill.png`).
- Unit walls: saved-layout page byte-stable across a profile change
  (CSRF-normalized); M3's Rule-B byte-identity test still guards the
  data layer. Old layouts / approved layout / runs untouched — proven
  at both layers.

## Test results
- **M5 suite 10/10**: ordering w/ + w/o designation · plain-links
  (no `<form>` in menu) · current-marked · prompt wording · Rule-I
  zero-writes across 4 opens · prefill w/ profile · defaults w/o
  profile · saved-layout-shows-own-values · byte-stable page.
- Two test-only fixes during the run (test bugs, not code bugs): menu
  extraction initially split on the separator `</div>`; byte-stable
  compare needed CSRF normalization (token rotates per request).

## Regression
patterns_ai **282/282 OK** (272 + 10 M5) · full manufacturing suite **1167/1167 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero migrations (pin stays 17) · M3 service contract untouched ·
docs updated: §2c lock + plan amendment + this report.

**STOPPED — awaiting approval for M6 (Pattern Design Hub + DEV-TEE
completion). Hub / Approve UI / Export not started, per scope.**
