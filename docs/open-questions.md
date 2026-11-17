# Open questions

Two lists. **A** = technical questions that can be answered from the repository or
official documentation; each names the phase by which it must be answered. **B** =
decisions only the owner can make; each states the default the work currently
assumes so nothing is blocked.

**None of the open items blocks Phase 1.** No blocking contradiction was found
between the brief, the repository and the verified facts.

Status: `OPEN` · `ANSWERED` (answer recorded here and in the relevant doc).

---

## A. Technical questions (answer from official docs / by testing)

| ID | Question | Why it matters | Answer by | Status |
|----|----------|----------------|-----------|--------|
| OQ-T01 | What is `httpx2`, and should it replace `httpx`? | `httpx` has had no stable release since 0.28.1 (2024-12-06); the Anthropic SDK depends on `httpx2`. | Phase 0 | **ANSWERED 2026-11-17:** PyPI describes it as a continuation of HTTPX maintained by the Pydantic organisation (BSD-3-Clause, import `httpx2`). We standardise on it. Its concrete API must be read from the installed package before use (C-05). |
| OQ-T02 | What is Kraken's numeric rate limit for **public REST** endpoints? | Token-bucket configuration for backfill. | Phase 3 | OPEN — not on the rate-limit page read (that page covers the per-key counter). Use a conservative ≤ 1 request/second until verified. |
| OQ-T03 | Do Kraken / Coinbase publish market-data display or redistribution terms for public API data? | `redistribution_allowed`; whether the dashboard may be shown to others. | Phase 3 | OPEN — nothing found. Default `false`, single-operator use. |
| OQ-T04 | Is Kraken `trade_id` strictly contiguous (+1) per pair? | Gap detection without false positives. | Phase 3 | OPEN — docs say "a sequence number unique per book". Verify empirically on a live capture before treating any jump as a gap. |
| OQ-T05 | How is the Kraken v2 book CRC32 checksum computed? | Needed only for order-book features. | Phase 5 (if order-flow features are built) | OPEN — in a separate Kraken guide not yet read. |
| OQ-T06 | Is the Coinbase Exchange `level2` channel still public, and what are connection/subscribe limits? | Second venue. | When Coinbase is added | OPEN. |
| OQ-T07 | Binance spot: 24-hour connection lifetime and ping interval? | Only if Binance is added. | When Binance is added | OPEN — not confirmed for spot. |
| OQ-T08 | Twelve Data free tier: what is the source/consolidation of "real-time US equities", and does "internal non-display usage only" forbid showing it in this dashboard? | Feed-quality label; licence compliance. | Phase 12 | OPEN — labelled `UNOFFICIAL` until documented. |
| OQ-T09 | Tiingo Starter licence terms and current limits from the pricing page (not the blog). | Compliance. | Phase 12 | OPEN. |
| OQ-T10 | Alpha Vantage: real-time vs delayed entitlement on free/premium tiers. | Only if adopted. | Phase 12 | OPEN — low priority (25 requests/day). |
| OQ-T11 | Stooq current terms of use. | The brief allows Stooq "only after verifying current terms". | Before any use | OPEN — the terms page returned no content. **Stooq must not be used until this is answered.** |
| OQ-T12 | ECB Data Portal reuse/licensing terms; does the API need any registration? | Phase 13 compliance. | Phase 13 | OPEN. |
| OQ-T13 | CFTC COT: dataset identifiers on the public reporting API, and whether the announced twice-weekly schedule is in effect. | Release-time correctness (no data before publication). | Phase 13 | OPEN. |
| OQ-T14 | SEC EDGAR: exact `User-Agent` format requirement. | Fair-access compliance. | Phase 13 | OPEN — the 10 requests/second limit is verified; the User-Agent rule was not stated on the two pages read (check the SEC developer FAQ). |
| OQ-T15 | Alpaca: valid `feed` parameter values, crypto data source/feed quality, WebSocket endpoints and auth flow, paper-account rate limits. | Phase 11–12 adapters. | Phase 11 | OPEN. |
| OQ-T16 | NYSE/Nasdaq extended-hours windows, including on early-close days. | Pre/post-market session modelling. | Phase 2 (model), Phase 12 (verify against the exchange/broker docs) | OPEN — `exchange_calendars` covers regular sessions, holidays and early closes; extended hours are our own layer. |
| OQ-T17 | Does `exchange_calendars` 4.13.3 work with pandas 3.1.1? | Calendar dependency. | Phase 2 | OPEN (C-04). |
| OQ-T18 | Do `eslint-plugin-jsx-a11y` 6.10.2 and `eslint-config-next` 16.4.6 work with ESLint 10 and TypeScript 6.0.3? | Lint gate. | Phase 1 | OPEN (C-01, C-02). |
| OQ-T19 | Which OpenAPI→TypeScript generator works with TypeScript 6.0.3? | Generated API types. | Phase 1 | OPEN (C-03). |
| OQ-T20 | Can Docker pull images through the agent proxy in this environment? | Docker build / compose smoke gates. | Phase 1 | OPEN (C-06). |
| OQ-T21 | Does CCXT's MIT package include WebSocket ("Pro") support today? | Only if CCXT is adopted. | When considered | OPEN. |
| OQ-T22 | Is Valkey fully compatible with our use of redis-py 8.1.0 (pub/sub, basic commands)? | Compose image choice. | Phase 1 | OPEN (C-07). |
| OQ-T23 | Next.js 16 specifics: rewrites for same-origin API proxying, caching defaults, config format. | Phase 1 web shell. | Phase 1 | OPEN — read current Next docs / installed package before writing config. |

