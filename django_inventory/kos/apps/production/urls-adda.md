---
id: app-production-urls-adda
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Adda lifecycle, stage panels, the R10-B generic action set, worker report + review, rate correction — each URL's full learning story."
related: [app-production-urls]
---

# production URLs · Part 2 — Adda Lifecycle · Generic Stage Set · Worker/Review (17)

> 📂 [URL index](urls.md) · [production app](README.md) · [LOS home](../../README.md)

---

### `addas/` — `adda-list`
**Purpose:** every batch, filterable. **Method:** GET → `AddaListView`. Read-only board.
**Why simple:** lists borrow truth. **Perf:** bulk-aggregate discipline (pinned pattern).

### `addas/start/` — `adda-create` ⭐
**Purpose:** ONE click births a batch: pick product → code auto-generated (3-PATTI-003) → one `AddaStageRecord` per WorkflowStage of that product's flow → role rates FROZEN per stage.
**Why one click:** the flow editor already made every decision; creation should be consumption, not re-entry.
**Method:** GET+POST → `AddaCreateView` (`views/adda_views.py`). **Service:** `adda_service` (+`stage_rate_service.ensure_stage_role_rates`).
**Transaction:** atomic — Adda + code + N ASRs + rate snapshots, all-or-nothing.
**The freeze (memorize):** `AddaStageRoleRate` snapshots at CREATION — a later flow-editor rate edit never re-prices this Adda (S2 law). Safety net: if `complete_worker_task` ever has to create them late, it LOGS a warning naming the missed site — loud-not-silent.
```
Journey: POST → view (mgmt) → adda_service [@atomic: Adda + code +
ASR per WorkflowStage + frozen role-rates] → redirect adda-detail
```
**Failure modes:** product without a flow · duplicate concurrent codes (serialized).
**Required knowledge:** [flow editor](urls-core.md) · frozen snapshots ([models.md](models.md)).

### `addas/<code>/` — `adda-detail`
**Purpose:** the batch's hub — stage workspaces, timeline, garment readiness, lanes.
**Method:** GET → `AddaDetailView`. Read-only assembly of everything other URLs maintain (+ A360 hub for management depth).
**Why simple-looking but big:** composition — each embedded panel is its own gated URL (`?embedded=1` iframes), so THIS view stays thin.

### `addas/<code>/bundles/create-sets/` — `adda-bundle-sets`
**Purpose:** GAP-5 one-tap "bundle ready sets" from the Garment Readiness panel.
**Method:** POST-only (mgmt). **Service enforces the post-join gate** — sets only after every blocking lane's cutting completed ([cutting §streams](../../features/cutting.md)).
**Lesson:** convenience buttons NEVER bypass gates — the service re-checks what the panel implied.

### `addas/<code>/lanes/add/` — `adda-add-lane` · `lanes/cancel/` — `adda-cancel-lane`
**Purpose:** GAP-4 — declare a NEW CuttingStream (seq>1: split lay / recut / additional production, **mandatory reason**) · cancel-if-empty escape (§9.4).
**Method:** POST → `AddaAddLaneView`/`AddaCancelLaneView`.
**Why reasons are DATA:** exceptional flows become auditable acts, not silent edits — six months later "why is there a lane 3?" answers itself.
**Failure modes:** cancel refuses once the lane has content. **Learn:** [cutting §streams](../../features/cutting.md) · fork-join DSA there.

---

### `addas/<code>/stage-rates/` — `stage-rates` · `…/<sr_id>/<role_id>/correct/` — `stage-rate-correct` 🔐
**Purpose:** S1.1 — list this Adda's frozen role rates · SA corrects ONE (stage_record, role) rate.
**Why it exists:** frozen ≠ infallible — a typo'd rate needs a lawful fix BEFORE money books.
**Method:** GET list · POST correct → `views/rate_views.py`. **Service:** `stage_rate_service.rerate_stage_role` — SA-only (service-enforced), window = **until settlement** (per (SR, role) lock M1), auto-recalcs frozen expected earnings, writes `RateCorrectionAudit` (old→new, actor, reason).
**Failure modes:** settled → refused (reverse first) · non-SA → refused · no reason → refused.
**The pattern to learn:** corrections-until-boundary — freedom before money, armor after ([two-truths §interlocks](../../concepts/architecture/two-truths.md)).
**Tests:** S1.1 suite.

---

### `addas/<code>/stage/<stage_type>/` — `stage-panel`
**Purpose:** the canonical per-stage console — standalone page AND iframe embed (`?embedded=1` strips chrome).
**Method:** GET → `StagePanelView` (`views/stage_views.py`), gates via mixins (access ∩ assignment).
**Why one URL for both modes:** two URLs would drift; a render flag can't ([rbac-access](../../features/rbac-access.md) drift lesson, applied to UI).

### `addas/<code>/stage-advanced/` — `stage-advanced`
**Purpose:** F-3 — a data-free bounce page after an embedded complete; pings the parent to reload.
**Why it exists at all (why simple):** an iframe can't redirect its parent — this tiny URL is the honest workaround. Documented so nobody "cleans it up."

