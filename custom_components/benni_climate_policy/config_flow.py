"""Config flow for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .bathroom import (
    BATH_OPTION_KEYS,
    OPT_BATH_AH_DELTA_AFTERRUN_OFF,
    OPT_BATH_AH_DELTA_AFTERRUN_ON,
    OPT_BATH_AH_DELTA_STOSS,
    OPT_BATH_BONUS_TEFF_0,
    OPT_BATH_BONUS_TEFF_5,
    OPT_BATH_BONUS_TEFF_WARM,
    OPT_BATH_COMFORT_SUPPRESSION_TEFF,
    OPT_BATH_DEWPOINT_ACUTE_THRESHOLD,
    OPT_BATH_FAN_ACUTE_MAX_MINUTES,
    OPT_BATH_FAN_AFTERRUN_MAX_MINUTES,
    OPT_BATH_FAN_HEAT_COORDINATION_DELTA,
    OPT_BATH_FAN_STOSS_DURATION_MINUTES,
    OPT_BATH_FAN_STOSS_INTERVAL_HOURS,
    OPT_BATH_HUMIDITY_ACUTE_THRESHOLD,
    OPT_BATH_HUMIDITY_END_THRESHOLD,
    OPT_BATH_SETPOINT_COMFORT,
    OPT_BATH_SETPOINT_GROUND,
    OPT_BATH_SETPOINT_PROTECTION,
    bath_tuning_from_options,
)
from .const import (
    CONF_APPLY_ACTIVE,
    CONF_APPLY_COOLDOWN_SECONDS,
    CONF_BATH_FAN,
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
    CONF_OUTDOOR_LUX,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_STARTUP_BLOCK_SECONDS,
    CONF_SUN,
    CONF_SYSTEM_READY,
    CONF_WEATHER_CONDITION,
    CONF_ZONE_HUMIDITY,
    CONF_ZONE_TEMPERATURE,
    CONF_ZONE_THERMOSTAT,
    DEFAULT_APPLY_ACTIVE,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_STARTUP_BLOCK_SECONDS,
    DOMAIN,
    PRESET,
    ZONE_BATHROOM,
    ZONE_KITCHEN,
    ZONE_LIVING,
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
    threshold_option_key,
)

ENTITY = selector.EntitySelector(selector.EntitySelectorConfig())
CLIMATE = selector.EntitySelector(selector.EntitySelectorConfig(domain="climate"))
SWITCH = selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))
BOOL = selector.BooleanSelector()
INT = selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=3600, step=10, mode="box"))
POS_INT = selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=86400, step=10, mode="box"))
TEMP_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=5, max=30, step=0.5, mode="box"))
THRESHOLD_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=35, step=0.5, mode="box"))
POS_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=0.1, max=100000, step=0.1, mode="box"))
WEIGHT_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=1, step=0.05, mode="box"))
PERCENT_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=0.5, mode="box"))
SMALL_DELTA_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=-10, max=30, step=0.1, mode="box"))
BATH_BONUS_FLOAT = selector.NumberSelector(selector.NumberSelectorConfig(min=-5, max=5, step=0.1, mode="box"))
BATH_MINUTES = selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=240, step=1, mode="box"))
BATH_HOURS = selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=48, step=1, mode="box"))

STEP_CONTEXT = (
    CONF_CONTEXT_ACTIVITY,
    CONF_CONTEXT_BIO,
    CONF_CONTEXT_DAY_CONTEXT,
    CONF_CONTEXT_DAY_STATE,
    CONF_CONTEXT_PRESENCE_BAND,
    CONF_CONTEXT_PRESENCE_HOUSEHOLD,
    CONF_CONTEXT_PRESENCE_PERSONAL,
    CONF_CONTEXT_PREHEAT_ACTIVE,
    CONF_CONTEXT_TRANSITION,
    CONF_CONTEXT_WORKDAY,
    CONF_CONTEXT_WAKEUP,
)
STEP_ENVIRONMENT = (
    CONF_OUTDOOR_TEMPERATURE,
    CONF_OUTDOOR_FEELS_LIKE,
    CONF_FORECAST_TEMPERATURE,
    CONF_WEATHER_CONDITION,
    CONF_OUTDOOR_LUX,
    CONF_SUN,
    CONF_SYSTEM_READY,
)
STEP_ZONES = (
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_LIVING),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_LIVING),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_LIVING),
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_KITCHEN),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_KITCHEN),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_KITCHEN),
    CONF_ZONE_TEMPERATURE.format(zone=ZONE_BATHROOM),
    CONF_ZONE_HUMIDITY.format(zone=ZONE_BATHROOM),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_BATHROOM),
    CONF_BATH_FAN,
)
STEP_WINDOWS = (
    CONF_LIVING_WINDOW_LEFT_OPEN,
    CONF_LIVING_WINDOW_LEFT_TILT,
    CONF_LIVING_WINDOW_RIGHT_OPEN,
    CONF_LIVING_WINDOW_RIGHT_TILT,
    CONF_KITCHEN_PATIO_OPEN,
    CONF_KITCHEN_PATIO_TILT,
)
STEP_APPLY = (CONF_APPLY_ACTIVE, CONF_STARTUP_BLOCK_SECONDS, CONF_APPLY_COOLDOWN_SECONDS)
STEP_TUNING_CORE = (
    OPT_SETPOINT_OFF,
    OPT_SETPOINT_SPAR,
    OPT_SETPOINT_KOMFORT,
    OPT_SETPOINT_BOOST,
    OPT_BOOST_DELTA,
    OPT_BOOST_ACTIVATION_DELTA,
)
STEP_TUNING_EFFECTIVE = (
    OPT_FLOOR_SLAB_TAU,
    OPT_LUX_BONUS_MAX,
    OPT_LUX_REFERENCE,
    OPT_FEELS_LIKE_DAMPING,
    OPT_FORECAST_WEIGHT,
)
STEP_TUNING_BATHROOM = BATH_OPTION_KEYS
STEP_TUNING_THRESHOLDS = tuple(
    threshold_option_key(band, field)
    for band in DEFAULT_THRESHOLD_BANDS
    for field in (
        "off_threshold",
        "comfort_threshold",
        "boost_threshold",
        "comfort_disabled",
        "boost_disabled",
    )
)

SELECTORS: dict[str, Any] = {
    key: ENTITY
    for key in (
        *STEP_CONTEXT,
        *STEP_ENVIRONMENT,
        *STEP_WINDOWS,
        CONF_ZONE_TEMPERATURE.format(zone=ZONE_LIVING),
        CONF_ZONE_HUMIDITY.format(zone=ZONE_LIVING),
        CONF_ZONE_TEMPERATURE.format(zone=ZONE_KITCHEN),
        CONF_ZONE_HUMIDITY.format(zone=ZONE_KITCHEN),
        CONF_ZONE_TEMPERATURE.format(zone=ZONE_BATHROOM),
        CONF_ZONE_HUMIDITY.format(zone=ZONE_BATHROOM),
    )
}
SELECTORS.update({
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_LIVING): CLIMATE,
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_KITCHEN): CLIMATE,
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_BATHROOM): CLIMATE,
    CONF_BATH_FAN: SWITCH,
    CONF_APPLY_ACTIVE: BOOL,
    CONF_STARTUP_BLOCK_SECONDS: POS_INT,
    CONF_COOLDOWN_SECONDS: INT,
    CONF_APPLY_COOLDOWN_SECONDS: POS_INT,
})
SELECTORS.update({
    OPT_SETPOINT_OFF: TEMP_FLOAT,
    OPT_SETPOINT_SPAR: TEMP_FLOAT,
    OPT_SETPOINT_KOMFORT: TEMP_FLOAT,
    OPT_SETPOINT_BOOST: TEMP_FLOAT,
    OPT_BOOST_DELTA: selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode="box")),
    OPT_BOOST_ACTIVATION_DELTA: selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode="box")),
    OPT_FLOOR_SLAB_TAU: POS_FLOAT,
    OPT_LUX_BONUS_MAX: selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode="box")),
    OPT_LUX_REFERENCE: selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=100000, step=100, mode="box")),
    OPT_FEELS_LIKE_DAMPING: WEIGHT_FLOAT,
    OPT_FORECAST_WEIGHT: WEIGHT_FLOAT,
})
SELECTORS.update({
    OPT_BATH_SETPOINT_PROTECTION: TEMP_FLOAT,
    OPT_BATH_SETPOINT_GROUND: TEMP_FLOAT,
    OPT_BATH_SETPOINT_COMFORT: TEMP_FLOAT,
    OPT_BATH_COMFORT_SUPPRESSION_TEFF: THRESHOLD_FLOAT,
    OPT_BATH_BONUS_TEFF_0: BATH_BONUS_FLOAT,
    OPT_BATH_BONUS_TEFF_5: BATH_BONUS_FLOAT,
    OPT_BATH_BONUS_TEFF_WARM: BATH_BONUS_FLOAT,
    OPT_BATH_HUMIDITY_ACUTE_THRESHOLD: PERCENT_FLOAT,
    OPT_BATH_HUMIDITY_END_THRESHOLD: PERCENT_FLOAT,
    OPT_BATH_DEWPOINT_ACUTE_THRESHOLD: selector.NumberSelector(selector.NumberSelectorConfig(min=-20, max=40, step=0.5, mode="box")),
    OPT_BATH_AH_DELTA_AFTERRUN_ON: SMALL_DELTA_FLOAT,
    OPT_BATH_AH_DELTA_AFTERRUN_OFF: SMALL_DELTA_FLOAT,
    OPT_BATH_AH_DELTA_STOSS: SMALL_DELTA_FLOAT,
    OPT_BATH_FAN_HEAT_COORDINATION_DELTA: selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode="box")),
    OPT_BATH_FAN_ACUTE_MAX_MINUTES: BATH_MINUTES,
    OPT_BATH_FAN_AFTERRUN_MAX_MINUTES: BATH_MINUTES,
    OPT_BATH_FAN_STOSS_INTERVAL_HOURS: BATH_HOURS,
    OPT_BATH_FAN_STOSS_DURATION_MINUTES: BATH_MINUTES,
})
SELECTORS.update({
    threshold_option_key(band, field): BOOL if field.endswith("_disabled") else THRESHOLD_FLOAT
    for band in DEFAULT_THRESHOLD_BANDS
    for field in (
        "off_threshold",
        "comfort_threshold",
        "boost_threshold",
        "comfort_disabled",
        "boost_disabled",
    )
})

REQUIRED_KEYS = {
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_LIVING),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_KITCHEN),
}


def _exists(hass, entity_id: str | None) -> bool:
    return bool(entity_id) and hass.states.get(entity_id) is not None


def _defaults(hass, data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    out = dict(data)
    tuning = default_policy_tuning()
    tuning_defaults = {
        OPT_SETPOINT_OFF: tuning.setpoint_off,
        OPT_SETPOINT_SPAR: tuning.setpoint_spar,
        OPT_SETPOINT_KOMFORT: tuning.setpoint_komfort,
        OPT_SETPOINT_BOOST: tuning.setpoint_boost,
        OPT_BOOST_DELTA: tuning.boost_delta,
        OPT_BOOST_ACTIVATION_DELTA: tuning.boost_activation_delta,
        OPT_FLOOR_SLAB_TAU: tuning.floor_slab_tau,
        OPT_LUX_BONUS_MAX: tuning.lux_bonus_max,
        OPT_LUX_REFERENCE: tuning.lux_reference,
        OPT_FEELS_LIKE_DAMPING: tuning.feels_like_damping,
        OPT_FORECAST_WEIGHT: tuning.forecast_weight,
    }
    bath_tuning = bath_tuning_from_options({})
    tuning_defaults.update({
        OPT_BATH_SETPOINT_PROTECTION: bath_tuning.setpoint_protection,
        OPT_BATH_SETPOINT_GROUND: bath_tuning.setpoint_ground,
        OPT_BATH_SETPOINT_COMFORT: bath_tuning.setpoint_comfort,
        OPT_BATH_COMFORT_SUPPRESSION_TEFF: bath_tuning.comfort_suppression_teff,
        OPT_BATH_BONUS_TEFF_0: bath_tuning.bonus_teff_0,
        OPT_BATH_BONUS_TEFF_5: bath_tuning.bonus_teff_5,
        OPT_BATH_BONUS_TEFF_WARM: bath_tuning.bonus_teff_warm,
        OPT_BATH_HUMIDITY_ACUTE_THRESHOLD: bath_tuning.humidity_acute_threshold,
        OPT_BATH_HUMIDITY_END_THRESHOLD: bath_tuning.humidity_end_threshold,
        OPT_BATH_DEWPOINT_ACUTE_THRESHOLD: bath_tuning.dewpoint_acute_threshold,
        OPT_BATH_AH_DELTA_AFTERRUN_ON: bath_tuning.ah_delta_afterrun_on,
        OPT_BATH_AH_DELTA_AFTERRUN_OFF: bath_tuning.ah_delta_afterrun_off,
        OPT_BATH_AH_DELTA_STOSS: bath_tuning.ah_delta_stoss,
        OPT_BATH_FAN_HEAT_COORDINATION_DELTA: bath_tuning.fan_heat_coordination_delta,
        OPT_BATH_FAN_ACUTE_MAX_MINUTES: bath_tuning.fan_acute_max_minutes,
        OPT_BATH_FAN_AFTERRUN_MAX_MINUTES: bath_tuning.fan_afterrun_max_minutes,
        OPT_BATH_FAN_STOSS_INTERVAL_HOURS: bath_tuning.fan_stoss_interval_hours,
        OPT_BATH_FAN_STOSS_DURATION_MINUTES: bath_tuning.fan_stoss_duration_minutes,
    })
    for band, config in tuning.threshold_bands.items():
        tuning_defaults.update({
            threshold_option_key(band, "off_threshold"): config.off_threshold,
            threshold_option_key(band, "comfort_threshold"): config.comfort_threshold,
            threshold_option_key(band, "boost_threshold"): config.boost_threshold,
            threshold_option_key(band, "comfort_disabled"): config.comfort_disabled,
            threshold_option_key(band, "boost_disabled"): config.boost_disabled,
        })
    for key in keys:
        if key in out:
            continue
        if key in tuning_defaults:
            out[key] = tuning_defaults[key]
            continue
        preset = PRESET.get(key)
        if _exists(hass, preset):
            out[key] = preset
    out.setdefault(CONF_APPLY_ACTIVE, DEFAULT_APPLY_ACTIVE)
    out.setdefault(CONF_STARTUP_BLOCK_SECONDS, DEFAULT_STARTUP_BLOCK_SECONDS)
    out.setdefault(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS)
    out.setdefault(CONF_APPLY_COOLDOWN_SECONDS, out.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS))
    return out


def _schema(hass, data: dict[str, Any], keys: tuple[str, ...]) -> vol.Schema:
    defaults = _defaults(hass, data, keys)
    fields: dict[Any, Any] = {}
    for key in keys:
        marker = vol.Required(key, default=defaults[key]) if key in defaults else vol.Required(key)
        if key not in REQUIRED_KEYS and key not in (
            CONF_APPLY_ACTIVE,
            CONF_STARTUP_BLOCK_SECONDS,
            CONF_COOLDOWN_SECONDS,
            CONF_APPLY_COOLDOWN_SECONDS,
        ):
            marker = vol.Optional(key, default=defaults[key]) if key in defaults else vol.Optional(key)
        fields[marker] = SELECTORS[key]
    return vol.Schema(fields)


class ClimatePolicyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return await self.async_step_context()

    async def _step(
        self,
        step_id: str,
        keys: tuple[str, ...],
        next_step: str | None,
        user_input: dict[str, Any] | None,
    ) -> FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            if next_step is None:
                return self.async_create_entry(title="Benni Climate Policy", data=self._data)
            return await getattr(self, f"async_step_{next_step}")()
        return self.async_show_form(step_id=step_id, data_schema=_schema(self.hass, self._data, keys))

    async def async_step_context(self, user_input=None):
        return await self._step("context", STEP_CONTEXT, "environment", user_input)

    async def async_step_environment(self, user_input=None):
        return await self._step("environment", STEP_ENVIRONMENT, "zones", user_input)

    async def async_step_zones(self, user_input=None):
        return await self._step("zones", STEP_ZONES, "windows", user_input)

    async def async_step_windows(self, user_input=None):
        return await self._step("windows", STEP_WINDOWS, "apply", user_input)

    async def async_step_apply(self, user_input=None):
        return await self._step("apply", STEP_APPLY, None, user_input)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return ClimatePolicyOptionsFlow(entry)


class ClimatePolicyOptionsFlow(OptionsFlow):
    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "context",
                "zones",
                "environment",
                "tuning_core",
                "tuning_effective",
                "tuning_bathroom",
                "tuning_thresholds",
                "apply",
                "windows",
                "diagnostics",
            ],
        )

    def _edit(self, step_id: str, keys: tuple[str, ...], user_input: dict[str, Any] | None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data={**self._entry.options, **user_input})
        defaults = {**self._entry.data, **self._entry.options}
        return self.async_show_form(step_id=step_id, data_schema=_schema(self.hass, defaults, keys))

    async def async_step_context(self, user_input=None):
        return self._edit("context", STEP_CONTEXT, user_input)

    async def async_step_environment(self, user_input=None):
        return self._edit("environment", STEP_ENVIRONMENT, user_input)

    async def async_step_zones(self, user_input=None):
        return self._edit("zones", STEP_ZONES, user_input)

    async def async_step_windows(self, user_input=None):
        return self._edit("windows", STEP_WINDOWS, user_input)

    async def async_step_apply(self, user_input=None):
        return self._edit("apply", STEP_APPLY, user_input)

    async def async_step_tuning_core(self, user_input=None):
        return self._edit("tuning_core", STEP_TUNING_CORE, user_input)

    async def async_step_tuning_effective(self, user_input=None):
        return self._edit("tuning_effective", STEP_TUNING_EFFECTIVE, user_input)

    async def async_step_tuning_bathroom(self, user_input=None):
        return self._edit("tuning_bathroom", STEP_TUNING_BATHROOM, user_input)

    async def async_step_tuning_thresholds(self, user_input=None):
        return self._edit("tuning_thresholds", STEP_TUNING_THRESHOLDS, user_input)

    async def async_step_diagnostics(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=self._entry.options)
        return self.async_show_form(step_id="diagnostics", data_schema=vol.Schema({}))

