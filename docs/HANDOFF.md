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

---

## Session log

| Date | Agent | Result | Commit |
|------|-------|--------|--------|
| 2026-11-17 | Claude (Fable 5.2 → Opus 5.5) | Phase 0 complete; Phase 1 backend core | `980be4b`, `11fc401` |
| 2026-11-17 | Codex | Phase 1 steps 2–3: backend tests, metrics-prefix fix, JSON Schema exports, `.env.example`; 164 tests; Phase 1 at 27/38. Stopped at the web step on a browser-provisioning rule. | `5e9eee8` |
| 2026-11-17 | Claude (Opus 5.5), review | Re-ran every gate on `5e9eee8` in the original environment: 164 passed; ruff, mypy, import contracts, brain checks clean. Found the browser rule was a mis-stated environment fact; replaced it with ADR-0012 and unblocked P1-E2E-001…003. | `e135a5f` |
| 2026-11-17 | Codex | Phase 1 steps 4–6: Next.js shell, generated API contracts, Compose dev/test/prod + smoke, audits (picomatch dev-only exception). Browser CDN blocked (HTTP 403); e2e passed only as a system-Chromium diagnostic. Phase 1 at 35/38. | `5ed43e2` |
| 2026-11-17 | Claude (Opus 5.5), review | Reproduced every gate on `5ed43e2`; ran P1-E2E-001…003 with the matching Chromium build 1243 → passed. **Phase 1 closed (38/38).** Added Phase 2 prompt below. | `b469bdc` |
| 2026-11-17 | Codex | Phase 2 group 1 (virtual timers, token bucket, retry, circuit breaker, error classification). Hit its usage limit during group 2; the calendar files it had written were never committed. | `eadc719` |
| 2026-11-19 | Claude (Opus 5.5) | Reviewed `eadc719` (green). Redid group 2 (market calendars, C-04 settled) and built group 3 (provider contract, conformance suite, mock provider). Phase 2: 12/45 passing, 1 implemented. | `aec0011`, `6f3c270`, this commit |

## Follow-up prompt for Codex (after the ADR-0012 fix)

```text
Pull the latest `claude/hopeful-einstein-krs00n` and follow AGENTS.md and the
original handoff prompt in docs/HANDOFF.md (all rules still apply).

What changed since your last session: your browser blocker was caused by a rule
in the handoff docs that described the previous agent's container, not the
project. It has been replaced by docs/decisions/0012-e2e-browser-provisioning.md.
Read that ADR. In short: pin @playwright/test to exactly 1.63.0 in
apps/web/package.json, then install its matching browser with
`pnpm --filter @klowb/web exec playwright install chromium`. Ignore the globally
installed playwright 1.62.1. P1-E2E-001..003 are back to `planned`.

Re-run the baseline from the original prompt (expect 164 pytest cases passing and
27 of 38 Phase 1 tests passing), then continue Phase 1 from step 4 of
"Next action" in progress.md: read the installed Next.js 16 package/docs before
writing any config, scaffold apps/web and packages/types, run the web gates, then
steps 5–6 (Docker Compose profiles + smoke script, dependency scans, full gate
run, adversarial self-review). Do not start Phase 2. If the browser download
itself fails, record the exact command and error with --status blocked and
continue with the non-browser work.
```

## Prompt for Codex — Phase 2

```text
Pull the latest `claude/hopeful-einstein-krs00n`. Follow AGENTS.md and every
rule in the original handoff prompt in docs/HANDOFF.md (anti-hallucination,
safety, and the before-you-stop protocol all still apply).

Status: Phase 1 is COMPLETE (38/38). The three browser tests were run by the
reviewer with Playwright 1.63.0's matching Chromium build 1243 and passed; see
progress.md "Phase 1 closing verification".

Re-run the baseline first (expect 165 pytest cases, clean ruff/mypy/
lint-imports, pnpm typecheck/lint/test clean, 46 of 274 tests passing,
8/8 brain checks). If anything differs, reconcile before changing code.

Then start Phase 2 (mock market-data provider and replay framework), following
"Next action" in progress.md and the Phase 2 section of docs/plan/phases.md.
Before writing code for it, read docs/architecture.md sections 4-5 and
docs/data-providers.md section 3 (adapter contract). Every new test name or
docstring carries its P2-* acceptance ID. Record every new dependency
(e.g. exchange_calendars, pandas) in docs/architecture/dependency-decisions.md
before installing it, and settle compatibility item C-04 with a test.
Do not connect any real market-data provider (that is Phase 3).

Browser tests: your environment cannot download Playwright's Chromium (HTTP 403).
If a Phase 2 task needs a browser test, run it as the ADR-0012 diagnostic with
KLOWB_DIAGNOSTIC_CHROMIUM set, record it `blocked` with that evidence, and note
it in progress.md for a matching-browser run later. Never mark a diagnostic run
as `passing`.

Phase 2 is large (45 tests). Commit and push after each completed group of
tests, and keep progress.md current so the next session can resume exactly.
```

## Prompt for Codex — resume Phase 2 at group 4

```text
Pull the latest `claude/hopeful-einstein-krs00n`. If your workspace still has
uncommitted files from your interrupted session (for example libs/calendars/ or
tests/unit/calendars/), discard them first (`git stash` or `git checkout -- .`
plus removing untracked files): committed versions supersede them.

Follow AGENTS.md and every rule in the original handoff prompt in
docs/HANDOFF.md (anti-hallucination, safety, before-you-stop protocol).

Baseline (expect): 258 pytest cases passing; ruff, mypy and lint-imports clean;
pnpm typecheck/lint/test clean; 8/8 brain checks; Phase 2 at 12 passing and
1 implemented of 45. Reconcile before coding if anything differs.

Then do group 4 from "Next action" in progress.md, in services/market_data/:
normalizer.py (P2-UNIT-015), quality.py (P2-UNIT-007..014), health.py
(P2-UNIT-016), bars.py (P2-UNIT-004..006, using
libs.calendars.registry.get_calendar), and P2-PROP-001..002. Read first:
docs/architecture.md section 5, libs/providers/base.py,
libs/providers/mock/provider.py, libs/schemas/market.py, libs/calendars/*.py,
tests/stream_driver.py. Reuse the existing types; do not redefine them.
Commit and push after each completed group of tests with progress.md updated.
```