### The R10-B generic action set — `…/stage/<stage_type>/start|complete|reopen|allocate|alloc-void/`

**The law first:** config-only stages NEVER add endpoints — these five
parameterized actions serve EVERY current and future config stage (frozen
rule 11). New stage = new ROW, same URLs.

**`…/start/` — `generic-stage-start`**
POST → handler `stages/generic_stage/service` start: ASR → in-progress, timestamps auto. **Why simple:** starting is just honest bookkeeping.

**`…/complete/` — `generic-stage-complete` ⭐**
POST → `GenericStageCompleteView` → generic handler complete:
```
[@atomic] C3 gate: workers mid-work? → REFUSE naming them
(SA override = audited reason) → untouched ASSIGNED tasks auto-cancel (F3)
→ ASR complete (duration auto) → pool_service.materialize_stage_pool
(freeze Σ verified-else-good as SPS; NONE-grain ⇒ 0 rows by design)
→ timeline event → bounce/redirect
```
**Failure modes:** mid-work block (the refusal names people — go resolve THEM) · already complete.
**Why this is THE production write:** completion is where a stage's truth becomes downstream's INPUT — the freeze moment for capacity, mirroring what task-complete is for pay-visibility.
**Learn:** [allocation](../../features/allocation.md) · [stage-tracking §resolver](../../features/stage-tracking.md).

**`…/reopen/` — `generic-stage-reopen` 🔐**
POST (admin). The downstream-consumer guard walks FORWARD: any later stage holding non-voided allocations / completed contributions → **REFUSE, naming the furthest blocker + the action** (void/reverse/reopen that first). Then `clear_stage_pool` + refreeze on re-complete.
**Mental model:** reverse-first peel — you unwind an onion from the outside; the error message is the peeling order.
**Misconception:** reopen ≠ undo — nothing is deleted; it's an authorized unlock with the past intact.

**`…/allocate/` — `generic-stage-allocate` · `…/alloc-void/` — `generic-stage-alloc-void`**
POST (mgmt) → `pool_service.allocate / void_allocation` (OP-1 "Split the work").
**Guards:** over-draw refused ALWAYS-ON (`qty > available`) · H-2: void refused while the worker's submitted production wouldn't fit the remainder (fix via Report Review first).
**Locks:** advisory `(5375, objid)` — per-pool sharding, disjoint from money's 5374.
**No money, ever** — capacity only (owner-locked ⊥).
**DSA:** semaphore-in-SQL ([allocation §DSA](../../features/allocation.md)).
**Tests:** S4 suites.

---

### `addas/<code>/report/<stage_type>/` — `worker-report` ⭐ THE PHONE FORM
**Purpose:** Meena's URL — report what she made (color/size × good/alter/missing), save drafts, submit, complete.
**Why it exists:** production truth must come from the HANDS — self-reported, then verified; C-TM makes this the only capture door.
**Method:** GET (schema-driven form) + POST → `WorkerReportView` (`views/worker_report_views.py`).
**Permissions:** OWN task only (assignment) + stage skill — access ∩ assignment; `?embedded=1` for the dashboard iframe.
**Blind reporting:** choices scoped to HER allocation dims — labels shown, quantities never (an allocation can't anchor a claim).
**Service:** `worker_task_service.report_contributions / save_draft_contributions / complete_worker_task` — the freeze with five guards (P0-5 lock-and-reread · bound check · FIXED-pay-once · role/rate freeze · NO ledger).
**Full hop-by-hop (canonical):** [request-through-stack](../../flows/request-through-stack.md).
**Failure modes:** each a designed refusal that names its fix (cancelled task, second fixed-pay report names WHO, bad quantity, bound).
**Mobile-first = FUNCTIONAL here** (rule 11) — she's standing at a cutting table.
**Tests:** `test_worker_task.py` · `test_s3_good_alter_missing.py`.
**Required knowledge:** [stage-tracking](../../features/stage-tracking.md) FIRST.

### `addas/<code>/review-reports/` — `adda-report-review` ⭐ THE RED PEN
**Purpose:** P1 — management corrects quantities BEFORE money books: sets/clears `verified_quantity`; `reported` untouched forever.
**Method:** GET+POST → `AddaReportReviewView`. **Service:** `set_verified_quantity` — locks the WSC `of=('self',)` (nullable-FK join lesson), **refuses settled lines NAMING the ADST**, parses raw strings safely (PA-07-2).
**The propagation (the whole point):** one correction here flows to BOTH the next stage's pool AND the settlement basis via the shared resolver — derive-don't-copy.
**Misconception:** "review edits the worker's report." Never — two hands, both visible ([stage-tracking](../../features/stage-tracking.md) mental model).
**Real question:** "PM: fix a settled count" → the refusal IS the answer: reverse → correct → re-settle.
**Tests:** guards in V2-3 + S3 suites.

## Learning Graph (this file)
**Before:** [urls-core.md](urls-core.md) (the configs these URLs consume).
**After:** [urls-layering-pattern.md](urls-layering-pattern.md) — the built-in workspaces where the four original stages live.
