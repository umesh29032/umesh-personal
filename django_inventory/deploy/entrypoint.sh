#!/bin/sh
# App-container entrypoint (deploy direction C).
# Owner rule #2: do NOT trust depends_on ordering alone — actively wait for a
# HEALTHY database and Redis before migrate/collectstatic/gunicorn.
set -e

echo "[entrypoint] waiting for database + redis…"
python - <<'PY'
import os, sys, time

import django
django.setup()
from django.db import connections

import redis as redis_lib

deadline = time.monotonic() + 120   # 2 min then fail loudly — never boot half-up
db_ok = cache_ok = False
while time.monotonic() < deadline:
    if not db_ok:
        try:
            connections['default'].ensure_connection()
            db_ok = True
            print("[entrypoint] database: ready")
        except Exception:
            pass
    if not cache_ok:
        try:
            redis_lib.from_url(os.environ['REDIS_URL']).ping()
            cache_ok = True
            print("[entrypoint] redis: ready")
        except Exception:
            pass
    if db_ok and cache_ok:
        sys.exit(0)
    time.sleep(2)
sys.exit("[entrypoint] FATAL: db_ok=%s cache_ok=%s after 120s" % (db_ok, cache_ok))
PY

echo "[entrypoint] applying migrations…"
python manage.py migrate --noinput

# Platform master data (stages · skills · stage-access · machine types).
# Migrations alone seed only 4 of 21 stages and 2 of 10 skills, so without this
# a fresh production database comes up UNABLE TO RUN AN ADDA — no worker can
# open any stage. Safe on every boot: the command is idempotent (natural-key
# get_or_create) and additive-only, so it fills gaps and NEVER overwrites an
# edit made through the UI. Business data (products, rates, cloth, users) is
# deliberately NOT seeded — that is the factory's own to enter.
echo "[entrypoint] ensuring platform master data…"
python manage.py seed_master_data --repair-access

echo "[entrypoint] collecting static files…"
python manage.py collectstatic --noinput

echo "[entrypoint] starting: $*"
exec "$@"
