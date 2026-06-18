# DESIGN SYSTEM — FINAL IMPLEMENTATION MASTERPLAN

> **The single execution reference.** Consolidates architecture + roadmap + all foundation
> matrices into one locked plan. **DESIGN ONLY — no code in this doc.** Phases approved + run
> one at a time, each through the per-stage gate.
>
> **Created 2026-06-16** (baseline HEAD `49578fc0`). **Refreshed 2026-06-18** (HEAD `b6cccd49`)
> to match the actually-shipped state — the old "remaining" list predated the Forms/Auth/Cards/
> Financial/Inputs/Tables work that has since landed.

---

## Architecture principles

- **One owner per concern** — exactly one file controls each concern; pages consume it, never re-declare it.
- **Public APIs only** — consume an owner's classes / tags / behaviors; never reach past its surface or fork it.
- **Byte-identical migrations preferred** — prove computed-identical; a visual change is the exception, not the default.
- **Visual convergence requires explicit approval** — no silent restyle during a migration.
- **Tokens first, skins second** — values live in `:root`; skins parameterize via tokens (`--input-*`, `--select-*`).
- **Backend / business logic untouched** — template + CSS only, unless a backend change is separately surfaced + approved.
- **FancySelect and FancyDate are behavior owners** — every `<select>` / `<input type=date>` upgrades through them (opt-out via `data-no-fancy`); never hand-roll a dropdown or calendar.

---

## 0. Status ledger — what actually shipped

### ✅ COMPLETE
| Foundation | Phase(s) | Commits | Result |
|---|---|---|---|
| Tokens | 0a | (pre-baseline) | `:root` global + semantic + dark — the one token source |
| Buttons (core) | B-1 / B-2 / B-3 | `ff1d5702` / `0317a65d` / `138dafab` | `.btn*` primitives canonical |
| Governance | Phase A | `2b7170f1` / `3e63f6de` / `49578fc0` | styleguide + `ds_lint` ratchet + SPEC/CATALOG frozen |
| **Forms** | F-1→F-5 | `6ff4eedb` (relocate) · `9b534995` F-2 · `0702a8bb` F-3 · `e1bcfc29`+`0f9db734`+`80c83a63` F-4 · `82f8bc3b` F-5 | **CLOSED** — `.field` single-owner; validation unified; multiselect → chip widget |
| **Auth** | C-1 / C-2 | `1166ae8d` (owner) · `43c8569b` · `5da4ba16` (OTP) · `780c643c` (login) | `_auth_shell.html` built; **5/7 pages** migrated byte-identical |
| **Inputs / Select / Date** | F-1 / F-2c / Select S1 | `25df8d2c` tokens · `a734a00c`+`cc1ec5c8` arrow+date · `4028d493` select owner | `--input-*` + `--select-*` tokens; `.select-field--form/--filter`; native dates → FancyDate |
| **Dropdowns (mobile)** | — | `7b045e84` · `fd5ddcc2` · `b6cccd49` | FancySelect/FancyDate now **opt-out + mobile-safe** everywhere (incl. iframes, dynamic rows, Django `DateInput` widgets); fancy CSS+JS+observer extracted to `_fancy_controls.html` |
| **Tables** | A2-CLEAN | `b06a5957` | `initFancyDataTable` on product / master / barcode lists (was HELD — now committed) |

### ⚠️ PARTIAL — owner exists, scope intentionally narrow (more is OPTIONAL)
| Foundation | Done | Not done (optional) |
|---|---|---|
| **Cards (D)** | `ccbfe8f7` D-1 (converge `.card`) · `b62b6157` D-2a (`.stat-card--serif`, user_dashboard) — **FROZEN at D-2a** | D-2b / D-2c — remaining inline-chrome consumer sweep |
| **Financial (E)** | `e8c0181e` E-1 (`{% money %}`) · `466f7d75` E-2 (`.status-pill`) | `shared/financial/` owners — LedgerGrid · TotalsBar (SummaryCards/MoneyCell delivered as tag+pill instead of partials) |
| **Export (F)** | `14b819b2` **Stage 1 (INERT)** — `_export_buttons.html` owner built; barcode_list + barcode_gen CSV/XLSX/PDF trios migrated byte-identical (computed-equal, console/overflow clean) | **Stage 2 (VISUAL)** — icons · label/variant convergence · `.action-link` pills (barcode_dashboard) · print-sheet button |

