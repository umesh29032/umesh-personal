---
id: docs-pkals-v2-pkals-v2-roadmap
type: topic-canonical
status: active
owner: handwritten
scope: docs
anchors: —
verified: 2026-07-18
---

# PKALS v2 — ROADMAP (Discovery, design-only)

> **PROPOSAL. Nothing implemented.** Every idea classified Must / Nice / Not-worth,
> for a SOLO dev on a large AI-assisted ERP. Bias (inherited from v1): automate the
> manual discipline, add no content, keep it cheap + robust. Sizing + cost/benefit:
> PKALS_V2_EFFORT_ESTIMATE.

## MUST BUILD (high ROI · low complexity · reuses v1 · robust)
1. **change-impact tool + /impact skill** (C+B+D) — `git diff` → CHANGE_IMPACT_MATRIX
   rows. Turns the single most-skipped manual step into one command. Highest ROI:
   it operationalizes PKALS-LIVE itself.
2. **route-map drift check** (C/E) — URL_ATLAS vs Django resolver. Catches the #1
   periphery drift deterministically; joins `scripts/check.sh`.
3. **model-map drift check** (C/E) — DATABASE_GUIDE vs `apps.get_models()`. Same, for
   the per-model docs. Together (2)+(3) close v1's periphery-lag ceiling.
4. **/find-canonical skill** (B) — manifest → the one canonical. Tiny, highest-use by
   AI agents; near-zero maintenance (manifest already CI-guarded).
5. **knowledge-sync hook** (D) — pre-push/CI advisory: changed files → docs to review.
   Thin wrapper over (1). Makes the discipline automatic at the moment of change.

## NICE TO HAVE (good ROI · more complexity or maintenance · do after Must proves out)
6. **missing-CHANGE_IMPACT detector** (E/R-E4) — commit touched a matrix-keyed file but
   none of its listed docs changed → warn. Valuable but needs tuning (N/A is legit).
7. **/trace-request + /debug-flow skills** (B) — wrap journeys + DEBUGGING_INDEX.
   Useful; /find-canonical + /impact already cover the core routing.
8. **/update-docs skill** (B/D) — guided doc-sync checklist (runs /impact, opens each).
   Convenience layer over Must items.
9. **dead-doc detector** (C/E) — doc cites a `module:symbol` that's gone. Useful but
   AST-cite parsing is brittle; report-only.
10. **stale-model-reference depth** (E/R-E2 beyond model names → field names in prose).

## NOT WORTH BUILDING (low ROI · bloat / unsafe / duplicates v1)
- **Heavy Online Learning System (A)** — duplicates `LEARNING/` + `LEARNING/10` +
  DJANGO_GUIDE; owner scope-rejected generic re-teaching. (Thin link-curation in
  LEARNING/10 only, on demand — not a system.)
- **Self-healing AUTO-REWRITE** — unsafe; prose correctness is human/agent judgment.
  Detection+notify is the safe ceiling (kept, as Must/Nice).
- **/architecture-review as an automated verdict** — review is adversarial judgment;
  a skill can checklist (Nice, low priority) but must not pretend to a verdict.
- **Docs website / static-site generator** — bloat for one maintainer; md + manifest
  serve humans + AI already.
- **Auto-generation of docs from code** — brittle; fights v1's verified-from-code,
  human-understanding ethos; would re-introduce the drift v1 guards against.

## Sequencing (each phase ships green + independently revertible, v1-style)
- **v2-A (foundation):** Must #1 (change-impact + /impact) → #4 (/find-canonical).
  Smallest, highest leverage; proves the "skills wrap v1, don't duplicate" pattern.
- **v2-B (drift CI):** Must #2 + #3 (route-map, model-map) → add to `scripts/check.sh`.
  Closes the periphery-lag ceiling.
- **v2-C (sync):** Must #5 (knowledge-sync hook). Makes discipline automatic.
- **v2-D (optional):** Nice items, only if v2-A..C demonstrably cut maintenance effort.
- **Never:** the Not-worth list, unless a future evidence-backed review reverses it.

## Decision gate (should v2 exist at all?)
**Yes — but small.** v2-A..C (5 Must items) are cheap, robust, reuse v1, add zero
content, and attack the exact ceiling v1 documented (periphery drift + manual
discipline). If only ONE thing is built: **#1 (change-impact + /impact)** — it
operationalizes PKALS-LIVE. If the Must set lands and effort visibly drops, the Nice
set is justified; if not, stop — v1 + Must is already excellent for a solo dev.
