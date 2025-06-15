from typing import Dict, Any
from .base import load_schema, validate_with_schema

def validate_scenario(instance: Dict[str, Any]) -> None:
    """
    Валідує сценарій проти json_schemas/scenario/scenario.json
    """
    schema = load_schema("scenario", "scenario.json")
    validate_with_schema(instance, schema)
    # тут можна додати додаткові перевірки сценарію, якщо потрібно
