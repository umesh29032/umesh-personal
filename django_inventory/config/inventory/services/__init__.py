"""Re-export shim — RBAC relocated to `accounts.services.permission_service` (2026-06).

Existing `from inventory.services import user_has_role, MANAGEMENT_ROLES, ...`
call-sites across the codebase keep working unchanged. New code SHOULD import
from `accounts.services` directly (accounts is the RBAC foundation); this shim
exists so the relocation didn't touch ~38 import sites at once.
"""
from accounts.services.permission_service import (  # noqa: F401
    build_menu_for, can_access_url_name, explain_visibility,
    user_has_perm, user_has_role, user_role_code, user_role_codes, user_principal,
    user_can_view_financials, user_can_edit_financials, user_does_production_work,
    ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER, ROLE_LISTING_TEAM, ROLE_ACCOUNTANT,
    ADMIN_ROLES, MANAGEMENT_ROLES, STOREFRONT_ROLES, PRODUCTION_ROLES, FINANCIAL_ROLES,
    FINANCIAL_READ_ROLES,
    permissions_qs_by_app, permissions_sectioned_for_role_editor,
)

__all__ = [
    'build_menu_for', 'can_access_url_name', 'explain_visibility',
    'user_has_perm', 'user_has_role', 'user_role_code', 'user_role_codes', 'user_principal',
    'user_can_view_financials', 'user_can_edit_financials', 'user_does_production_work',
    'ROLE_SUPER_ADMIN', 'ROLE_MANAGER', 'ROLE_WORKER', 'ROLE_LISTING_TEAM', 'ROLE_ACCOUNTANT',
    'ADMIN_ROLES', 'MANAGEMENT_ROLES', 'STOREFRONT_ROLES', 'PRODUCTION_ROLES', 'FINANCIAL_ROLES',
    'FINANCIAL_READ_ROLES',
    'permissions_qs_by_app', 'permissions_sectioned_for_role_editor',
]
