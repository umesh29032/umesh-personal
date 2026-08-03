---
id: app-tracking-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "tracking's two service monopolies — the history pen and the barcode toolkit: verbs, callers, guards."
related: [app-tracking, concept-single-writer]
---

# tracking — service knowledge (2 files, read both whole)

> 📂 [tracking app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`tracking` app ka kaam: **history aur barcode** — kya hua, kab hua, kisne kiya.)*

## `history_service.py` (48 lines) — THE history pen 🔒

**Sole writer of all three `*History` tables** (ADR-0002; CLAUDE.md rule 5).
Three verbs: `log_roll(roll, change_type, actor, field_name…, note)` ·
`log_adda(adda, change_type, actor, stage_from/to, roll, note, metadata,
stage_record)` · `log_product(product, change_type, actor, field diffs)`.
**Callers:** domain services ONLY (settlement finalize logs here; stage
completes log here; roll ops log here) — inside the CALLER's transaction,
so a rolled-back event never leaves a ghost timeline row.
**Failure modes:** none designed — logging never blocks the business write
(keep it that way; validation lives in the caller).
Path: `config/tracking/services/history_service.py`.

## `barcode_service.py` (176 lines) — the identity toolkit

| Verb | Job |
|---|---|
| `parse_value(value)` | string → (adda_code, seq) or None — THE input edge for scans (certification task 3's home: malformed values die HERE, cleanly) |
| `resolve_value(value)` | parsed → (BarcodeBatch, seq) — range membership check |
| `get_or_create_piece(batch, seq)` | lazy `BatchBarcode` materialization |
| `mark_status(user, value, status)` | the FSM transition — atomic, guarded (illegal jumps refuse), history event |
| `qr_data_uri(…)` | QR rendering for print sheets |

**Callers:** inventory's tracking views (scan/status/print) + exports.
**Failure modes = designed refusals:** unparseable value → None (surface
renders not-found, never 500) · unknown range · illegal FSM jump.
Path: `config/tracking/services/barcode_service.py` · tests:
`config/tracking/tests/test_barcode_service.py`.

## Adding/changing here — the checklist

New timeline event → the pen's verbs, same transaction as the change ·
scan validation → `parse_value` (one edge, all surfaces inherit) · status
lifecycle → `mark_status` FSM only · anything printed-range-adjacent →
ADR-0010 first · kos-sync: this file + inventory surface pages.

## Required Knowledge (this page)

- [ ] Single-writer discipline → [single-writer](../../concepts/architecture/single-writer.md)
- [ ] FSM guards → [stage-tracking §DSA](../../features/stage-tracking.md)

## Learning Graph

**Before:** [models.md](models.md). **After:** [inventory §§12–13](../inventory/urls.md)
(the scan surface) → open both service files — 224 lines total, the
cheapest complete-app read in the repo.
