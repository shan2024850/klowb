# Security

**Status:** controls agreed in Phase 0 (2026-11-17); each control lists the phase
in which it lands. A control is not "done" until its test in `tests.json` passes.

Scope assumption (owner default, `docs/open-questions.md` B-05): single operator,
self-hosted, local-first. The design still treats the browser, the network and
every external provider as untrusted.

---

## 1. Assets and threats

| Asset | Threat | Primary controls |
|-------|--------|------------------|
| Broker credentials (paper now; live if ever) | Theft via repo, logs, browser, error messages | Server-only settings as `SecretStr`; never serialised; log redaction; no `NEXT_PUBLIC_*` secrets; `.env` git-ignored; secret scan in CI |
| Ability to place orders | Unauthorised or forged requests; CSRF; replay; accidental live trading | Session auth; CSRF tokens; idempotent `client_order_id`; trading-mode gates; risk engine; audit log |
| Provider/LLM API keys | Leak; cost run-up | As above; outbound host allowlist (constants); LLM budget cap; rate limits |
| Integrity of market data | Malformed/poisoned data driving decisions | Schema validation; data-quality quarantine; fail-closed execution; provenance hash |
| LLM outputs | Prompt injection through news/filings; fabricated numbers | Untrusted-content delimiting; typed structured output only; no tool that can trade; outputs never become orders without deterministic validation and risk checks; source ids required |
| Database | Injection; over-privileged access | Parameterised queries (SQLAlchemy); least-privilege roles; migrations run by a separate role |
| Availability | Reconnect storms; retry storms; resource exhaustion | Bounded retries with jitter; circuit breakers; connection attempt budgets; request size/time limits; rate limiting |
| Supply chain | Malicious/compromised packages or skills | Pinned versions + lockfiles; dependency audit; decisions recorded before install; agent skills pinned by commit hash and reviewed before adoption |

---

## 2. Controls

### 2.1 Secrets management

- Secrets are read only from environment variables / `.env` (git-ignored) into a
  typed settings object; secret fields are `SecretStr`. *(Phase 1)*
- `.env.example` contains names and safe placeholders only. *(Phase 1)*
- A test asserts that no secret value appears in `repr(settings)`, in
  `/api/v1/system/info`, or in log output for a request cycle. *(Phase 1,
  `P1-UNIT-008`)*
- A repository check (`scripts/validate_brain.py`, later a dedicated secret scan)
  fails if `.env` or key-like files are tracked. *(Phase 0, `P0-SEC-001`)*
- Rotation: all keys are replaceable by environment change + restart; nothing is
  persisted in the database.

### 2.2 Browser boundary

- The browser never receives provider, broker or LLM keys. Only variables
  explicitly prefixed `NEXT_PUBLIC_` reach the bundle, and none of them is a
  secret (lint/test check on the built bundle in Phase 15).
- All provider calls are made by the backend. `data.sec.gov` does not support
  CORS anyway.
- Decimals for order tickets are handled as strings end to end.

### 2.3 Authentication and sessions *(lands before any state-changing trading endpoint — Phase 11 at the latest)*

- Single-user (extensible to several) username + password; passwords hashed with
  Argon2id.
- Server-side sessions; opaque random session id in a cookie with `HttpOnly`,
  `Secure` (outside local dev), `SameSite=Lax`, bounded lifetime, idle timeout,
  rotation on login, server-side revocation on logout.
- Login is rate-limited and uses constant-time comparison.
- **Hard rule:** no endpoint that creates, modifies or cancels orders, changes
  risk configuration, engages/disengages the kill switch or arms a mode may be
  merged before authentication, authorisation, CSRF protection and audit logging
  exist and are tested.

### 2.4 Authorisation

- Roles: `viewer` (read), `operator` (paper trading, kill switch), `admin`
  (configuration). Default single user is `admin`.
- Authorisation is enforced in API dependencies, not in the UI.
- Order endpoints additionally check trading mode and the risk engine.

### 2.5 CSRF

- Same-origin architecture (the browser talks to `/api/...` on the web origin).
- State-changing requests require a CSRF token (double-submit: cookie + header)
  and an `Origin`/`Referer` check. `SameSite=Lax` is defence in depth, not the
  only control.

