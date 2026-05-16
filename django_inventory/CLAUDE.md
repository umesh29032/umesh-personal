# CLAUDE.md — Kapil Enterprises Inventory

Django 5.2 + PostgreSQL. Personal project. Owner: Umesh (junior dev).

**Deep context lives in lazy-load docs — read them only when needed:**
- [ARCHITECTURE.md](ARCHITECTURE.md) — models, services, ER, security, perf
- [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) — why + how + learning map

## Rules
1. Terse. No greetings, no summaries unless asked.
2. Junior-Django mode: 1-line "why" comments naming Django/PG primitive on first touch.
3. Plan before ≥3-file edits. Use Edit not Write for existing files.
4. **Service layer owns all multi-row writes** (`config/inventory/services/`). Views call services. No signals.
5. `StockService.log(...)` is the only writer to `StockLedger`.
6. Permissions via `permission_service` (`user_has_perm` / `user_has_role`). No raw `is_superuser` checks in views.
7. Shadow `.py` files (inventory views/services/forms + `config/settings.py`) were deleted 2026-05-16. Only package forms exist. If you ever see a duplicate `.py` next to a same-named package dir, flag it.
8. gstack installed — route ship/review/qa/etc. to matching gstack skill. Don't auto-trigger.

## Run
Venv at `env/`. `env/bin/python config/manage.py <cmd>`. Settings: `config.settings.local`.

## Shortcuts
`?` → ≤2 sentences. `explain` → 5-line lesson. `fix` → patch + 1-line reason. `review` → bullets, severity-tagged.
