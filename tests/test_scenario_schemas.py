"""
Тести для валідації схем сценаріїв OMSpy
"""

import pytest
from jsonschema import ValidationError
from omspy.core.json_schema_validator import validate_scenario

# --- валідні словники ---------------------------------
valid_scenario_max_self_consumption = {
    "name": "Basic Self-Consumption Test",
    "description": "A simple scenario for testing max self-consumption",
    "type": "max_self_consumption",
    "version": "1.0",
    "technologies": ["pv_system", "battery_storage", "grid_connection"],
    "data_sources": {
        "load_profile": "data/load/residential_load.csv",
        "generation_profiles": {
            "pv_system": "data/generation/pv_profile.csv"
        },
        "price_profiles": {
            "import": "data/prices/import_tariff.csv",
            "export": "data/prices/export_tariff.csv"
        }
    },
    "self_consumption_config": {
        "target_percentage": 85,
        "priority_order": ["direct_consumption", "battery_charge", "battery_discharge", "grid_export", "grid_import"],
        "battery_strategy": {
            "charge_from_surplus": True,
            "discharge_to_load": True,
            "avoid_grid_charging": True,
            "min_soc_reserve_pct": 20
        }
    },
    "constraints": {
        "min_self_consumption_pct": 70,
        "max_grid_dependency_pct": 30,
        "backup_autonomy_hours": 4
    },
    "global_constraints": {
        "max_grid_import_kw": 100,
        "max_grid_export_kw": 50,
        "emergency_backup_hours": 24
    }
}

valid_scenario_time_of_use = {
    "name": "Time-of-Use Optimization",
    "description": "Scenario optimized for time-of-use tariffs",
    "type": "time_of_use",
    "version": "1.0",
    "technologies": ["pv_rooftop", "bess_home", "grid"],
    "data_sources": {
        "load_profile": "data/load/commercial_load.csv",
        "generation_profiles": {
            "pv_rooftop": "data/generation/pv_commercial.csv"
        },
        "price_profiles": {
            "tou_import": "data/prices/tou_tariff.csv"
        }
    },
    "tariff_periods": [
        {
            "name": "peak",
            "time_ranges": ["17:00-21:00"],
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "strategy": "avoid_import",
            "import_price_multiplier": 3.0,
            "export_price_multiplier": 1.5
        },
        {
            "name": "off_peak",
            "time_ranges": ["23:00-07:00"],
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "strategy": "charge_battery",
            "import_price_multiplier": 0.5,
            "export_price_multiplier": 0.3
        },
        {
            "name": "mid_peak",
            "time_ranges": ["07:00-17:00", "21:00-23:00"],
            "strategy": "normal_operation",
            "import_price_multiplier": 1.0,
            "export_price_multiplier": 0.8
        }
    ],
    "optimization_priorities": {
        "peak_hours": {
            "minimize_grid_import": True,
            "use_battery_first": True,
            "export_surplus": False
        },
        "off_peak_hours": {
            "charge_battery_from_grid": True,
            "max_grid_import_kw": 50,
            "target_soc_pct": 90
        },
        "mid_peak_hours": {
            "balanced_operation": True,
            "self_consumption_priority": True
        }
    },
    "battery_management": {
        "pre_peak_charging": {
            "enabled": True,
            "start_hours_before_peak": 2,
            "target_soc_pct": 90
        },
        "peak_discharge_limits": {
            "max_discharge_rate_pct": 100,
            "reserve_for_backup_pct": 20
        }
    },
    "constraints": {
        "max_peak_import_kw": 20,
        "max_daily_grid_import_kwh": 100,
        "min_export_during_peak": False,
        "backup_requirement_hours": 8
    }
}

valid_scenario_minimal = {
    "name": "Minimal Test Scenario",
    "type": "max_self_consumption",
    "technologies": ["grid"],
    "data_sources": {
        "load_profile": "data/load/minimal.csv"
    }
}

valid_scenario_cost_optimization = {
    "name": "Cost Optimization Test",
    "type": "cost_optimization",
    "technologies": ["pv_system", "battery_storage", "grid_connection"],
    "data_sources": {
        "load_profile": "data/load/office_load.csv",
        "generation_profiles": {
            "pv_system": "data/generation/pv_office.csv"
        },
        "price_profiles": {
            "spot_price": "data/prices/spot_market.csv"
        }
    }
}


# --- позитивні тести ----------------------------------
@pytest.mark.parametrize(
    "scenario",
    [
        valid_scenario_max_self_consumption,
        valid_scenario_time_of_use,
        valid_scenario_minimal,
        valid_scenario_cost_optimization,
    ],
)
def test_valid_scenarios(scenario):
    """Тест валідних конфігурацій сценаріїв"""
    # не повинно кидати ValidationError
    validate_scenario(scenario)


