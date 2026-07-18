# P1 ENGINEERING REVIEW — fresh hostile eyes (2026-07-07)

**Method:** full main-thread re-read of views/services/models/urls with a
hostile lens + live tamper probes on the running server + one independent
hostile reviewer sub-agent (supplemental per the audit-honesty rule; every
sub-agent finding re-verified main-thread before a verdict below).
**No code was changed — verification-only order.**

## Verdict

**SOUND. Freeze-worthy.** One new LOW-severity robustness defect found
(500 on tampered ids); zero critical, zero money-risk, zero
architecture violations. Full findings + triage below.

## 1. Architecture

- **Single-writer discipline holds:** every knowledge write flows through
  `marker_service` / `marker_feedback_service` / `capture_service`; the
  I-1 repo-wide source-scan test enforces it structurally. VERIFIED.
- **Views are parse→gate→delegate everywhere** — re-read of all 10
  endpoints found zero business rules in views; error paths re-render
  service messages verbatim. VERIFIED.
- **Read models write nothing:** `marker_query_service` SELECT-only
  (test-captured); board/detail/summary share ONE derivation path
  (`derive_metrics`, METRICS_VERSION=1) — divergence structurally
  impossible. VERIFIED.
- **Boundary:** no manufacturing model is written by patterns_ai (reads
  Product/Adda only); production never imports patterns_ai (purity wall +
  import-linter). VERIFIED.
- Sub-agent claimed a 🔴 IDOR on `captures/<pk>/thumb/` ("assets from
  products they're not entitled to"). **Rejected on premise:** this ERP has
  no per-product entitlement tier — management role = full library
  visibility by design (the list page already shows every product's
  markers). Kept as a one-line note: the thumb endpoint serves any
  asset's rendition to any management user, including retired/corrupt
  assets — same trust tier as every other library page. ACCEPTED DESIGN.

## 2. Maintainability

- Module map is small and boring (good): 9 models across 6 files,
  6 services with docstring contracts, one form module, one views module.
- Versions everywhere (`schema_version`, METRICS_VERSION,
  TRANSITIONS_VERSION) — future changes are additive by constitution.
- **Cosmetic:** dead `big = None` in `get_product_yield_board` else-branch
  (leftover; 1-line removal next code block).
- Deferred in-method imports in views are a deliberate style to keep the
  module surface small — consistent, fine.

## 3. Performance

- **Yield board = O(N markers × ~4 queries), detail = 1 query per usage
  for outcomes** (no `select_related('outcome')` in
  `get_marker_usage_history`), biography composes 3 selects. All are the
  F6 derive-at-read shape, pinned by the perf-sanity test (≤ 4 + 4·N)
  so growth is VISIBLE, not silent. At factory volumes (markers per
  product ≈ a handful) this is right; the documented future slot is a
  derived-class cache (ADR-G semantics: regenerable, deletable), NOT built.
- Thumbnails: lazy-built once, then served from disk; `loading="lazy"`.
- Library list: one `select_related` query + count (pagination). Fine.
- Lineage walk is 1 query per ancestor — chains are human-length;
  cycles structurally impossible (supersedes set only at creation).

## 4. Security

- **NEW FINDING (LOW): 500 on tampered non-integer ids** — verified live:
  `/patterns/yield/?product=abc` → `ValueError: Field 'id' expected a
  number` (Django's `get_object_or_404` does not catch ValueError).
  Three sites: yield-board `product` GET, manual-create `product` POST,
  usage-create `adda` POST. The `<int:pk>` routes are converter-guarded
  (clean 404). Exposure: authenticated management users only; no data
  risk; ugly error page (generic 500 in prod). **Fix (next approved code
  block): coerce with try/int() → 404, one line per site.**
- Upload pipeline walls re-confirmed: magic-byte type decision, size caps,
  traversal-proof hash naming, per-product dedup — all test-enforced.
- Renditions-only media serving: `originals/` has zero URL surface;
  literal-substring test keeps it out of HTML.
- CSRF on all forms; all 10 URLs management-gated (403/302 re-proven in
  the regression pass); reasons stored verbatim, rendered escaped.
- No secrets, no raw SQL, no user-controlled paths anywhere in the app.

## 5. Scalability

- Facts tables are append-only and integer-based — they only grow, never
  rewrite; indexes from 2A cover the read paths (usage by marker, outcome
  by usage, events by marker).
- The derive-at-read ceiling is the ONLY scaling pressure point and it is
  pinned + has a designed escape hatch (derived cache). No summary tables,
  no jobs, no cache invalidation problem exists — the hardest class of
  bug was designed out.
- Media: O(total bytes) integrity sweep — becomes an off-hours cron at
  deploy (runbook line exists since 3A).

## 6. Concurrency (hostile probes, triaged)

- **Outcome one-per-usage:** service guard is check-then-act; the OneToOne
  UNIQUE backstops it — a race loser gets a raw IntegrityError 500, data
  stays correct. LOW (single-user factory), documented.
- **record_usage TOCTOU** (sub-agent 🟡, verified real but narrow): marker
  could be retired between the usability check and the usage INSERT — the
  row would record work that DID happen against a just-retired marker;
  facts remain true, `void_usage` is the correction path. No
  `select_for_update` needed at this trust/volume tier. ACCEPTED, documented.
- **store_capture duplicate race:** two identical simultaneous uploads —
  loser's file remains on disk as an orphan; the integrity sweep reports
  exactly this as WARN-with-context (N-7, designed). ACCEPTED.
- MRK- reference allocation is under advisory lock 5376 — no gap.

## 7. Technical debt register (complete, carried forward)

| # | Item | Severity | Home |
|---|---|---|---|
| 1 | 500 on non-integer id at 3 sites | LOW (fix next code block) | views.py |
| 2 | Dead `big = None` | cosmetic | marker_query_service |
| 3 | Outcome guard check-then-act (DB-backstopped) | LOW accepted | marker_feedback_service |
| 4 | record_usage TOCTOU (void = correction) | LOW accepted | marker_feedback_service |
| 5 | Detail/board N+1 shape | by-design F6, pinned | query service |
| 6 | Adda dropdown cap 50 | revisit at volume | usage view |
| 7 | `ratio_text` parser UX | temporary by design | forms.py |
| 8 | Broken-image icon for unreadable originals | cosmetic | marker_list |
| 9 | `update_outcome_facts` service-only (no UI) | by scope | — |

## 8. Future ADR candidates

1. **DB-level append-only hardening** (grants/triggers on
   `MarkerTransitionEvent` + `CaptureAsset`) — carried from 2C/3A, now
   also relevant to `MarkerUsage`.
2. **Derived-metrics cache class** — only if a product ever holds
   hundreds of markers; must keep ADR-G regenerable semantics.
3. **D2/D3 mini-ADRs** (piece grain detail · capture provenance/EXIF
   depth) — P2 entry items, see P2_READINESS_REPORT.

No other candidates. **Review complete — no redesign recommended.**
