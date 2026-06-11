# Frontend Modernization & UI Audit — 2026-06-12 (report only, no code changed)

Scope: all 105 templates (18,794 lines), the single-source CSS in base.html
(2,398 lines: 1,924 CSS + 309 JS), 1 static CSS file (auth.css), zero static
JS files. Evidence: grep census + authenticated browser sweeps at 360px on the
worst-suspect pages (cutting workspace, Adda list, rolls list, payroll
overview, flow editor, login) on top of this session's already-verified pages
(My Earnings ×3 viewports, settlements, review page, worker report/dashboard).
Constraints honored: no business logic, no APIs, no permissions, no workflows,
no architecture, no framework migrations proposed.

---

## Phase 1 — UI & Mobile audit (measured findings)

### 🔴 F1 — CRITICAL (mobile): DataTables stacked rows clip their VALUES off-screen at 360px
Measured on Adda list and Rolls list: stacked `td` boxes are **558px wide
inside a 360px viewport**; the value text sits at x≈470 — off-screen, with NO
horizontal scrollbar (container clips). Users see ONLY the labels (CODE /
PRODUCT / STATUS…); the data is unreachable on a phone. Root cause:
DataTables writes an inline desktop `width` on the table and the mobile
stacking CSS never overrides it (`width:100% !important; table-layout:fixed`
missing in the stacked breakpoint). Affected: the DataTables list family —
adda list, rolls list, accounts user/skill/usertype lists, storefront
category/product lists (6–8 management screens). Contrast: payroll overview
(custom data-label CSS, no DataTables) measured fine (338px, value at x=222).
**This breaks rule 11 for every management list page on a phone. One shared
CSS rule fixes the family.**

### 🟠 F2 — Cutting workspace Section 01 at 360px: raw checkbox roster
Worker-assignment checkboxes render as unstyled inline checkbox+email text,
wrapping mid-name; touch targets ≪44px and adjacent. Functional but the
hardest screen's first section greets phones with the roughest UI. (Rest of
the workspace stacks acceptably; no h-scroll measured.)

### 🟡 F3 — Visual inconsistencies (census-confirmed, not opinions)
- **11 separate `hero-strip` definitions, 18 `.panel` definitions,
  13 `btn-copper` definitions, 5 `sticky-bar`s, 10 copies of the copper
  gradient** — the same design-system vocabulary re-implemented per page with
  drifting paddings/radii/font sizes. Buttons: `btn-copper` vs `btn-primary`
  vs `lybtn-primary` coexist as three primary-button dialects.
- 717 inline `style="…"` attributes (stage panels are the densest), 79
  scattered `@media` blocks in templates.
- Empty/loading states: good on new screens (settlements, review), absent on
  several older lists.

### Pages verified GOOD at 360 (no action)
Worker dashboard, worker report (flagship), My Earnings, settlement
queue/detail, report-review page, payment screen, login, payroll overview,
flow editor (usable; dense but scrolls vertically only), costing dashboard.

## Phase 2 — Frontend architecture (template/CSS quality)

- **Template giants:** base.html 2,398 · public_home 1,311 ·
  `_stage_panel_cutting` 1,051 · adda_detail 752 · login 618 ·
  `_stage_panel_cutting_pattern` 526. The two stage panels mix layout, forms,
  inline styles, and inline JS in single files.
- **Partials exist and work** (`_form_styles` ×10 includes, `_autosave`,
  `_stage_panel_collapse`, `_time_log_styles`) — the pattern is established,
  just under-used for the shared vocabulary (hero/stat-card/panel/sticky-bar
  never became partials or base classes despite rule 9's 3+ threshold being
  passed long ago).
- **CSS:** one intended source of truth (base.html tokens + components) +55
  page-scoped `<style>` blocks. The page-scoping rule (10) worked — no leakage
  found — but it normalized re-DEFINING shared components instead of extending
  them. Dead CSS risk is low (scoped blocks die with their page); duplication
  is the cost.
- **JS:** zero static JS files; 33 inline `<script>` blocks; 79
  `addEventListener`s; only 2 fetch/AJAX call sites (app is refreshingly
  server-rendered). jQuery+DataTables loaded **via CDN per page ×5**, not
  centralized — version drift risk + repeated network cost.

## Phase 3 — Scalability vs upcoming phases

| Upcoming phase | Frontend pressure point |
|---|---|
| MissingPiece / Alter | Two new CASE list+detail screens — without a shared list/card component they become duplications #12 and #13 of the same vocabulary; with one consolidation pass they're ~free |
| G4 Adda-360 | Composes hero+stats+timeline+tables on ONE page — the strongest argument for extracting `hero-strip`/`stat-grid`/`panel` into base.html components BEFORE it's built |
| G1 costing UI / G5 inventory / G2 orders | All are management LIST+DETAIL families → inherit F1's DataTables bug and the table-pattern duplication unless fixed first |
| TM-1 | Touches flow editor only — safe as-is |

Naming: BEM-lite holds inside pages; cross-page tokens (`--copper`,
`--stone`, `--border-card`) are consistently used — the foundation for
consolidation is healthy.

## Phase 4 — Performance

- **Real:** per-page CDN vendor loads (jQuery 87KB + DataTables 60KB,
  re-fetch risk per page family); Google Fonts on every page (accepted);
  base.html ships 1,924 CSS lines to every page including the 3-screen worker
  flow (fine at this scale; noted, not actionable now).
- **Not real problems:** AJAX (2 call sites), event listeners (79, no leak
  pattern found), DOM size (largest page = cutting workspace, acceptable),
  modals (few). **No premature optimization recommended.** The only
  performance item worth doing is centralizing the vendor `<script>` tags
  (one cached copy, one version).

