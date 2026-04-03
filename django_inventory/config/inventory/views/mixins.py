from django.contrib.auth.mixins import UserPassesTestMixin


class ManagerOrAdminMixin(UserPassesTestMixin):
    """
    Restrict write operations to admin and manager user types.
    Karigars and helpers can view but cannot create/edit/delete.
    """

    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, 'user_type', '') in ('admin', 'manager')
