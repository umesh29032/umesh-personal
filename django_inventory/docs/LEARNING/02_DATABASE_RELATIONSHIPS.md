---
id: learning-02-database-relationships
type: lesson
status: active
owner: handwritten
scope: learning — generic concept
anchors: —
verified: 2026-07-13
---

# Database — how models STORE data, how they CONNECT, how a row is BORN

> THE canonical answer to: "kaunsa model data kaise save karta hai, backend me
> kaise store hota hai, sab kaise jude hain, aur flow kya hai." Quick ER sketch:
> [PROJECT_KNOWLEDGE_MAP §6](../PROJECT_KNOWLEDGE_MAP.md). Per-model one-liners:
> each app's [GUIDE](../apps/README.md). Yeh file = poora picture + flow diagrams.

---

## 0) Pehle base — model = table, instance = row

Django me `class Foo(models.Model)` = PostgreSQL ki ek TABLE. Us class ka har
object = ek ROW. Har field = ek COLUMN.

```
class WorkerAdvance(models.Model):        →  TABLE expense_workeradvance
    amount = DecimalField(...)            →  COLUMN amount  NUMERIC(12,2)
    worker = ForeignKey(User, ...)        →  COLUMN worker_id  INTEGER → FK
```

Table naam default = `<app>_<modelname>` lowercase. FK column = `<field>_id`
(Postgres sirf ID store karta hai, poori row nahi — JOIN se milti hai). Money
HAMESHA `DecimalField` (Float kabhi nahi — paisa exact). `created_at/updated_at`
har table me `TimeStampedModel` (core, abstract) se aate hain.

`.save()` → Django `INSERT` (nayi row) ya `UPDATE` (purani) SQL chalata hai.
Is project me yeh VIEWS nahi karte — sirf SERVICES, `@transaction.atomic` ke
andar (rule 4). Truth/money tables me to har `.save()` single-writer service
se hi (rule 5, CI gates).

---

## 1) System ke 3 SPINE

```
 SPINE 1: MATERIAL       SPINE 2: WORK (production truth)   SPINE 3: MONEY (financial truth)
 ───────────────         ──────────────────────────────    ───────────────────────────────
 ClothRoll               Adda                               AddaSettlement
   │ adda FK (1→1)         │ stage_records (1→many)            │ items (frozen)
   ▼                       ▼                                   ▼
 RemainingCloth         AddaStageRecord                      AddaSettlementItem
 (leftover+weight)        │ worker_tasks                     StageWorkAssignment (earning line)
                          ▼                                   │ adda_settlement FK = era marker
                     WorkerStageTask (WHO)                     ▼
                          │ contributions                   WorkerLedgerEntry (THE money, append-only)
                          ▼                                   ▲ assignment FK
                   WorkerStageContribution (WHAT) ─settlement_line─┘   (provenance loop)
```

Material = raw_materials app · work = production app · money = expense app.
Tracking app har spine ke events ka append-only timeline rakhta hai (kisi ko
import nahi karta — primitive).

---

## 2) Har important model — kya store + example ROW

### Production truth (production app)
| Model → table | Key columns | Example row |
|---|---|---|
| **Adda** → `production_adda` | `code` unique editable=False (auto), `product_id`, `current_stage_id`, `status`, `started_at`(auto), `completed_at` | `3-PATTI-001, 3 Patti, stage=Cutting, in_progress` |
| **AddaStageRecord** → `production_addastagerecord` | `adda_id`, `workflow_stage_id`, `started_at`, `completed_at`, frozen `processing_cost` (honest-NULL) | `3-PATTI-001, Cutting, processing_cost=NULL until priced` |
| **WorkerStageTask (WST)** → `production_workerstagetask` | `stage_record_id`, `worker_id`, `status`, `*_at` stamps, `verified_by` | `Cutting#9, utest, status=completed` |
| **WorkerStageContribution (WSC)** → `production_workerstagecontribution` | `task_id`, `color_id`, `size_id`, `reported_quantity` (IMMUTABLE), `verified_quantity` (mgmt fix), frozen `expected_rate`/`expected_earning`, `settlement_line_id`, `bundle_item_id` | `task=…, Red, Size-1, reported=60, verified=NULL, rate=3.00, earning=180.00` |

### Material (raw_materials app)
| Model → table | Key columns | Example |
|---|---|---|
| **ClothRoll** → `raw_materials_clothroll` | `roll_id` (CR-seq global), type/color/location FKs, `purchased_date`, `cost_per_kg` (PURCHASE fact, nullable), `adda_id` (1→1), `status` | `CR-000142, Cotton/Red, ₹200/kg, adda=3-PATTI-001, used` |
| **RemainingClothOfClothRoll** → `production_remainingclothofclothroll` | `roll_id`, `source_adda_id`, `remaining_weight_kg`, `is_consumed`, `consumed_in_adda_id` | leftover 3.10kg of CR-000142 |

