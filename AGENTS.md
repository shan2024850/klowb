# AGENTS.md

Instructions for any AI coding agent (Codex, Claude, or other) working in this
repository. They are mandatory.

## What this project is

**klowb** — a multi-asset (US equities/ETFs, crypto spot, forex) quantitative
research and day/swing-trading platform. Research mode by default; live trading
disabled. The owner's requirements: `docs/brief/original-brief.md`.

## Read first, every session

1. `progress.md` — live status, unresolved problems, the exact next action.
2. `docs/BRAIN.md` — full context, non-negotiable rules (§1), decisions (§5),
   environment facts (§6), stale-knowledge traps (§7).
3. `docs/plan/phases.md` — the current phase's deliverables and test IDs.
4. `CLAUDE.md` — conventions and commands; they apply to every agent.
5. Taking over from another agent: `docs/HANDOFF.md`.

All work is on branch `claude/hopeful-einstein-krs00n` (`main` is empty).

## Protocol

1. Baseline before changing code:
   `python3 scripts/validate_brain.py`, `python3 scripts/tests_status.py summary`,
   `uv sync && uv run pytest && uv run ruff check . && uv run mypy && uv run lint-imports`.
   If reality differs from `progress.md`, reconcile first — trust git and test
   output over documents.
2. Work only on the current phase. Do not start phase N+1 while phase N has
   unfinished acceptance tests.
3. Each test references its acceptance-test ID from `tests.json`.
4. Before stopping for any reason: update `progress.md`, update `tests.json` via
   `scripts/tests_status.py`, run `python3 scripts/validate_brain.py`, commit, push.

## Do not hallucinate

- Never reference a file, symbol, endpoint, setting or package you have not
  opened or verified. Read the code instead of assuming.
- Installed library versions are newer than most training data. Read installed
  source/typings (`.venv/`, `node_modules/`) or official docs before using an
  API. Known traps: `docs/BRAIN.md` §7.
- Mark a test `passing` only after running it, with the exact command
  (`scripts/tests_status.py set … --command "…"`). Use `blocked` with notes when
  the environment prevents a run.
- Tag runbook commands `[VERIFIED date]` only after running them.
- Add a dependency only after recording version, licence, purpose and risk in
  `docs/architecture/dependency-decisions.md`.
- Unresolvable uncertainty goes into `docs/open-questions.md`; move on to work
  that does not depend on it.

## Hard limits

- Never enable live trading, add a live broker integration, or place a real
  order. `TRADING_MODE` defaults to `research`.
- Never commit secrets or `.env`; no key in logs, API responses or the browser.
- Never present delayed/single-venue/unofficial/simulated data as consolidated
  real-time.
- Never delete, skip, xfail or weaken a test; never `--no-verify`; never edit
  `tests.json` descriptions.
- Never claim guaranteed profit or certainty.
