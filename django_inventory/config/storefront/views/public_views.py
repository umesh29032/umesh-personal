from django.shortcuts import render

from ..models import (
    HomePageConfig, Category, FeaturedProduct,
    HeroShowcaseCard, WhyUsCard, FooterLink, NavLink,
)

# Default SVGs used when no custom icon is provided
DEFAULT_TSHIRT_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"/></svg>'

DEFAULT_CATEGORY_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'

DEFAULT_SHIELD_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>'


def public_home(request):
    """
    Public homepage — no login required.
    Queries all storefront models and renders the dynamic homepage.
    Falls back to sensible defaults if no data exists yet.
    """
    config = HomePageConfig.objects.filter(is_active=True).first()
    categories = Category.objects.filter(is_active=True)
    products = FeaturedProduct.objects.filter(is_active=True).select_related('category')
    showcase_cards = HeroShowcaseCard.objects.filter(is_active=True)
    why_cards = WhyUsCard.objects.filter(is_active=True)
    nav_links = NavLink.objects.filter(is_active=True)

    # Group footer links by column — single query, group in Python
    footer_links: dict[str, list] = {'products': [], 'company': [], 'access': []}
    for link in FooterLink.objects.filter(is_active=True):
        footer_links.setdefault(link.column, []).append(link)

    # Provide default SVGs for items missing custom icons
    for card in showcase_cards:
        if not card.icon_svg:
            card.icon_svg = DEFAULT_TSHIRT_SVG
    for cat in categories:
        if not cat.icon_svg:
            cat.icon_svg = DEFAULT_CATEGORY_SVG
    for card in why_cards:
        if not card.icon_svg:
            card.icon_svg = DEFAULT_SHIELD_SVG
    for product in products:
        if not product.icon_svg and not product.image:
            product.icon_svg = DEFAULT_TSHIRT_SVG

    context = {
        'config': config,
        'categories': categories,
        'products': products,
        'showcase_cards': showcase_cards,
        'why_cards': why_cards,
        'nav_links': nav_links,
        'footer_links': footer_links,
    }
    return render(request, 'public_home.html', context)
