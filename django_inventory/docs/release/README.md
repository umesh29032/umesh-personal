---
id: release-readme
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: —
verified: 2026-07-19
---

# Kapil Enterprises ERP v1.0 — Start Here

> **Who this is for:** a developer who knows Django but has never seen this
> project. Read this file first, then the [ARCHITECTURE_GUIDE](ARCHITECTURE_GUIDE.md),
> then the [DEVELOPER_GUIDE](DEVELOPER_GUIDE.md). Deploying? →
> [DEPLOYMENT_GUIDE](DEPLOYMENT_GUIDE.md). On call? → [OPERATIONS_MANUAL](OPERATIONS_MANUAL.md)
> and [TROUBLESHOOTING](TROUBLESHOOTING.md).

## What this ERP is

A **garment-factory operations system** for Kapil Enterprises: one factory,
one owner-operator, tens of workers. It tracks cloth from the moment a roll
is purchased to the moment a finished garment is packed — and it tracks every
rupee the factory owes its workers along the way.

The business problem it solves, in one sentence: **"Who did what work, on
which batch, and exactly how much do we owe them for it?"** Before this
system, that answer lived in notebooks and memory. Now it is a ledger that an
auditor can reconstruct from raw tables.

## The core workflow (learn this before anything else)

```
 Cloth Roll (raw_materials)        purchased by weight, priced ₹/kg
      │  assign to batch
      ▼
 Adda  =  one production batch of one product (production)
      │
      │  LAYERING   cloth spread in layers on the table
      │  CUTTING    layers cut into pieces  → bundles, size/color breakdown
      │  ...stages defined per-product (stitching, finishing, ironing …)
      ▼
 Workers report work per stage:  good / alter / missing quantities
      │                                   (WorkerStageContribution)
      ▼
 SETTLEMENT  (expense app)  ← THE ONLY PLACE MONEY IS BORN
      │  one AddaSettlement per batch: freezes quantities × rates
      │  → ledger credits (WorkerLedgerEntry, append-only)
      ▼
 Payment: cash payouts + advance recovery (PayrollSettlement)
      │
      ▼
 Costing & BOD dashboard: material cost + settled labor per batch
```

> **💡 Samjho aise (Hinglish):** kapda roll ke roop mein aata hai (kg mein,
> ₹/kg par). Ek batch banta hai — usse **Adda** kehte hain. Adda apne
> product ke workflow-stages se guzarta hai (layering → cutting → stitching
> …). Har stage par worker apna kaam report karta hai (kitne good, kitne
> alter, kitne missing). **Paisa tab tak sirf "expected" hota hai** — asli
> ledger entry SIRF settlement finalize par banti hai. Phir cash payment aur
> advance-recovery alag events hain. Costing sab kuch raw tables se derive
> hota hai — isliye har number ka proof nikala ja sakta hai.

Two vocabulary words you cannot work without (full list in
[../../GLOSSARY.md](../../GLOSSARY.md)):

- **Adda** — a production batch: one product, one workflow, one settlement
  boundary. Everything in production hangs off an Adda.
- **Settlement** — the act of freezing a batch's work into money. Work
  reports create *expected* earnings (visibility); **only settlement writes
  the ledger**. Settlement ≠ payment: paying cash is a later, separate event.

## Who uses it

| User | What they do | Where |
|---|---|---|
| Owner / super-admin | everything; BOD dashboard (`/bod/`), user & access admin, voids, overrides | desktop |
| Manager | run production: Addas, stages, worker assignment, settlements, payroll, costing | desktop + tablet |
| Worker | report own work, see own earnings ladder (`/expense/my/`) | **phone-first** (a standing rule: worker UI is designed for cheap Android phones) |
| Listing team | storefront catalog (`/storefront/`) | desktop |

> **💡 Note for readers:** this handbook teaches in **English + Hinglish**
> deliberately (owner preference; the codebase's own comments follow the same
> tradition — see `config/config/settings/base.py`). The Hinglish boxes are
> the "samjhao jaise junior ko samjhate hain" layer; the English text is the
> precise reference layer.

## The five design decisions that explain everything else

Full reasoning in the [ARCHITECTURE_GUIDE](ARCHITECTURE_GUIDE.md); the short
version:

