# Runbook

How to set up, run, verify, troubleshoot and operate klowb.

**Honesty rule for this file:** every command block is tagged.
`[VERIFIED yyyy-mm-dd]` = executed successfully in the development environment on
that date. `[PLANNED]` = expected to work once the named phase lands; replace the
tag when it has actually been run. Never tag something verified that was not run.

---

## 1. Prerequisites

| Tool | Version used in development | Notes |
|------|-----------------------------|-------|
| Python | 3.13.x | managed with `uv` 0.11.x |
| Node.js | 22.x | `pnpm` 10.28.x |
| PostgreSQL | 16.x | local service or Compose |
| Redis-protocol server | Redis 7.0.x locally; Valkey in Compose | optional at runtime (the API degrades without it) |
| Docker Engine + Compose | 29.x / v5.x | daemon must be started manually in the cloud dev container |
| Playwright | **1.63.0 with the preinstalled Chromium** | do not run `playwright install`; do not change the version |

---

## 2. Development environment (cloud session container)

### 2.1 Check the toolchain `[VERIFIED 2026-11-17]`

```bash
node -v && pnpm -v && python3 --version && uv --version
docker --version && docker compose version
psql --version && redis-server --version
node -e "console.log(require('playwright/package.json').version)"   # 1.63.0
```

### 2.2 Start local services `[VERIFIED 2026-11-17]`

```bash
# PostgreSQL 16 (cluster 16/main, port 5432)
service postgresql start
pg_lsclusters                                  # Status should be "online"
su postgres -c "psql -tAc 'select version()'"

# Redis (no persistence; dev only)
redis-server --daemonize yes --save '' --appendonly no
redis-cli ping                                 # PONG

# Docker daemon (only needed for Docker gates)
(dockerd > /tmp/dockerd.log 2>&1 &) ; sleep 8 ; docker info | grep "Server Version"
```

Create the development/test role and databases `[VERIFIED 2026-11-17]`
(idempotent; development-only password):

```bash
scripts/dev_db_setup.sh        # role klowb/klowb, databases klowb and klowb_test
PGPASSWORD=klowb psql -h localhost -U klowb -d klowb_test -tAc "select current_user"
```

### 2.3 Network facts `[VERIFIED 2026-11-17]`

