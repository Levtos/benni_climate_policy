from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.benni_climate_policy.bathroom import (
    OPT_BATH_SETPOINT_GROUND,
    BathroomClimateInput,
    BathroomHumidityInput,
    absolute_humidity_gm3,
    bath_outdoor_bonus,
    bath_tuning_from_options,
    decide_bathroom_climate,
    decide_bathroom_fan,
    dew_point_celsius,
    humidity_diagnostics,
)
from custom_components.benni_climate_policy.models import (
    ClimateContextSnapshot,
    EffectiveTemperatureBreakdown,
    SourceValue,
)


def sv(value):
    return SourceValue(value, "sensor.test", "ok", False)


def ctx(*, day_state="afternoon", workday="werktag"):
    return ClimateContextSnapshot(
        activity_state=sv("idle"),
        bio_state=sv("awake"),
        day_context=sv(workday),
        day_state=sv(day_state),
        presence_band=sv("home"),
        presence_household=sv("nicht_leer"),
        presence_personal=sv("zuhause"),
        presence_preheat_active=sv("off"),
        presence_transition=sv("none"),
        workday_state=sv(workday),
        planned_wakeup_time=sv(None),
    )


def eff(temp):
    return EffectiveTemperatureBreakdown(temp, 0, 0, 0, 0, 0, temp, "ok" if temp is not None else "missing")


def climate_input(temp=21.0):
    return BathroomClimateInput(temp, 55.0, "climate.bath")


def humidity_input(*, bath_temp=24.0, bath_humidity=60.0, living_temp=21.0, living_humidity=50.0):
    return BathroomHumidityInput(bath_temp, bath_humidity, living_temp, living_humidity)


def test_bathroom_defaults_ground_heat():
    plan = decide_bathroom_climate(climate_input(), ctx(), eff(10), datetime(2026, 1, 1, 12), bath_tuning_from_options({}))
    assert plan.profile == "grundwaerme"
    assert plan.target_temperature == 19.0


def test_bathroom_missing_effective_temperature_uses_protection():
    plan = decide_bathroom_climate(climate_input(), ctx(), eff(None), datetime(2026, 1, 1, 12), bath_tuning_from_options({}))
    assert plan.profile == "protection"
    assert plan.target_temperature == 16.0
    assert plan.reason == "effective_temperature_missing_protection"


def test_bathroom_comfort_windows_and_teff_limit():
    tuning = bath_tuning_from_options({})
    plan = decide_bathroom_climate(climate_input(), ctx(day_state="early_morning", workday="werktag"), eff(10), datetime(2026, 1, 1, 7), tuning)
    assert plan.profile == "komfort"
    assert plan.target_temperature == 22.5

    suppressed = decide_bathroom_climate(climate_input(), ctx(day_state="early_morning", workday="werktag"), eff(19), datetime(2026, 1, 1, 7), tuning)
    assert suppressed.profile == "grundwaerme"

    weekend = decide_bathroom_climate(climate_input(), ctx(day_state="late_morning", workday="wochenende"), eff(10), datetime(2026, 1, 3, 10), tuning)
    assert weekend.profile == "komfort"

    evening = decide_bathroom_climate(climate_input(), ctx(day_state="late_evening"), eff(10), datetime(2026, 1, 1, 22), tuning)
    assert evening.profile == "komfort"


def test_bathroom_outdoor_bonus_steps():
    tuning = bath_tuning_from_options({})
    assert bath_outdoor_bonus(0, tuning) == 0.5
    assert bath_outdoor_bonus(5, tuning) == 0.3
    assert bath_outdoor_bonus(16, tuning) == -0.5
    assert bath_outdoor_bonus(10, tuning) == 0.0


def test_bathroom_tuning_changes_plan_hash():
    base = decide_bathroom_climate(climate_input(), ctx(), eff(10), datetime(2026, 1, 1, 12), bath_tuning_from_options({}))
    tuned = decide_bathroom_climate(
        climate_input(),
        ctx(),
        eff(10),
        datetime(2026, 1, 1, 12),
        bath_tuning_from_options({OPT_BATH_SETPOINT_GROUND: 18.5}),
    )
    assert tuned.target_temperature == 18.5
    assert base.plan_hash != tuned.plan_hash


def test_dewpoint_absolute_humidity_and_delta():
    assert dew_point_celsius(24, 80) > 20
    assert 8.0 < absolute_humidity_gm3(20, 50) < 9.5
    diagnostics = humidity_diagnostics(humidity_input(bath_temp=24, bath_humidity=70, living_temp=20, living_humidity=50))
    assert diagnostics["absolute_humidity_bathroom"] > diagnostics["absolute_humidity_living"]
    assert diagnostics["ah_delta"] > 0


def test_bathroom_fan_acute_afterrun_stoss_and_end_thresholds():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=22), ctx(), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    acute = decide_bathroom_fan(humidity_input(bath_humidity=76), heating, now=now, day_state="afternoon", last_fan_active_at=now, tuning=tuning)
    assert acute.mode == "akut"

    afterrun = decide_bathroom_fan(humidity_input(bath_temp=22, bath_humidity=55, living_temp=21, living_humidity=50), heating, now=now, day_state="afternoon", last_fan_active_at=now, tuning=tuning)
    assert afterrun.mode == "nachluft"

    ended = decide_bathroom_fan(humidity_input(bath_temp=21, bath_humidity=45, living_temp=21, living_humidity=45), heating, now=now, day_state="afternoon", last_fan_active_at=now, tuning=tuning)
    assert ended.mode == "off"
    assert ended.reason == "bath_fan_afterrun_end_threshold"

    stoss = decide_bathroom_fan(
        humidity_input(bath_temp=22, bath_humidity=53, living_temp=21, living_humidity=50),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now - timedelta(hours=13),
        tuning=tuning,
    )
    assert stoss.mode == "stoss"

    night = decide_bathroom_fan(
        humidity_input(bath_temp=22, bath_humidity=53, living_temp=21, living_humidity=50),
        heating,
        now=now,
        day_state="early_night",
        last_fan_active_at=now - timedelta(hours=13),
        tuning=tuning,
    )
    assert night.mode == "off"


def test_bathroom_fan_heating_coordination_blocks_only_non_acute():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=17), ctx(day_state="early_morning"), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    blocked = decide_bathroom_fan(humidity_input(bath_temp=17, bath_humidity=70, living_temp=20, living_humidity=45), heating, now=now, day_state="afternoon", last_fan_active_at=now, tuning=tuning)
    assert blocked.mode == "off"
    assert "bath_heating_up_blocks_fan" in blocked.blocked_by

    acute = decide_bathroom_fan(humidity_input(bath_temp=17, bath_humidity=80), heating, now=now, day_state="afternoon", last_fan_active_at=now, tuning=tuning)
    assert acute.mode == "akut"
    assert acute.diagnostics["heating_fan_coordination_state"] == "acute_overrides_heating"
