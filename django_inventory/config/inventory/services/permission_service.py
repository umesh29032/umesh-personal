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
ROLE_ACCOUNTANT = 'accountant'      # can view + edit Supplier and Cost Per KG on cloth rolls

# Convenience sets
ADMIN_ROLES = {ROLE_SUPER_ADMIN}
MANAGEMENT_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER}
ALL_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_KARIGAR}
STOREFRONT_ROLES = {ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM}

# Production lifecycle: who can touch cloth + Adda + stages.
PRODUCTION_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_KARIGAR}

# Financial fields (Supplier, Cost Per KG): view + edit gated to these roles.
# Super Admin is included so universal-view is preserved by every gate.
FINANCIAL_ROLES = {ROLE_SUPER_ADMIN, ROLE_ACCOUNTANT}


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
    # M2M descriptor only resolves on User instances saved with the real model;
    # tests using bare ORM mocks may expose `extra_roles` as a plain attribute
    # without `.all()`. Guard with AttributeError, not bare except.
    extra_roles_qs = getattr(user, 'extra_roles', None)
    if extra_roles_qs is not None:
        try:
            roles_iter = extra_roles_qs.all()
        except (AttributeError, TypeError):
            roles_iter = ()
        for r in roles_iter:
            if r.code:
                codes.add(r.code)
    return codes


def user_has_role(user, codes: Iterable[str]) -> bool:
    """True if any of the user's roles (primary or extra) is in `codes`."""
    return bool(user_role_codes(user) & set(codes))


def user_can_view_financials(user) -> bool:
    """Gate for reading Supplier + Cost Per KG fields on cloth rolls."""
    return user_has_role(user, FINANCIAL_ROLES)


def user_can_edit_financials(user) -> bool:
    """Gate for writing Supplier + Cost Per KG fields on cloth rolls."""
    return user_has_role(user, FINANCIAL_ROLES)


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
            # Single unified Dashboard entry — same template + content for everyone.
            # Management role → inventory_dashboard URL. Others → user_dashboard URL.
            # Both routes render the same view content; this just keeps URL semantics
            # backward-compatible with existing bookmarks.
            MenuItem('Dashboard', 'inventory:inventory_dashboard',
                     predicate=_any_role(ROLE_SUPER_ADMIN, ROLE_MANAGER),
                     match=('inventory/dashboard',)),
            MenuItem('Dashboard', 'inventory:user_dashboard',
                     predicate=lambda u: u and u.is_authenticated and not user_has_role(u, [ROLE_SUPER_ADMIN, ROLE_MANAGER]),
                     match=('my-dashboard',)),
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
        label='Raw Materials',
        predicate=_any_role(*PRODUCTION_ROLES),
        items=(
            MenuItem('Raw Material Dashboard', 'raw_materials:dashboard', match=('raw-materials/',)),
            MenuItem('Cloth Dashboard', 'raw_materials:cloth-dashboard', match=('raw-materials/cloth/',)),
            MenuItem('Cloth Rolls', 'raw_materials:roll-list', match=('raw-materials/rolls',)),
            MenuItem('Cloth Types', 'raw_materials:cloth-type-list', match=('raw-materials/cloth-types',)),
            MenuItem('Cloth Colors', 'raw_materials:cloth-color-list', match=('raw-materials/cloth-colors',)),
            MenuItem('Storage Locations', 'raw_materials:storage-list', match=('raw-materials/storage-locations',)),
        ),
    ),
    MenuSection(
        label='Production',
        predicate=_any_role(*PRODUCTION_ROLES),
        items=(
            MenuItem('Adda Dashboard', 'production:dashboard', match=('production/',)),
            MenuItem('Addas', 'production:adda-list', match=('production/addas',)),
            MenuItem('Products', 'production:product-list', match=('production/products',)),
        ),
    ),
    MenuSection(
        label='Tracking',
        predicate=_any_role(*PRODUCTION_ROLES),
        items=(
            MenuItem('Barcode Dashboard', 'tracking:dashboard', match=('tracking/',)),
        ),
    ),
    MenuSection(
        label='Administration',
        predicate=_any_role(ROLE_SUPER_ADMIN),
        items=(
            MenuItem('Team Members', 'accounts:user_list', match=('users',)),
            MenuItem('User Skills', 'accounts:skill_list', match=('skills',)),
            MenuItem('Roles & Permissions', 'inventory:role_list', match=('roles',)),
            MenuItem('Stages', 'production:stage-list', match=('stages',)),
            MenuItem('Sidebar Access', 'inventory:sidebar-access', match=('sidebar-access',)),
        ),
    ),
)


