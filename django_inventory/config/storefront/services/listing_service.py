"""
Storefront listing service — all write operations for FeaturedProduct and Category.

CLAUDE.md rule #4: service layer owns all multi-row writes. Views call services.
Read-only queries (list, detail) go straight in views; writes route through here.
"""
from __future__ import annotations

import logging

from django.db import transaction

from ..models import Category, FeaturedProduct

logger = logging.getLogger(__name__)


class ListingService:

    # ── Category ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_category(*, name: str, **kwargs) -> Category:
        """Create a new storefront category and return it."""
        category = Category.objects.create(name=name, **kwargs)
        logger.info("category.created pk=%d name=%r", category.pk, category.name)
        return category

    @staticmethod
    def update_category(category: Category, **fields) -> Category:
        """Update arbitrary fields on a category and save."""
        for attr, value in fields.items():
            setattr(category, attr, value)
        category.save()
        logger.info("category.updated pk=%d", category.pk)
        return category

    @staticmethod
    def delete_category(category: Category) -> None:
        """Delete a category. Products linked via FK stay (SET_NULL)."""
        pk = category.pk
        category.delete()
        logger.info("category.deleted pk=%d", pk)

    # ── FeaturedProduct ───────────────────────────────────────────────────────

    @staticmethod
    def create_product(*, name: str, price, **kwargs) -> FeaturedProduct:
        """Create a new featured product listing and return it."""
        product = FeaturedProduct.objects.create(name=name, price=price, **kwargs)
        logger.info("product.created pk=%d name=%r", product.pk, product.name)
        return product

    @staticmethod
    def update_product(product: FeaturedProduct, **fields) -> FeaturedProduct:
        """Update arbitrary fields on a product and save."""
        for attr, value in fields.items():
            setattr(product, attr, value)
        product.save()
        logger.info("product.updated pk=%d", product.pk)
        return product

    @staticmethod
    def delete_product(product: FeaturedProduct) -> None:
        """Delete a featured product listing."""
        pk = product.pk
        product.delete()
        logger.info("product.deleted pk=%d", pk)

    @staticmethod
    @transaction.atomic
    def reorder_products(ordered_pks: list[int]) -> None:
        """
        Bulk-update display_order so products appear in `ordered_pks` order.
        Pass a list of PKs in the desired display order.
        """
        for idx, pk in enumerate(ordered_pks):
            FeaturedProduct.objects.filter(pk=pk).update(display_order=idx)
        logger.info("product.reordered count=%d", len(ordered_pks))
