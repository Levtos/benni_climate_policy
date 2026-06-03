"""Sensor entities for Benni Climate Policy."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, HEATING_ZONES, ZONE_BATHROOM, ZONE_KITCHEN, ZONE_LIVING
from .coordinator import ClimatePolicyCoordinator
from .diagnostics import compact_debug_attributes
from .entity import ClimatePolicyEntity


def _compact_zone_plan(plan) -> dict[str, Any]:
    return {
        "zone": plan.zone,
        "profile": plan.profile,
        "target_temperature": plan.target_temperature,
        "thermostat_target_temperature": plan.target_temperature,
        "policy_target_temperature": plan.raw_target_temperature,
        "raw_target_temperature": plan.raw_target_temperature,
        "floor_slab_delta": plan.floor_slab_delta,
        "reason": plan.reason,
        "apply_status": plan.apply_status,
        "apply_block_reason": plan.apply_block_reason,
        "apply_blocked": plan.apply_blocked,
        "blocked_by": list(plan.blocked_by),
        "input_quality": plan.input_quality,
        "effective_outdoor_temperature": plan.effective_outdoor_temperature,
        "is_boost_active": plan.is_boost_active,
        "room_comfort_label": plan.room_comfort.label if plan.room_comfort else None,
        "room_comfort_reason": plan.room_comfort.reason if plan.room_comfort else None,
        "room_comfort_quality": plan.room_comfort.quality if plan.room_comfort else None,
        "perceived_room_temperature": plan.room_comfort.perceived_temperature if plan.room_comfort else None,
        "hysteresis_state": plan.hysteresis_state,
        "policy_config_hash": plan.policy_config_hash,
        "plan_hash": plan.plan_hash,
        "last_applied": plan.last_applied,
    }


def _compact_fan_plan(plan) -> dict[str, Any]:
    diagnostics = plan.diagnostics or {}
    return {
        "zone": plan.zone,
        "mode": plan.mode,
        "reason": plan.reason,
        "target_switch_state": plan.target_switch_state,
        "apply_status": plan.apply_status,
        "apply_block_reason": plan.apply_block_reason,
        "apply_blocked": plan.apply_blocked,
        "blocked_by": list(plan.blocked_by),
        "dewpoint": diagnostics.get("dewpoint"),
        "absolute_humidity_bathroom": diagnostics.get("absolute_humidity_bathroom"),
        "absolute_humidity_living": diagnostics.get("absolute_humidity_living"),
        "ah_delta": diagnostics.get("ah_delta"),
        "heating_fan_coordination_state": diagnostics.get("heating_fan_coordination_state"),
        "policy_config_hash": plan.policy_config_hash,
        "plan_hash": plan.plan_hash,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: ClimatePolicyCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[SensorEntity] = [
        EffectiveOutdoorTemperatureSensor(coord),
        ForecastTemperature3hSensor(coord),
        OutdoorFeelsLikeTemperatureSensor(coord),
        ApplyStatusSensor(coord),
        LastApplySensor(coord),
        DebugSummarySensor(coord),
    ]
    for zone in (*HEATING_ZONES, ZONE_BATHROOM):
        entities.extend([
            ZoneModeSensor(coord, zone),
            ZoneTargetTempSensor(coord, zone),
            ZonePlanHashSensor(coord, zone),
            ZonePendingPlanHashSensor(coord, zone),
            ZoneLastAppliedPlanHashSensor(coord, zone),
            ZoneApplyReasonSensor(coord, zone),
        ])
    entities.extend([
        BathroomFanModeSensor(coord),
        BathroomFanPlanHashSensor(coord),
    ])
    async_add_entities(entities)


class EffectiveOutdoorTemperatureSensor(ClimatePolicyEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Effective Outdoor Temperature", "effective_outdoor_temperature")

    @property
    def native_value(self):
        return self.coord.decision.effective_temperature.effective_temperature if self.coord.decision else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        inputs = self.coord.effective_input_snapshot()
        forecast_resolution = inputs.get("forecast_resolution") or {}
        feels_like_resolution = inputs.get("feels_like_resolution") or {}
        compact_inputs = {
            "real_temperature": inputs.get("real_temperature"),
            "feels_like_temperature": inputs.get("feels_like_temperature"),
            "forecast_temperature": inputs.get("forecast_temperature"),
            "weather_condition": inputs.get("weather_condition"),
            "source_entities": inputs.get("source_entities"),
            "forecast_source": forecast_resolution.get("source"),
            "forecast_quality": forecast_resolution.get("quality"),
            "forecast_reason": forecast_resolution.get("reason"),
            "feels_like_source": feels_like_resolution.get("source"),
            "feels_like_quality": feels_like_resolution.get("quality"),
            "feels_like_reason": feels_like_resolution.get("reason"),
        }
        if not self.coord.decision:
            return compact_inputs
        breakdown = self.coord.decision.effective_temperature
        return {
            "real_temperature": breakdown.real_temperature,
            "effective_temperature": breakdown.effective_temperature,
            "input_quality": breakdown.input_quality,
            "debug_payload_available": True,
            "inputs": compact_inputs,
        }


class ForecastTemperature3hSensor(ClimatePolicyEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Forecast Temperature 3h", "forecast_temperature_3h")

    @property
    def native_value(self):
        return self.coord.weather_resolution.forecast_temperature if self.coord.weather_resolution else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coord.weather_resolution:
            return {}
        diag = self.coord.weather_resolution.forecast
        return {
            "source": diag.source,
            "weather_entity": diag.weather_entity,
            "quality": diag.quality,
            "fallback_used": diag.fallback_used,
            "reason": diag.reason,
            "target_time": diag.forecast_datetime,
            "forecast_time": diag.forecast_datetime,
        }


class OutdoorFeelsLikeTemperatureSensor(ClimatePolicyEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Outdoor Feels Like Temperature", "outdoor_feels_like_temperature")

    @property
    def native_value(self):
        return self.coord.weather_resolution.feels_like_temperature if self.coord.weather_resolution else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coord.weather_resolution:
            return {}
        diag = self.coord.weather_resolution.feels_like
        return {
            "source": diag.source,
            "source_entity_id": diag.source_entity_id,
            "quality": diag.quality,
            "fallback_used": diag.fallback_used,
            "reason": diag.reason,
        }


class ApplyStatusSensor(ClimatePolicyEntity, SensorEntity):
    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, "Climate Policy Apply Status", "apply_status")

    @property
    def native_value(self):
        return self.coord.last_apply_result.status if self.coord.last_apply_result else "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        result = self.coord.last_apply_result
        return {
            "status": result.status if result else "idle",
            "reason": result.reason if result else "idle",
            "dry_run": result.dry_run if result else False,
            "action_count": len(result.actions) if result else 0,
            "apply_active": self.coord.apply_active,
            "apply_ready": self.coord.apply_ready,
            "manual_apply_possible": self.coord.manual_apply_possible,
            "system_ready": self.coord.system_ready,
            "startup_ready": self.coord.startup_ready,
        }


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
        payload = {
            "system_ready": self.coord.system_ready,
            "apply_active": self.coord.apply_active,
            "apply_status": self.coord.last_apply_result.status if self.coord.last_apply_result else "idle",
            "effective_outdoor_temperature": self.coord.decision.effective_temperature.as_dict(),
            "plans": {
                zone: _compact_zone_plan(plan)
                for zone, plan in self.coord.decision.zone_plans.items()
            },
            "bathroom": self.coord.bathroom_debug(),
            "last_apply_result": self.coord.last_apply_result.as_dict() if self.coord.last_apply_result else None,
        }
        return compact_debug_attributes(payload)


class ZoneSensorBase(ClimatePolicyEntity, SensorEntity):
    suffix = ""
    label = ""

    def __init__(self, coord: ClimatePolicyCoordinator, zone: str) -> None:
        self.zone = zone
        display = "Living Room" if zone == ZONE_LIVING else "Kitchen" if zone == ZONE_KITCHEN else "Bathroom"
        super().__init__(coord, f"{display} Climate {self.label}", f"{zone}_{self.suffix}")

    @property
    def plan(self):
        return self.coord.zone_plan(self.zone)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _compact_zone_plan(self.plan) if self.plan else {}


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


class BathroomFanSensorBase(ClimatePolicyEntity, SensorEntity):
    suffix = ""
    label = ""

    def __init__(self, coord: ClimatePolicyCoordinator) -> None:
        super().__init__(coord, f"Bathroom Fan {self.label}", f"bathroom_fan_{self.suffix}")

    @property
    def plan(self):
        return self.coord.bathroom_fan_plan

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return _compact_fan_plan(self.plan) if self.plan else {}


class BathroomFanModeSensor(BathroomFanSensorBase):
    suffix = "mode"
    label = "Mode"

    @property
    def native_value(self):
        return self.plan.mode if self.plan else "unknown"


class BathroomFanPlanHashSensor(BathroomFanSensorBase):
    suffix = "plan_hash"
    label = "Plan Hash"

    @property
    def native_value(self):
        return self.plan.plan_hash if self.plan else "unknown"

