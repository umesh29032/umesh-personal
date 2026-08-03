#!/usr/bin/env python3
"""Knowledge Graph builder — Phase 8 KG-C (contract PHASE_08_KNOWLEDGE_GRAPH.md; Design
Record KG-D1..D9 ratified 2026-07-13; schema docs/knowledge_graph.schema.json v1.0.0).

READ-ONLY over inputs (code + corpus); writes ONLY docs/knowledge_graph.json.
Deterministic (KG-D4): sorted walks, canonical serialization, zero wall-clock timestamps,
content_hash = sha256 of the hash-blanked canonical body. Every edge carries its declared
extraction source (schema enum) — nothing inferred, nothing runtime-traced.

Evidence-absence law (owner, KG-C): a relationship that cannot be PROVEN from a certified
register stays ABSENT and is counted in the builder's stderr report — never guessed.
Absent-by-design in v1 first build (classified in the build log):
  * calls (view->service): no certified machine-extractable register at that grain exists.
  * gated_by: no gate census artifact exists (RBAC truth stays in code regardless).
  * supersedes: no ACTIVE-tree doc carries a strict single-successor banner (archive docs
    are outside the v1 node set).

Run:  env/bin/python scripts/build_knowledge_graph.py   (from repo root)
"""
import hashlib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "config"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django  # noqa: E402

django.setup()

from django.apps import apps as django_apps  # noqa: E402
from django.urls import get_resolver  # noqa: E402
from django.urls.resolvers import URLPattern, URLResolver  # noqa: E402

GRAPH_PATH = os.path.join(REPO, "docs", "knowledge_graph.json")
MANIFEST_PATH = os.path.join(REPO, "docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json")

VENDOR_PREFIXES = ("django.", "allauth.", "debug_toolbar.")


def slugify(s, maxlen=80):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:maxlen] or "root"


# ---------------------------------------------------------------- apps
def project_apps():
    labels = sorted(
        d for d in os.listdir(os.path.join(REPO, "config"))
        if os.path.exists(os.path.join(REPO, "config", d, "apps.py"))
    )
    return [a for a in sorted(django_apps.get_app_configs(), key=lambda x: x.label)
            if a.label in labels]


# ---------------------------------------------------------------- urls + views
def walk_urls():
    rows = []

    def rec(resolver, ns_stack, prefix):
        for p in resolver.url_patterns:
            if isinstance(p, URLResolver):
                rec(p, ns_stack + ([p.namespace] if p.namespace else []),
                    prefix + str(p.pattern))
            elif isinstance(p, URLPattern):
                cb = p.callback
                view = getattr(cb, "view_class", None)
                if view is not None:
                    vid = f"{view.__module__}.{view.__name__}"
                    vmod, vname = view.__module__, view.__name__
                else:
                    f = getattr(cb, "__wrapped__", cb)
                    vid = f"{f.__module__}.{getattr(f, '__qualname__', f.__name__)}"
                    vmod = f.__module__
                    vname = getattr(f, "__qualname__", f.__name__)
                rows.append({
                    "namespace": ":".join(ns_stack),
                    "url_name": p.name,
                    "pattern": str(p.pattern),
                    "mount": prefix + str(p.pattern),
                    "view_key": vid, "view_module": vmod, "view_name": vname,
                })

    rec(get_resolver(), [], "/")
    return rows


def url_node_id(r):
    if r["url_name"]:
        return (f"url:{r['namespace']}:{r['url_name']}" if r["namespace"]
                else f"url:{r['url_name']}")
    return f"url:_unnamed:{slugify(r['mount'])}"


def module_anchor(module):
    """repo-relative file path for a project module; None for vendor."""
    if module.startswith(VENDOR_PREFIXES):
        return None
    cand = os.path.join(REPO, "config", *module.split(".")) + ".py"
    if os.path.exists(cand):
        return os.path.relpath(cand, REPO)
    pkg = os.path.join(REPO, "config", *module.split("."), "__init__.py")
    if os.path.exists(pkg):
        return os.path.relpath(pkg, REPO)
    return None


