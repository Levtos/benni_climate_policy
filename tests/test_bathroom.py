from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.benni_climate_policy.bathroom import (
    OPT_BATH_HUMIDITY_GROUND_HEAT_OFF_AT,
    OPT_BATH_HUMIDITY_GROUND_HEAT_TARGET,
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


def climate_input(temp=21.0, humidity=55.0):
    return BathroomClimateInput(temp, humidity, "climate.bath")


def humidity_input(
    *,
    bath_temp=24.0,
    bath_humidity=60.0,
    living_temp=21.0,
    living_humidity=50.0,
    toilet_activity=False,
    shower_activity=False,
    usage_hold=False,
    usage_hold_until=None,
):
    return BathroomHumidityInput(
        bath_temp,
        bath_humidity,
        living_temp,
        living_humidity,
        toilet_activity_active=toilet_activity,
        shower_activity_active=shower_activity,
        fan_usage_hold_active=usage_hold,
        fan_usage_hold_until=usage_hold_until,
    )


def test_bathroom_defaults_ground_heat():
    plan = decide_bathroom_climate(climate_input(temp=18.5), ctx(), eff(10), datetime(2026, 1, 1, 12), bath_tuning_from_options({}))
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

    suppressed = decide_bathroom_climate(climate_input(temp=18.5), ctx(day_state="early_morning", workday="werktag"), eff(19), datetime(2026, 1, 1, 7), tuning)
    assert suppressed.profile == "grundwaerme"

    weekend = decide_bathroom_climate(climate_input(), ctx(day_state="late_morning", workday="wochenende"), eff(10), datetime(2026, 1, 3, 10), tuning)
    assert weekend.profile == "komfort"

    evening = decide_bathroom_climate(climate_input(), ctx(day_state="late_evening"), eff(10), datetime(2026, 1, 1, 22), tuning)
    assert evening.profile == "komfort"


def test_bathroom_over_target_forces_heating_off_even_when_fan_can_run():
    now = datetime(2026, 1, 1, 7)
    tuning = bath_tuning_from_options({})
    heating = decide_bathroom_climate(
        climate_input(temp=24.6),
        ctx(day_state="early_morning", workday="werktag"),
        eff(10),
        now,
        tuning,
    )
    fan = decide_bathroom_fan(
        BathroomHumidityInput(24.6, 80, 21, 45),
        heating,
        now=now,
        day_state="early_morning",
        last_fan_active_at=None,
        tuning=tuning,
    )

    assert heating.profile == "off"
    assert heating.target_temperature == 10.0
    assert heating.reason == "bath_temperature_above_target_no_heating"
    assert heating.allowed_profile == "komfort"
    assert heating.heat_demand is False
    assert fan.target_switch_state == "on"


def test_bathroom_ground_heat_stops_when_room_is_warm_enough():
    plan = decide_bathroom_climate(
        climate_input(temp=20.3),
        ctx(),
        eff(10),
        datetime(2026, 1, 1, 12),
        bath_tuning_from_options({}),
    )

    assert plan.allowed_profile == "grundwaerme"
    assert plan.profile == "off"
    assert plan.reason == "bath_temperature_above_target_no_heating"


def test_bathroom_humidity_ground_heat_overrides_warm_room_cutoff_when_cool_outside():
    plan = decide_bathroom_climate(
        climate_input(temp=21.4, humidity=72.0),
        ctx(),
        eff(12),
        datetime(2026, 6, 10, 6),
        bath_tuning_from_options({}),
    )

    assert plan.allowed_profile == "grundwaerme"
    assert plan.profile == "grundwaerme"
    assert plan.target_temperature == 22.0
    assert plan.reason == "bath_humidity_ground_heat"
    assert plan.heat_demand is True
    assert plan.indoor_heat_demand_reason == "bath_humidity_ground_heat_overrides_indoor_hysteresis"
    assert plan.indoor_heat_off_at == 22.5


def test_bathroom_humidity_ground_heat_respects_warm_weather_and_upper_cutoff():
    warm_weather = decide_bathroom_climate(
        climate_input(temp=21.4, humidity=78.0),
        ctx(),
        eff(24),
        datetime(2026, 7, 1, 6),
        bath_tuning_from_options({}),
    )

    assert warm_weather.profile == "off"
    assert warm_weather.reason == "bath_temperature_above_target_no_heating"

    already_warm = decide_bathroom_climate(
        climate_input(temp=22.6, humidity=78.0),
        ctx(),
        eff(12),
        datetime(2026, 6, 10, 6),
        bath_tuning_from_options({}),
    )

    assert already_warm.profile == "off"
    assert already_warm.reason == "bath_temperature_above_target_no_heating"


def test_bathroom_outdoor_bonus_steps():
    tuning = bath_tuning_from_options({})
    assert bath_outdoor_bonus(0, tuning) == 0.5
    assert bath_outdoor_bonus(5, tuning) == 0.3
    assert bath_outdoor_bonus(16, tuning) == -0.5
    assert bath_outdoor_bonus(10, tuning) == 0.0


def test_bathroom_tuning_changes_plan_hash():
    base = decide_bathroom_climate(climate_input(temp=18.0), ctx(), eff(10), datetime(2026, 1, 1, 12), bath_tuning_from_options({}))
    tuned = decide_bathroom_climate(
        climate_input(temp=18.0),
        ctx(),
        eff(10),
        datetime(2026, 1, 1, 12),
        bath_tuning_from_options({OPT_BATH_SETPOINT_GROUND: 18.5}),
    )
    assert tuned.target_temperature == 18.5
    assert base.plan_hash != tuned.plan_hash


def test_bathroom_humidity_ground_heat_tuning_changes_plan_hash():
    now = datetime(2026, 6, 10, 6)
    base = decide_bathroom_climate(
        climate_input(temp=21.0, humidity=72.0),
        ctx(),
        eff(12),
        now,
        bath_tuning_from_options({}),
    )
    tuned = decide_bathroom_climate(
        climate_input(temp=21.0, humidity=72.0),
        ctx(),
        eff(12),
        now,
        bath_tuning_from_options({
            OPT_BATH_HUMIDITY_GROUND_HEAT_TARGET: 21.5,
            OPT_BATH_HUMIDITY_GROUND_HEAT_OFF_AT: 22.0,
        }),
    )

    assert tuned.target_temperature == 21.5
    assert tuned.indoor_heat_off_at == 22.0
    assert tuned.plan_hash != base.plan_hash


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

    acute_rise = decide_bathroom_fan(
        BathroomHumidityInput(24, 65, 21, 50, previous_bathroom_humidity=49, previous_bathroom_humidity_at=now - timedelta(minutes=4)),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now,
        tuning=tuning,
    )
    assert acute_rise.mode == "akut"
    assert acute_rise.diagnostics["bathroom_humidity_rise_5m"] == 16

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


def test_bathroom_fan_acute_max_duration_stops_stuck_humidity_or_activity():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=22), ctx(), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    fan = decide_bathroom_fan(
        BathroomHumidityInput(
            24,
            80,
            21,
            45,
            fan_active_since=now - timedelta(minutes=tuning.fan_acute_max_minutes + 1),
        ),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now - timedelta(minutes=tuning.fan_acute_max_minutes + 1),
        tuning=tuning,
    )

    assert fan.mode == "off"
    assert fan.target_switch_state == "off"
    assert fan.reason == "bath_fan_akut_max_duration_reached"
    assert fan.diagnostics["fan_max_duration_reached"] is True
    assert fan.diagnostics["fan_uncapped_mode"] == "akut"
    assert fan.diagnostics["heating_fan_coordination_state"] == "max_duration_reached"


def test_bathroom_fan_afterrun_and_regular_stoss_max_duration_stop():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=22), ctx(), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    afterrun = decide_bathroom_fan(
        humidity_input(bath_temp=22, bath_humidity=55, living_temp=21, living_humidity=50),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now - timedelta(minutes=tuning.fan_afterrun_max_minutes + 1),
        tuning=tuning,
    )
    assert afterrun.mode == "nachluft"

    capped_afterrun = decide_bathroom_fan(
        BathroomHumidityInput(
            22,
            55,
            21,
            50,
            fan_active_since=now - timedelta(minutes=tuning.fan_afterrun_max_minutes + 1),
        ),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now - timedelta(minutes=tuning.fan_afterrun_max_minutes + 1),
        tuning=tuning,
    )
    assert capped_afterrun.mode == "off"
    assert capped_afterrun.reason == "bath_fan_nachluft_max_duration_reached"

    capped_stoss = decide_bathroom_fan(
        BathroomHumidityInput(
            22,
            53,
            21,
            50,
            fan_active_since=now - timedelta(minutes=tuning.fan_stoss_duration_minutes + 1),
        ),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now - timedelta(hours=13),
        tuning=tuning,
    )
    assert capped_stoss.mode == "off"
    assert capped_stoss.reason == "bath_fan_stoss_max_duration_reached"


def test_bathroom_fan_usage_hold_forces_30_minute_run():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=17), ctx(day_state="early_morning"), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    fan = decide_bathroom_fan(
        humidity_input(
            bath_temp=17,
            bath_humidity=45,
            living_temp=21,
            living_humidity=45,
            usage_hold=True,
            usage_hold_until=now + timedelta(minutes=30),
        ),
        heating,
        now=now,
        day_state="early_night",
        last_fan_active_at=now,
        tuning=tuning,
    )

    assert fan.mode == "stoss"
    assert fan.target_switch_state == "on"
    assert fan.reason == "bath_fan_usage_hold"
    assert fan.blocked_by == []
    assert fan.diagnostics["fan_usage_hold_active"] is True
    assert fan.diagnostics["fan_usage_hold_until"] == (now + timedelta(minutes=30)).isoformat()
    assert fan.diagnostics["heating_fan_coordination_state"] == "usage_hold_overrides_heating"

    protected = decide_bathroom_fan(
        BathroomHumidityInput(
            17,
            45,
            21,
            45,
            fan_active_since=now - timedelta(minutes=tuning.fan_stoss_duration_minutes + 1),
            fan_usage_hold_active=True,
            fan_usage_hold_until=now + timedelta(minutes=30),
        ),
        heating,
        now=now,
        day_state="early_night",
        last_fan_active_at=now,
        tuning=tuning,
    )
    assert protected.mode == "stoss"
    assert protected.reason == "bath_fan_usage_hold"
    assert protected.diagnostics["fan_max_duration_reached"] is False


def test_bathroom_fan_shower_activity_is_acute():
    now = datetime(2026, 1, 1, 12)
    heating = decide_bathroom_climate(climate_input(temp=17), ctx(day_state="early_morning"), eff(10), now, bath_tuning_from_options({}))
    tuning = bath_tuning_from_options({})

    fan = decide_bathroom_fan(
        humidity_input(bath_temp=17, bath_humidity=45, living_temp=21, living_humidity=45, shower_activity=True),
        heating,
        now=now,
        day_state="afternoon",
        last_fan_active_at=now,
        tuning=tuning,
    )

    assert fan.mode == "akut"
    assert fan.target_switch_state == "on"
    assert fan.reason == "bath_fan_shower_activity_hold"
    assert fan.blocked_by == []
    assert fan.diagnostics["shower_activity_active"] is True
    assert fan.diagnostics["heating_fan_coordination_state"] == "shower_activity_overrides_heating"
