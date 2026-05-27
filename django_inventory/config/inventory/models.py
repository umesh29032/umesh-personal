"""
Inventory app models — currently scoped to RBAC only.

Production lifecycle (Stage, Batch, BatchType, Machine, ClothRoll, Product,
StockLedger, Vendor, VendorDispatch, Payment, and all join tables) was
removed on 2026-05-19 to reset the flow. New domain models will be added
back as the redesigned flow is built.

RBAC artifacts:
  Role               — named bundle of Django permissions; users get one role.
  SidebarItemRule    — per-menu-item role visibility config (admin-editable).
"""
from django.db import models


class Role(models.Model):
    """
    Named bundle of Django permissions. A User.role points to one Role.
    Superuser bypasses all checks; everyone else is gated by their role's permissions.
    Seeded defaults: Super Admin, Manager, Karigar (see migration data).
    """
    name = models.CharField(max_length=64, unique=True)
    code = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles (admin/manager/karigar) cannot be deleted.",
    )
    permissions = models.ManyToManyField(
        'auth.Permission', blank=True, related_name='inventory_roles',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SidebarItemRule(models.Model):
    """Per-menu-item role visibility, driven by the Sidebar Access Control page.

    `url_name` is the stable identifier (Django URL name) for each sidebar
    entry — matches MenuItem.url_name in permission_service.SIDEBAR. Section
    + label are denormalized for display in the admin page so the table is
    self-contained (no need to walk the in-code SIDEBAR registry).

    Super Admin is hardcoded-always-visible at the service layer — never gated
    here so an admin cannot accidentally lock themselves out.
    """

    url_name = models.CharField(
        max_length=128, unique=True,
        help_text="Django URL name, e.g. 'raw_materials:roll-list'.",
    )
    section = models.CharField(max_length=64, help_text="Display section header.")
    label = models.CharField(max_length=64, help_text="Display label in the sidebar.")
    allowed_roles = models.ManyToManyField(
        Role, blank=True, related_name='visible_sidebar_items',
        help_text="Roles allowed to see this menu item.",
    )
    allowed_skills = models.ManyToManyField(
        'accounts.Skill', blank=True, related_name='visible_sidebar_items',
        help_text="Users with ANY of these skills also see this menu item.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'label']

    def __str__(self):
        return f"{self.section} · {self.label}"
