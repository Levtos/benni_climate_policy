"""Internal Apply Engine for Benni Climate Policy."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .models import ApplyActionResult, ApplyResult, ZonePlan


@dataclass(frozen=True)
class ApplyGateState:
    apply_active: bool
    manual: bool
    dry_run: bool
    system_ready: bool
    startup_ready: bool
    cooldown_seconds: int
    now: datetime
    target_state: str | None
    last_applied_hash: str | None
    last_apply_at: datetime | None


def evaluate_apply_gate(
    plan: ZonePlan,
    target_entity_id: str | None,
    gate: ApplyGateState,
) -> ApplyActionResult:
    if gate.dry_run:
        return ApplyActionResult(plan.zone, "dry_run", "dry_run", target_entity_id, plan.plan_hash)
    if not gate.manual and not gate.apply_active:
        return ApplyActionResult(plan.zone, "blocked", "auto_apply_inactive", target_entity_id, plan.plan_hash)
    if not gate.system_ready:
        return ApplyActionResult(plan.zone, "blocked", "system_not_ready", target_entity_id, plan.plan_hash)
    if not gate.startup_ready:
        return ApplyActionResult(plan.zone, "blocked", "startup_quiet_period", target_entity_id, plan.plan_hash)
    if plan.apply_blocked:
        return ApplyActionResult(plan.zone, "blocked", plan.apply_block_reason, target_entity_id, plan.plan_hash)
    if not target_entity_id:
        return ApplyActionResult(plan.zone, "blocked", "target_entity_missing", target_entity_id, plan.plan_hash)
    if gate.target_state in (None, "unknown", "unavailable", ""):
        return ApplyActionResult(plan.zone, "error", "target_entity_unavailable", target_entity_id, plan.plan_hash)
    if gate.last_applied_hash == plan.plan_hash:
        return ApplyActionResult(plan.zone, "skipped", "plan_unchanged", target_entity_id, plan.plan_hash)
    if gate.last_apply_at and gate.now - gate.last_apply_at < timedelta(seconds=gate.cooldown_seconds):
        return ApplyActionResult(plan.zone, "blocked", "cooldown_active", target_entity_id, plan.plan_hash)
    return ApplyActionResult(plan.zone, "applied", "ok", target_entity_id, plan.plan_hash)


def _call(
    service: str,
    target_entity_id: str | None,
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "domain": "climate",
        "service": service,
        "target": {"entity_id": target_entity_id} if target_entity_id else {},
        "service_data": dict(data),
    }


def _same_temperature(value: Any, target: float) -> bool:
    try:
        return abs(float(value) - target) < 0.05
    except (TypeError, ValueError):
        return False


def _planned_service_calls(
    plan: ZonePlan,
    target_entity_id: str | None,
    target_state: Any,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    if not target_entity_id or target_state is None:
        return [], "blocked_by_gate", {"gate_reason": "target_entity_missing"}

    state_value = getattr(target_state, "state", None)
    attrs = getattr(target_state, "attributes", {}) or {}
    hvac_modes = list(attrs.get("hvac_modes", []))
    current_temperature = attrs.get("temperature")
    calls: list[dict[str, Any]] = []

    if plan.profile == "off":
        if not _same_temperature(current_temperature, 10.0):
            calls.append(_call("set_temperature", target_entity_id, {"temperature": 10.0}))
        if "off" in hvac_modes and state_value != "off":
            calls.append(_call("set_hvac_mode", target_entity_id, {"hvac_mode": "off"}))
        reason = "would_call_services" if calls else "already_at_target"
        return calls, reason, {
            "planned_hvac_mode": "off" if "off" in hvac_modes else None,
            "planned_temperature": 10.0,
            "current_hvac_mode": state_value,
            "current_temperature": current_temperature,
        }

    if state_value != "heat" and "heat" in hvac_modes:
        calls.append(_call("set_hvac_mode", target_entity_id, {"hvac_mode": "heat"}))
    if not _same_temperature(current_temperature, plan.target_temperature) or state_value != "heat":
        calls.append(_call(
            "set_temperature",
            target_entity_id,
            {"temperature": plan.target_temperature, "hvac_mode": "heat"},
        ))
    reason = "would_call_services" if calls else "already_at_target"
    return calls, reason, {
        "planned_hvac_mode": "heat",
        "planned_temperature": plan.target_temperature,
        "current_hvac_mode": state_value,
        "current_temperature": current_temperature,
    }


class ApplyEngine:
    def __init__(self, hass: "HomeAssistant") -> None:
        self.hass = hass

    async def async_apply_plan(
        self,
        plan: ZonePlan,
        *,
        target_entity_id: str | None,
        gate: ApplyGateState,
    ) -> ApplyActionResult:
        result = evaluate_apply_gate(plan, target_entity_id, gate)
        if result.status == "dry_run":
            target_state = self.hass.states.get(target_entity_id) if target_entity_id else None
            hypothetical_gate = evaluate_apply_gate(plan, target_entity_id, replace(gate, dry_run=False))
            if hypothetical_gate.status == "applied":
                calls, reason, details = _planned_service_calls(plan, target_entity_id, target_state)
            elif hypothetical_gate.reason == "plan_unchanged":
                calls, reason, details = [], "no_relevant_change", {"gate_reason": hypothetical_gate.reason}
            else:
                calls, reason, details = [], "blocked_by_gate", {
                    "gate_status": hypothetical_gate.status,
                    "gate_reason": hypothetical_gate.reason,
                }
            return ApplyActionResult(
                result.zone,
                "dry_run",
                reason,
                result.target_entity_id,
                result.plan_hash,
                calls,
                details,
            )
        if result.status != "applied":
            return result

        calls: list[dict[str, Any]] = []
        if plan.profile == "off":
            calls.append(_call("set_temperature", target_entity_id, {"temperature": 10.0}))
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"temperature": 10.0},
                target={"entity_id": target_entity_id},
                blocking=False,
            )
            state = self.hass.states.get(target_entity_id) if target_entity_id else None
            modes = state.attributes.get("hvac_modes", []) if state else []
            if "off" in modes:
                calls.append(_call("set_hvac_mode", target_entity_id, {"hvac_mode": "off"}))
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {"hvac_mode": "off"},
                    target={"entity_id": target_entity_id},
                    blocking=False,
                )
        else:
            calls.append(_call(
                "set_temperature",
                target_entity_id,
                {"temperature": plan.target_temperature, "hvac_mode": "heat"},
            ))
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"temperature": plan.target_temperature, "hvac_mode": "heat"},
                target={"entity_id": target_entity_id},
                blocking=False,
            )
        return ApplyActionResult(
            result.zone,
            result.status,
            result.reason,
            result.target_entity_id,
            result.plan_hash,
            calls,
        )

    async def async_apply_many(
        self,
        plans: list[tuple[ZonePlan, str | None, ApplyGateState]],
    ) -> ApplyResult:
        actions = [
            await self.async_apply_plan(plan, target_entity_id=target, gate=gate)
            for plan, target, gate in plans
        ]
        if not actions:
            return ApplyResult("skipped", "no_zones", [])
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
        return ApplyResult(status, status, actions, dry_run=all(a.status == "dry_run" for a in actions))
