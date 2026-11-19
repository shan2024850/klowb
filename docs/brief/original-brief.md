# Original project brief (verbatim source of truth)

> **Why this file exists:** the brief below was pasted into the first working session
> (2026-11-17). A model that picks this project up later has no access to that
> conversation, so the brief is preserved here. **This file is the requirements
> baseline. Do not edit the brief text.** Interpretations and decisions live in
> `docs/BRAIN.md`, `docs/decisions/` and `docs/plan/phases.md`.
>
> **Transcription notes**
> - The paste came from a PDF. Stray page numbers (15–45) and mid-sentence line
>   wraps were removed; no wording was changed.
> - The paste is **truncated at the very end**: the last sentence stops at
>   "credibility is more important than hyp" (almost certainly "hype").
>
> **The owner's own instruction that accompanied the paste (verbatim):**
>
> > Create a day trading dashboard. Make no mistakes. Read the full prompt I pasted
> > and read that in full and take your time.
> >
> > Before coding I want you to create a doc/brain so in-depth that if u hit the
> > rate limit any other model should pick it up from where u left off.
>
> **Owner's standing preference:** give direct answers to questions asked, without
> making assumptions or connecting to previous memories.

---

You are the principal engineer, quantitative research lead, trading-systems architect,
security engineer, product designer, QA lead, and adversarial reviewer for this
repository.

We are building an institutional-style, free-first, open-source, multi-asset
quantitative research and day/swing trading platform covering:

- US equities and ETFs
- crypto spot markets
- forex
- architecture capable of later supporting futures/options without redesigning the core

## PROJECT PHILOSOPHY

This is not a toy trading bot, not a generic AI dashboard, and not a system that
promises perfect predictions.

The system must behave like a disciplined quantitative investment platform:

1. deterministic numerical calculations;
2. evidence-driven AI research agents;
3. explicit data provenance;
4. realistic execution and transaction costs;
5. reproducible backtests;
6. independent adversarial review;
7. transparent portfolio and risk decisions;
8. robust software engineering;
9. graceful degradation when external providers fail;
10. live trading DISABLED by default.

Never claim guaranteed profitability, perfect picks, zero errors or certainty.

No autonomous real-money order may be submitted without an explicit, deliberate
live-trading enablement process and human approval.

## RESEARCH BEFORE IMPLEMENTATION

Before changing code:

1. Run pwd.
2. Inspect the entire repository structure.
3. Read:
   - CLAUDE.md
   - README.md
   - docs/
   - package.json / workspace config
   - pyproject.toml
   - docker-compose files
   - environment examples
   - existing tests
   - git status
   - recent git log
4. Never speculate about a file or API you have not inspected.
5. Research official/current documentation for every external dependency whose API,
   licensing, syntax, limits or behavior may have changed.
6. Prefer primary sources:
   - official documentation
   - official GitHub repository
   - exchange/broker documentation
   - government sources

   over blog posts.
7. Before adopting an open-source repository record:
   - exact repository URL
   - license
   - current release/version
   - latest meaningful activity
   - maintenance state
   - integration purpose
   - major technical risks
   - licensing implications
8. Specifically investigate and consider:

   Frontend/charting
   - https://github.com/tradingview/lightweight-charts
   - https://github.com/apache/echarts

   Trading/research
   - https://github.com/QuantConnect/Lean
   - https://github.com/nautechsystems/nautilus_trader
   - https://github.com/ccxt/ccxt
   - https://github.com/freqtrade/freqtrade
   - https://github.com/hummingbot/hummingbot
   - https://github.com/microsoft/qlib
   - https://github.com/AI4Finance-Foundation/FinRL
   - https://github.com/AI4Finance-Foundation/FinRL-Trading
   - https://github.com/OpenBB-finance/OpenBB
   - https://github.com/dcajasn/Riskfolio-Lib
   - https://github.com/ranaroussi/quantstats
   - https://github.com/bukosabino/ta

   Agent orchestration
   - https://github.com/langchain-ai/langgraph
   - https://github.com/pydantic/pydantic-ai
   - https://github.com/crewAIInc/crewAI
   - https://github.com/microsoft/autogen

DO NOT blindly install all of these.
Choose the smallest coherent set.
Treat GPL/AGPL/LGPL/Commons-Clause or other nonpermissive licensing as a design
concern.
Record the decision in docs/architecture/dependency-decisions.md.

## TRADINGVIEW LIGHTWEIGHT CHARTS

Install/read the official Agent Skills if compatible with the current Claude Code
environment:

    npx skills add tradingview/lightweight-charts

Use the current Lightweight Charts API.
Do not rely on outdated training examples.
Inspect installed package typings before implementing chart APIs.

