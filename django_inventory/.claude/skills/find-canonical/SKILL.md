---
name: find-canonical
description: Return the ONE canonical PKALS doc for a topic by reading canonical_manifest.json. Use BEFORE reading or grepping when you need to know where the authoritative doc for a concept lives (settlement, two truths, costing, request flow, eras/lever, tracking mode, a URL, the data model, future-phase doc work, etc.). PKALS v2 tooling — read-only over frozen v1.
---

# /find-canonical — topic → the one canonical doc (project-local)

Thin wrapper over the v1 manifest. Single-source: it READS
`docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json`, never a copy.

## Use it
Given the user's topic/keyword, run:

```
env/bin/python scripts/pkals_canonical.py "<topic>"
```

Then OPEN the `Canonical ->` file it names (and `Also ->` only if you need depth).
Useful flags: `--list` (all topics), `--json` (machine output).

## Behaviour
- One best match → its canonical + also-links (real, resolvable paths).
- No match → it prints the known topics + the fallback (`DOCUMENTATION_INDEX.md`).
  In that case, route via DOCUMENTATION_INDEX; do NOT invent a path.

## Fallback if no shell is available
Read `docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json` directly and match
the user's topic against `topics[].match`; open that topic's `canonical`.

## Rules
- Do not modify the manifest or any v1 doc.
- Do not fabricate a canonical; if there's no match, say so and use DOCUMENTATION_INDEX.
- This skill adds no knowledge — the manifest is the source of truth (CI-guarded).