### 2.6 WebSocket

- `Origin` allowlist on handshake. *(Phase 2)*
- Public market-data channels need no session while the app is local-only;
  private channels (orders, portfolio, alerts) require an authenticated session.
  *(Phase 11)*
- Per-connection subscription and message-rate limits; server-side heartbeat;
  slow consumers are disconnected rather than buffered without bound. *(Phase 2)*

### 2.7 Input validation

- Every request body, query and path parameter is validated by Pydantic models
  with explicit bounds (lengths, ranges, enums, max page size). *(Phase 1)*
- Symbols and instrument ids are validated against strict patterns before use.
- Outbound provider URLs are built from constants plus validated identifiers;
  user input never selects a host (no SSRF).

### 2.8 Transport and headers

- API: `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options:
  DENY` / CSP `frame-ancestors 'none'`, `Cache-Control: no-store` on sensitive
  responses. *(Phase 1, `P1-SEC-002`)*
- Web: Content-Security-Policy (script/style/connect allowlist incl. the WS
  origin), HSTS in production. *(Phase 1 baseline, tightened in Phase 15)*
- CORS: disabled by default; an explicit allowlist from `CORS_ALLOWED_ORIGINS`
  when the API is exposed cross-origin. Never `*` with credentials.
- TLS is terminated by the reverse proxy in the `prod` profile.

### 2.9 Rate limiting

- Inbound: per-IP and per-session limits on API routes (strict on login and order
  endpoints). *(Phase 11; basic global limits in Phase 15)*
- Outbound: per-provider token buckets and circuit breakers (`docs/data-providers.md`
  §3). *(Phase 2)*
- LLM: per-call timeout and max tokens; daily budget cap in USD; when the cap is
  reached LLM-assisted agents abstain (the system continues on deterministic
  evidence). *(Phase 8)*

### 2.10 Audit log

- Append-only table recording: who, what, when (UTC), correlation id, before/after
  for configuration, and outcome — for logins, order lifecycle, risk decisions,
  kill-switch changes, mode arming, configuration changes. *(Phase 10–11)*
- The application role has `INSERT`/`SELECT` only on the audit table (no `UPDATE`
  / `DELETE`). *(Phase 11; verified in Phase 15)*

### 2.11 Least privilege

- Database: separate roles for migrations (DDL) and the application (DML only).
- Containers run as non-root with read-only root filesystems where practical;
  only required ports are published; Postgres/Redis are not exposed beyond the
  compose network outside `dev`.
- Broker API keys should be created with the narrowest permission the broker
  offers (paper keys for paper; never withdrawal permissions).

### 2.12 Logging hygiene

- Structured logs only; a redaction processor drops/masks any field whose name
  matches a secret pattern and any `SecretStr`. Request/response bodies of
  authenticated broker calls are not logged. *(Phase 1)*

### 2.13 Dependency and supply-chain security

- Every dependency is recorded with license and purpose before installation
  (`docs/architecture/dependency-decisions.md`).
- Lockfiles committed; installs use the lockfile.
- `pip-audit` (Python) and `pnpm audit` (Node) run as a quality gate; findings are
  fixed or documented with a dated justification. *(Phase 1, `P1-SEC-001`)*
- Agent skills are third-party instructions: the installed TradingView skills were
  read before adoption and are pinned by commit hash in `skills-lock.json`.

### 2.14 LLM-specific

- The LLM has **no tools that can act** (no order placement, no shell, no network
  fetch of arbitrary URLs).
- External text (news, filings) is passed as clearly delimited untrusted content;
  instructions inside it are not followed; outputs must cite `source_ids` that
  exist in the input snapshot or the signal is rejected.
- Numbers in LLM outputs are never trusted as market data; quantitative fields
  are bounded by schema and cross-checked against deterministic features.
- API key is server-only; prompts and outputs are stored for audit without
  secrets.

---

## 3. Things that must never happen (test-backed)

1. A secret in the repository, a log line, an API response or the JS bundle.
2. An order created without passing the risk engine.
3. An order created while `TRADING_MODE=research`.
4. Any request reaching a live broker endpoint in this codebase.
5. A state-changing endpoint reachable without authentication + CSRF.
6. Unbounded retry or reconnect loops.
