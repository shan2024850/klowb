# 0011 — Indicators, performance analytics and sizing in-house

- Status: Accepted
- Date: 2026-11-17

## Context

The brief requires features that are deterministic, versioned, unit-tested,
timestamp-safe and free of future leakage; transparent risk-based sizing with no
unbounded Kelly; and reproducible backtest statistics. Libraries considered
(verified 2026-11-17):

- `ta` — MIT; last PyPI release 0.11.0 on 2023-11-02.
- `quantstats` — Apache-2.0; 0.0.86 (2026-09-27); depends on yfinance,
  matplotlib, seaborn.
- `Riskfolio-Lib` — BSD-3-Clause; 7.4.1 (2026-11-04); depends on cvxpy, clarabel,
  scs, a C++ component, statsmodels, arch, astropy; recommends MOSEK for some
  models.

## Decision

- **Indicators and features are implemented in-house** on numpy/pandas inside a
  feature registry that records name, version, inputs and warm-up, with
  golden-value tests and an automated no-lookahead property test for every
  feature.
- **Performance statistics** (returns, volatility, Sharpe, Sortino, drawdown, hit
  rate, profit factor, exposure, turnover, bootstrap intervals) are implemented
  in-house with golden-value tests.
- **Position sizing** follows the brief's risk-budget formula
  (`docs/risk-model.md`); no optimiser is required for it.
- `ta` and `quantstats` are not adopted. **Riskfolio-Lib is deferred**: adopt in
  Phase 10 only if a concrete portfolio-optimisation feature is built.

## Alternatives considered

- **Use `ta`:** stale, unversioned semantics per indicator, unknown pandas 3
  behaviour; we would still need our own leak tests.
- **Use `quantstats` for reports:** brings plotting stacks and yfinance into the
  runtime; charts are rendered in the web app anyway.
- **TA-Lib:** C dependency; same versioning concern.

## Consequences

- More code to write, but each formula is explicit, versioned and tested, and a
  changed definition is a version bump rather than a silent upgrade.
- Third-party libraries may still be used **offline** as an independent
  cross-check when writing golden tests.

## Revisit when

A needed method is complex enough that a maintained, permissively licensed
implementation is clearly safer than our own (e.g. convex portfolio optimisation).
