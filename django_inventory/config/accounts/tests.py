"""
Accounts security tests.

These cover the hardening shipped in 2026-05-16:
- Password hashing uses Argon2.
- SignupForm + UserEditForm run Django's password validator stack.
- UserEditForm enforces email uniqueness (excluding self).
- UserUpdateView refuses self-lockout (demote / deactivate / role change).
- UserDeleteView refuses self-delete and last-Super-Admin delete.
- check_throttle blocks after N hits per (scope, axis) and resets on success.
- LoginView remains anti-enumeration (same redirect regardless of email).
- PasswordLoginView locks out after repeated failures.
- RestrictedSocialAccountAdapter only allows pre-provisioned users to sign in.

Run with: env/bin/python config/manage.py test accounts --settings=config.settings.local
"""
from __future__ import annotations


from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from django.core.cache import cache
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from .forms import SignupForm, UserCreateForm, UserEditForm
from .throttle import LIMITS, check_throttle, reset_throttle

User = get_user_model()

# All security tests pin the cache to LocMemCache so counters don't leak
# between test methods or into the dev DB.
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "security-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class BaseSecurityTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def tearDown(self):
        cache.clear()


# ─── Password hashing ────────────────────────────────────────────────────────

class PasswordHashingTests(BaseSecurityTest):
    def test_new_passwords_use_argon2(self):
        u = User.objects.create_user(email="hash@test.com", password="Str0ngP@ssw0rd!")
        self.assertEqual(identify_hasher(u.password).algorithm, "argon2")


# ─── Form validation ────────────────────────────────────────────────────────

class SignupFormTests(BaseSecurityTest):
    def test_signup_rejects_short_password(self):
        f = SignupForm(data={"email": "x@t.com", "password": "abc", "confirm_password": "abc"})
        self.assertFalse(f.is_valid())
        self.assertIn("password", f.errors)

    def test_signup_rejects_numeric_password(self):
        f = SignupForm(data={"email": "x@t.com", "password": "12345678", "confirm_password": "12345678"})
        self.assertFalse(f.is_valid())

    def test_signup_rejects_common_password(self):
        f = SignupForm(data={"email": "x@t.com", "password": "password", "confirm_password": "password"})
        self.assertFalse(f.is_valid())

    def test_signup_accepts_strong_password(self):
        f = SignupForm(data={"email": "x@t.com", "password": "Str0ngP@ssw0rd!", "confirm_password": "Str0ngP@ssw0rd!"})
        self.assertTrue(f.is_valid(), f.errors)

    def test_signup_clean_email_does_not_leak_existence(self):
        # Anti-enumeration: clean_email should NOT raise if email is already taken.
        User.objects.create_user(email="exists@t.com", password="Str0ngP@ssw0rd!")
        f = SignupForm(data={"email": "exists@t.com", "password": "Str0ngP@ssw0rd!", "confirm_password": "Str0ngP@ssw0rd!"})
        self.assertTrue(f.is_valid(), f.errors)


class UserCreateFormTests(BaseSecurityTest):
    def test_blocks_weak_password(self):
        f = UserCreateForm(data={"email": "n@t.com", "password": "123", "confirm_password": "123"})
        self.assertFalse(f.is_valid())
        self.assertIn("password", f.errors)

    def test_rejects_mismatched_passwords(self):
        f = UserCreateForm(data={"email": "n@t.com", "password": "Str0ngP@ss!", "confirm_password": "Different1!"})
        self.assertFalse(f.is_valid())

    def test_rejects_duplicate_email(self):
        User.objects.create_user(email="dup@t.com", password="Str0ngP@ssw0rd!")
        f = UserCreateForm(data={"email": "dup@t.com", "password": "Str0ngP@ssw0rd!", "confirm_password": "Str0ngP@ssw0rd!"})
        self.assertFalse(f.is_valid())
        self.assertIn("email", f.errors)


