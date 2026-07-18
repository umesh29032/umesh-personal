"""Domain 1 — code ⇄ documentation (KS-B; inherited contract: PHASE_05
§6.1.17 / the pkals_v2 MUST list — change-impact · route-map · model-map).

READ-ONLY detectors. Injection parameters exist for constructed-drift tests
(a planted failure class per detector); real runs use the repo defaults.
Extend-never-fork: the route/model censuses reuse the Phase-8 builder's own
walkers and id-builders (imported, single source)."""

import fnmatch
import os
import re
import sys

from devseed.knowledge import WARN, Finding

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
MATRIX_PATH = os.path.join(
    REPO_ROOT, "docs", "LEARNING_2_0", "LIVING_DOCUMENTATION_SYSTEM",
    "CHANGE_IMPACT_MATRIX.md")


def _builder():
    """Import the Phase-8 builder (single source for censuses + ids).
    Function-level: scripts/ is not a package; django is already set up in
    any context that runs a sweep."""
    scripts = os.path.join(REPO_ROOT, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import build_knowledge_graph as bkg
    return bkg


def _load_graph(graph=None):
    if graph is not None:
        return graph
    import json
    with open(os.path.join(REPO_ROOT, "docs", "knowledge_graph.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


# ── change-impact matrix ─────────────────────────────────────────────────────

_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
# explicit repo paths inside a matrix cell (the validatable references)
_PATH_REF = re.compile(r"\b((?:docs|config)/[A-Za-z0-9_/\.<>-]+\.md)\b")


def _matrix_rows(matrix_path=None):
    """(pattern_cell, docs_cell) pairs from BOTH matrix tables."""
    path = matrix_path or MATRIX_PATH
    rows = []
    for line in open(path, encoding="utf-8").read().splitlines():
        m = _ROW.match(line.strip())
        if m and not set(m.group(1)) <= {"-", " "}:
            rows.append((m.group(1), m.group(2)))
    return rows


def _pattern_matches(pattern_cell, changed_path):
    """Does a matrix pattern cell cover this changed file? Backticked globs,
    `any */x.py` phrasing, and the template row are the cell vocabulary."""
    cell = pattern_cell.strip().strip("*").strip()
    if changed_path.endswith(".html") and "template" in cell and ".html" in cell:
        return True
    for tick in re.findall(r"`([^`]+)`", cell):
        pat = tick.strip()
        if "*" in pat:
            if fnmatch.fnmatch(changed_path, pat) or fnmatch.fnmatch(changed_path, pat + "*"):
                return True
        elif pat and (changed_path == pat or changed_path.endswith("/" + pat)
                      or changed_path.startswith(pat.rstrip("/") + "/")):
            return True
    return False


def detect_change_impact(diff=False, deep=False, *, matrix_path=None,
                         changed=None, path_exists=None):
    """Sweep leg: matrix doc references must resolve (a dead reference routes a
    change to a doc that no longer exists — the matrix lies). Diff leg: every
    changed config code/template file needs a matrix row (the `/impact` rule:
    matrix-less changed files are flagged)."""
    exists = path_exists or (lambda p: os.path.exists(os.path.join(REPO_ROOT, p)))
    findings = []
    rows = _matrix_rows(matrix_path)

    for _pat, docs_cell in rows:
        for ref in _PATH_REF.findall(docs_cell):
            if "<" in ref:          # family placeholder (docs/apps/<app>/GUIDE.md) — not a literal path
                continue
            if not exists(ref):
                findings.append(Finding(
                    id=f"d1.matrix.dead-doc-ref:{ref}", domain="code-docs",
                    severity=WARN, evidence={"matrix": "CHANGE_IMPACT_MATRIX.md",
                                             "reference": ref},
                    venue="docs"))

    if diff:
        if changed is None:
            from devseed.knowledge.gitio import changed_files
            changed = changed_files()
        for path in changed:
            if not (path.startswith("config/") and path.endswith((".py", ".html"))):
                continue
            if path.split("/")[-1] == "__init__.py" or "/migrations/" in path or "/tests/" in path:
                continue
            if not any(_pattern_matches(pat, path) for pat, _ in rows):
                findings.append(Finding(
                    id=f"d1.matrix.unrouted:{path}", domain="code-docs",
                    severity=WARN,
                    evidence={"changed_file": path,
                              "rule": "pkals_v2 MUST: changed files need a matrix row"},
                    venue="docs"))
    return findings


# ── route-map (live URL census vs the graph's URL knowledge) ─────────────────

def detect_route_map(diff=False, deep=False, *, graph=None, live_ids=None):
    if live_ids is None:
        bkg = _builder()
        live_ids = {bkg.url_node_id(r) for r in bkg.walk_urls()}
    graph_ids = {n["id"] for n in _load_graph(graph)["nodes"] if n["kind"] == "url"}
    findings = []
    for uid in sorted(live_ids - graph_ids):
        findings.append(Finding(
            id=f"d1.route-map.missing:{uid}", domain="code-docs", severity=WARN,
            evidence={"route": uid, "state": "live but absent from the graph"},
            venue="graph"))
    for uid in sorted(graph_ids - live_ids):
        findings.append(Finding(
            id=f"d1.route-map.ghost:{uid}", domain="code-docs", severity=WARN,
            evidence={"route": uid, "state": "in the graph but no longer live"},
            venue="graph"))
    return findings


# ── model-map (live model census vs the graph's mapping-law floor) ───────────

def detect_model_map(diff=False, deep=False, *, graph=None, live_ids=None):
    if live_ids is None:
        bkg = _builder()
        live_ids = set()
        for app in bkg.project_apps():
            for model in app.get_models():
                live_ids.add(f"model:{app.label}.{model.__name__}")
    graph_ids = {n["id"] for n in _load_graph(graph)["nodes"] if n["kind"] == "model"}
    findings = []
    for mid in sorted(live_ids - graph_ids):
        findings.append(Finding(
            id=f"d1.model-map.missing:{mid}", domain="code-docs", severity=WARN,
            evidence={"model": mid, "state": "live but absent from the graph"},
            venue="graph"))
    for mid in sorted(graph_ids - live_ids):
        findings.append(Finding(
            id=f"d1.model-map.ghost:{mid}", domain="code-docs", severity=WARN,
            evidence={"model": mid, "state": "in the graph but no longer live"},
            venue="graph"))
    return findings
