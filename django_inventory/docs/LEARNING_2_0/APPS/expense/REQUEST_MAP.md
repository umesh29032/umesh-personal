# expense — URL → View → Service → Model (REQUEST_MAP)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

| URL name | View | Service | Models written |
|---|---|---|---|
| my-earnings | MyEarningsView | payroll_service (reads) | none |
| payroll-overview | PayrollOverviewView | payroll_service (reads) | none |
| worker-detail | WorkerPayrollDetailView | payroll_service (reads) | none |
| settlement-create | SettlementCreateView | settlement_service.create_settlement | PayrollSettlement(+Item), ledger DEBIT (payment) |
| advance-add | AdvanceCreateView | advance_service / record_advance | WorkerAdvance |
| adda-settlement-list | AddaSettlementListView | adda_settlement_service.settlement_queue (reads) | none |
| adda-settlement-start | AddaSettlementStartView | adda_settlement_service.create_draft | AddaSettlement (draft) |
| adda-settlement-detail | AddaSettlementDetailView | finalize/reverse/discard | ADST(+Item), era-B SWA, ledger credit/debit, WSC.settlement_line, AddaHistory |

RBAC: `_ManagementOnly` mixin on all management screens; `my/` always
self-scoped (worker sees own only). Reads route through payroll_service (it
knows the era rules so templates/views don't).

---
*Canonical depth (don't duplicate — read these):* business view →
[config/expense/README.md](../../../../config/expense/README.md) · file-by-file dev
view → [docs/apps/expense/GUIDE.md](../../../apps/expense/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