### Financial truth (expense app)
| Model → table | Key columns | Example |
|---|---|---|
| **WorkerLedgerEntry** → `expense_workerledgerentry` | `worker_id`, `entry_type` (credit/debit), `category` (stage_earning/advance_recovery/settlement_payment/reversal…), `amount` (CHECK >0), `entry_date`, FK `assignment`/`advance`/`settlement`, `reverses_id` (self-FK unique) | `utest, credit, stage_earning, 180.00, assignment=SWA#42` |
| **StageWorkAssignment (SWA)** → `expense_stageworkassignment` | `stage_record_id`, `worker_id`, color/size, `allocated_quantity`, frozen `earning_rate_snapshot`/`earning_amount_snapshot`, `adda_settlement_id` (NULL=era-A / set=era-B), `voided_at` | `Cutting#9, utest, 60, rate=3, amt=180, ADST-0003` |
| **AddaSettlement** → `expense_addasettlement` | `reference` (ADST-XXXX unique), `adda_id`, `status`, frozen totals, `supersedes_id`, `settled_at/by` | `ADST-0003, 3-PATTI-001, finalized, expected_total=225` |
| **AddaSettlementItem** → `expense_addasettlementitem` | FROZEN per-worker: `expected_earning`, `advance_outstanding_before`, `advance_recovered`, `final_payable` | `ADST-0003, utest, expected=225, recovered=0, payable=225` |
| **PayrollSettlement / Item** → `expense_payrollsettlement*` | cash payment (SETL-XXXX) + recovery lines (XOR-parented, `reversed_at`) | `SETL-0012, utest, amount_paid=225` |
| **WorkerAdvance** → `expense_workeradvance` | `worker_id`, `amount`, `advance_date`, `entered_by` | loan ₹500 to utest |

### History (tracking app — append-only)
`AddaHistory/ClothRollHistory/ProductHistory` → `tracking_*history`:
`change_type`, actor, `metadata` (JSONB), timestamp. `BarcodeBatch` →
`(adda,color,size)` + `start_seq`/`end_seq` = piece identity ranges.

---

## 3) FK rules — kaun kisko delete se bachata hai

`on_delete` = "parent delete hua to child ka kya":
- **PROTECT** (money+history default): parent delete = ERROR. Ledger ke peeche
  ka worker/Adda/SWA kabhi gayab nahi — woh ANCHOR hai.
- **CASCADE**: child bina parent bekaar (LayeringRollEntry apne SR ke saath marta).
- **SET_NULL**: optional reference; parent ja sakta, child NULL ho jaata.

Rule: **paisa/history? → PROTECT.**

---

## 4) Ek ROW kaise BANTI hai (backend write-flow = "kaise save hota hai")

```
STEP 1 — worker phone se report
  WorkerReportView (assignment-gate)
   └▶ worker_task_service.report_contributions(task, lines)   [@transaction.atomic]
        └▶ WSC.objects.create(...)  → INSERT production_workerstagecontribution
                                       (reported_quantity saved — IMMUTABLE)

STEP 2 — "Submit & Complete"
   └▶ worker_task_service.complete_worker_task(task)
        ├▶ task.status=COMPLETED; save()           → UPDATE WST
        └▶ har WSC pe expected_rate/earning FREEZE  → UPDATE (visibility only)

STEP 3 — owner Adda settle (paisa YAHAN banta hai)
  AddaSettlementDetailView(action=finalize)
   └▶ adda_settlement_service.finalize_adda_settlement(...)   [@transaction.atomic]
        [strict lock order — canonical: docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md]
        per WSC line:
          ├▶ SWA.objects.create(...)        → INSERT expense_stageworkassignment
          │     (amount frozen; adda_settlement set ⇒ era-B)
          ├▶ WSC.settlement_line = SWA; save() → UPDATE (provenance link)
          └▶ ledger_service.log_credit(assignment=SWA)
                → INSERT expense_workerledgerentry (credit, stage_earning)
        per worker: AddaSettlementItem.objects.create() → INSERT (FROZEN)
        AddaSettlement.status=finalized; save()         → UPDATE
        tracking.log_adda(SETTLEMENT_FINALIZED)          → INSERT addahistory

STEP 4 — cash day (alag event)
   └▶ settlement_service → ledger_service.log_debit(settlement_payment)
        → INSERT expense_workerledgerentry (debit)
```

Balance kabhi STORE nahi hota — HAR BAAR live SQL `SUM(credit) − SUM(debit)`.
Isi liye ledger append-only: galti = ulti REVERSAL row, balance khud sahi.

---

## 5) System design + architecture se connection

- **Service layer** (ADR-0001): har INSERT/UPDATE service se → saving
  predictable, atomic, guarded. Diagram: [04_SERVICE_LAYER.md](04_SERVICE_LAYER.md).
- **Single-writer** (ADR-0002): har truth-table ka EK writer → CI gates
  (4/4b/4c) row-integrity guarantee.
- **Production ≠ Financial truth** (ADR-0005): WSC me paisa save nahi hota
  (expected_* = dikhावा); asli paisa ledger me, settlement par. Do spine isliye.
- **Constraints = DB ki aakhri guard**: `amount>0`, `finalized⇒settled_at`,
  `recovered≤outstanding`, partial-unique active task — app bug ho tab bhi
  Postgres galat row store nahi karega. ([01](01_DJANGO_CONCEPTS.md), [03](03_TRANSACTIONS_AND_LOCKS.md))
- Race-safe saving: [03_TRANSACTIONS_AND_LOCKS.md](03_TRANSACTIONS_AND_LOCKS.md).
- Asli SQL me yeh sab: [09_SQL_BEGINNER_TO_ADVANCED.md](09_SQL_BEGINNER_TO_ADVANCED.md).

## 6) Cheap JOIN-walks
`select_related` (FK joins) + `prefetch_related` (reverse sets) read layer
(payroll_service); indexes on hot pairs (worker+status, adda+settled_at, task).
Perf-baseline tests query-count pin karte hain — N+1 = failing test.

## 7) Deeper
Field-by-field: app GUIDE + khud `config/<app>/models.py` (har model pe
architecture docstring + constraint comments). Domain breakdown:
`SYSTEM_DESIGN.md §5`. Core ER: `GLOSSARY.md`.
