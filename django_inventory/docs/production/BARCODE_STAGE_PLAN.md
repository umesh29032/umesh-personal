# Barcode Generation Stage + Cutting Refactor + Export — Plan

Status: **Plan only. No code yet.** Drafted 2026-05-29 after Phase-1 review.
Target session: next chat after user approval.

---

## 1. Phase-1 Review — Existing / Missing / Incorrect / Reusable

### Existing (working today)

- **3-stage flow live**: Layering → Cutting Pattern → Cutting. `Stage` table + `WorkflowStage` per-product join. Per-product flow editor at `/production/products/<pk>/flow/`. Adda advances via `advance_to_next_stage()`.
- **Cutting models** ([`config/production/models.py`](config/production/models.py)):
  - `CuttingRecord` OneToOne `AddaStageRecord` — header + denormalised `pieces_cut`.
  - `CuttingPieceBreakup` (size × color × pattern × count) — already acts as **suggested inventory** with `consumed_count` denorm.
  - `CuttingBundle` (cutting_record, size, total_pieces) — per-size header.
  - `CuttingBundleItem` (bundle, pattern, color, count, source_breakup FK) — physical grouping. **User's "Bundle = physical group of cut pieces" semantic ALREADY MATCHES current code.**
- **Cutting service** ([`config/production/services/cutting_service.py`](config/production/services/cutting_service.py)):
  - `upsert_breakup_row` / `delete_breakup_row` — manages suggested inventory
  - `create_bundle` / `add_pieces_to_bundle` / `add_item_to_bundle` / `delete_bundle_item` / `delete_bundle` — bundle CRUD with `consumed_count` recompute
  - `_complete_cutting_from_breakup` — workspace path validates + denormalises + advances
  - `reopen_cutting` — admin reopen with scan-block guard
  - `_recompute_bundle_total` + `_recompute_breakup_consumed` — invariant helpers
- **Barcode foundation** ([`config/tracking/`](config/tracking/)):
  - `BarcodeBatch` range header (adda, size, color, bundle, start_seq, end_seq, total_pieces)
  - `BatchBarcode` per-piece lazy scan-state (idempotent, atomic, scan view atomic per audit fix)
  - `barcode_service.generate_for_cutting()` — aggregates CuttingBundleItem by (size,color), allocates ranges
- **RBAC**: `access_service` + `permission_service` + Stage `access_by_skill` / `access_by_role` M2M
- **Invariants protected**: 9 tests in `test_counter_invariants.py` verify denorms

### Missing (this proposal will add)

1. **`barcode_generation` Stage row** — no DB seed, not in any product workflow.
2. **`BarcodeGenerationRecord`** typed stage record (OneToOne `AddaStageRecord`) — mirror of `LayeringRecord` / `CuttingRecord` / `CuttingPatternRecord`.
3. **`AddaProductSizeColorPieceBreakdown`** — verified per-(size, color) breakdown materialized at cutting completion.
4. **`BarcodeExportBatch`** + `BarcodeExportRow` — export history + downloadable label files.
5. **Service modules**: `barcode_generation_service`, `barcode_export_service`.
6. **Views + workspace**: `/production/addas/<code>/barcode-gen/` + actions.
7. **Templates**: barcode workspace + export download UI.
8. **Tests**: barcode generation stage workflow, export integrity, count match validation.
9. **Docs**: stage diagrams + export flow + future label tracking architecture.

### Incorrect (must refactor)

1. **`cutting_service._complete_cutting_from_breakup` line 855**: calls `generate_for_cutting(cr)` inline. This couples cutting completion to barcode generation. **Refactor**: cutting completion only produces breakdown rows. Barcode generation happens in its own stage when the workflow reaches it.
2. **`cutting_service._complete_cutting_legacy` line 771**: same inline barcode call. Refactor same way.
3. **`reopen_cutting` line 893**: deletes `BarcodeBatch.objects.filter(adda=adda)`. After refactor, cutting reopen should NOT touch barcode tables — that's the barcode stage's responsibility. Adda must roll back through both stages cleanly (refuse cutting reopen if barcode stage downstream has started).

