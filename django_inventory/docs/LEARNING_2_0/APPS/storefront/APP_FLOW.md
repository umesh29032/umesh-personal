# storefront — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Public marketing site today; commerce future home (G2). Boundary: ADR-0008/0010 §5 —
> NO production money/quantities here; Order→Adda FK banned (route via G5 stock).
## Flow 1 — Public homepage: config rows (HomePageConfig/Hero/WhyUs/Nav/Footer/
FeaturedProduct/Category) → rendered, no auth.
## Flow 2 — Listing editor: listing_team edits cards/categories (role-gated).
## Flow 3 (FUTURE) — G6 SKU → G5 finished-goods stock → G2 orders/revenue land HERE.

---
*Depth: [config/storefront/README.md](../../../../config/storefront/README.md) (business) ·
[docs/apps/storefront/GUIDE.md](../../../apps/storefront/GUIDE.md) (file-by-file). This = navigation/flow only.*
