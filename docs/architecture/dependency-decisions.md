# Dependency decisions, repository verification report and licensing matrix

**Verified:** 2026-11-17. **Method and limits:** see `docs/research/verification-log.md`.

- Versions, release dates and declared licenses come from the **PyPI and npm
  registry APIs** (primary, machine-readable).
- License names for GitHub repositories come from each repository's **GitHub page**
  (sidebar / README).
- **Limitation:** this environment blocks `api.github.com` and direct `github.com`
  requests from the container, and the rendered pages do not expose release or
  commit dates. "Latest activity" below is therefore the **latest published
  package release date**, which is a lower bound on repository activity, not the
  last commit date. Where a project has no recent package release this is called
  out explicitly.

Policy: **choose the smallest coherent set.** A dependency is added only when a
phase needs it, and only after its row here is filled in. The lockfiles
(`uv.lock`, `pnpm-lock.yaml`) are the truth for what is actually installed; this
document records *why*.

---

## 1. License policy

| Class | Examples | Policy |
|-------|----------|--------|
| Permissive | MIT, BSD-2/3, Apache-2.0, ISC, PostgreSQL License | Allowed. Keep notices. Apache-2.0 NOTICE files must be honoured. |
| Weak copyleft, file-level | MPL-2.0 | Allowed as an **unmodified** library. If we ever modify an MPL file we must publish that file. Currently dev-only (`hypothesis`, `@axe-core/playwright`). |
| Weak copyleft, library-level | LGPL-3.0 | Design concern. Allowed only as an unmodified, dynamically imported library, with a recorded reason and no vendoring. **None adopted.** `psycopg` (LGPL) was avoided in favour of `asyncpg` (Apache-2.0). |
| Strong copyleft | GPL-3.0, AGPL-3.0 | **Not imported, linked or vendored.** May be used only as a separate, unmodified process/tool if ever needed, with an ADR. **None adopted.** |
| Source-available / restricted | Commons Clause, BSL, SSPL, RSAL, Timescale License (TSL) | Design concern; requires an ADR. **None adopted.** |
| Data/API terms | provider terms of use | Tracked separately in `docs/data-providers.md`; `redistribution_allowed` defaults to `false`. |

The repository itself has **no license file yet** — the owner must choose
(`docs/open-questions.md` B-02). Apache-2.0 is compatible with everything adopted
below.

### Attribution obligations we must keep

| Component | Obligation | How it is met |
|-----------|-----------|---------------|
| TradingView Lightweight Charts (Apache-2.0) | README: "This license requires specifying TradingView as the product creator. You shall add the 'attribution notice' from the NOTICE file and a link to" the TradingView site; the `attributionLogo` chart option satisfies the link requirement. | Keep `layout.attributionLogo` enabled (default); add the NOTICE text to the app's third-party notices page; test `P4-WEB-001` asserts the option is not disabled. |
| FRED API | "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." must be shown; apps for other users must link the FRED Terms of Use. | Shown wherever FRED data appears (Phase 13). |

---

## 2. Repositories the brief asked us to investigate

Status values: **ADOPT** (will be installed in the phase named), **DEFER**
(re-evaluate at the phase named), **REFERENCE** (read for ideas, not installed),
**REJECT**.

### 2.1 Frontend / charting

| Repository | License | Current release (date) | Maintenance state | Purpose here | Technical risks | Licensing implications | Decision |
|---|---|---|---|---|---|---|---|
| https://github.com/tradingview/lightweight-charts | Apache-2.0 (+ attribution requirement, see §1) | npm `lightweight-charts` **5.3.0** (2026-11-10) | Active (release 7 days before verification) | All financial price charts: candles, volume, VWAP/overlays, markers, panes | v5 API differs from v4 examples common in training data; client-only (no SSR); time values are UTC seconds; canvas chart needs a separate text alternative for accessibility | Must keep attribution logo/notice | **ADOPT — Phase 4.** Official agent skills installed (`.agents/skills/`, pinned in `skills-lock.json` to commit `c29c51e1e5bc61981da5832c97797cb8283d120f`). |
| https://github.com/apache/echarts | Apache-2.0 | npm `echarts` **6.1.0** (2026-05-19) | Active (Apache project; last release 6 months before verification) | Analytical visualisation: distributions, heatmaps (correlation), drawdown, parameter sensitivity, breadth | Large bundle → import modularly (`echarts/core`) and load lazily; canvas → needs text alternatives; v6 API vs older examples | None beyond notice retention | **ADOPT — first analytical chart (Phase 4 breadth/volatility or Phase 9 lab).** No React wrapper dependency: a thin in-house wrapper is ~40 lines (`echarts-for-react` 3.0.6 is MIT but unnecessary). |

