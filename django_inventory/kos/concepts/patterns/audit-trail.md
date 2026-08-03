---
id: pattern-audit-trail
type: concept
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "The Audit Trail pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Audit Trail

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Every sensitive mutation leaves WHO/WHAT/WHY as a row.

> 💡 **Samjho aise:** Har important badlaav ke saath teen cheezein likhi jaati hain: **kisne, kya, aur kyun**. Baad mein "yeh kisne kiya?" ka jawaab dhoondhna nahi padta.

**Problem it solves.** 'Who changed this and why' must be answerable without forensics.

**Where it's used (the cross-app map).**
- `RateCorrectionAudit` · `WorkerPayBasisAudit` · `ExpenseTemplateAmountAudit` · `SettlementReconciliationEvidence` (override_reason) · stream reasons-as-data · timeline `*History` events

**How it works (one breath).** The mutating verb writes its audit row IN the same transaction; reason often MANDATORY (DB-level where it matters).

**Trade-offs.** More tables; reasons demand UI fields.

**Common mistakes.** Optional reasons (become empty) · audit rows written by a second path (single-writer applies to audits too) · logging instead of rows for contract-grade actions.

**Related.** [single-writer](../architecture/single-writer.md) · [append-only-tables](../database-design/append-only-tables.md)
