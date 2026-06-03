from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from custom_components.benni_climate_policy.const import (
    CONF_FORECAST_TEMPERATURE,
    CONF_OUTDOOR_FEELS_LIKE,
    CONF_WEATHER_ENTITY,
)
from custom_components.benni_climate_policy.weather_resolver import (
    AUTO_WEATHER_ENTITY,
    DEFAULT_FORECAST_CACHE_TTL_SECONDS,
    WeatherResolver,
    fallback_feels_like,
    fallback_forecast,
    looks_hourly_forecast,
    select_hourly_forecast,
)


class _State:
    def __init__(self, state):
        self.state = state
        self.attributes = {}


class _States:
    def __init__(self, values):
        self._values = values

    def get(self, entity_id):
        if entity_id not in self._values:
            return None
        return _State(self._values[entity_id])


class _Services:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def async_call(self, domain, service, data, *, blocking, return_response):
        self.calls.append({
            "domain": domain,
            "service": service,
            "data": data,
            "blocking": blocking,
            "return_response": return_response,
        })
        return self.response


class _Hass:
    def __init__(self, states, response=None):
        self.states = _States(states)
        self.services = _Services(response or {})


def _run(coro):
    return asyncio.run(coro)


def test_user_configured_forecast_entity_has_priority():
    hass = _Hass(
        {
            "sensor.forecast_3h": "12.5",
            AUTO_WEATHER_ENTITY: "rainy",
        },
        {
            AUTO_WEATHER_ENTITY: {
                "forecast": [
                    {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 1.0},
                    {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 2.0},
                ]
            }
        },
    )

    result = _run(WeatherResolver(hass, {CONF_FORECAST_TEMPERATURE: "sensor.forecast_3h"}).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert result.forecast_temperature == 12.5
    assert result.forecast.source == "entity"
    assert hass.services.calls == []


def test_user_configured_feels_like_entity_has_priority():
    hass = _Hass({"sensor.feels": "8.5"})

    result = _run(WeatherResolver(hass, {CONF_OUTDOOR_FEELS_LIKE: "sensor.feels"}).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert result.feels_like_temperature == 8.5
    assert result.feels_like.source == "entity"
    assert result.feels_like.fallback_used is False


def test_forecast_3h_is_resolved_from_hourly_weather_forecast():
    forecasts = [
        {"datetime": "2026-06-02T16:00:00+00:00", "temperature": 15.0, "condition": "cloudy"},
        {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 16.0, "condition": "rainy"},
        {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 17.0, "condition": "rainy"},
    ]
    hass = _Hass(
        {AUTO_WEATHER_ENTITY: "rainy"},
        {AUTO_WEATHER_ENTITY: {"forecast": forecasts}},
    )

    result = _run(WeatherResolver(hass, {}).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, 40, tzinfo=timezone.utc),
    ))

    assert result.forecast_temperature == 17.0
    assert result.forecast.source == "weather_forecast"
    assert result.forecast.weather_entity == AUTO_WEATHER_ENTITY
    assert result.forecast.reason == "nearest_hourly_forecast"
    assert hass.services.calls[0]["data"] == {"entity_id": AUTO_WEATHER_ENTITY, "type": "hourly"}


def test_weather_forecast_service_response_is_cached_between_resolver_runs():
    forecasts = [
        {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 16.0},
        {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 17.0},
        {"datetime": "2026-06-02T19:00:00+00:00", "temperature": 18.0},
    ]
    hass = _Hass(
        {AUTO_WEATHER_ENTITY: "rainy"},
        {AUTO_WEATHER_ENTITY: {"forecast": forecasts}},
    )
    cache = {}

    first = _run(WeatherResolver(hass, {}, forecast_cache=cache).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
    ))
    second = _run(WeatherResolver(hass, {}, forecast_cache=cache).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, 5, tzinfo=timezone.utc),
    ))

    assert len(hass.services.calls) == 1
    assert first.forecast.cache_hit is False
    assert second.forecast.cache_hit is True
    assert second.forecast.reason == "cached_nearest_hourly_forecast"
    assert second.forecast.cache_age_seconds == 300
    assert second.forecast.last_fetch_at == "2026-06-02T14:00:00+00:00"


def test_stale_weather_forecast_cache_is_refetched():
    forecasts = [
        {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 16.0},
        {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 17.0},
    ]
    hass = _Hass(
        {AUTO_WEATHER_ENTITY: "rainy"},
        {AUTO_WEATHER_ENTITY: {"forecast": forecasts}},
    )
    cache = {}

    _run(WeatherResolver(hass, {}, forecast_cache=cache).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc),
    ))
    _run(WeatherResolver(hass, {}, forecast_cache=cache).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, 0, tzinfo=timezone.utc)
        + timedelta(seconds=DEFAULT_FORECAST_CACHE_TTL_SECONDS + 1),
    ))

    assert len(hass.services.calls) == 2


def test_nearest_forecast_point_to_now_plus_3h_is_selected():
    target = datetime(2026, 6, 2, 17, 40, tzinfo=timezone.utc)
    forecasts = [
        {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 17.0},
        {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 18.0},
        {"datetime": "2026-06-02T19:00:00+00:00", "temperature": 19.0},
    ]

    selected = select_hourly_forecast(forecasts, target)

    assert selected["temperature"] == 18.0


def test_daily_forecast_shape_is_not_treated_as_3h_forecast():
    daily = [
        {"datetime": "2026-06-02T00:00:00+00:00", "temperature": 20.0},
        {"datetime": "2026-06-03T00:00:00+00:00", "temperature": 21.0},
    ]
    hass = _Hass(
        {CONF_WEATHER_ENTITY: "weather.dwd_home", "weather.dwd_home": "rainy"},
        {"weather.dwd_home": {"forecast": daily}},
    )

    result = _run(WeatherResolver(hass, {CONF_WEATHER_ENTITY: "weather.dwd_home"}).async_resolve(
        real_temperature=10.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert looks_hourly_forecast(daily) is False
    assert result.forecast_temperature == 10.0
    assert result.forecast.source == "fallback"
    assert result.forecast.reason == "hourly_weather_forecast_missing"


def test_missing_forecast_uses_neutral_fallback():
    hass = _Hass({})

    result = _run(WeatherResolver(hass, {}).async_resolve(
        real_temperature=11.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert result.forecast_temperature == 11.0
    assert result.forecast.source == "fallback"
    assert result.forecast.fallback_used is True


def test_unavailable_weather_entity_does_not_call_forecast_service():
    hass = _Hass(
        {AUTO_WEATHER_ENTITY: "unavailable"},
        {AUTO_WEATHER_ENTITY: {"forecast": [
            {"datetime": "2026-06-02T17:00:00+00:00", "temperature": 15.0},
            {"datetime": "2026-06-02T18:00:00+00:00", "temperature": 16.0},
        ]}},
    )

    result = _run(WeatherResolver(hass, {}).async_resolve(
        real_temperature=11.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert hass.services.calls == []
    assert result.forecast_temperature == 11.0
    assert result.forecast.source == "fallback"
    assert result.forecast.reason == "forecast_entity_missing_or_invalid"


def test_configured_unavailable_weather_entity_does_not_call_forecast_service():
    hass = _Hass({"weather.dwd_home": "unavailable"})

    result = _run(WeatherResolver(hass, {CONF_WEATHER_ENTITY: "weather.dwd_home"}).async_resolve(
        real_temperature=12.0,
        now=datetime(2026, 6, 2, 14, tzinfo=timezone.utc),
    ))

    assert hass.services.calls == []
    assert result.forecast_temperature == 12.0
    assert result.forecast.source == "fallback"


def test_missing_feels_like_uses_real_temperature_fallback():
    result = fallback_feels_like(9.0)

    assert result.value == 9.0
    assert result.source == "fallback_real_temperature"
    assert result.reason == "fallback_to_real_temperature"
    assert result.fallback_used is True


def test_fallback_diagnostics_are_visible_and_compact():
    target = datetime(2026, 6, 2, 17, tzinfo=timezone.utc)
    forecast = fallback_forecast(12.0, target, "hourly_weather_forecast_missing")
    feels_like = fallback_feels_like(12.0)

    assert forecast.as_dict()["source"] == "fallback"
    assert forecast.as_dict()["fallback_used"] is True
    assert feels_like.as_dict()["source"] == "fallback_real_temperature"
    assert "forecast" not in forecast.as_dict()