### 2.2 Trading / research

| Repository | License | Current release (date) | Maintenance state | Purpose considered | Technical risks | Licensing implications | Decision |
|---|---|---|---|---|---|---|---|
| https://github.com/QuantConnect/Lean | Apache-2.0 | PyPI `lean` CLI 1.0.233 (2026-10-27) | Active | Backtest/live engine | C#/.NET engine with Python bridge → second runtime, own data formats, own order/risk model that would diverge from ours | None | **REFERENCE.** Not adopted (ADR-0008). |
| https://github.com/nautechsystems/nautilus_trader | LGPL-3.0 (PyPI: LGPL-3.0-or-later) | PyPI `nautilus_trader` 1.231.0 (2026-08-02); README mentions `2.0.0rcN` wheels | Active, **mid v1→v2 transition**: "During the v2 transition, v1 receives only critical security backports"; "breaking changes can occur between releases" | High-fidelity event-driven backtest + live engine | API churn during v2 transition; Rust core + PyO3 build complexity; adopting it means adopting its domain model wholesale | LGPL: usable unmodified as a pip dependency, but a design concern per brief | **REFERENCE / named alternative** for ADR-0008. Re-evaluate at Phase 9 start and if in-house simulator fidelity proves insufficient. |
| https://github.com/ccxt/ccxt | MIT | PyPI + npm `ccxt` 4.5.92 (2026-11-04) | Very active | Unified REST/WS access to many crypto exchanges | Large surface; unified layer hides venue-specific sequence/heartbeat semantics we need for data quality; frequent releases | None | **DEFER.** First streaming adapter is native (ADR-0006). Candidate as a breadth layer for exchange metadata / REST backfill when a 2nd–3rd exchange is added. Whether WebSocket ("CCXT Pro") support is included in the MIT package was **not confirmed** from the page read — verify before relying on it. |
| https://github.com/freqtrade/freqtrade | GPL-3.0 (PyPI: GPLv3) | PyPI `freqtrade` 2026.10 (2026-10-30) | Active | Crypto bot framework | It is an application, not a library | **GPL-3.0: importing it would impose GPL on our code** | **REJECT** as a dependency. Ideas only. |
| https://github.com/hummingbot/hummingbot | Apache-2.0 | PyPI `hummingbot` 20260922 (2026-10-07) | Active | Market-making / connector framework | Application framework with its own runtime; market-making focus does not match | None | **REFERENCE.** Not adopted. |
| https://github.com/microsoft/qlib | MIT | PyPI `pyqlib` 0.9.7 (**2025-08-15** — no package release for ~15 months) | Repository public, not archived; README notes "The official dataset is disabled temporarily" and an unreleased breaking change to artifact loading | ML research workflow | Stale package release; own data format; heavy | None | **REFERENCE** for Phase 14 research design. Not adopted. |
| https://github.com/AI4Finance-Foundation/FinRL | MIT ("FinRL" name/logo are trademarks of FinRL LLC) | PyPI `finrl` 0.3.7 (**2024-04-12**) | README: "the original FinRL library for education, benchmarking, and research prototyping"; directs production users to FinRL-X | Reinforcement-learning research | Research-grade; stale package | None | **REFERENCE, research-only** (brief: "FinRL/RL is research-only until independently proven"). Not installed. |
| https://github.com/AI4Finance-Foundation/FinRL-Trading | Apache-2.0 | No release shown | Presents itself as "FinRL-X", a modular AI-native quant platform; data from FMP / Yahoo Finance / WRDS; execution through Alpaca | Reference for RL trading pipeline | Depends on data sources we do not treat as execution-grade | None | **REFERENCE.** Not adopted. |
| https://github.com/OpenBB-finance/OpenBB | README: "Distributed under the Apache License, Version 2.0." PyPI `openbb` 5.0.0 declares Apache-2.0. (GitHub sidebar did not name a license.) | PyPI `openbb` 5.0.0 (2026-09-29) | Active; product now called "Open Data Platform by OpenBB (ODP)" | Aggregated data access | Very large dependency tree; adds a second provider-abstraction layer and hides entitlements/feed quality we must track ourselves | Older OpenBB releases were commonly reported as AGPL-3.0 — **if an older version is ever pinned, re-check its license** | **REFERENCE.** Not adopted. |
| https://github.com/dcajasn/Riskfolio-Lib | BSD-3-Clause | PyPI `riskfolio-lib` 7.4.1 (2026-11-04) | Active | Portfolio optimisation, risk measures | Heavy: cvxpy ≥ 1.7.2, clarabel, scs, C++ component (pybind11/Eigen), statsmodels, arch, astropy; README recommends commercial MOSEK for some models | None | **DEFER to Phase 10.** Position sizing in the brief is risk-budget based and does not need an optimiser. Adopt only if a concrete optimisation feature is built. |
| https://github.com/ranaroussi/quantstats | Apache-2.0 | PyPI `quantstats` 0.0.86 (2026-09-27) | Active | Performance tear sheets | Pulls yfinance, matplotlib, seaborn; metrics must be deterministic and tested in-house anyway | None | **NOT ADOPTED** (ADR-0011). May be used ad hoc as an external cross-check, never as a runtime dependency. |
| https://github.com/bukosabino/ta | MIT | PyPI `ta` 0.11.0 (**2023-11-02** — no release in 3 years) | Not archived, but no package release since 2023 | Technical indicators | Stale; pandas 3 compatibility unknown; indicator definitions must be versioned and leak-tested by us | None | **NOT ADOPTED** (ADR-0011). Indicators are implemented in-house with golden-value tests. |

