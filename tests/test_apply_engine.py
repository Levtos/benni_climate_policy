from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from custom_components.benni_climate_policy.apply_engine import ApplyEngine, ApplyGateState, evaluate_apply_gate
from custom_components.benni_climate_policy.bathroom import BathroomFanPlan
from custom_components.benni_climate_policy.options import apply_cooldown_seconds_from_config
from custom_components.benni_climate_policy.models import ZonePlan


def plan(hash_reason="ok", blocked=None):
    return ZonePlan(
        zone="living_room",
        profile="spar",
        target_temperature=21.0,
        raw_target_temperature=21.0,
        reason=hash_reason,
        blocked_by=blocked or [],
        apply_block_reason=", ".join(blocked or []) if blocked else "none",
    )


def gate(**kw):
    now = datetime(2026, 1, 1, 12)
    data = {
        "apply_active": True,
        "manual": False,
        "dry_run": False,
        "system_ready": True,
        "startup_ready": True,
        "cooldown_seconds": 600,
        "now": now,
        "target_state": "heat",
        "last_applied_hash": None,
        "last_apply_at": None,
    }
    data.update(kw)
    return ApplyGateState(**data)


def test_apply_active_false_blocks_auto_apply():
    result = evaluate_apply_gate(plan(), "climate.living", gate(apply_active=False, manual=False))
    assert result.status == "blocked"
    assert result.reason == "auto_apply_inactive"


def test_manual_apply_ignores_auto_toggle_but_not_gates():
    result = evaluate_apply_gate(plan(), "climate.living", gate(apply_active=False, manual=True))
    assert result.status == "applied"

    blocked = evaluate_apply_gate(plan(), "climate.living", gate(apply_active=False, manual=True, system_ready=False))
    assert blocked.status == "blocked"
    assert blocked.reason == "system_not_ready"


def test_dry_run_always_possible():
    result = evaluate_apply_gate(plan(blocked=["window_blocks"]), None, gate(dry_run=True, apply_active=False, system_ready=False))
    assert result.status == "dry_run"


def test_unchanged_plan_is_not_reapplied():
    p = plan()
    result = evaluate_apply_gate(p, "climate.living", gate(last_applied_hash=p.plan_hash))
    assert result.status == "skipped"
    assert result.reason == "plan_unchanged"


def test_unavailable_thermostat_returns_error():
    result = evaluate_apply_gate(plan(), "climate.living", gate(target_state="unavailable"))
    assert result.status == "error"
    assert result.reason == "target_entity_unavailable"


def test_cooldown_blocks_reapply():
    result = evaluate_apply_gate(plan(), "climate.living", gate(last_apply_at=datetime(2026, 1, 1, 11, 55)))
    assert result.status == "blocked"
    assert result.reason == "cooldown_active"


class _FakeState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class _FakeStates:
    def __init__(self):
        self._states = {
            "climate.living": _FakeState("off", {"hvac_modes": ["off", "heat"], "temperature": 18.0}),
            "switch.bath_fan": _FakeState("off"),
            "switch.unavailable_fan": _FakeState("unavailable"),
        }

    def get(self, entity_id):
        return self._states.get(entity_id)


class _FakeServices:
    def __init__(self):
        self.calls = []

    async def async_call(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class _FakeHass:
    def __init__(self):
        self.states = _FakeStates()
        self.services = _FakeServices()


def test_dry_run_reports_planned_calls_without_writing():
    hass = _FakeHass()
    engine = ApplyEngine(hass)
    p = plan()

    result = asyncio.run(engine.async_apply_plan(
        p,
        target_entity_id="climate.living",
        gate=gate(dry_run=True, manual=True),
    ))

    assert result.status == "dry_run"
    assert result.reason == "would_call_services"
    assert [c["service"] for c in result.service_calls] == ["set_hvac_mode", "set_temperature"]
    assert result.service_calls[0]["target"] == {"entity_id": "climate.living"}
    assert result.details["planned_hvac_mode"] == "heat"
    assert result.details["planned_temperature"] == 21.0
    assert hass.services.calls == []


def test_protection_profile_uses_heat_setpoint_not_off_mode():
    hass = _FakeHass()
    engine = ApplyEngine(hass)
    p = ZonePlan(
        zone="bathroom",
        profile="protection",
        target_temperature=16.0,
        raw_target_temperature=16.0,
        reason="effective_temperature_missing_protection",
    )

    result = asyncio.run(engine.async_apply_plan(
        p,
        target_entity_id="climate.living",
        gate=gate(dry_run=True, manual=True),
    ))

    assert result.status == "dry_run"
    assert result.details["planned_hvac_mode"] == "heat"
    assert result.details["planned_temperature"] == 16.0


def test_apply_cooldown_option_is_used():
    assert apply_cooldown_seconds_from_config({"apply_cooldown_seconds": 120}) == 120
    assert apply_cooldown_seconds_from_config({"apply_cooldown_seconds": 0}) == 600
    assert apply_cooldown_seconds_from_config({"cooldown_seconds": 300}) == 300


def test_switch_dry_run_reports_planned_call_without_writing():
    hass = _FakeHass()
    engine = ApplyEngine(hass)
    fan_plan = BathroomFanPlan(
        zone="bathroom_fan",
        mode="akut",
        reason="bath_fan_acute_humidity_or_dewpoint",
        target_switch_state="on",
    )

    result = asyncio.run(engine.async_apply_switch_plan(
        fan_plan,
        target_entity_id="switch.bath_fan",
        gate=gate(dry_run=True, manual=True),
    ))

    assert result.status == "dry_run"
    assert result.reason == "would_call_services"
    assert result.service_calls == [{
        "domain": "switch",
        "service": "turn_on",
        "target": {"entity_id": "switch.bath_fan"},
        "service_data": {},
    }]
    assert result.details["planned_state"] == "on"
    assert hass.services.calls == []


def test_switch_unavailable_returns_readable_error():
    hass = _FakeHass()
    engine = ApplyEngine(hass)
    fan_plan = BathroomFanPlan(
        zone="bathroom_fan",
        mode="akut",
        reason="bath_fan_acute_humidity_or_dewpoint",
        target_switch_state="on",
    )

    result = asyncio.run(engine.async_apply_switch_plan(
        fan_plan,
        target_entity_id="switch.unavailable_fan",
        gate=gate(manual=True, target_state="unavailable"),
    ))

    assert result.status == "error"
    assert result.reason == "target_entity_unavailable"
    assert hass.services.calls == []

