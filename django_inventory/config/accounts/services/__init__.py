"""accounts service layer.

Brings accounts in line with every other app (CLAUDE.md rule #4): write-side
business logic + security invariants live in services, views stay thin.
"""
from . import auth_service, permission_service, user_service
# RBAC API — accounts is now the home of identity + access control. Other apps
# may keep importing these via the `inventory.services` re-export shim.
from .permission_service import (
    build_menu_for, can_access_url_name, explain_visibility,
    user_has_perm, user_has_role, user_role_code, user_role_codes, user_principal,
    user_can_view_financials, user_can_edit_financials,
    ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER, ROLE_LISTING_TEAM, ROLE_ACCOUNTANT,
    ADMIN_ROLES, MANAGEMENT_ROLES, STOREFRONT_ROLES, PRODUCTION_ROLES, FINANCIAL_ROLES,
    permissions_qs_by_app, permissions_sectioned_for_role_editor,
)

__all__ = [
    'auth_service', 'permission_service', 'user_service',
    'build_menu_for', 'can_access_url_name', 'explain_visibility',
    'user_has_perm', 'user_has_role', 'user_role_code', 'user_role_codes', 'user_principal',
    'user_can_view_financials', 'user_can_edit_financials',
    'ROLE_SUPER_ADMIN', 'ROLE_MANAGER', 'ROLE_WORKER', 'ROLE_LISTING_TEAM', 'ROLE_ACCOUNTANT',
    'ADMIN_ROLES', 'MANAGEMENT_ROLES', 'STOREFRONT_ROLES', 'PRODUCTION_ROLES', 'FINANCIAL_ROLES',
    'permissions_qs_by_app', 'permissions_sectioned_for_role_editor',
]
