# P1 — BLOCK 1 REPORT: patterns_ai Foundation (2026-07-06)

**Status: ✅ BLOCK 1 COMPLETE — STOPPED. Block 2 will NOT start without
explicit owner approval.**

## Scope compliance
Exactly the ordered foundation: **no models · no migrations · no business
logic · no CV/nesting/uploads/AI/geometry · no database tables · no Product
integration.** Two guard tests PIN this state (`test_block1_pin_no_models`,
`test_block1_pin_no_media_writes_yet`) so schema arrives at Block 2 by
decision, not drift.

## Files created (config/patterns_ai/)
`apps.py` (constitution note) · `urls.py` (`patterns_ai:home`) · `views.py`
(placeholder, management-gated, parse→gate→delegate) ·
`templates/patterns_ai/home.html` · `static/patterns_ai/` ·
`services/__init__.py` + **4 single-writer skeletons** (capture ·
pattern_geometry · marker · marker_feedback — docstrings name their landing
blocks; I-1 no-raw-ORM rule stated) · `tests/` (`test_purity.py`,
`test_smoke.py`) · `management/commands/seed_patterns_ai_sidebar.py`
(idempotent) · `README.md`. Docs: `docs/apps/patterns_ai/GUIDE.md` + apps-table
row.

## Wiring (authorized P1 class — machines-app precedent)
- `INSTALLED_APPS` + `path("patterns/", include("patterns_ai.urls"))`.
- **SIDEBAR registry `MenuItem('Pattern Intelligence', …)`** in
  `permission_service` (management-predicated) — same wiring class as the
  machines entry; menu + URL co-gated.
- Sidebar rule row seeded in the dev DB (`seed_patterns_ai_sidebar` run once).
- `.importlinter`: `patterns_ai` in root_packages + TOP layer with **zero
  ignore_imports** (stricter than machines, per ADR-H).
- Media: `media/patterns_ai/` tree convention documented (README/ADR-G);
  no write paths exist yet (pinned).
- `tblib` installed (readiness condition N-8 — parallel test failures now
  reportable).

## Validation
| Gate | Result |
|---|---|
| patterns_ai suite (purity source-scan · Block-1 pins · smoke 200-mgmt/403-worker) | ✅ OK |
| **Full manufacturing suite, serial** | ✅ **OK** (after one conscious re-pin, below) |
| `makemigrations --check` | ✅ No changes detected |
| import-linter | ✅ contract 1 KEPT; contract 2 = pre-existing registered worklist with **zero patterns_ai entries** |
| Browser smoke (8003, super-admin) | ✅ sidebar shows "Pattern Intelligence"; `/patterns/` renders placeholder |

## Findings
1. **Conscious pin update (65→67):** the A360 query-bound test caught that
   every role-predicated SIDEBAR MenuItem fires its own `extra_roles` read per
   render — my ONE new item = +2 queries on that page. Pre-existing per-item
   cost (all management items pay it), now surfaced by the pin. Re-pinned with
   written reason; **registered as a perf observation** (a per-request
   principal cache in `permission_service` would be a frozen-code change —
   owner-gated, not Block-1 scope).
2. **Doc-vs-reality note:** `SidebarItemRule` lives in **accounts** (not
   inventory as ADR-H's prose implied) with M2M roles and
   fallback-to-code-predicate semantics for unmanaged items — the seed command
   targets the real schema; ADR-H prose needs a one-word correction at its
   next touch (noted, not edited — frozen-doc discipline).
3. Reverse/URL/RBAC all proven by tests rather than assumption (worker gets
   403 by predicate even without visiting the Sidebar Access page).

**Awaiting owner approval for Block 2** (per master plan P1: memory-era models
+ services — Marker/MarkerUsage/MarkerOutcome/SuggestionEvent + the D2/D3
mini-ADR decision point).
