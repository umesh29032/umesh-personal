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
ROLE_WORKER = 'worker'      # renamed from 'karigar' 2026-06-02 (inventory 0019)
ROLE_LISTING_TEAM = 'listing_team'  # can manage storefront product/category listings
ROLE_ACCOUNTANT = 'accountant'      # can view + edit Supplier and Cost Per KG on cloth rolls

# Convenience sets
ADMIN_ROLES = {ROLE_SUPER_ADMIN}
MANAGEMENT_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER}
STOREFRONT_ROLES = {ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM}

# Production lifecycle: who can touch cloth + Adda + stages.
PRODUCTION_ROLES = {ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER}

# Financial fields (Supplier, Cost Per KG): view + edit gated to these roles.
# Super Admin is included so universal-view is preserved by every gate.
FINANCIAL_ROLES = {ROLE_SUPER_ADMIN, ROLE_ACCOUNTANT}

# Owner ruling 2026-08-02 — THE ACCOUNTANT READ TIER.
# Before this, every financial page was `_ManagementOnly` (read AND write behind one
# gate), so a pure `accountant` login had NO reachable page: their FINANCIAL_ROLES
# capability (supplier + cost-per-kg) was unreachable dead code, and their dashboard
# showed WORKER copy. RBAC.md previously recorded "pure accountant: dispatch-blocked
# from rm pages BY DESIGN"; that decision is now superseded by owner ruling.
#
# The split that makes it safe: READS widen to this set, WRITES do not move.
# Settlement finalize / advances / pay-basis / FnF / void / template edits all stay
# management-or-super-admin, at BOTH the view mixin and the service layer — so even
# if a view were mis-gated, `settlement_service`/`expense_service` still refuse.
# Settlement remains the single money-write boundary, untouched.
FINANCIAL_READ_ROLES = MANAGEMENT_ROLES | {ROLE_ACCOUNTANT}


# ── Permission helpers ──────────────────────────────────────────────────────

def user_role_code(user) -> str | None:
    """Return the user's access role code.

    Only two things grant access:
      1. is_superuser → ROLE_SUPER_ADMIN (always wins)
      2. user.role FK → role.code

    UserType does NOT grant access — it is display/classification only (a
    role-less user gets no privileged role, no matter their type). This is the
    architecture rule: "Role grants access, never User Type." A user with no
    Role can log in and see the Dashboard, nothing more.
    """
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return ROLE_SUPER_ADMIN
    role = getattr(user, 'role', None)
    if role:
        return role.code
    return None


def user_role_codes(user) -> set[str]:
    """
    Return ALL role codes for a user — primary role + any extra_roles.
    Use this when checking access that can be granted via either path.

    REQUEST-CACHED (2026-08-02), same pattern as `user_principal` and
    `_role_perm_codenames` in this module. Every `user_has_role()` call funnels
    through here, and each one was firing a fresh `extra_roles` M2M query — so a
    page doing a dozen role checks paid a dozen queries for an answer that cannot
    change mid-request. The perf baselines caught this the moment one more caller
    was added (`user_does_production_work`), which is exactly what they are for.
    """
    cached = getattr(user, '_rbac_role_codes', None)
    if cached is not None:
        return cached

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
    try:
        user._rbac_role_codes = codes
    except (AttributeError, TypeError):
        pass  # bare-ORM mock users in tests — just skip caching
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


