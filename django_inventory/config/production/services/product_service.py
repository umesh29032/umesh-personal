"""Product service — create / update / archive + code normalisation.

YEH FILE KYU HAI?
─────────────────
Factory products (T-SHIRT, NIKKAR, etc) ka CRUD yahan se hota hai.
Sirf Super Admin allowed — naya product banana rare aur high-impact event hai
(workflow stages bhi seed karne padte hain).

Code format kyun important?
──────────────────────────
Adda codes = '{PRODUCT.code}-001' format follow karte hain. Agar code change ho jaaye
to existing Adda codes orphan ho jaate hain. Isliye edit pe `code` field FORM
mein locked rehta hai.
"""
import re

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.services import ROLE_SUPER_ADMIN, user_has_role
from production.models import Product


# Code regex: uppercase letters/digits/hyphens, 2-30 chars, start+end alphanumeric.
# Example valid: 'T-SHIRT', 'NIKKAR', '1-6', '3-PATTI'
# Example invalid: '-PROD', 'PROD-', 'pro d' (lowercase/space)
_CODE_RE = re.compile(r'^[A-Z0-9][A-Z0-9-]{0,28}[A-Z0-9]$')


def _ensure_can_manage(user):
    """Sirf Super Admin product CRUD kar sakta hai — high-impact change.

    (Workflow already seeded hai. Naye product ke liye usually data migration
    likhna padega — wo task production manager nahi karta.)
    """
    if not user_has_role(user, [ROLE_SUPER_ADMIN]):
        # Local import — circular avoid karne ke liye (Django ka standard pattern)
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only Super Admin can manage products")


def _normalise_code(code: str) -> str:
    """User input ko canonical form mein laata hai — uppercase + hyphen separator.

    'T shirt' → 'T-SHIRT' (space → hyphen, lowercase → upper)
    Regex mismatch pe ValidationError throw karta hai.
    """
    code = (code or '').strip().upper().replace(' ', '-')
    if not _CODE_RE.match(code):
        raise ValidationError("Product code must be 2-30 chars; A-Z, 0-9, and '-' only; cannot start/end with '-'")
    return code


@transaction.atomic
def create_product(user, *, code: str, name: str, description: str = '') -> Product:
    """Naya Product banata hai. Note: workflow stages alag se seed karne padenge."""
    _ensure_can_manage(user)
    code = _normalise_code(code)
    # Duplicate check — unique constraint bhi DB level pe hai, but service-side
    # message friendlier hai (IntegrityError ki jagah ValidationError)
    if Product.objects.filter(code=code).exists():
        raise ValidationError(f"Product code '{code}' already exists")
    p = Product.objects.create(code=code, name=name, description=description)
    # History log — tracking app lazy-imported (production pe ulta depend karta hai)
    from tracking.services import log_product
    from tracking.models import ProductHistory
    log_product(p, ProductHistory.ChangeType.CREATED, user, new_value=p.code)
    return p


@transaction.atomic
def update_product(user, product: Product, *, name: str, description: str = '') -> Product:
    """Product ka name/description update karta hai. Code change NAHI hota — Adda codes
    stable rakhne ke liye form pe `code` field disabled rehti hai."""
    _ensure_can_manage(user)
    old_name = product.name
    product.name = name
    product.description = description
    product.save(update_fields=['name', 'description'])
    from tracking.services import log_product
    from tracking.models import ProductHistory
    # Field-level history — kya badla wo bhi record (audit-friendly)
    log_product(product, ProductHistory.ChangeType.UPDATED, user,
                field_name='name', old_value=old_name, new_value=name)
    return product


@transaction.atomic
def archive_product(user, product: Product) -> Product:
    """Soft-delete — is_active=False. Existing Addas intact rehte hain."""
    _ensure_can_manage(user)
    product.is_active = False
    product.save(update_fields=['is_active'])
    from tracking.services import log_product
    from tracking.models import ProductHistory
    log_product(product, ProductHistory.ChangeType.ARCHIVED, user, new_value='archived')
    return product
