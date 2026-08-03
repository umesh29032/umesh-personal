---
id: pattern-validation-chain
type: concept
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "The Validation Chain pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Validation Chain

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Parse at the edge → business-validate in the service → DB constraints as the floor.

> 💡 **Samjho aise:** Teen chhanniyaan: **form** (shakal theek hai?) → **service** (rule theek hai?) → **database** (aakhri pehra). Upar wali chook jaaye to neeche wali pakad legi.

**Problem it solves.** Single-layer validation fails the paths it doesn't cover.

**Where it's used (the cross-app map).**
- edge: `Decimal(str(x))` / PA-07-2 parsing in views
- service: loud ValidationErrors that NAME the fix (monthly-advance refusal = the exemplar)
- floor: 81 CHECKs + partial uniques ([constraints](../postgresql/constraints.md))
- config-time flavor: flow-editor monotonicity/grouping validation

**How it works (one breath).** Each tier catches what only it can: type-safety at the edge, context in the verb, race-proof invariants in PG.

**Trade-offs.** Three places to keep coherent (the S3 one-file migration pattern keeps data+constraint in step).

**Common mistakes.** Trusting the form layer for money · IntegrityError as control flow · constraints without negative probes.

**Related.** [constraints](../postgresql/constraints.md) · [service-layer](../architecture/service-layer.md)