## Phase 5 — UX consistency checklist (state today)

- Buttons: ❌ three primary dialects (btn-primary / btn-copper / lybtn) —
  consolidate names, keep visuals.
- Forms: ✅ two sanctioned systems (.field + .sf-*) consistently used; cream
  inputs everywhere; validation via Django messages — consistent.
- Tables: ❌ split-brain — DataTables family (broken at 360, F1) vs custom
  data-label family (correct). One blessed responsive-table pattern needed.
- Cards/panels: visual style consistent to the eye, implementation duplicated
  (18 definitions).
- Navigation: ✅ sidebar+gating consistent; breadcrumbs absent (back-links
  ad-hoc but present on money screens); acceptable.
- Empty states: ✅ new screens / ❌ some legacy lists.

## Phase 6 — Mobile-first compliance verdict

- Worker flows: **COMPLIANT, measured** (4-tap report, big targets, 360px
  verified across this session).
- Management flows: **compliant EXCEPT the DataTables list family (F1 =
  outright broken on phones) and workspace Section 01 (F2, rough)**.
- Tables: custom data-label pattern = the blessed strategy; DataTables pages
  currently violate the "no unusable wide data" rule via the clip bug.
- 26 `type="number"` inputs lack `inputmode="decimal/numeric"` — minor
  keyboard friction on phones (one-attribute sweep).

## Phase 7 — Accessibility (critical-only, per brief)

- **138 `<label>`s without `for=`** (47 with) — most wrap their input
  (implicit association, OK), but the settlement variance/recovery inputs and
  several filter selects are label-adjacent only → screen-reader gaps on
  MONEY inputs. Critical subset: settlement draft + review page + advance
  form (~15 labels).
- Focus styles exist (17 `:focus` rules in base) ✓; cream-on-white contrast
  was already designed out; copper-on-white links measured fine.
- 18 `onclick=` (all confirm dialogs — acceptable pattern); 3 imgs without
  alt (storefront admin widgets); icon-only buttons (×, ▼) lack `aria-label`
  (~10 sites).
- No keyboard traps found; DataTables keyboard nav default-OK.

## Phase 8 — Debt register

| Sev | Item | Where |
|---|---|---|
| **CRITICAL** | F1 DataTables 360px value-clip (data invisible) | 6–8 management lists |
| **HIGH** | Shared-vocabulary duplication (hero/stat/panel/btn/sticky ×11–18) — blocks cheap G4/Missing/Alter UI | 55 style blocks |
| **HIGH** | Vendor JS per-page CDN tags ×5 (version drift) | DataTables pages |
| MED | F2 workspace roster checkboxes on phone | _stage_panel_cutting §01 |
| MED | Money-input label associations + icon-button aria-labels | settlement draft, review, advance |
| MED | `inputmode` missing on 26 numeric inputs | global sweep |
| MED | Stage-panel giants (1,051/526 lines, inline style+JS) | split when next touched (rule: don't refactor untouched working screens pre-soak) |
| LOW | Three primary-button name dialects | global |
| LOW | Empty states on legacy lists | a few lists |
| LOW | public_home 1,311 lines | marketing page, cold path |

## Phase 9 — Execution plan (NOT executed; grouped, risk-assessed)

### Quick Wins (1 short session total — recommend BEFORE/при deploy; F1 arguably pre-soak)
1. **F1 fix:** one shared stacked-table CSS rule in base.html
   (`width:100%!important; table-layout:fixed` in the stacking breakpoint) +
   verify the 6–8 list pages at 360. Risk: trivial, display-only. Mobile
   impact: restores ALL management lists on phones.
2. Centralize jQuery+DataTables tags into base (or a `{% block vendor %}`),
   delete the 5 per-page copies. Risk: low (same versions).
3. `inputmode` sweep on numeric inputs; `aria-label` on icon buttons; `for=`
   on the ~15 money-input labels. Risk: zero.
4. F2: style the roster checkboxes as the existing chip pattern (CSS-only).

### Medium Refactors (1–2 sessions — schedule BEFORE G4/MissingPiece UIs)
5. **Promote the shared vocabulary into base.html**: `.hero-strip`,
   `.stat-grid/.stat-card`, `.panel`, `.btn-copper/.btn-danger/.btn-ghost`,
   `.sticky-bar`, the stacked-table pattern — then delete the 11–18 page
   copies page-by-page (each page = a 10-minute, individually-revertible
   diff). This is rule 9 finally applied at scale; G4/Missing/Alter then
   compose instead of copy.
6. Bless ONE responsive-table pattern (the custom data-label family) and
   document it in UI_COMPONENTS.md as the standard for all future lists;
   DataTables remains for the existing desktop-heavy admin lists only.

### Structural Improvements (when the area is next touched — NOT before soak)
7. Split the two stage-panel giants into section partials (assignment /
   evidence / breakup / bundles / completion) — only when a feature next
   forces edits there.
8. Extract base.html's 309 inline JS lines + per-page scripts into static
   files with `{% block scripts %}` — pairs naturally with the first
   WhiteNoise-served static work post-deploy.
9. public_home/login dedup — cosmetic, cold pages, last.

### Explicitly NOT recommended
CSS framework migration, JS framework, Tailwind-ification, design re-skin,
touching the worker flow (measured excellent), any refactor of working
screens before the soak baseline exists.

**Sequencing note:** Quick Wins fit the pre-deploy window without reopening
build scope (F1 is a functional mobile BUG under rule 11, same class as
P1/P2). Medium Refactors slot cleanly between TM-1 and the MissingPiece UI.
Owner decides whether F1 (+#2–4) ride pre-deploy or land as soak week-1.
