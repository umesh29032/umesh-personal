---
id: docs-ai-pattern-intelligence-product-vision-v2
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PRODUCT VISION V2 — THE SOURCE OF TRUTH (owner reset, 2026-07-07)

**This document supersedes every prior roadmap/vision statement for the
pattern project. Permanent direction. All future work aligns to THIS.**

## The product (verbatim intent)

Products contain Pattern Pieces. Digitize the physical pieces by photo →
accurate geometry. Generate the best possible marker layout inside a
user-defined fabric **width and height** to minimize wastage. Let the
user manually adjust the layout; AI rearranges the remaining pieces.
Export.

## The complete workflow (do not change)

Product → Pattern Pieces → Capture Photos → Extract Geometry → Human
Verification → Digital Pattern Library → Choose Fabric Width/Height →
Generate Marker Layout → AI Optimizes → Human Adjusts → AI Re-optimizes
Remaining Pieces → Export (DXF / SVG / PDF / Print).

## AI's ONLY responsibility

Best possible marker layout: arranging pieces, minimizing wastage,
maximizing utilization, multiple candidates, helping after manual edits,
improving layouts over time. **Nothing more.**

## Explicitly OUT (permanent do-not-build list)

Factory/Business/ERP intelligence · executive dashboards · production AI ·
multi-order optimization · fabric/cloth-stock AI · roll prediction ·
operator analytics · learning LLMs · chat assistants · management AI ·
ROI prediction · recommendation systems unrelated to marker generation ·
enterprise reporting · digital twin · predictive manufacturing.
Existing code purely serving these = **optional future research, OFF the
active roadmap, never extended.**

## Project rules (permanent)

Prefer simplicity · maintainability · correctness · practicality.
Avoid over-engineering · unnecessary abstraction · features without a
direct business need · enterprise assumptions · just-in-case building.
"Nice to have" = NOT implemented unless explicitly asked.

## Working method (every phase)

Design → architecture review → implementation → testing → browser
testing → engineering review → regression → documentation → freeze →
next phase. No phase starts before the previous is complete and reviewed.

Roadmap: [ROADMAP_V2](ROADMAP_V2.md). Audit of prior work: same file, §2.
