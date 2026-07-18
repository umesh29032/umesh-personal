---
id: docs-frontend-design-system-status
type: status-anchor
status: active
owner: handwritten
scope: campaign
anchors: —
verified: 2026-07-18
---

> # ⛔ SUPERSEDED (2026-06-15)
> This phase-based audit is **superseded** by the per-HTML
> [HTML_AUDIT_MASTER.md](HTML_AUDIT_MASTER.md) +
> [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (4-file system:
> + HTML_CANONICAL_CANDIDATES.md + HTML_FIX_HISTORY.md). **Do NOT run this audit
> in parallel.** Its 20-template inventory (`FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json`)
> is retained as **SEED evidence only** and imported into the new inventory. Kept
> for history; not the active tracker.

# Frontend Design System Consolidation Audit — STATUS

> **Single source of control** for reusable frontend components. Goal: eliminate UI
> drift, prevent mobile/desktop inconsistency. This is **inventory + classification**,
> not a redesign. Builds AFTER the closed 18-phase Production Readiness Audit
> ([PRODUCTION_AUDIT_STATUS.md](PRODUCTION_AUDIT_STATUS.md)).

- **Date:** 2026-06-15
- **Branch:** `new_flask_app`
- **Scope:** 113 content templates + `base.html` (the canonical CSS/JS source) across 7 apps.
- **Companion artifacts:** [`FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json`](FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json) (raw per-template records, 20/113), [UI_COMPONENTS.md](../UI_COMPONENTS.md) (existing component registry).

## Hard constraints (apply to every phase)

- ❌ No redesign · no color/branding change · no visual refresh.
- ❌ No Tailwind / React / Bootstrap. No new library unless a **verified** bug cannot be solved with existing project patterns.
- ❌ No speculative abstractions. Only standardize **proven existing** patterns.
- ✅ Mobile-first is a functional requirement. Verify every component at **320 / 375 / 390 / 414 / desktop 1280**. (Phase 01 is inventory-only — no viewport testing yet; that happens per-component in Phases 02–07.)

---

## ⚠️ PHASE 01 STATUS: IN PROGRESS (PARTIAL) — 20 / 113 templates

Phase 01 was run as a 12-chunk parallel inventory workflow. It **hit the account
session limit mid-run** (resets 9pm Asia/Kolkata, 2026-06-15). Per the session-limit-safe
rule, work **STOPPED at the phase boundary** — Phase 01 is **not complete** and the
remaining chunks are **NOT** marked clean / NOT fabricated.

### Owner directives (2026-06-15) — binding until Phase 01 = 100%

A partial inventory is **not** acceptable. Phase 01 succeeds ONLY when 100% of
targeted templates are classified AND the final synthesis is produced. Until then:

1. ❌ Do NOT create canonical standards.
2. ❌ Do NOT recommend migrations.
3. ❌ Do NOT update `UI_COMPONENTS.md`.
4. ❌ Do NOT commit Phase 01.
5. ⚠️ ALL findings below are **PROVISIONAL** — observations only, no decisions.

### Phase 01 completion criteria (definition of done)

- [ ] Total templates audited = total templates discovered (113/113).
- [ ] Every **select** implementation classified.
- [ ] Every **multiselect** implementation classified.
- [ ] Every **date-input** implementation classified.
- [ ] Every **modal** implementation classified.
- [ ] Every **table** implementation classified.
- [ ] Every **form-layout** implementation classified.
- [ ] Every **button / badge / chip** implementation classified.
- [ ] Every reusable component grouped into canonical **families** (grouping only — NOT standard selection).
- [ ] Final synthesis produced AFTER 100% coverage.

Only when every box is checked does Phase 01 become COMPLETE and the basis for Phase 02.

| Chunk | Templates | Status |
|---|---|---|
| A — accounts auth (8) | forgot_password, home, login, login_password, otp, reset_otp, signup, signup_otp | ✅ DONE |
| H — production worker report (5) | _worker_report_body, worker_report_embedded, worker_report, _worker_report_styles, _workers_widget | ✅ DONE |
| J — storefront (7) | category_confirm_delete, category_form, category_list, product_confirm_delete, product_form, product_list, croppable_image | ✅ DONE |
| B — accounts CRUD (11) | skill/user/usertype forms + lists + deletes + _user_form_styles | ⏳ PENDING (session limit) |
| C — expense (8) | settlement detail/list, advance/settlement/worker_profile forms, my_earnings, payroll_overview, worker_detail | ⏳ PENDING |
| D — production addas+reports (9) | adda dashboard/detail/form/list, adda_report_review, pending_reports, stalled_addas, _activity_feed, _autosave | ⏳ PENDING |
| E — production workspaces/costing (8) | barcode_gen, costing, cutting form/workspace, layering, product_flow, _form_styles, _layering_summary | ⏳ PENDING |
| F — production patterns/products (9) | pattern form/list/workspace/delete, product form/list/archive/patterns_edit/sizes_edit | ⏳ PENDING |
| G — production stages+panels (12) | stage form/list/delete/rate_correct/rate_list, _stage_panel_* (×6), stage_panel_embedded/standalone | ⏳ PENDING |
| I — raw_materials (11) | cloth/raw_material dashboards, master form/list/deletes, roll assign/bulk/detail/edit/list | ⏳ PENDING |
| K — inventory/core + errors + shared (18) | 403/404/500, public_home, dashboard, access_control, role_*, sidebar_access_list, accordions, icons, _time_log_styles, user_dashboard, _datatables_vendor_* | ⏳ PENDING |
| L — tracking (8) | barcode dashboard/list/print_sheet, export_list, adda/roll history, scan_detail | ⏳ PENDING |

**Resume Phase 01** (after 9pm IST limit reset) — caches the 3 done chunks, re-runs the 9 failed chunks + synthesis:

```
Workflow({
  scriptPath: "/home/tech/.claude/projects/-home-tech-umesh-personal-django-inventory/87004968-1f65-4335-97b9-6f4fbab57a0e/workflows/scripts/fds-phase01-inventory-wf_60a4d6b7-0b9.js",
  resumeFromRunId: "wf_60a4d6b7-0b9"
})
```
(Session-scoped path. If the session is gone, just re-run the workflow fresh — `base.html` is unchanged so chunk re-reads are deterministic.)

Then write the final, full-coverage Phase 01 doc and only then mark Phase 01 DONE and proceed to Phase 02.

---

## Phase ledger

| # | Phase | Output | Status |
|---|---|---|---|
| 01 | UI Inventory | this doc + inventory JSON | 🟡 IN PROGRESS (20/113) |
| 02 | Select + Multiselect audit | SELECT_STANDARD | ⏳ PENDING |
| 03 | Input audit (text/number/date/textarea/checkbox/radio) | FORM_CONTROL_STANDARD | ⏳ PENDING |
| 04 | Table audit | TABLE_STANDARD | ⏳ PENDING |
| 05 | Filter + search bar audit | FILTER_STANDARD | ⏳ PENDING |
| 06 | Form layout audit | FORM_LAYOUT_STANDARD | ⏳ PENDING |
| 07 | Modal + Card + Status audit | UI_FEEDBACK_STANDARD | ⏳ PENDING |
| 08 | Final consolidation | FRONTEND_DESIGN_SYSTEM_SUMMARY.md | ⏳ PENDING |

Session-limit rule: STOP at phase boundary, never continue into the next phase, always update this doc, resume from the next unfinished phase (currently: finish Phase 01).

---

## PROVISIONAL signals (from the 20 completed templates ONLY)

> ⚠️ **PROVISIONAL — not decisions, not recommendations, not canonical selections.**
> Evidence-backed observations from chunks A/H/J only. The production/inventory/expense
> bulk (93 templates) is still un-inventoried and will change this picture. No standard
> is chosen and no migration is proposed here — that is deferred to Phase 02+ AFTER
> Phase 01 reaches 100% coverage. Do not act on anything in this section.

### Inventory summary (partial, 20/113)

| Metric | Count (of 20) |
|---|---|
| Extend `base.html` | 8 (home, worker_report, 5 storefront, +) |
| Standalone HTML docs (bypass base) | 9 (all 8 auth pages + worker_report_embedded) |
| Carry local component CSS (not just page scoping) | 11 |
| Flagged with ≥1 duplicate implementation | 18 |
| Templates with NO drift | 2 (worker_report.html wrapper, worker_report_embedded wrapper — thin shells) |

### Drift hotspots (partial)

1. **Auth set (8 pages) bypasses `base.html` entirely.** Each re-declares its own
   `.field`, `.alert`/`.alert-*` (duplicating base `.msg`), `.btn-cta`/`.btn-verify`/`.btn-google`
   (duplicating base `.btn`/`.btn-copper`/`.btn-ghost`), and `.card`. The split-screen
   `.page/.left/.right/.form-shell` brand layout is copy-pasted across `login`, `login_password`,
   `signup` **with drift** (input border `#b8a48e` vs `--cream-2`; input font Inter vs Syne; left-pane flex 55% vs 42%).
2. **OTP 6-digit widget copy-pasted 3×** (`otp`, `reset_otp`, `signup_otp`) with **behavioral drift**
   (auto-submit + 60s countdown present in `otp`/`signup_otp`, missing in `reset_otp`). One reusable widget, three forks.
3. **Auth validation is inconsistent:** 7/8 surface only `messages` banners (no per-field errors);
   only `signup.html` does the proper `form.errors` per-field loop (the cleanest pattern).
4. **`.btn-danger` overridden with inline `background:#dc2626;color:white`** on both storefront
   confirm-delete pages — redundant restyle on top of the canonical token.
5. **Token bypass:** `croppable_image.html` hardcodes `#b87333/#0e0b09/#7a6a58/…` instead of
   `var(--copper)` etc.; `home.html` uses off-palette `#e5e7eb/#3b82f6` inline-styled mockup buttons.
6. **Unscoped `section{} !important` element selectors** leak globally in `category_form.html`
   and `product_form.html` (rule-10 violation) — numbered panels built inline instead of `.panel`.
7. **Storefront list pages fully meet the responsive-table standard** (`.table-responsive` +
   `td[data-label]` + `initFancyDataTable`) — but `th/td` are heavily inline-styled per cell.

### SELECT + MULTISELECT deep-dive (partial — seeds Phase 02)

| Pattern | Where (of 20) | Verdict |
|---|---|---|
| Native `<select>` (auto-upgraded by `fancify()`) | storefront: `category_list` (1, `.filter-select`), `product_list` (2, `.filter-select`), `product_form` (2, `.sf-input`) | ✅ Canonical path (fancy-select). Filter selects use a local `.filter-select` class, not a documented filter-control canonical. |
| `<select multiple>` (fancify **SKIPS** these — canonical GAP) | `_workers_widget.html` (1, via Django `ModelMultipleChoiceField`) | ⚠️ **No canonical multiselect.** Rendered as a hand-rolled checkbox-chip grid (`.workers-grid`/`.worker-chip`). De-facto multiselect pattern → promote in Phase 02. |
| `custom_local` select replacement (hand-rolled, not fancy-select) | `_worker_report_body.html` (chip-picker: hidden input + `.chip-row` buttons + JS, single-select) | Clean touch pattern; classify as the canonical **chip single-select** for mobile worker capture. |
| `data-no-fancy` opt-outs | none seen yet | — |
| Searchable selects | none seen yet | — |

**Phase 02 entry note:** the multiselect gap is confirmed real — `fancify()` early-returns on
`select.multiple`. The two non-native select replacements (checkbox-chip multi, chip single) are
the candidates to standardize. Re-scan the 93 pending templates for any `<select multiple>` and
any searchable/typeahead select before locking SELECT_STANDARD.

### Modals (partial — seeds Phase 07)

- **There is no canonical modal component in `base.html`.** The only modal in the 20 done
  is `croppable_image.html` — a hand-built custom-overlay (`position:fixed; inset:0; z-index:10000;
  backdrop blur`, JS show/hide, Escape + backdrop close). Phase 07 must define one modal standard
  and re-skin this overlay's buttons to `.btn-copper`/`.btn-ghost`.
- Other "modal-ish" patterns seen: `confirm()` (worker report submit), native confirm-card pages
  (storefront deletes use base `.confirm-card`).

### Repeated patterns observed so far (PROVISIONAL — no decisions, no migrations)

> Listed purely to track *where the same pattern recurs*. No "best" implementation is
> chosen and nothing is promoted here. Canonical-family grouping + any migration call
> happens only after 100% coverage, in Phase 02+.

| Pattern recurs | Seen in (of 20) | Provisional note (deferred) |
|---|---|---|
| Split-screen auth layout | `login`, `login_password`, `signup` | Duplicated with drift — revisit after full coverage |
| 6-digit OTP widget | `otp`, `reset_otp`, `signup_otp` | 3 forks, behavior diverges — revisit later |
| Multiselect (no native `<select multiple>` canonical) | `_workers_widget` | fancify GAP confirmed — classify all multiselects before deciding |
| Chip single-select replacement | `_worker_report_body` | touch pattern — classify all such before deciding |
| Confirm-delete page (base `.confirm-card`) | `category_confirm_delete`, `product_confirm_delete` | already on a base pattern — note only |
| List-page scaffold | `category_list`, `product_list` | near-identical structure — note only |
| Chromeless iframe embed scaffold | `worker_report_embedded` ↔ `stage_panel_embedded` (pending chunk G) | shared resize contract — note only |

---

## Open questions / risks for later phases

- **Auth-set refactor is the single biggest drift item but also the riskiest** (auth is
  security-sensitive + standalone-by-design for the login chrome). Decide in Phase 06 whether to
  unify under a shared `_auth_base.html` or leave standalone and only dedupe the OTP widget.
- **`.filter-select` vs `.ke-toolbar` vs `.filter-card`** — three filter idioms already; Phase 05
  must pick one canonical filter-control.
- **Inline `th/td` styling on DataTables lists** — Phase 04 should decide on a class-driven cell
  system vs leaving inline (low value, high churn).
- The 93 pending templates (esp. production stage panels, costing, cutting/layering workspaces)
  are the densest UI and will dominate the final standard — **do not lock any *_STANDARD before
  Phase 01 is complete.**

---

## Changelog

- **2026-06-15** — Phase 01 launched (12-chunk parallel inventory). Completed chunks A/H/J (20 templates) before account session limit (resets 9pm IST). Raw records saved to `FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json`. Phase 01 left IN PROGRESS at the phase boundary; resume instructions above.