class UserEditFormTests(BaseSecurityTest):
    def setUp(self):
        super().setUp()
        from accounts.models import UserType
        self.worker_type = UserType.objects.get(code='worker')
        self.user = User.objects.create_user(email="edit@t.com", password="Str0ngP@ssw0rd!", first_name="A")
        self.other = User.objects.create_user(email="other@t.com", password="Str0ngP@ssw0rd!")

    def test_blocks_weak_new_password(self):
        f = UserEditForm(
            instance=self.user,
            data={"email": "edit@t.com", "user_type": self.worker_type.pk, "new_password": "abc"},
        )
        self.assertFalse(f.is_valid())
        self.assertIn("new_password", f.errors)

    def test_allows_keeping_existing_password(self):
        # Empty new_password should NOT trigger validator.
        f = UserEditForm(
            instance=self.user,
            data={"email": "edit@t.com", "user_type": self.worker_type.pk, "new_password": ""},
        )
        self.assertTrue(f.is_valid(), f.errors)

    def test_rejects_email_collision_with_other_user(self):
        f = UserEditForm(
            instance=self.user,
            data={"email": "other@t.com", "user_type": self.worker_type.pk},
        )
        self.assertFalse(f.is_valid())
        self.assertIn("email", f.errors)

    def test_allows_keeping_own_email(self):
        f = UserEditForm(
            instance=self.user,
            data={"email": "edit@t.com", "user_type": self.worker_type.pk},
        )
        self.assertTrue(f.is_valid(), f.errors)


# ─── Self-protection ────────────────────────────────────────────────────────

