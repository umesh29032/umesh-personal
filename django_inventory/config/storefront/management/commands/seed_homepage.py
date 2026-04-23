"""
Seed the homepage with initial content.
Run: python manage.py seed_homepage
Safe to re-run — skips if data already exists.
"""
from django.core.management.base import BaseCommand

from storefront.models import (
    HomePageConfig, Category, FeaturedProduct,
    HeroShowcaseCard, WhyUsCard, FooterLink, NavLink,
)


# ── SVG Icons ────────────────────────────────────────────────────────────────

SVG_TSHIRT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"/></svg>'

SVG_PANTS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2h12l-1.5 5H7.5L6 2zM7.5 7h9v13a2 2 0 01-2 2h-5a2 2 0 01-2-2V7z"/><path d="M10 12h4"/></svg>'

SVG_HOSIERY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2a4 4 0 014 4v1H8V6a4 4 0 014-4zM8 7h8l1 15H7L8 7z"/><path d="M10 11v4M14 11v4"/></svg>'

SVG_SETS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="1.5" fill="currentColor"/><circle cx="16" cy="12" r="1.5" fill="currentColor"/><circle cx="10" cy="18" r="1.5" fill="currentColor"/></svg>'

SVG_SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>'

SVG_CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>'

SVG_PEOPLE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>'


