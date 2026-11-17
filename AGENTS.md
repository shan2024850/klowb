# AGENTS.md

Instructions for any AI coding agent working in this repository.

The authoritative operating manual is **`CLAUDE.md`** — follow it regardless of
which model or tool you are. The complete handoff context is **`docs/BRAIN.md`**.

Minimum protocol:

1. Read `progress.md`, then `docs/BRAIN.md`.
2. Run `python3 scripts/validate_brain.py`.
3. Work only on the current phase in `docs/plan/phases.md`.
4. Before stopping: update `progress.md` and `tests.json`, commit, and push to the
   designated work branch.

Hard limits: never enable live trading or place a real order; never commit
secrets; never weaken or delete tests; never present delayed/single-venue/unofficial
data as consolidated real-time.
