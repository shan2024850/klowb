# BRAIN — complete handoff context for the klowb trading platform

**Audience:** any engineer or AI model taking over this repository with zero prior
context. Read this file top to bottom once; after that `progress.md` tells you where
the work currently stands.

**Last full revision:** 2026-11-17 (Phase 0).
**Rule:** stable knowledge lives here; *live status* lives in `progress.md`; *test
status* lives in `tests.json`. If they disagree, `progress.md` and `tests.json` win
for status, this file wins for intent and rules.

---

## 0. Resume in five minutes

1. `cat progress.md` — current phase, what is finished, what is broken, the exact
   next action, and the commands last used to verify.
2. `git status && git log --oneline -15` — confirm the tree matches what
   `progress.md` claims. If it does not, trust git and fix `progress.md` first.
3. `python3 scripts/validate_brain.py` — proves the brain documents and `tests.json`
   are structurally intact (stdlib only, needs nothing installed).
4. Open `docs/plan/phases.md` at the current phase: deliverables, acceptance test
   IDs, exit criteria.
5. Run the quality gates listed in `docs/runbook.md` §"Quality gates" before
   changing anything, so you know the baseline is green (or know exactly what is red).
6. Do the "next action" from `progress.md`. Update `progress.md` and `tests.json`
   **before** you stop for any reason (rate limit, context limit, end of session).

If you are about to run out of budget: stop coding, write `progress.md`
(what is half-done, which files are mid-edit, what command fails and how), commit,
push to the designated branch. A half-finished feature with an accurate
`progress.md` is recoverable; an undocumented one is not.

---

## 1. What we are building

