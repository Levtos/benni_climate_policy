from __future__ import annotations

import json
import subprocess


def _frontend_values() -> dict:
    script = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync("custom_components/benni_climate_policy/frontend/app/main.js", "utf8");
const context = {
  console,
  setTimeout,
  clearTimeout,
  HTMLElement: class {
    attachShadow() {
      return {};
    }
  },
  customElements: {
    get() { return undefined; },
    define() {},
  },
};
vm.createContext(context);
vm.runInContext(source, context);
const values = {
  modeSpar: context.modeLabel("spar"),
  modeGround: context.modeLabel("grundwaerme"),
  effectiveLarge: context.effectiveOutdoorLabel("large"),
  effectiveChip: context.effectiveOutdoorLabel("chip"),
  weatherRainy: context.weatherConditionLabel("rainy"),
  weatherFallback: context.weatherConditionLabel("windy_variant"),
  rainyFeeling: context.outdoorFeelingFromParts({
    effectiveTemperature: 12.9,
    realTemperature: 13.2,
    weatherCondition: "rainy",
    outdoorLux: 900,
  }),
  humidFeeling: context.outdoorFeelingFromParts({
    effectiveTemperature: 25,
    realTemperature: 25,
    weatherCondition: "sunny",
    humidity: 72,
    outdoorLux: 28000,
  }),
  missingHumidityFeeling: context.outdoorFeelingFromParts({
    effectiveTemperature: 18,
    realTemperature: 18,
    weatherCondition: "rainy",
  }),
  localTimeDate: context.formatTimeDateLocal("2026-06-03T13:20:00+02:00"),
  neverApply: context.formatRelativeOrDateTime("never"),
  contextAwake: context.translateContextValue("bio_state", "awake"),
  contextParents: context.translateContextValue("presence_personal", "bei_eltern"),
  contextHousehold: context.translateContextValue("presence_household", "nicht_leer"),
  seasonSummer: context.seasonBandLabel("summer"),
};
console.log(JSON.stringify(values));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=".",
        check=True,
        encoding="utf-8",
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_mode_labels_are_centralized_for_visible_ux():
    values = _frontend_values()

    assert values["modeSpar"] == "Eco"
    assert values["modeGround"] == "Eco"


def test_effective_outdoor_temperature_uses_ux_labels():
    values = _frontend_values()

    assert values["effectiveLarge"] == "Heizrelevante Außentemperatur"
    assert values["effectiveChip"] == "Heizwert"


def test_weather_states_are_translated():
    values = _frontend_values()

    assert values["weatherRainy"] == "regnerisch"
    assert values["weatherFallback"] == "windig und bewölkt"


def test_outdoor_feeling_uses_weather_humidity_and_fallbacks():
    values = _frontend_values()

    assert "mild" not in values["rainyFeeling"]["outdoor_feeling_label"]
    assert any(
        word in values["rainyFeeling"]["outdoor_feeling_label"]
        for word in ("frisch", "regnerisch", "kühl")
    )
    assert any(
        word in values["humidFeeling"]["outdoor_feeling_label"]
        for word in ("schwül", "warm")
    )
    assert values["missingHumidityFeeling"]["outdoor_feeling_label"]
    assert values["missingHumidityFeeling"]["outdoor_feeling_parts"]["quality"] == "fallback"


def test_local_time_formatting_handles_iso_and_never():
    values = _frontend_values()

    assert "13:20 Uhr" in values["localTimeDate"]
    assert "03.06.2026" in values["localTimeDate"]
    assert values["neverApply"] == "Noch nie angewendet"


def test_context_and_season_labels_are_translated():
    values = _frontend_values()

    assert values["contextAwake"] == "Wach"
    assert values["contextParents"] == "Bei Eltern"
    assert values["contextHousehold"] == "Haushalt zuhause"
    assert values["seasonSummer"] == "Sommerpause"
