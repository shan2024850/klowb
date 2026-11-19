"""Refresh the Phase 1 API contract: uv run python -m scripts.export_openapi."""

import json

from apps.api.main import create_app
from scripts.export_schemas import SCHEMA_DIR


def snapshot() -> str:
    schema = create_app(configure_logs=False).openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    (SCHEMA_DIR / "openapi.json").write_text(snapshot(), encoding="utf-8")
