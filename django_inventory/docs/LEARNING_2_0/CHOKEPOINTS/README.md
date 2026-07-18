---
id: l2-chokepoints-readme
type: entry-index
status: active
owner: handwritten
scope: documentation system
anchors: —
verified: 2026-07-13
---

# CHOKEPOINTS — the single-writer services where integrity lives

> A chokepoint = the ONE service allowed to write a truth table. Bypass any of
> these and the system can be silently corrupted. CI gates enforce them
> (`scripts/check.sh` 4/4b/4c). Read these five to understand WHY this ERP
> can't be made to lie. Each file: why exists · owns · writes · who calls ·
> invariant protected · what breaks if bypassed.

1. [worker_task_service](worker_task_service.md) — production truth (WST/WSC)
2. [adda_settlement_service](adda_settlement_service.md) — the money event
3. [allocation_service](allocation_service.md) — legacy earning path (lever)
4. [ledger_and_payment](ledger_and_payment.md) — ledger_service + settlement_service
5. [cost_service](cost_service.md) — standard-cost freeze + role rates

Service-connection diagram: [../../LEARNING/04_SERVICE_LAYER.md](../../LEARNING/04_SERVICE_LAYER.md).

> EXPANSION STANDARD v2 (owner 2026-06-12, next pass): each chokepoint file
> also gets real execution example + before/after DB state + step-by-step
> walkthrough + common mistakes. Current files have why/owns/writes/invariant/
> breaks; the "why" companion is [../ARCHITECTURE_EXPLAINED/](../ARCHITECTURE_EXPLAINED/README.md).
