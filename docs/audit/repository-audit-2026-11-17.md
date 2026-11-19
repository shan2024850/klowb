# Repository audit — 2026-11-17 (Phase 0)

## 1. What was inspected

Per the brief's "research before implementation" checklist:

| Step | Command / action | Result |
|------|------------------|--------|
| 1 | `pwd` | `/home/user/klowb` |
| 2 | `ls -la`, `git ls-files` | Only `.git/`. **Zero tracked files.** |
| 3 | Read `CLAUDE.md`, `README.md`, `docs/`, `package.json`/workspace config, `pyproject.toml`, docker-compose files, environment examples, existing tests | **None exist.** |
| 3 | `git status` | Clean; branch `claude/hopeful-einstein-krs00n` |
| 3 | `git log` | 2 commits: `9c77450 Initial commit` (added a 2-line `README.md`, 2026-03-23) and `d93a754 Delete README.md` (2026-11-16) |
| 3 | `git branch -a` | local: `claude/hopeful-einstein-krs00n`, `main`; remotes: `origin/claude/hopeful-einstein-krs00n`, `origin/main` |

## 2. Findings

- The repository is **empty**. There is no existing code, configuration,
  convention or user work to preserve or conflict with.
- Therefore the brief's architectural default and proposed structure apply
  without adaptation pressure (ADR-0001).
- No license file exists (owner decision B-02).
- No CI configuration exists.
- No secrets are present in history (the only historical file was a 2-line
  README).

## 3. Environment audit

Recorded in `docs/BRAIN.md` §6 and `docs/research/verification-log.md` §1.5.
Summary: Node 22.23.4, pnpm 10.28.0, Python 3.13.18, uv 0.11.32, PostgreSQL 16.15
and Redis 7.0.15 installed (stopped by default, both start), Docker 29.9.2 +
Compose v5.6.1 (daemon starts manually), Playwright 1.63.0 + Chromium
preinstalled; outbound HTTPS via proxy; PyPI/npm reachable; third-party GitHub
blocked from the container; Kraken and Coinbase reachable; Binance global returns
HTTP 451.

## 4. Contradictions and how they were resolved

| # | Apparent contradiction | Resolution |
|---|------------------------|------------|
| 1 | Brief: "Do not push to remote without authorization." Session instructions: develop on branch `claude/hopeful-einstein-krs00n` and push there; the container is ephemeral. Owner: the brain must let another model continue after an interruption. | Pushing to the **designated work branch only** is the authorised channel and is required for the handoff to survive. No other branch is pushed; no pull request is opened unless requested. |
| 2 | Brief: install the Lightweight Charts skills "if compatible with the current Claude Code environment". | Compatible: `npx skills add` succeeded; files were read before adoption and committed with a lock file. |
| 3 | Brief lists TypeScript "strict" with the latest toolchain; `typescript@latest` is 7.0.2 but the lint stack supports `<6.1.0`. | Use TypeScript 6.0.x (ADR-0003). |
| 4 | Brief treats non-permissive licenses as a design concern; the conventional PostgreSQL driver alternative (psycopg) is LGPL and current Redis is AGPL/RSAL/SSPL. | asyncpg (Apache-2.0) and Valkey (BSD) chosen (ADR-0004). |
| 5 | Brief asks for a "latest meaningful activity" record for each repository; the environment blocks GitHub's API and release feeds. | Latest **package release date** recorded as a lower bound, with the limitation stated. |

**No blocking contradiction** was found. Phase 1 may begin.

## 5. Deliverables of the brief's "FIRST TASK" and where they are

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Repository audit | this file |
| 2 | Dependency/repository verification report | `docs/architecture/dependency-decisions.md` §2 |
| 3 | Licensing matrix | `docs/architecture/dependency-decisions.md` §1, §3 |
| 4 | Data-provider entitlement matrix | `docs/data-providers.md` |
| 5 | Architectural decision record(s) | `docs/decisions/0001…0011` |
| 6 | Phased task plan | `docs/plan/phases.md` |
| 7 | `tests.json` | `tests.json` (274 acceptance tests) |
| 8 | Initial `CLAUDE.md` | `CLAUDE.md` |
| 9 | Explicit unresolved questions | `docs/open-questions.md` |