def user_does_production_work(user) -> bool:
    """Does this person actually do work on the factory floor?

    WHY (owner feedback 2026-08-02): the app only knew two kinds of person —
    management (`MANAGEMENT_ROLES`) and "everyone else", who got the WORKER
    experience. So an `accountant` login landed on a worker dashboard telling them
    *"Jab manager aapko kaam dega"* and a "My Earnings" page reading
    *"Pieces Produced 0"*. An accountant never produces pieces.

    True when ANY of these hold:
      • holds the `worker` role (primary or extra), or
      • has at least one production **skill** (skill = stage access, so a skill
        means they are meant to open a stage), or
      • already has money on the books (a settled/expected earning row).

    The last clause exists so this can only ever *reveal* a money page, never
    hide one from somebody who has wages to see. Ordering matters: the first two
    checks read the request-cached principal (0 queries) and only a genuine
    non-worker pays the single EXISTS.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    # Request-cached: both the sidebar predicate and the dashboard context ask
    # this, and only the answer's *first* computation may cost a query.
    cached = getattr(user, '_rbac_floor_work', None)
    if cached is not None:
        return cached

    answer = False
    if user_has_role(user, {ROLE_WORKER}):
        answer = True
    elif user_principal(user)['skill_ids']:
        answer = True
    else:
        # Lazy import: permission_service is imported very early in app startup,
        # and accounts must not depend on a domain app at module level
        # (core/tests.py FoundationPurityTests enforces that direction).
        try:
            from expense.models import WorkerLedgerEntry
            answer = WorkerLedgerEntry.objects.filter(worker=user).exists()
        except Exception:  # pragma: no cover - DB not ready (migrate/collectstatic)
            answer = False
    try:
        user._rbac_floor_work = answer
    except (AttributeError, TypeError):
        pass  # bare-ORM mock users in tests
    return answer


def _role_perm_codenames(user) -> set[str]:
    """Request-cached set of the user's ROLE permission codenames (P3.2).

    `user_has_perm` runs many times per request (every perm-gated view/action);
    the role's permission set doesn't change mid-request, so compute it once and
    stash it on the request-scoped user instance — same pattern as `user_principal`.
    Tolerates anonymous / mock users (returns an empty set, skips the cache)."""
    cached = getattr(user, '_rbac_perm_codes', None)
    if cached is not None:
        return cached
    codes: set[str] = set()
    role = getattr(user, 'role', None)
    if role is not None:
        codes = set(role.permissions.values_list('codename', flat=True))
    try:
        user._rbac_perm_codes = codes
    except (AttributeError, TypeError):
        pass  # bare-ORM mock users in tests — just skip caching
    return codes


def user_has_perm(user, perm_codename: str) -> bool:
    """User ke paas given Django permission hai ya nahi.

    perm_codename format: 'app_label.codename' (e.g. 'production.change_stage').

    CHECK ORDER (sabse strong se shuru):
      1. Authenticated? Nahi to False.
      2. is_superuser? True → grant all (Django built-in).
      3. user.role.code == 'super_admin'? → grant all (project rule).
         WHY: Super Admin role roles + perms manage karta hai. Agar usko
         har perm tick karna pade to bootstrap problem.
      4. user ke role me yeh codename hai? → True
      5. Django default has_perm (groups + direct perms) → fallback

    PROJECT CONVENTION: views perm-check ke liye is helper ko call kare,
    raw user.is_superuser nahi (CLAUDE.md rule #6).
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Super Admin role implicit bypass — role-perm matrix mein har checkbox
    # tick karne ki zaroorat nahi.
    role = getattr(user, 'role', None)
    if role and role.code == ROLE_SUPER_ADMIN:
        return True
    # perm_codename "app.codename" format hai. Hum codename part match karte
    # hain (DB column codename store karta hai without app prefix).
    if perm_codename.split('.')[-1] in _role_perm_codenames(user):
        return True
    # Django default check — groups + user_permissions M2M.
    return user.has_perm(perm_codename)


def user_principal(user) -> dict:
    """Resolve + request-cache the user's RBAC identity: {role_ids, skill_ids}.

    The user's roles/skills don't change within a single request, but the sidebar
    build, the URL access-check, and SidebarAccessMiddleware each need them — so
    we compute the id-sets ONCE and stash them on the user instance (which is
    request-scoped). This is the single source of "who is this user, RBAC-wise",
    so stage access + sidebar + middleware all agree.

    Tolerates anonymous users and bare-ORM mock users (tests) by returning
    empty sets and skipping the cache when the attribute can't be set.
    """
    cached = getattr(user, '_rbac_principal', None)
    if cached is not None:
        return cached

    role_ids: set[int] = set()
    skill_ids: set[int] = set()
    if user and getattr(user, 'is_authenticated', False):
        if getattr(user, 'role_id', None):
            role_ids.add(user.role_id)
        extra = getattr(user, 'extra_roles', None)
        if extra is not None:
            try:
                role_ids.update(extra.values_list('id', flat=True))
            except (AttributeError, TypeError):
                pass
        skills = getattr(user, 'skills', None)
        if skills is not None:
            try:
                skill_ids.update(skills.values_list('id', flat=True))
            except (AttributeError, TypeError):
                pass

    principal = {'role_ids': role_ids, 'skill_ids': skill_ids}
    try:
        user._rbac_principal = principal
    except (AttributeError, TypeError):
        pass  # immutable / mock user — fine, just don't cache
    return principal


# ── Menu registry ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MenuItem:
    label: str
    url_name: str                     # Django URL name, e.g. 'inventory:batch_list'
    icon: str = ''                    # SVG markup (raw) — kept in template for clarity
    predicate: Callable[[object], bool] = lambda u: True
    match: tuple[str, ...] = ()       # path substrings that mark this item 'active'
    hidden: bool = False              # F-1: registry-only entry — NEVER rendered
                                      # (for anyone, incl. super admin). Keeps a
                                      # legacy url_name valid for SidebarItemRule
                                      # rows until the owner deletes them.

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


def _any_perm(*codenames):
    """Sidebar predicate factory — agar user ke paas in mein se KOI BHI
    perm ho to MenuItem visible.

    Usage in SIDEBAR registry:
        MenuItem('Stages', 'production:stage-list',
                 predicate=_any_perm('production.view_stage',
                                     'production.change_stage'))

    Super Admin bypass aur role-perm lookup `user_has_perm` ke andar hai —
    yeh factory just multiple perms ko OR karta hai.
    """
    return lambda user: any(user_has_perm(user, c) for c in codenames)


# Sidebar definition. Order here is the order the user sees.
SIDEBAR: tuple[MenuSection, ...] = (
    MenuSection(
        label='Main',
        items=(
            # Personal "My Dashboard" — ONE item, ONE live URL for every role
            # (F-1 polish 2026-07-05; the old role-split URL twins now redirect
            # here). Ungated on purpose, like My Earnings: it's the personal
            # landing every authenticated user must always reach. Labelled
            # "My Dashboard" to disambiguate from the management "Operations"
            # landing in the Production section (P1-1 sidebar dedupe / C-3).
            MenuItem('My Dashboard', 'inventory:my_dashboard',
                     match=('my-dashboard', 'inventory/dashboard')),
            # Phase-15 BOD (owner charter D1.5: a PRIMARY navigation item;
            # v1 Owner/SA only — code predicate; the owner may additionally
            # manage it via a SidebarItemRule row through Access Control).
            # String url_name only — no import of bod (layering stays clean).
            MenuItem('Business Operating Dashboard', 'bod:dashboard',
                     predicate=_any_role(ROLE_SUPER_ADMIN), match=('bod',)),
            # Registry-only legacy twins (hidden=True → never rendered): the
            # url_names stay valid so existing SidebarItemRule rows aren't
            # orphaned (P3.4 drift guard). Both URLs 301 to my_dashboard.
            # Owner may delete their rules via Sidebar Access, then remove these.
            MenuItem('My Dashboard', 'inventory:inventory_dashboard',
                     hidden=True, match=()),
            MenuItem('My Dashboard', 'inventory:user_dashboard',
                     hidden=True, match=()),
            # AUDIT-2 F-B: `production:my-work` ("My Assigned Work") kept a live
            # SidebarItemRule row after the F-1 dedupe dropped its menu item, so
            # the P3.4 drift guard failed. The URL itself still WORKS and is
            # still gated by that rule (workers 200 · listing/accountant 302), so
            # deleting the rule would REMOVE gating — the wrong repair. Registry-
            # only (renders for nobody) restores the invariant with zero
            # behaviour change; workers reach their bundles from My Dashboard's
            # "Report needed" links. OWNER CHOICE if you'd rather have the page
            # navigable: drop `hidden=True` and move this entry into Main.
            MenuItem('My Assigned Work', 'production:my-work',
                     hidden=True, match=()),
            # Every worker's own earnings page lives in Main, NOT the Payroll
            # section — workers never see the management payroll tools. Ungated
            # on purpose (self-scoped view): payroll is critical, no role gate.
            # Learning: the course reader. Ungated like My Dashboard/My Earnings —
            # it is educational content with no business data, and the owner
            # intends to open it more widely later (kos local-testing-environment).
            MenuItem('Learn', 'learning:index', match=('learn',)),
            # Owner feedback 2026-08-02: an accountant/listing_team/student saw
            # this and got a WORKER page ("Pieces Produced 0"). Show it to people
            # who actually do floor work OR already have money on the books — the
            # predicate can only reveal, never hide wages from someone who has them.
            MenuItem('My Earnings', 'expense:my-earnings', match=('expense/my',),
                     predicate=user_does_production_work),
        ),
    ),
    # P1-2 (C-2): the core manufacturing flow is the primary operational area, so
    # Production sits directly below Main, with Raw Materials production-adjacent;
    # Storefront (secondary e-commerce) moves below them. ORDER-ONLY change —
    # section/item contents, predicates, url_names + labels are untouched, so
    # permissions / SidebarItemRule visibility / URLs / routes are unchanged.
    MenuSection(
        label='Production',
        predicate=_any_role(*PRODUCTION_ROLES),
        items=(
            MenuItem('Operations', 'production:dashboard', match=('production/',)),
            # R10-A: the machine register (assets + operator windows) — ops,
            # management-only (frozen architecture rule 6).
            MenuItem('Machines', 'machines:list', match=('machines/',),
                     predicate=_any_role(*MANAGEMENT_ROLES)),
            # P1 Block 1: AI Pattern Intelligence landing (patterns_ai app) —
            # management-only; same wiring class as the machines entry above.
            MenuItem('Pattern Intelligence', 'patterns_ai:home', match=('patterns/',),
                     predicate=_any_role(*MANAGEMENT_ROLES)),
            MenuItem('Manufacturing Costing', 'production:costing', match=('production/costing',),
                     predicate=_any_role(*MANAGEMENT_ROLES)),
            MenuItem('Addas', 'production:adda-list', match=('production/addas',)),
            MenuItem('Products', 'production:product-list', match=('production/products',),
                     predicate=_any_role(*MANAGEMENT_ROLES)),
            MenuItem('Product Patterns', 'production:pattern-list', match=('production/patterns',),
                     predicate=_any_perm('production.view_productpattern', 'production.change_productpattern')),
        ),
    ),
    MenuSection(
        label='Raw Materials',
        # Accountant included (owner ruling 2026-08-02): their FINANCIAL_ROLES
        # capability — view + edit Supplier and Cost Per KG — is DEFINED on cloth
        # rolls, so without section access that capability was dead code. They get
        # the roll list only; every other item keeps the production-floor gate.
        predicate=_any_role(*(PRODUCTION_ROLES | {ROLE_ACCOUNTANT})),
        items=(
            MenuItem('Raw Material Dashboard', 'raw_materials:dashboard', match=('raw-materials/',),
                     predicate=_any_role(*PRODUCTION_ROLES)),
            MenuItem('Cloth Dashboard', 'raw_materials:cloth-dashboard', match=('raw-materials/cloth/',),
                     predicate=_any_role(*PRODUCTION_ROLES)),
            MenuItem('Cloth Rolls', 'raw_materials:roll-list', match=('raw-materials/rolls',),
                     predicate=_any_role(*(PRODUCTION_ROLES | {ROLE_ACCOUNTANT}))),
            MenuItem('Cloth Types', 'raw_materials:cloth-type-list', match=('raw-materials/cloth-types',)),
            MenuItem('Cloth Colors', 'raw_materials:cloth-color-list', match=('raw-materials/cloth-colors',)),
            MenuItem('Storage Locations', 'raw_materials:storage-list', match=('raw-materials/storage-locations',)),
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
        label='Tracking',
        predicate=_any_role(*PRODUCTION_ROLES),
        items=(
            MenuItem('Barcode Dashboard', 'tracking:dashboard', match=('tracking/',)),
        ),
    ),
    MenuSection(
        label='Payroll & Accounts',
        # Management + ACCOUNTANT (owner ruling 2026-08-02). Workers never see it —
        # their self-service "My Earnings" lives under Main instead.
        #
        # READ items widen to FINANCIAL_READ_ROLES so an accountant has a job to do;
        # WRITE items stay MANAGEMENT_ROLES. The section predicate must be the WIDER
        # set or the whole section would vanish for an accountant before its items
        # were ever consulted.
        predicate=_any_role(*FINANCIAL_READ_ROLES),
        items=(
            # ── reads: the accountant's actual work ──────────────────────────
            MenuItem('Payroll', 'expense:payroll-overview', match=('expense/payroll',),
                     predicate=_any_role(*FINANCIAL_READ_ROLES)),
            # V2-2: the earning+recovery event screens (settlement ≠ payment).
            # Read-only for an accountant: STARTING/finalizing a settlement is a
            # separate management-gated URL, not this list.
            MenuItem('Adda Settlements', 'expense:adda-settlement-list',
                     match=('expense/settlements',),
                     predicate=_any_role(*FINANCIAL_READ_ROLES)),
            # R5 (PDD §21 / ADR-0011): factory-level running costs (incl.
            # monthly salaries) — a cost record, never a ledger.
            MenuItem('Factory Expenses', 'expense:factory-expense-list',
                     match=('expense/expenses',),
                     predicate=_any_role(*FINANCIAL_READ_ROLES)),
            # MEE-C (Phase 16): recurring templates + monthly generation.
            # Accountants READ the schedule; changing a template amount stays
            # super-admin-only INSIDE expense_service, not just here.
            MenuItem('Recurring Expenses', 'expense:expense-template-list',
                     match=('expense/templates', 'expense/generate'),
                     predicate=_any_role(*FINANCIAL_READ_ROLES)),
            # Material spend (cloth ₹/kg) — previously reachable by URL only, with
            # NO menu entry anywhere. It is the accountant's core report, so it
            # finally gets one.
            MenuItem('Material Spend', 'expense:material-spend',
                     match=('expense/material-spend',),
                     predicate=_any_role(*FINANCIAL_READ_ROLES)),
            # ── writes: unchanged, management only ───────────────────────────
            MenuItem('Record Advance', 'expense:advance-add', match=('expense/advances',),
                     predicate=_any_role(*MANAGEMENT_ROLES)),
        ),
    ),
    MenuSection(
        label='Administration',
        # Section visible to Super Admin OR anyone holding a stage-management perm
        # (delegated via the Role editor) — they need the Stages entry to land here.
        # Per-item predicates still gate individual links.
        predicate=lambda u: (
            user_has_role(u, {ROLE_SUPER_ADMIN})
            or user_has_perm(u, 'production.view_stage')
            or user_has_perm(u, 'production.change_stage')
        ),
        items=(
            MenuItem('Access Control', 'inventory:access-control', match=('inventory/access',),
                     predicate=_any_role(ROLE_SUPER_ADMIN)),
            MenuItem('Team Members', 'accounts:user_list', match=('users',),
                     predicate=_any_role(ROLE_SUPER_ADMIN)),
            MenuItem('User Skills', 'accounts:skill_list', match=('skills',),
                     predicate=_any_role(ROLE_SUPER_ADMIN)),
            MenuItem('Roles & Permissions', 'inventory:role_list', match=('roles',),
                     predicate=_any_role(ROLE_SUPER_ADMIN)),
            MenuItem('Stages', 'production:stage-list', match=('stages',),
                     predicate=_any_perm('production.view_stage', 'production.change_stage')),
            MenuItem('Sidebar Access', 'inventory:sidebar-access', match=('sidebar-access',),
                     predicate=_any_role(ROLE_SUPER_ADMIN)),
        ),
    ),
)


def _db_visible_url_names(user) -> tuple[set[str], set[str]] | None:
    """Resolve SidebarItemRule rows for `user`.

    Returns a `(visible, managed)` tuple where `managed` is every url_name that
    has a DB rule (the set of items the Sidebar Access page governs) and
    `visible` is the subset this user's roles/skills may see. Returns None when
    the table is empty (fresh install before the seed migration) so the caller
    falls back to the in-code predicate.

    Items NOT in `managed` (new features added to SIDEBAR after the table was
    seeded, or perm-gated items the role/skill table can't express) must fall
    back to the in-code predicate at the caller — otherwise a brand-new menu
    item is silently invisible to every non-super-admin until someone hand-adds
    a row. The DB acts as an override for the items it knows about, not a
    blanket whitelist.

    Super Admin always sees everything — handled at caller.
    """
    if not user or not user.is_authenticated:
        return (set(), set())

    # Lazy import — permission_service is imported very early in app startup.
    from accounts.models import SidebarItemRule

    rules = list(
        SidebarItemRule.objects.prefetch_related('allowed_roles', 'allowed_skills').all()
    )
    if not rules:
        return None  # table empty → fall back to hardcoded predicate

    principal = user_principal(user)
    user_role_ids = principal['role_ids']
    user_skill_ids = principal['skill_ids']

    visible: set[str] = set()
    managed: set[str] = set()
    for rule in rules:
        managed.add(rule.url_name)
        # `.all()` reads the prefetch_related cache (0 extra queries). Using
        # `.values_list()` here would IGNORE the prefetch and fire a fresh query
        # PER rule — the N+1 that made every page render ~50+ RBAC queries.
        if {r.id for r in rule.allowed_roles.all()} & user_role_ids:
            visible.add(rule.url_name)
            continue
        if {s.id for s in rule.allowed_skills.all()} & user_skill_ids:
            visible.add(rule.url_name)
    return (visible, managed)


def build_menu_for(user, current_path: str = '') -> list[dict]:
    """
    Return a list of sections with only the items the user may see.
    Each item also gets a resolved URL; unreachable URLs are dropped silently
    so the sidebar never breaks during partial rollouts.

    Visibility precedence per item:
      1. Super Admin → always visible (built-in, never gated).
      2. SidebarItemRule (DB) → if a rule exists FOR THIS ITEM, role overlap decides.
      3. Hardcoded MenuItem.predicate / MenuSection.predicate → fallback when the
         DB table is empty (fresh install) OR the item has no DB rule yet (new
         feature / perm-gated item). Prevents new menu items from being silently
         invisible to non-super-admins before someone seeds a rule.

    Active-tab rule: only ONE item across the whole sidebar is marked
    `is_active=True` — the one whose `match` substring has the longest
    overlap with `current_path`. Avoids the bug where multiple items
    light up simultaneously when their match strings share a prefix.
    """
    visible_sections: list[dict] = []
    all_items: list[dict] = []  # flat list so we can pick a single winner

    is_super_admin = user_has_role(user, {ROLE_SUPER_ADMIN}) if user else False
    db_rules = None if is_super_admin else _db_visible_url_names(user)
    # `db_rules is None` → table empty, use hardcoded predicate for every item.
    # Otherwise db_rules = (visible, managed): managed items obey the DB set,
    # un-managed items (no rule yet) fall back to the in-code predicate.
    db_visible = db_rules[0] if db_rules is not None else None
    db_managed = db_rules[1] if db_rules is not None else None

    for section in SIDEBAR:
        items: list[dict] = []
        for item in section.items:
            # Registry-only entries (F-1 legacy twins) render for NOBODY —
            # checked BEFORE the super-admin bypass on purpose.
            if item.hidden:
                continue
            # Skip items that don't resolve (typo, removed URL) — sidebar must
            # never crash on a missing reverse().
            url = item.resolved_url()
            if url is None:
                continue

            # Visibility decision
            if is_super_admin:
                allowed = True
            elif db_managed is not None and item.url_name in db_managed:
                # The Sidebar Access page governs this item → DB set decides.
                allowed = item.url_name in db_visible
            else:
                # Empty table, or a new/perm-gated item with no rule yet →
                # honour the in-code predicate so it is never silently hidden.
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


def can_access_url_name(user, url_name: str) -> bool:
    """Can `user` open the page registered under `url_name`? Uses the SAME rule
    the sidebar uses (SidebarItemRule), so removing access in the Access-Control
    page blocks the URL too — not just the menu link (SidebarAccessMiddleware).

      • anonymous          → True  (let LoginRequired handle the redirect)
      • Super Admin        → True  (always)
      • item HAS a DB rule → role overlap OR skill overlap decides
      • item has NO rule   → True  (unmanaged — not governed by the panel; the
                                     view's own mixin gates it = defense in depth)
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return True
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return True

    from accounts.models import SidebarItemRule
    rule = SidebarItemRule.objects.filter(url_name=url_name).first()
    if rule is None:
        return True

    # Reuse the request-cached principal (this runs in middleware for both the
    # target URL and the referer on every request — don't re-query the user's
    # roles/skills each time).
    principal = user_principal(user)
    if {r.id for r in rule.allowed_roles.all()} & principal['role_ids']:
        return True
    if {s.id for s in rule.allowed_skills.all()} & principal['skill_ids']:
        return True
    return False


def explain_visibility(user, url_name: str) -> str:
    """Diagnostic: explain WHY `user` can / can't see the item under `url_name`.

    Mirrors the same 3-layer precedence as build_menu_for / can_access_url_name
    (super-admin bypass → DB SidebarItemRule → in-code predicate fallback), so
    "why can't X see Y?" is a one-call answer instead of a manual trace through
    the code predicate + the DB rule + the middleware. Surface on the Access hub.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return f"'{url_name}': hidden — anonymous (login required)."
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return f"'{url_name}': visible — Super Admin sees everything (built-in bypass)."

    from accounts.models import SidebarItemRule
    rule = SidebarItemRule.objects.filter(url_name=url_name).first()
    if rule is None:
        return (
            f"'{url_name}': no SidebarItemRule row (unmanaged) — NOT governed by "
            f"the Access Control panel; falls back to the in-code menu predicate "
            f"and the view's own permission mixin."
        )
    principal = user_principal(user)
    rule_role_ids = {r.id for r in rule.allowed_roles.all()}
    rule_skill_ids = {s.id for s in rule.allowed_skills.all()}
    if rule_role_ids & principal['role_ids']:
        return f"'{url_name}': visible — DB rule role overlap (user role ∈ {sorted(rule_role_ids)})."
    if rule_skill_ids & principal['skill_ids']:
        return f"'{url_name}': visible — DB rule skill overlap (user skill ∈ {sorted(rule_skill_ids)})."
    return (
        f"'{url_name}': hidden — a SidebarItemRule exists but the user matches "
        f"none of its roles {sorted(rule_role_ids)} or skills {sorted(rule_skill_ids)}."
    )


# ── View-layer helpers ──────────────────────────────────────────────────────

# ── Role Editor Sections (CURATED) ──────────────────────────────────────────
# YEH STRUCTURE KYU HAI?
# Default Django role editor 80+ perms ka noise dikha deta tha (har model
# ka view/add/change/delete). Admin overwhelmed ho jata tha. Yahan hum
# manually 5 logical sections curate karte hain — sirf un models ko
# expose karte hain jo non-developer admin grant kare.
#
# Hide kiye gaye models (service-only writes):
#   AddaStageRecord, LayeringRollEntry, LayeringRecord, CuttingPatternRecord,
#   CuttingPatternPhoto, CuttingRecord, RemainingClothOfClothRoll,
#   ProductPatternAssignment, *History tables
#
# Each section tuple: (label, description, [(app_label, model), ...])
ROLE_EDITOR_SECTIONS: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        'Production Flow',
        'Products, stages, workflows, and live Adda batches.',
        (
            ('production', 'product'),
            ('production', 'productpattern'),
            ('production', 'stage'),
            ('production', 'workflowstage'),
            ('production', 'adda'),
        ),
    ),
    (
        'Raw Materials',
        'Cloth inventory + master data (types, colors, storage).',
        (
            ('raw_materials', 'clothroll'),
            ('raw_materials', 'clothtype'),
            ('raw_materials', 'clothcolor'),
            ('raw_materials', 'storagelocation'),
        ),
    ),
    (
        'Tracking',
        'Per-piece barcodes generated after cutting.',
        (
            ('tracking', 'batchbarcode'),
        ),
    ),
    (
        'Storefront',
        'Public homepage content — categories, hero cards, featured products.',
        (
            ('storefront', 'homepageconfig'),
            ('storefront', 'category'),
            ('storefront', 'featuredproduct'),
            ('storefront', 'heroshowcasecard'),
            ('storefront', 'whyuscard'),
            ('storefront', 'footerlink'),
            ('storefront', 'navlink'),
        ),
    ),
    (
        'Administration',
        'Roles, sidebar visibility rules, and reusable Skills.',
        (
            ('accounts', 'role'),
            ('accounts', 'sidebaritemrule'),
            ('accounts', 'skill'),
        ),
    ),
)

