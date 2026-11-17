#!/usr/bin/env python3
"""Maintain tests.json without hand-editing JSON.

Standard library only.

    python3 scripts/tests_status.py summary
    python3 scripts/tests_status.py list --phase 1 [--status planned]
    python3 scripts/tests_status.py set P1-UNIT-001 P1-UNIT-002 \
        --status passing --command "uv run pytest tests/unit/schemas"
    python3 scripts/tests_status.py set P1-SMOKE-001 --status blocked \
        --notes "docker pull refused by proxy: <error>"
    python3 scripts/tests_status.py files P1-UNIT-001 path/a.py path/b.py

Rules enforced here (and re-checked by scripts/validate_brain.py):

* entries are never deleted and descriptions are never edited by this tool;
* 'passing' / 'failing' require --command and record time and commit;
* 'blocked' requires --notes;
* there is no 'skipped' status.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests.json"


def load() -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(TESTS.read_text(encoding="utf-8"))
    return doc


def save(doc: dict[str, Any]) -> None:
    doc["updated"] = datetime.now(UTC).date().isoformat()
    TESTS.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def head_commit() -> str | None:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return f"{sha}+dirty" if dirty else sha


def cmd_summary(doc: dict[str, Any], _: argparse.Namespace) -> int:
    phases: dict[int, dict[str, int]] = {}
    for test in doc["tests"]:
        phases.setdefault(test["phase"], {}).setdefault(test["status"], 0)
        phases[test["phase"]][test["status"]] += 1
    statuses = doc["status_values"]
    print("phase  total  " + "  ".join(f"{s:>11}" for s in statuses))
    for phase in sorted(phases):
        row = phases[phase]
        print(
            f"{phase:>5}  {sum(row.values()):>5}  "
            + "  ".join(f"{row.get(s, 0):>11}" for s in statuses)
        )
    total = len(doc["tests"])
    passing = sum(1 for t in doc["tests"] if t["status"] == "passing")
    print(f"\n{passing}/{total} passing")
    return 0


def cmd_list(doc: dict[str, Any], args: argparse.Namespace) -> int:
    for test in doc["tests"]:
        if args.phase is not None and test["phase"] != args.phase:
            continue
        if args.status and test["status"] != args.status:
            continue
        print(
            f"{test['id']:<18} {test['status']:<12} {test['type']:<18} {test['description'][:90]}"
        )
    return 0


def find(doc: dict[str, Any], ids: list[str]) -> list[dict[str, Any]]:
    by_id = {test["id"]: test for test in doc["tests"]}
    missing = [i for i in ids if i not in by_id]
    if missing:
        sys.exit(f"unknown test id(s): {', '.join(missing)}")
    return [by_id[i] for i in ids]


def cmd_set(doc: dict[str, Any], args: argparse.Namespace) -> int:
    if args.status not in doc["status_values"]:
        sys.exit(f"status must be one of {doc['status_values']}")
    if args.status in {"passing", "failing"} and not args.command:
        sys.exit("--command is required for passing/failing")
    if args.status == "blocked" and not args.notes:
        sys.exit("--notes is required for blocked")
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    commit = head_commit()
    for test in find(doc, args.ids):
        test["status"] = args.status
        if args.status in {"passing", "failing"}:
            test["last_execution"] = {
                "at": now,
                "command": args.command,
                "result": "pass" if args.status == "passing" else "fail",
                "commit": commit,
            }
        if args.notes is not None:
            test["notes"] = args.notes
        print(f"{test['id']} -> {args.status}")
    save(doc)
    return 0


def cmd_files(doc: dict[str, Any], args: argparse.Namespace) -> int:
    (test,) = find(doc, [args.id])
    test["relevant_files"] = list(args.paths)
    save(doc)
    print(f"{test['id']} relevant_files = {test['relevant_files']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("summary")

    p_list = sub.add_parser("list")
    p_list.add_argument("--phase", type=int)
    p_list.add_argument("--status")

    p_set = sub.add_parser("set")
    p_set.add_argument("ids", nargs="+")
    p_set.add_argument("--status", required=True)
    p_set.add_argument("--command")
    p_set.add_argument("--notes")

    p_files = sub.add_parser("files")
    p_files.add_argument("id")
    p_files.add_argument("paths", nargs="+")

    args = parser.parse_args()
    doc = load()
    handler = {"summary": cmd_summary, "list": cmd_list, "set": cmd_set, "files": cmd_files}
    return handler[args.cmd](doc, args)


if __name__ == "__main__":
    sys.exit(main())
