---
id: docs-ai-pattern-intelligence-phase1-pattern-dashboard-plan
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PHASE 1 PLAN — Pattern Dashboard entry
(2026-07-08 · ENGINEERING MODE · PLAN ONLY, no code until owner approval ·
supersedes MA1_IMPLEMENTATION_PLAN.md per the owner's final correction:
Patterns → PATTERN DASHBOARD, the single entry for all pattern work)

## The correction, restated as the target

```
Products row → Patterns
                  │
                  ▼
        PATTERN DASHBOARD  (?product=N — one entry, GitHub-repo model)
                  │
   ├── Pattern Blueprint        (Phase 1: the re-homed pieces+counts editor;
   │                             becomes the full rules module in Phase 2)
   ├── Pattern Manager          (exists — size verdict cards → Preparing Size)
   └── Digital Cutting Table    (gated ≥1 Ready size; Phase 1 target = the
                                 current tool page, replaced by the real DCT
                                 in Phases 4–7)
```

## Scope (four items)

1. **Pattern Dashboard page** (NEW, in `patterns_ai` — it renders
   patterns_ai truth; production stays behind the ADR-H wall).
   `patterns_ai:dashboard` · `?product=N` · product chooser without it.
   Content, deliberately minimal: product header · one readiness
   summary line (X/Y sizes Ready — from the existing facade summary) ·
   THREE module cards (Blueprint / Manager / DCT), each with a
   one-line honest description; DCT card carries the owner-locked gate
   (enabled at ≥1 Ready size, else `aria-disabled` + reason — same law,
   same facade field `any_size_ready`, computed once).
   UI composes from canon (standing rule): A360-hub module-card pattern
   + `piece_list` tokens; mobile-first stacked cards.
2. **Patterns action → Dashboard** — carried forward from M-A1 analysis:
   `production:product-patterns` (8 call sites mapped) becomes a
   login-gated redirect → `patterns_ai:dashboard?product=<pk>` (D-1
   shape, new target; D-2 gate reasoning unchanged). Legacy assignment
   editor re-homed at `products/<pk>/patterns/set/`
   (`product-pattern-set`), strict gate intact — it IS the Phase-1
   Blueprint card target, labeled honestly ("pieces + counts — full
   Blueprint editor arrives in Phase 2").
3. **Truth stamp** (carried from M-A1, flagged for explicit approval):
   `geometry_contract_version` CharField(default `'adr-c.1'`) on
   `PieceSizeGeometry` + explicit stamp at the single writer's 3
   creation points. ONE additive migration — the frozen law's
   "Geometry Contract Version" fact, cheapest before more geometry
   accumulates. Orthogonal to the dashboard; riding Phase 1 so no
   data is created unstamped during Phases 2–8.
4. **DCT label rename** — "Open Cutting Table" → "Open Digital Cutting
   Table" (owner-ruled; 2 strings in `piece_list.html`; dashboard card
   uses the full name from birth). Manager also gains a "← Dashboard"
   back link so the hierarchy reads Product → Dashboard → Manager →
   Preparing Size.

