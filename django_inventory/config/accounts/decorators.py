from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse


def login_required_view(view_func):
    """
    Custom login-required decorator for views.
    Redirects unauthenticated users to login page.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("accounts:login"))
        return view_func(request, *args, **kwargs)

    return wrapper
