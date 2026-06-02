from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.benni_climate_policy.models import (
    ClimateContextSnapshot,
    EffectiveTemperatureBreakdown,
    SourceValue,
    WindowState,
    ZoneInput,
)
from custom_components.benni_climate_policy.policy import (
    OPT_LUX_REFERENCE,
    OPT_SETPOINT_SPAR,
    default_policy_tuning,
    decide_zone,
    policy_tuning_from_options,
    policy_visibility_snapshot,
    setpoint_for,
    threshold_option_key,
)


def sv(value):
    return SourceValue(value, "sensor.test", "ok", False)


def ctx(
    *,
    bio="awake",
    band="home",
    transition="none",
    preheat=False,
    activity="idle",
    day_state="afternoon",
    wakeup=None,
):
    return ClimateContextSnapshot(
        activity_state=sv(activity),
        bio_state=sv(bio),
        day_context=sv("werktag"),
        day_state=sv(day_state),
        presence_band=sv(band),
        presence_household=sv("nicht_leer"),
        presence_personal=sv("zuhause"),
        presence_preheat_active=sv("on" if preheat else "off"),
        presence_transition=sv(transition),
        workday_state=sv("werktag"),
        planned_wakeup_time=sv(wakeup),
    )


def eff(temp):
    return EffectiveTemperatureBreakdown(temp, 0, 0, 0, 0, 0, temp, "ok")


def zone(**kw):
    return ZoneInput("living_room", room_temperature=kw.get("room_temperature", 20.0), thermostat_entity_id="climate.living")


def test_sleep_forces_off():
    plan = decide_zone(zone(), ctx(bio="sleep"), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile == "off"
    assert plan.reason == "bio_sleep_forces_off"


def test_waking_forces_off():
    plan = decide_zone(zone(), ctx(bio="waking"), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile == "off"


def test_window_unknown_open_blocks_but_unknown_tilt_ignored():
    plan = decide_zone(
        ZoneInput("living_room", thermostat_entity_id="climate.living", windows=(WindowState("unknown", "unknown"),)),
        ctx(),
        eff(0),
        datetime(2026, 1, 1, 12),
    )
    assert plan.profile == "off"
    assert plan.reason == "window_blocks_heating"

    plan = decide_zone(
        ZoneInput("living_room", thermostat_entity_id="climate.living", windows=(WindowState("off", "unknown"),)),
        ctx(),
        eff(0),
        datetime(2026, 1, 1, 12),
    )
    assert plan.profile in ("komfort", "boost")


def test_presence_far_forces_off():
    plan = decide_zone(zone(), ctx(band="far"), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile == "off"


def test_preheat_caps_to_spar():
    plan = decide_zone(zone(room_temperature=18), ctx(band="preheat", preheat=True), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile == "spar"
    assert plan.reason == "presence_preheat_caps_to_spar"


def test_passing_through_blocks_preheat():
    plan = decide_zone(zone(), ctx(band="preheat", transition="passing_through", preheat=True), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile == "off"
    assert plan.reason == "passing_through_blocks_preheat"


def test_june_july_august_allow_only_off_or_spar_and_disable_boost():
    for month in (6, 7, 8):
        plan = decide_zone(zone(room_temperature=16), ctx(), eff(0), datetime(2026, month, 1, 12))
        assert plan.profile == "spar"
        assert not plan.is_boost_active


def test_free_time_early_night_holds_comfort_outside_summer():
    plan = decide_zone(zone(), ctx(activity="free_time", day_state="early_night"), eff(14), datetime(2026, 10, 1, 21))
    assert plan.profile == "komfort"


def test_dynamic_wakeup_cutoff_forces_off():
    now = datetime(2026, 1, 1, 22)
    plan = decide_zone(zone(), ctx(wakeup=now + timedelta(hours=7, minutes=59)), eff(0), now)
    assert plan.profile == "off"
    assert plan.reason == "dynamic_wakeup_cutoff"


def test_missing_thermostat_blocks_apply_but_still_calculates_plan():
    plan = decide_zone(ZoneInput("living_room"), ctx(), eff(0), datetime(2026, 1, 1, 12))
    assert plan.profile in ("komfort", "boost")
    assert "thermostat_entity_missing" in plan.blocked_by


def test_policy_visibility_snapshot_uses_policy_thresholds():
    snapshot = policy_visibility_snapshot(7, 18)
    assert snapshot["active_month_band"] == "summer"
    assert snapshot["thresholds"]["off"] == 19.5
    assert snapshot["comfort_structurally_disabled"] is True
    assert snapshot["boost_structurally_disabled"] is True
    assert snapshot["setpoints"]["spar"] == 21.0


def test_policy_tuning_defaults_keep_existing_behavior():
    tuning = default_policy_tuning()
    assert setpoint_for("off", 0, tuning) == 10.0
    assert setpoint_for("spar", 18, tuning) == 21.0
    assert setpoint_for("spar", 10, tuning) == 21.5
    assert setpoint_for("komfort", 18, tuning) == 22.5
    assert setpoint_for("komfort", 10, tuning) == 23.0
    assert setpoint_for("komfort", 0, tuning) == 23.5
    assert setpoint_for("boost", 18, tuning) == 24.5


def test_policy_tuning_options_override_setpoints():
    tuning = policy_tuning_from_options({OPT_SETPOINT_SPAR: 20.0})
    assert setpoint_for("spar", 18, tuning) == 20.0
    assert tuning.source_for(OPT_SETPOINT_SPAR) == "user option"


def test_summer_off_threshold_option_changes_decision():
    default_plan = decide_zone(zone(), ctx(), eff(20), datetime(2026, 7, 1, 12), tuning=default_policy_tuning())
    tuned = policy_tuning_from_options({threshold_option_key("summer", "off_threshold"): 21.0})
    tuned_plan = decide_zone(zone(), ctx(), eff(20), datetime(2026, 7, 1, 12), tuning=tuned)

    assert default_plan.profile == "off"
    assert tuned_plan.profile == "spar"


def test_plan_hash_changes_when_relevant_tuning_changes():
    base = decide_zone(zone(), ctx(), eff(18), datetime(2026, 5, 1, 12), tuning=default_policy_tuning())
    tuned = decide_zone(
        zone(),
        ctx(),
        eff(18),
        datetime(2026, 5, 1, 12),
        tuning=policy_tuning_from_options({OPT_SETPOINT_SPAR: 20.0}),
    )

    assert base.plan_hash != tuned.plan_hash
    assert base.policy_config_hash != tuned.policy_config_hash


def test_invalid_tuning_options_fall_back_to_defaults():
    tuning = policy_tuning_from_options({OPT_LUX_REFERENCE: 0, OPT_SETPOINT_SPAR: "bad"})
    assert tuning.lux_reference == 30000.0
    assert tuning.setpoint_spar == 21.0
    assert tuning.source_for(OPT_LUX_REFERENCE) == "invalid_fallback_default"
    assert tuning.source_for(OPT_SETPOINT_SPAR) == "invalid_fallback_default"

