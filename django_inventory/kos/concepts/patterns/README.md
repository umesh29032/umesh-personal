---
id: readme-concepts-patterns
type: system
verified: 2026-07-19
---

# Engineering Patterns — the cross-app reuse map

*(Part of [Concepts](../README.md) → the [LOS](../../README.md). Born from
certification evidence: task 12 proved patterns were invisible across apps.)*

## Teacher's note

These cards are deliberately THIN. Deep teaching stays on the canonical
concept/feature pages (One-Canonical law); a pattern card answers the
question those pages can't: **"where ELSE is this used, and what's the
reuse contract when I need it in MY app?"** Before building anything that
smells familiar, scan this table — the repo probably already solved it.
*(Naya banane se pehle: kahin bana to nahi rakha?)*

| Pattern | One line | Reuse trigger |
|---|---|---|
| [tracked-export](tracked-export.md) | exports as recorded, re-downloadable artifacts | ANY new export |
| [append-only-ledger](append-only-ledger.md) | truth as immutable events | any contract-grade data |
| [settlement-gate](settlement-gate.md) | draft freely, commit through ONE gate | any draft→finalize lifecycle |
| [sidebar-authorization](sidebar-authorization.md) | menu = gate, one row | every new URL |
| [materialized-snapshot](materialized-snapshot.md) | freeze values at their moment of truth | anything priced/counted at an event |
| [workspace-pattern](workspace-pattern.md) | GET console + focused POST verbs | any multi-step floor UI |
| [audit-trail](audit-trail.md) | who/what/WHY as rows, same transaction | any sensitive mutation |
| [configuration-over-code](configuration-over-code.md) | business variability as rows | any "add another kind of X" |
| [golden-test](golden-test.md) | byte-identical end-to-end replays | any money-adjacent change |
| [validation-chain](validation-chain.md) | edge → service → DB floor | every input that matters |
| [transaction-boundary](transaction-boundary.md) | one event, one atomic verb, one lock plan | every multi-row write |

**Law for future app pages:** LINK a pattern card instead of re-explaining
the pattern. **Law for these cards:** stay thin; if a card starts teaching,
move the teaching to the canonical page and link it.
