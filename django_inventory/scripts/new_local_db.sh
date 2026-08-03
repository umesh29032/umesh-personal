#!/usr/bin/env bash
# new_local_db.sh — kept for muscle memory; forwards to the real tool.
#
# There is now ONE database tool: scripts/db.sh
#   ./scripts/db.sh new <name>      create a clean database (this script)
#   ./scripts/db.sh use <name>      switch to it
#   ./scripts/db.sh list            what do I have, which am I on
#   ./scripts/db.sh save|restore    keep / bring back a copy
#   ./scripts/db.sh delete          remove one (backs up first)
#
# Two scripts doing overlapping jobs is how a toolbox becomes confusing, so the
# implementation lives in one place and this file is a five-line signpost.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ $# -eq 0 ]; then
    echo "usage: $0 <new_database_name>"
    echo "   (this is now just a shortcut for: ./scripts/db.sh new <name>)"
    exit 1
fi

echo "note: forwarding to './scripts/db.sh new $1' — that is the tool to learn."
echo
exec "$ROOT/scripts/db.sh" new "$@"
