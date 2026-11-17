# Verification log

What was checked, how, when, and what could **not** be verified. Append new
entries; do not rewrite old ones. If behaviour and documentation disagree, record
it in §4.

---

## 1. Session 2026-11-17 (Phase 0)

### 1.1 Method

| Source type | How | Reliability |
|-------------|-----|-------------|
| PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) | direct request from the container | primary; version, upload date, declared license, `requires_python`, `requires_dist` |
| npm registry (`https://registry.npmjs.org/<pkg>`) | direct request from the container | primary; `dist-tags`, publish time, license, engines, peer dependencies |
| GitHub repository pages | fetched and summarised by a web-fetch tool (the container itself gets HTTP 403 from `github.com` / `api.github.com`) | license and README statements reliable; **release and commit dates were not visible** in the fetched pages |
| Provider documentation pages | web-fetch tool on official domains | reliable for what the page states; summarised by a small model, so quotes were requested verbatim |
| Web search restricted to official domains | search tool with `allowed_domains` | pointers; several result pages were old (noted per item) |
| Live probes | `curl` and a Python `websockets` client from the container | direct observation |

### 1.2 Registry facts

All package versions, dates and licenses in
`docs/architecture/dependency-decisions.md` §2–§3 were read from the registries on
2026-11-17. Notable observations:

- `typescript` dist-tags: `latest` 7.0.2, `rc` 7.0.1-rc, `beta` 7.1.0-beta; newest
  6.x is 6.0.3. `typescript-eslint` 8.73.0 peer: `typescript >=4.8.4 <6.1.0`.
- `httpx` stable is 0.28.1 (2024-12-06), with only `1.0.dev*` pre-releases after
  it; `httpx2` 2.16.2 (2026-11-16) exists; `anthropic` 2.9.0 requires
  `httpx2>=2.0.0,<3`.
- `exchange_calendars` 4.13.3 requires `pandas>=1.5.0`, `numpy>=1.26.4`.
- `numpy` 2.5.5 requires Python ≥ 3.12; `scipy` 1.18.1 requires Python ≥ 3.12.
- `crewai` 1.15.41 requires Python `<3.14,>=3.10`.
- `psycopg` 3.3.9 license `LGPL-3.0-only`; `asyncpg` 0.32.0 `Apache-2.0`.
- `next` 16.4.6 engines `node >=20.9.0`; `vitest` 5.1.0 engines
  `^22.12.0 || ^24.0.0 || >=26.0.0`; `jsdom` 31.0.1 engines
  `^22.22.2 || ^24.15.0 || >=26.0.0`; `skills` 1.9.0 engines `>=22.20.0`
  (container Node is 22.23.4).
- `@playwright/test` latest is 1.65.1; the container has Playwright 1.63.0 with
  Chromium build 1243.

### 1.3 Repository pages read

`tradingview/lightweight-charts`, `apache/echarts`, `QuantConnect/Lean`,
`nautechsystems/nautilus_trader`, `ccxt/ccxt`, `freqtrade/freqtrade`,
`hummingbot/hummingbot`, `microsoft/qlib`, `AI4Finance-Foundation/FinRL`,
`AI4Finance-Foundation/FinRL-Trading`, `OpenBB-finance/OpenBB`,
`dcajasn/Riskfolio-Lib`, `ranaroussi/quantstats`, `bukosabino/ta`,
`langchain-ai/langgraph`, `pydantic/pydantic-ai`, `crewAIInc/crewAI`,
`microsoft/autogen`, `ranaroussi/yfinance`.

Key statements captured:

- lightweight-charts README: "This license requires specifying TradingView as the
  product creator." / "You shall add the 'attribution notice' from the NOTICE file
  and a link to" TradingView; `attributionLogo` option satisfies the link; "This
  repository ships two Agent Skills for AI coding assistants" with
  `npx skills add tradingview/lightweight-charts`.
- nautilus_trader README: "During the v2 transition, v1 receives only critical
  security backports on the `develop_v1` branch."; "breaking changes can occur
  between releases".
- autogen: "This project has been archived and is no longer actively maintained by
  Microsoft"; "New users should start with Microsoft Agent Framework."
- crewAI: "CrewAI uses anonymous telemetry to collect usage data…"; "Users can
  disable telemetry by setting the environment variable OTEL_SDK_DISABLED to true."
- FinRL: directs production users to FinRL-X / FinRL-Trading; original repo is for
  "education, benchmarking, and research prototyping".
- qlib: "The official dataset is disabled temporarily."
- OpenBB README: "Distributed under the Apache License, Version 2.0."; product
  named "Open Data Platform by OpenBB (ODP)".
- yfinance: "not affiliated, endorsed, or vetted by Yahoo, Inc."; "intended for
  research and educational purposes"; "the Yahoo! finance API is intended for
  personal use only."
- freqtrade: the fetched page did not name the license; PyPI metadata says GPLv3.

### 1.4 Provider documentation read

| Topic | URL | Result |
|-------|-----|--------|
| Kraken WS v2 trade | https://docs.kraken.com/api/docs/websocket-v2/trade | full spec captured |
| Kraken WS v2 ticker | https://docs.kraken.com/api/docs/websocket-v2/ticker | full spec captured |
| Kraken WS v2 ohlc | https://docs.kraken.com/api/docs/websocket-v2/ohlc | full spec captured |
| Kraken WS v2 book | https://docs.kraken.com/api/docs/websocket-v2/book | spec captured; checksum algorithm is in a separate guide (not read) |
| Kraken WS v2 heartbeat | https://docs.kraken.com/api/docs/websocket-v2/heartbeat | captured |
| Kraken WS v2 status | https://docs.kraken.com/api/docs/websocket-v2/status | captured |
| Kraken WS intro | https://docs.kraken.com/api/docs/guides/spot-ws-intro | endpoints, limits, symbols, precision captured |
| Kraken REST OHLC | https://docs.kraken.com/api/docs/rest-api/get-ohlc-data | captured |
| Kraken REST rate limits | https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits | per-key counter only; **no public-endpoint limit stated** |
| Coinbase Exchange WS overview | https://docs.cdp.coinbase.com/exchange/websocket-feed/overview | endpoints, sequence semantics, 5-second subscribe rule captured |
| Coinbase Advanced Trade WS | search results on docs.cdp.coinbase.com | partial; pages ~500 days old |
| Binance spot WS | search results on developers.binance.com | limits captured; 24h lifetime/ping not confirmed |
| Alpaca market data | https://docs.alpaca.markets/docs/about-market-data-api | plan table captured |
| Alpaca paper trading | https://docs.alpaca.markets/docs/paper-trading | captured |
| Twelve Data pricing | https://twelvedata.com/pricing.md | plan table and licence wording captured |
| Massive (ex-Polygon) | search results on massive.com / polygon.io | free tier captured |
| Tiingo | search results on tiingo.com (blog) | limits from blog only |
| Finnhub | search results on finnhub.io | free tier captured; docs page was an old cached copy |
| Alpha Vantage | search results on alphavantage.co | 25 requests/day captured; entitlement detail not found |
| Interactive Brokers | search results on interactivebrokers.com | market-data requirements captured; pages of mixed age |
| SEC EDGAR APIs | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | endpoints, no auth, no CORS, bulk files captured |
| SEC developer resources | https://www.sec.gov/about/developer-resources | 10 requests/second captured; User-Agent rule not stated there |
| FRED terms | https://fred.stlouisfed.org/docs/api/terms_of_use.html | notice, copyrighted series, key requirement captured |
| ECB Data Portal | search results on data.ecb.europa.eu | API shape captured; reuse terms not found |
| CFTC COT | search results on cftc.gov | schedule and planned semiweekly change captured |
| Stooq terms | https://stooq.com/terms.html | **page returned no content** |
| Redis licensing | search results on redis.io | captured |
| Valkey | https://valkey.io/ | BSD, Linux Foundation backed, latest 9.1.3 |
| httpx2 | https://pypi.org/project/httpx2/ | captured |

### 1.5 Live probes from the development environment

| Probe | Result |
|-------|--------|
| `GET https://api.kraken.com/0/public/Time` | 200 |
| `GET https://api.exchange.coinbase.com/time` | 200 |
| `GET https://api.binance.com/api/v3/time` | **451** |
| `GET https://api.binance.us/api/v3/time` | 200 |
| `GET https://api.github.com/repos/tradingview/lightweight-charts` | **403** (policy) |
| `GET https://github.com/<repo>/releases.atom` | **403** (policy) |
| `wss://ws.kraken.com/v2` subscribe ticker(bbo) + trade(snapshot) + ping | received `status` (version 2.0.10, system online, `upcoming_maintenance` array), two subscribe acks, `pong`, ticker snapshot + updates, trade snapshot (50 trades) + updates, `heartbeat` |
| `wss://ws-feed.exchange.coinbase.com` subscribe ticker + heartbeat for BTC-USD | received `subscriptions`, `ticker` (with `sequence`, string prices), `heartbeat` |
| `npx skills@1.9.0 add tradingview/lightweight-charts --yes` | installed 2 skills (commit `c29c51e1e5bc61981da5832c97797cb8283d120f`) |
| `dockerd` | daemon starts ("Daemon has completed initialization") |
| `service postgresql start`, `redis-server --daemonize yes` | both start; `select version()` → PostgreSQL 16.15; `redis-cli ping` → PONG |

Sample of real Kraken messages captured (abridged; full fixtures to be recorded in
Phase 3):