An institutional-style, free-first, open-source, multi-asset quantitative research
and day/swing-trading platform ("day trading dashboard" in the owner's words):

- US equities and ETFs, crypto spot, forex; core designed so futures/options can be
  added later without a redesign.
- Deterministic numbers, evidence-driven AI research agents, explicit data
  provenance, realistic costs, reproducible backtests, adversarial review,
  transparent risk, graceful degradation.
- **Live trading is disabled by default** and nothing in this repository may place a
  real-money order without an explicit, deliberate enablement process plus human
  approval.

The full requirements baseline is `docs/brief/original-brief.md` (verbatim). When a
question comes up, re-read the relevant section of the brief rather than relying on
this summary.

### Non-negotiables (violating any of these is a defect, not a trade-off)

| # | Rule |
|---|------|
| N1 | Never claim guaranteed profit, perfect picks, zero errors or certainty — in code, UI copy, docs or commit messages. |
| N2 | `TRADING_MODE` defaults to `research`. Never enable live trading, never place a real order, never fall back from paper to live. |
| N3 | No secret in git, logs, API responses or the browser bundle. `.env` is never committed. |
| N4 | Delayed, single-venue, unofficial or simulated data is never displayed or treated as consolidated real-time. The feed-quality badge is always visible next to prices. |
| N5 | UTC everywhere internally, timezone-aware timestamps only; local/exchange time only at the UI boundary. |
| N6 | No future leakage: features, signals and backtests may only use data timestamped at or before the decision time. Automated lookahead tests guard this. |
| N7 | Execution fails closed when execution-critical data integrity is uncertain. Research may degrade with a visible warning. |
| N8 | Never delete, skip or weaken a test to make the build pass. Never use `--no-verify`. |
| N9 | No free-form LLM output can place or size an order. Orders are only created from typed, validated, risk-checked objects. |
| N10 | No unbounded retries; no blind retries of non-retryable 4xx; no unbounded Kelly sizing. |
| N11 | Do not install a dependency that is not recorded in `docs/architecture/dependency-decisions.md` with license and rationale. |
| N12 | Do not write chart/SDK code from memory. Inspect the installed typings / current official docs first (see §7). |

---

## 2. Where things stand

See `progress.md` (authoritative). Snapshot at handoff on 2026-11-17: Phase 0
complete; Phase 1 in progress — backend core written (schemas tested, the rest
smoke-checked only), web app and Docker not started; 20/274 acceptance tests
passing. Taking over from another agent: read `docs/HANDOFF.md`.

---

## 3. Document map

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Operating manual loaded by Claude Code every session: rules, commands, conventions. |
| `AGENTS.md` | Pointer for non-Claude agents to the same rules. |
| `progress.md` | **Live status**: current phase, finished work, unresolved problems, next action, verification commands. |
| `docs/HANDOFF.md` | How to hand the project to another agent (e.g. Codex), exact stopping point, and a ready-to-paste prompt. |
| `tests.json` | Every acceptance test with id, description, type, status, last execution, relevant files. |
| `docs/BRAIN.md` | This file. |
| `docs/brief/original-brief.md` | The owner's brief, verbatim. Requirements baseline. |
| `docs/plan/phases.md` | Phase-by-phase task plan with deliverables, acceptance test IDs and exit criteria. |
| `docs/architecture.md` | System architecture, module boundaries, canonical schemas, data flow, API and UI structure. |
| `docs/architecture/dependency-decisions.md` | Dependency/repository verification report and licensing matrix. |
| `docs/data-providers.md` | Data-provider entitlement matrix and adapter contract. |
| `docs/risk-model.md` | Hard/soft risk, position sizing, limits, kill switch. |
| `docs/execution-model.md` | Order model, state machine, simulator/fill/cost model, trading modes. |
| `docs/security.md` | Threat model and security controls. |
| `docs/runbook.md` | How to set up, run, test, troubleshoot and operate. |
| `docs/decisions/NNNN-*.md` | Architecture Decision Records (ADRs). |
| `docs/open-questions.md` | Unresolved questions: what must be verified from official docs, and what only the owner can decide (with the default currently assumed). |
| `docs/research/verification-log.md` | Evidence log: what was checked, where, when, and what could **not** be verified. |
| `docs/audit/repository-audit-2026-11-17.md` | Phase 0 repository and environment audit. |
| `scripts/validate_brain.py` | Stdlib-only checker for the brain documents and `tests.json`. |
| `scripts/tests_status.py` | Stdlib-only tool to update `tests.json` (`summary`, `list`, `set`, `files`) — use it instead of hand-editing JSON. |
| `.agents/skills/`, `.claude/skills/`, `skills-lock.json` | Official TradingView Lightweight Charts agent skills (pinned by commit hash). |

---

## 4. Architecture in one page

Full detail: `docs/architecture.md`. Decisions: `docs/decisions/`.

- **Shape:** modular monolith. One Python backend process (FastAPI) + one Next.js
  web app + PostgreSQL + Redis. DuckDB/Parquet files for research. Docker Compose
  for local orchestration. No Kafka, no microservices until measured need.
- **Python layout:** one uv-managed project at the repo root (Python 3.13). Import
  roots are `apps.api` (composition root), `services.<domain>` (business logic) and
  `libs.<name>` (shared kernel). Boundaries are enforced by `import-linter`
  contracts, so a domain can later be extracted into a service.
- **Dependency direction** (upper may import lower, never the reverse):

  ```
  apps.api
  services.backtesting   services.notifications
  services.agents
  services.execution
  services.risk
  services.portfolio
  services.signals
  services.research
  services.market_data
  libs.providers
  libs.calendars   libs.observability
  libs.schemas
  libs.domain
  ```

- **Data flow:** provider adapter → raw event (hashed) → normalizer → canonical
  `Observation` → data-quality service (accept / flag / quarantine) → event bus →
  bar aggregator + latest-quote cache + persistence → feature engine → universe
  filter → scanner/opportunities → agent committee → ensemble → risk → execution
  (simulator / paper / live-gated) → post-trade attribution.
- **Canonical market data:** every observation carries provenance: `provider`,
  `asset_class`, `venue`, `canonical_symbol`, `provider_symbol`, `event_timestamp`,
  `received_timestamp`, `data_type`, `feed_quality`, `delay_seconds`, `currency`,
  price/size fields, `sequence_number`, `is_adjusted`, `entitlement`,
  `redistribution_allowed`, `raw_payload_hash`. Prices and quantities are `Decimal`
  in canonical schemas; the feature engine converts to float64 at one explicit
  boundary.
- **Feed quality** (`REALTIME_CONSOLIDATED`, `REALTIME_SINGLE_VENUE`,
  `REALTIME_EXCHANGE`, `DELAYED`, `EOD`, `UNOFFICIAL`, `SIMULATED`): assigned by the
  adapter from documented entitlements, never upgraded downstream. When provenance
  is unverified the **weakest plausible** label is used.
- **Agents:** a typed committee graph implemented in-house on asyncio + Pydantic.
  Most "agents" are deterministic quantitative modules; an LLM is used only where
  language adds evidence (news, events, macro narrative, adversarial critique). All
  return the same typed `AgentSignal` contract. LLM access goes through an
  `LLMClient` protocol: `MockLLMClient` first (Phase 7), official Anthropic SDK
  with structured outputs second (Phase 8), disabled by default and budget-capped.
- **Execution:** one order model and one risk engine shared by the backtest
  simulator, paper trading and (gated, not implemented) live trading.
- **Frontend:** Next.js App Router, strict TypeScript, Tailwind CSS, Radix
  primitives, TanStack Query, Lightweight Charts (price charts), ECharts
  (analytics). The browser talks to the API through a same-origin path; no key ever
  reaches the browser.

---

## 5. Decisions already made (do not re-litigate without new evidence)

| ADR | Decision | One-line reason |
|-----|----------|-----------------|
| 0001 | Modular monolith; adapted version of the brief's repo layout | Brief default; empty repo gave no reason to deviate. |
| 0002 | Python 3.13, uv, single root project, ruff, mypy strict, pytest, hypothesis, import-linter | Smallest reliable toolchain; boundaries enforced mechanically. |
| 0003 | Next.js 16 / React 19 / **TypeScript 6.0.x (not 7)** / Tailwind 4 / Radix / pnpm / vitest / Playwright pinned to 1.63.0 (browser provisioning: ADR-0012) | typescript-eslint 8.73 supports `<6.1.0`; Playwright must match the installed browser. |
| 0004 | PostgreSQL 16 via SQLAlchemy 2.1 async + **asyncpg** (not psycopg), Alembic, Redis, DuckDB + Parquet; no TimescaleDB yet | asyncpg is Apache-2.0 (psycopg is LGPL); Timescale not yet justified. |
| 0005 | Canonical `Observation` model + feed-quality semantics + quarantine pipeline | Provenance and N4. |
| 0006 | First real streaming provider = **Kraken WebSocket v2** (native adapter); Coinbase Exchange is the documented alternate | No auth, documented heartbeat/status/ping, per-book `trade_id`; verified reachable; Binance global returns HTTP 451 here. |
| 0007 | In-house typed committee graph + `LLMClient` protocol; LangGraph / pydantic-ai / crewAI / AutoGen not adopted | Deterministic, fully traceable, fewest dependencies; AutoGen is archived. |
| 0008 | In-house event-driven backtest/execution simulator; nautilus_trader is the reference alternative; Lean/freqtrade/hummingbot not adopted | One execution model for sim/paper/live; license and runtime concerns. |
| 0009 | Trading modes `research` / `paper` / `live`; live needs five independent gates and is not implemented | Brief + N2. |
| 0010 | Background work = supervised asyncio tasks inside the API process | Simplest reliable approach. |
| 0011 | Indicators, performance analytics and sizing implemented in-house; `ta`, `quantstats`, `Riskfolio-Lib` not adopted (Riskfolio re-evaluated in Phase 10) | Determinism, testability, small dependency surface; `ta` is stale. |
| 0012 | `@playwright/test` pinned to 1.63.0 in `apps/web`; its matching Chromium is installed with `pnpm --filter @klowb/web exec playwright install chromium` unless the environment already provides it | The earlier "never run playwright install" rule described one container, not the project. |

Every ADR lists the evidence, the alternatives and the triggers that would justify
revisiting it.

---

## 6. Environment facts (cloud session container, verified 2026-11-17)

These are facts about the environment the first session ran in. A different
environment may differ — re-verify with the commands in `docs/runbook.md`.

| Item | Fact |
|------|------|
| OS / shell | Linux, bash; 4 CPUs, ~15 GB RAM |
| Node / package managers | Node v22.23.4, npm 10.9.9, pnpm 10.28.0 |
| Python | 3.13.18; uv 0.11.32 |
| PostgreSQL | 16.15 installed locally, cluster `16/main` on port 5432, **not running by default** |
| Redis | 7.0.15 installed locally, **not running by default** |
| Docker | Engine 29.9.2 + Compose v5.6.1 installed; daemon is **not running by default** but starts with `dockerd` (verified) |
| DuckDB CLI | not installed (the Python package is used instead) |
| Playwright | 1.63.0 with Chromium preinstalled at `/opt/pw-browsers` **in this container only**, so no browser download was needed here. Other environments install the matching browser with the project-local CLI (ADR-0012). |
| Outbound network | HTTPS through an agent proxy (`HTTPS_PROXY`, CA bundle `/root/.ccr/ca-bundle.crt`). PyPI and npm registries reachable. |
| GitHub from the container | `api.github.com` and `github.com` return **403 from the container** (policy). `git push/fetch` of *this* repo works. Third-party repo pages are readable only through the WebFetch tool. `npx skills add` worked (it fetched the skill files). |
| Exchange reachability | Kraken REST + WS v2: OK. Coinbase Exchange REST + WS: OK. Binance global REST: **HTTP 451** (geo-restricted from this network). Binance.US REST: 200. |
| Git | Work branch `claude/hopeful-einstein-krs00n`; default branch `main`. Push only to the work branch. No PR unless the owner asks. |

---

## 7. Traps that will bite a model working from memory

The package ecosystem moved a long way past most models' training data. **Verified
on 2026-11-17 from the PyPI and npm registries** (full table with licenses in
`docs/architecture/dependency-decisions.md`):

| Area | Current reality | Consequence |
|------|-----------------|-------------|
| Lightweight Charts | 5.3.0. v5 API: `chart.addSeries(CandlestickSeries, opts)`, `createSeriesMarkers(...)`, `createTextWatermark(...)`, panes via `paneIndex`. `addCandlestickSeries` / `series.setMarkers` are v4 and gone. `UTCTimestamp` is **seconds**. | Read `.agents/skills/lightweight-charts/SKILL.md` and `node_modules/lightweight-charts/dist/typings.d.ts` before writing chart code. |
| Lightweight Charts license | Apache-2.0 **with an attribution requirement**: show the NOTICE attribution and a link to TradingView; the `attributionLogo` chart option satisfies the link. | Never disable `layout.attributionLogo`. A test guards this. |
| TypeScript | `latest` is 7.0.2 (native compiler). `typescript-eslint` 8.73 supports `>=4.8.4 <6.1.0`. | Use TypeScript 6.0.x until typescript-eslint supports 7. |
| ESLint | 10.x (flat config only). `eslint-plugin-jsx-a11y` 6.10.2 declares peer `eslint ^3…^9`. | Verify the a11y plugin works under ESLint 10 at install time; otherwise pin ESLint 9 and record it. |
| Next.js / React | Next 16.4.6, React 19.3.1. | Check current Next docs for config/caching/async request APIs; do not assume Next 13/14 behavior. |
| Tailwind | 4.3.x: CSS-first config (`@import "tailwindcss"`, `@theme`), `@tailwindcss/postcss`. | No `tailwind.config.js`-first setup from memory. |
| Vitest / Vite | Vitest 5.1, Vite 8.3. | Check config shape at install. |
| Zod | 4.x. | v4 API differs from v3 in places. |
| Pydantic | 2.14. | v2 API only (`model_validate`, `field_validator`, `ConfigDict`). |
| FastAPI / Starlette | FastAPI 0.163, Starlette 1.10. | Lifespan handlers, not `on_event`. |
| SQLAlchemy | 2.1.9. | 2.x typed ORM (`Mapped[...]`, `mapped_column`), async engine. |
| pandas / numpy | pandas 3.1, numpy 2.5. | Copy-on-write semantics and string dtype defaults changed in pandas 3 — test, do not assume. |
| DuckDB | 2.0.0. | Check API at install. |
| redis-py | 8.1.0. | `redis.asyncio` API; verify at install. |
| pytest-asyncio | 1.5.0. | Configure `asyncio_mode` explicitly. |
| httpx | Last stable `httpx` is 0.28.1 (Dec 2024). A package named `httpx2` (2.16.x) exists and the Anthropic SDK depends on it. | Open question OQ-T01: inspect before choosing the HTTP client. |
| Anthropic API | Current default model `claude-opus-5-5`; thinking cannot be disabled on it; forced `tool_choice` is rejected; structured outputs via `output_config.format` / `client.messages.parse()`; `budget_tokens` removed. | In Phase 8 load the `claude-api` skill (or official docs) before writing any LLM code. Never date-suffix model IDs. |
| AutoGen | `microsoft/autogen` is **archived** ("no longer actively maintained by Microsoft"). | Not a candidate. |
| Polygon.io | Renamed **Massive** (massive.com). | Use the new name/hosts. |
| Kraken WS v2 | Live ticker messages contain an undocumented `trades` field; numbers are JSON floats (parse with `parse_float=Decimal`); `BTC/USD` not `XBT/USD`. | Tolerate unknown fields; keep fixtures from real captures. |

### Traps confirmed while writing Phase 1 code (2026-11-17)

| Area | Reality | Consequence |
|------|---------|-------------|
| Starlette 1.10 `TestClient` | Imports `httpx2`; plain `httpx` is deprecated there. | `httpx2` is a dependency; tests use `fastapi.testclient.TestClient`. |
| FastAPI 0.163 | `FastAPI(telemetry=...)` exists: native OpenTelemetry tracing/metrics/logs are **on by default** (global providers; no-op unless an SDK is configured). `strict_content_type=True` by default (bodies without `Content-Type` are not parsed as JSON — a CSRF mitigation). | Leave both defaults; decide on telemetry explicitly in Phase 15. |
| FastAPI 0.163 routing | Included routers are wrapped (`_IncludedRouter`); `app.routes` items may lack `.path`, and `scope["route"].path` is router-relative (no prefix). | Metrics route label currently drops `/api/v1` (open defect in `progress.md`). |
| Python `Decimal` | `str(Decimal("0.00000001"))` is `"1E-8"`. | JSON uses `format(value, "f")` (`libs.schemas.types.decimal_to_plain_string`). |
| Pydantic 2.14 | `AwareDatetime` rejects naive values (`timezone_aware`); `Decimal` fields reject NaN/Infinity (`finite_number`) but accept binary floats unless prevented. | Canonical decimal types reject floats explicitly. |
| import-linter 2.16 | A `forbidden` contract naming third-party modules requires `include_external_packages = true`. | Set in `pyproject.toml`. |
| Alembic 1.20 | Template `pyproject_async` writes `[tool.alembic]` to `pyproject.toml` and logging to `alembic.ini`. | URL comes from `Settings` in `migrations/env.py`, never from config files. |
| uv in this container | Prints a harmless `UV_NATIVE_TLS` deprecation warning. | Ignore. |

General rule: **registry metadata, installed typings and official docs beat memory.**
When they disagree with documentation, test actual behavior and record the
discrepancy in `docs/research/verification-log.md`.

---

## 8. How work is organised

- **Phases 0–15** exactly as in the brief; detail in `docs/plan/phases.md`.
- **One phase at a time.** Do not start phase N+1 while phase N has a failing or
  unimplemented acceptance test, unless the test is explicitly `blocked` with a
  recorded reason that is outside the repository's control.
- **Definition of done** (per feature): implementation, tests exist, tests pass,
  type check passes, lint passes, docs updated, observability exists, failure mode
  tested, UI has loading/error/empty/degraded states where relevant, no secret
  exposed, no TODO hiding missing critical behavior, acceptance criterion
  demonstrably met.
- **Quality gates** before a phase is called complete: backend tests, lint, type
  check; frontend tests, lint, type check; Playwright e2e; database migrations;
  Docker build; docker compose smoke test; security/dependency scan. Individual
  unit tests passing is not completion — an integrated smoke test must run.
- **After each phase:** run all phase acceptance tests → update `tests.json` →
  update `progress.md` → review `git diff` → adversarial self-review (write
  findings into `progress.md`, fix or record them) → commit → push to the work
  branch.
- **Commits:** small, logical, imperative subject, body explains why. Never commit
  secrets, `node_modules`, virtualenvs or local data.
- **Subagents:** only for genuinely independent, parallelisable work. Not for
  activity.

### Status vocabulary in `tests.json`

`planned` (specified, not written) → `implemented` (test code exists, not yet run
green) → `passing` | `failing`. `blocked` = cannot run for an external reason
(recorded in `notes`). `skipped` is **not allowed** as a way to get green. A test
may only move to `passing` with a `last_execution` timestamp and command.

---

## 9. Handoff protocol (how to keep this brain alive)

Update triggers — do these in the same commit as the change that causes them:

| When you… | Update |
|-----------|--------|
| finish or start a task, hit a blocker, or end a session | `progress.md` |
| write, run, break or fix an acceptance test | `tests.json` |
| add/remove/upgrade a dependency | `docs/architecture/dependency-decisions.md` |
| make a decision with lasting consequences | new ADR in `docs/decisions/` + row in §5 |
| learn a provider fact (limit, term, quirk) | `docs/data-providers.md` + `docs/research/verification-log.md` |
| discover docs ≠ behavior | `docs/research/verification-log.md` (discrepancy section) |
| answer or raise a question | `docs/open-questions.md` |
| change how to run/test/operate | `docs/runbook.md` |
| change module boundaries, schemas or flows | `docs/architecture.md` |
| discover an environment quirk or stale-knowledge trap | §6 / §7 of this file |

`progress.md` must always contain: current phase, finished work, unresolved
problems, next action, commands used for verification.

---

## 10. Owner decisions currently assumed (defaults; change if the owner says so)

Full list with rationale in `docs/open-questions.md` §B.

- Platform name: `klowb` (the repository name).
- Repository license: **not yet chosen** — no `LICENSE` file is added until the
  owner decides (Apache-2.0 is recommended and compatible with every adopted
  dependency).
- First market data: Kraken public feed (crypto). First paper broker: internal
  simulator, then Alpaca paper (Phase 11).
- LLM: Anthropic, model `claude-opus-5-5`, **off by default**, requires the owner's
  API key and a budget cap.
- Deployment target: local Docker Compose only.
- Auth: single-user, local-first; full session auth lands before any order-capable
  endpoint exists.

### Codex environment addendum (2026-11-17)
The §6 versions describe the first session. Codex uses system Python 3.13.5
through uv, Docker for local PostgreSQL/Redis, and a writable UV_CACHE_DIR.
Its Playwright 1.62.1 lacks the expected headless binary. The browser mismatch
is recorded in progress.md. The §7 metrics-prefix defect has a passing regression
using FastAPI's matched effective route context.

### Phase 1 web verification (2026-11-17)
The pnpm workspace, generated contracts, Next shell, builds and Compose profiles
are implemented. Use progress.md for live status. ADR-0012 was followed: the
pinned browser CDN returned HTTP 403 here; the system Chromium run is diagnostic.
