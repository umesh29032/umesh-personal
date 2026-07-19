---
id: debug-money-looks-wrong
type: debugging
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "A worker's balance / a settlement total / a payroll number looks wrong — what do I check, in what order?"
related: [feature-ledger, feature-settlement, feature-payroll]
---

# Playbook: "Yeh paisa galat kyun dikh raha hai?"

> 📂 [Debugging](README.md) · [KOS home](../README.md) — *symptom se shuru karo, code se nahi.*

## Symptoms this playbook covers

- Worker says their balance/Expected/Earned/Paid is wrong
- A settlement total doesn't match what the owner approved
- Two screens show different amounts for the same thing
- An advance's remaining looks off after a recovery or reversal

## First Five Minutes — how a senior starts *(the thought process)*

1. **Never debug from the screen.** Screens derive; the ledger is truth.
   Recompute first: `ledger_service.worker_balance(worker)` in shell.
   Screen ≠ recompute → display bug (find which surface does its own math).
   Screen == recompute → the DATA needs explaining, keep going.
2. **Get the itemized derivation** — one call, not manual math:
   `payroll_service.worker_balance_breakdown(worker)` → gross, reversed,
   debits-by-category, payable. *This call exists exactly for this moment.*
3. **Ask "which of the three numbers is wrong?"** Expected (unsettled work)
   / Earned (credits) / Paid (debits) never overlap — the wrong LADDER RUNG
   names the subsystem: Expected → production truth; Earned → settlement;
   Paid → cash event.
4. **Check era + reversals before suspecting bugs** — a reversal pair nets
   to zero but BOTH rows show in listings; era-A rows (old world) are
   legitimate history, not duplicates.
5. Only NOW open code — and you already know which service.

## Decision tree

```
Recompute balance == screen?
├─ NO → display/derivation bug in that surface
│        → which view does its own math instead of ledger sums? (grep the template/view)
└─ YES → breakdown(worker):
    ├─ Expected wrong? → production truth:
    │     reported vs verified on the WSC lines (Report Review)
    │     → [stage-tracking](../features/stage-tracking.md) debugging table
    ├─ Earned wrong (credits)?
    │     ├─ missing credit → was the line settled? WSC.settlement_line NULL
    │     │    = still Expected (settle the Adda) · funnel skipped it?
    │     │    (era guards / monthly-basis / grouped→0 — each refusal is a FEATURE)
    │     ├─ extra credit → follow its SWA → which ADST? reversed already?
    │     └─ wrong amount → qty (verified??reported at THAT time) × frozen
    │          rate snapshot — a later rate edit NEVER re-prices (S2 freeze)
    ├─ Paid wrong (debits)?
    │     → per-debit category: settlement_payment ↔ SETL ref ·
    │       advance_recovery ↔ PSI row (reversed_at stamp?)
    └─ Advance remaining wrong?
          → advance_remaining(adv): amount − non-reversed recoveries;
            check PSI.reversed_at + F&F write-offs (no ledger debit — by design)
```

## Which checks, concretely

| Check | How |
|---|---|
| Ledger rows for the worker | newest-first, follow every source FK (assignment/advance/settlement) — a row with NO source (non-reversal) = alarm |
| Four-way identity | ledger ≡ settlement totals ≡ Σ items ≡ Σ snapshots — if an IDENTITY breaks, stop everything; that's a real bug, not a display issue |
| Reversal pairing | every reversal points at its original (`reverses` FK); an unpaired anomaly = the DB partial-unique should have made it impossible |
| Frozen vs live | `AddaSettlement.expected_total` is a write-once AUDIT value — never reconcile against it as live truth (§11.9.4) |

## Known real causes (from this repo's history)

- **Not a bug — a refusal:** monthly workers' lines are structurally
  excluded (R4); grouped stages pay ₹0 by guard (F2). The "missing" money
  was never owed.
- **Reversal shown as duplicate:** both directions listed — reading rows
  without netting. Use the breakdown call.
- **The pre-V2 leak class (paid 120 / produced 105):** if reconciliation
  says over-paid vs produced → the S1/S5 reconciliation evidence flow; the
  allocation bound exists for exactly this.

## Escalation line

Identity broken · money row without provenance · double credit on one line
(era guards both bypassed) → STOP, don't fix data by hand. Owner + the
Money-Write STOP rule apply. *(Haath se ledger theek karna = itihas se
jhooth bolna.)*

## Where to learn the concepts

[ledger](../features/ledger.md) · [settlement](../features/settlement.md) ·
[payroll](../features/payroll.md) · [two-truths](../concepts/architecture/two-truths.md) ·
[append-only-tables](../concepts/database-design/append-only-tables.md)

## Implementation References

- Reconciliation: [docs/ARCHITECTURE_V2.md](../../docs/ARCHITECTURE_V2.md) §11.9 · S5 gate: [docs/S5_DESIGN_RECEIPT_2026_06_14.md](../../docs/S5_DESIGN_RECEIPT_2026_06_14.md)
- Ops view: [docs/release/TROUBLESHOOTING.md](../../docs/release/TROUBLESHOOTING.md)

## Code References

- `expense/services/ledger_service.py` (`worker_balance`) · `payroll_service.py` (`worker_balance_breakdown`, `advance_remaining`) · `adda_settlement_service.py` (`_settleable_lines` — the funnel that "loses" lines legally)
- Tests already covering: `test_v2_3_guards.py` · `test_reopen_voids_pay.py` · goldens
