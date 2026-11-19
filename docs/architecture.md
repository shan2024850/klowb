# Architecture

**Status:** target architecture, agreed in Phase 0 (2026-11-17). Sections are
marked *(built: phase N)* as they become real; anything unmarked is design intent.
Decisions with rationale: `docs/decisions/`.

---

## 1. System context

```
                        ┌──────────────────────────────────────────────┐
  Market data providers │  Kraken WS/REST · (later) Alpaca · Twelve    │
  Reference/regulatory  │  Data · SEC EDGAR · FRED · ECB · CFTC        │
  LLM provider          │  Anthropic API (off by default)              │
  Broker (paper only)   │  internal simulator · (later) Alpaca paper   │
                        └───────────────┬──────────────────────────────┘
                                        │ outbound HTTPS / WSS only
┌──────────┐  HTTPS (same origin)  ┌────▼─────────────────────────────────┐
│ Browser  │──────────────────────▶│ apps/web  Next.js (server + client)  │
│ operator │◀── WS (market stream) │   server components fetch the API    │
└──────────┘                       └────┬─────────────────────────────────┘
                                        │ HTTP (internal)
                                   ┌────▼─────────────────────────────────┐
                                   │ apps/api  FastAPI — modular monolith │
                                   │  routers · WS hub · task supervisor  │
                                   │  services.* (domain logic)           │
                                   │  libs.* (shared kernel)              │
                                   └───┬──────────────┬───────────────┬───┘
                                       │              │               │
                                 PostgreSQL 16   Redis/Valkey   DuckDB + Parquet
                                 (state, audit)  (cache, pubsub) (research files)
```

One backend process, one web process, two stateful servers, files for research.
Nothing else is deployed until a measured need exists (ADR-0001, ADR-0010).

---

## 2. Repository layout

```
/
├── CLAUDE.md  AGENTS.md  README.md  progress.md  tests.json
├── pyproject.toml  uv.lock                 # one Python project (root)
├── package.json  pnpm-workspace.yaml  pnpm-lock.yaml
├── docker-compose.yml  .env.example
├── apps/
│   ├── api/                # FastAPI composition root: main.py, routers/, deps.py, lifespan
│   └── web/                # Next.js app (App Router)
├── packages/
│   ├── types/              # generated TS types from OpenAPI (+ zod schemas)
│   └── ui/                 # shared primitives — created only when reuse is real
├── services/
│   ├── market_data/        # ingestion pipeline, normalisation, data quality, bars, replay
│   ├── research/           # universe selection, feature engine, ML research
│   ├── signals/            # scanner ranking, opportunity model
│   ├── agents/             # committee graph, agents, ensemble, LLM client
│   ├── portfolio/          # positions, P&L, exposure
│   ├── risk/               # hard/soft risk, sizing, limits, kill switch
│   ├── execution/          # order model, broker interface, simulator, paper broker
│   ├── backtesting/        # event-driven backtests, walk-forward, reports
│   └── notifications/      # alerts
├── libs/
│   ├── domain/             # enums and value objects; no I/O, no third-party beyond stdlib
│   ├── schemas/            # Pydantic models shared across services
│   ├── observability/      # logging, metrics, correlation IDs
│   ├── providers/          # provider base classes, resilience primitives, adapters
│   └── calendars/          # market sessions
├── data/
│   ├── fixtures/           # recorded provider payloads, replay files (committed)
│   └── schemas/            # JSON Schema exports of canonical models
├── migrations/             # Alembic
├── tests/
│   ├── unit/ integration/ contract/ property/ replay/
│   └── e2e/                # Playwright specs live in apps/web/e2e; this holds cross-stack smoke
├── scripts/
└── docs/
```

Deviations from the brief's proposed structure, with reasons:

| Deviation | Reason |
|-----------|--------|
| `migrations/` at the root | Alembic needs a home; migrations span all services. |
| Playwright specs in `apps/web/e2e/` | They need the web app's toolchain and config; `tests/e2e/` keeps cross-stack smoke scripts. |
| `packages/ui/` deferred | The brief says not to churn structure for aesthetics; a second consumer does not exist yet. |
| `scripts/`, `AGENTS.md`, `docs/BRAIN.md`, `docs/plan/`, `docs/research/` added | Handoff and tooling. |

