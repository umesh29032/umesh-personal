---
id: root-glossary
type: topic-canonical
status: active
owner: handwritten
scope: all — system-level
anchors: —
verified: 2026-07-13
---

# GLOSSARY — Kapil Enterprises Inventory

One-line definitions of the domain terms used across this codebase. This is a
garment-manufacturing business, so many terms are Hindi/Hinglish factory words.
**Read this first if you're new** — the model names won't make sense without it.

> Convention note: code comments are intentionally written in Hinglish (Hindi in
> Latin script) with short "why" notes. That's a deliberate house style, not a bug.

---

**Machine / MachineType / MachineAssignment (R10-A)** — physical asset · its KIND (reusable across operations; stages point at types, never instances) · operator possession window (one OPEN holder per machine; DateTime, append-only). **Stage Work Type** — Manual|Machine (Machine ⇒ MachineType mandatory; DB constraint). **StageCategory** — display grouping (Pre Production/Stitching/Finishing/Dispatch), NEVER workflow/money/access.

## Production / manufacturing terms

| Term | Means | Model / where |
|---|---|---|
| **Adda** | One **production batch** — a single run of a product (e.g. `T-SHIRT-001`). Moves through the workflow stages start→finish. | `production.Adda` |
| **Product** | A factory product *definition* (T-SHIRT, NIKKAR). This is the **manufacturing** master, NOT a sellable catalog item. | `production.Product` |
| **Stage** (library) | A reusable, admin-managed step definition (Layering, Cutting…). Holds access rules (skills/roles) + a default cost rate. | `production.Stage` |
| **WorkflowStage** | A Stage **attached to one Product** with an order position + binding cost rate. The per-product production flow = its ordered WorkflowStages. | `production.WorkflowStage` |
| **AddaStageRecord** | The execution row for "this Adda × this WorkflowStage" — one per stage an Adda passes through. Holds the **frozen manufacturing cost** snapshot. | `production.AddaStageRecord` |
| **Layering** | First stage: laying cloth rolls in stacked **layers** on the cutting table. | `LayeringRecord`, `LayeringRollEntry` |
| **Pattern Design** (renamed from "Cutting Pattern" 2026-07-05, R8; internal code stays `cutting_pattern`) | Stage where the pattern master verifies every Product Pattern Design on the layered cloth (checklist + photos/video) + per-size proportions. FIXED-per-Adda pay. | `CuttingPatternRecord` |
| **Cutting** | Stage that actually cuts the pieces; produces the piece **breakup** + **bundles**. | `production.CuttingRecord` |
| **Production Component** (= ProductPattern) | 🔒 Owner-ratified 2026-07-11: the manufacturing COMPONENT of a garment (Body, Panel, Sleeve, Collar…). Owns cut counts, shortages/bottlenecks, per-garment multiples (`ProductPatternAssignment.pieces_count`), bundle itemization, and the complete-garment derive. The table keeps its historical name `ProductPattern`; docs/UI labels say *Production Component*. Its `PatternPiece.fabric_group` is only the LAY-routing attribute (which CuttingStream lane cuts it) — never the component itself. Proof: docs/PRODUCTION_COMPONENT_ARCHITECTURE_REVIEW.md. | `production.ProductPattern` |
| **Pattern** (ProductPattern) | A reusable cut-piece shape (Front, Back, Sleeve, Collar). A product needs N of each. (Historical name — see **Production Component** above.) | `production.ProductPattern` |
| **CuttingStream** (lane / Production Cycle) | ONE lay→pattern→cut cycle inside an Adda, identity `(adda, fabric_group, sequence)`. seq 1 = derived from the Blueprint; seq >1 = declared management act with a mandatory reason (split lay / recut / additional production — reasons are DATA). The JOIN (bundles/barcodes/ops unlock) = every blocking lane's cutting complete; post-join lanes append, never regress. 🔒 Challenge-ratified 2026-07-11: sequence IS the production cycle; no third abstraction. | `production.CuttingStream` |
| **Breakup** (CuttingPieceBreakup) | Per-`(size, color, pattern)` **piece counts** produced by cutting. | `production.CuttingPieceBreakup` |
| **Bundle** (CuttingBundle) | A size-grouped container of cut pieces. Its **items** are `(pattern, color, count)` lines. | `CuttingBundle`, `CuttingBundleItem` |
| **Breakdown** (…PieceBreakdown) | The FINAL verified per-`(size, color)` piece count snapshot — the input that barcode generation + future stages consume. | `AddaProductSizeColorPieceBreakdown` |
| **Barcode Generation** | Stage that turns the verified breakdown into barcode **ranges**. | `BarcodeGenerationRecord` |
| **BarcodeBatch** | A contiguous sequence **range** for one `(Adda, color, size)` — e.g. seq 1..60. NOT one row per piece (storage win). | `tracking.BarcodeBatch` |
| **BatchBarcode** | Per-**piece** scan state (`pending→packed→dispatched`). Lazily created on first scan — untouched pieces have no row. | `tracking.BatchBarcode` |
| **Leftover** | Cloth left on a roll after layering — tracked for reuse, not waste. | `RemainingClothOfClothRoll` |
| **ClothRoll** | A physical roll of cloth (`CR-000142`). | `raw_materials.ClothRoll` |
| **StorageLocation** | Where rolls (and future finished goods) are physically kept. | `raw_materials.StorageLocation` |