### ⏸️ FROZEN / DEFERRED (intentional — not pending work)
- **Cards full 60-consumer sweep** — frozen at D-2a by owner decision; primitives are canonical, remaining consumers cosmetic.
- **Auth signup + signup_otp** — deferred; they are standalone `<!DOCTYPE>` docs, not on `_auth_shell` (signup flow gated separately).
- **A2-PAGINATED** (3 large list pages) — deferred pending a pagination decision.
- **Component-token tier** (`--btn-radius`…), Storybook + visual-regression CI, React/Tailwind port, npm/versioning — future capability, separate triggers.

### ❌ REMAINING (real, not started) → see §6 roadmap
- **Export Stage 2 (VISUAL)** — owner shipped (Stage 1, see §0 PARTIAL); convergence pass not started.
- **Buttons B-4 / B-5 / B-6** — rationalization, escaped-raw convergence, touch/a11y pass.

---

## 1. Canonical owners (shipped — one place per concern)

| Concern | Owner | File | Notes |
|---|---|---|---|
| Auth chrome | `_auth_shell.html` | `config/templates/shared/_auth_shell.html` | brand panel + centered card + form slot; 5/7 auth pages |
| Form chrome | `.field` (+ `.form-shell` · `.panel`/`.panel-*` · `.field-error` · `.worker-chip`) | `config/templates/shared/_form_styles.html` | the form single-source; `.panel` = form-shell numbered panels |
| Surface primitives | `.card` · `.stat-card` (+ `.kpi`) | `config/accounts/templates/accounts/base.html` | card/stat/kpi chrome; pages consume, never re-declare |
| Money text | `{% money %}` | `config/core/templatetags/finance.py` | `₹` + `floatformat:2`, byte-identical; never does math |
| Status badges | `.status-pill` (+ `--draft/--finalized/--reversed/--superseded`) | `config/accounts/templates/accounts/base.html` | settlement/ledger status |
| Selects | `.select-field--form` / `.select-field--filter` | `config/accounts/templates/accounts/base.html` (skins/tokens) | one chevron source; geometry skins |
| FancySelect + FancyDate (behavior) | `fancify` · `fancifyDate` · MutationObserver | `config/accounts/templates/accounts/_fancy_controls.html` | **extracted from base.html 2026-06-18**; opt-out; included by base.html + every standalone iframe/print doc |
| Table engine | `initFancyDataTable()` + vendor partials | `base.html` + `config/templates/shared/_datatables_vendor_{css,js}.html` | search/sort/paginate + responsive contract |
| Styleguide | `inventory/styleguide.html` | live gallery at `/inventory/styleguide/` | demonstrates, never defines |
| Governance | `ds_lint.sh` | `scripts/ds_lint.sh` | pre-commit ratchet — blocks NEW inline raw values |

> **`_fancy_controls.html` is the owner of the fancy CSS+JS+observer.** Any document that does
> NOT `{% extends "accounts/base.html" %}` (iframe panels, print sheets) MUST `{% include %}` it
> + define the tokens it uses — else its native `<select>`/date popups misposition inside the iframe.

---

## 2. Per-stage gate (every remaining phase)

implement → browser-verify 320/375/390/414/1280 → `scrollWidth==innerWidth` → console clean →
show diff → **STOP** → approve → commit. **INERT** = computed-identical proof; **VISUAL** =
before/after + sign-off. Backend untouched except explicitly approved.

---

## 3. Architecture tree (★ = permanent owner / API file)

