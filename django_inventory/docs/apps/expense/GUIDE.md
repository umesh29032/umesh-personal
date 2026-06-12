# expense app — file-by-file GUIDE (all the money)

> Business view: [config/expense/README.md](../../../config/expense/README.md).

## models.py (single file — money tables ek saath)
WorkerLedgerEntry (append-only kitab) · AddaSettlement(+Item frozen) ·
StageWorkAssignment (earning line, era-marker FK) · PayrollSettlement(+Item
XOR-parent) · WorkerAdvance · WorkerProfile. Har constraint ke paas comment
hai (finalized⇒settled_at, recovered≤outstanding, exactly-one-parent).

## services/ (the money funnels)
| File | Role |
|---|---|
| `adda_settlement_service.py` | ★ finalize/reverse/supersede + queue/preview/discard; lock order §11.5; SOLE writer ADST(+Item)+era-B SWA |
| `ledger_service.py` | ★ SOLE WorkerLedgerEntry writer (log_credit/debit, reverse_entry) |
| `settlement_service.py` | payment-ONLY (V2-2 narrowing; recovery refuse) |
| `allocation_service.py` | era-A legacy (lever-gated) + void (era-B refuse) |
| `payroll_service.py` | ★ READ layer — balances, rollups, unsettled_expected (era-aware) |
| `advance_service.py` | WorkerAdvance writer |
| `reconciliation_service.py` | PAY-4 read checks |
| `_shared.py` | auth gates |

## views.py + urls.py
FILE MAP top of views.py (9 view classes). urls.py header = poora money-URL
map (my/ · payroll/ · settle/ · advances/ · settlements lifecycle).

## templates/expense/
my_earnings · worker_detail · settlement_form (payment) · advance_form ·
worker_profile_form · payroll_overview · adda_settlement_list/detail —
SAB base.html canonicals pe (A-scope); page CSS = sirf extras.

## Dots
```
draft → finalize (settlement svc) → ledger_service credits/debits
     → frozen items → history events;  cash alag: settlement_service → debit
READS hamesha payroll_service se (era rules wahan hain)
```

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
