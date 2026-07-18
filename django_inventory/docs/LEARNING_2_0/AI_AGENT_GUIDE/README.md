---
id: l2-ai-agent-guide-readme
type: entry-index
status: active
owner: handwritten
scope: documentation system
anchors: —
verified: 2026-07-13
---

# AI AGENT GUIDE — zero-context entry for a future Claude

## TL;DR (the cheapest path — read ONE file to route)
You are an AI agent entering this repo with no memory. **To ROUTE a task, read the
one machine-readable file [canonical_manifest.json](canonical_manifest.json), then
open the single canonical doc it names for your topic.** That is the whole routing
step — one compact JSON instead of scanning the repo or reading several prose
indexes. For WRITES, obey the manifest's `never_modify` (CI gates enforce).

**Only if you need DEEP understanding** (not just routing), these narrative files
are the depth layer — optional, read the one that matches your need:
- [../../PROJECT_KNOWLEDGE_MAP.md](../../PROJECT_KNOWLEDGE_MAP.md) — the ONE overview (business→arch→DB→code).
- [../PROJECT_BRAIN/README.md](../PROJECT_BRAIN/README.md) — feature/search/debugging/decision/change indexes.
- [../ARCHITECTURE_EXPLAINED/README.md](../ARCHITECTURE_EXPLAINED/README.md) — the WHY.
- [../CHOKEPOINTS/README.md](../CHOKEPOINTS/README.md) — what you must never write directly.

Do NOT grep the whole repo first — the manifest + canonicals exist to prevent that.
(The table below is the human-readable mirror of the manifest; the JSON is the
source of truth and is CI-validated, so trust it if they ever differ.)

## Canonical-doc lookup (topic → the ONE file to read)
| Task touches… | Read THIS (canonical) |
|---|---|
| worker assignment / reporting / production truth | [../ARCHITECTURE_V2.md](../../ARCHITECTURE_V2.md) + CHOKEPOINTS/worker_task_service.md |
| settlement / earnings / ledger | ARCHITECTURE_V2 §11 + CHOKEPOINTS/adda_settlement_service.md + ADR-0005/0007 |
| costing | ADR-0009 + CHOKEPOINTS/cost_service.md |
| commerce / orders / SKU | ADR-0008 + ADR-0010 §5 |
| tracking mode / barcode reporting | [../../REQUIREMENT_REVIEW_STAGE_TRACKING.md](../../REQUIREMENT_REVIEW_STAGE_TRACKING.md) |
| an app's files | [../APPS/<app>/FILE_MAP.md](../APPS/) + docs/apps/<app>/GUIDE.md |
| a URL/route | [../URL_ATLAS.md](../URL_ATLAS.md) |
| a request's call chain | [../REQUEST_JOURNEYS/](../REQUEST_JOURNEYS/README.md) |
| data model / how rows save | [../../LEARNING/02_DATABASE_RELATIONSHIPS.md](../../LEARNING/02_DATABASE_RELATIONSHIPS.md) |
| "what's still to build" | [../../PENDING_BACKLOG.md](../../PENDING_BACKLOG.md) |
| "what's the roadmap" | [../../ROADMAP_REVIEW_POST_C1_2026_06_11.md](../../ROADMAP_REVIEW_POST_C1_2026_06_11.md) |
| working rules | [../../../CLAUDE.md](../../../CLAUDE.md) (rule 11 mobile-first, rule 12 docs-sync) |

## NEVER modify directly (CI gates 4/4b/4c WILL fail the build)
- `WorkerLedgerEntry` → only `ledger_service`
- `AddaSettlement`/`AddaSettlementItem` + era-B `StageWorkAssignment` → only `adda_settlement_service`
- `WorkerStageTask`/`WorkerStageContribution` → only `worker_task_service`
- `*History` → only `history_service` · `processing_cost` → only `cost_service`
- Never edit `reported_quantity` (use `verified_quantity`), never edit/delete a
 money row (reverse it), never sum processing_cost + settled labor (ADR-0009).

## Architecture boundaries (don't cross)
- core + accounts import NO domain app (foundation-purity gate).
- tracking imports NEITHER production nor expense (string FKs).
- production → expense allowed one-way; expense never imports production at module level.
- commerce: no Order→Adda FK, no price field on production models (ADR-0008/0010).

## Safe investigation of a bug (token-cheap path)
1. URL_ATLAS → find route → View → Service → Model. 2. Open the matching
REQUEST_JOURNEY (call chain + debug points) BEFORE grepping. 3. Money bug? it's
a live SUM — look for a missing/extra ledger row. 4. Invariant bug? check which
CI gate covers it. Only grep code if the docs don't resolve it — then UPDATE the
doc (rule 12) so the next agent doesn't pay the same cost.

## Safe feature implementation
Read the app GUIDE + topic-canonical + relevant ADRs → change the model →
write/extend a SERVICE (never write from a view) → add constraints + a test →
`bash scripts/check.sh` green → UPDATE docs same session (rule 12) → if UI,
mobile-first + 360/768/1280 verify (rule 11). New stage = new handler package
(open-closed), not if/else.

## Where decisions live
ADRs (binding): [../../adr/](../../adr/) (the full set; summaries KNOWLEDGE_MAP §9).
Locked requirements: ARCHITECTURE_V2, R1_STAGE_DOMAIN_REVIEW, REQUIREMENT_REVIEW_
STAGE_TRACKING. Roadmap + open items: ROADMAP_REVIEW + PENDING_BACKLOG. Senior
rationale + rejected alternatives: [../ARCHITECTURE_VALIDATION/README.md](../ARCHITECTURE_VALIDATION/README.md).

## Drift prevention (your job as an agent)
Code change ⇒ docs change, same session (rule 12). If you discover the docs are
stale vs code, fix the doc and note it — the doc IS the memory; stale docs cost
every future agent tokens. Confirm `scripts/check.sh` stays green.

### Verification Sources
Synthesizes CLAUDE.md rules, scripts/check.sh gates, the chokepoint services
(KNOWLEDGE_MAP §7), the ADR set under docs/adr/, and the LEARNING_2_0 structure.
Confidence: High.
