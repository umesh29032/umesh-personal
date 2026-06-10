# ADR 0006 — Architect for multi-factory / async / scale; do NOT implement them

**Status:** Accepted (governing principle; docs/TARGET_ARCHITECTURE.md)

## Context
The system runs one factory, ~5k rolls/yr, ~10 concurrent users. It must *not* paint itself
into a corner for a second factory or async processing later — but building that machinery
now (Celery/Redis, a factory switcher, per-factory RBAC, closing-balance snapshot tables)
would be **over-engineering**: complexity and bug surface with zero current payoff.

## Decision
**Seams, not features. Target 8.5–9 architecture quality at low complexity — not a forced 10/10.**
- **Multi-factory:** allow a nullable `factory` FK + a `current_factory()` scoping helper that
  is a no-op at one site. Columns get added across tenant tables in ONE wave only when site #2
  is funded — half-scoping now would risk cross-factory leaks.
- **Async:** service signatures already take ids + primitives so a call is task-movable later;
  Celery/Redis stay behind a flag, deferred. M5 scalability = cheap in-process wins only
  (kill N+1, paginate, derived-balance reconciliation) — proven by `assertNumQueries` oracles.
- **Derived over stored:** balances/outstanding are computed live; a snapshot table is a
  documented *deferred seam*, not built.

## Consequences
- New stages add via the registry (a handler folder), not engine edits.
- Reviews target the seam's existence, not a built feature.
- Chasing 10/10 (the over-engineering trap) is explicitly out of scope.