## People / access terms (three separate concepts — don't conflate)

| Term | Means | Model |
|---|---|---|
| **Worker** (was *karigar*) | An employee doing production work. Renamed from "karigar" 2026-06-02. | RBAC role `worker`. Identity boundary (WP-C): account data (email/phone_number/salary-reference/is_active) on `User`; payroll payout metadata (bank/UPI/pay_basis) on `expense.WorkerProfile` — status displays read `User.is_active` |
| **Role** | The **RBAC source of truth** for module/sidebar/URL access. Roles: `super_admin`, `manager`, `worker`, `listing_team`, `accountant`. | `inventory.Role` |
| **Skill** | What production *work* a user can do (`cutting_master`, …). Gates **stage** access — NOT module access. | `accounts.Skill` |
| **UserType** | Display/classification label only (e.g. "Supplier"). **Never** gates access. | `accounts.UserType` |

## Payroll / money terms (expense app)

| Term | Means | Model |
|---|---|---|
| **Allocation (earning line)** | The settlement-written earning line: created at settlement FINALIZE on `settlement_quantity` (verified-else-good) — era-B default (`LEDGER_CREDIT_AT_ALLOCATION=False`); allocation-time freeze only under the legacy era-A lever. | `expense.StageWorkAssignment` |
| **Allocation (work split)** | A worker's assigned slice of a stage's piece pool — production truth, NO money; dimension-scoped (colour/size), append-only with void. | `production.WorkerStageAllocation` (pool_service) |
| **Earning** | A **credit** in the ledger — money the factory owes the worker for allocated work. | `WorkerLedgerEntry` (credit) |
| **Advance** | Cash given to a worker *before* earnings — a **separate loan pool**. Does NOT touch the payable ledger; recovered at settlement. | `expense.WorkerAdvance` |
| **Payable / Balance** | What's owed a worker **right now** = `SUM(credits) − SUM(debits)`. Always computed live, **never stored**. | derived in `ledger_service.worker_balance` |
| **Settlement** | A payout event (any time the owner decides). Clears some/all payable + recovers some/all advances. | `expense.PayrollSettlement` |
| **Stage costing** | The **manufacturing** cost of running a stage (product profitability) — distinct from worker pay. Frozen at stage completion. | `AddaStageRecord.processing_cost` |

---

## How the core models relate (ER diagram)

Production lifecycle + the payroll ledger chain. (Renders on GitHub.)

```mermaid
erDiagram
    PRODUCT      ||--o{ WORKFLOWSTAGE : "ordered flow"
    PRODUCT      ||--o{ ADDA : "batched as"
    STAGE        ||--o{ WORKFLOWSTAGE : "library → bound"
    ADDA         ||--o{ ADDASTAGERECORD : "executes"
    WORKFLOWSTAGE ||--o{ ADDASTAGERECORD : "instance of"

    ADDASTAGERECORD ||--o| LAYERINGRECORD : "typed (1:1)"
    ADDASTAGERECORD ||--o| CUTTINGRECORD : "typed (1:1)"
    ADDASTAGERECORD ||--o| BARCODEGENERATIONRECORD : "typed (1:1)"

    CUTTINGRECORD ||--o{ CUTTINGPIECEBREAKUP : "produces"
    CUTTINGRECORD ||--o{ CUTTINGBUNDLE : "groups into"
    CUTTINGBUNDLE ||--o{ CUTTINGBUNDLEITEM : "contains"
    CUTTINGRECORD ||--o{ ADDAPRODUCTSIZECOLORPIECEBREAKDOWN : "verifies"

    ADDA          ||--o{ BARCODEBATCH : "seq ranges"
    BARCODEBATCH  ||--o{ BATCHBARCODE : "per-piece (lazy)"

    ADDASTAGERECORD ||--o{ STAGEWORKASSIGNMENT : "allocated to workers"
    USER          ||--o{ STAGEWORKASSIGNMENT : "earns via"
    STAGEWORKASSIGNMENT ||--o{ WORKERLEDGERENTRY : "credits (earning)"
    USER          ||--o{ WORKERLEDGERENTRY : "ledger of"
    USER          ||--o{ WORKERADVANCE : "loaned"
    USER          ||--o{ PAYROLLSETTLEMENT : "paid via"
    PAYROLLSETTLEMENT ||--o{ PAYROLLSETTLEMENTITEM : "recovers advances"
    WORKERADVANCE ||--o{ PAYROLLSETTLEMENTITEM : "recovered by"

    CLOTHROLL     }o--|| CLOTHTYPE : "is"
    CLOTHROLL     }o--|| CLOTHCOLOR : "is"
    ADDA          ||--o{ CLOTHROLL : "consumes"
```

*Read first for the big picture: [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md). Deeper:
[docs/production/OVERVIEW.md](docs/production/OVERVIEW.md),
[docs/archive/production/PAYROLL_ARCHITECTURE.md](docs/archive/production/PAYROLL_ARCHITECTURE.md).*
