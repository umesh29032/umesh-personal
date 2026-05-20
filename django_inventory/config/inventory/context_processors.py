"""
Template context processors — values injected into every render() call.

Registered in settings.TEMPLATES['OPTIONS']['context_processors']. Whatever
this function returns is merged into the template context for every view,
so the base layout can read {{ sidebar_menu }} without each view passing it.
"""
from .services import build_menu_for, user_role_code


def sidebar(request):
    """
    Inject the permission-filtered sidebar menu + the active user's role code
    into every template. The base layout iterates `sidebar_menu` to render nav.
    """
    user = getattr(request, 'user', None)
    return {
        'sidebar_menu': build_menu_for(user, request.path) if user and user.is_authenticated else [],
        'current_role_code': user_role_code(user),
    }