---

## B. Owner decisions (defaults assumed; nothing is blocked)

| ID | Decision | Default assumed | Impact if changed |
|----|----------|-----------------|-------------------|
| B-01 | Platform / product name | `klowb` (repository name); web package `@klowb/web` | Rename strings and package scope. |
| B-02 | Repository license ("open-source" in the brief) | **None added yet.** Recommendation: Apache-2.0 (compatible with all adopted dependencies; includes a patent grant). | Add `LICENSE` + headers/NOTICE. |
| B-03 | Jurisdiction and venues the operator may legally use | Not assumed. Kraken public data for development; no venue-specific trading. | Choice of exchanges/brokers (e.g. Binance availability). |
| B-04 | LLM provider, model and budget | Anthropic, `claude-opus-5-5`, **disabled** until an API key and a daily budget are supplied | Model id / client implementation. |
| B-05 | Users and exposure | Single operator, self-hosted, local network | Multi-user auth, hardening, data-display licences. |
| B-06 | Deployment target | Local Docker Compose | Cloud infrastructure, managed databases, TLS. |
| B-07 | Paper broker | Internal simulator first; Alpaca paper optional (needs the owner's free paper keys) | Adapter work in Phase 11. |
| B-08 | Paid data (e.g. consolidated US equities) | None; free tiers only, labelled honestly | Feed quality for equities, execution eligibility. |
| B-09 | Account base currency | USD | Portfolio accounting, FX conversion. |
| B-10 | Risk defaults (`docs/risk-model.md` §4) | Conservative defaults listed there | Config only. |
| B-11 | Pull request | Not opened unless requested; work is pushed to the designated branch | — |

### Codex browser environment — ANSWERED 2026-11-17
Can the web workflow use an environment preconfigured with Playwright 1.63.0
and its matching Chromium, or should the project adopt a different tested
browser and runner pair? See the Codex preflight in the verification log.

**Answer:** neither is required. The "preinstalled 1.63.0, never run
`playwright install`" rule described the first session's container only and was
wrongly written as a project rule. Decision recorded in
`docs/decisions/0012-e2e-browser-provisioning.md`: keep `@playwright/test`
pinned to 1.63.0 in `apps/web/package.json` and install its matching Chromium
with `pnpm --filter @klowb/web exec playwright install chromium`. The global
`playwright` 1.62.1 in the Codex environment is irrelevant.
