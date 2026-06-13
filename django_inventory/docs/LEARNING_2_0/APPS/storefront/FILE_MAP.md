# storefront — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — display-config rows: HomePageConfig, Category, **FeaturedProduct**
(FREE TEXT — deliberately NO FK to production.Product; G6 SKU will link),
HeroShowcaseCard, WhyUsCard, FooterLink, NavLink.
## services/ — master_service (listing CRUD), image_service (croppable image pipeline).
## views/ — public_views (no-auth homepage), listing_views (listing_team editor).
## processors.py, widgets.py, forms.py — image widget machinery.
## management/commands/seed_homepage.py — seed homepage config. admin.py — 7 admins.
## templates/storefront/{listing,widgets}/ — editor + croppable image widget.
## Junior note: everything here SAVES display config only (what the public sees).
The LAW: no price/revenue field on production models, no Order→Adda FK — ever.

---
*Depth: [config/storefront/README.md](../../../../config/storefront/README.md) (business) ·
[docs/apps/storefront/GUIDE.md](../../../apps/storefront/GUIDE.md) (file-by-file). This = navigation/flow only.*
