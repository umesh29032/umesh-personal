#!/usr/bin/env bash
# Design-System linter — enforces the "tokens/primitives, no raw values" governance rule.
#
# Two modes:
#   ds_lint.sh --changed   RATCHET (pre-commit): scan only ADDED lines in staged *.html.
#                          Block NEW inline raw-hex / inline font-size:Npx / inline
#                          border-radius:Npx. Existing code is NOT touched → safe to adopt
#                          mid-migration (stops new drift without forcing a full migration).
#   ds_lint.sh             REPORT (adoption score): count current violations across all
#                          templates so we track the 728→0 progress. Always exit 0.
#
# Allowed in inline style: var(--token), layout (width/flex/grid/max-width/margin/padding),
# display/position. Forbidden (new): raw #hex color, font-size:Npx, border-radius:Npx.
# The styleguide demo page is exempt (it intentionally showcases raw values).
set -euo pipefail
cd "$(dirname "$0")/.."   # -> django_inventory/

ROOT="config"
EXEMPT='styleguide.html'
# inline style="" containing a raw hex, or px font-size / border-radius (not via var())
VIOLATION='style="[^"]*(#[0-9a-fA-F]{3,6}|font-size:[[:space:]]*[0-9]+px|border-radius:[[:space:]]*[0-9]+px)'

if [ "${1:-}" = "--changed" ]; then
    # RATCHET: only added lines (+) in staged html, excluding the exempt demo page.
    files=$(git diff --cached --name-only --diff-filter=ACM -- '*.html' | grep -v "$EXEMPT" || true)
    [ -z "$files" ] && exit 0
    hits=0
    for f in $files; do
        # added lines only (strip the leading +), skip the +++ header
        added=$(git diff --cached --unified=0 -- "$f" | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^+//')
        bad=$(printf '%s\n' "$added" | grep -nE "$VIOLATION" || true)
        if [ -n "$bad" ]; then
            echo "❌ DS-LINT: new inline raw value in $f (use a token/class):"
            printf '%s\n' "$bad" | sed 's/^/     /'
            hits=$((hits+1))
        fi
    done
    if [ "$hits" -gt 0 ]; then
        echo "→ Forbidden: raw #hex / font-size:Npx / border-radius:Npx inline. Use var(--token) or a primitive class."
        exit 1
    fi
    exit 0
fi

# REPORT mode (adoption score; non-blocking)
inline_style=$(grep -rho 'style="' "$ROOT" --include=*.html | wc -l | tr -d ' ')
inline_fontsize=$(grep -rhoE 'style="[^"]*font-size:[[:space:]]*[0-9]+px' "$ROOT" --include=*.html | wc -l | tr -d ' ')
inline_radius=$(grep -rhoE 'style="[^"]*border-radius:[[:space:]]*[0-9]+px' "$ROOT" --include=*.html | wc -l | tr -d ' ')
inline_hex=$(grep -rhoE 'style="[^"]*#[0-9a-fA-F]{3,6}' "$ROOT" --include=*.html | wc -l | tr -d ' ')
page_style=$(grep -rl '<style>' "$ROOT" --include=*.html | wc -l | tr -d ' ')
echo "── Design-System adoption (lower = more centralized) ──"
echo "  inline style=\"\" attributes : $inline_style"
echo "  ├─ inline font-size:Npx    : $inline_fontsize  (→ tokens)"
echo "  ├─ inline border-radius:Npx: $inline_radius  (→ tokens)"
echo "  └─ inline raw #hex         : $inline_hex  (→ color tokens)"
echo "  templates with <style> block: $page_style  (→ shared owners)"
echo "  Ratchet (pre-commit) blocks NEW inline raw values in changed templates."
exit 0
