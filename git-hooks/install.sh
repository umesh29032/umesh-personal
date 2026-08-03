#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# install.sh — install this repo's git hooks into .git/hooks/.
#
# Run once per clone, per machine:
#     bash git-hooks/install.sh
#
# WHY AN INSTALLER IS NEEDED AT ALL
# Git never clones .git/hooks/ — by design, since a cloned repo that could
# auto-run scripts on your machine would be a security hole. So committed hooks
# must be copied in deliberately. That one manual step is the price of hooks
# being safe.
#
# These hooks are how this project replaces GitHub's PAID server-side branch
# protection with a free client-side equivalent. See CONTRIBUTING.md §2.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

# Resolve the repo root from git itself, so this works from any subdirectory.
if ! GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    red "✖ Not inside a git repository."
    exit 1
fi

SRC="$GIT_ROOT/git-hooks"
DEST="$(git rev-parse --git-path hooks)"    # honours worktrees and custom layouts
mkdir -p "$DEST"

HOOKS="pre-push commit-msg"

bold "Installing git hooks"
echo "  from: $SRC"
echo "  to:   $DEST"
echo

for hook in $HOOKS; do
    if [ ! -f "$SRC/$hook" ]; then
        red "  ✖ missing source hook: $SRC/$hook"
        exit 1
    fi

    # Back up a pre-existing hook rather than silently destroying it.
    if [ -e "$DEST/$hook" ] && ! cmp -s "$SRC/$hook" "$DEST/$hook"; then
        mv "$DEST/$hook" "$DEST/$hook.backup"
        dim "  ↩ existing $hook backed up as $hook.backup"
    fi

    cp "$SRC/$hook" "$DEST/$hook"
    chmod +x "$DEST/$hook"
    green "  ✓ $hook"
done

echo
bold "What is now enforced on this machine:"
echo "  • pre-push   → refuses a direct push to 'main' (open a PR instead)"
echo "  • commit-msg → refuses a message that is not Conventional Commits"
echo
dim "Verify:      ls -l \"$DEST\""
dim "Override:    git push --no-verify   /   git commit --no-verify"
dim "Uninstall:   rm \"$DEST/pre-push\" \"$DEST/commit-msg\""
echo

# pre-commit (ruff + design-system ratchet) is a separate, Python-based tool.
if [ -f "$GIT_ROOT/django_inventory/env/bin/pre-commit" ]; then
    dim "Also available — the lint gate (ruff + design-system ratchet):"
    dim "  django_inventory/env/bin/pre-commit install --config django_inventory/.pre-commit-config.yaml"
fi
