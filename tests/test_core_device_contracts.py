from __future__ import annotations

from pathlib import Path


CONST_SOURCE = Path("custom_components/benni_climate_policy/const.py").read_text(encoding="utf-8")
INIT_SOURCE = Path("custom_components/benni_climate_policy/__init__.py").read_text(encoding="utf-8")


def test_room_humidity_presets_use_core_device_entities():
    assert '"sensor.living_humidity_atomic"' not in CONST_SOURCE
    assert '"sensor.kitchen_humidity_atomic"' not in CONST_SOURCE
    assert '"sensor.bath_humidity_atomic"' not in CONST_SOURCE
    assert '"sensor.benni_device_living_climate"' in CONST_SOURCE
    assert '"sensor.benni_device_kitchen_climate"' in CONST_SOURCE
    assert '"sensor.benni_device_bath_climate"' in CONST_SOURCE


def test_window_presets_use_openings_master_entity():
    assert '"sensor.benni_device_living_window_left"' not in CONST_SOURCE
    assert '"sensor.benni_device_living_window_right"' not in CONST_SOURCE
    assert '"sensor.benni_device_kitchen_patio_door"' not in CONST_SOURCE
    assert CONST_SOURCE.count('"sensor.benni_combined_openings"') >= 1


def test_legacy_humidity_atomics_migrate_to_core_devices():
    for old, new in {
        "sensor.living_humidity_atomic": "sensor.benni_device_living_climate",
        "sensor.kitchen_humidity_atomic": "sensor.benni_device_kitchen_climate",
        "sensor.bath_humidity_atomic": "sensor.benni_device_bath_climate",
    }.items():
        assert f'"{old}": "{new}"' in INIT_SOURCE


def test_legacy_window_entities_migrate_to_openings_master():
    for old in (
        "binary_sensor.living_window_left_open_atomic",
        "binary_sensor.living_window_left_tilt_atomic",
        "binary_sensor.living_window_right_open_atomic",
        "binary_sensor.living_window_right_tilt_atomic",
        "binary_sensor.kitchen_patio_door_open_atomic",
        "binary_sensor.kitchen_patio_door_tilt_atomic",
        "sensor.benni_device_living_window_left",
        "sensor.benni_device_living_window_right",
        "sensor.benni_device_kitchen_patio_door",
    ):
        assert f'"{old}": CORE_OPENINGS_MASTER_ENTITY' in INIT_SOURCE
