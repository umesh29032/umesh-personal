# P4.2 — production↔tracking Cycle Break: Barcode Design Review

> Requested 2026-06-10. **Design review ONLY — no code, no migrations, no DB changes.**
> Validates the architecture before deciding whether to execute P4.2. Companion to
> [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md) (Phase 7) + [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md).

## TL;DR — the risk is much lower than the plan assumed
The barcode models in `tracking` reference production via **string FKs**
(`'production.Adda'`, `'production.CuttingBundle'`, `'production.ProductSize'`, …). **String FKs are
NOT import edges** — so the production↔tracking cycle lives entirely in the **service + view layer**, not
the models. Therefore P4.2 is most likely a **CODE RELOCATION (move the assembly/export logic + repoint
views), NOT a cross-app model + data migration.** The `BarcodeBatch` / `BatchBarcode` / `BarcodeExportBatch`
tables + their rows **stay exactly where they are** — no data moves, no irreversible DB step.
That flips the execute/defer calculus: the scariest part (data migration) probably isn't needed.

---

## 1. Current barcode ownership + dependencies
| Thing | Lives in | Notes |
|---|---|---|
| `BarcodeGenerationRecord` (stage record) + `LabelPrintQueue` | **production** | OneToOne to AddaStageRecord; the *stage* |
| `BarcodeBatch` (contiguous seq range per Adda·color·size) | **tracking** | string-FK → Adda/Product/CuttingBundle/ProductSize/ClothColor |
| `BatchBarcode` (lazy per-piece scan state) | **tracking** | string-FK → Adda/ProductSize; created on first scan |
| `BarcodeExportBatch` (export manifest) | **tracking** | re-download audit |
| `AddaHistory` / `ClothRollHistory` / `ProductHistory` | **tracking** | legit append-only history primitive |

**The cycle (service/view layer):**
- `production → tracking` (intended): production services call `log_adda` (history); `production.stages.
  barcode_generation.service.generate_barcodes` orchestrates + calls tracking's assembly + reads `BatchBarcode`.
- `tracking → production` (the violation, currently `ignore_imports`-suppressed):
  - `tracking.services.barcode_service` — **ASSEMBLY** (`generate_for_cutting`, `generate_from_breakdown`,
    `_generate_legacy_batch`) reads `CuttingBundleItem`, `AddaProductSizeColorPieceBreakdown`, `AddaStageRecord`
    to build `BarcodeBatch` rows.
  - `tracking.services.barcode_export_service` — reads `Adda`, `BarcodeGenerationRecord`, `AddaStageRecord`.
  - `tracking.views.{barcode,export,history,dashboard}` — import `Adda` (display).
- **Models do NOT import across apps** (string FKs) — so the *table* layout is already decoupled.

## 2. Proposed target architecture (Option A — recommended)
**`tracking` becomes a dumb primitive BELOW production: barcode RANGE + per-piece SCAN state + HISTORY,
taking plain IDs/values, importing NO production.** Barcode **ASSEMBLY** is a production concern (it reads
cutting data), so it moves INTO production.
- **Move to production:** `generate_for_cutting` / `generate_from_breakdown` / `_generate_legacy_batch`
  (the production-reading assembly). Production writes `tracking.BarcodeBatch` rows — a `production → tracking`
  import (allowed, downward, once the layers list places tracking below production).