### Reusable (lean on this hard — do not rebuild)

- **`AddaStageRecord` polymorphic parent** + OneToOne typed records — pattern is mature. New `BarcodeGenerationRecord` follows same shape.
- **Stage embedded panel + iframe + `?advanced=1` postMessage reload pattern** — reuse for barcode stage workspace.
- **`advance_to_next_stage` + `reopen_*` shape** — already handles per-product workflow + audit log + downstream guard.
- **Permission gate `_ensure_cutting_skill` + `_ensure_can_complete_cutting`** — copy structure for `_ensure_barcode_skill` / `_ensure_can_complete_barcode`.
- **`generate_for_cutting` aggregation logic** — keep as the deterministic range allocator; new caller is the barcode stage service, not cutting service.
- **`_get_or_create_*_stage_record` lazy-create pattern** — same for `get_or_create_barcode_stage_record`.
- **Existing tests fixture `CuttingWorkflowFixture`** in [`test_cutting_workflow.py`](config/production/tests/test_cutting_workflow.py) — extend for new stage.
- **`UI_COMPONENTS.md` form-shell + `.empty-state-row` + `.hero-strip`** — reuse for barcode workspace.
- **CSV export pattern** — `barcode_export_csv` view already exists, refactor to use new `BarcodeExportBatch` model.

### Risks

| Risk | Mitigation |
|------|-----------|
| **Cutting reopen with barcode stage already downstream** could lose data | Refuse reopen if barcode stage `started_at` set (mirror current "any barcode scanned" check) |
| **Migration breaks existing in-progress Addas** mid-flow | Migration must be additive only; existing CuttingRecord rows untouched. Existing BarcodeBatch rows preserved. Cutting completion path branches: legacy products that DON'T include barcode_generation stage still inline-generate (back-compat). |
| **Count mismatch validation** at barcode stage completion | Hard fail: refuse complete if `SUM(BarcodeBatch.total_pieces) != SUM(AddaProductSizeColorPieceBreakdown.verified_piece_count)`. Test coverage required. |
| **Per-product workflow flexibility** | Already supported. New products include `barcode_generation` Stage in workflow; legacy products skip it — `advance_to_next_stage` handles both transparently. |
| **Re-generation of barcodes** (e.g. accidental delete) | Reopen-only via management gate. Refuse if any `BatchBarcode` row exists (already-scanned protection). |
| **Export downloads exposing barcode values pre-completion** | Export-gate: only allow export AFTER barcode stage completed (`completed_at IS NOT NULL`). |
| **Concurrent export creating duplicate rows** | `BarcodeExportBatch` insertion atomic + unique `(adda, export_method, started_at)` or sequence-based unique code. |

### Recommendations

1. **NEW model `AddaProductSizeColorPieceBreakdown`** — *yes*, store the verified per-(size, color) aggregation. Reason: Cutting Stage produces it; Barcode Stage consumes it; future stages (Stitching, Packing) consume it without re-computing. Storage cost negligible (<100 rows per Adda).
2. **NEW model `BarcodeGenerationRecord`** — typed stage record. Holds completion stamp + reference to breakdown. Mirror `CuttingRecord` shape.
3. **NEW `BarcodeExportBatch` + `BarcodeExportRow`** — export history. Re-download by `export_code`. Track exported-by + method (CSV / XLSX / PDF).
4. **DO NOT re-purpose `BarcodeBatch`** as the breakdown source-of-truth. `BarcodeBatch` stays barcode-specific (range header). New breakdown is upstream of it.
5. **Bundle semantics** — current `CuttingBundle` + `CuttingBundleItem` already match user's intent (multi-pattern physical grouping). No model change needed. Documentation must clarify.
6. **Suggested cutting inventory** = `CuttingPieceBreakup` (already exists). User's "available = total - consumed" formula = `.available_count` property already on model. No model change.
7. **Future label-tracking architecture** — stub-only models in this PR: `LabelPrintQueue` (deferred fields) + interface hooks. Implementation deferred per user instruction.

