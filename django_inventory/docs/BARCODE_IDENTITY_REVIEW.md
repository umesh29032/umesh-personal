---
id: barcode-identity-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# BARCODE IDENTITY REVIEW — what a late-lane piece IS
(2026-07-11 · the permanent-identity gate · REVIEW ONLY, no code ·
answers the owner's A/B/C question from the complete piece lifecycle,
walked consumer-by-consumer against the implemented system)

# VERDICT: **The append-generation proposal STANDS UNCHANGED** — with
one doctrine made explicit (words, not schema): **identity is
meaning-blind; MEANING lives on the lane.** The A/B/C question is
real, but it is answered at the LANE grain, where the frozen lifecycle
already answers it — never at the identity grain.

---

## 1 · The piece lifecycle (when is a piece "real"?)

Three distinct moments, all already in the system:

1. **A piece becomes REAL at its lane's cutting completion** — the
   frozen breakdown row (APSCPB) is its birth certificate. Before
   that there is only fabric.
2. **It gets its NAME at barcode generation** — `{ADDA}-{SEQ}`,
   issued once, never changed, never reused.
3. **Its BIOGRAPHY begins on first scan** — the lazy `BatchBarcode`
   row; statuses (damaged, hold, …) are life events appended to it.

Birth (ERP cutting truth), name (tracking identity), biography
(tracking status). Three owners, no overlap — this is why the
architecture survives the hard questions below.

## 2 · The central question: A, B, or C?

**C — mixed — and the factory already told us where the distinction
lives.** The frozen lifecycle (CUTTING_STREAM_LIFECYCLE §3) makes a
REASON mandatory on every late lane, with 'Recut' and 'Additional
production' among the suggested picks. That is the operator's choice,
captured at exactly the right moment (opening the lane) and exactly
the right grain (the lane). Nothing new is needed at barcode time —
**barcode generation stays meaning-blind**, and that is a feature:

**Why meaning must NOT live on the identity: cut pieces are FUNGIBLE
within (pattern, size, color).** When 12 size-L panels fail checking
and 12 replacements are cut, no human on the floor pairs replacement
piece #61 with dead piece #37 — they are interchangeable cloth. A
piece-level "replaces" pointer would be data the factory cannot
truthfully supply, i.e. false precision — the exact thing our honesty
laws exist to prevent. Provenance the floor CAN truthfully state is:
"these 12 exist because lane 2 was opened for reason X" — and the
lane row already states it.

## 3 · Identity laws (frozen by this review)

- **One physical piece never changes identity.** Corrections are DB
  facts (statuses, verified counts) — the printed name stays.
- **Identity is never reused, never renumbered, never inherited.** A
  replacement piece gets a NEW identity; the damaged piece's identity
  is not "freed".
- **A destroyed piece's barcode is retired by STATUS, not deletion.**
  The `BatchBarcode` row with its terminal status IS the death
  certificate; the physical sticker burns with the piece; history
  never lies. There is no bulk-retirement mechanism to build — the 12
  failures were already individually marked damaged by the checker
  (that marking is what TRIGGERED the recut).
- **Old and new both exist in history, forever** — 12 damaged
  identities with statuses + 12 new identities in an appended batch +
  the lane's reason + the `stream_added` / `barcodes_generated` audit
  events. The full story, derivable, no schema.

## 4 · Consumer-by-consumer challenge (as ordered)

| Consumer | Does it care that a piece is replacement vs additional? | Verdict |
|---|---|---|
| **Tracking / QC** | Needs: what exists now + statuses + why extras appeared. Lane reason + statuses answer completely; piece-pairing adds nothing scannable | counts + lane reason ✓ |
| **Dispatch** | Ships N good garments per size/color — reads counts and statuses. It does not (and should not) care that #61 replaced #37. Additional-production lanes legitimately raise totals; dispatch reads the same numbers either way | no identity need ✓ |
| **Costing** | Recut lane freezes its OWN stage costs (ADR-0009 price-at-time) — the true cost of the recut, visible per lane. The original pieces' frozen cost was real work and STAYS (append-only money truth). "What did recuts cost us?" = derive over lanes with reason=recut — data already exists | per-lane freeze ✓ |
| **Settlement / earnings** | The workers who cut the originals earned for work that HAPPENED — never clawed back (append-only history; D2: good pays, damaged is an observation). Recut workers earn on the recut lane's own records. Identity plays no role in money — as it must be (settlement-only money law) | untouched ✓ |
| **Inventory** | Live counts = identities minus terminal statuses. Destroyed pieces fall out via status. No reuse means no double-count ever | statuses ✓ |
| **Auditing** | Wants BOTH sides + the why: damaged identities (statuses, actor, time) · new identities (appended batch, lane) · reason (lane row) · events (history). Complete without any new structure | derivable ✓ |
| **Future QC analytics** | "Damage rate by stage/fabric/lane" = statuses × lane facts — derive-at-read, later, zero schema | deferred ✓ |

No consumer, walked honestly, needs piece-level replacement semantics.
Every consumer's question is answered by: **identities (append-only) +
statuses (biography) + lane reason (meaning) + frozen lane costs
(money)** — all of which exist.

## 5 · Should the operator choose "replacement vs additional"?

**Yes — and the frozen design already makes them.** The mandatory lane
reason IS that choice, made once, at lane opening, by management. It
must NOT be asked again at barcode generation (a second asking invites
contradiction, and generation is identity-issuing, not
meaning-assigning). Whether reports later TREAT the two reasons
differently (e.g. exclude recuts from output KPIs) is a business
concern for the Reports module (campaign module 12) — a derive-at-read
decision over data we are already capturing. Correctly deferred.

## 6 · Effect on the append-generation readiness

**Unchanged**, plus one refinement folded in (audit wording, no
schema): the append run's `barcodes_generated` history event carries
the lane label + reason in metadata, so the audit trail reads "12
barcodes appended — panel fabric lane 2 (recut: failed checking)"
without any join archaeology.

Rejected (named so they stay rejected): piece-level `replaces` FK
(fungibility — false precision) · identity retirement/reuse pools ·
meaning encoded in values or sequence gaps · a second
replacement/additional prompt at generation time.

**STOP — review only. Identity rules above are final pending your
approval; the readiness then proceeds exactly as written.**
