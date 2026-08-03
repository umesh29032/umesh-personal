---
id: l2-project-brain-debugging-index
type: topic-canonical
status: active
owner: handwritten
scope: navigation index
anchors: —
verified: 2026-07-13
---

# DEBUGGING INDEX — symptom → where to look first

## TL;DR
Match your symptom; go to the listed doc/file BEFORE grepping. (Layer 3 of PKALS.)

| Symptom | Look first | Likely cause |
|---|---|---|
| Worker's balance looks wrong | ledger rows (SUM) — `expense_workerledgerentry` | missing/extra ledger row; balance is a LIVE SUM, never stored |
| "Nothing to settle" on a ready Adda | `adda_settlement_service.preview_lines` skip classes | all lines already era-A/era-B credited |
| Settlement amount wrong | WSC.verified_quantity vs reported_quantity | settle uses verified-else-reported; check the review page |
| Worker not in assignable list | their SKILL (Access Control) | skill-gate, not a bug; F7 future policy |
| Worker reported but no pay | did the stage complete before they submitted? | F3 auto-cancel of unreported tasks (P2 dialog warns) |
| Can't reopen a stage | it's settlement-credited | V2-3 armor: reverse the settlement first (error names the ADST) |
| Double pay suspicion | era guard / grouped-member | symmetric guard + cost_service grouped guard; check SWA.adda_settlement |
| Mobile table shows labels only, no values | base.html stacked-table CSS | F1 fix (`width:100%!important;min-width:0`) — should be fixed |
| Menu hidden but URL works / 403 | SidebarItemRule + middleware | every view needs a sidebar rule (whitelist) |
| Deadlock on settlement | lock order | someone broke §11.5 order (advisory→ADST→SR→profile→advance) |
| `FOR UPDATE cannot be applied…` | nullable FK + select_related | use `select_for_update(of=('self',))` |
| Migration "RunPython not subscriptable" | RunPython in `dependencies` not `operations` | move it to operations |
| Cost report too high | summed processing_cost + settled labor | ADR-0009: NEVER add — they're the same labor |
| Doc says X, code does Y | drift = architecture bug | fix the doc (DRIFT_PREVENTION), update via CHANGE_IMPACT_MATRIX |

General method: URL_ATLAS → REQUEST_JOURNEY (call chain + debug points) →
`print(qs.query)` for data, check the CI gate for invariants. See AI_AGENT_GUIDE.
