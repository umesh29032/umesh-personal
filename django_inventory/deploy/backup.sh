#!/bin/sh
# Nightly backup loop (backup service): pg_dump + media → restic → B2/R2.
# Runs at ~02:00 IST daily; retention 7d/4w/6m; weekly integrity check.
# RPO 24h. The offsite restic repo + the .env copy in the password manager are
# the disaster-recovery pair (see deploy/README.md restore drill).
set -e

apk add --no-cache restic >/dev/null 2>&1 || true   # accepted boot-time install (README note)

export PGPASSWORD="$POSTGRES_PASSWORD"

run_backup() {
    stamp=$(date +%Y%m%d-%H%M%S)
    echo "[backup] $stamp starting"
    pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
        -f "/backups/db-$stamp.dump"
    # keep only the 3 newest local dumps — offsite is the real archive
    ls -1t /backups/db-*.dump 2>/dev/null | tail -n +4 | xargs -r rm -f
    restic backup /backups /media --tag nightly
    restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
    if [ "$(date +%u)" = "7" ]; then
        echo "[backup] weekly restic check"
        restic check
    fi
    echo "[backup] done"
}

# Initialize the restic repo on first run (no-op if it exists).
restic snapshots >/dev/null 2>&1 || restic init

while true; do
    # Sleep until the next 02:00 (container TZ defaults UTC; 02:00 IST = 20:30 UTC).
    target="20:30"
    now=$(date +%s)
    next=$(date -d "today $target" +%s 2>/dev/null || date -D "%H:%M" -d "$target" +%s)
    [ "$next" -le "$now" ] && next=$((next + 86400))
    echo "[backup] sleeping $((next - now))s until next run"
    sleep $((next - now))
    run_backup || echo "[backup] FAILED — investigate (offsite copy missing for today)"
done
