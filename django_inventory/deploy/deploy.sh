#!/bin/sh
# Deploy/update script (run on the VPS from the repo root).
# Safety order: pre-deploy DB dump FIRST (the rollback anchor), then build,
# then switch. Rollback = git checkout <previous tag> + rerun this script;
# bad migration = restore the pre-deploy dump (deploy/README.md §rollback).
set -e

echo "[deploy] pre-deploy database dump (rollback anchor)…"
docker compose exec -T db sh -c \
    'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "predeploy-$(date +%Y%m%d-%H%M%S).dump"

echo "[deploy] pulling code…"
git pull --ff-only

echo "[deploy] building app image…"
docker compose build app

echo "[deploy] restarting stack (entrypoint migrates + collects static)…"
docker compose up -d

echo "[deploy] pruning old images…"
docker image prune -f

echo "[deploy] done. Smoke-check: login, dashboard, one media file."
