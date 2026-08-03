---
id: production-readiness-checklist
type: status-anchor
status: active
owner: handwritten
scope: all — navigation/state
anchors: —
verified: 2026-07-13
---

# FACTORY VALIDATION GUIDE — operate the ERP like a real garment factory

> **Purpose (owner, 2026-07-05):** validate the ERP like a REAL factory before
> any new feature work. Improvements come from this testing, not assumptions.
> **Foundation is FROZEN during validation** — only real bugs or findings from
> this checklist get implemented.
>
> **How to use:** walk each flow in order (they build on each other), tick
> boxes, and log every friction in the FEEDBACK LOG format at the bottom —
> even tiny ones ("this needed two taps, should be one"). Test each flow on
> **desktop AND a phone** (390-ish width), and in the role stated. Numbers
> that must AGREE across screens are called out explicitly — any mismatch is
> a finding.
>
> Roles/logins: Super Admin = your owner account · Manager = dev.manager ·
> Workers = utest (piece-rate master), dev.monthly (monthly), dev.helper
> (helper). Create fresh DEV-marked users freely. Dev server: restart it
> after pulling changes (templates cache).

---

# PART A — THE SEVEN PASSES (test like a factory owner, not a developer)

Run the passes in order, one sitting each if possible. Every pass has a
mindset, a script, and the questions that turn friction into findings. The
detailed per-flow checkboxes (Part B below) are your reference for WHAT to
verify at each step — the passes tell you HOW to walk them.

## PASS 1 — Happy Path (one complete factory cycle)
**Mindset:** a new order just came in; run it to payday without shortcuts.
**Script:** Product → Workflow (Flow Editor: stages, categories, work types,
machine types, rates, access) → Machines ready (types + instances + operators)
→ Adda → assign workers → produce stage by stage (worker phones report; you
verify; stages complete; snapshots carry forward) → settlement → payroll →
review every dashboard.
**At every step ask:** do the numbers I just entered show up EXACTLY where
they should next? (Part B sections 3-8 list the specific checks + the six
money surfaces that must agree.) Anything you had to hunt for = finding.

