# HTML_AUDIT_MASTER — Frontend HTML-by-HTML Canonicalization Audit

> **Single source of control** for reusable frontend controls + UI behavior.
> Goal: every future HTML reuses canonical components instead of re-implementing.
> Stabilization + canonicalization — **NOT** a feature project, redesign, or refresh.
>
> **This is the resume anchor.** A new session (even on a different account) reads
> this file → finds `CURRENT TEMPLATE` → continues from the exact next HTML.
> Never restart a `DONE` unit. Never lose progress.

- **Started:** 2026-06-15 · **Branch:** `new_flask_app`
- **Builds AFTER** the closed 18-phase Production Readiness Audit
  ([PRODUCTION_AUDIT_STATUS.md](PRODUCTION_AUDIT_STATUS.md) — CLOSED, do not reopen).

## 0. Architectural North Star (owner 2026-06-15)

The audit's purpose is not only to document behavior but to drive toward an **enterprise-style frontend
with a single source of control**. Target component-family tree: **Forms · Selects · Multiselects · Dates ·
Tables · Modals · Validation · Buttons · Shared behaviors.** Each family should EVENTUALLY have: **one
canonical implementation · one documented owner · one source of styling · one source of behavior ·
documented exceptions only where justified.** The per-family audit phases exist to discover **duplicate
implementations · ownership fragmentation · styling divergence · behavior divergence · missing
canonicalization** — then a future, separately-approved standardization phase converges each family.
**Documented exceptions are fine; uncontrolled divergence is not.** Evidence first → recommendations →
(only on explicit approval) changes. No UI_COMPONENTS promotion / migration / implementation without approval.

**APPROVED CANDIDATE FOUNDATIONS (owner-recorded; future canonical, NOT yet implemented):**
- **Forms → `production/_form_styles.html`** (accepted 2026-06-16, Form-Control Report)
- **Dates → fancy-date** (Date Report §7)
- **Selects → class-owned `fancify` path** (Select Report)
- **Multiselects → shared checkbox-chip direction** (future candidate; Multiselect Report)
- **Auth → one shared auth foundation** (Auth Report CC-22; still 7 copies today)
These are recorded targets only — no standardization/UI_COMPONENTS/refactor authorized; audit remains evidence-collection.

**ARCHITECTURE MAP — CLASSIFICATION FROZEN, DECISIONS DEFERRED (owner 2026-06-16):** FROZEN = the evidence + inventory + classification boundaries below (TC-1/TC-2/TC-3/TC-5/A1/A2 + browser-verified findings) — later phases may DISCOVER consumers/gaps/drift but may NOT redefine/merge these CLASSIFICATIONS. **NOT frozen / NOT decided yet = architecture decisions · canonical promotions · foundation approvals · migrations · standardization · UI_COMPONENTS changes.** Those happen ONLY in a final whole-system review AFTER every HTML is audited + every family report finalized. **Evidence first, decisions later.** The list below is candidate-classification, NOT locked architecture:
- **Foundations:** Forms→`production/_form_styles.html` · Selects→class-owned fancify · Multiselects→shared checkbox-chip · Dates→fancy-date · **TC-1 DataTable Foundation** (base.html `initFancyDataTable`+vendor) · **TC-3 Financial Foundation** (future; SummaryCards/MoneyCell/StatusPill/LedgerGrid/LedgerEmpty/ResponsiveLedger) · **TC-5 Export Foundation** (future, narrow).
- **Exception families (legit):** Workflow Queue · Inline Editor · Matrix · Dashboard Summary.
- **A1** = Canonical CRUD Lists (DataTable). **A2** = Canonical Drift (plain, shared primitives, no engine) = LOW-effort migration candidates, **NOT exceptions**.
- **Rule:** future phases may NOT redefine TC-1/TC-3/TC-5, merge exception families, or invent new foundations without evidence.

---

## 1. Tracking files (4-file system + canon)

