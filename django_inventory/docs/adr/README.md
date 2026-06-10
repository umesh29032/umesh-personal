# Architecture Decision Records (ADRs)

Each ADR captures **one durable architectural decision** — the context, the choice, and the
consequences — as an immutable record. Unlike `docs/production/DECISION_LOG.md` (a running
brainstorm log) these are the *load-bearing* decisions that constrain how the system is
allowed to grow. Supersede an ADR with a new one; don't rewrite history.

Format: Status · Context · Decision · Consequences. Numbered, append-only.

| # | Decision | Status |
|---|---|---|
| [0001](0001-service-layer-owns-writes-no-signals.md) | Service layer owns all multi-row writes; no Django signals | Accepted |
| [0002](0002-single-writer-per-ledger-and-history-table.md) | Exactly one writer service per ledger / audit table | Accepted |
| [0003](0003-three-concept-rbac-skill-gated-stages.md) | Three-concept RBAC (UserType / Role / Skill); stages skill-gated; menu+URL co-gated | Accepted |
| [0004](0004-tracking-is-append-only-history-primitive.md) | `tracking` is an append-only history + barcode primitive | Accepted |
| [0005](0005-production-truth-vs-financial-truth-option-b.md) | Production truth ≠ financial truth; ledger only at settlement (Option B) | Accepted (V2 §11 settlement build pending) |
| [0006](0006-architect-for-scale-do-not-implement.md) | Architect for multi-factory / async / scale; do NOT implement them | Accepted |
