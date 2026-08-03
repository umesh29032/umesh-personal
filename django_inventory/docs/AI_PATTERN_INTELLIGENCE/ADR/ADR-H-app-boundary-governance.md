---
id: docs-ai-pattern-intelligence-adr-adr-h-app-boundary-governance
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-H — App Boundary, RBAC Surface & Governance

**Status: DRAFT (Phase 1) — owner sign-off pending. Pack approval also
ratifies: the PDD amendment registration, the ops-master §11 wording amendment
(D8), and the D1–D11 finals mapped in the certification document.**

## Problem
The platform must live INSIDE the ERP without ever leaning on the frozen
manufacturing engine: no production writes, no reverse imports, a clean RBAC
surface (no pattern capability exists today), and governance that survives
years of convenient temptations ("just prefill the layering form…").

## Decision
1. **New app `patterns_ai`** with its own models/services/views/urls/templates
   and media tree. **FKs point INTO production only** (Product, ProductPattern,
   ProductPatternAssignment, ProductSize, Adda, stage records) — the machines-
   app direction rule.
2. **Production never imports patterns_ai — zero exceptions.** Stricter than
   machines (which has 3 sanctioned lazy reads): the UI seam is link-out /
   deep-link with query params only. Enforcement is layered: `patterns_ai`
   added to `config/.importlinter` root_packages + top layer with **no
   ignore_imports**, PLUS a FoundationPurityTests-style runtime test (the
   layers contract alone is report-only today and would not block creep).
3. **Proposals-only toward production (the constitution's clause 1):**
   patterns_ai persists proposals + its own knowledge; humans accept by acting
   in existing production UIs. On pack approval, ops-master §11's row is
   amended to say exactly this (D8) — closing the last documented wording
   contradiction.
4. **Single-writer services:** `capture_service` · `pattern_geometry_service` ·
   `marker_service` · `marker_feedback_service`. Import/backfill tooling uses
   the same chokepoints (I-1); raw-ORM writes are a review-reject.
5. **RBAC surface (D4 finals proposed):** capture + geometry approval =
   `cutting_master` skill (no new skill until a dedicated pattern-master role
   exists in reality); marker activation/promotion/retirement =
   MANAGEMENT_ROLES; workers never see geometry screens. Every URL registered
   in `SidebarItemRule` (menu + URL co-gated, V1 rule 6); capture trained to
   ≥2 people (succession).
6. **Money: none.** Meters/% only until GSM (D3, P1 mini-ADR on the
   manufacturing side, owner-approved); thereafter ₹ is read-only presentation
   honoring ADR-0009 honest-NULL; any write-path temptation trips the
   Money-Write STOP rule.
7. **Governance:** PDD amendment registered before P1 code; module changes
   after pack approval go through project ADR addenda; any discovered
   frozen-contract contradiction = STOP + report (owner global rule 11).

## Alternatives considered
- **Extend the production app** — rejected: violates the freeze; couples the
  knowledge platform to the engine's release discipline.
- **Sanctioned lazy reads from production (machines-style)** — rejected here:
  nothing in the manufacturing flow NEEDS to read patterns_ai; zero-exception
  is simpler to defend for a decade.
- **New `pattern_master` skill now** — deferred: today's factory reality is
  the cutting master; a skill row is config the owner can add the day the role
  exists.
- **Generic plugin framework** — rejected: YAGNI; one well-bounded app.

## Tradeoffs
Link-out UI means the pattern console never embeds patterns_ai widgets — a
deliberate UX ceiling that buys architectural certainty. Zero-exception import
rule may one day force a small duplication instead of a convenient read —
accepted; duplication is cheaper than erosion.

## Consequences
The module is deletable-in-theory (nothing in manufacturing would notice) —
the strongest possible proof of boundary health, and the property that keeps
Manufacturing V1's freeze meaningful for years.

## Future evolution
A future embedded surface (if ever owner-approved) would enter via a new ADR
defining a read-only context API; multi-factory site scoping arrives as
filters on site-scoped assets (V3 §4.0); new skills/roles = config rows.

## Why it respects Manufacturing V1
It is the freeze's §7 contracts translated into this module's constitution:
no production writes, FK direction, single-writer, RBAC via permission_service
+ SidebarItemRule, no money, docs-sync, ADR-gated change.

## Why it respects Blueprint V3
Implements the compliance clauses of V2 §7/V3 §5 verbatim; the zero-exception
import stance strengthens F4/F1; D8 execution removes the final documented
contradiction; simplicity over convenience throughout.
