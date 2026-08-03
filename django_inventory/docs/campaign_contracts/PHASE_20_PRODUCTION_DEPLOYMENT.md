---
id: docs-campaign-contracts-phase-20-production-deployment
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 20 Execution Contract — Production Deployment

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md) and **the entire Phase-19 documentation set**
> ([PHASE_19_DEPLOYMENT_DOCUMENTATION.md](PHASE_19_DEPLOYMENT_DOCUMENTATION.md) → the
> refreshed `deploy/README.md` + checklists + rollback/release docs): **the runbook is THE
> procedure of record — this contract wraps it with campaign gates, evidence, and stop
> conditions; it NEVER restates or duplicates a procedure** (a deployment step exists in
> exactly one place: the runbook). Also binds: PHASE_13 (post-deploy `verify_production` =
> mandatory, VER-D8) · PHASE_14 (pre-deploy sweep) · PHASE_21 (**whose contract §6 defines
> the GO evidence pack this phase's entry gate assembles** — the spec lives in that CONTRACT,
> authored now, so no ordering paradox with 21 executing after 20) · U10 (flags stay OFF
> through and beyond this phase) · the Phase-4 protocol (a deploy-blocking defect is fixed
> THERE, never live on the server).
> **This phase owns ONLY execution:** sequencing, verification, rollback execution, rollout.
> Evidence doc (created at PD-0): `docs/PRODUCTION_DEPLOYMENT_LOG.md`.

## 1. Phase objective

Put the certified system into production: assemble and verify the GO evidence pack, obtain
the owner's recorded GO, execute the runbook verbatim (provision → transfer per the DEP-D2
ruling → deploy → migrate → initial data per DEP-D3), verify the deployment with the
campaign's own instruments (`verify_production` green IN production, runbook smoke, first
backup landed, restore drill executed once), hold the stabilization window, and hand a
complete deployment record to Phase 21 for attestation. If anything crosses a rollback
trigger, roll back per the documented mechanics and report — a deployment that retreats
cleanly is a success of the system; only an undocumented improvisation is a failure.

## 2. Scope

### 2.1 Preconditions (the GO gate inputs — all hard)

| Precondition | Source |
|---|---|
| Phase 19 closed | the refreshed runbook + checklists + tabletop verdict |
| **The Phase-21 §6 evidence pack assembled + verified** | PHASE_21's contract defines it (certifications closed · Phase-4 reconciliation · fresh full battery green · flags OFF · backlog dispositions · sweep clean/accepted · verify_production dev-mode rehearsal green · snapshot state · restore-drill plan · open-items register) — PD-0 assembles; CERT-A later re-verifies + attests |
| **Phase 0 executed** (per the DEP-D2 ruling) | deploying single-copy uncommitted work without a validated snapshot is uninsurable; if DEP-D2 chose the Phase-0-artifact transfer, the snapshot IS the deployable artifact; if the owner instead re-sequenced Phase 22, the commit exists — either way the tension is RESOLVED before PD-0, never improvised at the keyboard |
| Owner GO recorded verbatim | PD-D1 authority; no GO, no deploy — under any pressure |
| DEP-D3 initial-data ruling + DEP-D5 window + PD-D2..D8 answered | the runbook's owner gates are all closed before step 1 |

### 2.2 In / out

