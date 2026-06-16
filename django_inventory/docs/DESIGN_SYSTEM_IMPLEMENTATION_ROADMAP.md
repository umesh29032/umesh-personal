# DESIGN SYSTEM IMPLEMENTATION ROADMAP

> **Status:** Roadmap — **DESIGN ONLY, NO CODE AUTHORIZED.**
> Companion to [FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md)
> (the map). This is the *build plan*: per-foundation files · owner · migration ·
> rollback · browser checklist · risks · effort.
> **Owner:** Umesh · **Created:** 2026-06-16 · **Branch:** `new_flask_app`.
>
> Philosophy target: Shopify Polaris / GitHub Primer / Material — centralized tokens,
> shared primitives, strict ownership, mobile-first, zero duplicated styles, React/Tailwind-
> portable later. Implementation runs **one foundation at a time, each separately approved.**

---

## 0. Ground truth (measured 2026-06-16)

| Surface | Count | Meaning |
|---|---|---|
| Templates total | 114 (113 + base.html) | scope ceiling |
| Files with inline `style="…"` | **75** | token-migration surface |
| Total inline `style="…"` occurrences | **728** | the real debt volume |
| Inline `font-size:Npx` | **204** | typography-token surface |
| Templates using `.btn`/`btn-` | **86** | button blast radius |
| Inline mini-button `padding:4px 10px` | 7 | `.btn-sm` migration targets |
| `_form_styles.html` consumers | 23 | form foundation reach |
| TC-1 DataTable consumers (A1 5 + A2-CLEAN 3) | 8 | tables done/near-done |
| A2-PAGINATED views (`paginate_by=50`) | 3 (adda/roll/export_list) | tables blocked-on-decision |
| Auth templates | 7 | auth dedup surface |
| Financial/money templates | ~10 | financial foundation surface |
| Export-button pages | 2 (barcode_list, _stage_panel_barcode_gen) | export dedup surface |
| Card primitive consumers (`.card/.stat-card/.kpi`) | **60** | card refinement surface |

### Effort scale (sessions, junior-dev pace)
- **S** = ≤1 focused session · **M** = 2–3 sessions · **L** = 4+ sessions (split into sub-PRs).
Each foundation = its own branch-less working-tree batch → ONE commit on approval (audit cadence).

### Global rollback contract
- Every foundation = **one commit**. Rollback = `git revert <hash>` (post-commit) or
  `git checkout -- <files>` (pre-commit, working tree).
- **Token migrations are value-identical** (literal → token, same px/hex) → zero visual
  change → rollback rarely needed; diff is mechanical and reviewable.
- Backend untouched in every foundation except the A2-PAGINATED *decision* (flagged).

### Universal browser verification (applies to EVERY foundation, all viewports 320/375/390/414/1280)
1. `scrollWidth === innerWidth` (0 horizontal overflow) on every touched page.
2. 0 new console errors/warnings (favicon 404 excluded).
3. Visual diff = **none** for token/primitive migrations (pixel-identical intent).
4. Touch targets ≥44px on interactive controls touched.
5. Dark theme renders (toggle) — tokens must theme automatically.
6. Keyboard focus-visible intact on interactive controls.

---

## FOUNDATION 1 — Design Tokens *(FOUNDATION ZERO — additive, unblocks all)*

- **Files affected:** `accounts/base.html` only (the `:root` + `[data-theme="dark"]`
  blocks). **Phase 1 = purely additive** — add radius/space/typography/touch/breakpoint
  vars; repoint nothing yet. (Consuming templates change in *later* foundations, not here.)
- **Shared owner:** base.html `:root` (+ dark override).
- **Migration strategy:** (a) add token scales from §1.2 of architecture, values harvested
  from existing literals (no new design). (b) Leave all current literals working
  (tokens unused = no effect). (c) Each later foundation repoints its literals → tokens.
- **Rollback:** delete the added `:root` lines (additive ⇒ trivial; nothing depends on
  them until later foundations).
- **Browser checklist:** load 3 representative pages (a list, a form, a dashboard) ×5
  viewports → confirm **zero visual change** (tokens added but unused) + dark toggle + 0
  console. This is the "additive proves inert" gate.
