# `expense` app — Worker Money: Settlement, Ledger, Advances, Payment

> Dual-register guide: for developers AND for the owner learning the system.
> Canonical truth: [docs/ARCHITECTURE_V2.md §11](../../docs/ARCHITECTURE_V2.md) +
> [ADR-0005](../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md) /
> [0007](../../docs/adr/0007-allocation-era-ledger-cutover.md) /
> [0009](../../docs/adr/0009-cost-truth.md). First-read:
> [docs/PROJECT_KNOWLEDGE_MAP.md](../../docs/PROJECT_KNOWLEDGE_MAP.md).
> (Pre-V2 payroll docs are archived under docs/archive/production/.)

## Purpose

Yeh app **paisa** sambhalta hai — aur sirf paisa. Workers ka kaam kitna hua
yeh `production` app ka sach hai; **us kaam ke paise kab bane, kitne bane,
kitne diye** — yeh sab yahan hai.

## Business responsibility

One sentence: **settlement banata hai earning; payment deta hai cash; ledger
sab kuch yaad rakhta hai — hamesha ke liye.**

- An **AddaSettlement** is the owner's approval event: "is Adda ka kaam
  check ho gaya, ab paise book karo." (Settlement ≠ payment!)
- A **PayrollSettlement** is now PAYMENT-ONLY: cash diya, bas.
- A **WorkerAdvance** is a loan pool — recovery happens ONLY at Adda
  settlement, owner ki marzi se, per-advance.
- The **WorkerLedgerEntry** table is the financial truth: append-only,
  kabhi edit nahi, kabhi delete nahi.

## What tables are created (database impact)

| Table | One row means | Lifecycle |
|---|---|---|
| `expense_workerledgerentry` | one money movement (credit/debit) for one worker | INSERT-only, forever. Mistake = opposite-direction REVERSAL row, never UPDATE |
| `expense_addasettlement` | one settlement EVENT on one Adda (`ADST-0007`) | draft → finalized → reversed/superseded; drafts may be discarded (no money yet) |
| `expense_addasettlementitem` | FROZEN per-worker snapshot of what the owner approved | write-once at finalize; NEVER recomputed (audit record) |
| `expense_stageworkassignment` (SWA) | one EARNING LINE (worker × stage × color/size) | created at settlement finalize (era-B) or, historically, at allocation (era-A — `adda_settlement` NULL); corrected by soft `voided_at`, never deleted |
| `expense_payrollsettlement` | one CASH PAYMENT to one worker (`SETL-0012`) | append-only |
| `expense_payrollsettlementitem` | one advance-recovery line (XOR-parented to payment OR adda-settlement) | append-only + `reversed_at` stamp (never signed/edited) |
| `expense_workeradvance` | one loan given to a worker | append-only; outstanding = live SUM minus recoveries |
| `expense_workerprofile` | bank/UPI/opening-balance per worker | normal mutable row (not history) |

**Example row (ledger):** `id=10, worker=utest, entry_type=credit,
category=stage_earning, amount=180.00, assignment=SWA#42, notes='ADST-0003 ·
3-PATTI-001'` — matlab: "utest ko 3-PATTI-001 ke settlement ADST-0003 se
₹180 ka earning मिला, line SWA#42 se."

## How data flows through this app

```
production truth (WSC: reported/verified qty, frozen expected_rate)
        │  (read-only — settlement NEVER edits production)
        ▼
 AddaSettlement DRAFT  ──discard──▶ (deleted; no money existed)
        │ finalize  (adda_settlement_service — THE chokepoint)
        ▼
 per line: SWA earning line + ledger CREDIT (stage_earning)
 per advance chosen: ledger DEBIT (advance_recovery) + PSI row
 per worker: FROZEN AddaSettlementItem  + settlement totals
        │
        ▼ mistake found?
 reverse_adda_settlement → compensating ledger rows + SWA voided
                         → optional successor draft (supersede chain)
        │
        ▼ cash day
 PayrollSettlement (payment-only) → ledger DEBIT (settlement_payment)
```

