# `tracking` app — Identity & History (the append-only memory)

> Dual-register guide. Canonical: [docs/production/TRACKING.md](../../docs/production/TRACKING.md) ·
> [ADR-0004](../../docs/adr/0004-tracking-is-append-only-history-primitive.md) ·
> barcode permanence: [ADR-0010 §3](../../docs/adr/0010-growth-and-identity-policy.md).

## Purpose & business responsibility

Do kaam, dono "yaad rakhna":
1. **History** — har important cheez ka timeline (roll, Adda, product,
   settlement events) — append-only, kabhi edit nahi.
2. **Barcode identity** — har piece ka number (`(adda, seq)` ranges).

R1 boundary (locked): **tracking owns identity + scan history; production
owns quantity truth.** Tracking imports NO production code (string FKs only).

## Models

| Model | Business | DB meaning / example |
|---|---|---|
| `AddaHistory` | one event in an Adda's life (stage moved, reopened, SETTLEMENT_FINALIZED/REVERSED/SUPERSEDED…) | append-only; `metadata` JSONB for event details. Row: `adda=3-PATTI-001, change_type=settlement_finalized, actor=manager1, metadata={'reference':'ADST-0003'}` |
| `ClothRollHistory` | roll movements/edits (incl. cost_per_kg corrections) | append-only |
| `ProductHistory` | product master changes | append-only |
| `BarcodeBatch` | ONE contiguous seq range per (adda,color,size) | `3-PATTI-001 Red Size-1 → seq 1..60` — **piece identity = (adda, seq), derivable without a Piece table; printed payloads are PERMANENT (ADR-0010 §3)** |
| `BatchBarcode` / `BarcodeExportBatch` | rendered/export bookkeeping | see docs/tracking/EXPORTS.md |

## How data flows through this app

```
any meaningful change in production/raw_materials/expense
        │  (the writer service calls…)
        ▼
 history_service.log_adda / log_roll / log_product   ← SOLE writer (gate: rule 5)
        ▼
 *History rows (INSERT only) ──▶ timeline accordions + future Adda-360 (G4)

barcode_generation stage (archetype E)
        ▼
 barcode_service → BarcodeBatch ranges ──▶ QR print sheets
```

**What breaks if bypassed:** history written ad-hoc loses the "who/when/why"
discipline (and signals are banned — ADR-0001, so there is no magic catcher);
a second barcode numbering scheme would orphan every physically printed
garment — the one thing no migration can fix.

## Views: barcode dashboard, export flows, print sheet (standalone A4 HTML).

## Common mistakes

1. Never write `*History` outside `history_service`.
2. Never re-number barcodes; future Piece/ScanEvent models must be born FROM
   existing ranges (TM-2 / Barcode review).
3. Don't put production logic here — string-FK boundary is deliberate.

## Django Learning Notes

- **String FKs** (`'production.Adda'`): dependency direction control — the
  app below imports nothing from above (import-linter contract material).
- **JSONField metadata**: display-grade detail without schema churn; promote
  to columns only if filtering is ever needed.
- **Append-only pattern**: no `updated_at` semantics on history — a fix is a
  NEW row that says what changed.

## Real factory example

3-PATTI-001 ki timeline kholo: started → layering complete → cutting complete
(by utest) → barcode batch 1..105 → SETTLEMENT_FINALIZED ADST-0001 →
SETTLEMENT_SUPERSEDED → SETTLEMENT_FINALIZED ADST-0003. Har garment pe jo QR
laga hai (`3-PATTI-001 · 37`) wo hamesha ke liye usi piece ka naam hai.
