# Progress

**This file is the live status of the project.** Update it whenever a task is
finished, a blocker appears, or a session ends. A new contributor (human or model)
should be able to continue from this file alone, with `docs/BRAIN.md` for context.

- Last updated: 2026-11-17
- Work branch: `claude/hopeful-einstein-krs00n` (push here only; no PR unless the
  owner asks)

---

## Current phase

**Phase 0 — Repository audit, research, architecture decisions and development
environment: COMPLETE.**

**Next: Phase 1 — Canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell,
health checks: NOT STARTED.**

No application code exists yet. The repository contains the handoff brain only.

---

## Finished work

### Phase 0 (2026-11-17)

- Audited the repository: empty (zero tracked files, two historical commits).
  → `docs/audit/repository-audit-2026-11-17.md`
- Audited the development environment (tool versions, services, network
  reachability). → `docs/BRAIN.md` §6
- Verified current versions and licenses of every candidate dependency from the
  PyPI and npm registries, and read all 18 repositories the brief names.
  → `docs/architecture/dependency-decisions.md`
- Researched provider entitlements from official documentation; probed Kraken and
  Coinbase public feeds live. → `docs/data-providers.md`,
  `docs/research/verification-log.md`
- Recorded 11 architecture decisions. → `docs/decisions/0001…0011`
- Wrote the architecture, risk, execution, security and runbook documents.
- Wrote the phased plan and enumerated 274 acceptance tests.
  → `docs/plan/phases.md`, `tests.json`
- Preserved the owner's brief verbatim. → `docs/brief/original-brief.md`
- Wrote the operating manual and handoff brain. → `CLAUDE.md`, `AGENTS.md`,
  `docs/BRAIN.md`
- Installed and reviewed the official TradingView Lightweight Charts agent skills
  (pinned by commit in `skills-lock.json`). → `.agents/skills/`, `.claude/skills/`
- Wrote a stdlib-only validator for the brain. → `scripts/validate_brain.py`

### Acceptance tests

| Phase | Total | Passing | Notes |
|-------|-------|---------|-------|
| 0 | 8 | 8 | all executed via `scripts/validate_brain.py` |
| 1–15 | 266 | 0 | planned |

---

## Unresolved problems

None blocking. Open items are tracked in `docs/open-questions.md`:

- **Technical (A):** 22 open questions, each tied to the phase that must answer
  it. The ones Phase 1 must settle at install time are the compatibility items
  C-01…C-03, C-06, C-07 in `docs/architecture/dependency-decisions.md` §5
  (ESLint 10 vs plugins, OpenAPI→TS generator, Docker pulls through the proxy,
  Valkey compatibility) and OQ-T23 (current Next.js 16 configuration).
- **Owner decisions (B):** defaults are assumed for all (name `klowb`, no license
  file yet, Kraken data, LLM off, single operator, local Compose). None blocks
  work.
- **Environment limitation:** third-party GitHub pages/API are blocked from the
  container, so repository "latest activity" was recorded as latest package
  release date.

---

## Next action

Start **Phase 1** (`docs/plan/phases.md` → Phase 1, work items 1–10), in this
order:

1. Start local services (`docs/runbook.md` §2.2).
2. Create `pyproject.toml` (uv, Python 3.13) with the backend versions in
   `dependency-decisions.md` §3.1–3.2; `uv sync`; configure ruff, mypy strict,
   pytest, import-linter. Record what was actually installed.
3. Implement `libs/domain` → `libs/schemas` → `libs/observability` with their
   unit/property tests (`P1-UNIT-001…009`, `P1-PROP-001…002`).
4. Implement `apps/api` (settings with trading-mode gates, health/readiness,
   metrics, system info, error envelope, security headers) and the database layer
   with Alembic (`P1-INT-*`, `P1-FAIL-*`, `P1-SEC-002`).
5. Scaffold the pnpm workspace and `apps/web` shell; **read the current Next.js
   documentation / installed package before writing configuration**; pin
   `@playwright/test` to 1.63.0 (`P1-WEB-*`, `P1-E2E-*`).
6. Add `.env.example`, Dockerfiles, `docker-compose.yml` profiles, smoke script,
   dependency scans (`P1-SMOKE-001`, `P1-SEC-001`, `P1-SEC-003`).
7. Run every quality gate (`docs/runbook.md` §5), update `tests.json`, replace
   `[PLANNED]` tags in the runbook with `[VERIFIED date]`, write the adversarial
   self-review here, commit, push.

---

## Commands used for verification

Executed on 2026-11-17 in the development environment:

```bash
# Repository and environment audit
pwd; ls -la; git status; git log --oneline -n 20; git branch -a; git ls-files | wc -l
node -v; npm -v; pnpm -v; python3 --version; uv --version
docker --version; docker compose version; psql --version; redis-server --version
node -e "console.log(require('playwright/package.json').version)"

# Services start
service postgresql start && pg_lsclusters && su postgres -c "psql -tAc 'select version()'"
redis-server --daemonize yes --save '' --appendonly no && redis-cli ping
(dockerd > dockerd.log 2>&1 &); sleep 8; docker info | grep "Server Version"

# Reachability
curl -sS -o /dev/null -w "%{http_code}\n" https://api.kraken.com/0/public/Time          # 200
curl -sS -o /dev/null -w "%{http_code}\n" https://api.exchange.coinbase.com/time        # 200
curl -sS -o /dev/null -w "%{http_code}\n" https://api.binance.com/api/v3/time           # 451
curl -sS -o /dev/null -w "%{http_code}\n" https://api.github.com/repos/tradingview/lightweight-charts  # 403

# Registry metadata (PyPI JSON API and npm registry) for every candidate package
# Live WebSocket probe of wss://ws.kraken.com/v2 and wss://ws-feed.exchange.coinbase.com
#   (python websockets 17.4 client; output in docs/research/verification-log.md §1.5)

# Agent skills
npx --yes skills@1.9.0 add tradingview/lightweight-charts --yes

# Brain validation (Phase 0 acceptance tests)
python3 scripts/validate_brain.py        # 8/8 checks passed
```

---

## Adversarial self-review

### Phase 0

Reviewed the Phase 0 output looking for overclaiming and gaps:

- **Claims about third parties are bounded by evidence.** Every provider fact in
  `docs/data-providers.md` carries a V/P/U status; unverified items are listed in
  `docs/research/verification-log.md` §2 and default to the conservative choice
  (`redistribution_allowed=false`, weakest plausible feed quality).
- **Not verified, stated as such:** repository last-commit dates; market-data
  redistribution terms; several free-tier details taken from search summaries of
  pages that were old. These must be re-checked in the phase that uses them.
- **Runbook honesty:** only commands that were executed are tagged verified; all
  application commands are tagged planned.
- **Risk of stale decisions:** package versions move weekly. The lockfiles created
  in Phase 1 become the truth; the tables in `dependency-decisions.md` are intent.
- **Design not yet proven by code:** every architectural claim is a plan until the
  corresponding acceptance tests pass. `tests.json` shows 266 of 274 as `planned`.
