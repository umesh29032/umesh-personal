"""Template context processors for the inventory app."""
from .services import build_menu_for, user_role_code


def sidebar(request):
    """
    Inject the permission-filtered sidebar menu + the active user's role code
    into every template. The base layout iterates `sidebar_menu` to render nav.
    """
    user = getattr(request, 'user', None)
    return {
        'sidebar_menu': build_menu_for(user) if user and user.is_authenticated else [],
        'current_role_code': user_role_code(user),
    }
