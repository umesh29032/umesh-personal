"""Domain 4 — generated-artifact drift (KS-C; inherited contract: the
PHASE_09 §6.6 stale-output contract EXACTLY — recorded graph-hash ≠ current =
STALE with the regeneration command printed · fence integrity corpus-wide ·
hand-edit detection).

EXTEND-NEVER-FORK: the graph hash comes through the Phase-9 generator's own
`load_graph()` gate; the deep hand-edit compare renders through the
generator's OWN `build_model`/`render_*` functions ENTIRELY IN MEMORY (the
generator's `write()` is never called — nothing is regenerated, nothing
touches disk). READ-ONLY."""

import os
import re
import sys

from devseed.knowledge import BLOCKER, WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT

GENERATED_ROOT = os.path.join(REPO_ROOT, "docs", "features")

# The Phase-9 banner grammar (template v1.0.0 — the output's own contract).
_STAMP = re.compile(r"^verified: graph:([0-9a-f]{12})$", re.MULTILINE)
_BANNER = re.compile(r"⚙️ GENERATED — an index, not truth")
_REGEN = re.compile(r"^> Regenerate: `(.+)`$", re.MULTILINE)
_FENCE = re.compile(r"<!--\s*KOS:GEN[: ]?(begin|end)?[^>]*-->", re.IGNORECASE)


