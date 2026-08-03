"""compute_bridge — the ONLY door to the isolated CV runtime (ADR-F).

Django never imports cv2/numpy/ezdxf; every geometry computation is a
subprocess call into compute/patterns_ai's own pinned venv with JSON-file
I/O (files/argv, no sockets). This module is NOT a writer — it computes
and returns; single-writer services persist the results.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings


class ComputeError(Exception):
    """Runtime missing/crashed — an operational fault, never silent."""


def compute_dir() -> Path:
    configured = getattr(settings, 'PATTERNS_AI_COMPUTE_DIR', None)
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR).parent / 'compute' / 'patterns_ai'


def runtime_available() -> bool:
    return (compute_dir() / 'venv' / 'bin' / 'python').exists()


TOOLS = {'extract': 'extract.py', 'calibrate': 'calibrate.py',
         'dxf': 'dxf_io.py', 'synth': 'synth.py', 'nest': 'nest.py',
         'pdf': 'pdf_io.py',           # phase-6: production PDF
         # M8 Evidence-Set capture: no-mat photo + human-stated scale
         'extract_plain': 'extract_plain.py'}
TIMEOUT_S = 120


def run_tool(tool: str, job: dict, timeout_s: float = None) -> dict:
    """Run one compute CLI with `job`, return its parsed result dict.
    timeout_s overrides the flat default (P5: nest runs need
    timebox + engine startup headroom)."""
    base = compute_dir()
    python = base / 'venv' / 'bin' / 'python'
    script = base / TOOLS[tool]
    if not python.exists():
        raise ComputeError(
            f'compute runtime venv missing at {python} — rebuild per '
            'compute/patterns_ai/README.md (ADR-F pinned lockfile).')
    with tempfile.TemporaryDirectory(prefix='pai_compute_') as td:
        jin = Path(td) / 'job.json'
        jout = Path(td) / 'result.json'
        jin.write_text(json.dumps(job))
        proc = subprocess.run(
            [str(python), str(script), '--in', str(jin), '--out', str(jout)],
            cwd=str(base), capture_output=True, text=True,
            timeout=timeout_s or TIMEOUT_S)
        if proc.returncode != 0:
            raise ComputeError(
                f'{tool} failed (rc={proc.returncode}): '
                f'{proc.stderr.strip()[-500:]}')
        try:
            return json.loads(jout.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ComputeError(f'{tool} produced no readable result: {exc}')
