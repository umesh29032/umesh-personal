---
name: commit-django
description: Commit current changes with a detailed Conventional Commits message, push to the active branch, and open a GitHub PR against `main`. Use when the user says `/commit-django`, "commit and PR", "ship this branch", or "commit + push + PR" inside the Kapil Enterprises Django inventory repo.
---

# /commit-django — commit, push, PR (project-local)

End-to-end ship flow for **this repo only** (`django_inventory`, owner `umesh29032/umesh-personal`, base branch `main`).

Do **not** invoke gstack `/ship` or `/land-and-deploy`. This skill is the lighter local equivalent — commit, push, open PR. No tests, no VERSION bump, no merge.

---

## Phase 1 — Inspect (parallel)

Run these in **one** message via parallel Bash calls:

1. `git status` (never `-uall` — large repos OOM)
2. `git diff` (unstaged)
3. `git diff --staged` (already staged)
4. `git log --oneline -10` (style reference)
5. `git branch --show-current`
6. `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no-upstream"`
7. `git log origin/main..HEAD --oneline 2>/dev/null` (commits already on branch beyond main)

Stop if `git status` is clean **and** no commits ahead of `main` — nothing to ship; tell user.

---

## Phase 2 — Draft commit message

Follow repo style (see `git log`): **Conventional Commits**, lowercase type, optional scope.

Allowed types seen in repo: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `perf`.

Subject line:
- ≤ 72 chars, imperative ("add", "fix", "refactor" — not "added")
- `<type>(<scope>): <summary>` — scope optional, use Django app name when changes are scoped (`accounts`, `inventory`, `config`, `templates`)

Body (REQUIRED — "detailed"):
- Blank line after subject
- Bullet list of concrete changes grouped by concern (models, services, views, templates, migrations, settings)
- Name the file/symbol changed and **why**, not just what
- Mention any new migrations by number (e.g. `migration 0011_add_xyz`)
- Call out any of: new dependencies, schema-breaking changes, permission/RBAC changes, signals (should be none per CLAUDE.md), settings.py changes
- If a change touches `StockLedger`, confirm it routes through `StockService.log(...)` (project rule)
- If a view bypasses `permission_service`, flag it in the body

Trailer (REQUIRED):
```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Heuristics for type selection
- New model / view / template / URL route → `feat`
- Bug fix, regression → `fix`
- Internal restructure, no behavior change → `refactor`
- `.gitignore`, deps, tooling, configs → `chore`
- `*.md` only → `docs`
- Tests only → `test`

### Mixed scope
If changes span apps (e.g. `accounts/` + `inventory/`), drop the scope: `feat: ...`.

---

## Phase 3 — Confirm with user

Print the drafted message in a fenced block. Ask:

> "Commit with this message, push to `<branch>`, and open PR against `main`? (y / edit / abort)"

- `y` → proceed
- `edit` → ask what to change, redraft, re-confirm
- `abort` → stop, do nothing

Skip confirmation only if user invoked with explicit `--yes` arg.

---

## Phase 4 — Stage + commit

Staging rules:
- Stage **specific** paths from `git status`, never `git add -A` / `git add .`
- **NEVER** stage: `.env`, `.env.*`, `*.sqlite3`, `*.pyc`, `__pycache__/`, `credentials.json`, `db.sqlite3`, `media/`, `staticfiles/`, anything matching `*secret*` or `*key*.json`
- If a sensitive-looking path appears in `git status`, warn user and ask before staging
- Untracked files mentioned in the diff plan must be `git add`'d explicitly

Commit via HEREDOC (preserves formatting):

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

- <bullet 1>
- <bullet 2>
- ...

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Rules:
- Never `--amend` (CLAUDE.md / harness rule — amend after hook failure destroys prior work)
- Never `--no-verify` — if a pre-commit hook fails, fix the underlying issue and create a NEW commit
- Never `--no-gpg-sign`

After commit, run `git status` to confirm tree is clean.

---

## Phase 5 — Push

```bash
git push -u origin <current-branch>
```

- Use `-u` only if upstream missing (from Phase 1 step 6).
- If upstream exists, plain `git push`.
- Never force-push. If push rejected (non-fast-forward), STOP and tell user — do not `--force` or `--force-with-lease` without explicit ask.

---

## Phase 6 — Open PR

Check first: does an open PR already exist for this branch?

```bash
gh pr view --json url,state 2>/dev/null
```

- If PR open → skip create, print existing URL.
- Else → create new PR.

Draft PR title from the **commit subject** (or, if branch has multiple commits, synthesize from `git log origin/main..HEAD`). Keep ≤ 70 chars.

PR body template (HEREDOC):

```bash
gh pr create --base main --title "<title>" --body "$(cat <<'EOF'
## Summary
- <1-3 bullets — what this PR changes at a product/behavior level>

## Changes
- <bullet per logical change group, mirroring commit body but higher-level>

## Migrations
- <list any new migrations, or "None">

## Permissions / RBAC
- <call out any permission_service / Role / sidebar registry changes, or "None">

## Test plan
- [ ] `env/bin/python config/manage.py migrate` runs clean
- [ ] `env/bin/python config/manage.py check` passes
- [ ] Manual: <feature-specific check>
- [ ] No regressions in <related screen/flow>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Print the returned PR URL to the user.

---

## Phase 7 — Final report

One-line summary:
```
Committed <sha>, pushed to <branch>, PR: <url>
```

Stop. No further action unless asked.

---

## Hard rules (project-specific)

- Base branch is **`main`**, not `master`.
- Repo: `umesh29032/umesh-personal` (personal GitHub, remote `origin` uses `github-personal` SSH host alias — already configured).
- gh CLI is authenticated as `umesh2030` — no auth setup needed.
- Stale `.py` shadows listed in CLAUDE.md (`inventory/views.py`, `services.py`, `forms.py`, `config/settings.py`) — if user staged edits to these, WARN that package wins and these are dead. Ask before committing.
- Django settings module: `config.settings.local`. If `config/settings.py` (dead shadow) is modified, flag it.
- Never auto-run migrations, tests, or the dev server as part of this skill — commit/push/PR only.
