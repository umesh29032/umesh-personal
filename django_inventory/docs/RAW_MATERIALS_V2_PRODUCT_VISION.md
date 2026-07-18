---
id: docs-raw-materials-v2-product-vision
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Raw Materials V2 — Product Vision

> **Status: VISION ONLY (owner-authorized 2026-07-18).** This document preserves the
> long-term business vision so it survives deployment and personnel/context changes.
> It is NOT a design document, NOT an implementation plan, NOT a roadmap, and it
> changes nothing about the frozen campaign roadmap (Phases 16–22).
> **Implementation begins only AFTER Phase 22 (First Git Checkpoint)** — see §10/§11.
> Companion decision of record: the 2026-07-18 roadmap impact review (owner ruling:
> roadmap kept exactly as-is; Phase 17 NOT expanded; no RM-V2 work before deployment).

## 1. Business motivation

Kapil Enterprises manufactures garments. A garment is never made of cloth alone: every
finished piece consumes elastic, thread, needles, buttons, labels, packaging, poly bags,
stickers, and more. Today the ERP gives cloth a complete, certified life story — intake,
warehouse, consumption, cost — while every other material the factory buys and consumes
lives outside the system (memory, paper, phone calls). The business cannot see its full
material position, cannot trace most of its material spend, and cannot answer "what did
this production run really consume?" beyond fabric. The motivation for Raw Materials V2
is simple: **the whole factory's material reality should live in the ERP, not just the
cloth part of it.**

## 2. Current ERP limitations

- **One material, hard-coded:** the raw_materials app models exactly one material —
  cloth rolls (type · color · roll · kg · storage location). Every other material on the
  raw-material dashboard is a placeholder tile ("coming later").
- **One unit assumption:** cloth thinks in rolls and kilograms. Thread thinks in cones,
  elastic in meters, buttons in gross, poly bags in packets. The current model has no
  concept of per-material units.
- **One purchasing shape:** cost-per-kg on the roll is the purchase fact (ADR-0009).
  Other materials are bought by piece, box, meter, or lot — none of which fit today.
- **One consumption story:** cloth is consumed by the layering/cutting workflow with
  full audit history. Other materials are consumed invisibly — no issue, no draw-down,
  no leftover story.
- **Adding a material = a code project:** today a new material means new models, new
  migrations, new views, new tests. The owner cannot introduce one.

## 3. Long-term owner vision

The Raw Materials domain becomes a **complete manufacturing inventory foundation**: one
place where every material the factory buys, stores, and consumes is registered, counted,
valued, and traceable — with the same discipline the ERP already applies to cloth,
production truth, and money. The owner (not a developer) defines what materials exist and
how each behaves; the ERP provides the certified machinery underneath.

## 4. Why cloth must not remain the only raw material

- Cloth is typically the largest single material cost, but the **sum** of secondary
  materials (elastic, thread, packaging, trims) is a real and currently invisible spend.
- Product cost truth is incomplete without them: the ADR-0009 full-cost picture can only
  ever be as honest as the material record behind it.
- Stock-outs of "small" materials stop production exactly as hard as missing fabric —
  a factory that can see 32 cloth rolls but not zero elastic is blind where it hurts.
- The ERP's own trajectory (production truth → settlement truth → expense truth →
  operating dashboard) points one direction: every business fact gets one certified home.
  Materials are the largest remaining fact without one.

## 5. Future examples of raw materials

Cloth · Rib · Elastic · Thread (dhaga) · Needles (sui) · Buttons · Labels/Tags ·
Packaging · Poly bags · Stickers — **and any future owner-defined material.** (The
current dashboard already anticipates several of these as placeholder tiles; this vision
makes them first-class.) Each may differ in units, purchasing method, inventory
behaviour, warehouse handling, and production consumption.

## 6. Owner-configurable material philosophy

The defining principle of V2: **introducing a new raw material must not require ERP code
changes.** The owner registers a material and describes how it behaves — its unit, how it
is purchased, how it is stored, whether and how production consumes it — and the system
runs it with the same guarantees as every existing material. The precedent already exists
in this ERP: the generic stage archetype made "new production stage" a configuration act
instead of a code project. Raw Materials V2 applies the same philosophy to materials.

## 7. High-level business goals

1. Every material the factory buys exists in the ERP with a live, trustworthy quantity.
2. Every material's purchase cost is recorded at intake, as a fact, once.
3. Production consumption of any material is visible and traceable to the work that
   consumed it.
4. Warehouse reality (where things physically are) is queryable for all materials.
5. Material spend becomes reportable — by material, by period, and (where honest)
   by product — under the existing cost-truth laws.
6. The owner can add, rename, and retire materials without a developer.
7. The Business Operating Dashboard can eventually summarize the full material position
   (through its existing Ladder/Registry laws — no new dashboard machinery).

## 8. Business principles

These are business commitments, not designs; any future design must honor them:

- **One truth per material fact** — a quantity, a cost, a location each live in exactly
  one authoritative place; everything else derives from it.
- **Facts over estimates** — purchase cost is recorded, never inferred; unknown stays
  honestly unknown (the honest-NULL principle, never a silent ₹0).
- **Work-that-happened is immutable** — consumption and movement history is append-only,
  corrections are new facts, nothing is silently rewritten.
- **Money laws unchanged** — ADR-0009 (cost truth, no processing-cost+labor blending) and
  ADR-0011 (factory expenses never per-Adda) continue to bind; material cost integration
  follows the same certification discipline as every money surface.
- **Cloth is the template, not the exception** — cloth's certified lifecycle is the
  quality bar every material must reach, and cloth itself must keep working unchanged
  throughout any transition.
- **Configuration over code** — per §6; developer involvement is for new *behaviours*,
  never for new *materials*.

## 9. Out of scope (for this document AND for V2's first breath)

- Database tables, models, services, APIs, workflows, UI — **no design of any kind here.**
- Supplier management / procurement workflows (purchase orders, approvals) — a possible
  later chapter, not the entry point.
- Automatic BOM (bill-of-materials) deduction, forecasting, reorder automation, or any
  predictive/AI capability.
- Multi-factory material transfer (bound by ADR-0010's growth/identity locks).
- Revenue, sales, or finished-goods commerce (separate domains entirely).

## 10. Relationship with the existing roadmap

The campaign roadmap (Phases 16–22) is **frozen and unchanged** by this vision:

- **Phase 16 (Monthly Expense Engine):** unaffected; raw-material purchasing is an
  explicit non-goal of MEE (boundary to be recorded at MEE-0).
- **Phase 17 (Raw Material → Expense Cost Integration):** executes its existing
  read-path contract unchanged. Two compatibility observations are to be recorded at its
  own Design Records (material-cost reads behind a service seam; prefer read-path models
  over materialization) so V2 later widens a seam instead of rewriting pages.
- **Phases 18–22:** unaffected; this document itself is the vision-capture item the
  roadmap review recommended.
- After Phase 22, the already-planned complete roadmap review sequences Raw Materials V2
  as its own program: PDD change-control → a dedicated RM_V2 DESIGN document (separate
  from this vision) → hostile review → its own phases, numbered after 22.

## 11. Implementation gate

**No Raw Materials V2 implementation — no schema, no services, no UI, no migrations, no
prototypes — begins before Phase 22 (First Git Checkpoint) is complete and the owner has
explicitly chartered the program through PDD change-control.** This document grants no
build authority; it exists so the vision cannot be lost.
