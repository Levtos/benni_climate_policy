"""Validation and snapshots for persisted climate policy tuning options."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .bathroom import (
    OPT_BATH_AH_DELTA_AFTERRUN_OFF,
    OPT_BATH_AH_DELTA_AFTERRUN_ON,
    OPT_BATH_AH_DELTA_STOSS,
    OPT_BATH_COMFORT_SUPPRESSION_TEFF,
    OPT_BATH_DEWPOINT_ACUTE_THRESHOLD,
    OPT_BATH_FAN_ACUTE_MAX_MINUTES,
    OPT_BATH_FAN_AFTERRUN_MAX_MINUTES,
    OPT_BATH_FAN_HEAT_COORDINATION_DELTA,
    OPT_BATH_FAN_STOSS_DURATION_MINUTES,
    OPT_BATH_FAN_STOSS_INTERVAL_HOURS,
    OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD,
    OPT_BATH_HUMIDITY_ACUTE_THRESHOLD,
    OPT_BATH_HUMIDITY_END_THRESHOLD,
    OPT_BATH_SETPOINT_COMFORT,
    OPT_BATH_SETPOINT_GROUND,
    OPT_BATH_SETPOINT_PROTECTION,
    bath_tuning_from_options,
)
from .const import (
    CONF_APPLY_COOLDOWN_SECONDS,
    CONF_BATH_FAN,
    CONF_BATH_SHOWER_ACTIVITY,
    CONF_BATH_TOILET_ACTIVITY,
    CONF_CONTEXT_ACTIVITY,
    CONF_CONTEXT_BIO,
    CONF_CONTEXT_DAY_CONTEXT,
    CONF_CONTEXT_DAY_STATE,
    CONF_CONTEXT_PRESENCE_BAND,
    CONF_CONTEXT_PRESENCE_HOUSEHOLD,
    CONF_CONTEXT_PRESENCE_PERSONAL,
    CONF_CONTEXT_PREHEAT_ACTIVE,
    CONF_CONTEXT_TRANSITION,
    CONF_CONTEXT_WAKEUP,
    CONF_CONTEXT_WORKDAY,
    CONF_COOLDOWN_SECONDS,
    CONF_FORECAST_TEMPERATURE,
    CONF_KITCHEN_PATIO_OPEN,
    CONF_KITCHEN_PATIO_TILT,
    CONF_LIVING_WINDOW_LEFT_OPEN,
    CONF_LIVING_WINDOW_LEFT_TILT,
    CONF_LIVING_WINDOW_RIGHT_OPEN,
    CONF_LIVING_WINDOW_RIGHT_TILT,
    CONF_OUTDOOR_FEELS_LIKE,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_LUX,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_OUTDOOR_WIND_SPEED,
    CONF_STARTUP_BLOCK_SECONDS,
    CONF_SUN,
    CONF_SYSTEM_READY,
    CONF_WEATHER_CONDITION,
    CONF_WEATHER_ENTITY,
    CONF_ZONE_HUMIDITY,
    CONF_ZONE_TEMPERATURE,
    CONF_ZONE_THERMOSTAT,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_STARTUP_BLOCK_SECONDS,
    ZONE_BATHROOM,
    ZONE_KITCHEN,
    ZONE_LIVING,
)
from .policy import (
    DEFAULT_THRESHOLD_BANDS,
    DEFAULT_FLOOR_SLAB_ANCHORS,
    DEFAULT_INDOOR_HEAT_RULES,
    FLOOR_SLAB_ANCHOR_NAMES,
    FLOOR_SLAB_MODE_DYNAMIC_3DAY,
    FLOOR_SLAB_MODE_STATIC_FALLBACK,
    OPT_BOOST_ACTIVATION_DELTA,
    OPT_BOOST_DELTA,
    OPT_FEELS_LIKE_DAMPING,
    OPT_FLOOR_SLAB_MAX_DELTA,
    OPT_FLOOR_SLAB_MIN_DELTA,
    OPT_FLOOR_SLAB_MODE,
    OPT_FLOOR_SLAB_TAU,
    OPT_FLOOR_SLAB_DELTA,
    OPT_FORECAST_WEIGHT,
    OPT_LUX_BONUS_MAX,
    OPT_LUX_REFERENCE,
    OPT_SETPOINT_BOOST,
    OPT_SETPOINT_KOMFORT,
    OPT_SETPOINT_OFF,
    OPT_SETPOINT_SPAR,
    default_policy_tuning,
    floor_slab_anchor_option_key,
    indoor_heat_option_key,
    policy_tuning_from_options,
    threshold_option_key,
)

THRESHOLD_FIELDS = (
    "off_threshold",
    "comfort_threshold",
    "boost_threshold",
    "comfort_disabled",
    "boost_disabled",
    "floor_slab_delta",
)

CORE_KEYS = (
    OPT_SETPOINT_OFF,
    OPT_SETPOINT_SPAR,
    OPT_SETPOINT_KOMFORT,
    OPT_SETPOINT_BOOST,
)
EFFECTIVE_KEYS = (
    OPT_FLOOR_SLAB_TAU,
    OPT_LUX_BONUS_MAX,
    OPT_LUX_REFERENCE,
    OPT_FEELS_LIKE_DAMPING,
    OPT_FORECAST_WEIGHT,
)
FLOOR_SLAB_KEYS = (
    OPT_FLOOR_SLAB_MODE,
    OPT_FLOOR_SLAB_MIN_DELTA,
    OPT_FLOOR_SLAB_MAX_DELTA,
    *(
        floor_slab_anchor_option_key(anchor, field)
        for anchor in FLOOR_SLAB_ANCHOR_NAMES
        for field in ("index", "delta")
    ),
)
BOOST_KEYS = (
    OPT_BOOST_DELTA,
    OPT_BOOST_ACTIVATION_DELTA,
)
INDOOR_LIVING_KEYS = tuple(
    indoor_heat_option_key("living_area", profile, field)
    for profile in ("spar", "komfort", "boost")
    for field in ("heat_on_below", "heat_off_at", "min_hold_minutes")
)
INDOOR_BATHROOM_KEYS = tuple(
    indoor_heat_option_key("bathroom", profile, field)
    for profile in ("grundwaerme", "komfort")
    for field in ("heat_on_below", "heat_off_at", "min_hold_minutes")
)
APPLY_KEYS = (
    CONF_APPLY_COOLDOWN_SECONDS,
    CONF_STARTUP_BLOCK_SECONDS,
)
BATH_KEYS = (
    OPT_BATH_SETPOINT_PROTECTION,
    OPT_BATH_SETPOINT_GROUND,
    OPT_BATH_SETPOINT_COMFORT,
    OPT_BATH_COMFORT_SUPPRESSION_TEFF,
    OPT_BATH_HUMIDITY_ACUTE_THRESHOLD,
    OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD,
    OPT_BATH_HUMIDITY_END_THRESHOLD,
    OPT_BATH_DEWPOINT_ACUTE_THRESHOLD,
    OPT_BATH_AH_DELTA_AFTERRUN_ON,
    OPT_BATH_AH_DELTA_AFTERRUN_OFF,
    OPT_BATH_AH_DELTA_STOSS,
    OPT_BATH_FAN_HEAT_COORDINATION_DELTA,
    OPT_BATH_FAN_ACUTE_MAX_MINUTES,
    OPT_BATH_FAN_AFTERRUN_MAX_MINUTES,
    OPT_BATH_FAN_STOSS_INTERVAL_HOURS,
    OPT_BATH_FAN_STOSS_DURATION_MINUTES,
)
THRESHOLD_KEYS = tuple(
    threshold_option_key(band, field)
    for band in DEFAULT_THRESHOLD_BANDS
    for field in THRESHOLD_FIELDS
)

TUNING_SECTIONS: dict[str, tuple[str, ...]] = {
    "thresholds": THRESHOLD_KEYS,
    "setpoints": CORE_KEYS,
    "effective": EFFECTIVE_KEYS,
    "floor_slab": FLOOR_SLAB_KEYS,
    "boost": BOOST_KEYS,
    "indoor_living": INDOOR_LIVING_KEYS,
    "indoor_bathroom": INDOOR_BATHROOM_KEYS,
    "apply": APPLY_KEYS,
    "bath": BATH_KEYS,
}
EDITABLE_OPTION_KEYS = tuple(
    key
    for section in ("thresholds", "setpoints", "effective", "floor_slab", "boost", "indoor_living", "indoor_bathroom", "apply", "bath")
    for key in TUNING_SECTIONS[section]
)
EDITABLE_OPTION_KEY_SET = set(EDITABLE_OPTION_KEYS)
SOURCE_BINDING_KEYS = (
    CONF_CONTEXT_ACTIVITY,
    CONF_CONTEXT_BIO,
    CONF_CONTEXT_DAY_CONTEXT,
    CONF_CONTEXT_DAY_STATE,
    CONF_CONTEXT_PRESENCE_BAND,
    CONF_CONTEXT_PRESENCE_HOUSEHOLD,
    CONF_CONTEXT_PRESENCE_PERSONAL,
    CONF_CONTEXT_PREHEAT_ACTIVE,
    CONF_CONTEXT_TRANSITION,
    CONF_CONTEXT_WAKEUP,
    CONF_CONTEXT_WORKDAY,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_OUTDOOR_FEELS_LIKE,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_WIND_SPEED,
    CONF_FORECAST_TEMPERATURE,
    CONF_WEATHER_ENTITY,
    CONF_WEATHER_CONDITION,
    CONF_OUTDOOR_LUX,
    CONF_SUN,
    CONF_SYSTEM_READY,
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_LIVING),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_LIVING),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_LIVING),
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_KITCHEN),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_KITCHEN),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_KITCHEN),
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_BATHROOM),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_BATHROOM),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_BATHROOM),
    CONF_LIVING_WINDOW_LEFT_OPEN,
    CONF_LIVING_WINDOW_LEFT_TILT,
    CONF_LIVING_WINDOW_RIGHT_OPEN,
    CONF_LIVING_WINDOW_RIGHT_TILT,
    CONF_KITCHEN_PATIO_OPEN,
    CONF_KITCHEN_PATIO_TILT,
    CONF_BATH_FAN,
    CONF_BATH_TOILET_ACTIVITY,
    CONF_BATH_SHOWER_ACTIVITY,
)
SOURCE_BINDING_KEY_SET = set(SOURCE_BINDING_KEYS)
SERVICE_EDITABLE_KEY_SET = EDITABLE_OPTION_KEY_SET | SOURCE_BINDING_KEY_SET


@dataclass(frozen=True)
class OptionSpec:
    kind: str
    default: float | int | bool | str
    min_value: float | int | None = None
    max_value: float | int | None = None


def default_option_values() -> dict[str, float | int | bool | str]:
    policy = default_policy_tuning()
    bath = bath_tuning_from_options({})
    values: dict[str, float | int | bool | str] = {
        OPT_SETPOINT_OFF: policy.setpoint_off,
        OPT_SETPOINT_SPAR: policy.setpoint_spar,
        OPT_SETPOINT_KOMFORT: policy.setpoint_komfort,
        OPT_SETPOINT_BOOST: policy.setpoint_boost,
        OPT_BOOST_DELTA: policy.boost_delta,
        OPT_BOOST_ACTIVATION_DELTA: policy.boost_activation_delta,
        OPT_FLOOR_SLAB_TAU: policy.floor_slab_tau,
        OPT_LUX_BONUS_MAX: policy.lux_bonus_max,
        OPT_LUX_REFERENCE: policy.lux_reference,
        OPT_FEELS_LIKE_DAMPING: policy.feels_like_damping,
        OPT_FORECAST_WEIGHT: policy.forecast_weight,
        OPT_FLOOR_SLAB_MODE: policy.floor_slab_mode,
        OPT_FLOOR_SLAB_MIN_DELTA: policy.floor_slab_min_delta,
        OPT_FLOOR_SLAB_MAX_DELTA: policy.floor_slab_max_delta,
        CONF_APPLY_COOLDOWN_SECONDS: DEFAULT_COOLDOWN_SECONDS,
        CONF_STARTUP_BLOCK_SECONDS: DEFAULT_STARTUP_BLOCK_SECONDS,
        OPT_BATH_SETPOINT_PROTECTION: bath.setpoint_protection,
        OPT_BATH_SETPOINT_GROUND: bath.setpoint_ground,
        OPT_BATH_SETPOINT_COMFORT: bath.setpoint_comfort,
        OPT_BATH_COMFORT_SUPPRESSION_TEFF: bath.comfort_suppression_teff,
        OPT_BATH_HUMIDITY_ACUTE_THRESHOLD: bath.humidity_acute_threshold,
        OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD: bath.humidity_acute_rise_threshold,
        OPT_BATH_HUMIDITY_END_THRESHOLD: bath.humidity_end_threshold,
        OPT_BATH_DEWPOINT_ACUTE_THRESHOLD: bath.dewpoint_acute_threshold,
        OPT_BATH_AH_DELTA_AFTERRUN_ON: bath.ah_delta_afterrun_on,
        OPT_BATH_AH_DELTA_AFTERRUN_OFF: bath.ah_delta_afterrun_off,
        OPT_BATH_AH_DELTA_STOSS: bath.ah_delta_stoss,
        OPT_BATH_FAN_HEAT_COORDINATION_DELTA: bath.fan_heat_coordination_delta,
        OPT_BATH_FAN_ACUTE_MAX_MINUTES: bath.fan_acute_max_minutes,
        OPT_BATH_FAN_AFTERRUN_MAX_MINUTES: bath.fan_afterrun_max_minutes,
        OPT_BATH_FAN_STOSS_INTERVAL_HOURS: bath.fan_stoss_interval_hours,
        OPT_BATH_FAN_STOSS_DURATION_MINUTES: bath.fan_stoss_duration_minutes,
    }
    for group, profiles in DEFAULT_INDOOR_HEAT_RULES.items():
        for profile, defaults in profiles.items():
            heat_on, heat_off, min_hold = defaults
            values.update({
                indoor_heat_option_key(group, profile, "heat_on_below"): heat_on,
                indoor_heat_option_key(group, profile, "heat_off_at"): heat_off,
                indoor_heat_option_key(group, profile, "min_hold_minutes"): min_hold,
            })
    for anchor in FLOOR_SLAB_ANCHOR_NAMES:
        index, delta = DEFAULT_FLOOR_SLAB_ANCHORS[anchor]
        values[floor_slab_anchor_option_key(anchor, "index")] = index
        values[floor_slab_anchor_option_key(anchor, "delta")] = delta
    for band, config in policy.threshold_bands.items():
        values.update({
            threshold_option_key(band, "off_threshold"): config.off_threshold,
            threshold_option_key(band, "comfort_threshold"): config.comfort_threshold,
            threshold_option_key(band, "boost_threshold"): config.boost_threshold,
            threshold_option_key(band, "comfort_disabled"): config.comfort_disabled,
            threshold_option_key(band, "boost_disabled"): config.boost_disabled,
            threshold_option_key(band, "floor_slab_delta"): config.floor_slab_delta,
        })
    return values


def option_specs() -> dict[str, OptionSpec]:
    defaults = default_option_values()
    specs = {key: OptionSpec("float", defaults[key], 5.0, 30.0) for key in CORE_KEYS}
    specs.update({
        OPT_BOOST_DELTA: OptionSpec("float", defaults[OPT_BOOST_DELTA], 0.0, 5.0),
        OPT_BOOST_ACTIVATION_DELTA: OptionSpec("float", defaults[OPT_BOOST_ACTIVATION_DELTA], 0.0, 10.0),
        OPT_FLOOR_SLAB_TAU: OptionSpec("float", defaults[OPT_FLOOR_SLAB_TAU], 0.1, 72.0),
        OPT_LUX_BONUS_MAX: OptionSpec("float", defaults[OPT_LUX_BONUS_MAX], 0.0, 10.0),
        OPT_LUX_REFERENCE: OptionSpec("float", defaults[OPT_LUX_REFERENCE], 1.0, None),
        OPT_FEELS_LIKE_DAMPING: OptionSpec("float", defaults[OPT_FEELS_LIKE_DAMPING], 0.0, 1.0),
        OPT_FORECAST_WEIGHT: OptionSpec("float", defaults[OPT_FORECAST_WEIGHT], 0.0, 1.0),
        OPT_FLOOR_SLAB_MODE: OptionSpec("str", defaults[OPT_FLOOR_SLAB_MODE]),
        OPT_FLOOR_SLAB_MIN_DELTA: OptionSpec("float", defaults[OPT_FLOOR_SLAB_MIN_DELTA], 0.0, 5.0),
        OPT_FLOOR_SLAB_MAX_DELTA: OptionSpec("float", defaults[OPT_FLOOR_SLAB_MAX_DELTA], 0.0, 5.0),
        CONF_APPLY_COOLDOWN_SECONDS: OptionSpec("int", defaults[CONF_APPLY_COOLDOWN_SECONDS], 1, None),
        CONF_STARTUP_BLOCK_SECONDS: OptionSpec("int", defaults[CONF_STARTUP_BLOCK_SECONDS], 1, None),
        OPT_BATH_SETPOINT_PROTECTION: OptionSpec("float", defaults[OPT_BATH_SETPOINT_PROTECTION], 5.0, 30.0),
        OPT_BATH_SETPOINT_GROUND: OptionSpec("float", defaults[OPT_BATH_SETPOINT_GROUND], 5.0, 30.0),
        OPT_BATH_SETPOINT_COMFORT: OptionSpec("float", defaults[OPT_BATH_SETPOINT_COMFORT], 5.0, 30.0),
        OPT_BATH_COMFORT_SUPPRESSION_TEFF: OptionSpec("float", defaults[OPT_BATH_COMFORT_SUPPRESSION_TEFF], -30.0, 35.0),
        OPT_BATH_HUMIDITY_ACUTE_THRESHOLD: OptionSpec("float", defaults[OPT_BATH_HUMIDITY_ACUTE_THRESHOLD], 0.0, 100.0),
        OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD: OptionSpec("float", defaults[OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD], 0.0, 100.0),
        OPT_BATH_HUMIDITY_END_THRESHOLD: OptionSpec("float", defaults[OPT_BATH_HUMIDITY_END_THRESHOLD], 0.0, 100.0),
        OPT_BATH_DEWPOINT_ACUTE_THRESHOLD: OptionSpec("float", defaults[OPT_BATH_DEWPOINT_ACUTE_THRESHOLD], -20.0, 40.0),
        OPT_BATH_AH_DELTA_AFTERRUN_ON: OptionSpec("float", defaults[OPT_BATH_AH_DELTA_AFTERRUN_ON], -10.0, 30.0),
        OPT_BATH_AH_DELTA_AFTERRUN_OFF: OptionSpec("float", defaults[OPT_BATH_AH_DELTA_AFTERRUN_OFF], -10.0, 30.0),
        OPT_BATH_AH_DELTA_STOSS: OptionSpec("float", defaults[OPT_BATH_AH_DELTA_STOSS], -10.0, 30.0),
        OPT_BATH_FAN_HEAT_COORDINATION_DELTA: OptionSpec("float", defaults[OPT_BATH_FAN_HEAT_COORDINATION_DELTA], 0.0, 10.0),
        OPT_BATH_FAN_ACUTE_MAX_MINUTES: OptionSpec("int", defaults[OPT_BATH_FAN_ACUTE_MAX_MINUTES], 1, None),
        OPT_BATH_FAN_AFTERRUN_MAX_MINUTES: OptionSpec("int", defaults[OPT_BATH_FAN_AFTERRUN_MAX_MINUTES], 1, None),
        OPT_BATH_FAN_STOSS_INTERVAL_HOURS: OptionSpec("int", defaults[OPT_BATH_FAN_STOSS_INTERVAL_HOURS], 1, None),
        OPT_BATH_FAN_STOSS_DURATION_MINUTES: OptionSpec("int", defaults[OPT_BATH_FAN_STOSS_DURATION_MINUTES], 1, None),
    })
    for key in (*INDOOR_LIVING_KEYS, *INDOOR_BATHROOM_KEYS):
        if key.endswith("_min_hold_minutes"):
            specs[key] = OptionSpec("int", defaults[key], 0, 240)
        else:
            specs[key] = OptionSpec("float", defaults[key], 5.0, 30.0)
    for anchor in FLOOR_SLAB_ANCHOR_NAMES:
        specs[floor_slab_anchor_option_key(anchor, "index")] = OptionSpec("float", defaults[floor_slab_anchor_option_key(anchor, "index")], -30.0, 35.0)
        specs[floor_slab_anchor_option_key(anchor, "delta")] = OptionSpec("float", defaults[floor_slab_anchor_option_key(anchor, "delta")], 0.0, 5.0)
    for band in DEFAULT_THRESHOLD_BANDS:
        specs[threshold_option_key(band, "off_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "off_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "comfort_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "comfort_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "boost_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "boost_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "comfort_disabled")] = OptionSpec("bool", defaults[threshold_option_key(band, "comfort_disabled")])
        specs[threshold_option_key(band, "boost_disabled")] = OptionSpec("bool", defaults[threshold_option_key(band, "boost_disabled")])
        specs[threshold_option_key(band, "floor_slab_delta")] = OptionSpec("float", defaults[threshold_option_key(band, "floor_slab_delta")], 0.0, 5.0)
    return specs


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "on", "1", "yes", "ja"):
            return True
        if lowered in ("false", "off", "0", "no", "nein"):
            return False
    raise ValueError("muss true oder false sein")


def _coerce_value(key: str, value: Any, spec: OptionSpec) -> float | int | bool | str:
    if spec.kind == "bool":
        return _as_bool(value)
    if spec.kind == "str":
        text = str(value)
        if key == OPT_FLOOR_SLAB_MODE and text not in (FLOOR_SLAB_MODE_DYNAMIC_3DAY, FLOOR_SLAB_MODE_STATIC_FALLBACK):
            raise ValueError("ungueltiger Bodenplatten-Modus")
        return text
    if value in (None, ""):
        raise ValueError("darf nicht leer sein")
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError("muss eine Zahl sein") from err
    if spec.min_value is not None and number < spec.min_value:
        raise ValueError(f"muss >= {spec.min_value} sein")
    if spec.max_value is not None and number > spec.max_value:
        raise ValueError(f"muss <= {spec.max_value} sein")
    if spec.kind == "int":
        if not number.is_integer():
            raise ValueError("muss eine ganze Zahl sein")
        return int(number)
    return float(number)


def _source_for(options: Mapping[str, Any], key: str) -> str:
    if key == CONF_APPLY_COOLDOWN_SECONDS and CONF_COOLDOWN_SECONDS in options and key not in options:
        return "user option"
    return "user option" if key in options else "default"


def active_option_values(options: Mapping[str, Any] | None) -> dict[str, float | int | bool | str]:
    options = options or {}
    defaults = default_option_values()
    policy = policy_tuning_from_options(options)
    bath = bath_tuning_from_options(options)
    values = dict(defaults)
    values.update({
        OPT_SETPOINT_OFF: policy.setpoint_off,
        OPT_SETPOINT_SPAR: policy.setpoint_spar,
        OPT_SETPOINT_KOMFORT: policy.setpoint_komfort,
        OPT_SETPOINT_BOOST: policy.setpoint_boost,
        OPT_BOOST_DELTA: policy.boost_delta,
        OPT_BOOST_ACTIVATION_DELTA: policy.boost_activation_delta,
        OPT_FLOOR_SLAB_TAU: policy.floor_slab_tau,
        OPT_LUX_BONUS_MAX: policy.lux_bonus_max,
        OPT_LUX_REFERENCE: policy.lux_reference,
        OPT_FEELS_LIKE_DAMPING: policy.feels_like_damping,
        OPT_FORECAST_WEIGHT: policy.forecast_weight,
        OPT_FLOOR_SLAB_MODE: policy.floor_slab_mode,
        OPT_FLOOR_SLAB_MIN_DELTA: policy.floor_slab_min_delta,
        OPT_FLOOR_SLAB_MAX_DELTA: policy.floor_slab_max_delta,
        CONF_APPLY_COOLDOWN_SECONDS: int(options.get(CONF_APPLY_COOLDOWN_SECONDS, options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS))),
        CONF_STARTUP_BLOCK_SECONDS: int(options.get(CONF_STARTUP_BLOCK_SECONDS, DEFAULT_STARTUP_BLOCK_SECONDS)),
        OPT_BATH_SETPOINT_PROTECTION: bath.setpoint_protection,
        OPT_BATH_SETPOINT_GROUND: bath.setpoint_ground,
        OPT_BATH_SETPOINT_COMFORT: bath.setpoint_comfort,
        OPT_BATH_COMFORT_SUPPRESSION_TEFF: bath.comfort_suppression_teff,
        OPT_BATH_HUMIDITY_ACUTE_THRESHOLD: bath.humidity_acute_threshold,
        OPT_BATH_HUMIDITY_ACUTE_RISE_THRESHOLD: bath.humidity_acute_rise_threshold,
        OPT_BATH_HUMIDITY_END_THRESHOLD: bath.humidity_end_threshold,
        OPT_BATH_DEWPOINT_ACUTE_THRESHOLD: bath.dewpoint_acute_threshold,
        OPT_BATH_AH_DELTA_AFTERRUN_ON: bath.ah_delta_afterrun_on,
        OPT_BATH_AH_DELTA_AFTERRUN_OFF: bath.ah_delta_afterrun_off,
        OPT_BATH_AH_DELTA_STOSS: bath.ah_delta_stoss,
        OPT_BATH_FAN_HEAT_COORDINATION_DELTA: bath.fan_heat_coordination_delta,
        OPT_BATH_FAN_ACUTE_MAX_MINUTES: bath.fan_acute_max_minutes,
        OPT_BATH_FAN_AFTERRUN_MAX_MINUTES: bath.fan_afterrun_max_minutes,
        OPT_BATH_FAN_STOSS_INTERVAL_HOURS: bath.fan_stoss_interval_hours,
        OPT_BATH_FAN_STOSS_DURATION_MINUTES: bath.fan_stoss_duration_minutes,
    })
    for group, profiles in policy.indoor_heat_rules.items():
        for profile, rule in profiles.items():
            values.update({
                indoor_heat_option_key(group, profile, "heat_on_below"): rule.heat_on_below,
                indoor_heat_option_key(group, profile, "heat_off_at"): rule.heat_off_at,
                indoor_heat_option_key(group, profile, "min_hold_minutes"): rule.min_hold_minutes,
            })
    for anchor, (index, delta) in zip(FLOOR_SLAB_ANCHOR_NAMES, policy.floor_slab_anchors):
        values[floor_slab_anchor_option_key(anchor, "index")] = index
        values[floor_slab_anchor_option_key(anchor, "delta")] = delta
    for band, config in policy.threshold_bands.items():
        values.update({
            threshold_option_key(band, "off_threshold"): config.off_threshold,
            threshold_option_key(band, "comfort_threshold"): config.comfort_threshold,
            threshold_option_key(band, "boost_threshold"): config.boost_threshold,
            threshold_option_key(band, "comfort_disabled"): config.comfort_disabled,
            threshold_option_key(band, "boost_disabled"): config.boost_disabled,
            threshold_option_key(band, "floor_slab_delta"): config.floor_slab_delta,
        })
    return values


def tuning_options_snapshot(options: Mapping[str, Any] | None) -> dict[str, Any]:
    options = options or {}
    values = active_option_values(options)
    defaults = default_option_values()
    sources = {key: _source_for(options, key) for key in EDITABLE_OPTION_KEYS}
    bands = {
        band: {
            "key": band,
            "months": list(DEFAULT_THRESHOLD_BANDS[band].months),
            "values": {field: values[threshold_option_key(band, field)] for field in THRESHOLD_FIELDS},
            "defaults": {field: defaults[threshold_option_key(band, field)] for field in THRESHOLD_FIELDS},
            "sources": {field: sources[threshold_option_key(band, field)] for field in THRESHOLD_FIELDS},
            "keys": {field: threshold_option_key(band, field) for field in THRESHOLD_FIELDS},
        }
        for band in DEFAULT_THRESHOLD_BANDS
    }
    return {
        "values": {key: values[key] for key in EDITABLE_OPTION_KEYS},
        "defaults": {key: defaults[key] for key in EDITABLE_OPTION_KEYS},
        "sources": sources,
        "sections": {section: list(keys) for section, keys in TUNING_SECTIONS.items()},
        "threshold_bands": bands,
    }


def _validate_threshold_order(values: Mapping[str, Any]) -> None:
    for band in DEFAULT_THRESHOLD_BANDS:
        off = float(values[threshold_option_key(band, "off_threshold")])
        comfort_disabled = bool(values[threshold_option_key(band, "comfort_disabled")])
        boost_disabled = bool(values[threshold_option_key(band, "boost_disabled")])
        comfort = float(values[threshold_option_key(band, "comfort_threshold")])
        boost = float(values[threshold_option_key(band, "boost_threshold")])
        if not comfort_disabled and comfort > off:
            raise ValueError(f"{band}: comfort_threshold darf nicht ueber off_threshold liegen")
        if not boost_disabled and comfort_disabled:
            raise ValueError(f"{band}: boost_threshold kann nicht aktiv sein, wenn comfort deaktiviert ist")
        if not boost_disabled and boost > comfort:
            raise ValueError(f"{band}: boost_threshold darf nicht ueber comfort_threshold liegen")


def _validate_indoor_heat_rules(values: Mapping[str, Any]) -> None:
    for group, profiles in DEFAULT_INDOOR_HEAT_RULES.items():
        for profile in profiles:
            heat_on = float(values[indoor_heat_option_key(group, profile, "heat_on_below")])
            heat_off = float(values[indoor_heat_option_key(group, profile, "heat_off_at")])
            if heat_on >= heat_off:
                raise ValueError(f"{group}/{profile}: heat_on_below muss unter heat_off_at liegen")


def _validate_floor_slab_options(values: Mapping[str, Any]) -> None:
    if float(values[OPT_FLOOR_SLAB_MIN_DELTA]) > float(values[OPT_FLOOR_SLAB_MAX_DELTA]):
        raise ValueError("floor_slab_min_delta darf nicht ueber floor_slab_max_delta liegen")
    indexes = [float(values[floor_slab_anchor_option_key(anchor, "index")]) for anchor in FLOOR_SLAB_ANCHOR_NAMES]
    if indexes != sorted(indexes, reverse=True):
        raise ValueError("floor_slab_anchor_index Werte muessen absteigend sortiert bleiben")


def validated_options_update(
    current_options: Mapping[str, Any] | None,
    updates: Mapping[str, Any] | None = None,
    *,
    reset_keys: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    current = dict(current_options or {})
    updates = dict(updates or {})
    specs = option_specs()
    unknown = sorted({*updates, *reset_keys} - SERVICE_EDITABLE_KEY_SET)
    if unknown:
        raise ValueError(f"Unbekannte Option: {', '.join(unknown)}")

    for key in reset_keys:
        current.pop(key, None)
        if key == CONF_APPLY_COOLDOWN_SECONDS:
            current.pop(CONF_COOLDOWN_SECONDS, None)

    active = active_option_values(current)
    for key, value in updates.items():
        if key in SOURCE_BINDING_KEY_SET:
            if value is None:
                current.pop(key, None)
            else:
                current[key] = str(value).strip()
            continue
        spec = specs[key]
        if value in (None, "") and key.endswith(("_comfort_threshold", "_boost_threshold")):
            disabled_key = key.replace("_comfort_threshold", "_comfort_disabled").replace("_boost_threshold", "_boost_disabled")
            disabled = _as_bool(updates.get(disabled_key, active[disabled_key]))
            if disabled:
                current.pop(key, None)
                active[key] = default_option_values()[key]
                continue
        coerced = _coerce_value(key, value, spec)
        current[key] = coerced
        active[key] = coerced
        if key == CONF_APPLY_COOLDOWN_SECONDS:
            current.pop(CONF_COOLDOWN_SECONDS, None)

    merged = active_option_values(current)
    _validate_threshold_order(merged)
    _validate_indoor_heat_rules(merged)
    _validate_floor_slab_options(merged)

    return current
