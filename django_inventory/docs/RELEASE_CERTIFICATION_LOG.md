---
id: docs-release-certification-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# Release Certification Program — Evidence Log (Campaign Phase 18A)

> Program of record: [RELEASE_CERTIFICATION_PROGRAM.md](RELEASE_CERTIFICATION_PROGRAM.md)
> (RATIFIED 2026-07-18 — binding wave structure RCP-0..RCP-9). Append-only; each wave
> appends its section; closed sections never rewritten. Severity taxonomy = program §4;
> evidence standard = program §5 + charter §3a.4.

## RCP-0 — Release Planning — ✅ COMPLETE 2026-07-18 (planning ONLY — zero certification executed, zero code, zero repairs)

**Gate:** Phase 18 CLOSED + owner authorization "PHASE 18A — RELEASE CERTIFICATION
PROGRAM" (defines the binding RCP-0..RCP-9 dimension structure; supersedes the
RC-0..RC-F sketch as structure; RC walk retained as the browser instrument — program
§3 mapping).

**Produced (the 7 ordered deliverables, all in the program doc):**
1. Release Certification Charter — §3a (scope · criteria · methodology · evidence
   standards · acceptance rules · blocking conditions · exit criteria · order ·
   deliverables).
2. Release Roadmap — §3 wave table + §1 campaign placement (after 18, gates 20,
   feeds 19/21).
3. Certification Plan — §3b (per-wave: inputs-to-REUSE → activities → evidence →
   exit; reuse-first per program law §2.6).
4. Release Scorecard Template — §3d (filled at RCP-9).
5. Risk Register — §3e (seeded RR-1..RR-12 from the campaign record; LIVING;
   headline RR-1 = the uncommitted tree, CRITICAL-operational, owner action).
6. Certification Matrix — §3c (dimension × certified base × gap-to-close).
7. Executive Summary — delivered in-session at RCP-0 close (below).

**Executive summary:** the ERP enters release certification with an unusually deep
certified substrate (battery 1871/1871 · verification engine 1.0.0 · golden money
journeys · 9-app permission certification · Phase-18 documentation permanence). The
program's job is INTEGRATION-GRADE proof: one feature inventory, one ₹-reconciliation
world, one integrated security matrix, one deployment-readiness verdict — every
subsystem exiting CERTIFIED or BLOCKED with objective evidence, then a Go/No-Go at
RCP-9. Biggest pre-known risks: the uncommitted tree (RR-1), monitoring/deployment
gaps (RR-2/3) — both owned by RCP-8 or earlier owner action.

