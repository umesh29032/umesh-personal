---
id: apps-expense-guide
type: app-guide
status: active
owner: handwritten
scope: expense
anchors: config/expense/
verified: 2026-07-13
---

# expense app — file-by-file GUIDE (all the money)


> **Accountant READ TIER (2026-08-02).** Read views here use `_FinancialRead`
> (management **+ accountant**); every write view keeps `_ManagementOnly`, and the
> service re-checks the actor independently. An accountant may **record** a factory
> expense but never **void** one. `generate_monthly_expenses(confirm=False)` is a
> pure preview and is allowed; `confirm=True` stays management. Policy:
> [RBAC.md](../../production/RBAC.md) § *The accountant READ TIER*.

> **Date primitive (2026-08-01).** Every "today"/"this month" in this app uses `timezone.localdate()`, never `timezone.now().date()` (which returns a **UTC** date and is one day behind for 5.5h daily under `TIME_ZONE=Asia/Kolkata`). Enforced repo-wide by `core.tests.LocalDateGuardTests`. Background: [UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md](../../UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md). The three money-record dates fixed there were `settlement_date` (`settlement_service.py`), ledger `entry_date` (`allocation_service.py`) and the advance date (`advance_service.py`) — a blank `required=False` date field took the UTC fallback, so a settlement finalised at 01:00 IST on the 1st landed in the previous month. Existing rows were NOT rewritten (append-only).

> Business view: [config/expense/README.md](../../../config/expense/README.md).

