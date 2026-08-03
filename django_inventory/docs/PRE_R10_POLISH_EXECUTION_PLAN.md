---
id: pre-r10-polish-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Pre-R10 Polish — Execution Plan (F-1 · F-2 · F-3 · F-4)

> **STATUS: ✅ IMPLEMENTED 2026-07-05 (owner approved plan + added F-1).
> Gate PASS 821 · golden intact · single-writer gates green · browser E2E on
> fresh 3-PATTI-012.** Results and the two design deltas vs this plan:
>
> - **F-1 (added by owner):** ONE ungated "My Dashboard" MenuItem for every
>   role, canonical url_name `inventory:my_dashboard` (live path unchanged:
>   `/my-dashboard/`); old `dashboard()` view → `dashboard_redirect` (301);
>   both legacy url_names redirect. **Delta:** the legacy url_names stay in the
>   SIDEBAR registry as `hidden=True` entries (a new presentation-only MenuItem
>   flag, skipped before even the super-admin bypass) so the existing
>   SidebarItemRule rows don't trip the P3.4 orphan-rule drift guard — zero DB
>   changes, per the owner's constraint. Owner may delete the two rules via
>   Sidebar Access, then remove the hidden entries.
> - **F-2:** exactly as planned (auto-assign call deleted; D6 guard + rate
>   snapshot retained; WORKERS_ASSIGNED now logged only on explicit assign).
>   E2E: 3-PATTI-012 created with 0 tasks + 3 frozen rate rows.
> - **F-3 delta (found by the new regression test):** the completed stage's own
>   panel is NOT always viewable either — stage completion auto-cancels the
>   completer's unreported task, so the assignment gate can refuse even that.
>   Final design: a **data-free bounce page** (`production:stage-advanced`,
>   `StageAdvancedBounceView` — login-only, no stage data, no gates) that
>   postMessages the parent to reload (iframe) or `location.replace`s to the
>   Adda page (standalone). All 4 embedded COMPLETE sites use
>   `mixins.embedded_advance_redirect`; reopen redirects unchanged.
>   E2E: worker completed layering → landed on the Adda page, no 403.
> - **F-4:** as planned — `eligible_stage_workers(stage_code)` in
>   access_service; all 4 start-forms rewired. E2E: cutting picker 17 → 3
>   masters; deactivated dev.leaver gone from pattern/layering/barcode pickers.
> - Tests: +10 (`test_pre_r10_polish` F-1/F-3/F-4 pins; `test_phase4` re-pinned
>   to empty-roster; `test_unified_tracking` + `test_rbac_matrix` updated for
>   explicit assignment; smoke accepts 301).
>
> Original plan below, kept as the approval record.

> Scope = the three operational-UX findings from
> [END_TO_END_BUSINESS_AUDIT_2026_07_05](END_TO_END_BUSINESS_AUDIT_2026_07_05.md),
> owner-selected 2026-07-05, + owner-added F-1. Appendix A = the ordered
> dashboard single-responsibility review.

## 1) Money-independence verification (done first, as ordered)

Question: can F-2/F-3/F-4 ship without touching settlement, payroll, ledger,
snapshots or calculations? **Yes — verified against code, evidence below.**

| WP | What it touches | What it writes | Money-pipeline contact |
|---|---|---|---|
| WP-1 (F-2) | `adda_service.create_adda` lines 112-132: drop the `set_stage_workers(sr, skilled_pks)` auto-call | `WorkerStageTask` rows are simply NOT created at start (creation of WST was never a money event) | **None.** Rate snapshot (`ensure_stage_role_rates`) stays at SR-create and is per *(stage_record, role)* — worker-independent by design (S1/S2). Earnings freeze happens per contribution at `complete_worker_task`; no contribution can exist without a task, and tasks now only come from the manager roster form → the SAME single writer `set_stage_workers`. Settlement funnel reads contributions, never "who was auto-assigned". |
| WP-2 (F-3) | 6 post-advance redirect sites (`stage_views.py:406,922,1259,1277` · `pattern_stage_views.py:408,577` · `barcode_gen_views.py:255,278` — the embedded `?advanced=1` targets) | Nothing — pure HTTP redirect choice AFTER the service call already committed | **None.** The completes themselves (`complete_layering` / `complete_pattern_stage` / cutting / barcode services) are untouched; only where the browser goes afterwards changes. |
| WP-3 (F-4) | 4 form querysets: `forms/_shared._worker_queryset` (cutting — role-only, no skill/active filter), `_layering_worker_queryset` (already correct), `pattern_stage_views.py:107` (skill, no active), `barcode_gen_views.py:71` (skill, no active) | Nothing — pickers only shape the OPTIONS; chosen ids still validate through the same forms into `set_stage_workers` | **None.** Narrowing options can only *reduce* who gets a task. |

