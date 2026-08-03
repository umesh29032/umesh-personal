"""Phase-3 archive guard (owner-approved D-3).

Registered into production's `ARCHIVE_VALIDATORS` from apps.ready() —
dependency inversion: patterns_ai knows about designs, production runs
the loop, the ADR-H wall stays intact (production imports nothing here).
"""
from django.core.exceptions import ValidationError


def _sizes_with_confirmed_designs(product):
    # lazy model import — apps.ready() registers this callable before
    # the model registry is guaranteed warm
    from patterns_ai.models import PieceSizeGeometry
    return set(
        PieceSizeGeometry.objects.filter(
            version__piece__product=product,
            version__status='confirmed',
        ).values_list('size_id', flat=True))


def refuse_archiving_sole_design_size(size):
    """Refuse archiving a size that holds confirmed Pattern Designs while
    NO OTHER active size of the product has any — archiving it would make
    the product's only design set vanish from every surface (owner law:
    never silently destroy designs). Applies to every size — Universal is
    a normal size (owner note #1)."""
    design_size_ids = _sizes_with_confirmed_designs(size.product)
    if size.pk not in design_size_ids:
        return                                   # no designs here — free
    other_active_with_designs = (
        size.product.sizes
        .filter(is_active=True, pk__in=design_size_ids)
        .exclude(pk=size.pk).exists())
    if not other_active_with_designs:
        # TODO (future roadmap, owner-registered — do NOT implement now):
        # "Copy Universal Designs into newly created sizes" — a convenience
        # migration offered at this exact block instead of a hard refusal.
        raise ValidationError(
            f"Cannot archive size '{size.label}' — it holds this product's "
            "only confirmed Pattern Designs. Confirm designs in another "
            "active size first (or add sizes and prepare them), then "
            "archive this one.")
