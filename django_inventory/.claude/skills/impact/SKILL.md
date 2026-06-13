---
name: impact
description: After editing code, list the PKALS docs to review/update from the CHANGE_IMPACT_MATRIX. Use before finishing a change to satisfy docs-sync (CLAUDE rule 12) — it maps changed files to the docs that must be reviewed, and flags changed files that have no matrix row. PKALS v2 tooling — read-only over frozen v1.
---

# /impact — changed files → docs to update (project-local)

Thin wrapper over the v1 CHANGE_IMPACT_MATRIX. Single-source: it READS
`docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md`, never a copy.
It echoes the matrix's own doc LABELS; it does not resolve them to files.

## Use it
After staging your change (`git add`), run:

```
env/bin/python scripts/pkals_impact.py --staged
```

Or pass paths explicitly, or compare to a base:

```
env/bin/python scripts/pkals_impact.py config/expense/services/adda_settlement_service.py
env/bin/python scripts/pkals_impact.py --base main
env/bin/python scripts/pkals_impact.py --json --staged
```

## Then
1. For each doc under **MATCHED**, open it and update it — or explicitly state N/A.
2. For each file under **UNMATCHED**, decide if it has doc impact; if yes, ADD a
   row to CHANGE_IMPACT_MATRIX.md (so it can't drift unnoticed).
3. Glance at the listed **concept rows** (new ADR / new app·model / TM-1 …) if relevant.
4. Confirm `bash scripts/check.sh` stays green.

## Rules
- Route only — NEVER claim to have updated a doc; the human/agent writes the prose.
- Do not modify the matrix or any v1 doc (except the doc updates your change requires).
- This skill adds no knowledge — the matrix is the source of truth.

## Fallback if no shell is available
Read CHANGE_IMPACT_MATRIX.md directly, find the row(s) whose backtick'd path/glob
matches your changed file(s), and review the listed docs.