**Quality gates:** zero implementation · zero certification claimed (nothing marked
CERTIFIED at RCP-0) · zero scope expansion (deliverables = exactly the owner's 7) ·
docs-sync same session (program doc revised · this log created · index row · status ·
memory). Battery not run (U5 — no code).

⏸ Next: **RCP-1 (Architecture Certification)** — owner-gated.

---

## RCP-1 — Architecture Certification — ✅ EVIDENCE COMPLETE 2026-07-18 (evidence ONLY — zero code/repairs; method: import-linter + main-thread single-writer census + 2 supplemental agents [ADR-evidence + adversarial layering hunt], every MAJOR/money claim re-verified main-thread)

### 1.1 Dependency Report

`lint-imports` (672 files, 1,910 dependencies): **Contract 1 (foundation purity,
ENFORCED): KEPT** — core+accounts import no domain app; C-1 closeout made it
stricter (retro-tag edge removed). **Contract 2 (acyclic target, REPORT-ONLY by
design — its violation list IS the M4 coupling worklist, per the contract's own
comments): 117 edges = 22 runtime + 95 test-only.** Runtime breakdown, ALL
pre-documented in `.importlinter` itself: production→expense **13** (SWA
allocation/credit + settlement/payroll reads; FUTURE-STAGE-REDESIGN tagged) ·
raw_materials→production **4** + raw_materials→tracking **4** (roll-assign view +
roll_service history logging; "relocation candidates, same pattern as P4.2") ·
production→inventory **1** (access_views Role read; the pending RBAC-relocation
tail). **CYCLE CHECK: NO CYCLES** — zero expense→production / tracking→production
reverse runtime imports (grep-proven); all 22 edges one-way upward reads.
Sanctioned function-level edges (R10 machines · VER devseed) all carry in-file
ignore rules with rationale.

### 1.2 ADR Compliance Matrix (all 11 active ADRs; agent-collected, money rows main-thread re-verified)

| ADR | Decision (headline) | Enforcement (verified) | Status |
|---|---|---|---|
| 0001 services-own-writes/no-signals | zero live receivers (tombstone only); services/ per app; FoundationPurityTests | **COMPLIANT** |
| 0002 single-writer per ledger/audit | ledger_service:42 sole WLE writer · history_service:20/36/45 · advance_service:46 · settlement_service:179 · adda_settlement_service:163/661; balances derived (worker_balance) | **COMPLIANT** (SWA = documented CLOSED 2-writer set via 0007: allocation_service:136 + adda_settlement_service:422 — main-thread verified, guard-tested) |
| 0003 three-concept RBAC | user_has_perm order exact (permission_service:127–146) · access_service skill gate · SidebarAccessMiddleware URL co-gate | **COMPLIANT** |
| 0004 tracking append-only primitive | string FKs · barcode value law + range CheckConstraints · one-shot pin | **COMPLIANT** (doc-drift note: body still says edge direction "deferred"; P4.2 resolved it — pointer staleness only) |
| 0005 Option B production≠financial | worker_task_service:147/372 "NO ledger here" · money only at finalize (log_credit:436) · LEDGER_CREDIT_AT_ALLOCATION default False (base.py:186) | **COMPLIANT** (main-thread verified) |
| 0006 architect-don't-implement | factory-FK/Celery ABSENT (the decision) · derived balances · assertNumQueries oracles | **COMPLIANT-as-designed** |
| 0007 era cutover Option A | symmetric double-credit guard both directions (allocation_service:84–93 · _settleable_lines:88–144) · armor (_shared:125–141 · void refusal:175–181) · lever pinned in 8 legacy test files | **COMPLIANT** (legacy-path deletion soak-gated BY the ADR) |
| 0008 commerce boundary | zero price/revenue fields on production models (grep) · no commerce models · FeaturedProduct = the ADR's own documented pre-existing G6 seed | **COMPLIANT-as-designed** |
| 0009 cost truth | Decision-4 grouped-guard (cost_service:156–174) · Decision-3 earn_map · Decision-5 honest-NULL + sole consume_leftover; + the P17 engine (RMX-E per-Decision table) | **COMPLIANT** |
| 0010 growth/identity locks | global sequences (ADST/SETL/CR-) · partial-unique first-pass lock (worker_task.py:83–85) · barcode permanence | **COMPLIANT-as-designed** |
| 0011 salary factory-level | _settleable_lines monthly exclusion (:140–141, main-thread verified) · record_expense sole writer · zero FactoryExpense refs in production/ | **COMPLIANT** |

**Zero ADR violations.** Pattern-tool pack (patterns_ai scope): walls hold everywhere
checked (compute_bridge sole CV door · ADR-H reverse-import wall incl. migrations ·
D2/D3 DECIDED and implemented); honest flags: most stamps still DRAFT (owner sign-off
never flipped post-V2-reset), ADR-B archived with its era, ADR-C integer-µm vs live
integer-mm helper (unit realignment never amended back).

### 1.3 Layering Report + Violation Register (adversarial hunt + main-thread verify)

**Money boundary AIRTIGHT** (hunter + main-thread census agree): WorkerLedgerEntry 1
write site (zero direct writes even in tests + devseed purity guard) · FactoryExpense
1 · WST/WSC 0 external · *History 0 runtime-external · AddaSettlement/Items/Evidence ·
WorkerAdvance · PayrollSettlement · RateCorrectionAudit all service-side · leftover
consumption sole-writer with the one view door delegating. **Signals EXTINCT** (full
grep; tombstone only). **Raw is_superuser as gate: ZERO** (all mixins route
user_has_role; residual hits = data display/form fields/sanctioned permission_service
internals). **bod window-never-engine VERIFIED** (no models.py; zero .objects/.save/
POST in non-test code). **Cross-layer clean** (services never import views; models
never import services; middleware write-free; templatetag exception = machines
read-only counts with documented direction rationale).

| # | Sev | Finding (main-thread confirmed) | Disposition needed |
|---|---|---|---|
| **F1** | **MAJOR** | `SidebarAccessListView.post` (inventory/views/sidebar_access_views.py:81–96): bulk M2M upsert over EVERY SidebarItemRule inside view-owned @transaction.atomic — Law-4 breach on permission-bearing data. No bypass (SA-gated; SA excluded at write + re-enforced at read) — architecture violation, not a security hole | **owner: fix (extract to service) or accept** |
| **F3** | MINOR (money-adjacent) | `WorkerProfileEditView.form_valid` = bare `form.save()` incl. `opening_advance` (seeds Advance Outstanding) — no service, no audit row; sibling pay_basis path correctly routes payroll_service. Mitigations: _ManagementOnly + min_value=0. **Reported per the Money-Write STOP rule (existing path; never silently fixed)** | **owner decision** |
| F2 | MINOR | WorkerProfile get_or_create on GET, duplicated (expense/views.py:303/314) | register |
| F4 | MINOR | scan-audit stamp written in view (tracking_barcodes.py:188–191; locked, atomic, documented) | register |
| F5 | MINOR | pattern photo REMOVE hard-deletes in view while attach uses the service (pattern_stage_views.py:396–399) | register |
| F6 | MINOR | User forms persist skills/extra_roles M2M via form.save_m2m() from views (standard Django idiom; guards service-routed) | register |
| F7 | MINOR | signals.py tombstone references removed StockService | register (doc drift) |
| F8 | NOTE | tests write guarded tables directly in 10+ files (WLE excepted — zero even in tests) | register (test hygiene) |

### 1.4 Extension Seam Report

**Stable seams (live):** ExpenseTemplate.frequency enum (monthly-only; future
frequencies without redesign — MEE charter) · WorkflowStage.cost_method +
allocation_dimensions (per-stage archetypes) · handler-dispatched stage registry
(open/closed, pinned by test_open_closed_proof) · BOD Widget Registry + Metric
Resolution Ladder (all future KPIs/widgets) · devseed feature-scenario registry (25
slugs) + verification check registry · knowledge_sync detector registry (23) ·
AddaStageRoleRate resolver · RM-V2 service seam (recorded, Appendix A amendment:
reads behind seam; read-path-over-materialization) · enforcement flags ×3 (OFF;
staged-enable runbook) · TM-1/TM-2 tracking modes behind the C-TM chokepoint ·
ADR-0006/0008/0010 future-scope fences (multi-factory site dimension · G1–G7 ·
Piece models from existing ranges). **Frozen interfaces:** PDD v1.0 ·
MANUFACTURING_V1_FREEZE · Operational Foundation · design system · patterns_ai
Foundation v1.0 · DOC_STANDARDS v1 · campaign contracts.

### 1.5 Architecture Risk Register (every finding classified; nothing omitted)

| Class | Items |
|---|---|
| CRITICAL | — none — |
| MAJOR | F1 (view-owned bulk permission write) — owner disposition required before RCP-9 |
| ACCEPTABLE | F2 · F3 (money-adjacent, owner decision) · F4 · F5 · F6 · F7 · F8 · 22 runtime layering edges (pre-documented worklist; no cycles) · 95 test-only edges · accounts ≈5 role-lookups/request · ADR-0004 pointer staleness · pattern-pack DRAFT stamps + ADR-C unit note · INFO residue #6–#14 |
| DEFERRED (by design, recorded) | production→expense facade retirement (FUTURE-STAGE-REDESIGN) · raw_materials relocations (P4.2 pattern) · RBAC-relocation tail (arch-remediation paused stream) · era-A physical deletion (0007 soak-gate) · S6 reported_quantity retirement · god-file splits (paused remediation) |

### 1.6 ARCHITECTURE CERTIFICATE

| Domain | Verdict |
|---|---|
| Application boundaries + import contracts | **CERTIFIED** (contract-1 KEPT enforced; contract-2 report-only with fully-documented worklist; no cycles) |
| ADR compliance (11 active) | **CERTIFIED** (zero violations; reservations are the ADRs' own design) |
| Ownership + single-writer rules | **CERTIFIED** (money boundary airtight; closed writer sets; devseed purity guard) |
| Service boundaries + layering | **BLOCKED-pending-owner-disposition** — F1 (MAJOR) must be fixed via the defect protocol or owner-accepted; F3 awaits the money-adjacent ruling. Everything else in the domain verified clean |
| Extension seams + frozen components | **CERTIFIED** (seam inventory §1.4; frozen set intact) |
| Technical debt | **CERTIFIED** (fully enumerated + classified §1.5; no unrecorded debt found) |
| Dependency rules | **CERTIFIED** (§1.1) |

**Overall: 6/7 domains CERTIFIED · 1 BLOCKED-pending-disposition (F1 fix-or-accept ·
F3 ruling).** Per program §4 a MAJOR blocks until fixed+re-verified or owner-
dispositioned; this wave is evidence-only, so the disposition is the owner's next
call — either inside the RCP-1 close review or as the first item of a defect wave.

**Quality gates:** zero code changed (estate untouched — evidence-only) · zero
redesign · agents supplemental, F1/F3 + all money citations re-verified main-thread ·
battery untouched at 1871 baseline (no code).

⏸ Next: owner disposition of F1/F3 → then **RCP-2 (Business Certification)** — owner-gated.

---

## RCP-1A — Architecture Defect Closure — ✅ COMPLETE 2026-07-18 → ARCHITECTURE: ALL DOMAINS CERTIFIED

### 1A.1 Architecture Defect Report + Repair Report

**F1 (MAJOR — Law-4 bulk permission write in view) — REPAIRED, smallest
architecture-preserving change:**
- NEW `config/inventory/services/sidebar_service.py` — `save_sidebar_rules(
  {rule_id: (role_ids, skill_ids)})`: THE SidebarItemRule assignment writer;
  primitives-only signature (ADR-0006); service-owned `@transaction.atomic`;
  super_admin excluded at write (read-time wall in `build_menu_for` unchanged —
  double wall preserved).
- `SidebarAccessListView.post` → PARSE-ONLY (POST checkbox lists → primitive
  mapping → one service call). `@transaction.atomic` + all M2M writes removed
  from the view. **Behaviour byte-same** (same clearing semantics: un-posted
  rule → empty lists → cleared; SA exclusion identical; same redirect+message).
  Authorization untouched (`_SuperAdminOnly` + middleware).

**F3 (money-adjacent) — DESIGN REVIEW then repair. Ruling: YES, service-governed —
with a corrected factual basis discovered during review:** the audit chain
contradicted itself — the form's PA-06-1 comment claimed `opening_advance` "seeds
Advance Outstanding — corrupts recovery math" while expense README row WP-A says
"informational only". **Code truth established (grep: zero service/computation
reads; the template's own hint: "Informational. To make a pre-system advance
recoverable, also record it as a dated Advance"): WP-A is CORRECT — it is a
DISPLAYED ₹ figure, not a computational input** (recoverable advances =
`record_advance` → WorkerAdvance rows). The RCP-1 finding's severity premise was
inflated by the wrong comment. Ruling stands YES on consistency grounds: a
management-facing ₹ figure follows the project's own pay-basis precedent
(chokepoint service + audit, never bare `form.save()` in a view), and the
chokepoint future-proofs it if it ever becomes computational.
- NEW `payroll_service.update_payout_profile(worker, *, actor, …9 fields)` —
  THE WorkerProfile payout-details writer: `@transaction.atomic` + row-locked
  `get_or_create` + ≥0 re-validation (never trust the form) + every
  opening_advance change audit-LOGGED old→new+actor. `pay_basis` deliberately
  NOT accepted (`set_pay_basis` stays the sole basis writer). **An append-only
  audit ROW (à la WorkerPayBasisAudit) = a new table = U14 owner-gated
  follow-up — offered, not built.**
- `WorkerProfileEditView.form_valid` → delegates to the service; `form.save()`
  eliminated from the money path. Module docstring, form comment (the wrong
  PA-06-1 claim), and view comment corrected to the code truth.

**Scope discipline:** F2 (get_or_create-on-GET) deliberately NOT touched
(registered ACCEPTABLE at RCP-1; no scope expansion).

### 1A.2 Re-verification Report (affected checks only + U5 battery)

- **Single-writer:** M2M writes exist ONLY in sidebar_service (view: zero
  `.set()`) · `form.save()` gone from the profile path (grep) · WorkerLedgerEntry/
  FactoryExpense/WST/WSC census unchanged (untouched files).
- **Permission boundaries:** SA write-time exclusion test-pinned
  (`SidebarAccessSaveTests.test_post_updates_roles_and_excludes_super_admin`);
  `_SuperAdminOnly`/`_ManagementOnly` gates unchanged.
- **Money boundaries:** opening_advance now chokepoint-owned + logged; pay_basis
  sole-writer intact; no ledger/settlement contact anywhere in the diff.
- **ADR compliance:** 0001 (services own writes) — the RCP-1 exception is GONE;
  0002 writer-census extended consciously (payroll_service docstring: TWO writes);
  0006 primitives signatures honored by both new functions.
- **Import contracts:** `lint-imports` re-run — contract-1 KEPT; contract-2
  runtime edges STILL 22 (zero new cross-app edges; new imports are downward).
- **Tests:** +7 (3 sidebar behavior/exclusion/Law-4-pin + 4 profile service-routing/
  negative-guard/audit-log/Law-4-pin) — 15/15 targeted, then full battery.
- **P14 guard catch #7 (designed):** devseed graph-floor fired on the new service
  module (57→58) + the RCP-0 evidence log (doc 957→958) → routine licensed
  P8→P9 loop → graph **`78a34fc3ba15`** (1,982 nodes; validator ALL PASS;
  fixed point — second build byte-identical) → 581 cards re-stamped → sweep
  BLOCKER=0/WARN=2 (the 2 accepted) → devseed suite GREEN.
- **BATTERY 1878/1878 — NEW BASELINE** (10-app **1132** [1125+7] · patterns_ai
  528 · devseed 140 · verification 78; sequential fresh-DB).
- **U6 docs same-session:** inventory GUIDE (+sidebar_service row + views row
  note) · expense GUIDE (payroll_service row: TWO writes) · expense README
  (workerprofile row: profile writes via the chokepoint) · the PA-06-1/WP-A
  contradiction resolved in favor of code truth.

### 1A.3 Updated Architecture Certificate

| Domain | Verdict |
|---|---|
| Application boundaries + import contracts | **CERTIFIED** |
| ADR compliance (11 active) | **CERTIFIED** |
| Ownership + single-writer rules | **CERTIFIED** |
| Service boundaries + layering | **CERTIFIED** (F1 repaired + re-verified; F3 ruled + repaired) |
| Extension seams + frozen components | **CERTIFIED** |
| Technical debt | **CERTIFIED** |
| Dependency rules | **CERTIFIED** |

**ARCHITECTURE CERTIFICATE: ALL 7 DOMAINS CERTIFIED.** RCP-1 scorecard row →
CERTIFIED (evidence: §RCP-1 + §RCP-1A).

### 1A.4 Updated Risk Register

MAJOR: **none open** (F1 closed). Moved to closed: F1 (repaired, test-pinned),
F3 (ruled + repaired; interim log-audit; audit-ROW = U14-gated follow-up on the
extension queue). Unchanged: the ACCEPTABLE set (F2/F4–F8 + documented layering
worklist + doc-drift notes) and the DEFERRED set (§1.5). One register correction:
F3's original "seeds recovery math" premise corrected to "displayed ₹ figure
(WP-A)" — severity basis was comment-drift, now fixed at source.

⏸ Next: **RCP-2 (Business Certification)** — owner-gated.

---

## RCP-2 — Business Certification — ✅ EVIDENCE COMPLETE 2026-07-18 (evidence ONLY — zero code; live scratch_2 world :8004, torn down after)

### 2.0 Method + the disclosed instrument failure

Planned agent fan-out (40 evidence collectors) **FAILED — session limit; 40/40 agents
errored; ZERO agent findings used** (recorded per the Audit-Subagent-Honesty rule:
finders fail ⇒ main-thread + record failure). Everything below is MAIN-THREAD:
scripted instruments + certified engines + live browser evidence + the campaign's own
certification corpus.

### 2.1 Canonical Feature Inventory (40 features — the release denominator)

Denominator = graph feature-index (28) ∪ campaign-era capabilities (12: MEE ·
material-spend · BOD · factory-expenses · FnF · payroll-overview · tracking-exports ·
storefront · access-hub · role-dashboard · rm-masters · scan-history). Per-feature
row: origin → entry route(s) → gate → test evidence → docs → verdict.

| # | Feature | Origin | Entry route(s) | Gate | Test evidence | Docs | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | login-auth (login/logout/reset; public signup CLOSED S2) | PDD + accounts baseline | /accounts/login/ | anon-open; lockout+rate-limit | accounts suite (Argon2/lockout/OTP pins); census: anon 200 | accounts README·GUIDE | **CERTIFIED** |
| 2 | user-role-admin (user CRUD · curated Roles editor · skills) | PDD §RBAC + OWN-D | /accounts/users/ · /inventory/roles/ | SA-only | `RolePermissionCurationTests` + accounts view tests; census 403-walled | RBAC.md · GUIDEs | **CERTIFIED** |
| 3 | sidebar-access-control | PDD RBAC + RCP-1A | /inventory/sidebar-access/ | SA-only + middleware co-gate | `SidebarAccessSaveTests` ×3 (RCP-1A) + middleware tests | RBAC.md · inv GUIDE | **CERTIFIED** |
| 4 | access-control-hub | OWN-D | /inventory/access/ | SA-only | `AccessControlHubTests` ×3; capture 3-width | inv GUIDE | **CERTIFIED** |
| 5 | public-homepage | PDD | / | anon | census anon 200; storefront tests | storefront README | **CERTIFIED** |
| 6 | role-aware-dashboard | PDD §27-D6 + R5 | /inventory/my-dashboard/ | login; role-aware content | inventory dashboard tests (helper badges · mgmt digest · perf 21) | inv GUIDE | **CERTIFIED** |
| 7 | roll-intake (bulk, priced wall) | PDD + ADR-0009 D5 | /raw-materials/rolls/ +bulk | mgmt; price fields FINANCIAL_ROLES (4-layer wall) | rm suite (wall · bulk · damage); RMX-A wall re-proof; capture | rm README·GUIDE | **CERTIFIED** |
| 8 | roll-adda-assign | PDD | /raw-materials/assign/ | layering-stage gate | rm assign tests; feature-allocation world 7/7 | rm README | **CERTIFIED** |
| 9 | leftover-consume | ADR-0009 D5 (sole writer) | via stage panel door | mgmt whole-piece | `test_c1_hardening` double-consume + RMX leftover-chain pins; rm-expense world 8/8 | pool/roll docs | **CERTIFIED** |
| 10 | rm-masters-dashboards | baseline | /raw-materials/ + masters | mgmt | rm suite; census 200s | rm README | **CERTIFIED** |
| 11 | product-flow-editor (+Stage library · TM/dimension fields) | PDD + REQ_REVIEW_STAGE_TRACKING | /production/products/ +flow | mgmt; Stage CRUD perm-gated | production flow_service + grain-monotonicity tests | production OVERVIEW | **CERTIFIED** |
| 12 | adda-create | PDD | /production/addas/ | mgmt | adda_service tests (race-safe counter); capture | production docs | **CERTIFIED** |
| 13 | layering (entries + mandatory leftover) | PDD + CUTTING_DESIGN | stage panel | skill-gated (access_service) | layering service tests; census; feature worlds | stage docs · material_flow | **CERTIFIED** |
| 14 | cutting-pattern (stage-trio: checklist/photos) | STAGE_TRIO_SPEC | stage panel | skill-gated | cutting_pattern service tests | stage docs | **CERTIFIED** |
| 15 | cutting (bundles · APSCPB breakdown) | CUTTING_DESIGN | cutting workspace | skill-gated | cutting suite (b422570a era + since) | production OVERVIEW | **CERTIFIED** |
| 16 | stage-completion-reopen (+downstream guard) | S4-P5 | stage panels | skill + guards | `test_s4_reopen_guard` + skeleton tests | pool_service chokepoint | **CERTIFIED** |
| 17 | worker-assignment (sole roster source) | PDD amendment 4 | stage panel | manager | set_stage_workers CI gate 4/4 | ARCH_V2 | **CERTIFIED** |
| 18 | worker-reporting (good/alter/missing) | ARCH_V2 + S3 | /production/worker-report/ | worker self, phone-first | task-lifecycle + S3 suites; golden ₹225 | stage_earnings_flow | **CERTIFIED** |
| 19 | pool-split-blind-reporting | S4 | stage panel | manager alloc; blind worker | `test_s4_pool` + bound tests (flags OFF by design) | pool_service | **CERTIFIED** |
| 20 | verify-quantity | ARCH_V2 | report review | manager | verified-else-reported settlement pins | fnf_business_flow | **CERTIFIED** |
| 21 | adda-360-hub | A360 plan (G4) | /production/addas/<code>/360/ | mgmt | `test_a360_overview` (pin 80) + parity pins; RMX-E identity | A360 plan · PAGES | **CERTIFIED** |
| 22 | costing-dashboard (+P17 Material/Full-Cost) | ADR-0009 + RMX-D | /production/costing/ | mgmt | perf pin 16 + RMX suites; capture: duality tiles + honest-NULL banner LIVE | costing_flow (RCP-1A-updated) | **CERTIFIED** |
| 23 | barcode-generation (one-shot, ranges) | ADR-0004/0010 | barcode workspace | mgmt | one-shot pin + range constraints tests | tracking docs | **CERTIFIED** |
| 24 | tracking-scan-history | ADR-0004 | /tracking/ + scan | production roles; dashboard mgmt-walled | scan/history/dashboard-audit tests; G-AUTH-1 | tracking docs | **CERTIFIED** |
| 25 | tracking-exports (csv/xlsx/pdf + re-download) | V1.1 item 3 | /inventory/tracking/exports/ | ManagerOrAdmin | exports tests; feature world 7/7 | EXPORTS.md | **CERTIFIED** |
| 26 | machines (register · possession windows · ⚙ stamp) | R10-A | /machines/ | mgmt; counts via templatetag | machines suite; feature world 7/7; capture | machines README·GUIDE | **CERTIFIED** |
| 27 | my-earnings (Expected→Earned→Paid) | V2-3 | /expense/my/ | worker SELF-scoped | visibility-ladder tests; capture (mobile ladder LIVE ₹900/₹350/₹900/₹0) | expense README | **CERTIFIED** |
| 28 | advances (separate loan pool) | payroll design | /expense/advances/add/ | mgmt; monthly-refused (M-2) | advance tests + recovery pins | expense README | **CERTIFIED** |
| 29 | settlement-queue (batched 6q) | OI-C1 | /expense/settlements/ | mgmt | `test_queue_batching` byte-identical | expense README | **CERTIFIED** |
| 30 | settlement-finalize (THE money boundary) | ARCH_V2 §11 + S1/S5 | settlement detail | mgmt; funnel skip-classes; S5 recon gate (flag OFF) | adda_settlement suite + goldens ₹801/₹344.25/₹633 + evidence S5 | ARCH_V2 · chokepoint | **CERTIFIED** |
| 31 | settlement-reverse-supersede | §11 + V2-3 armor | settlement detail | mgmt; era guards | `test_v2_3_guards` + reopen-voids-pay | ARCH_V2 | **CERTIFIED** |
| 32 | worker-payment (cash) | payroll design | /workers/<id>/settle/ | mgmt | settlement_service tests + ledger debit pins | expense README | **CERTIFIED** |
| 33 | full-and-final (R7) | PDD §20/§27-D5 | worker detail → FnF | super-admin + reason | fnf suite (blockers · only_worker · write-off); feature world 8/8 | fnf_business_flow | **CERTIFIED** |
| 34 | payroll-overview | R4 | /expense/payroll/ | mgmt | payroll tests (monthly badges) + perf; capture | expense README | **CERTIFIED** |
| 35 | factory-expenses (R5) | PDD §21 + ADR-0011 | /expense/expenses/ | mgmt; void SA+reason | `test_r5_factory_expense` (ADR-0011 named test) | expense README · ADR-0011 | **CERTIFIED** |
| 36 | monthly-expense-engine (P16) | PDD entry 7 | /expense/templates/ · /generate/ | mgmt; SA levers | MEE 44-scenario replay + engine suites; feature world 7/7; captures | MEE log · expense README | **CERTIFIED** |
| 37 | material-spend + costing completion (P17) | PDD entry 8 | /expense/material-spend/ | _ManagementOnly (D2 permanent) | RMX suites 28 + one-rupee-once; world 8/8; capture | RMX log · READMEs (FFD-E) | **CERTIFIED** |
| 38 | bod-dashboard (17 widgets + D9 landing) | PDD entry 6 | /bod/ | Owner/SA-only | bod suite + window-audit (RCP-1 re-verified no-ORM); world 8/8; capture LIVE numbers | BOD log · bod README | **CERTIFIED** |
| 39 | storefront (listing team) | baseline + ADR-0008 G6 seed | /storefront/ | listing_team/mgmt | storefront suite; world 7/7 | storefront README | **CERTIFIED** |
| 40 | pattern-layout-tool (phases 1–3) | PRODUCT_VISION_V2 | /patterns/ studio | mgmt | patterns_ai 528 suite; world 7/7 | PLATFORM_STATUS §8a | **CERTIFIED (shipped scope: phases 1–3; 4–6 = deferred register, unbuilt by design)** |

**40/40 features accounted; 0 BLOCKED; 0 orphan features** (every capability traces to
a PDD/freeze/campaign origin — nothing undocumented found).

### 2.2 Business Traceability Matrix

Chain per feature = the row above (origin→route→gate→tests→docs) + browser evidence
(§2.3) + certification (this section). Deep 7-link walk PROVEN on the RMX exemplar at
FFD-D (the protocol demonstration — every link resolved). Link-resolution instrument:
FFD-C/E sweeps (0 broken references estate-wide, BLOCKER=0). Origins verified against
the PDD amendment register (8 entries) + MANUFACTURING_V1_FREEZE + the four phase logs.

### 2.3 Browser Verification Report

- **Identity × URL census (live scratch_2, :8004): 100 argument-free GET routes × 4
  identities (anon/SA/manager/worker) = 400 requests → ZERO 5xx, zero errors.**
  anon: 17 public-by-design 200s + 83 auth-walls · SA 87×200 · manager 61×200/18×403 ·
  worker 22×200/47×403 — the walls hold live. Data: scratchpad `rcp2_census.json`.
- **verify_factory 19/19** on scratch_2 (body_hash `121c2ed5…` = the certified P16/P17
  determinism anchor) + **verify_feature 10/10 worlds ALL PASS (74 checks)** —
  business-correctness proven per feature family (allocation 7 · settlement 8 · fnf 8 ·
  machines 7 · patterns-ai 7 · storefront 7 · tracking-exports 7 · bod 8 ·
  monthly-expense 7 · rm-expense 8).
- **Captures: 48 (16 feature pages × 360/768/1280)** — SA + worker + anon sessions;
  spot-verified renders: BOD mobile (live widget numbers), costing desktop (ADR-0009
  duality tiles ₹10,049.75 vs ₹9,748.25 SEPARATE + live honest-NULL banner "14 consumed
  rolls without a purchase price"), My-Earnings mobile (ladder ₹900/₹350/₹900/₹0,
  card-stacked). Session-scratchpad storage — per PI-2 (pending owner ratification)
  not repo-archived; textual evidence recorded here.
- Console-error capture: not instrumented this wave (headless-screenshot method);
  the RC browser instrument (RCP-2's own deeper walk) remains available if owner
  orders it — recorded as a method boundary, not claimed.

### 2.4 Workflow Certification Report

Golden journeys: the three settled journeys (₹801 / ₹344.25 / ₹633) + golden ₹225
byte-asserted INSIDE the battery (their suites green at baseline 1878) and re-proven
live by verify_factory's goldens on scratch_2. The full owner chain (RM→production→
workers→settlement→reports→dashboard) is EXECUTED by the seeder through certified
writers and verified end-to-end by verify_factory + the 10 feature worlds; its
surfaces render live (census + captures). Worker journey (assign→report→earnings),
manager journey (adda→stages→settle→pay), administrator journey (users→roles→
sidebar→access-hub) — all covered by the certified suites + live census + captures.

### 2.5 Orphan Detection

| Class | Result |
|---|---|
| Orphan routes | **5 TRUE ORPHANS** (finding B-F1): `cutting-bundle-add-item` · `cutting-bundle-item-save` · `layering-entry-update` · `layering-full-create-roll` · `layering-remove-remaining` — ZERO references (no template/JS/test/reverse; pre-workspace legacy mutation endpoints). +4 by-design unreferenced: media-protected/public (runtime file URLs) · styleguide (demo) · user_dashboard (F-1 legacy 301 alias) |
| Unused templates | **0/174** |
| Undocumented features | none found (40/40 trace to origins) |
| Untested features | the 5 orphan routes only |
| Hidden functionality | none found beyond the 5 orphans |
| Duplicate functionality | product CRUD ×2 = storefront catalog vs production products — the ADR-0008 G6 boundary BY DESIGN, not duplication |

### 2.6 Business Risk Register

| Id | Risk | Class |
|---|---|---|
| B-F1 | 5 orphan legacy mutation routes, unreferenced + untested (permission posture unverified) | **MAJOR — owner disposition: remove or test+keep (RCP-2A candidate)** |
| B-F2 | 3-Patti stage-trio config pass blocked on dev-Adda teardown (RR-12) | acceptable (owner action queued) |
| B-F3 | pattern-tool phases 4–6 deferred (vision scope, unbuilt by design) | deferred |
| B-F4 | browser captures session-scoped (PI-2 pending) · console-error capture not instrumented | acceptable (method boundary, recorded) |
| B-F5 | agent fan-out failure (session limit) — inventory assembled main-thread from certified corpus + live instruments | disclosed (method, not product risk) |

### 2.7 BUSINESS CERTIFICATE

| Domain | Verdict |
|---|---|
| Feature inventory completeness (40/40, no orphan features) | **CERTIFIED** |
| Traceability (origins→…→certification; FFD-D-proven method) | **CERTIFIED** |
| Reachability + permission walls (live 400-request census, 0 errors) | **CERTIFIED** |
| Business correctness (verify_factory + 10 worlds + goldens) | **CERTIFIED** |
| Responsive UI evidence (48 captures, 3 widths, spot-verified) | **CERTIFIED** |
| Route hygiene | **CERTIFIED-WITH-FINDING** (B-F1: 5 orphan routes → owner disposition) |

**BUSINESS: CERTIFIED (with B-F1 open for owner disposition — analogous to RCP-1's
F1 pattern: disposition or a small RCP-2A closure wave).** Battery stands at
1878/1878 (no code this wave).

⏸ Next: owner B-F1 disposition → **RCP-3 (Security Certification)** — owner-gated.

---

## RCP-2A — Business Hygiene Closure — ✅ COMPLETE 2026-07-18 → BUSINESS: ALL DOMAINS CERTIFIED

### 2A.1 Route Disposition Register (B-F1: the 5 orphans, individually reviewed)

Evidence per route: zero references (template/JS/python/tests — 3 independent grep
passes incl. hardcoded-path hunt) · introduced in the cutting-overhaul era
(`b422570a` 2026-05-29, pre-workspace) · reachable only by hand-crafted POST
(gated: LoginRequired + ProductionRoleMixin, POST-only) · NO external dependents
(single-tenant ERP, no API consumers).

| Route | View | Disposition | Note |
|---|---|---|---|
| layering-entry-update | LayeringEntryUpdateView | **OBSOLETE → REMOVED** | its UI blocks ("Correct details", Section-04 mini-save) no longer exist; entry corrections flow via the workspace |
| layering-full-create-roll | LayeringFullCreateAndAttachView | **OBSOLETE → REMOVED** | full-intake variant with FINANCIAL fields (supplier/cost_per_kg) — unreferenced+untested money-adjacent endpoint; quick-create (referenced) survives; full intake = the roll bulk-intake page |
| layering-remove-remaining | LayeringRemoveRemainingClothView | **OBSOLETE → REMOVED** | service `remove_remaining_cloth` STAYS (tested, exported) |
| cutting-bundle-add-item | CuttingBundleAddItemView | **OBSOLETE → REMOVED** | service `add_item_to_bundle` STAYS |
| cutting-bundle-item-save | CuttingBundleItemSaveView | **OBSOLETE → REMOVED** | its own docstring said "kept for back-compat" — nothing consumed it; service `add_bundle_item` STAYS (tested: test_unified_tracking) |

### 2A.2 Repair Report (nothing left dangling)

Removed: 5 URL lines (production/urls.py) · 5 view classes (stage_views.py,
class-boundary-exact) · 10 re-export lines (views/__init__) · `EditRollEntryForm`
(sole consumer removed; form + docstring row + package exports) · 4 now-dead imports
(EditRollEntryForm · add_item_to_bundle · add_bundle_item · remove_remaining_cloth ·
update_layering_roll_entry — each verified import-only before removal). KEPT: all
service functions (tested, documented service surface). Generated hygiene: the 5
obsolete url-cards pruned from docs/features (generator renders-only, never prunes —
recorded as generator behavior).

### 2A.3 Re-verification Report

- **urlconf loads clean; 5/5 routes NoReverseMatch** (live reverse() proof).
- **Orphan re-scan: 0 true orphans.** Remaining by-design set (→ owner acceptance):
  media-protected/media-public (runtime file URLs) · styleguide (demo, ds_lint-exempt)
  · user_dashboard + inventory_dashboard (the F-1 legacy 301 aliases). No undocumented
  endpoints; no untested business endpoints remain.
- **Graph loop to FIXED POINT `5d159ece1df0`**: urls 551→546 · views 234→229 ·
  cards 581→576 · docs 958→953; validator ALL PASS; second build byte-identical;
  sweep **BLOCKER=0 / WARN=2** (the standing accepted pair).
- **BATTERY 1878/1878 — ALL GREEN, count unchanged** (10-app 1132 re-verified exact ·
  patterns_ai 528 · devseed 140 · verification 78) — the orphans had ZERO tests,
  which is exactly why they were orphans.
- **U6 docs same-session:** URL_ATLAS group counts 12→9 / 16→14 + removal notes ·
  COVERAGE_REPORT production route figure recounted (80; the old "64" was an era
  figure — noted) · production GUIDE removal banner · forms docstring row.

### 2A.4 Updated Business Certificate

| Domain | Verdict |
|---|---|
| Feature inventory completeness (40/40) | **CERTIFIED** |
| Traceability | **CERTIFIED** |
| Reachability + permission walls | **CERTIFIED** |
| Business correctness | **CERTIFIED** |
| Responsive UI evidence | **CERTIFIED** |
| Route hygiene | **CERTIFIED** (0 true orphans; 5 by-design unreferenced names recorded for owner acceptance) |

**BUSINESS CERTIFICATE: ALL DOMAINS CERTIFIED.** RCP-2 scorecard row → CERTIFIED
(evidence §RCP-2 + §RCP-2A).

### 2A.5 Updated Business Risk Register

B-F1 **CLOSED** (removed + re-verified). Remaining: B-F2 3-Patti config debt
(owner-queued) · B-F3 pattern phases 4–6 (deferred by design) · B-F4 capture/console
method boundaries (accepted; PI-2 pending) · B-F5 the disclosed agent-fan-out failure
(method note). NEW acceptance item: the 4+1 by-design unreferenced url names above —
recorded, awaiting the owner's blanket acceptance at RCP-9.

⏸ Next: **RCP-3 (Security Certification)** — owner-gated.

---

## RCP-3 — Security Certification — ✅ EVIDENCE COMPLETE 2026-07-18 (security-sensitive → ALL verdicts MAIN-THREAD, no delegated conclusions; live scratch_2 :8004 probes + static census; zero code)

### 3.1 Authentication

| Check | Evidence | Verdict |
|---|---|---|
| Inactive-user login | LIVE: `dev.min.inactive` (is_active=False) login POST → 302 `/accounts/inactive/`; every login-required page bounces to login → **NO session granted** | **CERTIFIED** (probe's URL-heuristic false-FAIL corrected main-thread — the exact reason security verdicts stay main-thread) |
| Login/logout | LIVE census (RCP-2): anon 200 on login only; auth flows route via `PasswordLoginView` | CERTIFIED |
| Password hashing | Argon2 primary (base.py:238) + PBKDF2/BCrypt fallbacks | CERTIFIED |
| Lockout / rate-limit | `accounts/throttle.py` — per-email + per-IP policies (tighter per-email = fraud surface); `check_throttle`/`reset_throttle` on every auth endpoint; SELF-lockout protection; security_logger warns on throttle/failure | CERTIFIED |
| Session/transport | production.py: SESSION_COOKIE_SECURE · CSRF_COOKIE_SECURE · SSL_REDIRECT · HSTS 1yr+preload+subdomains · NOSNIFF · proxy-ssl-header | CERTIFIED |
| Public signup | CLOSED (S2, V1.1) — pre-provisioned users only | CERTIFIED |

### 3.2 Authorization — Security Matrix (LIVE, corrected mounts)

| Surface | anon | worker | manager | SA |
|---|---|---|---|---|
| /app/users/ (user CRUD) | 302 | 302→dash | 302→dash | **200** |
| /app/users/add/ (GET+POST create) | 302 | **403** | **403** | 200 |
| /inventory/access/ (RBAC hub) | 302 | 302 | 302 (walled) | 200 |
| /inventory/sidebar-access/ POST | 302 | **302→dash (no write)** | — | 200 |
| /production/costing/ | 302 | **403** | 200 | 200 |
| /expense/material-spend/ | 302 (POST 403) | **403** | 200 | 200 |
| /expense/payroll/ · /settlements/ · /expenses/ | 302 | **403** | 200 | 200 |
| /bod/ (Owner/SA-only) | 302 | **403** | 403 | 200 |

Layered enforcement all verified present: **Roles** (Role FK + `user_has_role`) ·
**Skills** (`access_service.user_can_access_stage`, fail-closed) · **Sidebar rules**
(`SidebarItemRule`) **co-gated with URLs** by `SidebarAccessMiddleware` (menu hidden ⇒
URL blocked — live: worker→access-hub 302-redirect not 403, the middleware signature) ·
**View mixins** (`SuperuserRequiredMixin`/`SuperAdminOnly`/`_ManagementOnly`/
`ProductionRoleMixin`) · **permission_service** (no raw is_superuser gates — RCP-1
proven). Cross-app authorization holds (production stage access skill-gated regardless
of app entry).

### 3.3 Privilege Escalation Report (active attempts — all failed or classified)

| Attempt | Result |
|---|---|
| worker POST → sidebar-access save (SA-only) | 302→dashboard, **ZERO write** (SA-excluded even in the service, RCP-1A) |
| worker POST → /app/users/add/ (create user) | **403** |
| manager POST → /app/users/add/ | **403** |
| anon POST → /expense/material-spend/ | **403** (GET-only view, POST 405-class → 403 wall) |
| worker direct-URL → 7 financial/mgmt pages | **all walled** (6×403 + 1×302 middleware) |
| ID substitution: worker → /expense/workers/8/ (other worker detail) | **403** |
| parameter tampering: worker sidebar POST with forged role ids | no effect (redirect before write; SA-exclusion is server-side) |

**No successful escalation.** Every attempt failed with an authorization wall.

### 3.4 Financial Isolation Report

- **4-layer wall LIVE (the load-bearing RCP-3 proof):** roll detail page — **SA sees
  the price/supplier signals; manager gets the page (200) but the per-roll price is
  ABSENT** (RMX-D2 permanent rule: factory aggregates management-visible, per-roll
  economics FINANCIAL_ROLES-walled). Worker: 403 on every ₹ surface (costing,
  material-spend, payroll, settlements, expenses, BOD).
- Cost/material-price/payroll/settlement/advance/ledger/report surfaces: **no worker
  reachability** (§3.2 + §3.3); inference paths closed (worker gets zero a360 bytes,
  RCP-1 verified).

### 3.5 Object-Level Authorization Report

- Worker `/expense/my/` → 200, **SELF-scoped** (never role-gated, always own data —
  expense README invariant).
- Worker → another worker's management detail (`/expense/workers/8/`) → **403**.
- Cross-user/cross-role isolation: history G-AUTH-1 (test-pinned) + the 400-request
  RCP-2 census (worker 47×403) confirm record-level walls.

### 3.6 Write Boundaries (re-verified — consume RCP-1/RCP-1A)

Single-writer discipline intact (RCP-1 census, re-cited): WorkerLedgerEntry 1 site ·
FactoryExpense 1 (record_expense) · WST/WSC (worker_task_service) · *History
(history_service) · SWA (closed 2-writer set) · leftover (consume_leftover) ·
SidebarItemRule (sidebar_service, RCP-1A) · WorkerProfile money (update_payout_profile,
RCP-1A). Signals extinct. Money boundary airtight.

### 3.7 Auditability Report

| Security-sensitive action | Audit evidence | Enforcement |
|---|---|---|
| Permission/role changes | Role CRUD curated (RolePermissionCuration) · sidebar rules SA-gated | view gate |
| Pay-basis change | `WorkerPayBasisAudit` (old→new, actor, unsettled count) | sole-writer `set_pay_basis` |
| Template amount change | `ExpenseTemplateAmountAudit` + **DB CheckConstraint `~Q(reason='')`** (models:861) | append-only + reason-required |
| Rate correction | `RateCorrectionAudit` | sole writer `stage_rate_service` |
| FactoryExpense void | `voided_by` + mandatory `void_reason` (super-admin) | append-only, never edit |
| Settlement reverse/supersede | `reversed_at`/`reversed_by` + supersede chain; SWA soft-void | era guards (V2-3) |
| FnF write-off | write-off coherence CHECK (reason+actor together-or-neither) | DB constraint |
| Roll/Adda/Product edits | ClothRoll/Adda/ProductHistory | sole writer history_service |
| Login success/failure/throttle | `security_logger` (accounts.security) | logged every auth endpoint |

Owner P-3 satisfied: investigations don't depend on app logs — money/permission
mutations carry persisted audit rows with DB-enforced reason coherence.

### 3.8 Security Risk Register

| Id | Item | Class |
|---|---|---|
| S-R1 | PHASE_03 accountant contradiction (role reaches no page) — no accountant/listing_team identity seeded in scratch_2; role's live access indeterminate | **ACCEPTABLE — owner ruling needed (carried from RR-4)** |
| S-R2 | Console-error / client-side XSS surface not actively fuzzed (server-side authz is the certified layer) | acceptable (method boundary) |
| S-R3 | Rate-limit thresholds not load-tested (policy present + unit-pinned; live throttle not stress-fired) | acceptable (observe-only) |
| S-R4 | Security event logging = app logger, not a persisted SecurityEvent table (money/permission mutations DO persist audit rows; login events are log-only) | acceptable (P-3 met for money/permission; login-audit = log tier by design) |

### 3.9 SECURITY CERTIFICATE

| Domain | Verdict |
|---|---|
| Authentication (login/logout/inactive/reset/lockout/session) | **CERTIFIED** |
| Authorization (roles/skills/sidebar/middleware/mixins/permission_service/cross-app) | **CERTIFIED** |
| Privilege escalation (7 active attempts, all walled) | **CERTIFIED** |
| Financial isolation (4-layer wall live; worker fully walled) | **CERTIFIED** |
| Object-level authorization (self-scope + cross-user 403) | **CERTIFIED** |
| Write boundaries (single-writer, RCP-1/1A) | **CERTIFIED** |
| Auditability (audit rows + DB reason-coherence + security logging) | **CERTIFIED** |

**SECURITY: ALL 7 DOMAINS CERTIFIED.** One owner ruling outstanding (S-R1
accountant role — carried, non-blocking: no accountant surface is reachable-and-wrong,
the role simply has no seeded identity to certify). Battery stands 1878/1878 (no code).

⏸ Next: **RCP-4 (Financial Certification)** — owner-gated.

---

## RCP-4 — Financial Certification — ✅ EVIDENCE COMPLETE 2026-07-19 (money-sensitive → ALL verdicts MAIN-THREAD, zero delegated conclusions; zero code; ONE seeded world `inventory_seed_scratch_2` live :8004, torn down after; PRIMARY untouched — money sentinel EXACT)

### 4.0 Method + world provenance

Fresh allowlisted world (SEED-D5 law): DROP→CREATE→`migrate`→`seed_factory`
(created=156 · assertions=PASS) + the 4 money feature worlds layered on
(settlement/fnf/monthly-expense/rm-expense). Instruments: `verify_factory`
(engine 1.0.0) · `verify_feature` · scripted main-thread ORM census · LIVE HTTP
:8004 (real cast logins, GETs only) · targeted money suites on fresh test DBs.
**Instrument defects disclosed + corrected main-thread (the RCP-3 lesson, ×4):**
(i) SR-3 first attribution joined items' `first_swa` → false-FAIL (item stores
ONE SWA per worker; credits are per contribution line) — corrected to the
structural era-B marker `SWA.adda_settlement`; (ii) E-6 ₹-regex missed the
voided row's struck-through cell (₹ lives in the column header) — the row IS
rendered, "nothing disappears" holds; (iii) F-2 page-numeric duality check
degenerate when material Σ=0 — replaced by the component-identity check F-2b;
(iv) one test-module name typo (loader error, not a product failure). Zero
product defects behind any of the four.

### 4.1 Deterministic Replay Report

- `seed_factory` idempotency: second run **created=0 / skipped=234 / assertions=PASS**.
- `verify_factory` **19/19 PASS ×2 runs — body_hash byte-identical**
  `0aea27307bca4800…`. (Differs from RCP-2's `121c2ed5…` anchor: that world
  carried all 10 feature worlds — hash is world-composition-dependent;
  self-consistency, not point-in-time constants, is the engine's own law
  [MGT-C]. Recorded so future waves don't misread anchors.)
- Money feature worlds: **feature-settlement 8/8 · feature-fnf 8/8 ·
  feature-monthly-expense 7/7 · feature-rm-expense 8/8**.
- Golden journeys re-derived byte-identical on the fresh world:
  **₹344.25 (LOWER, ADST-0001) · ₹801.00 (T-SHIRT, ADST-0002) · ₹633.00
  (3-PATTI, ADST-0003)**; golden **₹225** byte-assert green in the targeted S3
  suite. Historical consistency = replay + goldens + the armor suites (§4.5).

### 4.2 Money Flow Report (writers → ledger → surfaces)

Single-writer chain re-verified LIVE in the seed logs + census: every
stage_earning credit written by `ledger_service` from
`adda_settlement_service.finalize` (ONE SWA per contribution line, dimension-true;
`assignment=swa`; structural era-B marker `adda_settlement` FK); recovery
debits carry `PayrollSettlementItem.ledger_entry`; payment debits
settlement-linked; **advances NEVER post to the ledger** (legacy categories
`advance`/`payment` EMPTY — LC-4). World category census: stage_earning/credit
84 · ₹2,228.25 · settlement_payment/debit 1 · ₹150.00. Source-FK discipline
exact (LC-5: exactly one source FK per non-reversal/adjustment entry, 0
violations). Balances DERIVED never stored (LC-3: `worker_balance` ≡
Σcredit−Σdebit for all 12 ledger workers).

### 4.3 Financial Reconciliation Report (RC-9 — the wave's gap-to-close)

**FOUR-WAY identity EXACT for every finalized settlement:
ledger ≡ expected_total ≡ Σitems ≡ ΣSWA:**

| ADST | Adda | ledger | expected_total | Σitems | ΣSWA |
|---|---|---|---|---|---|
| 0001 | LOWER-001 | 344.25 | 344.25 | 344.25 | 344.25 |
| 0002 | T-SHIRT-001 | 801.00 | 801.00 | 801.00 | 801.00 |
| 0003 | 3-PATTI-001 | 633.00 | 633.00 | 633.00 | 633.00 |
| 0004/0005/0006 | MIN/FNF/RME | 150.00 ×3 | 150.00 ×3 | 150.00 ×3 | 150.00 ×3 |

Global: Σ stage_earning credits **₹2,228.25 ≡ Σ finalized expected_totals**;
zero orphan/era-A credits (SR-8); item identity `final_payable ==
max(expected−recovered, 0)` exact (SR-7). **Live ₹-surface reconciliation (9
surface families, real HTTP):** settlement detail ×3 (each renders its
expected_total) · settlement queue (every finalized total) · payroll overview
(**12/12 worker balances ≡ `worker_balance` truth**) · worker detail
(dev.fin.a: balance + Σcredits ₹124.50) · **my-earnings as the WORKER**
(self-scope ladder shows own ₹124.50) · factory expenses (Σactive ₹9,000.00;
voided ₹100 visible struck-through, EXCLUDED from totals) · costing dashboard
(all 5 service-computed figures rendered) · material-spend (honest-NULL
banners) · A360 ×3 + BOD (§4.6).

### 4.4 ADR-0009 Verification Report (+ ADR-0011)

- **Decision-2 ONE assembly:** component identity `full_cost == material.net +
  settled_total + nonpayable_priced` for ALL 7 addas (F-2b); composition spot-read:
  T-SHIRT 921 = 801+120 · 3-PATTI 6933 = 633+6300 · LOWER 844.25 = 344.25+500.
  **A360 ≡ costing dashboard ≡ service** (F-3 parity byte-match ×3 addas).
- **Decision-3:** settled_total reads SWA earning snapshots ONLY (assembly
  source code-verified; never WSC.expected_*).
- **Decision-5 honest-NULL LIVE everywhere:** all consumed dev rolls unpriced
  on this world → material figures NULL-flagged, never fake ₹0; banner rendered;
  the priced-but-weightless roll CR-000006 (₹100/kg, weight NULL, purchased
  2026-01) NOT fake-valued on the purchases surface; unpriced events COUNTED.
- **One-rupee-once identity EXECUTED LIVE:** Σ `material_consumption_in_period`
  ≡ Σ per-adda material net — ₹-side 0.00 ≡ 0.00 (degenerate by world design,
  disclosed) **AND non-vacuously on the honest-NULL side: unpriced-event counts
  7 ≡ 7 both bases.** ₹-valuation with real prices = the priced-fixture pins:
  **31 RMX/costing tests green** (rupee-once, bulk/derive parity, Decision tables).
- **ADR-0011:** salary templates carry worker FK (DB CHECK, FE-2); monthly-basis
  workers excluded from settlement earning lines (FE-3); FactoryExpense void =
  reason-mandatory, voided excluded from Σ (FE-1); material-spend "sibling link
  only, never blended with FactoryExpense" honored (no blended figure found).

### 4.5 Financial Invariants Report (main-thread census)

**18/18 PASS** (after instrument correction): LC-1 amount>0 (0 violations, 85
rows) · LC-2 reversal integrity · LC-3 derived balances 12/12 · LC-4 legacy
categories EMPTY · LC-5 source-FK exact · SR-1 Σitems≡total (6 finalized) ·
SR-2 goldens present · SR-3′ four-way identity · SR-4 supersession net-0 ·
SR-5 double-credit guard 0 · SR-6 voided-SWA live credits 0 · SR-7 item
identity · SR-8 zero orphan credits · PP-1 payroll identity + ledger debits
exact (paid 150 ≡ debit 150) · AD-1 recovery ≤ principal · FE-1..3.
**Vacuous-on-world invariants (no live reversal/supersession/recovery specimens
seeded) proven by targeted armor suites instead — disclosed, not assumed:**
47 (v2_3 guards · adda_settlement_service · reopen-voids-pay · S5 recon BLOCK ·
S3 incl. golden ₹225) + 49 (material_spend · r5 factory-expense incl. the
ADR-0011-named test · expense generation) + 31 (RMX certification/read-paths ·
cost snapshot · flow cost) = **127 targeted money tests ALL GREEN** (fresh test
DBs; full battery not run — no code, U5).

### 4.6 Reporting Consistency Report (+ duplicate-money hunt)

**Same rupee, same everywhere:** worker balance identical across payroll
overview / worker detail / my-earnings (single source `worker_balance`);
settlement totals identical across queue / detail / ledger attribution / BOD
aggregate; expense Σ identical list / BOD; costing figures identical dashboard /
A360 / service (one assembly). **BOD explained-set EXACT — every rendered ₹ on
the combined view maps to a named service truth, zero unexplained figures:**
outstanding ₹2,078.25 (= 2,228.25 − 150.00) · Σ active expenses ₹9,000.00 ·
material ₹0.00 · advances ₹0.00. **Duplicate-money hunt: NONE FOUND** —
component identity (no hidden addend) + explained-set (no invented figure) +
one-rupee-once (no double-counted intake) + double-credit guard (no double
booking) + LC-4 (advances can't double-enter).

### 4.7 Financial Risk Register

| Id | Item | Class |
|---|---|---|
| FIN-R1 | World's material-₹ signal minimal BY DESIGN (all dev rolls unpriced → honest-NULL everywhere); live rendered-₹ material valuation therefore proven by priced-fixture suites + the count-side identity, not by non-zero live ₹ | acceptable (method boundary, disclosed) |
| FIN-R2 | PRIMARY `ADST-0011` draft ₹0 (XFB-001, 2026-07-18 02:44 UTC, 0 items — PRE-wave, zero money) | observation (owner may keep/discard) |
| FIN-R3 | `verify_factory` body_hash is world-composition-dependent (`0aea…` here vs RCP-2's `121c…`) — future waves must not read hashes as cross-world constants (MGT-C self-consistency law) | recorded (method note) |
| FIN-R4 | Four instrument false-fails this wave, all corrected main-thread — the standing reason money verdicts are never delegated | disclosed (method, not product) |

### 4.8 FINANCIAL CERTIFICATE

| Domain | Verdict |
|---|---|
| Ledger integrity (append-only, derived balances, reversal armor) | **CERTIFIED** |
| Money-write rules (single-writer chain, source-FK discipline) | **CERTIFIED** |
| Settlements (four-way identity, goldens, supersession/reopen armor) | **CERTIFIED** |
| Payroll + advances (payment identity, recovery bounds, separate pool) | **CERTIFIED** |
| Factory expenses + monthly engine (void discipline, ADR-0011) | **CERTIFIED** |
| Costing (ADR-0009 Decisions 1–5, one assembly, honest-NULL) | **CERTIFIED** |
| Material spend (one-rupee-once, purchases/consumption honesty) | **CERTIFIED** |
| Reporting consistency (cross-surface ≡, zero unexplained ₹) | **CERTIFIED** |
| Historical consistency + deterministic replay (idempotent seed, byte-identical verify, goldens) | **CERTIFIED** |

**FINANCIAL: ALL 9 DOMAINS CERTIFIED. No recalculation bugs found; no duplicate
money found.**

**Quality gates:** zero code · zero repairs · evidence-only · GETs only against
the live world · **PRIMARY money sentinel EXACT (read-only recount: ledger
170 / Σ₹10,880.25)** · world torn down after (server stopped + scratch DB
dropped) · battery baseline **1878/1878 stands** (no code; 127 targeted money
tests green this wave) · docs-sync same session (this log + campaign memory).

⏸ Next: **RCP-5 (Data Certification)** — owner-gated.

---

## RCP-5 — Data Certification — ✅ EVIDENCE COMPLETE 2026-07-19 (main-thread; zero code, zero schema work; scratch world `inventory_seed_scratch_2` rebuilt from empty, torn down after; PRIMARY read-only)

### 5.0 Method + world provenance

Fresh empty DB → **full `migrate` (186 migrations, zero errors)** → targeted
reverse-proofs → **ALL 21 executable scenarios seeded** (factory + 10 feature +
8 edge + minimal + demo; the 2 non-executable stay owner-refused by ruling:
₹225-historical + performance) — the richest data estate any wave has certified
(live supersession, rate-correction, reopen, damaged-roll, inactive-user,
composite-role, monthly-worker, over-allocation specimens). Negative probes are
INSERT/UPDATE attempts the DB must REFUSE — each rollback-wrapped, zero rows
persisted; scratch DB only. **Instrument false-fails disclosed + corrected
main-thread (×2):** (i) my reverse-proof used app-scoped forward
(`migrate production 0043`) after Django's cross-app dependency cascade had
also unapplied machines/patterns_ai/tracking dependents → seeds failed on a
missing table; recovery = one global `migrate` (21 re-applied) — recorded as
the recovery drill it accidentally was; (ii) append-only heuristic
`updated_at == created_at` false-FAILED on `auto_now`-vs-`auto_now_add`
microsecond insert skew (max 37µs) — corrected threshold >1s: **zero edited
rows**.

### 5.1 Data Integrity Report (structural)

- **Full migration history runs clean from empty: 186/186 applied, zero
  errors.** `makemigrations --check`: **"No changes detected"** — models ≡
  migration files exactly (zero drift).
- All 21 seed scenarios assert PASS at creation AND at re-seed; **verify_all:
  203/203 PASS, 0 fail, 0 skip** (engine v1.0.0) across every manifest on the
  world — structural + business assertions green over the whole estate.
- Zero negative money anywhere (ledger/expenses/SWA/items); zero future-dated
  ledger entries; zero invalid settlement states.

### 5.2 Referential Integrity Report

- **271 FK constraints, ALL VALIDATED** (pg census; zero NOT-VALID, zero
  deferred). History/audit tables use real FKs with PROTECT (`AbstractHistoryEntry.actor`
  PROTECT; money source-FKs PROTECT) — the "string FK" design in tracking is
  lazy app-label references, still DB-enforced.
- Orphan detection: zero parentless settlement items · WLE source-FK discipline
  exact on the 21-world estate (91 entries, 0 violations) AND on PRIMARY (170,
  0) · dual-FK cross-row coherence `BatchBarcode.adda ≡ batch.adda` exact.

### 5.3 Identity & Uniqueness Report

- **Zero duplicates on every natural identity key, both worlds:** user email ·
  Adda code · roll_id (CR-…) · AddaSettlement reference (ADST-…) ·
  PayrollSettlement reference (SETL-…) · barcode value. Worker identity: ≤1
  WorkerProfile per user.
- **Barcode identity:** ranges valid (start≤end, 0 bad), **zero overlapping
  ranges per (adda,color,size)** on scratch (11 batches) and PRIMARY (35
  batches, 5 lazy barcodes unique).
- **Identity permanence observed on PRIMARY:** Adda sequence gaps
  3-PATTI-009→010→012→016 — retired codes NEVER reused (ADR-0010).

### 5.4 Historical Integrity Report (lineage · append-only · lifecycle)

- **Append-only proven by edit-census:** ledger + ClothRoll/Adda/Product
  history + pay-basis/template-amount/rate-correction audits — **0 rows edited
  post-insert** (scratch: 348 rows; PRIMARY: 610 rows incl. AddaHistory 400)
  — a re-save would show seconds-scale `updated_at` drift; max observed 37µs
  (insert skew).
- **Lifecycle coherence:** finalized⇒settled_at (also DB CHECK) · reversed⇒
  reversed_at+by · supersedes targets only reversed/superseded — 0 violations
  both worlds. **Live supersession specimens (edge world + PRIMARY):**
  scratch chain ADST-0009(superseded)→ADST-0010(finalized): old net ledger
  **0.00**, successor carries the live ₹150; **PRIMARY chains ADST-0007→0008
  and ADST-0009→0010 BOTH net 0.00**. Voided SWAs: zero live credits.
  Rate-correction lineage: audit row 3.0000→4.0000, actor + reason + recalc_count=1.
- **Soft-state law:** deactivated identities present (is_active=False, 2 on
  scratch incl. the FnF leaver), nothing hard-deleted.

### 5.5 Constraint Verification Report

- **Census: 71 declared CheckConstraints + 8 UniqueConstraints + 9
  partial-uniques — 100% LIVE in PostgreSQL** (by name; partial-uniques as
  partial unique indexes). DB totals: 137 checks · 79 uniques · 271 FKs ·
  115 PKs. Zero NOT-VALID constraints.
- **Negative probes — the DB refused every invalid write (10/10 fired):**
  ledger amount=0 · expense amount<0 · finalized-without-settled_at ·
  salary-template-without-worker (the ADR-0011 CHECK itself, NOT-NULLs
  satisfied) · duplicate ADST reference · advance amount=0 · negative SWA
  snapshot via UPDATE · **second reversal of an already-reversed entry
  (uniq_one_reversal_per_entry — live specimen from the edge world)** ·
  negative WSC good_quantity via UPDATE · (duplicate barcode value: no lazy
  specimen on world — uniqueness enforced by the live unique constraint,
  D-2 census + PRIMARY 5-value dup-scan clean). All probes rolled back;
  post-probe convergence run proves zero residue.

### 5.6 Data Recovery Report

- **Reverse migrations proven live:** expense 0015→0014→0015 OK · production
  0043→0042→0041→forward OK (the U14-gated pair re-proven this wave; earlier
  documented reverse-proofs reused, not repeated).
- **Cross-app reverse cascade + recovery drill (unplanned, disclosed §5.0):**
  reversing production past R10 also unapplies machines/patterns_ai/tracking
  dependents (Django dependency graph — correct behavior); **recovery = one
  global `migrate` (21 re-applied, zero errors)**. Recorded as operational
  knowledge for the P19 runbook: after any targeted reverse, always finish
  with global `migrate`.
- **Rebuild-from-zero proven end-to-end:** empty DB → migrate → seed → 203/203
  verified — the full disaster-recovery path for the data estate (DB backup
  drill for PRIMARY itself = RCP-8 scope, unchanged).

### 5.7 Data Quality Report (+ PRIMARY hygiene census, RR-5)

- **PRIMARY (read-only): money sentinel EXACT (ledger 170 / Σ₹10,880.25 ·
  users 48 · dev.min 0)** · zero duplicate identities · zero lifecycle
  violations · zero edited append-only rows · zero negative/future-dated money
  · barcode ranges clean.
- **RR-5 hygiene finding: the four dev Addas (…011/013/014/015) are GONE** —
  teardown observed complete; sequence gaps preserved (identity law).
  Remaining dev data on PRIMARY: 33 `dev.*` cast users + DEV-NICKAR ×3 +
  DEV-P8B-A1 addas — the owner-authorized test cast (Test-Data rule
  2026-07-04), plus the pre-existing ₹0 draft ADST-0011 (FIN-R2). Disposition
  of the remaining dev cast = owner call at P19/P20 (deployment hygiene), not
  a data defect.
- Convergence/replay: **all 21 scenarios re-seed to created=0** (idempotent
  fixed point across the whole registry).

### 5.8 Data Risk Register

| Id | Item | Class |
|---|---|---|
| DAT-R1 | Targeted reverse of a mid-graph migration cascades across apps (machines/patterns_ai/tracking unapplied with production) — correct Django behavior, but a naive app-scoped forward leaves the estate partial; **runbook rule: always finish with global `migrate`** | acceptable (recorded → P19 runbook input) |
| DAT-R2 | Lazy `BatchBarcode` rows sparse on seeded worlds (0 scratch / 5 PRIMARY) — duplicate-value refusal proven by live unique constraint + census, not by probe specimen | acceptable (method note) |
| DAT-R3 | PRIMARY dev residue: 33 dev.* users · 4 DEV addas · ADST-0011 ₹0 draft — owner-authorized test data; production-deploy hygiene decision at P19/P20 | acceptable (owner decision queued, carried from RR-5) |
| DAT-R4 | 2 registry scenarios non-executable BY OWNER RULING (₹225-historical · performance) — refusal path itself verified (guard PASS, zero writes) | by design (recorded) |
| DAT-R5 | Instrument false-fails ×2 this wave (migration cascade · µs-skew heuristic) — corrected main-thread, disclosed | disclosed (method, not product) |

### 5.9 DATA CERTIFICATE

| Domain | Verdict |
|---|---|
| Data integrity (migrate-from-zero · models≡migrations · 203/203 verify_all) | **CERTIFIED** |
| Referential integrity (271 FKs validated · orphans 0 · cross-row coherence) | **CERTIFIED** |
| Identity & uniqueness (all natural keys duplicate-free · barcode ranges · identity permanence) | **CERTIFIED** |
| Lifecycle consistency (settlement/void/supersession states · 0 invalid states) | **CERTIFIED** |
| Cross-app consistency (dependency graph sound · dual-FK coherence · expense↔production links) | **CERTIFIED** |
| Historical integrity (append-only 0 edited rows · lineage · net-0 supersession, PRIMARY included) | **CERTIFIED** |
| Constraint verification (88 declared = 88 live · 10/10 negative probes refused) | **CERTIFIED** |
| Data recovery (reverse-proofs · cascade recovery · rebuild-from-zero) | **CERTIFIED** |
| Data quality (PRIMARY hygiene census clean · sentinel EXACT · convergence 21×created=0) | **CERTIFIED** |

**DATA: ALL 9 DOMAINS CERTIFIED.**

**Quality gates:** zero code · zero schema work · zero repairs · probes
rollback-wrapped (post-probe convergence + verify_all prove zero residue) ·
PRIMARY strictly read-only (sentinel EXACT before and after) · world torn down
· battery baseline **1878/1878 stands** (no code) · docs-sync same session
(this log + campaign memory).

⏸ Next: **RCP-6 (Testing Certification)** — owner-gated.

---

## RCP-6 — Testing Certification — ✅ EVIDENCE COMPLETE 2026-07-19 (main-thread; zero code, ZERO new tests; battery re-run at wave close per program §3b)

### 6.0 Method

Static suite-collection census (`runner.build_suite(...).countTestCases()` —
exact collected counts, no DB) + FULL live battery re-run (the 4-group canon,
sequential fresh-DB) + on-disk anchor verification for every RCP-2 feature row
+ pin/golden/perf inventories. **Instrument note (disclosed):** the live run's
per-group `tail -3` clipped Django's "Ran N tests" lines — counts are proven by
the static collection (exact) and greenness by the four per-group `OK`s + exit
code 0; arithmetic below.

### 6.1 Test Inventory Report

- **Battery canon (the documented law, followed):** 4 groups, SEQUENTIAL,
  FRESH-DB each — G1 10-app (`accounts core raw_materials production tracking
  expense storefront inventory machines bod`) · G2 `patterns_ai` · G3 `devseed`
  · G4 `verification`. Never `--parallel` (patterns_ai flakes), never
  `--keepdb` (TransactionTestCase truncates migration-seeded Roles) — both
  documented in DEPLOYMENT_BACKLOG #4.
- **Collected counts (static, exact): G1 = 1,132 · G2 = 528 · G3 = 140 ·
  G4 = 78 → Σ 1,878 ≡ the RCP-1A baseline arithmetic (1125+7 chain).**
- **189 test files across 13 apps**: production 70 · patterns_ai 51 · expense
  22 · devseed 13 · raw_materials 8 · verification 7 · bod 5 · tracking 4 ·
  accounts/core/storefront/inventory 2 each · machines 1.
- Suite ownership: app suites own domain behavior · devseed owns
  seeder/goldens/knowledge-guards · verification owns the engine (incl.
  polarity + purity + production-subset) · patterns_ai owns the pattern pack.

### 6.2 Coverage Verification Report (vs the RCP-2 40-feature inventory)

Every feature row's named test evidence verified ON DISK and inside the
battery: 19 anchor modules/classes probed — `RolePermissionCurationTests` /
`SidebarAccessSaveTests` / `AccessControlHubTests` (inventory) ·
`test_s4_reopen_guard` · `test_s4_pool` · `test_a360_overview` ·
`test_barcode_generation_workflow` · `test_queue_batching` ·
`test_v2_3_guards` · `test_r7_fnf` · `test_r4_monthly_basis` ·
`test_r5_factory_expense` · `test_expense_generation` · `test_material_spend`
· `test_golden_journeys` · `test_worker_role_certification` ·
`test_adda_settlement_service` · `test_rmx_certification` ·
`test_c1_hardening` — **19/19 exist** (one pointer note: `test_c1_hardening`
lives in production/tests, not raw_materials — RCP-2 row cited the test name
correctly, path implied loosely). Second coverage layer: the verification
engine's per-feature worlds (10 worlds / 74 checks at RCP-2; **verify_all
203/203 at RCP-5**). **Coverage method = feature→suite traceability + engine
worlds, NOT line-coverage tooling** (no coverage.py percentage exists —
recorded honestly, TST-R5).

### 6.3 Regression Protection Report (pin inventory + rationale)

| Pin | Home | Protects |
|---|---|---|
| Golden journeys ₹344.25 / ₹801.00 / ₹633.00 | devseed `test_golden_journeys` (+ idempotency test) | the three settled journeys REPLAYED through real services, exact-decimal |
| Golden ₹225 | **historical evidence** (S3-era receipts); scenario `regression-settlement-225` NON-executable by owner ruling (spec §12 A1) and **that refusal itself is pinned** (`test_guard`:126–135); byte-exact settlement asserts live in `test_adda_settlement_service` (240.00/90.00/30.00/135.00/0.00) | provenance honesty — the ₹225 world is history, not a seedable fixture |
| Queue batching byte-identity | `test_batched_queue_equals_per_adda_funnel_recomputation` + volume-independent query pin | OI-C1 35→6q rewrite can never drift from the per-adda funnel |
| One-shot barcode | `test_generate_one_shot_refuses_second_call` + wipe-rule tests | ADR-0004/0010 identity permanence |
| Open/closed stage registry | `test_open_closed_proof` + per-handler suites + `test_stage_registry` | handler dispatch stays extension-safe |
| Era/ledger armor | `test_v2_3_guards` · `test_reopen_voids_pay` · `test_s5_recon_block` · `test_s4_reopen_guard` · 8 legacy files pin the `LEDGER_CREDIT_AT_ALLOCATION` lever | settlement-money armor + ADR-0007 both-direction safety |
| Foundation purity | `FoundationPurityTests` (core) · devseed purity/money pins · verification purity/polarity suites | ADR-0001/0002 + seeder single-writer + engine read-only |
| Worker-permission certification | `test_worker_role_certification` | the 9-app V1.1 worker model |

### 6.4 Deterministic Execution Report

- **This wave's live re-run: 4/4 groups OK, exit 0 → BATTERY 1,878/1,878
  GREEN** (fresh DBs created + destroyed per group — `Destroying test
  database` ×4 in the transcript).
- Seed determinism consumed, not repeated: RCP-4 (idempotent re-seed ·
  verify_factory body_hash byte-identical ×2) + RCP-5 (21× re-seed created=0 ·
  verify_all 203/203) + the golden-journey idempotency test inside G3.
- Sequential fresh-DB law respected (the two documented flake modes —
  parallel patterns_ai · keepdb Role truncation — are AVOIDED by canon, not
  fixed; test-infra debt recorded TST-R3).

### 6.5 Performance Verification Report

**12 `assertNumQueries` pins, every one a named constant with in-file
rationale:** A360 overview **80** · costing dashboard **16** (11→16 conscious
at RMX-D) · adda list **8** · bulk snapshot **5** (×2 call-sites) · worker
dashboard **22** (16→22, C-2 freeze-closeout documented) · management
dashboard **26** (21→26, R1/R5 documented) · permission cache **1**
(second call cached) · settlement perf **2/0** · settlement queue **6/6**
(volume-independent — the batching proof). Query-count pins guard N+1
regressions; **latency/load is NOT covered by any pin** (RR-7 → manual
register M-5, RCP-8 observation).

### 6.6 Browser & Integration Report (consumed — never repeated)

RCP-2: live 400-request identity×URL census (0 errors) + 48 captures at
360/768/1280 + verify_factory 19/19 + 10 feature worlds live · RCP-3: live
auth/authz/escalation probes · RCP-4: RC-9 nine ₹-surface families reconciled
live · RCP-5: verify_all 203/203 on the 21-world estate. Integration-grade
browser evidence exists for every certified dimension; captures are
session-scoped (PI-2 pending ratification) — the textual evidence lives in
this log's wave sections.

### 6.7 Manual Verification Register (the honest not-automated list)

| Id | Area | Status |
|---|---|---|
| M-1 | C-4 strict-C3 transitional behavior | deferred to OWNER manual testing (frozen-foundation ruling) |
| M-2 | 3-Patti stage-trio config pass | owner action (B-F2/RR-12); **note: RCP-5 observed the blocking dev Addas (…011/013/014/015) already torn down ⇒ likely unblocked** |
| M-3 | Console-error / client-side JS capture | not instrumented (B-F4/S-R2 method boundary) |
| M-4 | Rate-limit thresholds under real load | policy unit-pinned; never load-fired (S-R3) |
| M-5 | Latency/load testing | absent by design — pins are query-count (RR-7 → RCP-8) |
| M-6 | Enforcement-flag live enables (allocation-bound · settlement-recon) | flag behaviors test-covered both states; live enable = post-deploy soak runbook (S5) |
| M-7 | Owner acceptance walks (PDD owner-cert phases) | campaign record: owner-certified phases 0–17; future features re-enter via the RC walk |

### 6.8 Testing Risk Register

| Id | Item | Class |
|---|---|---|
| TST-R1 | Live-run count lines clipped by the capture command — counts proven by static collection + per-group OK + exit 0 (arithmetic §6.1) | disclosed (method, not product) |
| TST-R2 | ₹225 golden is historical-only (non-executable scenario BY RULING; refusal pinned) — executable golden set = the three journeys | by design (recorded; provenance honest) |
| TST-R3 | patterns_ai parallel-unsafe + keepdb Role-truncation — battery canon avoids both; per-class media isolation fix deferred (DEPLOYMENT_BACKLOG #4) | acceptable (test-infra debt, canon documented) |
| TST-R4 | No latency/load coverage (query-count pins only) | acceptable → RCP-8 operational risk |
| TST-R5 | No line-coverage percentage tooling — coverage claim = feature→suite traceability + engine worlds, stated as such | acceptable (method honesty) |

### 6.9 TESTING CERTIFICATE

| Domain | Verdict |
|---|---|
| Test inventory (1,878 collected exact · 189 files · 4-group canon · ownership) | **CERTIFIED** |
| Feature coverage (40/40 features → on-disk suites + engine worlds) | **CERTIFIED** |
| Golden journeys (3 executable service-replayed + idempotent; ₹225 provenance pinned) | **CERTIFIED** |
| Regression protection (pin inventory §6.3, every pin named + rationaled) | **CERTIFIED** |
| Deterministic execution (green re-run · fresh-DB law · seed/engine determinism consumed) | **CERTIFIED** |
| Performance verification (12 named query pins; latency gap recorded, not hidden) | **CERTIFIED** |
| Browser & integration evidence (consumed across RCP-2..5, complete per dimension) | **CERTIFIED** |
| Manual verification register (M-1..M-7 enumerated — nothing silently assumed automated) | **CERTIFIED** |

**TESTING: ALL 8 DOMAINS CERTIFIED. BATTERY 1,878/1,878 GREEN — re-proven at
wave close (program §3b's own mandated activity; zero new tests, zero code).**

**Quality gates:** zero code · zero new tests · zero refactoring · evidence
only · counts exact by static collection · baseline unchanged · docs-sync same
session (this log + campaign memory).

⏸ Next: **RCP-7 (Documentation Certification)** — owner-gated.

---

## RCP-7 — Documentation Certification — ✅ EVIDENCE COMPLETE 2026-07-19 (main-thread; zero code; **CONSUME Phase 18, never repeat FFD** — program §3b law honored; zero doc rewrites: the two live-doc findings are REGISTERED, not repaired)

### 7.0 Method

The three §3b activities executed + the owner's stale-reference hunt: (1)
`knowledge_sync --deep` re-run · (2) graph fixed-point re-check (live rebuild +
validator) · (3) FFD-D-style certificate-consistency walk on ONE more sample
phase (Phase 16 MEE) · (4) targeted greps for every RCP-2A-removed
route/view/form + retired services + renamed terms across the ACTIVE doc tree
(docs/archive excluded; append-only receipts and campaign status/history
classified as legitimate historical record, not drift).

### 7.1 Documentation Inventory Report

- **Estate: 953 active docs** (graph census — the RCP-2A anchor figure, still
  exact) · **11 active ADRs** (docs/adr count ≡ graph census ≡ RCP-1 matrix) ·
  **13/13 apps carry BOTH `config/<app>/README.md` AND `docs/apps/<app>/GUIDE.md`**
  (accounts core raw_materials production tracking expense machines storefront
  bod patterns_ai devseed verification inventory).
- Release/certification set present and current: `RELEASE_CERTIFICATION_PROGRAM.md`
  (ratified structure) · `RELEASE_CERTIFICATION_LOG.md` (this log — waves
  RCP-0..7 appended, closed sections untouched) · `DOCUMENTATION_INDEX.md` ·
  `DEPLOYMENT_CAMPAIGN_STATUS.md` (resume anchor) · frozen specs (PDD v1.0 ·
  MANUFACTURING_V1_FREEZE · DOC_STANDARDS v1 · dataset spec frozen-v1 + A1–A4).

### 7.2 Accuracy Verification Report (the doc≡system proof)

- **`knowledge_sync --deep`: BLOCKER=0 / WARN=2 — EXACTLY the standing
  accepted pair** (d2 doc-islands note · d6 CLAUDE.md frontmatter), INFO=2,
  23 detectors, 8 domains, body_hash `622882e75da768e7…`. The certified
  drift-detector finds the estate synchronized with the code as it stands
  AFTER RCP-1A/2A.
- **Stale-reference hunt (all 11 RCP-2A-removed names + retired services +
  renamed terms):** every hit classified main-thread. Legitimate historical
  record: `AUDIT_SYSTEM_MAP.md` (type: receipt, append-only audit evidence) ·
  `PRODUCTION_AUDIT_STATUS.md` (closed baseline) · `DEPLOYMENT_CAMPAIGN_STATUS.md`
  + production GUIDE (they RECORD the removals) · WORKER_ROLE_CERTIFICATION
  ("historical, inert") · ADR-0003 ("renamed from karigar") · PDD §389
  ("karigar" as domain noun in a FROZEN doc — glossary vocabulary, not a role
  reference). **Two live-doc findings registered (§7.6): DOC-F1 · DOC-F2.**
  `update_layering_roll_entry` doc references = CORRECT (the service survived
  RCP-2A; only the dead view import was removed).
- RCP-wave changes reflected where they should be: RCP-1A (inventory GUIDE
  sidebar_service row · expense GUIDE/README chokepoint rows · PA-06-1
  comment corrected at source — all done in-wave, re-confirmed by today's
  sweep) · RCP-2A (URL_ATLAS counts · COVERAGE_REPORT recount · GUIDE removal
  banner — in-wave, sweep-clean) · RCP-3..6 outcomes live in THIS log by
  design (the certification record's canonical home).

### 7.3 Cross-reference Integrity Report

- **Graph fixed-point re-check: LIVE REBUILD BYTE-IDENTICAL** — builder re-run
  produced `content_hash sha256:5d159ece1df0…` with zero git diff (the RCP-2A
  anchor held through four appended log waves); **validator: ALL INVARIANTS
  PASS — GRAPH CERTIFIED AS BUILT** (1,967 nodes · 659 edges · absence report
  9 loud-not-silent classes unchanged).
- Link integrity consumed from Phase 18 (FFD-E: 228 refs, 0 broken) and
  re-guarded by today's sweep (BLOCKER=0). Doc-islands WARN = the standing
  accepted non-fatal note (Phase-9 cards are the designed resolution).

### 7.4 ADR/PDD Consistency Report

- **ADRs: 11 active ≡ RCP-1's compliance matrix ≡ graph census.** Zero
  violations found at RCP-1 (evidence consumed); RCP-4 re-proved 0009/0011
  live; RCP-5 re-proved 0004/0010 identity laws (one-shot pins · never-reused
  codes) and 0011's DB CHECK by negative probe. Known recorded drift stands
  unchanged: ADR-0004 body's "deferred" pointer note (RCP-1 §1.2) ·
  pattern-pack DRAFT stamps (honest flags).
- **PDD v1.0 FROZEN + amendments register current: entries verified through
  7 (MEE charter, cites MONTHLY_EXPENSE_ENGINE_LOG §0.12/§MEE-A) and 8 (RMX
  A+B, Material Spend window)** — the two campaign-era product charters both
  recorded via change-control, matching the shipped features certified at
  RCP-2 (#36, #37).

### 7.5 Operational & Release Documentation Report

- Runbooks exist and are current-pointing: `deploy/README.md` ·
  `ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md` (flags OFF→soak→enable — flags
  still OFF, matching base.py defaults verified at RCP-1) · P19 contract
  (`PHASE_19_DEPLOYMENT_DOCUMENTATION.md`). Their deep verification against a
  real target = RCP-8's job (RR-3), not claimed here.
- Release documentation: program + log + scorecard template §3d ready for
  RCP-9; campaign status anchor updated through the current wave; **DAT-R1
  (global-migrate-after-targeted-reverse) recorded at RCP-5 as P19 runbook
  input — handoff noted for RCP-8.**

### 7.6 Certificate-Consistency Spot-Walk (sample: Phase 16 MEE — §3b activity 3)

All chain links resolve: PDD amendment register **entry 7** (:83, owner-quote
+ log citation) → contract `PHASE_16_MONTHLY_EXPENSE_ENGINE.md` (index row
:106) → evidence log `MONTHLY_EXPENSE_ENGINE_LOG.md` with **COMPLETION
CERTIFICATE §E.8** (:1062) → expense README + GUIDE engine rows (3 refs each)
→ index row :97 → live routes (`/expense/templates/` · `/generate/` in
urls.py) → tests on disk + green in battery (test_expense_generation 21 +
test_expense_templates 14) → migration 0015 (reverse-re-proven at RCP-5) →
feature world `feature-monthly-expense` (7/7 at RCP-4 · inside verify_all 203
at RCP-5) → RCP-2 feature #36 CERTIFIED. **Walk PASSED — documentation, code,
tests, data world, and certificates describe the same system.**

### 7.7 Documentation Risk Register

| Id | Item | Class |
|---|---|---|
| DOC-F1 | `docs/production/LAYERING_STAGE.md` rows :97 + :250 present removed `LayeringFullCreateAndAttachView` ("+ Add Roll (Full Details)") and `EditRollEntryForm` ("Inline row edit") as CURRENT page UI — the RCP-2A U6 pass updated atlas/coverage/GUIDE but missed this page contract | **MINOR — registered; owner: fix-when-touched or a 2-row RCP-7A edit** |
| DOC-F2 | `docs/production/TRACKING.md` :178 cites "`StockService.log` referenced in CLAUDE.md rule #5" — rule #5 now records StockService as REMOVED 2026-05-19; the analogy's pointer is stale in wording (same family as the ADR-0004 note) | MINOR — registered (pointer staleness) |
| DOC-R3 | Standing accepted WARN pair (CLAUDE.md frontmatter · doc-islands note) + P18 accepted exceptions (RR-10) — unchanged | accepted (recorded) |
| DOC-R4 | Certification outcomes for RCP-3..7 live ONLY in this log (by design — the log IS the record); any future doc claiming per-wave outcomes must cite it | by design (noted) |

### 7.8 DOCUMENTATION CERTIFICATE

| Domain | Verdict |
|---|---|
| Documentation completeness (953 docs · 13/13 README+GUIDE · index · frozen set) | **CERTIFIED** |
| Documentation accuracy (deep sweep BLOCKER=0/WARN=2 accepted · hunt clean except 2 registered MINORs) | **CERTIFIED** (DOC-F1/F2 registered) |
| ADR consistency (11 active · zero violations · known notes unchanged) | **CERTIFIED** |
| PDD consistency (frozen v1.0 · register current through entry 8) | **CERTIFIED** |
| Architecture documentation (graph byte-identical fixed point · validator ALL PASS) | **CERTIFIED** |
| API / service documentation (GUIDE tables · chokepoint docs · RCP-1A rows in place) | **CERTIFIED** |
| Operational runbooks (exist, current-pointing; live-target walk = RCP-8) | **CERTIFIED** (scope boundary recorded) |
| Release documentation (program · log · scorecard-ready · status anchor current) | **CERTIFIED** |
| Cross-reference integrity (0 broken consumed + sweep-guarded · fixed point held) | **CERTIFIED** |

**DOCUMENTATION: ALL 9 DOMAINS CERTIFIED (two MINOR findings registered for
owner disposition — neither blocks: both are single-file wording/row drift
with the correct record already existing elsewhere).**

**Quality gates:** zero code · zero doc rewrites (findings registered, not
repaired — the owner's no-sync rule honored; the graph builder's byte-identical
output left the estate untouched, git-verified) · consume-never-repeat law
honored (FFD evidence cited, not re-derived) · battery baseline 1878/1878
stands (no code) · docs-sync = this log + campaign memory.

⏸ Next: **RCP-8 (Deployment Readiness Certification)** — owner-gated.

---

## RCP-8 — Deployment Readiness Certification — ✅ EVIDENCE COMPLETE 2026-07-19 (main-thread; zero code, zero config edits, zero infrastructure changes, NOTHING deployed; one live backup/restore drill on an allowlisted scratch DB)

### 8.0 Method

Settings/secrets audit (file-level, main-thread) · runbook-vs-implementation
coherence walk (every referenced artifact opened) · **LIVE core restore drill:
`pg_dump -Fc` of PRIMARY (read-only) → `pg_restore --clean --if-exists` into
allowlisted `inventory_seed_scratch_1` → sentinel verification → teardown**
(the runbook's own §Restore forms, executed on the real data) · observability
census · production-safety checks. This is the wave the program pre-loaded
with known gaps (RR-1/2/3) — findings expected and delivered, not hidden.

### 8.1 Deployment Configuration Report

- **Settings isolation:** three-file split (base/local/production).
  `production.py`: **DEBUG=False hard** · full TLS bundle (SSL redirect ·
  secure session+CSRF cookies · NOSNIFF · X-Frame DENY · HSTS 1yr+subdomains+
  preload · `SECURE_PROXY_SSL_HEADER` with the never-expose-gunicorn warning)
  · **fail-fast secrets: `SECRET_KEY` and `REDIS_URL` have NO default —
  missing env = crash, never a silent weak default** (Redis required
  specifically so the auth rate-limiter isn't N×-weakened under multi-worker
  gunicorn) · `CSRF_TRUSTED_ORIGINS` required from env · stdout logging
  (multi-process-safe; platform collects).
- **Debug-leak double wall (documented path):** the Dockerfile bakes
  `DJANGO_SETTINGS_MODULE=config.settings.production` into the image AND
  `.env.example` sets it again. **DEP-F1 (MINOR, registered):** `wsgi.py`/
  `asgi.py`/`manage.py` `setdefault` to `config.settings.local` — on an
  OFF-runbook bare-metal deploy with the env var forgotten, local settings
  (DEBUG=True, ALLOWED_HOSTS=['*']) would boot. Unreachable via the documented
  Docker path; recorded for owner disposition (fail-fast default = a one-line
  P19 candidate, NOT changed this wave).
- **Secrets externalized:** `.env` git-ignored (verified `git check-ignore`) ·
  `.env.example` = 21-var template with blank/CHANGE_ME markers · base.py dev
  SECRET_KEY fallback is explicitly dev-only and unreachable in production
  (no-default override). **Sentry hook exists opt-in** (env `SENTRY_DSN`,
  documented; no DSN today).
- **Structural prod guards:** `devseed` installed ONLY via local.py
  (commands undiscoverable in production — the SEED guard's factor 5) ·
  `verification` app production-PRESENT by design (VER-D1; no models/URLs) —
  `verify_production` runs as the mandated post-deploy gate (P13 certificate
  contract). **All 3 enforcement flags default OFF** (base.py:186/193/200) —
  matches the ENFORCEMENT_ROLLOUT_RUNBOOK deploy-OFF→soak→enable plan.

### 8.2 Operational Readiness Report (runbook ≡ implementation)

`deploy/README.md` (owner-approved direction C: single-VPS Docker Compose,
Caddy auto-TLS → gunicorn → Postgres 16.6 + Redis 7.4, nightly restic→B2/R2)
walked against the artifacts — **every referenced file exists and matches**:
`docker-compose.yml` (exact-pinned images caddy 2.9.1 / postgres 16.6-alpine /
redis 7.4.2-alpine · db+redis healthchecks · `condition: service_healthy` ·
restart policies) · `Dockerfile` (prod settings baked) · `deploy/entrypoint.sh`
(**active wait for HEALTHY db+redis → `migrate --noinput` → collectstatic →
gunicorn** — the documented startup order, and global-migrate satisfies the
RCP-5 DAT-R1 rule by construction) · `deploy/deploy.sh` (**pre-deploy dump
FIRST** → ff-only pull → build → up → prune) · `deploy/backup.sh` (nightly
pg_dump+media → restic, retention 7d/4w/6m, weekly `restic check`) ·
`deploy/Caddyfile` · `.env.example`. First-deploy checklist (11 steps incl.
firewall, DNS-before-TLS, password-manager .env custody, smoke tests, **"run
the restore drill once before handing out worker credentials"**) · shutdown/
update/rollback procedures present. **Operational ownership: single
owner-operator (RR-8) — defined, and recorded as the bus-factor-1 risk.**

### 8.3 Backup & Recovery Report

- **Strategy (documented):** nightly `pg_dump -Fc` + `/media` → restic →
  offsite B2/R2; RPO 24h; retention 7/4/6; weekly `restic check`; 3 newest
  dumps kept locally; extra pre-deploy dump on every deploy; disaster-recovery
  pair = password-manager `.env` + restic repo; **from-NOTHING restore
  procedure** (6 steps) with a monthly re-drill instruction.
- **CORE DRILL EXECUTED THIS WAVE (real data):** `pg_dump -Fc` of PRIMARY
  (734,265 bytes, rc=0, read-only) → fresh allowlisted scratch →
  `pg_restore --clean --if-exists` rc=0 → **restored copy sentinel-EXACT:
  ledger 170 / Σ₹10,880.25 · users 48 · ADST 9 · FE 4 · addas 18 · 0 unapplied
  migrations** → scratch dropped, dump deleted. The data-recovery path is
  PROVEN with the runbook's own commands on the actual database.
- Boundary (recorded): the offsite restic leg (B2/R2 credentials, network
  restore) is config-time and unproven until a real target exists → P19
  first-deploy step 10-11 IS that proof.

### 8.4 Rollback Verification Report

Three documented rollback classes, each anchored to proven mechanics: (1)
**bad code** → checkout previous tag + redeploy (ff-only history; infra files
git-versioned) · (2) **bad migration** → restore `predeploy-*.dump` (the exact
`pg_restore` path proven live in §8.3) + code rollback; targeted-reverse
mechanics additionally proven at RCP-5 (expense 0015 · production 0042/0043 ·
DAT-R1 global-migrate rule — now satisfied automatically by the entrypoint) ·
(3) **settlement-era lever** → `LEDGER_CREDIT_AT_ALLOCATION=True` env restart,
no schema change, cross-era double-credit guard both directions (ADR-0007,
test-pinned, RCP-4-verified). Enforcement flags likewise env-reversible.

### 8.5 Monitoring & Observability Report (the honest gap census — RR-2)

| Layer | State |
|---|---|
| Structured app logging | ✅ request-id formatted, security logger separate, stdout in prod (multi-process-safe) |
| Security-event logging | ✅ `accounts.security` on every auth endpoint (RCP-3 §3.7); money/permission mutations carry PERSISTED audit rows — investigations don't depend on logs (P-3) |
| Error aggregation | ⚠️ Sentry hook EXISTS, opt-in, NOT configured (no DSN, sdk not installed — documented) |
| App health endpoint | ❌ none (`/healthz` absent; compose healthchecks cover db+redis only; app liveness = restart policy + Caddy 502s) |
| Uptime/alerting | ❌ none defined |
| Metrics/dashboards | ❌ none defined |
| Post-deploy correctness gate | ✅ `verify_production` (engine 1.0.0, P13-certified, mandated) |

**Verdict: BLOCKED — monitoring/alerting posture is undefined beyond logging
+ the correctness gate.** Remediation menu for the owner at/before P19 (all
small): set `SENTRY_DSN` + add sdk (hook ready) · add a trivial `/healthz`
route + compose app-healthcheck · external uptime probe on `/` · platform
log-based alerts. Program pre-classified this gap critical (RR-2); the
deployment rule (§6: zero CRITICAL open) makes its disposition an explicit
owner decision before RCP-9 GO.

### 8.6 Production Safety (special-attention checklist)

production settings isolated ✅ · debug cannot leak via the documented path ✅
(DEP-F1 minor for off-path) · secrets externalized ✅ · migration order
documented + automated (entrypoint global migrate; DAT-R1) ✅ · rollback
procedures exist ✅ (+ drilled core) · backup/restore procedures exist ✅
(+ drilled core) · logging covers operational diagnosis ✅ (request-id +
security + persisted audit rows) · health checks: db/redis ✅, app ❌ (§8.5) ·
deployment checklist complete ✅ (11-step first deploy + update + rollback +
DR) · operational ownership defined ✅ (owner-operator; bus-factor-1 recorded)
· **no certification wave introduced undocumented deployment changes ✅** —
tree at 602 porcelain entries, every code delta this program made is logged in
§RCP-1A/§RCP-2A (waves 3–8: zero code); deploy/ untouched since its
owner-approved state; **RR-1 (whole campaign body uncommitted, HEAD
`49404001`) remains the HEADLINE operational risk — owner snapshot/commit
action, standing since P9.**

### 8.7 Deployment Risk Register

| Id | Item | Class |
|---|---|---|
| DEP-R1 | **Uncommitted campaign tree (602 entries; disk failure loses months)** — snapshot refresh overdue; commit gate = Phase 22 by owner policy | **CRITICAL (operational) — owner action NOW (carried RR-1)** |
| DEP-R2 | Monitoring/alerting undefined (§8.5) — error aggregation off, no health endpoint/uptime/alerts | **BLOCKED domain — owner disposition before RCP-9 (carried RR-2); remediation menu documented** |
| DEP-R3 | Full-stack runbook walk on a real VPS never performed (Docker/Caddy-TLS/restic-offsite legs) — core restore leg NOW proven; the remainder = P19 first-deploy steps themselves | acceptable (carried RR-3 → P19) |
| DEP-F1 | wsgi/asgi/manage `setdefault` → local settings (off-runbook bare-metal debug-leak vector; double-walled on the Docker path) | MINOR — registered (one-line P19 candidate) |
| DEP-R4 | restic installed at backup-container boot (one unpinned package) — the runbook's own accepted tradeoff | accepted (recorded) |
| DEP-R5 | Dev-data import decision at first deploy (runbook step 8: start CLEAN vs import dev dump; ties DAT-R3 residue: 33 dev.* users · 4 DEV addas · ADST-0011 ₹0 draft) | owner decision at P19/P20 |
| DEP-R6 | Bus factor 1 (single owner-operator) | deferred/accepted (RR-8 → RCP-9 note) |

### 8.8 DEPLOYMENT READINESS CERTIFICATE

| Domain | Verdict |
|---|---|
| Deployment readiness (artifact chain complete, coherent, pinned) | **CERTIFIED** |
| Environment configuration (isolation · fail-fast secrets · flags OFF) | **CERTIFIED** (DEP-F1 registered) |
| Operational runbooks (complete · current · match implementation) | **CERTIFIED** (live-VPS walk = P19, recorded) |
| Backup & restore strategy (documented + CORE DRILL PROVEN on real data) | **CERTIFIED** (offsite leg = P19 boundary) |
| Rollback readiness (3 classes documented; restore path + reverse-migrations + levers all proven) | **CERTIFIED** |
| Monitoring & observability | **BLOCKED — owner disposition required (§8.5 menu; carried RR-2)** |
| Logging (structured + security + persisted audit tier) | **CERTIFIED** |
| Disaster recovery (from-nothing procedure + drilled core + monthly re-drill rule) | **CERTIFIED** |
| Production safety (checklist §8.6 — all ✅ except the two registered items) | **CERTIFIED** (RR-1 headline carried) |

**DEPLOYMENT READINESS: 8/9 DOMAINS CERTIFIED · 1 BLOCKED (monitoring &
observability — pre-known RR-2, delivered as the honest census with a small
remediation menu). Plus one CRITICAL-operational owner action outside the
software: commit/snapshot the tree (RR-1).** Per program §6, P20 remains
FORBIDDEN until every wave is certified and zero CRITICAL items stand open —
both open items are the owner's next calls, not code work.

**Quality gates:** zero code · zero config/infra edits · nothing deployed ·
PRIMARY read-only (dump = read; drill on allowlisted scratch; dump file
deleted after) · battery baseline 1878/1878 stands (no code) · docs-sync =
this log + campaign memory.

⏸ Next: **RCP-9 (Release Decision)** — owner-gated; requires owner disposition
of DEP-R1 (tree) + DEP-R2 (monitoring) first or as part of the RCP-9 review.

---

## RCP-9 — RELEASE DECISION — ✅ COMPLETE 2026-07-19 (governance wave; consume-only — zero new investigation, zero code, zero estate edits; every conclusion cites prior wave evidence; decision main-thread)

### 9.0 Governance Review (completeness + internal consistency)

- **Every wave complete:** RCP-0 · 1 · 1A · 2 · 2A · 3 · 4 · 5 · 6 · 7 · 8 —
  eleven sections in this log, each closed with its certificate and quality
  gates. One wave per owner authorization, STOP honored after each (U3).
- **Every MAJOR dispositioned:** F1 (Law-4 sidebar write) → REPAIRED +
  test-pinned (§RCP-1A, "MAJOR: none open") · B-F1 (5 orphan routes) →
  REMOVED + re-verified (§RCP-2A, "B-F1 CLOSED"). **No unresolved MAJOR
  findings exist anywhere in the program record.**
- **Certificates internally consistent:** Architecture ALL 7 (§1A.3) ·
  Business ALL 6 (§2A.4) · Security ALL 7 (§3.9) · Financial ALL 9 (§4.8) ·
  Data ALL 9 (§5.9) · Testing ALL 8 (§6.9) · Documentation ALL 9 (§7.8) ·
  Deployment 8/9 + 1 BLOCKED (§8.8). Documentation≡certificates agreement
  proven at RCP-7 (deep sweep BLOCKER=0 · graph byte-identical fixed point ·
  Phase-16 spot-walk 9/9 links).
- **Baseline integrity across the program:** battery 1,878/1,878 GREEN
  (re-proven at RCP-6 close; counts exact) · PRIMARY money sentinel EXACT at
  every wave that touched a database (170/Σ₹10,880.25, last recount §8.3's
  restored-copy drill) · graph fixed point `5d159ece1df0` held live (§7.3).

### 9.1 FINAL RELEASE SCORECARD (program §3d, filled here)

| Wave | Dimension | Status | Evidence (log §) | Date | Owner acceptance |
|---|---|---|---|---|---|
| RCP-1 | Architecture | **CERTIFIED** | §RCP-1 + §RCP-1A | 2026-07-18 | ACCEPTED (RCP-2 auth) |
| RCP-2 | Business | **CERTIFIED** | §RCP-2 + §RCP-2A | 2026-07-18 | ACCEPTED (RCP-3 auth) |
| RCP-3 | Security | **CERTIFIED** | §RCP-3 | 2026-07-18 | ACCEPTED (RCP-4 auth) |
| RCP-4 | Financial | **CERTIFIED** | §RCP-4 | 2026-07-19 | ACCEPTED (RCP-5 auth) |
| RCP-5 | Data | **CERTIFIED** | §RCP-5 | 2026-07-19 | ACCEPTED (RCP-6 auth) |
| RCP-6 | Testing | **CERTIFIED** | §RCP-6 | 2026-07-19 | ACCEPTED (RCP-7 auth) |
| RCP-7 | Documentation | **CERTIFIED** | §RCP-7 | 2026-07-19 | ACCEPTED (RCP-8 auth) |
| RCP-8 | Deployment readiness | **CERTIFIED-WITH-ONE-BLOCKED-DOMAIN** (monitoring) | §RCP-8 | 2026-07-19 | ACCEPTED (RCP-9 auth) |
| **RCP-9** | **RELEASE DECISION** | **GO WITH ACCEPTED RISKS** (conditional — §9.6) | §RCP-9 | 2026-07-19 | ⏸ owner ratifies |

### 9.2 FINAL CERTIFICATION MATRIX

| Dimension | Verdict | Load-bearing evidence |
|---|---|---|
| Architecture | **CERTIFIED (7/7)** | no cycles · 11/11 ADRs compliant · money boundary airtight · F1 repaired |
| Business | **CERTIFIED (6/6)** | 40/40 features · 400-req live census 0 errors · goldens live · 0 orphans |
| Security | **CERTIFIED (7/7)** | 7 escalation attempts walled · 4-layer wall live · full auditability |
| Financial | **CERTIFIED (9/9)** | four-way ledger≡settlement identity exact · no duplicate money · goldens byte-exact |
| Data | **CERTIFIED (9/9)** | migrate-from-zero · 88 constraints live · 10/10 probes refused · append-only 0 edits |
| Testing | **CERTIFIED (8/8)** | battery 1,878/1,878 re-proven · pins inventoried · manual register honest |
| Documentation | **CERTIFIED (9/9)** | sweep BLOCKER=0 · graph byte-identical · docs≡system spot-walk passed |
| Deployment | **CERTIFIED 8/9 · monitoring BLOCKED** | runbook≡implementation · restore drill PROVEN on real data · RR-2 census delivered |
| **Overall release** | **GO WITH ACCEPTED RISKS — conditional (§9.6)** | this section |

### 9.3 FINAL RELEASE RISK REGISTER (consolidated — every remaining item)

| Id | Risk | Severity | Status | Owner | Recommended disposition |
|---|---|---|---|---|---|
| DEP-R1 (RR-1) | Entire campaign body uncommitted (602 porcelain entries; HEAD `49404001`) | **CRITICAL (operational)** | OPEN | Owner | **MUST COMPLETE BEFORE RELEASE — evidence-based, not precautionary: the documented deploy path is `git clone` + `deploy.sh` `git pull --ff-only` (deploy/README step 4; deploy.sh:14), so uncommitted work literally cannot reach a production VPS; rollback class 1 ("checkout previous tag") requires committed history; and a single disk failure erases months of certified work. Commit/snapshot precedes P20 regardless of where the ceremonial Phase-22 commit sits.** |
| DEP-R2 (RR-2) | Monitoring/alerting undefined (no error aggregation, health endpoint, uptime, alerts) | HIGH (gap) | BLOCKED domain | Owner | **Complete-at-P19 (preferred) or accept-for-soak with a dated commitment.** Menu is small and config-level (§8.5: SENTRY_DSN — hook already built · /healthz + app healthcheck · uptime probe · log alerts). Compensating controls certified: structured+security logging, persisted audit rows (P-3), mandatory verify_production gate, single-operator watching own factory. |
| DEP-F1 | wsgi/asgi/manage default to local settings (off-runbook bare-metal debug-leak vector) | MINOR | REGISTERED | Owner | ACCEPTABLE RISK (Docker path double-walled §8.1); one-line fail-fast change = P19 candidate |
| DEP-R3 (RR-3) | Full-stack runbook walk (Caddy TLS · restic offsite) never run vs a real target | MEDIUM | OPEN by design | Owner (P19) | ACCEPTABLE — P19 first-deploy steps 1–11 ARE the walk; core restore leg pre-proven (§8.3) |
| DEP-R5 (RR-5/DAT-R3) | Dev residue on PRIMARY (33 dev.* users · 4 DEV addas · ADST-0011 ₹0 draft) + start-CLEAN-vs-import decision | LOW | OPEN | Owner (P19/P20) | Decide at first deploy (runbook step 8); dev Addas …011/013/014/015 already torn down (§5.7) |
| S-R1 (RR-4) | Accountant role has no seeded identity to certify (reaches no page — nothing reachable-and-wrong) | LOW | CARRIED | Owner | ACCEPTABLE — rule the role's future at leisure; not release-relevant |
| M-2 (RR-12/B-F2) | 3-Patti stage-trio config pass outstanding | LOW | LIKELY UNBLOCKED (§5.7 teardown observed) | Owner | Schedule as owner manual pass; non-blocking |
| DOC-F1/DOC-F2 | Two single-file doc drifts (LAYERING_STAGE rows · TRACKING pointer) | MINOR | REGISTERED | Owner | Fix-when-touched or 2-row RCP-7A; correct record exists elsewhere |
| TST-R3/R4/R5 | patterns_ai sequential-only · no latency tests · no line-coverage tooling | MINOR | RECORDED | Owner | ACCEPTABLE — canon documented; latency = post-deploy observation |
| RR-6 | Enforcement flags default OFF | BY DESIGN | ON TRACK | Owner | Follow ENFORCEMENT_ROLLOUT_RUNBOOK (deploy-OFF→soak→enable) |
| RR-8 (DEP-R6) | Bus factor 1 | ACCEPTED | STANDING | Owner | Accept (single-owner business); mitigations = runbook + password-manager custody + offsite backups |
| RR-9 | S6 `reported_quantity` retirement deferred (irreversible) | DEFERRED | BY DESIGN | Owner | Post-deploy soak-gated, unchanged |
| Misc register | Arch minors F2/F4–F8 · FIN-R1..R4 · DAT-R1..R5 (DAT-R1 rule absorbed by entrypoint global-migrate) · by-design unreferenced URL names (media×2/styleguide/2 legacy aliases) · P18 accepted exceptions (RR-10) · INFO residue #6–#14 (RR-11) | MINOR/INFO | RECORDED | — | Blanket-accept with this certificate (each individually evidenced in its wave section) |

### 9.4 BLOCKING ISSUES REGISTER

| # | Item | Why it blocks | Unblock action |
|---|---|---|---|
| 1 | **DEP-R1 — uncommitted campaign tree** | The certified system cannot ride its own documented deploy path uncommitted; rollback anchor (tag) cannot exist; existential data-loss exposure | Owner commits/snapshots the tree (P22 ceremony may still formalize; a safety commit/branch/snapshot suffices to unblock) |

**No other blocking issues.** DEP-R2 is a blocked *domain* requiring owner
disposition, not an absolute release blocker — compensating controls are
certified and the remediation is config-level (§9.3 row 2). Everything else
in the program record is MINOR, accepted, deferred-by-design, or closed.

### 9.5 RELEASE READINESS ASSESSMENT (three options, each argued)

**OPTION A — GO (unconditional).** Supporting evidence: all eight dimensions
carry certificates; zero unresolved MAJORs; money identity exact; battery
green; restore drill proven. **Fails on evidence:** the program's own §6 rule
(zero CRITICAL open) is violated by DEP-R1, and the monitoring domain stands
BLOCKED. An unconditional GO would contradict the record this program built.
Operational consequence if forced: deploying would require bypassing the
documented deploy path (no commit) with no rollback tag and no alerting —
self-evidently unsafe. **Rejected.**

**OPTION B — GO WITH ACCEPTED RISKS (conditional).** Supporting evidence: the
entire certified substrate (§9.2) + both open items are OWNER ACTIONS, not
software defects — one is a git commit, the other a small config-level
instrumentation menu with certified compensating controls (logging + persisted
audit rows + verify_production gate). Remaining risks after conditions: the
accepted-risk set of §9.3 (all MINOR/deferred, individually evidenced).
Operational consequence: P19 proceeds immediately after the commit; first
deploy doubles as the full-stack runbook walk; flags stay OFF per runbook;
soak window observes with monitoring installed or explicitly accepted.
**Best supported by the evidence.**

**OPTION C — NO GO.** Supporting evidence: strictly reading §6 (a CRITICAL is
open) and treating RR-2 as release-blocking. Consequence: certification
freezes until the owner commits the tree and installs monitoring — but both
actions are hours, not weeks, and NO GO would misrepresent the system itself
(every product dimension is CERTIFIED; the two opens are operational,
owner-owned, and pre-known since RCP-0 seeded RR-1/RR-2). NO GO overweights
items this program always planned to route to the owner at exactly this
point. **Rejected as unnecessarily severe — but it is the automatic fallback
if condition 1 (§9.6) is refused.**

### 9.6 FINAL RECOMMENDATION

## **GO WITH ACCEPTED RISKS**

Conditions (both owner actions, both evidenced above):

1. **HARD (blocking): commit/snapshot the campaign tree before Phase 20.**
   DEP-R1 closes; the deploy path and rollback anchor become real.
2. **REQUIRED DISPOSITION (either branch acceptable): monitoring** — complete
   the §8.5 menu at P19 (preferred; config-level), OR record explicit owner
   acceptance for the soak window with a dated commitment. DEP-R2 closes
   either way.

Accepted-risk set ratified with this decision: every remaining §9.3 row
marked ACCEPTABLE/RECORDED/DEFERRED (each carries its wave evidence).

### 9.7 RELEASE CERTIFICATE

> **RELEASE CERTIFICATE — Kapil Enterprises ERP (Manufacturing V1 + Campaign
> Phases 0–18A) · issued 2026-07-19 at RCP-9 of the ratified Release
> Certification Program.**
>
> All eight certification dimensions are CERTIFIED on objective evidence
> recorded in this log: Architecture 7/7 · Business 6/6 · Security 7/7 ·
> Financial 9/9 · Data 9/9 · Testing 8/8 (battery 1,878/1,878 re-proven) ·
> Documentation 9/9 · Deployment readiness 8/9. Zero MAJOR findings remain
> open. The money boundary is airtight and its identities are byte-exact.
>
> **Verdict: GO WITH ACCEPTED RISKS — NOT unconditional GO**, because (i) the
> certified tree is uncommitted (DEP-R1, CRITICAL-operational: the documented
> deploy path requires committed history — §9.4), and (ii) the monitoring
> domain is BLOCKED pending owner disposition (DEP-R2, with certified
> compensating controls). Upon owner completion of condition 1 and
> disposition of condition 2 (§9.6), **Phase 20 (production deployment) is
> UNLOCKED under program §6**, with the P19 first deploy serving as the
> full-stack runbook walk and `verify_production` as the mandatory
> post-deploy gate. Owner ratification of this certificate completes the
> Release Certification Program.

**Quality gates:** consume-only (zero new investigation — every §9 claim
cites a prior wave section) · zero code/config/doc-estate changes (this
append = the decision record itself) · decision main-thread · battery
baseline 1,878/1,878 stands.

**🏁 RELEASE CERTIFICATION PROGRAM COMPLETE (RCP-0 → RCP-9). ⏸ Owner:
ratify the certificate · execute condition 1 (commit/snapshot) · disposition
condition 2 (monitoring) → then Phase 19.**
