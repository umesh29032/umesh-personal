# A2 → TC-1 DataTable — Implementation Plan (PLAN ONLY)

> **First scoped migration project** from the Whole-System Architecture Review (§3, item 1).
> **PLANNING ONLY — no code, no patches, no template edits, no execution, no commit.** Scoped/reviewed/approved independently.
> Evidence frozen (Family E A1/A2; Family G). Date 2026-06-16 · Branch `new_flask_app`.
>
> **Goal:** reclaim A2 ("CRUD/report lists with the shared responsive primitives but NO DataTable engine")
> onto the canonical **TC-1** engine (`initFancyDataTable` + shared vendor partials) — gaining search/sort/
> pagination — WITHOUT touching backend.

---

## 0. Critical scoping finding — A2 is NOT one migration

The 6 A2 candidates split by **server-side pagination** (verified `paginate_by`):

| Template | View `paginate_by` | DataTable swap | Backend impact |
|---|---|---|---|
| `raw_materials/master_list.html` | **None** ("masters tiny") | **CLEAN** | **none (template-only)** |
| `tracking/barcode_list.html` (per-Adda) | none | **CLEAN** | none (template-only) |
| `production/product_list.html` (prod) | none | **CLEAN** | none (template-only) |
| `production/adda_list.html` | **50** (server) | ⚠ NOT clean | view change (drop/replace pagination) |
| `tracking/export_list.html` (= inventory `ExportListView`) | **50** (server) | ⚠ NOT clean | view change |
| `raw_materials/roll_list.html` | **50** (server) | ⚠ NOT clean | view change |

**Why server-paginated tables are NOT a clean swap:** `initFancyDataTable` paginates/searches/sorts **client-side over the rows present in the DOM.** A server-paginated page ships only 50 rows → DataTable search/sort would silently operate on **just those 50** (misses other server pages) = a correctness regression. Resolving it means either dropping `paginate_by` (loads ALL rows — risky for large adda/roll datasets, AND changes the **view = backend**) or DataTable server-side/ajax mode (a larger build). **Either path violates "backend untouched."**

### Scope decision
- **THIS project = A2-CLEAN trio only** (master_list · barcode_list · product_list). Template-only, backend untouched, low risk, reversible.
- **A2-PAGINATED trio (adda_list · export_list · roll_list) = SEPARATE future project** (needs an explicit pagination decision: drop-pagination vs server-side-DataTable vs leave-as-is). **Out of scope here.** Recorded, deferred.

---

## 1. Target templates (this project — 3)

1. `config/raw_materials/templates/raw_materials/master_list.html` (shared ClothType/ClothColor/StorageLocation list)
2. `config/tracking/templates/tracking/barcode_list.html` (per-Adda barcode batches; has page-level export forms)
3. `config/production/templates/production/product_list.html` (production product list)

All 3 already have: `.table-responsive` wrapper + `data-label` cells (+ `.td-actions` on master/product). **None have `initFancyDataTable`.** None have server pagination.

---

## 2. Per-template change spec (DESCRIPTIVE — no code)

For each of the 3 templates, the change is **additive + small** (mirrors the existing A1 pages skill_list/user_list/usertype_list):
1. **Add an `id`** to the `<table>` (e.g. `id="masters-dt"` / `id="barcodes-dt"` / `id="products-dt"`).
2. **Include the shared vendor partials** in the page (`{% include 'shared/_datatables_vendor_css.html' %}` in extra_head; `..._js.html` in extra_scripts) — IF the page doesn't already pull them via base.
3. **Add one `initFancyDataTable('#<id>', {...})` call** in extra_scripts with: `itemName`, `searchPlaceholder`, `pageLength`, and `columnDefs` marking the Actions/non-sortable columns `orderable:false` (match the per-table column layout).
4. **No markup restructure** — keep `.table-responsive`/`data-label`/`.td-actions`/`.empty-state` as-is (TC-1 cooperates with them).

**Per-table column notes (for the columnDefs):**
- master_list: dynamic columns (Name + per-type + Status + Created + **Actions[non-orderable]**).
- barcode_list: Size·Color·Start·End·Pieces (all data; no row-actions; export forms are page-level — **leave outside the table**, unaffected by DataTable).
- product_list: product columns + **Actions[non-orderable]**.

---

## 3. Migration sequence

