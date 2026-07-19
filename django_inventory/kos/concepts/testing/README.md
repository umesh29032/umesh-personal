---
id: readme-concepts-testing
type: system
verified: 2026-07-19
---

# Testing — pin the truth, not the coverage number

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

1,878 tests guard this repo, and the interesting part is WHAT they pin: exact rupee amounts, refusals, query counts, constraint bites, both faces of every flag. *(Coverage batata hai kahan chale; pin saabit karta hai kya WAADA kiya.)*

| Page | Real question it answers |
|---|---|
| [testing-strategy.md](testing-strategy.md) | How does one developer trust a money system — what do tests actually PIN? |

**After this folder you can:** design test suites that make regressions loud and refactors fearless — the golden/refusal/probe/count/flag toolkit.

*Pairs with pg/constraints (negative probes) and query-performance (count pins).*
