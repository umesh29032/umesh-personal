---
id: pattern-tracked-export
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Tracked Export pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Tracked Export

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Every export is a recorded, re-downloadable artifact — never a fire-and-forget file.

**Problem it solves.** Un-tracked exports can't be reproduced byte-identically → disputes; regenerating may silently differ.

**Where it's used (the cross-app map).**
- inventory /tracking exports: `_BaseExportTriggerView` + manifest rows + re-download ([inventory §§16–20](../../apps/inventory/urls.md))
- gate: refuses until barcode-gen completes (never export fiction)
- REUSE TARGET: any new export anywhere (e.g. payroll XLSX — certification task 12) SUBCLASSES the base, never forks

**How it works (one breath).** POST trigger → guard → generate artifact + manifest row → later downloads serve the STORED artifact by code.

**Trade-offs.** Storage for artifacts; a manifest table to maintain.

**Common mistakes.** Regenerating instead of re-downloading · exporting before the data's birth-stage completes · new format as a copy-paste instead of a subclass.

**Related.** [inventory services](../../apps/inventory/services.md) · [append-only-tables](../database-design/append-only-tables.md)
