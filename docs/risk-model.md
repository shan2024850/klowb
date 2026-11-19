# Risk model

**Status:** design agreed in Phase 0 (2026-11-17); implemented in Phase 10
(`services/risk/`). Numbers below are **conservative defaults**, all configurable
through a validated `RiskConfig`; they are engineering defaults, not investment
advice and not a promise of any outcome.

---

## 1. Principles

1. **Two kinds of risk.** *Hard* rules are binary and non-negotiable: they reject.
   *Soft* factors are continuous: they shrink size.
2. **Every order passes the risk engine.** The only way to obtain an `Order` is
   `OrderIntent → RiskEngine.evaluate() → RiskDecision(approved) → Order`. There is
   no bypass flag, in any mode, including backtests.
3. **Fail closed on uncertainty** for anything execution-critical (data integrity,
   account state, market state, broker connectivity).
4. **Soft risk must not silently turn the platform into one that never trades.**
   Soft multipliers are floored; only hard rules or an explicitly extreme
   disagreement threshold produce an abstention; every rejection and abstention has
   a machine-readable reason, is logged, counted and shown in the UI; the abstain
   rate is a monitored metric.
5. **No unbounded Kelly sizing.** Size comes from a fixed fractional risk budget and
   a stop distance, then only ever *reduced* by multipliers and caps.
6. **Deterministic and explainable.** Same inputs → same decision; the decision
   records every rule evaluated, its inputs and its result.

---

## 2. Hard rules (reject)

Evaluated in this order; the first failure rejects, but all failures are recorded.

| Code | Rule | Source of truth |
|------|------|-----------------|
| `KILL_SWITCH` | Global or per-instrument kill switch is engaged. | risk state (persisted) |
| `MODE_FORBIDS` | Trading mode is `research` (no orders at all), or the order targets a broker not valid for the mode. | settings |
| `DATA_INTEGRITY` | Execution-critical data for the instrument is malformed, quarantined, stale beyond threshold, has an open sequence gap, or is below the minimum feed quality for the asset class. | market-data quality + provider health |
| `MARKET_CLOSED` | The instrument's calendar says the session is closed for the order type (e.g. market order outside the regular session), or the instrument is halted / delisted. | calendars, instrument status |
| `ACCOUNT_INVALID` | Balance/equity missing, non-finite, non-positive, or older than the freshness threshold. | portfolio |
| `DUPLICATE_ORDER` | Same `client_order_id`, or an equivalent open order within the de-duplication window. | execution |
| `MAX_ACCOUNT_EXPOSURE` | Resulting gross or net exposure would exceed the configured maximum. | portfolio |
| `MAX_DAILY_DRAWDOWN` | Realised + unrealised P&L for the trading day ≤ −configured limit → no new risk-increasing orders (risk-reducing exits stay allowed). | portfolio |
| `SYMBOL_HARD_CAP` | Resulting position notional in the instrument would exceed the per-symbol cap. | portfolio |
| `IMPOSSIBLE_STOP_OR_SIZE` | Stop missing where required, on the wrong side of entry, at a non-positive price, closer than one price increment / minimum stop distance; quantity ≤ 0 after rounding, below minimum notional/lot, or not a multiple of the quantity increment. | instrument metadata |
| `BROKER_UNSAFE` | Broker disconnected or its state unknown while an order would change exposure. | execution |
| `SHORT_UNAVAILABLE` | Short sale requested where borrow is known to be unavailable or shorting is disabled for the asset class. | instrument / config |

Risk-reducing orders (closing or reducing an existing position) are exempt from
`MAX_DAILY_DRAWDOWN`, `MAX_ACCOUNT_EXPOSURE` and `SYMBOL_HARD_CAP`, but never from
`KILL_SWITCH` semantics chosen by the operator (kill switch has two levels: *block
new risk* and *block everything*), `DATA_INTEGRITY`, `ACCOUNT_INVALID` or
`BROKER_UNSAFE`.

### Minimum feed quality for execution (defaults)

| Asset class | Paper | Live (if ever enabled) |
|-------------|-------|------------------------|
| Crypto | `REALTIME_SINGLE_VENUE` from the **venue being traded** | same |
| US equities / ETFs | `REALTIME_SINGLE_VENUE` (IEX) with an explicit warning that fills are simulated against partial-market data | `REALTIME_CONSOLIDATED` |
| FX | `REALTIME_SINGLE_VENUE` | `REALTIME_SINGLE_VENUE` from the executing venue |
| any | `SIMULATED` is accepted **only** by the simulator broker in backtests and by paper trading when `APP_ENV != prod` and the mock provider is the configured source | never |

`DELAYED`, `EOD` and `UNOFFICIAL` data are never execution-eligible.

---

## 3. Soft factors (reduce size)

Each produces a multiplier in `[floor, 1.0]`. Multipliers can only reduce.

| Multiplier | Driven by | Shape (default) | Floor |
|-----------|-----------|-----------------|-------|
| `confidence_multiplier` | calibrated ensemble confidence | linear from 0.5 at the minimum actionable confidence to 1.0 at high confidence | 0.50 |
| `liquidity_multiplier` | spread vs typical spread; order size vs ADV / top-of-book depth | 1.0 when spread ≤ typical and participation ≤ target; decreasing beyond | 0.25 |
| `regime_multiplier` | volatility percentile / regime classification | 1.0 in normal regimes; reduced in extreme volatility | 0.50 |
| `disagreement_multiplier` | dispersion of independent evidence-class edges | 1.0 at low dispersion, decreasing with dispersion | 0.50 |
| `correlation_multiplier` | correlation of the candidate with existing positions (crowding) | 1.0 when uncorrelated; reduced as average correlation with same-direction holdings rises | 0.50 |
| `event_multiplier` | proximity to scheduled events (earnings, macro releases) when known | reduced inside the event window | 0.50 |

