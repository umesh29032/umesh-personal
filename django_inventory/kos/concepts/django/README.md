---
id: readme-concepts-django
type: system
verified: 2026-07-19
---

# Django — the framework, the way THIS repo bends it

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

Django gives you ten ways to do everything; this repo chose ONE way each time, for reasons that transfer to any Django job. These pages teach the framework through those choices — boundaries on services, honest managers, fearless migrations, fail-fast settings. *(Framework seekhna = uske defaults ke saath JHAGDA samajhna — kahan maane, kahan nahi.)*

| Page | Real question it answers |
|---|---|
| [transactions.md](transactions.md) | Why does settlement wrap everything in atomic, and what breaks without it? |
| [orm-and-managers.md](orm-and-managers.md) | What is a Manager really — and why Model.active instead of a filtered default? |
| [migrations.md](migrations.md) | How does a money-bearing schema change without ever losing data? |
| [settings.md](settings.md) | How can production never boot half-configured? |

**After this folder you can:** place transaction boundaries like a senior, read/design managers honestly, stage irreversible schema changes, and classify config into convenience/safety/behavior.

*Read order: transactions → orm-and-managers → migrations → settings.*
