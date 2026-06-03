"""Base entity helpers."""
from __future__ import annotations

import json
from typing import Any

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
        self._last_published_payload: str | None = None

    async def async_added_to_hass(self) -> None:
        self.coord.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self.coord.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        payload = self._published_payload_signature()
        if payload == self._last_published_payload:
            self.coord.record_entity_publish(changed=False)
            return
        self._last_published_payload = payload
        self.coord.record_entity_publish(changed=True)
        self.async_write_ha_state()

    def _published_payload_signature(self) -> str:
        payload = {
            "state": self._published_state_value(),
            "attributes": self._published_attributes(),
        }
        return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))

    def _published_state_value(self) -> Any:
        for attr_name in ("native_value", "is_on"):
            try:
                value = getattr(self, attr_name)
            except Exception:  # noqa: BLE001 - entity properties should not make updates noisy
                continue
            if value is not None:
                return value
        return None

    def _published_attributes(self) -> dict[str, Any]:
        try:
            attrs = self.extra_state_attributes
        except Exception:  # noqa: BLE001 - invalid attrs should not trigger update loops
            return {}
        return dict(attrs or {})