```json
{"channel":"status","type":"update","data":[{"version":"2.0.10","system":"online","api_version":"v2","connection_id":1866123248566390069,"upcoming_maintenance":[{"affected_services":["futures_rest","futures_ws"], "...": "..."}]}]}
{"method":"subscribe","req_id":1,"result":{"channel":"ticker","event_trigger":"bbo","snapshot":true,"symbol":"BTC/USD"},"success":true,"time_in":"2026-11-17T00:26:57.323923Z","time_out":"2026-11-17T00:26:57.323961Z"}
{"method":"pong","req_id":3,"time_in":"2026-11-17T00:26:57.324010Z","time_out":"2026-11-17T00:26:57.324014Z"}
{"channel":"ticker","type":"snapshot","data":[{"symbol":"BTC/USD","bid":64571.1,"bid_qty":0.62005257,"ask":64571.2,"ask_qty":1.08866018,"last":64571.2,"volume":4251.11556157,"vwap":64759.1,"low":63840.0,"high":65633.5,"change":-389.7,"change_pct":-0.60,"trades":198780,"timestamp":"2026-11-17T00:26:57.234736Z"}]}
{"channel":"trade","type":"update","data":[{"symbol":"BTC/USD","side":"buy","price":64571.2,"qty":0.00052871,"ord_type":"limit","trade_id":116440301,"timestamp":"2026-11-17T00:26:57.909842Z"}]}
{"channel":"heartbeat"}
```

Sample of a real Coinbase Exchange message:

```json
{"type":"ticker","sequence":139598160387,"product_id":"BTC-USD","price":"64581.33","open_24h":"64886.67","volume_24h":"13420.26207141","low_24h":"63833.47","high_24h":"65626.98","volume_30d":"239966.74332920","best_bid":"64581.33","best_bid_size":"0.35816881","best_ask":"64581.34","best_ask_size":"0.00015690","side":"sell","time":"2026-11-17T00:27:08.692831Z","trade_id":1132590403,"last_size":"0.00000002"}
```

---

## 2. Not verified (do not treat as fact)

- Last-commit dates and GitHub release tags for all 18 repositories (blocked by
  the environment; package release dates used instead).
- Whether CCXT's MIT package includes WebSocket support.
- Market-data display/redistribution terms for Kraken, Coinbase, Binance.
- Kraken public REST numeric rate limit; `trade_id` contiguity; book checksum
  algorithm.
- Coinbase connection/subscribe limits; current `level2` access rules.
- Twelve Data's data source for "real-time US equities"; Tiingo Starter licence;
  Alpha Vantage entitlements; Finnhub's US trade source.
- Stooq terms; ECB reuse terms; CFTC dataset ids; SEC User-Agent format.
- Alpaca `feed` parameter values and WebSocket details.
- Extended-hours session times on early-close days.
- Compatibility items C-01…C-07 (`dependency-decisions.md` §5).

---

## 3. Facts from the session's built-in reference material (not independently re-verified)

- Anthropic API: current model ids and behaviours (default `claude-opus-5-5`;
  thinking cannot be disabled on it; forced `tool_choice` rejected; structured
  outputs through `output_config.format` / `client.messages.parse()`;
  `budget_tokens` removed; prices per million tokens: Opus 5.5 $4 in / $20 out,
  Sonnet 5.5 $2 / $10, Haiku 5.5 $0.10 / $0.50, reference cached 2026-11-03).
  **Re-read the official documentation at the start of Phase 8.**

---

## 4. Documentation vs behaviour discrepancies

| Date | Where | Documentation | Observed | Handling |
|------|-------|---------------|----------|----------|
| 2026-11-17 | Kraken WS v2 `ticker` | Field list has no `trades` | Live messages include integer `trades` | Provider models ignore unknown fields; fixture keeps the field. |
| 2026-11-17 | Kraken WS v2 `status` | Core shape: `api_version`, `connection_id`, `system`, `version` (optional maintenance arrays "only on deployments with the maintenance-status integration enabled") | Production sends `upcoming_maintenance` | Parse optional arrays; expose upcoming maintenance in provider health. |
| 2026-11-17 | Twelve Data pricing | Web pricing page vs machine-readable `pricing.md` list different Grow prices ($79 vs from $29 with three tiers) | — | Use the plan table in `pricing.md`; re-check before relying on it. |
| 2026-11-17 | valkey.io | "Latest release 9.1.3, October 26, 2026" while 9.0.7 is dated October 27, 2026 | — | Dates on the page are inconsistent; pick the image tag at Phase 1 from the registry. |

### 2026-11-17 — Codex baseline
The local-service instructions describe the previous environment. Here the host
has neither server nor sudo. The same DB bootstrap succeeded inside postgres:16;
redis:7 answered PONG. Docker image pulls succeeded for both. uv selected
/usr/bin/python3 (3.13.5) with a writable UV_CACHE_DIR. See progress.md.

Browser preflight: the installed playwright package reports 1.62.1. Its default
headless launch failed because chromium_headless_shell-1234 is missing from the
Playwright cache. /opt/pw-browsers is absent. The separately packaged system
Chromium reports 156.0.8078.79. The handoff requires a preinstalled 1.63.0
pair and prohibits downloading another browser or installing another version.

**Resolution (2026-11-17, reviewed in the original environment):** the handoff
rule was an environment fact mis-stated as a project rule. Superseded by
ADR-0012: project-pinned `@playwright/test` 1.63.0 + `playwright install
chromium` via the project-local CLI.

FastAPI 0.163.1: the P1-INT-005 regression first failed with /system/info as
the access-log route. The matched effective route context in the ASGI scope
contains the full path template. With that context the regression passed.
