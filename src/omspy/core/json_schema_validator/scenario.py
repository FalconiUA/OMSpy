from typing import Dict, Any
from .base import load_schema, validate_with_schema


def validate_scenario(instance: Dict[str, Any]) -> None:
    """
    Валідує сценарій проти відповідної схеми на основі типу
    """
    # Спочатку валідуємо базову схему
    base_schema = load_schema("scenario", "base.json")
    validate_with_schema(instance, base_schema)

    # Потім валідуємо специфічну схему на основі типу
    scenario_type = instance.get("type")
    if not scenario_type:
        raise ValueError("Missing required 'type' field in scenario")

    # Мапінг типів сценаріїв до файлів схем
    type_to_schema = {
        "max_self_consumption": "max_self_consumption.json",
        "time_of_use": "time_of_use.json",
        # Можна легко додавати нові типи:
        # "backup_priority": "backup_priority.json",
        # "cost_optimization": "cost_optimization.json",
        # "custom": "custom.json"
    }

    schema_file = type_to_schema.get(scenario_type)
    if not schema_file:
        # Якщо тип не знайдено, використовуємо загальну схему
        # (або можна кинути помилку для строгої валідації)
        return

    # Валідуємо проти специфічної схеми
    specific_schema = load_schema("scenario", schema_file)
    validate_with_schema(instance, specific_schema)