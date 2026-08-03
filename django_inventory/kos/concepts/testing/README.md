---
id: readme-concepts-testing
type: system
verified: 2026-07-27
---

# Testing — pin the truth, not the coverage number

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

1,878 tests guard this repo, and the interesting part is WHAT they pin: exact rupee amounts, refusals, query counts, constraint bites, both faces of every flag. *(Coverage batata hai kahan chale; pin saabit karta hai kya WAADA kiya.)*

| Page | Real question it answers |
|---|---|
| [testing-strategy.md](testing-strategy.md) | How does one developer trust a money system — what do tests actually PIN? |
| [local-testing-environment.md](local-testing-environment.md) | My local DB is full of old test junk — how do I get a CLEAN factory to hand-test on, without destroying what I have? |

**After this folder you can:** design test suites that make regressions loud and refactors fearless — the golden/refusal/probe/count/flag toolkit — and stand up a clean local factory to hand-test on in five minutes.

*Pairs with pg/constraints (negative probes) and query-performance (count pins).*