# Flattened (app_label, model) allowlist derived from the section map.
ROLE_EDITABLE_CONTENT_TYPES: frozenset[tuple[str, str]] = frozenset(
    ct for _, _, cts in ROLE_EDITOR_SECTIONS for ct in cts
)
# Distinct app labels used by the editor — kept for backward compat callers.
ROLE_EDITABLE_APPS: tuple[str, ...] = tuple(
    sorted({app for app, _ in ROLE_EDITABLE_CONTENT_TYPES})
)
# Legacy alias — earlier code referenced an excluded set. Empty now because
# the allowlist above is positive. Kept so existing imports don't break.
ROLE_EDITABLE_MODELS_EXCLUDED: frozenset[tuple[str, str]] = frozenset()


def permissions_qs_by_app(app_labels: tuple[str, ...] = ROLE_EDITABLE_APPS):
    """Role editor perm list — restricted to curated content types.

    Reads ROLE_EDITOR_SECTIONS to decide which perms surface. Internal models
    (history tables, stage records, join tables) stay invisible because they're
    only ever written by services. `app_labels` is honored as a final narrowing
    filter for callers that want a subset.
    """
    qs = (
        Permission.objects
        .filter(content_type__app_label__in=app_labels)
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )
    return [
        p for p in qs
        if (p.content_type.app_label, p.content_type.model)
        in ROLE_EDITABLE_CONTENT_TYPES
    ]


def permissions_sectioned_for_role_editor():
    """Return [(section_label, section_desc, [(model_label, [perm, ...]), ...]), ...].

    Drives the role-edit form's section-by-section layout. Each inner tuple is
    a model with its 4 standard CRUD perms (view/add/change/delete) — sorted so
    the UI is predictable.
    """
    perms = list(permissions_qs_by_app())
    by_ct: dict[tuple[str, str], list] = {}
    for p in perms:
        by_ct.setdefault((p.content_type.app_label, p.content_type.model), []).append(p)
    # Sort each model's perms in conventional CRUD order.
    crud_order = {'view': 0, 'add': 1, 'change': 2, 'delete': 3}
    for k in by_ct:
        by_ct[k].sort(key=lambda p: (crud_order.get(p.codename.split('_', 1)[0], 9), p.codename))

    sections = []
    for label, desc, cts in ROLE_EDITOR_SECTIONS:
        models = []
        for app, model in cts:
            plist = by_ct.get((app, model), [])
            if not plist:
                continue
            # Friendly model label — first matching perm's content_type.name
            # ("cloth roll" → "Cloth Roll").
            model_label = plist[0].content_type.name.title()
            models.append((model_label, plist))
        if models:
            sections.append((label, desc, models))
    return sections
