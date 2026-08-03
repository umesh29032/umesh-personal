---
id: pattern-workspace-pattern
type: concept
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "The Workspace Pattern pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Workspace Pattern

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** One GET console + many focused POST action URLs, one service verb each.

> 💡 **Samjho aise:** **Ek page dikhane ke liye, aur har action ke liye alag chhota URL** — har URL ek hi kaam karta hai. Isliye har button ka asar saaf-saaf pata chalta hai.

**Problem it solves.** Monolithic form-submits can't model multi-step floor work; fat POST handlers hide verbs.

**Where it's used (the cross-app map).**
- layering (8 URLs) · pattern design (10) · cutting (14) · barcode-gen (5) — [production Parts 3–4](../../apps/production/urls-layering-pattern.md)
- settlement cockpit = the money flavor (GET cockpit + action= dispatch, [expense §13](../../apps/expense/urls.md))

**How it works (one breath).** Workspace view assembles read-only state; every mutation = its own URL → one auditable service verb; `?embedded=1` for iframe hosting.

**Trade-offs.** Many small URLs (the LOS documents each — that's the price and the discoverability win).

**Common mistakes.** Logic creeping into the workspace GET · combining verbs into one POST · forgetting reopen as a guarded verb.

**Related.** [production views](../../apps/production/views.md)
