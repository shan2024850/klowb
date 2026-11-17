# Handoff — continuing this project with another agent (e.g. OpenAI Codex)

**Written:** 2026-11-17, at the end of the first working session. The previous
model stopped because of rate limits, mid-way through Phase 1.

## Where everything is

| What | Where |
|------|-------|
| All work | git branch **`claude/hopeful-einstein-krs00n`** (`main` is still empty) |
| Live status + exact next steps | `progress.md` |
| Full context, rules, decisions, stale-knowledge traps | `docs/BRAIN.md` |
| Rules every agent must follow | `AGENTS.md` (read automatically by Codex), `CLAUDE.md` |
| The owner's original brief (requirements baseline) | `docs/brief/original-brief.md` |
| Phase plan + acceptance-test IDs | `docs/plan/phases.md`, `tests.json` |

## Exact stopping point

- Phase 0 complete. Phase 1 in progress: backend core is written; only the schema
  layer has automated tests. Web app, Docker, `.env.example` not started.
- 20 of 274 acceptance tests pass (Phase 0: 8/8, Phase 1: 12/38).
- The next concrete task is step 2 of "Next action" in `progress.md`: write the
  missing backend tests listed there, starting with `tests/unit/test_settings.py`
  (P1-UNIT-007).
- One known defect to fix first in that work: metrics route label loses the
  `/api/v1` prefix (`progress.md` → Unresolved problems #1).

## Before you start Codex

1. Make sure Codex works on branch `claude/hopeful-einstein-krs00n` (or a branch
   created from it). Starting from `main` would give it an empty repository.
2. Codex's environment needs Python 3.13 + `uv`, Node 22 + `pnpm`, and ideally
   PostgreSQL 16 and Redis. If its environment lacks one, it must record the
   affected tests as `blocked` with the error — not pretend they pass.

## Prompt to paste into Codex

```text
You are taking over an in-progress software project. The previous agent stopped
mid-task because of rate limits. Your job is to continue exactly where it
stopped, without inventing anything.

REPOSITORY AND BRANCH
- Work on git branch `claude/hopeful-einstein-krs00n` (main is empty). If you are
  not on it, check it out first. Commit there (or on a branch created from it if
  your setup requires a new branch). Never force-push, never rewrite history.

READ BEFORE DOING ANYTHING (in this order, in full)
1. AGENTS.md
2. progress.md            <- live status and the exact next action
3. docs/BRAIN.md          <- context, non-negotiable rules, decisions, traps
4. docs/plan/phases.md    <- read the Phase 1 section
5. CLAUDE.md              <- conventions and commands (they apply to you too)
Read docs/brief/original-brief.md when a requirement is unclear.

ESTABLISH THE BASELINE BEFORE CHANGING CODE
- Run: python3 scripts/validate_brain.py           (expect 8/8 checks passed)
- Run: python3 scripts/tests_status.py summary     (expect 20 passing of 274)
- Check tools: python3 --version, uv --version, node -v, pnpm -v, psql --version,
  redis-server --version, docker --version.
- Start PostgreSQL and Redis if available, then run scripts/dev_db_setup.sh.
- Run: uv sync && uv run pytest && uv run ruff check . && uv run mypy && uv run lint-imports
  (expect 143 tests passed and every check clean).
- If anything differs from what progress.md says, STOP changing code, report
  the difference in progress.md, and reconcile before continuing. Trust git and
  test output over documents.

WHAT TO DO
- Continue Phase 1 only, following "Next action" in progress.md step by step,
  starting with step 2 (missing backend tests; fix the metrics route-label
  defect described under "Unresolved problems"). Do not start Phase 2.
- Every test must reference its acceptance-test ID from tests.json in its name
  or docstring (e.g. test_p1_unit_007_...).

ANTI-HALLUCINATION RULES (mandatory)
- Never describe, import or call a file, function, class, endpoint, setting or
  package you have not opened or verified in this repository or its installed
  dependencies. If you need to know how something works, read the code.
- Library versions here are newer than your training data (e.g. FastAPI 0.163,
  Starlette 1.10, Pydantic 2.14, SQLAlchemy 2.1, pandas 3.1, Next.js 16,
  TypeScript 6/7, Lightweight Charts 5). Before using any library API, read the
  installed source/typings under .venv/ or node_modules/, or the official docs.
  docs/BRAIN.md section 7 lists known traps — read it.
- Pinned versions are in pyproject.toml / uv.lock and
  docs/architecture/dependency-decisions.md. Do not add a dependency without
  first recording its version, licence, purpose and risk in that file.
- Do not claim a test passes unless you ran it and saw it pass. Record results
  only with: python3 scripts/tests_status.py set <ID...> --status passing
  --command "<the exact command you ran>". If something cannot run in your
  environment, use --status blocked --notes "<command and error>". Never mark
  'passing' from reasoning alone.
- Never delete, skip, xfail or weaken a test or an acceptance criterion to get
  green. Never use --no-verify. Never edit tests.json descriptions.
- In docs/runbook.md, tag a command [VERIFIED <date>] only after running it.
- If documentation and actual behaviour disagree, test the behaviour and record
  the discrepancy in docs/research/verification-log.md.
- If you are unsure, investigate (read code, run a command) instead of guessing.
  If it still cannot be resolved, write the question into docs/open-questions.md
  and continue with the next task that does not depend on it.

SAFETY RULES (mandatory)
- TRADING_MODE stays "research" by default. Never enable live trading, never
  add a live broker integration, never place any real order.
- Never commit secrets or a .env file. No key may reach logs, API responses or
  the browser bundle.
- Never present delayed / single-venue / unofficial / simulated market data as
  consolidated real-time; the feed-quality label must stay visible.
- UTC, timezone-aware timestamps only; no future data leakage.
- Never claim guaranteed profit or certainty in code, UI text or docs.

BEFORE YOU STOP FOR ANY REASON (finished, blocked, or running low on budget)
1. Update progress.md: current phase, finished work (tested vs untested),
   unresolved problems, the exact next action, and the commands you ran.
2. Update tests.json via scripts/tests_status.py.
3. Run python3 scripts/validate_brain.py (must pass).
4. Commit with a clear message and push to the work branch.
A half-finished task with an accurate progress.md is fine; an undocumented
change is not.
```
