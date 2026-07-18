# ADR-B — Background Job Architecture (the ERP's first async worker)

**Status: DRAFT (Phase 1) — owner sign-off pending. Scope: ERP-level primitive,
introduced by AI Pattern Intelligence.**

## Problem
Nesting runs take seconds to minutes; capture reprocessing can batch. The ERP
has NO background execution today (a deliberate Manufacturing V1 absence). The
first async mechanism will become load-bearing plumbing for years, on a single
small factory server that also serves the floor — it must be boring, offline,
and owned.

## Decision
1. **Postgres-backed job queue, no new infrastructure.** A `JobRun` table in
   `patterns_ai` (MarkerRun is its first specialization): status, priority,
   payload (versioned JSON), progress fields, timeout, cancel flag, attempts,
   created/started/finished, actor.
2. **One dedicated worker process** (systemd service) polling with
   `SELECT … FOR UPDATE SKIP LOCKED`; concurrency cap = **1 CPU-heavy job**;
   per-job timeout; orphan recovery on restart (stale `running` → `retry` or
   `failed`); graceful cancel.
3. **Overnight batch window** via cron management command (e.g. bulk
   re-derivation, refinement runs) — same table, same worker.
4. Job rows are append-only history (never deleted; F5 knowledge class for
   MarkerRuns, regenerable class for transient maintenance jobs — flagged).
5. **Governance:** any OTHER module adopting this worker requires its own
   mini-ADR — this prevents the accidental-standard failure mode.

## Alternatives considered
- **Celery + Redis / django-rq** — rejected: new always-on infrastructure on a
  factory box, network dependency at deploy, ops burden; our concurrency need
  is literally one job.
- **Threads inside Django process** — rejected: dev-server lifecycle, deploy
  coupling, GIL contention with request serving.
- **Cron-only** — rejected: no interactive "generate now + watch progress" UX,
  no cancel.

## Tradeoffs
Polling adds ~1s latency to job start (irrelevant at minutes-scale). Postgres
queue lacks fancy routing (not needed). One worker = jobs serialize (desired:
protects the floor ERP's CPU).

## Consequences
The ERP gains a durable, offline, dependency-free async primitive with full
audit history. Deploy runbook gains one systemd unit + one cron line. Progress
UI reads the job row (poll), matching existing page patterns.

## Future evolution
Priority lanes, a second worker on a second box, or container execution are
config/deploy changes — the table contract stays. If a queue product is ever
truly needed, jobs migrate by draining, not by rewriting callers (interface =
service functions, not the table).

## Why it respects Manufacturing V1
Zero impact on any frozen path: no production writes, no request-cycle change,
no new dependency for the manufacturing engine; the worker only executes
`patterns_ai` services (single-writer discipline intact).

## Why it respects Blueprint V3
Offline/no-new-infra honors simplicity + open-source locks; append-only job
history honors the deletion policy (F5) and decision spine (F2 — runs are
auditable events); versioned payloads honor F3; MarkerRun contract from V3 §4
is implemented, not altered.
