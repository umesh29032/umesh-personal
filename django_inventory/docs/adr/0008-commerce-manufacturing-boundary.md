---
id: docs-adr-0008-commerce-manufacturing-boundary
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR 0008 — Commerce↔Manufacturing Boundary (future-safe ownership model)

**Status: 🔒 ACCEPTED 2026-06-11 — owner locked all points incl. the MTS/MTO clause and gap registry G1-G7.** Seams-not-features (ADR
0006 discipline): this ADR names boundaries and relationships so V2-2/V2-3,
Missing/Alter, Costing, Reporting, and future commerce converge — it builds
NOTHING now.

## The ownership model

```
  COMMERCE DOMAIN (future)            BRIDGE (future, G5)            MANUFACTURING DOMAIN (built/building)
┌─────────────────────────┐   ┌──────────────────────────────┐   ┌─────────────────────────────────┐
│ Customer                │   │ FINISHED-GOODS INVENTORY     │   │ Adda (production batch)         │
│ Order / OrderLine       │──▶│  stock units = PIECES        │◀──│  stages, tasks, contributions   │
│   (REVENUE TRUTH)       │   │  (BatchBarcode already IS    │   │  AddaSettlement (LABOR COST)    │
│ Invoice / Payment-in    │   │   the piece identity)        │   │  material consumption (G1)      │
└─────────────────────────┘   │  on-hand · reserved ·        │   │   (COST TRUTH)                  │
        ▲                     │  allocated-to-order ·        │   └─────────────────────────────────┘
        │ prices, discounts   │  dispatched                  │            ▲
        │ live HERE only      └──────────────────────────────┘            │ costs live HERE only
        │                                                                 │
        └───────────── PROFITABILITY = DERIVED READ-MODEL ────────────────┘
                       (reporting layer; computed, never stored on either side —
                        same discipline as Option B and the §5A two-truths rule)

  PRODUCT MASTER: production.Product is THE product identity (G6).
  Catalog/storefront entities are sales-side PROJECTIONS referencing it —
  never parallel product definitions.
```

## The six answers

