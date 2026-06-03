"""Benni Climate Policy integration."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    SERVICE_APPLY_NOW,
    SERVICE_APPLY_ZONE,
    SERVICE_DRY_RUN,
    SERVICE_RESET_OPTIONS,
    SERVICE_RECALCULATE,
    SERVICE_SET_APPLY_ACTIVE,
    SERVICE_UPDATE_OPTIONS,
)

PLATFORM_NAMES = ["sensor", "binary_sensor", "switch", "button"]


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    from homeassistant.const import Platform

    from .coordinator import ClimatePolicyCoordinator

    platforms = [Platform(name) for name in PLATFORM_NAMES]
    coord = ClimatePolicyCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coord}

    coord.async_start()
    await coord.async_evaluate(auto_apply=False, reason="setup_entry")
    from .view import async_setup_view

    await async_setup_view(hass)
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    _register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: "HomeAssistant", entry: "ConfigEntry") -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    from homeassistant.const import Platform

    platforms = [Platform(name) for name in PLATFORM_NAMES]
    unloaded = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unloaded:
        bucket = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if bucket:
            bucket[DATA_COORDINATOR].async_stop()
        if not hass.data.get(DOMAIN):
            for service in (
                SERVICE_APPLY_NOW,
                SERVICE_APPLY_ZONE,
                SERVICE_SET_APPLY_ACTIVE,
                SERVICE_RECALCULATE,
                SERVICE_DRY_RUN,
                SERVICE_UPDATE_OPTIONS,
                SERVICE_RESET_OPTIONS,
            ):
                hass.services.async_remove(DOMAIN, service)
            from .view import async_remove_view

            async_remove_view(hass)
    return unloaded


def _coordinators(hass: "HomeAssistant"):
    return [
        bucket[DATA_COORDINATOR]
        for bucket in hass.data.get(DOMAIN, {}).values()
        if isinstance(bucket, dict) and DATA_COORDINATOR in bucket
    ]


def _register_services(hass: "HomeAssistant") -> None:
    if hass.services.has_service(DOMAIN, SERVICE_APPLY_NOW):
        return

    async def _apply_now(call: "ServiceCall") -> None:
        zone = call.data.get("zone")
        for coord in _coordinators(hass):
            await coord.async_apply(zone=zone, manual=True, dry_run=False)

    async def _apply_zone(call: "ServiceCall") -> None:
        zone = call.data.get("zone")
        for coord in _coordinators(hass):
            await coord.async_apply(zone=zone, manual=True, dry_run=False)

    async def _set_apply_active(call: "ServiceCall") -> None:
        active = bool(call.data.get("active", False))
        for coord in _coordinators(hass):
            await coord.async_set_apply_active(active)

    async def _recalculate(_call: "ServiceCall") -> None:
        for coord in _coordinators(hass):
            await coord.async_evaluate(auto_apply=False, reason="service_recalculate")

    async def _dry_run(call: "ServiceCall") -> None:
        zone = call.data.get("zone")
        for coord in _coordinators(hass):
            await coord.async_apply(zone=zone, manual=True, dry_run=True)

    async def _update_options(call: "ServiceCall") -> None:
        from homeassistant.exceptions import HomeAssistantError

        updates = dict(call.data.get("options") or {})
        reset_keys = list(call.data.get("reset_keys") or ())
        try:
            for coord in _coordinators(hass):
                await coord.async_update_options(updates, reset_keys=reset_keys)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    async def _reset_options(call: "ServiceCall") -> None:
        from homeassistant.exceptions import HomeAssistantError

        keys = list(call.data.get("keys") or ())
        try:
            for coord in _coordinators(hass):
                await coord.async_update_options({}, reset_keys=keys)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_APPLY_NOW, _apply_now)
    hass.services.async_register(DOMAIN, SERVICE_APPLY_ZONE, _apply_zone)
    hass.services.async_register(DOMAIN, SERVICE_SET_APPLY_ACTIVE, _set_apply_active)
    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, _recalculate)
    hass.services.async_register(DOMAIN, SERVICE_DRY_RUN, _dry_run)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_OPTIONS, _update_options)
    hass.services.async_register(DOMAIN, SERVICE_RESET_OPTIONS, _reset_options)
