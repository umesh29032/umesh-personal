---
id: docs-adr-0010-growth-and-identity-policy
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-0010 — Growth & identity policy locks (multi-factory, references, barcode, rework)

Status: **ACCEPTED** (owner, 2026-06-11 — C-1 pre-deploy hardening).
Source: docs/archive/audits/ARCH_AUDIT_FOUNDATION_2026_06_11.md. Pure policy — zero schema
today; each lock converts a potential rewrite into a bounded future migration.

## Decision 1 — References are globally unique, forever

Every business reference and sequence (Adda codes, `ADST-XXXX`, `SETL-XXXX`,
roll IDs `CR-XXXXXX`, barcode sequences) is **one global namespace**. A second
factory SHARES the same sequences — it never restarts at ADST-0001 or gets a
prefixed parallel series. Rationale: two ledgers with colliding references can
never be merged; globally-unique references make any future consolidation,
audit, or site-scoping a filter, not a renumbering.

## Decision 2 — Multi-factory = one database + a site dimension. Never a fork.

If factory #2 arrives, it is implemented as a `site` dimension (FK on Adda,
scoped queues/dashboards) inside the SAME PostgreSQL database — **never as a
second deployment**. A forked deployment splits `WorkerLedgerEntry` (the
financial crown jewel) into two unmergeable ledgers. Workers/roles/skills stay
global (one User table — people move between sites). Nothing is built now.

## Decision 3 — Barcode identity is permanent

Printed barcode payloads are **physical history** — the one thing no migration
can rewrite. Piece identity = `(adda, seq)` resolved through `BarcodeBatch`
ranges. Any future Piece/ScanEvent model (Barcode/Traceability review, TM-2)
must be **born FROM the existing ranges** — materializing pieces for already-
printed sequences — never minting a new numbering scheme. Reprints reuse the
original payload.

## Decision 4 — Rework is case-scoped; first-pass production truth is never diluted

`WorkerStageContribution` rows under a worker's first task on a stage = the
permanent FIRST-PASS production truth that yield, productivity, missing-piece,
and settlement math all read. The future Alter/Rework module carries its OWN
work records inside `AlterCase` — rework never inserts additional WST/WSC
rows into the original stage record. The existing partial-unique constraint
`(stage_record, worker) WHERE status != cancelled` is intentional and STAYS.
Rework pay (if any) flows through additional settlements reading case records
via the §11.10 variance/earning seam.

## Decision 5 — Commerce boundary enforcement (restates ADR-0008 in schema terms)

Production models never grow price/revenue fields. Commerce references
manufacturing identity ONLY via the future G6 SKU/variant entity — never raw
FKs into production tables, and never Order→Adda (the locked route is through
G5 finished-goods inventory).

## Consequences

- Factory #2, barcode module, Alter module, and commerce each open with their
  constraint already decided — design starts from these locks, not toward them.
- Anyone proposing a second deployment, a new numbering scheme, rework rows in
  WSC, or a price field on Product is contradicting an accepted ADR, not making
  a fresh choice.
