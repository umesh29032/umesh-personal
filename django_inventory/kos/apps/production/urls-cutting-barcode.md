---
id: app-production-urls-cutting-barcode
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Every Cutting and Barcode-Generation URL — the mint and the identity printer, action by action."
related: [app-production-urls]
---

# production URLs · Part 4 — Cutting (14) + Barcode-Gen (5)

> 📂 [URL index](urls.md) · [production app](README.md) · [LOS home](../../README.md)
> Handlers: `stages/cutting/service.py` · `stages/barcode_generation/…`.
> Skill-gated (`_ensure_cutting_skill`); completes management-checked.

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`production` app ka kaam: **factory floor** — Adda, stages, worker ka kaam, allocation. Project ka dil yahin hai.)*

## Cutting — where quantities are born

**Mental model:** the MINT ([cutting](../../features/cutting.md)). Bulk
metal in, coined currency out — and the mint's OUTPUT REGISTER (APSCPB) is
the only count the whole economy downstream trusts.

### `cutting/` — `cutting-complete` (legacy)
POST: the old single-submit form, kept for simple flows. **Why it survives:** working URLs are contracts (same lesson as the pattern redirects); the workspace below supersedes it for real flows.

### `cutting/workspace/` — `cutting-workspace`
GET → `CuttingWorkspaceView` (`views/stage_views.py`): breakups, bundles, suggestions, reconciliation — the mint's console. Read-only assembly.

### `cutting/start/` — `cutting-start`
POST: begin (per-stream aware — lanes cut independently until the JOIN).

### `cutting/breakup/save/` — `cutting-breakup-save` ⭐
POST: record per-(size, color, pattern) piece counts (`CuttingPieceBreakup`).
**Helper intelligence:** `get_suggested_breakup` pre-fills from the pattern layout; `layout_reconciliation` diffs claim-vs-layout so typos surface NOW, not downstream.
**Failure modes:** validation; reconciliation warnings are teachers, not blockers.
**Lesson:** catch data-entry error at the BIRTHPLACE — every later screen inherits this number.

### `cutting/breakup/<pk>/delete/` — `cutting-breakup-delete`
POST: remove a breakup row pre-complete. Correctable-until-consumed, again.

### `cutting/bundle/create/` — `cutting-bundle-create`
POST: create a per-size bundle header (PR8/9 two-step: header, then pieces).

### `cutting/bundle/<pk>/add-pieces/` — `cutting-bundle-add-pieces`
POST: multi-select CONSUME breakup rows into the bundle (PR10). **The invariant:** bundle items = the same pieces, physically grouped — itemization must reconcile against breakups (counts-mismatch playbook's bundle branch).

### `cutting/bundle/item/<pk>/delete/` — `cutting-bundle-item-delete` · `cutting/bundle/<pk>/delete/` — `cutting-bundle-delete`
POST pair: undo itemization / drop an empty header. Pre-complete lanes; PROTECT-style guards on consumed content.

### `cutting/bundle/item/<pk>/allocate/` — `cutting-item-allocate` · `cutting/allocation/<pk>/delete/` — `cutting-allocation-delete`
POST pair: assign bundle-item work to workers / undo (the era-A-adjacent cutting allocation lane).
**Careful (naming trap):** this is CUTTING's bundle-work allocation — NOT the piece-pool WSA ([allocation feature](../../features/allocation.md)) and NOT expense's legacy `allocation_service`. Three "allocation"s exist; this page is why the LOS documents every URL individually.

### `cutting/draft/` — `cutting-draft`
POST: save work-in-progress state. Simple, honest.

### `cutting/workspace/complete/` — `cutting-workspace-complete` ⭐⭐ THE MATERIALIZATION
POST → handler complete:
```
[@atomic] stream JOIN check (blocking lanes done?) → verify breakups/bundles
coherent → _materialize_breakdown → **APSCPB rows** (the single verified
per-(size,color) count) → ASR complete → timeline
```
**Why THE moment:** everything downstream — barcode ranges, the piece pool, paid-vs-produced reconciliation — consumes APSCPB and nothing else. Wrong here = wrong everywhere; hence the reconciliation helpers upstream.
**Failure modes:** blocking lane incomplete (JOIN — names it) · incoherent counts.
**DSA:** the fork-join barrier + the canonical aggregate at the merge point ([cutting §DSA](../../features/cutting.md)).
**Engineering Decision.** *Problem:* every downstream number needs ONE
trustworthy piece count. *Options:* (A) each consumer recounts from
breakups — N counters, N drifts; (B) trust the last reporter — anchored
claims; (C) one verified materialized snapshot (APSCPB) at the barrier,
everyone reads it. *Chosen:* C. *Trade-offs:* a write-once table to guard,
reopen complexity (refreeze). *Still today?* **Yes** — the 120-vs-105 leak
is exactly what (A)/(B) worlds produce.
**Evolution Timeline.** Originally: single-submit cutting form (the legacy
route above) → *problem:* real cutting is multi-lane, multi-day, bundled →
*refactor:* PR3–PR12 workspace (breakups→bundles→breakdown), then
CuttingStreams with the JOIN (2026-07 ratified: sequence IS the production
cycle) → *current:* the mint + APSCPB single source → *future:* piece-level
traceability rides the same identity (ADR-0010).

### `cutting/reopen/` — `cutting-reopen` 🔐
POST (admin): the heaviest reopen — downstream consumers (barcodes! pools! reports!) all walk the guard; expect the refusal to name barcode-gen or allocations. Printed barcodes make some ground PERMANENT (below).

---

## Barcode Generation — printing identity

**Mental model:** the PASSPORT OFFICE. The breakdown says who exists;
this stage issues each piece its permanent identity (adda, seq). And like
passports: **once printed, an identity is never reused or reassigned** —
ADR-0010 §3.

### `barcode-gen/` — `barcode-gen-workspace`
GET → `BarcodeGenWorkspaceView` (`views/barcode_gen_views.py`): preview ranges vs APSCPB. Read-only.

### `barcode-gen/start/` — `barcode-gen-start`
POST: begin. Simple.

### `barcode-gen/generate/` — `barcode-gen-generate` ⭐
POST → handler generate: APSCPB → `BarcodeBatch` RANGES per (adda, color, size) — ranges, not per-piece rows (storage win; per-piece `BatchBarcode` rows lazily appear on first SCAN, over in the tracking surface).
**Failure modes:** breakdown missing/stale → refused; regenerate guarded once printed.
**Misconception:** "generate creates stickers." It creates IDENTITY SPANS; printing + scanning are separate acts (print sheet lives on the /tracking/ surface — [inventory app](../inventory/urls.md)).

### `barcode-gen/complete/` — `barcode-gen-complete`
POST: close the stage; downstream ops (dispatch/scan flows) unlock.

### `barcode-gen/reopen/` — `barcode-gen-reopen` 🔐
POST (admin): guarded — **printed payloads are PERMANENT** (ADR-0010): reopen can extend/append ranges but the printed past is untouchable. The strongest immutability lesson outside the ledger.

## Learning Graph (this file)
**Before:** [urls-layering-pattern.md](urls-layering-pattern.md) (the verified lay these counts come from).
**After:** the [inventory app's /tracking/ surface](../inventory/urls.md) (scans, exports) → then [apps/expense](../expense/README.md) — pieces become pay.