### 2.3 Agent orchestration

| Repository | License | Current release (date) | Maintenance state | Purpose considered | Technical risks | Licensing implications | Decision |
|---|---|---|---|---|---|---|---|
| https://github.com/langchain-ai/langgraph | MIT | PyPI `langgraph` 1.2.22 (2026-11-14) | Very active | Graph orchestration with checkpointing / interrupts | Extra abstraction + dependency tree for a graph that is small, static and code-routed; release cadence is fast | None | **NOT ADOPTED** (ADR-0007). Revisit if durable checkpoint/resume or human-in-the-loop interrupts become requirements. |
| https://github.com/pydantic/pydantic-ai | MIT | PyPI `pydantic-ai` 2.68.0 (2026-11-12) | Very active (near-daily releases) | Typed agents, structured output, test models, usage limits, `pydantic-graph` | Very fast release cadence; would sit between us and the provider SDK whose exact request shape we need to control and log | None | **NOT ADOPTED** (ADR-0007). Closest fit philosophically; first choice if multi-provider LLM support is ever required. |
| https://github.com/crewAIInc/crewAI | MIT | PyPI `crewai` 1.15.41 (2026-11-12) | Very active | Role-based multi-agent crews | Prompt-driven free-form collaboration conflicts with the typed-contract requirement; **anonymous telemetry is collected unless `OTEL_SDK_DISABLED=true`** | None | **REJECT.** |
| https://github.com/microsoft/autogen | Code MIT, docs CC-BY-4.0 | PyPI `autogen-agentchat` 0.7.5 (2025-09-30) | **Archived**: "This project has been archived and is no longer actively maintained by Microsoft"; successor named as Microsoft Agent Framework | Multi-agent conversation | Unmaintained: no security fixes | None | **REJECT.** |

---

## 3. Stack selected for implementation

Versions are the registry `latest` on 2026-11-17 and are the **intended** pins.
Phase 1 installs them and this table is then reconciled with the lockfiles
(anything that had to change gets a note in §5).

