#!/usr/bin/env python3
"""Validate the project "brain": handoff documents and tests.json.

Standard library only, so it runs before anything is installed:

    python3 scripts/validate_brain.py

Implements the Phase 0 acceptance tests:

    P0-DOC-001  required documents exist and are non-empty
    P0-DOC-002  tests.json is structurally valid
    P0-DOC-003  dependency decisions cover every repository named in the brief
    P0-DOC-004  provider matrix covers every provider named in the brief
    P0-DOC-005  progress.md has the five required sections
    P0-DOC-006  every ADR referenced in docs/BRAIN.md exists
    P0-DOC-007  every brief failure-injection / edge case is covered by a test
    P0-SEC-001  no secret-like file is tracked by git

Exit status is 0 only if every check passes. Checks never modify files.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "progress.md",
    "tests.json",
    "docs/BRAIN.md",
    "docs/brief/original-brief.md",
    "docs/architecture.md",
    "docs/architecture/dependency-decisions.md",
    "docs/data-providers.md",
    "docs/risk-model.md",
    "docs/execution-model.md",
    "docs/security.md",
    "docs/runbook.md",
    "docs/plan/phases.md",
    "docs/open-questions.md",
    "docs/research/verification-log.md",
    "docs/HANDOFF.md",
]
REQUIRED_DIRS = ["docs/decisions"]

# Repositories the brief asks to investigate (docs/brief/original-brief.md).
BRIEF_REPOSITORIES = [
    "https://github.com/tradingview/lightweight-charts",
    "https://github.com/apache/echarts",
    "https://github.com/QuantConnect/Lean",
    "https://github.com/nautechsystems/nautilus_trader",
    "https://github.com/ccxt/ccxt",
    "https://github.com/freqtrade/freqtrade",
    "https://github.com/hummingbot/hummingbot",
    "https://github.com/microsoft/qlib",
    "https://github.com/AI4Finance-Foundation/FinRL",
    "https://github.com/AI4Finance-Foundation/FinRL-Trading",
    "https://github.com/OpenBB-finance/OpenBB",
    "https://github.com/dcajasn/Riskfolio-Lib",
    "https://github.com/ranaroussi/quantstats",
    "https://github.com/bukosabino/ta",
    "https://github.com/langchain-ai/langgraph",
    "https://github.com/pydantic/pydantic-ai",
    "https://github.com/crewAIInc/crewAI",
    "https://github.com/microsoft/autogen",
]

# Providers the brief asks to evaluate.
BRIEF_PROVIDERS = [
    "Alpaca",
    "Twelve Data",
    "Massive",
    "Tiingo",
    "Finnhub",
    "Interactive Brokers",
    "Alpha Vantage",
    "SEC EDGAR",
    "yfinance",
    "Stooq",
    "FRED",
    "ECB",
    "CFTC",
    "Binance",
    "Coinbase",
    "Kraken",
    "CCXT",
]

# Brief section "TESTING > Failure injection".
BRIEF_FAILURE_INJECTION = [
    "API 429",
    "API 500",
    "timeout",
    "malformed JSON",
    "disconnected websocket",
    "stale event",
    "duplicate event",
    "reordered event",
    "DB unavailable",
    "Redis unavailable",
    "agent timeout",
    "broker rejection",
    "partial fill",
]

# Brief section "FINANCIAL EDGE CASES".
BRIEF_EDGE_CASES = [
    "DST transition",
    "early close",
    "market holiday",
    "weekend crypto",
    "symbol changes",
    "stock splits",
    "dividends",
    "reverse splits",
    "halted asset",
    "delisting",
    "zero-volume bar",
    "missing candle",
    "crossed bid/ask",
    "huge gap",
    "negative/zero erroneous price",
    "crypto decimal precision",
    "forex pip precision",
    "stablecoin depeg",
    "rate-limit exhaustion",
    "sequence gap",
    "duplicate order acknowledgement",
]

PROGRESS_SECTIONS = [
    "Current phase",
    "Finished work",
    "Unresolved problems",
    "Next action",
    "Commands used for verification",
]

TEST_REQUIRED_KEYS = {
    "id",
    "phase",
    "type",
    "description",
    "status",
    "last_execution",
    "relevant_files",
    "covers",
    "notes",
}
EXECUTED_STATUSES = {"passing", "failing"}
ID_PATTERN = re.compile(r"^P(\d{1,2})-[A-Z][A-Z0-9]*-\d{3}$")

SECRET_FILE_PATTERNS = [
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.env\.(?!example$)[^/]+$"),
    re.compile(r"\.pem$"),
    re.compile(r"(^|/)id_(rsa|ed25519|ecdsa)$"),
    re.compile(r"(^|/)secrets?/"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def check_required_documents() -> list[str]:
    errors = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing file: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty file: {rel}")
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        if not path.is_dir():
            errors.append(f"missing directory: {rel}")
        elif not any(path.glob("*.md")):
            errors.append(f"directory has no .md files: {rel}")
    return errors


def load_tests() -> tuple[dict[str, Any], list[str]]:
    try:
        doc = json.loads(read("tests.json"))
    except FileNotFoundError:
        return {}, ["tests.json not found"]
    except json.JSONDecodeError as exc:
        return {}, [f"tests.json is not valid JSON: {exc}"]
    return doc, []


def check_tests_json() -> list[str]:
    doc, errors = load_tests()
    if errors:
        return errors
    for key in ("schema_version", "updated", "status_values", "type_values", "tests"):
        if key not in doc:
            errors.append(f"tests.json: missing top-level key '{key}'")
    if errors:
        return errors

    statuses = set(doc["status_values"])
    types = set(doc["type_values"])
    if "skipped" in statuses:
        errors.append("tests.json: 'skipped' must not be an allowed status")

    seen: set[str] = set()
    for index, test in enumerate(doc["tests"]):
        label = test.get("id", f"<entry {index}>")
        missing = TEST_REQUIRED_KEYS - test.keys()
        if missing:
            errors.append(f"{label}: missing keys {sorted(missing)}")
            continue
        match = ID_PATTERN.match(test["id"])
        if not match:
            errors.append(f"{label}: id does not match P<phase>-<TYPE>-<nnn>")
        elif int(match.group(1)) != test["phase"]:
            errors.append(f"{label}: id phase does not match 'phase' field")
        if test["id"] in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(test["id"])
        if not isinstance(test["phase"], int) or not 0 <= test["phase"] <= 15:
            errors.append(f"{label}: phase must be an integer 0..15")
        if test["type"] not in types:
            errors.append(f"{label}: unknown type '{test['type']}'")
        if test["status"] not in statuses:
            errors.append(f"{label}: unknown status '{test['status']}'")
        if not isinstance(test["description"], str) or len(test["description"]) < 20:
            errors.append(f"{label}: description too short")
        if not isinstance(test["relevant_files"], list):
            errors.append(f"{label}: relevant_files must be a list")
            continue

        execution = test["last_execution"]
        if test["status"] in EXECUTED_STATUSES:
            if not isinstance(execution, dict):
                errors.append(f"{label}: status '{test['status']}' requires last_execution")
            else:
                for key in ("at", "command", "result"):
                    if not execution.get(key):
                        errors.append(f"{label}: last_execution.{key} is required")
                expected = "pass" if test["status"] == "passing" else "fail"
                if execution.get("result") != expected:
                    errors.append(
                        f"{label}: status '{test['status']}' contradicts "
                        f"last_execution.result '{execution.get('result')}'"
                    )
            if not test["relevant_files"]:
                errors.append(f"{label}: executed tests must list relevant_files")
        if test["status"] in EXECUTED_STATUSES | {"implemented"}:
            for rel in test["relevant_files"]:
                if not (ROOT / rel).exists():
                    errors.append(f"{label}: relevant file does not exist: {rel}")
        if test["status"] == "blocked" and not test["notes"]:
            errors.append(f"{label}: blocked tests must explain why in 'notes'")
    return errors


def check_repositories_covered() -> list[str]:
    try:
        text = read("docs/architecture/dependency-decisions.md")
    except FileNotFoundError:
        return ["docs/architecture/dependency-decisions.md not found"]
    return [f"repository not recorded: {url}" for url in BRIEF_REPOSITORIES if url not in text]


def check_providers_covered() -> list[str]:
    try:
        text = read("docs/data-providers.md")
    except FileNotFoundError:
        return ["docs/data-providers.md not found"]
    return [f"provider not covered: {name}" for name in BRIEF_PROVIDERS if name not in text]


def check_progress_sections() -> list[str]:
    try:
        text = read("progress.md").lower()
    except FileNotFoundError:
        return ["progress.md not found"]
    return [
        f"progress.md: missing section '{section}'"
        for section in PROGRESS_SECTIONS
        if not re.search(rf"^#+\s*{re.escape(section.lower())}", text, re.MULTILINE)
    ]


def check_adrs_exist() -> list[str]:
    try:
        brain = read("docs/BRAIN.md")
    except FileNotFoundError:
        return ["docs/BRAIN.md not found"]
    section = brain.split("## 5.", 1)[-1].split("\n## ", 1)[0]
    numbers = sorted(set(re.findall(r"^\|\s*(\d{4})\s*\|", section, re.MULTILINE)))
    if not numbers:
        return ["docs/BRAIN.md section 5 lists no ADR numbers"]
    decisions = ROOT / "docs" / "decisions"
    return [
        f"ADR {number} is referenced in docs/BRAIN.md but docs/decisions/{number}-*.md is missing"
        for number in numbers
        if not list(decisions.glob(f"{number}-*.md"))
    ]


def check_brief_cases_covered() -> list[str]:
    doc, errors = load_tests()
    if errors:
        return errors
    covered = {item for test in doc.get("tests", []) for item in test.get("covers", [])}
    known = set(BRIEF_FAILURE_INJECTION) | set(BRIEF_EDGE_CASES)
    errors = [
        f"brief failure-injection case has no acceptance test: {case}"
        for case in BRIEF_FAILURE_INJECTION
        if case not in covered
    ]
    errors += [
        f"brief financial edge case has no acceptance test: {case}"
        for case in BRIEF_EDGE_CASES
        if case not in covered
    ]
    errors += [f"unknown 'covers' value (typo?): {item}" for item in sorted(covered - known)]
    return errors


def check_no_tracked_secrets() -> list[str]:
    errors = []
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"could not list tracked files: {exc}"]
    for rel in tracked:
        if any(pattern.search(rel) for pattern in SECRET_FILE_PATTERNS):
            errors.append(f"secret-like file is tracked by git: {rel}")
    gitignore = ROOT / ".gitignore"
    if not gitignore.is_file():
        errors.append(".gitignore is missing")
    else:
        lines = {line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()}
        if ".env" not in lines:
            errors.append(".gitignore does not ignore '.env'")
    return errors


CHECKS: list[tuple[str, str, Callable[[], list[str]]]] = [
    ("P0-DOC-001", "required documents exist", check_required_documents),
    ("P0-DOC-002", "tests.json is valid", check_tests_json),
    ("P0-DOC-003", "brief repositories recorded", check_repositories_covered),
    ("P0-DOC-004", "brief providers covered", check_providers_covered),
    ("P0-DOC-005", "progress.md sections present", check_progress_sections),
    ("P0-DOC-006", "referenced ADRs exist", check_adrs_exist),
    ("P0-DOC-007", "brief failure/edge cases traced to tests", check_brief_cases_covered),
    ("P0-SEC-001", "no tracked secret files", check_no_tracked_secrets),
]


def main() -> int:
    failed = 0
    for check_id, title, check in CHECKS:
        errors = check()
        print(f"{'PASS' if not errors else 'FAIL'}  {check_id}  {title}")
        for error in errors:
            print(f"        - {error}")
        failed += bool(errors)

    doc, _ = load_tests()
    tests = doc.get("tests", [])
    if tests:
        counts: dict[str, int] = {}
        for test in tests:
            counts[test["status"]] = counts.get(test["status"], 0) + 1
        summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
        print(f"\ntests.json: {len(tests)} acceptance tests ({summary})")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
