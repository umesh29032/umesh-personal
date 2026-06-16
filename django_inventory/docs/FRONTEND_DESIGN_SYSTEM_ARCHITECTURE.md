# FRONTEND DESIGN SYSTEM ARCHITECTURE

> **Status:** Architecture spec — **DESIGN ONLY, NO CODE AUTHORIZED.**
> **Purpose:** the permanent frontend architecture of Kapil Enterprises Inventory.
> Successor to the closed HTML-by-HTML audit (113/113, families A–G frozen).
> **Owner:** Umesh. **Created:** 2026-06-16. **Branch:** `new_flask_app`.
>
> This document defines *where every frontend concern lives and who owns it* so that
> **changing one rule changes the whole project.** It does not authorize any edit.
> Implementation happens later, one foundation at a time, each separately approved.

---

## 0. North Star + Principles + Non-Goals

**End goal:** an industry-level frontend design system — Buttons · Forms · Tables ·
Selects · Multiselects · Cards · Financial UI · Export UI · Design Tokens all
**centrally controlled, one owner per concern.**

**Principles (owner-locked 2026-06-16):**
1. **No HTML component duplication.** Templates stay mostly intact — they *consume*
   shared primitives, they do not re-implement them.
2. **No business logic moved.** Backend untouched. Views/services/context unchanged.
3. **Single source of styling + behavior per family** = one CSS owner + one JS owner.
4. **Change-once-affects-all** is the acceptance test. If changing a button style or a
   form spacing rule requires editing >1 file, the foundation has failed.
5. **Tokens before pixels.** No new hardcoded color/space/radius/font/breakpoint in any
   template once its token exists. Inline `style="…"` is debt, not architecture.
6. **Mobile-first is FUNCTIONAL** (standing rule). Every foundation ships a responsive
   contract; touch targets ≥44px are first-class.
7. **Evidence-grounded, additive, reversible.** Foundations extend the existing
   base.html system; they do not redesign it. Every migration is rollback-simple.

**Non-goals:** no redesign · no color/branding change · no Tailwind/React/Bootstrap ·
no new vendor lib · no speculative abstraction · no backend change · no markup
restructure beyond swapping inline styles → shared classes/tokens.

**Where the system lives today:** `config/accounts/templates/accounts/base.html` is the
single style+script sink (`:root` tokens, `.btn`/`.card`/`.badge` primitives,
`fancify`/`fancifyDate`/`initFancyDataTable` JS). Shared partials:
`shared/_datatables_vendor_css.html` · `_datatables_vendor_js.html` ·
`production/_form_styles.html` (23 consumers). **base.html stays the canonical sink** —
this architecture formalizes and *completes* it, it does not replace it.

---

## 1. Design Tokens  *(FOUNDATION ZERO — everything depends on this)*

### 1.1 What exists (STRONG — keep)
base.html `:root` already centralizes:
- **Brand/neutral palette:** `--ink --copper --copper-l --copper-d --cream --stone
  --smoke --white --page-bg --card-bg`.
- **Semantic aliases:** `--surface --surface-input --text-primary/secondary/tertiary
  --border-card --border-default --border-subtle --shadow-card --shadow-card-hover`.
- **Status pairs:** `--status-{success,warning,danger,info,neutral}-{bg,text}`.
- **Layout:** `--sidebar-w --topbar-h`. **Full dark-theme override block.**

→ **Color/surface/status/shadow = already one-owner. No work needed beyond consuming
them where templates still hardcode hex.**

### 1.2 What is MISSING (the real token debt — to add)
No tokens exist for these; they are hardcoded across templates and base.html:

