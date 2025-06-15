from typing import Dict, Any
from .base import load_schema, validate_with_schema
from jsonschema import ValidationError

def validate_technology(instance: Dict[str, Any], tech: str) -> None:
    schema = load_schema("technology", f"{tech}.json")
    validate_with_schema(instance, schema)

    # додаткові перевірки, наприклад:
    soc_min = instance.get("soc_min_pct")
    soc_max = instance.get("soc_max_pct")
    if soc_min is not None and soc_max is not None and soc_min >= soc_max:
        raise ValidationError(f"soc_min_pct ({soc_min}) >= soc_max_pct ({soc_max})")
