---
id: l2-living-documentation-system-readme
type: entry-index
status: active
owner: handwritten
scope: documentation system (PKALS-LIVE)
anchors: —
verified: 2026-07-13
---

# LIVING DOCUMENTATION SYSTEM (PKALS-LIVE)

## TL;DR (2 min)
**Documentation drift is now an architecture bug.** Any change (feature, model,
service, ADR, UI, workflow, bug-fix) is NOT done until its docs are updated the
same session. Use:
- [CHANGE_IMPACT_MATRIX.md](CHANGE_IMPACT_MATRIX.md) — "I changed file X → which
 docs to review" (the token-saver: don't rediscover, just update).
- [OWNERSHIP_MATRIX.md](OWNERSHIP_MATRIX.md) — every doc's owner + update trigger.
- [FUTURE_AGENT_WORKFLOW.md](FUTURE_AGENT_WORKFLOW.md) — the 7-step loop every session runs.
- [DRIFT_PREVENTION.md](DRIFT_PREVENTION.md) — the rules + how stale docs are caught.
- [MAINTAINING_PKALS.md](MAINTAINING_PKALS.md) — how this survives years.

## The PKALS-LIVE rule (the contract)
On ANY add/modify/remove/deprecate/replace/supersede/archive/refactor, the
implementation is incomplete until these are updated (or you state WHY each is
N/A): ADRs · Architecture docs · App README · Request Journey · Data Flow ·
Chokepoint page · Database Guide page · Django-in-this-project page ·
PROJECT_KNOWLEDGE_MAP · AI_AGENT_GUIDE · Coverage Report · WORK_LOG (if PKALS
active) · CLAUDE.md refs. Mirrored as CLAUDE.md rule 12.
