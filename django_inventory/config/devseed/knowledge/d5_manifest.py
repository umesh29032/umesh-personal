"""Domain 5 — canonical-manifest synchronization, the A-1 OWNER-RATIFIED scope
ONLY (dated amendment, PHASE_14 Appendix A, 2026-07-17): the manifest is
HANDWRITTEN and CI-guarded — this detector does (a) manifest path validation,
(b) canonical topic coverage vs the knowledge graph, (c) consistency
validation. REGENERATE-COMPARE DOES NOT EXIST and shall not be implemented.

READ-ONLY. Path validation = the report-side of the PkalsNavigationGuardTests
concern (a dead CI-guarded path = the §6.4 BLOCKER class)."""

import json
import os

from devseed.knowledge import BLOCKER, INFO, WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT, _load_graph

MANIFEST_PATH = os.path.join(
    REPO_ROOT, "docs", "LEARNING_2_0", "AI_AGENT_GUIDE", "canonical_manifest.json")


def _load_manifest(manifest=None):
    if manifest is not None:
        return manifest, None
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh), None
    except (json.JSONDecodeError, OSError) as e:
        return None, str(e)


def _manifest_paths(m):
    """Every doc path the manifest routes to: entry values + topic canonicals
    + topic 'also' lists."""
    paths = []
    for v in (m.get("entry") or {}).values():
        paths.append(("entry", v))
    for t in m.get("topics", []):
        if t.get("canonical"):
            paths.append(("canonical", t["canonical"]))
        for a in t.get("also", []):
            paths.append(("also", a))
    return paths


def detect_manifest_paths(diff=False, deep=False, *, manifest=None, path_exists=None):
    m, err = _load_manifest(manifest)
    if err:
        return [Finding(id="d5.paths.unreadable", domain="manifest-sync",
                        severity=BLOCKER, evidence={"error": err[:200]}, venue="docs")]
    exists = path_exists or (lambda p: os.path.exists(os.path.join(REPO_ROOT, p)))
    findings = []
    for role, path in _manifest_paths(m):
        if not exists(path):
            findings.append(Finding(
                id=f"d5.paths.dead:{path}", domain="manifest-sync",
                severity=BLOCKER,   # §6.4: a dead CI-guarded path — knowledge LIES
                evidence={"role": role, "path": path,
                          "guard": "PkalsNavigationGuardTests class (report-side)"},
                venue="docs"))
    return findings


def detect_manifest_coverage(diff=False, deep=False, *, manifest=None, graph=None):
    """Every topic canonical the manifest routes to should be KNOWN to the
    graph (a doc node anchors it) — unknown = the graph is stale or the
    manifest points off the knowledge boundary."""
    m, err = _load_manifest(manifest)
    if err:
        return []  # the paths detector already reports the BLOCKER
    known = set()
    for n in _load_graph(graph)["nodes"]:
        if n["kind"] == "doc":
            anchors = n.get("anchors")
            if isinstance(anchors, str):
                anchors = [a.strip(" '\"") for a in anchors.strip("[]").split(",")]
            known.update(anchors or [])
    findings = []
    for t in m.get("topics", []):
        c = t.get("canonical")
        if c and c not in known:
            findings.append(Finding(
                id=f"d5.coverage.graph-unknown:{c}", domain="manifest-sync",
                severity=WARN,
                evidence={"canonical": c,
                          "state": "manifest routes here but no graph doc node anchors it"},
                venue="graph"))
    return findings


def detect_manifest_consistency(diff=False, deep=False, *, manifest=None):
    """Internal consistency of the handwritten router: topics need non-empty
    match terms + a canonical (WARN); the same match term routing to two
    different canonicals is ambiguity hygiene (INFO)."""
    m, err = _load_manifest(manifest)
    if err:
        return []
    findings = []
    seen_terms = {}
    for i, t in enumerate(m.get("topics", [])):
        if not t.get("match") or not t.get("canonical"):
            findings.append(Finding(
                id=f"d5.consistency.incomplete-topic:{i}", domain="manifest-sync",
                severity=WARN, evidence={"index": i, "topic": str(t)[:120]},
                venue="docs"))
            continue
        for term in t["match"]:
            key = term.lower()
            if key in seen_terms and seen_terms[key] != t["canonical"]:
                findings.append(Finding(
                    id=f"d5.consistency.ambiguous-term:{key}", domain="manifest-sync",
                    severity=INFO,
                    evidence={"term": term, "canonicals": sorted({seen_terms[key], t['canonical']})},
                    venue="docs"))
            seen_terms.setdefault(key, t["canonical"])
    return findings
