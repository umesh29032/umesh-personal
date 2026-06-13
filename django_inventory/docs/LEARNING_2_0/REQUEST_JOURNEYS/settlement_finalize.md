# Journey: Settlement Finalize (the money write) — TEMPLATE

> The richest journey. Copy this 16-section shape for every other journey.

**1. URL** — `/expense/settlements/<reference>/` POST `action=finalize` ·
name `expense:adda-settlement-detail` (`config/expense/urls.py`).

**2. View/Handler** — `config/expense/views.py` → `AddaSettlementDetailView.post`
→ helper `_parse_finalize_inputs`. Mixin `_ManagementOnly`.

**3. Forms** — none (dynamic POST keys parsed in the view: `var_<wid>_<field>`
for variance, `recover_<advid>` for recovery — rows are per-worker/per-advance).

**4. Services called** — `expense/services/adda_settlement_service.py:finalize_adda_settlement`
→ which calls `ledger_service.log_credit/log_debit` and `tracking.log_adda`.

**5. Models READ** — WorkerStageContribution (settle qty = `verified_quantity`
else `reported_quantity`), AddaStageRecord (payable stages), WorkflowStage (rate),
WorkerProfile, WorkerAdvance, existing StageWorkAssignment (era guard).

**6. Models WRITTEN** — StageWorkAssignment (INSERT, era-B earning line) ·
WorkerStageContribution.settlement_line (UPDATE, provenance) · WorkerLedgerEntry
(INSERT credit stage_earning; INSERT debit advance_recovery) · PayrollSettlementItem
(INSERT recovery rows) · AddaSettlementItem (INSERT, frozen) · AddaSettlement
(UPDATE status=finalized) · AddaHistory (INSERT SETTLEMENT_FINALIZED).

**7. Transaction boundaries** — entire `finalize_adda_settlement` = ONE
`@transaction.atomic`. Lock order: canonical in [../CHOKEPOINTS/adda_settlement_service.md](../CHOKEPOINTS/adda_settlement_service.md) (advisory→ADST→SR→profiles→advances)
row (select_for_update) → AddaStageRecord rows → WorkerProfile → WorkerAdvance.

**8. Permissions/RBAC** — `_ManagementOnly` (view) + `_ensure_management` (service);
URL also sidebar-rule gated.

**9. ADRs** — 0005 (truth split), 0002 (single writer), 0007 (eras+lever), 0009 (labor sourcing).

**10. Database tables affected** — expense_stageworkassignment, expense_workerledgerentry,
expense_addasettlement, expense_addasettlementitem, expense_payrollsettlementitem,
production_workerstagecontribution (settlement_line), tracking_addahistory.

**11. Example request payload** (POST form-encoded):
```
action=finalize
var_42_packed=73
var_42_missing=2
recover_7=15.00 # advance #7, recover ₹15
csrfmiddlewaretoken=…
```

**12. Example DB rows BEFORE → AFTER**
```
BEFORE
 AddaSettlement(ADST-0003, status=draft, expected_total=0)
 WorkerStageContribution(#88, reported=75, verified=NULL, settlement_line=NULL)
 WorkerLedgerEntry: (none for this settlement)

AFTER
 AddaSettlement(ADST-0003, status=finalized, settled_at=now, expected_total=225.00)
 StageWorkAssignment(#42, worker=utest, amount=225.00, adda_settlement=ADST-0003)
 WorkerStageContribution(#88, … settlement_line=#42) ← provenance linked
 WorkerLedgerEntry(#10, utest, credit, stage_earning, 225.00, assignment=#42)
 AddaSettlementItem(ADST-0003, utest, expected=225, recovered=15, final_payable=210) [frozen]
 WorkerLedgerEntry(#11, utest, debit, advance_recovery, 15.00, advance=#7)
 AddaHistory(3-PATTI-001, SETTLEMENT_FINALIZED, {reference:ADST-0003})
```

**13. Common debugging points** — "Nothing to settle" → all lines already
era-A/era-B credited (check the skip classes in `preview_lines`). Wrong amount →
check `verified_quantity` vs `reported_quantity` on the WSC. Deadlock → someone
broke the lock order. Balance off → it's a live SUM, look for a missing reversal.

**14. Common mistakes** — finalizing before verifying quantities (use the
review page first); expecting recovery on the payment screen (it's here, not
there); reading `WSC.expected_*` as the paid amount (it's visibility only).

**15. Why this architecture** — settlement ≠ payment (Model A): earning+recovery
is an Adda-scoped, reviewable, reversible APPROVAL; cash is a separate worker-scoped
event. One atomic finalize with frozen snapshots = auditable forever.

**16. What breaks if bypassed** — writing the ledger/SWA directly = double-pay,
no provenance, unauditable money, deadlocks (lock order lost). The gate [4b/4c]
makes this impossible.

Chokepoint: [../CHOKEPOINTS/adda_settlement_service.md](../CHOKEPOINTS/adda_settlement_service.md).
