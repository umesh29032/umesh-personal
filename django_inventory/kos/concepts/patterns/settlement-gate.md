---
id: pattern-settlement-gate
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Settlement Gate pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Settlement Gate

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Provisional data flows freely; committed truth passes ONE atomic, locked, audited gate.

**Problem it solves.** Committing at capture time makes every correction a commitment correction.

**Where it's used (the cross-app map).**
- THE gate: `finalize_adda_settlement` ([expense §13](../../apps/expense/urls.md))
- same shape smaller: stage complete → pool materialization ([allocation](../../features/allocation.md)) — capacity's gate
- generalizes to: any draft→finalize lifecycle you ever add

**How it works (one breath).** Draft = recomputable scratchpad (rich, cheap) → gate = validate-everything-first, locks in fixed order, write, freeze snapshots → after = reverse-only.

**Trade-offs.** Gate code is dense (it absorbs everyone else's complexity — draft-heavy/gate-thin).

**Common mistakes.** Second gates · preview surfaces with different guards than the gate (PA-11-2) · editing past the gate.

**Related.** [settlement](../../features/settlement.md) · [two-truths](../architecture/two-truths.md)
