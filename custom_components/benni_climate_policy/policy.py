"""Pure climate policy engine."""
from __future__ import annotations

from datetime import datetime, timedelta
import math

from .models import (
    ClimateContextSnapshot,
    EffectiveTemperatureBreakdown,
    EffectiveTemperatureInput,
    SourceValue,
    ZoneInput,
    ZonePlan,
)

SUMMER_MONTHS = {6, 7, 8}
BOOST_DISABLED_MONTHS = {5, 6, 7, 8, 9}


def _to_bool(value: object) -> bool:
    return value in (True, "on", "true", "True", "aktiv", "active", "1")


def _context_value(ctx: ClimateContextSnapshot, field: str, default: str | None = None) -> str | None:
    value = getattr(ctx, field).value
    if value in (None, "", "unknown", "unavailable"):
        return default
    return str(value)


def effective_outdoor_temperature(
    inp: EffectiveTemperatureInput,
    *,
    floor_slab_tau: float = 8.0,
    lux_bonus_max: float = 3.0,
    lux_reference: float = 30000.0,
    feels_like_damping: float = 0.5,
    forecast_weight: float = 0.3,
) -> EffectiveTemperatureBreakdown:
    """Calculate the Opus-style effective outdoor temperature."""
    real = inp.real_temperature
    if real is None:
        return EffectiveTemperatureBreakdown(None, 0, 0, 0, 0, 0, None, "missing")

    floor_offset = 0.0
    if real < 15.0:
        floor_offset = -2.7 * (1.0 - math.exp(-(15.0 - real) / max(floor_slab_tau, 0.1)))

    feels_offset = 0.0
    if inp.feels_like_temperature is not None:
        feels_offset = (inp.feels_like_temperature - real) * feels_like_damping
        feels_offset = max(-3.0, min(3.0, feels_offset))

    lux_bonus = 0.0
    if (inp.sun_elevation or 0.0) >= 5.0 and (inp.outdoor_lux or 0.0) > 0.0:
        lux_bonus = min(lux_bonus_max, lux_bonus_max * ((inp.outdoor_lux or 0.0) / lux_reference))

    condition = (inp.weather_condition or "neutral").lower()
    weather_base = {
        "sunny": 0.0,
        "partlycloudy": 0.0,
        "cloudy": 0.0,
        "rainy": -1.5,
        "pouring": -2.5,
        "snowy": -3.5,
        "snowy-rainy": -3.0,
        "fog": -1.0,
        "windy": -1.5,
        "windy-variant": -2.0,
    }.get(condition, 0.0)
    if condition == "sunny":
        weather_offset = weather_base + lux_bonus
    elif condition == "partlycloudy":
        weather_offset = weather_base + lux_bonus * 0.5
    else:
        weather_offset = weather_base

    forecast_offset = 0.0
    if inp.forecast_temperature is not None:
        forecast_offset = (inp.forecast_temperature - real) * forecast_weight
        forecast_offset = max(-1.5, min(1.5, forecast_offset))

    effective = real + floor_offset + feels_offset + weather_offset + forecast_offset
    quality = "ok"
    if inp.feels_like_temperature is None or inp.forecast_temperature is None:
        quality = "degraded"
    return EffectiveTemperatureBreakdown(
        real_temperature=round(real, 2),
        floor_slab_offset=round(floor_offset, 2),
        feels_like_offset=round(feels_offset, 2),
        weather_offset=round(weather_offset, 2),
        forecast_offset=round(forecast_offset, 2),
        lux_bonus=round(lux_bonus, 2),
        effective_temperature=round(effective, 2),
        input_quality=quality,
    )


def threshold_for_month(month: int) -> dict[str, float | None]:
    if month in (12, 1, 2):
        return {"off": 15.5, "comfort": 11.0, "boost": 5.0}
    if month == 3:
        return {"off": 16.0, "comfort": 11.5, "boost": 6.0}
    if month == 4:
        return {"off": 17.0, "comfort": 12.5, "boost": 8.0}
    if month == 5:
        return {"off": 18.5, "comfort": 14.0, "boost": None}
    if month in SUMMER_MONTHS:
        return {"off": 19.5, "comfort": None, "boost": None}
    if month == 9:
        return {"off": 18.5, "comfort": 14.0, "boost": None}
    if month == 10:
        return {"off": 17.0, "comfort": 12.5, "boost": 8.0}
    return {"off": 16.0, "comfort": 11.5, "boost": 6.0}


def setpoint_for(profile: str, effective_temperature: float | None) -> float:
    if profile == "off":
        return 10.0
    if profile == "boost":
        return min(25.0, setpoint_for("komfort", effective_temperature) + 2.0)
    if profile == "komfort":
        if effective_temperature is not None and effective_temperature <= 5:
            return 23.5
        if effective_temperature is not None and effective_temperature <= 12:
            return 23.0
        return 22.5
    if effective_temperature is not None and effective_temperature <= 12:
        return 21.5
    return 21.0


