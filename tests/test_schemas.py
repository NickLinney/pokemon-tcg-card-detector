import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_all_json_schemas_are_valid():
    for path in (Path(__file__).parents[1] / "schemas").glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