---

## 2. Architecture Decision Points (need user nod before code)

### D1. Breakdown materialisation timing

**Recommendation:** materialise `AddaProductSizeColorPieceBreakdown` rows at `_complete_cutting_from_breakup` completion, before `advance_to_next_stage`. Atomic within cutting completion transaction.

**Alternative considered:** materialise on-demand in barcode stage. Rejected — leaves cutting completion non-canonical; future stages depend on this aggregate.

### D2. Bundle FK on breakdown

User's draft: `bundle_reference` field. **Question:** one-to-one with bundle (per size, since bundle is per-size), or aggregate may span bundles?

Today: 1 bundle = 1 size. So per-(adda, size, color) breakdown has exactly 1 bundle to reference. **Recommendation:** nullable FK to `CuttingBundle` (since legacy non-bundle products will have NULL).

### D3. Legacy back-compat

Products without `barcode_generation` in workflow today inline-call `generate_for_cutting` from cutting completion. **Recommendation:**

- Refactor: cutting completion ALWAYS materializes breakdown rows.
- If `barcode_generation` stage IS in product workflow → don't generate barcodes; let barcode stage do it.
- If `barcode_generation` stage NOT in workflow → cutting completion ALSO calls `generate_for_cutting` (back-compat for NIKKAR-style simple products).

This keeps legacy tests passing without forcing all products to add a new stage.

### D4. Export storage

**Recommendation:** generate exports on-the-fly from `BatchBarcode` + breakdown rows (no per-row stored copy). Store ONLY the manifest header (`BarcodeExportBatch`) for audit. Re-download regenerates from live data.

**Alternative:** store actual CSV/XLSX file in `STORAGES['default']`. Rejected — bloat + sync risk if barcode rows mutate.

### D5. Where to introduce `barcode_generation` Stage in default seed

**Recommendation:** seed migration adds Stage row but does NOT auto-attach to any existing Product workflow. Admin opts in per-product via `/production/products/<pk>/flow/`.

---

## 3. Model Plan

All in `config/production/models.py` (breakdown + barcode gen record + label queue stub).
Export models in `config/tracking/models.py`.

### 3.1 `AddaProductSizeColorPieceBreakdown` (production app)

```text
- adda                FK Adda (PROTECT)
- product             FK Product (PROTECT)  — denorm for fast queries
- cutting_record      FK CuttingRecord (CASCADE)
- bundle              FK CuttingBundle (SET_NULL, nullable) — per-size; null for legacy
- size                FK ProductSize (PROTECT, nullable for legacy)
- color               FK ClothColor (PROTECT, nullable for legacy)
- verified_piece_count PositiveIntegerField
- created_by          FK User (PROTECT, nullable)
- created_at / updated_at (TimeStampedModel)

Meta:
  unique_together = [('cutting_record', 'size', 'color')]
  indexes = [
    Index(fields=['adda', 'size', 'color']),       # dashboard breakdown
    Index(fields=['cutting_record']),              # FK-natural
  ]
```

**Hinglish docstring:**
> Yeh model Cutting Stage ka final verified per-(size, color) breakdown
> store karta hai. Pieces verify ho jaane ke baad aggregate yahaan freeze
> hota hai. Barcode generation aur future stages (Stitching, Packing)
> isse hi consume karenge — recompute nahi.

### 3.2 `BarcodeGenerationRecord` (production app)

```text
- stage_record        OneToOne AddaStageRecord (CASCADE, related_name='barcode_generation')
- total_barcodes      PositiveIntegerField (denorm; SUM(BarcodeBatch.total_pieces))
- notes               TextField (blank=True)
- generated_at        DateTimeField (set when barcodes actually generated)
```

### 3.3 `LabelPrintQueue` stub (production app, deferred logic)

