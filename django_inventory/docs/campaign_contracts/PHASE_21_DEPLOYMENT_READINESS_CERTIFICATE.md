---
id: docs-campaign-contracts-phase-21-deployment-readiness-certificate
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 21 Execution Contract — Deployment Readiness Certificate

> Authored 2026-07-13 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), **the Phase-19 documentation set** (the runbook/checklists it
> attests against) and **the Phase-20 deployment record** (the execution it attests to).
> Deltas only.
> **Two roles, one contract, no ordering paradox:** (a) **§6.1 of THIS CONTRACT — authored
> now — is the GO evidence-pack SPECIFICATION that Phase 20's PD-0 gate assembles** (the spec
> lives in the frozen contract, so it exists before Phase 20 runs even though Phase 21
> EXECUTES after it); (b) at execution, this phase FRESHLY RE-VERIFIES every item and issues
> the certificate covering both the pre-release evidence and the deployment outcome.
> **The certificate is the MANDATORY input to Phase 22** (First Git Checkpoint): no
> certificate, no checkpoint.
> Certificate + evidence doc (created at CERT-0): `docs/DEPLOYMENT_READINESS_CERTIFICATE.md`
> (an `evidence-cert`, append-only from birth — the Standard's class).

## 1. Phase objective

Attest, with freshly verified evidence, that the deployed system is what the campaign
certified: every certification closed, every fix reconciled, the battery at its documented
number, the flags in their declared state, the knowledge system drift-clean or
owner-accepted, production verified by the campaign's own instruments, the deployment
executed per its record, and every open item consciously registered — then render the final
verdict (CERTIFIED-FOR-OPERATION / CERTIFIED-WITH-CONDITIONS / NOT-CERTIFIED) that Phase 22
requires before the one commit. **Attestation is verification, not trust:** every input is
re-checked at CERT-A; a certificate that merely collects claims certifies nothing.

## 2. Scope

### 2.1 In / out

**In:** the evidence-pack specification (§6.1, normative for PD-0) · fresh verification of
every pack item + the Phase-20 deployment record · the open-items register · the verdict +
certificate issuance · the Phase-22 handoff.
**Out:** producing ANY of the evidence itself (certifications, fixes, battery runs, deploys
— all owned by their phases; a missing/red item is a FINDING routed to its owner, and the
certificate waits) · re-running the battery (the NUMBER and its arithmetic chain are
verified against the status record; a doubt = stop + route, not a convenience re-run that
would mask drift) · re-deploying or touching production (verify_production's PROD report is
read from the Phase-20 record; a freshness doubt → one read-only re-run of
`verify_production` is the ONLY production-touching action this phase may request, owner-
attended per PD-D6) · any code/doc repair · the commit (Phase 22) · the R11 flip.

## 3. Success criteria

Phase 21 is DONE when ALL hold:
1. Every §6.1 pack item LOCATED + FRESHLY VERIFIED (hash/number/quote checks per §6.2) with
   its verdict row — none trusted on prior assertion; the Phase-20 record cross-checked
   internally (GO → steps → verification → stabilization coherent).
2. The open-items register complete: every known deferral consciously listed with its owner
   disposition — S6 (reported_quantity retirement, soak-gated) · R11 flag flips (post-
   campaign, runbook-owned) · backlog residue (#1, #3, #4, #6–#9 states as then disposed) ·
   accepted sweep WARNs · PENDING_BACKLOG survivors · anything the certifications or Phase 4
   left deferred — nothing discovered later may say "we forgot".
3. The verdict rendered per CERT-D1's taxonomy, with grounds; CONDITIONS (if any) named,
   owner-accepted, and each carrying its post-certificate owner + venue.
4. The certificate issued as an append-only `evidence-cert` with the owner's attestation
   (CERT-D3 form) — quoting, for permanence: the final battery number + arithmetic chain ·
   the verify_production PROD envelope + body-hash · the sweep state · the deployment
   verdict · the snapshot/Phase-0 state · the flags state.
5. The Phase-22 handoff written: the certificate named as the mandatory input; the
   pre-checkpoint knowledge sweep obligation (P14) restated; the checkpoint's own owner
   gates pointed to (Phase 22's contract — deliberately unauthored — will consume this).
6. Zero changes to anything but the certificate + the §9 sync set; battery untouched;
   production untouched (except the §2.1 owner-attended re-run allowance, if invoked).
7. Status + memory synced.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Verify, never trust:** each item's verification method is prescribed (§6.2) and its
  execution recorded. "The log says green" is a citation, not a verification — the log's
  artifact (hash, number, output) is re-read at source.
- **A red/missing item never bends the certificate:** it routes to its owning phase/protocol
  and the certificate WAITS (or issues NOT-CERTIFIED / WITH-CONDITIONS per the owner). The
  certificate has no fix mandate whatsoever.
- **Freshness discipline (CERT-D2):** every item carries a maximum evidence age; stale =
  re-evidence at the owner (e.g. a battery run older than the window → Phase-4-style re-run
  ORDERED there, not run here).
- **Append-only from birth:** the certificate document is never edited after issuance —
  post-issuance reality changes are dated addenda (incidents, condition closures).
- All verification main-thread (U7 — final verdicts are never delegated).

## 5. Evidence standard

Per pack item: the claim · the source artifact · the verification method executed · the
observed value · the verdict. The certificate's quoted permanents (§3.4) carry their
hashes/numbers inline. The owner attestation verbatim. The open-items register with per-item
owner dispositions. Everything in the certificate itself (it IS the evidence doc — one
artifact, self-contained, readable in five years with zero context).

## 6. Methodology

### 6.1 THE EVIDENCE PACK (normative spec — PD-0 assembles it; CERT-A re-verifies it)

1. **Certifications closed:** Worker (CLOSED) · Management (CERTIFIED) · Owner (Phase 2
   final verdict) · Office/Support (Phase 3 final verdict) — the four role-lattice verdicts
   quoted from their evidence docs.
2. **Phase-4 reconciliation:** the FIX-G statement (every finding in a terminal state;
   ledger arithmetic: findings in = dispositions out).
3. **Battery:** the final number + the arithmetic chain from 1526/1526 through every
   executed phase's pins/suites (status-dashboard history reconciled); the PD-0 run's
   record as the last-run evidence.
4. **Flags:** ENFORCE_ALLOCATION_BOUND=False · ENFORCE_SETTLEMENT_RECONCILIATION=False —
   declared, and confirmed in the verify_production report (U10).
5. **Knowledge state:** the latest full knowledge_sync sweep — BLOCKER/WARN-clean or the
   owner-attributed acceptance list (P14/P18 close conditions); the graph validates
   (hash-true).
6. **Verification instrument:** verify_production GREEN — the dev-mode rehearsal (pre-deploy)
   AND the in-production run (post-deploy), envelopes + body-hashes.
7. **Backlog + PENDING_BACKLOG dispositions:** line-by-line, as of certification.
8. **Snapshot/Phase-0:** the Decision Record executed state + the artifact's last validation
   (the DR posture at go-live).
9. **Deployment record (Phase 20):** GO verbatim · per-step execution record complete ·
   post-deploy verification set green (incl. the restore drill) · stabilization outcome ·
   any rollback stories.
10. **Runbook currency:** the Phase-19 tabletop verdict + no unexecuted dated amendments
    pending against the runbook.
11. **Open-items register:** §3.2's conscious-deferral list.
Items 1–8 + 10 are assemble-able at PD-0 (pre-release); 9 completes after deployment; 11
spans both — the certificate covers the whole arc.

### 6.2 Verification methods (per item class)

Documents → read the closing verdict at source (not the status file's summary). Numbers →
reconcile the arithmetic chain across the status history. Reports → body-hash re-check
against the stored artifact (and the §2.1 owner-attended re-run allowance for
verify_production if freshness is doubted). Sweeps → the report + acceptance list re-read;
graph hash re-validated. Deployment record → internal-coherence pass (every GO-pack ref
resolves; every step has its record; every verification has its output). Registers →
line-by-line against their source docs.

### 6.3 The verdict (CERT-D1)

**CERTIFIED-FOR-OPERATION** — every item green, open-items register accepted.
**CERTIFIED-WITH-CONDITIONS** — specific named conditions, each with owner + venue + (where
sensible) a review date; the owner explicitly accepts operating under them; Phase 22 may
proceed with the conditions quoted into the checkpoint record.
**NOT-CERTIFIED** — grounds named; the certificate records the state honestly; Phase 22 is
blocked until re-certification.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); everything into the certificate document;
battery never runs.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **CERT-0** — Charter + gate + ratification | Gate: Phase 20 closed (the deployment record exists — DEPLOYED-STABLE or a rolled-back story, either is attestable). Owner ratifies CERT-D1..CERT-D5. The certificate skeleton created (evidence-cert class, append-only). **Stop:** gate fails; any CERT-D unanswered. |
| **CERT-A** — Evidence verification | §6.1 items 1–11 each: locate → verify per §6.2 → verdict row; the open-items register assembled; red/missing items routed (and the phase waits or the verdict path chosen with the owner). **Stop:** any verification reveals a contradiction with a closed record (conflict rule — owner before anything else); a routed item's owner declines to resolve (verdict-path decision needed). |
| **CERT-B** — Verdict + issuance + handoff | The verdict per §6.3 with grounds; conditions (if any) owner-accepted; the owner attestation (CERT-D3); the permanents quoted; the Phase-22 handoff (mandatory-input declaration + pre-checkpoint sweep pointer + the unauthored-Phase-22 note); status Phase-21 → ✅. **Stop:** owner attestation absent (the certificate cannot self-sign). |

## 8. Deliverables

- **`docs/DEPLOYMENT_READINESS_CERTIFICATE.md`** — the self-contained, append-only
  certificate: pack verification tables · open-items register · verdict + grounds +
  conditions · owner attestation · quoted permanents · the Phase-22 handoff.
- Filled Design Record (CERT-D1..CERT-D5); status + memory sync.

## 9. Files expected to change

**Docs only:** `docs/DEPLOYMENT_READINESS_CERTIFICATE.md` (new — certificate + evidence in
one) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DOCUMENTATION_INDEX.md` (certificate
row) · this file (Design Record + amendments) · memory files. Nothing else — this phase
repairs nothing, generates nothing, deploys nothing.

## 10. Files that must never change (touching one = STOP + report)

- EVERY source it verifies: certification docs, phase logs, the deployment record, sweep
  reports, the status history — attestation reads; it never adjusts an input to make a row
  green (the cardinal sin of certification).
- ANY application file · the runbook + deploy scripts · production state (except the §2.1
  owner-attended verify_production re-run, which writes nothing by that instrument's own
  proofs) · flags (U10) · generated artifacts · truth-locks · `.git` (U2).
- The certificate itself after issuance (dated addenda only).

## 11. Documentation update rules

At each sub-phase close, same session: (a) the certificate document grows append-only;
(b) status-file Phase-21 row + dashboard + "Next action" (→ Phase 22, gated on this
certificate); (c) DOCUMENTATION_INDEX row at CERT-0; (d) owner ratifications + attestation
quoted verbatim the session they are given; (e) routed findings recorded with their venue
pointers (never worked here).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-21
bullet: verification state, verdict, certificate pointer) + MEMORY.md index line at each
sub-phase close. Agents without memory: skip — the certificate is deliberately self-contained
(readable with zero context; that property is a §3.4 requirement, not a courtesy).

## 13. Battery policy

**Never runs in this phase.** The battery NUMBER is verified (arithmetic chain + the PD-0
run's record); a doubt about it = a routed finding (re-run ordered at its owner under the
Phase-4/PD-0 machinery), never a convenience run here — an attestation phase that quietly
re-runs evidence generators blurs who owns the proof.

## 14. Regression policy

- The certificate's verification tables ARE the campaign's final regression sweep — every
  certified property re-evidenced at source.
- A verification-revealed regression = a routed finding (its owning phase/protocol) + a
  verdict-path decision with the owner; never a quiet fix.
- No pins, no tests (U4 vacuously satisfied).

## 15. Rollback policy

- Pre-issuance: the draft certificate's rows may be corrected as verification proceeds
  (drafting, not history). Post-issuance: append-only, dated addenda only.
- A routed finding that resolves re-enters at its CERT-A row with a fresh verification.
- Session crash: the certificate's last verified row is the resume point (each row is
  self-contained evidence).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. CERT-0 gate fails (no deployment record) or CERT-D items unanswered.
3. A verification contradicts a closed record (conflict rule — the finding may unseat more
   than a certificate row).
4. Any temptation to adjust an input, re-run someone else's evidence, or soften a red row —
   the §10 cardinal sin.
5. A routed finding's owner path stalls and the owner has not chosen a verdict path.
6. The owner attestation is unavailable (the phase waits; nothing self-signs).
7. Production freshness doubt that the single allowed re-run cannot resolve.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-21 row →
   `docs/DEPLOYMENT_READINESS_CERTIFICATE.md` (the draft's verified rows = the resume point).
2. Read `docs/campaign_contracts/README.md` → this contract (§6.1 = the pack; §6.2 = the
   methods) → the Phase-20 deployment record → the sources each unverified row names.
3. Verify nothing by summary — sources only (§4).
4. The verify_production re-run allowance is owner-attended only (PD-D6 custody applies).
5. Execute exactly ONE sub-phase per §7. STOP per §16.
6. Anything inconsistent between a source and a prior verified row → §16.3 before
   continuing.

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (CERT-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| CERT-D1 | Verdict taxonomy | §6.3 exactly: CERTIFIED-FOR-OPERATION / CERTIFIED-WITH-CONDITIONS (named, owned, accepted, quoted into Phase 22) / NOT-CERTIFIED (blocks Phase 22) | _(pending)_ |
| CERT-D2 | Evidence freshness windows | Per item class: battery = the PD-0 run unless code changed since (then re-run at its owner) · verify_production = the post-deploy run unless production changed (then the one allowed re-run) · sweeps = post-final-doc-change · documents = their closing versions | _(pending)_ |
| CERT-D3 | Attestation form | The owner's verbatim statement (date + name + the verdict + conditions acknowledged), quoted in the certificate; no proxy signing | _(pending)_ |
| CERT-D4 | Open-items acceptance authority | The owner alone accepts each open item into the register (per-item, not blanket); unaccepted items force the WITH-CONDITIONS or NOT-CERTIFIED path | _(pending)_ |
| CERT-D5 | Post-issuance addenda | Dated, append-only, owner-visible: condition closures, incidents, the R11 flip when it happens (a pointer addendum — the runbook owns the procedure) | _(pending)_ |

Date · answered by: _(pending)_

## Dated amendments

- **2026-07-13 (Campaign Approval Pass): the owner CONFIRMED the 20/21 ordering
  interpretation** — this contract's §6.1 is the GO evidence-pack specification consumed by
  PHASE_20's PD-0 gate; this phase executes after deployment and attests the whole arc
  (pre-release evidence + deployment outcome). Mirror amendment recorded in PHASE_20.

# Evidence note

The certificate IS the evidence document — one self-contained, append-only artifact
(`docs/DEPLOYMENT_READINESS_CERTIFICATE.md`) that a reader with zero context can trust in
five years. Phase 22 (deliberately unauthored — the first commit and campaign closure
deserve their own contract) consumes it as a mandatory input; nothing else in the campaign
may substitute for it.
