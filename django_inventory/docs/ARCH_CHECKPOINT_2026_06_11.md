# Architecture Checkpoint — post-validation health assessment (2026-06-11)

Requested by owner after the validation cycle closed (all 5 scenarios, full Adda
cycle, parity stable, fix-before-P3 board empty). Assessment only — no work
proposed. Companion: SOAK_TRACKER.md (evidence), REMEDIATION_SCORECARD.md (M7
baseline), ERP_MASTER_CONTEXT_REVIEW.md (the founding review).

## 1) Current architecture scorecard (M7 baseline → today)

| # | Dimension | M7 | Today | Driver |
|---|---|---|---|---|
| 1 | Architecture | 8.7 | **8.9** | R1 contracts + ADR-0007 locked; survived end-to-end validation unchanged |
| 2 | Scalability | 8.5 | **8.5** | unchanged; known cliffs documented (mgmt dashboard pagination, costing aggregates) |
| 3 | Maintainability | 8.4 | **8.5** | R0 doc-truth + tracker discipline; still capped by stage_views god-file (Phase 8 parked) |
| 4 | Extensibility | 9.0 | **9.0 (proven)** | two real schemas through one renderer, live; synthetic-handler proof |
| 5 | Tech Debt | 8.3 | **8.5** | F3/F8 removed lifecycle ambiguity; purity chore fixed; honest minus: mypy island 211→242 |
| 6 | RBAC/Security | 8.8 | **8.8** | isolation validated live (403 sweep, cross-worker payroll); F7 policy duplication holds it at 8.8 |
| 7 | Data Integrity | 9.0 | **9.0** | freeze immutability + correction independence + parity now witnessed |
| 8 | Coupling | 7.8 | **8.7** | P4.2 executed; tracking↔production cycle gone; production→expense dies at V2-3 |
| 9 | Observability | 8.3 | **8.3** | unchanged; deploy-time bundle pending |
| 10 | Testing/Gates | 8.5 | **8.8** | 445 tests, 5/5 gates incl. live parity, lifecycle characterized, browser-validated |

All 10 dimensions in the locked 8.5–9 target band (ADR 0006).

## 2) Risks that still worry me most
1. **The dual-money-surface window.** Every allocation made before V2-2 adds
   allocation-era ledger rows the cutover must coexist with. ADR-0007 makes this
   safe, but the window's LENGTH is the risk — the longer real usage runs pre-V2-2,
   the bigger cohort A gets and the more mixed-Adda settlements V2-2 must label.
2. **Deploy blockers are security-shaped.** A casual first deploy ships a rate
   limiter that silently doesn't work (LocMem per-process) and a password hasher
   missing from requirements. The PD PR is small; skipping it would be invisible
   until it matters.
3. **reverse_settlement gap stays live until V2-2.** A wrong PayrollSettlement
   permanently reduces advance outstanding. Manual-ops caution is the only guard.
4. **Single-operator risk.** One dev DB, one owner, no CI, backups asserted but
   not rehearsed. Process risk, not code risk — but it dwarfs most code risks.
5. **Real-worker adoption.** English-only, online-only, phone-based reporting in
   a factory. The architecture validated; the human interface hasn't.

## 3) Top 5 future rewrite risks
1. **Stage-key hardcoding compounds** (~30 sites, 4 template elif chains, per-stage
   view modules). Contained by the registry-only rule + markers, but every stage
   shipped on the old pattern raises taxonomy-refactor cost.
2. **Pre-V2-2 settlement history accumulates** — each real PayrollSettlement made
   before the WRAP split is a row V2-2 must re-home semantically (nullable FK
   seam exists; volume is the risk).
3. **Offline/connectivity reality.** The report flow assumes online. If the
   factory floor needs offline-first, that's a genuine retrofit — never scoped,
   never seamed. The closest thing to an unexamined assumption in the system.
4. **attributes JSONB seam is locked but unproven** — the first machine stage may
   stress the contribution model in ways the design review didn't predict.
5. **Worker-facing language/i18n** — zero strategy; templates are English with
   Hinglish comments. If Hindi UI becomes mandatory for adoption, it touches
   every worker surface.

## 4) Where we may still be OVER-engineered
- **The `verified` task status**: five statuses, but nothing writes `verified`
  (no service, no UI) — designed-in optionality carried as dead weight until a QC
  workflow exists.
- **The embedded worker-report route**: built to D1, but nothing iframes it; the
  badge links to the standalone page. Speculative until the dashboard embeds it.
- **Documentation apparatus**: heavy for a solo project — though this very cycle
  (R0 catching doc-drift, the review building on locked docs) is the
  counter-argument. Borderline, net positive so far.
- Honest overall: remarkably little. ADR 0006 discipline held.

## 5) Where we may still be UNDER-designed
- **Management operational surfaces** — corrections (F5), readiness (F6), reopen
  visibility: worker UX got pt.2b polish; manager UX runs on workspaces + shell.
- **A form-feedback convention.** Two independent silent-failure finds
  (user-create stall, draft drop) = systemic gap, not coincidence. No global
  "every save tells you what happened" rule exists.
- **Operational runbook.** Flag-flip procedures, parity-failure repair, backup/
  restore, reopen policies — all exist, scattered across six docs. No single
  ops document a non-author could follow.
- **Concurrency under real load** — select_for_update is placed correctly, but
  nothing has ever run with 10 simultaneous users.

## 6) Would I change any major decision, starting again today?
**No locked decision would I reverse.** Option B (checked against the live dual
surface — correct), task/contribution split (proven under multi-worker churn),
dual-write migration strategy (parity machinery paid for itself five times this
week), per-stage typed records over generic JSON (the gates and cost freeze
depend on it), expense as a separate app (made P4.2-style extraction thinkable).
Two **sequencing** regrets, not architecture regrets: (1) the worker report UI
should have been built before the manager workspaces matured — worker-first
ordering would have surfaced F1/F3-class issues weeks earlier; (2) the legacy
`/cutting/` complete form should have died when the workspace shipped — it now
exists only as F7's worst offender.

## 7) Validation evidence that INCREASED confidence most
**Parity OK five consecutive times, including immediately after the F3/F8
lifecycle change landed.** The dual-write machinery absorbed assignment churn,
multi-worker reporting, auto-cancellation, and a data migration without a single
divergence — that is precisely the evidence V2-1d's point-of-no-return needed.
Close second: the dual money surface behaving exactly as documented (ledger ₹135
vs expected ₹150, never crossing; payroll reading only the ledger) — ADR-0007's
premise observed in the wild, not just asserted.

## 8) Validation evidence that DECREASED confidence most
**The silent-failure pattern.** Two unrelated surfaces swallowed user input with
a success-shaped outcome (user-create's dead click, layering's "Draft saved" over
dropped rows). Both fixed/logged — but two independent occurrences in one day of
developer-driven use predicts more under real-worker use. This is a UI-convention
debt, not an architecture defect, and it is the most likely source of true-soak
noise. Second: doc-drift recurred even after R0 (the "mandatory-rate flow editor"
that isn't; the scan→mark_status diagram) — the doc-accuracy guard covers only
some surfaces, and claims outside its reach decay.

## Verdict
The foundation is validated, in-band on every dimension, and carrying no known
architectural defect. What remains between here and V2-1d is operational
(deploy, onboard, soak, rehearse) plus a small UX-policy backlog (F4–F7), and the
two watch-items above (silent-failure convention, dual-surface window length)
are the things to keep eyes on during true soak.
