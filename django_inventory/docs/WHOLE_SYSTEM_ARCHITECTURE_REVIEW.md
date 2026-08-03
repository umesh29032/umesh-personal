---
id: docs-whole-system-architecture-review
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Whole-System Frontend Architecture Review (post-audit)

> **The one-time architecture decision pass.** Evaluated ONLY from the FROZEN audit evidence (Families A-G:
> inventories, ownership maps, consumer counts, browser findings + all family reports). **Architecture proposals
> only — NO code, NO migration executed.** Nothing here ships without explicit per-item owner approval.
> Date 2026-06-16 · Branch `new_flask_app`.
>
> **Foundation-test (applied to every system):** a canonical foundation is justified ONLY when (a) a real
> shared CODE owner exists or is cheap to extract, (b) it has multiple genuine consumers, (c) convergence
> removes real divergence/drift, and (d) it does NOT force unrelated surfaces into one abstraction.
> **Popularity ≠ foundation. Consumer count ≠ foundation. Shared primitive ≠ foundation.**

---

## 0. Root of the tree — `base.html`

`base.html` is the de-facto foundation root (**78 consumers**): layout (sidebar/topbar/overlay), global JS
(`fancify`, `fancifyDate`, `initFancyDataTable`, `toggleSidebar`), shared CSS primitives (`.card`/`.kpi`/
`.stat-card`/`.form-control`/`.table-responsive`/`.empty-state`/`.btn`). **It already IS the canonical owner of the
low-level primitives.** Foundations below either live in base.html or in shared partials it cooperates with.
**Decision: keep base.html as the primitive owner; do NOT split it.** Primitives (`.card`/`.kpi`/`.stat-card`)
stay LOW-LEVEL primitives, not "Card Foundations".

---

## 1. Per-system evaluation

Columns: **Canonical?** · **Code owner exists?** · **Mature?** · **Migration safe?** · **Backend untouched?** · **Exceptions** · **Order**

### Forms → `production/_form_styles.html`
- **Canonical? YES.** **Owner exists? YES** (`_form_styles`, **19 consumers, cross-app**). **Mature? YES** (responsive `.form-grid` collapses ≤768; per-field `.field-error`; browser-proven safe across 6+ surfaces). **Migration safe? YES** (template/CSS only). **Backend untouched? YES.**
- **Adopt `_form_styles` as the canonical Form foundation.** `_user_form_styles`(4, management) = a sibling that should **fold into / align with** it (same per-field-inline model). **Converge:** base-`.form-card` page (pattern_form, CC-30 under-built) + auth forms (CC-22) → onto `_form_styles`. Raise `.sf-input` to ≥44px (CC-05).
- **Exceptions:** none structural. **Migration order: 3** (after A2-tables + dates).

### Selects → class-owned `fancify` path (base.html)
- **Canonical? YES.** **Owner exists? YES** (base.html `fancify()` + `.fancy-select-*`). **Mature? YES** (single JS owner; `--bare` fallback). **Safe? YES. Backend untouched? YES.**
- **Adopt fancify as canonical.** **Exceptions:** native `<select multiple>` (fancify skips — correct); the `--bare` fallback is a styling gap to tidy, not a new system. Fix CC-01 keyboard-grid once (shared with fancy-date). **Order: 4** (low; mostly already canonical).

### Multiselects → shared checkbox-chip (FUTURE)
- **Canonical? NOT YET — propose to BUILD.** **Owner exists? PARTIAL** (CC-16 `_WorkerCheckboxes` chip = closest; CC-17 `.chip-pick` + CC-20 bare + CC-18 matrix diverge). **Mature? NO** (4 implementations, CC-19 duplication). **Safe? MEDIUM. Backend untouched? YES.**
- **Propose ONE shared checkbox-chip** (native checkbox + `label[for]` a11y of CC-20 + chip look of CC-16 + ≥44px); converge CC-17/CC-19/CC-20; **worker-picker = one widget everywhere** (resolve CC-16/CC-20 split). **Exception: CC-18 permission matrix** = its own control (Type-4, stays). **Order: 5.**

