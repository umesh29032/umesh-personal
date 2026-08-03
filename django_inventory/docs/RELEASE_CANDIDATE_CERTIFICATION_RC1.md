# Release Candidate Certification — RC1

**Date:** 2026-07-21
**Question:** "If I deploy this ERP into a real garment factory tomorrow morning, am I truly ready?"
**Signing role:** CTO / Release Manager. Not the developer. Not optimistic.
**Method:** deployment-readiness audit only (no re-run of the 6 prior functional/workflow certifications). Five parallel read-only audits — codebase health, security, config+deployment+observability, DB health+performance — plus direct CTO verification of settings, migrations, secrets, Django/Pillow pins, and media authorization. No Git commit; no production data modified; no test data created.

---

## EXECUTIVE SUMMARY

The engineering foundation is **genuinely production-grade**: strong DB integrity (30+ CheckConstraints, all money FKs PROTECT, full transaction-atomicity on every money/production write), strong application security (env-only secrets, correct prod hardening, Argon2, rate-limiting, consistent RBAC, no SQLi/CSRF/mark_safe/IDOR on money paths), a clean codebase (no shadow files, no migration drift, no debug leftovers in request paths), and deployment artifacts that are actually ready **for the target they are built for** (single-VPS Docker Compose + Caddy, not Cloud Run).

**But I will not sign an unconditional release.** There is a small, well-defined set of pre-go-live blockers: an **uncommitted critical fix** (adda-create can wedge), a **~18-month-stale framework** shipping with known CVEs (Django 5.0.1), an **unverified/likely-mis-seeded pay rate** (cutting ₹100/piece), and **two security MEDIUMs that touch worker financial PII and a public page**. None require a rebuild; all are known and small.

**Overall readiness: 8.5 / 10. Verdict: READY FOR PRODUCTION AFTER BLOCKERS.**

---

## OVERALL READINESS SCORE

| Dimension | Score | Note |
|---|---|---|
| DB integrity & money correctness | 9.5 | 30+ constraints, PROTECT FKs, atomic + locked writes |
| Application security | 8.0 | strong; −2 for stale framework (HIGH) + PII/media + public-XSS MEDIUMs |
| Codebase health / tech debt | 9.0 | clean; one post-v1 god-file |
| Deployment (VPS/Compose target) | 8.5 | ready; needs external cron + error-alerting |
| Deployment (Cloud Run target) | 3.0 | 2 blockers — but NOT the built target |
| Observability | 8.5 | request-id + actor audit logs; error-alerting off by default |
| Performance | 7.5 | barcode-print + bundle N+1 need work at scale |
| Business/operational readiness | 7.5 | reconciles; training + summary-report gaps (see Ops cert) |
| **Composite** | **8.5** | |

## DEPLOYMENT RECOMMENDATION
Deploy on the **VPS / Docker-Compose + Caddy** path it is actually built for, **after clearing the 5 blockers below.** Do NOT target Cloud Run without first closing the 2 Cloud-Run blockers (or accept the VPS path as final). The core factory operation is safe; the blockers are framework/config/PII hygiene, not architecture.

---

## RELEASE BLOCKERS (must fix before go-live)

| ID | Blocker | Evidence | Fix |
|---|---|---|---|
| **B-1** | **Adda-create wedges (500) if the per-product counter ever desyncs** from real codes (out-of-band insert / migration / import). Fix EXISTS but is **uncommitted**. | Reproduced live this session (`IntegrityError` on `3-PATTI-016` code collision); fix = counter-skip loop in `adda_service.create_adda`. | **Commit the fix** (+ its regression), then deploy. Non-negotiable — without it, a manager can be unable to start production. |
| **B-2** | **Django 5.0.1 is ~18 months stale on security patches** (Jan 2024); ships with known upstream CVEs across the 5.0.x line. | `requirements.txt: Django==5.0.1`. | **Bump to latest 5.0.x** (keeps the `CheckConstraint(check=)` API — only 5.1+ renames it, so no code change). Also **Pillow 10.2.0 → latest 10.x** (CVE-2024-28219; app runs Pillow on uploaded images). |
| **B-3** | **Stage pay rate looks mis-seeded** — cutting configured at **₹100/piece** (UAT Adda: cutting cost ₹15,000 vs worker earn ₹7,500). A wrong rate = wrong pay = direct financial + labor-trust harm on day one. | Ops cert §10; flow-editor config. | **Audit every stage rate** in the flow editor against the owner's real piece rates before go-live. |
| **B-4** | **Broken object-level auth on protected media** — `/media/<path>` is `login_required` only, not scoped to the owner. Any authenticated worker can fetch another worker's **advance financial attachment** (PII) if the path is known; advance files keep their original name. | `config/config/urls.py:57` (`media-protected` route); `expense/models.py:236`. | Scope `/media/` to the owning user/object, or move financial attachments behind an authorization-checked view. (Public `/media/storefront/*` is intentionally open — fine.) |
| **B-5** | **Stored XSS on the PUBLIC homepage** via storefront `icon_svg` (rendered `\|safe`; forms are `fields='__all__'`, no sanitization). A listing_team/super_admin can inject `<svg><script>` that runs for every anonymous visitor + admin. | `storefront/forms.py:21,44,65…`; `templates/public_home.html` `\|safe`. | Whitelist/sanitize `icon_svg` (or render escaped). Privileged-actor + public-page = fix before exposing `/`. |

