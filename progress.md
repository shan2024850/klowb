# Progress

**This file is the live status of the project.** Update it whenever a task is
finished, a blocker appears, or a session ends. A new contributor (human or model)
should be able to continue from this file alone, with `docs/BRAIN.md` for context.

- Last updated: 2026-11-17 (Phase 1 closed: matching-browser e2e run in the original environment)
- Work branch: `claude/hopeful-einstein-krs00n` — **all work lives on this branch;
  `main` is still empty.**
- Handoff instructions for the next agent: `docs/HANDOFF.md`

### Codex baseline (2026-11-17)

Fetched the work branch at 11fc401. Brain checks: 8/8. Tracker: 20/274.
Host version probes: Python 3.12.14, uv 0.13.6, Node 24.22.1, pnpm 11.25.0,
Docker 29.9.2. Bare `uv sync` failed on the read-only home cache. With
`export UV_CACHE_DIR=/tmp/klowb-uv-cache`, uv selected system CPython 3.13.5.
`uv sync && uv run pytest && uv run ruff check . && uv run mypy && uv run lint-imports`
passed (143 cases, 59 mypy source files, two import contracts).
Host psql, redis-server and sudo absent; host `scripts/dev_db_setup.sh` failed.
Started postgres:16 and redis:7 containers (klowb-pg and klowb-redis) with ports
5432 and 6379 published on loopback. `docker exec -i klowb-pg bash -s < scripts/dev_db_setup.sh`
created the dev role and both databases. `docker exec klowb-redis redis-cli ping` returned PONG.

---

## Current phase

- **Phase 0 — audit, research, decisions, environment: COMPLETE** (8/8 tests).
- **Phase 1 — canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell,
  health checks: COMPLETE** (38/38 acceptance tests passing; 46/274 overall).
  Screenshot of the running shell: `docs/assets/phase1-shell.png`.
- **Phase 2 — mock market-data provider and replay framework: NOT STARTED.**

---

## Finished work

### Phase 0 (2026-11-17)

Audit, dependency/licence verification, provider entitlement matrix, 11 ADRs,
architecture/risk/execution/security/runbook docs, phased plan, 274 acceptance
tests, brief preserved verbatim, `CLAUDE.md`/`AGENTS.md`/`docs/BRAIN.md`,
Lightweight Charts agent skills, `scripts/validate_brain.py`,
`scripts/tests_status.py`. Commit `980be4b`.

### Phase 1 at the original handoff (historical)

Each line says whether it is **tested** (automated test exists and passes),
**smoke-checked** (run by hand once, no automated test yet) or **untested**.

| Area | Files | State |
|------|-------|-------|
| Python project, pinned deps, tool config | `pyproject.toml`, `uv.lock` | ruff, mypy strict, pytest, import-linter configured; all pass |
| Domain enums, clock, symbol rules | `libs/domain/enums.py`, `clock.py`, `symbols.py` | **tested** (via schema tests) |
| Canonical schemas | `libs/schemas/types.py`, `market.py`, `instrument.py`, `hashing.py`, `system.py` | **tested**: 143 tests in `tests/unit/schemas/`, `tests/property/` |
| Structured logging + redaction | `libs/observability/logging.py`, `redaction.py` | smoke-checked; **no tests** |
| Correlation-ID middleware | `libs/observability/correlation.py` | smoke-checked; **no tests** |
| Prometheus metrics | `libs/observability/metrics.py` | smoke-checked; **no tests**; known defect below |
| DB / cache clients, table base, audit table | `libs/storage/database.py`, `cache.py`, `base.py`, `audit.py` | smoke-checked; **no tests** |
| Market-data tables | `services/market_data/tables.py` | migration round-trip checked by hand |
| App settings with trading-safety gates | `apps/api/settings.py` | smoke-checked (live refused); **no tests** |
| Error envelope, middleware, health, routers, app factory | `apps/api/errors.py`, `middleware.py`, `health.py`, `deps.py`, `routers/health.py`, `routers/system.py`, `main.py`, `tables.py`, `version.py` | smoke-checked; **no tests** |
| Alembic + initial migration | `alembic.ini`, `pyproject.toml [tool.alembic]`, `migrations/env.py`, `migrations/versions/20261117_dc947b200818_initial_schema.py` | upgrade → downgrade → upgrade and `alembic check` verified by hand; **no test** |
| Local DB setup script | `scripts/dev_db_setup.sh` | run successfully (idempotent) |
| Test factories | `tests/factories.py` | used by tests |

