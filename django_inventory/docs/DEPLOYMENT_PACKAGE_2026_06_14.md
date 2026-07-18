---
id: deployment-package-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Staging Deployment Package — 2026-06-14

Companion to [STAGING_READINESS_2026_06_14](STAGING_READINESS_2026_06_14.md). Planning only — no code, no migrations, no foundation work. The staging bundle (P0-1…5, P1-1, P1-2, G-AUTH-1, H-2A+B, F-3) is complete; suite 537/537 green; `check --deploy` clean.

## 1. Governing-docs commit verification ✅
All governing documentation is now committed and the working tree is **clean**:
- **Audit A–I:** `docs/audit_phases/PHASE_{A..I}` + `POLICY_DECISIONS_B1_A5_B3` + `ARCH_EVAL_*` (commit `1753cc5c`).
- **Locked foundation:** `PRODUCTION_TRUTH_FOUNDATION_{REVIEW,FINAL,ROADMAP,LOCKED}` (`1753cc5c`).
- **Plan + risk:** `IMPLEMENTATION_MASTER_PLAN(.md → _V2)` + `IMPLEMENTATION_RISK_REVIEW` (`1753cc5c`).
- **Reports:** `ERP_PRESTAGING_AUDIT_2026_06_14` + `STAGING_READINESS_2026_06_14` (`1753cc5c`).
- **Per-feature DOCS-SYNC** (PENDING_BACKLOG done-log, production FILE_MAP, worker_task_service chokepoint) shipped **with their code commits** (`f5998531`, `455df834`, `b3ae3beb`, `0012d807`, `a249c137`).
- Nothing untracked/modified. 9 implementation commits (`9898e6a9`→`a249c137`) + 1 test relocation (`37d76a65`) + 1 docs commit (`1753cc5c`).

---

## 2. Staging deployment checklist (from readiness §3 + MT gates)

### Pre-deploy — code/repo (DONE)
- [x] Suite green **537/537**; `check --deploy` 0 issues; 0 unapplied migrations.
- [x] Tree clean; all governing docs committed.

### Pre-deploy — infra (owner; PENDING_BACKLOG §0/§1)
- [ ] VPS provisioned (~2 vCPU / 4 GB to start).
- [ ] Domain + TLS (single terminating proxy — Caddy/nginx; `SECURE_PROXY_SSL_HEADER` is set, so never expose gunicorn directly).
- [ ] **MT-1** — backup provider configured (restic → Backblaze B2 / Cloudflare R2) + first backup taken + **restore fire-drill** rehearsed.
- [ ] **MT-5** — staging DB engine **== PostgreSQL** (advisory locks + dup-draft protection are PG-only).
- [ ] **RC-1** — **FRESH** staging DB (disposable; migrate from zero — do NOT import dev data; staging data is never promoted to prod).
- [ ] Redis reachable (auth rate-limiter + cache depend on it; fail-fast).

