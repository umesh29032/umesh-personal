from django.contrib import admin
from .models import (
    HomePageConfig, Category, FeaturedProduct,
    HeroShowcaseCard, WhyUsCard, FooterLink, NavLink,
)
from .forms import (
    HomePageConfigForm, CategoryForm, FeaturedProductForm,
    HeroShowcaseCardForm, WhyUsCardForm,
)


# ── Inline for footer links ─────────────────────────────────────────────────

class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1
    fields = ('label', 'url', 'column', 'display_order', 'is_active')


# ── HomePageConfig (Singleton) ───────────────────────────────────────────────

@admin.register(HomePageConfig)
class HomePageConfigAdmin(admin.ModelAdmin):
    form = HomePageConfigForm
    fieldsets = (
        ('Hero Section', {
            'fields': (
                'hero_badge_text',
                ('hero_title_line1', 'hero_title_line2'),
                'hero_description',
                'hero_background_image',
                ('hero_cta_primary_text', 'hero_cta_primary_link'),
                ('hero_cta_secondary_text', 'hero_cta_secondary_link'),
            ),
        }),
        ('Brand', {
            'fields': ('brand_logo',),
            'classes': ('collapse',),
            'description': 'Upload a brand logo for the navbar/footer. Falls back to "KE" monogram if empty.',
        }),
        ('Hero Stats', {
            'fields': (
                ('stat1_value', 'stat1_label'),
                ('stat2_value', 'stat2_label'),
                ('stat3_value', 'stat3_label'),
            ),
        }),
        ('Section Headings', {
            'fields': (
                ('categories_tag', 'categories_title'),
                'categories_description',
                ('products_tag', 'products_title'),
                'products_description',
                ('whyus_tag', 'whyus_title'),
                'whyus_description',
            ),
            'classes': ('collapse',),
        }),
        ('CTA Banner', {
            'fields': (
                ('cta_title_line1', 'cta_title_line2'),
                'cta_description',
                ('cta_primary_text', 'cta_primary_link'),
                ('cta_secondary_text', 'cta_secondary_link'),
            ),
        }),
        ('Footer', {
            'fields': ('footer_description', 'footer_copyright', 'footer_tagline'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    list_display = ('__str__', 'is_active', 'updated_at')

    def has_add_permission(self, request):
        # Allow only one config row
        if HomePageConfig.objects.exists():
            return False
        return super().has_add_permission(request)


# ── Category ─────────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('name', 'subtitle', 'item_count_label', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'subtitle', 'item_count_label', 'image', 'display_order', 'is_active'),
        }),
        ('SVG Icon (fallback)', {
            'fields': ('icon_svg',),
            'classes': ('collapse',),
            'description': 'Paste SVG markup for the category icon. Only used when no image is uploaded.',
        }),
    )


# ── FeaturedProduct ──────────────────────────────────────────────────────────

@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    form = FeaturedProductForm
    list_display = ('name', 'display_category', 'price', 'original_price', 'badge', 'display_order', 'is_active')
    list_editable = ('price', 'badge', 'display_order', 'is_active')
    list_filter = ('badge', 'is_active', 'category')
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'category_label', 'description'),
        }),
        ('Pricing', {
            'fields': (('price', 'original_price'),),
        }),
        ('Display', {
            'fields': ('sizes', 'badge', 'image', 'display_order', 'is_active'),
        }),
        ('Icon (when no image)', {
            'fields': ('icon_svg',),
            'classes': ('collapse',),
        }),
    )

    def display_category(self, obj):
        return obj.display_category
    display_category.short_description = 'Category'


# ── HeroShowcaseCard ─────────────────────────────────────────────────────────

@admin.register(HeroShowcaseCard)
class HeroShowcaseCardAdmin(admin.ModelAdmin):
    form = HeroShowcaseCardForm
    list_display = ('title', 'price_label', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'price_label', 'image', 'display_order', 'is_active'),
        }),
        ('SVG Icon (fallback)', {
            'fields': ('icon_svg',),
            'classes': ('collapse',),
        }),
    )


# ── WhyUsCard ────────────────────────────────────────────────────────────────

@admin.register(WhyUsCard)
class WhyUsCardAdmin(admin.ModelAdmin):
    form = WhyUsCardForm
    list_display = ('title', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image', 'display_order', 'is_active'),
        }),
        ('SVG Icon (fallback)', {
            'fields': ('icon_svg',),
            'classes': ('collapse',),
        }),
    )


# ── FooterLink ───────────────────────────────────────────────────────────────

@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'column', 'display_order', 'is_active')
    list_editable = ('url', 'display_order', 'is_active')
    list_filter = ('column', 'is_active')


# ── NavLink ──────────────────────────────────────────────────────────────────

@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'display_order', 'is_active')
    list_editable = ('url', 'display_order', 'is_active')