- Combined soft multiplier = product of the above, with a **global floor of 0.10**:
  if the product falls below it, the engine does not shrink further — it returns
  `SOFT_FLOOR_REACHED` as an informational flag and sizes at the floor. Soft
  factors therefore cannot produce a zero size on their own.
- **Abstention from disagreement** happens only when dispersion exceeds
  `extreme_disagreement_threshold` (a separate, explicit, high threshold) — brief:
  "Do NOT automatically convert any disagreement into NO TRADE".
- Rounding down to the instrument's quantity increment can legitimately produce
  zero (account too small for the minimum lot); that is reported as
  `IMPOSSIBLE_STOP_OR_SIZE`, not hidden.

---

## 4. Position sizing

```
risk_budget   = equity × risk_per_trade
stop_distance = |entry_price − stop_price|                (price units, > 0)
base_qty      = risk_budget / (stop_distance × contract_multiplier)

effective_qty = base_qty
              × confidence_multiplier
              × liquidity_multiplier
              × regime_multiplier
              × disagreement_multiplier
              × correlation_multiplier × event_multiplier   (bounded as in §3)

final_qty     = min(effective_qty, caps…) rounded DOWN to quantity_increment
```

Caps applied in order (each records how much it cut):

1. `max_order_notional`
2. `max_symbol_exposure` (existing position + this order)
3. `max_sector_theme_exposure`
4. `max_gross_exposure`, `max_net_exposure`
5. `remaining_portfolio_risk` — sum over open positions of (distance to stop ×
   quantity) plus this trade's risk must stay within `max_portfolio_risk`
6. `max_participation` — order quantity ≤ a fraction of recent average volume

`equity` for sizing is the lower of current equity and start-of-day equity
(sizing does not grow intraday on unrealised gains).

### Default `RiskConfig`

| Parameter | Default | Hard validation bounds |
|-----------|---------|------------------------|
| `risk_per_trade` | 0.25 % of equity | (0, 1 %] |
| `max_portfolio_risk` (sum of open risk) | 2 % of equity | (0, 10 %] |
| `max_daily_drawdown` | 2 % of start-of-day equity | (0, 10 %] |
| `max_gross_exposure` | 100 % of equity (no leverage) | (0, 200 %] |
| `max_net_exposure` | 100 % of equity | (0, 200 %] |
| `max_symbol_exposure` | 10 % of equity | (0, 25 %] |
| `max_sector_theme_exposure` | 30 % of equity | (0, 50 %] |
| `max_order_notional` | 10 % of equity | (0, 25 %] |
| `max_open_positions` | 10 | [1, 100] |
| `max_participation` | 1 % of 20-bar average volume | (0, 10 %] |
| `min_stop_distance` | max(1 price increment, 0.25 × ATR) | > 0 |
| `data_staleness_limit` | 5 s for quotes during an open session | > 0 |
| `account_staleness_limit` | 60 s | > 0 |
| `extreme_disagreement_threshold` | calibrated in Phase 7; default = top decile of observed dispersion | — |
| `allow_short` | `false` for every asset class until borrow/margin modelling exists | — |

A `RiskConfig` outside the validation bounds fails to load. Live mode additionally
requires the config to be explicitly reviewed (ADR-0009).

---

## 5. Portfolio risk measures (reporting)

Displayed on the Portfolio/Risk page; they inform, they do not size:

- cash, positions, realised/unrealised P&L, gross/net exposure, concentration
  (largest position share, Herfindahl index), current risk budget used/remaining,
  drawdown (intraday, peak-to-trough);
- correlation matrix of holdings (rolling returns);
- asset-class exposure; sector/theme exposure when classification data exists;
- **VaR / Expected Shortfall** by historical simulation over a rolling window, at
  95 % and 99 %, with the window length and data quality shown; reported as
  estimates with their limitations stated in the UI (historical VaR understates
  tail risk and regime change).

---

## 6. Kill switch

- Levels: `OFF`, `BLOCK_NEW_RISK` (only risk-reducing orders pass), `BLOCK_ALL`.
- Engaged manually (UI/API, audited) or automatically on: daily drawdown breach
  (`BLOCK_NEW_RISK`), repeated broker errors, loss of account state, or data
  integrity failure across all providers for held instruments.
- State is persisted; a restart never clears it. Disengaging requires an explicit,
  audited operator action.
- The kill switch never sends liquidating orders by itself; flattening is a
  separate explicit operator action.

---

## 7. Decision record

Every evaluation persists a `RiskDecision`: intent id, timestamp (clock), mode,
inputs snapshot (equity, exposures, feed health, instrument metadata), each hard
rule's result, each multiplier's value and driver, each cap's effect, final
quantity, outcome (`APPROVED`, `REDUCED`, `REJECTED`, `ABSTAINED`) and reason
codes. Metrics: decisions by outcome and reason; abstain rate; average size
reduction by factor.

---

## 8. Tests

Acceptance tests `P10-*` in `tests.json`: one per hard rule, one per soft
multiplier (monotonic, bounded, floored), sizing formula golden cases, each cap,
property tests (final quantity never exceeds any cap; multipliers never increase
size; risk-reducing orders always permitted under drawdown block), kill-switch
persistence, config validation bounds.
