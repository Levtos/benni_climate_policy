"""Recorder-safe and full diagnostics payload helpers."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping


def _plan(payload: Mapping[str, Any], zone: str) -> Mapping[str, Any]:
    plans = payload.get("plans") or {}
    if isinstance(plans, Mapping):
        value = plans.get(zone) or {}
        return value if isinstance(value, Mapping) else {}
    return {}


def _last_apply(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    result = payload.get("last_apply_result") or {}
    if not result:
        debug = payload.get("debug") or {}
        result = debug.get("last_apply_result") if isinstance(debug, Mapping) else {}
    return result if isinstance(result, Mapping) else {}


def compact_debug_attributes(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a small attributes dict suitable for Home Assistant Recorder."""
    living = _plan(payload, "living_room")
    kitchen = _plan(payload, "kitchen")
    bathroom = _plan(payload, "bathroom")
    bathroom_debug = payload.get("bathroom") or {}
    if not bathroom_debug and isinstance(payload.get("debug"), Mapping):
        bathroom_debug = payload["debug"].get("bathroom") or {}
    fan = bathroom_debug.get("fan_plan") if isinstance(bathroom_debug, Mapping) else {}
    fan = fan if isinstance(fan, Mapping) else {}
    last_apply = _last_apply(payload)
    effective = payload.get("effective_outdoor_temperature")
    if isinstance(effective, Mapping):
        effective_value = effective.get("effective_temperature")
    else:
        effective_value = effective
    return {
        "system_ready": payload.get("system_ready"),
        "integration_version": payload.get("integration_version"),
        "apply_active": payload.get("apply_active"),
        "apply_status": payload.get("apply_status"),
        "effective_outdoor_temperature": effective_value,
        "living_room_mode": living.get("profile"),
        "living_room_target_temp": living.get("target_temperature"),
        "living_room_policy_target_temp": living.get("policy_target_temperature") or living.get("raw_target_temperature"),
        "living_room_floor_slab_delta": living.get("floor_slab_delta"),
        "living_room_allowed_profile": living.get("allowed_profile"),
        "living_room_heat_demand": living.get("heat_demand"),
        "living_room_indoor_reason": living.get("indoor_heat_demand_reason"),
        "living_room_comfort": living.get("room_comfort_label"),
        "living_room_policy_reason": living.get("reason"),
        "living_room_apply_blocker": living.get("apply_block_reason"),
        "kitchen_mode": kitchen.get("profile"),
        "kitchen_target_temp": kitchen.get("target_temperature"),
        "kitchen_policy_target_temp": kitchen.get("policy_target_temperature") or kitchen.get("raw_target_temperature"),
        "kitchen_floor_slab_delta": kitchen.get("floor_slab_delta"),
        "kitchen_allowed_profile": kitchen.get("allowed_profile"),
        "kitchen_heat_demand": kitchen.get("heat_demand"),
        "kitchen_indoor_reason": kitchen.get("indoor_heat_demand_reason"),
        "kitchen_comfort": kitchen.get("room_comfort_label"),
        "kitchen_policy_reason": kitchen.get("reason"),
        "kitchen_apply_blocker": kitchen.get("apply_block_reason"),
        "bathroom_mode": bathroom.get("profile"),
        "bathroom_target_temp": bathroom.get("target_temperature"),
        "bathroom_policy_target_temp": bathroom.get("policy_target_temperature") or bathroom.get("raw_target_temperature"),
        "bathroom_floor_slab_delta": bathroom.get("floor_slab_delta"),
        "bathroom_allowed_profile": bathroom.get("allowed_profile"),
        "bathroom_heat_demand": bathroom.get("heat_demand"),
        "bathroom_indoor_reason": bathroom.get("indoor_heat_demand_reason"),
        "bathroom_comfort": bathroom.get("room_comfort_label"),
        "bathroom_fan_mode": fan.get("mode"),
        "bathroom_fan_reason": fan.get("reason") or fan.get("fan_reason"),
        "last_apply_status": last_apply.get("status"),
        "last_apply_reason": last_apply.get("reason"),
        "debug_payload_available": True,
    }


def compact_json_size(payload: Mapping[str, Any]) -> int:
    return len(json.dumps(payload, default=str).encode("utf-8"))


def full_debug_payload(
    *,
    timestamp: datetime | str,
    context: Mapping[str, Any] | None,
    effective_outdoor_temperature: Mapping[str, Any] | None,
    plans: Mapping[str, Any],
    debug: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the full read-only diagnostics payload served by the HTTP view."""
    last_apply = debug.get("last_apply_result")
    return {
        "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
        "integration_version": debug.get("integration_version"),
        "context": dict(context or {}),
        "effective_outdoor_temperature": dict(effective_outdoor_temperature or {}),
        "plans": dict(plans),
        "thresholds": debug.get("thresholds"),
        "tuning_options": debug.get("tuning_options"),
        "last_apply_result": last_apply,
        "dry_run_diagnostics": last_apply if isinstance(last_apply, Mapping) and last_apply.get("dry_run") else None,
        "inputs": debug.get("inputs"),
        "effective_inputs": debug.get("effective_inputs"),
        "weather_resolution": (debug.get("effective_inputs") or {}).get("weather_resolution")
        if isinstance(debug.get("effective_inputs"), Mapping)
        else None,
        "bathroom": debug.get("bathroom"),
        "performance": debug.get("performance"),
        "debug": dict(debug),
    }
