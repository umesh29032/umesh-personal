#!/usr/bin/env python3
"""Knowledge Graph validator — Phase 8 KG-D (independent verifier; trusts NOTHING from the
builder). Enforces schema shape + semantic invariants 1-8 (KG-D5, all fatal except the
contract's explicit doc-island orphan-signal carve-out) + determinism/reproducibility +
content-hash. Reads the schema file for its enums (schema-driven where expressible).

Invariant-4 interpretation (KG-C finding C-3, recorded): the single-successor rule
constrains docs that HAVE outgoing supersedes EDGES (each such doc: exactly one), not
lifecycle strings — a doc with lifecycle 'superseded' and zero supersedes edges is an
honest-absence state, reported informationally.

Island rules (contract §6.3-7): app islands FATAL; doc islands = orphan-signal FINDINGS
(counted, routed out, non-fatal); other kinds permit islands (reported informationally).

READ-ONLY except the reproducibility check, which re-runs the builder and byte-compares
against the pre-existing artifact (identical or FAIL — inputs unchanged implies bytes
unchanged).

Run: env/bin/python scripts/validate_knowledge_graph.py
Exit 0 = ALL PASS; exit 1 = fatal invariant violation(s).
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(REPO, "docs", "knowledge_graph.json")
SCHEMA = os.path.join(REPO, "docs", "knowledge_graph.schema.json")

FATAL, FINDINGS, INFO = [], [], []


def check(name, ok, detail=""):
    line = f"{name}: {'PASS' if ok else 'FAIL'}{' — ' + detail if detail else ''}"
    print(("  ✓ " if ok else "  ✗ ") + line)
    if not ok:
        FATAL.append(line)


def main():
    print("== KG-D VALIDATOR ==")
    schema = json.load(open(SCHEMA))
    raw = io.open(GRAPH, encoding="utf-8").read()
    g = json.loads(raw)

    # ---- schema-driven enums ----
    node_kinds = set(schema["definitions"]["node"]["properties"]["kind"]["enum"])
    edge_kinds = set(schema["definitions"]["edge"]["properties"]["kind"]["enum"])
    edge_sources = set(schema["definitions"]["edge"]["properties"]["source"]["enum"])
    doc_allof = {c["if"]["properties"]["kind"]["const"]: c["then"]
                 for c in schema["definitions"]["node"]["allOf"]}
    id_pat = {k: v["properties"]["id"]["pattern"] for k, v in doc_allof.items()}
    kind_req = {k: [r for r in v.get("required", []) if r not in
                    ("id", "kind", "label", "anchors")] for k, v in doc_allof.items()}

    print("\n[1] SCHEMA SHAPE (schema-file-driven)")
    check("top-level keys", set(g.keys()) == {"meta", "nodes", "edges"})
    m = g["meta"]
    check("meta.schema_version 1.x.y", bool(re.match(r"^1\.\d+\.\d+$", m["schema_version"])),
          m["schema_version"])
    check("meta.content_hash format", bool(re.match(r"^sha256:[0-9a-f]{64}$",
                                                    m["content_hash"])))
    census = m["built_from"]["census"]
    check("meta.built_from.census has all 9 denominators",
          set(census.keys()) == {"app", "url", "view_project", "view_vendor", "service",
                                 "model", "doc", "adr", "feature"})
    shape_bad = 0
    for n in g["nodes"]:
        k = n.get("kind")
        if (k not in node_kinds or not re.match(id_pat[k], n["id"])
                or not n.get("anchors")
                or any(r not in n for r in kind_req.get(k, []))):
            shape_bad += 1
            if shape_bad <= 3:
                INFO.append(f"shape offender: {n.get('id')}")
    check(f"node shapes (kinds/id-patterns/required/anchors) over {len(g['nodes'])} nodes",
          shape_bad == 0, f"{shape_bad} offenders {INFO[:3] if shape_bad else ''}")
    e_bad = sum(1 for e in g["edges"]
                if e.get("kind") not in edge_kinds or e.get("source") not in edge_sources
                or "from" not in e or "to" not in e)
    check(f"edge shapes (kind/source enums) over {len(g['edges'])} edges", e_bad == 0)

    print("\n[2] SEMANTIC INVARIANTS 1–8")
    ids = [n["id"] for n in g["nodes"]]
    check("INV-1 id uniqueness", len(ids) == len(set(ids)),
          f"{len(ids)} ids, {len(set(ids))} unique")
    idset = set(ids)
    dangling = [(e["from"], e["to"]) for e in g["edges"]
                if e["from"] not in idset or e["to"] not in idset]
    check("INV-2 referential integrity", not dangling,
          f"{len(dangling)} dangling: {dangling[:3]}")
    check("INV-3 kinds closed", all(n["kind"] in node_kinds for n in g["nodes"]))

    kind_of = {n["id"]: n["kind"] for n in g["nodes"]}
    ENDPOINTS = {"routes_to": ({"url"}, {"view"}),
                 "gated_by": ({"url"}, {"service", "doc"}),
                 "calls": ({"view"}, {"service"}),
                 "writes": ({"service"}, {"model"}),
                 "documented_by": ({"url", "model", "service", "view", "app"}, {"doc"}),
                 "belongs_to_feature": ({"url", "doc", "service", "model"}, {"feature"}),
                 "supersedes": ({"doc"}, {"doc"}),
                 "cites": ({"doc"}, {"doc", "adr"})}
    ek_bad = [e for e in g["edges"]
              if kind_of.get(e["from"]) not in ENDPOINTS[e["kind"]][0]
              or kind_of.get(e["to"]) not in ENDPOINTS[e["kind"]][1]]
    check("endpoint-kind correctness (all 8 edge kinds)", not ek_bad,
          f"{len(ek_bad)} bad: {[(e['from'],e['kind'],e['to']) for e in ek_bad[:3]]}")

    # INV-4 cardinality
    routes = {}
    for e in g["edges"]:
        if e["kind"] == "routes_to":
            routes.setdefault(e["from"], []).append(e["to"])
    url_ids = [n["id"] for n in g["nodes"] if n["kind"] == "url"]
    bad_card = [u for u in url_ids if len(routes.get(u, [])) != 1]
    check("INV-4a every url routes_to exactly 1 view", not bad_card,
          f"{len(bad_card)} violations")
    doc_types = {n["id"]: n.get("doc_type") for n in g["nodes"] if n["kind"] == "doc"}
    cards = {}
    for e in g["edges"]:
        if e["kind"] == "documented_by" and kind_of.get(e["from"]) == "url" \
                and doc_types.get(e["to"]) == "url-card":
            cards[e["from"]] = cards.get(e["from"], 0) + 1
    check("INV-4b url documented_by ≤1 url-card", all(v <= 1 for v in cards.values()),
          f"({len(cards)} url→card edges exist; cards ship in Phase 9)")
    sup = {}
    for e in g["edges"]:
        if e["kind"] == "supersedes":
            sup.setdefault(e["from"], []).append(e["to"])
    check("INV-4c docs WITH supersedes edges have exactly 1 successor "
          "(interpretation per KG-C C-3: edges, not lifecycle strings)",
          all(len(v) == 1 for v in sup.values()), f"{len(sup)} superseding docs")
    sup_status_no_edge = [n["id"] for n in g["nodes"] if n["kind"] == "doc"
                          and str(n.get("lifecycle", "")).startswith("superseded")
                          and n["id"] not in sup]
    if sup_status_no_edge:
        INFO.append(f"INFO: {len(sup_status_no_edge)} doc(s) lifecycle=superseded with 0 "
                    f"supersedes edges (honest absence): {sup_status_no_edge}")

    # INV-5 acyclicity (trivial when 0 edges, still checked)
    seen, stack_flag = {}, {}

    def cyclic(v):
        seen[v] = 1
        for w in sup.get(v, []):
            if seen.get(w) == 1 or (w not in seen and cyclic(w)):
                return True
        seen[v] = 2
        return False
    check("INV-5 supersedes acyclic", not any(cyclic(v) for v in list(sup)),
          f"{sum(len(v) for v in sup.values())} supersedes edges")

    # INV-6 doc paths exist (independent disk check)
    missing = [n["id"] for n in g["nodes"] if n["kind"] == "doc"
               and not os.path.exists(os.path.join(REPO, n["path"]))]
    check("INV-6 every doc path exists on disk", not missing,
          f"{len(missing)} missing: {missing[:3]}")

    # INV-7 islands
    touched = set()
    for e in g["edges"]:
        touched.add(e["from"]); touched.add(e["to"])
    app_islands = [n["id"] for n in g["nodes"] if n["kind"] == "app"
                   and n["id"] not in touched]
    check("INV-7 app islands = 0 (FATAL class)", not app_islands, str(app_islands))
    island_counts = {}
    for n in g["nodes"]:
        if n["id"] not in touched:
            island_counts[n["kind"]] = island_counts.get(n["kind"], 0) + 1
    doc_islands = island_counts.get("doc", 0)
    FINDINGS.append(f"doc islands (orphan-signal FINDINGS, non-fatal per §6.3-7): "
                    f"{doc_islands} — Phase-9 documented_by/card edges are the designed "
                    f"resolution; other-kind islands (permitted): "
                    f"{ {k: v for k, v in island_counts.items() if k != 'doc'} }")

    # INV-8 completeness floors — INDEPENDENT recount (validator's own instruments)
    print("\n[3] COMPLETENESS FLOORS (independent recount)")
    sys.path.insert(0, os.path.join(REPO, "config"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    django.setup()
    from django.apps import apps as dapps
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver
    labels = sorted(d for d in os.listdir(os.path.join(REPO, "config"))
                    if os.path.exists(os.path.join(REPO, "config", d, "apps.py")))
    papps = [a for a in dapps.get_app_configs() if a.label in labels]
    r_model = sum(1 for a in papps for _ in a.get_models())
    r_urls, r_views = [], set()

    def rec(res):
        for p in res.url_patterns:
            if isinstance(p, URLResolver):
                rec(p)
            elif isinstance(p, URLPattern):
                r_urls.append(p)
                cb = p.callback
                v = getattr(cb, "view_class", None)
                if v is not None:
                    r_views.add(f"{v.__module__}.{v.__name__}")
                else:
                    f = getattr(cb, "__wrapped__", cb)
                    r_views.add(f"{f.__module__}.{getattr(f,'__qualname__',f.__name__)}")
    rec(get_resolver())
    r_view_proj = sum(1 for v in r_views
                      if not v.startswith(("django.", "allauth.", "debug_toolbar.")))
    r_service = 0
    for l in labels:
        d = os.path.join(REPO, "config", l, "services")
        if os.path.isdir(d):
            r_service += sum(1 for f in os.listdir(d) if f.endswith(".py")
                             and f != "__init__.py" and not f.startswith("_"))
    r_doc = 0
    for root, dn, names in os.walk(os.path.join(REPO, "docs")):
        if os.path.relpath(root, REPO).startswith("docs/archive"):
            continue
        for n in names:
            if n.endswith((".md", ".json")) and \
                    os.path.relpath(os.path.join(root, n), REPO) != "docs/knowledge_graph.json":
                r_doc += 1
    r_doc += sum(1 for c in ["README.md", "CHANGELOG.md", "CLAUDE.md", "GLOSSARY.md",
                             "SYSTEM_DESIGN.md", "UI_COMPONENTS.md", "ABOUT_THIS_PROJECT.md",
                             "deploy/README.md"] if os.path.exists(os.path.join(REPO, c)))
    r_doc += sum(1 for l in labels
                 if os.path.exists(os.path.join(REPO, f"config/{l}/README.md")))
    r_adr = sum(1 for f in os.listdir(os.path.join(REPO, "docs/adr"))
                if re.match(r"\d{4}-", f))
    fi = io.open(os.path.join(REPO, "docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md"),
                 encoding="utf-8").read()
    r_feat = sum(1 for l in fi.splitlines() if l.startswith("| ")
                 and "---" not in l and not l.startswith("| Feature"))
    built = {k: sum(1 for n in g["nodes"] if n["kind"] == k) for k in node_kinds}
    built["view_project"] = sum(1 for n in g["nodes"]
                                if n["kind"] == "view" and not n["vendor"])
    recount = {"app": len(labels), "url": len(r_urls), "view_project": r_view_proj,
               "service": r_service, "model": r_model, "doc": r_doc, "adr": r_adr,
               "feature": r_feat}
    for k, floor in recount.items():
        have = built.get(k, built.get("view") if k == "view_project" else 0)
        check(f"INV-8 floor {k}: nodes {have} >= recount {floor} (meta says "
              f"{census.get(k, census.get('view_project'))})", have >= floor)

    print("\n[4] CONTENT HASH (independent recompute)")
    blank = dict(g, meta=dict(g["meta"], content_hash="sha256:" + "0" * 64))
    body = (json.dumps(blank, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            ).replace("sha256:" + "0" * 64, "", 1)
    calc = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    check("stored content_hash matches independent recompute (hand-edit guard)",
          calc == m["content_hash"], f"stored {m['content_hash'][:20]}… calc {calc[:20]}…")

    print("\n[5] SERIALIZATION + DETERMINISM")
    reser = json.dumps(g, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    check("on-disk bytes == canonical re-serialization", raw == reser)
    check("nodes sorted by id", ids == sorted(ids))
    ek = [(e["from"], e["kind"], e["to"], e["source"]) for e in g["edges"]]
    check("edges sorted by (from,kind,to,source)", ek == sorted(ek))
    check("no wall-clock timestamps in body",
          not re.search(r"20\d\d-\d\d-\d\dT\d\d:", raw))
    pre = raw
    subprocess.run([os.path.join(REPO, "env/bin/python"),
                    os.path.join(REPO, "scripts/build_knowledge_graph.py")],
                   capture_output=True, cwd=REPO)
    post = io.open(GRAPH, encoding="utf-8").read()
    check("REPRODUCIBILITY: independent builder re-run → byte-identical artifact",
          pre == post)

    print("\n== FINDINGS (non-fatal, routed out) ==")
    for f in FINDINGS + INFO:
        print("  •", f)
    print(f"\n== VERDICT: {'ALL INVARIANTS PASS — GRAPH CERTIFIED AS BUILT' if not FATAL else str(len(FATAL)) + ' FATAL VIOLATION(S)'} ==")
    sys.exit(0 if not FATAL else 1)


if __name__ == "__main__":
    main()
