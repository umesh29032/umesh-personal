"""
RBAC + sidebar menu registry.

Three layers:
1. Role objects (DB)      — bundles of Django Permissions assigned per user.
2. Permission constants   — stable codenames referenced by views / menu items.
3. Menu registry          — declarative sidebar, filtered per user at render time.

Superuser bypasses every check. Everyone else is gated by their Role's
permissions + a few hard-coded role-code rules for legacy `user_type`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from django.contrib.auth.models import Permission
from django.urls import NoReverseMatch, reverse


# ── Role codes (must match the seed migrations) ──────────────────────────────
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_MANAGER = 'manager'
ROLE_KARIGAR = 'karigar'
ROLE_LISTING_TEAM = 'listing_team'  # can manage storefront product/category listings

# Convenience sets
ADMIN_ROLES = {ROLE_SUPER_ADMIN}
MANAGEMENT_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER}
ALL_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_KARIGAR}
STOREFRONT_ROLES = {ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM}


# ── Permission helpers ──────────────────────────────────────────────────────

def user_role_code(user) -> str | None:
    """Return the user's primary Role.code, falling back to the legacy user_type field."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return ROLE_SUPER_ADMIN
    role = getattr(user, 'role', None)
    if role:
        return role.code
    legacy = getattr(user, 'user_type', None)
    # 'normal' intentionally maps to None — no privileged role. Such users can
    # log in and see Dashboard only; nothing else in the sidebar resolves.
    legacy_map = {'admin': ROLE_SUPER_ADMIN, 'manager': ROLE_MANAGER, 'karigar': ROLE_KARIGAR, 'helper': ROLE_KARIGAR, 'normal': None}
    return legacy_map.get(legacy)


def user_role_codes(user) -> set[str]:
    """
    Return ALL role codes for a user — primary role + any extra_roles.
    Use this when checking access that can be granted via either path.
    """
    codes: set[str] = set()
    primary = user_role_code(user)
    if primary:
        codes.add(primary)
    # extra_roles is a M2M; only available on the real User model (not in tests
    # that use the ORM directly), so guard with getattr.
    extra_roles_qs = getattr(user, 'extra_roles', None)
    if extra_roles_qs is not None:
        try:
            for r in extra_roles_qs.all():
                if r.code:
                    codes.add(r.code)
        except Exception:
            pass
    return codes


def user_has_role(user, codes: Iterable[str]) -> bool:
    """True if any of the user's roles (primary or extra) is in `codes`."""
    return bool(user_role_codes(user) & set(codes))


def user_has_perm(user, perm_codename: str) -> bool:
    """
    Check a Django-style permission. Looks at:
      - superuser flag
      - user's Role.permissions
      - Django's built-in user.has_perm (groups / direct perms)
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    if role and role.permissions.filter(codename=perm_codename.split('.')[-1]).exists():
        return True
    return user.has_perm(perm_codename)


# ── Menu registry ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MenuItem:
    label: str
    url_name: str                     # Django URL name, e.g. 'inventory:batch_list'
    icon: str = ''                    # SVG markup (raw) — kept in template for clarity
    predicate: Callable[[object], bool] = lambda u: True
    match: tuple[str, ...] = ()       # path substrings that mark this item 'active'

    def resolved_url(self) -> str | None:
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return None


@dataclass(frozen=True)
class MenuSection:
    label: str
    items: tuple[MenuItem, ...] = field(default_factory=tuple)
    predicate: Callable[[object], bool] = lambda u: True


def _any_role(*codes):
    return lambda user: user_has_role(user, codes)


# Sidebar definition. Order here is the order the user sees.
SIDEBAR: tuple[MenuSection, ...] = (
    MenuSection(
        label='Main',
        items=(
            MenuItem('Dashboard', 'inventory:inventory_dashboard', match=('dashboard',)),
            MenuItem('My Work', 'inventory:my_work', predicate=_any_role(ROLE_KARIGAR), match=('my-work',)),
            MenuItem('Production Batches', 'inventory:batch_list',
                     predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER), match=('batches',)),
        ),
    ),
    MenuSection(
        label='Inventory',
        predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER),
        items=(
            MenuItem('Products', 'inventory:product_list',
                     predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER), match=('products',)),
            MenuItem('Cloth Stock', 'inventory:cloth_roll_list',
                     predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER), match=('cloth',)),
        ),
    ),
    MenuSection(
        label='Production',
        predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER),
        items=(
            MenuItem('Batch Types', 'inventory:batch_type_list', match=('batch-types',)),
            MenuItem('Stages', 'inventory:stage_list', match=('stages',)),
            MenuItem('Machines', 'inventory:machine_list', match=('machines',)),
        ),
    ),
    MenuSection(
        label='Logistics & Finance',
        predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER),
        items=(
            MenuItem('Vendors', 'inventory:vendor_list', match=('vendors',)),
            MenuItem('Dispatches', 'inventory:dispatch_list', match=('dispatches',)),
            MenuItem('Payments', 'inventory:payment_list',
                     predicate=_any_role(ROLE_SUPER_ADMIN), match=('payments',)),
        ),
    ),
    MenuSection(
        label='Storefront',
        predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM),
        items=(
            MenuItem('Featured Products', 'storefront:product_list', match=('storefront/products',)),
            MenuItem('Categories', 'storefront:category_list', match=('storefront/categories',)),
        ),
    ),
    MenuSection(
        label='Administration',
        predicate=_any_role(ROLE_SUPER_ADMIN),
        items=(
            MenuItem('Team Members', 'accounts:user_list', match=('users',)),
            MenuItem('User Skills', 'accounts:skill_list', match=('skills',)),
            MenuItem('Roles & Permissions', 'inventory:role_list', match=('roles',)),
        ),
    ),
)


def build_menu_for(user) -> list[dict]:
    """
    Return a list of sections with only the items the user may see.
    Each item also gets a resolved URL; unreachable URLs are dropped silently
    so the sidebar never breaks during partial rollouts.
    """
    visible_sections: list[dict] = []
    for section in SIDEBAR:
        if not section.predicate(user):
            continue
        items: list[dict] = []
        for item in section.items:
            if not item.predicate(user):
                continue
            url = item.resolved_url()
            if url is None:
                continue
            items.append({
                'label': item.label,
                'url': url,
                'url_name': item.url_name,
                'match': item.match,
            })
        if items:
            visible_sections.append({'label': section.label, 'items': items})
    return visible_sections


# ── View-layer helpers ──────────────────────────────────────────────────────

def permissions_qs_by_app(app_labels: tuple[str, ...] = ('inventory', 'accounts')):
    """For the role editor — list permissions grouped by app / model."""
    return (
        Permission.objects
        .filter(content_type__app_label__in=app_labels)
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )
