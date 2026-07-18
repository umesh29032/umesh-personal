# P1 REGRESSION REPORT — full re-verification (2026-07-07)

**Everything re-run TODAY for this package — nothing inherited from block
reports.** All commands serial (the concurrent-run/test-DB race rule).

## Result: ✅ ALL GREEN — zero regressions, zero re-pins needed.

## 1. Test suites

| Gate | Command | Result |
|---|---|---|
| Full manufacturing + patterns suite (serial) | `manage.py test --noinput` | **979 tests — OK** (155s; run three times today, all green) |
| patterns_ai suite | `manage.py test patterns_ai --noinput` | **94/94 OK** (7.4s; three green runs today) |
| Migrations | `makemigrations --check --dry-run` | **No changes detected** |
| Import contracts | `lint-imports --config .importlinter` | **patterns_ai layer kept**; "1 broken" = the PRE-EXISTING aspirational `Acyclic app layering (target)` contract — all 7 violations are `tracking.tests → production` (Arch-Remediation backlog, predates this project; verified identical to Blocks 1–3E) |
| Media integrity sweep | `verify_patterns_media` | **checked=2 corrupt=0 missing=0 orphans=0** |

## 2. Query pins (all inside the suites above, re-run green)

A360 conscious pin (67) · ADDA_LIST_QUERIES (8) · patterns_ai perf-sanity
ceiling (yield board ≤ 4 + 4·N for N=8 markers) · sidebar-order tests.
No pin moved in this package (last conscious move: Block 1, 65→67,
documented then).

## 3. Guarantee walls (each is a named test, re-run green today)

| Guarantee | Enforcement re-verified |
|---|---|
| Single-writer (I-1) | Repo-wide source-scan: raw ORM writes on knowledge models outside their service = test failure; covers Marker, MarkerUsage, MarkerOutcome, MarkerTransitionEvent, CaptureAsset |
| Read-models write nothing | `CaptureQueriesContext` captures on biography AND yield board assert zero INSERT/UPDATE/DELETE |
| Immutability | Event save-after-create refused, delete refused; CaptureAsset identity-field edits refused, delete refused; retire requires reason; file survives retirement |
| Facts never change | Outcome one-per-usage (friendly service refusal + OneToOne constraint); usage void-not-edit with mandatory reason |
| Derived never stored | No metric column exists (schema fact); METRICS_VERSION lives in code; flash + board text say "derived, not stored" (rendering asserted) |
| Model surface pinned | Exactly-9-models test; FileField confined to `models/capture.py` + `forms.py` |
| Boundary | Purity scan: production never imports patterns_ai; import-linter layer holds |
| Access | Every URL: worker 403 + anonymous redirect re-proven in suite; `originals/` literal absent from HTML (test) |

## 4. Browser walkthroughs — re-done live TODAY (server 8003)

**Desktop (1280×900)** and **mobile (390×844)**, logged in as super-admin:

| Page | Verified |
|---|---|
| `/patterns/` home | nav to library/yield/record |
| `/patterns/markers/` | both markers, real thumbnail, stacked cards @390 |
| `/patterns/markers/MRK-000002/` | summary **Avg m/100 = 96.00**, biography "created → candidate", usage row with **— 96.00 m/100** |
| `/patterns/yield/` (LOWER) | **MRK-000002 · 1× · n=1 · 96.00 m/100 · 0.96 m/garment**; 3-PATTI board shows MRK-000001 honest-NULL `— (no facts yet)` |

Screenshots (final package, scratchpad): `p1f_home_390/desktop`,
`p1f_library_390/desktop`, `p1f_detail_390/desktop`,
`p1f_yield_390/desktop` — 8 total.

**Hostile tamper probes (live):** `?product=abc` → 500 ValueError
(the ONE new finding — registered in
[P1_ENGINEERING_REVIEW](P1_ENGINEERING_REVIEW.md) §4, fix queued for next
approved code block); `<int:pk>` routes → clean 404 on garbage; anonymous
thumb fetch → 302 (gated).

## 5. Live data state (read-only check)

2 markers (MRK-000001 3-PATTI honest-NULL · MRK-000002 LOWER) · 1 usage ·
1 outcome · 2 capture assets (1 junk-byte dev file = the living
corrupt-original proof) · 2 creation transition events. Consistent with
every number the UI shows — because the UI derives from exactly these rows.

## 6. Manufacturing untouched — verified

P1 feature work modified ZERO manufacturing files. The only manufacturing
edits in the whole project were Block-1 wiring (config urls/settings,
sidebar seed) + conscious test re-pins, all documented then. Golden ₹225
and the three journey totals live in the manufacturing suite that just
ran green. Enforcement flags remain OFF (owner rollout policy).
