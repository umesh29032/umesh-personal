---
id: pre-freeze-final-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Pre-Freeze Final Audit — retro-tag · F-11 · Stage-Access sync · foundation review

> **CLOSEOUT STATUS (same day, owner-approved): C-1 ✅ · C-2 ✅ · C-3 ✅
> IMPLEMENTED — gate PASS 827, foundation-purity KEPT (stricter: the
> accounts→production ignore rule is gone), golden intact, browser E2E on
> :8003 (zero blocked iframes on utest's dashboard; Adda tabs =
> iframe/Not-assigned/Restricted; report 403 on revoked-access active task —
> probe cleaned; Team-Members create of a skilled user ⇒ 0 tasks; helper board
> assignment-scoped; 390px no-overflow). C-4 ⏸ deferred by owner (manual
> business testing first). V-1 = documented split (RBAC.md "Visibility vs
> Action capability"); PDD amendment 4 registers the permanent rule. Final
> hidden-behavior sweep ran CLEAN before implementation (0 signals, task
> creation only in the 2 chokepoint functions, no background jobs, no auto
> perm-sync, no remaining event-driven cross-app writes).
> **The operational foundation (R1 → A360 + Pre-R10 Polish + this closeout)
> is hereby FROZEN.** Original audit follows as the decision record.

> Owner-ordered, 2026-07-05, BEFORE the operational-foundation freeze.
> Every claim below verified main-thread (code reads + live browser on the
> owner's own dev server, port 8000, as utest AFTER the owner's real
> Access-Control change).

---

## Part 1 — `sync_layering_workers_for_skill`: removal safety re-verified ✅

The function writes exactly ONE thing: `WorkerStageTask` rows via
`add_stage_worker` (its only business caller — grep census). Surface by
surface:

| Surface | Why removal cannot touch it |
|---|---|
| Earning flow | earnings exist only as `WorkerStageContribution` rows written by `report_contributions` (worker's own act); a bare task has no quantities |
| Expected earnings | frozen per CONTRIBUTION at `complete_worker_task` (rate × good); no contribution → nothing to freeze |
| Settlement | `_settleable_lines` funnel reads contributions on completed tasks; bare/assigned tasks are invisible to it |
| Payroll | live ledger sums (`WorkerLedgerEntry`) — written only at settlement finalize |
| F&F | `fnf_service` blockers = OPEN TASKS (`fnf_service.py:47,65,138`) — retro-tag phantom tasks could **falsely BLOCK** an F&F; removal makes F&F *more* correct, never less |
| Snapshots | render-only references read stage/typed records, never tasks |
| A360 | reads tasks only for worker-board COUNTS — counts become truthful (that was F-2's goal) |
| Roster truth | `set_stage_workers` (manager panel) untouched — becomes the ONLY task writer besides report-flow status flips |

Confirmed unchanged from the [first audit](RETRO_TAG_SYNC_AUDIT_2026_07_05.md):
sole business caller `sync_user_skills` (3 trigger sites, edit-save fires
unconditionally), re-adds workers over manager cancellations
(`add_stage_worker:134-144` — "a prior cancelled task does not block"),
roadmap:212 already sentences it, REMEDIATION P4.1/COUP-5 edge deleted outright.

**Verdict: removal is safe and completes "manager assignment is the only
source of truth". Recommend: REMOVE inside this freeze** (removal plan §5 of
the retro-tag audit; `add_stage_worker` primitive itself can stay as a
documented chokepoint utility or go — recommend keep, docstring updated).
The permanent business rule belongs in the PDD amendments register.

---

## Part 2 — F-11 re-verified: dashboards render workspaces the viewer can never open

Live repro chain (utest, owner's server): dashboard offers
"▸ Open Barcode Generation workspace" accordions → iframe →
`{status: 403, x-frame-options: DENY}` → Chrome paints "localhost refused to
connect". The 403 is CORRECT (gate live, fail-closed); rendering the iframe
at all is the bug.

**The codebase already contains the right pattern** — the Adda page:
`AddaDetailView` computes `stage_access_map(user, stages)` (LIVE access rows)
and the template renders the iframe only `{% if s.has_access %}`, else a
proper "🔒 Restricted" card ([adda_views.py:113-119](../config/production/views/adda_views.py),
[adda_detail.html:700-724](../config/production/templates/production/adda_detail.html)).
Verified live: same utest request shows "Barcode Generation — Restricted" on
the Adda page while the dashboard still offers the workspace.

**Architecture recommendation: keep iframes** (CSS isolation + postMessage
sizing are working design, shared by both surfaces); the flaw is
*unconditional rendering*, not the embed mechanism. Fix = context-level
access filtering (the Adda-page pattern) applied to `user_dashboard`:
- Adda-card CURRENT-stage accordion: render only when
  `access ∩ (assignment for workers)` — else show the compact status line
  only (minimum-info: the pipeline chips already tell the story).
- DONE-stage revisit accordions: same filter.
- No new pages, no SPA, no per-iframe probing.

---

## Part 3 — Stage-Access synchronization audit (the 6 questions)

Repro state verified in DB: owner's change IS saved —
`barcode_generation.access_by_skill = []` (was master+helper).

**1. Single source of truth:** `Stage.access_by_skill` / `access_by_role`
rows (edited by the Access-Control hub), read by
`production.services.access_service` (`user_can_access_stage` /
`stage_access_map`). There is **no cache** — every request reads live rows.

**2. What draws the worker dashboard:** `inventory/views/dashboard.py::
_build_dashboard_context` — three independent sources, NONE of them the
access rules: (a) Adda cards = "Addas where I hold any active task", with
workspace accordions emitted for every card's stages unconditionally;
(b) MY ACTIVE STAGES = my active tasks; (c) helper board + `is_skilled_user`
= **hardcoded skill constants** (`SKILL_CUTTING_MASTER[_HELPER]`), not the
stage's access rows.

**3. Live rules or stale cache?** Neither — the dashboard simply **never
consults** the access rules. Nothing is cached anywhere in the chain.

**4. Why removal didn't update the dashboard:** the entries the owner saw
come from flow-shape/task/skill-constant sources (Q2); only the Adda page
asks `stage_access_map`. Enforcement (panel/action gates) DID update
instantly — the same click that showed the stage refused to open it.

**5. UI refresh or deeper problem?** Deeper, but bounded: an
**enforcement/listing split**. Enforcement is a single live predicate,
fail-closed everywhere (no privilege leak found: panel 403s, actions refuse).
Listings on ONE surface (user_dashboard) + the hardcoded skill constants
bypass the predicate — so revoked access *looks* stale while actually being
enforced. One exception found at the enforcement layer itself:
**`WorkerReportView` checks own-task ONLY** ([worker_report_views.py:137-149](../config/production/views/worker_report_views.py))
— a worker holding an active task on a stage whose access was later revoked
can still open and submit the report form. Assignment-implies-access holds at
assignment time (F-4 pickers = gate population), but **revocation after
assignment does not close the report path**.

**6. Census — every surface that shows stage work:**

| Surface | Source today | Live-access? |
|---|---|---|
| Adda page stage tabs | `stage_access_map` | ✅ correct (Restricted card) |
| Adda page "My Work" | own tasks | task-only (links to report) |
| Worker dashboard Adda-card accordions | flow shape | ❌ F-11 |
| Worker dashboard MY ACTIVE STAGES | active tasks | ❌ access-unaware rows |
| Worker dashboard helper board / `is_skilled_user` | hardcoded skill constants | ❌ ignores access rows |
| Broadcast rows | Adda codes only | ✅ by design (D6) |
| Operations dashboard | mgmt digest; worker subset links to Adda page | ✅ |
| A360 | management-only ctx | ✅ |
| Stage panels / stage actions / pickers | `user_can_access_stage` (+assignment) / `eligible_stage_workers` | ✅ live |
| Worker report view | own active task only | ⚠️ no access check |

Template census confirms no other worker-facing stage entry points exist
(grep over all templates for stage-panel/worker-report/workspace URLs).

**Recommendation — ONE visibility predicate, used everywhere:** a worker
sees/loads a stage surface iff `user_can_access_stage(user, stage)` AND
(management OR actively assigned) — exactly what `StageViewAccessMixin`
already enforces. Apply it to: dashboard accordions + MY ACTIVE STAGES rows
(show a "restricted" note instead of a dead link if a task exists but access
was revoked), helper-board gating (derive from access rows, delete the
hardcoded constants), and add the access check to `WorkerReportView`
(closing the revocation gap; management unaffected). All view/template-level;
zero writes, zero money, zero migrations.

---

## Part 4 — Final foundation review

**Remaining pre-freeze items (all found by this audit series, all
operational, none touch money):**

| # | Item | Recommendation |
|---|---|---|
| C-1 | Remove `sync_layering_workers_for_skill` (+ `sync_user_skills` wrapper + 3 call sites + pins) | **in freeze** (Part 1) |
| C-2 | Dashboard access-filtering (F-11 + Q6 census rows) via the Adda-page `stage_access_map` pattern; derive helper-board/`is_skilled_user` from access rows | **in freeze** (Parts 2-3) |
| C-3 | `WorkerReportView` access check (revocation closes the report path too) | **in freeze** (Part 3 Q5) |
| C-4 | Strict-C3 flip — completion blocks on bare ASSIGNED (roadmap:212's "THEN"; both auto-assign halves gone ⇒ ASSIGNED = pure manager intent; super-admin override already exists from R3) | **recommend in freeze** — it is the designed completion of the migration; owner may defer |
| — | Junk stages (`verify`, `verify-86f27f0a`, `cross_cutting` unused) + junk users on real surfaces | owner's planned dev-data cleanup batch (F-5) — data, not architecture; fine post-freeze |
| — | Legacy cutting single-shot path (`complete_cutting_legacy`, `CuttingForm`) | dormant compat path, gate-covered; leave; candidate for R10-era pruning |
| — | F-1 leftovers: 2 orphan SidebarItemRules + hidden registry twins | owner deletes rules via Sidebar Access whenever; cosmetic |
| — | SWA transitional-RETAINED, era-A rollback lever, S6 reported-retirement, enforcement flags OFF | **money-side stream, intentionally soak-gated** — NOT operational-freeze scope (ARCHITECTURE_V2 / PENDING_BACKLOG own these) |

**Honest bottom line:** after C-1 + C-2 + C-3 (+ C-4 if approved) there is
nothing else I can find that contradicts the frozen operational story —
every audit trail in this series (E2E business audit → polish → retro-tag →
access-sync) now converges on one rule set: *manager assignment is the only
roster source; one live access predicate governs every worker-facing stage
surface; money moves only at settlement.* **Recommend freezing the
operational foundation (R1 → A360 + Pre-R10 Polish + this closeout) once
C-1..C-3 land and gate+E2E pass.**

---

## Part 5 — ONE-predicate census (owner follow-up, same day)

Question: is there exactly ONE access predicate? **Answer: one predicate per
LENS — five lenses, each with a single owner — plus the violations below.**

| Lens | The single owner | Consumers verified |
|---|---|---|
| Role | `permission_service.user_has_role` / `user_has_perm` (`is_superuser` bypass lives INSIDE it) | every role mixin in every app delegates (production ×3, inventory ×2, tracking ×2 private copies, storefront `ListingTeamMixin`, expense `_ManagementOnly`, accounts `SuperuserRequiredMixin`) — no independent role logic anywhere |
| Menu + URL | `build_menu_for` + `can_access_url_name` + `SidebarAccessMiddleware` | single funnel; menu-hidden ⇒ URL-blocked |
| Stage access | `access_service.user_can_access_stage` / `stage_access_map` / `eligible_stage_workers` | panel gates + Adda-page tabs + pickers (F-4) |
| Object/assignment | `AddaStageRecord.is_worker_assigned` (one model method) | `StageViewAccessMixin` + report `_resolve` compose it |
| Financial fields | `user_can_view/edit_financials` | roll cost/supplier surfaces |

Clean sweeps: **zero** raw `is_superuser` checks in views (only inside
permission_service + user_service account-invariants — rule #6 holds), zero
raw `role.code` comparisons outside the owners, templates check nothing
(display-only badges), expense/storefront/tracking all delegate.

**Violations found (hardcoded / duplicated / unconsulted):**

| # | Where | Problem |
|---|---|---|
| V-1 | Stage-service ACTION gates: `_shared._ensure_can_complete_layering` · `cutting/service._ensure_cutting_skill` + `_ensure_can_complete_cutting` · `cutting_pattern/service.py:106,121` · `barcode_generation/service.py:68` | **Hardcoded skill constants — a second, frozen truth at the action layer.** Access-hub edits change who can SEE a stage but not who can ACT: grant a new skill in the hub → user can open the panel but completion still refuses ("only cutting_master_helper…"); remove a skill → view already blocks, so no leak — asymmetric, not unsafe |
| V-2 | Display mirrors of V-1: `_build_layering_context` / `_build_pattern_context` / `barcode_gen_views` ctx flags (`can_complete`, `can_attach`…) + `dashboard.py:39,48,152` (`is_skilled_user`, helper board) | duplicated skill constants driving button/section visibility — the C-2 family |
| V-3 | `WorkerReportView` | task-only, never consults stage access — C-3 (already in closeout) |
| V-4 | `adda_service._skilled_user_pks` (D6 creation guard) + dying retro-tag | skill constants; guard is creation-time sanity only — align to `eligible_stage_workers` when touching (C-1 does the retro-tag half) |
| V-5 | Cosmetic: 3 duplicate `ProductionRoleMixin`-class copies (production, tracking ×2) + per-app SuperAdmin mixins | thin wrappers over the SAME predicate — no truth split; consolidation optional, zero risk carrying it |

**V-1 recommendation (the only genuinely new decision):** completion/action
capability ("who may complete a stage") is a BUSINESS rule, today expressed
in code, distinct from view access. Two honest options: (a) freeze-scope —
KEEP the code-level action gates but document them as intentional
("view access = hub-editable; action capability = code rule") in RBAC.md;
(b) post-freeze phase — make action capability hub-editable (per-stage
"complete/act skills" config on the Stage model → migration + UI). Do NOT
silently change completion permissions inside a freeze. C-2/C-3 stay as
planned either way.

### Verification sources
Main-thread 2026-07-05: dashboard.py:30-199 · adda_views.py:95-125 ·
adda_detail.html:690-725 · worker_report_views.py:125-165 ·
worker_task_service.py:129-144 · fnf_service.py:4-138 · layering/service.py:296-320 ·
stage access DB dump (barcode = []) · live browser as utest on :8000
(dashboard mentions ×5 / fetch 403+DENY / Restricted card) · template+view
census greps · Part-5 greps: user_has_skill/SKILL_* all callsites,
is_superuser, role.code, template perms, every Mixin class, expense/
storefront/tracking gating. Confidence: High.
