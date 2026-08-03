# P5 REGRESSION REPORT — final full re-verification (2026-07-07)

**Nothing inherited: every gate re-ran fresh against the finished
P5 tree, serial.**

| Gate | Result |
|---|---|
| patterns_ai suite | **176/176 OK** (94 P1 + 34 P2 + 19 P3 + 19 P4 + 10 P5) |
| Full manufacturing suite (serial) | **1061 tests — OK** (206 s, fresh) |
| `makemigrations --check` | **No changes detected** — P5 shipped ZERO migrations; model pin stays 15 |
| import-linter | patterns_ai layer kept; broken = the same pre-existing `tracking.tests → production` target (predates this project) |
| Media integrity sweep | **checked=3 corrupt=0 missing=0 orphans=0** |
| `patterns_ai_health` | **HEALTHY** (compute venv + 5 tools + node + media + integrity + census) |
| Compute runtime | available; engines smoke inside the green suites (real BLF + SVGnest + CV goldens run in-tests) |
| I-1 single-writer scan | green — 7 writers / 15 models final census |
| ADR-F walls | green (no cv-stack in Django; no django/network in compute; lockfile + manifest present) |
| ADR-H boundary | green — standing purity scan + NEW P5-local production-imports assertion after the template edit |
| Manufacturing behavior | untouched: ONE production file changed in all of P0–P5 (`adda_detail.html`, three mgmt-gated LINKS); golden ₹225 + journeys green inside the suite; enforcement flags still OFF |

## Browser + mobile walkthroughs (fresh, this phase)
- **Insights** desktop + @390: KPI chips (3 markers/1 generated ·
  acceptance 100% of 1 decided) · per-product saving table with POTENTIAL
  label · manual-vs-generated · suggestion follow-up ("reality since
  decision") · trend bars · honesty footer.
- **Adda LOWER-001** (the real decision point): Pattern-Intelligence
  action row renders for management → **Cut Advisor link lands prefilled
  (`?product=17`) showing "Best marker: MRK-000002"** — the workflow
  integration loop, live.
- Prior-era pages spot-checked green: advisor, yield board, generation
  run, marker detail, mats.
- Screenshots: `p5_insights_{desktop,390}` · `p5_adda_integration_desktop`
  (+ the full p1–p4 archive).

## Conscious changes to earlier eras in P5
- `compute_bridge.run_tool` gained an optional `timeout_s` (additive
  signature; P3 generation passes headroom) — latent timeout bug fixed.
- ONE production template gained three gated links (the sanctioned
  project-composition mechanism; python boundary untouched).
Nothing else in any frozen era was modified.
