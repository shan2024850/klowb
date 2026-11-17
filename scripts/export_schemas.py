"""Regenerate the canonical JSON contracts with python -m scripts.export_schemas."""

import json
from pathlib import Path
from typing import Any

from libs.schemas.instrument import Instrument
from libs.schemas.market import ObservationAdapter
from libs.schemas.system import ErrorEnvelope, LivenessReport, ReadinessReport, SystemInfo

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"


def contracts() -> dict[str, dict[str, Any]]:
    models = (Instrument, LivenessReport, ReadinessReport, SystemInfo, ErrorEnvelope)
    return {
        "Observation": ObservationAdapter.json_schema(),
        **{model.__name__: model.model_json_schema() for model in models},
    }


def export(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, schema in contracts().items():
        (directory / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    export(SCHEMA_DIR)
