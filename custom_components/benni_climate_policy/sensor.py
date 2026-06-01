"""Sensor entities for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, HEATING_ZONES, ZONE_KITCHEN, ZONE_LIVING
from .coordinator import ClimatePolicyCoordinator
from .entity import ClimatePolicyEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: ClimatePolicyCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[SensorEntity] = [
        EffectiveOutdoorTemperatureSensor(coord),
        ApplyStatusSensor(coord),
        LastApplySensor(coord),
        DebugSummarySensor(coord),
    ]
    for zone in HEATING_ZONES:
        entities.extend([
            ZoneModeSensor(coord, zone),
            ZoneTargetTempSensor(coord, zone),
            ZonePlanHashSensor(coord, zone),
            ZonePendingPlanHashSensor(coord, zone),
            ZoneLastAppliedPlanHashSensor(coord, zone),
            ZoneApplyReasonSensor(coord, zone),
        ])
    async_add_entities(entities)


class EffectiveOutdoorTemperatureSensor(ClimatePolicyEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Effective Outdoor Temperature", "effective_outdoor_temperature")

    @property
    def native_value(self):
        return self.coord.decision.effective_temperature.effective_temperature if self.coord.decision else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coord.decision.effective_temperature.as_dict() if self.coord.decision else {}


class ApplyStatusSensor(ClimatePolicyEntity, SensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Apply Status", "apply_status")

    @property
    def native_value(self):
        return self.coord.last_apply_result.status if self.coord.last_apply_result else "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coord.last_apply_result.as_dict() if self.coord.last_apply_result else {}


class LastApplySensor(ClimatePolicyEntity, SensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Last Apply", "last_apply")

    @property
    def native_value(self):
        times = [v for v in self.coord.last_apply_at.values() if v is not None]
        return max(times).isoformat() if times else "never"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {zone: value.isoformat() if value else None for zone, value in self.coord.last_apply_at.items()}


class DebugSummarySensor(ClimatePolicyEntity, SensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Debug Summary", "debug_summary")

    @property
    def native_value(self):
        return self.coord.debug_summary()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coord.decision:
            return {}
        return {
            "context": self.coord.decision.context.as_dict(),
            "effective_outdoor_temperature": self.coord.decision.effective_temperature.as_dict(),
            "plans": {zone: plan.as_dict() for zone, plan in self.coord.decision.zone_plans.items()},
        }


class ZoneSensorBase(ClimatePolicyEntity, SensorEntity):
    suffix = ""
    label = ""

    def __init__(self, coord: ClimatePolicyCoordinator, zone: str) -> None:
        self.zone = zone
        display = "Living Room" if zone == ZONE_LIVING else "Kitchen" if zone == ZONE_KITCHEN else zone
        super().__init__(coord, f"{display} Climate {self.label}", f"{zone}_{self.suffix}")

    @property
    def plan(self):
        return self.coord.zone_plan(self.zone)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.plan.as_dict() if self.plan else {}


class ZoneModeSensor(ZoneSensorBase):
    suffix = "mode"
    label = "Mode"

    @property
    def native_value(self):
        return self.plan.profile if self.plan else "unknown"


class ZoneTargetTempSensor(ZoneSensorBase):
    suffix = "target_temp"
    label = "Target Temp"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        return self.plan.target_temperature if self.plan else None


class ZonePlanHashSensor(ZoneSensorBase):
    suffix = "plan_hash"
    label = "Plan Hash"

    @property
    def native_value(self):
        return self.plan.plan_hash if self.plan else "unknown"


class ZonePendingPlanHashSensor(ZonePlanHashSensor):
    suffix = "pending_plan_hash"
    label = "Pending Plan Hash"


class ZoneLastAppliedPlanHashSensor(ZoneSensorBase):
    suffix = "last_applied_plan_hash"
    label = "Last Applied Plan Hash"

    @property
    def native_value(self):
        return self.coord.last_applied_hash.get(self.zone) or "never"


class ZoneApplyReasonSensor(ZoneSensorBase):
    suffix = "apply_reason"
    label = "Apply Reason"

    @property
    def native_value(self):
        return self.plan.apply_block_reason if self.plan else "not_calculated"

