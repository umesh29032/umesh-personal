---
id: readme-concepts-database-design
type: system
verified: 2026-07-19
---

# Database Design — tables that can face an audit

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

Schema design here is one question asked table by table: will someone ever need to PROVE what happened? Yes → evidence table (append-only, corrections as counter-events). *(Saboot kabhi edit nahi hota — naya saboot judta hai.)*

| Page | Real question it answers |
|---|---|
| [append-only-tables.md](append-only-tables.md) | Why never UPDATE/DELETE money & history rows — and how do corrections work then? |

**After this folder you can:** decide evidence-vs-state for any table, and design correction paths that survive audits.

*Grows in later phases (frozen-snapshots, schema-design) — only when the project anchors them.*
