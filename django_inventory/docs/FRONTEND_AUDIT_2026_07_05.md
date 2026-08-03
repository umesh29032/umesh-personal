---
id: frontend-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Frontend / UX Audit — recent-phase pages vs the canonical design system

> **STATUS: ✅ FE-1..FE-5 EXECUTED same day (owner approved + added the 7
> permanent UI-architecture rules — saved to standing memory + the
> UI_COMPONENTS checklist). Gate PASS 854; 390/768/1280 sweep clean; rule-5
> re-census clean (zero inline styles, zero invented classes without CSS,
> only canonical hero-gradient hex remains). Reuse mapping: machine form +
> master form → STAGE FORM shell (shared/_form_styles) · machine list +
> master lists → SKILLS CRUD chrome (.page-header/.kpi/.card + badge family +
> stacked-table standard) · generic panel → LAYERING panel family
> (.panel/.lybtn/.chip) + PA-15 stacking · stage-list ghosts → .add-btn
> modifier · canonical-partial completions: form-shell + stage-form now style
> FancySelect/Date TRIGGERS (PA-14-3 closed at the source). Bounce =
> token-mirrored; Alter/Missing visually quieter than Good (D2 emphasis).**

> Owner-ordered (2026-07-05, post-R10 acceptance): audit-only, no redesigns.
> Canon = [UI_COMPONENTS.md](../UI_COMPONENTS.md) + base.html tokens + the
> money-family reference screens. Method: class-existence census (which CSS
> classes the new templates use vs what base.html/shared partials actually
> define) + computed-style browser probes at 390px. **Root cause found and it
> is systemic, not taste:** the R10-era templates invented classes
> (`.page-hero`, `.count-chip`, `.m-card`, `.row-card`, `.gbtn`…) and did NOT
> include `shared/_form_styles.html` — so on those pages `.field` inputs
> render WHITE (violates the cream-input standing rule), heroes render as
> unstyled text blocks, and `.sticky-actions` is a static div. That is exactly
> the "unfinished / developer-oriented" feel.

## Per-page audit

### A. Machines register — `machines/machine_list.html` · **HIGH · ~1h**
1. **Good:** mobile summary-card idea (one line per machine, expand for
   actions) matches the density philosophy; counts strip = right instinct;
   inline assign/release flows are correct UX.
2. **Inconsistent:** invented `.page-hero/.count-chip/.m-card/.st-*` with
   hardcoded hex (`#fffdf7`, `#8a5a2b`, `#e6f4e6`) instead of tokens; hero is
   an unstyled block; assign-row selects are class-less (bare FancySelect
   fallback, off-look next to canon inputs); buttons mix `.btn btn-primary`
   with page CSS.
3. **Reference:** Payroll Overview + Adda list (card/list language, counts as
   `.stat-grid/.stat-card`), chips per `.skill-tag/.badge` family.
4. **Improve:** replace counts strip with `.stat-grid/.stat-card`; machine
   cards → `.card`/`.panel` + `<details>` keeping the summary line; tokens
   everywhere; class the selects (`.sf-input` or `.form-control`); hero →
   `.page-header` (or the navy `.hero-strip`); status chips → `.badge-*`
   with `--status-*` tokens.

### B. Machine form — `machines/machine_form.html` · **HIGH · ~30m**
1. **Good:** correct structure intent (numbered panel, help texts, cancel/save).
2. **Inconsistent (probe-proven):** missing `{% include 'shared/_form_styles.html' %}`
   → inputs WHITE bg/2px default border (cream rule violated), `.sticky-actions`
   static, `.page-hero` unstyled, `.help-text/.field-error` dead.
3. **Reference:** Stage form (`stage_form.html`) — same app family, already
   canonical (it includes the shared styles).
4. **Improve:** add the include; hero → form-shell hero pattern; widget
   classes on inputs where needed; verify FancySelect triggers pick up
   `.field` styling.