Worker visibility ladder (V2-3): **Expected (unsettled)** — frozen
`expected_*` on WSC, sirf dikhane ke liye → **Earned (settled)** — ledger →
**Paid (cash)**. Teeno kabhi overlap nahi karte (tested).

## What services are allowed to write (single-writer rules)

| Table | SOLE writer | Enforced by |
|---|---|---|
| WorkerLedgerEntry | `ledger_service` | CLAUDE rule 5 + code review |
| AddaSettlement + Item | `adda_settlement_service` | **CI gate [4b/4]** |
| StageWorkAssignment | `allocation_service` (era-A, lever-only) + `adda_settlement_service` (era-B) | **CI gate [4c/4]** |
| PayrollSettlement(+Item) | `settlement_service` (payment-only since V2-2) | review |
| WorkerAdvance | `payroll_service.record_advance` | review |
| SettlementReconciliationEvidence | `adda_settlement_service.record_reconciliation_evidence` (S1.1, H2) | review |

**M-6 reconciliation (S1.1):** at finalize, `record_reconciliation_evidence` PERSISTS
an append-only `SettlementReconciliationEvidence` row per stage where settled qty >
recorded output (the B-1 leak). Scoped to `SETTLEMENT_WARN_FLAGS = {over_allocated}`
only (H1 — `no_output_qty`/`grouped_paid`/`unpriced_paid` stay in `reconcile_pay`'s
full report, not the settlement WARN — they were noise). Persisted, not log-scraped,
so the soak's B-1 metric survives later corrections. WARN-only in S1.1; S5 → BLOCK.

**M-6 BLOCK (S5):** when `ENFORCE_SETTLEMENT_RECONCILIATION` (default **False**=WARN) is on,
`finalize` **refuses** an `over_allocated` stage (settled good > produced `cost_quantity_snapshot`)
beyond `SETTLEMENT_RECONCILIATION_TOLERANCE` (abs pieces, default 0) — quantity-only (no
rate/earning); pre-check rolls back the atomic finalize so nothing books. A **super-admin** may
finalize anyway with `reconciliation_override=<reason>` (stamped append-only on
`SettlementReconciliationEvidence.override_reason/overridden_by`, migration 0011). Actionable
block diagnostics; super-admin override field on the settlement screen. Both this flag and
`ENFORCE_ALLOCATION_BOUND` ship OFF + are enabled per the
[enforcement rollout runbook](../../docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md).

### Why this design exists / what breaks if bypassed

- **Why one writer per money table?** Paise ka hisaab tab hi bharosemand hai
  jab likhne ka EK hi darwaza ho. Har guard (double-credit, recovery ≤
  remaining, lock order) us darwaze pe baitha hai.
- **What breaks if you write the ledger directly?** Balances are live SUMs —
  a stray row silently changes what the factory owes a worker, with no
  reversal path and no settlement reference. The append-only promise means
  your mistake is PERMANENT history.
- **What breaks if you edit a frozen AddaSettlementItem?** The audit record
  of "what the owner approved" stops matching the ledger — the entire
  correction system (reverse/supersede) assumes snapshots never move.
- **What breaks if settlement money is touched outside the lifecycle?**
  Exactly the two V2-3 PR-A holes: reopen/void used to reverse settlement
  credits while the settlement still read FINALIZED. Now both refuse and
  name the ADST reference.

## Chokepoint services (who calls / what writes / invariant protected)

### `adda_settlement_service` — THE money event
- **Who calls:** management UI (Payroll → Adda Settlements) only;
  `_ensure_management` inside.
- **Writes:** SWA lines, ledger credits/debits (via ledger_service),
  PSI recovery rows, frozen items, settlement status, AddaHistory events.
- **Why single writer:** finalize is a multi-table money transaction with a
  strict lock order (advisory lock 5374 → ADST row → stage records →
  worker profiles → advances). Two writers = deadlocks + double credits.
- **Invariant protected:** *a contribution line is paid at most once, ever*
  (cross-era guard both directions), and *every paise is traceable*:
  item ↔ SWA ↔ ledger ↔ WSC.settlement_line.

