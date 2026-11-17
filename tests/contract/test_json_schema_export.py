from pathlib import Path

from scripts.export_schemas import SCHEMA_DIR, export


def test_p1_contract_002_schema_exports(tmp_path: Path) -> None:
    export(tmp_path)
    generated = {p.name: p.read_bytes() for p in tmp_path.glob("*.schema.json")}
    assert {"Observation.schema.json", "Instrument.schema.json"} <= generated.keys()
    assert generated == {p.name: p.read_bytes() for p in SCHEMA_DIR.glob("*.schema.json")}
