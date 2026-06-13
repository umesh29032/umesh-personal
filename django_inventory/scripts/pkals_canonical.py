#!/usr/bin/env python3
"""/find-canonical core — a topic/keyword -> the ONE canonical PKALS doc.

PKALS v2 tooling. Thin, read-only wrapper over the v1 manifest
(docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json, already CI-guarded).
Stdlib only: no Django, no third-party deps, never writes. Reads v1, never v1's
owner (ADR-V2-P1/P3). Rollback = delete this file.

Usage:
    python3 scripts/pkals_canonical.py "settlement"
    python3 scripts/pkals_canonical.py --json "costing"
    python3 scripts/pkals_canonical.py --list
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # .../django_inventory
MANIFEST = ROOT / "docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json"


def load_manifest(path: pathlib.Path = MANIFEST) -> dict:
    """Load + parse the v1 canonical manifest (raises on bad JSON — fail fast)."""
    return json.loads(path.read_text(encoding="utf-8"))


def match_topic(manifest: dict, query: str):
    """Best (topic, score) for query; score 3=exact term, 2=substring, 1=path, 0=none."""
    q = query.lower().strip()
    best, best_score = None, 0
    for topic in manifest.get("topics", []):
        score = 0
        for term in topic.get("match", []):
            tl = term.lower()
            if q == tl:
                score = max(score, 3)
            elif q and (q in tl or tl in q):
                score = max(score, 2)
        if q and q in topic.get("canonical", "").lower():
            score = max(score, 1)
        if score > best_score:
            best, best_score = topic, score
    return best, best_score


def _render(topic: dict) -> str:
    label = (topic.get("match") or ["?"])[0]
    sec = f" §{topic['section']}" if topic.get("section") else ""
    lines = [f"Topic: {label}", f"Canonical -> {topic['canonical']}{sec}"]
    also = topic.get("also") or []
    if also:
        lines.append("Also      -> " + ("\n             ".join(also)))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Find the ONE canonical PKALS doc for a topic.")
    ap.add_argument("query", nargs="?", help="topic/keyword, e.g. 'settlement'")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--list", action="store_true", help="list every topic + canonical")
    args = ap.parse_args(argv)

    manifest = load_manifest()
    topics = manifest.get("topics", [])

    if args.list:
        if args.json:
            print(json.dumps([{"match": t.get("match"), "canonical": t.get("canonical")} for t in topics], indent=2))
        else:
            for t in topics:
                print(f"{(t.get('match') or ['?'])[0]:<45} -> {t.get('canonical')}")
        return 0

    if not args.query:
        ap.error("a topic/keyword is required (or use --list)")

    topic, score = match_topic(manifest, args.query)
    if not topic:
        known = " · ".join((t.get("match") or ["?"])[0] for t in topics)
        if args.json:
            print(json.dumps({"query": args.query, "match": None,
                              "fallback": manifest.get("entry", {}).get("doc_index", "docs/DOCUMENTATION_INDEX.md")}))
        else:
            print(f"No canonical match for '{args.query}'.")
            print(f"Known topics: {known}")
            print(f"Fallback -> {manifest.get('entry', {}).get('doc_index', 'docs/DOCUMENTATION_INDEX.md')}")
        return 1

    if args.json:
        print(json.dumps({"query": args.query, "score": score,
                          "topic": (topic.get("match") or ["?"])[0],
                          "canonical": topic.get("canonical"),
                          "section": topic.get("section"),
                          "also": topic.get("also", [])}))
    else:
        print(_render(topic))
    return 0


if __name__ == "__main__":
    sys.exit(main())
