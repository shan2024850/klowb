# Execution model

**Status:** design agreed in Phase 0 (2026-11-17). Simulator in Phase 9, risk in
Phase 10, paper trading in Phase 11. **No live broker adapter exists and none is
planned without an explicit owner request** (ADR-0009).

Realism statement: a simulator approximates markets; it does not reproduce queue
position, hidden liquidity, or the market impact of our own orders. Results are
estimates. The UI and reports say so.

---

## 1. Trading modes

| Mode | Orders | Broker | Data requirement |
|------|--------|--------|------------------|
| `research` (default) | none — the order API rejects with `MODE_FORBIDS` | none | any (labelled) |
| `paper` | simulated only | internal `SimBroker` (Phase 11); optional Alpaca **paper** endpoint (`paper-api.alpaca.markets`) | per `docs/risk-model.md` §2 minimum feed quality |
| `live` | real money | **not implemented** | — |

Gates for `live` (all required; evaluated at startup and again per order):

1. `TRADING_MODE=live`
2. `LIVE_TRADING_ENABLED=true` (capability flag)
3. live broker credentials present (server-only)
4. `LIVE_TRADING_ACK` equals the exact acknowledgement phrase
5. `RiskConfig` validates and has been explicitly marked reviewed
6. a human arms the session in the UI (two-step confirmation, audited), and the
   arm expires at session end

If `TRADING_MODE=live` and any of 2–5 is missing the process refuses to start.
The system never changes mode on its own; in particular a paper broker failure
never routes to a live endpoint. Paper and live credentials are different
settings, paper and live base URLs are different constants, and the paper adapter
refuses to run against a non-paper base URL.

---

## 2. Order model

```
OrderIntent      what a strategy/committee wants (instrument, side, entry logic,
                 stop, targets, horizon, source decision id) — no quantity yet
   │  RiskEngine.evaluate()
   ▼
RiskDecision     approved quantity + reasons, or rejection
   │  ExecutionService.submit()
   ▼
Order            client_order_id, instrument_id, side, type, quantity, limit/stop
                 prices, time_in_force, mode, broker, parent/child links
   ▼
Fill*            fill_id, order_id, price, quantity, fee, liquidity flag, timestamp
```

- **Order types:** `MARKET`, `LIMIT`, `STOP` (stop-market), `STOP_LIMIT`. Brackets
  (entry + stop + target) are modelled as linked child orders with OCO semantics
  handled by the execution service, not assumed from the broker.
- **Time in force:** `DAY`, `GTC`, `IOC`, `FOK` (only those the venue supports;
  unsupported → reject before submission).
- **Quantities and prices** are `Decimal`, quantised to the instrument's increments
  before submission; quantisation that changes risk materially is rejected rather
  than silently applied.

### State machine

```
NEW ──submit──▶ SUBMITTED ──ack──▶ ACKNOWLEDGED ──fill──▶ PARTIALLY_FILLED ──fill──▶ FILLED
 │                 │                    │                       │
 │                 ├──reject──▶ REJECTED│                       ├──cancel──▶ CANCELLED (remaining)
 └──risk reject──▶ REJECTED             ├──cancel──▶ CANCELLED   └──expire──▶ EXPIRED
                                        └──expire──▶ EXPIRED
```

- Terminal states: `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`. No transition out
  of a terminal state; illegal transitions raise and are logged as defects.