# ---------------------------------------------------------------- docs (DD-1 active boundary)
DOC_TIER_TYPE_RULES = "census-heuristic (DOCDISC-A adjudicated rules, re-implemented verbatim)"

T1_ROOT = {"PRODUCT_DESIGN_DOCUMENT.md", "MANUFACTURING_V1_FREEZE.md", "ARCHITECTURE_V2.md",
           "PRE_S1_DESIGN_ADDENDUM.md", "FACTORY_OPERATIONS_MASTER.md", "DOC_STANDARDS.md",
           "REQUIREMENT_REVIEW_STAGE_TRACKING.md"}
T0_ROOT = {"START_HERE.md", "DOCUMENTATION_INDEX.md", "PROJECT_KNOWLEDGE_MAP.md"}
STATUSY = re.compile(r"(STATUS|BACKLOG|TRACKER|PENDING|CHECKLIST)")
RECEIPTY = re.compile(r"(RECEIPT|EXECUTION_PLAN|AUDIT|REVIEW|REPORT|SUMMARY|_LOG|LEDGER|"
                      r"HANDOFF|CHALLENGE|HOSTILE|SWEEP|CERTIFICATION)")


def census_tier_type(rel, fn):
    if rel.startswith("docs/adr/"):
        return ("T1", "adr") if re.match(r"\d{4}-", fn) else ("T1", "entry-index")
    if rel.startswith("docs/campaign_contracts/"):
        return "T5", "campaign-contract"
    if rel.startswith("docs/apps/"):
        return ("T3", "entry-index") if fn == "README.md" else ("T3", "app-guide")
    if rel.startswith("docs/PAGES/"):
        return ("T2", "entry-index") if fn == "README.md" else ("T2", "page-contract")
    if rel.startswith(("docs/production/", "docs/tracking/")):
        return "T2", "topic-canonical"
    if rel.startswith("docs/LEARNING/"):
        return ("T6", "entry-index") if fn == "README.md" else ("T6", "lesson")
    if rel.startswith("docs/LEARNING_2_0/"):
        sub = rel.split("/")[2] if len(rel.split("/")) > 2 else ""
        m = {"DATA_FLOWS": "data-flow", "REQUEST_JOURNEYS": "request-journey",
             "CHOKEPOINTS": "chokepoint", "DATABASE_GUIDE": "database-guide"}
        if fn.endswith(".json") or fn == "COVERAGE_REPORT.md":
            return ("T0", "machine-index") if fn.endswith(".json") else ("T6", "machine-index")
        if fn == "README.md" or fn == "PROJECT_ATLAS.md":
            return ("T2" if sub == "CHOKEPOINTS" else "T6", "entry-index")
        if sub in m:
            return ("T2" if sub == "CHOKEPOINTS" else "T6", m[sub])
        if sub == "AI_AGENT_GUIDE":
            return "T0", "entry-index"
        if fn == "URL_ATLAS.md":
            return "T2", "topic-canonical"
        return "T6", "topic-canonical"
    if rel.startswith("config/"):
        return "T3", "app-readme"
    if rel == "deploy/README.md":
        return "T2", "topic-canonical"
    if fn in T1_ROOT:
        return "T1", "truth-lock"
    if fn in T0_ROOT:
        return "T0", "entry-index"
    if fn == "CLAUDE.md":
        return "T0", "entry-index"
    if fn.endswith("_CERTIFICATION.md") or fn in (
            "CONFIRMED_FINDINGS_LEDGER.md", "DOCUMENT_DISCOVERY_REPORT.md",
            "DOCUMENT_CLEANUP_LOG.md", "KNOWLEDGE_GRAPH_BUILD_LOG.md",
            "DOCUMENT_CLEANUP_CERTIFICATION.md"):
        return "T7", "evidence-cert"
    if STATUSY.search(fn):
        return "T5", "status-anchor"
    if RECEIPTY.search(fn) or re.search(r"_20\d{2}_\d{2}_\d{2}\.md$", fn):
        return "T7", "receipt"
    if fn == "CHANGELOG.md":
        return "T5", "status-anchor"
    return "T2", "topic-canonical"


