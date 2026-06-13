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

    # ARCHITECTURE.md archived 2026-06-12 (merged into SYSTEM_DESIGN.md);
    # the guard now also covers the first-read knowledge map.
    SOURCE_DOCS = ('SYSTEM_DESIGN.md', 'docs/PROJECT_KNOWLEDGE_MAP.md')

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


DOCS_ROOT = REPO_ROOT / 'docs'
PKALS_ROOT = DOCS_ROOT / 'LEARNING_2_0'

# The canonical single-writer chokepoint service MODULES the docs route to
# (CHOKEPOINTS/ pages + AI_AGENT_GUIDE never-modify list). If one is renamed,
# every canonical doc pointing at it goes stale — this list makes that a build
# failure instead of silent drift. Paths are relative to config/.
CANONICAL_CHOKEPOINT_SERVICES = (
    'expense/services/adda_settlement_service.py',
    'expense/services/allocation_service.py',
    'expense/services/ledger_service.py',
    'expense/services/settlement_service.py',
    'production/services/cost_service.py',
    'production/services/worker_task_service.py',
    'tracking/services/history_service.py',
)


class PkalsNavigationGuardTests(SimpleTestCase):
    """C-1 longevity hardening — cheap, drift-effective guards over the PKALS
    knowledge system (docs/LEARNING_2_0). Reuses the DocAccuracyTests framework
    (stdlib only, no DB). Validates REFERENCES, COUNTS, and NAVIGATION INTEGRITY
    rather than prose — these are the failure modes that silently make 98 docs
    lie after a rename/move/new-phase. See PKALS_LONGEVITY_HARDENING.md.
    """

    import re as _re
    _LINK = _re.compile(r'\]\(([^)]+)\)')

    def _pkals_markdown(self):
        files = list(PKALS_ROOT.rglob('*.md'))
        files.append(DOCS_ROOT / 'START_HERE.md')  # the single front door (H3)
        return [f for f in files if f.exists()]

    def test_pkals_internal_links_resolve(self):
        # Reference integrity: every relative markdown/dir link inside PKALS (+ the
        # front door) must point at a real path. Catches renamed/deleted/moved docs.
        broken = []
        for md in self._pkals_markdown():
            for raw in self._LINK.findall(md.read_text()):
                target = raw.split('#', 1)[0].strip()  # drop #anchor
                if not target:
                    continue  # pure in-page anchor
                if target.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                    continue
                if '<' in target or '*' in target:
                    continue  # template placeholder like APPS/<app>/...
                resolved = (md.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"{md.relative_to(REPO_ROOT)} -> {raw}")
        self.assertEqual(
            broken, [],
            "PKALS has dangling internal links (a doc was renamed/moved/deleted "
            "without updating its referrers). Fix the link or restore the target:\n"
            + "\n".join(broken),
        )

    def test_adr_sequence_is_contiguous(self):
        # Count integrity: ADRs are append-only 0001..N. A gap means one was
        # deleted/misnamed, which breaks every 'read 0001-00NN' instruction.
        import re
        nums = sorted(
            int(m.group(1))
            for p in (DOCS_ROOT / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')
            if (m := re.match(r'(\d{4})-', p.name))
        )
        self.assertTrue(nums, "no ADR files found under docs/adr/")
        expected = list(range(1, nums[-1] + 1))
        self.assertEqual(
            nums, expected,
            f"ADR numbering is not contiguous (gap/dupe). Found {nums}, expected "
            f"1..{nums[-1]}. PKALS docs that enumerate ADRs will be wrong.",
        )

    def test_canonical_chokepoint_services_exist(self):
        # Reference integrity (doc -> code): the services the CHOKEPOINTS pages +
        # AI_AGENT_GUIDE never-modify list name MUST exist. A rename here silently
        # invalidates the most load-bearing docs in PKALS.
        missing = [
            rel for rel in CANONICAL_CHOKEPOINT_SERVICES
            if not (CONFIG_DIR / rel).exists()
        ]
        self.assertEqual(
            missing, [],
            "A canonical chokepoint service was renamed/moved; the CHOKEPOINTS "
            f"docs + AI_AGENT_GUIDE now point at nothing: {missing}. Update both "
            "the code reference and the docs, or fix this list.",
        )

    def test_front_door_navigation_chain_is_intact(self):
        # Navigation integrity (the H3/H4 baseline): repo root must route to the
        # single front door, and the front door must route to the one overview +
        # the AI entry. Guards against re-fragmenting the entry path.
        readme = (REPO_ROOT / 'README.md').read_text()
        self.assertIn('docs/START_HERE.md', readme,
                      "README.md no longer links the single front door START_HERE (H3).")
        start = (DOCS_ROOT / 'START_HERE.md').read_text()
        for must in ('PROJECT_KNOWLEDGE_MAP.md', 'AI_AGENT_GUIDE'):
            self.assertIn(must, start,
                          f"START_HERE.md no longer routes to {must} (H3/H4 chain broken).")

    def test_ai_canonical_manifest_is_valid(self):
        # Session-3A: the machine-readable routing manifest an AI agent reads FIRST
        # must parse and every path it points at must resolve — otherwise it routes
        # an agent into a wall (worse than no manifest). All paths repo-root-relative.
        import json
        manifest_path = PKALS_ROOT / 'AI_AGENT_GUIDE' / 'canonical_manifest.json'
        self.assertTrue(manifest_path.exists(),
                        "canonical_manifest.json missing — AI routing layer gone.")
        data = json.loads(manifest_path.read_text())  # fails loudly on bad JSON

        broken = []
        # entry.* paths
        for k, p in data.get('entry', {}).items():
            if not (REPO_ROOT / p).exists():
                broken.append(f"entry.{k} -> {p}")
        # topics: canonical + also[]
        for t in data.get('topics', []):
            for p in [t.get('canonical', '')] + t.get('also', []):
                if p and not (REPO_ROOT / p).exists():
                    broken.append(f"topic {t.get('match', ['?'])[0]!r} -> {p}")
        # never_modify writers + chokepoint services
        for nm in data.get('never_modify', []):
            p = nm.get('only_writer', '')
            if p and not (REPO_ROOT / p).exists():
                broken.append(f"never_modify {nm.get('target')!r} -> {p}")
        for p in data.get('chokepoint_services', []):
            if not (REPO_ROOT / p).exists():
                broken.append(f"chokepoint_services -> {p}")
        self.assertEqual(broken, [],
                         "canonical_manifest.json points at paths that no longer "
                         "exist (a doc/service was renamed/moved). Fix the manifest "
                         "or restore the target:\n" + "\n".join(broken))

        # Single source of truth: the manifest's chokepoint list must equal the
        # constant the other guard methods use — they cannot silently diverge.
        # (Constant is config-relative; manifest is repo-root-relative — align.)
        self.assertEqual(
            sorted(data.get('chokepoint_services', [])),
            sorted(f'config/{c}' for c in CANONICAL_CHOKEPOINT_SERVICES),
            "canonical_manifest.json chokepoint_services has drifted from "
            "CANONICAL_CHOKEPOINT_SERVICES — keep them identical (one source).",
        )

    def test_pkals_v2_tool_parsers_succeed(self):
        # The PKALS v2 read-only tools (scripts/pkals_canonical.py + pkals_impact.py)
        # are thin wrappers over v1 artifacts. Validate their PARSERS against the live
        # manifest + matrix here, so a reformat that would silently break
        # /find-canonical or /impact fails the build instead (PKALS-LIVE: doc drift =
        # an architecture bug; fail fast). The tools themselves are not run in CI.
        import importlib.util
        scripts = REPO_ROOT / 'scripts'

        def _load(name):
            spec = importlib.util.spec_from_file_location(name, scripts / f'{name}.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

        canonical = _load('pkals_canonical')
        impact = _load('pkals_impact')

        # /find-canonical: manifest loads + a known topic resolves to its canonical.
        manifest = canonical.load_manifest()
        topic, score = canonical.match_topic(manifest, 'settlement')
        self.assertTrue(topic and score >= 2,
                        "pkals_canonical can't match 'settlement' — manifest match-terms changed?")
        self.assertIn('adda_settlement_service', topic['canonical'])

        # /impact: matrix parses to a healthy row count + a known file still matches.
        file_rows, _concept = impact.parse_matrix()
        self.assertGreaterEqual(
            len(file_rows), 15,
            f"CHANGE_IMPACT_MATRIX parsed only {len(file_rows)} file rows — table "
            "format changed? /impact would mis-route.")
        self.assertTrue(
            impact.match_file('config/production/services/worker_task_service.py', file_rows),
            "worker_task_service.py no longer matches any matrix row — /impact broken.")


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