One template at a time, **fix-don't-commit-STOP** (the established cadence):
1. **master_list** first (smallest, `paginate_by=None` explicit, shared template across 3 master types → 1 edit covers ClothType/ClothColor/StorageLocation). Verify all 3 master types.
2. **product_list** (prod) second.
3. **barcode_list** third (verify the page-level export forms still work + aren't swept into the DataTable).
- Each: edit → browser-verify (checklist §7) → STOP for review → (on approval) commit dedicated → next.

---

## 4. Risk analysis

| Risk | Severity | Mitigation |
|---|---|---|
| **Server-pagination conflict** | HIGH (but **avoided** — clean trio has none; the 3 paginated tables are OUT of scope) | scope-split (§0) |
| Export forms (barcode_list) swept into DataTable / broken | MED | export forms are page-level, OUTSIDE `<tbody>`; verify they sit outside the `#barcodes-dt` table; DataTable only manages the table |
| `columnDefs` index wrong → Actions column sorts | LOW | match indices to actual columns; verify sort per column |
| master_list dynamic columns (varies per master type) → columnDefs index drift | MED | verify all 3 master types (ClothType/Color/Location) since column count differs |
| data-label mobile stacking breaks under DataTable | LOW | A1 pages prove TC-1 + data-label coexist (skill/user/usertype); re-verify @320 |
| Empty state: `.empty-state` vs DataTable "no records" double | LOW | check empty list renders cleanly (DataTable shows its own empty row) |
| Touch targets (action-link ~23px) | LOW (pre-existing CC-25; not introduced by this migration) | out of scope; note only |
| Large master dataset → client DataTable slow | LOW (masters are 10s-100s per view comment) | acceptable; paginated big lists explicitly excluded |

**No data risk** — read-only list pages; no writes, no settlement/money logic.

---

## 5. Rollback strategy

- **Fully additive + per-template independent.** Each migration = (a) add table `id`, (b) add vendor includes if missing, (c) add one `initFancyDataTable(...)` script block.
- **Rollback = remove those additions** for that template → page returns to plain A2 (table-responsive + data-label, no engine). No data/schema/state to undo.
- Per-template dedicated commits → `git revert <hash>` cleanly reverts one without affecting others.
- No migrations, no model changes, nothing stateful.

---

## 6. Backend impact confirmation

- **A2-CLEAN trio (this project): ZERO backend impact.** Changes are template + (shared, already-existing) vendor partial + one JS init call. **No views, no models, no services, no urls, no settings, no migrations.** `master_list` view `paginate_by=None` unchanged; product/barcode views unchanged.
- **A2-PAGINATED trio (deferred): WOULD touch the view** (`paginate_by`) → that's why they're excluded from this "backend-untouched" project.

---

## 7. Browser verification checklist (per template, real Chromium 1280/320)

- [ ] DataTable initializes (`.dataTables_wrapper`, search box, info "Showing X of Y <itemName>").
- [ ] **Search filters** rows live (type a known value → count drops, "filtered from N").
- [ ] **Sort** works on data columns; **Actions column NOT sortable** (columnDefs).
- [ ] Pagination control present + works (if rows > pageLength).
- [ ] **Mobile @320:** `.table-responsive` + `data-label` card-stack STILL works (td=flex, ::before labels), **0 overflow**.
- [ ] **Row actions** (edit/delete links / `.td-actions`) still navigate correctly post-init.
- [ ] **barcode_list:** page-level export forms (CSV/XLSX/PDF) still present + outside the DataTable, still submit.
- [ ] **master_list:** verify ALL 3 master types (ClothType/ClothColor/StorageLocation) — dynamic columns OK.
- [ ] **Empty list:** renders cleanly (DataTable empty-row, no broken `.empty-state` overlap).
- [ ] **Console: 0 errors** (excluding the app-wide favicon CC-28).
- [ ] No regression vs current page (compare before/after screenshots).

---

## 8. Decision asks

1. Approve the **scope split** — this project = A2-CLEAN trio only (master_list · barcode_list · product_list); A2-PAGINATED trio deferred to a separate pagination-decision project.
2. Approve the **plan** (additive `id` + vendor + `initFancyDataTable`; no markup restructure; backend untouched).
3. Approve the **sequence** (master_list → product_list → barcode_list; one at a time; fix → browser-verify → STOP → approve → dedicated commit).
4. Confirm **fix-don't-commit-STOP** cadence + **no commit until you approve each**.

**No code until you approve this plan. Nothing committed.**

---

## 9. EXECUTION LOG

### master_list — IMPLEMENTED + VERIFIED (UNCOMMITTED, awaiting approval) 2026-06-16
- **Pre-impl check done** (DOM · vendor per-page · config · baselines `/tmp/master_list_BEFORE_1280.png`+`_320.png` · rollback).
- **Edit (additive, template-only, 18+/1−):** added `id="masters-dt"` + `{% block extra_head %}`(vendor css) + `{% block extra_scripts %}`(vendor js + `initFancyDataTable('#masters-dt', {pageLength:25, itemName:'{{title|lower}}', searchPlaceholder})`). **NO markup restructure. NO columnDefs** (Actions stays non-sortable via existing `data-orderable="false"` th — dynamic-column-safe).
- **Browser-verified (all 3 master types):** DataTable inits — cloth-types(4 rows/4 cols, "cloth types") · cloth-colors(6/5, "cloth colors") · storage-locations(2/5, "storage locations"). **Search filters** ("Black"→"1 of 1, filtered from 6"; clear→6). **Sort** works (Name→sorting_desc). **Actions NOT sortable** ✓. **Row-actions intact** (18 links). **Mobile @320: data-label stack UNCHANGED** (td=flex, "Name", 0-overflow) — matches baseline. **Console clean.**
- **Before/after:** BEFORE dtWrapper=0 (plain) → AFTER dtWrapper=1 (search/sort/paginate/info); data-label/mobile/row-actions **unchanged** = no regression. Screenshots: `/tmp/master_list_AFTER_1280.png`+`_320.png`.
- **Backend: 0 `.py` changed** (template-only). **Rollback:** revert the 18+/1− template diff.
- **Status: APPROVED (owner) — UNCOMMITTED (owner-directed hold; commit strategy decided after all A2-CLEAN done).**

### product_list (production) — IMPLEMENTED + VERIFIED (UNCOMMITTED) 2026-06-16
- **Edit (additive, template-only):** `id="products-dt"` + `extra_head`(vendor css) + `extra_scripts`(vendor js + `initFancyDataTable('#products-dt', {pageLength:25, itemName:'products', searchPlaceholder})`). NO restructure, NO columnDefs (Actions `data-orderable="false"` th, fixed 6 cols).
- **Baseline:** 8 rows/6 cols, dtWrapper=0, mobile flex 0-overflow (`/tmp/product_list_BEFORE_*`).
- **Verified:** DataTable inits ("Showing 1–8 of 8 products"); **search filters** ("1-6"→"1 of 1, filtered from 8"); **sort** (Name→sorting_desc); **row-actions intact** (40 links = 8×5 Edit/Flow/Patterns/Sizes/Archive); **mobile @320 data-label UNCHANGED** (flex, "Code", 0-overflow); **console clean**. After-shots `/tmp/product_list_AFTER_*`.
- **Backend: 0 `.py`.** Before→after: dtWrapper 0→1; no regression.
- **Status: DONE, UNCOMMITTED — STOP, awaiting approval before barcode_list.**

### barcode_list — IMPLEMENTED + VERIFIED (UNCOMMITTED) 2026-06-16
- **Edit (additive, template-only):** `id="barcodes-dt"` + `extra_head`(vendor css) + `extra_scripts`(vendor js + `initFancyDataTable('#barcodes-dt', {pageLength:25, itemName:'batches', searchPlaceholder})`). NO restructure. 5 data cols (no Actions → all sortable, fine); no columnDefs.
- **Baseline:** 1 row/5 cols, tfoot=1, 3 export forms, dtWrapper=0 (`/tmp/barcode_list_BEFORE_1280.png`).
- **Verified:** DataTable inits ("Showing 1–1 of 1 batches"); **`<tfoot>` Total intact** + **console CLEAN (no DataTables tfoot/column-mismatch warning — the flagged risk did NOT materialize)**; **export forms OUTSIDE the table** (`#barcodes-dt form`=0; all 3 export forms still on page in `.card-header`) ✓ (requirement met); **sort** (Size→sorting_desc); **mobile @320 data-label UNCHANGED** (flex, "Size", 0-overflow). Search box present (filtering proven on master/product, same engine; golden has 1 row). After-shots `/tmp/barcode_list_AFTER_*`.
- **Backend: 0 `.py`.** **Status: DONE, UNCOMMITTED.**

### ✅ ALL 3 A2-CLEAN MIGRATIONS IMPLEMENTED + VERIFIED — UNCOMMITTED (intentional, owner-approved)
- Working tree: **master_list + product_list + barcode_list** (3 templates, **0 `.py`**). HEAD `2e5910b9`. **Nothing committed.**
- **Next (owner-directed): review the 3 together** — TC-1 config parity · consistency · rollback simplicity · no hidden regressions — THEN decide commit strategy.

### STATUS 2026-06-16 — ACCEPTED, HELD UNCOMMITTED (owner-directed)
- Hard evidence delivered + **accepted** (diffs · stat · status · mobile 320/375/414 · desktop 1280 · console · config · export-safety). A2-CLEAN ×3 = implementation + browser SUCCESS.
- **Owner directive: DO NOT COMMIT.** Keep working tree uncommitted (commit decision deferred until the broader frontend-migration picture is complete). **No cleanup · no squash · no new commits · no further migrations without explicit approval.**
- **Held state:** master_list · product_list · barcode_list = migrated, UNCOMMITTED (3 templates, 0 `.py`, HEAD `2e5910b9`). Rollback = `git checkout -- <3 templates>` (additive, trivial).
- **A2-PAGINATED (adda_list · export_list · roll_list) = still DEFERRED** (separate pagination-decision project).
