---
id: worker-profile-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# WorkerProfile architecture audit (owner-ordered roadmap pause, 2026-07-05)

> Read-only audit of the `WorkerProfile` model, its writers, consumers, and
> the worker-identity concepts that overlap it. Method: full writer/consumer
> greps (cited) + the R4/R5 hostile-review baseline.
> **RESOLUTION (same day, owner "continue" = recommendations applied, gate
> 800):** WP-A → docstring corrected (informational-only) · WP-B → worker-
> detail Status badge reads `User.is_active` (browser-proven "Inactive" on
> the F&F exemplar); profile flag documented legacy/display-only · WP-C →
> identity boundary documented in GLOSSARY + expense README (phone prefill
> NOT built — unconfirmed optional). Findings below = the original analysis.

## 1) The model today (expense/models.py)

| Field | Purpose | Verdict |
|---|---|---|
| `user` O2O PROTECT | identity anchor; profile is `get_or_create`-on-demand (no backfill ever needed) | sound |
| `pay_basis` (R4) | piece_rate \| monthly — THE money-structure lever | sound; sole writer `set_pay_basis` (audited, lock-5374-joined), form excludes it, admin readonly — re-verified |
| `phone`, `bank_*`, `upi_id`, `joining_date`, `notes` | payout metadata, display-only | sound (see WP-C) |
| `opening_advance` | *"seeds Advance Outstanding for loans given before the system"* (docstring) | **WP-A: docstring overclaims — the field is DEAD in business logic** |
| `is_active` | profile-level active flag | **WP-B: duplicate/contradictory vs `User.is_active`** |

## 2) Writers (complete census — greps 2026-07-05)

| Writer | What it writes | Discipline |
|---|---|---|
| `WorkerProfileForm.save()` (profile edit page) | payout metadata fields ONLY (explicit field list; `pay_basis` excluded) | single-row, sanctioned |
| `payroll_service.set_pay_basis` | `pay_basis` + `WorkerPayBasisAudit` row | sole writer, super-admin, audited, race-locked |
| lazy `get_or_create` sites (profile edit, pay-basis view, cash settlement, adda-settlement finalize) | row CREATION only (defaults) + row LOCKS for money serialization | sound — creation is not mutation |

No rogue writers. The R5 payment-path census result stands.

## 3) Findings

### WP-A — `opening_advance` is dead code with a misleading docstring (LOW)
Grep: consumed NOWHERE except the admin list column and the edit form. No
money math reads it — `advance_outstanding` = Σ `WorkerAdvance` − recovered,
with no opening term. The FORM hint already tells the truth ("Informational.
To make a pre-system advance recoverable, also record it as a dated
Advance") but the MODEL docstring claims it "seeds Advance Outstanding" —
false. Options: (a) fix the docstring to "informational only" (recommended,
zero risk); (b) actually add it to the outstanding math (money change —
needs its own mini-phase + tests); (c) drop the field (migration; loses
recorded history — against the data principles).

### WP-B — two `is_active` flags disagree after F&F (LOW/MED, real confusion)
`WorkerProfile.is_active` is consumed ONLY by the worker-detail "Status"
badge (worker_detail.html:73). F&F (and the user admin) flip
**`User.is_active`** — the profile flag stays True, so an exited worker's
payroll page shows "Status: Active" while their login is dead. Options:
(a) point the badge at `viewed_worker.is_active` and demote the profile flag
to unused (recommended — one-line template change + docstring note);
(b) sync both in F&F (two sources of truth — worse); (c) drop the profile
field later with (a) as the first step.

### WP-C — duplicate identity concepts across User ↔ WorkerProfile (LOW, by design but document)
- `User.phone_number` (accounts form) vs `WorkerProfile.phone` (payroll form)
  — two phones, independently editable, no sync.
- `User.salary` (reference salary; L-3 — now the salary-expense prefill) vs
  `pay_basis` on the profile — related concepts split across models.
This split is historical (profile = payroll-owned metadata, ADR-boundary
clean). Recommendation: keep the split but document it in GLOSSARY + the
expense README ("payroll contact/payout data lives on the profile; account
identity on User"), and optionally prefill profile.phone from
User.phone_number at lazy-create (convenience, not sync).

### Clean (re-verified)
- `pay_basis` chain: R4/R5 guarantees intact (sole writer, audit rows
  reconstruct history, monthly exclusions all guard-tested — gate 800 green).
- Profile locking order in settlements (5374 → profile rows) unchanged.
- No PII leak: bank/UPI render only on management-gated pages.

## 4) F&F deliverables status (owner asked re-verification, not redo)
The 8-scenario business audit + the canonical
[fnf_business_flow.md](LEARNING_2_0/DATA_FLOWS/fnf_business_flow.md) were
delivered and accepted post-R7. They remain accurate after R8: the guarantees
are pinned by `test_r7_fnf` (9 tests) inside the passing 800-test gate; the
R8 teardown removed the DEV *exemplar rows* (owner C-1) but the doc cites
them as a dated verification record, which stays true. One doc-level note
added by THIS audit: WP-B above is exactly the "deactivation blocks login
only" §31.2 story leaking into a stale profile badge.

### Verification sources
Greps: opening_advance / profile.is_active / profile.phone / WorkerProfile.objects
writers (all cited above); worker_detail.html:68-73; R4/R5 receipts;
gate PASS 800. Confidence: High.
