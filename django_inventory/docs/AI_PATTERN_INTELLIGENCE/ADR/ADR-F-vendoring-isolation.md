---
id: docs-ai-pattern-intelligence-adr-adr-f-vendoring-isolation
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-F — Vendoring & Runtime Isolation

**Status: DRAFT (Phase 1) — owner sign-off pending.**

## Problem
The platform must run offline, forever, from our own repository (owner lock).
Its pillars rot upstream: SAM-family checkpoints move or vanish, torch/ONNX
versions drift, libnest2d C++ stops compiling on new toolchains, SVGnest is
dormant JS. A future `pip install` at deploy is a time bomb; an accidental
`import torch` in Django's venv holds security upgrades hostage.

## Decision
1. **Everything vendored, checksummed, owned:** model weights (ONNX), engine
   sources/forks (SVGnest runner, libnest2d, BLF), JS libs for the geometry
   editor, print-pipeline deps — in the repo or the owned artifact store;
   NOTHING fetched from upstream at deploy or runtime. License recorded per
   artifact in a manifest.
2. **Two-runtime isolation:** Django's venv NEVER imports torch/onnxruntime or
   nesting engines. Compute runs in a separate pinned runtime (own venv/
   subprocess, own lockfile), invoked by the ADR-B worker via files/argv.
   LGPL libnest2d stays subprocess-isolated PERMANENTLY (license hygiene —
   inlining is a review-reject).
3. **No-network guarantee is tested:** a CI/test asserts the compute paths
   make zero network calls (socket-blocking test harness); fonts, tiles, CDNs
   included — the print pipeline embeds its assets.
4. **Annual rebuild-from-vendored drill** in the deploy runbook: fresh machine,
   no internet, repo + artifact store only → full stack builds and a golden
   capture + golden nesting run reproduce (render-level, per C16).
5. **If training scripts are ever needed** (owner vision): scripts, datasets,
   and documentation live in-repo under the same manifest discipline.

## Alternatives considered
- **pip/npm at deploy** — rejected: link-rot + supply-chain drift; violates
  repo-reproducibility.
- **Containers as the only isolation** — insufficient alone (images rot too);
  containers may WRAP the pinned runtimes, but the vendored sources +
  lockfiles are the truth. Accepted as an optional packaging layer.
- **Monolithic single venv** — rejected: torch pin conflicts would hostage
  Django/security upgrades; GIL/lifecycle coupling.

## Tradeoffs
Repo/artifact store grows by hundreds of MB (weights) — bounded, owned, and
cheap versus a dead capture pipeline. Vendoring means WE ship upstream fixes
(budgeted "own the fork" line item from research). The drill costs one day a
year and is the only honest proof of the offline promise.

## Consequences
A fresh machine with no internet rebuilds the platform. Upstream death is a
non-event. Engine/model swaps are artifact-manifest changes behind stable
adapters (ADR-A, ADR-E ladders).

## Future evolution
Local-LLM slot (D10, if ever enabled) enters under the SAME manifest +
isolation rules. GPU runtimes = a second pinned compute profile. Artifact
store may move to MinIO alongside ADR-G's media switch — same checksums.

## Why it respects Manufacturing V1
The manufacturing venv and deploy remain untouched; no new runtime dependency
enters the frozen engine's process; the drill lives in the existing deploy
runbook structure.

## Why it respects Blueprint V3
Directly implements the open-source/offline/no-paid-API lock and F4 engine
independence at the operational level; honest-AI (golden-run proof, not
promises); simplicity (files + subprocess, no orchestration frameworks).