## CLAUDE CODE WORKFLOW

Create and maintain:

    CLAUDE.md
    docs/architecture.md
    docs/data-providers.md
    docs/risk-model.md
    docs/execution-model.md
    docs/security.md
    docs/runbook.md
    docs/decisions/
    progress.md
    tests.json

progress.md must contain:

- current phase
- finished work
- unresolved problems
- next action
- commands used for verification

tests.json must list every acceptance test with:

- id
- description
- type
- current status
- last execution
- relevant files

Never delete or weaken a test to make implementation pass.

When context becomes large, write durable progress to files before continuing.

Use subagents only when tasks are truly independent or can run safely in parallel.
Do not create agents simply to produce activity.

## ARCHITECTURAL DEFAULT

Unless repository investigation reveals a strong reason otherwise:

Frontend:
- Next.js
- React
- TypeScript
- strict TypeScript
- server/client boundary kept intentional
- accessible component primitives
- responsive desktop/tablet/mobile layouts
- Lightweight Charts for financial charts
- ECharts for analytical visualization

Backend:
- Python
- FastAPI
- Pydantic v2
- asyncio for streaming workloads

Data:
- PostgreSQL for relational state
- TimescaleDB optional when justified
- Redis for cache/pubsub
- DuckDB + Parquet for research/backtests

Workers:
- begin with the simplest reliable async/background-worker approach
- do not deploy Kafka or microservices without measured need

Infrastructure:
- Docker Compose local development
- separate dev/test/prod profiles
- .env.example
- secrets never committed
- structured logs
- metrics
- tracing where helpful
- health/readiness endpoints

Start as a modular monolith.
Create domain boundaries that can later be extracted into services.

## PROPOSED REPOSITORY STRUCTURE

    /
      CLAUDE.md
      README.md
      docker-compose.yml
      .env.example
      apps/
        web/
        api/
      packages/
        ui/
        types/
      services/
        market_data/
        research/
        signals/
        agents/
        portfolio/
        risk/
        execution/
        backtesting/
        notifications/
      libs/
        domain/
        schemas/
        observability/
        providers/
        calendars/
      data/
        fixtures/
        schemas/
      tests/
        unit/
        integration/
        contract/
        property/
        replay/
        e2e/
      docs/
        architecture.md
        data-providers.md
        risk-model.md
        execution-model.md
        security.md
        runbook.md
        decisions/

Adapt this structure if the existing repo strongly suggests something better.
Do not churn structure for aesthetics.

## MARKET DATA DESIGN

Implement provider adapters behind canonical interfaces.

Every observation must include as appropriate:

    provider
    asset_class
    venue
    canonical_symbol
    provider_symbol
    event_timestamp
    received_timestamp
    data_type
    feed_quality
    delay_seconds
    currency
    bid
    ask
    last
    open
    high
    low
    close
    volume
    trade_size
    sequence_number
    is_adjusted
    entitlement
    redistribution_allowed
    raw_payload_hash

feed_quality enum must include at minimum:

    REALTIME_CONSOLIDATED
    REALTIME_SINGLE_VENUE
    REALTIME_EXCHANGE
    DELAYED
    EOD
    UNOFFICIAL
    SIMULATED

The frontend must visibly show feed quality.
Never display delayed/single-venue/unofficial data as if it were consolidated
realtime.

## PROVIDERS TO EVALUATE

Stocks:
- Alpaca
- Twelve Data
- Massive
- Tiingo
- Finnhub
- Interactive Brokers
- Alpha Vantage
- SEC EDGAR
- yfinance ONLY as noncritical research fallback
- Stooq only after verifying current terms

Macro/regulatory:
- FRED
- ECB
- CFTC COT
- SEC EDGAR

Crypto:
- Binance
- Coinbase
- Kraken
- CCXT abstraction

Provider adapters must implement:
- typed schemas
- timeout
- rate limiting
- retry with jitter for retryable failures
- circuit breaker
- reconnect strategy
- heartbeat
- sequence-gap detection when possible
- stale-data detection
- idempotency
- structured error classification
- provider health metrics

Never infinite-retry.
Do not retry nonretryable 4xx errors blindly.

Use UTC internally.
Store timezone-aware timestamps.
Render user-local or exchange-local time only at UI boundaries.

## MARKET SESSION LOGIC

Implement exchange calendars rather than assuming all instruments trade 24/7.

Support:
- regular session
- premarket
- postmarket
- holidays
- early closes
- crypto 24/7
- forex session concepts

Do not create bars across closed periods unless explicitly configured.

## DATA QUALITY

