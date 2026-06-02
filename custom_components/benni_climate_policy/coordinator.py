"""Coordinator for Benni Climate Policy."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .apply_engine import ApplyEngine, ApplyGateState
from .const import (
    CONF_APPLY_ACTIVE,
    CONF_APPLY_COOLDOWN_SECONDS,
    CONF_BATH_FAN,
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
    HEATING_ZONES,
    PRESET,
    ZONE_BATHROOM,
    ZONE_KITCHEN,
    ZONE_LIVING,
)
from .bathroom import (
    BathroomClimateInput,
    BathroomFanPlan,
    BathroomHumidityInput,
    bath_tuning_from_options,
    decide_bathroom_climate,
    decide_bathroom_fan,
)
from .context_resolver import ContextResolver
from .models import (
    ApplyResult,
    ClimateDecision,
    EffectiveTemperatureInput,
    WindowState,
    ZoneInput,
    ZonePlan,
)
from .options import apply_cooldown_seconds_from_config
from .policy import decide_zone, effective_outdoor_temperature, empty_context, policy_tuning_from_options, policy_visibility_snapshot

_LOGGER = logging.getLogger(__name__)


def _float(value: str | None) -> float | None:
    if value in (None, "", "unknown", "unavailable", "none"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _state_value(value: str | None) -> str | None:
    if value in (None, "", "unknown", "unavailable", "none"):
        return None
    return str(value)


def _input_role(key: str) -> str:
    if key == CONF_BATH_FAN:
        return "actuator"
    if key.startswith("context_"):
        return "context"
    if key in (
        CONF_OUTDOOR_TEMPERATURE,
        CONF_OUTDOOR_FEELS_LIKE,
        CONF_FORECAST_TEMPERATURE,
        CONF_WEATHER_CONDITION,
        CONF_OUTDOOR_LUX,
        CONF_SUN,
    ):
        return "weather"
    if "window" in key or "patio_door" in key:
        return "window"
    if key.endswith("_thermostat"):
        return "thermostat"
    if key.endswith("_temperature") or key.endswith("_humidity"):
        return "room"
    if key == CONF_SYSTEM_READY:
        return "system"
    return "other"


def _input_status(state_value: str | None) -> str:
    if state_value is None:
        return "missing"
    if state_value in ("unknown", "unavailable"):
        return state_value
    return "ok"


class ClimatePolicyCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.apply_engine = ApplyEngine(hass)
        self._unsub: list[CALLBACK_TYPE] = []
        self._listeners: list[CALLBACK_TYPE] = []
        self._ha_started = False
        self._started_at = time.monotonic()
        self.decision: ClimateDecision | None = None
        self.bathroom_fan_plan: BathroomFanPlan | None = None
        self.last_apply_result: ApplyResult | None = None
        apply_zones = (*HEATING_ZONES, ZONE_BATHROOM, "bathroom_fan")
        self.last_applied_hash: dict[str, str | None] = {zone: None for zone in apply_zones}
        self.last_apply_at: dict[str, datetime | None] = {zone: None for zone in apply_zones}
        self.last_bath_fan_active_at: datetime | None = None

    @property
    def config(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    @property
    def apply_active(self) -> bool:
        return bool(self.config.get(CONF_APPLY_ACTIVE, DEFAULT_APPLY_ACTIVE))

    @property
    def cooldown_seconds(self) -> int:
        return apply_cooldown_seconds_from_config(self.config)

    @property
    def startup_block_seconds(self) -> int:
        return int(self.config.get(CONF_STARTUP_BLOCK_SECONDS, DEFAULT_STARTUP_BLOCK_SECONDS))

    @property
    def policy_tuning(self):
        return policy_tuning_from_options(self.entry.options)

    @property
    def bath_tuning(self):
        return bath_tuning_from_options(self.entry.options)

    @property
    def startup_ready(self) -> bool:
        return self._ha_started and (time.monotonic() - self._started_at) >= self.startup_block_seconds

    def add_listener(self, cb: CALLBACK_TYPE) -> None:
        self._listeners.append(cb)

    def remove_listener(self, cb: CALLBACK_TYPE) -> None:
        if cb in self._listeners:
            self._listeners.remove(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    @callback
    def async_start(self) -> None:
        if self.hass.is_running:
            self._on_started(None)
        else:
            self._unsub.append(self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, self._on_started))

        watch = {v for v in self.config.values() if isinstance(v, str) and "." in v}
        if watch:
            self._unsub.append(async_track_state_change_event(self.hass, list(watch), self._on_state_change))
        self._unsub.append(async_track_time_interval(self.hass, self._on_interval, timedelta(minutes=15)))

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()

    @callback
    def _on_started(self, _event) -> None:
        self._ha_started = True
        self._started_at = time.monotonic()
        self.hass.async_create_task(self.async_evaluate(auto_apply=False))

    @callback
    def _on_interval(self, _now) -> None:
        self.hass.async_create_task(self.async_evaluate(auto_apply=True))

    @callback
    def _on_state_change(self, _event: Event) -> None:
        self.hass.async_create_task(self.async_evaluate(auto_apply=True))

    def _state(self, key: str) -> str | None:
        entity_id = self.config.get(key)
        state = self.hass.states.get(entity_id) if entity_id else None
        return state.state if state else None

    def _float_state(self, key: str) -> float | None:
        return _float(self._state(key))

    def _sun_elevation(self) -> float | None:
        entity_id = self.config.get(CONF_SUN)
        state = self.hass.states.get(entity_id) if entity_id else None
        if not state:
            return None
        return _float(str(state.attributes.get("elevation")))

    def input_snapshot(self) -> list[dict[str, Any]]:
        keys = sorted({*PRESET, *(key for key, value in self.config.items() if isinstance(value, str))})
        out: list[dict[str, Any]] = []
        for key in keys:
            configured = self.config.get(key)
            preset = PRESET.get(key)
            entity_id = configured or preset
            state = self.hass.states.get(entity_id) if entity_id else None
            if configured and preset and configured == preset:
                source = "candidate"
            elif configured:
                source = "user configured"
            elif preset:
                source = "fallback"
            else:
                source = "missing"
            out.append({
                "role": _input_role(key),
                "key": key,
                "entity_id": entity_id,
                "state": state.state if state else None,
                "status": _input_status(state.state if state else None),
                "source": source,
            })
        return out

    def effective_input_snapshot(self) -> dict[str, Any]:
        sun_entity = self.config.get(CONF_SUN)
        sun_state = self.hass.states.get(sun_entity) if sun_entity else None
        return {
            "real_temperature": self._float_state(CONF_OUTDOOR_TEMPERATURE),
            "feels_like_temperature": self._float_state(CONF_OUTDOOR_FEELS_LIKE),
            "forecast_temperature": self._float_state(CONF_FORECAST_TEMPERATURE),
            "weather_condition": self._state(CONF_WEATHER_CONDITION),
            "outdoor_lux": self._float_state(CONF_OUTDOOR_LUX),
            "sun_elevation": self._sun_elevation(),
            "source_entities": {
                "real_temperature": self.config.get(CONF_OUTDOOR_TEMPERATURE),
                "feels_like_temperature": self.config.get(CONF_OUTDOOR_FEELS_LIKE),
                "forecast_temperature": self.config.get(CONF_FORECAST_TEMPERATURE),
                "weather_condition": self.config.get(CONF_WEATHER_CONDITION),
                "outdoor_lux": self.config.get(CONF_OUTDOOR_LUX),
                "sun": sun_entity,
            },
            "sun_state": sun_state.state if sun_state else None,
        }

    @property
    def system_ready(self) -> bool:
        external = self._state(CONF_SYSTEM_READY)
        if external in ("off", "false", "False", "unknown", "unavailable", ""):
            return False
        if self.decision is None:
            return False
        return self.decision.effective_temperature.effective_temperature is not None

    @property
    def apply_ready(self) -> bool:
        return self.apply_active and self.system_ready and self.startup_ready

    @property
    def manual_apply_possible(self) -> bool:
        return self.system_ready and self.startup_ready

    async def async_evaluate(self, *, auto_apply: bool = False) -> ClimateDecision:
        now = dt_util.now()
        tuning = self.policy_tuning
        bath_tuning = self.bath_tuning
        context = ContextResolver(self.hass, self.config).resolve()
        effective = effective_outdoor_temperature(
            EffectiveTemperatureInput(
                real_temperature=self._float_state(CONF_OUTDOOR_TEMPERATURE),
                feels_like_temperature=self._float_state(CONF_OUTDOOR_FEELS_LIKE),
                forecast_temperature=self._float_state(CONF_FORECAST_TEMPERATURE),
                weather_condition=self._state(CONF_WEATHER_CONDITION),
                outdoor_lux=self._float_state(CONF_OUTDOOR_LUX),
                sun_elevation=self._sun_elevation(),
                month=now.month,
            ),
            floor_slab_tau=tuning.floor_slab_tau,
            lux_bonus_max=tuning.lux_bonus_max,
            lux_reference=tuning.lux_reference,
            feels_like_damping=tuning.feels_like_damping,
            forecast_weight=tuning.forecast_weight,
        )
        plans = {
            ZONE_LIVING: decide_zone(self._zone_input(ZONE_LIVING), context, effective, now, tuning=tuning),
            ZONE_KITCHEN: decide_zone(self._zone_input(ZONE_KITCHEN), context, effective, now, tuning=tuning),
            ZONE_BATHROOM: decide_bathroom_climate(
                self._bathroom_climate_input(),
                context,
                effective,
                now,
                bath_tuning,
            ),
        }
        self.bathroom_fan_plan = decide_bathroom_fan(
            self._bathroom_humidity_input(),
            plans[ZONE_BATHROOM],
            now=now,
            day_state=_state_value(context.day_state.value),
            last_fan_active_at=self.last_bath_fan_active_at,
            tuning=bath_tuning,
        )
        self.decision = ClimateDecision(context, effective, plans, now, self.system_ready)
        self._notify()
        if auto_apply and self.apply_active:
            await self.async_apply(manual=False, dry_run=False)
        return self.decision

    def _zone_input(self, zone: str) -> ZoneInput:
        windows: tuple[WindowState, ...]
        if zone == ZONE_LIVING:
            windows = (
                WindowState(self._state(CONF_LIVING_WINDOW_LEFT_OPEN), self._state(CONF_LIVING_WINDOW_LEFT_TILT)),
                WindowState(self._state(CONF_LIVING_WINDOW_RIGHT_OPEN), self._state(CONF_LIVING_WINDOW_RIGHT_TILT)),
            )
        else:
            windows = (
                WindowState(self._state(CONF_KITCHEN_PATIO_OPEN), self._state(CONF_KITCHEN_PATIO_TILT)),
            )
        return ZoneInput(
            zone=zone,
            room_temperature=self._float_state(CONF_ZONE_TEMPERATURE.format(zone=zone)),
            room_humidity=self._float_state(CONF_ZONE_HUMIDITY.format(zone=zone)),
            thermostat_entity_id=self.config.get(CONF_ZONE_THERMOSTAT.format(zone=zone)),
            windows=windows,
        )

    def _bathroom_climate_input(self) -> BathroomClimateInput:
        return BathroomClimateInput(
            room_temperature=self._float_state(CONF_ZONE_TEMPERATURE.format(zone=ZONE_BATHROOM)),
            room_humidity=self._float_state(CONF_ZONE_HUMIDITY.format(zone=ZONE_BATHROOM)),
            thermostat_entity_id=self.config.get(CONF_ZONE_THERMOSTAT.format(zone=ZONE_BATHROOM)),
        )

    def _bathroom_humidity_input(self) -> BathroomHumidityInput:
        return BathroomHumidityInput(
            bathroom_temperature=self._float_state(CONF_ZONE_TEMPERATURE.format(zone=ZONE_BATHROOM)),
            bathroom_humidity=self._float_state(CONF_ZONE_HUMIDITY.format(zone=ZONE_BATHROOM)),
            living_temperature=self._float_state(CONF_ZONE_TEMPERATURE.format(zone=ZONE_LIVING)),
            living_humidity=self._float_state(CONF_ZONE_HUMIDITY.format(zone=ZONE_LIVING)),
        )

    async def async_set_apply_active(self, value: bool) -> None:
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_APPLY_ACTIVE: bool(value)},
        )
        await self.async_evaluate(auto_apply=bool(value))

    async def async_apply(
        self,
        *,
        zone: str | None = None,
        manual: bool,
        dry_run: bool,
    ) -> ApplyResult:
        if self.decision is None:
            await self.async_evaluate(auto_apply=False)
        decision = self.decision
        if decision is None:
            self.last_apply_result = ApplyResult("error", "no_decision", [])
            self._notify()
            return self.last_apply_result

        selected = [zone] if zone else [*HEATING_ZONES, ZONE_BATHROOM, "bathroom_fan"]
        now = dt_util.now()
        apply_specs = []
        switch_specs = []
        for zone_id in selected:
            if zone_id == "bathroom_fan":
                plan = self.bathroom_fan_plan
                if plan is None:
                    continue
                target = self.config.get(CONF_BATH_FAN)
                target_state = self.hass.states.get(target).state if target and self.hass.states.get(target) else None
                gate = ApplyGateState(
                    apply_active=self.apply_active,
                    manual=manual,
                    dry_run=dry_run,
                    system_ready=self.system_ready,
                    startup_ready=self.startup_ready,
                    cooldown_seconds=self.cooldown_seconds,
                    now=now,
                    target_state=target_state,
                    last_applied_hash=self.last_applied_hash.get(zone_id),
                    last_apply_at=self.last_apply_at.get(zone_id),
                )
                switch_specs.append((plan, target, gate))
                continue
            plan = decision.zone(zone_id)
            if plan is None:
                continue
            target = self.config.get(CONF_ZONE_THERMOSTAT.format(zone=zone_id))
            target_state = self.hass.states.get(target).state if target and self.hass.states.get(target) else None
            gate = ApplyGateState(
                apply_active=self.apply_active,
                manual=manual,
                dry_run=dry_run,
                system_ready=self.system_ready,
                startup_ready=self.startup_ready,
                cooldown_seconds=self.cooldown_seconds,
                now=now,
                target_state=target_state,
                last_applied_hash=self.last_applied_hash.get(zone_id),
                last_apply_at=self.last_apply_at.get(zone_id),
            )
            apply_specs.append((plan, target, gate))

        result = await self.apply_engine.async_apply_many(apply_specs)
        switch_actions = [
            await self.apply_engine.async_apply_switch_plan(plan, target_entity_id=target, gate=gate)
            for plan, target, gate in switch_specs
        ]
        if switch_actions:
            actions = [*result.actions, *switch_actions]
            if any(a.status == "error" for a in actions):
                status = "error"
            elif any(a.status == "applied" for a in actions):
                status = "applied"
            elif all(a.status == "dry_run" for a in actions):
                status = "dry_run"
            elif any(a.status == "blocked" for a in actions):
                status = "blocked"
            else:
                status = "skipped"
            result = ApplyResult(status, status, actions, dry_run=all(a.status == "dry_run" for a in actions))
        if not dry_run:
            for action in result.actions:
                if action.zone == "bathroom_fan":
                    if self.bathroom_fan_plan:
                        self.bathroom_fan_plan = replace(
                            self.bathroom_fan_plan,
                            apply_status=action.status,
                            apply_block_reason=action.reason,
                        )
                    plan = self.bathroom_fan_plan
                else:
                    plan = decision.zone(action.zone)
                    if plan:
                        plan.apply_status = action.status
                        plan.apply_block_reason = action.reason
                if action.status == "applied":
                    self.last_applied_hash[action.zone] = action.plan_hash
                    self.last_apply_at[action.zone] = now
                    if action.zone == "bathroom_fan":
                        if self.bathroom_fan_plan and self.bathroom_fan_plan.target_switch_state == "on":
                            self.last_bath_fan_active_at = now
                    elif plan:
                        plan.last_applied = now.isoformat()
        self.last_apply_result = result
        self._notify()
        return result

    def zone_plan(self, zone: str) -> ZonePlan | None:
        return self.decision.zone(zone) if self.decision else None

    def bathroom_debug(self) -> dict[str, Any]:
        return {
            "climate_plan": self.zone_plan(ZONE_BATHROOM).as_dict() if self.zone_plan(ZONE_BATHROOM) else None,
            "fan_plan": self.bathroom_fan_plan.as_dict() if self.bathroom_fan_plan else None,
            "tuning": self.bath_tuning.as_dict(),
        }

    def debug_summary(self) -> str:
        if self.decision is None:
            return "not_calculated"
        modes = ",".join(f"{z}:{p.profile}" for z, p in self.decision.zone_plans.items())
        return f"ready={self.system_ready}; apply={self.apply_active}; {modes}"

    def debug_payload(self) -> dict[str, Any]:
        now = dt_util.now()
        effective_temperature = (
            self.decision.effective_temperature.effective_temperature
            if self.decision
            else None
        )
        thresholds = policy_visibility_snapshot(now.month, effective_temperature, self.policy_tuning)
        return {
            "system_ready": self.system_ready,
            "apply_active": self.apply_active,
            "apply_ready": self.apply_ready,
            "manual_apply_possible": self.manual_apply_possible,
            "startup_ready": self.startup_ready,
            "startup_block_seconds": self.startup_block_seconds,
            "cooldown_seconds": self.cooldown_seconds,
            "thresholds": {
                **thresholds,
                "apply_cooldowns": {
                    "cooldown_seconds": self.cooldown_seconds,
                    "startup_block_seconds": self.startup_block_seconds,
                    "startup_ready": self.startup_ready,
                    "last_apply_at": {
                        zone: value.isoformat() if value else None
                        for zone, value in self.last_apply_at.items()
                    },
                },
            },
            "last_applied_hash": dict(self.last_applied_hash),
            "last_apply_at": {
                zone: value.isoformat() if value else None
                for zone, value in self.last_apply_at.items()
            },
            "last_apply_result": self.last_apply_result.as_dict() if self.last_apply_result else None,
            "effective_inputs": self.effective_input_snapshot(),
            "bathroom": self.bathroom_debug(),
            "inputs": self.input_snapshot(),
        }

