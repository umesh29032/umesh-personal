# Owner Workflow Audit — factory operations & adoption readiness (2026-06-11)

Owner-requested, pre-deployment. NOT architecture — operations, usability,
onboarding, adoption. Constraints honored: no redesign, no new domains, no
large features, ADRs respected, mobile-first mandatory.

Evidence: live browser walks this session (worker phone 360×740: dashboard +
report screen; manager desktop: Adda start, flow editor, settlement
queue/detail, payment, My Earnings at 3 viewports) + flows built/validated
earlier (cutting workspace, advances, costing). Click counts are MEASURED
where walked, marked (est.) where derived from templates.

**Verdict up front: architecturally ready AND operationally practical — with
TWO small pre-soak UI fixes (P1/P2 below). Both close flows where a normal
human mistake silently becomes wrong pay. Everything else is training +
soak observation.**

---

## The twelve workflows

### 1) Product setup — owner/super-admin, desktop
- Screens: 2–3 (product create → sizes → patterns if used). Clicks: ~8–15 (est.).
- Mobile: management flow; form-shell responsive — fine.
- Training: owner-only, LOW.
- **Mistake:** creating a product but forgetting ProductSizes → cutting
  report's size chips render empty → worker confusion mid-stage.
- Improvement (during soak): "add sizes next" hint after product create.
- Confusion/manual work/adoption risk: minimal — infrequent task.

### 2) Workflow/stage setup — super-admin only, desktop (MEASURED)
- One screen (flow editor): visual stage strip, per-stage card with skill
  chips, billing method + rate + paid-at + Save per stage, reorder, remove.
  ~4–6 clicks per stage.
- Honest-NULL is already user-facing: red "Unpriced — set a rate" pill;
  grouping shown as "Billed at: Cutting".
- **Mistakes:** (a) forgetting a rate → unpriced (surfaced, never ₹0 — good);
  (b) misunderstanding "paid at" grouping — C-1's guard now makes the
  dangerous version (double-pay) impossible, so the residual is cosmetic.
- Confusion spot: pay-eligibility (credits_workers) isn't visually prominent
  per card — training item; TM-1's dropdown will land on this same card.
- Adoption risk: LOW (one person, infrequent).

### 3) Adda creation — manager (MEASURED)
- ONE screen, ONE field (product picker), code auto-allocated, race-safe.
  **2 clicks.** As frictionless as it can get.
- No mistakes available to make. Adoption risk: none.

### 4) Worker assignment — manager, workspace Section 01
- Path: dashboard → Adda → stage workspace → worker chips → save. 3–4 taps +
  picks (est.).
- **Mistakes:** (a) expected worker missing from the pool → cause is a missing
  skill, fixed in Access Control hub — managers won't guess that (TRAINING
  ITEM #2; F7's pool definition is the locked future fix); (b) roster is
  full-replace — unticking someone cancels their task (cancel-note preserved;
  re-tick re-creates). Behavior correct, needs one training sentence.
- Mobile: chips usable on tablet/phone.
- Adoption risk: MED until the skill→pool link is internalized.

### 5) Worker reporting — worker, PHONE (MEASURED — the flagship)
- Path: login → dashboard ("● Report needed" badge) → report screen → qty →
  SUBMIT & COMPLETE WORK. **~4 taps + typing.**
- Screen quality: numbered panels, plain language ("What did you make?"),
  large numeric input, sticky Submit/Draft CTAs, locked state after submit.
  Genuinely strong on 360px.
- Training: LOW — one demonstration covers it. Highest-leverage training
  sentence: **"Draft is not submitted. Only SUBMIT counts."**
- **Mistakes:**
  - (a) **Save Draft, never Submit → stage completes → task auto-cancels →
    NO PAY.** Correct by design (F3/F8) but brutal silently — see P2.
  - (b) Wrong quantity submitted → worker cannot edit (locked, by design) and
    **management has NO UI lever to correct it** (verified_quantity exists in
    the model, F5 surface was parked) → settlement pays the wrong number.
    See P1 — the single most important pre-soak fix.
  - (c) Over-reporting (no expected-quantity hint — intentional, §5
    visibility rule): caught only by the manager's eye until
    MissingPiece/variance reporting.
- Adoption risk: the #1 overall (will workers report at all) — that is what
  the soak measures; the screen itself is not the obstacle.