> **🛡 Worker Role Certification Phase B (V1.1 item-4) — CLOSED OUT
> 2026-07-12:** B1 code audit + B2 browser verification (previous session)
> found **no bugs**; zero code / test / battery change. Close-out is
> **owner-attested** (that session's artifacts were lost before docs-sync) —
> record of record: [docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md)
> (Phase B section, incl. provenance caveats). Next phase: C — Tracking.

## models.py (single file — money tables ek saath)
WorkerLedgerEntry (append-only kitab) · AddaSettlement(+Item frozen) ·
StageWorkAssignment (earning line, era-marker FK) · PayrollSettlement(+Item
XOR-parent) · WorkerAdvance · WorkerProfile (**R4: `pay_basis`
piece_rate|monthly — worker-level, PDD §27-D4**) · WorkerPayBasisAudit
(**R4 append-only; sole writer `payroll_service.set_pay_basis`**) ·
FactoryExpense (**R5 PDD §21 + 🔒 ADR-0011: factory-level cost, create/void
never edit, amount>0 CHECK, salary⇒worker audit-only link; NEVER allocated
into Adda cost**) · **MEE-A (Phase 16, 2026-07-18, migration 0015
U14-approved): ExpenseTemplate (config; §21 Category reuse; mutable-audited
amount; salary⇄worker biconditional; one-active-salary-per-worker partial
unique; frequency enum monthly-only) + ExpenseGenerationRecord (coverage;
frequency-agnostic period_key; partial-unique current per (template,period);
supersession chain reason-required; OneToOne→FactoryExpense) +
ExpenseTemplateAmountAudit (append-only; reason<>''; old≠new) — writers land
MEE-B post-census-addendum; tests `tests/test_expense_templates.py`**.
Har constraint ke paas comment hai (finalized⇒settled_at,
recovered≤outstanding, exactly-one-parent).

## services/ (the money funnels)
| File | Role |
|---|---|
| `adda_settlement_service.py` | ★ finalize/reverse/supersede + queue/preview/discard; lock order §11.5; SOLE writer ADST(+Item)+era-B SWA. **R4: `_settleable_lines` = 4-tuple (lines, skip_a, skip_b, skip_monthly) — monthly workers structurally excluded at THE funnel; basis read settlement-time (P-1). R7: `finalize(only_worker=)` = pure filter on funnel OUTPUT (guards ran first) — creates the verified-safe mixed settled/unsettled-lines-on-one-SR state (§11.8). OI-C1 (BOD-D, owner Option B 2026-07-18): `settlement_queue()` read-path BATCHED — one bulk SR query + ONE `_settleable_lines` pass over the union, partitioned by adda (helpers/preview/finalize untouched); output proven byte-identical on primary + parity-pinned vs the per-Adda algorithm (`tests/test_queue_batching.py`); 35→6 queries, volume-independent** |
| `ledger_service.py` | ★ SOLE WorkerLedgerEntry writer (log_credit/debit, reverse_entry) |
| `settlement_service.py` | payment-ONLY (V2-2 narrowing; recovery refuse). **R7: + `write_offs=` — audited F&F advance write-off PSI rows (super-admin+reason, NO ledger debit, reversible); sole PSI writer stays here** |
| `fnf_service.py` | **R7 (PDD §20): F&F ORCHESTRATION — writes NOTHING itself; `fnf_preview` (blockers checklist) + `fnf_execute` (per-Adda only_worker settlements → cash+write-off closure → deactivate §31.2); super-admin only (P-4); monthly = zero lines (ADR-0011 pin)** |
| `allocation_service.py` | era-A legacy (lever-gated) + void (era-B refuse) |
| `payroll_service.py` | ★ READ layer — balances, rollups, unsettled_expected (era-aware). **R4: + `is_monthly`/`unsettled_contribution_count` reads AND the write `set_pay_basis` (super-admin, joins lock 5374, confirm-gated when unsettled lines exist, sole WorkerPayBasisAudit writer). RCP-1A F3 2026-07-18: + `update_payout_profile` — THE WorkerProfile payout-details writer (view kabhi form.save() nahi karta); `opening_advance` = displayed-₹ (WP-A informational), ≥0 re-validated + change audit-LOGGED old→new+actor (audit ROW = U14-gated follow-up); pay_basis yahan accept NAHI hota (set_pay_basis hi sole basis writer)** |
| `advance_service.py` | WorkerAdvance writer |
| `management/commands/generate_monthly_expenses.py` | **MEE-E (D4): THIN wrapper over THE service function — preview default, `--confirm` writes, `--actor` = management email; external-cron candidate post-deploy (documented, not wired); purity-pinned** |
| `views.py` +RMX-D | **`MaterialSpendView` (Phase 17, 2026-07-18): /expense/material-spend/ — the read-only WINDOW over the certified RMX-C period reads (consumption PRIMARY + purchases, basis-labelled; honest-NULL banners; GET-only POST→405; _ManagementOnly per the D2 PERMANENT rule; zero FactoryExpense numbers on-page — ADR-0011 sibling links only); template `material_spend.html` (factory-expense canon); nav = Factory-Expenses header link (NO sidebar MenuItem — recorded decision, a360-pin cost); tests `test_material_spend.py` (11: matrices · wall re-proof · content==services · banners/empty · purity)** |
| `views.py` +MEE-C / `forms.py` +MEE-C / `urls.py` +MEE-C | **Surfaces 2026-07-18:** `ExpenseTemplateListView` (status via THE preview path; SA POST actions) · `ExpenseTemplateCreateView` (thin FormView → `create_expense_template`) · `GenerateExpensesView` (GET=preview / POST=confirm + SA regenerate action) · `ExpenseTemplateForm` (fields only) · 3 routes (`expense-template-list/-add`, `expense-generate`) · `_parse_month` promotion (INERT) · templates `expense_template_list/form.html` + `generate_expenses.html` (factory-expense canon) · sidebar MenuItem 'Recurring Expenses' (a360 pin 76→78 conscious: predicate + rule-check per visible item) · tests `test_expense_surfaces.py` (8) |
| `expense_service.py` | **MEE-B 2026-07-18: +Monthly-Expense-Engine section (additive; existing fns byte-untouched; census ADDENDUM 1) — template lifecycle (SA) · `generate_monthly_expenses` (mgmt; preview=pure-read; M-3 skip policy; Q13 auto-stop) · `regenerate_period` (SA+reason, voided-only, CURRENT-amount policy); every fn carries an owner-mandated RESPONSIBILITY banner; tests `test_expense_generation.py` (19)** · prior: | **R5**: sole FactoryExpense writer — `record_expense` (management; salary⇒worker) / `void_expense` (super-admin+reason) / `monthly_totals` (derived live). ADR-0011: zero ledger/settlement/costing imports (test-pinned + gate-4c documented exclusion) |
| `reconciliation_service.py` | PAY-4 read checks |
| `_shared.py` | auth gates |

## views.py + urls.py
FILE MAP top of views.py (9 view classes + R4 `WorkerPayBasisUpdateView` —
parse POST → `set_pay_basis`, service owns every guard). urls.py header =
poora money-URL map (my/ · payroll/ · settle/ · advances/ · settlements
lifecycle · workers/<pk>/pay-basis/ · workers/<pk>/fnf/ (**R7 checklist+execute**) ·
**R5: expenses/ list+month-nav+void,
expenses/add/ mobile form — salary category par worker picker**). R4
presentation: My Earnings + worker_detail + settlement draft (4th labeled
skip panel) monthly-aware — monthly worker ko ₹ expectation NAHI dikhta
(badge dikhta hai). R5 sidebar: Payroll → Factory Expenses (management);
admin dashboard month digest inventory/views/dashboard.py me hai.

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