```
config/
├─ accounts/templates/accounts/
│   ├─ base.html ...................... ★ TOKENS (:root global+semantic+dark) + PRIMITIVES
│   │                                     (.btn .card .kpi .stat-card .badge .status-pill
│   │                                      .empty-state .action-link .action-icon
│   │                                      .select-field--form/--filter) + app shell      ✅
│   └─ _fancy_controls.html ........... ★ FANCYSELECT + FANCYDATE + observer (CSS+JS)      ✅ NEW
├─ core/templatetags/
│   └─ finance.py ..................... ★ {% money %} (₹ format)                           ✅
├─ templates/
│   ├─ shared/
│   │   ├─ _form_styles.html .......... ★ FORMS (.form-shell · .field · .panel · chips)    ✅
│   │   ├─ _datatables_vendor_css.html
│   │   ├─ _datatables_vendor_js.html . ★ TABLES vendor (engine = initFancyDataTable)      ✅
│   │   ├─ _auth_shell.html ........... ★ AUTH (brand + card + slot) — 5/7 pages           ✅
│   │   ├─ _export_buttons.html ....... ★ EXPORT (CSV/XLSX/PDF group)              ✅ S1 (S2 visual TODO)
│   │   └─ financial/ ................. ★ FINANCIAL partials                       [partial]
│   │        ├─ (MoneyCell → delivered as {% money %})                            ✅ (tag)
│   │        ├─ (StatusPill → delivered as .status-pill)                          ✅ (class)
│   │        ├─ summary_cards.html ....                                           [optional]
│   │        ├─ ledger_grid.html ......                                           [optional — D]
│   │        └─ totals_bar.html .......                                           [optional]
│   └─ inventory/styleguide.html ...... ★ LIVING GALLERY                                    ✅
├─ <app>/templates/<app>/*.html ....... PAGES — consume owners; zero page CSS / inline
├─ scripts/ds_lint.sh ................. ★ GOVERNANCE ratchet                               ✅
└─ docs/
    ├─ DESIGN_SYSTEM_MASTERPLAN.md .... this file
    ├─ DESIGN_SYSTEM_SPEC.md .......... rulebook (contract)                                ✅ frozen
    └─ UI_COMPONENTS_CATALOG.md ....... per-component reference                            ✅ frozen
```

---

## 4. Ownership map (boundaries)

### `base.html` — Tokens + Primitives + Shell
- **OWNS:** all design tokens (`:root` + dark) · button primitives (`.btn*`) · surface primitives
  (`.card`/`.kpi`/`.stat-card`) · `.badge` · `.status-pill` · `.empty-state` ·
  `.action-link`/`.action-icon` · `.select-field--form/--filter` skins + `--select-*` tokens ·
  the app shell (sidebar/topbar) · global responsive rules · **includes `_fancy_controls.html`**.
- **MUST NOT OWN:** composed-surface CSS (form-shell, auth shell, financial, export) ·
  the fancy behaviors themselves (now in `_fancy_controls.html`) · page-specific layout · business markup.

### `_fancy_controls.html` — FancySelect + FancyDate (behavior owner, NEW 2026-06-18)
- **OWNS:** `.fancy-select*` + `.fancy-date*` CSS · `fancify`/`fancifyDate` · the MutationObserver
  that auto-upgrades dynamically-added `<select>`/`<input type=date>` (opt-out via `data-no-fancy`).
- **MUST NOT OWN:** tokens (→ base) · the closed-state `.select-field` skin geometry (→ base).
- **CONSUMED BY:** `base.html` (include) + standalone iframe/print docs
  (`stage_panel_embedded` · `worker_report_embedded` · `barcode_print_sheet`).

### `shared/_form_styles.html` — Forms ✅ CLOSED
- **OWNS:** `.form-shell` · numbered `.panel`/`.panel-*` · `.field`/`.field-error` · cream/r10 inputs ·
  `.form-error` box · `.worker-chip`/`.workers-grid` · `.sticky-actions` · `.breakup-table`.
- **MUST NOT OWN:** button geometry (→ `.btn`) · tokens (→ `:root`) · table engine.
- **CONSUMED BY:** ~17 create/edit/workspace pages.

