# DB: WorkerStageContribution (WSC) — production truth

## TL;DR
What: dimensional output line (color/size/qty) under a task. Why: the granular
"what was made" that settlement values. Writes: worker_task_service ONLY. Reads:
settlement (verified-else-reported), My Earnings expected strip, costing. Breaks
if removed: settlement can't compute pay; G3 has no base. ADRs: 0005. File: `worker_task.py`.

## Every field (key)
task FK→WST, color FK→ClothColor (null), size FK→ProductSize (null),
**reported_quantity** Decimal (IMMUTABLE), **verified_quantity** Decimal (null, mgmt fix),
**expected_rate/expected_earning** Decimal (frozen at complete = VISIBILITY, not money),
**settlement_line** FK→SWA (null, provenance), bundle_item FK (null).

## Example row
`task=…, Red, S1, reported=60, verified=NULL, expected_rate=3.00, expected_earning=180.00, settlement_line=SWA#42`

## FK chain
`WSC → WST → AddaStageRecord → Adda`; `WSC.settlement_line → SWA → AddaSettlement`.

## How data reaches / leaves
IN: report_contributions (reported). complete → expected_* frozen. set_verified_quantity
→ verified (reported untouched). finalize → settlement_line stamped. OUT: never deleted.

## SQL
```sql
SELECT COALESCE(verified_quantity,reported_quantity) AS settle_qty, expected_earning
FROM production_workerstagecontribution WHERE task_id=<id>;
```

## Debug in production
Settlement amount wrong → verified vs reported. expected_* as money = mistake
(visibility only). Query by task_id.

### Verification Sources
worker_task.py (WSC) + worker_task_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** Tests: test_worker_task.py, test_v2_3_guards.py.