### `ledger_service` — the pen that writes money
- **Who calls:** other expense services only — never views.
- **Writes:** WorkerLedgerEntry INSERTs (log_credit / log_debit /
  reverse_entry).
- **Invariant:** append-only; a reversal copies `entry_date` so monthly
  totals net correctly in-period.

### `allocation_service` — the LEGACY path (rollback lever only)
- Since V2-3 the default refuses (`LEDGER_CREDIT_AT_ALLOCATION=False`);
  env True restores it fully (tested by 8 pinned test classes).
- `void_allocation` corrects era-A lines only; era-B refuses → "reverse the
  settlement instead."

### `settlement_service` — payment-only
- Rejects any recovery input loudly (recovery moved to Adda settlement).

### `payroll_service` — the READ layer
- All dashboards/My Earnings read through here. Knows the era rules so
  templates never do.

## Views (what enters)

`/expense/my/` worker self-view (never role-gated, always self-scoped) ·
`/expense/payroll/` + `/workers/<id>/` management · `/workers/<id>/settle/`
CASH payment · `/advances/add/` · `/expense/settlements/…` the settlement
queue/detail/actions. All money POSTs: management-gated + confirm dialogs.

## Common mistakes (developers: DO NOT)

1. Never `WorkerLedgerEntry.objects.create(...)` outside ledger_service.
2. Never UPDATE/DELETE money rows — reversal/void/stamp patterns only.
3. Never read `WSC.expected_*` as money (visibility only — ADR-0005).
4. Never sum `processing_cost + settled labor` (same labor twice — ADR-0009).
5. Per-Adda actual labor = Σ non-voided SWA snapshots (both eras) — never
   Σ settlement totals (partial/reversed chains mis-sum).
6. Don't add fields to frozen tables casually — frozen means frozen.

## Django Learning Notes (is app mein kaunse patterns kyun)

- **`transaction.atomic` + `select_for_update()`**: finalize/reverse pura ek
  transaction hai; `select_for_update` row ko lock karta hai taaki do
  managers ek saath finalize na kar dein. Lock ORDER fixed hai (5374 →
  ADST → SR → profile → advance) kyunki alag order = deadlock.
- **`pg_advisory_xact_lock(5374)`**: Postgres ka app-level lock — reference
  numbering (`ADST-0007`) race-safe banata hai bina table banaye.
- **`on_delete=PROTECT`** on every money FK: ledger row ke peeche ka Adda/
  worker/SWA kabhi delete nahi ho sakta — history anchor hai.
  (CASCADE sirf wahan jahan child bina parent ke meaningless ho;
  SET_NULL sirf optional references pe.)
- **CheckConstraints** (DB-level): `finalized ⇒ settled_at`, `recovered ≤
  outstanding`, XOR exactly-one-parent on PSI — app bug bhi DB ko jhooth
  nahi likhwa sakta.
- **No signals** (ADR-0001): sab kuch service functions mein, explicitly —
  "yeh kab chala?" ka jawab hamesha stack trace mein milta hai.
- **Frozen snapshot vs live SUM**: snapshot = "us waqt kya approve hua"
  (kabhi recompute nahi); balance = "abhi kitna baaki" (hamesha SUM). Dono
  ka mix hi audit + accuracy dono deta hai.

## Related ADRs

0001 (services own writes) · 0002 (single writer) · 0005 (Option B — truth
split) · 0007 (era cutover + lever) · 0009 (cost truth / never-add) ·
0010 §4 (rework case-scoping).

## Real factory example (end-to-end)

3-PATTI-001: utest ne cutting pe 60 Red Size-1 + 15 Size-2 report kiya
(15 verified ho ke 15 hi rahe). Stage complete → settlement queue mein Adda
"Ready ₹225". Accountant draft kholta hai → lines check → variance "73
packed, 2 missing" → Finalize → ledger mein do credit (₹180 + ₹45), frozen
item ₹225, ADST-0003. Galti mili? Reverse & settle again → compensating rows,
naya draft, chain ADST-0001→0002→0003 hamesha dikhega. Phir cash day pe
worker detail → Pay → ₹225 — payment-only screen, ledger DEBIT, ho gaya.