- **Risks:** LOW. Only risk = a token name later collides/conflicts — mitigate with a
  documented naming convention (`--space-N`, `--radius-*`, `--fs-*`, `--touch-min`).
- **Effort:** **S.** One file, additive.

---

## FOUNDATION 2 — Button Foundation

- **Files affected:** `base.html` (`.btn` family, resolve `:not(.btn)` hack ~L1544–1553,
  add `.btn-sm`) + **86 templates** consume `.btn` but most need NO change; the active
  edits = **7 files** with inline `padding:4px 10px;font-size:12px` mini-buttons →
  `.btn-sm` (product_list, master_list + 5 others). Repoint `.btn` geometry to tokens (§1).
- **Shared owner:** `base.html` `.btn` + modifiers.
- **Migration strategy:** (a) tokenize `.btn` (radius/space/fs/touch → vars, value-
  identical). (b) Add `.btn-sm` matching today's mini-button geometry. (c) Replace the 7
  inline mini-button patterns with `.btn-sm` (per-template, one at a time). (d) Collapse
  `:not(.btn)` two-geometry hack into base + documented modifier; verify the ~handful of
  bare `.btn-ghost`/`.btn-danger` (no `.btn`) callsites still match.
- **Rollback:** revert base.html `.btn` block + the touched templates (one commit).
- **Browser checklist:** every button-bearing page-type (list/form/dashboard/auth/modal)
  ×5 viewports: geometry pixel-identical · `:active` scale · hover · focus ring · `.btn-sm`
  ≥ comfortable tap · danger/ghost/primary unchanged · dark theme.
- **Risks:** MED — the `:not(.btn)` callsites are the trap (two real geometries today).
  Mitigate: grep every `btn-ghost`/`btn-danger`/`btn-copper` WITHOUT `.btn`, verify each.
- **Effort:** **M.** Tokenize (S) + `:not(.btn)` reconciliation + 7 inline swaps.

---

## FOUNDATION 3 — Form Foundation

- **Files affected:** `production/_form_styles.html` → relocate to `shared/_form_styles.html`
  (update **23 include paths**) + tokenize its spacing/typography. Select/date already
  centralized (`fancify`/`fancifyDate` in base.html). Multiselect: bare-Django CC-20
  surfaces (2) → shared checkbox-chip partial.
- **Shared owner:** `shared/_form_styles.html` (CSS) + base.html `fancify`/`fancifyDate`
  (JS) + one validation-error contract.
- **Migration strategy:** (a) move partial, fix 23 includes (mechanical). (b) tokenize its
  spacing → `--space-*` (value-identical). (c) build shared checkbox-chip partial, retire
  CC-20 bare selects on the 2 surfaces. (d) confirm `.field` vs `.sf-*` boundary documented
  (both kept, not merged). (e) verify per-field error render (CC-29 contract) everywhere.
- **Rollback:** revert partial move + 23 include edits + base CSS (one commit). Include-path
  change is the only "wide" edit — but mechanical + greppable.
- **Browser checklist:** every create/edit page (form-shell) + admin `.field` forms + the
  2 multiselect surfaces ×5 viewports: spacing rhythm unchanged · inputs cream/readable ·
  select fancify · date picker · chip pickers · sticky CTA · per-field errors show ·
  no overflow · touch ≥44px · dark theme.
- **Risks:** MED — 23 include-path edits (miss one → broken form). Mitigate: grep-verify 0
  remaining `production/_form_styles` references after move; smoke every form page.
- **Effort:** **M–L.** Move+tokenize (M) + multiselect partial (S) split into sub-PRs.

---

## FOUNDATION 4 — Tables (TC-1 finalize)

- **Files affected:** **A2-CLEAN (3, DONE/HELD):** master_list, product_list, barcode_list
  — already migrated+verified+uncommitted → just **commit** (owner-timed). **A2-PAGINATED
  (3):** adda_list, roll_list, export_list + their views (`paginate_by=50`:
  `adda_views.py`/`roll_views.py`/`tracking_exports.py`) — **backend decision required.**
- **Shared owner:** `initFancyDataTable` + `_datatables_vendor_css/js.html` + responsive
  contract (all base.html/shared).