---

## 3. Module boundaries

Python import roots: `apps.api`, `services.<domain>`, `libs.<name>`.

### 3.1 Layers (enforced by `import-linter`; a module may import only from layers below it)

```
apps.api
services.backtesting  |  services.notifications
services.agents
services.execution
services.risk
services.portfolio
services.signals
services.research
services.market_data
libs.providers
libs.calendars  |  libs.observability
libs.schemas
libs.domain
```

Additional contracts:

- `libs.domain` imports nothing outside the standard library.
- `libs.*` never imports `services.*` or `apps.*`.
- `services.*` never imports `apps.*`.
- Modules on the same line (`|`) are independent of each other.
- Services exchange data only through types in `libs.schemas`; a service's
  internals (`services.x._internal`, repositories, tables) are private. This is
  what makes later extraction into separate processes mechanical.
- Only `services.execution` may talk to a broker. Only `libs.providers` may open
  outbound market-data connections. Only `services.agents.llm` may call an LLM.

### 3.2 Responsibilities

| Module | Owns | Must not |
|--------|------|----------|
| `libs.domain` | `AssetClass`, `FeedQuality`, `DataType`, `TradingMode`, `Side`, `OrderType`, `OrderStatus`, `Timeframe`, error kinds, money/quantity helpers | do I/O |
| `libs.schemas` | `Instrument`, `Observation` variants, `Bar`, `ProviderHealth`, `QualityVerdict`, `QuarantinedEvent`, `FeatureSnapshot`, `Opportunity`, `AgentSignal`, `EnsembleDecision`, `RiskDecision`, `OrderIntent`, `Order`, `Fill`, `Position`, API DTOs | contain business logic |
| `libs.observability` | structlog configuration, correlation-ID context, Prometheus registry and metric helpers, redaction | know about domains |
| `libs.calendars` | `MarketCalendar` protocol; equity (exchange_calendars + extended hours), crypto 24/7, FX week | fetch network data |
| `libs.providers` | `MarketDataProvider` protocol, `Clock`, rate limiter, retry, circuit breaker, WS session supervisor, error taxonomy, mock provider, concrete adapters | persist or aggregate |
| `services.market_data` | ingestion supervisor, normaliser, data-quality service, quarantine store, bar aggregator, latest-quote cache, bar store, replay engine, provider-health registry | compute alpha |
| `services.research` | universe filters, feature registry + engine, feature snapshots, research datasets, ML experiments | place orders |
| `services.signals` | opportunity model, scanner ranking, cost-aware edge | call LLMs |
| `services.agents` | committee graph, routing, deterministic agents, LLM-assisted agents, `LLMClient`, ensemble, reliability tracker, decision log | create orders directly |
| `services.portfolio` | positions, cash, P&L, exposures | talk to brokers |
| `services.risk` | hard rules, soft multipliers, sizing, limits, kill switch, VaR/ES | be bypassed — every `OrderIntent` passes through it |
| `services.execution` | order state machine, idempotency, `Broker` protocol, simulator fill engine, paper broker, reconciliation, live gate | size positions |
| `services.backtesting` | event loop, data snapshots, run registry, walk-forward, statistics, reports | use wall-clock time |
| `services.notifications` | alert rules and delivery | block the event loop |
| `apps.api` | wiring, HTTP/WS surface, auth, lifespan (starts/stops supervised tasks) | contain domain logic |

---

## 4. Canonical data model

### 4.1 Identity

- `asset_class`: `EQUITY` | `ETF` | `CRYPTO` | `FX` | (reserved) `FUTURE` | `OPTION`.
- `canonical_symbol`: equities/ETFs = ticker in upper case (`AAPL`, `BRK.B`);
  crypto and FX = `BASE/QUOTE` (`BTC/USD`, `EUR/USD`).
