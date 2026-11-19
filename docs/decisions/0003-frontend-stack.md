# 0003 — Frontend stack and version pins

- Status: Accepted — Playwright provisioning amended by [0012](0012-e2e-browser-provisioning.md)
- Date: 2026-11-17

## Context

Brief default: Next.js, React, strict TypeScript, intentional server/client
boundary, accessible primitives, responsive layouts, Lightweight Charts for
financial charts, ECharts for analytics. npm registry state on 2026-11-17:
Next 16.4.6, React 19.3.1, TypeScript `latest` 7.0.2 (6.0.3 is the newest 6.x),
typescript-eslint 8.73.0 with peer `typescript >=4.8.4 <6.1.0`, ESLint 10.15.0,
Tailwind 4.3.5, vitest 5.1.0, lightweight-charts 5.3.0, echarts 6.1.0. The
environment ships Playwright 1.63.0 with a matching Chromium; registry `latest`
is 1.65.1.

## Decision

- **Next.js 16 (App Router) + React 19**, **pnpm** workspace.
- **TypeScript 6.0.x**, not 7: the lint toolchain does not yet declare support for
  7. `strict` plus `noUncheckedIndexedAccess`.
- **Tailwind CSS 4** for styling; **Radix** primitives (unified `radix-ui`
  package) for accessible interactive components, added only as needed.
- **TanStack Query** for server state; **zod** for runtime validation at the API
  boundary; no global client store until a need appears.
- **Lightweight Charts 5** for price charts, **ECharts 6** for analytical charts
  (modular imports, lazy-loaded, thin in-house React wrapper).
- **ESLint** (Next config + typescript-eslint + jsx-a11y), **vitest** + Testing
  Library + jsdom for unit/component tests, **Playwright pinned to 1.63.0**
  (browser provisioning per ADR-0012) with
  `@axe-core/playwright` for end-to-end and accessibility checks.
- Browser → API traffic is same-origin (`/api/*` rewritten to the backend); the
  market stream is a WebSocket to the API with an Origin allowlist.
- Server components by default; `'use client'` only where interactivity requires;
  chart components are client-only.

## Alternatives considered

- **TypeScript 7.0.2:** rejected for now (typescript-eslint peer range).
- **Biome instead of ESLint:** faster, but `eslint-config-next` and `jsx-a11y`
  rules are wanted.
- **Component kits (MUI, Ant, Chakra):** heavier, harder to give an institutional,
  dense look; Radix + Tailwind gives control and accessibility.
- **Zustand/Redux:** no global client state yet.
- **Latest Playwright:** would not match the preinstalled browser.

## Consequences

- Chart APIs must be taken from installed typings and the bundled agent skill;
  Lightweight Charts attribution must stay enabled.
- Compatibility items C-01…C-03 (`dependency-decisions.md` §5) are settled during
  Phase 1 install; fallbacks are recorded there.

## Revisit when

typescript-eslint supports TypeScript 7; the environment's Playwright changes.
