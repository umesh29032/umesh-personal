> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/R1_STAGE_DOMAIN_REVIEW.md](../../R1_STAGE_DOMAIN_REVIEW.md) (contribution_schema contract).

# P2 Pre-Implementation Validation — Schema-Driven Worker Reporting

**Date:** 2026-06-10 · **Purpose:** prove the worker reporting surface is schema-driven, stage-agnostic, open-closed BEFORE building pt.2b. Grounded in shipped code: `stages/base/handler.py` (`contribution_schema`), `stages/cutting/handler.py` (reference override), `worker_task_service.py` (`report_contributions` / `save_draft_contributions` / `complete_worker_task`). Validates against R1 locks (I1-I10, §2A Stage Contract, §5A two truths, §8A scan seam).

## 0) The generic renderer (the ONLY worker-UI logic — zero stage conditionals)

```
GET  /…/report/        view: task → handler = registry.get(stage_record.workflow_stage.stage.code)
                              schema  = handler.contribution_schema(adda)
                              template loops schema['fields']:
                                kind == 'choice'   → chip-picker from field['options'] (swatch optional)
                                kind == 'quantity' → numeric input, field['unit'] label
POST Save Draft        parse lines BY SCHEMA KEYS → save_draft_contributions(task, lines)
POST Submit & Complete parse lines BY SCHEMA KEYS → save_draft_contributions(...) → complete_worker_task(task)
```

Dispatch = registry by `Stage.code` (I1/I2). Rendering = data (`kind` vocabulary). Persistence = generic `lines` dict. Money = data (`credits_workers`, rates). **The renderer never sees a stage name.** The only framework-level dependency is the `kind` vocabulary — adding a *stage* requires nothing; adding a new *kind* is a one-place framework extension every stage then shares.

**P2 build rules derived from this (anti-overfit guards):**
1. Template iterates `schema['fields']` — never hardcodes colour/size/qty names.
2. POST parsing iterates schema keys — unknown future keys flow through to the service layer (which maps known columns now; the `attributes` JSONB catch-all is the locked additive seam).
3. No stage names in view/template/JS; no money rendered (D-locked).
4. Locked (submitted) state renders the SAME schema read-only + Submitted-At.
5. Line add/remove is generic (`line_label` from schema).

## 1) Example: quantity-only stage (archetype A or simple C — e.g. thread-cutting-like)

| Aspect | Content |
|---|---|
| **Stage Contract** | Inputs: upstream typed record. Outputs: completed qty (dimensional, adda-level). Contribution: base schema. Costing: per_piece (or per_layer), `cost_quantity` from typed record. Completion rule: handler-local. Traceability: dimensional (expected-piece). Missing: count-mismatch. Alter: detected_stage. Settlement: `credits_workers=True`, expected-freeze applies. |
| **Contribution Schema** | Base default (handler.py:127-133): `{'line_label':'line','fields':[{'key':'reported_quantity','kind':'quantity','label':'Quantity','required':True,'unit':'pieces'}]}` |
| **Worker UI fields** | One numeric input. Nothing else appears — the renderer simply has one field to draw. |
| **Saved contribution** | `WorkerStageContribution(task, reported_quantity=120, color=NULL, size=NULL, bundle_item=NULL, expected_*=NULL)` |
| **Draft** | `save_draft_contributions` — deletes the task's current lines, recreates from POST (draft ≠ history → replace is safe), task `assigned→in_progress`. Excluded from readiness/costing/settlement/earnings (only COMPLETED tasks count). |
| **Submit & Complete** | `complete_worker_task` — freezes `expected_rate = role_rate | stage rate`, `expected_earning = qty × rate` (HALF_UP), NO ledger entry (Option B), status→`completed`, locked for the worker (manager correction via `verified_quantity`). |

## 2) Example: colour + size + quantity stage (Cutting — the shipped reference)

