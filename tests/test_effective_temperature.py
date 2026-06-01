from custom_components.benni_climate_policy.models import EffectiveTemperatureInput
from custom_components.benni_climate_policy.policy import effective_outdoor_temperature


def test_effective_temperature_degrades_without_optional_sources():
    result = effective_outdoor_temperature(EffectiveTemperatureInput(real_temperature=10))
    assert result.effective_temperature is not None
    assert result.input_quality == "degraded"
    assert result.floor_slab_offset < 0


def test_effective_temperature_missing_real_temperature():
    result = effective_outdoor_temperature(EffectiveTemperatureInput(real_temperature=None))
    assert result.effective_temperature is None
    assert result.input_quality == "missing"


def test_lux_bonus_requires_sun_elevation():
    dark = effective_outdoor_temperature(
        EffectiveTemperatureInput(real_temperature=10, weather_condition="sunny", outdoor_lux=30000, sun_elevation=0)
    )
    sunny = effective_outdoor_temperature(
        EffectiveTemperatureInput(real_temperature=10, weather_condition="sunny", outdoor_lux=30000, sun_elevation=10)
    )
    assert sunny.effective_temperature > dark.effective_temperature

