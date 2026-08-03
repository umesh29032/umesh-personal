---
id: manufacturing-excellence-audit-2026-07-06
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Manufacturing Excellence Audit + Final Readiness Report (2026-07-06)

> Owner-ordered pre-freeze audit. NOT a bug hunt — a factory-owner's daily-use
> review of every workflow through 10 lenses: worker · manager · owner · mobile ·
> speed · cognitive load · clicks · information hierarchy · discoverability ·
> real factory usability. Frozen architecture and design system fully respected:
> every change below is presentation/copy/ordering-level; zero schema, zero
> service-contract, zero new concepts. Method: live browser walk of the three
> daily loops (worker @390, manager, owner) on real data (3-PATTI-016 settled
> world + live dev worlds), fix-immediately for clear wins, defer the rest.

## 1. What was IMPLEMENTED this audit (all verified live, gate suite green)

| # | Lens | Finding | Fix | File |
|---|---|---|---|---|
| E-1 | Manager · daily allocate (highest-frequency mgmt action) | Split-the-work used TWO dropdowns (colour, size) built row-wise → duplicate entries ("Red, Red, Blue"), non-existent pairs selectable, and a helper note *apologising* for it | ONE **"Cut lot (colour · size)"** select listing exactly the pool rows ("Red · Size 1 — 24 left"); picking a lot **pre-fills its remaining pieces** (edit to split); hidden `color_id`/`size_id` synced on change+submit — endpoint contract untouched. Proven live: allocation posted on 3-PATTI-009 | `_stage_panel_generic.html` |
| E-2 | Worker @390 · earnings | "17.00 × ₹1.5000" on a worker phone — decimal pieces + 4-dp rate = floor-language violation | "17 × ₹1.50" (`floatformat`) | `expense/my_earnings.html` |
| E-3 | Worker @390 · empty state | "When a manager assigns you to a Layering or Cutting stage…" — stale pre-OP-1 copy, wrong for all 14 new operations | "Jab manager aapko kaam dega, woh yahan dikhega." (+ English) | `inventory/user_dashboard.html` |
| E-4 | Manager · morning triage | "In-Progress by Stage" rendered ALL ~20 configured stages incl. 17 zeros — wall of noise burying the 2-3 numbers that matter | Only stages actually holding an in-progress Adda; honest empty copy | `production/views/dashboard.py` |
| E-5 | Manager/owner · dashboards | Literal **"None layers · None m · None min"** rendered for records missing layering numbers | Guarded pills + "—" defaults (compact + card variants) | `_layering_summary.html` |
| E-6 | Manager · pending reports | Raw email shown where every other surface shows the floor name | `get_full_name` first | `pending_reports.html` |
| E-7 | Manager · machines | Assign-picker ordered by email — unscannable | Ordered by name (reads like the floor roster) | `machines/views.py` |
| E-8 | Owner · costing | "Pieces" summed `barcode_batches.total_pieces` → **0** for any Adda whose flow skips/hasn't reached barcodes — misleading daily number | Sum APSCPB `verified_piece_count` — the canonical cut-piece truth (ops-master §2 rule 6) | `costing_views.py` |

Same-day journey fixes (same audit spirit, shipped hours earlier): nullable
`completed_by` crashed the whole Adda page (`_so_tile.html`, guarded);
multi-line `{# #}` comment leaking on every worker report page
(`_worker_report_body.html` + `signup_otp.html`; repo swept — one new own-goal
caught and fixed the same hour, proving the sweep habit).

## 2. What was checked and found GOOD (no change needed)

- **Worker daily loop @390**: login lands on My Dashboard; task card → report =
  ~3 taps; report page = hinglish stage hint + ⚙ machine chip + J-2 prefilled
  rows + 4-way G/A/M/D; My Earnings = Expected→Earned→Paid ladder with
  stage-wise, adda-wise, and recent-work views. Blind rule holds everywhere.
- **Manager loop**: dashboard KPI triage row (stalled / pending reports / active /
  payable / advances / machines) is the right morning hierarchy; Pending Reports
  page answers "who's holding up each Adda, oldest first"; Report Review =
  verified-qty correction + audited void; machines register shows holder + since-when.
