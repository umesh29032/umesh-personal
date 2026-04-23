from django.db import models


class HomePageConfig(models.Model):
    """
    Singleton model — controls the hero section, CTA banner, and global page settings.
    Only the first active row is used; create one row and edit it from admin.
    """

    # ── Hero section ─────────────────────────────────────────────────────────
    hero_badge_text = models.CharField(
        max_length=100, default="New Collection 2024",
        help_text="Small badge above the hero title (e.g. 'New Collection 2024')",
    )
    hero_title_line1 = models.CharField(
        max_length=200, default="Premium Kids",
        help_text="First line of the hero heading",
    )
    hero_title_line2 = models.CharField(
        max_length=200, default="Garments",
        help_text="Second line (shown in copper/italic)",
    )
    hero_description = models.TextField(
        default="Crafted with care for little ones. Explore our range of premium hosiery, "
                "comfortable pants, and vibrant t-shirts — designed for comfort, built to last.",
        help_text="Paragraph below the hero title",
    )
    hero_cta_primary_text = models.CharField(max_length=100, default="Explore Collection")
    hero_cta_primary_link = models.CharField(max_length=200, default="#products")
    hero_cta_secondary_text = models.CharField(max_length=100, default="Manage Inventory")
    hero_cta_secondary_link = models.CharField(
        max_length=200, default="/app/",
        help_text="URL for the secondary button (e.g. login page)",
    )

    # ── Stats strip ──────────────────────────────────────────────────────────
    stat1_value = models.CharField(max_length=20, default="500+")
    stat1_label = models.CharField(max_length=50, default="Products")
    stat2_value = models.CharField(max_length=20, default="50+")
    stat2_label = models.CharField(max_length=50, default="Designs")
    stat3_value = models.CharField(max_length=20, default="1000+")
    stat3_label = models.CharField(max_length=50, default="Happy Customers")

    # ── CTA banner (bottom section) ──────────────────────────────────────────
    cta_title_line1 = models.CharField(max_length=200, default="Ready to")
    cta_title_line2 = models.CharField(
        max_length=200, default="partner with us?",
        help_text="Shown in copper/italic",
    )
    cta_description = models.TextField(
        default="Log in to our inventory management system to track orders, "
                "manage batches, and keep your production running smoothly.",
    )
    cta_primary_text = models.CharField(max_length=100, default="Get Started")
    cta_primary_link = models.CharField(max_length=200, default="/app/")
    cta_secondary_text = models.CharField(max_length=100, default="View Products")
    cta_secondary_link = models.CharField(max_length=200, default="#products")

    # ── Section headings ─────────────────────────────────────────────────────
    categories_tag = models.CharField(max_length=100, default="Our Collection")
    categories_title = models.CharField(max_length=200, default="Shop by Category")
    categories_description = models.TextField(
        default="From everyday essentials to special occasions — we have the perfect garment for every little one.",
        blank=True,
    )
    products_tag = models.CharField(max_length=100, default="Bestsellers")
    products_title = models.CharField(max_length=200, default="Featured Products")
    products_description = models.TextField(
        default="Our most popular garments, loved by parents and kids alike.",
        blank=True,
    )
    whyus_tag = models.CharField(max_length=100, default="Why Kapil Enterprises")
    whyus_title = models.CharField(max_length=200, default="Trusted by Businesses")
    whyus_description = models.TextField(
        default="We combine quality craftsmanship with modern manufacturing to deliver garments that exceed expectations.",
        blank=True,
    )

    # ── Images ───────────────────────────────────────────────────────────────
    hero_background_image = models.ImageField(
        upload_to='storefront/hero/', null=True, blank=True,
        help_text="Optional hero background image. Overlays the gradient.",
    )
    brand_logo = models.ImageField(
        upload_to='storefront/brand/', null=True, blank=True,
        help_text="Brand logo shown in navbar and footer. Falls back to 'KE' monogram.",
    )

    # ── Footer ───────────────────────────────────────────────────────────────
    footer_description = models.TextField(
        default="Premium kids garment manufacturer. Hosiery, pants, t-shirts and more. "
                "Quality craftsmanship trusted by businesses across India.",
    )
    footer_copyright = models.CharField(max_length=200, default="2024 Kapil Enterprises. All rights reserved.")
    footer_tagline = models.CharField(max_length=200, default="Crafted with care in India")

    # ── Meta ─────────────────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homepage Configuration"
        verbose_name_plural = "Homepage Configuration"

    def __str__(self):
        return "Homepage Configuration"

    def save(self, *args, **kwargs):
        # Ensure only one active config exists
        if self.is_active:
            HomePageConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Category(models.Model):
    """Product categories displayed on the homepage grid."""

    name = models.CharField(max_length=100, help_text="e.g. T-Shirts, Pants & Trousers")
    subtitle = models.CharField(
        max_length=200, blank=True,
        help_text="Short description shown below the name (e.g. 'Round neck, V-neck, Polo — all styles')",
    )
    item_count_label = models.CharField(
        max_length=50, default="50+ Items",
        help_text="Badge shown on the card (e.g. '120+ Items')",
    )
    image = models.ImageField(
        upload_to='storefront/categories/', null=True, blank=True,
        help_text="Category image. If uploaded, replaces the SVG icon.",
    )
    icon_svg = models.TextField(
        blank=True,
        help_text="SVG markup for the category icon. Used when no image is uploaded.",
    )
    display_order = models.PositiveIntegerField(default=0, help_text="Lower number = shown first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class FeaturedProduct(models.Model):
    """Products showcased on the homepage."""

    BADGE_CHOICES = [
        ('', 'No Badge'),
        ('new', 'New'),
        ('hot', 'Hot'),
        ('bestseller', 'Bestseller'),
    ]

    name = models.CharField(max_length=255, help_text="e.g. 'Cotton Round Neck Tee — Multicolor Pack'")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
        help_text="Category this product belongs to",
    )
    category_label = models.CharField(
        max_length=100, blank=True,
        help_text="Override label shown above the name (e.g. 'Kids T-Shirt'). Falls back to category name.",
    )
    description = models.TextField(
        blank=True,
        help_text="Short product description (1-2 lines)",
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Current selling price (INR)",
    )
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Original/MRP price for strikethrough display. Leave blank to hide.",
    )
    sizes = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-separated sizes to display (e.g. '2Y,4Y,6Y' or 'S,M,L,XL')",
    )
    badge = models.CharField(
        max_length=20, choices=BADGE_CHOICES, blank=True, default='',
        help_text="Promotional badge shown on the product card",
    )
    image = models.ImageField(
        upload_to='storefront/products/', null=True, blank=True,
        help_text="Product image. If blank, a placeholder icon is shown.",
    )
    icon_svg = models.TextField(
        blank=True,
        help_text="SVG icon shown when no image is uploaded. Leave blank for default.",
    )
    display_order = models.PositiveIntegerField(default=0, help_text="Lower number = shown first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.name

    @property
    def size_list(self):
        """Return sizes as a list for template iteration."""
        if not self.sizes:
            return []
        return [s.strip() for s in self.sizes.split(',') if s.strip()]

    @property
    def display_category(self):
        """Return category_label override or category name."""
        return self.category_label or (self.category.name if self.category else '')

    @property
    def badge_css_class(self):
        """Map badge choice to CSS class."""
        mapping = {
            'new': 'badge-new',
            'hot': 'badge-hot',
            'bestseller': 'badge-bestseller',
        }
        return mapping.get(self.badge, '')


class HeroShowcaseCard(models.Model):
    """Cards displayed in the hero section showcase grid (right side)."""

    title = models.CharField(max_length=100, help_text="e.g. 'Kids T-Shirts'")
    description = models.TextField(help_text="Short description shown on the card")
    price_label = models.CharField(
        max_length=50, blank=True,
        help_text="Price tag text (e.g. 'From ₹149'). Leave blank to hide.",
    )
    image = models.ImageField(
        upload_to='storefront/showcase/', null=True, blank=True,
        help_text="Card image. If uploaded, replaces the SVG icon.",
    )
    icon_svg = models.TextField(
        blank=True,
        help_text="SVG markup for the card icon. Used when no image is uploaded.",
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = "Hero Showcase Card"

    def __str__(self):
        return self.title


class WhyUsCard(models.Model):
    """Feature/benefit cards in the 'Why Choose Us' section."""

    title = models.CharField(max_length=100, help_text="e.g. 'Quality Assured'")
    description = models.TextField(help_text="Explanation of this benefit")
    image = models.ImageField(
        upload_to='storefront/whyus/', null=True, blank=True,
        help_text="Card image/icon. If uploaded, replaces the SVG icon.",
    )
    icon_svg = models.TextField(
        blank=True,
        help_text="SVG markup for the card icon. Used when no image is uploaded.",
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = "Why Us Card"

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    """
    Links in the footer columns.
    Group them by column_name to organize into footer sections.
    """
    COLUMN_CHOICES = [
        ('products', 'Products'),
        ('company', 'Company'),
        ('access', 'Access'),
    ]

    label = models.CharField(max_length=100, help_text="Link text")
    url = models.CharField(max_length=300, help_text="URL or anchor (e.g. '#products' or '/app/')")
    column = models.CharField(max_length=20, choices=COLUMN_CHOICES)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['column', 'display_order']

    def __str__(self):
        return f"{self.get_column_display()} → {self.label}"


class NavLink(models.Model):
    """Navigation links in the top navbar (public pages)."""

    label = models.CharField(max_length=100, help_text="Link text shown in navbar")
    url = models.CharField(max_length=300, help_text="URL or anchor (e.g. '#categories')")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.label
