---
id: release-known-limitations
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: —
verified: 2026-07-19
---

# Known Limitations — ERP v1.0 (imaandaar register)

> Har item ke saath: kya hai, KYU aisa chhoda gaya, aur kab/kaise band hoga.
> Yeh list release certification ke consolidated risk register (log §9.3) se
> nikli hai — yahan koi surprise nahi hona chahiye. "Limitation chhupao mat,
> register karo" — isi discipline ne certification ko sach rakha.

## Accepted risks (temporary, dated)

| # | Item | Kyu accepted | Band kaise hoga |
|---|---|---|---|
| 1 | **Monitoring/alerting gap** — Sentry off (hook built, DSN unset), no `/healthz`, no uptime probe/alerts | C2 branch-B: single-operator internal ERP; compensating controls certified (structured+security logs, persisted audit rows, `verify_production` gate). TEMPORARY acceptance recorded at P19 | §8.5 menu at/near first deploy — sab config-level (Sentry DSN + sdk · healthz + app healthcheck · uptime probe · log alerts) |
| 2 | **wsgi/asgi/manage default = local settings** (DEP-F1) | Docker path double-walled (Dockerfile bakes production + .env sets it); sirf off-runbook bare-metal deploy par risk | one-line fail-fast default — P19/v1.1 candidate |
| 3 | **No latency/load testing** — perf pins query-count hain, latency nahi (RR-7) | single-factory load chhota; N+1 regressions pins pakadte hain | post-deploy observation; zaroorat dikhe to load test |
| 4 | **Rate-limit thresholds live-fire tested nahi** (S-R3) | policy unit-pinned; live brute-force simulate karna low-value tha | soak window mein security log observe karo |

## Intentional trade-offs (design, badlenge nahi bina ADR ke)

| # | Trade-off | Wajah |
|---|---|---|
| 5 | **RPO 24h** (nightly backups) | chhoti factory; pre-deploy dumps + monthly restore drill isse practical banate hain. Ghatana ho to WAL-archiving/managed-PG (runbook future-exit) |
| 6 | **Enforcement flags default OFF** (allocation-bound · settlement-recon · ledger lever era-B default) | naya refusal-behavior soak ke baad hi ON hota hai — runbook-gated, kabhi casual flip nahi |
| 7 | **BOD = window-only** | owner dashboard kabhi engine nahi banega — drift-se-bachav ka structural decision (no models/writes) |
| 8 | **Salary never per-Adda** (ADR-0011) | costing noise-free rahe; monthly = FactoryExpense |
| 9 | **Media Django-gated** (no CDN/S3 v1) | private files (photos/receipts); S3 future-exit documented |
| 10 | **restic backup container mein boot-time apk install** (ek unpinned package) | runbook ka apna accepted tradeoff — "revisit if it ever bites" |

## Deferred work (soch-samajh kar postponed)

| # | Item | Status |
|---|---|---|
| 11 | **S6: `reported_quantity` retirement** (dual-write ka aakhri kadam) | IRREVERSIBLE — post-deploy soak-gate ke baad hi; tab tak `good` hi read-truth hai, `reported=good` dual-write chalta hai |
| 12 | **Era-A (allocation-credit) legacy path physical deletion** | ADR-0007 soak-gated; lever tested rehta hai tab tak |
| 13 | **Pattern tool phases 4–6** (interactive workspace, locked-piece re-nest, PDF/print) | vision-scope, unbuilt by design (owner reset 2026-07-07) |
| 14 | **RM-V2** (raw-material service seam ka read-path expansion) | recorded seam; post-v1.0 |
| 15 | **MEE future frequencies** (weekly/quarterly…) | enum seam ready; sirf owner-charter se aayengi |
| 16 | **Multi-factory / commerce (G1–G7) / TM-2 barcode capture** | ADR-fenced future scope — jab aayega, design-first aayega |
| 17 | **KOS consolidation program** | approved-but-deferred post-campaign (owner order; disk par NA likha jaana tha isliye sirf pointer) |
| 18 | **Accountant role** | role exists, koi surface certified nahi (S-R1) — owner ruling pending; koi galat access NAHI hai (role reaches nothing) |

## Technical debt (chhota, register mein, kaategا jab chhuenge)

| # | Debt | Note |
|---|---|---|
| 19 | ruff nits in 43 files | release commit ne certified bytes rakhe (ruff autofix reverted); future incremental commits ratchet se saaf karenge |
| 20 | ds-lint inline-style migration incomplete | ratchet NEW violations rokta hai; purane migrate-on-touch |
| 21 | DOC-F1: `docs/production/LAYERING_STAGE.md:97,250` removed view/form ko current dikhata hai | 2-row fix-when-touched |
| 22 | DOC-F2: `docs/production/TRACKING.md:178` StockService pointer-stale | wording fix-when-touched |
| 23 | 22 documented cross-app import edges (report-only contract) | coupling-worklist hai, cycle zero hai |
| 24 | accounts ≈5 role-lookups/request | perf micro-debt, flagged |
| 25 | patterns_ai tests parallel-unsafe | battery law sequential — fix = per-class media isolation (backlog) |
| 26 | INFO residue #6–#14 | fix-when-touched class |

## Operational realities / Zameeni sach

| # | Item | Matlab |
|---|---|---|
| 27 | **Bus factor 1** | ek hi owner-operator. Mitigation = yehi handbook + password-manager custody + offsite backups. Naya developer aaye to yeh folder uska day-1 hai |
| 28 | **Dev residue PRIMARY dev-DB mein** (33 `dev.*` users, 4 DEV addas, ₹0 draft ADST-0011) | production first-deploy par "start CLEAN vs import" owner decision — CLEAN recommended |
| 29 | **3-Patti stage-trio config pass** pending | blocking dev-addas ab hat chuke (certification observation) — owner manual pass schedule karo |
| 30 | **Full-stack runbook walk** (Caddy TLS + restic offsite) abhi real target par nahi hua | first deploy hi wo walk hai; core restore path REAL data par drilled hai |