*(Cloud-Run-only blockers — N/A for the VPS target: gunicorn hardcodes `:8000` ignoring `$PORT`; local-FS media is ephemeral on autoscaled instances. Only relevant if Cloud Run is chosen.)*

---

## HIGH PRIORITY (fix in the first days)
- **H-1** Worker "My Assigned Work" shows **ALLOCATED/REMAINING** — contradicts the blind-accountability rule; workers can report to target. Owner decision: hide or accept. (UAT F1.)
- **H-2** **No active error alerting** — Sentry is wired but off (no DSN, `sentry-sdk` not in requirements) and there is no `ADMINS`/`mail_admins`. Production errors live only in stdout logs. Set `SENTRY_DSN` + add the dep, or configure error emails.
- **H-3** **No health/readiness endpoint** — acceptable behind Caddy on a single VPS, but add a `/healthz` (DB+Redis reachable) before scaling or moving platforms.
- **H-4** **Monthly recurring expenses need an external scheduler** — `generate_monthly_expenses --confirm` is not wired into the stack (by design, no in-repo scheduler). The deploy runbook MUST add an OS cron; otherwise recurring expenses silently never generate.

## MEDIUM PRIORITY
- **M-1** Unvalidated uploads — `video` (cutting) + advance `attachment` are plain `FileField` (no ext/type/size check), served **inline** → a privileged uploader can store `evil.html`/`.svg` that executes for viewers. Validate + serve with `Content-Disposition: attachment`.
- **M-2** **Expected vs Settled clarity** — when a QC verified-quantity correction happens, "Expected Earnings" (frozen) ≠ Settlement paid (verified), with no on-screen correction trail. Correct math, real support-call risk. Surface "reported → verified → paid". (Ops cert OPS-1, evidence: 3-PATTI-016 checker 21→20, ₹0.75.)
- **M-3** **Barcode PRINT view has no streaming/pagination** — generates a QR per piece into one HTML doc; memory/CPU/response spike on a large Adda (hundreds–thousands of pieces). Paginate/stream server-side. (Exports CSV/XLSX/PDF are fine.)
- **M-4** **bundle_service N+1 cluster** (`bundles_for_stage`/`worker_bundles`/`my_assigned_work`/`stage_snapshot`) — bounded by SKU×worker count, tolerable at factory scale, slow on a big multi-color Adda. Batch `available()` + bulk-load contributions.
- **M-5** **No consolidated production/financial summary report; no revenue/profitability** — owner reconstructs across screens; ERP tracks labor cost, not profit. (Ops cert.)

## LOW / NICE-TO-HAVE
- WSGI defaults to `config.settings.local` (mitigated by Dockerfile `ENV DJANGO_SETTINGS_MODULE=production`; risk only if run outside the image).
- `patterns_ai/views.py` = 3024-line god-file (post-v1 AI module, not core ERP) — split later.
- Missing indexes: `WorkerStageContribution(task,color,size)`, standalone `AddaSettlement.status` — add if those surfaces slow.
- 2 deferred-roadmap TODOs; `restic` unpinned in backup container; login page redirects when already authenticated (shared-device friction); snapshot is a live view not a frozen artifact; alter/missing/damaged have no rework/recovery lifecycle; venv urllib3 version-mismatch warning (env hygiene).

---

## SECURITY FINDINGS (summary)
**Strong, no BLOCKER.** Env-only secrets (nothing hardcoded, `.env` not git-tracked), correct prod hardening (DEBUG off, HSTS 1yr+preload, secure cookies, SSL redirect, trusted origins, nosniff, X-Frame DENY, proxy-SSL header), Argon2, cache-backed per-email/IP rate limiting (fail-fast on Redis), consistent `permission_service` RBAC (no raw is_superuser gating), **no `@csrf_exempt`, no raw SQL, no `mark_safe`/`format_html` on user input**, money + worker-report paths self-scoped (verified no IDOR — worker-report resolves `worker=request.user` + live access re-check). **1 HIGH (stale Django, B-2), 4 MEDIUM (B-4/B-5/M-1 + Pillow).**

## PERFORMANCE FINDINGS (summary)
No correctness risk. `a360.build_a360` + settlement lines + adda-list are N+1-hardened (verified). Two scale concerns: barcode-print QR-per-piece (M-3) and the bundle_service snapshot N+1 (M-4). Both bounded at current scale; profile first on a large multi-color Adda.