class Command(BaseCommand):
    help = 'Seed homepage with initial storefront data'

    def handle(self, *args, **options):
        if HomePageConfig.objects.exists():
            self.stdout.write(self.style.WARNING('Homepage data already exists. Skipping seed.'))
            return

        self.stdout.write('Seeding homepage data...')

        # ── HomePageConfig (singleton) ───────────────────────────────
        HomePageConfig.objects.create(is_active=True)
        self.stdout.write('  + HomePageConfig')

        # ── Nav Links ────────────────────────────────────────────────
        nav_data = [
            ('Categories', '#categories', 1),
            ('Products', '#products', 2),
            ('About', '#why-us', 3),
        ]
        for label, url, order in nav_data:
            NavLink.objects.create(label=label, url=url, display_order=order)
        self.stdout.write(f'  + {len(nav_data)} NavLinks')

        # ── Categories ───────────────────────────────────────────────
        cat_data = [
            ('T-Shirts', 'Round neck, V-neck, Polo — all styles', '120+ Items', SVG_TSHIRT, 1),
            ('Pants & Trousers', 'Joggers, Cargo, Track pants & more', '85+ Items', SVG_PANTS, 2),
            ('Hosiery', 'Innerwear, vests, thermals & socks', '200+ Items', SVG_HOSIERY, 3),
            ('Sets & Combos', 'Co-ord sets, loungewear, gift packs', '50+ Items', SVG_SETS, 4),
        ]
        cats = {}
        for name, subtitle, count, svg, order in cat_data:
            cats[name] = Category.objects.create(
                name=name, subtitle=subtitle, item_count_label=count,
                icon_svg=svg, display_order=order,
            )
        self.stdout.write(f'  + {len(cat_data)} Categories')

        # ── Hero Showcase Cards ──────────────────────────────────────
        showcase_data = [
            ('Kids T-Shirts', 'Vibrant colors, soft cotton blends. Sizes 2Y to 14Y available in 24+ designs.', 'From \u20b9149', SVG_TSHIRT, 1),
            ('Hosiery', 'Premium knitted comfort wear for all seasons.', 'From \u20b999', SVG_HOSIERY, 2),
            ('Kids Pants', 'Durable, flexible pants for active kids.', 'From \u20b9199', SVG_PANTS, 3),
        ]
        for title, desc, price, svg, order in showcase_data:
            HeroShowcaseCard.objects.create(
                title=title, description=desc, price_label=price,
                icon_svg=svg, display_order=order,
            )
        self.stdout.write(f'  + {len(showcase_data)} HeroShowcaseCards')

        # ── Featured Products ────────────────────────────────────────
        product_data = [
            ('Cotton Round Neck Tee — Multicolor Pack', 'T-Shirts', 'Kids T-Shirt',
             '100% cotton, pre-shrunk, vibrant prints that last 50+ washes',
             249, 399, '2Y,4Y,6Y', 'bestseller', SVG_TSHIRT, 1),
            ('Elastic Waist Jogger — Navy Blue', 'Pants & Trousers', 'Kids Pants',
             'Stretchable cotton blend, side pockets, reinforced knees',
             349, 549, '4Y,6Y,8Y', 'hot', SVG_PANTS, 2),
            ('Premium Cotton Vest — 3 Pack White', 'Hosiery', 'Hosiery',
             'Breathable hosiery fabric, soft seams, machine washable',
             199, 299, '2Y,4Y,6Y', 'new', SVG_HOSIERY, 3),
            ('Polo Collar Tee — Striped Collection', 'T-Shirts', 'Kids T-Shirt',
             'Premium pique cotton, button placket, embroidered logo',
             399, 599, '6Y,8Y,10Y', 'bestseller', SVG_TSHIRT, 4),
            ('Cargo Pants — Olive Green', 'Pants & Trousers', 'Kids Pants',
             '6-pocket utility style, adjustable waist, durable twill',
             449, 699, '6Y,8Y,12Y', 'new', SVG_PANTS, 5),
            ('Thermal Inner Set — Winter Essential', 'Hosiery', 'Hosiery',
             'Warm fleece-lined hosiery, soft elastic, anti-pilling',
             349, 499, '4Y,6Y,8Y', 'hot', SVG_HOSIERY, 6),
            ('Graphic Print Tee — Superhero Edition', 'T-Shirts', 'Kids T-Shirt',
             'Bio-washed cotton, fade-resistant prints, fun character designs',
             299, 449, '4Y,6Y,8Y', 'bestseller', SVG_TSHIRT, 7),
            ('Track Pants — Dry-Fit Sports', 'Pants & Trousers', 'Kids Pants',
             'Quick-dry polyester, zippered pockets, reflective stripes',
             299, 449, '6Y,10Y,14Y', 'new', SVG_PANTS, 8),
        ]
        for name, cat_name, cat_label, desc, price, orig, sizes, badge, svg, order in product_data:
            FeaturedProduct.objects.create(
                name=name, category=cats.get(cat_name), category_label=cat_label,
                description=desc, price=price, original_price=orig,
                sizes=sizes, badge=badge, icon_svg=svg, display_order=order,
            )
        self.stdout.write(f'  + {len(product_data)} FeaturedProducts')

        # ── Why Us Cards ─────────────────────────────────────────────
        why_data = [
            ('Quality Assured',
             'Every garment passes through 5-point quality checks before dispatch. Premium fabrics, strong stitching, lasting colors.',
             SVG_SHIELD, 1),
            ('Fast Production',
             'Our streamlined manufacturing process ensures quick turnaround — from order placement to dispatch in record time.',
             SVG_CLOCK, 2),
            ('Bulk Orders Welcome',
             'Whether you need 100 pieces or 10,000 — we have the capacity, infrastructure and supply chain to deliver at scale.',
             SVG_PEOPLE, 3),
        ]
        for title, desc, svg, order in why_data:
            WhyUsCard.objects.create(
                title=title, description=desc, icon_svg=svg, display_order=order,
            )
        self.stdout.write(f'  + {len(why_data)} WhyUsCards')

        # ── Footer Links ─────────────────────────────────────────────
        footer_data = [
            ('T-Shirts', '#products', 'products', 1),
            ('Pants & Trousers', '#products', 'products', 2),
            ('Hosiery', '#products', 'products', 3),
            ('Sets & Combos', '#products', 'products', 4),
            ('About Us', '#why-us', 'company', 1),
            ('Quality Policy', '#why-us', 'company', 2),
            ('Collections', '#categories', 'company', 3),
            ('Sign In', '/app/', 'access', 1),
            ('Create Account', '/app/signup/', 'access', 2),
            ('Inventory Dashboard', '/app/', 'access', 3),
        ]
        for label, url, col, order in footer_data:
            FooterLink.objects.create(
                label=label, url=url, column=col, display_order=order,
            )
        self.stdout.write(f'  + {len(footer_data)} FooterLinks')

        self.stdout.write(self.style.SUCCESS('\nHomepage seeded successfully!'))
        self.stdout.write('Go to /admin/ to edit any content.')
