# Distributed Job Scheduler & Monitor — Requirements (v0.1)

**Goal**: Build a Python system that schedules, dispatches, executes, and monitors jobs across multiple worker processes/containers. It must be fault‑tolerant (worker crashes, timeouts), observable (logs/metrics/UI), and deterministic/offline. No external cloud services.

---

## 1. Scope & Objectives
- **Primary objectives**
  - Submit one‑off and scheduled jobs via REST API.
  - Dispatch jobs to available workers; queueing with fairness.
  - Workers execute shell commands or registered Python callables.
  - Collect stdout/stderr/exit code; persist results and logs.
  - Heartbeats and health checks; detect dead workers; reassign work.
  - Admin dashboard (HTTP) for jobs/workers/queues.
- **Non‑goals (v0.1)**
  - No multi‑tenant auth (single admin only).
  - No horizontal scale across many hosts (single docker‑compose network is sufficient).
  - No external message broker; use DB or in‑process queue with advisory locks.

---

## 2. System Overview
- **Services**: `scheduler` (FastAPI + dispatcher), `worker` (agent process), `db` (Postgres default; SQLite acceptable), optional `ui` (templated dashboard served by scheduler).
- **Queues**: Named queues (default `general`). Jobs target a queue; workers declare queue subscriptions and concurrency.
- **Dispatching**: Pull or push model acceptable; MUST be robust with at‑least‑once semantics and idempotent execution.

---

## 3. Data Model (relational)
- **jobs** (`id` UUID PK, `queue`, `type` enum `shell|python`, `payload` JSONB, `schedule_cron?`, `priority` INT, `retries_max` INT, `retries_attempted` INT DEFAULT 0, `status` enum `queued|running|succeeded|failed|canceled|expired`, `created_at`, `scheduled_at?`, `started_at?`, `finished_at?`, `result` JSONB, `stdout` TEXT, `stderr` TEXT, `error` TEXT, `owner` TEXT)
- **workers** (`id` UUID PK, `name`, `queues` TEXT[], `concurrency` INT, `last_heartbeat`, `started_at`, `status` enum `online|offline|degraded`)
- **leases** (`job_id` FK, `worker_id` FK, `leased_at`, `lease_expires_at`) for lock/visibility timeouts
- **events** (`id`, `job_id?`, `worker_id?`, `type`, `payload` JSONB, `created_at`) append‑only audit
- **schedules** (materialized next runs for cron jobs) or generate on the fly

---

## 4. Job Submission & Types
- **Shell job**: `{"type":"shell","cmd":"python script.py --flag","env":{...},"timeout_s": N}`
- **Python job**: `{"type":"python","callable":"pkg.module:function","args":[...],"kwargs":{...},"timeout_s": N}`
- **Common fields**: `queue`, `priority` (lower = higher priority), `retries_max`, `scheduled_at` (ISO ts) or `schedule_cron`.
- Payload JSON is persisted verbatim and echoed in results.

---

## 5. REST API (Scheduler)
- `POST /jobs` → submit job; returns `{id}`
- `GET /jobs/{id}` → status + metadata + logs (paginated) + result
- `POST /jobs/{id}/cancel` → best‑effort cancel
- `GET /jobs?status=&queue=&owner=&created_from=&created_to=&page=&page_size=`
- `POST /schedules` → create cron schedule (`*/5 * * * *`); returns logical schedule id
- `GET /workers` → list workers and health
- `POST /workers/register` (worker boot handshake)
- `POST /workers/{id}/heartbeat` (worker heartbeat; optional if using WS/stream)
- Errors are JSON with 4xx/5xx; OpenAPI schema must validate.

---

## 6. Dispatching, Leases & Retries
- **Visibility timeout**: when a worker leases a job, set `lease_expires_at = now + visibility_timeout`. If worker misses renewal or dies, job returns to queue.
- **Idempotency key** (optional field) prevents duplicate execution if client retries submissions.
- **Retry policy**: exponential backoff with jitter; stop at `retries_max`; record attempts.
- **Fairness**: round‑robin across queues or weighted by queue priority; within a queue order by `(priority, created_at)`.

---

## 7. Worker Agent
- On start: register with scheduler; declare `queues`, `concurrency`.
- Pull jobs (or receive via push); acquire lease atomically.
- Execute with:
  - separate subprocess for shell jobs (capture stdout/stderr, enforce `timeout_s`).
  - dynamic import for Python jobs; run in isolated process (multiprocessing) to avoid global state leakage.
