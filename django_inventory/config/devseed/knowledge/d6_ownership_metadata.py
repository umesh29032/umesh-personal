"""Domain 6 — ownership + metadata + lifecycle (KS-B; inherited contracts:
DOC_STANDARDS §11/§12/§13 [R2-ratified 7-field frontmatter; archive never
retrofitted] + OWNERSHIP_MATRIX [DOCCLEAN-B family rows]).

READ-ONLY. The docs census is the Phase-8 builder's own `doc_boundary()`
(imported — single source). Injection parameters exist for constructed-drift
tests."""

import fnmatch
import os
import re

from devseed.knowledge import WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT, _builder

MATRIX_PATH = os.path.join(
    REPO_ROOT, "docs", "LEARNING_2_0", "LIVING_DOCUMENTATION_SYSTEM",
    "OWNERSHIP_MATRIX.md")

# DOC_STANDARDS §13 — the R2-ratified 7-field core.
FRONTMATTER_FIELDS = ("id", "type", "status", "owner", "scope", "anchors", "verified")
# DOC_STANDARDS §12 — the closed lifecycle set, PLUS the two sanctioned forms:
# versioned frozen labels ("frozen-vN ... are dated instances of the frozen
# state", §12 verbatim) and `generated` (the Phase-9 template-ratified status
# of the generated layer — GEN-B validated 558/558 with it).
LIFECYCLE_STATES = ("draft", "active", "frozen", "superseded", "archived",
                    "remove-later", "generated")
import re as _re
_FROZEN_VN = _re.compile(r"^frozen-v\d+$")


def _valid_status(value):
    return value in LIFECYCLE_STATES or bool(_FROZEN_VN.match(value))


def _docs_census(census=None):
    """Markdown docs in the active knowledge boundary (builder's own walk —
    archive excluded there, matching §13 'archive NEVER retrofitted')."""
    if census is not None:
        return census
    return [p for p in _builder().doc_boundary() if p.endswith(".md")]


def _read(path, reader=None):
    if reader is not None:
        return reader(path)
    with open(os.path.join(REPO_ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def _frontmatter(text):
    """The builder's frontmatter convention (--- fenced YAML-lite, key: value)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


# ── ownership (OWNERSHIP_MATRIX coverage) ────────────────────────────────────

_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")


def _matrix_patterns(matrix_path=None):
    """Column-1 doc/family patterns from every matrix table. `<placeholder>` →
    glob; plain names match by path fragment or basename stem."""
    text = open(matrix_path or MATRIX_PATH, encoding="utf-8").read()
    patterns = []
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m or set(m.group(1)) <= {"-", " "} or m.group(1) == "Doc / family":
            continue
        cell = m.group(1).strip().strip("*").strip("`").strip()
        if cell and cell not in ("Doc",):
            patterns.append(cell)
    return patterns


def _owned(path, patterns):
    base = os.path.basename(path)
    stem = base[:-3] if base.endswith(".md") else base
    for raw in patterns:
        # split "PENDING_BACKLOG / ROADMAP" alternatives — never inside real
        # paths (lowercase segments) or before a <placeholder>
        for alt in re.split(r"\s*/\s*(?![a-z<])", raw):
            pat = re.sub(r"<[^>]+>", "*", alt.strip())
            pat = re.sub(r"\.\.[A-Za-z0-9]+", "*", pat)  # ADR-0001..0011 → ADR-0001*
            if not pat or set(pat) <= {"*", "/"}:   # a wildcard-only alt matches nothing
                continue
            if "*" in pat:
                if (fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat + "*")
                        or fnmatch.fnmatch(path, "*" + pat)
                        or fnmatch.fnmatch(path, "*" + pat + "*")):
                    return True
            else:
                if pat in path or stem == pat or stem.startswith(pat):
                    return True
    return False


def detect_ownership(diff=False, deep=False, *, matrix_path=None, census=None):
    """Every active doc is covered by an OWNERSHIP_MATRIX row (the matrix's
    whole purpose: 'who updates this when X changes'). Uncovered → WARN."""
    patterns = _matrix_patterns(matrix_path)
    findings = []
    for path in _docs_census(census):
        if not _owned(path, patterns):
            findings.append(Finding(
                id=f"d6.ownership.unowned:{path}", domain="ownership-metadata",
                severity=WARN,
                evidence={"path": path, "rule": "OWNERSHIP_MATRIX: every doc has an owner concept"},
                venue="docs"))
    return findings


# ── metadata (R2 7-field frontmatter) ────────────────────────────────────────

def detect_metadata(diff=False, deep=False, *, census=None, reader=None):
    """§13: frontmatter mandatory on new docs since Phase-5 + retrofit onto the
    active tier at Phase 7 (archive never — excluded by the census). Missing
    frontmatter or missing core fields or an invalid lifecycle state → WARN."""
    findings = []
    for path in _docs_census(census):
        fm = _frontmatter(_read(path, reader))
        if fm is None:
            findings.append(Finding(
                id=f"d6.metadata.missing-frontmatter:{path}",
                domain="ownership-metadata", severity=WARN,
                evidence={"path": path, "rule": "DOC_STANDARDS §13 (R2 7-field core)"},
                venue="docs"))
            continue
        missing = [f for f in FRONTMATTER_FIELDS if f not in fm]
        if missing:
            findings.append(Finding(
                id=f"d6.metadata.incomplete:{path}", domain="ownership-metadata",
                severity=WARN, evidence={"path": path, "missing_fields": missing},
                venue="docs"))
        if "status" in fm and not _valid_status(fm["status"]):
            findings.append(Finding(
                id=f"d6.metadata.bad-status:{path}", domain="ownership-metadata",
                severity=WARN,
                evidence={"path": path, "status": fm["status"],
                          "allowed": list(LIFECYCLE_STATES) + ["frozen-vN"]},
                venue="docs"))
    return findings


# ── lifecycle (§12 banners) ──────────────────────────────────────────────────

def detect_lifecycle(diff=False, deep=False, *, census=None, reader=None):
    """§12: superseded/archived docs carry the banner naming their successor
    ('Truth is never deleted; it is superseded.'). Bannerless → WARN."""
    findings = []
    for path in _docs_census(census):
        text = _read(path, reader)
        fm = _frontmatter(text)
        if not fm or fm.get("status") not in ("superseded", "archived"):
            continue
        lowered = text.lower()
        if "superseded" not in lowered.replace("status: superseded", "", 1) \
                and "archived" not in lowered.replace("status: archived", "", 1):
            findings.append(Finding(
                id=f"d6.lifecycle.no-banner:{path}", domain="ownership-metadata",
                severity=WARN,
                evidence={"path": path, "status": fm["status"],
                          "rule": "DOC_STANDARDS §12 banner convention"},
                venue="docs"))
    return findings