1. **Services own all writes.** Views parse input and call one service
   function; no business logic in views, **no Django signals** (zero
   receivers exist). Multi-row writes live in `config/<app>/services/`.
2. **One writer per money/audit table.** `WorkerLedgerEntry` has exactly one
   writing function in the whole codebase. So do the history and audit
   tables. This is enforced by tests and was re-verified at release
   certification — it is why the money numbers can be trusted.
3. **Settlement is the only money boundary** (ADR-0007 "era-B"). Production
   activity never books earnings directly; it produces *expected* figures.
   The ledger is append-only: mistakes are reversed with new rows, never
   edited.
4. **Three-concept RBAC:** Roles (who you are) × Skills (which production
   stages you may touch) × SidebarItemRule (which menu items — and their
   URLs, enforced together by middleware — you can reach).
5. **Honest numbers over convenient numbers** (ADR-0009). A consumed cloth
   roll without a purchase price makes the cost figure *incomplete and
   flagged*, never a fake ₹0. Every derived figure is reconstructable from
   raw tables; snapshots are frozen at business boundaries and immutable.

## The apps (13)

| App | Owns |
|---|---|
| `core` | shared abstract models (`TimeStampedModel`, `ActiveManager`); no tables |
| `accounts` | users, roles, auth hardening (Argon2, rate-limits, lockout) |
| `inventory` | dashboards, sidebar/access administration, tracking views, exports |
| `raw_materials` | cloth rolls, suppliers, master data, purchases |
| `production` | Addas, workflows/stages, cutting, allocation, costing, worker tasks |
| `tracking` | barcodes (range-based) + append-only history tables |
| `expense` | **all money**: ledger, settlements, advances, payroll, factory expenses, monthly-expense engine, material-spend |
| `machines` | physical machines + operator possession windows |
| `storefront` | public homepage + listing-team catalog (walled from production by ADR-0008) |
| `bod` | owner dashboard — a read-only *window*, never an engine (no models, no writes) |
| `patterns_ai` | pattern photo → geometry → marker layout tool (phases 1–3 shipped) |
| `devseed` | **dev-only** (not installed in production): deterministic world seeder |
| `verification` | read-only verification engine; `verify_production` is the post-deploy gate |

## Certification summary (why you can trust the state you inherited)

v1.0 shipped through a formal **Release Certification Program** (RCP-0..9,
2026-07-18/19 — full evidence: [../RELEASE_CERTIFICATION_LOG.md](../RELEASE_CERTIFICATION_LOG.md)):

- **Architecture** 7/7 · **Business** 40/40 features · **Security** 7/7
  (escalation attempts all walled) · **Financial** 9/9 (ledger ≡ settlement ≡
  items ≡ snapshots, byte-exact) · **Data** 9/9 (88 DB constraints live,
  append-only proven) · **Testing** 8/8 (battery **1,878/1,878**) ·
  **Documentation** 9/9 · **Deployment** 8/9 (monitoring gap accepted
  temporarily — see [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md)).
- Final verdict: **GO WITH ACCEPTED RISKS**; Release Certificate at log §9.7.

## Release status

| Field | Value |
|---|---|
| Version | **ERP v1.0 (Manufacturing V1)** |
| Release tag | `erp-v1.0.0` = commit `90c1f2f3` (2026-07-19), pushed to origin |
| Branch | `new_flask_app` (historical name; this IS the mainline) |
| Deployed | not yet — awaiting owner-provisioned VPS; the runbook is ready ([DEPLOYMENT_GUIDE](DEPLOYMENT_GUIDE.md)) |
| Test baseline | 1,878/1,878 (sequential fresh-DB — see DEVELOPER_GUIDE for the law) |

## Where the deep documentation lives

This handbook is the *entry point*, not the whole truth. The living estate:

- [../../CLAUDE.md](../../CLAUDE.md) — working rules + lazy-load doc map (read its rules before editing anything)
- [../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md) — business flow → architecture → database → code
- [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) — index of every active document
- [../adr/](../adr/) — the 11 binding architecture decisions
- [../PRODUCT_DESIGN_DOCUMENT.md](../PRODUCT_DESIGN_DOCUMENT.md) — frozen product truth (changes only via its amendment register)
- per-app `config/<app>/README.md` + `docs/apps/<app>/GUIDE.md` — all 13 apps have both
