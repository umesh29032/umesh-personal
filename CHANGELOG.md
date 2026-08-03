# Changelog

All notable changes to the Kapil Enterprises ERP.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**How this file is maintained.** Commits follow Conventional Commits
(`CONTRIBUTING.md` §4), which is what makes this file *derivable* rather than
remembered: `feat:` → Added, `fix:` → Fixed, `BREAKING CHANGE:` → a MAJOR bump.
Update it in the release PR, not months later — a changelog written from memory
is fiction.

---

## [Unreleased]

### Added
- **Engineering workflow system** — big-tech PR discipline on GitHub's free tier
  (`CONTRIBUTING.md` as the rulebook):
  - `git-hooks/pre-push` refuses direct pushes to `main`/`master`, the free
    client-side replacement for GitHub's paid server-side branch protection.
  - `git-hooks/commit-msg` enforces Conventional Commits, a ≤72-char subject and
    no trailing period.
  - `git-hooks/install.sh` installs both (git never clones `.git/hooks/`, so an
    installer is unavoidable).
  - `.github/workflows/ci.yml` — four gates on every PR: ruff + design-system
    ratchet, `makemigrations --check`, the full 2,033-test battery against a real
    Postgres service, and `knowledge_sync` BLOCKER=0. `concurrency` cancels
    superseded runs and `test` needs `lint` first, so free Actions minutes are
    not wasted.
  - `.github/CODEOWNERS`, `.github/pull_request_template.md`,
    `.github/dependabot.yml` (weekly pip + monthly actions, grouped patches).
- **Git & GitHub From Zero** — a third course at `/learn/git/`, 40 chapters on
  the same 19-section contract as the SQL and deployment courses, taught from
  this repo's own hooks, CI and real incidents.

### Changed
- Root `.gitignore` is now monorepo-wide: blocks `*.sql`, `*.dump`, `*.sql.gz`,
  `db_backups/`, `backups/`, `node_modules/` in **every** folder. Previously only
  `django_inventory/.gitignore` carried the rule, so it did not reach sibling
  projects.

### Fixed
- Untracked 2,954 files that were never code: two `pg_dump` database dumps and
  2,952 `node_modules` files from the old `Django_app/myproject/` practice app
  (`git rm --cached`, files kept on disk). A dump is plaintext, so committing one
  publishes every row.
  Audited before acting — OAuth tables empty, no plaintext passwords, 2 hashes at
  `pbkdf2_sha256` with 1,000,000 iterations, sessions long expired: **exposure
  mild**. History deliberately **not** rewritten (0 forks, repo going private,
  nothing usable inside), so the dumps remain in earlier commits by decision, not
  by oversight.

---

## [erp-v1.0.0] — 2026-07-19

First production release. Certified through an 18-phase deployment campaign;
Release Certificate verdict **GO WITH ACCEPTED RISKS**.

### Added
- Manufacturing V1 — Adda lifecycle, 12-stage configurable workflows, layering,
  cutting with size/colour breakdown and bundles, barcode generation, per-stage
  worker reporting.
- Settlement-based payroll — Option B (no ledger entry until settlement),
  settlement ≠ payment, frozen `expected_*` for visibility, advances as a
  separate owner-controlled loan pool.
- Production-truth foundation — `WorkerStageTask` / `WorkerStageContribution` as
  the sole production truth, `StagePoolSnapshot`, `WorkerStageAllocation`,
  reconciliation evidence and enforcement flags (default off, soak-gated).
- Three-concept RBAC — Role (access) × Skill (which production stage) × UserType
  (display), with sidebar and URL gated together by `SidebarItemRule`.
- Machines app — physical assets plus operator possession windows.
- Pattern intelligence — photo → geometry → marker layout.
- Learning platform at `/learn/` — SQL (25 ch) and Deployment (42 ch) courses
  rendered from markdown, with generated interview bank, mistakes and cheat sheets.
- Deployment kit — Docker Compose (Caddy, Gunicorn, Postgres, Redis), nightly
  `pg_dump` + restic off-site backups, `verify_production` post-deploy gate.

[Unreleased]: https://github.com/umesh29032/umesh-personal/compare/erp-v1.0.0...HEAD
[erp-v1.0.0]: https://github.com/umesh29032/umesh-personal/releases/tag/erp-v1.0.0
