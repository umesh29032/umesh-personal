---
id: l2-database-guide-stage-work-assignment
type: database-guide
status: active
owner: handwritten
scope: stage_work_assignment (model)
anchors: —
verified: 2026-07-13
---

# DB: StageWorkAssignment (SWA) — the earning line

## TL;DR
What: one worker's earning line for a stage (also the era marker). Why: ties a
ledger credit to a (worker, stage, color/size) with frozen rate/amount. Writes:
adda_settlement_service (era-B) + allocation_service (era-A). Reads: payroll_service
rollups, costing dashboard, ledger.assignment. Breaks if removed: ledger credits
lose provenance + era distinction. ADRs: 0007/0002. File: `config/expense/models.py`.

## Every field (key)
| Field | Type | Meaning |
|---|---|---|
| stage_record | FK→AddaStageRecord | which Adda-stage |
| worker | FK→User | who earned |
| color / size | FK (null) | dimension |
| allocated_quantity | Decimal | pieces |
| earning_rate_snapshot / earning_amount_snapshot | Decimal | FROZEN rate × qty |
| adda_settlement | FK→AddaSettlement (PROTECT, null) | **NULL=era-A, set=era-B** |
| voided_at | datetime (null) | soft-void (correction) |

## Example row
`#42, sr=Cutting#9, utest, Red/S1, qty=60, rate=3.00, amount=180.00, adda_settlement=ADST-0003, voided_at=NULL`

## FK chain
`SWA → AddaStageRecord → Adda`; `SWA → AddaSettlement` (era-B); `WorkerLedgerEntry.assignment → SWA`; `WorkerStageContribution.settlement_line → SWA`.

## How data reaches / leaves
IN: created at settlement finalize (era-B) or allocation (era-A). OUT: never
deleted; correction = `voided_at` set + ledger reverse. era guard reads adda_settlement NULL-ness.

## SQL
```sql
SELECT SUM(earning_amount_snapshot) FROM expense_stageworkassignment
WHERE worker_id=7 AND voided_at IS NULL; -- actual labor (both eras)
```

## Debug in production
Double-pay suspicion → check era guard (adda_settlement_id). Void refused = era-B
(reverse the settlement). Query by stage_record_id.

### Verification Sources
expense/models.py + adda_settlement_service/allocation_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** Tests: test_v2_3_guards.py.