### Deploy steps
- [ ] `DJANGO_SETTINGS_MODULE=config.settings.production`.
- [ ] Env vars set (all fail-fast, no defaults): `SECRET_KEY` (≥50 chars), `REDIS_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- [ ] `migrate` (expect 0 pending).
- [ ] **`collectstatic --noinput`** (CompressedManifestStaticFilesStorage requires it).
- [ ] Provision real users + roles (super_admin, manager, worker[s] + skills); decide if accountant/listing-team needed.
- [ ] Seed minimal master data (cloth types/colors/storage, products + workflow stages **with rates** — A-5: unpriced stages still settle to ₹0 until the foundation blocks it).

### Post-deploy smoke (desktop + real phone) — readiness §4
- [ ] Role landing: manager → Operations; worker → My Dashboard.
- [ ] Digest 6 tiles; Stalled → drill-down, Pending Reports → drill-down; counts match tiles.
- [ ] Sidebar: Production above Storefront.
- [ ] `GET /expense/settlements/start/<pk>/` → **405** (not 500).
- [ ] Worker hits a management page → **branded 403**; bad URL → **branded 404**; forced error → **branded 500** (no traceback).
- [ ] Worker can't open an unassigned Adda's history (403); own → 200.
- [ ] Settlement happy path: start → finalize from the list (worker-complete unaffected).
- [ ] Mobile: digest, drill-downs, My Earnings, settlement detail — no horizontal scroll.

---

## 3. Post-deployment observation checklist (soak instruments)

### A. Settlement workflow
- Every finalize **reconciles**: ledger net per worker == `final_payable`; reversals net to zero; supersede chain coherent.
- No 500s on settlement-start (P0-1 holds in prod).
- **Watch for the B-1 leak:** any settlement where Σ(worker piece-reports) > the stage's recorded output (e.g. `pieces_cut`). Log frequency + ₹ impact — this is the core evidence for the foundation's urgency.

### B. Manager verification discipline (RC-6 — THE critical instrument)
- Is management actually opening **`review-reports/`** and setting `verified_quantity` **before** finalize?
- Track **% of payable contributions verified before settlement**. If it trends low → workers paid on self-reports → wrong pay with real workers. This directly tests whether the over-report risk is process-mitigable (the premise of staging-first / Option B).

### C. Assignment workflow
- Are workers assigned (`set_stage_workers`) and do they report? Watch the **Pending Reports** queue (F-3): tasks lingering, or silently auto-cancelled at stage close (F-2)?
- **Validate RC-5:** does management actually **pre-assign per stage**, or is the floor ad-hoc ("grab a bundle")? This decides whether the foundation's **Strict** allocation fits — or whether Open mode must be revisited.

### D. Stalled Addas (H-2)
- Do the digest tile + drill-down surface **real** stalls? Are flagged Addas genuinely stuck?
- Tune **`STALLED_ADDA_DAYS`** to the factory's actual cycle pace (default 3).

### E. Pending Reports (F-3)
- Does the count/list match floor reality? Are workers chased **before** stages close (so work isn't lost to auto-cancel)?
- Confirm worker isolation in the wild (a worker sees only their own queue).

### Cross-cutting
- Errors/observability (the stack has the seams — wire error reporting).
- Real-worker mobile feedback (touch targets, numeric entry, readability).
- Denial UX consistency (branded 403 vs the redirect-with-flash on managed URLs).

---

## 4. Recommended staging duration before Foundation Sprint S1

**Gate on evidence, not the calendar — target ~2–4 weeks.** A garment Adda cycle (cutting → … → settlement) runs days-to-weeks, and the soak must produce the data the foundation design depends on (RC-5, RC-6, B-1 frequency). Recommend a **2–4 week window**, started when real production begins, and **begin S1 only when ALL exit criteria are met**:

**Exit criteria (S1 go-gate):**
1. **≥2–3 Addas completed end-to-end through settlement**, money reconciled each time.
2. **RC-6 answered:** verification-before-settle discipline measured (is it happening? what %?).
3. **RC-5 answered:** does the floor tolerate per-stage pre-assignment (Strict), or is it ad-hoc?
4. **B-1 frequency measured:** how often Σreports ≠ stage output, and the ₹ impact (sizes the foundation's payoff).
5. **No P0-class production incident** during the window (500s, money mis-book, access leak).
6. **Thresholds tuned** (STALLED_ADDA_DAYS; any digest/queue calibration).

**Rationale:** Option B (staging-first) was chosen *specifically* so the foundation's worker-report + stage-assignment redesign (the two carved-out screens) is informed by **observed real usage**. Cutting the soak short forfeits that. If cycles are fast and criteria are met by ~2 weeks, start S1 then; if the floor is slow or discipline questions remain open, hold to ~4 weeks. **Do not exceed ~4 weeks** without S1 — the over-report leak (B-1) persists until the foundation lands, and prolonged staging just accumulates mitigated-but-real risk.

---

## Verdict
Build is **staging-deployable**: code green + clean, docs committed + synchronized, prod-config verified. Remaining work is **owner-side deploy-infra** (§2 infra block). After deploy, run the §3 observation checklist for the §4 window, then gate S1 on the exit criteria.
