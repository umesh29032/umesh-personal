---
id: readme-concepts-postgresql
type: system
verified: 2026-07-19
---

# PostgreSQL — where the truth actually lives

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

The app can lie to you; the database can't — IF you can read it. This is the owner's priority track (SQL = weakest area, so we go deepest here): every page carries REAL captured SQL and EXPLAIN plans from this repo's own dev DB — including the famous honest Seq Scan that ignores five declared indexes. *(SQL padhna aa gaya to ORM jaadu nahi, kaanch hai.)*

| Page | Real question it answers |
|---|---|
| [from-orm-to-sql.md](from-orm-to-sql.md) | What SQL does my queryset really run, and how do I SEE it? |
| [indexes.md](indexes.md) | Why does PG sometimes ignore my index — and when will it stop ignoring it? |
| [query-performance.md](query-performance.md) | Where does query time actually go, and how are regressions made impossible? |
| [locks.md](locks.md) | Row locks vs advisory locks — and why ORDER is the whole game? |
| [constraints.md](constraints.md) | Why 80+ CHECKs when services already validate? |

**After this folder you can:** debug any slow or wrong query with evidence instead of guesses, and design DB-level armor no code path can bypass.

*Read order: from-orm-to-sql → indexes → query-performance → locks → constraints.*
