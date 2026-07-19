---
id: pattern-materialized-snapshot
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Materialized / Frozen Snapshot pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Materialized / Frozen Snapshot

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Freeze a value at its moment of truth so later config changes never rewrite history.

**Problem it solves.** Live-computed values drift under config edits; history must mean what it meant.

**Where it's used (the cross-app map).**
- `AddaStageRoleRate` (rates frozen at Adda creation) · `expected_*` (at task complete) · `processing_cost` (ADR-0009) · `AddaSettlementItem` + settlement totals (at finalize) · `StagePoolSnapshot` (at stage complete) · APSCPB (at cutting complete)

**How it works (one breath).** Compute once at the boundary event, write-once, NEVER re-read as live truth for money math (audits only) unless the snapshot IS the contract (rates).

**Trade-offs.** Storage + the discipline to know which reads use snapshot vs live.

**Common mistakes.** Re-deriving from live config 'because fresher' · editing snapshots · snapshotting without a correction lane (rerate-until-settlement is the lawful one).

**Related.** [two-truths](../architecture/two-truths.md) · [production models](../../apps/production/models.md)