Implement a market-data quality service that detects:
- stale timestamps
- duplicate events
- backwards time
- missing sequence numbers
- impossible negative prices
- crossed markets where not legitimate
- extreme outliers
- zero/invalid volume
- malformed symbols
- provider latency degradation

Bad data must be quarantined and surfaced.

Research mode may degrade to another provider or delayed feed.

Trading execution mode must fail closed when execution-critical data integrity is
uncertain.

## UNIVERSE SELECTION

Build multi-stage universe selection.

Stocks:
- minimum price
- minimum ADV
- minimum dollar volume
- spread threshold
- market capitalization if available
- session eligibility
- corporate-event flags
- borrow availability for short candidates when known

Crypto:
- minimum quote volume
- exchange status
- spread
- depth
- funding when relevant
- stablecoin/quote currency filters

Forex:
- supported pair
- spread
- session activity
- liquidity proxy

Do not evaluate thousands of illiquid assets using expensive AI calls.
Perform deterministic quantitative screening first.
AI agents analyze the reduced candidate set.

## FEATURE ENGINE

Implement deterministic features including:

returns:
- 1m
- 5m
- 15m
- 30m
- 1h
- daily

trend:
- moving averages
- distance from moving averages
- trend slope
- breakout distance

momentum:
- ROC
- RSI if useful
- relative strength
- multi-horizon momentum

volatility:
- ATR
- realized volatility
- Parkinson/Garman-Klass where appropriate
- volatility percentile
- compression/expansion

volume:
- relative volume
- volume z-score
- VWAP
- price/VWAP distance

market structure:
- gap
- prior high/low
- opening range
- intraday high/low
- support/resistance features derived mechanically

order-flow where true data exists:
- spread
- depth
- imbalance
- aggressive trade proxy
- microprice where appropriate

cross-asset:
- rolling correlation
- beta
- residual return
- index-relative return

All features:
- deterministic
- versioned
- unit-tested
- timestamp-safe
- no future leakage

## AGENT ARCHITECTURE

Create a typed investment-committee graph.

Agents:
1. Market Data Quality Agent
2. Universe/Liquidity Agent
3. Regime Agent
4. Momentum Agent
5. Mean Reversion Agent
6. Statistical Arbitrage Agent
7. Volatility Agent
8. Technical/Market Structure Agent
9. Order Flow Agent
10. Macro Agent
11. Fundamental/Event Agent
12. News Agent
13. Sentiment Agent
14. Cross-Asset Agent
15. Portfolio Construction Agent
16. Risk Agent
17. Execution Agent
18. Independent Adversarial Critic
19. Post-Trade Attribution Agent

Do not call all agents for every asset.

Use routing based on:
- asset class
- available data
- horizon
- regime
- strategy eligibility

## AGENT OUTPUT CONTRACT

Every signal agent must return a schema like:

    symbol
    asset_class
    strategy_family
    horizon
    direction
    probability
    expected_move_bps
    expected_cost_bps
    expected_edge_bps
    confidence
    data_quality
    model_reliability
    supporting_evidence[]
    counter_evidence[]
    invalidators[]
    source_ids[]
    feature_snapshot_id
    timestamp
    model_version

No free-form output may directly place an order.

## AGENT DIVERSITY

Do not create 10 agents using identical indicators and call that diversity.

Ensure evidence comes from genuinely different classes:
- price trend
- mean reversion
- volatility
- liquidity/order flow
- cross-sectional relative value
- statistical relationships
- macro
- fundamental/event
- news
- cross-asset relationships

Prevent correlated agents from being double-counted.

Maintain rolling agent performance by:
- asset class
- regime
- strategy
- horizon

Use this reliability history only after enough observations exist.

## ENSEMBLE

Implement transparent ensemble scoring.

Suggested concept:

    agent_edge =
        calibrated_probability
        * expected_move
        * data_quality
        * reliability

    ensemble_edge =
        weighted aggregate of independent agent edges
        - spread
        - slippage
        - commissions
        - funding
        - borrow
        - uncertainty penalty

Compute disagreement statistics.

High disagreement:
- reduce confidence
- reduce size
- potentially abstain at an extreme threshold

Do NOT automatically convert any disagreement into NO TRADE.

## RISK DESIGN

There must be both hard and soft risk.

Hard risk:
- malformed/stale execution-critical data
- invalid account balance
- duplicate order
- maximum account exposure
- configured max daily drawdown
- per-symbol hard cap
- impossible stop/size
- market closed
- broker disconnect during unsafe condition
- kill switch

Soft risk:
- high volatility
- moderate disagreement
- correlation crowding
- wider spread
- event uncertainty

