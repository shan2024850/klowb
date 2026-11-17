# Data providers: entitlement matrix and adapter contract

**Verified:** 2026-11-17 from official provider documentation unless marked
otherwise. Evidence and source URLs: `docs/research/verification-log.md`.

**Read this first**

- Provider terms and free-tier limits change. Each fact below has a verification
  status: **V** = read on an official page on the date above; **P** = partially
  verified (official page read, but the specific point was not stated there);
  **U** = not verified (treat as unknown).
- **Default for every provider: `redistribution_allowed = false`** and data is for
  the operator's own internal use. Nothing here is legal advice. Before showing any
  provider's data to third parties, the owner must read that provider's current
  terms.
- **When provenance or entitlement is unverified, use the weakest plausible
  `feed_quality`** and never `REALTIME_CONSOLIDATED`.

---

## 1. `feed_quality` semantics

| Value | Meaning | Examples |
|-------|---------|----------|
| `REALTIME_CONSOLIDATED` | Real-time data consolidated across all venues trading the instrument (a consolidated tape / NBBO), obtained under an entitlement that permits it. | US equities SIP (CTA/UTP) via a paid plan. |
| `REALTIME_EXCHANGE` | Real-time data direct from the single authoritative market for the instrument (the instrument trades on one venue only). | A futures contract from its listing exchange. |
| `REALTIME_SINGLE_VENUE` | Real-time data from **one** venue among several that trade the instrument. Not representative of the whole market; prices and especially volume are partial. | IEX-only US equity data; a single crypto exchange's BTC/USD book; one FX liquidity source. |
| `DELAYED` | Intentionally delayed data. `delay_seconds` must be set (e.g. 900). | 15-minute delayed SIP. |
| `EOD` | End-of-day data. | Free daily bars. |
| `UNOFFICIAL` | Data without a documented, licensed entitlement or with unknown provenance. Research only; never execution-critical. | yfinance; scraped sources; any provider whose source we cannot document. |
| `SIMULATED` | Synthetic or replayed data. | Mock provider, replay framework, backtests. |

Rules:

1. The adapter assigns `feed_quality` per observation from documented entitlement;
   nothing downstream may upgrade it. Aggregations inherit the **weakest** quality
   of their inputs.
2. Historical bars fetched from a real-time-entitled source keep that source's
   label; replays of recorded data are `SIMULATED` regardless of origin.
3. The UI shows the badge wherever a price is shown, and uses distinct text (not
   colour alone) for each value.
4. Execution (paper and, if ever enabled, live) declares the minimum feed quality
   it accepts per asset class; anything weaker fails closed (`docs/risk-model.md`).

---

## 2. Entitlement matrix

### 2.1 Crypto

| Provider | Access needed | What the free/public tier gives | `feed_quality` we assign | Limits | Redistribution / display | Role | Phase |
|---|---|---|---|---|---|---|---|
| **Kraken** (spot) | None for public market data | WebSocket v2 `wss://ws.kraken.com/v2`: `ticker`, `trade`, `ohlc`, `book`, `instrument`, automatic `status` and `heartbeat`. REST `GET /0/public/OHLC` (≤ 720 most-recent candles; last entry is the uncommitted current candle), AssetPairs, Trades, Ticker. **V** | `REALTIME_SINGLE_VENUE` | Connection/reconnection attempts ≈150 per rolling 10 min per IP (exceeding → 10-minute IP ban). Server closes connections after ≈1 min of inactivity. Reconnect instantly a handful of times after a random drop; after maintenance no faster than every 5 s. **V**. Numeric public REST rate limit: **P** (not stated on the rate-limit page read). | **U** — no market-data licence text found; default `false`. | **First real streaming provider** (ADR-0006) | 3 |
| **Coinbase Exchange** | None for the public feed | `wss://ws-feed.exchange.coinbase.com` (ticker, heartbeat, matches, level2 …). Per-product `sequence` increasing by exactly one per message; gaps mean dropped messages. Must send `subscribe` within 5 s of connecting. **V** | `REALTIME_SINGLE_VENUE` | Connection / subscribe rate limits: **P** (not stated on the page read). | **U**; default `false`. | Documented alternate / second venue | later |
| **Coinbase Advanced Trade** | None for public channels | `wss://advanced-trade-ws.coinbase.com`; public channels listed as level2, ticker, ticker_batch, candles, heartbeats, market_trades, status. **P** (documentation pages were ~500 days old) | `REALTIME_SINGLE_VENUE` | **U** | **U**; default `false`. | Not planned | — |
| **Binance** (global spot) | None for public market data | Market-data-only WS base `wss://data-stream.binance.vision`; ≤ 1024 streams per connection; 5 incoming messages/s; 300 connection attempts per 5 min per IP. **V**. 24-hour connection lifetime and ping interval for spot: **P** (not confirmed). | `REALTIME_SINGLE_VENUE` | as left | **U**; default `false`. | Optional; **`api.binance.com` returned HTTP 451 from the development network**, so it cannot be integration-tested there. Availability depends on the operator's jurisdiction. | later |
| **Binance.US** | None for public market data | REST reachable (HTTP 200 from the development network). Details **U**. | `REALTIME_SINGLE_VENUE` | **U** | **U** | Not planned | — |
| **CCXT** (abstraction, MIT) | per exchange | Unified REST (and WS) clients. | inherits the underlying venue | per exchange | per exchange | Deferred breadth layer (see dependency decisions) | later |

