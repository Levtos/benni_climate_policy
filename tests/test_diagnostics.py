from __future__ import annotations

from datetime import datetime

from custom_components.benni_climate_policy.diagnostics import (
    compact_debug_attributes,
    compact_json_size,
    full_debug_payload,
)


def _large_debug_payload():
    plans = {
        zone: {
            "profile": "komfort",
            "target_temperature": 22.5,
            "reason": f"{zone}_reason",
            "apply_block_reason": "none",
            "plan_hash": f"{zone}_hash",
            "decision_path": [f"step_{idx}" for idx in range(80)],
            "source_entities": [f"sensor.{zone}_{idx}" for idx in range(80)],
        }
        for zone in ("living_room", "kitchen", "bathroom")
    }
    return {
        "system_ready": True,
        "apply_active": False,
        "apply_status": "idle",
        "effective_outdoor_temperature": {"effective_temperature": 12.3, "large": "x" * 3000},
        "plans": plans,
        "bathroom": {
            "fan_plan": {
                "mode": "nachluft",
                "reason": "bath_fan_afterrun_ah_delta",
                "diagnostics": {"large": "x" * 2000},
            },
            "tuning": {"large": "x" * 3000},
        },
        "last_apply_result": {
            "status": "dry_run",
            "reason": "would_call_services",
            "actions": [{"details": "x" * 1000} for _ in range(10)],
        },
        "context": {"large": "x" * 5000},
        "thresholds": {"large": "x" * 5000},
        "tuning_options": {"large": "x" * 5000},
        "inputs": [{"entity_id": f"sensor.{idx}", "state": "x" * 50} for idx in range(100)],
        "effective_inputs": {
            "weather_resolution": {
                "forecast": {"source": "weather_forecast", "value": 17.0},
                "feels_like": {"source": "fallback_real_temperature", "value": 12.0},
            },
        },
        "debug": {"large": "x" * 5000},
    }


def test_compact_debug_attributes_stay_under_recorder_safe_size():
    attrs = compact_debug_attributes(_large_debug_payload())

    assert compact_json_size(attrs) < 4096


def test_compact_debug_attributes_do_not_include_large_payloads():
    attrs = compact_debug_attributes(_large_debug_payload())

    for key in ("context", "plans", "debug", "thresholds", "tuning_options", "inputs", "last_apply_result"):
        assert key not in attrs
    assert attrs["debug_payload_available"] is True
    assert attrs["living_room_mode"] == "komfort"
    assert attrs["bathroom_fan_mode"] == "nachluft"


def test_compact_debug_attributes_only_expose_allowed_summary_keys():
    attrs = compact_debug_attributes(_large_debug_payload())

    assert set(attrs) == {
        "system_ready",
        "integration_version",
        "apply_active",
        "apply_status",
        "effective_outdoor_temperature",
        "living_room_mode",
        "living_room_target_temp",
        "living_room_policy_target_temp",
        "living_room_floor_slab_delta",
        "living_room_comfort",
        "living_room_policy_reason",
        "living_room_apply_blocker",
        "kitchen_mode",
        "kitchen_target_temp",
        "kitchen_policy_target_temp",
        "kitchen_floor_slab_delta",
        "kitchen_comfort",
        "kitchen_policy_reason",
        "kitchen_apply_blocker",
        "bathroom_mode",
        "bathroom_target_temp",
        "bathroom_policy_target_temp",
        "bathroom_floor_slab_delta",
        "bathroom_comfort",
        "bathroom_fan_mode",
        "bathroom_fan_reason",
        "last_apply_status",
        "last_apply_reason",
        "debug_payload_available",
    }


def test_full_debug_payload_keeps_large_debug_data_for_endpoint():
    payload = _large_debug_payload()
    full = full_debug_payload(
        timestamp=datetime(2026, 6, 2, 12),
        context=payload["context"],
        effective_outdoor_temperature=payload["effective_outdoor_temperature"],
        plans=payload["plans"],
        debug=payload,
    )

    assert full["context"] == payload["context"]
    assert full["plans"] == payload["plans"]
    assert full["thresholds"] == payload["thresholds"]
    assert full["tuning_options"] == payload["tuning_options"]
    assert full["last_apply_result"] == payload["last_apply_result"]
    assert full["inputs"] == payload["inputs"]
    assert full["weather_resolution"] == payload["effective_inputs"]["weather_resolution"]
    assert full["timestamp"] == "2026-06-02T12:00:00"


def test_panel_has_missing_debug_endpoint_fallback():
    source = open("custom_components/benni_climate_policy/frontend/app/main.js", encoding="utf-8").read()

    assert "Debug-Endpunkt nicht erreichbar" in source
    assert "debugEndpointNotice" in source


def test_panel_apply_debug_rendering_is_collapsible_and_summarized():
    source = open("custom_components/benni_climate_policy/frontend/app/main.js", encoding="utf-8").read()

    assert "function renderApplySummary" in source
    assert "Blockiert durch Start-Ruhephase" in source
    assert "jsonDetails(\"Details als JSON anzeigen\", lastApply)" in source
    assert "JSON_CACHE" in source
    assert "scrollbar-gutter: stable" in source
    assert "if (this._lastHtml === html) return;" in source
