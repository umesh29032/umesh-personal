---
id: r5-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R5 EXECUTION PLAN — FactoryExpense module (PDD §21)

> Phase R5 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> implementing 🔒 PDD §21 (design — minimal): *`FactoryExpense(category
> [rent|electricity|salary|other], amount>0, expense_date, notes, entered_by)`
> in the expense app; admin CRUD (create/void, no edit — append-only posture);
> monthly dashboard sum. Monthly salaries recorded here (links to §17 MONTHLY /
> R4). NOT a general ledger — YAGNI.*
> STATUS: **✅ ACCEPTED by owner 2026-07-05 (uncommitted,
> checkpoint policy).** Owner approved P-1 (worker FK: required for salary,
> audit-only, never ledger/settlement) / P-2 (management create, super-admin
> void + mandatory reason, no edit path) + BUSINESS CLARIFICATION locked as
> **[ADR-0011](adr/0011-monthly-salary-factory-level.md)**: monthly workers
> stay full production workers; salary = factory-level FactoryExpense; NO
> per-Adda allocation until an owner-approved allocation phase (which must
> never rewrite history). ADR indexed + pointed from CLAUDE.md, model
> docstring, service docstring, expense README/GUIDE.
> Results: gate PASS **767** (+17 test_r5_factory_expense; perf baseline
> MANAGEMENT 20→21 documented — the one management-only digest aggregate;
> gate-4c expense_service.py exclusion added with why-correct/why-safe/
> revisit, mirroring the pool_service precedent) · golden ₹225 byte-identical ·
> ADR-0011 pinned by test (record+void salary ⇒ ZERO ledger rows) · LIVE
> browser E2E: rent ₹12000 + salary ₹9000 (worker picker appears only on
> salary, FancySelect/fancy-date, dev.monthly named — R4 loop closed) +
> electricity ₹1500 (as DEV-Manager via service); super-admin void with
> reason (totals ₹22500→₹10500, struck-through row shows who+why); manager
> sees list but ZERO void controls; worker: no sidebar item, no dashboard
> panel, direct URL 403; dashboard digest live at 360/desktop; list + form +
> dashboard 360px no-overflow.
> Anchors verified against code 2026-07-05 (post-R4 acceptance).

## 1) Current behavior vs target

| | Today | R5 target (§21) |
|---|---|---|
| Factory running costs (rent, electricity, salaries) | nowhere in the system | `FactoryExpense` rows, append-only (create/void, never edit) |
| Monthly workers' salary | R4 excluded them from settlement; salary itself unrecorded | recorded HERE as `category=salary` rows — closes the R4 loop |
| Admin visibility | none | "Expenses (this month)" panel on the admin dashboard (total + per-category) + a filterable list page |
| Ledger | — | **UNTOUCHED.** FactoryExpense never writes WorkerLedgerEntry; it is a cost record, not a balance (PDD: "NOT a general ledger") |

## 2) Design

### 2a. Model (migration expense **0013**)
`FactoryExpense(TimeStampedModel)` — PDD §21 literal:
- `category` TextChoices **rent | electricity | salary | other** (the PDD-locked
  set; extending it later = PDD revision, not a code tweak)
- `amount` Decimal(12,2) + **DB CheckConstraint amount > 0**
- `expense_date` DateField (the month bucket) · `notes` · `entered_by` FK PROTECT
- append-only posture: `voided_at` / `voided_by` / `void_reason` (mirror of the
  SWA soft-void pattern — a mistake is voided with a reason, never edited/deleted)
- (P-1) optional `worker` FK PROTECT, service-required when `category=salary`

### 2b. Service — new `expense_service.py` (sole FactoryExpense writer, rule 4/5)
- `record_expense(*, category, amount, expense_date, notes, actor, worker=None)`
  — management gate; validates amount>0, category, salary⇒worker (P-1).
- `void_expense(expense, *, actor, reason)` — (P-2) super-admin only, mandatory
  reason; stamps the void trio; refuses double-void. No edit function EXISTS.
- `monthly_totals(year, month)` — Σ non-voided by category + grand total
  (derived live, never stored).

### 2c. UI (management, mobile-first per rule 11)
- **List** `/expense/expenses/` — month filter (default current), per-category
  totals + rows; void button (super-admin, reason prompt); voided rows shown
  struck-through with reason (nothing disappears — owner data principle).
- **Entry** `/expense/expenses/add/` — small phone-friendly form (category
  FancySelect, amount, fancy-date, notes, worker picker visible only for
  salary). Form-shell pattern.
- **Sidebar**: `MenuItem('Factory Expenses', …, match=('expense/expenses',))`
  in the existing Payroll section (permission_service MENU — auto URL-gated by
  the sidebar middleware).
