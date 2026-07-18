---
id: deploy-readme
type: topic-canonical
status: active
owner: handwritten
scope: deployment
anchors: deploy/
verified: 2026-07-13
---

# Deploy & Operations Runbook — single-VPS Docker Compose (direction C)

Owner-approved 2026-06-11. This file is the ops runbook the architecture
checkpoint (§5) called for. Stack: Caddy (auto-TLS) → gunicorn app →
Postgres 16.6 + Redis 7.4, nightly restic backups to B2/R2.
All images exact-pinned; app boots only after HEALTHY db+redis (compose
condition + entrypoint wait-loop).

## First deploy (checklist)
1. VPS (India region — DO Bangalore / Vultr Mumbai), 2-4 GB RAM.
   SSH-key-only login; `ufw allow 22,80,443; ufw enable`.
2. Install docker + compose plugin (`curl -fsSL https://get.docker.com | sh`).
3. DNS A record → VPS IP (Caddy needs it resolving before first start for TLS).
4. `git clone <repo> && cd <repo>`.
5. `cp .env.example .env` → fill EVERY value → **store the filled .env in the
   password manager** (it is half of the disaster-recovery pair; the restic
   repo is the other half).
6. `docker compose up -d --build`
   - entrypoint waits for db/redis → migrates → collectstatic → gunicorn.
   - watch: `docker compose logs -f app caddy`.
7. `docker compose exec app python manage.py createsuperuser`
8. Owner decision: start CLEAN (re-enter master data via admin UIs — recommended;
   dev DB contains validation test rows) OR import the dev dump (restore §below).
9. Smoke: login → dashboard → start an Adda → upload a pattern photo →
   `/media/...` gated for anon → public homepage renders.
10. Confirm the first nightly backup landed: `docker compose exec backup restic snapshots`.
11. **Run the restore drill once (below) before handing out worker credentials.**

## Backups (automatic)
`backup` service: nightly ~02:00 IST — `pg_dump -Fc` + `/media` → restic →
`RESTIC_REPOSITORY` (B2/R2). Retention 7 daily / 4 weekly / 6 monthly; weekly
`restic check`; 3 newest dumps also kept locally in the `backups` volume.
RPO 24 h. A pre-deploy dump is additionally taken by `deploy.sh` on every deploy.
Accepted tradeoff (noted): restic is `apk add`-ed at backup-container boot —
one unpinned package; revisit if it ever bites.
Manual backup any time: `docker compose exec backup sh -c '. /srv/backup.sh'`
(or run the pg_dump line by hand).

## Restore drill / disaster recovery
From NOTHING but: repo + password-manager .env + restic credentials.
1. Fresh VPS → steps 1-4 above → write `.env`.
2. `docker compose up -d db redis`
3. `docker compose run --rm backup sh -c 'apk add restic && restic restore latest --target /restore'`
4. `docker compose exec -T db pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists < <newest db-*.dump from /restore>`
5. Copy restored media into the volume:
   `docker compose run --rm -v media:/m backup sh -c 'cp -r /restore/media/* /m/'`
6. `docker compose up -d` → smoke (login, dashboard, one media file).
Drill passes when 1-6 complete unaided. Re-run monthly.

## Deploys / updates
`./deploy/deploy.sh` — order: pre-deploy dump → `git pull --ff-only` →
build → `up -d` (entrypoint migrates) → prune. Then smoke.

## Rollback
- Bad code: `git checkout <previous tag>` → `./deploy/deploy.sh` (skip pull).
- Bad migration: restore the `predeploy-*.dump` taken by deploy.sh, then roll
  code back. (No destructive migrations on the roadmap until V2-1d, which gets
  its own clone rehearsal.)
- Infra files (compose/Caddyfile/Dockerfile) are git-versioned — revert like code.
- Settlement cutover (V2-3 / ADR-0007 — EXECUTED): default is now `False` —
  Adda settlement is the ONLY way earnings book; the allocation path refuses
  with a clear error and its workspace UI hides. ROLLBACK = set
  `LEDGER_CREDIT_AT_ALLOCATION=True` in `.env` + restart (no deploy, no schema
  change; the cross-era guard prevents double credit in both directions, and
  the lever path stays fully tested in CI). Physical deletion of the legacy
  path is soak-gated — do not remove the lever until the real-worker soak
  passes.

## Future exits (recorded; all config-level, no app rewrites)
- Managed Postgres (Neon/RDS): change DATABASE_URL; drop db+backup pg_dump half.
- S3 media: STORAGES swap + django-storages/boto3 dep + delete the two /media/
  routes in config/urls.py; backup target changes. (Leak-audit verified: zero
  .path/MEDIA_ROOT use in business code.)
- Managed containers: push this same image; compose file maps 1:1.
