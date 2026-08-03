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
from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest import mock

from django.test import Client, SimpleTestCase, TestCase
from django.utils import timezone

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


class LocalDateGuardTests(SimpleTestCase):
    """`timezone.now().date()` returns a **UTC** date. With TIME_ZONE='Asia/Kolkata'
    and USE_TZ=True, the factory's books run on IST, so a UTC date is one day behind
    for 5.5 hours every day — and a whole month behind on the 1st.

    That bug shipped in **15** places (2026-08-01), FIVE of them stamping dates onto
    money records: `settlement_date`, advance date, and ledger `entry_date` in BOTH
    the per-worker and the Adda settlement paths. It was found only because bod's
    money-tile cross-check compared an IST tile against a UTC page and failed on a
    month boundary. Report: docs/UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md

    The correct primitive is `timezone.localdate()` — and `timezone.localdate(dt)`
    when an instant already exists, so a derived date can never disagree with the
    datetime it came from.

    **Why this test is AST-based, not a string scan.** The first version of this pin
    matched the literal text `timezone.now().date()`. It passed while FIVE real bugs
    survived, because they were written as:

        now = timezone.now()      # aware UTC datetime
        ... now.date() ...        # <- UTC date, invisible to a string scan

    A guard that only catches the shape you already fixed is not a guard. This one
    walks the tree and follows the variable.

    **The stored-field shape is covered too.** `obj.created_at.month` is the UTC
    month and is the same bug — it bit immediately, in `outcome_trend`, where the
    bucket *keys* were local while the bucket *fill* read `created_at.month`. Type
    inference is impossible here, so `DATETIME_FIELDS` is a curated list of this
    project's aware-datetime field names. **Add to it when you add such a field.**

    Parsing an explicit string (`datetime.strptime(s, '%Y-%m-%d').date()`) is
    legitimate and must stay allowed.
    """

    DATE_PARTS = ('date', 'year', 'month', 'day')

    # Aware datetime fields in this project: reading a date part off one of these
    # gives the UTC value. Not exhaustive by construction — extend it.
    DATETIME_FIELDS = frozenset({
        'created_at', 'updated_at', 'completed_at', 'started_at', 'settled_at',
        'reversed_at', 'voided_at', 'last_opened_at', 'finalized_at', 'paid_at',
        'timestamp', 'logged_at', 'recorded_at', 'issued_at', 'generated_at',
        'last_login', 'date_joined', 'locked_until', 'deleted_at', 'cancelled_at',
    })

    def _offenders(self, path):
        """Every UTC-derived date-part access in one file, as readable strings."""
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:                     # pragma: no cover - not our files
            return []
        found = []

        def is_tz_now(node):
            return (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'now'
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'timezone')

        # 1. names bound to timezone.now() — the shape the string scan missed
        utc_names = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and is_tz_now(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        utc_names[target.id] = node.lineno

        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or node.attr not in self.DATE_PARTS:
                continue
            recv = node.value
            # 2. inline: timezone.now().date() / .year / .month / .day
            if is_tz_now(recv):
                found.append(f'L{node.lineno}: timezone.now().{node.attr}')
            # 3. via a variable: now = timezone.now(); now.date()
            elif isinstance(recv, ast.Name) and recv.id in utc_names:
                found.append(f'L{node.lineno}: {recv.id}.{node.attr} '
                             f'({recv.id} = timezone.now() at L{utc_names[recv.id]})')
            # 4. off a stored aware field: obj.created_at.month  (UTC month)
            elif isinstance(recv, ast.Attribute) and recv.attr in self.DATETIME_FIELDS:
                found.append(f'L{node.lineno}: .{recv.attr}.{node.attr} '
                             '(stored field is UTC — wrap in timezone.localtime())')

        # 5. Python's date.today() reads the SERVER clock, not Django's TIME_ZONE —
        #    on a UTC container that is the same bug by another route.
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == 'today' \
                    and isinstance(node.func.value, ast.Name) \
                    and node.func.value.id in ('date', 'datetime', '_date'):
                found.append(f'L{node.lineno}: {node.func.value.id}.today()')
        return found

    def test_no_utc_date_used_as_a_local_date(self):
        offenders = {}
        for py in CONFIG_DIR.rglob('*.py'):
            # Tests may build fixtures from a UTC date; migrations are frozen history.
            if 'migrations' in py.parts or 'tests' in py.parts \
                    or py.name == 'tests.py' or py.name.startswith('test_'):
                continue
            hits = self._offenders(py)
            if hits:
                offenders[str(py.relative_to(CONFIG_DIR))] = hits
        self.assertEqual(
            offenders, {},
            'UTC date used where a LOCAL date is meant. Use timezone.localdate() — '
            'or timezone.localdate(dt) to derive from an existing instant. '
            '(TIME_ZONE=Asia/Kolkata, USE_TZ=True.) See '
            f'docs/UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md. Offenders: {offenders}')

    def test_the_guard_actually_catches_the_shape_that_escaped_it(self):
        """Meta-test: prove the AST guard sees the variable form. Without this,
        a future refactor could silently weaken the guard back to a string scan
        and nothing would fail."""
        import tempfile
        cases = {
            'inline.py': 'from django.utils import timezone\nd = timezone.now().date()\n',
            'viavar.py': ('from django.utils import timezone\n'
                          'now = timezone.now()\nd = now.date()\n'),
            'year.py': ('from django.utils import timezone\n'
                        'now = timezone.now()\ny = now.year\n'),
            'today.py': 'from datetime import date\nd = date.today()\n',
            'stored.py': 'k = f"{o.created_at.year}-{o.created_at.month}"\n',
        }
        ok = {
            'good1.py': 'from django.utils import timezone\nd = timezone.localdate()\n',
            'good2.py': ('from django.utils import timezone\n'
                         'w = timezone.now()\nd = timezone.localdate(w)\n'),
            'good3.py': ("from datetime import datetime\n"
                         "d = datetime.strptime(s, '%Y-%m-%d').date()\n"),
            'good4.py': ('from django.utils import timezone\n'
                         'c = timezone.localtime(o.created_at)\n'
                         'k = f"{c.year}-{c.month}"\n'),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name, src in {**cases, **ok}.items():
                (root / name).write_text(src)
            for name in cases:
                self.assertTrue(self._offenders(root / name),
                                f'guard MISSED the offending shape in {name}')
            for name in ok:
                self.assertEqual(self._offenders(root / name), [],
                                 f'guard false-positived on legitimate {name}')

    def test_localdate_is_actually_local_not_utc(self):
        """Proves the primitive we mandate does the thing we claim, rather than
        trusting the name."""
        from datetime import timedelta

        from django.utils import timezone
        self.assertEqual(timezone.get_current_timezone_name(), 'Asia/Kolkata')
        # IST is UTC+05:30, so the local date can never be BEHIND the UTC date,
        # and is one day AHEAD for 5.5h every day.
        self.assertIn(timezone.localdate() - timezone.now().date(),
                      (timedelta(0), timedelta(days=1)))


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


class MidnightBoundaryTests(TestCase):
    """Prove the local-date contract holds **inside the divergence window**.

    IST is UTC+05:30, so between 00:00 and 05:30 IST the UTC date is one day
    behind — and on the 1st of a month, a whole month behind. Every test that
    exercises "today" therefore PASSES mid-month and can only fail in that
    5.5-hour window. `bod`'s money-tile cross-check was exactly such a test: it
    sat green for months and only went red because someone ran it at 01:27 IST
    on the 1st (docs/UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md).

    Luck is not a test strategy. These freeze the clock **at** the boundary so
    the contract is checked on every run, at any hour.
    """

    # 2026-07-31 19:30 UTC == 2026-08-01 01:00 IST — different DAY *and* MONTH.
    UTC_INSTANT = datetime(2026, 7, 31, 19, 30, tzinfo=dt_timezone.utc)
    LOCAL_DATE = date(2026, 8, 1)      # what the factory calls "today"
    UTC_DATE = date(2026, 7, 31)       # what a naive .date() would give

    def test_the_fixture_really_straddles_the_boundary(self):
        """Guard the guard: if this ever stops diverging, the tests below become
        vacuous and would pass while proving nothing."""
        self.assertEqual(self.UTC_INSTANT.date(), self.UTC_DATE)
        self.assertEqual(timezone.localtime(self.UTC_INSTANT).date(), self.LOCAL_DATE)
        self.assertNotEqual(self.UTC_DATE, self.LOCAL_DATE)
        self.assertNotEqual(self.UTC_DATE.month, self.LOCAL_DATE.month)

    def test_localdate_of_that_instant_is_the_local_day(self):
        self.assertEqual(timezone.localdate(self.UTC_INSTANT), self.LOCAL_DATE)

    def test_expense_month_default_uses_the_LOCAL_month_at_the_boundary(self):
        """The exact divergence that made a BOD tile disagree with its own source
        page: tile said August (local), page said July (UTC)."""
        from django.test import RequestFactory

        from expense.views import _parse_month
        with mock.patch('django.utils.timezone.now', return_value=self.UTC_INSTANT):
            year, month = _parse_month(RequestFactory().get('/expense/expenses/'))
        self.assertEqual((year, month), (2026, 8),
                         'expense month default fell back to the UTC month')

    def test_month_start_uses_the_LOCAL_month_at_the_boundary(self):
        from expense.views import _month_start
        with mock.patch('django.utils.timezone.now', return_value=self.UTC_INSTANT):
            self.assertEqual(_month_start(), date(2026, 8, 1))

    def test_bod_tile_and_expense_page_agree_at_the_boundary(self):
        """The two sides of the original bug, compared directly. They must bucket
        the same month whatever the clock says."""
        from django.test import RequestFactory

        from expense.views import _parse_month
        with mock.patch('django.utils.timezone.now', return_value=self.UTC_INSTANT):
            tile_now = timezone.localtime()          # what bod/widgets.py uses
            page_year, page_month = _parse_month(
                RequestFactory().get('/expense/expenses/'))
        self.assertEqual((tile_now.year, tile_now.month), (page_year, page_month),
                         'BOD money tile and the expense page are on different clocks')

    def test_completed_today_uses_the_LOCAL_day_at_the_boundary(self):
        """An Adda completed at 01:00 IST on the 1st belongs to the 1st, not to
        the previous month's last day."""
        from production.services.operations_digest import adda_status_counts
        with mock.patch('django.utils.timezone.now', return_value=self.UTC_INSTANT):
            with mock.patch(
                    'production.services.operations_digest.timezone.localdate',
                    return_value=self.LOCAL_DATE) as m:
                adda_status_counts(fields={'completed_today'})
            self.assertTrue(m.called, 'completed_today no longer derives a local date')


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
