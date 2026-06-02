"""Binary sensor entities for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, HEATING_ZONES, ZONE_BATHROOM, ZONE_KITCHEN, ZONE_LIVING
from .coordinator import ClimatePolicyCoordinator
from .entity import ClimatePolicyEntity


def _zone_block_attrs(plan) -> dict[str, Any]:
    return {
        "zone": plan.zone,
        "profile": plan.profile,
        "target_temperature": plan.target_temperature,
        "reason": plan.reason,
        "apply_block_reason": plan.apply_block_reason,
        "blocked_by": list(plan.blocked_by),
        "plan_hash": plan.plan_hash,
    }


def _fan_block_attrs(plan) -> dict[str, Any]:
    return {
        "zone": plan.zone,
        "mode": plan.mode,
        "reason": plan.reason,
        "target_switch_state": plan.target_switch_state,
        "apply_block_reason": plan.apply_block_reason,
        "blocked_by": list(plan.blocked_by),
        "plan_hash": plan.plan_hash,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: ClimatePolicyCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[BinarySensorEntity] = [
        SystemReadyBinarySensor(coord),
        ApplyReadyBinarySensor(coord),
    ]
    entities.extend(ZoneApplyBlockedBinarySensor(coord, zone) for zone in (*HEATING_ZONES, ZONE_BATHROOM))
    entities.append(BathroomFanApplyBlockedBinarySensor(coord))
    async_add_entities(entities)


class SystemReadyBinarySensor(ClimatePolicyEntity, BinarySensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate System Ready", "system_ready")

    @property
    def is_on(self) -> bool:
        return self.coord.system_ready

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "startup_ready": self.coord.startup_ready,
            "debug": self.coord.debug_summary(),
            "debug_payload_available": True,
        }


class ApplyReadyBinarySensor(ClimatePolicyEntity, BinarySensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Apply Ready", "apply_ready")

    @property
    def is_on(self) -> bool:
        return self.coord.apply_ready

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "apply_active": self.coord.apply_active,
            "system_ready": self.coord.system_ready,
            "startup_ready": self.coord.startup_ready,
            "manual_apply_possible": self.coord.manual_apply_possible,
        }


class ZoneApplyBlockedBinarySensor(ClimatePolicyEntity, BinarySensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator, zone: str) -> None:
        self.zone = zone
        display = "Living Room" if zone == ZONE_LIVING else "Kitchen" if zone == ZONE_KITCHEN else "Bathroom"
        super().__init__(coord, f"{display} Climate Apply Blocked", f"{zone}_apply_blocked")

    @property
    def is_on(self) -> bool:
        plan = self.coord.zone_plan(self.zone)
        return bool(plan.apply_blocked) if plan else True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        plan = self.coord.zone_plan(self.zone)
        return _zone_block_attrs(plan) if plan else {"reason": "not_calculated"}


class BathroomFanApplyBlockedBinarySensor(ClimatePolicyEntity, BinarySensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Bathroom Fan Apply Blocked", "bathroom_fan_apply_blocked")

    @property
    def is_on(self) -> bool:
        plan = self.coord.bathroom_fan_plan
        return bool(plan.apply_blocked) if plan else True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        plan = self.coord.bathroom_fan_plan
        return _fan_block_attrs(plan) if plan else {"reason": "not_calculated"}

