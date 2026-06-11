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

echo "[entrypoint] collecting static files…"
python manage.py collectstatic --noinput

echo "[entrypoint] starting: $*"
exec "$@"
