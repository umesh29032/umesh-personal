---
id: kos-target-vision
type: topic-canonical
status: draft
owner: handwritten
scope: all — the long-term target of the Knowledge Operating System itself
anchors: docs/campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md, docs/campaign_contracts/PHASE_08_KNOWLEDGE_GRAPH.md, docs/campaign_contracts/PHASE_09_DOCUMENTATION_GENERATION.md, docs/campaign_contracts/PHASE_14_KNOWLEDGE_SYNC.md, docs/campaign_contracts/PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md
verified: 2026-07-13
---

# KOS TARGET VISION — the Engineering Knowledge Operating System (long-term)

> **Amendment 2026-07-19 (owner-approved two-layer split):** the human/prose half of
> this vision now lives in **`kos/`** (repo root) — the owner-approved Knowledge
> Operating System v1 (translation layer: code + docs/ → human understanding;
> constitution: [kos/STANDARDS.md](../kos/STANDARDS.md)). The structural/generated
> half (URL cards, graph, per-page items 3–10/12–14 of §2) remains this document's
> docs/-side scope (Phases 8–9/14/18 unchanged). This amendment changes NO contract;
> the register note in §2 (structural=generated, prose=handwritten) is exactly the
> line along which the split was made.

> **Status: `draft` — LONG-TERM VISION ONLY (owner-approved for recording 2026-07-13).**
> This document is **NOT a contract**. It modifies NO existing contract, changes NO frozen
> phase's scope (Phase 7 included), and introduces NO implementation work by itself. It is
> subordinate to every truth lock ([PDD](PRODUCT_DESIGN_DOCUMENT.md), [ADRs](adr/README.md),
> [ARCHITECTURE_V2](ARCHITECTURE_V2.md), [MANUFACTURING_V1_FREEZE](MANUFACTURING_V1_FREEZE.md),
> [FACTORY_OPERATIONS_MASTER](FACTORY_OPERATIONS_MASTER.md)), to
> [DOC_STANDARDS.md](DOC_STANDARDS.md) (the frozen documentation constitution), and to the
> frozen campaign contracts ([campaign_contracts/](campaign_contracts/README.md)).
> **Binding force:** none directly — each future phase's Design Record (KG-0, GEN-0, SYNC-0,
> FFD-0, and any post-Phase-22 charter) decides at its own owner-gated ratification how much
> of this vision it adopts. This document is the INPUT they cite.

## 1. The vision

This repository must not end as only a documentation repository. The long-term target is a
complete **Engineering Knowledge Operating System**: every important URL, feature, workflow,
business process, service, model, handler, view, form, API, transaction, permission, and
database relationship has **exactly one canonical knowledge home**, and both humans and AI
agents can understand a feature completely **without repeatedly scanning the repository**.

Core tenets:

1. **Every important URL has exactly one canonical knowledge home** (the URL knowledge card,
   Design Record R4: one card per route).
2. **Every business feature has exactly one canonical knowledge home** (the features/ layer,
   Design Record R3; the Single-Canonical-Home owner directive of 2026-07-13).
3. **Every page explains its business purpose before implementation details** — business-first
   ordering is a structural rule of every future knowledge unit.

## 2. The per-page knowledge target (21 items)

Every page/feature eventually documents, in one navigable home:

| # | Knowledge item | # | Knowledge item |
|---|---|---|---|
| 1 | Business purpose | 12 | Audit/history writers |
| 2 | Workflow | 13 | Calculations |
| 3 | URLs | 14 | Related ADRs |
| 4 | Handlers/views | 15 | Related business rules |
| 5 | Forms | 16 | Debugging entry points |
| 6 | Services | 17 | Common failure modes |
| 7 | Models | 18 | Testing strategy |
| 8 | Database relationships | 19 | Future extension points |
| 9 | Important fields / foreign keys | 20 | AI context |
| 10 | Permissions | 21 | Developer learning notes |
| 11 | Transactions and why they exist | | |

