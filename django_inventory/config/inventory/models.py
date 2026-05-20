"""
Inventory app models — currently scoped to RBAC only.

Production lifecycle (Stage, Batch, BatchType, Machine, ClothRoll, Product,
StockLedger, Vendor, VendorDispatch, Payment, and all join tables) was
removed on 2026-05-19 to reset the flow. New domain models will be added
back as the redesigned flow is built.
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