# --- граничні випадки для позитивних тестів -----------
def test_max_self_consumption_different_target_percentages():
    """Тест різних цільових відсотків само споживання"""
    percentages = [0, 25, 50, 75, 90, 100]

    for percentage in percentages:
        scenario = valid_scenario_max_self_consumption.copy()
        scenario["self_consumption_config"]["target_percentage"] = percentage
        validate_scenario(scenario)


def test_max_self_consumption_different_priority_orders():
    """Тест різних порядків пріоритетів"""
    priority_orders = [
        ["direct_consumption", "battery_charge", "grid_export"],
        ["direct_consumption", "grid_export", "battery_charge"],
        ["battery_discharge", "direct_consumption", "grid_import"]
    ]

    for priority_order in priority_orders:
        scenario = valid_scenario_max_self_consumption.copy()
        scenario["self_consumption_config"]["priority_order"] = priority_order
        validate_scenario(scenario)


def test_time_of_use_different_strategies():
    """Тест різних стратегій для TOU"""
    strategies = ["avoid_import", "maximize_export", "charge_battery", "discharge_battery", "normal_operation"]

    for strategy in strategies:
        scenario = valid_scenario_time_of_use.copy()
        scenario["tariff_periods"][0]["strategy"] = strategy
        validate_scenario(scenario)


def test_time_of_use_different_time_ranges():
    """Тест різних часових діапазонів"""
    time_ranges = [
        ["00:00-06:00"],
        ["06:00-12:00", "18:00-24:00"],
        ["09:30-17:45"],
        ["22:15-05:30"]
    ]

    for time_range in time_ranges:
        scenario = valid_scenario_time_of_use.copy()
        scenario["tariff_periods"][0]["time_ranges"] = time_range
        validate_scenario(scenario)


def test_scenario_optional_fields():
    """Тест з опціональними полями"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["version"] = "2.1.5"
    scenario["description"] = "Updated test scenario with new features"
    validate_scenario(scenario)


def test_scenario_single_technology():
    """Сценарій з однією технологією"""
    scenario = valid_scenario_minimal.copy()
    scenario["technologies"] = ["grid_only"]
    validate_scenario(scenario)


# --- граничні значення --------------------------------
def test_max_self_consumption_boundary_values():
    """Граничні значення для само споживання"""
    scenario = valid_scenario_max_self_consumption.copy()

    # Мінімальні значення
    scenario["self_consumption_config"]["target_percentage"] = 0
    scenario["self_consumption_config"]["battery_strategy"]["min_soc_reserve_pct"] = 0
    scenario["constraints"]["min_self_consumption_pct"] = 0
    validate_scenario(scenario)

    # Максимальні значення
    scenario["self_consumption_config"]["target_percentage"] = 100
    scenario["self_consumption_config"]["battery_strategy"]["min_soc_reserve_pct"] = 100
    scenario["constraints"]["max_grid_dependency_pct"] = 100
    validate_scenario(scenario)


def test_time_of_use_boundary_multipliers():
    """Граничні значення множників цін"""
    scenario = valid_scenario_time_of_use.copy()

    # Мінімальні множники (0)
    scenario["tariff_periods"][0]["import_price_multiplier"] = 0
    scenario["tariff_periods"][0]["export_price_multiplier"] = 0
    validate_scenario(scenario)

    # Великі множники
    scenario["tariff_periods"][0]["import_price_multiplier"] = 10.0
    scenario["tariff_periods"][0]["export_price_multiplier"] = 5.0
    validate_scenario(scenario)


def test_global_constraints_boundary_values():
    """Граничні значення глобальних обмежень"""
    scenario = valid_scenario_max_self_consumption.copy()

    # Мінімальні значення
    scenario["global_constraints"]["max_grid_import_kw"] = 0
    scenario["global_constraints"]["max_grid_export_kw"] = 0
    scenario["global_constraints"]["emergency_backup_hours"] = 0
    validate_scenario(scenario)


# --- негативні тести для граничних значень ------------
def test_scenario_invalid_type():
    """Невалідний тип сценарію"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["type"] = "invalid_scenario_type"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_max_self_consumption_invalid_target_percentage():
    """Невалідний цільовий відсоток (поза межами 0-100)"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["self_consumption_config"]["target_percentage"] = 150
    with pytest.raises(ValidationError):
        validate_scenario(scenario)

    scenario["self_consumption_config"]["target_percentage"] = -10
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_max_self_consumption_invalid_priority_order():
    """Невалідний порядок пріоритетів"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["self_consumption_config"]["priority_order"] = ["invalid_priority", "another_invalid"]
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_max_self_consumption_duplicate_priorities():
    """Дублікати в порядку пріоритетів"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["self_consumption_config"]["priority_order"] = ["direct_consumption", "direct_consumption"]
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_invalid_time_format():
    """Невалідний формат часу"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0]["time_ranges"] = ["25:00-30:00"]  # Невалідний час
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_invalid_strategy():
    """Невалідна стратегія"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0]["strategy"] = "invalid_strategy"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_negative_multiplier():
    """Негативний множник ціни"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0]["import_price_multiplier"] = -1.0
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_invalid_day():
    """Невалідний день тижня"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0]["days"] = ["invalid_day"]
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_global_constraints_negative_values():
    """Негативні значення в глобальних обмеженнях"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["global_constraints"]["max_grid_import_kw"] = -100
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