def parse_frontmatter(path):
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    if not txt.startswith("---\n"):
        return None
    parts = txt.split("---\n", 2)
    if len(parts) < 3:
        return None
    fm = {}
    for line in parts[1].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def doc_boundary():
    docs = []
    for root, dnames, names in os.walk(os.path.join(REPO, "docs")):
        rel = os.path.relpath(root, REPO)
        if rel.startswith("docs/archive"):
            continue
        for n in sorted(names):
            if n.endswith((".md", ".json")):
                rel_f = os.path.relpath(os.path.join(root, n), REPO)
                # determinism guard: the graph must not node ITSELF — first build would
                # lack the node, second would have it (self-inclusion instability, KG-D4)
                if rel_f == "docs/knowledge_graph.json":
                    continue
                docs.append(rel_f)
    for c in ["README.md", "CHANGELOG.md", "CLAUDE.md", "GLOSSARY.md", "SYSTEM_DESIGN.md",
              "UI_COMPONENTS.md", "ABOUT_THIS_PROJECT.md", "deploy/README.md"]:
        if os.path.exists(os.path.join(REPO, c)):
            docs.append(c)
    for a in project_apps():
        p = f"config/{a.label}/README.md"
        if os.path.exists(os.path.join(REPO, p)):
            docs.append(p)
    return sorted(set(docs))


# ---------------------------------------------------------------- never_modify writer map
def writer_edges(models_by_name, absent):
    """service->model writes edges from the manifest never_modify register (certified,
    ADR-0002). Deterministic model-name resolution: unique registry-name match only."""
    manifest = json.load(open(MANIFEST_PATH))
    edges = []
    for row in manifest["never_modify"]:
        writer = row["only_writer"]  # e.g. config/expense/services/ledger_service.py
        m = re.match(r"config/([a-z_]+)/services/([a-z0-9_]+)\.py", writer)
        if not m:
            absent.append(f"never_modify writer unparsable: {writer}")
            continue
        sid = f"service:{m.group(1)}.{m.group(2)}"
        target = row["target"]
        names = re.findall(r"[A-Z][A-Za-z0-9]+", target)
        if "History" in target and "*History" in target:
            names = [n for n in models_by_name if n.endswith("History")]
        matched = False
        for name in names:
            hits = models_by_name.get(name, [])
            if len(hits) == 1:
                edges.append((sid, f"model:{hits[0]}.{name}", "writes",
                              "register:never_modify"))
                matched = True
            elif len(hits) > 1:
                absent.append(f"ambiguous model name '{name}' in never_modify target "
                              f"'{target}' — edge ABSENT, not guessed")
        if not matched and not names:
            absent.append(f"never_modify target '{target}' names no registry model "
                          f"(non-model target) — writes edge ABSENT by evidence")
    return edges


