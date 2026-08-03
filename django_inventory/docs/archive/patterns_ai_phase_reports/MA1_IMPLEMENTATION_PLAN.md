> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M-A1 IMPLEMENTATION PLAN — platform entry + truth stamp
**⚠ SUPERSEDED 2026-07-08 (same day, pre-implementation) by
[PHASE1_PATTERN_DASHBOARD_PLAN.md](PHASE1_PATTERN_DASHBOARD_PLAN.md) —
owner's final correction: the Patterns action opens a PATTERN DASHBOARD
(Blueprint · Manager · DCT modules), not the Manager directly. The
analysis below (call-site map, D-1/D-2, truth stamp) carries forward
into the Phase-1 plan. Never implemented as written.**

(2026-07-08 · ENGINEERING MODE, milestone 1 · PLAN ONLY — no code until
owner approval · architecture PERMANENTLY FROZEN, this plan implements it)

## Scope (exactly three things, nothing else)

1. **Truth stamp** — `geometry_contract_version` on `PieceSizeGeometry`
   (the 500-factory insurance; cheapest before more geometry
   accumulates). ONE additive migration.
2. **Patterns action → Pattern Manager** — the production `Patterns`
   button opens the Pattern Manager; the legacy assignment editor
   remains fully functional at a new URL, linked from the Manager
   (fold-in as a real section = M-A2, not now).
3. **DCT label rename** — "Open Cutting Table" → "Open Digital Cutting
   Table" (owner-ruled earlier; 2 strings, zero test impact).

NOT in M-A1 (deferred to keep the milestone atomic): Blueprint section
fold-in (M-A2) · `grain_rule` field (M-B, lands with its editor) ·
Universal size convention (M-A2) · any DCT work.

## Current state (verified this session)

- `production:product-patterns` (`products/<pk>/patterns/`) →
  `ProductPatternsEditView` = the legacy assignment editor
  (add/remove/update_count on `ProductPatternAssignment`), gated by
  `production.change_productpattern` (super-admin bypass).
- Referenced by 8 call sites: `production/urls.py:53` ·
  `product_list.html:42` (the Patterns button) ·
  `product_sizes_edit.html:152` ("Patterns →") ·
  `pattern_views.py:208,231` (POST success self-redirects) ·
  `test_pattern_pieces_count.py:21` · `test_phase6_m4.py:189,201` ·
  `test_pdm_w2.py:251`.
- Geometry rows are created at exactly 3 points in
  `pattern_geometry_service` (lines 140, 223, 431) — the single writer;
  DXF/manual rows have `source_extraction=NULL`, so the row itself must
  carry the contract stamp (extraction `pipeline_version` doesn't cover
  them).

## Design decisions (2, with recommendation)

**D-1 · Wiring shape: redirect at the OLD name, editor re-homed.**
`production:product-patterns` keeps its URL and becomes a redirect to
`patterns_ai:piece-list?product=<pk>`; the editor view moves unchanged
to `products/<pk>/patterns/set/` (`name='product-pattern-set'`).
Why this shape: every existing link (product list, sizes page, any
bookmark, any future reverse) lands on the Manager with ZERO template
churn beyond none — and the editor loses nothing. Alternative (retarget
each template link, keep editor at old URL) rejected: leaves "Patterns"
meaning two different things at two entry points.

**D-2 · Redirect gate = login-only; destination gates itself.**
The old editor gate (`change_productpattern`) stays on the editor at its
new URL. The redirect itself requires only login — the Manager already
enforces its own access (worker → 403, tested). Keeping the strict perm
on a pure redirect would 403 manager-role users who are allowed into the
Manager — an accidental tightening. Net: editor access unchanged,
Manager access unchanged, entry consistent.

## File touch list (9 files + 1 migration)

