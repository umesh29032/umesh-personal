#!/usr/bin/env bash
# db.sh — ONE command for all your local databases.
#
#   ./scripts/db.sh fresh test_production     ⭐ START HERE: create + switch +
#                                                make your login, in one step
#   ./scripts/db.sh run                       start the app on the current db
#
#   ./scripts/db.sh list                      what databases do I have?
#   ./scripts/db.sh current                   which one am I using?
#   ./scripts/db.sh new test_01               make a fresh empty factory
#   ./scripts/db.sh use test_01               switch to it
#   ./scripts/db.sh save                      save a copy of the current one
#   ./scripts/db.sh backups                   list saved copies
#   ./scripts/db.sh restore <file> --into x   bring a copy back as a new db
#   ./scripts/db.sh delete test_01 --yes-delete test_01
#
# You never type a database password — it reuses what .env already has.
#
# Safety, by design:
#   • deleting takes a backup FIRST (unless you pass --no-backup)
#   • it refuses to delete the database you are currently using
#   • it refuses to overwrite an existing database
#   • delete refuses live-looking names (prod/production/live) UNLESS the name
#     also marks itself disposable (test/dev/local/tmp/scratch/sandbox/...),
#     so test_production is fine. Creating is unrestricted — creating cannot
#     destroy anything, so a name guard there would be friction, not safety.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ $# -eq 0 ]; then
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

exec "$ROOT/env/bin/python" "$ROOT/scripts/_db_admin.py" "$@"
