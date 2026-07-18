---
id: l2-architecture-explained-04-why-workerledgerentry
type: topic-canonical
status: active
owner: handwritten
scope: learning — architecture rationale
anchors: —
verified: 2026-07-13
---

# Why WorkerLedgerEntry exists

**Problem:** "Worker ko abhi kitna dena hai?" — agar yeh ek number kahin STORE
karein, woh drift karta hai (do jagah update, ek miss, balance galat).

**Solution:** WorkerLedgerEntry = ek APPEND-ONLY kitab. Har paisa-harkat ek row:
credit (earning) ya debit (recovery/payment). Balance kabhi store nahi —
HAMESHA live `SUM(credit) − SUM(debit)`.

**Isi liye:** ek hi source of truth, jo jhooth nahi bol sakta. Galti = ULTI
direction REVERSAL row (entry_date copy hoti hai → mahine ka total net ho jaata
hai). Row kabhi edit/delete nahi.

**Agar na ho:** stored balance + multiple writers = silent corruption jo kabhi
pakad me nahi aata; "yeh ₹500 kahan se aaye" ka koi trail nahi. Append-only
ledger hi pure financial truth deta hai.

ADR-0002/0005 · [chokepoint](../CHOKEPOINTS/ledger_and_payment.md) ·
[07](07_why_append_only.md).
