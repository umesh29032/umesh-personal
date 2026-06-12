# `storefront` app — Public Marketing Site (commerce's future home)

> Dual-register guide. Boundary law: [ADR-0008](../../docs/adr/0008-commerce-manufacturing-boundary.md)
> + [ADR-0010 §5](../../docs/adr/0010-growth-and-identity-policy.md).

## Purpose & business responsibility

Aaj: public homepage + catalog DISPLAY (marketing). Kal (G6→G5→G2): orders,
revenue, customers — the commerce side of the boundary. **Owns: presentation
+ (future) revenue. NEVER owns production data.**

## Models (all display-config today)

| Model | Business | Note |
|---|---|---|
| `HomePageConfig`, `HeroShowcaseCard`, `WhyUsCard`, `FooterLink`, `NavLink` | homepage sections | singleton-ish config rows |
| `Category` | public catalog grouping | display-only |
| `FeaturedProduct` | a showcased product CARD | **free text — deliberately NO FK to production.Product.** G6 will introduce the SKU entity that finally links sellable identity to the factory triple (product,color,size) |

## What records are written & by whom

`listing` views (listing_team role) write display rows via storefront
services (`master_service`, `image_service` — croppable images). No money,
no production writes, none ever (boundary).

## How data flows / why / what breaks

```
listing_team edits cards → public pages render → (future) SKU (G6) →
FinishedGood stock (G5) → Orders/revenue (G2) — Order↔Adda ONLY via stock,
NEVER a direct FK (locked).
```
**What breaks if bypassed:** a price field on production.Product or an
Order→Adda FK quietly couples revenue into manufacturing — the exact failure
ADR-0008 exists to prevent. Any such PR contradicts an accepted ADR.

## Common mistakes

1. No production imports beyond read-only display needs.
2. No price/revenue fields outside this app — ever.
3. Don't "quick-link" FeaturedProduct to production.Product — that's G6's
   SKU entity, designed properly, not a hotfix FK.

## Django Learning Notes

- **Image handling** (`image_service`, croppable widget): uploads processed
  server-side; templates stay dumb.
- **Config-as-rows**: homepage layout DB-driven — owner edits without deploys.

## Real factory example

Owner homepage pe "Cotton Round Neck Tee — Multicolor" card lagata hai
(photo + badge 'Bestseller'). Factory mein wahi product `1-6` code se banta
hai — aaj dono ka rishta sirf naam mein hai; G6 ke baad SKU unhe officially
jodega, tab stock + orders aa payenge.
