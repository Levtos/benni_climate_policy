"""Switch entities for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ClimatePolicyCoordinator
from .entity import ClimatePolicyEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: ClimatePolicyCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([ApplyActiveSwitch(coord)])


class ApplyActiveSwitch(ClimatePolicyEntity, SwitchEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Apply Active", "apply_active")

    @property
    def is_on(self) -> bool:
        return self.coord.apply_active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "meaning": "Auto-Apply aktiv. Manueller Apply und Dry Run bleiben separat.",
            "apply_ready": self.coord.apply_ready,
            "system_ready": self.coord.system_ready,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coord.async_set_apply_active(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coord.async_set_apply_active(False)

