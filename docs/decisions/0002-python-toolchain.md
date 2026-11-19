# 0002 — Python toolchain and single root project

- Status: Accepted
- Date: 2026-11-17

## Context

The development environment provides Python 3.13.18 and uv 0.11.32. Current
package versions (PyPI, 2026-11-17) are far ahead of most reference material:
FastAPI 0.163, Pydantic 2.14, SQLAlchemy 2.1, pandas 3.1, numpy 2.5 (requires
Python ≥ 3.12), pytest 9, mypy 2.4, ruff 0.17.

## Decision

- **Python 3.13**, managed by **uv**; one `pyproject.toml` at the repository root;
  `uv.lock` committed. The project is an application (`package = false`): source
  is importable because the repository root is on the path (`pythonpath` for
  pytest, `PYTHONPATH`/workdir in containers).
- **ruff** for lint and formatting (single tool), **mypy --strict** for types,
  **pytest** + **pytest-asyncio** + **hypothesis** for tests, **import-linter**
  for module boundaries, **pip-audit** for dependency scanning.
- HTTP client: **httpx2** (see `dependency-decisions.md` §3.1). WebSocket client:
  **websockets**.
- JSON: standard library `json` with `parse_float=Decimal` for provider payloads.
- Time: all access through an injected `Clock`; `datetime.now()`/`utcnow()` banned
  outside `SystemClock`.

## Alternatives considered

- **Poetry / pip-tools:** uv is already installed, faster, and lockfile-based.
- **pyright instead of mypy:** either works; mypy has first-class Pydantic and
  SQLAlchemy plugins. One type checker only.
- **black + isort + flake8:** replaced by ruff.
- **orjson:** faster, but adds an MPL-2.0 component and float handling we do not
  want on the price path.

## Consequences

- Pydantic v2 / SQLAlchemy 2.x idioms only; older idioms are rejected in review.
- pandas 3 behaviour (copy-on-write, string dtype) must be verified by tests, not
  assumed.

## Revisit when

A dependency drops Python 3.13 support or a tool here is superseded.