```text
- export_batch        FK BarcodeExportBatch (PROTECT)
- vendor_name         CharField(max_length=120, blank=True)  — future
- status              CharField (TextChoices: queued/sent/received/printed)
- sent_at             DateTimeField (nullable)
- received_at         DateTimeField (nullable)
- printed_at          DateTimeField (nullable)
- notes               TextField (blank=True)

Comment block: "Future: vendor + factory print workflow. Implementation deferred."
```

### 3.4 `BarcodeExportBatch` (tracking app)

```text
- export_code         CharField(max_length=24, unique=True)  — 'EXP-2026-001' etc.
- adda                FK Adda (PROTECT)
- product             FK Product (PROTECT, denorm)
- barcode_gen_record  FK BarcodeGenerationRecord (PROTECT)
- export_method       CharField (TextChoices: csv/xlsx/pdf)
- exported_by         FK User (PROTECT)
- total_labels        PositiveIntegerField
- created_at          DateTimeField

Meta:
  indexes = [Index(fields=['adda', '-created_at'])]
  ordering = ['-created_at']
```

No `BarcodeExportRow` — rows generated on-the-fly from `BatchBarcode` per D4.

---

## 4. Migration Plan

| # | App | Migration name | Operations |
|---|-----|----------------|------------|
| 0020 | production | `add_barcode_generation_models` | CreateModel `AddaProductSizeColorPieceBreakdown`, `BarcodeGenerationRecord`, `LabelPrintQueue` |
| 0021 | production | `seed_barcode_generation_stage` | RunPython: `Stage.objects.get_or_create(code='barcode_generation', name='Barcode Generation', access_by_skill = cutting_master + cutting_master_helper)`. Reverse = no-op. |
| 0009 | tracking | `add_barcode_export_batch` | CreateModel `BarcodeExportBatch` |
| 0022 | production | `data_backfill_breakdown_for_completed_addas` | RunPython: for each completed Adda with CuttingRecord, aggregate CuttingBundleItem by (size, color) → create `AddaProductSizeColorPieceBreakdown` rows. Idempotent. Reverse = no-op. |

All forward-safe. No destructive operations.

---

## 5. Service Plan

### 5.1 Refactor `production/services/cutting_service.py`

- `_complete_cutting_from_breakup`: after validation, BEFORE `advance_to_next_stage`:
  - Materialize `AddaProductSizeColorPieceBreakdown` rows (aggregate `CuttingBundleItem` by (size, color, bundle)).
  - **REMOVE** inline `generate_for_cutting(cr)` call.
  - If `barcode_generation` Stage NOT in product workflow → keep inline barcode call (back-compat).
- `_complete_cutting_legacy`: same back-compat branch.
- `reopen_cutting`: refuse if downstream `barcode_generation` stage `started_at` set OR if any `BatchBarcode` scanned. On reopen, delete `AddaProductSizeColorPieceBreakdown` rows AND `BarcodeBatch` rows. Atomic.

### 5.2 New `production/services/barcode_generation_service.py`

```text
- _ensure_barcode_skill(user)
- _ensure_can_complete_barcode(user)
- _barcode_workflow_stage(adda)
- get_or_create_barcode_stage_record(adda, user)
- start_barcode_generation(*, adda, worker_ids, user)        # mgmt-only
- preview_barcode_counts(adda)                                # read breakdown + show what will be generated
- generate_barcodes(*, adda, user)                            # idempotent — calls tracking.barcode_service.generate_for_cutting OR new helper that uses breakdown rows
- complete_barcode_generation(*, adda, user)                  # validate count match + advance
- reopen_barcode_generation(*, adda, user)                    # mgmt; refuse if any scanned
- get_barcode_snapshot(adda)                                  # dashboard
```

### 5.3 Refactor `tracking/services/barcode_service.py`

- Rename internal `generate_for_cutting(cutting_record)` → keep signature for back-compat, but add `generate_from_breakdown(barcode_gen_record)` that reads `AddaProductSizeColorPieceBreakdown` rows instead of `CuttingBundleItem`. Both produce equivalent `BarcodeBatch` rows. Aggregation key stable.

