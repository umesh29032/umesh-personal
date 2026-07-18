---
id: l2-apps-expense-app-flow
type: topic-canonical
status: active
owner: handwritten
scope: expense
anchors: config/expense/
verified: 2026-07-13
---

# expense — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Junior: yeh app sirf PAISA sambhalta hai. Kaam ka sach production app me;
> us kaam ke paise kab/kitne bane/diye — sab yahan. **settlement ≠ payment.**

## Flow 1 — Settlement (earning banta hai)
```
Adda ke payable stages complete → settlement queue me "Ready"
 → manager draft kholta hai → lines + variance + recovery dekhta hai
 → FINALIZE → ledger me CREDIT (earning) + DEBIT (advance recovery)
 → frozen AddaSettlementItem (jo approve hua) + SWA earning line
```
Galti? → REVERSE (compensating rows) ya REVERSE & SUPERSEDE (naya draft, chain).

## Flow 2 — Payment (cash diya — ALAG event)
```
worker detail → Pay → amount (pending payable prefilled) → Confirm
 → ledger DEBIT (settlement_payment). Recovery yahan NAHI (refuse).
```

## Flow 3 — Advance (loan)
Record Advance → WorkerAdvance row. Recovery sirf settlement par hoti hai
(owner per-advance chunta hai, ≤ remaining).

## Flow 4 — Worker visibility (3 alag numbers, kabhi overlap nahi)
Expected (unsettled, frozen WSC) → Earned (settled, ledger) → Paid (cash).

## Eras
Default ab settlement-first (V2-3); purana allocation-time credit = era-A
(SWA.adda_settlement NULL), readable/reversible forever. Mechanism + the
`LEDGER_CREDIT_AT_ALLOCATION` lever (canonical):
[ARCHITECTURE_EXPLAINED/10_why_eras.md](../../ARCHITECTURE_EXPLAINED/10_why_eras.md).

---
*Canonical depth (don't duplicate — read these):* business view →
[config/expense/README.md](../../../../config/expense/README.md) · file-by-file dev
view → [docs/apps/expense/GUIDE.md](../../../apps/expense/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