**Installed so far (Phase 1, 2026-11-17, `uv.lock`):** fastapi 0.163.1,
uvicorn 0.54.0, pydantic 2.14.3, pydantic-settings 2.16.3, sqlalchemy 2.1.9
(`[asyncio]`, pulls greenlet), asyncpg 0.32.0, alembic 1.20.1, redis 8.1.0,
structlog 26.1.0, prometheus-client 0.26.0, httpx2 2.16.2; dev: pytest 9.2.0,
pytest-asyncio 1.5.0, pytest-cov 7.1.0, hypothesis 6.170.15, ruff 0.17.5,
mypy 2.4.1, import-linter 2.16, pip-audit 2.10.1 — all exactly the intended pins.
Transitive: fastapi 0.163 depends on `opentelemetry-api` (Apache-2.0).

**Installed in Phase 2 (2026-11-19):** exchange-calendars 4.13.3 (Apache-2.0) and
pandas 3.1.1 (BSD-3-Clause), plus their transitive packages, licences read from
PyPI for the exact locked versions: numpy 2.5.5 (BSD-3-Clause AND 0BSD AND MIT
AND Zlib AND CC0-1.0), python-dateutil 4.0.0 (BSD-3-Clause), tzdata 2026.6
(Apache-2.0), toolz 1.2.0 (BSD-3-Clause), korean-lunar-calendar 0.4.0 (MIT),
pyluach 2.3.0 (MIT). All permissive. Holiday/time-zone rule changes and numpy
wheel compatibility mean the calendar tests must be re-run on upgrades.
The remaining rows are installed in the phase listed.

### 3.1 Backend runtime (Python ≥ 3.13)

| Package | Version | License | Purpose | Phase |
|---|---|---|---|---|
| fastapi | 0.163.1 | MIT | HTTP/WebSocket API | 1 |
| uvicorn | 0.54.0 | BSD-3-Clause | ASGI server | 1 |
| pydantic | 2.14.3 | MIT | Canonical schemas, validation | 1 |
| pydantic-settings | 2.16.3 | MIT | Typed configuration from environment | 1 |
| sqlalchemy | 2.1.9 | MIT | ORM / SQL toolkit (async) | 1 |
| asyncpg | 0.32.0 | Apache-2.0 | PostgreSQL driver | 1 |
| alembic | 1.20.1 | MIT | Migrations | 1 |
| redis (redis-py) | 8.1.0 | MIT | Cache / pub-sub client | 1 |
| structlog | 26.1.0 | MIT OR Apache-2.0 | Structured JSON logging | 1 |
| prometheus-client | 0.26.0 | Apache-2.0 AND BSD-2-Clause | Metrics | 1 |
| httpx2 | 2.16.2 | BSD-3-Clause | Outbound HTTP client (see note) | 2–3 |
| websockets | 17.4 | BSD-3-Clause | Outbound WebSocket client | 3 |
| numpy | 2.5.5 | BSD-3-Clause (+ bundled permissive) | Numerics | 5 |
| pandas | 3.1.1 | BSD-3-Clause | Time-series frames for features | 2–5 |
| exchange_calendars | 4.13.3 | Apache-2.0 | Exchange sessions, holidays, early closes | 2 |
| duckdb | 2.0.0 | MIT | Research / backtest queries | 9 |
| pyarrow | 26.0.1 | Apache-2.0 | Parquet | 9 |
| anthropic | 2.9.0 | Apache-2.0 | LLM provider SDK | 8 |
| argon2-cffi | 25.1.0 | MIT | Password hashing | 11 |
| scikit-learn | 1.9.1 | BSD-3-Clause | Interpretable ML baselines | 14 |
| statsmodels | 0.15.0 | BSD-3-Clause | Cointegration / stat tests | 14 |

Note on **httpx2**: the last stable `httpx` release is 0.28.1 (2024-12-06). PyPI
describes `httpx2` as "a continuation" of HTTPX under the Pydantic organisation
(author Tom Christie, maintainer Pydantic Services Inc., repo
`github.com/pydantic/httpx2`, BSD-3-Clause, import name `httpx2`), stating HTTPX
itself has seen limited activity. The Anthropic SDK 2.9.0 depends on
`httpx2>=2.0.0,<3`. We standardise on `httpx2`; its API must be read from the
installed package before use (do not assume it is identical to `httpx`).

