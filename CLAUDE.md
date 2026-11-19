# CLAUDE.md — operating manual for this repository

You are working on **klowb**: an institutional-style, free-first, open-source,
multi-asset quantitative research and day/swing-trading platform (US equities/ETFs,
crypto spot, forex). Live trading is disabled by default.

## Start of every session

1. Read `progress.md` (live status + exact next action).
2. Read `docs/BRAIN.md` if you have not already in this session (full context,
   decisions, environment facts, stale-knowledge traps).
3. `git status && git log --oneline -10`; reconcile with `progress.md`.
4. `python3 scripts/validate_brain.py`.
5. Work on the current phase only (`docs/plan/phases.md`).

Before you stop for any reason: update `progress.md` and `tests.json`, commit, push
to the work branch.

## Hard rules

- Never enable live trading, never place a real order, never fall back from paper
  to live. `TRADING_MODE` defaults to `research`.
- Never commit secrets or `.env`. Never log or return keys. No key in the browser.
- Never show delayed / single-venue / unofficial / simulated data as consolidated
  real-time. The feed-quality badge stays visible wherever a price is shown.
- UTC and timezone-aware timestamps internally; local time only at the UI boundary.
- No future leakage in features, signals or backtests.
- Never delete, skip or weaken a test to get green. Never `--no-verify`.
- No free-form LLM output may create or size an order.
- No infinite retries; do not blindly retry non-retryable 4xx.
- Never claim guaranteed profit, perfect picks or certainty anywhere.
- Add a dependency only after recording it (license, version, purpose, risk) in
  `docs/architecture/dependency-decisions.md`.
- Do not write chart, SDK or framework code from memory: read installed typings and
  current official docs first. Versions here are far newer than most training data
  (see `docs/BRAIN.md` §7).
- Do not push to any branch except the designated work branch; do not open a pull
  request unless the owner asks.
- Do not start phase N+1 while phase N has unfinished acceptance tests.

## Repository layout (target; created phase by phase)

```
apps/api/            FastAPI composition root (routers, lifespan, wiring)
apps/web/            Next.js app (App Router, strict TypeScript)
packages/types/      TypeScript types generated from the API's OpenAPI schema
packages/ui/         shared UI primitives (created only when reuse is real)
services/<domain>/   market_data, research, signals, agents, portfolio, risk,
                     execution, backtesting, notifications
libs/<name>/         domain, schemas, observability, providers, calendars
data/fixtures/       recorded provider payloads and replay files (committed)
data/schemas/        JSON Schemas exported from canonical models
tests/               unit, integration, contract, property, replay, e2e
docs/                architecture, decisions, plan, runbook, …
scripts/             repo tooling (stdlib only unless noted)
```

Python import roots are `apps.api`, `services.*`, `libs.*`. Allowed import
direction is in `docs/architecture.md` §3 and enforced by `import-linter`.

## Commands

Verified commands are maintained in `docs/runbook.md`. Always available (standard
library only):

```bash
python3 scripts/validate_brain.py                 # brain + tests.json integrity
python3 scripts/tests_status.py summary           # acceptance-test status by phase
python3 scripts/tests_status.py list --phase 1    # tests of one phase
python3 scripts/tests_status.py set <ID…> --status passing --command "<exact command>"
```

Update `tests.json` only through `scripts/tests_status.py` (never delete entries,
never edit descriptions to make something pass).

Backend gates (verified 2026-11-17; keep in sync with `docs/runbook.md` §5):

```bash
scripts/dev_db_setup.sh                   # local role + klowb / klowb_test databases
uv sync                                   # install Python deps
uv run ruff check . && uv run ruff format --check .
uv run mypy                               # strict; file list in pyproject.toml
uv run lint-imports                       # module boundary contracts
uv run pytest                             # unit + property (integration tests pending)
uv run alembic upgrade head               # needs DATABASE_URL or the dev default
```

Planned (not yet runnable):

```bash
pnpm install
pnpm -r typecheck && pnpm -r lint && pnpm -r test
pnpm --filter @klowb/web e2e -- --trace off   # Playwright
docker compose config -q && docker compose build
```

## Conventions

- **Python:** 3.13, type hints everywhere, mypy strict, ruff for lint + format.
  Pydantic v2 models for every boundary. `Decimal` for prices/quantities in
  canonical schemas. No naive datetimes. No bare `except`. Structured logging via
  the helpers in `libs.observability` — never `print`.
- **Errors:** classify provider/broker errors (`retryable`, `rate_limited`,
  `auth`, `invalid_request`, `not_found`, `malformed_response`, `timeout`,
  `unavailable`); only the first two and the last two may be retried, with bounded,
  jittered backoff.
- **TypeScript:** strict mode, no `any` without a comment explaining why, server
  components by default, `'use client'` only where interactivity requires it.
  Charts are client-only.
- **UI:** semantic HTML first, ARIA only when necessary, visible focus states,
  `prefers-reduced-motion` respected, every data panel has loading / error / empty /
  degraded states, every chart has a text alternative.
- **Tests:** one acceptance-test ID per behavior in `tests.json`; the ID appears in
  the test name or docstring. Use virtual clocks, seeds and fixtures — tests must
  not depend on wall-clock time or the public internet (live smoke tests are
  opt-in and marked).
- **Docs:** update in the same commit as the code (table in `docs/BRAIN.md` §9).
- **Commits:** small and logical; imperative subject; body explains why.

## Where to look

| Need | File |
|------|------|
| Full context / decisions / traps | `docs/BRAIN.md` |
| Requirements baseline | `docs/brief/original-brief.md` |
| What to do next | `progress.md`, `docs/plan/phases.md` |
| Architecture and schemas | `docs/architecture.md` |
| Dependencies and licenses | `docs/architecture/dependency-decisions.md` |
| Providers and entitlements | `docs/data-providers.md` |
| Risk / execution models | `docs/risk-model.md`, `docs/execution-model.md` |
| Security | `docs/security.md` |
| Run / test / operate | `docs/runbook.md` |
| Open questions | `docs/open-questions.md` |