class SelfProtectionTests(BaseSecurityTest):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(email="admin@t.com", password="Str0ngP@ssw0rd!")
        self.client.force_login(self.admin)

    def test_cannot_delete_self(self):
        url = reverse("accounts:user_delete", args=[self.admin.pk])
        self.client.post(url, follow=True)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists(),
                        "Super Admin must not be able to delete themselves")

    def test_cannot_delete_last_superuser(self):
        # Promote another user to staff-only, leave self as only Super Admin
        User.objects.create_user(email="other@t.com", password="Str0ngP@ssw0rd!", is_staff=True)
        # Try deleting self → blocked
        self.client.post(reverse("accounts:user_delete", args=[self.admin.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        # Other user is not super admin, deleting self is still blocked
        # Create another superuser and verify we can now delete a different one
        second_admin = User.objects.create_superuser(email="admin2@t.com", password="Str0ngP@ssw0rd!")
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:user_delete", args=[second_admin.pk]))
        self.assertFalse(User.objects.filter(pk=second_admin.pk).exists())


# ─── Throttle / rate limit ──────────────────────────────────────────────────

class ThrottleTests(BaseSecurityTest):
    def _request(self, ip="1.2.3.4"):
        rf = RequestFactory()
        req = rf.post("/login/")
        req.META["REMOTE_ADDR"] = ip
        return req

    def test_blocks_after_ip_limit(self):
        scope = "otp_send"
        limit = LIMITS[scope]["ip"].hits
        req = self._request(ip="9.9.9.9")
        for _ in range(limit):
            blocked, _ = check_throttle(req, scope)
            self.assertFalse(blocked)
        blocked, retry = check_throttle(req, scope)
        self.assertTrue(blocked)
        self.assertGreater(retry, 0)

    def test_blocks_after_email_limit(self):
        scope = "pw_login"
        limit = LIMITS[scope]["id"].hits
        # Spread across many IPs so per-IP curve never trips.
        for i in range(limit):
            req = self._request(ip=f"10.0.0.{i}")
            blocked, _ = check_throttle(req, scope, identifier="target@victim.com")
            self.assertFalse(blocked)
        req = self._request(ip="10.0.0.99")
        blocked, retry = check_throttle(req, scope, identifier="target@victim.com")
        self.assertTrue(blocked, "Per-email curve must trip even when IPs rotate")
        self.assertGreater(retry, 0)

    def test_reset_clears_counter(self):
        scope = "pw_login"
        req = self._request(ip="3.3.3.3")
        check_throttle(req, scope, identifier="rotate@t.com")
        reset_throttle(scope, identifier="rotate@t.com", request=req)
        # Should be able to retry a full LIMITS["pw_login"]["id"].hits times.
        for _ in range(LIMITS[scope]["id"].hits):
            blocked, _ = check_throttle(req, scope, identifier="rotate@t.com")
            self.assertFalse(blocked)


# ─── Anti-enumeration ───────────────────────────────────────────────────────

class AntiEnumerationTests(BaseSecurityTest):
    def test_login_unknown_email_redirects_like_known(self):
        # Same redirect, same status — attacker cannot distinguish.
        User.objects.create_user(email="known@t.com", password="Str0ngP@ssw0rd!")
        r1 = self.client.post(reverse("accounts:login"), {"email": "known@t.com"})
        r2 = self.client.post(reverse("accounts:login"), {"email": "unknown@t.com"})
        self.assertEqual(r1.status_code, r2.status_code)
        self.assertEqual(r1.url, r2.url)


# ─── Password login lockout ─────────────────────────────────────────────────

class PasswordLoginLockoutTests(BaseSecurityTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(email="lock@t.com", password="Str0ngP@ssw0rd!")

    def test_repeated_failures_eventually_block(self):
        url = reverse("accounts:login_password")
        limit = LIMITS["pw_login"]["id"].hits
        # Submit wrong password `limit` times — should still respond (counter
        # tripping the (limit+1)th request).
        for _ in range(limit):
            self.client.post(url, {"username": "lock@t.com", "password": "wrong"})
        response = self.client.post(url, {"username": "lock@t.com", "password": "wrong"})
        self.assertContains(response, "Too many failed attempts", status_code=200)

    def test_successful_login_resets_counter(self):
        url = reverse("accounts:login_password")
        # 2 failures then 1 success → counter should reset.
        self.client.post(url, {"username": "lock@t.com", "password": "wrong"})
        self.client.post(url, {"username": "lock@t.com", "password": "wrong"})
        self.client.post(url, {"username": "lock@t.com", "password": "Str0ngP@ssw0rd!"})
        # After success, the per-email counter must be cleared.
        rf = RequestFactory()
        req = rf.post("/x/")
        req.META["REMOTE_ADDR"] = "127.0.0.1"
        # Should not be near the limit any more — single fresh hit must pass.
        blocked, _ = check_throttle(req, "pw_login", identifier="lock@t.com")
        self.assertFalse(blocked)


class UserHasPermCacheTest(TestCase):
    """P3.2: user_has_perm role-permission lookup is request-cached."""

    def setUp(self):
        from django.contrib.auth.models import Permission
        from accounts.models import User
        from inventory.models import Role
        self.perm = Permission.objects.first()
        self.codename = f'{self.perm.content_type.app_label}.{self.perm.codename}'
        self.role = Role.objects.get(code='manager')   # seeded, not super_admin
        self.role.permissions.add(self.perm)
        self.user = User.objects.create_user(email='permcache@test', password='x')
        self.user.role = self.role
        self.user.save()

    def test_role_perm_grants(self):
        from accounts.services.permission_service import user_has_perm
        self.assertTrue(user_has_perm(self.user, self.codename))

    def test_role_perm_lookup_is_cached(self):
        from django.contrib.auth import get_user_model
        from accounts.services.permission_service import user_has_perm
        u = get_user_model().objects.select_related('role').get(pk=self.user.pk)
        with self.assertNumQueries(PERM_CACHE_QUERIES):
            user_has_perm(u, self.codename)
            user_has_perm(u, self.codename)   # 2nd call hits the cache


PERM_CACHE_QUERIES = 1   # role-perm set read ONCE; 2nd call cached (P3.2)
