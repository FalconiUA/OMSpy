from __future__ import annotations
import json
from pathlib import Path
import importlib.resources as pkg
from typing import Any, Dict

from jsonschema import validate as _js_validate  # or `from jsonschema import ValidationError`

_SCHEMAS_ROOT = "omspy.json_schemas"  # adjust if needed

def load_schema(kind: str, name: str) -> Dict[str, Any]:
    """
    Load a JSON schema named `name` (e.g. 'pv.json') from
    the subpackage `omspy.json_schemas.<kind>`.
    """
    pkg_path = pkg.files(f"{_SCHEMAS_ROOT}.{kind}")
    schema_file = pkg_path.joinpath(name)
    with schema_file.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_with_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Run jsonschema.validate() and let it raise ValidationError on failure.
    """
    _js_validate(instance=instance, schema=schema)

def validate_file(path: Path | str, kind: str, name: str) -> None:
    """
    Load a JSON file from disk and validate it against
    the schema at `<kind>/<name>`.
    """
    p = Path(path)
    inst = json.loads(p.read_text(encoding="utf-8"))
    schema = load_schema(kind, name)
    validate_with_schema(inst, schema)

def is_valid(instance: Dict[str, Any], kind: str, name: str) -> bool:
    """
    Return True/False instead of raising.
    """
    try:
        schema = load_schema(kind, name)
        validate_with_schema(instance, schema)
        return True
    except Exception:
        return False
