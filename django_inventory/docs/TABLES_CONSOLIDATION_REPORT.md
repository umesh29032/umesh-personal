---
id: docs-tables-consolidation-report
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Tables Consolidation Report (Phase E)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase E (Tables).**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-049…059 + §"FAMILY E TABLE-SYSTEM COMPLETENESS SCAN")
> + [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (Table-family evidence ledger · TC-1 · A1/A2 split ·
> TC-2 5-type taxonomy · TC-3 financial · TC-4 not-opened · TC-5 export · migration counters).
> Companion reports: Select · Multiselect · Date · Auth · Form-Control (all accepted).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** No code · no migration · no UI_COMPONENTS change · no promotion.
> Date 2026-06-16 · Branch `new_flask_app` · browser-verified where marked; signal-classified items flagged.
> **TC-1 · TC-2 · TC-3 · TC-5 are kept SEPARATE — the separation IS the architecture.**

---

## 1. Coverage — how many table systems exist?

Full grep: **26 templates contain `<table>`**; **0 unclassified.** (`base.html` = the `initFancyDataTable` OWNER, not a page table. `my_earnings`/`roll_detail` = no tables — card/div money.) Classified by **table SYSTEM, not page** (a multi-system page appears in multiple buckets).

| Bucket | Count | What |
|---|---|---|
| **A1** Canonical CRUD Lists (DataTable) | **5** | skill/user/usertype + storefront category/product lists |
| **A2** CRUD/Report drift (no engine) | **6** | master_list · barcode_list · export_list · adda_list · product_list(prod) · roll_list |
| **TC-2** Legitimate exceptions | Type-1..5 (several) | workflow / financial-ledger / inline / matrix / dashboard |
| **TC-3** Financial Foundation consumers | **≈6** | settlement_detail · settlement_list · payroll · worker_detail · costing · settlement_form |
| **TC-5** Export Foundation consumers | **2 trigger + 1 manifest** | barcode_list · barcode_gen panel · export_list |

**Browser-verified-as-table:** 049-059 (Family E) + 036/044 (Phase D). **Signal-classified in the scan** (browser-verified for their original phase concern, table-aspect code-read here): adda_list(004) · product_list-prod(006) · roll_list(015) · dashboards(011/024/025) · stage panels(010/045/071) · product_patterns_edit(007). Flag for targeted re-check if a future phase needs them browser-verified as table-systems.

---

## 2. TC-1 — DataTable Foundation

- **Owner: `base.html`** — `initFancyDataTable(selector, opts)` (single JS bootstrapper) + shared vendor partials `templates/shared/_datatables_vendor_css.html` + `_datatables_vendor_js.html`.
- **Responsibilities:** init · vendor ownership · search · sort · pagination · responsive wrapper (`.table-responsive` + data-label card-stack) · row actions (`.td-actions`/`.action-link`) · empty state (`.empty-state`) · optional filter-row (`filterRowId`, e.g. user_list skill chips).
- **Bootstrapper proof (Q1/Q2):** **5** `initFancyDataTable(` callers; the **only** raw `.DataTable(` is *inside the helper itself* (`base.html:2819`). **No page-specific DataTable wrappers, no init drift.**
- **Consumers (A1):** all 5 A1 tables (049/050/051/018/020) — browser-verified (search filters live, info "X of Y", sort, mobile data-label stack, 0-overflow, console clean).
- **Verdict: STRONG shared foundation.** One owner, responsive-by-default, reused across accounts + storefront. The table-family analogue of the form `_form_styles.html`. **TC-1 = engine only — no financial/export/workflow logic mixed in.**

---

## 3. A1 vs A2 (very important)

**The same business purpose implemented two ways — one canonical, one drifted.**

**A1 — Canonical CRUD Lists** (DataTable engine + search + sort + paginate + shared empty-state + td-actions):
- skill_list(049) · user_list(050) · usertype_list(051) · storefront category_list(018) · product_list(020). **5 consumers, all browser-verified, all on TC-1.**

**A2 — Same purpose, MISSING the DataTable engine** (plain table, but already uses the shared `.table-responsive` + data-label + `.td-actions` primitives — "World A minus the engine"):
| Page | System | Migration A2→A1 |
|---|---|---|
| master_list(056) | CRUD list | **LOW** (add init helper) |
| barcode_list(058) | read-only Report+Export | LOW |
| export_list(059) | Audit/Manifest | LOW |
| adda_list(004) | Adda CRUD list | LOW |
| product_list-prod(006) | Product list | LOW |
| roll_list(015) | Cloth-roll list | LOW-MED |

- **A2 is NOT an exception. A2 = canonical drift** (implemented-incorrectly), distinct from TC-2 (implemented-correctly). Migration difficulty **LOW** (mostly: add `initFancyDataTable`; they already share the responsive/action primitives).
- **Architectural distinction:** *Canonical-but-wrong (A2)* ≠ *Exception-but-right (TC-2)*. Different outcomes. **Do NOT merge A2 into TC-2.**

---

## 4. TC-2 — Legitimate Exception Families (DataTable would damage)

Exception rule applied: *"Would DataTable damage the business workflow?"* YES → exception; NO → A1/A2.

- **Type-1 Workflow Queue** — settlement_list(052) · settlement_detail(036) · stage panels (010/045/071).
  - *Why DataTable fails:* grouped multi-section state (ready/waiting/history), per-row action FORMS (Start/Reverse/Verify), state transitions + money/status/chain. A single sortable/paginated grid would break the section grouping + in-cell forms. **Justified.**
- **Type-2 Financial Ledger** — payroll(053) · costing(055) · worker_detail-advances(054) · settlement_form.
  - *Convertibility:* these are flat money lists + an outside total → **DataTable CAN be the grid engine with totals/cards outside → World-B CONVERTIBLE → fold into A1.** **Mostly NOT true exceptions** (only the money DISPLAY, via TC-3, stays special).
- **Type-3 Inline Editor** — product_sizes_edit(044) · product_patterns_edit(007).
  - *Why DataTable fails:* inputs/forms inside rows, inline save, archive/reactivate per row. DataTable re-render + pagination break row-level form state. **Justified.**
- **Type-4 Matrix** — role_form permission matrix (CC-18) — **the SOLE matrix** (access_control is read-only overview, not a matrix).
  - *Why DataTable fails:* row×column checkbox editing + section bulk-toggle; not a row list. **Justified.** (1 impl → no Matrix Foundation, TC-4 not opened.)
- **Type-5 Dashboard Summary** — worker_detail-page(054) · adda/cloth/barcode dashboards(024/011/025) · access_control(057).
  - *Why DataTable fails (mostly):* aggregates-first (stat-cards / KPIs / read-only overviews); the table is secondary or read-only. DataTable adds little; some sub-tables are convertible. **Investigate-separately.**

---

## 5. TC-3 — Financial Foundation (most important)

**A business component system, NOT DataTable** (it may USE DataTable internally for the LedgerGrid). **Concept shared across ~6 financial pages; implementation duplicated page-scoped.**

| Primitive | Concept shared? | Implementation shared? | Evidence |
|---|---|---|---|
| **SummaryCards** (hero total / stat-cards) | **YES** | **NO** (page-local) | hero `.total .v` ×4 (costing/payroll/settlement_detail/roll_detail) + stat-cards (worker_detail) |
| **MoneyCell** (`₹{{x\|floatformat:2}}`) | **YES** | **NO** (inline Django filter) | ~7 financial pages |
| **StatusPill** (`.pill`) | partial | **NO** | settlement_list + settlement_detail only |
| **LedgerGrid** (money table) | **YES** | **NO** (page-scoped each) | 052·053·054·055·036·settlement_form |
| **LedgerEmpty** (inline `.empty`) | **YES** | **NO** (≠ World-A `.empty-state`) | all financial |
| **ResponsiveLedger** (page-scoped data-label) | **YES** | **NO** (reimplemented ×7) | all financial + 3 production |

- **Consumers ≈ 6** (settlement_detail · settlement_list · payroll · worker_detail · costing · settlement_form).
- **Verdict: the Financial Foundation exists CONCEPTUALLY (consistent recurring primitives) but ownership is FRAGMENTED — each page rolls its own CSS/data-label/empty/total.** No shared partial, no shared component. **This is the future Financial Foundation** (`FinancialFoundation = SummaryCards + MoneyCell + StatusPill + LedgerGrid + LedgerEmpty + ResponsiveLedger`). Keep separate from TC-1.

---

## 6. TC-5 — Export Foundation (narrow)

| Component | Concept shared? | Implementation shared? | Consumers |
|---|---|---|---|
| **ExportButtonGroup** (CSV/XLSX/PDF, 3 POST forms) | **YES** | **NO — inline-duplicated** | barcode_list(058) + barcode_gen panel(071) = **2** |
| **ExportManifest** (audit/history table) | — | page-scoped | export_list(059) = 1 |
| **ExportDownload** (regenerate from live data) | **YES** | service-backed (`barcode_export_service`) | 059 |

- **Shared workflow** (trigger → manifest → download/regenerate), **duplicated implementation** (button-group copy-pasted ×2). **NARROW** (barcode-export only). **Future foundation candidate** — dedupe the button-group into one partial. Keep separate from TC-1.

---

## 7. Enterprise Architecture Direction (most important)

The audit (all families) converges on a clear target architecture:

| Family | Canonical Foundation (owner) | Status today |
|---|---|---|
| Forms | `production/_form_styles.html` | strong (cross-app) + page-scoped tail |
| Selects | class-owned `fancify` path | shared, some `--bare` drift |
| Multiselects | shared checkbox-chip (future) | fragmented (CC-16/17/20) |
| Dates | fancy-date (future) | opt-in, under-applied |
| **Tables (DataTable)** | **TC-1 (base.html `initFancyDataTable`)** | **strong; A2 drift to reclaim** |
| **Financial** | **TC-3 Financial Foundation (future)** | **conceptual, fragmented impl** |
| **Export** | **TC-5 Export Foundation (future, narrow)** | **duplicated ×2** |
| Workflow tables | (exception — no foundation) | legit Type-1 |
| Matrix | (exception — 1 impl, no foundation) | legit Type-4 |

**Principle (proven repeatedly): one owner · one implementation · documented exceptions only. Shared ownership correlates with correctness (TC-1 A1, shared `.form-grid`, `.table-responsive` → all mobile-safe); page-scoped ownership correlates with drift (A2, page-scoped financial ledgers, XC-1 custom grids, duplicated export buttons).** The table family is the clearest case: a strong shared engine (TC-1) with a reclaimable drift set (A2), legitimate exceptions (TC-2), and two emerging business-component foundations (TC-3 financial, TC-5 export) that exist as concepts but are duplicated in code.

---

## 8. Decision asks (nothing happens without these)

1. Approve **TC-1** = the DataTable Foundation (base.html `initFancyDataTable` + shared vendor) as the canonical table engine.
2. Approve the **A1 vs A2** distinction (A2 = canonical drift, LOW-effort A1 migration, NOT an exception).
3. Confirm **TC-2** legitimate exception families (Type-1 Workflow · Type-3 Inline · Type-4 Matrix · Type-5 Dashboard) — and that **Type-2 Financial ledgers are CONVERTIBLE** (grid → A1, money display → TC-3).
4. Endorse **TC-3 Financial Foundation** as a future business-component system (concept proven, impl fragmented, ~6 consumers).
5. Endorse **TC-5 Export Foundation** as a future (narrow) candidate.
6. Confirm **TC-1 · TC-2 · TC-3 · TC-5 stay SEPARATE** (the separation is the architecture).
7. Only then (separate future phase): any code / migration / UI_COMPONENTS promotion.

**Until then: no changes. Table evidence FROZEN. UI_COMPONENTS.md untouched. No implementation / no migration.**

---

## Table evidence — FROZEN 2026-06-16
TC-1 (DataTable engine, 5 A1 consumers) · A1/A2 split (5 canonical / 6 drift) · TC-2 (5-type exceptions) · TC-3 (Financial Foundation, Evidence B, ≈6) · TC-4 (not opened, 1 matrix) · TC-5 (Export, narrow). Migration counters: A2→TC-1 (6) · Financial→TC-3 (≈4-6) · Export→TC-5 (2) · Workflow/Matrix → no foundation (single each). Kept separate. No promotion / no standardization until owner decision asks (§8). Next family on owner go: **F — Modals** (or remaining surfaces).
