"""Domain 3 — graph census / completeness / consistency (KS-C; inherited
contracts: PHASE_08 §6.7 cheap-tier census + the builder-consumed invariants).

BUILDER-CONSUMED INVARIANTS ONLY (owner KS-C order): every live census here is
the Phase-8 builder's OWN walker, imported (project_apps · doc_boundary);
graph self-integrity reuses the Phase-9 generator's `load_graph()` gate (hash
recompute + schema-major pin — the R-10 hand-edit guard) — nothing validated
elsewhere is re-implemented (validator territory stays in d2). READ-ONLY."""

import json
import os
import sys

from devseed.knowledge import BLOCKER, WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT, _builder, _load_graph


def detect_graph_census(diff=False, deep=False, *, graph=None, live_counts=None):
    """Cheap tier (PHASE_08 §6.7): census COUNTS vs graph node counts, for the
    kinds whose live census is an importable builder walker — apps
    (`project_apps`) and docs (`doc_boundary`). URL/model sets are the KS-B
    route/model-map detectors; everything else is the deep rebuild's job."""
    if live_counts is None:
        bkg = _builder()
        live_counts = {
            "app": len(list(bkg.project_apps())),
            "doc": len([p for p in bkg.doc_boundary() if p.endswith((".md", ".json"))]),
        }
    g = _load_graph(graph)
    graph_counts = {}
    for n in g["nodes"]:
        graph_counts[n["kind"]] = graph_counts.get(n["kind"], 0) + 1
    findings = []
    for kind, live in sorted(live_counts.items()):
        got = graph_counts.get(kind, 0)
        if got != live:
            findings.append(Finding(
                id=f"d3.census.count-mismatch:{kind}", domain="docs-graph",
                severity=WARN,
                evidence={"kind": kind, "live_census": live, "graph_nodes": got,
                          "meaning": "the graph no longer mirrors the live census — rebuild"},
                venue="graph"))
    return findings


def detect_graph_completeness(diff=False, deep=False, *, graph=None, census=None):
    """Disk→graph direction ONLY: every doc in the builder's own boundary has
    a graph doc node (new docs since the last build = the classic gap). The
    graph→disk direction (dead anchors) is the d2 validator's own check —
    never duplicated here."""
    if census is None:
        census = [p for p in _builder().doc_boundary() if p.endswith(".md")]
    known = set()
    for n in _load_graph(graph)["nodes"]:
        if n["kind"] == "doc":
            anchors = n.get("anchors")
            if isinstance(anchors, str):
                anchors = [a.strip(" '\"") for a in anchors.strip("[]").split(",")]
            known.update(anchors or [])
    findings = []
    for path in census:
        if path not in known:
            findings.append(Finding(
                id=f"d3.completeness.unindexed:{path}", domain="docs-graph",
                severity=WARN,
                evidence={"path": path,
                          "meaning": "in the builder's doc boundary but absent from the graph"},
                venue="graph"))
    return findings


def detect_graph_consistency(diff=False, deep=False, *, loader=None):
    """Graph self-integrity via the Phase-9 generator's OWN gate
    (`generate_docs.load_graph`: content-hash recompute + schema-major pin —
    the R-10 hand-edit guard, IMPORTED). Its refusal = BLOCKER (a hand-edited
    or schema-drifted graph means every generated artifact lies)."""
    if loader is None:
        scripts = os.path.join(REPO_ROOT, "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import generate_docs
        loader = generate_docs.load_graph
    try:
        loader()
    except SystemExit as e:
        return [Finding(id="d3.consistency.graph-integrity", domain="docs-graph",
                        severity=BLOCKER, evidence={"refusal": str(e)[:200]},
                        venue="graph")]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        return [Finding(id="d3.consistency.graph-unreadable", domain="docs-graph",
                        severity=BLOCKER, evidence={"error": str(e)[:200]},
                        venue="graph")]
    return []