| Token family | Proposed scale (names only — values harvested from existing usage) | Today |
|---|---|---|
| **Radius** | `--radius-sm 6` · `--radius 8` · `--radius-md 10` · `--radius-lg 12` · `--radius-pill 999` | literals 6/8/10/12 scattered |
| **Spacing** | `--space-1 4` · `--space-2 8` · `--space-3 12` · `--space-4 16` · `--space-5 20` · `--space-6 24` (4px base) | literal px in padding/margin/gap |
| **Typography** | `--fs-xs 11` · `--fs-sm 12` · `--fs-base 13` · `--fs-md 14` · `--fs-lg 18` · `--fs-xl 22`; `--lh-tight/base` | inline `font-size:12px` etc. |
| **Touch target** | `--touch-min 44` (min interactive height/width) | many controls 23/29px (audit debt) |
| **Breakpoints** | documented scale: `xs 414 · sm 600 · md 768 · lg 1024` (CSS can't `var()` in `@media` → these are a **documented constant set**, not live vars) | mixed 560/600 inconsistency |
| **Control height** | `--control-h 39` (matches audited fancified `sf-input` 39px) | 37/42/43 native variance |

### 1.3 Token contract (the rule that makes "change once" true)
- **One owner:** the `:root` block in base.html (+ `[data-theme="dark"]` override).
- **Consumption rule:** templates/components reference `var(--token)` — never raw hex,
  raw px radius, or inline `font-size`. New literals are a review-blocker.
- **Dark mode = free:** any component built on tokens themes automatically.
- **Migration is mechanical:** literal → token, value-identical (no visual change).

> **Token layer is FOUNDATION ZERO. Buttons/Forms/Cards/Financial all consume it, so it
> migrates FIRST.** Adding tokens is purely additive (new `:root` lines); zero risk until
> a component is repointed to them.

---

## 2. Button Foundation

### 2.1 What exists
`.btn` base + modifiers `.btn-primary .btn-copper .btn-ghost .btn-danger .btn-filter
.btn-clear` — all in base.html. Already a centralized family.

### 2.2 The divergence to resolve (evidence: base.html ~1544–1553)
A `:not(.btn)` hack gives `.btn-copper/.btn-ghost/.btn-danger` a **second geometry**
(radius 10, font 13) when used WITHOUT the `.btn` base. → two button shapes in the wild.
Plus **inline-styled mini buttons** everywhere (`style="padding:4px 10px;font-size:12px"`
on row-action links — seen in product_list/master_list).

### 2.3 Target architecture
- **One owner:** `.btn` + modifiers in base.html, all built on tokens (radius/space/fs/
  touch from §1).
- **Add ONE size modifier** `.btn-sm` (replaces the inline `padding:4px 10px;font-size:12px`
  row-action pattern) → kills the inline-style duplication. Optionally `.btn-mini`.
- **Resolve `:not(.btn)`:** fold the two geometries into base `.btn` + a documented
  modifier; remove the hack so there is ONE button shape.
- **Touch target:** `.btn` min-height `var(--touch-min)`; `.btn-sm` documented exception
  where density is required (tables) but still ≥ comfortable tap on mobile.
- **A11y:** focus-visible ring from tokens; icon-only buttons get `aria-label`.

**Acceptance:** change `.btn` radius/padding once → every button in the project moves.
No template carries button geometry inline.

---

## 3. Form Foundation

### 3.1 What exists
- **`production/_form_styles.html`** — shared partial, **23 consumers** = the de-facto
  form foundation (approved candidate, audit Form-Control Report).
- **Two input systems** (audit finding): `.field` (label+control+error) and `.sf-*`
  (form-shell: hero + numbered panels + cream inputs + chip pickers + sticky bar).
- **Validation:** per-field `.field-error`/`.form-error` (CC-29 fixed the swallow).
- **Selects:** `fancify()` (class-owned fancify path = approved candidate).
- **Dates:** `fancifyDate()` (fancy-date opt-in = approved candidate).
- **Multiselects:** shared checkbox-chip direction (candidate; CC-20 bare-Django still
  exists on 2 surfaces).

### 3.2 Target architecture
- **One owner:** `_form_styles.html` (CSS) — promoted from `production/` to a neutral
  `shared/_form_styles.html` location (cross-app already; 23 consumers), built on §1
  spacing/typography tokens so **one spacing rule = whole-project form rhythm.**
- **Keep both systems, document the boundary:** `.sf-*` form-shell = create/edit hero
  pages (owner's mandatory shell); `.field` = lightweight/admin/inline forms. Not merged
  — documented exception, one owner each.
- **Selects → `fancify`** the single select behavior owner. Bare `<select>` keeps the
  `--bare` fallback (Phase-14) so unclassed selects still get a 44px box.
- **Dates → `fancifyDate`** opt-in via `data-fancy-date`.
- **Multiselects → one shared checkbox-chip partial**; retire bare-Django CC-20 surfaces.
- **Validation → one error-render partial/contract** (per-field, never swallowed).

**Acceptance:** change form spacing/label rhythm once in the form foundation → every
create/edit/list form moves. No form re-implements input/label/error CSS.

---

## 4. Table Foundation

### 4.1 What exists (already a foundation — TC-1, audit Tables Report FROZEN)
- **`initFancyDataTable(selector, opts)`** in base.html = SOLE DataTable bootstrapper
  (only raw `.DataTable()` lives inside the helper). Opts: `pageLength itemName
  searchPlaceholder columnDefs filterRowId`.
- **Vendor per-page** via `shared/_datatables_vendor_css.html` + `_datatables_vendor_js.html`.
- **Responsive contract:** `.table-responsive` wrapper + `data-label` cells → mobile
  card-stack (`td{display:flex}` + `::before` label) + `.td-actions`/`.action-link` +
  `.empty-state`.
- **Classification (frozen):** **A1** = canonical CRUD on TC-1 (skill/user/usertype +
  storefront ×2). **A2** = same purpose, shared primitives, **no engine** = accidental
  drift, low-effort migration. **A2-CLEAN** (master/product/barcode_list, no
  `paginate_by`) = **MIGRATED + VERIFIED + HELD** (uncommitted). **A2-PAGINATED**
  (adda/roll/export_list, `paginate_by=50`) = deferred, needs pagination decision.
- **TC-2 exceptions (legit, do NOT force onto DataTable):** Type-1 Workflow Queue ·
  Type-2 Financial Ledger (convertible) · Type-3 Inline Editor · Type-4 Matrix ·
  Type-5 Dashboard Summary.

### 4.2 Target architecture
- **One owner:** `initFancyDataTable` + the two vendor partials + the
  `.table-responsive`/`data-label` responsive contract.
- **All list/CRUD tables → TC-1.** Finish A2: commit A2-CLEAN (owner-timed), then resolve
  A2-PAGINATED (drop `paginate_by` for small sets OR server-side mode — backend decision,
  separate project).
- **TC-2 exceptions stay exceptions**, documented — DataTable only where it doesn't break
  the workflow/inline-edit/matrix.
- **Responsive contract is mandatory** for every new table (data-label or scroll/summary).

**Acceptance:** change table search/sort/paginate/responsive behavior once in
`initFancyDataTable` + the contract → every list table moves.

---

## 5. Card Strategy

### 5.1 What exists
base.html primitives: `.card` (+`.card-clip`/`.card-header`/`.card-title`) · `.kpi` ·
`.stat-card` · `.badge` · `.empty-state` — ~78 consumers. Audit (Family G) found
**multiple intentional systems**: dashboard cards, detail cards, timeline cards,
card-lists — page-scoped variants on top of the shared primitives.

### 5.2 Target architecture (strategy, NOT a single forced foundation)
- **Centralize the PRIMITIVES** (`.card .card-header .card-title .stat-card .kpi .badge
  .empty-state`) on §1 tokens (radius/space/shadow/border already mostly `--border-card`/
  `--shadow-card`). One owner = base.html.
- **`.stat-card` = the SummaryCards primitive** shared with Financial (§7).
- **Keep page-scoped card SYSTEMS as documented consumers**, NOT new foundations —
  dashboards/detail/timeline legitimately differ. They must consume the shared primitive +
  tokens; they may add page-scoped layout under a page class (rule 10), never re-define
  card chrome (border/radius/shadow/header).
- **Rule:** a new card style appears in 3+ templates → promote to a base modifier;
  otherwise page-scoped. (CLAUDE.md rule 9/11.)

**Acceptance:** change card border/radius/shadow once → every card moves; page systems
keep their layout but inherit chrome.

---

## 6. Auth Foundation

### 6.1 What exists (debt)
**7 auth templates** (forgot/login/login_password/otp/reset_otp/signup/signup_otp) =
**7 near-duplicate copies** of the same auth shell (audit Auth Report, CC-22).

### 6.2 Target architecture
- **One shared auth foundation:** a single `shared/_auth_shell.html` (split-panel/centered
  card + brand + slot) that each of the 7 pages extends/includes — page supplies only its
  form + copy.
- Built on §1 tokens; inputs via the form foundation (§3); buttons via §2.
- **Backend untouched** — same allauth views/URLs/rate-limit; template-only consolidation.

**Acceptance:** change auth page chrome once → all 7 move. 7 copies → 1 shell + 7 thin pages.

---

## 7. Financial Foundation  *(TC-3 — build, future)*

### 7.1 What exists
Audit found a **hidden, duplicated financial UI** across ~6 surfaces (settlement list,
payroll overview, costing, advances, settlement form, worker earnings): money cells,
status pills, totals bars, grouped ledgers — **shared CONCEPT, duplicated IMPL.**

### 7.2 Target architecture (component set, may use DataTable internally but ≠ DataTable)
| Primitive | Role | Built from |
|---|---|---|
| **SummaryCards** | top KPI/grand-total strip | `.stat-card` (§5) + tokens |
| **MoneyCell** | right-aligned ₹ formatting, sign/zero rules | typography tokens |
| **StatusPill** | settlement/payment status | `--status-*` pairs (§1) |
| **LedgerGrid** | the money table body | may use `initFancyDataTable` (§4) when convertible |
| **TotalsBar / LedgerEmpty** | footer totals (outside engine) + empty state | tokens + `.empty-state` |
| **ResponsiveLedger** | mobile stack/summary contract for money tables | §9 |

- **One owner:** a `shared/financial/` partial set + scoped CSS, tokenized.
- **Convertibility rule (frozen):** Type-2 ledgers become LedgerGrid+TotalsBar only where
  DataTable can be the grid engine with totals kept OUTSIDE the table; structural
  exceptions (grouped workflow forms) stay exceptions.
- **Money formatting is presentation-only** — never moves money logic from backend.

**Acceptance:** change money-cell/pill/totals styling once → every financial surface moves.

---

## 8. Export Foundation  *(TC-5 — build, future, NARROW)*

### 8.1 What exists
Export button-group (CSV/XLSX/PDF) **duplicated inline** in ≥2 pages (barcode_list,
export_list — 3 `<form>`s each, no shared partial) + manifest/regenerate UI.

### 8.2 Target architecture
- **One shared partial** `shared/_export_buttons.html` taking `{csv_url, xlsx_url,
  pdf_url}` (+ optional quick-CSV) → renders the POST form group, tokenized buttons (§2).
- **Stays page-level / outside the table** (proven: barcode_list export forms live in
  `.card-header`, 0 inside `.dataTables_wrapper`).
- **Backend untouched** — same export views/URLs/CSRF; injection-safe (PA-13-6 stays).

**Acceptance:** change export-button layout/labels once → every export surface moves.

---

## 9. Shared Responsive Rules

- **Breakpoint scale (documented constants):** `xs 414 · sm 600 · md 768 · lg 1024`.
  Resolve the 560/600 inconsistency → standardize on this set. (CSS media queries can't
  use `var()`; the scale is a documented constant + a SCSS-free convention, enforced by review.)
- **Table responsive contract (mandatory):** every table = `.table-responsive` +
  `data-label` card-stack OR explicit scroll/summary strategy. `data-label` is INERT
  without a `.table-responsive` ancestor (audit gotcha) → both required.
- **Touch targets ≥ `--touch-min` (44px)** for all interactive controls. Audit recorded
  sub-44 debt (action-link ≈23px, filter-chip 29px) → fixed via §2/§3 during migration.
- **Form-input cells can't shrink → clip; text cells wrap → fit** (audit KEY INSIGHT):
  inline-edit tables need data-label + cell-edit stacking; shared partials must own their
  own responsive CSS.
- **Mobile-first FUNCTIONAL:** worker flows phone-first; management flows desktop+tablet+
  mobile; no UI "complete" without 320/375/390/414 verification.
- **No horizontal overflow** at any audited width (`scrollWidth === innerWidth`).

---

## 10. Migration Order  *(dependency-ordered; each step backend-untouched, template-mostly-intact, separately approved)*

| # | Foundation | Why this order | Risk | Backend |
|---|---|---|---|---|
| **0** | **Design Tokens** (§1: add radius/space/typography/touch/breakpoint to `:root`) | Everything consumes them. Purely additive — nothing repointed yet. | None (additive) | untouched |
| **1** | **Buttons** (§2: tokenize `.btn`, add `.btn-sm`, kill `:not(.btn)` hack, replace inline mini-buttons) | Smallest blast radius; high reuse; unblocks touch-target fixes. | Low | untouched |
| **2** | **Tables — finish A2** (§4: commit A2-CLEAN [owner-timed]; then A2-PAGINATED pagination decision) | Already migrated/verified/held; just close it out. | Low (clean) / Med (paginated=backend) | clean: untouched · paginated: decision |
| **3** | **Forms** (§3: relocate `_form_styles`→shared, tokenize spacing, unify select/date/multiselect/validation owners) | 23 consumers; depends on tokens(0)+buttons(1). | Medium | untouched |
| **4** | **Auth** (§6: 7 copies → 1 `_auth_shell`) | Self-contained; depends on tokens/forms/buttons. | Low-Med | untouched |
| **5** | **Financial Foundation** (§7: TC-3 component set) | New build; depends on tokens+cards+tables. | Medium | untouched (presentation only) |
| **6** | **Export Foundation** (§8: shared `_export_buttons`) | Narrow; depends on buttons. | Low | untouched |
| **7** | **Cards** (§5: tokenize primitives, document page systems as consumers) | Broadest consumer count (78) → do last, lowest urgency, mostly already tokenized. | Low-Med | untouched |

**Per-step cadence (unchanged from audit discipline):** plan → implement one foundation →
browser-verify 320/375/390/414/1280 → STOP → owner review → ONE commit on approval → next.
**No batching. No parallel foundations. Backend stays untouched throughout.**

---

## 11. Ownership Matrix  *(one owner per concern — the contract)*

| Concern | Single owner | Consumed by |
|---|---|---|
| Color/surface/status/shadow tokens | base.html `:root` (+dark) | everything |
| Radius/space/type/touch/breakpoint tokens | base.html `:root` (NEW) | everything |
| Buttons | base.html `.btn`+modifiers | every page |
| Cards (primitives) | base.html `.card/.kpi/.stat-card/.badge/.empty-state` | ~78 surfaces + page systems |
| Forms (chrome/spacing) | `shared/_form_styles.html` | 23+ forms |
| Selects | `fancify()` (base.html) | all selects |
| Dates | `fancifyDate()` (base.html) | opt-in date inputs |
| Multiselects | shared checkbox-chip partial (to build) | worker/perm pickers |
| Validation render | per-field error contract | all forms |
| Tables | `initFancyDataTable` + vendor partials + responsive contract | all list tables |
| Financial UI | `shared/financial/*` (to build) | ~6 money surfaces |
| Export UI | `shared/_export_buttons.html` (to build) | export pages |
| Auth shell | `shared/_auth_shell.html` (to build) | 7 auth pages |
| Responsive contract | §9 rules + base.html media queries | all |

## 12. Governance (keeps it industry-level over time)
- New literal hex/px-radius/inline-font in a template = **review-blocker** (use tokens).
- New component appearing in 3+ templates → **promote to base/shared**; else page-scoped.
- Every new UI ships its responsive + touch-target contract (mobile-first FUNCTIONAL).
- **Docs-sync:** any foundation change updates UI_COMPONENTS.md (locked canon) same session.
- This doc = the permanent architecture; UI_COMPONENTS.md = the locked per-rule registry.

---

**No code authorized by this document.** It is the map. Implementation = the §10 order,
one foundation at a time, each separately approved, backend untouched.