Manual smoke results (2026-11-17, `TestClient`, local PostgreSQL 16 + Redis 7):
`/healthz` 200; `/readyz` 200 with postgres+redis `up`; unreachable DB →
`/readyz` 503 `unavailable` while `/healthz` stays 200; `/api/v1/system/info`
200 with `trading_mode=research`, `live_trading_available=false`; unknown route →
404 in the standard envelope with the request's correlation id; security headers
present; `/metrics` exposes `http_requests_total` and `dependency_up`;
`Settings(trading_mode="live")` raises `LiveTradingRefused`.

### Phase 1 backend checkpoint (2026-11-17)

Completed steps 2 and 3. Added tests for settings, redaction, time policy,
liveness/readiness and dependency failures, migration round trip in a private
transactional schema, correlation, metrics, system info, errors, security
headers/CORS, canonical JSON exports and the environment example. Fixed the
prefix-aware route template and prevented opaque nested values past the redaction
depth limit from reaching log output. Generated six JSON contracts.

### Phase 1 web and deployment checkpoint (2026-11-17)

Fast-forwarded to e135a5f and reproduced the 164-case backend baseline, all
quality gates, 8/8 brain checks and 27/38 Phase 1. Read the installed Next.js
16.4.6 App Router, testing, route handler and deployment docs. Built the web
shell and pnpm workspace, generated TS types and runtime Zod validators from
the committed OpenAPI snapshot, and added component and browser tests.

All Compose profiles were built and smoke-tested with isolated databases.
dev uses a development web server, test has a tmpfs database, and prod uses the
standalone Next build and production API settings. A one-shot migrator owns
the schema. PostgreSQL and Valkey stay internal; the HTTP ports bind to loopback.
See docs/runbook.md §4–5 for setup and commands.

## Unresolved problems

**Resolved — matching-browser e2e (2026-11-17):** P1-E2E-001…003 passed in the
original Claude environment, which ships Chromium build 1243 (the exact build
Playwright 1.63.0 expects). Command and environment in "Phase 1 closing
verification" below and in each test's `notes` in `tests.json`.

**Still open — browser downloads in the Codex environment.** Codex cannot
download Playwright's browser (CDN returned HTTP 403 "Domain forbidden").
Later phases add more e2e tests (P4-E2E-*, P6-E2E-*, …). Until the owner
decides (`docs/open-questions.md` B-12), Codex runs them as an ADR-0012
diagnostic with system Chromium, records them `blocked` with that evidence, and
the matching-browser run is done in an environment that has build 1243.

History of the block (kept for the record):

The project-local Playwright 1.63.0 install requested Chromium build 1243.
The CDN returned HTTP 403 ("Domain forbidden"), including on the network retry.
The standard E2E run reported its missing headless shell. All three specs passed
in a diagnostic run against the Compose test stack using system Chromium
156.0.8078.79. ADR-0012 and the owner's instruction keep those IDs blocked.

The full JS audit has one high advisory at two dev-only versions of picomatch,
with no available patched version reported. The dated exception and mitigation
are in docs/security.md. Python and production JS audits were clean.

## Next action

Start **Phase 2 — mock market-data provider and replay framework**
(`docs/plan/phases.md` → Phase 2; 45 acceptance tests `P2-*`). Suggested order:

1. `libs/providers`: `Clock`-driven `VirtualClock` (reuse/extend
   `libs.domain.clock.ManualClock`), error taxonomy, token-bucket rate limiter,
   bounded jittered retry, circuit breaker (P2-UNIT-017…020, P2-UNIT-026).
2. `libs/calendars`: equity (XNYS via `exchange_calendars` + extended hours),
   crypto 24/7, FX week with sessions and DST (P2-UNIT-021…025). Settle C-04
   (exchange_calendars 4.13.3 with pandas 3.1.1) first and record the result;
   record both packages in `dependency-decisions.md` before installing.
3. `MarketDataProvider` protocol + shared conformance suite + seeded mock
   provider labelled `SIMULATED` (P2-UNIT-001…003).
