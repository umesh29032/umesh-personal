---
id: docs-ai-pattern-intelligence-p5-deployment-runbook
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# P5 DEPLOYMENT RUNBOOK — Pattern Intelligence (2026-07-07)

The manufacturing ERP's existing deploy stays untouched (frozen). This
runbook adds the Pattern-Intelligence pieces on top.

## 1. Install / provision

```bash
# 1. Django side: NOTHING new — the app ships inside the repo; the Django
#    venv gained ZERO packages across P1–P5 (ADR-F promise, test-walled).

# 2. Compute runtime (ADR-F isolated venv, pinned):
cd compute/patterns_ai
python3 -m venv venv
./venv/bin/pip install -r requirements.lock.txt        # offline: use the
                                                       # wheel artifact store

# 3. Node 18.x (system package) — svgnest primary engine.
#    Absent node = honest degradation: BLF floor keeps generation alive.

# 4. Migrations (patterns_ai 0001–0006, all additive):
env/bin/python config/manage.py migrate patterns_ai

# 5. Sidebar rule (idempotent):
env/bin/python config/manage.py seed_patterns_ai_sidebar

# 6. Verify:
env/bin/python config/manage.py patterns_ai_health     # must print HEALTHY
```

## 2. Crons

| When | Command | Why |
|---|---|---|
| daily 02:00 | `manage.py verify_patterns_media` | ADR-G integrity sweep (sha re-hash; corrupt/missing flagged with reasons; orphans WARN) |
| daily 06:00 | `manage.py patterns_ai_health \|\| mail-ops` | ops truth: runtime, node, media writable, integrity summary, census; exit 1 = degraded |

## 3. Backup & restore

- **Knowledge (backup, forever):** PostgreSQL dump (all patterns_ai tables
  are append-only knowledge) + `media/patterns_ai/*/originals/**`
  (immutable, hash-named).
- **Regenerable (NO backup needed):** `media/patterns_ai/*/derived/**`
  (thumbnails — rebuild lazily), compute venv (rebuild from lockfile),
  node (reinstall).
- **Restore drill:** restore DB + originals → rebuild compute venv →
  `verify_patterns_media` (expect corrupt=0 missing=0) →
  `patterns_ai_health` HEALTHY → open the Yield Board (numbers re-derive;
  nothing else to restore BECAUSE nothing derived is stored).

## 4. Disaster recovery

Fresh machine, repo + DB dump + originals only:
install per §1 → restore per §3 → the ADR-F **annual rebuild drill** is
exactly this procedure, scheduled once a year, with a golden capture +
golden nest run re-executed and compared (P0 harness in `poc/` = the
reference numbers).

## 5. Monitoring & logging

- Health cron exit code = the pager signal.
- Loggers (all under Django's logging config): `capture_service`
  (store/retire/corrupt), `marker_service` (create/transition),
  `marker_feedback_service` (usage/outcome), basehttp access log.
- Slow requests: generation is the only long call (timeboxed ≤ ~20 s +
  engine startup; bridge timeout = timebox + 90 s headroom).

## 6. Maintenance calendar

| Cadence | Task |
|---|---|
| daily | crons above (automatic) |
| weekly | glance at Insights (`/patterns/insights/`) — pending suggestions, integrity |
| monthly | mat RECHECK on a fresh capture (mat detail page, one click) |
| yearly | ADR-F rebuild drill (§4) · review artifact MANIFEST pins |
| on mat replacement | retire old mat (reason) + commission new (tape ritual) |

## 7. Serving notes

Knowledge files have NO public URL (renditions-only via gated views) —
no web-server media exposure needed for patterns_ai originals. Thumbnails
stream through Django (fine at factory scale; a gated X-Accel handoff is
the future lever if volume demands).
