"""
Custom decorators for accounts views.

`login_required_view` is the function-based equivalent of Django's
`LoginRequiredMixin`. The class-based views in views.py use the mixin;
this decorator is here for any standalone function-based views.

Note: most views in this project use CBVs + LoginRequiredMixin, so this
decorator is currently unused — kept for completeness in case FBVs are added.
"""
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse


def login_required_view(view_func):
    """Redirects unauthenticated users to the OTP login page."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("accounts:login"))
        return view_func(request, *args, **kwargs)
    return wrapper