- **Migration strategy:** (a) commit A2-CLEAN (no new work). (b) A2-PAGINATED = decide per
  table: **Option A** drop `paginate_by` → client DataTable (small sets) · **Option B**
  server-side DataTable (`serverSide`, ajax — backend) · **Option C** leave paginated.
  Then migrate template + (A/B) the view. **This is the ONLY backend-touching step in the
  whole roadmap** → isolated, separately approved.
- **Rollback:** A2-CLEAN = `git checkout -- <3 templates>`. A2-PAGINATED = revert template
  + view per table (independent).
- **Browser checklist:** each table ×5 viewports: search · sort · paginate · data-label
  stack · `.td-actions` · empty-state · export forms OUTSIDE wrapper (barcode/export) ·
  totals/tfoot intact · **A2-PAGINATED: verify search/sort act on FULL dataset not 1 page.**
- **Risks:** LOW (A2-CLEAN) / MED (A2-PAGINATED — correctness: client DataTable on a
  paginated queryset silently breaks search/sort scope; row-count growth unbounded if
  Option A on large tables).
- **Effort:** A2-CLEAN **S** (commit only). A2-PAGINATED **M** (decision + 3 migrations).

---

## FOUNDATION 5 — Auth Foundation

- **Files affected:** 7 auth templates (forgot_password, login, login_password, otp,
  reset_otp, signup, signup_otp) + NEW `shared/_auth_shell.html`. Backend untouched
  (allauth views/URLs/rate-limit unchanged).
- **Shared owner:** `shared/_auth_shell.html` (chrome) + form foundation (§3) for inputs +
  button foundation (§2).
- **Migration strategy:** (a) extract the common shell (brand + centered/split card +
  slot) into `_auth_shell.html`. (b) rewrite each of the 7 pages to extend/include it,
  supplying only its form + copy. (c) one page at a time, browser-verify each before next.
- **Rollback:** revert the 7 pages + delete shell (one commit). Each page independently
  revertible if done incrementally.
- **Browser checklist:** all 7 auth flows ×5 viewports: layout identical · form submits ·
  validation/errors · rate-limit messaging intact · OTP flows · mobile centered/no-overflow
  · touch ≥44px · dark theme · **login still rate-limited (security: do not alter POST).**
- **Risks:** LOW–MED — auth is security-sensitive; template-only keeps backend/rate-limit
  intact, but verify no POST field name/CSRF/redirect changes. Test with real login (rate-
  limited — enter creds exactly).
- **Effort:** **M.** 7 pages but each thin once shell exists.

---

## FOUNDATION 6 — Financial Foundation (TC-3)

- **Files affected:** ~10 money templates (adda_settlement_list/detail, payroll_overview,
  costing, worker_detail, settlement_form, advance_form, stage_rate_list, adda_detail) +
  NEW `shared/financial/` partial set (SummaryCards/MoneyCell/StatusPill/LedgerGrid/
  TotalsBar/LedgerEmpty). **Presentation only — money logic stays in backend.**
- **Shared owner:** `shared/financial/*` partials + scoped CSS, on tokens + `.stat-card`
  (§5) + `--status-*` pills + `initFancyDataTable` (where convertible).
- **Migration strategy:** (a) build the 6 primitives from existing markup (extract, don't
  invent). (b) migrate one surface at a time, lowest-risk first (read-only overview before
  forms). (c) Type-2 ledgers → LedgerGrid only where convertible (totals OUTSIDE engine);
  structural exceptions (grouped settlement workflow) keep their layout.
- **Rollback:** per-surface revert (independent) + delete partials.
- **Browser checklist:** each money surface ×5 viewports: amounts/totals correct
  (presentation only — cross-check a known figure, e.g. golden ₹225 settlement READ-ONLY) ·
  money right-aligned · pills correct status · totals outside table · responsive money-table
  stack/summary · no overflow · dark theme. **GET-only on money pages; never reopen/settle
  the golden chain.**
- **Risks:** MED — money is high-trust; a presentation regression (wrong total alignment,
  pill mislabel) erodes confidence. Mitigate: read-only verification against known figures;
  never touch money services.
- **Effort:** **L.** New component set + ~10 surfaces → split into sub-PRs (primitives →
  read-only surfaces → form surfaces).

---

