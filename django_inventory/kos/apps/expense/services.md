---
id: app-expense-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Which expense service owns which responsibility, who calls it, what does it write, and how does it fail?"
related: [app-expense, concept-single-writer, concept-service-layer]
---

# expense — service knowledge (`config/expense/services/`)

> 📂 [expense app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> These 10 modules are the ONLY money writers in the system. Every one:
> keyword-only args · docstring side-effect contracts · `@transaction.atomic`
> on writers · loud `ValidationError` refusals that name their fix.

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`expense` app ka kaam: **paisa** — settlement, ledger, advance, payroll. Yahan galti sabse mehngi padti hai.)*

## The sole-writer table (who holds which pen)

| Service | Sole writer of | Called by |
|---|---|---|
| `ledger_service` | `WorkerLedgerEntry` | sibling services ONLY — views NEVER |
| `adda_settlement_service` | `AddaSettlement`+`Item`, era-B SWA, recovery PSIs, recon evidence | settlement detail/start views · `fnf_service` |
| `settlement_service` | `PayrollSettlement`+cash PSIs | SettlementCreateView · `fnf_service` |
| `advance_service` | `WorkerAdvance` | AdvanceCreateView |
| `payroll_service` | `WorkerProfile`, `WorkerPayBasisAudit` (all else = reads) | most views (read), pay-basis/profile views (write) |
| `expense_service` | `FactoryExpense`, `ExpenseTemplate`+audits+generation records | factory-expense views |
| `allocation_service` | era-A SWA (+its credit) — LEGACY lane | (era-A history; naming trap: NOT the pool — that's `production.pool_service`) |
| `fnf_service` | nothing directly — orchestrates the two settlement services | WorkerFnFView |
| `settlement_resolver` | nothing — the ONE quantity rule (`verified ?? reported`) | settlement + (same rule re-implemented in pool per concern) |
| `reconciliation_service` | nothing — reads both truths, reports drift | S1/S5 surfaces, `preview` commands |

## Per-service: responsibility · side effects · failure modes

**`ledger_service.py` (135 lines — read it whole).**
Verbs: `log_credit` · `log_debit` · `reverse_entry` · `worker_balance`.
Fails loud: amount ≤ 0 · double-reversal (app check + DB race-proof).
No atomic of its own — callers own the boundary. [ledger](../../features/ledger.md).

**`adda_settlement_service.py` (681) — THE chokepoint.**
Verbs: `create_draft` · `settlement_queue`/`preview_lines` (guards = finalize's, PA-11-2) · `finalize_adda_settlement` · `reverse_adda_settlement` · `discard_draft` · `record_reconciliation_evidence` · internals `_settleable_lines` (the funnel), `_payable_stage_records`.
Side effects at finalize: locks (5374 → ADST → SRs → WSC `of=self` → profiles sorted → advances) → SWA+CREDIT per line → DEBIT+PSI per recovery → frozen items → FINALIZED + timeline event.
Failure modes: not-draft · empty funnel ("nothing to settle" — usually guards working) · recovery > remaining · S5 recon BLOCK (flag-gated; SA override with reason) · deadlock only if a caller broke lock order.
Full anatomy: [settlement](../../features/settlement.md) · verified trace: [chokepoint doc](../../../docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md).

**`settlement_service.py` — cash only.**
`create_settlement(user, worker, amount_paid, method, …, write_offs=)`.
Refuses: recoveries (V2-2 re-homing) · amount > payable · write-offs by non-SA.
Races handled: global ref advisory lock (SETL numbering) · WorkerProfile row-lock (over-pay). [payroll](../../features/payroll.md) tells both stories.

**`advance_service.py`** — `record_advance`: immutable row, no ledger; refuses monthly workers (no recovery path — the message teaches the reason).

**`payroll_service.py` (~480)** — the READ library (ladder sums, `worker_summary`, `worker_balance_breakdown`, `advance_remaining/outstanding(+bulk)`, `worker_ledger/assignments`, `unsettled_expected`, `is_monthly`) + two writes: `set_pay_basis` (SA, audited, joins 5374) and `update_payout_profile`.
Failure mode to respect: these reads are count-pinned — adding N+1 here fails perf tests.

**`expense_service.py`** — `record_expense` / `void_expense(reason)` / `monthly_totals` / template CRUD + `change_template_amount(reason)` / `generate_monthly_expenses(confirm=)` (idempotent per period; generates THROUGH record_expense — sole writer even internally) / `regenerate_period`.
Law: factory-level always; never per-Adda allocation (ADR-0011).

**`fnf_service.py`** — `fnf_preview` / `fnf_execute(write_off_reason)`: partial settlement via `only_worker=` (chokepoint stays sole writer), then cash, then audited write-offs. SA-only.

**`reconciliation_service.py`** — `reconcile_stage_pay(adda=)` + `summarize`: paid-vs-produced drift detection feeding S1 WARN / S5 BLOCK.

**`settlement_resolver.py`** — `settlement_quantity(contribution)`: verified ?? reported. One rule, one place, for money.

## External APIs / non-DB side effects

None. This app touches PostgreSQL and the tracking timeline
(`tracking.services.log_adda`) — no email, no HTTP, no queues. That's why
its transactions can be clean ([transactions §on_commit](../../concepts/django/transactions.md)).

## Adding/changing a verb here — the checklist

Money-Write STOP rule first (new write path = owner decision) → verb in the
owning service only → docstring side-effects block → refusal messages that
name the fix → tests: golden-identical + refusal pin (+ count pin if a read
surface) → kos-sync: this file + the feature page's Change Impact.

## Required Knowledge (this page)

- [ ] transaction.atomic + lock ordering → [transactions](../../concepts/django/transactions.md) · [locks](../../concepts/postgresql/locks.md)
- [ ] Single-writer discipline + its CI enforcement → [single-writer](../../concepts/architecture/single-writer.md)
- [ ] The resolver rule (verified ?? reported) → [two-truths](../../concepts/architecture/two-truths.md)

## Learning Graph

**Before:** [views.md](views.md) (who calls these) · [models.md](models.md)
(what they write). **After:** the chokepoint doc's verified trace →
[settlement-lifecycle](../../flows/settlement-lifecycle.md) → modify code.
