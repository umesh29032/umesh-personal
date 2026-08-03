---
id: pattern-transaction-boundary
type: concept
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "The Transaction Boundary pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Transaction Boundary

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** One business event = one atomic function = one lock plan.

> 💡 **Samjho aise:** Ek business kaam = **ek hi atomic function**. Ya poora hoga, ya bilkul nahi — aadha-adhoora kabhi nahi. Bijli chali jaaye tab bhi.

**Problem it solves.** Boundaries drawn by code shape (view/request) instead of event shape corrupt half-events.

**Where it's used (the cross-app map).**
- ALL 206 atomic sites live on service verbs
- the canon: finalize's lock order (5374 → … ) · pool ops (5375, objid) · the payment races pair

**How it works (one breath).** @atomic on the DECIDING verb; validate-first to keep lock windows thin; on_commit for side effects; locks ordered totally.

**Trade-offs.** Callers must come through the verb (single-writer makes that law).

**Common mistakes.** ATOMIC_REQUESTS · atomic in views · locks without joining the documented order.

**Related.** CANONICAL: [transactions](../django/transactions.md) + [locks](../postgresql/locks.md).
