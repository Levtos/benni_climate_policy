from __future__ import annotations

from pathlib import Path


SENSOR_SOURCE = Path("custom_components/benni_climate_policy/sensor.py").read_text(encoding="utf-8")
FRONTEND_SOURCE = Path("custom_components/benni_climate_policy/frontend/app/main.js").read_text(encoding="utf-8")


def _class_source(class_name: str) -> str:
    marker = f"class {class_name}"
    start = SENSOR_SOURCE.index(marker)
    next_class = SENSOR_SOURCE.find("\nclass ", start + len(marker))
    return SENSOR_SOURCE[start:] if next_class == -1 else SENSOR_SOURCE[start:next_class]


def test_weather_resolver_temperature_sensors_are_registered():
    assert "ForecastTemperature3hSensor(coord)" in SENSOR_SOURCE
    assert "OutdoorFeelsLikeTemperatureSensor(coord)" in SENSOR_SOURCE
    assert '"Climate Forecast Temperature 3h", "forecast_temperature_3h"' in SENSOR_SOURCE
    assert '"Climate Outdoor Feels Like Temperature", "outdoor_feels_like_temperature"' in SENSOR_SOURCE


def test_weather_resolver_temperature_sensors_use_temperature_device_class_without_state_class():
    forecast = _class_source("ForecastTemperature3hSensor")
    feels_like = _class_source("OutdoorFeelsLikeTemperatureSensor")

    for source in (forecast, feels_like):
        assert "_attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS" in source
        assert "_attr_device_class = SensorDeviceClass.TEMPERATURE" in source
        assert "_attr_state_class" not in source


def test_weather_resolver_sensor_attributes_are_compact():
    forecast = _class_source("ForecastTemperature3hSensor")
    feels_like = _class_source("OutdoorFeelsLikeTemperatureSensor")

    for key in ("source", "weather_entity", "quality", "fallback_used", "reason", "target_time", "forecast_time"):
        assert f'"{key}"' in forecast
    assert '"forecast"' not in forecast
    assert "forecast_datetime" in forecast

    for key in ("source", "source_entity_id", "quality", "fallback_used", "reason"):
        assert f'"{key}"' in feels_like
    assert '"weather_entity"' not in feels_like
    assert '"forecast"' not in feels_like


def test_panel_links_weather_resolver_temperature_sensors():
    assert 'forecastTemp3h: "sensor.climate_forecast_temperature_3h"' in FRONTEND_SOURCE
    assert 'outdoorFeelsLike: "sensor.climate_outdoor_feels_like_temperature"' in FRONTEND_SOURCE
    assert 'metric("Forecast +3h", stateText(hass, ENTITIES.forecastTemp3h), ENTITIES.forecastTemp3h)' in FRONTEND_SOURCE
    assert 'metric("Gefühlte Außentemperatur", stateText(hass, ENTITIES.outdoorFeelsLike), ENTITIES.outdoorFeelsLike)' in FRONTEND_SOURCE