### 2.2 US equities / ETFs

| Provider | Access needed | What the free tier gives | `feed_quality` we assign | Limits | Redistribution / display | Role | Phase |
|---|---|---|---|---|---|---|---|
| **Alpaca** (Basic, free) | API key (free account; "Paper Only" accounts available globally) | Real-time equities from **IEX only**; WebSocket limit 30 symbols; historical API 200 calls/min; historical data restricted from the **latest 15 minutes** (i.e. SIP history is available only once 15 minutes old). Options: indicative feed. Historical crypto endpoints need no auth. Paper-only accounts "are only entitled to receive and make use of IEX market data". **V** | IEX stream → `REALTIME_SINGLE_VENUE`; SIP history older than 15 min → `DELAYED` (`delay_seconds=900`); paid SIP → `REALTIME_CONSOLIDATED` (only with the paid plan) | as left | **U**; default `false`. | Primary stocks data + **paper broker** | 11–12 |
| **Alpaca** (Algo Trader Plus, $99/mo) | paid | "All US Stock Exchanges" real-time, unlimited WS symbols, 10,000 calls/min, OPRA options. **V** | `REALTIME_CONSOLIDATED` | as left | **U** | Optional upgrade | — |
| **Twelve Data** (Basic, free) | API key | 8 API credits/min, 800/day; pricing file says "Real-time US equities, forex, crypto"; WebSocket is trial-only (8 trial credits, restricted symbols). Individual plans: "personal, internal, and non-commercial use"; Basic described as "internal non-display usage only". **V** (source of the "real-time" US data not stated → **P**) | `UNOFFICIAL` until the data source/consolidation is documented; then re-label | as left | Not for display; default `false`. **Note:** "non-display" conflicts with showing it in a dashboard — read the terms before using it in the UI. | Candidate FX/reference REST source | 12 |
| **Massive** (formerly Polygon.io; Stocks Basic, free) | API key | End-of-day data, 5 API calls/min, 2 years history, REST only; no trades/quotes/WebSocket. Paid: Starter $29 (15-min delayed), Developer $79, Advanced $199 (real-time). **V** | `EOD` (free); `DELAYED` (Starter) | as left | **U**; default `false`. | Candidate EOD/reference source | 12 |
| **Tiingo** (Starter, free) | API key | 500 unique symbols/month, 50 requests/hour, 1,000 requests/day, 1 GB/month (from Tiingo's own blog, not the pricing page). Real-time via IEX. Licence terms for Starter not found. **P** | IEX → `REALTIME_SINGLE_VENUE`; EOD → `EOD` | as left | **U**; default `false`. | Candidate EOD source | 12 |
| **Finnhub** (Free) | API key | 60 API calls/min (plus a 30 calls/s cap), US coverage, WebSocket 50 symbols, one connection per key; "personal use" licence. **V** (docs page was an old cached copy → **P** for details) | `UNOFFICIAL` until the US trade source is documented | as left | Personal use; default `false`. | Candidate news/fundamentals | 13 |
| **Alpha Vantage** (free) | API key | 25 API requests/day; several endpoints (incl. intraday) are premium. Real-time vs 15-min-delayed US entitlement: **U**. **V** for the daily cap. | `EOD` / `UNOFFICIAL` | as left | **U** | Low priority (25/day is too small) | — |
| **Interactive Brokers** | Funded PRO account; paid Level-1 subscriptions for most securities; ≥ USD 500 equity beyond subscription cost; 100 concurrent market-data lines initially; subscriptions are per username; demo accounts cannot subscribe. FX and crypto need no extra subscription. **V** (pages of mixed age → **P**) | depends on subscription | as left | per exchange agreements | Optional future broker/data adapter | later |
| **SEC EDGAR** | No key | `data.sec.gov` submissions / companyconcept / companyfacts / frames JSON APIs; nightly bulk ZIPs; no CORS (server-side only). Fair access: **≤ 10 requests/second** per user regardless of machines; SEC may block excessive requesters. **V**. Declared `User-Agent` requirement: **P** (not stated on the two pages read; the SEC developer FAQ must be checked in Phase 13). | n/a (filings, not prices) | 10 req/s | US government data | Fundamental/event intelligence | 13 |
| **yfinance** | none | Unofficial access to Yahoo Finance. Project README: "not affiliated, endorsed, or vetted by Yahoo, Inc."; "intended for research and educational purposes"; "the Yahoo! finance API is intended for personal use only". **V** | `UNOFFICIAL` | unknown, unstable | Personal use only | **Non-critical research fallback only**; never execution-critical | 12+ |
| **Stooq** | none | Terms page could not be retrieved (`stooq.com/terms.html` returned no content). Third parties report a low daily request quota. **U** | `UNOFFICIAL` / `EOD` | **U** | **U** | **Do not use until the current terms are read** (brief requirement) | — |

### 2.3 Forex

No free, documented, consolidated FX feed exists; FX is a decentralised market, so
every source is a single liquidity source or an indicative composite.

| Provider | Notes | `feed_quality` | Phase |
|---|---|---|---|
| Twelve Data (free) | Real-time FX within 8 credits/min, 800/day; "non-display" licence wording. **V/P** | `UNOFFICIAL` or `REALTIME_SINGLE_VENUE` once the source is documented | 12 |
| Kraken spot FX pairs (e.g. `EUR/USD`) | Exchange-traded spot FX on a crypto venue; thin relative to interbank. Symbol availability to be confirmed via the `instrument` channel. **U** | `REALTIME_SINGLE_VENUE` | 3/12 |
| ECB reference rates | Daily euro reference rates via the ECB Data Portal SDMX API (`data-api.ecb.europa.eu/service/data/EXR/...`). No credentials shown in the docs. Reuse policy: **P**. | `EOD` (reference rate, not tradable) | 13 |
| Interactive Brokers | FX needs no extra market-data subscription. **P** | `REALTIME_SINGLE_VENUE` | later |

### 2.4 Macro / regulatory

| Provider | Access | Facts | Phase |
|---|---|---|---|
| **FRED** | API key | Required notice: "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." Apps for other users must link the Terms of Use. Third-party **copyrighted series** (notes contain "Copyright") need the data owner's permission for anything other than personal use. No numeric rate limit stated; the Bank may impose limits. **V** | 13 |
| **ECB Data Portal** | none shown | SDMX 2.1 REST API; CSV via `format` parameter; https only. Reuse/licensing terms: **P**. | 13 |
| **CFTC Commitments of Traders** | none | Public Reporting Environment with an API (CSV/RDF/RSS/TSV/XML). Released Fridays 15:30 ET with data as of the prior Tuesday; holidays can delay. CFTC announced a move to **twice-weekly** publication by end of 2026 (Monday data on Wednesday, Wednesday data on Friday) — re-check the schedule when implementing. Dataset identifiers: **U**. **V** | 13 |
| **SEC EDGAR** | none | See 2.2. | 13 |

---

## 3. Adapter contract (applies to every provider)

Implemented in `libs/providers/`; verified by a **shared conformance test suite**
that every adapter must pass (`P2-UNIT-001`).

| Requirement | Specification |
|---|---|
| Typed schemas | Raw payloads are parsed into provider-specific Pydantic models (tolerant of unknown fields), then mapped to canonical `Observation`s. A payload that fails parsing becomes a quarantined event; it never raises out of the stream loop. |
| Timeouts | Every network call has explicit connect and read timeouts. No call without a timeout. |
| Rate limiting | Client-side token bucket per provider and per endpoint class, configured from the documented limits above with headroom. |
| Retry | Only for retryable classes (`timeout`, `unavailable`/5xx, `rate_limited`, connection errors). Exponential backoff with **full jitter**, capped delay, **bounded attempts**, honours `Retry-After`. Never retries `auth`, `invalid_request`, `not_found`, or `malformed_response`. |
| Circuit breaker | Closed → open after N consecutive failures → half-open probe after a cool-down. While open, calls fail fast and health is `DOWN`. |
| Reconnect | WebSocket reconnect with jittered backoff, bounded attempts per window (Kraken: far below 150 per 10 min), resubscribe, then gap repair by REST backfill. Reconnect count is a metric. |
| Heartbeat | Liveness watchdog on the last received message; if silent for longer than the provider's documented heartbeat interval × tolerance, force reconnect. Application-level ping where documented. |
| Sequence gaps | Where the provider exposes a sequence (Coinbase `sequence`, Kraken `trade_id`, order-book checksums), gaps are detected, logged, counted and trigger repair. |
| Stale data | Compare `event_timestamp` to `received_timestamp` and to the session calendar; stale beyond threshold → flagged; execution consumers fail closed. |
| Idempotency | Every observation has a deterministic identity (`provider`, `data_type`, `provider_symbol`, `sequence_number` or `event_timestamp` + `raw_payload_hash`); reprocessing the same event is a no-op. |
| Error classification | `ProviderError` with a closed `kind` enum (`timeout`, `unavailable`, `rate_limited`, `auth`, `invalid_request`, `not_found`, `malformed_response`, `protocol`) and `retryable` flag. |
| Health metrics | Per provider: state (`HEALTHY`/`DEGRADED`/`DOWN`/`UNKNOWN`), last message age, message rate, latency (event→receive), error rate by kind, reconnects, gaps, quarantined count, circuit state. Exposed on `/metrics`, `/api/v1/providers/health` and in the UI. |
| Provenance | Every observation sets `provider`, `venue`, `feed_quality`, `delay_seconds`, `entitlement`, `redistribution_allowed`, `raw_payload_hash` (SHA-256 of the canonical raw payload). |
| Time | `event_timestamp` from the provider (UTC); `received_timestamp` from the injected clock (UTC). Never naive. |
| Precision | Prices/sizes parsed as `Decimal` (JSON floats are parsed with `parse_float=Decimal`); never through binary float. |
| Secrets | Keys come from typed settings (`SecretStr`), are sent only to the provider's own hosts, and never appear in logs, errors, metrics labels or API responses. |
| Hosts | Provider base URLs are constants in code (not user input) — no SSRF surface. |

---

## 4. Kraken WebSocket v2 — implementation notes (Phase 3)

All **V** on 2026-11-17 from docs.kraken.com and from a live capture taken through
the development environment.

- Endpoint: `wss://ws.kraken.com/v2` (public). Beta endpoint exists
  (`wss://beta-ws.kraken.com/v2`); do not use it.
- Symbols: `BASE/QUOTE`, e.g. `BTC/USD` (**not** `XBT/USD` — that returns "Currency
  pair not supported"). REST still uses legacy names unless `assetVersion=1`.
- On connect the server sends a `status` message: `{"channel":"status","type":"update","data":[{"api_version":"v2","connection_id":…,"system":"online","version":"2.0.10", …}]}`. `system` ∈ `online`, `cancel_only`, `maintenance`, `post_only`. Optional `upcoming_maintenance` / `emergency` arrays may appear (observed live).
- Subscribe: `{"method":"subscribe","params":{"channel":"trade","symbol":["BTC/USD"],"snapshot":true},"req_id":1}` → one ack per symbol: `{"method":"subscribe","req_id":1,"result":{"channel":"trade","snapshot":true,"symbol":"BTC/USD"},"success":true,"time_in":"…","time_out":"…"}`; failures carry `"success":false` and `error`.
- `ticker`: params `event_trigger` = `bbo` | `trades` (default `trades`); data fields `symbol, bid, bid_qty, ask, ask_qty, last, volume, vwap, low, high, change, change_pct, timestamp`. **Discrepancy:** live messages also carry an undocumented integer `trades` field.
- `trade`: snapshot = most recent 50 trades; updates may batch several trades; each has `symbol, side, price, qty, ord_type, trade_id, timestamp` (RFC 3339, microseconds). `trade_id` is documented as "a sequence number unique per book" → used for gap detection; strict contiguity is **to be confirmed empirically** in Phase 3 (`OQ-T04`).
- `ohlc`: `interval` ∈ 1, 5, 15, 30, 60, 240, 1440, 10080, 21600 minutes; fields `symbol, open, high, low, close, vwap, trades, volume, interval_begin, interval` (`timestamp` inside data is deprecated). Updates stream on trade events, so the current candle is **not final** until its interval has ended.
- `book`: depth 10/25/100/500/1000; CRC32 checksum over top 10 levels; checksum algorithm is in a separate guide (not yet read — needed only if order-flow features are built).
- `heartbeat`: `{"channel":"heartbeat"}` roughly once per second **only when no other channel traffic is flowing**; cannot be subscribed explicitly.
- `ping`: `{"method":"ping","req_id":n}` → `{"method":"pong","req_id":n,"time_in":"…","time_out":"…"}` (verified live; any request keeps the connection alive).
- Numbers arrive as JSON numbers; Kraken's guide says full precision is preserved if they are decoded as decimal/string → use `json.loads(raw, parse_float=Decimal)`.
- REST OHLC: `GET https://api.kraken.com/0/public/OHLC?pair=…&interval=…&since=…`; arrays `[time, open, high, low, close, vwap, volume, count]` with prices as strings; `last` is the id to pass as `since`; at most 720 entries; the final entry is the in-progress candle.

Real captured payloads from 2026-11-17 are to be stored under
`data/fixtures/kraken/` in Phase 3 as contract fixtures.
