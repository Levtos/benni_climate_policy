from __future__ import annotations

from datetime import datetime
import pytest

from custom_components.benni_climate_policy.policy import (
    OPT_FLOOR_SLAB_MIN_DELTA,
    OPT_FLOOR_SLAB_MAX_DELTA,
    OPT_SETPOINT_SPAR,
    decide_zone,
    default_policy_tuning,
    indoor_heat_option_key,
    policy_tuning_from_options,
    threshold_option_key,
)
from custom_components.benni_climate_policy.const import CONF_APPLY_ACTIVE
from custom_components.benni_climate_policy.tuning_options import (
    TUNING_SECTIONS,
    active_option_values,
    default_option_values,
    tuning_options_snapshot,
    validated_options_update,
)
from tests.test_policy import ctx, eff, zone


def test_update_options_saves_valid_matrix_values():
    key = threshold_option_key("summer", "off_threshold")
    updated = validated_options_update({}, {key: 21.0})

    assert updated[key] == 21.0
    snapshot = tuning_options_snapshot(updated)
    assert snapshot["values"][key] == 21.0
    assert snapshot["sources"][key] == "user option"


def test_invalid_values_are_rejected_atomically():
    current = {threshold_option_key("summer", "off_threshold"): 20.5}
    with pytest.raises(ValueError):
        validated_options_update(current, {
            threshold_option_key("summer", "comfort_disabled"): False,
            threshold_option_key("summer", "comfort_threshold"): 22.0,
        })

    assert current == {threshold_option_key("summer", "off_threshold"): 20.5}


def test_reset_removes_user_overrides():
    key = threshold_option_key("summer", "off_threshold")
    updated = validated_options_update({}, {key: 21.0})
    reset = validated_options_update(updated, {}, reset_keys=[key])

    assert key not in reset
    assert active_option_values(reset)[key] == default_option_values()[key]
    assert tuning_options_snapshot(reset)["sources"][key] == "default"


def test_update_preserves_unrelated_options():
    key = threshold_option_key("summer", "off_threshold")
    updated = validated_options_update({CONF_APPLY_ACTIVE: True}, {key: 21.0})

    assert updated[CONF_APPLY_ACTIVE] is True


def test_update_options_accepts_source_binding_values():
    updated = validated_options_update(
        {},
        {
            "living_room_thermostat": "climate.eve_thermo_20ebp1701",
            "kitchen_thermostat": "climate.eve_thermo_20ebp1701_2",
            "bathroom_thermostat": "climate.eve_thermo_20ebp1701_3",
        },
    )

    assert updated["living_room_thermostat"] == "climate.eve_thermo_20ebp1701"
    assert updated["kitchen_thermostat"] == "climate.eve_thermo_20ebp1701_2"
    assert updated["bathroom_thermostat"] == "climate.eve_thermo_20ebp1701_3"


def test_update_options_still_rejects_unknown_keys():
    with pytest.raises(ValueError, match="Unbekannte Option"):
        validated_options_update({}, {"made_up_binding": "sensor.anything"})


def test_policy_uses_persisted_matrix_values():
    key = threshold_option_key("summer", "off_threshold")
    options = validated_options_update({}, {key: 21.0})
    plan = decide_zone(
        zone(),
        ctx(),
        eff(20),
        datetime(2026, 7, 1, 12),
        tuning=policy_tuning_from_options(options),
    )

    assert plan.profile == "spar"


def test_plan_hash_changes_after_relevant_tuning_update():
    base = decide_zone(zone(), ctx(), eff(18), datetime(2026, 5, 1, 12), tuning=default_policy_tuning())
    options = validated_options_update({}, {OPT_SETPOINT_SPAR: 20.0})
    tuned = decide_zone(zone(), ctx(), eff(18), datetime(2026, 5, 1, 12), tuning=policy_tuning_from_options(options))

    assert tuned.plan_hash != base.plan_hash
    assert tuned.policy_config_hash != base.policy_config_hash


def test_defaults_stay_when_no_options_are_set():
    assert active_option_values({}) == default_option_values()


def test_panel_service_uses_same_flat_options_structure():
    snapshot = tuning_options_snapshot({})
    service_keys = set().union(*TUNING_SECTIONS.values())

    assert service_keys == set(snapshot["values"])
    assert service_keys == set(snapshot["defaults"])
    assert service_keys == set(snapshot["sources"])


def test_indoor_heat_demand_options_are_validated():
    on_key = indoor_heat_option_key("living_area", "spar", "heat_on_below")
    off_key = indoor_heat_option_key("living_area", "spar", "heat_off_at")

    updated = validated_options_update({}, {on_key: 20.0, off_key: 21.5})
    assert active_option_values(updated)[on_key] == 20.0

    with pytest.raises(ValueError):
        validated_options_update({}, {on_key: 22.0, off_key: 21.5})


def test_floor_slab_delta_bounds_are_validated():
    updated = validated_options_update({}, {OPT_FLOOR_SLAB_MIN_DELTA: 0.2, OPT_FLOOR_SLAB_MAX_DELTA: 1.8})
    assert active_option_values(updated)[OPT_FLOOR_SLAB_MAX_DELTA] == 1.8

    with pytest.raises(ValueError):
        validated_options_update({}, {OPT_FLOOR_SLAB_MIN_DELTA: 2.0, OPT_FLOOR_SLAB_MAX_DELTA: 1.0})