def decide_zone(
    zone_input: ZoneInput,
    ctx: ClimateContextSnapshot,
    effective: EffectiveTemperatureBreakdown,
    now: datetime,
    *,
    boost_activation_delta: float = 1.5,
) -> ZonePlan:
    path: list[str] = []
    blockers: list[str] = []
    month = now.month
    teff = effective.effective_temperature

    bio = _context_value(ctx, "bio_state", "sleep")
    presence_band = _context_value(ctx, "presence_band", "far")
    transition = _context_value(ctx, "presence_transition", "none")
    activity = _context_value(ctx, "activity_state", "idle")
    day_state = _context_value(ctx, "day_state", "late_night")
    preheat = _to_bool(ctx.presence_preheat_active.value)

    source_entities = [
        v.source_entity_id
        for v in (
            ctx.bio_state,
            ctx.presence_band,
            ctx.presence_transition,
            ctx.activity_state,
            ctx.day_state,
        )
        if v.source_entity_id
    ]

    profile = "spar"
    reason = "threshold_profile"

    if bio in ("sleep", "waking"):
        profile = "off"
        reason = f"bio_{bio}_forces_off"
        path.append(reason)
    elif any(w.blocks_heating for w in zone_input.windows):
        profile = "off"
        reason = "window_blocks_heating"
        path.append(reason)
    elif presence_band == "far":
        profile = "off"
        reason = "presence_far_forces_off"
        path.append(reason)
    elif presence_band == "preheat" and transition == "passing_through":
        profile = "off"
        reason = "passing_through_blocks_preheat"
        path.append(reason)
    else:
        wake_value = ctx.planned_wakeup_time.value
        if isinstance(wake_value, datetime) and now >= wake_value - timedelta(hours=8):
            profile = "off"
            reason = "dynamic_wakeup_cutoff"
            path.append(reason)
        elif activity == "free_time" and day_state == "early_night" and month not in SUMMER_MONTHS:
            profile = "komfort"
            reason = "free_time_early_night_holds_comfort"
            path.append(reason)
        else:
            thresholds = threshold_for_month(month)
            if teff is None:
                profile = "spar"
                reason = "effective_temperature_missing_spar"
            elif teff >= float(thresholds["off"]):
                profile = "off"
                reason = "effective_temperature_above_off_threshold"
            elif month in SUMMER_MONTHS:
                profile = "spar"
                reason = "summer_june_july_august_only_off_or_spar"
            elif thresholds["comfort"] is None or teff > float(thresholds["comfort"]):
                profile = "spar"
                reason = "effective_temperature_in_spar_band"
            else:
                profile = "komfort"
                reason = "effective_temperature_in_comfort_band"
                boost_threshold = thresholds["boost"]
                comfort_target = setpoint_for("komfort", teff)
                room_temp = zone_input.room_temperature
                if (
                    boost_threshold is not None
                    and month not in BOOST_DISABLED_MONTHS
                    and teff <= float(boost_threshold)
                    and room_temp is not None
                    and room_temp <= comfort_target - boost_activation_delta
                ):
                    profile = "boost"
                    reason = "boost_threshold_and_room_delta"
            path.append(reason)

        if preheat and presence_band == "preheat" and profile in ("komfort", "boost"):
            profile = "spar"
            reason = "presence_preheat_caps_to_spar"
            path.append(reason)

    target = setpoint_for(profile, teff)
    if not zone_input.thermostat_entity_id:
        blockers.append("thermostat_entity_missing")

    quality = "ok"
    if effective.input_quality != "ok":
        quality = effective.input_quality
    if teff is None:
        blockers.append("effective_temperature_missing")
        quality = "missing"

    return ZonePlan(
        zone=zone_input.zone,
        profile=profile,  # type: ignore[arg-type]
        target_temperature=target,
        raw_target_temperature=target,
        reason=reason,
        decision_path=path,
        blocked_by=blockers,
        source_entities=source_entities,
        input_quality=quality,  # type: ignore[arg-type]
        effective_outdoor_temperature=teff,
        is_boost_active=profile == "boost",
        hysteresis_state=profile,
        last_calculated=now.isoformat(),
        apply_block_reason=", ".join(blockers) if blockers else "none",
    )


def empty_context() -> ClimateContextSnapshot:
    missing = SourceValue(None, None, "missing", False)
    return ClimateContextSnapshot(
        activity_state=missing,
        bio_state=missing,
        day_context=missing,
        day_state=missing,
        presence_band=missing,
        presence_household=missing,
        presence_personal=missing,
        presence_preheat_active=missing,
        presence_transition=missing,
        workday_state=missing,
        planned_wakeup_time=missing,
    )

