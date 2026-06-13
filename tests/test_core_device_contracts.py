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


def test_legacy_humidity_atomics_migrate_to_core_devices():
    for old, new in {
        "sensor.living_humidity_atomic": "sensor.benni_device_living_climate",
        "sensor.kitchen_humidity_atomic": "sensor.benni_device_kitchen_climate",
        "sensor.bath_humidity_atomic": "sensor.benni_device_bath_climate",
    }.items():
        assert f'"{old}": "{new}"' in INIT_SOURCE
