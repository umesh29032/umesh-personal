---
id: docs-adr-0011-monthly-salary-factory-level
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-0011 — Monthly salary is a FACTORY-LEVEL cost: no per-Adda allocation

Status: **ACCEPTED** (owner, 2026-07-05 — R5 approval message).
Source: PDD §17 (MONTHLY, §27-D4) + §21 (FactoryExpense) + owner business
clarification at R5 approval. Companion locks: ADR-0009 (cost truth),
[R4_EXECUTION_PLAN.md](../R4_EXECUTION_PLAN.md) (settlement exclusion).

## Decision

Monthly workers are **still full production workers**. Nothing about
production tracking changes for them — Addas, stages, quantities, completed
stages, work history, dashboard progress: ALL tracked exactly like piece-rate
workers. The ONLY difference is **how they are paid**:

1. Their payment NEVER comes from Adda settlement (R4 structural exclusion at
   `_settleable_lines`).
2. Their salary is recorded in `FactoryExpense` (`category=salary`,
   `worker` FK — **audit-only**: it must never create a ledger or settlement
   relationship).
3. **Monthly salary is NOT allocated into individual Adda manufacturing
   cost.** This is an intentional business decision, not missing
   functionality.

## Why no allocation (yet)

A monthly worker may work on many Addas during the month. No allocation model
has been chosen — candidates (production quantity, pieces, layers, working
time, stage contribution, …) have materially different outcomes and the owner
has not decided. Guessing one would freeze wrong numbers into cost history.

Consequently, until a future cost-allocation phase:

- Production tracking stays complete (per above).
- Worker dashboards stay complete.
- `FactoryExpense` records monthly salaries (factory-level).
- Per-Adda manufacturing cost (`processing_cost`, ADR-0009 full-cost formula,
  costing dashboards) **EXCLUDES monthly salaries** — and must not silently
  start including them.

## Future (reserved, not built)

1. **Factory-level monthly reporting** — FactoryExpense totals (salary, rent,
   electricity, other) alongside production output (Addas completed,
   manufacturing output) → factory operating cost for the month. Uses
   FactoryExpense + production data as they already exist.
2. **A later cost-allocation feature** may distribute monthly expenses across
   Addas ONLY after the business rules are finalized — and it **must not
   require changing production history, settlement history, worker history,
   or FactoryExpense history**. (Derived-report or new-table designs qualify;
   anything rewriting frozen rows does not.)

## Guardrails for future phases

- Any design that adds salary (or any FactoryExpense) into
  `processing_cost`, the ADR-0009 full-cost formula, costing dashboards, or
  settlement math **violates this ADR** — it needs an explicit owner-approved
  revision here first.
- The `FactoryExpense.worker` FK is for "whose salary was this?"
  investigations only. Joining it into pay/cost computations is out of bounds.
