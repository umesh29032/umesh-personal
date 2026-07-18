---
id: docs-ai-pattern-intelligence-adr-adr-a-nesting-engine
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-A — Nesting Engine Selection & Bake-off Protocol

**Status: DRAFT (Phase 1) — owner sign-off pending. Scope: AI Pattern Intelligence.**
Ratifies decision inputs: Blueprint V3 §6-refs (V2 §8/§11), 01_RESEARCH §2.

## Problem
Marker generation needs a 2D irregular nesting engine honoring garment
constraints (grain 0/180, mirror pairs, cut-on-fold, tubular lays). Candidate
open-source engines are unproven for our shapes: pynest2d is a thin binding
built for Cura's convex "arrange" use case; SVGnest is battle-tested but
dormant JS; writing our own NFP+GA engine is months of work. Choosing wrong —
or coupling the schema to any engine — is the expensive mistake.

## Decision
1. **Engine-agnostic boundary first**: one `nesting_service` interface; engines
   are adapters invoked as isolated subprocesses; garment constraints compiled
   to engine primitives BEFORE the call; canonical geometry/placements never
   contain engine-native data (V3 constitution F4).
2. **P0 hostile bake-off** with criteria fixed in advance, on the REAL harness:
   digitised T-shirt front/back/sleeve + 3-Patti pieces, one >1 m piece, one
   curved-heavy piece, one on-fold tubular piece; real widths (µm); 0/180 +
   mirror + fold constraints; wall-clock budget on the factory server.
   Candidates: (a) **SVGnest via pinned headless Node runner** (expected
   primary), (b) **libnest2d/pynest2d subprocess** with a mandatory
   concave-vs-concave adjacency test before trust, (c) **bottom-left-fill
   fallback in pure Python** — the always-works floor, kept forever.
3. Selection = utilization on harness + constraint fidelity + wall-clock +
   rebuild-from-vendored viability. Numbers become an ADR-A addendum; the
   losing adapters remain in-tree behind the same interface.
4. Every `MarkerRun` stores engine id + commit + seed + params (audit).

## Alternatives considered
- **Commit to one engine now** — rejected: concave behavior unproven; the
  bake-off is one week and prevents a year-long regret.
- **Write our own NFP+GA immediately** — rejected for v1: months of effort;
  BLF floor + adapters give the same optionality cheaper.
- **Cloud nesting API** — rejected outright: violates offline / no-paid-API /
  no-cloud locks.

## Tradeoffs
Adapter indirection costs a little plumbing; subprocess isolation costs
serialization overhead (acceptable: nesting is seconds-to-minutes, ADR-B
handles async). Maintaining a BLF floor costs ~200 lines once and removes the
"engine died, factory stuck" failure class.

## Consequences
Engines are commodity plug-ins; the marker library outlives any of them.
P0 cannot be skipped — generation work is blocked until bake-off numbers exist.
We accept possible fork-maintenance of the winner (budgeted, ADR-F vendoring).

## Future evolution
New engines (or a future in-house NFP) join as adapters with zero schema
change. GPU or remote-worker execution would be an ADR-B evolution, not a
schema event. Strategy set (mixed/sectioned/fold-aware) can grow additively.

## Why it respects Manufacturing V1
No production table, service, or flow is touched; nesting runs entirely inside
`patterns_ai` compute isolation; no money paths; frozen contracts §7 untouched.

## Why it respects Blueprint V3
Implements F4 engine-independence as a hard boundary; keeps stored placements
as the artifact (C16 render-reproducibility); honest-AI vocabulary ("strategy
search", never intelligence); P0 gate matches V3 roadmap; simplicity principle
(floor fallback over speculative engine work).

---

## ADDENDUM 1 — P0 bake-off results (2026-07-06, empirical)

Harness: `poc/patterns_ai/` (reproducible; pinned venv + vendored SVGnest
@1248dc2, MIT; Node v18.20.8). Sets: T-SHIRT body S2:M2:L1 (20 pieces,
1100 mm) · 3-PATTI brief S2:M2:L1 (15 pieces, 940 tube-flat) · stress
(>1 m leg ×4 mirrored, curved sleeves, on-fold half-front; 940 mm).
Spacing 2 mm; utilization = piece area ÷ (width × marker length), end
allowances excluded by design.

| Set | BLF-grid floor (deterministic) | SVGnest core headless (201 seeded trials) |
|---|---|---|
| T-SHIRT | **79.86 %** · 4974 mm · 172 s | **80.11 %** · 4959 mm · 106 s |
| 3-PATTI | 73.90 % · 1160 mm · 11 s | **79.30 %** · 1081 mm · 15 s |
| stress | 76.78 % · 2412 mm · 29 s (fold-pinned) | 75.91 % · 2440 mm · 3 s (piece unfolded) |

Findings:
1. **Gate (≥75–80 %) MET.** SVGnest's real NFP core (Minkowski/Clipper path)
   runs headless with a ~180-line Node runner; all pieces placed on every set
   including the >1 m panel.
2. **The BLF floor is honest competition** (wins T-SHIRT vs a shallow search)
   — kept forever as specified; deeper GA search is the known upside left on
   the table (browser SVGnest runs minutes, we ran 201 trials).
3. **pynest2d: NOT VIABLE** — no PyPI distribution exists at all
   (`pip install pynest2d` → no versions); source build = libnest2d + SIP +
   Qt toolchain. Fails the maintainability criterion; eliminated.
4. Runner lessons encoded: clipper.js needs a `navigator` shim; grain axis
   must be normalized to the lay axis (a real bug caught by the >1 m piece —
   the stress set doing exactly its job).
5. **SELECTION: SVGnest core (headless) = primary engine; BLF-grid = the
   always-works floor.** Node runtime + SVGnest fork enter the ADR-F vendor
   manifest (readiness condition N-3 satisfied — harness already runs from
   the vendored tree).
