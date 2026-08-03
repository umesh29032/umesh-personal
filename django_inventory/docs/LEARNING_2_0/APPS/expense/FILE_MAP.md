---
id: l2-apps-expense-file-map
type: topic-canonical
status: active
owner: handwritten
scope: expense
anchors: config/expense/
verified: 2026-07-13
---

# expense — every important file (FILE_MAP)

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py (one file — money tables together)
- **WorkerLedgerEntry** — append-only money kitab. entry_type (credit/debit),
 category (stage_earning/advance_recovery/settlement_payment/reversal…),
 amount (CHECK >0), FK assignment/advance/settlement, `reverses` self-FK.
 Balance = live SUM, never stored.
- **StageWorkAssignment (SWA)** — earning LINE; frozen rate/amount snapshot;
 `adda_settlement` FK = era marker (NULL=era-A, set=era-B); `voided_at` soft.
- **AddaSettlement** — the event (ADST-XXXX, status, frozen totals, `supersedes`).
- **AddaSettlementItem** — FROZEN per-worker snapshot (what owner approved).
- **PayrollSettlement(+Item)** — cash payment (SETL-XXXX) + recovery lines (XOR-parent, reversed_at).
- **WorkerAdvance**, **WorkerProfile**. Constraints carry inline comments.

## services/
- `adda_settlement_service.py` ★ — sole ADST(+Item)+era-B SWA writer (gates
 4b/4c). create_draft / finalize_adda_settlement / reverse_adda_settlement /
 settlement_queue / preview_lines / discard_draft. Lock order §11.5.
- `ledger_service.py` ★ — sole WorkerLedgerEntry writer. log_credit/debit,
 reverse_entry, worker_balance.
- `settlement_service.py` — payment-only (recovery refused).
- `allocation_service.py` — era-A legacy (lever-gated) + void (era-B refuse).
- `payroll_service.py` ★ — ALL reads (balances, rollups, unsettled_expected — era-aware).
- `advance_service.py`, `reconciliation_service.py`, `_shared.py` (auth gates).

## views.py — FILE MAP at top; 9 view classes (My Earnings, payroll overview,
worker detail, payment, advance, profile, settlement list/start/detail).

## forms.py — SettlementForm, AdvanceForm, WorkerProfileForm.
## urls.py — money-URL map in header. admin.py — read-only ADST/Item admins.
## management/commands/reconcile_pay.py — pay reconciliation (PAY-4).
## templates/expense/ — my_earnings, worker_detail, settlement_form (payment),
adda_settlement_list/detail, advance_form, worker_profile_form, payroll_overview.
All on base.html canonicals (A-scope).

## transaction boundaries
finalize_adda_settlement + reverse_adda_settlement = atomic, advisory lock 5374
+ ordered row locks. create_settlement = atomic. ledger writes inside caller's atomic.

---
*Canonical depth (don't duplicate — read these):* business view →
[config/expense/README.md](../../../../config/expense/README.md) · file-by-file dev
view → [docs/apps/expense/GUIDE.md](../../../apps/expense/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