- **Admin dashboard** (`inventory/views/dashboard.py`, `is_admin_view` +
  management-gated, same read-only ctx pattern as the R1 broadcast): "Expenses
  (this month)" panel — grand total + category chips. PDD §23: panels arrive
  with their modules.
- **Django admin**: `_MoneyReadOnlyAdmin` (inspection only — writes via service).

### What deliberately does NOT happen
- No ledger rows, no worker-balance effect, no P&L (G6→…→P&L phase), no
  recurring/auto-generated expenses, no attachments, no approval workflow —
  all YAGNI per PDD §21.
- R4's monthly-exclusion machinery untouched; a salary expense row is
  informational cost truth, not a payment event.

## 3) Files

| File | Change |
|---|---|
| `config/expense/models.py` + migration **0013** | FactoryExpense (+constraint) |
| `config/expense/services/expense_service.py` (new) + services facade | record/void/monthly_totals |
| `config/expense/views.py` + `urls.py` | list + create + void POST views |
| `config/expense/templates/expense/factory_expense_list.html` + `_form.html` (new) | UI |
| `config/accounts/services/permission_service.py` | Payroll-section MenuItem |
| `config/inventory/views/dashboard.py` + admin dashboard template | month panel |
| `config/expense/admin.py` | read-only admin |
| `config/expense/tests/test_r5_factory_expense.py` (new) | §5 |

## 4) Owner confirmations ❓

| ID | Question | Recommendation |
|---|---|---|
| P-1 | **Salary rows: optional `worker` FK?** PDD §21's minimal spec has no worker column, but §17/R4 route monthly salaries here — without the FK, "whose salary was this?" lives only in free-text notes, against your audit posture. | **YES** — nullable FK, service-enforced required when `category=salary`, hidden for other categories. Not a ledger link (no balance effect). |
| P-2 | Who creates / who voids? | create = **management** (same gate as Record Advance); void = **super-admin + mandatory reason** (corrections posture, same spirit as D3/R4). |

## 5) Tests
1. Constraint: amount ≤ 0 refused (service ValidationError + DB IntegrityError).
2. Salary⇒worker required; other categories reject a worker (or ignore — pinned per P-1 answer).
3. Void: super-admin+reason only (manager PermissionDenied, empty reason refused);
   voided excluded from `monthly_totals`; double-void refused; NO edit path exists.
4. `monthly_totals`: rows across months/categories bucket correctly by `expense_date`.
5. Views: worker blocked from list/create/void; manager can create, cannot void.
6. Dashboard panel: present for management, absent for worker.
7. **Ledger untouched proof**: recording+voiding expenses changes zero
   WorkerLedgerEntry rows; golden ₹225 byte-identical; full gate.

## 6) Browser E2E (test-data authorization; DEV data retained per owner)
DEV-marked rows: rent ₹X, electricity ₹Y + **salary row for dev.monthly@test.local**
(closing the R4 story live: excluded from settlement → paid via Expenses).
Entry form at 360 (FancySelect category, fancy-date, worker picker appears on
salary); list month-filter + totals; void with reason as super-admin (struck-through
row); manager void refused; dashboard panel at 360 + desktop; worker sees none of it.

## 7) Risks
| Risk | Mitigation |
|---|---|
| Category set too small later | PDD-locked; extending = PDD revision (documented in model comment) |
| Expense creep toward "general ledger" | service has NO ledger imports; test 5-7 pins zero ledger interaction |
| Sidebar item leaks to workers | section+item predicates = MANAGEMENT_ROLES; middleware blocks the URL when hidden |
| Salary double-count vs settlement | impossible — R4 already excludes monthly from settlement; salary row has no payment semantics |

## 8) Rollback
Additive migration ⇒ `migrate expense 0012` + `git revert`. No flags.

## 9) Acceptance criteria
- [ ] Create rent/electricity/salary expenses (salary tied to the DEV monthly
      worker), browser-verified at 360 + desktop.
- [ ] Void = super-admin + reason; voided row visible-but-excluded from totals.
- [ ] Admin dashboard shows this-month total + categories; worker sees nothing.
- [ ] Zero ledger rows created; golden intact; `bash scripts/check.sh` PASS.
- [ ] Docs synced (expense README/GUIDE, dashboard GUIDE row, roadmap, memory).

## 10) Order (estimated)
1. Model + migration + service + constraint/service tests — ~1 h
2. Views + templates + sidebar + URL + permission tests — ~1.5 h
3. Dashboard panel + tests — ~30 min
4. Browser E2E + docs — ~1 h
Total ≈ half a day. Uncommitted (checkpoint policy).