| File | Role | Written when |
|---|---|---|
| **HTML_AUDIT_MASTER.md** (this) | State · progress · ordering · constraints · recovery. The "where are we." | Every HTML boundary |
| [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) | One record per HTML (HTML-001…113): controls, issues, status, audit method. The queue + per-template truth. | Every HTML audited |
| [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) | **Staging** for proposed canonical rules found during audit — evidence + template count. NOT locked canon. Promoted to UI_COMPONENTS.md once proven across templates. | When a reusable pattern is observed |
| [HTML_FIX_HISTORY.md](HTML_FIX_HISTORY.md) | Chronological fix log: HTML id · issue · change · files · commit hash. The "what changed when." | When a fix is committed |
| [../UI_COMPONENTS.md](../UI_COMPONENTS.md) | **Locked canon** — the project's authoritative component registry. | Only when a candidate is promoted (reusable rule proven) |

Supersedes the phase-based [FRONTEND_DESIGN_SYSTEM_STATUS.md](FRONTEND_DESIGN_SYSTEM_STATUS.md)
(⛔ SUPERSEDED). Its 20-template JSON (`FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json`)
is **SEED evidence only**, imported into the ledger. Never run the old audit in parallel.

## 2. Hard constraints (every HTML)

- ❌ No redesign · no color/branding change · no visual refresh.
- ❌ No Tailwind/React/Bootstrap. No new library unless a **verified** bug can't be
  solved with existing project patterns.
- ❌ No speculative abstractions — standardize only **proven existing** patterns.
- ❌ **No batch auditing.** One HTML = one audit unit. Never >1 at a time.
- ❌ Never depend on unfinished agent/workflow output across a session reset.
- ❌ No auto-commit. Fix → verify → STOP → owner review → ONE commit on approval.
- ✅ Mobile-first is FUNCTIONAL. Browser-verify every unit at **320/375/390/414/1280**.
  Real browser, not code-reading alone.
- ✅ Honesty rule: never mark clean on a dead/failed check. If browser verification
  can't run, record that explicitly — never fabricate "clean".

## 3. Per-HTML cycle (then STOP)

1. Desktop review (code + browser). 2. Mobile review (320/375/390/414).
3. Identify issues (classification §6). 4. Fix verified issues (stabilization/
canonicalization only). 5. Verify fix (re-browser all widths). 6. Update
HTML_AUDIT_LEDGER record. 7. Update this MASTER (current → next). 8. Log any
reusable pattern in HTML_CANONICAL_CANDIDATES; promote to UI_COMPONENTS.md only if
proven. 9. Show owner: findings · files · evidence · candidate rules. **10. STOP.
No commit. Wait for review.** On approval → ONE commit → record hash in
HTML_FIX_HISTORY + ledger `Commit:` → next HTML.

## 4. Ordering — by CONTROL FAMILY (execution order)

Highest-reuse controls first. Each HTML filed under the **highest-priority** family
of any control it contains → audited once, covers all its controls.

