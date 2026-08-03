> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M4 REPORT — smart redirect + entry button (Rules C/D/E)
(2026-07-07)

**Status: ✅ M4 COMPLETE — STOPPED. M5 will not start without approval.**

Rules C/D/E were conflict-checked against every frozen ADR/boundary
first — **no conflicts** — and locked into INTEGRATION_DESIGN **§2b**
before coding. One implementation ruling inside Rule E: the audit is the
**application log** (`logger.info`, timestamped records), NOT a table —
no analytics, no reporting, nothing to prune, and "M2 is the ONE
Phase-6 migration" stays true.

## Redirect decision table (owner-locked, implemented, all branches tested)

| # | State | Destination | Logged reason |
|---|---|---|---|
| 1 | ProductionLayout designation exists | editor on the approved layout | `approved layout` |
| 2 | any saved layout | editor on the LATEST saved layout | `latest layout` |
| 3 | confirmed geometry (drafts don't count — tested) | Generate form `?product=N` | `generate` |
| 4 | pattern pieces only | Pattern Library `?product=N` | `library` |
| 5 | nothing | Register Piece `?product=N` | `register` |

Guards: management-gated (worker ⇒ 403, anonymous ⇒ login redirect),
tampered/unknown/inactive product ⇒ 404. Deterministic — no heuristics.

## Entry-button implementation review
- ONE line-set in `production/templates/production/product_patterns_edit.html`
  (the per-product Pattern Design page): an `<a>` with
  `{% url 'patterns_ai:tool' product.pk %}` — **template-level URL
  composition only**, the ADR-H-safe precedent.
- The page itself is management-perm-gated
  (`production.change_productpattern`), so the button inherits the gate;
  the redirect view re-gates independently (defense in depth — tested
  from both sides).

## Boundary verification
- Production python imports NOTHING from patterns_ai — the change is one
  template URL tag; the purity/import-direction walls re-ran green.
- Test asserts the template contains the `{% url %}` tag and no python
  import; worker gets 403 on BOTH the production page and the tool URL.
- Rule C: the editor has no product selector (`name="product"` absent —
  tested); the redirect pins product by URL. The shared Generate/Library
  pages keep their standalone filter until M5/M6 rework them (locked in
  §2b, stated honestly).

## Rule D — context strip (editor header)
Read-only chips from stored facts: **Product name (code) · Layout #N
(· ★ Production when designated) · Ratio · Fabric width**. Mobile:
flex-wrap chips, page-scoped CSS only.

## Browser walkthrough (dev server 8003, fresh restart)
1. Super-admin → `/production/products/18/patterns/` (DEV-TEE): the
   **🧵 Open Layout Tool** button renders, href `/patterns/tool/18/`
   (screenshot `m4_button.png`).
2. Click → landed `/patterns/workspace/12/` = the LATEST saved layout
   (no designation yet — priority 2). Context strip:
   `Classic Crew Neck T-Shirt (DEV) (DEV-TEE) | Layout #12 | Ratio: L×1
   | Fabric width: 990 mm` (screenshot `m4_workspace_strip.png`).
   Log: `patterns.tool.redirect product=18 dest=/patterns/workspace/12/
   reason="latest layout" user=1`.
3. **Priority-1 live proof:** approved the OLDER layout #11 via the M3
   service (real dev data), reopened `/patterns/tool/18/` → landed
   **workspace/11** (the designation beats the newer draft #12), strip
   shows **`Layout #11 · ★ Production`**, log reason flipped to
   `"approved layout"` (screenshot `m4_priority1_star.png`).
4. Worker (utest, worker role): `/patterns/tool/18/` → **403 page**;
   `/production/products/18/patterns/` → **403** (screenshot
   `m4_worker_403.png`). Button unreachable for workers from both sides.

## Test results
- **M4 suite 16/16**: all 5 priority branches · draft-geometry ≠
  confirmed (falls to library) · worker 403 · anon → login · tamper +
  inactive 404 · **Rule-E log asserted** (product/dest/reason/user via
  `assertLogs`) · button rendered for management w/ correct href ·
  worker never sees the page · template-boundary check · Rule-D strip
  (product/layout/ratio/width) · ★ Production marker · Rule-C no
  product selector in the editor.
- One test fix during the run (test bug): the button test first used a
  `manager` user, but the production page requires the
  `change_productpattern` perm — switched to the seeded `super_admin`
  (the precedent in production's own tests).

## Regression
patterns_ai **272/272 OK** (256 + 16 M4) · full manufacturing suite **1157/1157 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero migrations (pin stays 17) · services untouched (M3 contract frozen).

**STOPPED — awaiting approval for M5 (Layout ▾ switcher + profile
prefills).**
