# P1 — BLOCK 2B REPORT: Single-Writer Service Layer (2026-07-06)

**Status: ✅ BLOCK 2B COMPLETE — STOPPED. Block 2C will NOT start without
explicit owner approval.**

## Scope compliance
Exactly the two services + the I-4 quantization home. No views, no UI, no
uploads, no geometry, no generation. Every public method documents purpose /
invariants / allowed transitions / why-the-service-exists (module + method
docstrings).

## Service API summary

**`services/units.py` — the ONE quantization home (I-4):**
`to_int_mm` (facts = integer mm, HALF_UP) · `mm_to_m` (2dp) · `q2` (2dp) ·
`width_band` (floor(mm/10) — stamped only by marker_service).

**`services/marker_service.py` — single writer for `Marker`:**
- `create_marker(user, product, origin, usable_width_mm, …)` — MRK-000001
  references under **advisory lock 5376** (own domain, disjoint from 5374/5375);
  width_band stamped; D11 adda⇔temporary validated pre-DB with friendly
  errors; ratio normalized to `{schema_version:1, counts:{…}}`; strategy only
  for generated; **lineage validation** (same product, never a rejected
  target, callers' stale rows re-read); `supersedes=` flips the old marker to
  SUPERSEDED in the same transaction.
- `transition_marker(user, marker, to_status, reason='')` — the governed
  status machine (below); `select_for_update`; negative targets require a
  reason (F2, DB CHECK backs it); PROMOTED reachable only by adda_temporary.

**`services/marker_feedback_service.py` — single writer for usage/outcomes:**
- `record_usage(…)` — the human join-key act; marker must be USABLE
  (candidate/validated/promoted; refusal message carries the marker's own
  status_reason); temporary markers usable ONLY on their own Adda (D11).
- `void_usage(user, usage, reason)` — void-never-edit; reason mandatory.
- `record_outcome(…)` — explicit human act (N-6); one per usage; refused on
  voided usage; honest-NULL facts.
- `update_outcome_facts(…)` — **null→value ONLY**; a non-null fact never
  changes (correction = void + re-record).
- `derive_metrics(outcome)` — pure, `METRICS_VERSION = 1`, returns
  fabric_in_m / meters_per_garment / meters_per_100 / leftover_m;
  `utilization_pct = None` honestly until the geometry era; **persists
  nothing** (test-proven byte-identical row before/after).

## State-transition diagram (ADR-D, service-enforced + DB-checked)

```
                 ┌────────────► VALIDATED ──────► SUPERSEDED (terminal)
                 │                  │    ▲
 CANDIDATE ──────┤                  └────┼──────► RETIRED(reason) (terminal)
   │             │                       │
   │ (origin=adda_temporary ONLY, D11)   │
   ├────────────► PROMOTED ──────────────┘─────► SUPERSEDED | RETIRED(reason)
   │
   ├────────────► REJECTED(reason) (terminal)
   └────────────► RETIRED(reason)  (terminal)
 (creation with supersedes=X flips X → SUPERSEDED automatically)
```

## Public method list
`units`: to_int_mm · mm_to_m · q2 · width_band ·
`marker_service`: create_marker · transition_marker ·
`marker_feedback_service`: record_usage · void_usage · record_outcome ·
update_outcome_facts · derive_metrics (+ METRICS_VERSION const).

## Test summary — patterns_ai suite now 35 tests, all green
Happy paths (manual marker, usage, outcome, fills, derivations) · every
illegal transition incl. terminal-lock loops · duplicate-reference safety
(sequential uniqueness under the lock) · **promotion**: wrong-origin refusal +
temporary→promoted→validated ladder · rejection/retirement reason walls ·
append-only: facts never change, usage void-not-edit, double-void refused ·
lineage: cross-product refused, rejected-target refused, PROTECT proven ·
width_band stamping · quantization (HALF_UP edges) · derive-at-read: versioned,
honest-NULLs, **zero persistence** · **I-1 guard**: repo-wide source scan —
`.objects.create/get_or_create/update_or_create/bulk_create` on any knowledge
model outside `patterns_ai/services/` (tests/migrations exempt) fails the build.

## Validation
Full manufacturing suite serial ✅ · patterns_ai 35/35 ✅ ·
`makemigrations --check` clean ✅ (no schema drift — services only) ·
import-linter unchanged ✅.

## Findings
1. **Stale-instance robustness (real bug caught by tests):** services now
   re-read status/lineage state inside their transaction — callers holding
   stale rows can't bypass gates.
2. **Transition audit (who/when per transition) has no schema home** —
   status_reason exists, actor/timestamp of each transition is only logged.
   Already noted at 2A; formal fix = `MarkerTransitionEvent` (append-only) as
   a Block-2C candidate for owner decision.
3. Promotion's placement-pin confirmation gate is DOCUMENTED as deferred —
   placements don't exist yet; the origin gate + status machine hold D11's
   shape until then.
4. MRK reference generation deliberately local (no expense import — same-layer
   apps stay independent; same next_reference pattern, own lock 5376).

**Awaiting owner approval for Block 2C.**