NOT in Phase 1 (per the owner's phase list): full Blueprint module
(P2) · Universal size + archive guard (P3, a Manager/size concern) ·
grain_rule field (P2, lands with its editor) · any DCT build (P4–7) ·
Adda (P8).

## File touch list (11 files + 1 migration)

| # | File | Change |
|---|---|---|
| 1 | `patterns_ai/views.py` | `PatternDashboardView` (thin: facade summary + 3 card contexts; GET-only, writes nothing) |
| 2 | `patterns_ai/urls.py` | `dashboard/` route |
| 3 | `patterns_ai/templates/patterns_ai/dashboard.html` | NEW page (module cards, readiness line, chooser, mobile-first) |
| 4 | `patterns_ai/templates/patterns_ai/piece_list.html` | "← Dashboard" back link · 2 gate-label strings → "Open Digital Cutting Table" |
| 5 | `patterns_ai/models/geometry.py` | `geometry_contract_version` field + why-comment |
| 6 | `patterns_ai/migrations/00XX` | AddField, additive only |
| 7 | `patterns_ai/services/pattern_geometry_service.py` | `GEOMETRY_CONTRACT_VERSION = 'adr-c.1'` constant; stamp at the 3 creation points (`:140/:223/:431`) |
| 8 | `production/urls.py` | `product-patterns` → entry redirect; `products/<pk>/patterns/set/` = `product-pattern-set` |
| 9 | `production/views/pattern_views.py` | `ProductPatternsEntryView` (LoginRequired → dashboard); editor's 2 POST self-redirects → new name |
| 10 | `production/templates/production/product_patterns_edit.html` | header line: "Pattern Blueprint (pieces + counts) — part of the Pattern Dashboard · ← back" |
| 11 | tests: NEW `patterns_ai/tests/test_phase1_dashboard.py` + 3 conscious updates (`test_pattern_pieces_count.py` new reverse name · `test_phase6_m4.py:189,201` and `test_pdm_w2.py:251` → assert 302 → dashboard), each commented "Phase 1 dashboard" | acceptance proof; no silent edits |

Docs same session (rule 12): Phase-1 report · app GUIDE table (+2 new
files) · DOCUMENTATION_INDEX · MA1 plan already marked superseded.

## New-test coverage (`test_phase1_dashboard.py`)

Dashboard renders 3 module cards + readiness line · DCT card gate
enabled (fixture with a Ready size) and disabled + reason (none ready) ·
product chooser without `?product` · worker 403 · unknown product 404 ·
GET writes nothing · `product-patterns` 302 → dashboard (+ login
required) · editor functional at `product-pattern-set` (spot check —
full editor suite runs via updated reverse) · contract stamp present on
rows from all 3 service paths + default on a pre-existing row · Manager
back link · both DCT labels renamed.

## Risks (carried + new)

- R-1 populated-table AddField-with-default — safe additive (verified
  shape).
- R-2 sidebar middleware on `/patterns/` prefix — Manager already
  reachable from production (browser-validated M4+); dashboard shares
  the prefix; browser step re-verifies super-admin, manager, worker.
- R-3 entry perm consciously login-only (D-2); editor keeps
  `change_productpattern`; dashboard itself enforces the Manager's
  management-role rule (worker 403) so the entry never shows a worker
  the modules.
- R-4 template caching — dev-server restart before browser validation.
- R-5 test drift — 3 conscious commented updates, listed above.
- R-6 double-hop feel (list → dashboard → manager) — accepted by
  design: the dashboard IS the product's pattern home (owner's GitHub
  analogy); Manager stays one tap away.

## Acceptance criteria

1. Products → Patterns → **Pattern Dashboard** for the product; three
   module cards visible; readiness line correct against facade truth.
2. Blueprint card → re-homed editor (fully functional, strict gate
   intact); Manager card → Manager (unchanged URL); DCT card obeys the
   ≥1-Ready gate with honest reason when disabled.
3. Every new geometry row carries `geometry_contract_version='adr-c.1'`;
   pre-existing rows read it via default.
4. Gate labels read "Open Digital Cutting Table" (both variants);
   Manager shows "← Dashboard".
5. `makemigrations --check` clean; facade contract untouched
   (dashboard READS existing summary fields only); frozen writers
   untouched beyond the stamp constant.
6. Full battery green — patterns_ai + full manufacturing suite, serial,
   fresh, counts verified from output.
7. Browser walkthrough desktop + 390×844: list → Patterns → Dashboard →
   each card → back; worker blocked; screenshots.

## Estimate
~11 files · 1 additive migration · 1 new page · no new models beyond
the field · no frozen-writer signature changes · money untouched.

---
**STOP — Phase-1 plan delivered. No code written. Implementation begins
ONLY on your explicit approval (including the truth-stamp rider and
D-1/D-2 carried decisions).**