### C. Stage Categories + Machine Types (masters) — `master_list.html` /
`master_form.html` (serves both) · **HIGH · ~45m**
1. **Good:** exactly the right scope per page (one question: "what
   classifications exist, which are active, where used"); usage counts;
   inactive chip; back-links.
2. **Inconsistent:** same systemic issues — no shared-styles include, invented
   `.row-card/.m-*` classes, hardcoded hex, unstyled hero, dead
   `.help-text/.field-error` on the form.
3. **Reference:** User Skills list (`accounts` skills CRUD) — the existing
   canonical "simple master" pages — + Stage form for the edit form.
4. **Improve:** list rows → `.card`-based rows or the stacked-table standard
   (`.table-responsive` + `data-label`); form → form-shell include + `.field`;
   status → `.badge-active/-inactive`; tokens.

### D. Generic stage panel — `production/_stage_panel_generic.html` · **HIGH · ~1h**
1. **Good:** section-per-question layout (Workers / Machine / Output /
   Complete) mirrors the bespoke panels; completion-override partial reused;
   output table wrapped for overflow.
2. **Inconsistent:** invented `.gsp/.gbtn` button+chip family with hardcoded
   hex — sits visibly off-language beside the sibling panels' `lybtn` family;
   Output table lacks the `data-label` stacking standard (scrolls instead of
   stacking on phones); worker roster chips re-implement `_workers_widget`
   look by hand.
3. **Reference:** `_stage_panel_layering.html` (THE panel family reference:
   section headers, lybtn buttons, chip usage, embedded conventions).
4. **Improve:** adopt the panel-family button/chip classes (or promote the
   panel section header/button to a shared partial if a third panel needs it —
   3+ rule); Output table → panel-scoped stacking block per PA-15; tokens;
   roster → `_workers_widget.html` include with `_WorkerCheckboxes`-compatible
   markup.

### E. Stage form additions (category/work-type/machine-type pickers) —
`stage_form.html` · **LOW · ~15m**
1. **Good:** already canonical (shared styles included; fields inside the
   numbered panel; conditional machine-type with friendly clean()).
2. **Inconsistent:** the three new selects are class-less → bare FancySelect
   trigger (canon best-practice: class the select); inline `<script>` fine.
3. **Reference:** itself (rest of the page).
4. **Improve:** add a widget class per select; move the toggle script to the
   page's script block.

### F. Stage library header buttons (Categories / Machine Types) —
`stage_list.html` · **MEDIUM · ~15m**
1. **Good:** right placement (masters live beside the library).
2. **Inconsistent:** inline `style="background:transparent;color:var(--copper)…"`
   on `.add-btn` — an inline re-theme instead of a modifier.
3. **Reference:** the page's own `.add-btn` + `.btn-ghost` conventions.
4. **Improve:** page-scoped `.add-btn--ghost` modifier class in extra_head.

### G. Ops dashboard machines tile — `machines/_ops_tile.html` · **LOW · ~10m**
1. **Good:** reuses the host page's `.digest-tile` classes = perfectly
   consistent; graceful-degrade.
2. **Inconsistent:** one inline `style="text-decoration:none"`; renders dead
   if ever included outside `adda_dashboard` (classes are page-scoped there —
   acceptable, documented coupling).
3. **Reference:** sibling digest tiles. 4. **Improve:** move the inline style
   into the host's scoped CSS; add a `{# host-coupled #}` comment.

### H. Adda-detail category rollup (`.so-cat`) + `_so_tile.html` · **LOW–NONE**
Tokens used throughout, tile extracted to one shared partial, collapsible
`<details>` matches density rules. **Reference-quality; no change.** (Only
nit: `so-cat-count` could read "x/y complete" in stone — already does.)

### I. A360 category chips + worker current-op focus + `_stage_admin_snapshot`
usage · **NONE** — pure reuse of existing chip/pill classes; consistent.

### J. Bounce page — `stage_advanced_bounce.html` · **LOW · ~10m**
Purpose-built blank page (visible for a blink). Hardcoded colors → tokens;
otherwise fine.

### K. Sidebar "Machines" nav icon — `_nav_icon.html` · **LOW · ~10m**
Falls back to the dot. Add a gear/machine SVG keyed on `machines:list`.

### L. Worker report observation fields (Good/Alter/Missing) · **LOW · ~15m**
Reuses the canonical qty-row rendering (consistent). Improve: visual
de-emphasis of Alter/Missing vs Good (help hint "won't affect pay — tracked
for quality") to keep the worker's eye on the payable number — one CSS hint +
one help-text, still schema-driven.

## Consolidated improvement plan (owner approval → execute in this order)

| Phase | Scope | Effort | Priority |
|---|---|---|---|
| **FE-1** | Machines register + Machine form + both master pages → compose from canonicals (shared/_form_styles include, `.page-header`/hero pattern, `.stat-card` counts, `.card` rows, `.badge-*` statuses, tokens only, classed selects, live sticky bar) | ~2.5h | **HIGH** |
| **FE-2** | Generic stage panel → panel-family language (buttons/chips), PA-15 stacking for the Output board, `_workers_widget` reuse, tokens | ~1h | **HIGH** |
| **FE-3** | Stage-library ghost modifier · stage-form select classes · Machines nav icon · ops-tile inline style | ~40m | **MEDIUM** |
| **FE-4** | Bounce tokens · observation-field de-emphasis + hint | ~30m | **LOW** |
| **FE-5** | Rule-11 sweep of every touched page at 360/768/1280 + UI_COMPONENTS.md/GUIDE docs-sync (no new base.html components expected — everything composes from existing canon; promote ONLY if a pattern hits the 3-template rule) | ~45m | required |

Total ≈ **5.5h**. Nothing here touches behavior, money, or the engine —
presentation only, per the frozen rules. Guard for the future: the audit's
root cause (invented classes + missing style include) becomes a checklist
line — *"new template: run the class-existence check against base.html +
shared partials before calling it done"* — added to the UI_COMPONENTS
template checklist on execution.

### Verification sources
Class-existence census (grep of every class used in the 12 new templates vs
base.html + shared/_form_styles.html + _user_form_styles.html) · computed-style
probes at 390px (machine form: white inputs / transparent hero / static
sticky-actions) · UI_COMPONENTS.md canon · standing rules (cream inputs,
mobile-first, one-question-per-section). Confidence: High.
