import subprocess
import sys
from pathlib import Path


def test_p1_static_004_domain_time_policy() -> None:
    root = Path(__file__).resolve().parents[3]
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "TID251,DTZ",
            "apps/api",
            "libs",
            "services",
        ],
        cwd=root,
        check=True,
    )
