# Database relationships — how the rows actually connect

Full ER sketch: [PROJECT_KNOWLEDGE_MAP §6](../PROJECT_KNOWLEDGE_MAP.md).
Yahan the three spines, row-level:

## Spine 1 — material
ClothRoll.adda (FK, PROTECT-ish semantics via guards): ek roll EK hi Adda ka.
Leftover row = (roll, source_adda, weight) — consumption ka exact fact.
Example: `CR-000142 → 3-PATTI-001, 25.40kg attach, leftover 3.10kg`
⇒ consumed = 22.30kg. G1 isi se cloth cost nikalega — retroactively.

## Spine 2 — work (production truth)
Adda → AddaStageRecord (one per WorkflowStage) → WorkerStageTask (per worker)
→ WorkerStageContribution (per color/size line).
Row: `WSC(task=utest@cutting, color=Red, size=S1, reported=60, verified=NULL,
expected_rate=3.00 frozen, settlement_line=SWA#42)`.

## Spine 3 — money (financial truth)
AddaSettlement → SWA earning lines → WorkerLedgerEntry credits;
PSI recovery rows → ledger debits; frozen AddaSettlementItem per worker.
The provenance loop: WSC.settlement_line → SWA.adda_settlement → ADST;
ledger.assignment → SWA. Har paise ka raasta dono taraf walk hota hai.

## Why JOIN-walks stay cheap
select_related (FK joins) + prefetch_related (reverse sets) at the read
layer (payroll_service); indexes on the hot pairs (worker+status,
adda+settled_at, task). Perf baselines pin query counts in tests —
N+1 regression = failing test, silent nahi.