### 5.4 New `tracking/services/barcode_export_service.py`

```text
- _next_export_code()                                         # 'EXP-YYYY-NNN' via DB sequence or count+lock
- generate_csv(adda, user) -> (BarcodeExportBatch, bytes)
- generate_xlsx(adda, user) -> (BarcodeExportBatch, bytes)
- generate_pdf_summary(adda, user) -> (BarcodeExportBatch, bytes)
- list_exports(adda) -> queryset
- regenerate_for_export(export_batch) -> bytes               # re-download
```

Hard gate: refuse export unless `barcode_generation` stage complete for that Adda.

---

## 6. View + URL Plan

### Production URLs (add to `production/urls.py`)

```text
POST  addas/<code>/barcode-gen/start/           BarcodeGenStartView
POST  addas/<code>/barcode-gen/generate/        BarcodeGenGenerateView (idempotent)
POST  addas/<code>/barcode-gen/complete/        BarcodeGenCompleteView
POST  addas/<code>/barcode-gen/reopen/          BarcodeGenReopenView
GET   addas/<code>/barcode-gen/                 BarcodeGenWorkspaceView (+ ?embedded=1)
```

### Tracking URLs (add to `tracking/urls.py`)

```text
GET   exports/                                  ExportListView (recent exports across Addas)
POST  exports/<adda_code>/csv/                  ExportCSVView
POST  exports/<adda_code>/xlsx/                 ExportXLSXView
POST  exports/<adda_code>/pdf/                  ExportPDFView
GET   exports/<export_code>/download/           ReDownloadView (re-generates from live data)
```

### Refactor `tracking/views/barcode_views.barcode_export_csv` → call new service.

---

## 7. Template + UI Plan

All mobile-first. Use existing `form-shell` pattern. No isolated CSS.

### New templates

- `production/templates/production/barcode_gen_workspace.html` — full-page workspace
  - Section 1: Verified breakdown summary (read-only — pulls from `AddaProductSizeColorPieceBreakdown`)
  - Section 2: Start stage form (workers picker — mgmt-only)
  - Section 3: Generate Barcodes button (idempotent; shows count preview)
  - Section 4: Generated batches table (after generation: link to print sheet + export)
  - Section 5: Complete button (validates count match)
  - Section 6: Export panel (CSV / XLSX / PDF buttons)
  - Section 7: Export history (recent BarcodeExportBatch rows + re-download links)
- `production/templates/production/_stage_panel_barcode_gen.html` — embedded panel mirror

### Touched templates

- `production/templates/production/adda_detail.html` — add barcode_generation tab/iframe (auto via stage_panel pattern, no template edit needed if pattern holds)
- `tracking/templates/tracking/barcode_list.html` — add link to ExportListView + recent exports
- New `tracking/templates/tracking/export_list.html` — table of `BarcodeExportBatch` with re-download buttons

### Reusable components (already in base.html)

- `.hero-strip` for workspace headers
- `.empty-state-row` for empty breakdown / empty batches
- `.field`, `.sf-*`, panel-num for form shell
- DataTables helper for list pages

---

## 8. RBAC Plan

Reuse existing primitives:

- `Stage.access_by_skill` M2M includes `cutting_master` + `cutting_master_helper` for new `barcode_generation` stage row (seed migration).
- `_ensure_barcode_skill(user)` mirrors `_ensure_cutting_skill`.
- `_ensure_can_complete_barcode(user)` — same gate as cutting (helper skill OR super_admin).
- Export endpoints: require `PRODUCTION_ROLES` OR explicit perm `tracking.add_barcodeexportbatch`.
- Sidebar: add "Exports" entry under Administration (gated `tracking.view_barcodeexportbatch` OR `ROLE_SUPER_ADMIN`).

---

## 9. Test Plan

New test files (in addition to existing 141 tests):

