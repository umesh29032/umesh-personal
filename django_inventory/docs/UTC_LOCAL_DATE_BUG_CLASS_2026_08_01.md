---
id: utc-local-date-bug-class-2026-08-01
type: receipt
status: active
owner: append-only
scope: expense, bod, inventory, production — date bucketing across the whole codebase
anchors: config/expense/services/settlement_service.py, config/bod/widgets.py, config/expense/views.py
verified: 2026-08-01
---

# UTC-vs-IST date bug class + the battery definition gap (2026-08-01)

> **How this was found:** a hostile verification agent was asked to REFUTE the claim
> "full test battery 1953 green". It refuted it. Two independent problems fell out —
> one about what "full" means, one a real date-correctness bug class.
> **Nothing in this document was fixed.** The money sites are reported under the
> owner's Money-Write STOP Rule, not silently changed.
>
> **↑ THAT SENTENCE IS SUPERSEDED — see §6, then §7.** The owner ruled *"fix the issue
> if it is really one"* on 2026-08-01. It was really one.
>
> **⚠️ READ §7 BEFORE TRUSTING §6.** §6 claimed 10 sites and "none remain" — that was
> **wrong**, because the sweep behind it grepped for one literal text shape. An AST
> re-review (§7) found **6 more**, including the ledger `entry_date` in the *primary*
> Adda settlement path. **True total 16 sites; 5 touch money records, not 3.**
> Final state: all 16 fixed, guard rewritten AST-based with a meta-test, `bod` inside
> the battery, **1994 green across all 14 installed apps**.
> §1–§6 are kept verbatim (append-only: findings are not rewritten once superseded).

## 1. The battery definition gap (my claim was wrong)

**Claimed:** "full battery 1953 green" = 1206 (10 apps + learning) + 528 patterns_ai
+ 141 devseed + 78 verification.

**Reality:** project-wide discovery is **1990**. The 37-test delta is exactly the
**`bod`** app, which is in `INSTALLED_APPS` (`config/config/settings/base.py:82`) but
appears in none of the four groups anyone runs.

```
project-wide discovery: 1990
  production 685 · patterns_ai 528 · expense 241 · devseed 141 · verification 78
  learning 56 · accounts 55 · raw_materials 44 · tracking 40 · inventory 38
  bod 37 · core 19 · machines 17 · storefront 11
1990 − 1953 = 37 = bod
```

**This is not new.** The project's own historical baselines excluded `bod` too
(`1878 = 1132 + 528 + 140 + 78`, and the later `1896`). The gap was inherited and
repeated, not introduced. But it means **an installed app has been outside the
release gate**, and it is currently RED:

```
FAIL: test_money_tiles_equal_their_source_pages
      (bod.tests.test_widgets_money.MoneyCrossCheckTests)
AssertionError: Decimal('1750.50') != Decimal('0.00')
Ran 37 tests in 6.268s — FAILED (failures=1)
```

**Action needed:** the battery definition must include `bod` (making it 1990), or
`bod` must be explicitly and visibly excluded with a reason. Silent exclusion is the
worst of the three options.

## 2. Why that test fails — a genuine date bug, not a flaky test

Settings: `TIME_ZONE = 'Asia/Kolkata'`, `USE_TZ = True` (`base.py:246,248`) — so the
database stores UTC and every user-facing value should be converted to IST.

Two code paths bucket "this month" on **different clocks**:

| Site | Call | Clock |
|---|---|---|
| `config/bod/widgets.py:163` | `timezone.localtime()` | **IST** (correct) |
| `config/expense/views.py:415` | `timezone.now().date()` | **UTC** (wrong) |

Measured at the moment of the audit:

```
bod  localtime()      -> 2026-08-01 01:27:31+05:30  => month (2026, 8)
expense now().date()  -> 2026-07-31                 => month (2026, 7)
SAME MONTH? False
```

So the BOD money tile reports **₹1750.50** for August while its own source page
reports **₹0.00** for July. The cross-check test comparing tile-vs-page is doing its
job correctly — it caught a real divergence.