- **Owner loop**: A360 (12/12 chips, expected vs settled, ADR-0009 variance
  framing); Costing page carries the honest-NULL banner and the never-add
  standard-vs-actual warning; Settlements list separates "Ready to settle" from
  "Waiting on production — blocked by X" (exactly the owner's question); flow
  editor exposes method/rate/paid-at/grain/payability per stage with the frozen
  history guarantees behind it.
- R1 "New Addas Started" broadcast on worker dashboards = owner-accepted product
  behaviour (test-pinned) — reviewed, intentionally left.

## 3. Deferred (documented, NOT built — register/owner-gated)

| Idea | Why deferred | Where registered |
|---|---|---|
| Rate matrix (operation × product, read-only) for rate maintenance at scale | Pre-approved as a **presentation-only** lever "when maintenance measurably hurts" — one-time real-rate-card entry via flow editor is fine today | ops-master §5.15 |
| Skill-aware machine assign picker (only workers whose skills match the machine type's stages) | Current role-based picker is a **documented R10-A decision** — overriding needs owner ruling | this doc |
| Manager bulk-split affordances ("assign colour X to W", "repeat previous split") | Pre-approved pure-UI follow-up WHEN split time measurably hurts (§6 metric) | ops-master §5.2 |
| Worker-dashboard relevance filter for the R1 broadcast (only product/stages the worker can ever serve) | Touches an owner-accepted R1 behaviour | this doc |
| my-earnings URL is `/expense/my/` while sidebar label says "My Earnings" — fine via sidebar; direct-URL guessers 404 | Cosmetic; URL renames churn bookmarks | this doc |

## 4. AI Pattern Intelligence idea-register additions from this audit

- **I-3 (added to blueprint §12):** the E-1 lesson — *offer concrete existing
  options, never abstract dimension pickers*. The marker room must list real
  candidate markers ("M1 · tube 17″ · S2:M2:L1 — 84.8%, used on 3 Addas"), not
  width/ratio form fields with a matching table beside them.

## 5. FINAL READINESS REPORT

**Verdict: READY TO FREEZE.** I genuinely believe the manufacturing platform is:

1. **Architecturally complete.** One engine, 4 independent concerns
   (allocation / cost / earning / settlement), single-writer services, append-only
   history, frozen rate/cost snapshots, verify-confirms-or-reduces, audited void
   as the only upward path. The 100-product verdict held for the third product
   with ZERO engine code: the real 3-Patti flow was pure config.
2. **Business-complete for the in-house knitwear set.** All three real flows
   (T-Shirt 16 ops · Lower 13 · 3-Patti 12) proven END-TO-END with money identity
   exact (₹801.00 / ₹344.25 / ₹633.00 = A360 = draft = SWA = ledger = per-worker
   items = hand calculation). Known future business (washing, printing, job-work,
   bundles, attendance/min-wage) is deliberately REGISTERED, not built
   (ops-master §7/§11) — per owner rulings.
3. **Production-ready** with two explicit, owner-controlled gates left:
   **(a) the real rate card** (all rates are DEV placeholders — engine treats
   them as data; entering them is the flow editor, no code), and
   **(b) enforcement flags stay OFF** (`ENFORCE_ALLOCATION_BOUND`,
   `ENFORCE_SETTLEMENT_RECONCILIATION`) per the rollout policy — R11 rework is
   the registered prerequisite of the permanent flip. Gate suite: **885/885 OK**
   after every change today. Dev-runserver-only caveats (template cache →
   restart) are deploy-runbook items, not product gaps.
4. **Ready to be the permanent foundation for AI Pattern Intelligence.** The
   seams the blueprint consumes are live and clean: ProductPattern masters,
   CuttingPatternRecord + photos, CuttingPatternSizeAllocation, LayeringRecord
   (plies × lay length + verified widths), APSCPB piece truth, machine/timestamps
   telemetry — and nothing else writes those tables. 3-PATTI-016 already serves
   as the grounded worked example for the future MarkerOutcome math (blueprint §12 I-2).

**Recommended freeze sequence:** owner enters/sends real rate card → one
re-validation pass of the three settled journeys' money identities at real rates
→ declare **FREEZE** → checkpoint commit (whole tree, checkpoint policy) →
**AI Pattern Intelligence kickoff** (blueprint review → ADR pack → P0).

*Post-freeze rule (inherited): frozen modules change only by owner-approved
ADR/amendment; config (products, flows, rates, stages, machines, skills) remains
freely editable — that is the design.*
