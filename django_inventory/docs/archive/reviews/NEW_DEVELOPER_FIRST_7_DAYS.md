> **ARCHIVED 2026-06-13** -- merged into the single canonical learning path. See docs/LEARNING_PATH.md (now carries the 7-day pacing + common-beginner-mistakes). NEVER-modify / debug / safe-feature reference: AI_AGENT_GUIDE.

# NEW DEVELOPER — first 7 days (survival kit)

> Basic Python + Django aata hai, is project ka kuch nahi. Follow this; by day 7
> you can trace a request, debug a screen, and add a feature safely.

## Day 1 — the shape
Read [PROJECT_ATLAS.md](PROJECT_ATLAS.md) → [../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md).
Then [ARCHITECTURE_EXPLAINED/](ARCHITECTURE_EXPLAINED/README.md) §1–6.
Goal: understand cloth→Adda→stages→report→settle→pay, and the two truths.

## Day 2 — run it
Login (creds in test memory / ask owner). Walk a worker report on a phone-size
window, then settle an Adda, then pay. Match each screen to
[REQUEST_JOURNEYS/](REQUEST_JOURNEYS/README.md).

## Day 3 — the money
ARCHITECTURE_EXPLAINED §3–10 + [CHOKEPOINTS/](CHOKEPOINTS/README.md). Read
`expense/services/adda_settlement_service.py` + `ledger_service.py` with the
chokepoint docs open.

## Day 4 — production truth
`production/services/worker_task_service.py` + ARCHITECTURE_EXPLAINED §1,2,9,11.
Read the open-closed stage engine (`production/stages/base/`).

## Day 5 — data
[LEARNING/02_DATABASE_RELATIONSHIPS.md](../LEARNING/02_DATABASE_RELATIONSHIPS.md)
+ [LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md](../LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md).
`manage.py dbshell`, run the live-balance SUM, `print(qs.query)`.

## Day 6 — your app
Pick the app you'll work in → its [APPS/<app>/FILE_MAP.md](APPS/) + GUIDE + README.

## Day 7 — make a change safely
`bash scripts/check.sh` (must stay green). Make a tiny change in a service,
add a test, watch the gate. Update the app's docs (CLAUDE rule 12).

---
## NEVER modify directly (write through the service — CI gates enforce)
- `WorkerLedgerEntry` → only `ledger_service`
- `AddaSettlement`/Item, era-B SWA → only `adda_settlement_service`
- `WorkerStageTask`/`WorkerStageContribution` → only `worker_task_service`
- `*History` → only `history_service`
- `processing_cost` freeze → only `cost_service`
- Never edit `reported_quantity` (use `verified_quantity`); never edit a money
 row (reverse it); never sum processing_cost + settled labor (ADR-0009).

## The chokepoint services (memorize)
worker_task · adda_settlement · ledger/payment · allocation (lever) · cost (+history).
Canonical list: [PROJECT_KNOWLEDGE_MAP §7](../PROJECT_KNOWLEDGE_MAP.md). Pages:
[CHOKEPOINTS/](CHOKEPOINTS/README.md).

## Mandatory ADR reading
0001 (services own writes) · 0002 (single writer) · 0005 (two truths) ·
0007 (eras/lever) · 0009 (cost duality) · 0010 (growth/identity).

## Common mistakes
Writing a model in a view · reading `expected_*` as money · adding a stage with
if/else instead of a handler · a new menu item without a SidebarItemRule (URL
left unprotected) · a UI without 360/768/1280 verification (rule 11) ·
forgetting docs-sync (rule 12).

## Debugging strategy / trace a bug
1. Reproduce on dev. 2. Find the URL (URL_ATLAS) → View → Service → Model.
3. Open the matching REQUEST_JOURNEY for the call chain + debug points.
4. `print(qs.query)` for data bugs; check the relevant CI gate for invariant bugs.
5. Money looks wrong? It's a live SUM — look for a missing/extra ledger row, not a stored value.

## How to safely add a feature
Read the app GUIDE + relevant ADRs → write the model change + a service (never
write from the view) → add constraints + a test → `check.sh` green → update the
app's docs same session. New UI = mobile-first + 3-viewport verify.

### Verification Sources
Synthesizes this repo's CLAUDE.md rules, CI gates (scripts/check.sh), the
chokepoint services, and ADRs 0001/0002/0005/0007/0009/0010. Confidence: High.
