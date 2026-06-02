"""Config flow for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_APPLY_ACTIVE,
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

ENTITY = selector.EntitySelector(selector.EntitySelectorConfig())
CLIMATE = selector.EntitySelector(selector.EntitySelectorConfig(domain="climate"))
SWITCH = selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))
BOOL = selector.BooleanSelector()
INT = selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=3600, step=10, mode="box"))

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
STEP_APPLY = (CONF_APPLY_ACTIVE, CONF_STARTUP_BLOCK_SECONDS, CONF_COOLDOWN_SECONDS)

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
    CONF_STARTUP_BLOCK_SECONDS: INT,
    CONF_COOLDOWN_SECONDS: INT,
})

REQUIRED_KEYS = {
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_LIVING),
    CONF_ZONE_THERMOSTAT.format(zone=ZONE_KITCHEN),
}


def _exists(hass, entity_id: str | None) -> bool:
    return bool(entity_id) and hass.states.get(entity_id) is not None


def _defaults(hass, data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    out = dict(data)
    for key in keys:
        if key in out:
            continue
        preset = PRESET.get(key)
        if _exists(hass, preset):
            out[key] = preset
    out.setdefault(CONF_APPLY_ACTIVE, DEFAULT_APPLY_ACTIVE)
    out.setdefault(CONF_STARTUP_BLOCK_SECONDS, DEFAULT_STARTUP_BLOCK_SECONDS)
    out.setdefault(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS)
    return out


def _schema(hass, data: dict[str, Any], keys: tuple[str, ...]) -> vol.Schema:
    defaults = _defaults(hass, data, keys)
    fields: dict[Any, Any] = {}
    for key in keys:
        marker = vol.Required(key, default=defaults[key]) if key in defaults else vol.Required(key)
        if key not in REQUIRED_KEYS and key not in (CONF_APPLY_ACTIVE, CONF_STARTUP_BLOCK_SECONDS, CONF_COOLDOWN_SECONDS):
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
            menu_options=["context", "zones", "environment", "apply", "windows", "diagnostics"],
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

    async def async_step_diagnostics(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=self._entry.options)
        return self.async_show_form(step_id="diagnostics", data_schema=vol.Schema({}))

