---
id: tracking-architecture-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# TRACKING ARCHITECTURE REVIEW — first principles, real factory
(2026-07-11 · Module 8 opening review · REVIEW ONLY, no code ·
method: full surface census (inventory/tracking_urls: 12 endpoints) +
scan/status code read + a LIVE full-lifecycle reconstruction of
LOWER-002 executed against the system)

# VERDICT: **No architectural gap. Module 8 proceeds DIRECTLY to
browser verification — no TRACKING_IMPLEMENTATION_READINESS needed.**
Tracking is already the read-side of the Identity Law: it stores
biography and memory, derives everything else, and consumed the
Cutting Streams + append changes without a single modification —
the strongest evidence the architecture is right. Three
simplification recommendations (UI-only, no architecture) and two
honest notes are listed for the verification pass.

---

## 1 · Purpose of Tracking
The factory's MEMORY: (a) the identity registry (batch ranges —
written by generation, read here), (b) each piece's BIOGRAPHY (lazy
scan rows: statuses, last-scan stamps), (c) the append-only HISTORY of
everything that happened (AddaHistory / RollHistory / ProductHistory).
Tracking never decides, never blocks, never writes production truth —
it remembers, so every other module can be lean.

## 2 · Who uses it (role by role, verified against gates)
- **Manager / Supervisor**: Barcode Dashboard, per-Adda barcode list,
  exports, Adda/Roll history — all `ProductionRoleMixin`+sidebar-gated
  management surfaces.
- **Production staff** (incl. skilled workers): the SCAN endpoint —
  correctly gated to PRODUCTION_ROLES because a scan STAMPS audit
  fields (last_scanned_by/at); office roles are refused.
- **Quality**: consumes statuses; damage itself is recorded on the
  production report (gam fields) — the correct split (M7 note).
- **Dispatch**: `packed`/`dispatched` statuses + per-size counts.
- **Workers**: NO tracking screens — correct. Workers report through
  stage flows; tracking is memory, not work.
- **Owner/audit**: the history timelines.

## 3 · Decisions made from Tracking
Dispatch readiness (packed counts vs order) · loss investigation
(`missing` biographies + last-scan trail) · dispute resolution (who
completed/voided/corrected what, when — the event trail) · recut
justification (the damage evidence chain). None of these WRITE
production truth from tracking — decisions route back through the
owning modules. Correct.

## 4–5 · Operational vs historical · live vs derived
- **Operational + live**: piece statuses and batch ranges — they are
  rows, instantly consistent; nothing cached.
- **Historical**: the `*History` tables — append-only, single writer
  (`history_service`), never edited.
- **Derived at read**: every rollup — dashboard aggregates, per-Adda
  totals, lifecycle reconstruction, "reports affected". Nothing
  derived is persisted. Already exactly the law.

## 6 · Screen census
Exists (12 endpoints): dashboard · per-Adda barcode list · print sheet
(A4 standalone) · scan detail · Adda history · Roll history · export
list + CSV/XLSX/PDF triggers + re-download · legacy dashboard CSV.
**Missing: nothing a real workflow demands today.** (A piece-search
box "type a code, jump to its biography" is the one convenience the
floor may someday ask for — the scan URL already IS that; not built,
noted only.)
**Redundant (simplification candidate №1):** the dashboard's legacy
`barcode-export` CSV duplicates the exports family — fold the button
into the export flow when touched next; zero architecture.

## 7 · Identity Law compliance
Every action maps: scan = write one biography stamp (never identity) ·
print/export = reproduce labels for existing names (idempotent
manifests) · statuses = biography · history = memory. Nothing renames,
renumbers, reuses, or encodes meaning. Fully compliant.

## 8 · Genericity
No product names, no workflow assumptions — values are `{code}-{seq}`,
ranges are dimension rows, history is event-typed. A future garment
needs zero tracking changes. Compliant.

## 9 · Cutting Streams consumption — the decisive test
Tracking absorbed the entire streams+append redesign with **zero
tracking-code changes**: appended ranges are just more batch rows
(dashboard/list/print/export pick them up automatically — verified:
`81–82 S Red` lists beside `1–32`/`33–80`) · late lanes and recuts
surface through the `barcodes_generated` event's lane metadata
(*"appended: 2 — body (lane 2) (Recut — 2 pieces damaged at Side Seam
Close)"*) · statuses work identically on appended pieces
(`LOWER-002-0081` → packed, lazy row 0→1). A read-side that survives a
write-side redesign untouched is proof its boundary was drawn right.

## 10 · The LOWER-002 reconstruction (executed live)
From the system alone, no human memory: **lanes** (derived body ·
declared "body lane 2 — Recut, 2 pieces damaged at Side Seam Close",
actor + timestamp) → **lane truth** (each trio record with completer +
its OWN frozen cost — including the recut lane's honest ₹4) →
**identities** (1–32 S · 33–80 M · appended 81–82 S) → **biography**
(0081 packed) → **event census** (created 1 · workers 9 · roll 1 ·
cost-frozen 7 · advanced 7 · corrected 4 · voided 2 · reopened 1 ·
bundles 2 · barcodes 2). The complete story of a real production order,
reconstructable forever. **Q10 = YES.**

## Honest notes (not gaps, recorded so nothing hides)
1. `stream_added`/`stream_cancelled` history events have no writer yet —
   they land WITH the deferred Add-lane button (lifecycle §10). The
   lane ROW itself already carries actor/reason/time, so reconstruction
   is complete without them.
2. `BatchBarcode.Status` = pending/packed/dispatched/missing — no
   `damaged`: damage is a PRODUCTION observation (gam fields on
   reports), not a biography status. Correct split; dispatch never
   ships what production recorded as damaged because pools already
   excluded it.

## Simplification recommendations (UI-only; for the verification pass
or a later polish — NO architecture)
1. Fold the dashboard's legacy CSV button into the exports family.
2. **Scan detail = the floor's phone moment** — verify it renders
   thumb-first (value huge, status huge, one-tap status buttons); if
   it's desktop-shaped, simplify within the existing template.
3. Barcode list on phone: ranges as cards, not a wide table
   (data-label rule) — verify, adjust only if it fails the phone test.

**Module 8 proceeds directly to browser verification of the existing
architecture. STOP — review only, no code.**