# ---------------------------------------------------------------- build
def build():
    absent = []          # loud absence report (owner rule)
    nodes = {}
    edges = []

    def add_node(n):
        if n["id"] in nodes:
            raise SystemExit(f"BUILD FAILURE: duplicate node id {n['id']} "
                             f"(collision = source finding, never auto-suffixed)")
        nodes[n["id"]] = n

    apps_ = project_apps()
    for a in apps_:
        add_node({"id": f"app:{a.label}", "kind": "app", "label": a.label,
                  "anchors": [f"config/{a.label}/"], "app_label": a.label})

    # models
    models_by_name = {}
    for a in apps_:
        for m in sorted(a.get_models(), key=lambda m: m.__name__):
            models_by_name.setdefault(m.__name__, []).append(a.label)
    single_writer = {}
    for a in apps_:
        for m in sorted(a.get_models(), key=lambda m: m.__name__):
            anchor = module_anchor(m.__module__) or f"config/{a.label}/"
            add_node({"id": f"model:{a.label}.{m.__name__}", "kind": "model",
                      "label": f"{a.label}.{m.__name__}", "anchors": [anchor],
                      "app_label": a.label, "model_name": m.__name__,
                      "table": m._meta.db_table, "single_writer": None})

    w_edges = writer_edges(models_by_name, absent)
    for sid, mid, kind, src in w_edges:
        if mid in nodes:
            nodes[mid]["single_writer"] = sid

    # urls + views
    url_rows = walk_urls()
    view_nodes = {}
    for r in url_rows:
        vid = f"view:{r['view_key']}"
        if vid not in view_nodes:
            vendor = r["view_module"].startswith(VENDOR_PREFIXES)
            anchor = module_anchor(r["view_module"])
            view_nodes[vid] = {
                "id": vid, "kind": "view", "label": r["view_name"],
                "anchors": [anchor] if anchor else [r["mount"]],
                "module": r["view_module"], "name": r["view_name"], "vendor": vendor}
        else:
            if r["mount"] not in view_nodes[vid]["anchors"] and \
               view_nodes[vid]["anchors"][0].startswith("/"):
                view_nodes[vid]["anchors"].append(r["mount"])
    for v in view_nodes.values():
        v["anchors"] = sorted(set(v["anchors"]))
        add_node(v)

    seen_urls = set()
    for r in url_rows:
        uid = url_node_id(r)
        if uid in seen_urls:
            raise SystemExit(f"BUILD FAILURE: url id collision {uid} "
                             f"(unnamed-slug or duplicate name — source finding)")
        seen_urls.add(uid)
        node = {"id": uid, "kind": "url",
                "label": r["url_name"] or r["mount"],
                "anchors": ["config/config/urls.py"],
                "pattern": r["pattern"], "mount": r["mount"],
                "named": bool(r["url_name"])}
        if r["namespace"]:
            node["namespace"] = r["namespace"]
        node["url_name"] = r["url_name"]
        add_node(node)
        edges.append({"from": uid, "to": f"view:{r['view_key']}",
                      "kind": "routes_to", "source": "urlconf"})

    # services
    for a in apps_:
        d = os.path.join(REPO, "config", a.label, "services")
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".py") and f != "__init__.py" and not f.startswith("_"):
                mod = f[:-3]
                sid = f"service:{a.label}.{mod}"
                sw = sorted(mid for (s, mid, k, src) in w_edges if s == sid)
                n = {"id": sid, "kind": "service", "label": f"{a.label}.{mod}",
                     "anchors": [f"config/{a.label}/services/{f}"],
                     "app_label": a.label, "module": mod}
                if sw:
                    n["single_writer_of"] = sw
                add_node(n)
    for sid, mid, kind, src in w_edges:
        edges.append({"from": sid, "to": mid, "kind": kind, "source": src})

    # docs
    boundary = doc_boundary()
    fm_used = 0
    for rel in boundary:
        fn = os.path.basename(rel)
        tier, dtype = census_tier_type(rel, fn)
        owner_class = ("append-only" if dtype in ("receipt", "evidence-cert")
                       else "frozen" if dtype in ("adr", "truth-lock", "campaign-contract")
                       else "handwritten")
        lifecycle = "unknown"
        if rel.endswith(".md"):
            fm = parse_frontmatter(os.path.join(REPO, rel))
            if fm:
                fm_used += 1
                tier = fm.get("tier", tier)
                dtype = fm.get("type", dtype)
                owner_class = fm.get("owner", owner_class)
                lifecycle = fm.get("status", "unknown")
            else:
                lifecycle = ("frozen" if dtype in ("adr", "truth-lock", "campaign-contract")
                             else "unknown")
        else:
            dtype = "machine-index"
            lifecycle = "active"
        add_node({"id": f"doc:{rel}", "kind": "doc", "label": fn,
                  "anchors": [rel], "path": rel, "tier": tier, "doc_type": dtype,
                  "owner_class": owner_class, "lifecycle": lifecycle})

    # documented_by (deterministic filename-match rules over certified registers)
    for a in apps_:
        for tgt in (f"config/{a.label}/README.md", f"docs/apps/{a.label}/GUIDE.md"):
            if f"doc:{tgt}" in nodes:
                edges.append({"from": f"app:{a.label}", "to": f"doc:{tgt}",
                              "kind": "documented_by", "source": "register:guide"})
    for a in apps_:
        for m in sorted(a.get_models(), key=lambda m: m.__name__):
            snake = re.sub(r"(?<!^)(?=[A-Z])", "_", m.__name__).lower()
            tgt = f"docs/LEARNING_2_0/DATABASE_GUIDE/{snake}.md"
            if f"doc:{tgt}" in nodes:
                edges.append({"from": f"model:{a.label}.{m.__name__}", "to": f"doc:{tgt}",
                              "kind": "documented_by", "source": "register:guide"})
    choke_dir = os.path.join(REPO, "docs/LEARNING_2_0/CHOKEPOINTS")
    choke_pages = {f[:-3] for f in os.listdir(choke_dir) if f.endswith(".md")}
    for nid, n in list(nodes.items()):
        if n["kind"] == "service" and n["module"] in choke_pages:
            edges.append({"from": nid,
                          "to": f"doc:docs/LEARNING_2_0/CHOKEPOINTS/{n['module']}.md",
                          "kind": "documented_by", "source": "register:chokepoints"})
    unmatched_choke = choke_pages - {n["module"] for n in nodes.values()
                                     if n["kind"] == "service"} - {"README"}
    for c in sorted(unmatched_choke):
        absent.append(f"chokepoint page '{c}.md' matches no service module by filename "
                      f"rule — documented_by ABSENT (manual mapping not machine-provable)")

    # features + belongs_to_feature (FEATURE_INDEX parse, exact-token matches only)
    fi = io.open(os.path.join(REPO, "docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md"),
                 encoding="utf-8").read()
    rows = [l for l in fi.splitlines()
            if l.startswith("| ") and "---" not in l and not l.startswith("| Feature")]
    for row in rows:
        cells = [c.strip() for c in row.split("|")[1:-1]]
        name = cells[0]
        slug = slugify(re.sub(r"\(.*?\)", "", name), 60).strip("-") or slugify(name, 60)
        fid = f"feature:{slug}"
        add_node({"id": fid, "kind": "feature", "label": name,
                  "anchors": ["docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md"],
                  "slug": slug,
                  "seed_source": "docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md"})
        linked = False
        if len(cells) > 1:
            for tok in re.findall(r"[a-z_]+:[a-z0-9_-]+", cells[1]):
                uid = f"url:{tok}"
                if uid in nodes:
                    edges.append({"from": uid, "to": fid,
                                  "kind": "belongs_to_feature", "source": "feature_index"})
                    linked = True
        if len(cells) > 4:
            for tok in re.findall(r"[A-Z][A-Za-z0-9]+", cells[4]):
                hits = models_by_name.get(tok, [])
                if len(hits) == 1:
                    edges.append({"from": f"model:{hits[0]}.{tok}", "to": fid,
                                  "kind": "belongs_to_feature", "source": "feature_index"})
                    linked = True
        if not linked:
            absent.append(f"feature '{slug}': no exact-token url/model match in its row — "
                          f"belongs_to_feature edges ABSENT, not guessed")

    # adrs + cites (manifest-derived only)
    adr_dir = os.path.join(REPO, "docs/adr")
    for f in sorted(os.listdir(adr_dir)):
        m = re.match(r"(\d{4})-", f)
        if not m:
            continue
        txt = io.open(os.path.join(adr_dir, f), encoding="utf-8", errors="replace").read()
        sm = re.search(r"\*?\*?Status\*?\*?[:\s]+([A-Za-z][A-Za-z ]*)", txt)
        status = sm.group(1).strip() if sm else "unstated"
        add_node({"id": f"adr:{m.group(1)}", "kind": "adr", "label": f,
                  "anchors": [f"docs/adr/{f}"], "number": int(m.group(1)),
                  "status": status})
    manifest = json.load(open(MANIFEST_PATH))
    for t in manifest["topics"]:
        c = t["canonical"]
        for also in t.get("also", []):
            am = re.match(r"docs/adr/(\d{4})-", also)
            if am and f"doc:{c}" in nodes:
                edges.append({"from": f"doc:{c}", "to": f"adr:{am.group(1)}",
                              "kind": "cites", "source": "manifest"})
            elif f"doc:{c}" in nodes and f"doc:{also}" in nodes:
                edges.append({"from": f"doc:{c}", "to": f"doc:{also}",
                              "kind": "cites", "source": "manifest"})

    # ---- loud-absence classes (owner rule: absent-not-inferred, never silent) ----
    absent.insert(0, "EDGE-KIND calls: ABSENT in v1 first build — no certified "
                     "machine-extractable view->service register exists (GUIDE tables are "
                     "file-grain); classified, never inferred")
    absent.insert(1, "EDGE-KIND gated_by: ABSENT — no gate-census artifact exists; RBAC "
                     "truth stays in code; candidate future instrument")
    absent.insert(2, "EDGE-KIND supersedes: ABSENT — no ACTIVE-tree doc carries a strict "
                     "single-successor banner (RAW_MATERIALS lifecycle=superseded names TWO "
                     "live-truth pointers -> not a provable single successor; classified)")

    # ---- meta + canonical serialization ----
    git_head = "unknown"
    head_file = os.path.join(REPO, ".git", "HEAD")
    if os.path.exists(head_file):
        ref = io.open(head_file).read().strip()
        if ref.startswith("ref: "):
            rf = os.path.join(REPO, ".git", ref[5:])
            if os.path.exists(rf):
                git_head = io.open(rf).read().strip()[:12]
        else:
            git_head = ref[:12]

    census = {
        "app": sum(1 for n in nodes.values() if n["kind"] == "app"),
        "url": sum(1 for n in nodes.values() if n["kind"] == "url"),
        "view_project": sum(1 for n in nodes.values()
                            if n["kind"] == "view" and not n["vendor"]),
        "view_vendor": sum(1 for n in nodes.values()
                           if n["kind"] == "view" and n["vendor"]),
        "service": sum(1 for n in nodes.values() if n["kind"] == "service"),
        "model": sum(1 for n in nodes.values() if n["kind"] == "model"),
        "doc": sum(1 for n in nodes.values() if n["kind"] == "doc"),
        "adr": sum(1 for n in nodes.values() if n["kind"] == "adr"),
        "feature": sum(1 for n in nodes.values() if n["kind"] == "feature"),
    }
    schema_version = json.load(open(
        os.path.join(REPO, "docs", "knowledge_graph.schema.json")
    ))["properties"]["meta"]["properties"]["schema_version"]["description"].split(
        "this schema document is ")[1].split(" ")[0].rstrip(".")
    graph = {
        "meta": {
            "schema_version": schema_version,
            "content_hash": "sha256:" + "0" * 64,
            "built_from": {"git_head": git_head, "census": census},
        },
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["from"], e["kind"], e["to"], e["source"])),
    }

    def canonical(g):
        return json.dumps(g, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    blank = dict(graph, meta=dict(graph["meta"], content_hash="sha256:" + "0" * 64))
    body = canonical(blank).replace("sha256:" + "0" * 64, "", 1)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    graph["meta"]["content_hash"] = f"sha256:{digest}"

    io.open(GRAPH_PATH, "w", encoding="utf-8").write(canonical(graph))

    ec = {}
    for e in graph["edges"]:
        ec[e["kind"]] = ec.get(e["kind"], 0) + 1
    sys.stderr.write("NODES: %s total %d\n" % (census, len(graph["nodes"])))
    sys.stderr.write("EDGES: %s total %d\n" % (ec, len(graph["edges"])))
    sys.stderr.write("frontmatter-sourced doc attrs: see build log\n")
    sys.stderr.write("ABSENCE REPORT (%d, loud-not-silent):\n" % len(absent))
    for a in absent:
        sys.stderr.write("  - %s\n" % a)
    sys.stderr.write("hash: %s\n" % graph["meta"]["content_hash"])


if __name__ == "__main__":
    build()
