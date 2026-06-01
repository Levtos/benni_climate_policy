"""Base entity helpers."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .coordinator import ClimatePolicyCoordinator
from .const import DOMAIN


class ClimatePolicyEntity(Entity):
    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, coord: ClimatePolicyCoordinator, name: str, unique_suffix: str) -> None:
        self.coord = coord
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{unique_suffix}"

    async def async_added_to_hass(self) -> None:
        self.coord.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self.coord.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