- `instrument_id` = `"{asset_class_lower}:{canonical_symbol}"`, e.g.
  `crypto:BTC/USD`, `equity:AAPL`, `fx:EUR/USD`. Unique and stable; used in URLs
  (URL-encoded) and as the storage key.
- `venue`: where the data came from (`KRAKEN`, `IEX`, `SIP`, `SIM`); market
  identifier codes where they exist (`XNYS`, `XNAS`).
- `provider_symbol`: exactly what the provider calls it (`BTC/USD`, `XXBTZUSD`).
- `Instrument` carries: `kind` (`SPOT`, `PERPETUAL`, `FUTURE`, `OPTION`), `base`,
  `quote`, `currency`, `price_increment`, `quantity_increment`, `min_notional`,
  `calendar_id`, `status` (`ACTIVE`, `HALTED`, `DELISTED`), and optional derivative
  fields (`underlying_id`, `expiry`, `strike`, `option_right`, `multiplier`) that
  stay `None` for spot. These fields exist from day one so futures/options do not
  need a schema redesign.

### 4.2 Observation

A discriminated union on `data_type` (`TRADE`, `QUOTE`, `BAR`, `TICKER`). All
variants share the provenance block; the brief's field list maps as follows:

| Brief field | Type | Present on | Notes |
|-------------|------|-----------|-------|
| `provider` | str (lower-case id) | all | `kraken`, `alpaca`, `mock` |
| `asset_class` | enum | all | |
| `venue` | str | all | |
| `canonical_symbol` | str | all | validated per asset class |
| `provider_symbol` | str | all | |
| `event_timestamp` | aware datetime (UTC) | all | provider's event time; for bars = interval **start** |
| `received_timestamp` | aware datetime (UTC) | all | injected clock at receipt |
| `data_type` | enum | all | discriminator |
| `feed_quality` | enum | all | `docs/data-providers.md` §1 |
| `delay_seconds` | int ≥ 0 | all | 0 unless `DELAYED` |
| `currency` | ISO-4217 / asset code | all | quote currency of the prices |
| `bid`, `ask` | Decimal \| None | QUOTE, TICKER | plus `bid_size`, `ask_size` |
| `last` | Decimal \| None | TRADE, TICKER | trade price |
| `open`, `high`, `low`, `close` | Decimal | BAR | plus `timeframe`, `is_final`, `vwap`, `trade_count` |
| `volume` | Decimal \| None | BAR, TICKER | base-asset units |
| `trade_size` | Decimal \| None | TRADE | plus `aggressor_side` when known |
| `sequence_number` | int \| None | all | provider sequence when one exists |
| `is_adjusted` | bool | all | split/dividend adjusted |
| `entitlement` | str | all | short description of the licence tier, e.g. `kraken-public`, `alpaca-basic-iex` |
| `redistribution_allowed` | bool | all | default `False` |
| `raw_payload_hash` | hex str | all | SHA-256 over canonical JSON of the raw message fragment |

Validation at the schema level (violations → quarantined, never silently fixed):

- timestamps must be timezone-aware; they are normalised to UTC; naive → error;
- prices must be finite and > 0; sizes/volume finite and ≥ 0;
- bars: `low ≤ min(open, close)`, `high ≥ max(open, close)`, `low ≤ high`;
- `delay_seconds > 0` ⇔ `feed_quality == DELAYED`;
- symbol format per asset class.

A crossed quote (`bid > ask`) is **representable** (it can be legitimate briefly on
a consolidated tape); deciding whether it is acceptable is the quality service's
job, not the schema's.

### 4.3 Numeric policy

- Canonical schemas, orders, fills, positions, cash: `Decimal`. Quantisation to
  `price_increment` / `quantity_increment` happens in `services.execution` only.
- Feature engine, statistics, backtest analytics: `float64`. The conversion happens
  once, at the feature-engine input boundary.
- JSON: Decimals are serialised as **strings** in the API; the web client parses
  them deliberately (never `parseFloat` for anything that feeds an order ticket).

### 4.4 Time policy

- UTC everywhere inside the backend and in storage (`timestamptz`).
- All time access goes through an injected `Clock` (`SystemClock`, `VirtualClock`)
  so replay and backtests are deterministic; `datetime.now()` is banned outside
  `SystemClock` (lint rule).
- Bar timestamps are interval starts; a bar is `is_final` only once the clock has
  passed its interval end **and** the calendar says the interval was open.
- The UI formats to the user's or the exchange's timezone with
  `Intl.DateTimeFormat`; chart data stays in UTC seconds.

---

## 5. Market-data pipeline

```
adapter (WS/REST) ──raw message──▶ RawEvent{provider, received_ts, payload, hash}
        │
        ▼
   normaliser ──parse failure──────────────────────▶ quarantine (SCHEMA_INVALID)
        │ Observation
        ▼
 data-quality service (stateful per instrument+provider)
        │ verdict: ACCEPT | ACCEPT_FLAGGED(flags) | QUARANTINE(reason)
        ├──────────────── quarantine store (Postgres) ──▶ API / UI
        ▼
     event bus (in-process; Redis pub/sub fan-out when available)
        ├─▶ latest-quote cache (memory + Redis)
        ├─▶ bar aggregator (calendar-aware) ─▶ bar store (Postgres) ─▶ bus
        ├─▶ provider-health registry ─▶ metrics / API / UI
        └─▶ WebSocket hub ─▶ browsers
```

Data-quality checks (each has a test in `tests.json`): stale timestamp, duplicate
event, backwards/reordered time, sequence gap, non-positive price, crossed market,
extreme outlier (robust jump filter vs recent median/MAD and a hard percentage
band), zero/invalid volume, malformed symbol, provider latency degradation.

Degradation rules:

- **Research mode:** may fall back to another provider or a delayed feed; the UI
  shows the weaker feed-quality badge and a degraded banner.
- **Execution (paper/live):** an instrument is tradable only while its required
  feed is `HEALTHY`, fresh and at or above the minimum feed quality. Otherwise the
  risk engine rejects with a hard reason (fail closed).

Bars are never synthesised across closed periods; a missing candle stays missing
(the chart shows whitespace) unless a strategy explicitly configures forward-fill.

---

## 6. Storage

| Store | Holds | Notes |
|-------|-------|-------|
| PostgreSQL | instruments, bars, quarantined events, provider-health snapshots, feature snapshots (metadata), opportunities, agent decisions, ensemble results, risk decisions, orders, fills, positions, account ledger, audit log, backtest run registry, users/sessions | SQLAlchemy 2.1 async + asyncpg; Alembic migrations; `timestamptz`; `numeric` for money. Bars are a plain table keyed `(instrument_id, provider, timeframe, ts)`, partition-ready. TimescaleDB only if measured need (ADR-0004). |
| Redis / Valkey | latest quotes, pub/sub fan-out, rate-limit counters, short-lived caches | **Optional at runtime**: if unavailable the API degrades to in-process bus/cache and reports `redis: down`. Never the system of record. |
| DuckDB + Parquet | research datasets, backtest inputs/outputs | Data snapshots are immutable Parquet sets identified by a content hash (`data_snapshot_id`). |
| Files (`data/fixtures`) | recorded payloads, replay streams | Committed; small. |

---

## 7. Agents and ensemble (Phases 7–8)

- The committee is a **static, typed DAG** executed by a small in-house runner
  (asyncio). Nodes are `Agent` objects with typed input and output; routing is a
  pure function of `(asset_class, available data, horizon, regime, strategy
  eligibility)`. Not every agent runs for every asset.
- Agent kinds: **deterministic** (pure functions of a `FeatureSnapshot` and market
  state) and **LLM-assisted** (News, Sentiment, Fundamental/Event, Macro narrative,
  Adversarial Critic). Both return `AgentSignal` (fields exactly as in the brief).
- Evidence classes (`price_trend`, `mean_reversion`, `volatility`,
  `liquidity_order_flow`, `cross_sectional`, `statistical`, `macro`,
  `fundamental_event`, `news`, `cross_asset`): each agent declares one. The
  ensemble aggregates **within** a class first (so correlated agents are not
  double-counted) and **across** classes second.
- Ensemble: `agent_edge = calibrated_probability × expected_move × data_quality ×
  reliability`; `ensemble_edge = weighted aggregate of independent class edges −
  spread − slippage − commissions − funding − borrow − uncertainty penalty`.
  Disagreement statistics reduce confidence and size; abstention only above an
  extreme threshold; disagreement alone never means "no trade".
- Reliability history per (agent, asset class, regime, strategy, horizon) is used
  only after a minimum number of resolved observations; before that a neutral
  prior applies.
- `LLMClient` protocol with `MockLLMClient` (deterministic, fixtures) and
  `AnthropicLLMClient` (official SDK, structured outputs validated against Pydantic
  schemas, default model `claude-opus-5-5`, per-call timeout, daily budget cap,
  token/cost metrics). When the LLM is disabled, over budget, refusing or timing
  out, LLM-assisted agents return a typed `ABSTAIN` signal with a reason — the
  committee continues on deterministic evidence.
- Every decision is persisted with: input snapshot id, model, prompt version,
  raw output, parsed output, latency, token usage, error, and the downstream
  ensemble result (traceability requirement).
- An order can only originate from `EnsembleDecision → OrderIntent → RiskDecision
  → Order`. No code path turns text into an order.

---

## 8. Execution, risk, backtesting (Phases 9–11)

Detailed in `docs/execution-model.md` and `docs/risk-model.md`. Architectural
invariants:

- One `Order` model, one state machine, one risk engine, one cost model shared by
  simulator, paper and (gated) live. The only thing that changes is the `Broker`
  implementation and the clock.
- Backtests run on a `VirtualClock`, consume immutable data snapshots, and persist
  code hash, data snapshot id, parameters, provider, date range, cost model, seed
  and results.
- A decision made on bar *t* can fill no earlier than the next market event after
  *t* plus modelled latency, unless a strategy explicitly declares a
  close-auction timing model.

---

## 9. API surface (versioned under `/api/v1`)

| Endpoint | Phase | Purpose |
|----------|-------|---------|
| `GET /healthz` | 1 | Liveness; no dependency access. |
| `GET /readyz` | 1 | Readiness; per-dependency status; 503 if a required dependency is down. |
| `GET /metrics` | 1 | Prometheus exposition. |
| `GET /api/v1/system/info` | 1 | Version, trading mode, feed-quality legend, enabled providers. No secrets. |
| `GET /api/v1/providers/health` | 2 | Provider health registry. |
| `GET /api/v1/instruments` | 2 | Instrument list. |
| `GET /api/v1/bars` | 2 | Historical bars (`instrument_id`, `timeframe`, `start`, `end`, `limit`). |
| `GET /api/v1/quality/quarantine` | 2 | Quarantined events. |
| `GET /api/v1/market/status` | 2 | Session status per calendar. |
| `WS /api/v1/stream` | 2 | Subscribe to bars / quotes / health. |
| `GET /api/v1/scanner`, `/opportunities/{id}` | 6 | Ranked candidates, idea detail. |
| `GET /api/v1/agents/decisions` | 7 | Decision log. |
| `POST/GET /api/v1/backtests` | 9 | Strategy lab. |
| `GET /api/v1/portfolio`, `/risk` | 10 | Portfolio and risk state. |
| `POST/GET/DELETE /api/v1/orders` | 11 | Paper orders (auth + CSRF + audit required). |
| `GET /api/v1/news`, `/events` | 13 | News and events. |

Conventions: JSON; Decimals as strings; timestamps RFC 3339 UTC; errors as
`{"error": {"code", "message", "correlation_id", "details"}}`; cursor pagination;
every response carries `X-Request-ID`. The OpenAPI document is snapshot-tested and
is the source for generated TypeScript types.

---

## 10. Frontend

- Next.js App Router. **Server components by default**; client components only for
  interactivity (charts, live tables, forms). Charts are client-only and loaded
  with `next/dynamic` (`ssr: false`) from a client wrapper.
- The browser reaches the API through a same-origin path (`/api/...` rewritten to
  the backend) so there is no CORS surface for REST and cookies stay same-site.
  The market stream uses a WebSocket to the API with an `Origin` allowlist; private
  channels require the session.
- State: TanStack Query for server state; a small WebSocket hook feeding query
  cache/chart series; URL for navigational state. No global store until needed.
- API payloads are validated at the boundary with zod schemas generated from (or
  checked against) the OpenAPI document.
- Routes: `/` Market Command Center · `/scanner` · `/ideas/[id]` Trade Idea Detail
  · `/agents` Agent Decision Log · `/lab` Strategy Lab · `/portfolio` Portfolio/Risk
  · `/orders` Order Blotter · `/attribution` Post-Trade Attribution · `/news`
  News/Events · `/system` provider health and configuration.
- Persistent chrome: trading-mode banner (`RESEARCH` / `PAPER` / `LIVE`), provider
  health summary, degraded-data banner, skip link.
- Design language: dense, calm, typographic; tabular numerals; restrained colour
  (colour never the only signal); no decorative gradients or "AI glow".
- Responsive: desktop = multi-panel workstation; tablet = two-column, functional;
  mobile = single-column for alerts, watchlist, scanner, trade idea, risk overview
  only.
- Accessibility: semantic landmarks, keyboard reachability for every control,
  visible focus, `prefers-reduced-motion`, labelled controls, text summary/table
  alternative for every chart; automated axe checks in Playwright.
- Every data panel implements four non-happy states: loading, error, empty,
  degraded (stale or weaker feed).

---

## 11. Observability

- **Logs:** structlog JSON to stdout; fields `timestamp` (UTC), `level`, `event`,
  `correlation_id`, `service`, plus context. Secrets are redacted by a processor.
- **Correlation:** `X-Request-ID` accepted or generated per request, bound to a
  context variable, propagated into background tasks and outbound calls.
- **Metrics (Prometheus):** HTTP rate/latency/errors; dependency health gauges;
  provider latency, error rate by kind, reconnects, gaps, last-message age, stale
  alerts; quarantine counts; agent latency; LLM tokens and cost; job/queue depth;
  WebSocket clients; order lifecycle counters; DB pool stats.
- **Tracing:** OpenTelemetry hooks added in Phase 15 where helpful.
- **Frontend errors:** error boundaries report to an API endpoint (rate-limited,
  no PII) — Phase 4.

---

## 12. Configuration and trading safety

Typed settings (`pydantic-settings`) loaded from environment / `.env`. Secrets are
`SecretStr`. Key settings: `APP_ENV` (`dev`/`test`/`prod`), `TRADING_MODE`
(default `research`), `DATABASE_URL`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS`,
`LOG_LEVEL`, `MARKET_DATA_PROVIDERS`, `LLM_ENABLED` (default `false`), `LLM_MODEL`,
`LLM_DAILY_BUDGET_USD`, provider keys.

Live trading requires **all** of: `TRADING_MODE=live`; `LIVE_TRADING_ENABLED=true`;
broker credentials present; `LIVE_TRADING_ACK` equal to the exact acknowledgement
phrase; a risk configuration that validates; a per-session human arm action. If
`TRADING_MODE=live` is set and any gate is missing, the process **refuses to
start** with an explicit error (it does not quietly run in another mode). If
`TRADING_MODE` is `research` or `paper`, missing live configuration is irrelevant
and the app runs normally. No live broker adapter exists in this repository
(ADR-0009).

---

## 13. Deployment topology

Phase 1 provides a same-origin web shell, versioned system information,
readiness, liveness and metrics. The web calls two fixed server-side proxy
routes, validates responses with generated Zod schemas and reads the generated
TypeScript contracts. Screens beyond the shell remain planned.

Docker Compose profiles (choose one per project):

| Profile | Services | Use |
|---------|----------|-----|
| `dev` | postgres, valkey, api (reload), web (dev server) | local development |
| `test` | tmpfs postgres, valkey, API in test mode, standalone web | isolated integration and browser gates |
| `prod` | postgres, valkey, production API, standalone web | loopback-only on one host; reverse proxy and external deployment hardening are Phase 15 work |

Images run as non-root, with health checks. Secrets come from environment/secret
files, never baked into images.
