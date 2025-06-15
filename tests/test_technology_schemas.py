import pytest
from jsonschema import ValidationError
from omspy.core.json_schema_validator import validate_technology

# --- валідні словники ---------------------------------
valid_pv = {
    "id": "pv_test",
    "dc_power_kw": 100,
    "degradation_pct_per_year": 0.5,
    "energy_profile": "data/profiles/test_pv.csv",
    "installation_cost_per_kw": 700,
    "om_cost_per_kw_per_year": 15,
    "lifetime_years": 25,
}

valid_grid = {
    "id": "grid_test",
    "max_import_kw": 200,
    "max_export_kw": 50,
    "tariff_import_profile": "data/tariffs/import.csv",
    "tariff_export_profile": "data/tariffs/export.csv",
    "is_islanding_allowed": True,
}

valid_bess_default = {
    "id": "bess_default",
    "energy_nominal_kwh": 200,
    "power_nominal_kw": 100,
    "soc_min_pct": 10,
    "soc_max_pct": 90,
    "initial_soc_pct": 50,
    "roundtrip_efficiency_pct": 90,
    "cycle_life": 5000,
    "degradation": {"type": "default"},
}

valid_bess_fixed = {
    "id": "bess_fixed",
    "energy_nominal_kwh": 250,
    "power_nominal_kw": 125,
    "soc_min_pct": 5,
    "soc_max_pct": 95,
    "initial_soc_pct": 80,
    "roundtrip_efficiency_pct": 88,
    "cycle_life": 6000,
    "degradation": {
        "type": "fixed",
        "first_year_degradation_pct": 5,
        "avg_degradation_pct_after_first_year": 2.5,
    },
}

valid_bess_custom = {
    "id": "bess_custom",
    "energy_nominal_kwh": 300,
    "power_nominal_kw": 150,
    "soc_min_pct": 0,
    "soc_max_pct": 100,
    "initial_soc_pct": 50,
    "roundtrip_efficiency_pct": 92,
    "cycle_life": 7000,
    "degradation": {
        "type": "custom",
        "degradation_pct_per_year": [0, 1, 1, 1, 1, 1, 1]
    },
}


# --- позитивні тести ----------------------------------
@pytest.mark.parametrize(
    ("instance", "tech"),
    [
        (valid_pv, "pv"),
        (valid_grid, "grid"),
        (valid_bess_default, "bess"),
        (valid_bess_fixed, "bess"),
        (valid_bess_custom, "bess"),
    ],
)
def test_valid(instance, tech):
    # не повинно кидати ValidationError
    validate_technology(instance, tech)


# --- граничні випадки для позитивних тестів -----------
def test_pv_with_ac_power_instead_of_dc():
    """Тест альтернативного поля ac_power_kw замість dc_power_kw"""
    pv_ac = valid_pv.copy()
    pv_ac.pop("dc_power_kw")
    pv_ac["ac_power_kw"] = 95
    validate_technology(pv_ac, "pv")


def test_pv_with_total_cost_instead_of_per_kw():
    """Тест альтернативного поля total_cost замість installation_cost_per_kw"""
    pv_total = valid_pv.copy()
    pv_total.pop("installation_cost_per_kw")
    pv_total["total_cost"] = 70000
    validate_technology(pv_total, "pv")


def test_grid_zero_export():
    """Grid з нульовим експортом (дозволено)"""
    grid_no_export = valid_grid.copy()
    grid_no_export["max_export_kw"] = 0
    validate_technology(grid_no_export, "grid")


def test_bess_with_separate_efficiencies():
    """BESS з окремими ефективностями заряду/розряду"""
    bess_separate = valid_bess_default.copy()
    bess_separate.pop("roundtrip_efficiency_pct")
    bess_separate["charge_efficiency_pct"] = 95
    bess_separate["discharge_efficiency_pct"] = 92
    validate_technology(bess_separate, "bess")


def test_bess_equal_soc_min_max():
    """BESS з рівними soc_min і soc_max - повинно проходити схему, але падати на додатковій перевірці"""
    bess_equal = valid_bess_default.copy()
    bess_equal["soc_min_pct"] = 50
    bess_equal["soc_max_pct"] = 50
    with pytest.raises(ValidationError, match="soc_min_pct.*>=.*soc_max_pct"):
        validate_technology(bess_equal, "bess")


