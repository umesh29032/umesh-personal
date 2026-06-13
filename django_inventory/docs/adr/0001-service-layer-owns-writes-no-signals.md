# ADR 0001 — Service layer owns all multi-row writes; no Django signals

**Status:** Accepted (CLAUDE.md rule #4)

## Context
Business state changes (advance a stage, freeze cost, allocate work, settle a worker) touch
multiple rows and must be atomic, auditable, and greppable. Two anti-patterns we explicitly
reject: (a) ORM writes scattered in views/forms, and (b) `save()`-override / signal-driven
side effects that fire invisibly and make control flow impossible to trace.

## Decision
- Every multi-row write lives in `config/<app>/services/`. Views are thin: parse the POST,
  call one service function, render. **Zero ORM writes in views.**
- **No Django signals** for business logic; no `save()` overrides that mutate other rows.
  State transitions are explicit, named service calls.
- Services own their own `transaction.atomic` boundary and any row locks.
- Async-readiness: service signatures take ids + primitives (`user_id`, not `request`) so a
  call can move to a task later with no signature change.

## Consequences
- One obvious place to read/lock/audit each transition; grep finds every writer.
- The old `accounts/signals.py` skill→layering retro-tag became the explicit
  `user_service.sync_user_skills` call (invoked from the views + admin `save_related`).
- Slightly more boilerplate than signals — accepted for traceability.