| # | File | Change | Why |
|---|---|---|---|
| 1 | `patterns_ai/models/geometry.py` | `geometry_contract_version = CharField(max_length=16, default='adr-c.1')` on `PieceSizeGeometry` + 1-line why-comment | frozen law: every geometry row declares its contract; default backfills all existing rows (all created under ADR-C) |
| 2 | `patterns_ai/migrations/00XX_geometry_contract_version.py` | AddField, additive only | principle 3 (additive-only) |
| 3 | `patterns_ai/services/pattern_geometry_service.py` | module constant `GEOMETRY_CONTRACT_VERSION = 'adr-c.1'`; stamp explicitly at the 3 creation points | future contract bump = single-writer-controlled, never a stray default |
| 4 | `production/urls.py` | `product-patterns` → redirect view; new `products/<pk>/patterns/set/` = `product-pattern-set` (editor) | D-1 |
| 5 | `production/views/pattern_views.py` | tiny `ProductPatternsEntryView` (LoginRequired redirect → Manager); editor's 2 POST self-redirects (`:208,231`) → `product-pattern-set` | D-1/D-2; editor logic untouched |
| 6 | `production/templates/production/product_patterns_edit.html` | unchanged body; header gets one line "part of the Pattern Manager — ← back" | orientation after re-home |
| 7 | `patterns_ai/templates/patterns_ai/piece_list.html` | 2 label strings → "Open Digital Cutting Table"; details sheet gains link "Pattern set & counts →" (`product-pattern-set`) | scope items 2+3; editor stays reachable |
| 8 | tests (3 conscious updates, commented M-A1): `test_pattern_pieces_count.py` (reverse new name), `test_phase6_m4.py:189,201` + `test_pdm_w2.py:251` (assert 302 → Manager instead of button-in-page) | page evolved by design, not regression |
| 9 | `patterns_ai/tests/test_ma1_entry.py` (NEW) | redirect 302+target+login-required · editor functional at new URL · contract stamp on all 3 creation paths + default on legacy rows · Manager details-sheet link · DCT label | acceptance proof |

Docs (same session, rule 12): this plan → M-A1 report; app GUIDE table
gains the new test file; DOCUMENTATION_INDEX entry.

## Risks

- **R-1 migration on populated table** — AddField-with-default on ~30+
  real geometry rows: standard safe additive; verified reversible.
- **R-2 SidebarAccessMiddleware** — redirect target `/patterns/pieces/`
  already reachable from production today (M4 button, browser-validated)
  → low; browser step re-verifies both roles.
- **R-3 perm-shift at entry** (D-2) — consciously decided, documented
  above; editor keeps its strict gate.
- **R-4 template caching** — dev server restart after template edits
  (known lesson) before browser validation.
- **R-5 test drift** — 3 assertions change meaning; each carries an
  M-A1 comment naming the design change (no silent edits).

## Acceptance criteria

1. Product list → Patterns → lands on Pattern Manager `?product=<pk>`
   (302 chain), for a management user; worker still 403 at the Manager.
2. Legacy editor fully functional at `products/<pk>/patterns/set/`
   (add/remove/update_count suite green at the new name), linked from
   the Manager details sheet, old strict gate intact.
3. Every new `PieceSizeGeometry` row (all 3 service paths) carries
   `geometry_contract_version='adr-c.1'`; every pre-existing row reads
   `'adr-c.1'` via default.
4. Gate button reads "Open Digital Cutting Table" (enabled AND disabled
   variants).
5. `makemigrations --check` clean after the one migration; frozen
   single-writer services otherwise untouched; facade contract
   untouched.
6. Full battery green (patterns_ai + full manufacturing suite, serial,
   fresh; counts verified from output, never predicted).
7. Browser walkthrough desktop + mobile 390×844: list → Patterns →
   Manager → details sheet → legacy editor → back; screenshots.

## Estimate

~9 files · 1 additive migration · no data migration · no new models ·
no frozen-writer signature changes · money boundary untouched.

---
**STOP — plan delivered. No code written. Implementation begins ONLY on
explicit owner approval of this plan (with D-1/D-2 accepted or
adjusted).**