## FOUNDATION 7 — Export Foundation (TC-5, narrow)

- **Files affected:** 2 pages (barcode_list, `_stage_panel_barcode_gen`) + export_list
  manifest + NEW `shared/_export_buttons.html`. Backend untouched (export views/CSRF).
- **Shared owner:** `shared/_export_buttons.html` (params: csv/xlsx/pdf urls + optional
  quick-CSV), tokenized buttons (§2).
- **Migration strategy:** (a) build partial from the existing 3-form group. (b) replace the
  duplicated inline form-groups with the include. (c) keep forms page-level, OUTSIDE the
  DataTable wrapper (proven safe).
- **Rollback:** revert 2–3 templates + delete partial (one commit).
- **Browser checklist:** each export page ×5 viewports: CSV/XLSX/PDF POST works · forms
  outside `.dataTables_wrapper` · CSRF present · injection-safe output (PA-13-6 holds) ·
  button layout/labels unchanged · mobile wrap · touch ≥44px.
- **Risks:** LOW — narrow, additive, depends only on buttons.
- **Effort:** **S.**

---

## FOUNDATION 8 — Card primitives refinement

- **Files affected:** base.html (`.card/.card-header/.card-title/.stat-card/.kpi/.badge/
  .empty-state` → tokens) + **60 consumers** (most need NO change; only ones with inline
  card chrome — border/radius/shadow/padding — get cleaned). Page card SYSTEMS
  (dashboard/detail/timeline) stay as documented consumers.
- **Shared owner:** base.html card primitives.
- **Migration strategy:** (a) tokenize primitives (value-identical; most already use
  `--border-card`/`--shadow-card`). (b) sweep consumers for inline card chrome → replace
  with class/token. (c) document the legit page-scoped card systems as consumers (rule:
  3+ uses → promote; else page-scoped). **Do last — broadest reach, lowest urgency.**
- **Rollback:** revert base.html primitives + touched consumers (one commit; or per-app sub-PRs).
- **Browser checklist:** dashboards, detail pages, timelines, card-lists ×5 viewports:
  card chrome identical · hover · header/title · stat-card values · badges · empty-state ·
  no overflow · dark theme.
- **Risks:** LOW–MED — 60 consumers = wide; mitigate by tokenizing primitives first
  (inert), then sweeping inline chrome per-app in sub-PRs (not one mega-commit).
- **Effort:** **L** (by reach) — but mostly mechanical; split per app.

---

## Sequencing summary

| # | Foundation | Effort | Backend | Blast radius | Gate |
|---|---|---|---|---|---|
| 1 | Design Tokens | S | untouched | base.html only (additive) | inert-proof |
| 2 | Buttons | M | untouched | 86 consume / 7 active edits | `:not(.btn)` reconciled |
| 3 | Forms | M–L | untouched | 23 includes + 2 multiselect | 0 stale include paths |
| 4 | Tables finalize | S + M | A2-CLEAN none / A2-PAGINATED decision | 3 held + 3 paginated | full-dataset search/sort |
| 5 | Auth | M | untouched (security) | 7 pages → 1 shell | rate-limit/POST intact |
| 6 | Financial | L | untouched (money logic) | ~10 surfaces | figures correct, GET-only golden |
| 7 | Export | S | untouched | 2–3 pages | forms outside engine, CSRF |
| 8 | Cards | L (reach) | untouched | 60 consumers | chrome identical |

**Cadence (every foundation):** plan → implement → browser-verify 320/375/390/414/1280 →
STOP → owner review → ONE commit on approval → next. **No batching · no parallel
foundations · backend untouched** (except the isolated A2-PAGINATED decision in #4).

**Order note:** owner priority puts Forms (#3) before Tables-finalize (#4); both are
independent of each other (only depend on Tokens #1 + Buttons #2), so either order is safe.

**Portability (React/Tailwind later):** tokens-as-CSS-vars + named primitives + strict
ownership = a clean mapping target (vars → theme config, primitives → components). This
roadmap deliberately keeps style in tokens/classes (not inline) so a future port reads one
source per concern.

---

**No code authorized by this document.** Roadmap only. Implementation begins at Foundation 1
(Design Tokens) on explicit owner approval, one foundation at a time.