4. `services/market_data`: normaliser, data-quality service + quarantine store,
   calendar-aware bar aggregator with finality, provider-health registry
   (P2-UNIT-004…016, P2-PROP-001…002).
5. Event bus with Redis fan-out and in-process fallback, ingestion supervisor,
   replay engine + fixtures (P2-REPLAY-*, P2-INT-006, P2-FAIL-007).
6. API: instruments, bars, quarantine, provider health, market status, WS stream
   with Origin allowlist and limits (P2-INT-001…005, P2-INT-007).
7. Failure-injection suite (P2-FAIL-001…008), all gates, docs, self-review.

Do not connect any real provider in Phase 2 (that is Phase 3).

### Current verification commands (2026-11-17)

- `uv sync && uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports`: 165 tests, lint and formatting clean, 76 typed sources, two contracts kept.
- Alembic upgrade → downgrade → upgrade and `uv run alembic check` on a separate gate database: clean.
- `uv run python -m scripts.export_openapi && pnpm --filter @klowb/types generate && git diff --exit-code -- packages/types/generated data/schemas/openapi.json && pnpm -r typecheck && uv run pytest -q tests/contract/test_openapi_snapshot.py`: reproducible contracts, type check and snapshot passed.
- `pnpm -r lint && pnpm -r test`: lint clean, three component tests passed.
- `pnpm --filter @klowb/web build`: built the shell; Compose also built and served it.
- `scripts/smoke.sh`: all three profiles passed with their respective port pairs.
- `KLOWB_WEB_URL=http://127.0.0.1:13000 KLOWB_DIAGNOSTIC_CHROMIUM=/usr/bin/chromium pnpm --filter @klowb/web e2e`: three diagnostic passes. Default runner launch blocked as above.
- `pnpm audit --prod && uv run pip-audit --cache-dir /tmp/klowb-audit`: no findings. `pnpm audit --json`: one advisory at two dev-only versions after the js-yaml override.
- `python3 scripts/validate_brain.py` and `python3 scripts/tests_status.py summary` for handoff integrity.

### Codex verification commands (2026-11-17)

- `uv run python -m scripts.export_schemas` generated the snapshots.
- `uv run pytest`: 164 passed, including service-backed cases.
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports`:
  clean, 104 formatted files, 74 typed source files, two import contracts kept.
- `node -p "require('playwright/package.json').version"`: 1.62.1.
  Default `require('playwright').chromium.launch()` failed (headless shell missing).
- Tracker updated via `scripts/tests_status.py set`. No web, Docker stack smoke
  or audit result is claimed. Test services ran in local Docker containers.
- Baseline commands and the Docker database bootstrap are recorded above.

## Commands used for verification in the original environment

Executed on 2026-11-17 in the development environment.

```bash
# Phase 0
python3 scripts/validate_brain.py                       # 8/8 checks passed

# Phase 1 environment
service postgresql start && redis-server --daemonize yes --save '' --appendonly no
scripts/dev_db_setup.sh                                 # creates role klowb, dbs klowb + klowb_test
uv sync                                                 # Python 3.13.18, deps per uv.lock

# Phase 1 gates that exist so far
uv run ruff check . && uv run ruff format --check .    # All checks passed / 88 files formatted
uv run mypy                                             # Success: no issues found in 59 source files
uv run lint-imports                                     # Contracts: 2 kept, 0 broken
uv run pytest                                           # 143 passed

# Migrations (manual)
export DATABASE_URL=postgresql+asyncpg://klowb:klowb@localhost:5432/klowb_test
uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head
uv run alembic check                                    # No new upgrade operations detected.

# Manual API smoke: create_app(Settings()) with fastapi.testclient.TestClient,
# GET /healthz, /readyz, /api/v1/system/info, /metrics, /nope; then a second app
# with an unreachable DATABASE_URL and REDIS_URL="" (results under "Finished work").
```

---

## Phase 1 closing verification (original environment, 2026-11-17)

Reviewer re-ran everything on Codex commit `5ed43e2`:

```bash
uv sync && pnpm install --frozen-lockfile
uv run pytest                                  # 165 passed
uv run ruff check . && uv run ruff format --check .   # clean, 107 files
uv run mypy                                    # 76 source files, no issues
uv run lint-imports                            # 2 contracts kept
pnpm -r typecheck && pnpm -r lint && pnpm -r test     # clean; 3 component tests passed
uv run python -m scripts.export_openapi && pnpm --filter @klowb/types generate \
  && git diff --exit-code -- packages/types/generated data/schemas/openapi.json   # reproducible