## PASS 2 — Worker only
**Mindset:** you are utest with a phone in the workshop. Never open desktop.
- Do I immediately know what work I have today?
- Can I report my work in under a minute, one-thumbed?
- Is anything on my screen NOT about my work? (that's overload)
- Do I understand my money (Expected → Earned → Paid) without asking anyone?
- Try to be nosy: other workers' numbers, management pages, unassigned
  stages — I should politely hit walls everywhere.
Repeat once as dev.monthly: I should see my WORK but never a ₹ expectation.

## PASS 3 — Manager only
**Mindset:** 8am, dev.manager, plan the day and keep it moving.
- In ONE look at Operations: what's stalled, who hasn't reported, what's
  active, what needs me?
- Assign today's workers on two Addas — how many clicks/pages did that take?
- Verify yesterday's reports and correct one quantity — was the trail obvious?
- Find delayed work WITHOUT being told where it is.
- Complete today's production end-of-day: can I do it without opening more
  than ~3 pages? Every extra page = finding.

## PASS 4 — Factory Owner only (business questions, stopwatch mindset)
Forget how it's built. Sit with the dashboards and ANSWER these, timing
yourself; anything that takes >30s or >2 pages = UX finding:
- Which Adda is delayed right now? · Which workers are actively working
  this minute? · Which workers are waiting/blocked?
- Which machine is idle? Under maintenance? Who holds OL-001?
- Which stage is each Adda at? Which operations are blocked?
- Which product costs the most to make? Which Adda's labor beat/exceeded
  standard? · Which worker earned the most this cycle? · How much do I owe
  everyone right now? · What did the factory spend this month (expenses)?
Write down every question the ERP could NOT answer — Part D question 5.

## PASS 5 — Permissions (all three roles)
Part B section 9 is the URL-forcing matrix. Run it as worker, then manager.
Everything must be a clean refusal (styled 403/redirect) — any 500 or any
page that leaks data = blocker.

## PASS 6 — Edge cases (break it on purpose)
Part B section 10 is the script: double-clicks on money buttons, two-tab
races, access revoked mid-task, worker deactivated mid-Adda, settlement
reverse → re-settle, reopen chains, garbage input, abandoning forms halfway.
The bar: the system may refuse you, but it must NEVER lie, double-pay, 500,
or lose a number.

## PASS 7 — Mobile only (phone in hand, desktop forbidden)
Walk PASS 1's critical path + every dashboard at ~390px. Per page ask:
- What is the ONE business question this page answers — and does it answer
  it in the first screenful?
- Summary first, details behind a tap?
- Any sideways scrolling, cramped touch targets, keyboard covering the
  submit button, dropdowns opening in the wrong place?
Part B section 11 lists the specific mobile checks.

---

# PART A2 — TIME & USABILITY MEASUREMENTS

For each common operation, record clicks · seconds · pages visited (count a
page = any full navigation). Do each one twice — first attempt (learning) and
second attempt (practiced); the SECOND number is the honest one. "Feels slow"
at any count is still a finding.

| Operation | Clicks | Time (s) | Pages | Felt OK? / note |
|---|---|---|---|---|
| Create a product + its full flow | | | | |
| Create an Adda | | | | |
| Assign workers to a stage | | | | |
| Worker: submit a report (phone) | | | | |
| Verify/correct one report | | | | |
| Create a machine (+type) | | | | |
| Assign a machine to an operator | | | | |
| Configure a NEW stage end-to-end (library+access+flow) | | | | |
| Run a settlement (draft → finalize) | | | | |
| Record a cash payment | | | | |
| Answer "who owes what" (payroll glance) | | | | |
| Find why an Adda is stalled | | | | |

---

# PART B — DETAILED FLOW CHECKLIST (the reference layer)

## 0) Setup sanity (once)

- [ ] Login works for all 5 roles; each lands on the RIGHT home (management →
      Operations, workers → My Dashboard)
- [ ] Sidebar per role matches expectations (worker: no Machines/Payroll/
      Costing/Admin; manager: no Administration section, no Stage Rates)
- [ ] Dark-mode toggle renders every page you visit acceptably (spot-check)
- [ ] Phone: sidebar collapses to hamburger; every tested page has NO
      horizontal scroll

## 1) Business masters (Super Admin)

- [ ] Stage Categories: create one (e.g. Washing) → rename it → reorder it →
      deactivate it → it disappears from the Stage-form picker but existing
      stages keep their old label
- [ ] Machine Types: create (e.g. Iron Press) → deactivate → hidden from
      pickers; still shown on machines that already use it
- [ ] Stage library: create a MANUAL stage (e.g. Checking; category
      Finishing) and a MACHINE stage (e.g. Flatlock + Flatlock Machine type);
      Machine Type field only appears when Work Type = Machine; saving a
      Machine stage without a type is refused with a clear message
- [ ] Access: wire each new stage's skills in the hub; give a worker the
      skill; confirm picker + dashboard visibility follow within one reload
- [ ] CRUD polish: every create/edit form has cream inputs, sticky Save bar,
      clear errors on bad input (duplicate code, blank name)

## 2) Machines register (Manager + Super Admin)

- [ ] Create machine types + physical machines (several per type: OL-001…)
- [ ] Counts strip (total/active/maintenance/assigned) always adds up
- [ ] Assign an operator (+optional Adda) → holder chip appears; the SAME
      truth shows on the Operations tile (assigned/active)
- [ ] Double-assign is refused and NAMES the current holder
- [ ] Release → re-assign same day works (sequential windows)
- [ ] Maintenance status blocks assignment with a clear message
- [ ] Machine code edit is refused once history exists
- [ ] Worker login: /machines/ is 403 and no menu entry

## 3) Product + workflow configuration (Super Admin)

- [ ] Create a NEW product (code immutable after first Adda — verify the
      guard fires on edit attempt)
- [ ] Build its flow in the Flow Editor: mix manual + machine operations,
      several categories (so the category rollup appears later)
- [ ] Set per-stage cost: per_piece / per_layer / fixed; Pays-workers on
      payable stages; try a grouped stage (cost_billed_at) if used
- [ ] Role-rate override on one stage (WorkflowStageRoleRate) — verify it
      wins over the base rate at freeze time later
- [ ] Patterns + sizes configured for the product (pattern checklist stage
      needs them)
- [ ] Reorder stages BEFORE any Adda exists; confirm reorder is blocked /
      safe once production started

## 4) Raw material flow (Manager)

- [ ] Create cloth types/colors/locations; bulk-create rolls
- [ ] Roll list: financial fields (cost, supplier) hidden from workers
- [ ] Attach rolls at Layering (stock pickers filter correctly); roll status
      flips used; leftovers recorded; roll history shows the trail

## 5) Adda lifecycle — run at least TWO full Addas end-to-end

For each Adda (use different worker mixes: piece-rate only · piece+monthly):

- [ ] Start Adda → NO workers auto-assigned; layering roster empty
- [ ] Manager assigns via picker (only active + skilled workers offered)
- [ ] WORKER PHONE: task appears with "Report needed"; report own quantities;
      form is one-thumb usable; after submit the report is LOCKED
- [ ] Monthly worker: no ₹ anywhere, badge instead; production counts still
      tracked
- [ ] Complete each stage in role: does the completer land somewhere sane
      (never a 403)? does the next stage open with the PREVIOUS stage's
      reference snapshot correct (numbers match what was entered)?
- [ ] Pattern stage: partial checklist refused naming the missing design;
      photo/video + 100% sizes required to complete
- [ ] Cutting: breakups match reported; bundles; barcode preview count right
- [ ] A generic operation (Overlock/your new stages): assign → phone report
      Good/Alter/Missing → Output board per worker → complete → snapshot
      carries machine type + instances
- [ ] Machine section on machine-stage panels shows the ACTUAL instances
      assigned on this Adda
- [ ] C3 guard: try completing a stage while a worker is mid-report →
      blocked; super-admin override demands a reason; reason visible in
      history
- [ ] Reopen a completed stage (before settlement): downstream guard message
      is actionable; after reopen + re-complete, numbers still true

## 6) Verification + corrections (Manager)

- [ ] Review reports: set a verified quantity ≠ reported; BOTH numbers stay
      visible; history logs who/old/new
- [ ] Settlement later pays verified-else-reported (check the draft line)
- [ ] Super Admin: re-rate a stage-role before settlement → expected
      earnings recalc; audit row exists; after settlement the same re-rate
      is refused

## 7) Money: settlement → payroll → F&F (Super Admin + each worker)

**The six surfaces that must show the SAME truth:** settlement draft ·
finalize snapshot · Payroll Overview · worker My Earnings · A360 money strip ·
Manufacturing Costing row.

- [ ] Draft: payable lines per worker correct (qty × frozen rate); monthly
      workers in the excluded section with the why-text; non-payable stages
      absent
- [ ] Finalize: per-worker frozen snapshot; ledger credits; "Reverse" +
      "Reverse & settle again" present
- [ ] Worker phone: Expected → 0, Pending payable ↑, per-Adda drill-down
      matches
- [ ] Advance: give one, then settle → recovery math right on both sides;
      advance to a MONTHLY worker is refused (temporary rule)
- [ ] Partial settlement: settle mid-Adda, keep producing, settle again —
      no double-pay (queue empties per line)
- [ ] Reverse a settlement → balances net to zero → re-settle pays once
- [ ] Cash payment (PayrollSettlement) → Paid updates; Last payment date
- [ ] F&F on a DEV leaver: blockers listed (open tasks) → resolve → execute
      → settlements + write-off + deactivation; login blocked; pages render
- [ ] Duplicate monthly salary in FactoryExpense warns and requires confirm;
      voided rows excluded from month totals

## 8) Dashboards + visibility (each role)

- [ ] Operations: stalled / pending reports / active / by-stage / payable /
      advances / machines tile — spot-verify each number against its
      drill-down page
- [ ] A360 on a live Adda: category chips roll up correctly; worker board
      matches reality (assigned/active/completed); money strip = settlement
      truth; timeline attributes every action to the right person
- [ ] Worker dashboard: ONLY their world (assigned Addas, current-op focus,
      own earnings); no workspace offered that 403s when opened
- [ ] Revoke a stage's access in the hub while a worker holds a task →
      their dashboard rows/accordions disappear on refresh; report URL 403s;
      re-grant restores
- [ ] My Dashboard appears exactly once in every role's menu

## 9) Permissions spot-matrix (10 minutes of URL forcing)

As WORKER, paste management URLs directly — all must refuse: /machines/,
/expense/payroll/, /expense/settlements/…, /production/costing/,
/production/stages/, /production/stage-categories/, another worker's report
URL, an unassigned stage panel. As MANAGER: Stage Rates + Administration
pages refuse; F&F button absent. Log any 500 (should always be a clean 403
page or redirect).

## 10) Error + edge scenarios

- [ ] Double-click every money button once (settle, finalize, assign) — no
      double effect
- [ ] Two browser tabs: complete the same stage from both — second gets a
      clean refusal
- [ ] Bad inputs: negative/zero/absurd quantities; letters in number fields;
      future dates — clear messages, never a 500
- [ ] Empty states: brand-new product/Adda pages look intentional (no blank
      cards)
- [ ] Deactivate a worker mid-Adda: their history/earnings intact; picker
      hides them; F&F path still works
- [ ] Session expiry mid-form → login → no data corruption
- [ ] Print/export paths you use (QR sheet, exports) render

## 11) Mobile pass (repeat the critical path at ~390px)

Worker: login → dashboard → report → submitted state → My Earnings.
Manager: Operations → Adda → assign → verify → settle draft.
- [ ] No horizontal scroll anywhere; touch targets comfortable; selects/date
      pickers open correctly INSIDE panels (iframes); tables stack into
      label:value cards; sticky bars reachable above the keyboard

---

# PART C — FEEDBACK LOG (per finding)

| # | Page / flow | Role | Device | What felt wrong / missing | Severity (blocker · friction · nice-to-have) |
|---|---|---|---|---|---|
| 1 | | | | | |

**Severity guide:** *blocker* = stops real factory use · *friction* = works
but slow/confusing/too many taps · *nice-to-have* = polish.

> When done, hand the log back. We fix blockers first, then friction by
> role (worker → manager → owner), then polish — as UX/workflow refinements
> on the frozen foundation. Only after that: R10-C, R11, barcode, backlog.

---

# PART D — SESSION NOTES (write after EVERY sitting — more valuable than bug reports)

Copy this block per session:

```
SESSION: <date> · <pass(es) run> · <role> · <device>

1. What felt EXCELLENT?
   -

2. What felt CONFUSING?
   -

3. What felt FRUSTRATING?
   -

4. What would I improve IMMEDIATELY?
   -

5. What business information did I EXPECT to see but couldn't find?
   -
```

> Triage when validation ends: blockers → friction by role (worker → manager
> → owner) → polish; Part D answers set the UX-improvement priorities.
> Foundation stays FROZEN until then — the next improvements come from THIS
> guide's findings, not assumptions. Only after: R10-C · R11 · barcode ·
> backlog.
