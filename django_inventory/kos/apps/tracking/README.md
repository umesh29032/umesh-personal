---
id: app-tracking
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "What does the tracking app own — and why does it have models and services but NO views or URLs of its own?"
related: [app-inventory, feature-machines, pattern-append-only-ledger]
---

# tracking — the complete app map (a pure DATA app)

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*

## Mental Model — read this before anything

> **A notary's office.** It witnesses and records — piece identities and
> every domain's history — but it runs no counter of its own. You never
> "visit" the notary (no URLs here); other offices (inventory's /tracking/
> surface) bring people to its records. Its two seals: identity (barcodes)
> and memory (history timelines). *(Gawah + munshi — dukaan nahi.)*

## Common Misconceptions

- **"tracking has no UI, so it's minor."** It holds TWO system-critical
  monopolies: piece identity (permanent, ADR-0010) and the SOLE history
  writer (`history_service` — every timeline event in the system).
- **"The /tracking/ pages live here."** They moved to inventory (P4.2 D1)
  so THIS app imports no production — `views/` here is deliberately EMPTY
  (only `__pycache__` — the removal's receipt). Learn from absence.
- **"Scan rows exist for every piece."** Lazy: `BatchBarcode` materializes
  on FIRST scan; ranges (`BarcodeBatch`) are the stored truth.
- **"History rows can be fixed."** Append-only — a wrong event is followed
  by its correcting event, never edited.

## Real Engineering Questions

**PM: "Add 'returned' as a piece status."**
Chain: `BatchBarcode` FSM (pending→packed→dispatched) → `mark_status`
guards in `barcode_service` → which surfaces render states (inventory
§12–13) → history event for the transition → tests
(`test_barcode_service`). Schema change? No — status choices + FSM edges +
pins.

**PM: "Why does the Adda timeline show an event I can't find in any table?"**
Timelines ARE the table — `AddaHistory` rows via `log_adda` (sole writer);
find the WRITER (grep callers of log_adda), not a hidden table.

## Reading Strategy

- **Beginner:** Mental Model → [models.md](models.md) (identity + memory) →
  inventory's [/tracking/ surface](../inventory/urls.md).
- **Senior:** [services.md](services.md) (the two monopolies) → the P4.2
  boundary story in [urls.md](urls.md) → [pattern: append-only](../../concepts/patterns/append-only-ledger.md).

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Change scan behavior/validation | [services.md](services.md) `barcode_service` (`parse_value`/`resolve_value`/`mark_status`) |
| Add a history event type | [services.md](services.md) `history_service` — the sole writer's three verbs |
| Piece status lifecycle | [models.md](models.md) `BatchBarcode` FSM |
| The SCREENS for all this | NOT here → [inventory §§8–20](../inventory/urls.md) |
| Exports | [pattern: tracked-export](../../concepts/patterns/tracked-export.md) |

## What this app owns

Piece identity (`BarcodeBatch` ranges + lazy `BatchBarcode` states +
`BarcodeExportBatch` manifests) · **ALL history timelines** (`ClothRollHistory`,
`AddaHistory`, `ProductHistory`) via the system's sole history writer ·
the QR/parse/resolve toolkit.

## What it does NOT own

Any URL or view (inventory hosts the surface — P4.2) · barcode GENERATION
(production's barcode-gen stage creates ranges) · print sheets (inventory).

## The census

- **URLs/Views: 0 by design** (`views/` = empty husk; the boundary receipt)
- **Models:** 6 in `config/tracking/models.py` (410 lines) — [models.md](models.md)
- **Services:** 2 (`barcode_service.py` 176 · `history_service.py` 48 — read both whole)
- **Tests:** `test_barcode_service` · `test_barcode_export` · `test_dashboard_audit`

## The laws to carry in

1. **history_service is the ONLY history writer** (ADR-0002) — domain
   services call `log_roll`/`log_adda`/`log_product`; views never.
2. **Printed payloads are PERMANENT** (ADR-0010 §3) — identity never reused.
3. Import direction: tracking imports NOTHING domain-heavy; everyone
   imports tracking's services.

## Engineering Checklist — pre-flight

- [ ] Adding a surface? It goes in INVENTORY (P4.2 boundary), calling services here
- [ ] New history event → through the sole writer, in the SAME transaction as the change
- [ ] Status changes → FSM-guarded in `mark_status`, never raw field writes
- [ ] Anything touching printed ranges → ADR-0010 read FIRST
- [ ] kos-sync: this app + inventory's surface pages together

## Change Impact — touching this app affects

Every domain's timeline (all apps log here) · scan/export surfaces
(inventory) · piece-identity permanence (dispatch flows, future
traceability) · certification history-isolation guarantees (wall #4 strips
read THESE rows).

## Learning Graph

**Before:** [production Part 4](../production/urls-cutting-barcode.md)
(where identity is born). **After:** [inventory's surface](../inventory/urls.md)
→ [pattern: audit-trail](../../concepts/patterns/audit-trail.md).
