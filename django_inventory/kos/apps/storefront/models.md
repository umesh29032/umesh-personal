---
id: app-storefront-models
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "storefront's 7 presentation models — replicas by design; data ownership as the trust boundary."
related: [app-storefront]
---

# storefront — model knowledge (`models.py`, 317 lines · 7 models)

> 📂 [storefront app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Models = **database ke tables**
>
> Yeh file batati hai is app mein **kaunsi cheezein store hoti hain** aur har cheez ke kaunse column hain. Socho Excel ki sheets ki list — kaunsi sheet, aur usme kaunse columns. Code mein ek `class` = ek table.
>
> *(`storefront` app ka kaam: public website — featured products aur categories jo bahar dikhte hain.)*

## The ownership decision (the lesson in schema form)

Every model here is PRESENTATION — content the window-dresser curates:

| Model (line) | Role |
|---|---|
| `HomePageConfig` (4) | the page's knobs — hero text, toggles, ordering |
| `Category` (115) | display grouping (NOT production's StageCategory, NOT a manufacturing taxonomy) |
| `FeaturedProduct` (147) | the display item — name/images/copy owned HERE |
| `HeroShowcaseCard` (229) · `WhyUsCard` (257) | homepage cards |
| `FooterLink` (281) · `NavLink` (305) | navigation content |

**The deliberate ABSENCE of FKs into production/expense** is the design:
replicas reference by content, so nothing the street sees couples to the
workshop, and no listing edit can corrupt manufacturing truth. Data
ownership = the boundary made of schema. **Trade-off accepted:** display
copy can drift from factory reality — a HUMAN curation duty (and the
correct side to err on; the alternative couples tiers).

## Editing physics

Replicas: freely editable, truly deletable — no append-only obligations,
because nothing here is EVIDENCE ([append-only](../../concepts/database-design/append-only-tables.md)
teaches the opposite pole; storefront is the contrast that proves the rule).

## Required Knowledge (this page)

- [ ] Evidence vs presentation data → [append-only-tables](../../concepts/database-design/append-only-tables.md)
- [ ] Why decoupling = the boundary → README Mental Model

## Learning Graph

**Before:** README. **After:** [services.md](services.md) → the G2 REQ
(orders will be NEW models here — the ownership law extending).
