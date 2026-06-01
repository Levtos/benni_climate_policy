"""Button entities for manual apply and dry run."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, HEATING_ZONES, ZONE_KITCHEN, ZONE_LIVING
from .coordinator import ClimatePolicyCoordinator
from .entity import ClimatePolicyEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: ClimatePolicyCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[ButtonEntity] = [
        ApplyNowButton(coord, None),
        DryRunButton(coord),
    ]
    entities.extend(ApplyNowButton(coord, zone) for zone in HEATING_ZONES)
    async_add_entities(entities)


class ApplyNowButton(ClimatePolicyEntity, ButtonEntity):
    def __init__(self, coord: ClimatePolicyCoordinator, zone: str | None) -> None:
        self.zone = zone
        if zone is None:
            name = "Climate Policy Apply Now"
            suffix = "apply_now"
        else:
            display = "Living Room" if zone == ZONE_LIVING else "Kitchen" if zone == ZONE_KITCHEN else zone
            name = f"{display} Climate Apply Now"
            suffix = f"{zone}_apply_now"
        super().__init__(coord, name, suffix)

    async def async_press(self) -> None:
        await self.coord.async_apply(zone=self.zone, manual=True, dry_run=False)


class DryRunButton(ClimatePolicyEntity, ButtonEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Dry Run", "dry_run")

    async def async_press(self) -> None:
        await self.coord.async_apply(zone=None, manual=True, dry_run=True)