def _db_visible_url_names(user) -> set[str] | None:
    """Resolve SidebarItemRule rows into a set of url_names visible to `user`.

    Returns None when the table is empty (no rules seeded yet) — caller should
    fall back to the in-code predicate. Returns a (possibly empty) set when
    DB rules exist, even if the user has no matching rule.

    Super Admin always sees everything — handled at caller.
    """
    if not user or not user.is_authenticated:
        return set()

    # Lazy import — permission_service is imported very early in app startup.
    from inventory.models import SidebarItemRule

    rules = list(
        SidebarItemRule.objects.prefetch_related('allowed_roles', 'allowed_skills').all()
    )
    if not rules:
        return None  # table empty → fall back to hardcoded predicate

    user_role_ids: set[int] = set()
    if getattr(user, 'role_id', None):
        user_role_ids.add(user.role_id)
    user_role_ids.update(user.extra_roles.values_list('id', flat=True))
    user_skill_ids: set[int] = set(user.skills.values_list('id', flat=True))

    visible: set[str] = set()
    for rule in rules:
        allowed_role_ids = set(rule.allowed_roles.values_list('id', flat=True))
        if allowed_role_ids & user_role_ids:
            visible.add(rule.url_name)
            continue
        allowed_skill_ids = set(rule.allowed_skills.values_list('id', flat=True))
        if allowed_skill_ids & user_skill_ids:
            visible.add(rule.url_name)
    return visible


def build_menu_for(user, current_path: str = '') -> list[dict]:
    """
    Return a list of sections with only the items the user may see.
    Each item also gets a resolved URL; unreachable URLs are dropped silently
    so the sidebar never breaks during partial rollouts.

    Visibility precedence per item:
      1. Super Admin → always visible (built-in, never gated).
      2. SidebarItemRule (DB) → if seeded, role overlap decides.
      3. Hardcoded MenuItem.predicate / MenuSection.predicate → final fallback
         when the DB table is empty (e.g., fresh install before migrations).

    Active-tab rule: only ONE item across the whole sidebar is marked
    `is_active=True` — the one whose `match` substring has the longest
    overlap with `current_path`. Avoids the bug where multiple items
    light up simultaneously when their match strings share a prefix.
    """
    visible_sections: list[dict] = []
    all_items: list[dict] = []  # flat list so we can pick a single winner

    is_super_admin = user_has_role(user, {ROLE_SUPER_ADMIN}) if user else False
    db_visible = None if is_super_admin else _db_visible_url_names(user)
    # `db_visible is None` → no DB rules at all, use hardcoded predicate.

    for section in SIDEBAR:
        items: list[dict] = []
        for item in section.items:
            # Skip items that don't resolve (typo, removed URL) — sidebar must
            # never crash on a missing reverse().
            url = item.resolved_url()
            if url is None:
                continue

            # Visibility decision
            if is_super_admin:
                allowed = True
            elif db_visible is not None:
                allowed = item.url_name in db_visible
            else:
                allowed = section.predicate(user) and item.predicate(user)

            if not allowed:
                continue

            entry = {
                'label': item.label,
                'url': url,
                'url_name': item.url_name,
                'match': item.match,
                'is_active': False,
            }
            items.append(entry)
            all_items.append(entry)
        if items:
            visible_sections.append({'label': section.label, 'items': items})

    # Pick the single most-specific match (longest substring that appears in path).
    if current_path:
        best = None
        best_len = 0
        for entry in all_items:
            for m in entry['match']:
                if m and m in current_path and len(m) > best_len:
                    best, best_len = entry, len(m)
        if best is not None:
            best['is_active'] = True

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