# --- граничні значення --------------------------------
def test_pv_minimum_degradation():
    """PV з мінімальною деградацією (0%)"""
    pv_min_deg = valid_pv.copy()
    pv_min_deg["degradation_pct_per_year"] = 0
    validate_technology(pv_min_deg, "pv")


def test_pv_maximum_degradation():
    """PV з максимальною деградацією (10%)"""
    pv_max_deg = valid_pv.copy()
    pv_max_deg["degradation_pct_per_year"] = 10
    validate_technology(pv_max_deg, "pv")


def test_bess_extreme_soc_ranges():
    """BESS з екстремальними SOC діапазонами"""
    bess_extreme = valid_bess_default.copy()
    bess_extreme["soc_min_pct"] = 0
    bess_extreme["soc_max_pct"] = 100
    bess_extreme["initial_soc_pct"] = 0
    validate_technology(bess_extreme, "bess")


def test_bess_minimum_efficiency():
    """BESS з мінімальною ефективністю (50%)"""
    bess_min_eff = valid_bess_default.copy()
    bess_min_eff["roundtrip_efficiency_pct"] = 50
    validate_technology(bess_min_eff, "bess")


# --- негативні тesti для граничних значень ------------
def test_pv_invalid_degradation_too_high():
    """PV з надто високою деградацією (>10%)"""
    pv_bad_deg = valid_pv.copy()
    pv_bad_deg["degradation_pct_per_year"] = 15
    with pytest.raises(ValidationError):
        validate_technology(pv_bad_deg, "pv")


def test_pv_invalid_degradation_negative():
    """PV з негативною деградацією"""
    pv_neg_deg = valid_pv.copy()
    pv_neg_deg["degradation_pct_per_year"] = -1
    with pytest.raises(ValidationError):
        validate_technology(pv_neg_deg, "pv")


def test_pv_invalid_power_zero():
    """PV з нульовою потужністю"""
    pv_zero_power = valid_pv.copy()
    pv_zero_power["dc_power_kw"] = 0
    with pytest.raises(ValidationError):
        validate_technology(pv_zero_power, "pv")


def test_pv_invalid_power_negative():
    """PV з негативною потужністю"""
    pv_neg_power = valid_pv.copy()
    pv_neg_power["dc_power_kw"] = -10
    with pytest.raises(ValidationError):
        validate_technology(pv_neg_power, "pv")


def test_grid_invalid_max_import_zero():
    """Grid з нульовим max_import_kw"""
    grid_zero_import = valid_grid.copy()
    grid_zero_import["max_import_kw"] = 0
    with pytest.raises(ValidationError):
        validate_technology(grid_zero_import, "grid")


def test_grid_invalid_max_export_negative():
    """Grid з негативним max_export_kw"""
    grid_neg_export = valid_grid.copy()
    grid_neg_export["max_export_kw"] = -10
    with pytest.raises(ValidationError):
        validate_technology(grid_neg_export, "grid")


def test_bess_invalid_soc_out_of_range():
    """BESS з SOC поза діапазоном 0-100%"""
    bess_bad_soc = valid_bess_default.copy()
    bess_bad_soc["soc_min_pct"] = -5
    with pytest.raises(ValidationError):
        validate_technology(bess_bad_soc, "bess")

    bess_bad_soc["soc_min_pct"] = 105
    with pytest.raises(ValidationError):
        validate_technology(bess_bad_soc, "bess")


def test_bess_invalid_efficiency_too_low():
    """BESS з надто низькою ефективністю (<50%)"""
    bess_low_eff = valid_bess_default.copy()
    bess_low_eff["roundtrip_efficiency_pct"] = 45
    with pytest.raises(ValidationError):
        validate_technology(bess_low_eff, "bess")


def test_bess_invalid_efficiency_too_high():
    """BESS з надто високою ефективністю (>100%)"""
    bess_high_eff = valid_bess_default.copy()
    bess_high_eff["roundtrip_efficiency_pct"] = 105
    with pytest.raises(ValidationError):
        validate_technology(bess_high_eff, "bess")


def test_bess_invalid_cycle_life_zero():
    """BESS з нульовим cycle_life"""
    bess_zero_cycles = valid_bess_default.copy()
    bess_zero_cycles["cycle_life"] = 0
    with pytest.raises(ValidationError):
        validate_technology(bess_zero_cycles, "bess")


