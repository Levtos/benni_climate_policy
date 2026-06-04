"""Read-only weather input resolver for effective temperature inputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import (
    CONF_FORECAST_TEMPERATURE,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_OUTDOOR_WIND_SPEED,
    CONF_WEATHER_ENTITY,
    SELF_GENERATED_INPUT_ENTITY_IDS,
)
from .models import Quality

AUTO_WEATHER_ENTITY = "weather.dwd_home"
DEFAULT_FORECAST_CACHE_TTL_SECONDS = 15 * 60
ForecastCache = dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ForecastDiagnostics:
    value: float | None
    source: str
    quality: Quality
    reason: str
    weather_entity: str | None = None
    target_time: str | None = None
    forecast_datetime: str | None = None
    condition: str | None = None
    dew_point: float | None = None
    wind_speed: float | None = None
    precipitation_probability: float | None = None
    fallback_used: bool = False
    cache_hit: bool = False
    cache_age_seconds: float | None = None
    last_fetch_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "quality": self.quality,
            "reason": self.reason,
            "weather_entity": self.weather_entity,
            "target_time": self.target_time,
            "forecast_datetime": self.forecast_datetime,
            "condition": self.condition,
            "dew_point": self.dew_point,
            "wind_speed": self.wind_speed,
            "precipitation_probability": self.precipitation_probability,
            "fallback_used": self.fallback_used,
            "cache_hit": self.cache_hit,
            "cache_age_seconds": self.cache_age_seconds,
            "last_fetch_at": self.last_fetch_at,
        }


@dataclass(frozen=True)
class FeelsLikeDiagnostics:
    value: float | None
    source: str
    quality: Quality
    reason: str
    source_entity_id: str | None = None
    source_entities: dict[str, str | None] = field(default_factory=dict)
    outdoor_humidity: float | None = None
    outdoor_wind_speed: float | None = None
    outdoor_wind_speed_mps: float | None = None
    formula: str | None = None
    fallback_used: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "quality": self.quality,
            "reason": self.reason,
            "source_entity_id": self.source_entity_id,
            "source_entities": dict(self.source_entities),
            "outdoor_humidity": self.outdoor_humidity,
            "outdoor_wind_speed": self.outdoor_wind_speed,
            "outdoor_wind_speed_mps": self.outdoor_wind_speed_mps,
            "formula": self.formula,
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True)
class WeatherResolution:
    forecast_temperature: float | None
    feels_like_temperature: float | None
    forecast: ForecastDiagnostics
    feels_like: FeelsLikeDiagnostics
    floor_slab_tomorrow_temperature: float | None = None
    floor_slab_forecast: ForecastDiagnostics | None = None
    weather_entity_candidates: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "forecast_temperature": self.forecast_temperature,
            "feels_like_temperature": self.feels_like_temperature,
            "floor_slab_tomorrow_temperature": self.floor_slab_tomorrow_temperature,
            "forecast": self.forecast.as_dict(),
            "feels_like": self.feels_like.as_dict(),
            "floor_slab_forecast": self.floor_slab_forecast.as_dict() if self.floor_slab_forecast else None,
            "weather_entity_candidates": list(self.weather_entity_candidates),
        }


def _float(value: Any) -> float | None:
    if value in (None, "", "unknown", "unavailable", "none"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def select_hourly_forecast(
    forecasts: list[Mapping[str, Any]],
    target_time: datetime,
) -> Mapping[str, Any] | None:
    """Return the hourly forecast nearest to the target time."""
    candidates: list[tuple[float, Mapping[str, Any]]] = []
    for item in forecasts:
        if _float(item.get("temperature")) is None:
            continue
        forecast_time = _parse_datetime(item.get("datetime"))
        if forecast_time is None:
            continue
        delta = abs((forecast_time - target_time).total_seconds())
        candidates.append((delta, item))
    if not candidates:
        return None
    return min(candidates, key=lambda pair: pair[0])[1]


def looks_hourly_forecast(forecasts: list[Mapping[str, Any]]) -> bool:
    """Return True if the response shape is plausible for hourly forecasts."""
    times = sorted(
        value
        for value in (_parse_datetime(item.get("datetime")) for item in forecasts)
        if value is not None
    )
    if len(times) < 2:
        return False
    gaps = [
        (later - earlier).total_seconds()
        for earlier, later in zip(times, times[1:])
        if later > earlier
    ]
    return bool(gaps) and min(gaps) <= 7200


def fallback_forecast(real_temperature: float | None, target_time: datetime, reason: str) -> ForecastDiagnostics:
    quality: Quality = "fallback" if real_temperature is not None else "missing"
    return ForecastDiagnostics(
        value=real_temperature,
        source="fallback",
        quality=quality,
        reason=reason if real_temperature is not None else "real_temperature_missing",
        target_time=target_time.isoformat(),
        fallback_used=True,
    )


def fallback_feels_like(real_temperature: float | None, *, reason: str = "fallback_to_real_temperature") -> FeelsLikeDiagnostics:
    if real_temperature is None:
        return FeelsLikeDiagnostics(
            value=None,
            source="missing",
            quality="missing",
            reason="real_temperature_missing",
            fallback_used=False,
        )
    return FeelsLikeDiagnostics(
        value=real_temperature,
        source="fallback_real_temperature",
        quality="fallback",
        reason=reason,
        fallback_used=True,
    )


def wind_speed_to_mps(value: float | None, unit: str | None = None) -> float | None:
    if value is None:
        return None
    unit_text = (unit or "km/h").lower()
    if unit_text in ("m/s", "mps", "meter/s", "meters/s"):
        return value
    if unit_text in ("mph", "mi/h"):
        return value * 0.44704
    if unit_text in ("kn", "kt", "kts", "knots"):
        return value * 0.514444
    return value / 3.6


def apparent_temperature_celsius(temperature: float, relative_humidity: float, wind_speed_mps: float) -> float:
    humidity = max(0.0, min(100.0, relative_humidity))
    vapor_pressure = humidity / 100.0 * 6.105 * math.exp((17.27 * temperature) / (237.7 + temperature))
    apparent = temperature + 0.33 * vapor_pressure - 0.70 * max(0.0, wind_speed_mps) - 4.0
    return round(apparent, 2)


class WeatherResolver:
    """Resolve optional weather-derived effective temperature inputs."""

    def __init__(
        self,
        hass: "HomeAssistant",
        config: Mapping[str, Any],
        *,
        forecast_cache: ForecastCache | None = None,
        forecast_cache_ttl_seconds: int = DEFAULT_FORECAST_CACHE_TTL_SECONDS,
    ) -> None:
        self.hass = hass
        self.config = config
        self.forecast_cache = forecast_cache if forecast_cache is not None else {}
        self.forecast_cache_ttl_seconds = forecast_cache_ttl_seconds

    def _state(self, entity_id: str | None):
        return self.hass.states.get(entity_id) if entity_id else None

    def _external_entity_id(self, entity_id: Any) -> str | None:
        if not isinstance(entity_id, str) or entity_id in SELF_GENERATED_INPUT_ENTITY_IDS:
            return None
        return entity_id

    def _weather_state_available(self, entity_id: str | None) -> bool:
        state = self._state(entity_id)
        return bool(state) and state.state not in (None, "", "unknown", "unavailable")

    def _float_state(self, entity_id: str | None) -> float | None:
        state = self._state(entity_id)
        return _float(state.state if state else None)

    def _weather_entity_candidates(self) -> list[str]:
        configured = self.config.get(CONF_WEATHER_ENTITY)
        if configured and self._weather_state_available(str(configured)):
            return [str(configured)]
        return [AUTO_WEATHER_ENTITY] if self._weather_state_available(AUTO_WEATHER_ENTITY) else []

    async def async_resolve(
        self,
        *,
        real_temperature: float | None,
        now: datetime,
        outdoor_humidity: float | None = None,
        outdoor_wind_speed: float | None = None,
    ) -> WeatherResolution:
        target_time = now + timedelta(hours=3)
        forecast = await self._resolve_forecast(real_temperature=real_temperature, target_time=target_time, now=now)
        tomorrow_target = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        floor_slab_forecast = await self._resolve_floor_slab_forecast(
            real_temperature=real_temperature,
            target_time=tomorrow_target,
            now=now,
        )
        feels_like = self._resolve_feels_like(
            real_temperature=real_temperature,
            outdoor_humidity=outdoor_humidity,
            outdoor_wind_speed=outdoor_wind_speed,
        )
        return WeatherResolution(
            forecast_temperature=forecast.value,
            feels_like_temperature=feels_like.value,
            forecast=forecast,
            feels_like=feels_like,
            floor_slab_tomorrow_temperature=floor_slab_forecast.value,
            floor_slab_forecast=floor_slab_forecast,
            weather_entity_candidates=self._weather_entity_candidates(),
        )

    async def _resolve_forecast(
        self,
        *,
        real_temperature: float | None,
        target_time: datetime,
        now: datetime,
    ) -> ForecastDiagnostics:
        entity_id = self._external_entity_id(self.config.get(CONF_FORECAST_TEMPERATURE))
        entity_value = self._float_state(entity_id)
        if entity_value is not None:
            return ForecastDiagnostics(
                value=entity_value,
                source="entity",
                quality="ok",
                reason="configured_forecast_entity",
                target_time=target_time.isoformat(),
                weather_entity=self.config.get(CONF_WEATHER_ENTITY),
            )

        for weather_entity in self._weather_entity_candidates():
            forecast = await self._resolve_weather_forecast(weather_entity, target_time, now)
            if forecast.quality == "ok":
                return forecast

        reason = "forecast_entity_missing_or_invalid"
        if self._weather_entity_candidates():
            reason = "hourly_weather_forecast_missing"
        return fallback_forecast(real_temperature, target_time, reason)

    async def _resolve_floor_slab_forecast(
        self,
        *,
        real_temperature: float | None,
        target_time: datetime,
        now: datetime,
    ) -> ForecastDiagnostics:
        for weather_entity in self._weather_entity_candidates():
            forecast = await self._resolve_weather_forecast(weather_entity, target_time, now)
            if forecast.quality == "ok":
                return ForecastDiagnostics(
                    **{
                        **forecast.as_dict(),
                        "reason": "floor_slab_tomorrow_noon_forecast" if not forecast.cache_hit else "cached_floor_slab_tomorrow_noon_forecast",
                    }
                )
        return fallback_forecast(real_temperature, target_time, "floor_slab_tomorrow_forecast_missing")

    def _forecast_from_list(
        self,
        forecasts: list[Mapping[str, Any]],
        *,
        weather_entity: str,
        target_time: datetime,
        reason: str,
        cache_hit: bool,
        cache_age_seconds: float | None,
        last_fetch_at: str | None,
    ) -> ForecastDiagnostics:
        if not looks_hourly_forecast(forecasts):
            return ForecastDiagnostics(
                value=None,
                source="weather_forecast",
                quality="degraded",
                reason="hourly_forecast_not_available",
                weather_entity=weather_entity,
                target_time=target_time.isoformat(),
                cache_hit=cache_hit,
                cache_age_seconds=cache_age_seconds,
                last_fetch_at=last_fetch_at,
            )
        selected = select_hourly_forecast(forecasts, target_time)
        if selected is None:
            return ForecastDiagnostics(
                value=None,
                source="weather_forecast",
                quality="degraded",
                reason="no_hourly_forecast_temperature",
                weather_entity=weather_entity,
                target_time=target_time.isoformat(),
                cache_hit=cache_hit,
                cache_age_seconds=cache_age_seconds,
                last_fetch_at=last_fetch_at,
            )

        return ForecastDiagnostics(
            value=_float(selected.get("temperature")),
            source="weather_forecast",
            quality="ok",
            reason=reason,
            weather_entity=weather_entity,
            target_time=target_time.isoformat(),
            forecast_datetime=selected.get("datetime"),
            condition=selected.get("condition"),
            dew_point=_float(selected.get("dew_point")),
            wind_speed=_float(selected.get("wind_speed")),
            precipitation_probability=_float(selected.get("precipitation_probability")),
            fallback_used=False,
            cache_hit=cache_hit,
            cache_age_seconds=cache_age_seconds,
            last_fetch_at=last_fetch_at,
        )

    def _cached_forecasts(self, weather_entity: str, now: datetime) -> tuple[list[Mapping[str, Any]], datetime] | None:
        entry = self.forecast_cache.get(weather_entity)
        if not isinstance(entry, Mapping):
            return None
        fetched_at = entry.get("fetched_at")
        forecasts = entry.get("forecasts")
        if not isinstance(fetched_at, datetime) or not isinstance(forecasts, list):
            return None
        cache_age = (now - fetched_at).total_seconds()
        if cache_age < 0 or cache_age > self.forecast_cache_ttl_seconds:
            return None
        return forecasts, fetched_at

    async def _resolve_weather_forecast(
        self,
        weather_entity: str,
        target_time: datetime,
        now: datetime,
    ) -> ForecastDiagnostics:
        cached = self._cached_forecasts(weather_entity, now)
        if cached is not None:
            forecasts, fetched_at = cached
            return self._forecast_from_list(
                forecasts,
                weather_entity=weather_entity,
                target_time=target_time,
                reason="cached_nearest_hourly_forecast",
                cache_hit=True,
                cache_age_seconds=(now - fetched_at).total_seconds(),
                last_fetch_at=fetched_at.isoformat(),
            )

        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": weather_entity, "type": "hourly"},
                blocking=True,
                return_response=True,
            )
        except Exception:  # noqa: BLE001 - HA service failures degrade to neutral forecast input
            return ForecastDiagnostics(
                value=None,
                source="weather_forecast",
                quality="degraded",
                reason="weather_forecast_service_failed",
                weather_entity=weather_entity,
                target_time=target_time.isoformat(),
            )

        data = response.get(weather_entity) if isinstance(response, Mapping) else None
        forecasts = data.get("forecast") if isinstance(data, Mapping) else None
        if not isinstance(forecasts, list):
            return ForecastDiagnostics(
                value=None,
                source="weather_forecast",
                quality="degraded",
                reason="hourly_forecast_not_available",
                weather_entity=weather_entity,
                target_time=target_time.isoformat(),
            )
        self.forecast_cache[weather_entity] = {
            "fetched_at": now,
            "forecasts": [dict(item) for item in forecasts if isinstance(item, Mapping)],
        }
        return self._forecast_from_list(
            self.forecast_cache[weather_entity]["forecasts"],
            weather_entity=weather_entity,
            target_time=target_time,
            reason="nearest_hourly_forecast",
            cache_hit=False,
            cache_age_seconds=0,
            last_fetch_at=now.isoformat(),
        )

    def _resolve_feels_like(
        self,
        *,
        real_temperature: float | None,
        outdoor_humidity: float | None,
        outdoor_wind_speed: float | None,
    ) -> FeelsLikeDiagnostics:
        humidity_entity = self._external_entity_id(self.config.get(CONF_OUTDOOR_HUMIDITY))
        wind_entity = self._external_entity_id(self.config.get(CONF_OUTDOOR_WIND_SPEED))
        humidity = outdoor_humidity if outdoor_humidity is not None else self._float_state(humidity_entity)
        wind_speed = outdoor_wind_speed if outdoor_wind_speed is not None else self._float_state(wind_entity)
        wind_state = self._state(wind_entity)
        wind_unit = wind_state.attributes.get("unit_of_measurement") if wind_state else None
        wind_mps = wind_speed_to_mps(wind_speed, wind_unit)
        source_entities = {
            "real_temperature": self.config.get(CONF_OUTDOOR_TEMPERATURE),
            "outdoor_humidity": humidity_entity,
            "outdoor_wind_speed": wind_entity,
        }
        if real_temperature is None:
            diag = fallback_feels_like(None)
            return FeelsLikeDiagnostics(**{**diag.as_dict(), "source_entities": source_entities})
        if humidity is None or wind_mps is None:
            diag = fallback_feels_like(real_temperature, reason="raw_humidity_or_wind_missing")
            return FeelsLikeDiagnostics(
                value=diag.value,
                source=diag.source,
                quality="fallback",
                reason=diag.reason,
                source_entities=source_entities,
                outdoor_humidity=humidity,
                outdoor_wind_speed=wind_speed,
                outdoor_wind_speed_mps=wind_mps,
                fallback_used=True,
            )
        return FeelsLikeDiagnostics(
            value=apparent_temperature_celsius(real_temperature, humidity, wind_mps),
            source="computed_apparent_temperature",
            quality="ok",
            reason="computed_from_raw_temperature_humidity_wind",
            source_entities=source_entities,
            outdoor_humidity=humidity,
            outdoor_wind_speed=wind_speed,
            outdoor_wind_speed_mps=round(wind_mps, 3),
            formula="Australian apparent temperature",
            fallback_used=False,
        )
