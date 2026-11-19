# 0012 — End-to-end browser provisioning

- Status: Accepted (amends the Playwright part of ADR-0003)
- Date: 2026-11-17

## Context

ADR-0003 and the handoff docs said "pin `@playwright/test` to 1.63.0, never run
`playwright install`". That sentence described **one environment** — the first
session's cloud container, which ships Playwright 1.63.0 with a matching Chromium
in `/opt/pw-browsers` — and was mistakenly written as a project rule.

In the second environment (Codex, 2026-11-17) the globally installed `playwright`
package was 1.62.1, its headless shell was missing, `/opt/pw-browsers` did not
exist, and a system Chromium 156 was present. Following the wrong rule, the agent
correctly stopped and recorded P1-E2E-001…003 as `blocked`.

## Decision

1. The project pins **`@playwright/test` to exactly `1.63.0`** in
   `apps/web/package.json` (devDependency, no `^`). This is the project's runner;
   any globally installed `playwright` package in an environment is ignored.
2. The browser must be the one that **matching** runner expects. Provision it with
   the project-local CLI:

   ```bash
   pnpm --filter @klowb/web exec playwright install chromium
   # add --with-deps only if OS libraries are missing and you have root
   ```

   Downloading the matching browser is **allowed and expected** in any
   environment that does not already have it.
3. **Exception — environment already provides it:** if the environment ships the
   matching browser (e.g. Claude Code cloud containers set
   `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` with Playwright 1.63.0), do not
   download a second copy.
4. **If the download is impossible** (no network to the browser CDN), record the
   e2e tests as `blocked` with the exact command and error. A system Chromium via
   `launchOptions.executablePath` may be tried as a diagnostic, but e2e results
   obtained that way must say so in `tests.json` notes and
   `docs/research/verification-log.md` (runner/browser version mismatch is a
   known source of flakiness).
5. Changing the pin is allowed when there is a reason (e.g. a needed fix); update
   `apps/web/package.json`, `docs/architecture/dependency-decisions.md` and this
   ADR together.

## Alternatives considered

- **Require every environment to preinstall 1.63.0:** brittle; blocks work for an
  environmental reason that a one-line install fixes.
- **Track `latest`:** non-reproducible e2e results.
- **Always use the system Chromium:** version drift between runner and browser.

## Consequences

- P1-E2E-001…003 are unblocked (back to `planned`).
- Phase 1 step 4 can proceed in any environment with access to the npm registry
  and the Playwright browser download host.

## Revisit when

The pinned runner needs an upgrade, or the project adds Firefox/WebKit coverage.