Cross-checks that stay green by construction: golden ₹225 path (no rate/freeze/
funnel code touched) · gates 4/4b/4c single-writer census (no new writer; WP-1
*removes* a call to an existing writer) · snapshots (render-only references
read stage rows, not tasks-at-creation) · ADR-0005/0009/0011 untouched.

One functional consequence to be aware of (intended): **fewer phantom tasks**
⇒ Operations "Pending reports", A360 "workers · open tasks" and worker
dashboards stop counting people who were never going to work that Adda. That
is the point of F-2 — numbers become truthful, no calculation changes.

## 2) Work packages

### WP-1 — Explicit assignment at Adda start (F-2)
- `adda_service.create_adda`: keep Adda + layering `AddaStageRecord` +
  `ensure_stage_role_rates(sr)` exactly as today; **delete** the
  `set_stage_workers(sr, skilled_pks)` call and the now-empty
  `WORKERS_ASSIGNED` history log (log only when workers were actually set —
  i.e. never at create any more).
- **Keep the spec-D6 guard** ("no cutting_master/helper users exist → refuse
  create") — still a sensible dead-end check; `_skilled_user_pks()` stays for it.
- UI already handles the empty state: layering panel shows "No workers
  assigned yet." and the button label flips to **"Start layering"**
  (`_stage_panel_layering.html:98-103`) — the manager assigns explicitly, same
  as Pattern/Cutting/Barcode stages already do. Zero template work expected.
- Docstrings updated (the Phase-4 "spec D1 auto-populate" note becomes
  historical); this partially delivers the roadmap's gated
  "explicit-assignment" backlog row (first stage only — the C3-transitional
  completion-block story is NOT touched).
- Tests: `test_phase4` pins the auto-populate — update to pin the NEW contract
  (create ⇒ SR exists, zero tasks; roster form ⇒ tasks). Sweep the other
  ~25 `create_adda` call sites in tests (census done: test_adda_service,
  task_lifecycle, r1_navigation, r2/r3, unified_tracking, expense views …) —
  most create their own rosters already; any that relied on auto-assign get an
  explicit `set_stage_workers` line in their setup.

### WP-2 — Post-completion redirect never 403s (F-3)
- Root cause (audit, reproduced 3×): embedded completes redirect to the
  **next** stage's panel (`?embedded=1&advanced=1`); `StageViewAccessMixin`
  gates that panel on next-stage skill+assignment, so the completing WORKER
  gets 403 while the completion succeeded.
- Fix: ONE shared helper (in `views/_stage_redirects.py` or `mixins.py`), used
  by all 6 sites: embedded post-advance target = **the completed stage's OWN
  panel** `?embedded=1&advanced=1`.
  - Safe for the completer: `is_worker_assigned` counts non-cancelled tasks —
    their `completed` task passes the gate (verified `adda.py:191-193`).
  - Behavior identical for management: the `advanced=1` postMessage handler
    lives in the SHARED embedded wrapper (`stage_panel_embedded.html:226-234`),
    so the parent Adda page reloads to fresh flow state either way.
  - Non-embedded fallback already redirects to `adda-detail` (worker-viewable,
    PDD D7 My-Work lens) — unchanged.
- Tests: view tests per stage complete as a non-management worker → assert
  302 → own-stage panel (not 403 target); management path asserted unchanged.

### WP-3 — One shared, gate-consistent worker picker (F-4)
- New single source `eligible_stage_workers(stage_code)` in
  `production/services/access_service.py`:
  `User.objects.filter(is_active=True, skills__in=Stage(code).access_by_skill)`
  (+distinct, order by email) — i.e. **exactly the population that
  `user_can_access_stage` will later admit**. Pickers and the access gate can
  never disagree again (the audit's 403s were precisely this disagreement).
- Replace the 4 querysets: `_layering_worker_queryset` (delegates),
  pattern `AssignPatternWorkersForm`, cutting `CuttingStartForm` (+ legacy
  `CuttingForm`), `BarcodeGenStartForm`.
- Intentional behavior changes: **deactivated users disappear everywhere**
  (dev.leaver bug); **cutting narrows to cutting_master holders** (matches its
  access rule — today it offers all 17 users incl. managers/super-admin, and an
  unskilled assignee couldn't even open the workspace); pattern/barcode/
  layering stay master+helper per their Stage access rows. Management stays
  out of pickers (assigns, doesn't self-assign) — unchanged from layering's
  current correct behavior.
- Skill map is DB-driven (`Stage.access_by_skill`), so a future stage's picker
  follows its Access-Control config automatically — open-closed, no per-stage
  picker code.
- Tests: parity test (picker set == users passing `user_can_access_stage`,
  active-only), inactive-excluded test, per-form queryset tests updated.

## 3) Gate + E2E (unchanged bar)
Full suite green (expect ~811 + new; test_phase4 pins rewritten) · golden ₹225
byte-identical · gates 4/4b/4c · perf pins (adda-detail 61 — creation path only,
verify no drift) · REAL-browser E2E on a fresh 3-PATTI Adda: create (⇒ no
tasks) → manager assigns via pickers (only active skill-holders offered) →
worker completes layering → lands back on layering panel with success message
+ parent reload → same check on pattern complete → teardown per test-data rule.
Docs same session: audit doc F-statuses, apps/production GUIDE, KNOWLEDGE_MAP
flow note, roadmap backlog row.

## 4) Non-goals / risks
- NOT in scope: F-1 (dashboard menu dedupe — Appendix A recommendation, owner
  may attach it), F-5 data cleanup, F-6..F-9, anything R10.
- Risk: hidden test reliance on auto-assign (mitigated by census + full gate);
  WP-2 helper must preserve the `advanced=1` contract (pinned by tests);
  WP-3 could hide a legitimately-needed unskilled assignee — impossible today
  anyway (gate would 403 them), so no capability is lost.
- Rollback: three independent, revertable diffs; no migrations anywhere.

Estimate: WP-1 ~1h (mostly tests) · WP-2 ~45m · WP-3 ~45m · E2E+docs ~45m.

---

## Appendix A — Dashboard single-responsibility review (ordered with this plan)

| Surface | URL / owner | Audience | Single responsibility | Verdict |
|---|---|---|---|---|
| Home router | `/app/home/` (`accounts.HomeView`) | all | pure role router: management → Operations, others → My Dashboard. No content. | ✔ clean |
| My Dashboard | `/inventory/my-dashboard/` + twin `/inventory/dashboard/` (same template/context) | everyone (personal) | "what should *I* do now" — my active stages, report-needed badges, my Addas + workspace links, skill KPIs | ✔ role — but **URL/menu twin = F-1**: only super-admin sees both entries (menu bypass at `permission_service.py:453`). Recommend: one MenuItem, twin URL becomes redirect. `is_admin_view` flag is unused today — drop or use, don't keep half. |
| Operations | `/production/` (`AddaDashboardView`) | management landing (workers get non-money subset) | "how is the factory right now" — stalled/pending-reports/active/by-stage + payable/advance digest (digest management-gated, verified `dashboard.py:100-105`; stalled drill-down worker-scoped) | ✔ clean; money leak-safe |
| A360 | Adda detail (mgmt-only ctx) | management | ONE Adda end-to-end (progress, health, workers, money trio, timeline) | ✔ distinct grain (per-Adda); reuses single owners — no second calc path |
| Costing | `/production/costing/` | management | all-Addas money table (std vs settled vs variance) | ✔ distinct grain (Adda table); lens split vs A360 documented in audit §1 |
| Payroll Overview | `/expense/payroll/` | management | per-WORKER money ops (payable, advance, settle, salary link) | ✔ distinct grain (worker table). Its payable total intentionally equals Operations' digest tile — same live ledger sum, single source, two zoom levels; not duplication of logic |
| My Earnings | `/expense/my/` | worker (self-scoped) | personal money: Expected → Earned → Paid + history | ✔ clean (F-8 label nit stays on backlog) |
| Raw Material / Cloth dashboards | `/raw-materials/`, `/raw-materials/cloth/` | production roles | material index (hub; cloth live, future materials) vs cloth Type×Color/location breakup (drill-down) | ✔ hub + drill-down pair, not overlap |
| Barcode Dashboard | `/tracking/` | production roles | traceability/barcode ops | ✔ clean |

**Conclusion:** every dashboard has one defensible job; the grains don't
overlap (personal / factory-pulse / per-Adda / per-worker / stock / trace).
The only true redundancy in the whole family is the **My Dashboard URL+menu
twin (F-1)** — recommend fixing alongside this polish phase or right after.
Two soft notes, no action required: worker My Dashboard lists all active
Addas (links are 403-protected; could be scoped to assigned/skill-relevant
later), and Operations remains the natural home for the R10 "Machines" tile.

### Verification sources
Code reads 2026-07-05: adda_service.py:43-135 · worker_task_service.set_stage_workers ·
stage_views.py:294-355/360-408/916-922 · mixins.py:16-46 · adda.py:191 ·
stage_panel_embedded.html:226-234 · forms/_shared.py:27-43 · forms/layering.py:36 ·
forms/cutting.py:43 · pattern_stage_views.py:100-111 · barcode_gen_views.py:68-84 ·
dashboard.py (production):95-130 · dashboard.py (inventory):216-239 ·
accounts/views.py:236-244 · settings LOGIN_REDIRECT_URL. Confidence: High.