Register note (per the frozen Standard): items whose content is STRUCTURAL (URLs, views,
services, models, relationships, permissions, writers) are generation targets from the
knowledge graph; items whose content is PROSE (purpose, transactions-why, failure modes,
debugging, AI context, learning notes) are **handwritten/hybrid forever** — prose is never
machine-rewritten (ratified R7, permanent).

## 3. The lifecycle principle (long-term)

**A production feature should eventually be considered complete only when all applicable
artifacts are synchronized:** implementation · tests · the Knowledge Operating System ·
feature documentation · graph relationships · AI context.

This principle does **not** replace the existing roadmap — it IS the existing roadmap's
end-state, and it lands through:

- **[PHASE_18](campaign_contracts/PHASE_18_FUTURE_FEATURE_DOCUMENTATION_UPDATES.md)** — the
  permanent feature-documentation protocol already encodes this rule ("docs-complete IS
  feature-DONE": charter → U6-instrumented waves → merge gate → feature-close with graph
  rebuild + regeneration + certification sweep). This vision adds emphasis, not mechanism.
- **[PHASE_14](campaign_contracts/PHASE_14_KNOWLEDGE_SYNC.md)** — `knowledge_sync`, the pure
  detector that makes desynchronization visible (detect-and-report only; no `--fix`, ever).
- **U6** (docs-sync same session) + the **PHASE_04** permanent implementation protocol
  (tests/pins) — already standing.

## 4. The educational-code vision (future only)

Future developers should understand not only WHAT the code does but **WHY it was written
that way** — Django transactions, ORM behavior, signals policy, permissions, middleware —
so the repository doubles as a learning resource.

- The existing **CLAUDE.md rule 2** (junior-Django mode: 1-line "why" comments naming the
  Django/PG primitive on first touch) **remains unchanged** and already covers newly touched
  code.
- A **repository-wide educational comment retrofit is only a future vision** — it is NOT
  scheduled, NOT implemented now, and would require its own post-Phase-22 owner-gated phase
  (it touches application code: battery-bearing, and must be reconciled with U1
  engine-frozen and the Frozen-Foundation rules at that time).

## 5. Architectural principle (owner-stated, 2026-07-13)

> **"The Knowledge Operating System is a first-class production artifact. Its correctness is
> as important as source code, tests, database migrations, and deployment. A feature is not
> truly complete until both the implementation and its knowledge representation agree."**

## 6. How this vision connects to the existing roadmap (reference map — no scope changed)

| Vision element | Existing home | Status |
|---|---|---|
| One canonical home per URL/feature | DOC_STANDARDS §1.3/§5 · R3/R4 · Phases **8–9** | planned |
| Structural page knowledge (items 3–10, 12–14 partially) | R4 card fields + graph edges (Phase **8** build, Phase **9** generate); denominators measured in [DOCUMENT_DISCOVERY_REPORT](DOCUMENT_DISCOVERY_REPORT.md) §8 | planned |
| Templates/forms/FK-fields as first-class graph elements | additive-minor schema candidates already enumerated (DISCOVERY report §8.2) → **KG-0/GEN-0 Design Records** | amendment-sized input |
| Prose page knowledge (items 1–2, 11, 15–21) | hybrid card sections (GEN-0 template decision) + authoring lane via the **PHASE_18** per-feature lifecycle or a future dedicated phase | new content effort, owner-gated at those Design Records |
| Lifecycle principle (§3) | **PHASE_18** + **PHASE_14** + U6 + PHASE_04 | planned — already the design |
| Educational comments (§4) | CLAUDE.md rule 2 (new touches) today; retrofit = reserved **post-Phase-22** decision | future only |
| First-class-artifact principle (§5) | philosophically live in DOC_STANDARDS §1 (docs = resumability substrate; drift = bug); enforcement instruments = Phases 13/14/18 | planned |

## 7. Change control for this document

While `status: draft`: owner edits freely. If the owner later freezes it, changes follow
DOC_STANDARDS §20 discipline (dated amendments). Future Design Records that adopt parts of
this vision cite the section they adopt; nothing here binds a phase until its own -0 gate
ratifies it.