- **Stays in tracking (no production import):** `BarcodeBatch`/`BatchBarcode`/`BarcodeExportBatch`/`*History`
  models (string-FK'd data — UNCHANGED); the **scan** + **QR render** + lazy `BatchBarcode` create logic
  (takes a barcode value/IDs); the export FILE generation (reads only tracking rows).
- **Move out of tracking:** `barcode_export_service`'s production reads + the 4 production-coupled VIEWS →
  to **production** (they're production-stage surfaces) or the **inventory/apps layer** (which already
  composes production+tracking). Decision D1 below.
- **Flip the `.importlinter` layers list:** tracking BELOW production (it's a primitive). Then drop the
  `ignore_imports` block (P4.4) and the acyclic contract goes green for real.
- **Rejected — Option B** (keep tracking above production, invert the logging edge): would force moving the
  history-logging out of production, churning far more call sites; and it fights the "tracking = primitive"
  intent. Option A matches the existing string-FK data design + the microservice goal (§9).

## 3. Migration sequence (CODE relocation — no data migration expected)
1. **Characterization first** (§5): lock barcode-gen + export + scan behavior.
2. **Relocate assembly:** move the 3 assembly fns into a `production` service (e.g.
   `production/stages/barcode_generation/assembly.py`); `generate_barcodes` calls them directly (no longer
   hops to tracking). They import `tracking.models.BarcodeBatch` to write rows (production→tracking).
3. **Relocate export production-reads + the 4 views** to production/apps (D1); tracking keeps pure scan/QR/file.
4. **Confirm tracking imports zero production** (`grep -rn "from production\|import production" tracking/`),
   then **flip the layers list + delete the `ignore_imports`** (P4.4). Contract green.
5. **No `makemigrations`/`migrate` expected** — if any model `Meta`/app-label is untouched, Django generates
   nothing. VERIFY with `makemigrations --check` (must say "No changes"). If a model *does* need to move
   apps later, that's a SEPARATE, explicitly-flagged data migration — not part of this code relocation.

## 4. Rollback strategy
- It's a **code move behind characterization tests** → rollback = `git revert` the relocation commits. No
  data touched, so no down-migration, no data-loss window.
- Do it as **small reversible PRs** (assembly move; export/view move; contract flip) — each independently
  revertable, each gate-green. The contract flip is the last, most-isolated step.
- If `makemigrations --check` ever reports a change, STOP — that signals an unintended model move; reassess
  (a real data migration would then need P0.5 clone rehearsal).

## 5. Characterization tests (lock before moving)
Existing safety net: `production.tests.test_barcode_generation_workflow`, `tracking.tests.test_barcode_export`,
`tracking.tests.test_scan_view`. Before relocating, assert + (if thin) extend: barcode ranges generated for a
cutting Adda match expected (seq ranges, per-color/size counts, legacy single-batch); export file/manifest
content; scan creates the lazy `BatchBarcode` with correct status. Re-run identical after each relocation
step — output must be byte-identical.

## 6. Future Missing-Piece compatibility
Missing pieces = pieces expected but not packed/scanned. The per-piece truth is `BatchBarcode` (status) +
`BarcodeBatch` (the expected range) — **kept in tracking as the scan primitive**. A future `MissingPieceCase`
(production/QC domain) READS that scan state + the (color,size) dims to compute/track shortfall. Relocating
*assembly* into production does NOT disturb this — the scan/range data stays put + addressable by IDs. ✓ compatible.

## 7. Future Alter/Rework compatibility
Alter/Rework attaches to a piece/defect. It references `BatchBarcode` (the piece) + dims + stage. Same as
§6: tracking remains the per-piece primitive; `AlterCase` is a future domain that reads it. The relocation
keeps barcodes as a clean, ID-addressable primitive — exactly what a rework lifecycle needs to point at. ✓

## 8. Future stage-engine compatibility
`barcode_generation` is a registered stage (handler). After relocation, `BarcodeGenHandler.complete` →
production assembly → tracking ranges; the stage stays open-closed (a future stage that also needs barcodes
calls the production assembly service). `contribution_schema`/cost/credit seams are untouched. ✓

## 9. Future microservice-extraction implications (strong argument FOR Option A)
With assembly moved out, `tracking` becomes a **pure scan/range/history service that imports no production
and is already string-FK'd** (refs are IDs, not Python imports). That is the *ideal* shape for a future
extraction (barcode/scan microservice): it takes IDs + values, owns its tables, exposes scan/range APIs.
Option A actively moves us toward extractability; the current cycle actively blocks it. ✓✓

## 10. Risks · coupling · irreversible decisions
- **Risk (down-rated):** NO data migration expected → the big irreversible risk is likely absent. Main risk
  = a missed production read left in tracking (caught by the post-move grep + the layers contract) or a view
  move that breaks a URL/template (caught by tests + smoke).
- **Coupling after:** one-way `production → tracking` (assembly writes ranges; logging writes history).
  tracking → production = ZERO. Acyclic, contract-enforced (ignores removed).
- **Irreversible decisions to confirm BEFORE executing:**
  - **D1 — where do the barcode/export/history VIEWS live?** production (stage surfaces) vs inventory/apps
    layer (composition). Recommend **inventory/apps** for the cross-cutting list/export/dashboard views;
    keep stage-embedded barcode panel in production. *(Reversible, but pick once.)*
  - **D2 — layers direction: tracking BELOW production** (primitive). This is the architectural commitment;
    everything else follows. (Matches the string-FK data design + microservice goal.)
  - **D3 — do the `BarcodeBatch`/`BatchBarcode` MODELS ever move to production?** Recommendation: **NO** —
    leave them in tracking (that's what makes tracking a reusable scan primitive + avoids a data migration).
    Only revisit if barcodes become a production-owned concept during the manufacturing-domain redesign.

## Recommendation
P4.2 is **safer than first framed** — a service/view **code relocation**, not a data migration (because the
models are string-FK'd). It is **compatible with** the pending Missing-Piece / Alter-Rework / stage-engine
work and **advances** microservice extractability. **But** it intersects the still-evolving manufacturing
domain (barcode ownership could shift in that redesign — D3). Reasonable paths: (a) execute now as small
reversible code-relocation PRs (low data risk), or (b) defer until the manufacturing-domain review settles
barcode ownership, since that review could change D3. No code until you decide.