## DEPLOYMENT FINDINGS (summary)
VPS/Compose target: Dockerfile (pinned python:3.10.16-slim, non-root), pinned requirements (gunicorn/redis/argon2/whitenoise; no dev-dep leak), `.env.example` complete (21 vars, 4 no-default fail-fast), entrypoint gates on healthy db+redis → migrate → collectstatic → gunicorn, restic nightly backups + documented restore drill + pre-deploy dump + rollback. `verify_production` command is a solid pre/post-deploy gate. **Ready for VPS after B-1..B-5 + H-2/H-4.** Cloud Run: not built for it (2 blockers).

## DOCUMENTATION FINDINGS
Strong: root `DEPLOYMENT.md` (zero-DevOps kit), `deploy/README.md` (runbook), `docs/release/` Operations Handbook (8 docs), architecture/DB/RBAC docs, KOS human layer, and this session's 6 certification reports. **Gaps:** no single "known limitations / release notes" doc consolidating the open items (this RC1 + the ops cert are the closest); worker/manager/owner/finance user manuals are partial (KOS covers concepts, not step-by-step role guides).

## OPERATIONAL FINDINGS
See `docs/PRODUCTION_OPERATIONS_CERTIFICATION.md`: numbers reconcile (mfg cost == frozen expected to the rupee; settlement pays verified), no data corruption, but training needed (two-step allocate, pre-production gates) and no consolidated summary/profitability. Restart/refresh/partial-transaction safety: writes are atomic + locked, so a mid-write crash rolls back cleanly (no partial settlement/contribution). Concurrency protected by advisory locks (5374 settlement / 5375 pool, disjoint).

## BUSINESS FINDINGS
Owner can run production decisions but not see profit (labor cost only). Finance reconciles + exports but needs the correction trail (M-2). Workers/managers/QC can complete their day. Support burden: week-one training on allocation + pre-production gates + the expected/verified/settled distinction.

## TECHNICAL DEBT
Low for a v1: one post-v1 god-file, a few large service files, the S6 `reported_quantity` retirement (soak-gated, not written), no rework/recovery module, no frozen stage-snapshot artifact. None gate release.

---

## POST-GO-LIVE RECOMMENDATIONS
Run `verify_production` immediately post-deploy. Watch stdout logs for the first settlement + first multi-color Adda (perf). Keep enforcement flags OFF until soak per the manufacturing-freeze policy.

## 30-DAY IMPROVEMENT PLAN
1. Close B-1..B-5 (pre-go-live) + H-2/H-4 (error alerting + monthly cron). 2. Health endpoint (H-3). 3. Surface the QC correction trail (M-2). 4. Validate uploads + attachment disposition (M-1). 5. Decide the blind-rule (H-1).

## 90-DAY ROADMAP
1. Consolidated production/financial summary report (data ~70% in A360). 2. Barcode-print streaming + bundle_service N+1 batching (M-3/M-4). 3. Role-by-role user manuals. 4. Frozen `StageCompletionSnapshot` + rework/recovery module. 5. Revenue/profitability if in scope. 6. Split `patterns_ai/views.py`.

---

## FINAL CTO REVIEW

- **Would I deploy tomorrow?** Not tomorrow morning as-is. After a short blocker sprint (B-1..B-5), yes — on the VPS/Compose path.
- **What absolutely must be fixed?** Commit the adda-create fix (B-1); bump Django+Pillow (B-2); verify stage rates (B-3); scope protected media (B-4); sanitize the public-page SVG (B-5).
- **What can safely wait?** Error alerting, health endpoint, N+1/print streaming, summary report, blind-rule decision, rework module, god-file split.
- **Biggest TECHNICAL risk:** running an 18-month-stale Django with known CVEs into production (B-2).
- **Biggest BUSINESS risk:** a mis-seeded pay rate paying workers wrong on day one (B-3) — direct money + trust damage.
- **Biggest OPERATIONAL risk:** the adda-create wedge halting new production (B-1), plus week-one confusion over allocation/pre-production gates and expected-vs-settled.
- **Biggest MAINTENANCE risk:** low overall; the post-v1 patterns_ai god-file + the un-retired S6 dual-write are the largest, neither release-gating.

**Evidence for the positives:** migration drift = "No changes detected"; production settings verified secure + env-driven fail-fast; DB money paths 100% PROTECT + atomic + locked; no request-path debug code; no hardcoded secret; no SQLi/CSRF/mark_safe/money-IDOR; observability = request-id + actor-tagged audit logs to stdout; the 6 prior certifications passed the functional/workflow/adversarial/operational bars.

---

# FINAL VERDICT

## READY FOR PRODUCTION AFTER BLOCKERS

Clear B-1 (commit the adda-create fix), B-2 (bump Django 5.0.x + Pillow), B-3 (verify stage rates), B-4 (scope protected media), and B-5 (sanitize the public-homepage SVG) — all small, known, no rebuild — and this ERP is safe to run a real garment factory on the VPS/Compose stack it is built for. It is **NOT** ready to deploy unchanged tomorrow morning, and it is **NOT** a "not ready / rebuild" system either. Five fixes stand between it and production.

---

## STOP — awaiting manual audit
No Git commit. No production data modified. No test data created. Awaiting your inspection.