pnpm --filter @klowb/web build
pnpm audit --prod                              # No known vulnerabilities found
pnpm audit                                     # GHSA-fc5q-39xc-vjpf (picomatch 4.0.7, 2.3.2; dev-only);
                                               # registry latest is 4.0.7, advisory lists no patched version
# Stack for e2e: API + built standalone web, local PostgreSQL 16 + Redis 7
DATABASE_URL=postgresql+asyncpg://klowb:klowb@localhost:5432/klowb \
  uv run uvicorn apps.api.main:create_app --factory --host 127.0.0.1 --port 8000
cp -r apps/web/.next/static apps/web/.next/standalone/apps/web/.next/static
(cd apps/web/.next/standalone && API_ORIGIN=http://127.0.0.1:8000 PORT=3000 HOSTNAME=127.0.0.1 node apps/web/server.js)
KLOWB_WEB_URL=http://127.0.0.1:3000 pnpm --filter @klowb/web e2e --trace off --reporter=list   # 3 passed
# Browser used: /opt/pw-browsers/chromium-1243 (153.0.8010.12) = Playwright 1.63.0's expected build
```

## Adversarial self-review

### Phase 0

- Provider facts carry V/P/U verification status; unverified items default to the
  conservative choice and are listed in `docs/research/verification-log.md` §2.
- Not verified: repository last-commit dates, market-data redistribution terms,
  several free-tier details. Re-check in the phase that uses them.
- Runbook tags only executed commands as verified.

### Phase 1 (partial, at handoff)

- **Do not over-trust the backend code that has no tests.** It was smoke-checked
  once by hand; edge cases (redaction of nested secrets, CORS validation, error
  boundary after a started response, Redis disabled path) are unproven.
- A real defect was already found by testing: `str(Decimal("0.00000001"))` is
  `1E-8`; JSON serialisation now uses fixed-point (`decimal_to_plain_string`)
  with a regression test. Expect similar issues in untested code.
- `libs/schemas` rejects binary floats on purpose; adapters must parse provider
  JSON with `parse_float=Decimal` (`libs.schemas.hashing.parse_json_exact`).


### Phase 1 closing review (reviewer, 2026-11-17)

- Every Phase 1 claim from Codex was reproduced independently; no discrepancy.
- The e2e acceptance run used a locally started API + standalone web server, not
  the Compose stack. Compose itself was smoke-tested by Codex (P1-SMOKE-001);
  the two together cover the criterion, but a single e2e run against Compose
  with the matching browser has not happened yet. Do it when an environment
  has both Docker image pulls and Chromium build 1243.
- The shell's API row shows "Up" whenever readiness loaded (the readiness call
  itself proves the API answered); acceptable, but it has no latency figure.
- The picomatch exception is real and correctly scoped (dev tooling only;
  production audit clean). Recheck on every dependency update.
- Phase 1 contains no market data, prices or orders, so feed-quality display
  and trading-safety UI are only exercised as a legend and a mode badge.

### Phase 1 web and deployment self-review

- Verified three different failure paths: an optional cache outage degrades
  readiness, a required DB outage reports unavailable, and the browser shows an
  explicit network error and recovers on refresh. Unknown mode stays visibly
  unknown until system info arrives. Prices and order entry are outside this shell.
- Checked keyboard skip navigation and axe on the running shell using the
  diagnostic browser. The matching runner/browser result remains outstanding.
- Confirmed the API runs as UID 10001 and built web as UID 1000. The application
  role can read bars but cannot create objects in public and is not a superuser.
  Verified upgrades on startup and a separate migration round trip. Compose
  uses a build-only CA mount where the network requires it.
- Regeneration and strict compilation protect the OpenAPI boundary. Vite/ESLint
  continue to depend on affected picomatch versions. Revisit the exception on
  dependency updates. Later-phase navigation is explicitly labeled as planned.
