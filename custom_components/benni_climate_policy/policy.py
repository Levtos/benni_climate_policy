"""Pure climate policy engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import math
from typing import Any, Mapping

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
SETPOINT_OFF = 10.0
SETPOINT_SPAR = 21.0
SETPOINT_KOMFORT = 22.5
BOOST_DELTA = 2.0
SETPOINT_BOOST = SETPOINT_KOMFORT + BOOST_DELTA
FLOOR_SLAB_TAU = 8.0
LUX_BONUS_MAX = 3.0
LUX_REFERENCE = 30000.0
FEELS_LIKE_DAMPING = 0.5
FORECAST_WEIGHT = 0.3
BOOST_ACTIVATION_DELTA = 1.5
NIGHT_RAMP_LATE_EVENING_TARGET = 23.0
NIGHT_RAMP_EARLY_NIGHT_TARGET = 22.0
NIGHT_RAMP_LATE_NIGHT_TARGET = 21.0

OPT_SETPOINT_OFF = "setpoint_off"
OPT_SETPOINT_SPAR = "setpoint_spar"
OPT_SETPOINT_KOMFORT = "setpoint_komfort"
OPT_SETPOINT_BOOST = "setpoint_boost"
OPT_BOOST_DELTA = "boost_delta"
OPT_BOOST_ACTIVATION_DELTA = "boost_activation_delta"
OPT_FLOOR_SLAB_TAU = "floor_slab_tau"
OPT_LUX_BONUS_MAX = "lux_bonus_max"
OPT_LUX_REFERENCE = "lux_reference"
OPT_FEELS_LIKE_DAMPING = "feels_like_damping"
OPT_FORECAST_WEIGHT = "forecast_weight"


@dataclass(frozen=True)
class ThresholdBand:
    months: tuple[int, ...]
    off_threshold: float
    comfort_threshold: float
    boost_threshold: float
    comfort_disabled: bool = False
    boost_disabled: bool = False

    def active_thresholds(self) -> dict[str, float | None]:
        return {
            "off": self.off_threshold,
            "comfort": None if self.comfort_disabled else self.comfort_threshold,
            "boost": None if self.boost_disabled else self.boost_threshold,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "months": list(self.months),
            "off_threshold": self.off_threshold,
            "comfort_threshold": self.comfort_threshold,
            "boost_threshold": self.boost_threshold,
            "comfort_disabled": self.comfort_disabled,
            "boost_disabled": self.boost_disabled,
        }


DEFAULT_THRESHOLD_BANDS: dict[str, ThresholdBand] = {
    "winter": ThresholdBand((12, 1, 2), 15.5, 11.0, 5.0),
    "late_winter": ThresholdBand((3,), 16.0, 11.5, 6.0),
    "spring": ThresholdBand((4,), 17.0, 12.5, 8.0),
    "late_spring": ThresholdBand((5,), 18.5, 14.0, 0.0, boost_disabled=True),
    "summer": ThresholdBand((6, 7, 8), 19.5, 0.0, 0.0, comfort_disabled=True, boost_disabled=True),
    "early_autumn": ThresholdBand((9,), 18.5, 14.0, 0.0, boost_disabled=True),
    "autumn": ThresholdBand((10,), 17.0, 12.5, 8.0),
    "late_autumn": ThresholdBand((11,), 16.0, 11.5, 6.0),
}

TUNING_OPTION_KEYS = (
    OPT_SETPOINT_OFF,
    OPT_SETPOINT_SPAR,
    OPT_SETPOINT_KOMFORT,
    OPT_SETPOINT_BOOST,
    OPT_BOOST_DELTA,
    OPT_BOOST_ACTIVATION_DELTA,
    OPT_FLOOR_SLAB_TAU,
    OPT_LUX_BONUS_MAX,
    OPT_LUX_REFERENCE,
    OPT_FEELS_LIKE_DAMPING,
    OPT_FORECAST_WEIGHT,
)


def threshold_option_key(band: str, field_name: str) -> str:
    return f"threshold_{band}_{field_name}"


def _float_option(
    options: Mapping[str, Any] | None,
    key: str,
    default: float,
    sources: dict[str, str],
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if options is None or key not in options:
        sources[key] = "default"
        return default
    try:
        value = float(options[key])
    except (TypeError, ValueError):
        sources[key] = "invalid_fallback_default"
        return default
    if min_value is not None and value < min_value:
        sources[key] = "invalid_fallback_default"
        return default
    if max_value is not None and value > max_value:
        sources[key] = "invalid_fallback_default"
        return default
    sources[key] = "user option"
    return value


def _bool_option(
    options: Mapping[str, Any] | None,
    key: str,
    default: bool,
    sources: dict[str, str],
) -> bool:
    if options is None or key not in options:
        sources[key] = "default"
        return default
    sources[key] = "user option"
    value = options[key]
    if isinstance(value, str):
        if value.lower() in ("false", "off", "0", "no"):
            return False
        if value.lower() in ("true", "on", "1", "yes"):
            return True
        sources[key] = "invalid_fallback_default"
        return default
    return bool(value)


@dataclass(frozen=True)
class PolicyTuning:
    setpoint_off: float = SETPOINT_OFF
    setpoint_spar: float = SETPOINT_SPAR
    setpoint_komfort: float = SETPOINT_KOMFORT
    setpoint_boost: float = SETPOINT_BOOST
    boost_delta: float = BOOST_DELTA
    boost_activation_delta: float = BOOST_ACTIVATION_DELTA
    floor_slab_tau: float = FLOOR_SLAB_TAU
    lux_bonus_max: float = LUX_BONUS_MAX
    lux_reference: float = LUX_REFERENCE
    feels_like_damping: float = FEELS_LIKE_DAMPING
    forecast_weight: float = FORECAST_WEIGHT
    threshold_bands: dict[str, ThresholdBand] = field(default_factory=lambda: DEFAULT_THRESHOLD_BANDS.copy())
    sources: dict[str, str] = field(default_factory=dict)

    @property
    def signature(self) -> str:
        payload = {
            "setpoints": {
                "off": self.setpoint_off,
                "spar": self.setpoint_spar,
                "komfort": self.setpoint_komfort,
                "boost": self.setpoint_boost,
                "boost_delta": self.boost_delta,
            },
            "boost_activation_delta": self.boost_activation_delta,
            "effective_temperature": {
                "floor_slab_tau": self.floor_slab_tau,
                "lux_bonus_max": self.lux_bonus_max,
                "lux_reference": self.lux_reference,
                "feels_like_damping": self.feels_like_damping,
                "forecast_weight": self.forecast_weight,
            },
            "threshold_bands": {key: band.as_dict() for key, band in sorted(self.threshold_bands.items())},
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def source_for(self, key: str) -> str:
        return self.sources.get(key, "default")


def default_policy_tuning() -> PolicyTuning:
    return policy_tuning_from_options({})


def policy_tuning_from_options(options: Mapping[str, Any] | None) -> PolicyTuning:
    sources: dict[str, str] = {}
    setpoint_komfort = _float_option(options, OPT_SETPOINT_KOMFORT, SETPOINT_KOMFORT, sources, min_value=5.0, max_value=30.0)
    boost_delta = _float_option(options, OPT_BOOST_DELTA, BOOST_DELTA, sources, min_value=0.0, max_value=5.0)
    threshold_bands: dict[str, ThresholdBand] = {}
    for band_key, default in DEFAULT_THRESHOLD_BANDS.items():
        threshold_bands[band_key] = ThresholdBand(
            months=default.months,
            off_threshold=_float_option(
                options,
                threshold_option_key(band_key, "off_threshold"),
                default.off_threshold,
                sources,
                min_value=0.0,
                max_value=35.0,
            ),
            comfort_threshold=_float_option(
                options,
                threshold_option_key(band_key, "comfort_threshold"),
                default.comfort_threshold,
                sources,
                min_value=0.0,
                max_value=35.0,
            ),
            boost_threshold=_float_option(
                options,
                threshold_option_key(band_key, "boost_threshold"),
                default.boost_threshold,
                sources,
                min_value=0.0,
                max_value=35.0,
            ),
            comfort_disabled=_bool_option(
                options,
                threshold_option_key(band_key, "comfort_disabled"),
                default.comfort_disabled,
                sources,
            ),
            boost_disabled=_bool_option(
                options,
                threshold_option_key(band_key, "boost_disabled"),
                default.boost_disabled,
                sources,
            ),
        )
    return PolicyTuning(
        setpoint_off=_float_option(options, OPT_SETPOINT_OFF, SETPOINT_OFF, sources, min_value=5.0, max_value=30.0),
        setpoint_spar=_float_option(options, OPT_SETPOINT_SPAR, SETPOINT_SPAR, sources, min_value=5.0, max_value=30.0),
        setpoint_komfort=setpoint_komfort,
        setpoint_boost=_float_option(
            options,
            OPT_SETPOINT_BOOST,
            setpoint_komfort + boost_delta,
            sources,
            min_value=5.0,
            max_value=30.0,
        ),
        boost_delta=boost_delta,
        boost_activation_delta=_float_option(
            options,
            OPT_BOOST_ACTIVATION_DELTA,
            BOOST_ACTIVATION_DELTA,
            sources,
            min_value=0.0,
            max_value=10.0,
        ),
        floor_slab_tau=_float_option(options, OPT_FLOOR_SLAB_TAU, FLOOR_SLAB_TAU, sources, min_value=0.1, max_value=72.0),
        lux_bonus_max=_float_option(options, OPT_LUX_BONUS_MAX, LUX_BONUS_MAX, sources, min_value=0.0, max_value=10.0),
        lux_reference=_float_option(options, OPT_LUX_REFERENCE, LUX_REFERENCE, sources, min_value=1.0),
        feels_like_damping=_float_option(options, OPT_FEELS_LIKE_DAMPING, FEELS_LIKE_DAMPING, sources, min_value=0.0, max_value=1.0),
        forecast_weight=_float_option(options, OPT_FORECAST_WEIGHT, FORECAST_WEIGHT, sources, min_value=0.0, max_value=1.0),
        threshold_bands=threshold_bands,
        sources=sources,
    )


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
    floor_slab_tau: float = FLOOR_SLAB_TAU,
    lux_bonus_max: float = LUX_BONUS_MAX,
    lux_reference: float = LUX_REFERENCE,
    feels_like_damping: float = FEELS_LIKE_DAMPING,
    forecast_weight: float = FORECAST_WEIGHT,
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
    return threshold_for_month_config(month, default_policy_tuning())


def monthly_band(month: int) -> str:
    for key, band in DEFAULT_THRESHOLD_BANDS.items():
        if month in band.months:
            return key
    return "late_autumn"


def threshold_for_month_config(month: int, tuning: PolicyTuning) -> dict[str, float | None]:
    return tuning.threshold_bands[monthly_band(month)].active_thresholds()


def setpoint_for(profile: str, effective_temperature: float | None, tuning: PolicyTuning | None = None) -> float:
    tuning = tuning or default_policy_tuning()
    if profile == "off":
        return tuning.setpoint_off
    if profile == "boost":
        return min(25.0, max(tuning.setpoint_boost, setpoint_for("komfort", effective_temperature, tuning) + tuning.boost_delta))
    if profile == "komfort":
        target = tuning.setpoint_komfort
        if effective_temperature is not None and effective_temperature <= 5:
            return target + 1.0
        if effective_temperature is not None and effective_temperature <= 12:
            return target + 0.5
        return target
    target = tuning.setpoint_spar
    if effective_temperature is not None and effective_temperature <= 12:
        return target + 0.5
    return target


def night_ramp_target(day_state: str | None) -> float | None:
    if day_state == "late_evening":
        return NIGHT_RAMP_LATE_EVENING_TARGET
    if day_state == "early_night":
        return NIGHT_RAMP_EARLY_NIGHT_TARGET
    if day_state == "late_night":
        return NIGHT_RAMP_LATE_NIGHT_TARGET
    return None


def policy_visibility_snapshot(
    month: int,
    effective_temperature: float | None,
    tuning: PolicyTuning | None = None,
) -> dict[str, object]:
    tuning = tuning or default_policy_tuning()
    band_key = monthly_band(month)
    thresholds = threshold_for_month_config(month, tuning)
    band_fields = (
        "off_threshold",
        "comfort_threshold",
        "boost_threshold",
        "comfort_disabled",
        "boost_disabled",
    )
    return {
        "month": month,
        "active_month_band": band_key,
        "thresholds": thresholds,
        "comfort_structurally_disabled": thresholds["comfort"] is None,
        "boost_structurally_disabled": thresholds["boost"] is None,
        "setpoints": {
            "off": setpoint_for("off", effective_temperature, tuning),
            "spar": setpoint_for("spar", effective_temperature, tuning),
            "komfort": setpoint_for("komfort", effective_temperature, tuning),
            "boost": setpoint_for("boost", effective_temperature, tuning),
        },
        "hysteresis": {
            "boost_activation_delta": tuning.boost_activation_delta,
            "boost_delta": tuning.boost_delta,
        },
        "effective_temperature_parameters": {
            "floor_slab_tau": tuning.floor_slab_tau,
            "lux_bonus_max": tuning.lux_bonus_max,
            "lux_reference": tuning.lux_reference,
            "feels_like_damping": tuning.feels_like_damping,
            "forecast_weight": tuning.forecast_weight,
        },
        "sources": {
            "setpoints": {
                "off": tuning.source_for(OPT_SETPOINT_OFF),
                "spar": tuning.source_for(OPT_SETPOINT_SPAR),
                "komfort": tuning.source_for(OPT_SETPOINT_KOMFORT),
                "boost": tuning.source_for(OPT_SETPOINT_BOOST),
            },
            "hysteresis": {
                "boost_activation_delta": tuning.source_for(OPT_BOOST_ACTIVATION_DELTA),
                "boost_delta": tuning.source_for(OPT_BOOST_DELTA),
            },
            "effective_temperature_parameters": {
                "floor_slab_tau": tuning.source_for(OPT_FLOOR_SLAB_TAU),
                "lux_bonus_max": tuning.source_for(OPT_LUX_BONUS_MAX),
                "lux_reference": tuning.source_for(OPT_LUX_REFERENCE),
                "feels_like_damping": tuning.source_for(OPT_FEELS_LIKE_DAMPING),
                "forecast_weight": tuning.source_for(OPT_FORECAST_WEIGHT),
            },
            "active_threshold_band": {
                field_name: tuning.source_for(threshold_option_key(band_key, field_name))
                for field_name in band_fields
            },
        },
        "threshold_bands": {
            key: {
                **band.as_dict(),
                "active_thresholds": band.active_thresholds(),
                "sources": {
                    field_name: tuning.source_for(threshold_option_key(key, field_name))
                    for field_name in band_fields
                },
            }
            for key, band in tuning.threshold_bands.items()
        },
        "tuning_signature": tuning.signature,
    }


def decide_zone(
    zone_input: ZoneInput,
    ctx: ClimateContextSnapshot,
    effective: EffectiveTemperatureBreakdown,
    now: datetime,
    *,
    tuning: PolicyTuning | None = None,
) -> ZonePlan:
    path: list[str] = []
    blockers: list[str] = []
    tuning = tuning or default_policy_tuning()
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
    target_override: float | None = None

    if bio in ("sleep", "waking"):
        profile = "off"
        reason = f"bio_{bio}_forces_off"
        path.append(reason)
    elif any(w.blocks_heating_at(now, immediate=day_state in ("early_night", "late_night")) for w in zone_input.windows):
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
            target_override = NIGHT_RAMP_EARLY_NIGHT_TARGET
            path.append(reason)
        elif day_state in ("late_evening", "early_night", "late_night", "night") and month not in SUMMER_MONTHS:
            if day_state == "night":
                profile = "spar"
                reason = "night_hard_spar"
            else:
                target_override = night_ramp_target(day_state)
                profile = "spar" if target_override == NIGHT_RAMP_LATE_NIGHT_TARGET else "komfort"
                reason = f"night_temperature_ramp_{day_state}"
            path.append(reason)
        else:
            thresholds = threshold_for_month_config(month, tuning)
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
                comfort_target = setpoint_for("komfort", teff, tuning)
                room_temp = zone_input.room_temperature
                if (
                    boost_threshold is not None
                    and teff <= float(boost_threshold)
                    and room_temp is not None
                    and room_temp <= comfort_target - tuning.boost_activation_delta
                ):
                    profile = "boost"
                    reason = "boost_threshold_and_room_delta"
            path.append(reason)

        if preheat and presence_band == "preheat" and profile in ("komfort", "boost"):
            profile = "spar"
            reason = "presence_preheat_caps_to_spar"
            path.append(reason)

    target = target_override if target_override is not None else setpoint_for(profile, teff, tuning)
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
        policy_config_hash=tuning.signature,
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

