---
id: l2-data-flows-adda-settlement-flow
type: data-flow
status: active
owner: handwritten
scope: adda_settlement_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Adda Settlement (finalize)

## TL;DR
Production truth (WSC) → finalize → money rows (SWA + ledger + frozen items). One
atomic transaction, strict lock order. Reads WSC; writes the money spine.

```
INPUT VALIDATION SERVICE → DB WRITE
───── ────────── ──────────────────
variance{wid:{...}} + → management gate → adda_settlement_service.finalize_adda_settlement
recoveries{advid:amt} payable stages complete [@atomic; strict lock order → see CHOKEPOINTS/adda_settlement_service.md]
(POST on the draft) recovery ≤ remaining per line: SWA INSERT (era-B) + WSC.settlement_line UPDATE
 era skip (A/B already paid) + ledger_service.log_credit (stage_earning)
 per recovery: log_debit + PSI INSERT
 per worker: AddaSettlementItem INSERT (frozen)
 status=finalized; log_adda(SETTLEMENT_FINALIZED)
```
**Reads:** WorkerStageContribution (verified-else-reported), AddaStageRecord,
WorkflowStage rate, WorkerProfile, WorkerAdvance. **Tx boundary:** whole finalize.
**Events:** AddaHistory SETTLEMENT_FINALIZED. **Constraints:** amount>0,
finalized⇒settled_at, recovered≤outstanding, PSI XOR, era guards.

### Debug entry points
`adda_settlement_service.py:finalize`; query `expense_stageworkassignment`
+ `expense_workerledgerentry` by worker; log `adda_settlement.finalize`. Failure:
"Nothing to settle" (all lines already credited); deadlock (lock order broken).
Recovery: `reverse_adda_settlement`.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (finalize installment 4). Full call
chain: [../REQUEST_JOURNEYS/settlement_finalize.md](../REQUEST_JOURNEYS/settlement_finalize.md). ADRs 0005/0007/0009/0002.
