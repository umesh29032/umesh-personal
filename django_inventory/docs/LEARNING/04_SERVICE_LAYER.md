# Service layer — the architecture's load-bearing wall

## The pattern
View = parse request + permission gate + call ONE service + redirect.
Service = `config/<app>/services/…` — ALL multi-row writes, atomic, explicit.
Model = data + tiny read helpers. NO signals (ADR-0001).

## Single-writer discipline (ADR-0002) — and why CI enforces it
| Truth table | Sole writer | CI gate |
|---|---|---|
| WorkerStageTask/Contribution | worker_task_service | [4/4] |
| AddaSettlement(+Item) | adda_settlement_service | [4b/4] |
| StageWorkAssignment | allocation_service + adda_settlement_service | [4c/4] |
| WorkerLedgerEntry | ledger_service | rule 5 |
| *History | history_service | rule 5 |

Grep-based gates in `scripts/check.sh` — discipline as a failing build, not
a code-review hope. Ek darwaza per table matlab: har guard (double-credit,
recovery≤remaining, era checks) us darwaze pe baith ke SAB ko cover karta hai.

## Chokepoint = convergence point
C-TM lock: manual report ho ya future barcode scan — production truth WSC
mein SIRF worker_task_service se ghusta hai. Naya capture path? Usi function
ko call karo. Bypass = settlement unverifiable numbers pe paise dega.

## What breaks if a view writes directly
Atomicity gone (partial writes on error), guards skipped, history events
missing, gates red. Isi liye rule 4 absolute hai.

## Service connection map (kaun kisko call karta hai)

```
                         VIEWS (har app ki)
                              │  (sirf parse + gate + delegate)
      ┌───────────────────────┼─────────────────────────────┐
      ▼                       ▼                             ▼
 PRODUCTION SIDE         EXPENSE SIDE                  FOUNDATION
 ───────────────         ────────────                  ──────────
 adda_service ──┐        payroll_service (READS only)  permission_service
 flow_service   │              ▲    reads ledger/SWA/WSC   (har view ka gate)
 product/size   │              │                           auth/user_service
 access_service │        adda_settlement_service ◀── settlement queue/detail UI
      │         │         │ │ │ writes: ADST(+Item), era-B SWA
      ▼         │         │ │ └▶ ledger_service ──▶ WorkerLedgerEntry
 stage services │         │ └──▶ history_service (SETTLEMENT_* events)
 (layering/cut/ │         │
  pattern/bcode)│        settlement_service (payment-only) ─▶ ledger_service
      │         │        advance_service ─▶ WorkerAdvance
      ▼         ▼        allocation_service (LEVER-only era-A) ─▶ ledger_service
 worker_task_service ◀───┘ reads WSC (settle qty); writes WSC.settlement_line
   │ writes WST/WSC        stamp via the SAME chokepoint family
   │ freeze rates ◀── cost_service.role_rate_for (grouped-member guard C-1)
   ▼
 cost_service ─▶ AddaStageRecord.processing_cost (standard cost freeze)
 _shared.reopen_stage_record ─▶ void_allocation (era-A only) + V2-3 block
 roll_service (raw_materials) ─▶ ClothRoll/leftovers; consume_leftover sole writer
 history_service (tracking)  ◀── EVERY service above logs its timeline events
 barcode_service (tracking)  ─▶ BarcodeBatch ranges (identity primitive)

 ARROWS' LAW: production → expense allowed (one way); expense NEVER imports
 production at module level (string FKs); tracking imports NEITHER (primitive).
 core + accounts import NO domain app (CI: foundation-purity gate).
```

Padhne ka tareeka: koi bhi paisa-flow neeche ledger_service pe hi khatam hota
hai; koi bhi kaam-flow worker_task_service se hi guzarta hai; har event ka
zikr history_service karta hai. Yeh teen "funnels" hi poora system hai.
