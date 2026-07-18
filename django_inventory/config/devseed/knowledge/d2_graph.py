"""Domain 2 — code ⇄ graph (KS-C; inherited contract: PHASE_08 §6.7 — the
validator re-run + the deep-tier builder dry-run compare).

EXTEND-NEVER-FORK: the Phase-8 validator is IMPORTED and re-run (its FATAL/
FINDINGS/INFO streams map to BLOCKER/WARN/INFO); the deep tier runs the
Phase-8 BUILDER with its file-write intercepted IN MEMORY (the builder file is
untouched, no graph is written anywhere — pure dry-run compare). READ-ONLY."""

import contextlib
import io
import json
import os
import sys

from devseed.knowledge import BLOCKER, INFO, WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT, _builder


def _scripts_on_path():
    scripts = os.path.join(REPO_ROOT, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)


def detect_graph_validator(diff=False, deep=False, *, validator=None):
    """Re-run the Phase-8 validator against today's tree (PHASE_08 §6.7: sync
    re-checks graph invariants continuously — IMPORTED, never re-implemented).
    FATAL → BLOCKER (the §6.4 graph-invariant-violation class).

    ⚠ §16.3 WRITE-PATH NEUTRALIZATION (incident 2026-07-17, log §KS-C): the
    validator's REPRODUCIBILITY check re-runs the BUILDER as a SUBPROCESS and
    REWRITES docs/knowledge_graph.json IN PLACE (the documented R-10 hazard —
    it FIRED under this detector's first sweep). A pure detector may never
    write: the subprocess is no-op'd for the duration, which makes that one
    check vacuous — DISCLOSED as a standing INFO finding on every run (never
    silent). Reproducibility certification = the --deep dry-run compare here
    (write-free) or the standalone Phase-8 ceremony."""
    if validator is None:
        _scripts_on_path()
        import validate_knowledge_graph as validator
    validator.FATAL, validator.FINDINGS, validator.INFO = [], [], []
    buf = io.StringIO()
    real_run = getattr(getattr(validator, "subprocess", None), "run", None)
    if real_run is not None:
        validator.subprocess.run = lambda *a, **k: None   # the builder NEVER spawns
    try:
        with contextlib.redirect_stdout(buf):
            validator.main()
    except SystemExit:
        pass  # the validator exits nonzero on FATALs — we read the lists
    except Exception as e:  # unreadable graph/schema = an invariant violation itself
        return [Finding(id="d2.validator.crashed", domain="code-graph",
                        severity=BLOCKER, evidence={"error": str(e)[:200]},
                        venue="graph")]
    finally:
        if real_run is not None:
            validator.subprocess.run = real_run
    findings = []
    if real_run is not None:
        findings.append(Finding(
            id="d2.validator.repro-check-neutralized", domain="code-graph",
            severity=INFO,
            evidence={"why": "the validator's repro check rebuilds the graph IN PLACE "
                             "(R-10 hazard) — a pure detector no-ops it; its PASS proves "
                             "nothing here",
                      "write_free_equivalent": "--deep graph.deep-rebuild dry-run compare"},
            venue="graph"))
    for sev, rows, tag in ((BLOCKER, validator.FATAL, "fatal"),
                           (WARN, validator.FINDINGS, "finding"),
                           (INFO, validator.INFO, "info")):
        for i, line in enumerate(rows):
            findings.append(Finding(
                id=f"d2.validator.{tag}:{i}:{str(line)[:60]}", domain="code-graph",
                severity=sev, evidence={"validator_line": str(line)[:300]},
                venue="graph"))
    return findings


def _dry_run_rebuild_hash():
    """Run the Phase-8 builder with its single file-write captured in memory
    (build() writes GRAPH_PATH via `io.open(...).write(...)` — intercepted at
    the module's own io.open; NOTHING touches disk). Returns the content_hash
    the rebuild WOULD produce."""
    bkg = _builder()
    captured = {}

    class _Sink(io.StringIO):
        def __exit__(self, *a):  # pragma: no cover - not used as ctx manager
            return False

    real_open = bkg.io.open

    def fake_open(path, mode="r", *a, **kw):
        if "w" in mode:
            sink = _Sink()
            captured["path"] = path

            class _W:
                def write(self, text):
                    captured["text"] = text
                    return len(text)
            return _W()
        return real_open(path, mode, *a, **kw)

    bkg.io.open = fake_open
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            bkg.build()
    finally:
        bkg.io.open = real_open
    return json.loads(captured["text"])["meta"]["content_hash"]


def detect_graph_deep_rebuild(diff=False, deep=False, *, rebuilt_hash=None,
                              current_hash=None):
    """DEEP TIER ONLY (SYNC-D7 ratified: the expensive builder dry-run +
    body-hash compare lives behind --deep; cost = one full in-memory build,
    seconds). 'Rebuild would differ' = the graph is stale vs today's tree."""
    if current_hash is None:
        with open(os.path.join(REPO_ROOT, "docs", "knowledge_graph.json"),
                  encoding="utf-8") as fh:
            current_hash = json.load(fh)["meta"]["content_hash"]
    if rebuilt_hash is None:
        try:
            rebuilt_hash = _dry_run_rebuild_hash()
        except SystemExit as e:   # builder refuses (e.g. id collision) = drift evidence
            return [Finding(id="d2.deep-rebuild.builder-refused", domain="code-graph",
                            severity=WARN, evidence={"error": str(e)[:200]},
                            venue="graph")]
    if rebuilt_hash != current_hash:
        return [Finding(
            id="d2.deep-rebuild.would-differ", domain="code-graph", severity=WARN,
            evidence={"current": current_hash[:19], "rebuild": rebuilt_hash[:19],
                      "meaning": "a rebuild today produces a different graph — the graph is stale"},
            venue="graph")]
    return []