- Every transition is persisted with timestamps (ours and the broker's), broker
  order id, and correlation id; the blotter is a projection of this log.
- **Idempotency:** `client_order_id` is deterministic
  (`hash(decision_id, leg, attempt)`); submitting it twice returns the existing
  order. Duplicate acknowledgements and duplicate fill reports (same broker fill
  id) are no-ops. Fills arriving out of order are applied by broker sequence/time.
- **Reconciliation:** on startup and periodically, open orders and positions are
  reconciled against the broker; any mismatch engages `BLOCK_NEW_RISK` and raises
  an alert.
- **Stale orders:** working orders older than their validity (TIF or a configured
  maximum age) are cancelled; in the simulator they expire.

---

## 3. Broker interface

`Broker` protocol (`services/execution`): `submit`, `cancel`, `get_order`,
`list_open_orders`, `get_positions`, `get_account`, plus an async event stream of
order updates. Implementations:

| Implementation | Phase | Notes |
|----------------|-------|-------|
| `SimBroker` | 9 | Deterministic fill engine on a `VirtualClock` (backtests) or the system clock (paper). |
| `AlpacaPaperBroker` | 11 (optional) | Paper endpoint only. Alpaca's docs state paper trading does not model market impact, information leakage, latency slippage, queue position, price improvement, regulatory fees or dividends, and fills eligible orders partially at random 10 % of the time. |
| live adapter | — | Not implemented. |

Broker errors use the same closed taxonomy as providers (`timeout`, `unavailable`,
`rate_limited`, `auth`, `invalid_request`, `not_found`, `rejected`, `protocol`).
Order submission is **not** retried blindly: a timeout on submit is resolved by
querying by `client_order_id`, never by re-sending.

---

## 4. Simulator fill model (`SimBroker`)

Inputs: quote stream (bid/ask) when available, otherwise bars with a modelled
spread; instrument metadata; calendar; cost model; latency model; seed.

| Aspect | Model |
|--------|-------|
| Latency | An order becomes eligible to trade at `submit_time + latency` (configurable constant or seeded distribution). No fill can occur at or before the timestamp of the data that triggered the decision. |
| Market order | Fills at the opposite side of the first quote **after** eligibility: buys at ask, sells at bid, plus slippage. With bars only: next bar's open ± half the modelled spread ± slippage. |
| Limit order | Fills when the market trades through the limit (buy: ask ≤ limit; with bars: low < limit, i.e. strictly through, to avoid assuming queue priority at the touch). Fill price = limit, or better if the market gaps through at the open. |
| Stop order | Triggers when the market trades at/through the stop; then behaves as a market order. **Gap-through:** if the first eligible price is beyond the stop, the fill is at that worse price, not at the stop. |
| Stop-limit | Triggers like a stop, then rests as a limit (may not fill). |
| Partial fills | Fill quantity per event ≤ `max_participation × event volume` (bars) or ≤ displayed size (quotes); the remainder keeps working. |
| Rejections | Outside session for the order type, halted/delisted instrument, below minimum notional, unsupported TIF, insufficient buying power, short without borrow. |
| Market hours | From `libs.calendars`: no fills while closed; `DAY` orders expire at the session close; early closes and holidays honoured. |
| Corporate actions | Splits/reverse splits adjust open positions and working orders; cash dividends credit/debit on the ex-date; delisting closes the position at the last price with a flag. Unadjusted prices are used for execution; adjusted series only for returns/features, never mixed (`is_adjusted`). |
| Slippage | Configurable: fixed bps, spread-proportional, or volatility/participation-scaled. Seeded when stochastic. |
| Costs | See §5. |
| Determinism | Same data snapshot + parameters + seed ⇒ identical fills and results (replay test). |

### Timing / lookahead rule

A strategy that decides using the close of bar *t* may be filled no earlier than
the first tradable event after *t* (+ latency). Filling at the close of the same
bar is allowed **only** if the strategy explicitly declares a close-auction timing
model, which the run metadata records. Automated lookahead tests enforce this by
(a) shifting/perturbing future data and asserting decisions up to *t* do not
change, and (b) asserting no fill timestamp ≤ its decision timestamp.

---

## 5. Cost model

All costs are explicit, itemised per fill, and reported both in currency and bps.

| Cost | Default model | Notes |
|------|---------------|-------|
| Commission / fees | per-venue schedule (maker/taker bps for crypto; per-share or zero-commission with regulatory fees for US equities) | Schedules are configuration with a source and date; they are not hard-coded as facts. |
| Spread | paid implicitly by crossing; with bar data, a modelled half-spread per side | From observed quotes when available. |
| Slippage | see §4 | |
| Funding | for perpetuals/margin when modelled | Reserved for derivatives. |
| Borrow | short-borrow fee accrual when modelled and data exists | Otherwise shorts are disabled, not assumed free. |
| FX conversion | when instrument currency ≠ account currency | |

`expected_cost_bps` in agent signals and the scanner's "net expected edge" use the
same cost model as the simulator, so research, backtest and paper numbers are
comparable.

---

## 6. Fail-closed data dependency

Before submission and while an order is working, the execution service asks the
market-data health registry whether the instrument's required feed is healthy,
fresh and of sufficient quality (`docs/risk-model.md` §2). If not:

- new risk-increasing orders are rejected (`DATA_INTEGRITY`);
- working entry orders are cancelled;
- protective stops already at the broker are left in place;
- the UI shows which instruments are blocked and why.

---

## 7. Backtest run record

Persisted for every run (Phase 9): run id, code version (git commit + dirty flag),
`data_snapshot_id`, strategy id and parameters, provider(s), date range,
train/test split definition, cost model + parameters, latency model, random seed,
calendar version, results (trades, equity curve, statistics), benchmark, and
warnings (e.g. multiple-hypothesis warning when a parameter search exceeded the
configured number of trials).

Evaluation methods: chronological split, walk-forward, out-of-sample test,
parameter-stability surface, benchmark comparison, bootstrap confidence intervals,
multiple-hypothesis warning.

---

## 8. Post-trade attribution

For each closed trade: expected edge (at decision) vs realised result; cost
expected vs realised (spread, slippage, fees); execution quality (arrival price,
implementation shortfall); contribution of each evidence class to the ensemble
edge; forecast error fed back into the reliability tracker (Phase 7/11).
