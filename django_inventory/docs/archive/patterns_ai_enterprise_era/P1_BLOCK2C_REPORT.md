# P1 — BLOCK 2C REPORT: Immutable Events + Marker Biography (2026-07-06)

**Status: ✅ BLOCK 2C COMPLETE — STOPPED. Block 3 will NOT start without
explicit owner approval.**

## Scope compliance
Exactly the four deliverables: `MarkerTransitionEvent` · biography read model ·
read-only query services · docs + tests. No generation, no CV, no geometry, no
uploads, no UI, no recommendations. The exactly-N model pin was consciously
moved 7→8; the I-1 single-writer guard now covers the event table too.

## 1. Event model (`patterns_ai.0002_markertransitionevent`)

Append-only, permanent history of every marker status change:
`marker` (PROTECT — history outlives intent) · `from_status` ('' for the
CREATION event) · `to_status` · `actor` (PROTECT) · timestamp · `reason`
(verbatim from the governed transition) · **`transition_version`**
(= `marker_service.TRANSITIONS_VERSION` at write time — rule-set changes never
make old events ambiguous) · **versioned `metadata` JSON** (creation carries
origin+width; supersede-flip carries `superseded_by` reference).

**Immutability = belt AND braces:** model-level `save()` refuses updates and
`delete()` refuses deletes (RuntimeError); creation happens only inside
`marker_service` (I-1 source-scan guard). Emission points: marker creation ·
every governed transition · the supersede-flip on the OLD marker. **Failed
transitions emit nothing** (test-proven).

## 2. Biography architecture (read model)

`marker_query_service` composes the lifecycle from the append-only sources —
transition events + usages (+voids) + outcomes — into ONE oldest-first
timeline: `created → validated/promoted → used → outcomes → superseded/
retired/rejected`, each entry carrying kind/actor/reason/metrics. Lineage
walker returns the full `supersedes` chain (backward), `superseded_by`
(forward), `benchmarked_against`, and `benchmark_children`. **Pure read:
proven SELECT-only via `CaptureQueriesContext`** — zero INSERT/UPDATE across
all five helpers. Derived numbers REUSE `derive_metrics` (one math home, one
METRICS_VERSION — no duplication).

## 3. Query API

`get_marker_biography(marker)` · `get_marker_lineage(marker)` ·
`get_marker_usage_history(marker)` · `get_marker_outcomes(marker)` (facts +
derived metrics) · `get_marker_summary(marker)` (status, active/voided usage
counts, outcome n, **avg meters/100 with honest n — None until n≥1**,
last_used_at).

## 4. Tests — patterns_ai suite now **47 tests, all green**

Events: exactly-one per creation/transition, no duplicates, supersede-flip on
the old marker with reference metadata, failed transitions emit nothing,
update/delete both refused. Biography: full-lifecycle ordering (oldest-first
asserted), promoted chain (∅→candidate→promoted→validated), rejected chain
with reason surfaced. Lineage: multi-hop supersedes walk, forward links,
benchmark relations. Summary: counts, voided exclusion, 67.50 average
calculation, honest-None at n=0. Read-only proof: SELECT-only capture.

## Validation
Full manufacturing suite serial ✅ · patterns_ai 47/47 ✅ ·
`makemigrations --check` clean ✅ · import-linter unchanged ✅ · docs updated
(app GUIDE rewritten to Block-2C state).

## Engineering review

1. **Technical debt:** queryset-level `.delete()`/`.update()` on the event
   table bypasses model guards (Django semantics). Unreachable through
   services and blocked-by-review via the I-1 guard, but a DB-level wall
   (revoke DELETE/UPDATE or a trigger) is the honest hardening —
   **future-ADR candidate, not implemented** (production-DB grants are a
   deploy-layer decision).
2. **Performance:** biography is O(events+usages+outcomes) per marker —
   fine at any realistic per-marker volume; `get_marker_summary` derives
   per-outcome at read (by design, F6). A cached summary column is a
   documented slot ONLY if a future list view measures pain (V3 F8 discipline).
3. **Security:** biography entries carry actor objects; when a UI renders
   them (Block 3+), display names only + management-gating apply (ADR-H §5) —
   noted for the UI block's checklist.
4. **Long-term maintenance:** both the transition RULES and the event SHAPE
   are versioned (`TRANSITIONS_VERSION`, metadata `schema_version`) —
   rule-set evolution is additive by construction; ordering uses insertion id
   (monotonic per marker), immune to clock skew.
5. **Future ADR instead of implementation:** event-table DB-grant/trigger
   hardening (above) · biography pagination/serialization contract when the
   UI needs it.

## Findings
None blocking. The 2A/2B transition-audit gap is now closed — who/when/why of
every marker decision is permanent, attributed knowledge.

**Awaiting owner approval for Block 3.**