### 3.2 Backend development

| Package | Version | License | Purpose |
|---|---|---|---|
| pytest | 9.2.0 | MIT | Test runner |
| pytest-asyncio | 1.5.0 | Apache-2.0 | Async tests |
| pytest-cov | 7.1.0 | MIT | Coverage |
| hypothesis | 6.170.15 | MPL-2.0 (dev only, unmodified) | Property-based tests |
| ruff | 0.17.5 | MIT | Lint + format |
| mypy | 2.4.1 | MIT | Static typing (strict) |
| import-linter | 2.16 | BSD-2-Clause | Enforce module boundaries |
| pip-audit | 2.10.1 | Apache-2.0 | Dependency vulnerability scan |

### 3.3 Frontend

| Package | Version | License | Purpose | Phase |
|---|---|---|---|---|
| next | 16.4.6 | MIT | Web framework (App Router) | 1 |
| react, react-dom | 19.3.1 | MIT | UI | 1 |
| typescript | **6.0.3** (not 7.0.2) | Apache-2.0 | Type checking | 1 |
| tailwindcss, @tailwindcss/postcss | 4.3.5 | MIT | Styling | 1 |
| radix-ui | 1.8.1 | MIT | Accessible primitives | 1+ (as needed) |
| @tanstack/react-query | 5.107.1 | MIT | Server-state cache | 1 |
| zod | 4.6.7 | MIT | Runtime validation of API payloads | 1 |
| clsx | 2.1.1 | MIT | Class composition | 1 |
| lightweight-charts | 5.3.0 | Apache-2.0 (+attribution) | Price charts | 4 |
| echarts | 6.1.0 | Apache-2.0 | Analytical charts | 4+ |
| eslint | 10.15.0 (fallback 9.x, see §5) | MIT | Lint | 1 |
| eslint-config-next | 16.4.6 | MIT | Next lint rules | 1 |
| typescript-eslint | 8.73.0 | MIT | TS lint (peer `typescript >=4.8.4 <6.1.0`) | 1 |
| eslint-plugin-jsx-a11y | 6.10.2 | MIT | Accessibility lint | 1 |
| vitest | 5.1.0 | MIT | Unit/component tests | 1 |
| @vitejs/plugin-react | 6.3.0 | MIT | JSX transform for vitest | 1 |
| @testing-library/react | 16.3.3 | MIT | Component tests | 1 |
| jsdom | 31.0.1 | MIT | DOM for tests | 1 |
| @playwright/test | **1.63.0** (exact project pin; browser per ADR-0012) | Apache-2.0 | E2E | 1 |
| @axe-core/playwright | 4.14.0 | MPL-2.0 (dev only) | Automated a11y checks | 1 |
| OpenAPI → TypeScript generator | to be chosen in Phase 1 (`@hey-api/openapi-ts` 0.99.0 MIT supports TS ≥6; `openapi-typescript` 7.13.0 MIT declares peer TS ^5) | MIT | Generated API types | 1 |

### 3.4 Infrastructure

| Component | Version | License | Notes |
|---|---|---|---|
| PostgreSQL | 16.x | PostgreSQL License | Local install is 16.15. |
| Redis-protocol server | local dev: **Redis 7.0.15** (BSD-3-Clause). Compose image: **Valkey** (BSD-3-Clause, Linux Foundation backed; latest 9.1.3 per valkey.io) | BSD-3-Clause | Redis ≤ 7.2.x is BSD-3; Redis 7.4 is RSALv2/SSPLv1; Redis 8+ is tri-licensed RSALv2 / SSPLv1 / AGPLv3 (redis.io). Using a server over the network does not bind our code, but to keep the stack permissive the Compose file uses Valkey. Compatibility is proven by running the integration tests against it (Phase 1 smoke). |
| TimescaleDB | — | Apache-2.0 core + Timescale License for community features | **Not adopted** (ADR-0004). |
| Docker Engine / Compose | 29.9.2 / v5.6.1 | Apache-2.0 | Local orchestration only. |

---

## 4. Explicitly not adopted (and what replaces them)