- Outbound HTTPS goes through a proxy (`HTTPS_PROXY`); the CA bundle is
  `/root/.ccr/ca-bundle.crt` (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`,
  `NODE_EXTRA_CA_CERTS` are preset). Never disable TLS verification.
- PyPI and the npm registry are reachable.
- `api.github.com` and `github.com` return 403 from the container for third-party
  repositories; `git fetch/push` for this repository works.
- Kraken (`api.kraken.com`, `wss://ws.kraken.com/v2`) and Coinbase Exchange
  (`api.exchange.coinbase.com`, `wss://ws-feed.exchange.coinbase.com`) are
  reachable. `api.binance.com` returns HTTP 451.
- Python `websockets` 17.4 connects through the proxy without extra configuration.

---

## 3. Verify the brain `[VERIFIED 2026-11-17]`

```bash
python3 scripts/validate_brain.py
```

Checks: required documents exist; `tests.json` is well-formed (unique ids, valid
enums, `passing` tests have an execution record and existing files); every
repository and provider named in the brief is covered by the decision documents;
no secret-like file is tracked by git.

---

## 4. Install, run, test

Backend `[VERIFIED 2026-11-17]` (with local PostgreSQL + Redis running):

```bash
uv sync
export DATABASE_URL=postgresql+asyncpg://klowb:klowb@localhost:5432/klowb   # default if unset
uv run alembic upgrade head
uv run pytest
```

API server `[PLANNED — not yet run as a server; only exercised via TestClient]`:

```bash
uv run uvicorn apps.api.main:create_app --factory --reload --port 8000
```

Web and smoke `[PLANNED — Phase 1]`:

```bash

# Web
pnpm install
pnpm --filter @klowb/web dev            # http://localhost:3000

# Smoke
curl -s localhost:8000/healthz
curl -s localhost:8000/readyz
```

## 5. Quality gates

Run **all applicable** gates before declaring a phase complete, then record the
commands and results in `progress.md` and update `tests.json`.

| # | Gate | Command | Status |
|---|------|---------|--------|
| 0 | Brain integrity | `python3 scripts/validate_brain.py` | `[VERIFIED 2026-11-17]` |
| 1 | Backend tests | `uv run pytest` | `[VERIFIED 2026-11-17]` (143 passed; integration tests not written yet) |
| 2 | Backend lint | `uv run ruff check . && uv run ruff format --check .` | `[VERIFIED 2026-11-17]` |
| 3 | Backend type check | `uv run mypy` (files configured in `pyproject.toml`) | `[VERIFIED 2026-11-17]` |
| 4 | Module boundaries | `uv run lint-imports` | `[VERIFIED 2026-11-17]` |
| 5 | Frontend tests | `pnpm -r test` | `[PLANNED — Phase 1]` |
| 6 | Frontend lint | `pnpm -r lint` | `[PLANNED — Phase 1]` |
| 7 | Frontend type check | `pnpm -r typecheck` | `[PLANNED — Phase 1]` |
| 8 | Playwright e2e | `pnpm --filter @klowb/web e2e -- --trace off` | `[PLANNED — Phase 1]` |
| 9 | Database migrations | `uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head && uv run alembic check` | `[VERIFIED 2026-11-17]` (manual; automated test P1-INT-003 pending) |
| 10 | Docker build | `docker compose build` | `[PLANNED — Phase 1]` |
| 11 | Compose smoke test | `docker compose --profile dev up -d && scripts/smoke.sh` | `[PLANNED — Phase 1]` |
| 12 | Dependency scan | `uv run pip-audit` and `pnpm audit --prod` | `[PLANNED — Phase 1]` |

If a gate cannot run for an environmental reason, record it as `blocked` with the
evidence (command + error) — never as passed.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `certificate verify failed` | A tool ignores the preset CA bundle | Point it at `/root/.ccr/ca-bundle.crt` (see `/root/.ccr/README.md`). Never disable verification. |
| HTTP 403 from the proxy on `github.com` / `api.github.com` | Policy block for third-party repositories | Do not retry or route around. Use registry metadata (PyPI/npm) or the WebFetch tool for public pages. |
| HTTP 451 from `api.binance.com` | Geo restriction | Use Kraken/Coinbase; do not attempt to bypass. |
| `Cannot connect to the Docker daemon` | Daemon not started | Start `dockerd` (§2.2). |
| `psql: connection refused` | PostgreSQL not started | `service postgresql start`. |
| Playwright "browser not found" / version mismatch | A different Playwright version was installed | Pin `@playwright/test` to `1.63.0`; if a project must pin another version, launch with `executablePath: '/opt/pw-browsers/chromium'`. |
| `No space left on device` | Session disk allowance used | Delete build artifacts/caches (`.next`, `node_modules/.cache`, Docker images) and retry. |
| Chart code fails with `addCandlestickSeries is not a function` | v4 API used with v5 library | Use `chart.addSeries(CandlestickSeries, …)`; read the skill and installed typings. |

---

## 7. Operations (filled in as features land)

### 7.1 Trading mode

- Default `TRADING_MODE=research`: the order API rejects everything.
- `paper`: simulated orders only.
- `live`: not implemented; the process refuses to start if `TRADING_MODE=live`
  without every gate (`docs/execution-model.md` §1).

### 7.2 Incident playbooks `[PLANNED — phases noted]`

| Incident | Detection | Action |
|----------|-----------|--------|
| Provider feed stale / down (Phase 2–3) | provider health `DEGRADED`/`DOWN`, stale-feed metric, UI banner | Research continues with a degraded banner; execution for affected instruments fails closed automatically. Check provider status; the adapter reconnects with bounded backoff. |
| Sequence gap (Phase 3) | gap counter, quarantine entries | Adapter backfills over REST; if repair fails the instrument stays blocked for execution. |
| Database unavailable (Phase 1) | `/readyz` 503 `db: down` | API keeps serving liveness and cached read models where possible; writes fail with explicit errors; restore the database, then verify with `/readyz`. |
| Redis unavailable (Phase 1) | `/readyz` reports `redis: down` | API degrades to in-process bus/cache; restore Redis; no data loss expected (Redis is not a system of record). |
| LLM over budget / unavailable (Phase 8) | budget metric, agent errors | LLM-assisted agents abstain; committee continues on deterministic evidence. |
| Daily drawdown breach (Phase 10) | risk metric / alert | Kill switch moves to `BLOCK_NEW_RISK` automatically; operator reviews; disengage is manual and audited. |
| Broker disconnect (Phase 11) | broker health | New risk blocked (`BROKER_UNSAFE`); reconcile on reconnect. |

### 7.3 Kill switch `[PLANNED — Phase 10]`

Engage/disengage via the UI or API (audited). State persists across restarts.

---

## 8. Resuming work after an interruption

1. `cat progress.md`
2. `git status && git log --oneline -15`
3. `python3 scripts/validate_brain.py`
4. Start services (§2.2), run the gates that exist (§5) to establish the baseline.
5. Continue with the "Next action" in `progress.md`.