# --- негативні тести ID та додаткових полів -----------
def test_scenario_invalid_technology_id():
    """Невалідний ID технології"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["technologies"] = ["invalid@technology#id"]
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_scenario_additional_properties_forbidden():
    """Додаткові властивості заборонені"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["unknown_property"] = "should_fail"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


# --- негативні тести для обов'язкових полів -----------
@pytest.mark.parametrize("field", ["name", "type", "technologies", "data_sources"])
def test_scenario_missing_required_fields(field):
    """Сценарій без обов'язкових полів"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario.pop(field)
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_scenario_empty_technologies():
    """Порожній список технологій"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["technologies"] = []
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_scenario_missing_load_profile():
    """Відсутній обов'язковий load_profile"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["data_sources"].pop("load_profile")
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_missing_tariff_periods():
    """TOU сценарій без tariff_periods"""
    scenario = valid_scenario_time_of_use.copy()
    scenario.pop("tariff_periods")
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_empty_tariff_periods():
    """TOU сценарій з порожніми tariff_periods"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"] = []
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


@pytest.mark.parametrize("field", ["name", "time_ranges", "strategy"])
def test_time_of_use_missing_tariff_period_fields(field):
    """TOU сценарій без обов'язкових полів у tariff_periods"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0].pop(field)
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


# --- тести типів даних --------------------------------
def test_scenario_invalid_technologies_type():
    """technologies має бути масивом"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["technologies"] = "not_an_array"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_scenario_invalid_data_sources_type():
    """data_sources має бути об'єктом"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["data_sources"] = "not_an_object"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_max_self_consumption_invalid_target_type():
    """target_percentage має бути числом"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["self_consumption_config"]["target_percentage"] = "not_a_number"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


def test_time_of_use_invalid_multiplier_type():
    """price_multiplier має бути числом"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"][0]["import_price_multiplier"] = "not_a_number"
    with pytest.raises(ValidationError):
        validate_scenario(scenario)


# --- тести мета-полів ----------------------------------
def test_scenario_meta_fields_allowed():
    """$schema та $id мета-поля дозволені"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["$schema"] = "http://json-schema.org/draft-07/schema#"
    scenario["$id"] = "https://omspy.tech/schema/scenario/test.json"
    validate_scenario(scenario)  # не повинно падати


# --- тести комбінацій ----------------------------------
def test_max_self_consumption_with_backup_constraint():
    """Само споживання з обмеженням резервного живлення"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["constraints"]["backup_autonomy_hours"] = 12
    scenario["self_consumption_config"]["battery_strategy"]["min_soc_reserve_pct"] = 30
    validate_scenario(scenario)


def test_time_of_use_complex_schedule():
    """Складний розклад TOU з багатьма періодами"""
    scenario = valid_scenario_time_of_use.copy()
    scenario["tariff_periods"].append({
        "name": "weekend_peak",
        "time_ranges": ["19:00-22:00"],
        "days": ["saturday", "sunday"],
        "strategy": "maximize_export",
        "import_price_multiplier": 2.5,
        "export_price_multiplier": 2.0
    })
    validate_scenario(scenario)


def test_scenario_all_constraint_types():
    """Сценарій з усіма типами обмежень"""
    scenario = valid_scenario_max_self_consumption.copy()
    scenario["global_constraints"] = {
        "max_grid_import_kw": 150,
        "max_grid_export_kw": 75,
        "emergency_backup_hours": 48
    }
    scenario["constraints"] = {
        "min_self_consumption_pct": 80,
        "max_grid_dependency_pct": 20,
        "backup_autonomy_hours": 6
    }
    validate_scenario(scenario)