| Not adopted | Replaced by |
|---|---|
| psycopg 3 (LGPL-3.0-only) | asyncpg (Apache-2.0) |
| orjson (MPL-2.0 AND (Apache-2.0 OR MIT)) | stdlib `json` with `parse_float=Decimal` (needed for price precision anyway) |
| polars | pandas + numpy (one dataframe library) |
| Celery / RQ / Kafka | supervised asyncio tasks (ADR-0010) |
| respx | the HTTP client's own mock transport (verify availability in `httpx2` at install) |
| `ta`, `quantstats`, `Riskfolio-Lib` | in-house, tested implementations (ADR-0011) |
| LangGraph, pydantic-ai, crewAI, AutoGen | in-house typed graph + provider SDK (ADR-0007) |
| Lean, nautilus_trader, freqtrade, hummingbot | in-house simulator (ADR-0008) |
| yfinance (Apache-2.0 code; Yahoo data is "intended for personal use only") | permitted **only** as a non-critical research fallback, labelled `UNOFFICIAL`, never for execution (Phase 12 at the earliest) |

---

## 5. Known compatibility questions to settle at install time

Record the outcome here when settled.

| # | Question | Fallback |
|---|----------|----------|
| C-01 | `eslint-plugin-jsx-a11y` 6.10.2 declares peer `eslint ^3…^9`; does it work with ESLint 10 flat config? | Pin ESLint 9.x. |
| C-02 | Does `eslint-config-next` 16.4.6 work with ESLint 10 + TypeScript 6.0.3? | Pin ESLint 9.x. |
| C-03 | Which OpenAPI→TS generator works cleanly with TypeScript 6.0.3? | Hand-written zod schemas validated against the OpenAPI snapshot. |
| C-04 | Does `exchange_calendars` 4.13.3 (requires `pandas>=1.5.0`) work with pandas 3.1.1? | **Settled 2026-11-19: works, with one caveat.** Sessions, holidays, early closes and DST shifts match NYSE's official 2026/2027 calendar (tests in `tests/unit/calendars/`). The library triggers pandas `Pandas4Warning` deprecations (`Series.values` / `DatetimeIndex.values` dropping timezone) while building a calendar and on per-minute lookups; today's results are correct UTC values. Mitigation: `libs/calendars/equity.py` extracts the schedule once, silencing only those two messages there, and never calls the library's per-minute API. **Do not upgrade to pandas 4 until exchange_calendars supports it** — re-run `tests/unit/calendars` on any upgrade of either package. |
| C-05 | Is the `httpx2` API (AsyncClient, timeouts, mock transport) as expected? | **Settled 2026-11-17:** installed 2.16.2; exposes `MockTransport`, `ASGITransport`, `AsyncHTTPTransport`. Starlette 1.10's `TestClient` imports `httpx2` (plain `httpx` is deprecated there), so it is a runtime dependency in Phase 1. |
| C-06 | Can Docker pull images through the agent proxy in this environment? | Record the Docker gates as `blocked` with evidence; validate `docker compose config` only. |
| C-07 | Does Valkey pass the Redis integration tests with redis-py 8.1.0? | Use a BSD-licensed Redis 7.2 image. |

Phase 1 web tooling: @types/react and @types/react-dom 19.3.0 (MIT), and
@types/node 24.19.2 (MIT) provide build-time declarations. Keep major versions
aligned with runtime packages. Use the §3.3 Hey API generator with its TypeScript
and Zod plugins; verify generated output against the OpenAPI snapshot on regeneration.
@testing-library/dom 10.4.2 (MIT) supplies DOM queries for component tests; pin alongside the React adapter to avoid peer drift.
Pin transitive js-yaml to 4.3.2 (MIT) for the generator. Earlier 4.x versions
reported three high advisories. Regenerate and compile to check compatibility.

Phase 1 verification (2026-11-17): the Next 16.4.6 flat configs and JSX
accessibility rules ran cleanly on strict TS 6.0.3 with ESLint 10.15.0 despite
older declared ESLint peers. Hey API 0.99.0 generates both TS and Zod contracts.
The full audit has one development advisory at two versions; see docs/security.md.
PostgreSQL 16 and Valkey 9.1.3 answered the actual API readiness probes in Compose.
