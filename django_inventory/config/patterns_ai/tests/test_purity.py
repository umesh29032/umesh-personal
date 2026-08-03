"""Runtime purity wall (ADR-H §2): production never imports patterns_ai —
zero exceptions (stricter than machines) — and Block-1 shape pins.

Source-level scan (not sys.modules) so lazy/function-level imports are caught
too — the exact failure mode the report-only import-linter contract misses.
"""
import pathlib
import re

from django.apps import apps
from django.test import TestCase

CONFIG_DIR = pathlib.Path(__file__).resolve().parents[2]
PRODUCTION_APPS = ('production', 'expense', 'inventory', 'raw_materials',
                   'tracking', 'machines', 'accounts', 'core', 'storefront')
IMPORT_RE = re.compile(r'^\s*(from|import)\s+patterns_ai', re.M)


class PurityTests(TestCase):
    def test_no_production_module_imports_patterns_ai(self):
        offenders = []
        for app in PRODUCTION_APPS:
            for py in (CONFIG_DIR / app).rglob('*.py'):
                if 'migrations' in py.parts:
                    continue
                if IMPORT_RE.search(py.read_text(encoding='utf-8', errors='ignore')):
                    offenders.append(str(py.relative_to(CONFIG_DIR)))
        self.assertEqual(offenders, [],
                         'production-side code imports patterns_ai: %s' % offenders)

    def test_block2a_pin_exactly_the_foundation_models(self):
        # Block-2A pin (consciously updated from the Block-1 no-models pin):
        # EXACTLY the owner-approved entities — new models arrive per-block
        # by decision, not drift.
        # Block-2C conscious update: + MarkerTransitionEvent (owner-approved).
        # Block-3A conscious update: + CaptureAsset (owner-approved).
        # P2 conscious update (owner-approved phase): + CalibrationMatCheck,
        # GeometryExtraction, PieceSizeGeometry, PatternSetLabel (ADR-D2/D3).
        # P3 conscious update (owner-approved phase): + MarkerGenerationRun,
        # GeneratedMarkerCandidate (ADR-A engines, D11 promotion).
        # Phase-6 M2 conscious update (owner-approved two-model split,
        # §3h): + ProductFabricProfile (defaults only) + ProductionLayout
        # (designation only).
        # PLATFORM Phase-7 conscious update (owner-approved persistence
        # rules 1-10): + ApprovedLayout (the manufacturing library —
        # immutable, versioned, append-only; migration 0010).
        # PLATFORM Phase-8A conscious update (owner-approved plan +
        # freezes F1-F3): + ApprovedLayoutUsage (Adda↔layout contract,
        # append-only history; migration 0011).
        # M2 conscious update (owner-approved UI_WORKFLOW_FREEZE §2.4/§4,
        # the Acquisition Layer made first-class): + EvidenceItem (the
        # piece×size Evidence Stack; migration 0012).
        # M4 conscious update (owner-approved plan §4 + refinement R1):
        # + ManufacturingStrategy (the "Marker Recipe" — a named Marker
        # Plan preset; manufacturing knowledge as data; migration 0014).
        names = sorted(m.__name__ for m in apps.get_app_config('patterns_ai').get_models())
        self.assertEqual(names, [
            'ApprovedLayout', 'ApprovedLayoutUsage',
            'CalibrationMat', 'CalibrationMatCheck', 'CaptureAsset',
            'EvidenceItem',
            'GeneratedMarkerCandidate', 'GeometryExtraction',
            'ManufacturingStrategy', 'Marker',
            'MarkerGenerationRun', 'MarkerOutcome',
            'MarkerTransitionEvent', 'MarkerUsage', 'PatternPiece',
            'PatternPieceVersion', 'PatternSetLabel', 'PieceSizeGeometry',
            'ProductFabricProfile', 'ProductionLayout',
            'SuggestionEvent',
        ])

    def test_block3a_pin_filefield_only_in_capture_model(self):
        # Block-3A conscious update of the Block-1 no-FileField pin: uploads
        # exist now, but file storage stays confined to the capture model.
        src = (CONFIG_DIR / 'patterns_ai')
        hits = sorted(str(p.relative_to(CONFIG_DIR)) for p in src.rglob('*.py')
                      if 'FileField' in p.read_text(errors='ignore')
                      and 'tests' not in p.parts and 'migrations' not in p.parts)
        # Block-3B conscious update: forms.FileField (upload widget) allowed.
        # M2 conscious update: EvidenceItem keeps original DXF/SVG bytes —
        # evidence is a fact (same immutable-storage philosophy as capture).
        self.assertEqual(hits, ['patterns_ai/forms.py',
                                'patterns_ai/models/capture.py',
                                'patterns_ai/models/geometry.py'])