### 6) Stage completion — cutting master/manager
- Workspace → Mark Complete (+ cutting's completion validations). 2–3 clicks
  after work entry (est.). Cutting workspace itself is the system's most
  complex screen (breakup, verification, bundles) — cutting-master training
  is the LONGEST item (~an hour with a real Adda), everyone else's is minutes.
- **Mistake:** completing while workers still have drafts/unreported tasks →
  silent auto-cancel of their pay eligibility. No warning shown today (F6
  readiness panel was parked). See P2.
- Adoption risk: MED — one impatient completion can cost a worker's pay and
  the system's credibility in week one.

### 7) Settlement preparation — accountant/manager (MEASURED this session)
- Payroll → Adda Settlements: queue shows READY (with workers/lines/expected ₹)
  vs WAITING (with the exact blocking stage names). Start settlement → draft
  preview: per-worker lines, ✓ on verified quantities, variance inputs,
  per-advance recovery inputs, three labeled line classes with plain-language
  "why excluded". **3–4 clicks to a reviewable draft.**
- Confusion spots: era-A exclusions (labeled, will fade); variance fields
  skipped → zeros (acceptable until MissingPiece; training: "count packed
  before settling").
- Manual-work hotspot: variance counting stays manual by design until
  MissingPiece — named, scheduled.

### 8) Settlement execution — accountant/manager (MEASURED)
- Finalize = 1 click + confirm. Mistake recovery = Reverse / Reverse & settle
  again, also 1 click + confirm + notes; chain banner shows the history.
- **Training item #1 (accountant): settlement ≠ payment.** Settle the Adda
  (books earnings + recovers advances), THEN pay cash per worker. Every screen
  label now reinforces it; the refusal message on the payment screen catches
  the old habit loudly.
- **Mistake:** finalizing before quantities were verified — same root as 5(b);
  P1 gives the lever, training gives the habit ("check the draft's ✓ marks").
- Adoption risk: LOW-MED with the two-step model trained.

### 9) Advance management — manager/accountant
- Record Advance: one screen, ~4 fields (est. 5–6 clicks). Worker detail shows
  outstanding; recovery happens ONLY in the settlement draft (per-advance
  inputs, capped at remaining).
- **Mistake:** trying to recover at payment (old habit) → refused with a
  pointer to Adda Settlements ✓ (built + tested this session).
- Adoption risk: LOW.

### 10) Payment flow — accountant (MEASURED)
- Worker detail → Pay → amount prefilled with pending payable → method →
  Confirm Payment. **3 clicks.** Overpay blocked client+server; recovery
  inputs gone; advances shown info-only with a link to settlements.
- Adoption risk: LOW — this is the simplest money screen.

### 11) Adda tracking — owner/manager
- Today: story spans dashboard → Adda detail/workspace → settlement screens →
  costing. 3–4 screens to assemble one Adda's picture. KNOWN gap — G4 thin
  slice is scheduled DURING soak precisely as the fix; nothing else needed.
- Mobile: each piece responsive; the composition is what's missing.

### 12) Cost visibility — owner/accountant
- Costing dashboard: per-Adda manufacturing cost + worker earnings side by
  side, honest-NULL unpriced-stage pills, NEW C-1 red banner + per-Adda
  "unpriced rolls — material cost incomplete" lines.
- **Confusion spot: the duality.** Standard cost vs worker earnings side by
  side invites mental addition — ADR-0009 fences the code; the HUMAN needs
  one explanatory line on the page. See P3.
- Adoption risk: LOW (read-only); wrong mental models are the risk, not clicks.

---

## Persona summaries

| Persona | Surface | Training | Biggest risk |
|---|---|---|---|
| **Worker** | dashboard + report + My Earnings (3 screens, phone) | ~10 min + one demo | draft-vs-submit; will-they-report-at-all (the soak question) |
| **Manager** | assignment, stage ops, settlements | ~1–2 hrs | impatient stage completion (P2); skill→pool confusion |
| **Accountant** | settlements, advances, payments, costing | ~1 hr | settlement≠payment model; trusting drafts without quantity check (P1) |
| **Owner** | everything + flow editor + costing | self-taught (built it) | none — but G4 absence means owner assembles stories manually until soak |
| **Cutting master** | the cutting workspace | longest (~1 hr, real Adda) | workspace complexity — unavoidable, it mirrors the real job |

## Cross-cutting adoption risks (no code change proposed)

- **Accounts/passwords:** pre-provisioned users; workers WILL forget passwords
  → owner resets. Needs a 3-line runbook entry + long session lifetime
  consideration on phones (settings-level, deploy decision).
- **Language:** UI is English; worker screens use simple words but training
  cards in Hinglish will carry the day. Not an i18n project — a training
  artifact.
- **Connectivity:** no offline mode; factory WiFi dead spots = lost form input.
  Observe during soak before considering anything.
- **Shared phones:** if workers share a device, isolation rules hold (own-task
  gating), but logout discipline needs one training sentence.

## Pre-soak fix list (small, UI-only, zero architecture)

| # | Fix | Why it can't wait | Size |
|---|---|---|---|
| **P1** | **F5-lite: verified_quantity management surface** — a management-only "verified qty" input per contribution (stage workspace or the locked report view). The model field, the settle-uses-verified-else-reported logic, and the draft's ✓ marks ALL exist; only the input is missing. | A wrong worker report currently has NO UI correction path before money books — the only honest lever is shell access. This converts the most likely human error (typo'd quantity) from "wrong pay" to "two taps". | ~half session |
| **P2** | **F6-lite: stage-complete confirmation dialog** listing workers with draft/unreported tasks — "these N workers will be auto-cancelled (no pay eligibility): …" | One impatient Mark Complete in week one silently strips a worker's pay and torches trust in the system. The data for the dialog already exists on the stage record. | small |
| **P3** | One explanatory line on the costing dashboard: "Manufacturing cost (standard) and worker earnings (actual) are two views of the same labor — never add them." | ADR-0009 fences code, not human mental models; the two columns sit adjacent. | one template line |
| P4 | Runbook entries (no code): worker password reset procedure; session-lifetime decision for phones; Hinglish one-page training cards per persona (worker card = 5 lines). | Deploy-week operational reality. | docs only |

Everything else observed (size-hint after product create, settlement-queue→
workspace nav link, etc.) goes on the DURING-SOAK list — collect real friction
before polishing imagined friction.

## Final verdict

**Architecturally ready: yes (established previously). Operationally
practical: yes — conditionally on P1+P2.** The worker phone flow — the
make-or-break surface — is genuinely excellent: 4 taps, plain language, big
targets, honest states. Money flows are 2–4 clicks with loud refusals on every
wrong path. The two conditions are the two places where a NORMAL mistake
(typo'd report, impatient completion) currently produces silent pay damage
with no UI remedy; both are half-session UI fixes consistent with parked
F5/F6 directions, no architecture touched. Recommend: ship P1+P2+P3 as one
small pre-deploy PR, write P4 runbook entries during deploy week, then deploy.
