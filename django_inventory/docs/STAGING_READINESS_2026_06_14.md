---
id: staging-readiness-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Staging Deployment-Readiness Report — 2026-06-14

Fresh review of the current build against [IMPLEMENTATION_MASTER_PLAN_V2](IMPLEMENTATION_MASTER_PLAN_V2.md), after the staging-bundle implementation (P0-1…5, P1-1, P1-2, G-AUTH-1, H-2A+B, F-3). **Report only — nothing implemented.**

## Headline
**One blocker: the test suite is RED (537 tests, 1 failure).** The failure is a self-introduced test-layering violation (not production code). Fix it → green → the build is staging-ready on the code side. Everything else is deploy-infra prep.

---

## 1. Is the staging bundle complete?
**Yes (code), pending the test fix.** V2 Step-1 bundle — P0-1…P0-5 + P1-1 + P1-2 + H-2 — all implemented, reviewed, committed (9 commits, `9898e6a9`→`a249c137`). Bonus beyond the bundle: **G-AUTH-1** (P1-5) + **F-3** (P1-8). No uncommitted *code* (clean tree). 0 unapplied migrations.

## 2. Remaining P0/P1 findings open?
- **P0: NONE** — all five closed.
- **P1 done:** P1-1 (landing+digest), P1-2 (sidebar), P1-3 (branded denial — delivered by P0-2's `handler403`), P1-5 (G-AUTH-1 history isolation), P1-8 (F-3 pending reports).
- **P1 still open — all NON-blocking, post-staging or parallel:**
  - **P1-4** (D-1) — buttonize per-card actions ("Settle" tap target). S.
  - **P1-7** (H-7) — full advance-exposure debtors report (the digest *tile* + payroll link exist; a dedicated ranked report is the fuller version). S–M.
  - **P1-9** (A-1) — guard non-numeric quantity (contained by atomic today; UX only). S.
  - **P1-10** (A-3) — friendly "stage not started" page (raw 404 today). S.
  - **P1-11** (I-3) — DB partial-unique dup-draft backstop (prod-safe via PG advisory lock today). S.
  - **P1-12** (E-1) — correct ARCHITECTURE_V2 §5/§6 variance text. S (doc).
  - **P1-13** (B-4) — populate `WorkerLedgerEntry.settlement` FK (auditability). S.
  - None gate staging.

## 3. Required before staging deployment
**🔴 Code (must fix — green the suite):**
- Move/lazy-import in `config/accounts/test_sidebar_order.py`: it imports `inventory.models.Role` at module level, which the architecture guard forbids (`accounts` = identity/RBAC foundation, must not import domain apps). Fix = relocate the test to `inventory/` (can import both layers) **or** lazy-import `Role` inside the test. ~1 min. **Self-introduced in P1-2; production code unaffected.**

**🟡 Housekeeping:**
- Commit the **9 untracked docs** (audit_phases/, the foundation docs, V2 plan, risk review, this report) as a `docs:` batch — the governing plan shouldn't sit uncommitted.

**🟢 Deploy-infra (owner / PENDING_BACKLOG §0 — not code):**
- Provision VPS + domain + TLS (Caddy/nginx).
- **MT-1:** backup provider + a backup taken (restic → B2/R2).
- Set prod env vars (all fail-fast, no defaults): `SECRET_KEY` (≥50 chars), `REDIS_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- Run **`collectstatic`** (manifest storage requires it).
- **MT-5:** confirm staging DB engine == PostgreSQL (advisory locks + dup-draft protection are PG-only).
- **RC-1:** declare staging data **disposable** (never promoted; prod starts clean).
- **RC-6:** operate staging with **verify-before-settle discipline** (`review-reports/`) until the foundation lands — the over-report (B-1) is process-mitigated meanwhile.

*Verified clean:* `config.settings.production` loads + `check --deploy` = **0 issues** (DEBUG off, HSTS/SSL/secure-cookies all pass). Migration 0014 applied; 0 pending.

## 4. Changes to smoke-test manually (prefer a real phone)
1. **Role landing (P1-1):** manager login → Operations dashboard; worker login → My Dashboard.
2. **Digest + drill-downs:** 6 tiles render; **Stalled** tile → stalled list (H-2B); **Pending Reports** tile → pending list (F-3); counts match the tiles.
3. **Sidebar (P1-2):** Production directly below Main, above Storefront.
4. **P0-1:** open `/expense/settlements/start/<pk>/` directly → **405**, not 500.
5. **P0-2 / denials:** worker hits a management page → **branded 403**; a bad URL → **branded 404**; (and a forced 500 in staging shows the branded 500, not a traceback).
6. **G-AUTH-1:** a worker opening another (unassigned) Adda's history URL → 403; their own → 200.
7. **P0-5 + settlement happy path:** start → finalize a settlement from the list (confirm worker-complete still works, no regression).
8. **Mobile:** digest, both drill-downs, My Earnings, settlement detail — no horizontal scroll; tap targets usable.

## 5. Any reason not to deploy to staging now?
**Yes — one, and it's trivial: the suite is RED.** Don't ship a red build. The single failure is a misplaced test import (my P1-2 regression), not a product defect — a ~1-minute fix. **After** that fix + the deploy-infra prep (§3), there is **no code reason** blocking staging: P0 done, money engine reconciles + is hardened (Phase-B/I), prod-config passes `check --deploy`, migrations clean, 536/537 green. The only standing risks are the consciously-accepted, process-mitigated ones (RC-1 disposable data, RC-6 verify-discipline).

---

## Verdict
**CONDITIONAL-GO.** Green the suite (1 test-file fix) + commit the docs + complete deploy-infra (§3) → deploy to staging. No new code work beyond the test fix is needed to ship the bundle.