Soft risk should reduce position size.
It should NOT silently transform the platform into a system that never trades.

## POSITION SIZING

Risk-based sizing default:

    risk_budget = equity * configured_risk_per_trade

    base_qty = risk_budget / stop_distance

    effective_qty =
        base_qty
        * confidence_multiplier
        * liquidity_multiplier
        * regime_multiplier
        * disagreement_multiplier

Cap by:
- max notional
- max symbol exposure
- max sector/theme exposure
- max gross/net exposure
- remaining portfolio risk

No unbounded Kelly sizing.

## BACKTESTING

Implement an event-driven simulator or integrate a carefully selected engine.

Simulation must support:
- bid/ask
- market/limit/stop orders
- partial fills
- order rejection
- commissions
- slippage
- volume participation approximation
- latency
- market hours
- corporate actions
- borrow fees where modeled
- funding where modeled
- gap-through-stop behavior
- stale orders

No backtest may use a closing price to make an order that was supposedly submitted
before that close unless the strategy explicitly models that timing.

Implement automated lookahead tests.

Implement:
- chronological split
- walk-forward testing
- parameter stability testing
- out-of-sample test
- benchmark comparison
- bootstrap/confidence intervals where useful
- multiple-hypothesis warning when large parameter searches occur

Persist:
- code/version hash
- data snapshot ID
- parameters
- provider
- date range
- cost model
- random seed
- results

## ML RESEARCH

ML is optional and must earn its place.

Begin with interpretable baselines:
- logistic regression
- linear models
- tree-based models

Then consider:
- gradient boosting
- PyTorch models
- sequence models
- regime-aware models

Never deploy a model because its training accuracy looks good.

Require:
- time-aware CV
- out-of-sample performance
- probability calibration
- feature leakage test
- stability analysis
- benchmark against simple rules

FinRL/RL is research-only until independently proven.

## UI/UX

Build an institutional but usable interface.

Avoid generic AI-dashboard aesthetics.

Required pages/panels:

MARKET COMMAND CENTER
- market status
- provider health
- crypto/equity/FX overview
- major movers
- breadth
- volatility
- regime
- scheduled events

SCANNER
- ranked candidates
- asset class
- direction
- horizon
- strategy
- net expected edge
- calibrated confidence
- spread/liquidity
- regime
- agent agreement
- freshness
- data-feed badge

TRADE IDEA DETAIL
- interactive candlestick chart
- multi-timeframe switching
- volume
- VWAP
- overlays
- entry zone
- stop/invalidation
- targets
- expected R:R
- expected costs
- agent evidence
- counter-evidence
- source provenance
- timeline

AGENT DECISION LOG
- each agent
- input snapshot
- output
- probability
- evidence
- disagreement
- latency
- errors
- model/version

STRATEGY LAB
- backtest editor/config
- train/test ranges
- costs
- performance
- benchmark
- drawdown
- rolling performance
- trade distribution
- parameter sensitivity

PORTFOLIO/RISK
- cash
- positions
- unrealized/realized P&L
- gross/net exposure
- correlation
- factor/asset exposure where available
- VaR/expected shortfall where appropriate
- current risk budget
- drawdown
- concentration

ORDER BLOTTER
- submitted
- acknowledged
- partial
- filled
- rejected
- cancelled
- timestamps
- provider/broker IDs

POST-TRADE ATTRIBUTION
- expected edge
- realized result
- signal contribution
- cost difference
- execution quality
- forecast error

NEWS/EVENTS
- timestamp
- source
- symbol
- event category
- relevance
- sentiment where applicable
- link/provenance

## ACCESSIBILITY

Meet WCAG-oriented practices:
- keyboard navigation
- focus states
- semantic HTML
- ARIA only where necessary
- contrast
- reduced-motion support
- screen-reader labels
- chart alternatives/text summaries

## RESPONSIVE DESIGN

Desktop first for the full trading station.
Tablet must remain functional.

Mobile must support:
- alerts
- watchlist
- scanner
- trade idea
- risk overview

without pretending a 6-panel trading workstation fits on a phone.

## SECURITY

Implement:
- secure secrets management
- no keys exposed to browser
- no keys logged
- CSRF protection where relevant
- secure cookies
- auth/session controls
- API authorization
- input validation
- WebSocket auth where private
- dependency scanning
- rate limiting
- audit logs
- least privilege

Any live broker credentials must be server-only.
Never commit .env.

## TRADING SAFETY

Default:

    TRADING_MODE=research

Supported modes:

    research
    paper
    live

Live must require:
- explicit environment configuration
- broker credentials
- live capability flag
- human acknowledgement
- risk configuration validation