**IST is UTC+05:30, so every day between 00:00 and 05:30 IST the UTC date is one day
behind.** On the 1st of a month, that is a whole month behind. The test therefore
passes mid-month and fails on boundaries — it has been a latent flake with a real bug
underneath it the whole time.

## 3. The bug CLASS — eight sites, three of them on money records

`timezone.now().date()` returns a **UTC** date. In an IST-displaying app that is
almost always the wrong primitive; `timezone.localdate()` is the correct one.

| # | Site | What the date decides | Severity |
|---|---|---|---|
| 1 | `expense/services/settlement_service.py:110` | **`settlement_date` written onto `PayrollSettlement`** | ⚠️ money record |
| 2 | `expense/services/allocation_service.py:144` | **`entry_date` on a ledger entry** | ⚠️ money record |
| 3 | `expense/services/advance_service.py:44` | **advance date** | ⚠️ money record |
| 4 | `expense/views.py:415` | default month of the expense list page | display (causes the red test) |
| 5 | `expense/views.py:72` | start-of-current-month filter | display |
| 6 | `expense/views.py:260` | `ctx['today']` into the template | display |
| 7 | `inventory/views/dashboard.py:262` | dashboard "today" | display |
| 8 | `production/services/operations_digest.py:80` | `completed_at__date=` filter — work done 00:00–05:30 IST is bucketed to the previous day | reporting |

**The money sites are reachable in normal use, not theoretical.**
`settlement_date` is a `forms.DateField(required=False)` (`expense/forms.py:49`), so
leaving the field blank takes the `or timezone.now().date()` fallback. A settlement
finalised at 01:00 IST on the 1st is therefore stamped with the **previous month's**
last day. Same shape for advances and ledger `entry_date`.

Only one place in the entire codebase currently uses the correct primitive:
`config/learning/progress_service.py` (`timezone.localdate()`).

## 4. Recommended fix — NOT APPLIED, owner decision required

The **Money-Write STOP Rule** (owner standing rule, 2026-07-05) says a problem on a
money path is reported, never silently fixed. Sites 1–3 stamp dates onto financial
records, so they stop here.

Recommendation, for the owner to rule on:

1. **Sites 1–3 (money records):** replace `timezone.now().date()` with
   `timezone.localdate()`. The factory's books run on IST; a settlement made at 01:00
   IST on 1 August belongs to August. **Owner must confirm** — if any external
   reporting has already been reconciled against the UTC-stamped dates, changing the
   primitive changes which period historical-adjacent records land in. Existing rows
   are NOT rewritten either way (append-only history, `feedback_data_history_principles`).
2. **Sites 4–8 (display/reporting):** `timezone.localdate()` is unambiguously correct;
   low risk.
3. **Add a lint/test pin** so `timezone.now().date()` cannot come back — the correct
   form is `timezone.localdate()`. One grep-based test would hold the whole class.
4. **Fix the battery definition** to include `bod` (1990), or exclude it visibly.

Until 1–3 are ruled on, `bod` stays red on month boundaries. That is the honest state:
**a real bug is being reported by a working test.** Making the test pass by weakening it
would be the wrong repair.

## 5. What this says about the audit itself

The claim "1953 green" was assembled from four groups I chose, and the group list was
inherited rather than derived from `INSTALLED_APPS`. **A battery is only a gate if its
membership is derived from the code, not from a remembered list.** That is the durable
lesson, and it is the same shape as the learning-platform lesson from the same session:
*count what the system actually contains, not what you remember it containing.*

---

## 6. RESOLVED 2026-08-01 — owner ruled "fix the issue if it is really one"

It was really one. Verified, then fixed. **10 sites**, not the 8 in §3 — a wider sweep
(`now().year/.month/.day`, `date.today()`) found two more.

