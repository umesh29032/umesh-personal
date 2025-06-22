
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
# def admin_required(function=None, login_url='/accounts/login/'):
#     """
#     Decorator for views that checks that the user is logged in and is an admin.
#     """
#     actual_decorator = user_passes_test(
#         lambda u: u.is_authenticated and u.user_type == 'admin',
#         login_url=login_url
#     )
#     if function:
#         return actual_decorator(function)
#     return actual_decorator 


def user_type_required(user_type):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to access this page.")
            if request.user.user_type != user_type:
                return HttpResponseForbidden(f"This page is restricted to {user_type} users only.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Example usage with multiple allowed types
def user_types_required(*user_types):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to access this page.")
            if request.user.user_type not in user_types:
                return HttpResponseForbidden(f"This page is restricted to {', '.join(user_types)} users only.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator