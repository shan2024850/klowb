# Phased task plan

Order and scope follow the brief exactly. Each phase lists: goal, deliverables,
acceptance tests (IDs in `tests.json`), and exit criteria. **A phase is complete
only when every one of its acceptance tests is `passing` (or `blocked` for a
recorded external reason), all quality gates in `docs/runbook.md` §5 pass, docs are
updated, and the adversarial self-review is written into `progress.md`.**

After each phase: run acceptance tests → update `tests.json` → update `progress.md`
→ inspect `git diff` → adversarial self-review → commit → push to the work branch.

Legend: ☐ not started · ◐ in progress · ☑ done. Live status is in `progress.md`;
update the marks here when a phase closes.

| Phase | Title | Tests | Status |
|-------|-------|-------|--------|
| 0 | Repository audit, research, architecture decisions, dev environment | `P0-*` (8) | ☑ |
| 1 | Canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell, health checks | `P1-*` (38) | ☐ |
| 2 | Mock market-data provider and replay framework | `P2-*` (45) | ☐ |
| 3 | One real crypto streaming provider (Kraken) with reconnect and data quality | `P3-*` (17) | ☐ |
| 4 | Dashboard with Lightweight Charts and provider-health display | `P4-*` (15) | ☐ |
| 5 | Universe selection and deterministic feature engine | `P5-*` (20) | ☐ |
| 6 | Scanner ranking and opportunity data model | `P6-*` (9) | ☐ |
| 7 | Investment-committee agent graph with mocked LLM outputs | `P7-*` (16) | ☐ |
| 8 | Actual LLM provider with typed schemas and budget controls | `P8-*` (10) | ☐ |
| 9 | Backtest / execution simulator | `P9-*` (22) | ☐ |
| 10 | Portfolio / risk engine | `P10-*` (21) | ☐ |
| 11 | Paper trading | `P11-*` (18) | ☐ |
| 12 | Stocks / FX provider adapters | `P12-*` (9) | ☐ |
| 13 | SEC / FRED / CFTC and event intelligence | `P13-*` (8) | ☐ |
| 14 | Stat-arb / ML / walk-forward research | `P14-*` (8) | ☐ |
| 15 | Production hardening | `P15-*` (10) | ☐ |

New acceptance tests may be **added** in any phase when a requirement is found to
be uncovered. Existing tests are never deleted or weakened.

---

## Phase 0 — Audit, research, decisions, environment ☑

**Goal:** know what exists, verify the outside world, decide the architecture,
write the brain.

**Deliverables (all in this repository):** repository audit
(`docs/audit/repository-audit-2026-11-17.md`); dependency/repository verification
report and licensing matrix (`docs/architecture/dependency-decisions.md`);
data-provider entitlement matrix (`docs/data-providers.md`); ADRs 0001–0011
(`docs/decisions/`); this plan; `tests.json`; `CLAUDE.md`; open questions
(`docs/open-questions.md`); evidence log (`docs/research/verification-log.md`);
`docs/BRAIN.md`; verbatim brief; `scripts/validate_brain.py`; Lightweight Charts
agent skills installed.

**Exit:** `python3 scripts/validate_brain.py` passes; no blocking contradiction
found (see `docs/open-questions.md` — none of the open items blocks Phase 1).

---

## Phase 1 — Canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell, health checks ☐

**Goal:** a running, tested, typed skeleton: the canonical data contracts, an API
with health/readiness/metrics, database migrations, a web shell that shows system
health, and every quality gate wired up.

**Work items (suggested order):**

1. Python project: `pyproject.toml` (uv, Python 3.13), ruff, mypy strict, pytest,
   hypothesis, import-linter contracts for `docs/architecture.md` §3. Record the
   installed versions in `dependency-decisions.md` §3.
2. `libs/domain`: enums (`AssetClass`, `FeedQuality`, `DataType`, `TradingMode`,
   `Timeframe`, `Side`, …), `Clock` protocol + `SystemClock`.
3. `libs/schemas`: `Instrument`, `Observation` variants, `Bar`, payload hashing,
   health DTOs, error envelope. JSON Schema export to `data/schemas/`.
4. `libs/observability`: structlog JSON logging with redaction, correlation-ID
   context + middleware, Prometheus registry and HTTP metrics.
5. `apps/api`: typed settings (trading-mode gates, `SecretStr`), app factory with
   lifespan, `/healthz`, `/readyz`, `/metrics`, `/api/v1/system/info`, error
   envelope, security headers, optional CORS allowlist.
6. Database: SQLAlchemy async engine + session, Alembic (async template), first
   migration (instruments, bars, quarantined events, audit log skeleton). Redis
   client with graceful degradation.
7. Web: pnpm workspace, Next.js 16 app (`@klowb/web`), strict TypeScript 6.0.x,
   Tailwind 4, ESLint (+ jsx-a11y), vitest + Testing Library, Playwright 1.63.0 +
   axe. App shell: landmarks, skip link, navigation to the planned routes,
   trading-mode banner, `FeedQualityBadge`, system status panel with
   loading/ok/degraded/error states. Generated API types in `packages/types`.
8. Infrastructure: `.env.example`, `docker-compose.yml` with `dev`/`test`/`prod`
   profiles (Postgres 16, Valkey, api, web), Dockerfiles (non-root),
   `scripts/smoke.sh`.
9. Dependency scan (pip-audit, pnpm audit).
10. Update `README.md`, `docs/runbook.md` (replace `[PLANNED]` with
    `[VERIFIED date]`), `docs/architecture.md` (mark built sections).

**Acceptance tests:** `P1-UNIT-001…009`, `P1-PROP-001…002`, `P1-INT-001…007`,
`P1-FAIL-001…002`, `P1-CONTRACT-001…002`, `P1-STATIC-001…004`, `P1-WEB-001…005`,
`P1-E2E-001…003`, `P1-SMOKE-001`, `P1-SEC-001…003`.

**Exit:** all gates green including an **integrated smoke test** (API + DB + Redis
+ web up together, health visible in the browser via Playwright).

**Known risks:** tool-version compatibility items C-01…C-07 in
`dependency-decisions.md` §5; Docker image pulls through the proxy.

---

## Phase 2 — Mock market-data provider and replay framework ☐

**Goal:** the entire market-data pipeline working end to end on deterministic
simulated data, including every data-quality rule and failure mode, before any
real provider is connected.

**Deliverables:** `MarketDataProvider` protocol + conformance suite; resilience
primitives (rate limiter, retry, circuit breaker, error taxonomy); `VirtualClock`;
mock provider (seeded generators + scripted fault injection); normaliser;
data-quality service + quarantine store; event bus (in-process + Redis fan-out
with fallback); bar aggregator (calendar-aware); calendars (equity via
`exchange_calendars` + extended hours, crypto 24/7, FX week); replay engine and
recorded fixtures; provider-health registry; API: instruments, bars, quarantine,
provider health, market status, WebSocket stream; ingestion supervisor.

**Acceptance tests:** `P2-UNIT-001…026`, `P2-PROP-001…002`, `P2-REPLAY-001…002`,
`P2-INT-001…007`, `P2-FAIL-001…008`.

**Exit:** replay determinism proven; every data-quality check and failure
injection has a passing test; streaming visible through the WebSocket endpoint.

---

## Phase 3 — One real crypto streaming provider (Kraken) ☐

**Goal:** real market data flowing through the same pipeline with production-grade
connection handling.

**Deliverables:** Kraken WebSocket v2 adapter (status, ticker, trade, ohlc,
heartbeat, ping), REST client for backfill and instrument metadata, symbol
mapping, Decimal-safe parsing, heartbeat watchdog, reconnect policy within
Kraken's documented limits, `trade_id` gap detection + backfill, provenance
labelling (`REALTIME_SINGLE_VENUE`), recorded contract fixtures from real
captures, a local fake Kraken server for integration tests, opt-in live smoke
test, stablecoin depeg check.

**Acceptance tests:** `P3-CONTRACT-001…002`, `P3-UNIT-001…009`, `P3-INT-001…004`,
`P3-FAIL-001`, `P3-LIVE-001`.

**Exit:** default test suite needs no internet; live smoke test passes when run
explicitly; reconnect and gap repair demonstrated against the fake server.
Resolve `OQ-T02…T05` and record results.

---

## Phase 4 — Dashboard with Lightweight Charts and provider-health display ☐

**Goal:** the first real screen: Market Command Center with an interactive
candlestick chart, volume, timeframe switching, live updates, market status and
provider health — accessible and responsive.

**Before coding:** read `.agents/skills/lightweight-charts/SKILL.md` and
`node_modules/lightweight-charts/dist/typings.d.ts`; load the data-visualisation
guidance available in the environment.

**Deliverables:** `PriceChart` (client-only, v5 API, attribution kept), chart data
mapping with whitespace for closed periods, stream hook, provider-health panel,
market-status panel, price display with feed badge, chart text alternative,
panel state components (loading/error/empty/degraded), responsive layouts,
frontend error reporting endpoint, third-party notices page.

**Acceptance tests:** `P4-WEB-001…007`, `P4-E2E-001…007`, `P4-INT-001`.

**Exit:** dashboard works against the mock provider in CI and against Kraken
manually; axe checks clean; screenshots reviewed at desktop/tablet/mobile widths.

---

## Phase 5 — Universe selection and deterministic feature engine ☐

**Deliverables:** feature registry (name, version, inputs, warm-up), feature
families from the brief (returns, trend, momentum, volatility, volume, market
structure, order flow where real data exists, cross-asset), feature snapshots
with deterministic ids, automated no-lookahead harness covering every registered
feature, multi-stage universe selection for stocks / crypto / FX with recorded
drop reasons.

**Acceptance tests:** `P5-UNIT-001…016`, `P5-PROP-001…002`, `P5-REPLAY-001`,
`P5-INT-001`.

**Exit:** every feature has golden-value tests and passes the no-lookahead
property; expensive stages never see filtered-out instruments.

---

## Phase 6 — Scanner ranking and opportunity data model ☐

**Deliverables:** `Opportunity` model; cost-aware net expected edge using the
shared cost model; deterministic ranking; scanner API; Scanner page (all columns
from the brief, feed badge, freshness); Trade Idea Detail page (chart with entry
zone, stop, targets, R:R, costs, provenance; agent evidence placeholders filled in
Phase 7).

**Acceptance tests:** `P6-UNIT-001…004`, `P6-INT-001…002`, `P6-WEB-001`,
`P6-E2E-001…002`.

---

## Phase 7 — Investment-committee agent graph (mocked LLM) ☐

**Deliverables:** `AgentSignal` contract; typed committee graph runner; routing;
deterministic agents; LLM-assisted agents behind `LLMClient` with
`MockLLMClient`; evidence-class independence; ensemble and disagreement
statistics; reliability tracker with minimum-observation gating; adversarial
critic; decision log persistence + API; Agent Decision Log page.

**Acceptance tests:** `P7-UNIT-001…010`, `P7-FAIL-001…002`, `P7-INT-001…002`,
`P7-REPLAY-001`, `P7-E2E-001`.

**Exit:** no code path from free-form text to an order; committee replay is
deterministic.

---

## Phase 8 — Actual LLM provider ☐

**Before coding:** read the current official Anthropic SDK documentation (the
`claude-api` skill if available). Do not write SDK calls from memory.

**Deliverables:** `AnthropicLLMClient` (structured outputs validated against
Pydantic schemas; default model `claude-opus-5-5`, configurable); refusal /
max-tokens handling; per-call timeout; daily budget cap; token and cost metrics;
prompt versioning; prompt-injection hardening; recorded fixtures; opt-in live
test. **LLM stays disabled by default** and requires the owner's API key.

**Acceptance tests:** `P8-UNIT-001…007`, `P8-FAIL-001…002`, `P8-LIVE-001`.

---

## Phase 9 — Backtest / execution simulator ☐

**Start by re-evaluating ADR-0008** against the then-current state of
nautilus_trader.

**Deliverables:** order model + state machine; `SimBroker` fill engine (bid/ask,
market/limit/stop, partial fills, rejections, latency, participation, market
hours, corporate actions, borrow/funding where modelled, gap-through-stop, stale
orders); cost model; event-driven backtest loop on a `VirtualClock`; data
snapshots (Parquet + DuckDB); run registry; statistics; chronological split,
walk-forward, parameter stability, out-of-sample, benchmark, bootstrap CIs,
multiple-hypothesis warning; lookahead tests; Strategy Lab page.

**Acceptance tests:** `P9-UNIT-001…016`, `P9-PROP-001…002`, `P9-REPLAY-001`,
`P9-INT-001…002`, `P9-E2E-001`.

---

## Phase 10 — Portfolio / risk engine ☐

**Deliverables:** portfolio accounting; `RiskConfig` with validated bounds; hard
rules; soft multipliers with floors; sizing and caps; kill switch (persisted,
audited); VaR / expected shortfall; risk decision log; Portfolio/Risk page.
Re-evaluate Riskfolio-Lib only if an optimisation feature is actually needed.

**Acceptance tests:** `P10-UNIT-001…017`, `P10-PROP-001…002`, `P10-INT-001`,
`P10-E2E-001`.

---

## Phase 11 — Paper trading ☐

**Precondition:** authentication, authorisation, CSRF and audit logging exist and
are tested **before** the first order endpoint is exposed.

**Deliverables:** auth + sessions; audit log; paper broker (internal); optional
Alpaca paper adapter (needs the owner's paper keys); idempotent order flow;
reconciliation; fail-closed data dependency; post-trade attribution; Order Blotter
and Post-Trade Attribution pages; mode banner.

**Acceptance tests:** `P11-UNIT-001…006`, `P11-FAIL-001…002`, `P11-CONTRACT-001`,
`P11-SEC-001…004`, `P11-INT-001…002`, `P11-E2E-001…003`.

---

## Phase 12 — Stocks / FX provider adapters ☐

**Before coding:** re-verify the entitlement facts in `docs/data-providers.md`
(they will be at least weeks old) and resolve the open provider questions.

**Deliverables:** Alpaca market-data adapter (IEX stream, delayed SIP history);
one FX/reference source; corporate actions; symbol changes, halts, delistings;
equity session-aware bars; optional `UNOFFICIAL` research fallback (off by
default); multi-asset Command Center.

**Acceptance tests:** `P12-CONTRACT-001…002`, `P12-INT-001`, `P12-UNIT-001…005`,
`P12-E2E-001`.

---

## Phase 13 — SEC / FRED / CFTC and event intelligence ☐

**Deliverables:** SEC EDGAR client (declared User-Agent, ≤ 10 req/s), FRED client
(required notice, copyrighted-series flag), CFTC COT client (release-time
awareness), ECB reference rates; event/news model with point-in-time
availability; Macro, Fundamental/Event, News and Sentiment agents wired to real
inputs; News/Events page; scheduled events on the Command Center.

**Acceptance tests:** `P13-CONTRACT-001…004`, `P13-UNIT-001…002`, `P13-INT-001`,
`P13-E2E-001`.

---

## Phase 14 — Stat-arb / ML / walk-forward research ☐

**Deliverables:** pairs/stat-arb research module; interpretable ML baselines;
time-aware CV; leakage tests; calibration; model acceptance gate (must beat
simple rules out of sample, with stability); model cards; RL flagged
research-only.

**Acceptance tests:** `P14-UNIT-001…007`, `P14-INT-001`.

---

## Phase 15 — Production hardening ☐

**Deliverables:** prod compose profile with reverse proxy and TLS notes; CSP/HSTS;
inbound rate limiting; least-privilege DB roles; bundle secret scan; backup and
restore; load and chaos tests; tracing; alert rules; full regression across
viewports; final security review.

**Acceptance tests:** `P15-SEC-001…004`, `P15-INT-001…004`, `P15-SMOKE-001`,
`P15-E2E-001`.

---

## Cross-cutting: UI pages and where they land

| Page (brief) | First version | Completed |
|--------------|---------------|-----------|
| Market Command Center | Phase 4 (status, health, chart) | Phase 12–13 (multi-asset overview, movers, breadth, volatility, regime, scheduled events) |
| Scanner | Phase 6 | Phase 7 (agent agreement) |
| Trade Idea Detail | Phase 6 | Phase 7 (evidence, timeline) |
| Agent Decision Log | Phase 7 | Phase 8 |
| Strategy Lab | Phase 9 | Phase 14 |
| Portfolio / Risk | Phase 10 | Phase 11 |
| Order Blotter | Phase 11 | Phase 11 |
| Post-Trade Attribution | Phase 11 | Phase 11 |
| News / Events | Phase 13 | Phase 13 |
