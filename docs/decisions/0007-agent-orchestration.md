# 0007 — Agent orchestration: in-house typed graph

- Status: Accepted
- Date: 2026-11-17

## Context

The brief requires a *typed* investment-committee graph of 19 agents, routing so
that not every agent runs for every asset, a strict output contract, genuinely
diverse evidence, no double counting of correlated agents, full traceability
(input snapshot, model, prompt version, output, ensemble result), mocked LLM
outputs first, and the rule that no free-form output may place an order. It asks
us to consider LangGraph, pydantic-ai, crewAI and AutoGen, and to choose the
smallest coherent set. Verified 2026-11-17: LangGraph 1.2.22 (MIT), pydantic-ai
2.68.0 (MIT, near-daily releases), crewAI 1.15.41 (MIT, telemetry on by default),
AutoGen archived by Microsoft.

Most of the 19 "agents" are not language tasks. Momentum, mean reversion,
volatility, market structure, order flow, cross-asset, universe/liquidity, data
quality, portfolio construction, risk, execution and attribution are deterministic
computations. Language models add evidence only for news, sentiment,
fundamental/event text, macro narrative and adversarial critique.

## Decision

- Implement the committee as a **small in-house typed DAG runner** on asyncio and
  Pydantic: nodes with typed inputs/outputs, pure routing function, per-node
  timeout, error isolation, and a persisted decision log.
- Two agent kinds behind one `Agent` protocol and one `AgentSignal` output:
  **deterministic agents** and **LLM-assisted agents**.
- LLM access only through an **`LLMClient` protocol**: `MockLLMClient` (Phase 7),
  then `AnthropicLLMClient` using the official `anthropic` SDK with structured
  outputs validated against our Pydantic schemas (Phase 8). The LLM has no tools
  that can act.
- LLM use is **off by default**, budget-capped, and every LLM-assisted agent
  degrades to a typed abstain when the LLM is unavailable.
- None of LangGraph, pydantic-ai, crewAI or AutoGen is installed.

## Alternatives considered

- **LangGraph:** strong for durable, interruptible, dynamic graphs. Our graph is
  static, short-lived and code-routed; the extra abstraction and dependency tree
  buy little, and traceability is easier when we own the runner.
- **pydantic-ai (+ pydantic-graph):** closest in spirit (typed outputs, test
  models, usage limits). Not adopted because we want exact control and logging of
  the provider request, and its release cadence is very fast. First choice if
  multi-provider LLM support becomes a requirement.
- **crewAI:** conversational role-play orchestration conflicts with strict typed
  contracts; default telemetry.
- **AutoGen:** archived, unmaintained.

## Consequences

- We own ~300 lines of orchestration code and its tests.
- Determinism: with the mock LLM the whole committee is replayable bit-for-bit.
- Switching LLM vendors means writing another `LLMClient`, not rewriting agents.

## Revisit when

We need checkpoint/resume across process restarts, human-in-the-loop interrupts
inside the graph, dynamic agent-created sub-graphs, or several LLM providers.