| # | Site | Before | After |
|---|---|---|---|
| 1 | `expense/services/settlement_service.py:110` | `settlement_date or timezone.now().date()` | `… or timezone.localdate()` |
| 2 | `expense/services/advance_service.py:44` | `advance_date or timezone.now().date()` | `… or timezone.localdate()` |
| 3 | `expense/services/allocation_service.py:144` | `entry_date or timezone.now().date()` | `… or timezone.localdate()` |
| 4 | `expense/views.py:72` | `timezone.now().date().replace(day=1)` | `timezone.localdate().replace(day=1)` |
| 5 | `expense/views.py:260` | `ctx['today'] = timezone.now().date()` | `… = timezone.localdate()` |
| 6 | `expense/views.py:415` | `today = timezone.now().date()` | `today = timezone.localdate()` |
| 7 | `inventory/views/dashboard.py:262` | `today = timezone.now().date()` | `today = timezone.localdate()` |
| 8 | `production/services/operations_digest.py:80` | `completed_at__date=timezone.now().date()` | `…=timezone.localdate()` |
| 9 | `production/stages/barcode_generation/export_service.py:90` | `year = timezone.now().year` | `year = timezone.localdate().year` (**new find** — a barcode export batch code would carry the previous year for 5.5h on 1 January) |
| 10 | `production/views/stage_views.py:700` | `_date.today()` | `timezone.localdate()` (**new find** — Python's `date.today()` reads the SERVER clock, not `TIME_ZONE`; on a UTC container it is the same bug by another route) |

`_date` is still imported there for `fromisoformat` — no dead import left behind.

### Why `localdate()` is the correct primitive here

Site 8 proves it. Django's `__date` lookup **converts a `DateTimeField` to the current
timezone before extracting the date** when `USE_TZ=True`. So `completed_at__date` was
already IST while the value compared against it was UTC — the two sides of one filter
disagreed. Both are local now.

### Existing rows were NOT rewritten

Append-only history principle: any settlement/advance/ledger row already stamped with a
UTC-derived date keeps that date. This fix changes only what **future** writes record.
No data migration, no backfill.

### One test was encoding the bug — corrected, not weakened

`production/tests/test_g4_status_reads.py` pinned its fixture to **noon UTC on the UTC
date** with a comment describing the mismatch as "pre-existing dashboard semantics,
preserved verbatim". That fixture only matched while the filter was also UTC, so it went
red the moment the filter was fixed. The fixture now builds **noon local** via
`timezone.make_aware(datetime.combine(timezone.localdate(), time(12, 0)))`, so both
sides are local and the "no midnight straddle" property is kept. **The assertion was not
relaxed** — three tests failed, and all three failed for the right reason.

### The pin, so the class cannot come back

`config/core/tests.py :: LocalDateGuardTests` — repo-wide, alongside the existing
architecture guardrails:
- `test_no_utc_date_used_as_a_local_date` — scans every non-test, non-migration `.py` for
  `timezone.now().date()`, `.year`, `.month`, `.day` and `date.today()`, and names every
  offender with a pointer to this document.
- `test_localdate_is_actually_local_not_utc` — asserts `TIME_ZONE` really is
  `Asia/Kolkata` and that `localdate() - now().date()` is 0 or +1 day, so the mandated
  primitive is proven rather than trusted by name.

### Battery definition FIXED — `bod` is inside the gate now

`bod` (37 tests) was in `INSTALLED_APPS` but in none of the four groups anyone ran, so an
installed app sat outside the release gate through the `1878` and `1896` baselines. It is
now included.

**New baseline: 1992 green, zero failures, all 14 installed apps**
= 1245 (accounts core inventory raw_materials production tracking expense machines
storefront learning **bod**) + 747 (patterns_ai devseed verification).
That is the previous project-wide 1990 plus the 2 new guard tests.

**Rule going forward: derive the battery from `INSTALLED_APPS`, never from a remembered
list of app names.** That was the actual root cause of the gap.

---

## 7. RE-REVIEW 2026-08-01 (owner: *"review please again, i cant take risk"*) — §6 WAS INCOMPLETE

The §6 claim *"10 sites, none remain"* was **wrong**. The sweep that produced it grepped
for the literal text `timezone.now().date()`, so it was blind to two other shapes. An
**AST** sweep found **5 more**, and fixing one of those exposed a **6th**.

**True total: 16 sites.** Five of them touch money records, not three.

### The shapes the string scan could not see

| Shape | Example | Why grep missed it |
|---|---|---|
| **Via a variable** | `now = timezone.now()` … `now.date()` | no `now().date()` text anywhere |
| **Off a stored field** | `o.created_at.month` | no `timezone.` on the line at all |

### The 6 additional sites

| # | Site | What it decides | Severity |
|---|---|---|---|
| 11 | `expense/services/adda_settlement_service.py:438` | **ledger `entry_date` for every earning credit at Adda settlement finalize** | ⚠️ **money record** |
| 12 | `expense/services/adda_settlement_service.py:448` | **ledger `entry_date` for every advance-recovery debit** | ⚠️ **money record** |
| 13 | `production/services/operations_digest.py:135` | a **second** `completed_today`, on the opposite clock from line 80 — two counts in one file that could disagree | reporting |
| 14 | `learning/progress_service.py:263` | the learning **day-streak**: `seen` held UTC dates while `day` started from `localdate()`, so a learner studying at 1 a.m. saw streak **0** | display (my own code) |
| 15 | `patterns_ai/services/intelligence_service.py:138` | month-bucket **keys** for the outcome trend | reporting |
| 16 | `patterns_ai/services/intelligence_service.py:152` | the bucket **fill** (`created_at.month`) — **found only because fixing 15 made the two sides disagree and a test went red** | reporting |

Sites 11–12 are the **primary settlement path** (the Adda-centric one that actually
runs). They were the most important date-writes in the system and the first pass left
them untouched.

### Fixed with `timezone.localdate(when)`, not a fresh call

Where an instant already exists, the date is now derived **from that same instant**:

```python
when = timezone.now()                       # aware; settled_at needs the datetime
...
entry_date=timezone.localdate(when)         # same instant → can never disagree
...
settlement.settled_at = when
```

A fresh `timezone.localdate()` would be *almost* right and could differ from
`settled_at` if the clock ticked past midnight mid-transaction. `when` itself is
**unchanged** — the DateTimeFields (`settled_at`, `reversed_at`, `voided_at`) are
correct as aware UTC and were not touched.

### Site 16 is the lesson

Site 15 and 16 were **consistently wrong together** (keys UTC, fill UTC). Fixing only
15 made them **inconsistently wrong**, and `test_trend_buckets` went red immediately.
That is the failure mode to remember: *a half-fixed date basis is worse than an
unfixed one*, because agreement is what made the old behaviour survivable. Both sides
of any bucketing must move together.

### The guard was the real defect — now AST-based

`core.tests.LocalDateGuardTests` was a **string scan**, which is precisely why it
passed while 5 real bugs lived. It now walks the AST and catches four shapes:

1. inline `timezone.now().date()/.year/.month/.day`
2. **via a variable** bound to `timezone.now()`
3. **off a stored aware field** (curated `DATETIME_FIELDS` list — *extend it when you
   add such a field*; type inference is not possible here)
4. `date.today()` / `datetime.today()` (server clock, not `TIME_ZONE`)

It allows what must stay legal: `timezone.localdate()`, `timezone.localdate(dt)`,
`timezone.localtime(dt)`, and `datetime.strptime(s, '%Y-%m-%d').date()`.

Plus **`test_the_guard_actually_catches_the_shape_that_escaped_it`** — a meta-test that
feeds the guard each offending shape and each legitimate one, so a future refactor
cannot quietly weaken it back to a string scan.

### Verified

- **Battery 1994 green, all 14 installed apps, 0 failures** (1247 + 747).
- `expense` alone: 241 green — run first and separately, as the highest-risk change.
- `knowledge_sync` BLOCKER=0; graph validates.

### Honest note on the first pass

§6 stated the work was complete when it was not. The cause was a **grep whose pattern
matched only the shape already known** — the same root error as the learning-platform
defects earlier in the session (*count what the system contains, not what you remember
it containing*). **A sweep is only as wide as its pattern; use the AST for anything
that matters.**