### Dates → fancy-date (base.html)
- **Canonical? YES (target).** **Owner exists? YES** (base.html `fancifyDate` + `.fancy-date-*`). **Mature? YES but UNDER-APPLIED** (1 consumer: birth_date). **Safe? YES** (opt-in attr). **Backend untouched? YES.**
- **Adopt fancy-date as canonical for SINGLE-VALUE form dates;** roll out `data-fancy-date` to `purchased_date`/`advance_date`/`settlement_date`/`joining_date`. Add CC-01 keyboard-nav before wide rollout. **Exceptions:** dashboard date-RANGE filters stay native (range, intentional); standalone print/no-base surfaces stay native. **Order: 2** (low, opt-in).

### Tables → TC-1 DataTable foundation (base.html `initFancyDataTable` + vendor)
- **Canonical? YES.** **Owner exists? YES** (`initFancyDataTable` sole bootstrapper + shared vendor partials; **5 A1 consumers**). **Mature? YES** (search/sort/paginate/responsive/empty-state, browser-proven). **Safe? YES. Backend untouched? YES.**
- **Adopt TC-1 as the canonical CRUD-list table engine.** **A2 (master_list/barcode_list/export_list/adda_list/product_list/roll_list) = DRIFT → migrate to A1** (add init helper; they already use the shared responsive/action primitives → near-zero risk). **Exceptions (TC-2, stay): Workflow Queue · Inline Editor · Matrix · Dashboard Summary** (DataTable would break them). **Type-2 Financial ledgers = convertible** (grid→A1, money display→TC-3). **Order: 1** (safest, highest ROI).

### Financial → TC-3 Financial Foundation (BUILD)
- **Canonical? SHOULD EXIST — but BUILD (no owner yet).** **Owner exists? NO** (concept recurs across ~6 pages — SummaryCards/MoneyCell/StatusPill/LedgerGrid/LedgerEmpty/ResponsiveLedger — **duplicated page-scoped impl**). **Mature? NO** (conceptual). **Safe? MEDIUM-HIGH** (new component system; touches money pages). **Backend untouched? YES** (presentation only; settlement money-logic stays).
- **Propose building a Financial Foundation** (extract the 6 primitives; base `.stat-card` already = SummaryCards). Real debt-reduction (~6 consumers). **Exception:** settlement-detail's workflow/money-armor forms stay (Type-1 overlap). **Order: 5-6** (higher effort/risk; after the cheap wins; needs its own design pass).

### Export → TC-5 Export Foundation (NARROW)
- **Canonical? OPTIONAL/low-priority.** **Owner exists? PARTIAL** (`barcode_export_service` backs it; button-group duplicated ×2). **Mature? NO** (narrow: barcode-export only). **Safe? YES (small). Backend untouched? YES.**
- **Propose a small shared `ExportButtonGroup` partial** (dedupe the CSV/XLSX/PDF group across barcode_list + barcode_gen). NARROW — don't over-build. **Order: 6 (optional).**

### Workflow Queue → EXCEPTION (keep)
- **Canonical? NO — legitimate exception.** settlement_list (3 sections + per-row action forms + status/chain). DataTable would break it. **No foundation** (1-2 surfaces, intentional). Keep page-scoped. Its money-armor is a separate valuable pattern (workflow-protection track).

### Inline Editor → EXCEPTION (keep)
- **Canonical? NO — legitimate exception.** product_sizes_edit / product_patterns_edit (in-row forms, inline save). DataTable damages UX. **No foundation.** Keep. (2 consumers; if a 3rd appears, revisit a shared inline-edit-row partial.)

### Matrix → EXCEPTION (keep; no foundation)
- **Canonical? NO.** **Only 1 implementation** (role_form permission CRUD matrix, CC-18). A foundation needs ≥2. **No Matrix Foundation.** Keep as-is; fix its CC-18 mobile-clip separately if desired.

### Standalone → EXCEPTION LANE (keep) + auth sub-debt
- **Canonical? NO (lane, not foundation).** public_home + 403/404/500 = **intentionally standalone** (no base.html → render when base/DB broken; pre-auth). **Keep the standalone lane.**
- **BUT auth (7 standalone copies, CC-22/23/24) = real internal debt** → **propose ONE shared auth foundation** (`base_auth` or shared auth partial) WITHIN the standalone lane (dedupe the 7 form-CSS copies + the 3 OTP-widget copies CC-23 + converge the signup validation outlier CC-24). **Order: 3-4.**

---

## 2. Explicit answers

**Which foundations SHOULD exist?**
- **Already exist + mature → adopt canonically:** Forms (`_form_styles`) · Tables (TC-1) · Selects (fancify) · Dates (fancy-date) · base.html primitives.
- **Should be BUILT (concept proven, no owner):** TC-3 Financial · shared Multiselect-chip · shared Auth foundation (CC-22).
- **Optional/narrow:** TC-5 Export.

