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
    CONF_COOLDOWN_SECONDS,
    CONF_STARTUP_BLOCK_SECONDS,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_STARTUP_BLOCK_SECONDS,
)
from .policy import (
    DEFAULT_THRESHOLD_BANDS,
    OPT_BOOST_ACTIVATION_DELTA,
    OPT_BOOST_DELTA,
    OPT_FEELS_LIKE_DAMPING,
    OPT_FLOOR_SLAB_TAU,
    OPT_FORECAST_WEIGHT,
    OPT_LUX_BONUS_MAX,
    OPT_LUX_REFERENCE,
    OPT_SETPOINT_BOOST,
    OPT_SETPOINT_KOMFORT,
    OPT_SETPOINT_OFF,
    OPT_SETPOINT_SPAR,
    default_policy_tuning,
    policy_tuning_from_options,
    threshold_option_key,
)

THRESHOLD_FIELDS = (
    "off_threshold",
    "comfort_threshold",
    "boost_threshold",
    "comfort_disabled",
    "boost_disabled",
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
BOOST_KEYS = (
    OPT_BOOST_DELTA,
    OPT_BOOST_ACTIVATION_DELTA,
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
    "boost": BOOST_KEYS,
    "apply": APPLY_KEYS,
    "bath": BATH_KEYS,
}
EDITABLE_OPTION_KEYS = tuple(
    key
    for section in ("thresholds", "setpoints", "effective", "boost", "apply", "bath")
    for key in TUNING_SECTIONS[section]
)
EDITABLE_OPTION_KEY_SET = set(EDITABLE_OPTION_KEYS)


@dataclass(frozen=True)
class OptionSpec:
    kind: str
    default: float | int | bool
    min_value: float | int | None = None
    max_value: float | int | None = None


def default_option_values() -> dict[str, float | int | bool]:
    policy = default_policy_tuning()
    bath = bath_tuning_from_options({})
    values: dict[str, float | int | bool] = {
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
    for band, config in policy.threshold_bands.items():
        values.update({
            threshold_option_key(band, "off_threshold"): config.off_threshold,
            threshold_option_key(band, "comfort_threshold"): config.comfort_threshold,
            threshold_option_key(band, "boost_threshold"): config.boost_threshold,
            threshold_option_key(band, "comfort_disabled"): config.comfort_disabled,
            threshold_option_key(band, "boost_disabled"): config.boost_disabled,
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
    for band in DEFAULT_THRESHOLD_BANDS:
        specs[threshold_option_key(band, "off_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "off_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "comfort_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "comfort_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "boost_threshold")] = OptionSpec("float", defaults[threshold_option_key(band, "boost_threshold")], 0.0, 35.0)
        specs[threshold_option_key(band, "comfort_disabled")] = OptionSpec("bool", defaults[threshold_option_key(band, "comfort_disabled")])
        specs[threshold_option_key(band, "boost_disabled")] = OptionSpec("bool", defaults[threshold_option_key(band, "boost_disabled")])
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


def _coerce_value(key: str, value: Any, spec: OptionSpec) -> float | int | bool:
    if spec.kind == "bool":
        return _as_bool(value)
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


def active_option_values(options: Mapping[str, Any] | None) -> dict[str, float | int | bool]:
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
    for band, config in policy.threshold_bands.items():
        values.update({
            threshold_option_key(band, "off_threshold"): config.off_threshold,
            threshold_option_key(band, "comfort_threshold"): config.comfort_threshold,
            threshold_option_key(band, "boost_threshold"): config.boost_threshold,
            threshold_option_key(band, "comfort_disabled"): config.comfort_disabled,
            threshold_option_key(band, "boost_disabled"): config.boost_disabled,
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


def validated_options_update(
    current_options: Mapping[str, Any] | None,
    updates: Mapping[str, Any] | None = None,
    *,
    reset_keys: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    current = dict(current_options or {})
    updates = dict(updates or {})
    specs = option_specs()
    unknown = sorted({*updates, *reset_keys} - EDITABLE_OPTION_KEY_SET)
    if unknown:
        raise ValueError(f"Unbekannte Option: {', '.join(unknown)}")

    for key in reset_keys:
        current.pop(key, None)
        if key == CONF_APPLY_COOLDOWN_SECONDS:
            current.pop(CONF_COOLDOWN_SECONDS, None)

    active = active_option_values(current)
    for key, value in updates.items():
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

    return current