**In:** the GO gate · environment provisioning (runbook steps 1–3) · artifact transfer +
first deploy (steps 4–7 per DEP-D2) · initial data per DEP-D3 · post-deploy verification
(verify_production in prod + runbook smoke + backup confirmation + the restore drill,
runbook step 11) · the stabilization window · rollback EXECUTION if triggered · the
deployment record.
**Out:** ANY code/doc change (a deploy-blocking defect → STOP, rollback if needed, route to
the Phase-4 protocol, re-enter via a fresh GO — nothing is ever patched live on the server)
· runbook edits (a procedure found wrong mid-deploy = STOP + rollback decision + a dated
Phase-19 amendment; never an on-the-fly rewrite) · the R11 flag flip (post-campaign;
ENFORCEMENT_ROLLOUT_RUNBOOK) · worker credential distribution beyond the runbook's own
sequencing (after the restore drill — step 11's rule) · the attestation itself (Phase 21) ·
dev-environment anything (the dev machine is untouched by this phase except running the
GO-pack instruments).

## 3. Success criteria

Phase 20 is DONE when ALL hold:
1. The GO pack assembled, every item verified fresh, and the owner's GO quoted verbatim in
   the log — BEFORE any provisioning.
2. The runbook executed VERBATIM with a per-step execution record (step → command → output
   summary → checklist tick → operator) — zero undocumented actions; any deviation = the
   §16 stop machinery, not a footnote.
3. Migrations applied cleanly (entrypoint boot per DEP-D5); `showmigrations` consistent;
   the 16/17 additive tables present.
4. Initial data per DEP-D3 executed and recorded (clean-start entries enumerated, or the
   dump import + its provenance).
5. **Post-deploy verification green:** `verify_production` IN PRODUCTION (report envelope +
   body-hash quoted — the DEV-contamination scan, flags-vs-declaration [OFF], migrations
   consistency, integrity checks all pass) · runbook smoke complete · first nightly backup
   confirmed (`restic snapshots`) · **the restore drill executed once and passed** (runbook:
   before worker credentials go out).
6. The stabilization window (PD-D4) held with its observation record; zero unresolved
   incidents at close (an incident either resolved via rollback+re-entry or explicitly
   owner-accepted into the record).
7. Flags confirmed OFF in production (U10) — part of the verify_production evidence.
8. The deployment record complete and handed to Phase 21: GO pack refs · execution record ·
   verification evidence · stabilization outcome · any rollback events with their full story.
9. Status + memory synced every sub-phase; the dev working tree byte-untouched by this phase
   (porcelain-hash pre/post — the Phase-0 proof pattern; this phase runs instruments, it
   edits nothing).

## 4. Rules of engagement (deltas beyond U1–U14 + inheritance)

- **Verbatim or stop:** the runbook + checklists are executed as written. A step that cannot
  be executed as written = STOP (assess rollback need → report → dated Phase-19 amendment →
  fresh GO). Improvisation on a production box is the phase's cardinal sin.
- **No live fixes, ever:** defects found by the deploy → Phase-4 protocol on the dev side
  after a clean stop/rollback. The server never hosts uncommitted-to-record changes beyond
  what the artifact contains.
- **Secrets:** handled per DEP-D4 (password-manager pair); values never enter the log
  (presence/verification noted, contents never).
- **Evidence in real time:** the per-step execution record is written AS steps run (the
  worker-cert crash lesson: evidence incrementally, never reconstructed).
- **One sub-phase per session (U3) with a deployment-day exception:** PD-A through PD-C MAY
  run in one owner-attended session if the owner is present and the window (DEP-D5) demands
  it — the per-step record and STOP conditions apply identically; PD-0 and PD-D never merge
  with anything.
- The GO is single-use: any stop/rollback after GO voids it; re-entry needs a fresh GO with
  a refreshed pack (deltas verified).

## 5. Evidence standard

The GO pack (item → source → fresh-verification note → verdict) + the owner GO verbatim ·
the per-step execution record · command outputs quoted (migrations, restic snapshots,
verify_production envelope + body-hash, smoke results) · the restore-drill record ·
stabilization observations (dated entries) · any rollback: trigger → decision → mechanics
executed → post-rollback verification · the dev-tree porcelain-hash pre/post pair. All
main-thread (U7 — nothing about a production deploy is delegated to sub-agents).

## 6. Methodology

The runbook is the methodology (§4 verbatim rule). This contract adds only the campaign
wrapper per sub-phase: what gates it, what evidence it emits, what stops it. Rollback
mechanics = the DEP-D6-ratified chain (pre-deploy dump → restic restore → compose re-pin);
rollback DECISION = the PD-D3 triggers + owner voice; after any rollback, production is
re-verified to its pre-deploy state (or torn down, for a first-deploy abort) and the phase
re-enters at PD-0.

## 7. Sub-phase breakdown

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **PD-0** — GO gate | Assemble + freshly verify the PHASE_21 §6 pack (fresh full battery run included — the last pre-deploy battery); confirm preconditions §2.1 incl. the Phase-0/DEP-D2 resolution; owner GO verbatim; PD-D1..D8 answered. **Stop:** any pack item red/stale; GO absent; the artifact question unresolved. |
| **PD-A** — Environment provisioning | Runbook steps 1–3 (VPS, hardening, docker, DNS) per checklist; no application material transferred yet. **Stop:** provider/DNS reality diverges from DEP-D1 (report; owner). |
| **PD-B** — Deploy | Artifact transfer per DEP-D2 → runbook steps 4–7 (env from custody, compose up, entrypoint migrate/collectstatic, superuser) — per-step record. **Stop:** any step deviates from the written procedure; entrypoint/migration failure (assess → rollback/teardown → report). |
| **PD-C** — Initial data + verification | DEP-D3 execution + record → post-deploy verification set (§3.5: verify_production in prod, smoke, backup confirmation, **restore drill executed once**) → worker credentials only after the drill passes (runbook rule). **Stop:** verify_production red (its exit code is authoritative — diagnose from the report, never "probably fine"); drill failure. |
| **PD-D** — Stabilization + close | The PD-D4 window: observation record, rollback triggers armed, incidents handled per §6; at window end — the deployment record completed + handed to Phase 21; dev-tree untouched proof; PHASE-20 VERDICT (DEPLOYED-STABLE / ROLLED-BACK-with-story). **Stop:** an unresolved incident at window end (the window extends or the cord is pulled — owner). |

## 8. Deliverables

- A running, verified production system (or a cleanly rolled-back one with its complete
  story — both are valid phase outputs; only an undocumented state is not).
- The deployment record (GO pack + execution record + verification evidence + stabilization
  outcome) — Phase 21's primary input.
- `docs/PRODUCTION_DEPLOYMENT_LOG.md` (the record's home) · status + memory per sub-phase.
- Filled Design Record (PD-D1..PD-D8) + the verbatim GO.

## 9. Files expected to change

**Docs only (dev side):** `docs/PRODUCTION_DEPLOYMENT_LOG.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · this file (Design Record + amendments) · memory
files. **Production side:** the server per the runbook (its state is the phase's product,
not a "file change"). **NOTHING else on the dev side** — no code, no runbook edits (dated
Phase-19 amendments only, via that contract), no `.env` edits, no docs beyond the log; the
dev working tree's porcelain hash is proven unchanged.

## 10. Files that must never change (touching one = STOP + report)

- The ENTIRE dev working tree outside §9's three doc touchpoints — this phase deploys the
  tree; it does not edit it (porcelain-proof enforced).
- `deploy/README.md` + scripts DURING the phase (amendments = Phase-19's dated process,
  between attempts, never mid-run).
- Enforcement flags — OFF, verified, untouched (U10; R11 is post-campaign).
- Production data beyond the runbook's own steps (no manual DB surgery, no shell writes on
  the server outside documented steps).
- The PRIMARY dev DB · the snapshot artifacts (read/transfer only) · the 2 stashes · `.git`
  state (U2 — unless the owner's DEP-D2 ruling re-sequenced Phase 22, in which case THAT
  contract governs the commit, not this one).

## 11. Documentation update rules

At every sub-phase close (and incrementally during PD-B/C), same session: (a) the log's
per-step record + evidence; (b) status-file Phase-20 row + dashboard + "Next action";
(c) owner decisions + the GO quoted verbatim; (d) any Phase-19 amendment need recorded as a
dated pointer (executed there); (e) NO other doc changes (the release docs were Phase-19's;
the attestation is Phase-21's).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-20
bullet: sub-phase closed, GO state, deployment/rollback outcome, log pointer) + MEMORY.md
index line at each sub-phase close. Agents without memory: skip — the log is the complete
binding record; nothing about production state may exist only in memory.

## 13. Battery policy

**The full sequential fresh-DB battery runs ONCE, at PD-0, as a GO-pack item** (the final
pre-deploy proof; expected = the current documented baseline + all pins accumulated by
executed phases — arithmetic quoted from the status dashboard). It does NOT run during or
after deployment (nothing code-side changes; production is verified by `verify_production`,
not by tests). A red battery at PD-0 = no GO (route to Phase 4).

## 14. Regression policy

- The GO pack IS the regression gate (everything the campaign certified, re-evidenced fresh).
- Post-deploy: `verify_production` + smoke = the production regression instruments; the
  restore drill = the DR regression instrument.
- Any behavioral surprise in production = an incident (stabilization machinery), then a
  Phase-4 finding on the dev side — never a live patch.
- No pins, no new tests (U4 — this phase writes no code).

## 15. Rollback policy

- Mechanics per DEP-D6 (pre-deploy dump → restic restore → compose re-pin; first-deploy
  abort = documented teardown); triggers per PD-D3 + owner voice at any moment.
- After rollback: production re-verified to its pre-action state (or confirmed torn down);
  the full story into the log; the GO voided; re-entry = fresh PD-0.
- The log + Design Record are append-only (dated amendments).
- Session crash mid-deploy: the per-step record shows the last completed step; next session
  VERIFIES server state against it before deciding continue-vs-rollback (never assumes).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3; deployment-day exception per §4).
2. Any §2.1 precondition unmet at PD-0; GO absent or stale.
3. A runbook step cannot execute as written (deviation = stop, never improvisation).
4. verify_production red in production; restore-drill failure; backup not landing.
5. A rollback trigger fires (execute the mechanics, then stop + report).
6. Any temptation toward a live fix, manual server-side data surgery, or a mid-run runbook
   rewrite.
7. Secrets exposure risk of any kind (report before proceeding).
8. The dev-tree porcelain proof fails (something edited the tree during the phase).
9. An incident unresolved at the stabilization window's end (owner extends or pulls).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-20 row + the log's per-step record —
   **then verify actual server state against the record before ANY action** (continue vs
   rollback is an evidence decision, never an assumption).
2. Read `docs/campaign_contracts/README.md` → the refreshed `deploy/README.md` + checklists
   (the procedure of record) → PHASE_21 §6 (the pack spec) → this contract → the log.
3. Confirm: GO validity (voided by any stop/rollback since), flags OFF, secrets custody,
   snapshot/artifact state per DEP-D2.
4. All production work = main-thread, owner-attended per PD-D1/D6.
5. Execute exactly ONE sub-phase per §7 (deployment-day exception only with the owner
   present). STOP per §16.
6. Anything inconsistent between the record and observed server state → report before
   touching anything (framework conflict rule, applied to a live system).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (PD-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| PD-D1 | GO authority + form | The owner alone; recorded verbatim in the log with date + the pack version it approves; single-use (voided by any stop/rollback) | _(pending)_ |
| PD-D2 | Deployment window | Owner-set (DEP-D5 posture applies); first deploy has no users — downtime tolerance is about owner availability + DNS/TLS propagation, stated anyway | _(pending)_ |
| PD-D3 | Rollback triggers | Hard: verify_production red · migration failure · data-integrity doubt · restore-drill failure · owner's voice at any moment. Soft (owner judgment): smoke anomalies, resource distress | _(pending)_ |
| PD-D4 | Stabilization window | Length + observation checklist + exit criteria (owner-set; the runbook's monthly-drill cadence begins after close) | _(pending)_ |
| PD-D5 | Production access + secrets custody | Per DEP-D4; who holds SSH keys, the password-manager pair, restic credentials — named | _(pending)_ |
| PD-D6 | Operator model | Owner-attended for every production action (solo-operator reality); the agent narrates + records, the owner executes or explicitly delegates per step | _(pending)_ |
| PD-D7 | Credential rollout | Worker/manager production credentials only AFTER the restore drill passes (runbook rule made a gate); rollout list + sequencing owner-set | _(pending)_ |
| PD-D8 | Post-phase flag posture | Flags remain OFF; R11 = a post-campaign owner decision via ENFORCEMENT_ROLLOUT_RUNBOOK (pointer recorded, nothing armed) | _(pending)_ |

Date · answered by: _(pending)_

## Dated amendments

- **2026-07-13 (Campaign Approval Pass): the owner CONFIRMED the 20/21 ordering
  interpretation** — go/no-go evidence is DEFINED by the PHASE_21 contract's §6.1
  (spec-in-contract, frozen text), CAPTURED and freshly verified at this contract's PD-0
  gate, and ATTESTED by Phase 21 after deployment. The locked order (20 before 21) stands
  exactly as written.

# Evidence note

The deployment record lives in `docs/PRODUCTION_DEPLOYMENT_LOG.md` (created at PD-0) —
contract = the campaign wrapper, runbook = the procedure, log = what actually happened on
the box (framework hierarchy rule). Phase 21 attests against this record; it never
re-deploys to check.