### `shared/_auth_shell.html` — Auth ✅ (5/7)
- **OWNS:** auth chrome — brand panel + centered card + form slot.
- **CONSUMED BY:** login · login_password · otp · reset_otp · forgot_password.
- **NOT YET:** signup · signup_otp (deferred — standalone docs).

### `core/templatetags/finance.py` — Money ✅ · `base.html .status-pill` — Status ✅
- **OWN:** `₹` text formatting (template-only) · settlement/ledger status badge.
- **MUST NOT OWN:** any money math · ledger writes · the golden ₹225 chain (server-side).

### `shared/_export_buttons.html` — Export ✅ Stage 1 (INERT)
- **OWNS:** the CSV/XLSX/PDF POST export form group (csrf + tokenized `.btn` buttons). Labels +
  per-format variant are caller args; included WITHOUT `only` so `csrf_token` resolves.
- **MUST NOT OWN:** export view logic / routes / cell escaping (server-side) · button geometry (→ `.btn`).
- **CONSUMED BY:** `barcode_list` · `_stage_panel_barcode_gen` (both live, byte-identical).
- **STAGE 2 (VISUAL, TODO):** icons · label/variant convergence · fold in `barcode_dashboard` `.action-link` pills + the standalone `barcode_print_sheet` print button.

### `shared/financial/*` — Financial UI [PARTIAL]
- Money + status delivered (tag + pill). **Remaining (optional):** `ledger_grid.html` · `totals_bar.html` ·
  `summary_cards.html` for settlement/payroll/costing surfaces.

### Tables — `initFancyDataTable()` + vendor partials ✅
- **CONSUMED BY:** A1 (5) + A2-CLEAN (3, now committed). A2-PAGINATED (3) deferred.

---

## 5. Confirmations
- ✅ A2-CLEAN **committed** (`b06a5957`) — product_list · master_list · barcode_list (was HELD).
- ✅ Backend untouched except explicitly approved (additive `/styleguide/` route; no widget edits were needed — date fix is JS opt-out, not forms.py).
- ✅ Golden ₹225 chain unaffected by any UI work.

---

## 6. Remaining roadmap (execution order)

| # | Phase | Foundation | Files | Risk | Visual? | Kind |
|---|---|---|---|---|---|---|
| — | ~~F — Export Stage 1~~ | Export | `shared/_export_buttons.html` owner + barcode_list/barcode_gen | LOW | none | ✅ DONE `14b819b2` (INERT) |
| 1 | **F — Export Stage 2 (VISUAL)** | Export | icons + label/variant convergence + `.action-link` pills + print-sheet button | MED | YES | OPTIONAL (owner already shipped) |
| 2 | **B-4 Buttons** | Buttons | inline-mini (7) + inline-styled (15) + `.btn-mini` (2) → `.btn*` | MED | YES (rationalize) | OPTIONAL |
| 3 | **B-5 Buttons** | Buttons | escaped raw (`.lybtn` 6 · next-up · so-tile) + delete `.lybtn` | LOW | small | OPTIONAL |
| 4 | **B-6 Buttons** | Buttons | base touch ≥44 + `:focus-visible` · `.action-link`/`.action-icon` | LOW–MED | YES (intended a11y) | FUTURE (separable, important) |
| 5 | **Cards D-2b / D-2c** | Cards | remaining inline-chrome consumers (beyond D-2a) | LOW–MED | mostly NO | OPTIONAL (frozen until resumed) |
| 6 | **Financial LedgerGrid / TotalsBar** | Financial | NEW `shared/financial/ledger_grid.html` · `totals_bar.html` + ~10 surfaces | MED–HIGH | YES (new components) | OPTIONAL (money+status already owned) |

**Resume point:** Export owner shipped (Stage 1, `14b819b2`) — all mandatory owners now exist.
Next per owner's plan: **Buttons B-4 → B-5 → B-6**. Export Stage 2 (VISUAL), Cards D-2b/2c,
Financial LedgerGrid/TotalsBar = optional polish, separate approval.

---

**Masterplan only — no code, no migration.** Approve phases one at a time; each runs the per-stage gate.
