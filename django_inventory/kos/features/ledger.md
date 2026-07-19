---
id: feature-ledger
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Where does every rupee in this system actually live, and how do I read the money book?"
related: [feature-settlement, feature-advances, feature-payroll, concept-append-only-tables]
---

# The Worker Ledger — the factory's money book

> 📂 [Features](README.md) · [LOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Every rupee the factory owes or has paid a worker exists as exactly one row
in one table: `WorkerLedgerEntry`. Not in balances, not in totals, not in
reports — those are all *derived*. When any money question turns into a
dispute, this book is the answer, and it is designed so the answer is
**provable years later**.

## Mental Model

> The ledger is a **diary, not a whiteboard**. You may only add lines at the
> bottom; you may never erase. A wrong line is corrected by writing a new
> counter-line. Whoever controls the pen controls the truth — so exactly ONE
> service holds the pen.

## 💡 Samjho Aise

Kirana dukaan ki udhaar-kitab. Har lambi entry: *kis ki, kitni, kis wajah
se, kis din*. Mahine ke end mein hisaab = poori kitaab ka jod, kisi ke
yaad ka nahi. Galti ho gayi? Kalam se kaatna mana hai — neeche ulti entry
likho ("₹50 galti se zyada likhe the, wapas"). Aur kitaab mein likhne ka
haq sirf EK munshi ko hai — `ledger_service`.

## Technical Deep Dive

**The row** (`WorkerLedgerEntry`, `config/expense/models.py`):

```
worker · entry_type (credit|debit) · category · amount (ALWAYS > 0)
· entry_date · notes · created_by
· source FKs: assignment (earning) | advance (recovery) | settlement (payment)
· reverses (self-FK → the corrected entry)
```

**Direction lives in `entry_type`, never in the sign** — so `SUM(amount)`
aggregates stay clean and the DB CHECK (`amount > 0`, live in PostgreSQL as
`expense_ledgerentry_amount_positive`) can hold the line.

**Live categories** (money vocabulary):

| Category | Direction | Written when |
|---|---|---|
| `stage_earning` | CREDIT | settlement finalize — per contribution line |
| `advance_recovery` | DEBIT | settlement finalize — owner-chosen per advance |
| `settlement_payment` | DEBIT | cash payment (`PayrollSettlement`) |
| `reversal` | opposite of original | correction of any entry |
| `adjustment` / `deduction` | as needed | audited manual corrections |
| `advance` / `payment` | — | **legacy labels** — advances no longer post to the ledger |

**The four writer functions** (`ledger_service` — the SOLE pen, ADR-0002):
`log_credit` · `log_debit` · `reverse_entry` (refuses double-reversal at app
level; the DB partial-unique index `uniq_one_reversal_per_entry` is the
race-proof backstop — note for PG explorers: a conditional `UniqueConstraint`
lives in `pg_indexes`, NOT `pg_constraint`) · `worker_balance` (the only
read that matters: `SUM(credit) − SUM(debit)`, real SQL + index story in
[transactions §6](../concepts/django/transactions.md#6-how-this-project-uses-it)).

**Provenance law:** every credit points at its earning line (SWA), every
debit at its advance or payment, every earning line at its `ADST-xxxx`
settlement. Follow the FKs and any balance explains itself.

## Debugging Guide

| Symptom | Do this |
|---|---|
| Balance looks wrong | `ledger_service.worker_balance(w)` in shell; then read that worker's entries newest-first — find the entry that surprises you, follow its source FK |
| Entry has no source FK | Only legal for reversal/adjustment; anything else = alarm-bell, check which code path wrote it (should be impossible) |
| Need to "fix" an amount | You don't edit — `reverse_entry` + write the correct one; both stay visible forever |
| Totals differ between two screens | Both must derive from the ledger; the one doing its own math is the bug (grep for stored totals) |

## Change Impact

Touch the ledger schema/writers → review: settlement finalize + reverse ·
payroll cash flow · `worker_balance` + `worker_balance_breakdown` consumers
(My Earnings, payroll overview, worker detail) · reconciliation identities ·
goldens ₹344.25/₹801/₹633 · tests `test_adda_settlement_service.py`,
`test_v2_3_guards.py`.

## AI Implementation Pitfalls

- ❌ `WorkerLedgerEntry.objects.create(...)` anywhere outside `ledger_service`
  — including tests and data migrations. The single-writer rule has no exceptions.
- ❌ Negative amounts to express direction — CHECK will refuse; direction = `entry_type`.
- ❌ Storing a balance/total column "for performance" — derived-live is the law;
  the registered seam is a snapshot table, owner-gated.
- ❌ UPDATE/DELETE on any ledger row — append-only, corrections are rows.
- ✅ Always verify: after ledger-adjacent changes, `worker_balance` recompute
  matches every UI figure + goldens byte-identical.

## Interview Notes

*Interview Signal: 🟠 Senior — audit-proof money store design.*

**Q. "Design an audit-proof money store."**
- *Short:* Append-only event log; derived balances; single writer; DB constraints as backstop.
- *Senior:* Direction-as-type keeps aggregates trivial; provenance FKs make every figure self-explaining; corrections as compensating events preserve history; partial-unique constraints make idempotency race-proof at the DB, not just the app.
- *Project example:* This table — 1 writer service, 5 indexes, CHECK + partial-unique live in PG, every row traceable to ADST references.
- *Follow-ups:* "Ledger grows forever — reads?" (indexed aggregates now; snapshot-table seam registered) · "GDPR/deletion?" (PROTECT chains — anonymize the user, never the money).

## 🧠 Remember This

Diary, whiteboard nahi. Ek munshi (ledger_service), ek kalam, koi rubber
nahi. Amount hamesha positive, disha type mein. Har entry apna saboot
(source FK) saath rakhti hai. Balance kitaab ka JOD hai, kitaab ka column nahi.

## 30-Second Revision

- One table = all worker money; balances always derived
- 4 writers only: log_credit · log_debit · reverse_entry · (read) worker_balance
- amount > 0 CHECK · one-reversal partial-unique (lives in pg_indexes!)
- credit→SWA, debit→advance/payment, everything→ADST reference
- Legacy categories `advance`/`payment` = old era labels, don't reuse

## Implementation References

- ADR: [0002 single-writer](../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)
- Pattern teaching: [append-only tables](../concepts/database-design/append-only-tables.md) · [single-writer](../concepts/architecture/single-writer.md)
- The writers' caller: [settlement](settlement.md) · [payroll](payroll.md)

## Code References
- `config/expense/services/ledger_service.py` (entire file — 135 lines, read it) · model in `config/expense/models.py`

## Related Concepts

[append-only-tables](../concepts/database-design/append-only-tables.md) ·
[single-writer](../concepts/architecture/single-writer.md) ·
[pg/constraints](../concepts/postgresql/constraints.md) ·
[transactions](../concepts/django/transactions.md)