| Aspect | Content |
|---|---|
| **Stage Contract** | Archetype C. Inputs: layered material + pattern plan. Outputs: **grain I3** pieces + bundles + breakdown. Contribution: override below. Costing: per_piece / per_bundle (handler maps). Completion rule: qty validations vs upstream. Traceability: dimensional (expected-piece truth born here). Missing: count-mismatch. Alter: detected/origin/rework target. Settlement: payable. |
| **Contribution Schema** | Shipped override (cutting/handler.py): colour choice (active `ClothColor` palette, swatches) + size choice (product's active `ProductSize`) + quantity. `line_label='piece line'`. |
| **Worker UI fields** | Colour chips (with swatches) · size chips · qty input — per line, multi-line add/remove. Same template as example 1; it just has three fields to draw. |
| **Saved contribution** | One row per line: `WSC(task, reported_quantity=40, color_id=3, size_id=7, expected_*=NULL)` — keys map 1:1 from schema keys to model columns. |
| **Draft / Submit** | **Byte-identical mechanics to example 1** — same two service calls, zero stage logic. This is the proof the pipeline is stage-blind. |

## 3) Example: future machine-based stage (e.g. Overlock)

| Aspect | Content |
|---|---|
| **Stage Contract** | Archetype C, machine actor. Inputs: pieces from upstream. Outputs: grain I3 (operated pieces). Contribution: below. Costing: per_piece or per_operation/per_hour (**additive enum value + handler arithmetic — §4 lock; no schema redesign**). Completion rule: handler-local. Traceability: dimensional. Missing: count-mismatch. Alter: prime origin_stage candidate. Settlement: payable. Sub-stage ONLY if the §9 trigger rule fires (different workers/rates OR independent progress) — else ONE stage with operation measures. |
| **Contribution Schema** | `fields: [colour choice, size choice, qty(pieces), machine choice (options from future Machine registry), machine_hours quantity(unit:'hours')]` — first two kinds already exist; machine + hours reuse `choice` + `quantity`. **NO new renderer kind needed.** |
| **Worker UI fields** | Colour chips · size chips · qty · machine chips · hours input — rendered by the SAME loop, no UI edit. |
| **Saved contribution** | `WSC(qty, color_id, size_id, attributes={'machine_id':4,'machine_hours':'6.5'})` — `machine_*` keys map into the **`attributes` JSONB**, the F1-locked deferred column. **This stage is its trigger:** column + a generic services pass-through (schema-unknown keys → attributes) land additively with it. |
| **Draft** | Unchanged — replace-semantics covers any field set. |
| **Submit & Complete** | Unchanged freeze for piece-rate; per_hour/per_operation earning = the §4 cost≠earning extension point (handler/cost_service arithmetic, additive). Option B unchanged: no ledger entry. |

## 4) Example: future scan-capable stage (e.g. Packing, `scan_policy=required`)

| Aspect | Content |
|---|---|
| **Stage Contract** | Archetype F. Inputs: identified pieces. Outputs: packed qty per (colour,size) = **expected-piece truth** + scan events (identified truth, tracking-owned). Contribution: below. Costing: per_piece/flat. **Completion rule: handler-local packing validations + scan threshold via `scan_policy=required` + future `validate_scan` hook (§8A) — a STAGE-completion gate (contract field 5), not a contribution requirement.** Traceability: identified + dimensional. Missing: scan-shortfall (plus count-mismatch). Settlement: configurable. |
| **Contribution Schema** | `fields: [colour choice, size choice, qty(unit:'pieces packed')]` — **dimensional only.** Scanning is NOT a contribution field: scan events flow to the tracking primitive through the §8A seam; the worker's REPORT stays production truth. (A future `'scan'` field kind MAY be added by the Barcode/Traceability review — one renderer extension, all stages inherit. Not designed now.) |
| **Worker UI fields** | Colour chips · size chips · qty — same renderer, zero barcode awareness in the worker report UI. |
| **Saved contribution** | `WSC(qty, color_id, size_id)` — identical shape to example 2. **No barcode reference in production truth (§5A).** |
| **Draft** | Unchanged. |
| **Submit & Complete** | Worker task completes on the dimensional report — unchanged freeze. The `required` scan policy gates the STAGE's completion (handler `complete()` checks scan state via IDs from the tracking primitive), not the worker's task. So: production truth exists with zero scans; the gate is a stage rule; Missing detection can compare expected (contributions/breakdown) vs scanned — derived, never stored (§5A.3). |

## 5) Verdict

| R1/owner requirement | Holds? | Why |
|---|---|---|
| Schema-driven, no stage conditionals in worker UI | ✅ | Registry dispatch + `kind`-keyed rendering; examples 1-4 use one renderer |
| Open-closed for new stages | ✅ | New stage = handler + Stage row + WorkflowStage placement; UI/services untouched |
| Singer/Overlock/Flatlock/Covering fit | ✅ | Example 3 — existing kinds + JSONB seam; no redesign |
| QC fits | ✅ | Archetype D: counts via base/quantity schema or no contribution (`credits_workers=False`); JSONB if defect-counts needed |
| Packing/scan-capable fits | ✅ | Example 4 — scan = stage capability + completion gate, never contribution data |
| Missing/Alter independent of barcodes | ✅ | Cases anchor on WSC/breakdown dimensional truth (§5A); scan-shortfall = optional detection source |
| Production truth without barcodes | ✅ | Contributions + freezes + settlement read dimensional truth only |
| Barcode lifecycle NOT designed | ✅ | Only the §8A seam referenced; everything scan-detailed deferred |

**Residual risks for P2 (the two ways we could still overfit — build rules 1-2 in §0 exist to prevent them):** hardcoding the three Cutting field names in template/POST parsing; or binding parse logic to model columns instead of schema keys. Both are caught by adding ONE P2 test: render+parse a synthetic handler whose schema has a field set ≠ Cutting's (the open-closed proof test pattern, extended to the report surface).

— End. No implementation in this document.