# --- негативні тести ID та додаткових полів -----------
@pytest.mark.parametrize("tech", ["pv", "grid", "bess"])
def test_invalid_id_with_spaces(tech):
    """ID з пробілами (заборонено)"""
    instance = {
        "pv": valid_pv,
        "grid": valid_grid,
        "bess": valid_bess_default
    }[tech].copy()

    instance["id"] = "invalid id with spaces"
    with pytest.raises(ValidationError):
        validate_technology(instance, tech)


@pytest.mark.parametrize("tech", ["pv", "grid", "bess"])
def test_invalid_id_with_special_chars(tech):
    """ID зі спеціальними символами (заборонено)"""
    instance = {
        "pv": valid_pv,
        "grid": valid_grid,
        "bess": valid_bess_default
    }[tech].copy()

    instance["id"] = "invalid@id#"
    with pytest.raises(ValidationError):
        validate_technology(instance, tech)


@pytest.mark.parametrize("tech", ["pv", "grid", "bess"])
def test_additional_properties_forbidden(tech):
    """Додаткові властивості заборонені (additionalProperties: false)"""
    instance = {
        "pv": valid_pv,
        "grid": valid_grid,
        "bess": valid_bess_default
    }[tech].copy()

    instance["unknown_property"] = "should_fail"
    with pytest.raises(ValidationError):
        validate_technology(instance, tech)


# --- негативні тести для обов'язкових полів -----------
def test_invalid_pv_missing_required():
    bad = valid_pv.copy()
    bad.pop("dc_power_kw")
    with pytest.raises(ValidationError):
        validate_technology(bad, "pv")


def test_invalid_pv_missing_both_power_fields():
    """PV без dc_power_kw і ac_power_kw"""
    bad = valid_pv.copy()
    bad.pop("dc_power_kw")
    # ac_power_kw не додаємо
    with pytest.raises(ValidationError):
        validate_technology(bad, "pv")


def test_invalid_pv_missing_both_cost_fields():
    """PV без installation_cost_per_kw і total_cost"""
    bad = valid_pv.copy()
    bad.pop("installation_cost_per_kw")
    # total_cost не додаємо
    with pytest.raises(ValidationError):
        validate_technology(bad, "pv")


@pytest.mark.parametrize("field", ["max_import_kw", "tariff_import_profile"])
def test_invalid_grid_missing_required(field):
    bad = valid_grid.copy()
    bad.pop(field)
    with pytest.raises(ValidationError):
        validate_technology(bad, "grid")


@pytest.mark.parametrize("field", ["energy_nominal_kwh", "power_nominal_kw"])
def test_invalid_bess_missing_required(field):
    bad = valid_bess_default.copy()
    bad.pop(field)
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")


def test_bess_degradation_missing_fields():
    bad = valid_bess_fixed.copy()
    bad["degradation"] = {"type": "fixed"}
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")
    bad = valid_bess_custom.copy()
    bad["degradation"] = {"type": "custom"}
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")


def test_bess_degradation_empty_array():
    """BESS з порожнім масивом деградації"""
    bad = valid_bess_custom.copy()
    bad["degradation"]["degradation_pct_per_year"] = []
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")


def test_bess_degradation_invalid_values():
    """BESS з невалідними значеннями деградації"""
    bad = valid_bess_custom.copy()
    bad["degradation"]["degradation_pct_per_year"] = [-1, 101]  # поза діапазоном 0-100
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")


def test_soc_min_gte_soc_max():
    bad = valid_bess_default.copy()
    bad["soc_min_pct"] = 90
    bad["soc_max_pct"] = 10
    with pytest.raises(ValidationError):
        validate_technology(bad, "bess")


# --- тести мета-полів ----------------------------------
@pytest.mark.parametrize("tech", ["pv", "grid", "bess"])
def test_meta_fields_allowed(tech):
    """$schema та $id мета-поля дозволені"""
    instance = {
        "pv": valid_pv,
        "grid": valid_grid,
        "bess": valid_bess_default
    }[tech].copy()

    instance["$schema"] = "http://json-schema.org/draft-07/schema#"
    instance["$id"] = f"https://omspy.tech/schema/technology/{tech}.json"
    validate_technology(instance, tech)  # не повинно падати