class SingleWriterGuardTests(TestCase):
    """I-1: knowledge rows are born ONLY in patterns_ai/services/ (plus tests
    and migrations). Source-scan wall — a raw `.objects.create` anywhere else
    in the repo is a review-reject made mechanical."""

    KNOWLEDGE = ('Marker', 'MarkerUsage', 'MarkerOutcome', 'MarkerTransitionEvent',
                 'CaptureAsset',
                 'PatternPiece', 'PatternPieceVersion',
                 'SuggestionEvent', 'CalibrationMat',
                 # P2 conscious extension (geometry era):
                 'CalibrationMatCheck', 'GeometryExtraction',
                 'PieceSizeGeometry', 'PatternSetLabel',
                 # P3 conscious extension (generation era):
                 'MarkerGenerationRun', 'GeneratedMarkerCandidate',
                 # Phase-6 M2 (two-model split):
                 'ProductFabricProfile', 'ProductionLayout')

    def test_no_raw_knowledge_writes_outside_services(self):
        pat = re.compile(
            r'(?:' + '|'.join(self.KNOWLEDGE) + r')\.objects\.(create|update_or_create|get_or_create|bulk_create)')
        offenders = []
        for py in CONFIG_DIR.rglob('*.py'):
            parts = py.parts
            if 'migrations' in parts or 'tests' in parts or 'venv' in parts:
                continue
            rel = py.relative_to(CONFIG_DIR)
            if rel.parts[0] == 'patterns_ai' and len(rel.parts) > 1 and rel.parts[1] == 'services':
                continue
            txt = py.read_text(encoding='utf-8', errors='ignore')
            if pat.search(txt):
                offenders.append(str(rel))
        self.assertEqual(offenders, [],
                         'raw knowledge-model writes outside the single-writer services: %s' % offenders)


class RuntimeIsolationTests(TestCase):
    """ADR-F walls (P2): Django never imports the CV stack; the compute
    runtime never imports Django or opens the network. Source-scan walls,
    same philosophy as the reverse-import wall above."""

    CV_IMPORT_RE = re.compile(
        r'^\s*(from|import)\s+(cv2|numpy|ezdxf|shapely|torch|onnxruntime)\b',
        re.M)
    NET_IMPORT_RE = re.compile(
        r'^\s*(from|import)\s+(socket|requests|urllib|http\.client|httpx)\b',
        re.M)
    DJANGO_IMPORT_RE = re.compile(r'^\s*(from|import)\s+django\b', re.M)

    def _compute_dir(self):
        return CONFIG_DIR.parent / 'compute' / 'patterns_ai'

    def test_django_venv_never_imports_the_cv_stack(self):
        offenders = []
        for py in CONFIG_DIR.rglob('*.py'):
            if any(x in py.parts for x in ('migrations', 'venv')):
                continue
            if self.CV_IMPORT_RE.search(py.read_text(errors='ignore')):
                offenders.append(str(py.relative_to(CONFIG_DIR)))
        self.assertEqual(offenders, [],
                         'ADR-F breach — cv stack imported in Django code: %s'
                         % offenders)

    def test_compute_runtime_imports_no_django_and_no_network(self):
        offenders = []
        for py in self._compute_dir().rglob('*.py'):
            if 'venv' in py.parts:
                continue
            txt = py.read_text(errors='ignore')
            if self.DJANGO_IMPORT_RE.search(txt):
                offenders.append(f'{py.name}: django import')
            if self.NET_IMPORT_RE.search(txt):
                offenders.append(f'{py.name}: network import')
        self.assertEqual(offenders, [], 'ADR-F breach: %s' % offenders)

    def test_compute_runtime_lockfile_exists(self):
        base = self._compute_dir()
        self.assertTrue((base / 'requirements.lock.txt').exists(),
                        'compute runtime lockfile missing (ADR-F vendoring)')
        self.assertTrue((base / 'artifacts' / 'MANIFEST.md').exists(),
                        'artifact manifest missing (ADR-F)')
