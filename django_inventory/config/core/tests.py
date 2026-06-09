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

from django.test import SimpleTestCase

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
