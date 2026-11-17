from apps.api.settings import Settings
from scripts.export_openapi import snapshot
from scripts.export_schemas import SCHEMA_DIR


def test_p1_contract_001_openapi(settings: Settings) -> None:
    assert snapshot() == (SCHEMA_DIR / "openapi.json").read_text(encoding="utf-8")