- Send heartbeats every `hb_interval` (e.g., 5s) with currently running job ids.
- On graceful shutdown: finish current tasks or mark as `canceled` if interrupted.

---

## 8. Fault Tolerance & Recovery
- **Dead worker detection**: if `last_heartbeat` stale beyond threshold, mark worker `offline`, reclaim leases.
- **Crash mid‑job**: lease timeout returns job to `queued`; increment retry count.
- **Scheduler crash**: state persists in DB; workers reconnect and resume; jobs not lost.
- **Poison pill**: after `retries_max`, mark `failed` with `error` populated.

---

## 9. Scheduling (Cron & Delayed)
- Support ISO `scheduled_at` for one‑off delayed jobs.
- Support standard 5‑field cron strings; compute next run times.
- Missed runs (downtime) are executed on recovery with a cap (`catchup_limit`).

---

## 10. Admin Dashboard (Minimal)
- `/ui` (Jinja2) with: Jobs list (filters), Job detail (live log tail via SSE or polling), Workers list (status), Queues (depth, throughput).
- No auth for v0.1 (bind to localhost); future: token gate.

---

## 11. Logging & Metrics
- **Logs**: structured JSON (`ts, level, component, job_id, worker_id, event`). Store job stdout/stderr separately with pagination.
- **Metrics** (expose `/metrics` optional): `jobs_submitted_total`, `jobs_succeeded_total`, `jobs_failed_total`, `queue_depth{queue}`, `dispatch_latency_ms`, `run_time_ms`, `worker_online_gauge`.

---

## 12. Performance Targets (v0.1, local compose)
- Dispatch latency (queued→running) P95 ≤ **300 ms** with 10 workers, 100 qps submissions.
- Throughput: ≥ **50 jobs/sec** for trivial shell jobs (echo) with 10 workers.
- Log tail latency ≤ **200 ms** for active job.

---

## 13. Security & Resource Limits
- Workers run with **resource caps** (ulimits/cgroups via container): CPU shares and memory limit configurable.
- Denylist shell commands (configurable) for v0.1; sandbox heavy ops by running in containers.
- Environment allowlist for jobs; redact secrets in logs.

---

## 14. Configuration
- `.env`/YAML: `DATABASE_URL`, `VISIBILITY_TIMEOUT_S`, `LEASE_RENEWAL_S`, `RETRY_MAX_DEFAULT`, `HEARTBEAT_S`, `CATCHUP_LIMIT`, `WORKER_CONCURRENCY`, `DENYLIST_CMDS`, `LOG_LEVEL`.

---

## 15. Testing & Acceptance Criteria
- **Unit**: scheduler queue selection; lease/visibility logic; retry backoff; cron parser; log pagination.
- **Integration**: submit N jobs; assert dispatch order; worker death + reassignment; retries; timeout; result capture.
- **Chaos tests**: kill worker containers mid‑run; stop scheduler; verify recovery and no job loss.
- **Performance**: synthetic load reaching throughput & latency targets with provided compose profile.
- **Determinism**: ordered submissions with fixed seeds → identical final states.
- **Completion criterion**: All required tests pass within harness time cap for the project.

---

## 16. Directory Layout (reference)
```
scheduler/
  api/
    main.py
    routes/
  core/
    db.py
    dispatch.py
    leases.py
    schedules.py
    logging.py
  ui/
    templates/
  tests/
worker/
  agent.py
  exec_shell.py
  exec_py.py
  tests/
common/
  models.py
  dto.py
  utils.py
pyproject.toml
docker-compose.yml
README.md
```

---

## 17. Milestones
- **M1 (Skeleton)**: DB schema, FastAPI skeleton, job submit/get, basic worker register/heartbeat.
- **M2 (Dispatch + Leases)**: visibility timeout, at‑least‑once, retries; unit tests.
- **M3 (Execution)**: shell + python job executors with timeout and result capture.
- **M4 (Scheduling)**: cron + delayed jobs; catchup limit.
- **M5 (Resilience)**: dead worker reclaim; chaos tests; structured logs/metrics.
- **M6 (Perf pass)**: hit dispatch/throughput targets with provided compose profile.

---

## 18. Future Extensions
- Priority queues per user; rate limits; quotas.
- Horizontal scale with external broker (e.g., Redis/Kafka) and multiple schedulers.
- AuthN/Z for APIs and UI; audit export.
- Pluggable executors (Docker jobs, k8s, WASM sandboxes).

