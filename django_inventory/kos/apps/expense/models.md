---
id: app-expense-models
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Which expense model holds what, who may write it, and what protects it?"
related: [app-expense, feature-ledger, feature-settlement]
---

# expense — model knowledge (`config/expense/models.py`, 873 lines)

> 📂 [expense app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Line numbers = class definitions (drift-tolerant: search the class name).

> 💡 **Samjho aise** — Models = **database ke tables**
>
> Yeh file batati hai is app mein **kaunsi cheezein store hoti hain** aur har cheez ke kaunse column hain. Socho Excel ki sheets ki list — kaunsi sheet, aur usme kaunse columns. Code mein ek `class` = ek table.
>
> *(`expense` app ka kaam: **paisa** — settlement, ledger, advance, payroll. Yahan galti sabse mehngi padti hai.)*

## The money spine

**`WorkerLedgerEntry` (128)** — THE book. Append-only, immutable.
Writers: `ledger_service` ONLY. Readers: everyone (balances derive).
Lifecycle: INSERT → (maybe) one reversal row → forever.
Armor: `CHECK amount>0` · partial-unique one-reversal-per-entry · 5 query-shaped indexes · PROTECT on all FKs.
Deep page: [ledger](../../features/ledger.md).

**`AddaSettlement` (534)** + **`AddaSettlementItem` (616)** — the obligation event + per-worker frozen snapshots.
Writers: `adda_settlement_service` ONLY. Lifecycle: draft → finalized → (reversed | superseded); `supersedes` self-FK chain; frozen totals write-once (never live truth, §11.9.4).
Deep pages: [settlement](../../features/settlement.md) · [settlement-lifecycle](../../flows/settlement-lifecycle.md).

**`StageWorkAssignment` (35)** — the earning line. Two eras: era-A (legacy credit-at-allocation, writer `allocation_service`, readable+reversible) · era-B (settlement-born, writer `adda_settlement_service`, `adda_settlement` FK = the era marker). Rate/amount snapshots frozen at write.

**`WorkerAdvance` (226)** — the loan pool. Writer: `advance_service`. Immutable; NO ledger row on creation; remaining = derived. `CHECK amount>0`. Deep page: [advances](../../features/advances.md).

**`PayrollSettlement` (261)** + **`PayrollSettlementItem` (327)** — the CASH event (`SETL-xxxx`) + recovery/write-off lines (advance ↔ ledger-debit link, `reversed_at` stamp).
Writer: `settlement_service` (cash) / `adda_settlement_service` (recovery PSIs at finalize). Snapshot identity CHECKs: `amount_paid + advance_deducted == payable_settled` family.

## Worker metadata

**`WorkerProfile` (409)** — payout metadata + `pay_basis` (piece-rate|monthly). Writers: `payroll_service` only. Doubles as the **stable per-worker lock row** (payment/settlement serialization — [pg/locks](../../concepts/postgresql/locks.md)).

**`WorkerPayBasisAudit` (502)** — append-only basis-flip audit (old→new, actor, reason). Sole writer: `payroll_service.set_pay_basis`.

## Factory expenses (ADR-0011 lane — never per-Adda, never ledger)

**`FactoryExpense` (450)** — factory-level running cost rows; void-with-reason (soft), monthly aggregates. Writer: `expense_service`.
**`ExpenseTemplate` (729)** + **`ExpenseGenerationRecord` (793)** + **`ExpenseTemplateAmountAudit` (840)** — recurring definitions · per-period idempotency record · audited amount changes (reason mandatory). Writer: `expense_service`.

## Evidence

**`SettlementReconciliationEvidence` (677)** — persisted reconciliation results + the audited super-admin override (`override_reason`, `overridden_by`) for the S5 finalize BLOCK. Writer: `adda_settlement_service.record_reconciliation_evidence`.

## Cross-model laws

- **PROTECT everywhere money points** — a financial row's parents can never vanish.
- **Positive amounts + direction-as-type** on every money row.
- **Nothing here stores a balance/remaining/total that could be derived** — the only stored totals are write-once audit snapshots, clearly named.
- Migrations for this app follow the staged patterns religiously — [migrations](../../concepts/django/migrations.md).

Full column detail: read the model docstrings — they're written as teaching
text (Hinglish why-notes), then [config/expense/README.md](../../../config/expense/README.md)
"What tables are created" for the DB-impact view.

## Required Knowledge (this page)

- [ ] FKs + PROTECT semantics → [from-orm-to-sql](../../concepts/postgresql/from-orm-to-sql.md)
- [ ] Append-only + reversal thinking → [append-only-tables](../../concepts/database-design/append-only-tables.md)
- [ ] Constraints as armor → [constraints](../../concepts/postgresql/constraints.md)

## Learning Graph

**Before:** [money-story](../../project/money-story.md) ·
[ledger feature](../../features/ledger.md). **After:** [services.md](services.md)
(who writes these tables) → the model docstrings themselves (teaching-grade).
