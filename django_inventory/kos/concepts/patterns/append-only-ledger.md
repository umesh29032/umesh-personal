---
id: pattern-append-only-ledger
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Append-Only Ledger pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Append-Only Ledger

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Money (or any contract-grade truth) as an immutable event log; corrections = compensating rows.

**Problem it solves.** Edited history is unprovable history.

**Where it's used (the cross-app map).**
- `WorkerLedgerEntry` ([ledger](../../features/ledger.md)) — the canon
- settlement reverse/supersede chains ([settlement-lifecycle](../../flows/settlement-lifecycle.md))
- histories: `*History` timelines (tracking) · possession windows (machines)

**How it works (one breath).** INSERT-only + direction-as-type + derived balances + one-reversal-per-entry partial unique.

**Trade-offs.** Tables grow forever; reads are folds (snapshot seam = the registered escape).

**Common mistakes.** Storing balances · UPDATE 'fixes' · netting reversal pairs away.

**Related.** CANONICAL TEACHING: [append-only-tables](../database-design/append-only-tables.md) — this card only maps usage.
