---
id: docs-pkals-v2-pkals-v2-effort-estimate
type: topic-canonical
status: active
owner: handwritten
scope: docs
anchors: —
verified: 2026-07-18
---

# PKALS v2 — COST / BENEFIT + EFFORT ESTIMATE (Discovery, design-only)

> **PROPOSAL. Nothing implemented.** Sizing is for a solo dev with AI assistance
> (Claude does most of the typing; estimates are wall-clock incl. review/test).
> Scale: XS ≈ <½ day · S ≈ ½–1 day · M ≈ 1–2 days · L ≈ 3+ days.

## F. Cost / Benefit per feature

| # | Feature | Value | Complexity | Maint. burden | Risk | Recommendation |
|---|---|---|---|---|---|---|
| 1 | change-impact tool + **/impact** | **High** — operationalizes PKALS-LIVE (the most-skipped step) | S | Low (reads matrix) | Low | **MUST** |
| 2 | route-map drift check | **High** — catches periphery URL drift in CI | S | Low (introspection) | Low (false-pos low) | **MUST** |
| 3 | model-map drift check | **High** — catches per-model doc drift in CI | M | Low | Low–Med (field-name matching) | **MUST** |
| 4 | **/find-canonical** skill | **High** — cheapest AI routing; high call volume | XS | ~0 (manifest CI-guarded) | Low | **MUST** |
| 5 | knowledge-sync hook | **High** — makes the matrix lookup automatic at commit | S | Low | Low (advisory first) | **MUST** |
| 6 | missing-CHANGE_IMPACT detector | Med-High — flags skipped doc updates | M | Med (N/A is legit → tuning) | Med (false-pos) | NICE |
| 7 | /trace-request + /debug-flow | Med — convenience over journeys/index | XS each | Low | Low | NICE |
| 8 | /update-docs skill | Med — guided checklist over #1 | XS | Low | Low | NICE |
| 9 | dead-doc detector (cite→symbol) | Med — finds stale code citations | M | Med (AST cite parsing brittle) | Med | NICE |
| 10 | /architecture-review (checklist) | Low-Med — can't replace judgment | S | Med (drifts from rules) | **Med-High** (false confidence) | NICE (checklist only) |
| 11 | Online Learning System (heavy) | Low — duplicates v1 LEARNING/ | L | **High** (parallel tree) | High (bloat/drift) | **NOT WORTH** |
| 12 | Self-healing auto-rewrite | Negative — unsafe prose generation | L | High | **High** | **NOT WORTH** |
| 13 | Docs website / generator | Low — md+manifest already serve | M-L | High | Med | **NOT WORTH** |
| 14 | Doc auto-generation from code | Low — fights verified-from-code ethos | L | High | High | **NOT WORTH** |

## Effort by phase (Must set)
| Phase | Items | Est. | Notes |
|---|---|---|---|
| v2-A foundation | #1 /impact + change-impact, #4 /find-canonical | **S–M (~1–1.5 d)** | smallest, highest leverage; proves the wrap-not-copy pattern |
| v2-B drift CI | #2 route-map, #3 model-map | **M (~1.5–2 d)** | introspection-based; add to scripts/check.sh |
| v2-C sync | #5 knowledge-sync hook | **S (~½–1 d)** | thin wrapper over #1 |
| **Must total** | 5 items | **~3–4.5 days** | each phase independently shippable + revertible |
| v2-D optional (Nice) | #6–#10 | **~3–5 days** | only if Must visibly cuts maintenance effort |

## ROI summary (solo dev, AI-assisted ERP)
- **Best ROI single item:** #1 (change-impact + /impact) — converts the core
  discipline into one command; ~S effort, High value, Low risk.
- **Best ROI pair for drift:** #2 + #3 — close the exact ceiling v1 documented
  (periphery lag), deterministically, in CI; ~M total.
- **Cheapest win:** #4 /find-canonical — XS, near-zero maintenance, high call volume.
- **Avoid:** the L-effort/High-risk Not-worth items (#11–#14) — they re-introduce the
  bloat/drift v1 spent five sessions eliminating, for low value to one maintainer.

## Recommendation (does v2 exist?)
**Build a small v2 = the 5 Must items (v2-A..C, ~3–4.5 days), gated.** They are cheap,
robust, reuse v1, add no content, and directly reduce the solo dev's per-change
maintenance burden while catching periphery drift in CI. **Defer the Nice set** until
the Must set proves it cuts effort. **Do not build the Not-worth set.** If budget is
one item only: ship #1. If zero appetite: v1 alone is already at the practical-quality
band — v2 is an optimization, not a necessity.

*Estimates are planning-grade, not commitments; refine at build time per phase.*
