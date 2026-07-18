"""ProductSize CRUD service — add / update / archive / reactivate.

YEH FILE KYU HAI?
─────────────────
Per-product size chart (S/M/L ya 1/2/3) ka CRUD yahan se hota hai.
Pehle ye logic seedha view ke andar tha (product_views.ProductSizesEditView.post)
— CLAUDE.md rule #4 violation. Service layer mein hone se:

  1. Har function `@transaction.atomic` se wrap — partial writes impossible
  2. Code regex + duplicate check ek hi jagah (testable)
  3. View patla — sirf POST parse karke service call

PERMISSIONS:
  Sirf Super Admin allowed (ProductSize change Adda flow ko affect karta hai;
  high-impact like Product CRUD).
"""
from __future__ import annotations

import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import ROLE_SUPER_ADMIN, user_has_role
from production.models import Product, ProductSize


# Size code = lowercase letters/digits, optional hyphen. Examples: 's', 'm', 'xl', '2y'.
# Slug-friendly + short — display label alag CharField mein.
_SIZE_CODE_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,15}$')


def _ensure_can_manage(user):
    """Sirf Super Admin ProductSize CRUD kar sakta hai."""
    if not user_has_role(user, {ROLE_SUPER_ADMIN}):
        raise PermissionDenied("Only Super Admin can manage product sizes")


# ── Phase-3 platform convention: Universal size ─────────────────────────────

UNIVERSAL_CODE = 'universal'

# Archive guard hooks (Phase-3 D-3, dependency inversion): other apps append
# callables(size) that raise ValidationError to BLOCK an archive. patterns_ai
# registers its confirmed-designs guard in apps.ready() — production imports
# nothing (ADR-H wall intact).
ARCHIVE_VALIDATORS = []


@transaction.atomic
def ensure_universal_size(product: Product) -> ProductSize:
    """Idempotent platform convention (Phase-3 D-1/D-2): every product
    entering pattern preparation has ≥1 active size — creates, or adopts/
    reactivates, the REAL ProductSize row code='universal'. No user gate:
    convention write, not operator CRUD (callers already role-gated).
    Universal is a NORMAL size everywhere else (owner note #1)."""
    size = ProductSize.objects.filter(product=product,
                                      code=UNIVERSAL_CODE).first()
    if size is None:
        return ProductSize.objects.create(
            product=product, code=UNIVERSAL_CODE, label='Universal',
            display_order=0, is_active=True)
    if not size.is_active:
        size.is_active = True
        size.save(update_fields=['is_active', 'updated_at'])
    return size


def _normalise_code(code: str) -> str:
    code = (code or '').strip().lower()
    if not _SIZE_CODE_RE.match(code):
        raise ValidationError(
            "Size code must be 1-16 chars; a-z, 0-9, and '-' only; cannot start with '-'"
        )
    return code


@transaction.atomic
def add_product_size(
    user, *, product: Product, code: str, label: str, display_order: int = 0,
) -> ProductSize:
    """Naya size row banao. Duplicate code pe ValidationError (service-friendly
    message; DB unique_together violation ki jagah)."""
    _ensure_can_manage(user)
    code = _normalise_code(code)
    label = (label or '').strip()
    if not label:
        raise ValidationError("Size label is required")
    if ProductSize.objects.filter(product=product, code=code).exists():
        raise ValidationError(f"Size '{code}' already exists on this product")
    return ProductSize.objects.create(
        product=product, code=code, label=label[:40],
        display_order=display_order, is_active=True,
    )


@transaction.atomic
def update_product_size(
    user, *, product: Product, size_id: int, label: str, display_order: int = 0,
) -> ProductSize:
    """Existing size ka label / order update karo. code immutable —
    barcodes + breakup rows iss FK pe depend karte hain."""
    _ensure_can_manage(user)
    label = (label or '').strip()
    if not label:
        raise ValidationError("Size label is required")
    try:
        size = ProductSize.objects.get(pk=size_id, product=product)
    except ProductSize.DoesNotExist:
        raise ValidationError("Size not found on this product")
    size.label = label[:40]
    size.display_order = display_order
    size.save(update_fields=['label', 'display_order', 'updated_at'])
    return size


@transaction.atomic
def archive_product_size(user, *, product: Product, size_id: int) -> ProductSize:
    """Soft-archive — is_active=False. Pichle Addas ke FK rows intact rehte hain
    (PROTECT FK barcodes/breakups me)."""
    _ensure_can_manage(user)
    try:
        size = ProductSize.objects.get(pk=size_id, product=product)
    except ProductSize.DoesNotExist:
        raise ValidationError("Size not found on this product")
    # Phase-3 D-3: registered guards may refuse (ValidationError bubbles
    # with the guard's honest message).
    for validator in ARCHIVE_VALIDATORS:
        validator(size)
    size.is_active = False
    size.save(update_fields=['is_active', 'updated_at'])
    return size


@transaction.atomic
def reactivate_product_size(user, *, product: Product, size_id: int) -> ProductSize:
    """Archived size ko phir se active. Code already canonical hai —
    revival pe duplicate check zaroori nahi (unique_together already enforces)."""
    _ensure_can_manage(user)
    try:
        size = ProductSize.objects.get(pk=size_id, product=product)
    except ProductSize.DoesNotExist:
        raise ValidationError("Size not found on this product")
    size.is_active = True
    size.save(update_fields=['is_active', 'updated_at'])
    return size
