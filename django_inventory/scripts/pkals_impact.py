#!/usr/bin/env python3
"""/impact core — changed file(s) -> the PKALS docs to review/update (CLAUDE rule 12).

PKALS v2 tooling. Thin, read-only wrapper over the v1 CHANGE_IMPACT_MATRIX
(docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md). Stdlib
only: no Django, no third-party deps, never writes. Echoes the matrix's own doc
LABELS; it does NOT resolve them into file paths (that is the v1 guard's job).
Reads v1, never modifies it (ADR-V2-P1/P3). Rollback = delete this file.

Usage:
    python3 scripts/pkals_impact.py --staged                 # default: git diff --cached
    python3 scripts/pkals_impact.py config/production/services/worker_task_service.py
    python3 scripts/pkals_impact.py --base main              # git diff main..HEAD
    python3 scripts/pkals_impact.py --json --staged
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # .../django_inventory
MATRIX = ROOT / "docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md"

_BACKTICK = re.compile(r"`([^`]+)`")


def parse_matrix(path: pathlib.Path = MATRIX):
    """Parse the matrix table.

    Returns (file_rows, concept_rows):
      file_rows    = [(pattern, [doc_labels])]  for each backtick'd path/glob in col 1
      concept_rows = [(label, [doc_labels])]     for non-file rows (e.g. **TM-1 lands**)
    """
    file_rows, concept_rows = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) != 2:
            continue
        key, docs_cell = cols
        if key in ("Changed file/area", "Phase") or set(key) <= set("-: "):  # header / separator
            continue
        docs = [d.strip() for d in docs_cell.split("·") if d.strip()]
        patterns = _BACKTICK.findall(key)        # may be >1 (e.g. models.py / roll_service.py)
        if patterns:
            for pat in patterns:
                file_rows.append((pat.strip(), docs))
        else:
            concept_rows.append((key.replace("*", "").strip(), docs))
    return file_rows, concept_rows


def _changed_files(args) -> list[str]:
    if args.files:
        return args.files
    cmd = (["git", "diff", "--name-only", f"{args.base}..HEAD"] if args.base
           else ["git", "diff", "--cached", "--name-only"])      # --staged default
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]


def match_file(path: str, file_rows) -> list:
    """Rows whose pattern is contained in path (suffix-style *fnmatch*; no prefix map)."""
    norm = path.replace("\\", "/")
    hits = []
    for pat, docs in file_rows:
        p = pat.replace("\\", "/").strip("/")
        if fnmatch.fnmatch(norm, "*" + p + "*"):
            hits.append((pat, docs))
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="List PKALS docs to review after a code change.")
    ap.add_argument("files", nargs="*", help="changed file paths (default: --staged)")
    ap.add_argument("--staged", action="store_true", help="use git diff --cached (default if no files/base)")
    ap.add_argument("--base", help="compare against a base ref: git diff <base>..HEAD")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    file_rows, concept_rows = parse_matrix()
    changed = _changed_files(args)

    matched, unmatched = {}, []
    for f in changed:
        hits = match_file(f, file_rows)
        if hits:
            matched[f] = hits
        else:
            unmatched.append(f)

    if args.json:
        print(json.dumps({
            "changed": changed,
            "matched": {f: sorted({d for _, docs in hits for d in docs}) for f, hits in matched.items()},
            "unmatched": unmatched,
            "concept_rows": [c[0] for c in concept_rows],
        }, indent=2))
        return 0

    if not changed:
        print("No changed files (try --staged after `git add`, or pass paths / --base).")
        return 0

    if matched:
        print("== MATCHED — review/update this session (CLAUDE rule 12) ==")
        for f, hits in matched.items():
            print(f"\n{f}")
            for pat, _ in hits:
                print(f"  ↳ matrix row: `{pat}`")
            docs = sorted({d for _, dlist in hits for d in dlist})
            for d in docs:
                print(f"    • {d}")

    if unmatched:
        print("\n== UNMATCHED — no CHANGE_IMPACT_MATRIX row ==")
        for f in unmatched:
            print(f"  • {f}")
        print("  → If a change here has documentation impact, ADD a row to "
              "CHANGE_IMPACT_MATRIX.md (else it can drift unnoticed).")

    print("\nAlso check concept rows if relevant: "
          + " · ".join(c[0] for c in concept_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