def _gen():
    scripts = os.path.join(REPO_ROOT, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import generate_docs
    return generate_docs


# Hand-written KOS satellites that live INSIDE the generated folder. Excluded
# by exact filename, never by a frontmatter field: `owner: handwritten` is
# editable, so trusting it would let a hand-edited card opt out of detection.
_HANDWRITTEN = frozenset({"HUMAN_GUIDE.md"})


def _generated_files(root=None):
    base = root or GENERATED_ROOT
    out = []
    for r, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if f.endswith(".md") and f not in _HANDWRITTEN:
                out.append(os.path.relpath(os.path.join(r, f), base))
    return sorted(out)


def _current_graph12(graph12=None):
    if graph12 is not None:
        return graph12
    return _gen().load_graph()["meta"]["content_hash"][7:19]


def detect_generated_stale(diff=False, deep=False, *, graph12=None, files=None,
                           reader=None, changed=None):
    """The stale-output contract + banner validation, per file: (a) a
    generated file whose stamped graph-hash ≠ the current graph = STALE (WARN,
    the regeneration command quoted from its own banner); (b) a file missing
    its stamp or its banner = BLOCKER (a generated artifact that no longer
    declares itself is hand-edit evidence — knowledge lies). Diff-mode scopes
    to changed generated files."""
    root = GENERATED_ROOT
    if files is None:
        files = _generated_files()
    if diff:
        if changed is None:
            from devseed.knowledge.gitio import changed_files
            changed = changed_files()
        scope = {os.path.relpath(os.path.join(REPO_ROOT, c), root)
                 for c in changed if c.startswith("docs/features/")}
        files = [f for f in files if f in scope]
    current = _current_graph12(graph12)
    read = reader or (lambda rel: open(os.path.join(root, rel), encoding="utf-8").read())
    findings = []
    for rel in files:
        text = read(rel)
        stamp = _STAMP.search(text)
        banner = _BANNER.search(text)
        regen = _REGEN.search(text)
        if not stamp or not banner or not regen:
            findings.append(Finding(
                id=f"d4.banner.corrupt:docs/features/{rel}", domain="generated-drift",
                severity=BLOCKER,
                evidence={"path": f"docs/features/{rel}",
                          "missing": [n for n, ok in (("hash-stamp", stamp),
                                                      ("generated-banner", banner),
                                                      ("regenerate-line", regen)) if not ok]},
                venue="generated"))
            continue
        if stamp.group(1) != current:
            findings.append(Finding(
                id=f"d4.stale:docs/features/{rel}", domain="generated-drift",
                severity=WARN,
                evidence={"path": f"docs/features/{rel}", "stamped": stamp.group(1),
                          "current": current, "remedy": regen.group(1)},
                venue="generated"))
    return findings


_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def detect_fence_integrity(diff=False, deep=False, *, census=None, reader=None):
    """Corpus-wide KOS:GEN fence scan (PHASE_09 fence rules): fences must pair
    begin/end; an orphan fence = corruption (BLOCKER). GEN-C certified ZERO
    live fences — any appearance is validated, never assumed. Markers quoted
    inside markdown code blocks/spans are DOCUMENTATION of the grammar (the
    PHASE_05 contract carries the spec example), not live fences — stripped
    before scanning."""
    if census is None:
        from devseed.knowledge.d1_code_docs import _builder
        census = [p for p in _builder().doc_boundary() if p.endswith(".md")]
    read = reader or (lambda p: open(os.path.join(REPO_ROOT, p), encoding="utf-8").read())
    findings = []
    for path in census:
        text = _INLINE_CODE.sub("", _CODE_BLOCK.sub("", read(path)))
        marks = [m.group(1) or "" for m in _FENCE.finditer(text)]
        if not marks:
            continue
        depth, corrupt = 0, False
        for m in marks:
            if m.lower() == "begin":
                depth += 1
            elif m.lower() == "end":
                depth -= 1
                if depth < 0:
                    corrupt = True
            else:
                corrupt = True   # a KOS:GEN marker that is neither begin nor end
        if corrupt or depth != 0:
            findings.append(Finding(
                id=f"d4.fence.corrupt:{path}", domain="generated-drift",
                severity=BLOCKER,
                evidence={"path": path, "markers": marks[:8],
                          "rule": "PHASE_09 fence integrity (begin/end pairing)"},
                venue="generated"))
    return findings


def _in_memory_render():
    """Render the ENTIRE generated corpus through the generator's own
    functions, capturing (relpath → body) in memory — `write()` never runs."""
    gd = _gen()
    g = gd.load_graph()
    m = gd.build_model(g)
    common = dict(graph12=g["meta"]["content_hash"][7:19],
                  schema_version=g["meta"]["schema_version"],
                  template_version=gd.TEMPLATE_VERSION)
    outputs = []
    for uid in sorted(m["routes"]):
        outputs.append(gd.render_card(g, m, uid, common))
    for n in sorted((n for n in g["nodes"] if n["kind"] == "feature"),
                    key=lambda n: n["id"]):
        outputs.append(gd.render_feature(g, m, n["id"], common))
    outputs.append(gd.render_unassigned_index(g, m, common))
    outputs.append(gd.render_index(g, m, common))
    return dict(outputs)


def detect_hand_edits(diff=False, deep=False, *, expected=None, actual=None):
    """DEEP TIER ONLY (in-memory render-compare — the GEN-E hand-edit
    mechanics as a detector): a file whose bytes differ from what the
    generator would produce TODAY, while its stamp claims the CURRENT graph,
    was hand-edited (BLOCKER). Files with old stamps are the stale detector's
    findings, not this one's."""
    if expected is None:
        expected = _in_memory_render()
    if actual is None:
        root = GENERATED_ROOT
        actual = {rel: open(os.path.join(root, rel), encoding="utf-8").read()
                  for rel in _generated_files()}
    current = None
    findings = []
    for rel in sorted(set(expected) & set(actual)):
        if expected[rel] == actual[rel]:
            continue
        stamp = _STAMP.search(actual[rel])
        if current is None:
            exp_stamp = _STAMP.search(expected[rel])
            current = exp_stamp.group(1) if exp_stamp else None
        if stamp and current and stamp.group(1) != current:
            continue   # stale, not hand-edited — d4.stale owns it
        findings.append(Finding(
            id=f"d4.hand-edit:docs/features/{rel}", domain="generated-drift",
            severity=BLOCKER,
            evidence={"path": f"docs/features/{rel}",
                      "meaning": "bytes differ from the generator's own output for the CURRENT graph",
                      "rule": "PHASE_09: hand-edit-in-generated = BLOCKER; fix source → rebuild → regenerate"},
            venue="generated"))
    for rel in sorted(set(actual) - set(expected)):
        findings.append(Finding(
            id=f"d4.hand-edit.orphan:docs/features/{rel}", domain="generated-drift",
            severity=WARN,
            evidence={"path": f"docs/features/{rel}",
                      "meaning": "exists on disk but the generator would not produce it"},
            venue="generated"))
    return findings
