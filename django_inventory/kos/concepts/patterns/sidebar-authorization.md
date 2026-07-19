---
id: pattern-sidebar-authorization
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The Sidebar Authorization (The Pair) pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Sidebar Authorization (The Pair)

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Menu visibility and URL access from ONE rule row — drift is unrepresentable.

**Problem it solves.** Hide-only menus are security theater; separate gate configs drift from menus.

**Where it's used (the cross-app map).**
- `SidebarItemRule` + middleware + context processor ([inventory services — the trio](../../apps/inventory/services.md))
- same collapse-the-pair idea: Stage model carrying its own access rules ([production urls-core §stages](../../apps/production/urls-core.md))

**How it works (one breath).** One row read by the renderer AND the enforcer; unmanaged URLs keep view mixins (additive defense).

**Trade-offs.** Every request pays a rule lookup; exempt lanes need loop care.

**Common mistakes.** A second predicate for one surface · menu edits treated as cosmetic · forgetting the rule row for a new URL.

**Related.** [rbac-access](../../features/rbac-access.md) — canonical teaching.
