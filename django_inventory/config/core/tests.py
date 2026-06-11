"""Architecture guardrail tests — enforce dependency DIRECTION so the acyclic
layering established in the 2026-06 RBAC-relocation remediation can't silently rot.

Lightweight (stdlib `ast`, no extra dependency). For the full layered contract see
`.importlinter` at the repo root (`pip install import-linter && lint-imports`).

Rule enforced: the FOUNDATION apps (core, accounts) must not import higher/domain
apps at MODULE level. (Lazy imports inside functions are allowed — they don't form
an import-load cycle — but should stay rare.)
"""
import ast
import pathlib

from django.test import Client, SimpleTestCase, TestCase

CONFIG_DIR = pathlib.Path(__file__).resolve().parent.parent  # .../config
DOMAIN_APPS = {
    'production', 'tracking', 'expense', 'inventory', 'storefront', 'raw_materials',
}


def _module_level_import_roots(py_path: pathlib.Path) -> set[str]:
    """Top-level package names imported at MODULE scope (not inside functions)."""
    tree = ast.parse(py_path.read_text(), filename=str(py_path))
    roots: set[str] = set()
    for node in tree.body:  # only module-level statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split('.')[0])
    return roots


def _offenders(app: str, forbidden: set[str]) -> dict[str, list[str]]:
    app_dir = CONFIG_DIR / app
    out: dict[str, list[str]] = {}
    for py in app_dir.rglob('*.py'):
        if 'migrations' in py.parts or py.name == 'tests.py' or 'tests' in py.parts:
            continue
        bad = _module_level_import_roots(py) & forbidden
        if bad:
            out[str(py.relative_to(CONFIG_DIR))] = sorted(bad)
    return out


class FoundationPurityTests(SimpleTestCase):
    def test_accounts_does_not_import_domain_apps_at_module_level(self):
        offenders = _offenders('accounts', DOMAIN_APPS)
        self.assertEqual(
            offenders, {},
            f"accounts is the identity+RBAC foundation — it must not import "
            f"domain apps at module level. Use a lazy import if truly needed. "
            f"Offenders: {offenders}",
        )

    def test_core_imports_no_app_code(self):
        offenders = _offenders('core', DOMAIN_APPS | {'accounts', 'inventory'})
        self.assertEqual(
            offenders, {},
            f"core is the shared kernel — it must depend on nothing app-specific. "
            f"Offenders: {offenders}",
        )


REPO_ROOT = CONFIG_DIR.parent  # .../django_inventory


class DocAccuracyTests(SimpleTestCase):
    """P6.1 doc-accuracy guard — the source-of-truth docs can't silently re-drift.

    Asserts only MACHINE-CHECKABLE facts (version, app list, relocated module,
    debunked import claims). Prose accuracy still needs human review, but the
    high-severity drift we just fixed (Django 5.2, karigar, inventory-owns-RBAC,
    'never imports') now fails CI if it reappears.
    """

    SOURCE_DOCS = ('SYSTEM_DESIGN.md', 'ARCHITECTURE.md')

    def _doc(self, name):
        return (REPO_ROOT / name).read_text()

    def test_django_version_claims_match_actual(self):
        import re

        import django
        actual = django.get_version()  # e.g. '5.0.1'
        for name in self.SOURCE_DOCS:
            for claimed in re.findall(r'Django (\d+\.\d+(?:\.\d+)?)', self._doc(name)):
                self.assertEqual(
                    claimed, actual,
                    f"{name} claims 'Django {claimed}' but the installed version is "
                    f"{actual}. Update the doc (this guard auto-validates on upgrade).",
                )

    def test_no_debunked_dependency_or_relocation_claims(self):
        # These exact phrasings were FALSE (cross-app lazy imports exist; RBAC
        # moved to accounts). If they come back, the doc is lying again.
        banned = ('imports nothing', 'never imports', 'inventory/services/permission_service')
        for name in self.SOURCE_DOCS:
            text = self._doc(name)
            for phrase in banned:
                self.assertNotIn(
                    phrase, text,
                    f"{name} contains the debunked claim '{phrase}'.",
                )

    def test_karigar_mentions_are_historical_only(self):
        # The role was renamed worker<-karigar (2026-06-02). Any surviving
        # 'karigar' must be a historical note ('renamed from'/'was'), never a
        # live role description.
        for name in self.SOURCE_DOCS:
            for line in self._doc(name).splitlines():
                if 'karigar' in line.lower():
                    self.assertTrue(
                        ('renamed' in line.lower()) or ('was' in line.lower()),
                        f"{name}: live 'karigar' reference (renamed to 'worker'): {line!r}",
                    )

    def test_expense_and_core_apps_are_documented_and_installed(self):
        from django.conf import settings
        installed = ' '.join(settings.INSTALLED_APPS)
        for app in ('expense', 'core'):
            self.assertIn(app, installed, f"{app} missing from INSTALLED_APPS")
            self.assertIn(
                app, self._doc('SYSTEM_DESIGN.md'),
                f"SYSTEM_DESIGN.md never mentions the '{app}' app.",
            )

    def test_permission_service_lives_in_accounts(self):
        # The relocation (2026-06) is load-bearing for the whole RBAC story.
        from accounts.services import permission_service
        self.assertTrue(permission_service.__name__.startswith('accounts.'))


class ObservabilityTests(TestCase):
    """P0.4: request-id correlation (core.observability)."""

    def test_request_id_filter_injects_attribute(self):
        import logging
        from core.observability import RequestIDFilter
        rec = logging.LogRecord('t', logging.INFO, __file__, 1, 'msg', None, None)
        self.assertTrue(RequestIDFilter().filter(rec))
        self.assertEqual(rec.request_id, '-')   # '-' outside a request

    def test_response_carries_request_id_header(self):
        resp = Client().get('/')
        self.assertIn('X-Request-ID', resp)
        self.assertTrue(resp['X-Request-ID'])   # non-empty id on every response

    def test_inbound_request_id_is_honoured(self):
        resp = Client().get('/', HTTP_X_REQUEST_ID='abc123')
        self.assertEqual(resp['X-Request-ID'], 'abc123')


class MediaServingTests(TestCase):
    """PD bundle: two-tier /media/ serving — storefront assets public, all other
    uploads login-gated (business evidence must never be world-readable).

    NOTE: document_root is bound into the URLconf at import time, so these tests
    write throwaway files under the REAL MEDIA_ROOT and clean them up.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.conf import settings
        cls._pub = settings.MEDIA_ROOT / 'storefront' / '_test_media_pub.txt'
        cls._priv = settings.MEDIA_ROOT / 'advances' / '_test_media_priv.txt'
        for f, body in ((cls._pub, 'public asset'), (cls._priv, 'business evidence')):
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body)

    @classmethod
    def tearDownClass(cls):
        for f in (cls._pub, cls._priv):
            f.unlink(missing_ok=True)
        super().tearDownClass()

    def test_storefront_media_is_public(self):
        resp = self.client.get('/media/storefront/_test_media_pub.txt')
        self.assertEqual(resp.status_code, 200)

    def test_other_media_requires_login(self):
        resp = self.client.get('/media/advances/_test_media_priv.txt')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('next=', resp['Location'])

    def test_other_media_served_when_authenticated(self):
        from accounts.models import User
        user = User.objects.create_user(email='media@test', password='x')
        self.client.force_login(user)
        resp = self.client.get('/media/advances/_test_media_priv.txt')
        self.assertEqual(resp.status_code, 200)
