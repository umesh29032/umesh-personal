---
id: app-expense-views
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Which expense view/handler do I open, what may it do, and what does it call?"
related: [app-expense, app-expense-urls]
---

# expense — handler knowledge (`config/expense/views.py`, 888 lines)

> 📂 [expense app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> House law first: views PARSE and GATE — **every multi-row/money write
> happens in the service the view calls**; transaction boundaries live on
> the service functions, never here ([service-layer](../../concepts/architecture/service-layer.md)).

> 💡 **Samjho aise** — Views = **reception counter**
>
> Browser se request aati hai to sabse pehle yahin aati hai. View ka kaam sirf teen cheezein hai: **request padho → permission check karo → service ko bhej do**. View khud database mein likhta **nahi** — isiliye yeh files patli hoti hain. Moti view = design ki galti.
>
> *(`expense` app ka kaam: **paisa** — settlement, ledger, advance, payroll. Yahan galti sabse mehngi padti hai.)*

## The shared gate mixins (top of file)

- `_ManagementOnly(UserPassesTestMixin)` — `user_has_role(request.user, MANAGEMENT_ROLES)`; wall #2 for every management view below.
- `_WorkerFromPk` — resolves the `<pk>` worker consistently for worker-scoped pages.
- ALL views are `LoginRequiredMixin`. Super-admin requirements are enforced INSIDE services (pay-basis, F&F write-off, reconciliation override) — the view never trusts itself with that decision.

## Handler groups at a glance

- **READ (7):** MyEarnings · WorkerPayrollDetail · PayrollOverview · FactoryExpenseList · ExpenseTemplateList · MaterialSpend · AddaSettlementList
- **WRITE (8):** SettlementCreate · AdvanceCreate · WorkerProfileEdit · FactoryExpenseCreate · ExpenseTemplateCreate · GenerateExpenses · AddaSettlementStart · **AddaSettlementDetail (the money cockpit)**
- **ADMIN — super-admin enforced in service (2):** WorkerPayBasisUpdate · WorkerFnF
- **DELETE / ASYNC:** none — nothing money-bearing is ever deleted (drafts discard via the cockpit); no async surfaces in this app.

## READ handlers (safe to open, nothing to break)

| View (line) | Template | Reads via | Notes |
|---|---|---|---|
| `MyEarningsView` (75) | `my_earnings.html` | `payroll_service` ladder sums + ledger | worker's own data only |
| `WorkerPayrollDetailView` (98) | `worker_detail.html` | `worker_summary`, `worker_balance_breakdown`, `worker_ledger` | `can_view_worker` gate: mgmt OR self |
| `PayrollOverviewView` (130) | `payroll_overview.html` | `payroll_totals`, `outstanding_advances_bulk` | bulk aggregates — count-pinned; don't add per-row queries |
| `FactoryExpenseListView` (419) | `factory_expense_list.html` | `expense_service.monthly_totals` | shows void action (SA) |
| `ExpenseTemplateListView` (511) | `expense_template_list.html` | template QS | amount-change needs reason |
| `MaterialSpendView` (659) | `material_spend.html` | read-only report | GET-only by design |
| `AddaSettlementListView` (682) | `adda_settlement_list.html` | `settlement_queue` | **PA-11-2: preview = money-write surface — same guards as finalize** |

## WRITE + ADMIN handlers (the ones that matter)

**`SettlementCreateView` (238)** — POST → `settlement_service.create_settlement(user, worker, amount_paid, method, …)`
Inputs: amount, method, date, notes (+ SA-only write-offs via F&F path, not here). Refuses: recoveries (V2-2), amount > payable.
Side effects: `PayrollSettlement` + PSI + ledger DEBIT. Boundary: `@transaction.atomic` on the SERVICE. Template `settlement_form.html`.
Debug: [money-looks-wrong](../../debugging/money-looks-wrong.md) · Interview: [payroll Q](../../features/payroll.md#interview-notes) (the two race stories).

**`AdvanceCreateView` (218)** — FormView → `advance_service.record_advance`.
Side effects: 1 immutable `WorkerAdvance`, NO ledger. Refusal: monthly workers (message explains why).

**`WorkerPayBasisUpdateView` (337)** — POST-only `View` → `payroll_service.set_pay_basis(worker, new_basis, actor, confirmed=)`.
SA-only (service). Side effects: profile update + `WorkerPayBasisAudit`. Joins advisory 5374 — cannot race finalize.

**`WorkerFnFView` (360)** — GET preview (`fnf_service.fnf_preview`) / POST execute (`fnf_execute(worker, user, write_off_reason)`).
Side effects: partial settlement (`only_worker=` through the chokepoint — guards untouched) + cash + optional audited write-off (NO debit).
Template `worker_fnf.html`.

**`AddaSettlementStartView` (698)** — POST-only → `adda_settlement_service.create_draft`. Side effect: 1 DRAFT row, zero money.

**`AddaSettlementDetailView` (726)** — the cockpit. GET: `preview_lines` + items + reconciliation context. POST dispatches on `action`:
`finalize` → `finalize_adda_settlement(settlement, user, variance=, recoveries=, reconciliation_override=)` — THE money write · `reverse` / `supersede` → `reverse_adda_settlement` · `discard` → `discard_draft`.
Inputs parsed here: per-worker variance counts, per-advance recovery amounts (strings → validated in service; PA-07-2 pattern).
Everything else — locks, funnel, order — belongs to the service:
[settlement §Backend](../../features/settlement.md) is the walkthrough.

**`FactoryExpenseCreateView` (462)** / **`ExpenseTemplateCreateView` (565)** / **`GenerateExpensesView` (602)** — thin FormView/TemplateView wrappers over `expense_service` verbs (`record_expense`, `create_expense_template`, `generate_monthly_expenses(confirm=)`); generation is idempotent per period via `ExpenseGenerationRecord`.

**`WorkerProfileEditView` (295)** — FormView → `update_payout_profile`. Profile metadata only; pay-basis has its OWN audited handler above.

## Handler rules of thumb (this app)

1. New action on a page → new `action=` branch calling an EXISTING service
   verb, or a new verb IN the service — never logic here.
2. Anything touching money amounts: parse to `Decimal(str(x))` at this
   boundary or pass raw strings to services that do (they do).
3. `is_super_admin` context vars are for TEMPLATE display only — the
   service re-checks (wall #3).
4. Adding a URL? It needs: urls.py row + sidebar rule + this file's table
   + [urls.md](urls.md) row (kos-sync).

## Required Knowledge (this page)

- [ ] Django CBVs + mixins · FormView GET/POST cycle → [transactions](../../concepts/django/transactions.md) §boundary-placement
- [ ] Why views never write money → [service-layer](../../concepts/architecture/service-layer.md)
- [ ] The four walls → [rbac-access](../../features/rbac-access.md)

## Learning Graph

**Before:** [urls.md](urls.md) (each handler's URL story). **After:**
[services.md](services.md) — the verbs these handlers call → then open
`config/expense/views.py` with this page beside it.