| Phase | Family | Units | Status |
|---|---|---|---|
| **0** | **Pre-work: fancy-date control** | 1 | ✅ CLOSED · commit `7e105b92` |
| A | Selects | 21 (HTML-006 reclassified → E) | ✅ COMPLETE (21/21) |
| B | Multiselects | 4 impls (CC-16 worker-chip · CC-17 chip-pick · CC-18 perm-matrix · CC-20 Django-default) / 4 domains | ✅ COMPLETE + report |
| C | Date controls | 2 impls (fancy-date opt-in · native default) | ✅ COMPLETE + report |
| D | Form controls + validation | ~23 (multi-system: .field/.sf-*/form-shell/generic/auth) | ✅ **INPUT INVENTORY COMPLETE** — 026-048 + 070/071 (23 units) + confirm-dialog rep; completeness scan done (ledger §inventory). 8 validation families; XC-1 ×5; CC-13 ×2; CC-20 closed; `_form_styles` ×6; CC-27/CC-29 committed. **Next = Form-Control Consolidation Report.** |
| E | Tables | 11 seeded (+full scan) | ✅ **COMPLETE + REPORTED** ([TABLES_CONSOLIDATION_REPORT.md](TABLES_CONSOLIDATION_REPORT.md), FROZEN). A1=5 · A2=6 · TC-2(Type1-5) · TC-3 financial≈6 · TC-5 export(narrow); TC-1=engine owner; TC-4 not-opened. Awaiting §8 decision asks. **Next = Family F (Modals).** |
| F | Modals | 1 | ✅ **COMPLETE + REPORTED** ([FAMILY_F_MODALS_REPORT.md](FAMILY_F_MODALS_REPORT.md), FROZEN). 1 app-owned modal (Crop Modal, widget-private, 2 consumers) — behavior solid + responsive, **MOD-A11Y gaps** (record-only); native confirm()=browser; NO TC-6 modal foundation. "No modal fragmentation" = success. |
| G | Remaining surfaces | ~20 surfaces + ~22 partials | ✅ **COMPLETE + REPORTED** ([FAMILY_G_REMAINING_SURFACES_REPORT.md](FAMILY_G_REMAINING_SURFACES_REPORT.md), FROZEN). base.html master-shell(78); existing shared owners (`_form_styles`/vendor=TC-1/time_log/user_form/`_activity_feed`); multiple card/dashboard/detail/timeline systems; standalone lane; 2 dead surfaces. Architecture OPEN. **Next = whole-system review (after any remaining family work).** |
| — | `base.html` | canonical sink (edited when rules emerge; never a standalone unit) | n/a |

Full numbered queue → [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md). A unit may
move family if its audit reveals a higher-priority control.

### Surface-group cross-index (review lens — NOT the execution order)

Same 113 templates grouped by SURFACE, for review readability. Execution still runs
control-family A→G above. The ledger holds each template's authoritative single
family assignment; a template is listed in just one surface group here.

| Surface group | ~Count | Example HTML ids |
|---|---|---|
| Auth | 7 | 026–032 (forgot/login/login_password/otp/reset_otp/signup/signup_otp) |
| Forms (create/edit) | 28 | 001–003,005,007,012–014,016,017,019,033–048 |
| Lists / Tables | 24 | 004,006,015,018,020,049–059,076,077,080,084,085,102,105 |
| Workspaces | 10 | 008,010,036,048,070,072,082,083,086,087 |
| Dashboards | 8 | 011,024,025,061,091,099,107,108 |
| Modals | 1 | 060 |
| Shared partials (CSS/JS/panel/accordion/vendor) | 21 | 009,021–023,045,065,067,069,071,073,074,081,088,098,100,103,104,106,109,110 |
| System (errors + confirm/delete) | 14 | 062–064,075,078,079,089,090,093,094,095,096,097,101 |

## 4a. Control-family discovery rule (owner 2026-06-15)

The objective is not only to fix individual HTML — it is to **discover and
converge toward ONE canonical implementation** per family (select / multiselect /
date / form-control / table / validation / modal). So during each family's phase:

1. Audit each HTML normally (full §3 cycle).
2. Record **every** family-control implementation encountered → evidence in
   [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md): HTML file ·
   variant · mobile behavior · a11y behavior · browser issues · **DEPENDENCY
   DISCOVERY** (so future canonicalization misses no hidden dependency): CSS owner
   (base.html / shared partial / page-specific / duplicated) · JS owner (base.html /
   shared partial / page-specific / inline) · whether the control depends on hidden
   page-specific behavior (inline handler, view-supplied context var, sibling JS) ·
   **SELECT SOURCE TYPE** (literal HTML `<select>` / Django form-widget select /
   dynamic-AJAX select / multiselect / chip-picker / other) — inventory only ·
   **INTERACTION MODEL** (single-select / multi-select / chip-toggle / filter-select /
   auto-submit select / date-picker / other) — inventory only · **VISUAL OWNER**
   (base.html / shared partial / page-specific css / fallback styling / mixed) = who
   actually controls the RENDERED appearance — may differ from where the CSS lives
   (e.g. page-tag CSS that misses a fancified `<button>` trigger → real owner = the
   `--bare` fallback) — inventory only.
