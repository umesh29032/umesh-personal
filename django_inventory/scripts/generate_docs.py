#!/usr/bin/env python3
"""Phase-9 documentation generator — graph-only, deterministic, stdlib-only.

Law (PHASE_09 §2.1 + GEN-D1..D9, all owner-ratified 2026-07-13):
- INPUT = docs/knowledge_graph.json (verified: content-hash recompute + schema major-1 pin)
  + the versioned templates in scripts/doc_templates/. NEVER code, NEVER other docs, NEVER DB.
- OUTPUT = whole `generated`-class markdown files under --out (explicit, required — no
  default corpus path, so an accidental corpus write is impossible). Total overwrite (GEN-D3).
- DETERMINISM (GEN-D4/D6): selections sorted by node id · LF · trailing newline · NO
  wall-clock dates anywhere (frontmatter `verified` = graph:<hash12>, per the OI-1/A3
  amendment principle) · byte-identical output for identical graph+templates.
- HONEST ABSENCE: an edge kind the graph lacks renders as a "not machine-known" line naming
  the Phase-8 residual — never an invented fact (cards cite, never assert).

Target classes (v1 mandatory trio minus manifest-view, which is GEN-D and carries a
classified graph-gap finding — see DOCUMENTATION_GENERATION_LOG.md §GEN-A):
  url-card         one per url node → <feature_slug|_unassigned>/<url_name>.md   (R4/R8)
  feature-doc      one per feature node → <slug>/README.md
  features-index   one master README.md

Run:  env/bin/python scripts/generate_docs.py --out <dir> [--sample]
      --sample renders exactly one url-card + its feature-doc + the index (GEN-A evidence).
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
from string import Template

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(REPO, "docs", "knowledge_graph.json")
TPL_DIR = os.path.join(REPO, "scripts", "doc_templates")
TEMPLATE_VERSION = "1.0.0"   # bump on ANY template change (GEN-D6 version stamp)
SCHEMA_MAJOR_PIN = 1         # refuse a graph whose schema major exceeds this (PHASE_08 §6.6)


def load_graph():
    """Read-only verification per the R-10 law: hash recompute + schema pin, no rebuild."""
    raw = io.open(GRAPH, encoding="utf-8").read()
    g = json.loads(raw)
    blank = dict(g, meta=dict(g["meta"], content_hash="sha256:" + "0" * 64))
    body = (json.dumps(blank, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            ).replace("sha256:" + "0" * 64, "", 1)
    calc = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    if calc != g["meta"]["content_hash"]:
        sys.exit("REFUSED: graph content-hash mismatch (hand-edit guard) — rebuild the graph")
    major = int(g["meta"]["schema_version"].split(".")[0])
    if major > SCHEMA_MAJOR_PIN:
        sys.exit(f"REFUSED: graph schema major {major} exceeds generator pin {SCHEMA_MAJOR_PIN}")
    return g


def tpl(name):
    text = io.open(os.path.join(TPL_DIR, name), encoding="utf-8").read()
    # the first line is template-file provenance, NOT output content — stripping it keeps
    # frontmatter as line 1 of every output (frontmatter parsers require '---' first)
    if text.startswith("<!-- template:"):
        text = text.split("\n", 1)[1]
    return Template(text)


def write(out_dir, rel, text):
    p = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)


def slug_for_file(u):
    """Deterministic card filename stem for a url node (R8: <url_name>.md)."""
    return u["url_name"] or u["id"].split(":", 1)[1].replace(":", "__")


# Route namespaces that get NO url-card (2026-08-03 audit).
#
# `docs/features/` is a FEATURE-knowledge surface for this factory. Django's admin
# and allauth's auth pages are framework-provided CRUD: auto-generated one per
# model x action, carrying zero business meaning. They made up **314 of 538**
# cards in `_unassigned/` (58%) and actively drowned the 224 real app URLs — the
# folder could not be navigated, which was the whole point of building it.
#
# Worse than noise in one case: a card titled `admin_expense_workerledgerentry_delete`
# presents "delete a ledger entry" as a documented feature, when the ledger is
# append-only by design (ADR-0009 / ch 12). Removing it removes a wrong message.
#
# Nothing is lost: INV-4b allows a url to have ZERO cards (`documented_by <= 1`),
# the url NODES stay in the graph either way, and doc nodes are derived from disk —
# so an ungenerated card creates no dangling reference. The admin remains reachable
# and unchanged; it simply is not documented as a product feature.
_CARDLESS_NAMESPACES = ("admin", "_unnamed")
_CARDLESS_PREFIXES = ("account_", "socialaccount_", "google_")


def _wants_card(uid):
    """False for framework routes (Django admin / allauth). See above.

    The namespace is read from the node ID (`url:<namespace>:<name>`), which is the
    only place it reliably lives — `url_name` is None for unnamed routes and `label`
    holds the URL PATH, not the name.
    """
    parts = uid.split(":")
    if len(parts) < 2:
        return True                      # unexpected shape → keep the card
    # Two shapes exist in the graph:
    #   url:<namespace>:<name>   e.g. url:admin:index, url:learning:chapter
    #   url:<name>               e.g. url:account_login  (allauth: no namespace)
    ns = parts[1]
    name = ":".join(parts[2:]) if len(parts) > 2 else parts[1]
    if ns in _CARDLESS_NAMESPACES:
        return False
    return not (ns.startswith(_CARDLESS_PREFIXES)
                or name.startswith(_CARDLESS_PREFIXES))


def build_model(g):
    nodes = {n["id"]: n for n in g["nodes"]}
    apps = {n["app_label"]: n for n in g["nodes"] if n["kind"] == "app"}
    routes = {e["from"]: e["to"] for e in g["edges"] if e["kind"] == "routes_to"}
    routes = {u: v for u, v in routes.items() if _wants_card(u)}
    url_feat, feat_urls, feat_models = {}, {}, {}
    for e in g["edges"]:
        if e["kind"] != "belongs_to_feature":
            continue
        if e["from"].startswith("url:"):
            url_feat[e["from"]] = e["to"]
            feat_urls.setdefault(e["to"], []).append(e["from"])
        elif e["from"].startswith("model:"):
            feat_models.setdefault(e["to"], []).append(e["from"])
    app_docs = {}
    for e in g["edges"]:
        if e["kind"] == "documented_by" and e["from"].startswith("app:"):
            app_docs.setdefault(e["from"], []).append(e["to"])
    # deterministic collision census: same (dir, filename) from >1 url ⇒ ALL colliders
    # switch to <namespace>__<name>.md (order-independent rule)
    names = {}
    for uid in sorted(routes):
        u = nodes[uid]
        d = url_feat.get(uid, "feature:_unassigned").split(":", 1)[1]
        names.setdefault((d, slug_for_file(u)), []).append(uid)
    collide = {k: v for k, v in names.items() if len(v) > 1}
    fname = {}
    for (d, stem), uids in names.items():
        for uid in uids:
            u = nodes[uid]
            if (d, stem) in collide and u.get("namespace"):
                fname[uid] = f"{u['namespace']}__{stem}.md"
            else:
                fname[uid] = f"{stem}.md"
    return dict(nodes=nodes, apps=apps, routes=routes, url_feat=url_feat,
                feat_urls=feat_urls, feat_models=feat_models, app_docs=app_docs,
                fname=fname, collide=collide)


def derive_app(view, apps):
    """Deterministic display derivation (NOT a graph edge): view module's first segment
    matched exact-token against app labels; no match = honestly not derivable."""
    seg = view["module"].split(".")[0]
    return apps.get(seg)


def doc_link(nodes, did, depth):
    n = nodes[did]
    path = n["path"] if n["kind"] == "doc" else n["anchors"][0]
    rel = "../" * depth + os.path.relpath(path, "docs")
    return f"[{path}]({rel})"   # full path as label — basenames (README.md ×N) are ambiguous


def render_card(g, m, uid, common):
    nodes, u = m["nodes"], m["nodes"][uid]
    v = nodes[m["routes"][uid]]
    app = derive_app(v, m["apps"])
    if app:
        docs = m["app_docs"].get(app["id"], [])
        links = " · ".join(doc_link(nodes, d, 2) for d in sorted(docs)) or "no documented_by targets in the graph"
        app_section = (f"Derived from the view module (`{v['module']}` → app `{app['app_label']}`; "
                       f"a render rule, not a graph edge).\n\nApp documentation: {links}")
    else:
        app_section = ("Not derivable — the view module matches no project app label "
                       "(vendor or config-level view).")
    fid = m["url_feat"].get(uid)
    if fid:
        f = nodes[fid]
        feature_section = f"[{f['label']}](README.md) (`{f['slug']}`, via `belongs_to_feature`)"
        governing = f"Feature seed: `{f['seed_source']}`"
    else:
        feature_section = ("None machine-provable — no `belongs_to_feature` edge for this url "
                           "(fix at source: enrich FEATURE_INDEX, rebuild, regenerate).")
        governing = "None machine-known at route grain — see the app documentation above."
    dirname = (nodes[fid]["slug"] if fid else "_unassigned")
    body = tpl("url_card.md.tpl").substitute(
        card_id=f"url-card-{re.sub(r'[^a-z0-9]+', '-', uid[4:].lower()).strip('-')}",
        url_id=uid, route_name=u["label"] or u["id"].split(":", 1)[1],
        namespace=f"`{u['namespace']}`" if u.get("namespace") else "— (none)",
        mount=u["mount"],
        pattern=(f"`{u['pattern']}`" if u["pattern"] else "*(empty — the mount root itself)*"),
        named=str(u["named"]).lower(),
        view_name=v["name"], view_module=v["module"],
        view_anchor=f"`{v['anchors'][0]}`", vendor=str(v["vendor"]).lower(),
        app_section=app_section, feature_section=feature_section,
        governing_docs=governing, anchors=u["anchors"][0], **common)
    return os.path.join(dirname, m["fname"][uid]), body


def render_feature(g, m, fid, common):
    nodes, f = m["nodes"], m["nodes"][fid]
    urls = sorted(m["feat_urls"].get(fid, []))
    if urls:
        rows = ["| Route | Mount | View | Card |", "|---|---|---|---|"]
        for uid in urls:
            u, v = nodes[uid], nodes[m["routes"][uid]]
            rows.append(f"| `{uid[4:]}` | `{u['mount']}` | `{v['name']}` "
                        f"| [{m['fname'][uid]}]({m['fname'][uid]}) |")
        routes_section = "\n".join(rows)
    else:
        routes_section = ("No machine-provable member routes — this feature row carries no "
                          "exact-token url reference (Phase-8 residual R-5 class). Fix at "
                          "source: enrich FEATURE_INDEX, rebuild the graph, regenerate.")
    models = sorted(m["feat_models"].get(fid, []))
    if models:
        rows = ["| Model | Table | Single writer |", "|---|---|---|"]
        for mid in models:
            n = nodes[mid]
            rows.append(f"| `{mid[6:]}` | `{n['table']}` | "
                        f"{('`' + n['single_writer'] + '`') if n.get('single_writer') else 'not machine-known'} |")
        models_section = "\n".join(rows)
    else:
        models_section = "No machine-provable member models (`belongs_to_feature` model edges: 0)."
    seen, apps_lines = set(), []
    for uid in urls:
        app = derive_app(nodes[m["routes"][uid]], m["apps"])
        if app and app["id"] not in seen:
            seen.add(app["id"])
            # depth 2: feature READMEs live at docs/features/<slug>/ — two levels below docs/
            docs = " · ".join(doc_link(nodes, d, 2) for d in sorted(m["app_docs"].get(app["id"], [])))
            apps_lines.append(f"- `{app['app_label']}` — {docs or 'no documented_by targets'}")
    apps_section = ("\n".join(apps_lines) if apps_lines
                    else "Not derivable — no member routes with project-app views.")
    body = tpl("feature_readme.md.tpl").substitute(
        doc_id=f"feature-{f['slug']}", slug=f["slug"], label=f["label"],
        seed_source=f"`{f['seed_source']}`", anchors=f["anchors"][0],
        routes_section=routes_section, models_section=models_section,
        apps_section=apps_section,
        governing_docs=f"Seed row: `{f['seed_source']}` (the feature's source of truth).",
        **common)
    return os.path.join(f["slug"], "README.md"), body


def render_unassigned_index(g, m, common):
    """Generated index for the _unassigned bucket — every card must be reachable from an
    index (PHASE_09 §3.6 no-orphans); a bare directory link would orphan these cards."""
    nodes = m["nodes"]
    uids = sorted(u for u in m["routes"] if u not in m["url_feat"])
    rows = ["| Route | Mount | View | Card |", "|---|---|---|---|"]
    for uid in uids:
        u, v = nodes[uid], nodes[m["routes"][uid]]
        rows.append(f"| `{uid[4:]}` | `{u['mount']}` | `{v['name']}` "
                    f"| [{m['fname'][uid]}]({m['fname'][uid]}) |")
    body = tpl("feature_readme.md.tpl").substitute(
        doc_id="feature-unassigned", slug="_unassigned",
        label="(no machine-provable feature)",
        seed_source="`docs/knowledge_graph.json` (urls with zero `belongs_to_feature` edges)",
        anchors="docs/knowledge_graph.json",
        routes_section="\n".join(rows),
        models_section="Not applicable — this is the coverage-gap bucket, not a feature.",
        apps_section="See each card's App section.",
        governing_docs=("This bucket is the countable FEATURE_INDEX coverage gap: assigning a "
                        "route = add its exact url token to a FEATURE_INDEX row, rebuild the "
                        "graph, regenerate — the card then moves to its feature directory."),
        **common)
    return os.path.join("_unassigned", "README.md"), body


def render_index(g, m, common):
    feats = sorted((n["slug"], n) for n in g["nodes"] if n["kind"] == "feature")
    rows = []
    for slug, f in feats:
        nr = len(m["feat_urls"].get(f["id"], []))
        nm = len(m["feat_models"].get(f["id"], []))
        rows.append(f"| {f['label']} | `{slug}` | {nr} | {nm} | [{slug}/](./{slug}/README.md) |")
    unassigned = len(m["routes"]) - len(m["url_feat"])
    rows.append(f"| _(no machine-provable feature)_ | `_unassigned` | {unassigned} | — "
                f"| [_unassigned/](./_unassigned/README.md) |")
    coverage = (f"- url nodes: {len(m['routes'])} → cards: {len(m['routes'])} (1:1)\n"
                f"- urls with machine-provable feature membership: {len(m['url_feat'])} · "
                f"in `_unassigned`: {unassigned}\n"
                f"- feature nodes: {len(feats)} → feature docs: {len(feats)}\n"
                f"- membership is exact-token evidence from FEATURE_INDEX (Phase-8 law) — "
                f"growing it = enrich FEATURE_INDEX at source, rebuild, regenerate.")
    body = tpl("features_index.md.tpl").substitute(
        feature_rows="\n".join(rows), coverage=coverage, **common)
    return "README.md", body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output dir (explicit — no default)")
    ap.add_argument("--sample", action="store_true",
                    help="GEN-A mode: one card + its feature doc + the index only")
    a = ap.parse_args()
    g = load_graph()
    m = build_model(g)
    common = dict(graph12=g["meta"]["content_hash"][7:19],
                  schema_version=g["meta"]["schema_version"],
                  template_version=TEMPLATE_VERSION)
    outputs = []
    if a.sample:
        uid = sorted(m["url_feat"])[0]              # deterministic sample pick
        outputs.append(render_card(g, m, uid, common))
        outputs.append(render_feature(g, m, m["url_feat"][uid], common))
    else:
        for uid in sorted(m["routes"]):
            outputs.append(render_card(g, m, uid, common))
        for n in sorted((n for n in g["nodes"] if n["kind"] == "feature"),
                        key=lambda n: n["id"]):
            outputs.append(render_feature(g, m, n["id"], common))
        outputs.append(render_unassigned_index(g, m, common))
    outputs.append(render_index(g, m, common))
    for rel, body in outputs:
        write(a.out, rel, body)
    pruned = [] if a.sample else prune_orphans(a.out, {rel for rel, _ in outputs})
    sys.stderr.write(f"rendered {len(outputs)} files -> {a.out} "
                     f"(graph {common['graph12']}, tpl v{TEMPLATE_VERSION}, "
                     f"collisions resolved: {len(m['collide'])}"
                     + (f", pruned {len(pruned)} orphan(s)" if pruned else "") + ")\n")
    for rel in pruned:
        sys.stderr.write(f"  pruned orphan: {rel}\n")


# The exact marker every generated card carries (same string d4_generated.py keys
# on). A file WITHOUT it is hand-written and must never be pruned.
GENERATED_BANNER = "⚙️ GENERATED — an index, not truth"


def prune_orphans(out_dir, written):
    """Delete generated cards this run no longer emits. Returns what was removed.

    WHY (2026-08-03): the generator only ever WROTE. Any file it stopped emitting
    stayed on disk forever as a stale duplicate — same `id:`, old graph stamp — and
    `knowledge_sync` then reported it as drift. That happened twice in one session:

      • `learning:*` cards moved out of `_unassigned/` once the feature was
        registered in FEATURE_INDEX, leaving 9 copies behind;
      • `admin:index` reverted from `admin__index.md` to `index.md` when that move
        dissolved the filename collision, leaving the namespaced copy behind.

    SAFETY — this can only ever delete a file the generator itself produced:
      1. it must sit under `out_dir`;
      2. it must carry the generated banner (hand-written files never do — that is
         exactly how `HUMAN_GUIDE.md` survives, and why we do not special-case names);
      3. it must NOT be in this run's output set.
    All three must hold. A file failing any check is left completely alone.
    """
    import os
    removed = []
    for root, dirs, files in os.walk(out_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, out_dir)
            if rel in written:
                continue
            try:
                head = io.open(path, encoding="utf-8").read(4096)
            except OSError:                       # pragma: no cover
                continue
            if GENERATED_BANNER not in head:      # hand-written → never touch
                continue
            os.remove(path)
            removed.append(rel)
    return removed


if __name__ == "__main__":
    main()