**1. Order↔Adda relationship: INDIRECT, mediated by finished-goods inventory.**
An Adda *produces pieces into stock*; an Order *consumes pieces from stock*.
The piece (BatchBarcode — already string-FK'd, already carrying adda identity)
is the natural join. A direct Order→Adda FK is the retrofit trap: it hard-wires
make-to-order and breaks the moment one Adda serves stock + two orders, or one
order pulls from three Addas. One soft seam is allowed later: an optional
`initiated_for` provenance reference on Adda ("this batch was started because
of order X") — a planning hint, NEVER a money/ownership edge.

**2. One Order → multiple Addas: YES.** An order for 1,000 pieces may be
fulfilled by three Addas plus existing stock. The order's fulfillment plan is a
commerce-side concern reading inventory; manufacturing never needs to know.

**3. One Adda → multiple Orders: YES.** A stock Adda's 500 pieces may ship to
five customers across months. This is precisely why the relationship must run
through inventory, not an FK.

**4. Revenue truth lives in the COMMERCE domain** — Order/OrderLine (and a
future Invoice). Never on the Adda, never in production models. Mirror of the
locked production-truth ≠ financial-truth split: the Adda knows what was MADE
and what it COST; only commerce knows what it SOLD FOR.

**5. Profitability = a DERIVED read-model, never stored.** Three levels, all
computed in the reporting layer:
- **Adda production margin** = output valuation − (settled labor + material
  cost (G1) + variance valuation (G3)). Needs a *valuation policy* for output —
  part of G3's decision.
- **Order margin** = order revenue − cost of the pieces allocated to it, where
  per-piece cost = its Adda's total cost / pieces (traceable TODAY via the
  barcode's adda linkage — piece-level traceability is the cost-attribution
  bridge we already own).
- **Period P&L** = aggregation of the above.
Storing a "profit" column anywhere would violate the derived-never-stored rule
the way storing readiness or balances would; this keeps both truths clean and
the comparison honest.

**6. G1-G3 are NOT sufficient. Two deeper gaps, named now:**
- **G5 — Finished-goods inventory & allocation domain (THE missing mediator).**
  Today an Adda "completes" and its pieces exist only as barcode ranges; there
  is no stock concept (on-hand / reserved / allocated / dispatched). Without
  G5, any future order system WILL grab a direct Adda FK — the exact retrofit
  this ADR exists to prevent. Seams already in place: the R1 F-archetype
  (packing/dispatch), scan statuses (packed/dispatched), piece identity. G5 is
  a future module, not current work.
- **G6 — Single product master.** `production.Product` is the identity; the
  storefront's standalone catalog entities (FeaturedProduct etc.) are already a
  small parallel-definition seed. Direction locked: sales-side entities become
  projections REFERENCING production.Product; no second product definition
  ever. (Cheap to honor now: any new commerce model points at the master.)

## Make-to-Stock AND Make-to-Order under the same model (owner clarification)

The unifying rule: **MTO is MTS with zero dwell time — pieces ALWAYS flow
produce → stock → allocate, even when "stock" holds them for one second.** One
model, both modes, no future reversal:

1. **Order requiring fresh production:** the order's lines try to reserve from
   G5 stock; the shortfall stands as visible UNFULFILLED DEMAND. Production
   responds by creating Adda(s) (a human decision now, optionally
   planning-assisted later), each carrying the `initiated_for` provenance hint.
   On completion the pieces enter stock and G5 allocates them to the waiting
   lines. The order never touches the Adda; it watches its reservations fill.
2. **`Adda.initiated_for` scope:** sufficient for what it is — PROVENANCE
   (traceability + MTO reporting: "this batch existed because of order X").
   It is NOT a reservation. "These future pieces are promised to order X"
   is a G5 reservation-against-incoming-production state, order-side —
   exactly where promise/priority logic belongs. The two concepts must not
   be merged onto the Adda.
3. **Mixed fulfillment** (part stock, part fresh production) is the model's
   home turf: an order line's allocations are G5 records spanning existing
   pieces + reservations against initiated Addas. This is the case that
   structurally breaks a direct Order→Adda FK — and works trivially here.
4. **Planning/scheduling domain:** NOT required between Orders and Addas.
   If MRP-lite ever becomes worth building (demand → production suggestions,
   capacity views), it is an OPTIONAL OVERLAY that READS both sides
   (unfulfilled demand from G5, capacity from manufacturing) and OWNS NO
   TRUTH — derived-never-stored, same as profitability. Its absence costs
   nothing; its later addition reverses nothing. Recorded as **G7 (optional
   planning overlay)** for completeness.

## Gap registry (consolidated, all FUTURE-owned, none block V2-2)
| Gap | What | Owning future phase |
|---|---|---|
| G1 | Material-cost rollup per Adda (data already captured: rolls, weights, ₹/kg, leftovers) | **Costing-2** (after V2-3) |
| G2 | Revenue capture + linkage | Commerce/Orders phase (via G5, per this ADR) |
| G3 | Variance/output valuation policy (₹ value of missing/rejected/output) | Costing-2 / Reporting design |
| G4 | Adda-360 screen | Reporting's first deliverable |
| G5 | Finished-goods inventory & allocation domain | Commerce prerequisite module |
| G6 | Product-master unification direction | standing rule from lock-date |
| G7 | Optional planning/MRP-lite overlay (derived, owns no truth) | only if demonstrated need |

## What this changes about current work: NOTHING.
V2-2's AddaSettlement is exactly the Adda-side cost-closing event this model
needs; V2-3, Missing/Alter, Costing-2 and Reporting all slot in unchanged. The
only behavioral rule effective immediately: **new commerce-adjacent models
reference production.Product and never gain a direct Adda money-edge.**

## Sign-off
- [x] Owner locked 2026-06-11: indirect Order↔Adda via G5 inventory · revenue in
      commerce · profitability derived-never-stored · G5+G6+G7 in the gap
      registry · product-master rule effective now · MTO = MTS with zero dwell

## Addendum — C-1 margin-formula amendment (2026-06-11, ADR-0009 companion)

The locked margin formula is amended to close the non-payable-stage hole:

> Adda production margin = output valuation − (ACTUAL settled labor
> + material cost (G1) + variance valuation (G3)
> **+ processing_cost of NON-payable priced stages** + future overhead).

Without the bolded clause, flows containing priced `credits_workers=False`
stages (outsourced/machine work — their cost exists ONLY as processing_cost)
would overstate margin. Companion rule (ADR-0009): settled labor and
processing_cost of PAYABLE stages are the same money — never both.

Enforcement line (schema form of this ADR's boundary): production models never
grow price/revenue fields; commerce references manufacturing identity only via
the future G6 SKU entity (see ADR-0010 §5).
