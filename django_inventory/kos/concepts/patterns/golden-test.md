---
id: pattern-golden-test
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Golden Test pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Golden Test

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Real business scenarios replayed end-to-end, asserting byte-identical outcomes.

**Problem it solves.** Unit tests can all pass while the composed money math drifts.

**Where it's used (the cross-app map).**
- ₹344.25 / ₹801 / ₹633 settled journeys (+ historical ₹225) — devseed worlds replayed through REAL services
- flag both-states testing rides them (OFF ⇒ goldens identical)

**How it works (one breath).** Seed via services → run the full flow → assert EXACT decimals; changing a golden = an owner decision with a receipt, never a fix.

**Trade-offs.** Failures say WHAT broke, not always where; worlds need change-control.

**Common mistakes.** assertAlmostEqual · raw-fixture seeding · updating the number to green.

**Related.** CANONICAL: [testing-strategy](../testing/testing-strategy.md) §weapon-1.