3. **Evidence only — do NOT standardize, do NOT migrate other pages, do NOT touch
   UI_COMPONENTS.md** unless promotion criteria are already satisfied.
4. **At end of the family phase** (all that family's templates audited) produce a
   **Family Consolidation Report**: all implementations found · duplicates · broken
   ones · mobile issues · candidate canonical · migration impact · est. affected
   templates. **Informational only — does NOT authorize migration work.**
5. Then continue the normal HTML-by-HTML process into the next family.

Phase A deliverable = the **Select Family Consolidation Report** (after the last select unit).

**Per-select record — 7 LOCKED dimensions (owner 2026-06-15), capture for EVERY select:**
1. source type · 2. visual owner (shared-partial / sf-input(base) / native / fallback) ·
3. interaction model · 4. touch-target height (px) · 5. native vs fancified ·
6. hidden dependencies · 7. reason for `data-no-fancy` (if present). **Keep the
`data-no-fancy` reasons SEPARATE — do NOT merge into one category:** (a) filter-select
behavior, (b) template-cloned dynamic rows. **Family A = evidence + classification ONLY —
no consolidation, no migration, NO promotion to UI_COMPONENTS.md until the whole family is done.**

**Evidence so far (Family A, do not act):** native control height is NOT a fixed tier
(37px filter · 42px cloned-row select · 43px native date); the ONLY consistent height signal
is **fancified `sf-input` triggers = 39px** across independent surfaces (CC-05).

## 5. Pre-work — Step 0: fancy-date control (owner decision 2026-06-15)

Review + commit the uncommitted `fancy-date` control **before Phase A** so
`base.html` is clean before any select-canonical edit:
- Files: `accounts/base.html` (+359 `fancifyDate` JS + `.fancy-date-*` CSS),
  `accounts/user_form.html` (`birth_date` → `data-fancy-date`), `UI_COMPONENTS.md`
  (+21 date-picker section), `docs/apps/accounts/GUIDE.md`, `docs/PENDING_BACKLOG.md`.
- Verify (browser, desktop+mobile, on `user_form`): date selection · year navigation
  · form save/edit persistence · validation · mobile rendering · no console errors.
- Show evidence + every changed file → STOP for review → on approval a **dedicated
  commit** → record hash → mark Step 0 CLOSED. Only then start Phase A / HTML-001.

## 6. Findings classification (every audit tags findings into these buckets)

Select controls · Multi-select controls · Date controls · Tables (responsive/
data-label) · Forms (layout/inputs) · Buttons · Modals · Validation rendering ·
Mobile responsiveness (overflow/clip/hidden-control/touch-target ≥44px) ·
Accessibility (aria/labels/focus) · Console errors. Each finding → severity +
"can this recur elsewhere?" → if yes, a HTML_CANONICAL_CANDIDATES entry.

## 7. Session-limit recovery (account-switch safe)

State lives ONLY in these md files — never in agent/workflow memory.
1. New session reads **this MASTER** → `CURRENT STATE` table.
2. `Current template` = the exact next HTML to do. `Last completed HTML id` = last DONE.
3. Open [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md), find that HTML's row, run the §3 cycle.
4. Never re-audit a `DONE`/`CLEAN` unit. SEED ≠ done (still needs the full cycle).
5. If a fix was mid-flight (status `IN-PROGRESS`/`FIXED`, uncommitted), `git status`
   + the ledger record + HTML_FIX_HISTORY show exactly what was changed; finish or
   restart that single HTML — no other unit is affected.

## 🔒 AUDIT CLOSED — 2026-06-16 (owner-accepted)

113/113 templates audited. Families A–G COMPLETE + reported + FROZEN. Evidence frozen.
**No new audit families · no new inventories · no expanding scope.** Buttons accepted as
transversal base.html-primitive coverage; a11y/touch-target debt carried into implementation.

**Successor = [FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md)**
(permanent frontend architecture; design-only). Implementation runs its §10 order:
0 Tokens → 1 Buttons → 2 Tables(finish A2) → 3 Forms → 4 Auth → 5 Financial → 6 Export → 7 Cards.
**A2-CLEAN (master/product/barcode_list) = MIGRATED+VERIFIED+HELD (uncommitted).** No code authorized yet.

## CURRENT STATE

| | |
|---|---|
| **Total content templates** | 113 (+ `base.html` sink = 114 files) |
| **DONE (audited+verified+committed)** | 0 |
| **SEED imported (classified only)** | 20 |
| **Current phase** | **D — Form controls** (A·B·C complete + reports approved evidence-only; Date arch-preference recorded §7) |
| **Current template** | **AUDIT A-G COMPLETE → WHOLE-SYSTEM ARCHITECTURE REVIEW delivered ([WHOLE_SYSTEM_ARCHITECTURE_REVIEW.md](WHOLE_SYSTEM_ARCHITECTURE_REVIEW.md)) → next = owner decision asks (§4), then scoped per-item implementation (recommend #1 A2→TC-1)** |
| **Last completed** | **Whole-System Architecture Review — per-system canonical/exception rulings + debt-vs-intentional + migration order (1 A2→TC-1 … 6 TC-3/TC-5). Architecture proposals only, NO code. Adopt: Forms `_form_styles`/Tables TC-1/Selects fancify/Dates fancy-date. Build: TC-3/multiselect-chip/auth. NOT foundations: Card/Dashboard/Detail/Timeline/Matrix/Standalone.** |
| **Last completed HTML id** | HTML-059 (seeded Family E 049-059 done; Phase D + Form-Control Report FROZEN; A·B·C·Auth done; CC-27 `20fccbd7`, CC-29 `2e5910b9`; North Star §0 + candidate foundations; 002 `bcf508f2`) |
| **Framework status** | 🟢 **Phase D COMPLETE + Form-Control Report ACCEPTED/FROZEN** (owner decisions recorded: 3-axis map approved · findings kept separate · `production/_form_styles.html` = approved canonical form-foundation candidate · candidate foundations recorded in §0 · no standardization/promotion/refactor — still evidence-collection). **🔄 FAMILY E (Tables) STARTED. HTML-049 skill_list (super-admin, CLEAN, read-only):** `#skills-dt` DataTable = **shared foundation — base.html `initFancyDataTable` + shared `_datatables_vendor_css/js.html` partials + `.table-responsive`+data-label stacking + `.td-actions`/`.action-link` + `.empty-state`**; browser-verified init (search filters live, info "X of Y skills", sort on Skill Name), **mobile = data-label card-stack (@320 td=flex/::before, 0-overflow)**, console clean. Touch: action-link ≈23px (<44px). **→ TC-1 (POSITIVE shared DataTable foundation — candidate; inventory NOT complete, no conclusion yet).** Table-family discovery dims established (10). **HTML-050 user_list: TC-1 REUSE (2nd consumer) — same `initFancyDataTable('#users-dt')` + shared vendor; 6-col data-label stack (0-overflow @320); + shared DataTable FILTER-ROW (`.dt-filter-row`+`.skill-filter-chip`, GET, `filterRowId` JS-inject; ?skills=1→2 rows; PA-13-4 ?skills=abc→HTTP 200 guard holds); filter-row horizontal-scroll @narrow; console clean. Touch: action-link 23px / filter-chip 29px.** TC-1 strengthens (still candidate, inventory incomplete). **HTML-051 usertype_list: TC-1 3rd consumer (live, 5 rows). Q1/Q2 ANSWERED — `initFancyDataTable` = SOLE bootstrapper (only raw `.DataTable(` is inside the helper @base.html:2819; no page-specific wrappers). Q5: 5 DataTable pages (049/050/051 + storefront 018/020). Q3 (separate finding): ~19 PLAIN non-DataTable tables exist (money/settlement/payroll/dashboard/detail/inline-edit) → TWO table approaches; consistency Q for 052-059. Q4: 051 uses bare `.action-link` (no `.td-actions` wrapper) — minor action-column variance.** Touch action-link 23px consistent. (Op note: browse session dropped mid-turn → re-logged-in.) **HTML-052 adda_settlement_list = first WORLD-B plain table → LEGITIMATE EXCEPTION** (3 grouped workflow sections ready/waiting/history + per-row Start-settlement POST forms + money/status-pill/supersedes-chain; DataTable inappropriate; `initFancy` exists but not called). Minor variance: own page-scoped `.adst-list` data-label stack (not shared `.table-responsive`); mobile-safe @320. → **TC-2 World-A/B classifier opened.** **HTML-053 payroll_overview = 2nd World-B → BORDERLINE/convertible** (flat per-worker money table 8-col + hero grand-total ₹360; no row forms/grouping → DataTable would IMPROVE not damage → leans accidental, candidate for World A; distinct from 052's structural exception). **TC-2 STRICT 5-TYPE taxonomy (owner): Type-1 Workflow Queue · Type-2 Financial Ledger (convertibility test → World-B Convertible if DataTable can be grid engine + totals outside) · Type-3 Inline Editor · Type-4 Matrix · Type-5 Dashboard Summary. Exception ONLY if DataTable BREAKS workflow (not for money/totals/pills).** Classified: 052=Type-1 legit · 053=Type-2 convertible · 054=Type-5 (page) + Type-2 convertible (advances sub-table) · 044=Type-3 legit · CC-18/access_control=Type-4 legit (pending). **HTML-055 costing = Type-2 Financial Ledger → CONVERTIBLE (3rd convertible). New rule applied: audit table-SYSTEMS not pages.** **TC-3 = Evidence B (hidden financial foundation EMERGING).** **HTML-056 master_list = PLAIN CRUD list = World-A ACCIDENTAL DIVERGENCE** (flat list like accounts skill/user/usertype DataTables but no `initFancyDataTable`; uses shared table-responsive/td-actions → "World A minus the engine"; NOT financial → TC-3 N/A). **TC-3 reframed (owner) = BUSINESS COMPONENT SYSTEM (SummaryCards/MoneyCell/StatusPill/LedgerGrid/TotalsBar/EmptyState/ResponsiveRules), may USE DataTable internally but ≠ DataTable; 6-primitive scorecard = every primitive shared-CONCEPT/duplicated-IMPL.** Migration counters: TC-3 financial ~4-5 + World-A plain-CRUD-lists (master_list 056). **HTML-057 access_control = 4 READ-ONLY OVERVIEW tables (NOT matrix — 0 checkboxes — NOT DataTable); sole row×col matrix = role_form CC-18 → TC-4 Matrix Foundation NOT opened (1 impl, no duplication, no foundation). World-A SPLIT recorded: A1 canonical (TC-1: 049/050/051+storefront) vs A2 accidental-divergence (master_list 056: shared primitives, missing engine; A2→A1 = safe migration; NOT merged into TC-2). Migration counters: A2→TC-1, Financial→TC-3, Workflow→Workflow-Foundation(1), Matrix→none(1).** **HTML-058 barcode_list = read-only Report/Export table (plain, shared table-responsive/data-label, no engine, 3 page-level export forms, no row actions) → A2-ADJACENT (read-only, not strict CRUD) → World-A migration candidate (low effort, reuse TC-1 for sort/search; export stays page-level). World-A migration counter now master_list(056)+barcode_list(058).** **HTML-059 export_list = read-only Audit/Manifest table (A2-adjacent) + TC-5 Export Foundation OPENED (NARROW): export-button-group (CSV/XLSX/PDF) DUPLICATED inline in 2 pages (058+071, 3 forms each, no shared partial) + manifest(059) + Download/regenerate → shared concept, duplicated impl (like TC-3). SEEDED FAMILY E (049-059) COMPLETE.** **FAMILY E COMPLETENESS SCAN DONE (ledger §): 26 table templates, 0 unclassified. A1=5 (skill/user/usertype/storefront ×2, TC-1) · A2=6 (master_list/barcode_list/export_list + adda_list/product_list/roll_list, low-effort migration) · TC-2 exceptions grouped (Type-1 workflow: 052/036/stage-panels · Type-2 financial CONVERTIBLE: 053/055/054-sub/settlement_form · Type-3 inline: 044/007 · Type-4 matrix: role_form CC-18 SOLE · Type-5 dashboard: 054/024/011/025/057) · TC-3 financial≈6 (concept shared/impl dup, 6-primitive matrix) · TC-5 export narrow (button-group dup ×2 + manifest). base.html=TC-1 owner. 5 inventories produced; my_earnings/roll_detail=no tables. Browser-as-table = 049-059+036/044; rest signal-classified (browser in original phase).** **Next = Tables Consolidation Report (owner go); NO report/recs/promotion yet.** Prior fixes: CC-27 `20fccbd7`, CC-29 `2e5910b9`. **STOP — completeness scan delivered.** |
| | | | **HTML-070/071 barcode_gen (workspace HOST + panel, CLEAN, GET-only — reopen/start/generate/complete mutate):** host = thin wrapper incl. `_form_styles.html` (6th consumer); panel renders **`{{ start_form.workers }}` = bare Django-default CC-20 (13px, no chip), identical to 045 → CC-20 INVENTORY COMPLETE (both surfaces browser-confirmed)**; barcode tables stack @mobile (tr→block), auto-fit grid reflows, **no XC-1**; raw-POST action forms (same family as 045); console clean. **CONFIRM-DIALOG REP (skill_confirm_delete): bucket C = 11 uniform confirm dialogs (extends base + 1 submit 44px + cancel + 0 inputs), no unique impl → COVERED/out-of-scope.** **➡ FORM-CONTROL INPUT INVENTORY CONFIRMED COMPLETE.** Next = Form-Control Consolidation Report (on owner go). | shared **`_form_styles.html`** 4th consumer (CROSS-APP) + responsive `.form-grid` (NO XC-1); generic loop + per-field `.field-error` (NO swallow); hex pattern vOK; sf-input 41px. **HTML-048 pattern_workspace (HOST, CLEAN):** thin wrapper — hero + includes the 045 panel + back; NO new controls; **PA-15-3 breakup-table stacking VERIFIED** (≤600: tr→block/td→flex/thead-hidden/data-label::before, 0-overflow 320/414/600); host adds thin owner layer (inline hero + host-local breakup-stacking, dup of embedded path; `_form_styles.html` 5th consumer). **PHASE-D SEEDED RANGE 026-048 COMPLETE (20 units audited + auth subset).** Next = owner direction (Form-control completeness scan / Form-Control Consolidation Report / next family E/F/G). |

## Audit fixtures (owner-provisioned, do NOT settle)

- **3-PATTI-004** — disposable cutting-stage Adda, created by owner for frontend
  verification of otherwise-blocked UI states (used for HTML-010 cutting entry panel).
  **Reuse** it to expose blocked stage-panel UI in later units; **never advance it into
  settlement flows**; it is an audit fixture, separate from the golden ₹225 chain
  (**3-PATTI-001 = golden, never touch/reopen**). Current left-state: cutting started,
  utest assigned, 1 empty Size-1 bundle.
- Evidence-grade rule: **browser-verified ≠ code-read.** Never silently upgrade a
  code-read control to verified — it must be actually rendered + interacted with.
  Open code-read item: HTML-010 `worker_id` (sf-input; verify when a populated bundle exists).

## Changelog

- **2026-06-15** — Framework established + reconciled to the 4-file tracking system
  (MASTER/LEDGER/CANONICAL_CANDIDATES/FIX_HISTORY + UI_COMPONENTS canon). Superseded
  the phase-based audit; imported its 20 templates as SEED. Classified all 113 into
  control families + a surface-group review lens. Set fancy-date as Step 0 pre-work.
  Defined classification buckets + account-switch recovery. **No HTML audited; no
  fancy-date work done — awaiting owner approval of this framework.**
