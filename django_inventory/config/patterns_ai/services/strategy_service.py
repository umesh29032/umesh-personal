"""strategy_service — SINGLE WRITER for ManufacturingStrategy (M4 §4).

UI name: "Marker Recipe" (R1). A recipe = a saved Marker Plan (fabric
group · lay type · pieces · size mix · intent) — manufacturing
knowledge as data. The resolver output is rows only; the ENGINE never
receives a recipe name (genericity gate).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import ManufacturingStrategy, PatternPiece


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


def _clean(*, product, name, fabric_group, layering_type, piece_ids,
           size_ratio, optimize_intent):
    name = (name or '').strip()
    if not name:
        raise ValidationError('recipe name is required.')
    if fabric_group not in PatternPiece.FabricGroup.values:
        raise ValidationError(f'unknown fabric group: {fabric_group!r}')
    if layering_type not in ManufacturingStrategy.LayeringType.values:
        raise ValidationError(f'unknown layering type: {layering_type!r}')
    if optimize_intent not in ManufacturingStrategy.OptimizeIntent.values:
        raise ValidationError(f'unknown intent: {optimize_intent!r}')
    try:
        piece_ids = sorted({int(p) for p in (piece_ids or [])})
    except (TypeError, ValueError):
        raise ValidationError('piece ids must be numbers.')
    known = set(PatternPiece.objects.filter(
        product=product, pk__in=piece_ids).values_list('pk', flat=True))
    missing = [p for p in piece_ids if p not in known]
    if missing:
        raise ValidationError(f'pieces {missing} are not in this product.')
    ratio = {}
    for k, v in (size_ratio or {}).items():
        try:
            sid, n = int(k), int(v)
        except (TypeError, ValueError):
            raise ValidationError('size ratio must map size ids to counts.')
        if n < 1:
            raise ValidationError('garments-per-size must be ≥ 1.')
        ratio[str(sid)] = n
    if not product.sizes.filter(
            pk__in=[int(s) for s in ratio]).count() == len(ratio):
        raise ValidationError('size ratio contains foreign sizes.')
    return name, piece_ids, ratio


@transaction.atomic
def save_recipe(*, user, product, name, fabric_group,
                layering_type='single', piece_ids=None, size_ratio=None,
                optimize_intent='balanced', notes=''):
    """Create-or-update by (product, name) — saving the same recipe name
    updates it (the factory iterates on its recipes)."""
    _gate(user)
    name, piece_ids, ratio = _clean(
        product=product, name=name, fabric_group=fabric_group,
        layering_type=layering_type, piece_ids=piece_ids,
        size_ratio=size_ratio, optimize_intent=optimize_intent)
    recipe, _created = ManufacturingStrategy.objects.update_or_create(
        product=product, name=name,
        defaults={'fabric_group': fabric_group,
                  'layering_type': layering_type,
                  'piece_ids': piece_ids, 'size_ratio': ratio,
                  'optimize_intent': optimize_intent,
                  'notes': notes or '', 'is_active': True,
                  'created_by': user})
    return recipe


def deactivate_recipe(*, user, recipe):
    _gate(user)
    if recipe.is_active:
        recipe.is_active = False
        recipe.save(update_fields=['is_active', 'updated_at'])
    return recipe


def active_recipes(product):
    """Read helper for the Marker Plan dialog (rows, newest first)."""
    return (ManufacturingStrategy.objects
            .filter(product=product, is_active=True).order_by('-id'))
