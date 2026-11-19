# 0010 — Background work: supervised asyncio tasks

- Status: Accepted
- Date: 2026-11-17

## Context

Brief: "begin with the simplest reliable async/background-worker approach; do not
deploy Kafka or microservices without measured need"; asyncio for streaming
workloads. Workloads: long-lived provider streams, bar aggregation, periodic
health evaluation, later scheduled scans, committee runs and backtests.

## Decision

- Long-lived and periodic work runs as **supervised asyncio tasks inside the API
  process**, started and stopped by the FastAPI lifespan.
- A small **supervisor** owns each task: restart with bounded, jittered backoff,
  crash counting, health reporting, cooperative cancellation, clean shutdown.
- An **`EventBus` abstraction** decouples producers and consumers: in-process
  implementation by default; Redis pub/sub fan-out when Redis is available;
  automatic fallback to in-process when it is not.
- Queues are **bounded**; overflow policy is explicit per queue (drop-oldest for
  display-only streams, back-pressure for persistence) and queue depth is a
  metric.
- CPU-heavy jobs (backtests, feature recomputation) run in a process pool so they
  do not block the event loop.

## Alternatives considered

- **Celery / RQ / Dramatiq:** another moving part and broker dependency before any
  measured need.
- **Kafka / Redpanda:** explicitly ruled out by the brief at this stage.
- **Separate worker process from day one:** the `EventBus` and supervisor make
  this a later deployment choice, not a rewrite.

## Consequences

- A single process means a crash stops ingestion; the supervisor and Compose
  restart policy mitigate this, and Phase 15 revisits it.
- Durable job state (backtest runs) lives in PostgreSQL, not in the queue.

## Revisit when

Measured queue depth, event-loop lag or CPU contention shows the API process is
overloaded, or independent scaling of ingestion is needed.