Never silently fall back from paper to live.

If live is not configured:
- application continues normally in research/paper mode.

If market data fails:
- research may show stale/degraded data with a clear warning if permitted
- execution must fail closed for instruments whose required feed is unhealthy

## OBSERVABILITY

Add:
- structured JSON logging
- correlation IDs
- provider latency
- provider error rates
- agent latency
- token/cost usage
- job queue depth
- websocket reconnect counts
- stale feed alerts
- order lifecycle metrics
- DB health
- frontend error reporting

Every agent decision should be traceable to:
- input snapshot
- model
- prompt version
- output
- downstream ensemble result

## TESTING

Use multiple layers.

Python:
- pytest
- property-based tests where useful
- type checking
- linting

TypeScript:
- typecheck
- lint
- unit/component tests

E2E:
- Playwright

Contract tests:
- provider response fixtures
- schema compatibility

Replay tests:
- feed recorded events through pipeline
- confirm deterministic final state

Failure injection:
- API 429
- API 500
- timeout
- malformed JSON
- disconnected websocket
- stale event
- duplicate event
- reordered event
- DB unavailable
- Redis unavailable
- agent timeout
- broker rejection
- partial fill

## FINANCIAL EDGE CASES

Test:
- DST transition
- early close
- market holiday
- weekend crypto
- symbol changes
- stock splits
- dividends
- reverse splits
- halted asset
- delisting
- zero-volume bar
- missing candle
- crossed bid/ask
- huge gap
- negative/zero erroneous price
- crypto decimal precision
- forex pip precision
- stablecoin depeg
- rate-limit exhaustion
- sequence gap
- duplicate order acknowledgement

## QUALITY GATES

Before considering any phase complete run all applicable:

    backend tests
    backend lint
    backend typecheck
    frontend tests
    frontend lint
    frontend typecheck
    Playwright e2e
    database migrations
    Docker build
    docker compose smoke test
    security/dependency scan

Do not declare success because individual unit tests pass.
Perform an actual integrated smoke test.

## DEFINITION OF DONE

A feature is done only when:

1. implementation exists;
2. tests exist;
3. tests pass;
4. type checking passes;
5. lint passes;
6. docs updated;
7. observability exists;
8. failure mode tested;
9. UI state for loading/error/empty/degraded exists where relevant;
10. no secret is exposed;
11. no TODO masks missing critical behavior;
12. acceptance criterion is demonstrably satisfied.

## IMPLEMENTATION ORDER

Do NOT try to generate the entire platform in one uncontrolled pass.

PHASE 0
Repository audit, research, architecture decisions and development environment.

PHASE 1
Canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell, health checks.

PHASE 2
Mock market-data provider and replay framework.

PHASE 3
One real crypto streaming provider with reconnect and data-quality handling.

PHASE 4
Dashboard with Lightweight Charts and provider-health display.

PHASE 5
Universe selection and deterministic feature engine.

PHASE 6
Scanner ranking and opportunity data model.

PHASE 7
Investment-committee agent graph with mocked LLM outputs first.

PHASE 8
Actual LLM provider implementation with typed schemas and budget controls.

PHASE 9
Backtest/execution simulator.

PHASE 10
Portfolio/risk engine.

PHASE 11
Paper trading.

PHASE 12
Stocks/FX provider adapters.

PHASE 13
SEC/FRED/CFTC and event intelligence.

PHASE 14
Stat-arb/ML/walk-forward research.

PHASE 15
Production hardening.

After each phase:
- run all phase acceptance tests
- update tests.json
- update progress.md
- commit logically if git use is permitted
- inspect git diff
- perform adversarial self-review

## FIRST TASK

Do not start writing production feature code immediately.

Begin by producing:

1. repository audit;
2. dependency/repository verification report;
3. licensing matrix;
4. data-provider entitlement matrix;
5. architectural decision record;
6. phased task plan;
7. tests.json;
8. initial/updated CLAUDE.md;
9. explicit unresolved questions that can be answered from repository or official
   docs.

Then begin Phase 1 only if no blocking contradiction exists.

You are authorized to make reversible local changes and run tests.

Do not:
- push to remote without authorization
- modify production infrastructure
- delete user work
- bypass tests
- disable security checks
- use --no-verify to hide failures
- enable live trading
- place a real order

Continue systematically until the current phase satisfies its definition of done.

When uncertain:
investigate before guessing.

When a dependency/API changed:
adapt to current official documentation rather than old examples.

When implementation and documentation disagree:
test actual behavior and record the discrepancy.

The finished system must be ambitious, but credibility is more important than hyp
*[paste truncated here]*