**Which foundations should NOT exist?**
- **TC-Card · Dashboard Foundation · Detail Foundation · Timeline Foundation · Standalone Foundation · Matrix Foundation.** Reason: base `.card`/`.kpi`/`.stat-card` are **low-level primitives** (keep), not foundations; dashboards/details/timelines/card-lists are **legitimately MULTIPLE systems**; matrix has only 1 impl; standalone is a lane.

**Which systems should remain MULTIPLE?**
- Dashboards (base-primitive + page-scoped domain dashboards) · Details (A complex-360 vs B lightweight) · Timelines (`_activity_feed` vs history) · Card-lists (where domain-specific). **Multiple = acceptable when intentional.**

**Which page-scoped systems are acceptable?**
- adda_detail (360) · domain dashboards (pending/stalled/rm) · workflow queue · inline editors · standalone pages. (Page-scoped where the surface is genuinely unique.)

**Which duplications are ARCHITECTURAL DEBT (fix later, approved):**
- Auth 7-copy form-CSS (CC-22) + OTP-widget ×3 (CC-23) + signup validation outlier (CC-24).
- A2 plain CRUD lists drifted off TC-1.
- `.chip-pick` CSS/JS duplication (CC-19).
- `.history-page` timeline duplicated ×2.
- TC-3 financial primitives duplicated ×~6.
- base-`.form-card` under-built (CC-30A bare inputs, CC-30B grid clip).
- Export button-group ×2 (TC-5).
- `pattern_form`/`stage_form` custom 2-col grids (XC-1, bypassed shared `.form-grid`).

**Which duplications are INTENTIONAL (keep):**
- Error pages ×3 (resilience — must render without base/DB).
- Standalone auth/public *lane* (pre-auth/no-chrome) — the lane is intentional; auth's *internal* 7-copy is the debt.
- Native date-RANGE filters (range ≠ single-value).
- Multiple dashboard/detail/timeline *systems* where domain-driven.

---

## 3. Proposed migration order (safest-first; ALL frontend/template/CSS; backend untouched; per-item approval required)

1. **A2 → TC-1** (plain CRUD lists adopt `initFancyDataTable`). Near-zero risk, high ROI.
2. **Dates → fancy-date** rollout to single-value form dates (+ CC-01 keyboard-nav once). Opt-in, low risk.
3. **Auth shared foundation** (dedupe CC-22 form-CSS + CC-23 OTP-widget + CC-24 validation). Self-contained, standalone-lane.
4. **base-`.form-card` + custom form-grids → `_form_styles`** (fix CC-30 + XC-1 by using the shared responsive grid). Medium.
5. **Multiselect chip unify** (CC-16/17/19/20 → one chip; worker-picker single widget). Medium.
6. **TC-3 Financial Foundation BUILD** (extract SummaryCards/MoneyCell/StatusPill/LedgerGrid/LedgerEmpty/ResponsiveLedger) + **TC-5 Export dedupe**. Highest effort; own design pass.
- Cross-cutting (any time): `.sf-input`/button ≥44px touch baseline (CC-05/CC-25); CC-01 keyboard-nav (fancy-select+date); favicon (CC-28); dead-surface disposition (home 062, scan_detail 067); dormant-bug-on-re-enable (CC-04 + signup throttle).

**Backend: untouched in all of the above** — every item is template/CSS/widget-rendering; no models/services/settlement-logic change.

---

## 4. Decision asks

1. Approve the **adopt-as-canonical** set (Forms `_form_styles` · Tables TC-1 · Selects fancify · Dates fancy-date · base.html primitives).
2. Approve **BUILD** proposals (TC-3 Financial · Multiselect-chip · Auth foundation) — each as a separate, future, design-then-approve project.
3. Approve **NOT-a-foundation** rulings (Card/Dashboard/Detail/Timeline/Standalone/Matrix stay primitives/exceptions/multiple).
4. Approve the **debt vs intentional** split (§2) + the **migration order** (§3) — as a roadmap, not an execution order.
5. Pick the FIRST migration to scope (recommend #1 A2→TC-1: smallest, safest, reversible).

**Nothing executes without per-item approval. No code yet.** This review is the architecture map; implementation is separate, scoped, reviewed work.