- `production/tests/test_barcode_generation_workflow.py`
  - Fixture: Adda completed Cutting with breakdown rows
  - start_barcode_generation requires mgmt
  - generate_barcodes idempotent
  - complete refuses if count mismatch
  - complete advances Adda (or COMPLETES if last stage)
  - reopen refuses if any barcode scanned
  - reopen rolls back batches + record cleanly
- `production/tests/test_breakdown_materialization.py`
  - cutting completion creates breakdown rows matching CuttingBundleItem aggregation
  - cutting reopen deletes breakdown rows
  - back-compat: legacy product without barcode_generation stage still generates barcodes inline
- `tracking/tests/test_barcode_export.py`
  - CSV / XLSX / PDF export format correctness
  - export refused before barcode stage complete
  - re-download regenerates identical content
  - unique export_code

Target: +15-20 tests.

---

## 10. Documentation Plan

Update:

- `README.md` — add barcode_generation stage to workflow diagram
- `ARCHITECTURE.md` — add §5.X for breakdown model + barcode stage + export
- `docs/production/OVERVIEW.md` — refresh stage list
- `docs/production/CUTTING_DESIGN.md` — mark as superseded; pointer to this plan
- `docs/production/BARCODE_GENERATION.md` (NEW) — stage spec
- `docs/tracking/EXPORTS.md` (NEW) — export flow + future label tracking
- ARCHITECTURE/Workflow diagrams (ASCII, since no design tool): stage flow + breakdown→batch→export sequence

---

## 11. Implementation Phases (5 PRs)

| PR | Scope | Files | Tests |
|----|-------|-------|-------|
| **PR-A** | Models + migrations + seed Stage. No service/view changes yet. | 4 models, 4 migrations | model-level unit tests |
| **PR-B** | Refactor cutting completion to materialise breakdown. Keep inline barcode for back-compat. | cutting_service, barcode_service (rename helper) | 5 tests (materialisation + back-compat) |
| **PR-C** | New `barcode_generation_service` + views + workspace template. Wire to Stage. | service, views, templates, urls | 7 tests (workflow + reopen + count match) |
| **PR-D** | Export service + views + templates. Refactor existing CSV export. | export service, views, templates | 5 tests (3 formats + gate + re-download) |
| **PR-E** | Docs + diagrams + LabelPrintQueue stub clarification | doc files | 0 tests (doc only) |

Each PR self-contained: tests must pass at end of each. Total estimate: 6-8 hours focused work.

---

## 12. Risks + Edge Cases (for next session implementer)

- **Adda mid-flight migration**: if 0022 backfill runs while an Adda is mid-cutting (`completed_at` IS NULL on cutting sr), skip that Adda — only backfill for completed cutting records.
- **Bundle delete after breakdown materialised**: should refuse — breakdown rows are derived. Add guard in `delete_bundle` service.
- **Export of incomplete Adda**: gate at service layer (raise ValidationError if barcode stage not complete).
- **Re-generation after reopen**: barcode stage reopen MUST clear export batches too (or refuse if any export exists). Safer: refuse reopen if export exists; admin must hard-cancel exports first.
- **Per-product workflow without barcode stage**: cutting completion path falls through to inline `generate_for_cutting`. Must not break legacy `test_golden_path.py`.
- **Concurrent export creation**: `_next_export_code` uses DB sequence or `select_for_update` on a counter row. Same pattern as `Product.adda_counter`.

---

## 13. What this plan does NOT do

- Implement label print queue logic (deferred per user instruction). Stub model only.
- Add ffmpeg / video compression / printer integration.
- Refactor BatchBarcode schema (kept stable).
- Touch storefront / inventory / accounts apps.
- Implement Phase 2-11 of original modernization ask (mobile pass, design system overhaul, etc.) — separate workstream.

---

## Next step

User approves this plan → next session opens with PR-A (models + migrations + seed). Each subsequent session = one PR. Tests must stay green throughout.

Ready for review. No code touched.
