---
id: pattern-configuration-over-code
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Configuration over Code pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Configuration over Code

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Business variability lives in ROWS; code ships capabilities, not cases.

**Problem it solves.** Every hardcoded case = a deploy per business change.

**Where it's used (the cross-app map).**
- Stage library + WorkflowStage flows + R10-B generic endpoints ([flow editor ED](../../apps/production/urls-core.md))
- R10-C masters (categories, machine types)
- devseed scenarios-as-data · enforcement FLAGS (deploy-off→soak→enable)

**How it works (one breath).** Model the VOCABULARY (rows) + one parameterized engine (handlers/generic endpoints); validate configs at config-time, loudly.

**Trade-offs.** Config UIs need guards; bad config must fail at save, not at runtime.

**Common mistakes.** Name-conditionals on config values (the handler-dispatch rule exists against this) · enums for factory-changeable lists.

**Related.** [production README ED](../../apps/production/urls-core.md) · [settings §flags](../django/settings.md)
