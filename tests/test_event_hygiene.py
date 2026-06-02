from __future__ import annotations

from pathlib import Path


ENTITY_SOURCE = Path("custom_components/benni_climate_policy/entity.py").read_text(encoding="utf-8")
SENSOR_SOURCE = Path("custom_components/benni_climate_policy/sensor.py").read_text(encoding="utf-8")
COORDINATOR_SOURCE = Path("custom_components/benni_climate_policy/coordinator.py").read_text(encoding="utf-8")

def _function_source(source: str, function_name: str) -> str:
    marker = f"def {function_name}"
    start = source.index(marker)
    next_def = source.find("\ndef ", start + len(marker))
    next_class = source.find("\nclass ", start + len(marker))
    candidates = [idx for idx in (next_def, next_class) if idx != -1]
    end = min(candidates) if candidates else len(source)
    return source[start:end]


def _method_source(source: str, method_name: str) -> str:
    marker = f"    async def {method_name}"
    start = source.index(marker)
    next_method = source.find("\n    def ", start + len(marker))
    next_async_method = source.find("\n    async def ", start + len(marker))
    candidates = [idx for idx in (next_method, next_async_method) if idx != -1]
    end = min(candidates) if candidates else len(source)
    return source[start:end]


def test_entity_update_handler_deduplicates_published_payloads():
    assert "_last_published_payload" in ENTITY_SOURCE
    assert "payload == self._last_published_payload" in ENTITY_SOURCE
    assert "return" in _function_source(ENTITY_SOURCE, "_handle_update")
    assert "async_write_ha_state()" in _function_source(ENTITY_SOURCE, "_handle_update")
    assert "json.dumps(payload, sort_keys=True" in ENTITY_SOURCE


def test_normal_plan_sensor_attributes_do_not_publish_last_calculated():
    zone_attrs = _function_source(SENSOR_SOURCE, "_compact_zone_plan")
    fan_attrs = _function_source(SENSOR_SOURCE, "_compact_fan_plan")

    assert "last_calculated" not in zone_attrs
    assert "last_calculated" not in fan_attrs


def test_coordinator_uses_15_minute_interval_not_short_polling():
    assert "async_track_time_interval" in COORDINATOR_SOURCE
    assert "timedelta(minutes=15)" in COORDINATOR_SOURCE
    assert "timedelta(seconds=1)" not in COORDINATOR_SOURCE
    assert "timedelta(seconds=3)" not in COORDINATOR_SOURCE


def test_dry_run_does_not_force_recalculate_loop():
    apply_source = _method_source(COORDINATOR_SOURCE, "async_apply")

    assert "dry_run: bool" in apply_source
    assert "await self.async_evaluate(auto_apply=False)" in apply_source
    assert apply_source.count("await self.async_evaluate(auto_apply=False)") == 1
    assert apply_source.count("self._notify()") <= 2
    assert "return self.last_apply_result" in apply_source


def test_weather_resolver_sensor_tests_guard_against_forecast_lists_in_attributes():
    forecast_sensor = SENSOR_SOURCE[SENSOR_SOURCE.index("class ForecastTemperature3hSensor"):SENSOR_SOURCE.index("class OutdoorFeelsLikeTemperatureSensor")]
    feels_like_sensor = SENSOR_SOURCE[SENSOR_SOURCE.index("class OutdoorFeelsLikeTemperatureSensor"):SENSOR_SOURCE.index("class ApplyStatusSensor")]

    assert '"forecast"' not in forecast_sensor
    assert '"forecast"' not in feels_like_sensor
    assert "forecast_time" in forecast_sensor
