---
id: l2-architecture-explained-05-why-settlement-not-payment
type: topic-canonical
status: active
owner: handwritten
scope: learning — architecture rationale
anchors: —
verified: 2026-07-13
---

# Why settlement ≠ payment (Model A)

**Problem:** "Settle karna" aur "cash dena" ek hi cheez maan lein to: earning,
recovery, aur cash handover sab ghul-mil jaate hain — partial payments, later
payments, disputes sab uljh jaate hain.

**Solution (Model A):** DO alag events.
- **AddaSettlement (finalize)** = earning BOOK + advance recover. Adda-scoped,
 reviewable, reversible. NO cash moves.
- **PayrollSettlement (payment)** = sirf CASH diya. Worker-scoped, partial/later
 allowed.

**Kyun:** earning approve karna ek BUSINESS faisla hai (kitna bana, kya recover);
cash dena ek alag physical event (kab, kitna). Inhe alag rakhne se: pehle saaf
"owe" banta hai, phir aaram se cash flow.

**Agar na ho:** recovery + cash + earning ek transaction me → reverse karna
nightmare; "settle ho gaya par paisa nahi mila" jaisa normal state represent hi
nahi hota.

ADR-0005 · settlement_service refuses recovery (payment-only).
