# Frontend Consolidation Review — Stage 2 classification (2026-06-12)

Review only — no implementation. Companion: FRONTEND_AUDIT_2026_06_12.md
(Stage 1 hardening PR shipped separately). Constraint set honored: no
redesign, no re-theme, no framework, no workflow/architecture/behavior change.

**Headline discovery (changes the plan's shape):** base.html ALREADY defines
canonical `hero-strip`, `.panel`, and `.btn-copper`. The duplication is pages
re-declaring page-scoped variants ON TOP of existing base classes — so
consolidation is mostly *deleting* page CSS and letting base win, not
inventing a design system. That makes the work smaller and safer than the
audit estimated.

The duplication clusters in two distinct populations:
- **The "money-screen family" (10 templates)** — expense/* (8: my_earnings,
  worker_detail, settlement_form, advance_form, worker_profile_form,
  payroll_overview, adda_settlement_list, adda_settlement_detail) +
  production/adda_report_review + production/costing. All built or rebuilt
  THIS session, all already browser-verified at 360/768/1280, all using the
  same class names as base.
- **The "legacy/complex population" (~9 templates)** — product_flow,
  stage_form, product_sizes/patterns_edit, access_control,
  sidebar_access_list, roll_bulk_form, _user_form_styles (+login,
  public_home). Older, individually styled, not recently verified.

---

## Per-item classification

### 1. hero-strip standardization — **A (money family) / B (legacy)**
- Templates: 11 total (list in audit); base.html canonical exists.
- Change type: CSS-only — align base's canonical (padding/radius/h1 size to
  the majority variant), then DELETE the 10 page-scoped `.X .hero-strip`
  blocks page-by-page. HTML untouched (markup already `<div class="hero-strip">`).
- Business logic: none. Rollback: one commit per page → `git revert`.
- Regression risk: LOW — worst case is ±2px font/padding drift where a page
  variant differed from canonical; caught by per-page screenshots.
- Mobile plan: scripted browse pass, 3 viewports per migrated page.
- Effort: ~10 min/page.

### 2. stat-card standardization — **A**
- Templates: 3 (my_earnings, worker_detail, settlement_form) + the prod-strip
  cousins. base has NO canonical yet → ADD `.stat-grid/.stat-card` to base
  (additive), delete 3 page copies.
- CSS-only · no logic · revert-per-page · risk LOW · effort ~30 min total.

### 3. panel standardization — **A (money family) / B (legacy)**
- 18 definitions; base canonical exists. Money family deletes cleanly (8
  pages). Legacy `.panel`s (product_flow, access_control, public_home,
  _user_form_styles…) have page-specific structure (numbered panels,
  collapsible) — defer to touch-time (B).
- CSS-only for A-scope · risk LOW-MED (panel paddings vary more than heros —
  verify each) · effort ~15 min/page.

### 4. button standardization — **split**
- **A:** ensure base's `.btn-copper/.btn-ghost/.btn-danger` are canonical and
  delete the 10 page-scoped redefinitions (money family + review page).
  CSS-only.
- **B:** unifying the three NAME dialects (`btn-primary` vs `btn-copper` vs
  `lybtn-*`) — that's HTML class renames across stage panels and forms;
  zero user value pre-deploy, mechanical post-soak or touch-time.

### 5. sticky-bar standardization — **A**
- 5 definitions, all money-family pages I shipped; base lacks canonical →
  add once, delete 5. CSS-only · risk LOW · ~30 min total.

### 6. data-label table standardization — **A (docs) / B (conversions)**
- The pattern is already canonical in base (and Stage 1 fixed its one bug).
- **A:** document it in UI_COMPONENTS.md as THE responsive-table standard for
  all future lists (G4/Missing/Alter/G1/G5/G2 UIs). Docs-only.
- **B:** converting existing DataTables pages to the custom pattern — no
  longer urgent (F1 fixed them); only if/when DataTables itself is retired.

### 7. duplicate CSS removal — **A = consequence of items 1–5** for the money
  family (≈400–500 duplicated lines deleted); **B** for the legacy
  population. No separate work item.

### 8. reusable UI pattern extraction (partials) — **B entirely**
- Splitting stage-panel giants, extracting hero/panel as `{% include %}`
  partials, JS → static files: structural, touch-time, post-soak per the
  audit's Phase 9. Pre-deploy value ≈ 0, diff surface large.

---

## Recommended pre-deploy package ("A-scope", one session)

1. Add to base.html: `.stat-grid/.stat-card`, `.sticky-bar` canonicals;
   align `hero-strip`/`.panel`/`.btn-*` canonicals to majority variant.
   (Additive — zero pages change until their local CSS is deleted.)
2. Migrate the 10 money-family templates page-by-page (delete local
   duplicates, keep page-specific extras like `.adst-list .pill`), ONE COMMIT
   PER PAGE.
3. UI_COMPONENTS.md: document hero/stat/panel/button/sticky/table patterns as
   the vocabulary for every future UI phase.
4. Verification: scripted 360/768/1280 browse sweep over all 10 pages +
   before/after screenshots on the 3 money-critical ones (My Earnings,
   settlement detail, payment).

Net effect: the screens the NEXT phases copy from (G4 composes exactly these
components; MissingPiece/Alter clone the list+detail money patterns) become
the clean reference implementations, and ~500 lines of duplicated CSS die
before production ever sees them.

## Explicitly deferred to B (post-soak / touch-time)
Legacy-page migrations (product_flow, access_control, forms, public_home,
login) · button name unification · DataTables→data-label conversions ·
partial extraction · JS-to-static · stage-panel splits.

**Awaiting owner go/no-go on executing A-scope before deployment.**
