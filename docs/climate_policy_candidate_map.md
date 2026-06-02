# Climate Policy Candidate Map

Stand: 2026-06-01. Diese Map basiert auf zwei Quellen:

- Repo-Scan in `D:\Dokumente\GitHub\einhornzentrale`
- Live-HA-Discovery ueber den `einhornzentrale` MCP

Bewertung: `confirmed` = live vorhanden und fachlich passend, `likely` =
Repo-/Namenshinweis plausibel, `unclear` = nicht sicher zuordenbar, `conflict`
= Repo und Live-HA widersprechen.

## Gefundene Integrationen

| Name | Pfad/Quelle | Zweck | Relevanz | Bewertung |
|---|---|---|---|---|
| `benni_context` | Live HA + `D:\Dokumente\GitHub\benni_context` | Presence, Bio, Day, Activity | Primaere Context-Quelle/Fallback | confirmed |
| `context_*_combined` | `einhornzentrale/packages/combined/context.yaml` | normalisierte Consumer-Context-Schicht | bevorzugte Vorschlaege fuer Config Flow | confirmed |
| Weather/DWD Atomics | `packages/atomics/dwd_weather.yaml` | DWD Condition, Temperatur, Feuchte, Wind, Season | Wetter-/Aussenklima-Inputs | confirmed |
| Climate/Lux Atomics | `packages/atomics/z2m_climate_lux.yaml` | Raumtemperatur/-feuchte, Garten-Temp, Lux | Raum-/Aussenklima-Inputs | confirmed |
| Opening Atomics | `packages/atomics/z2m_openings.yaml` | Fenster/Tuer offen/gekippt | Fenster-Gates | confirmed |
| alte Climate Combined/YAML Apply | `packages/combined/climate.yaml`, `packages/climate_apply/*` | bisherige Shadow-/Apply-Logik | Migration/Referenz, keine Runtime-Abhaengigkeit | confirmed |
| Bath Fan Combined/YAML Apply | `packages/combined/bath.yaml`, `packages/bath/*` | Badluefter-Entscheidung/Apply | PR4-Referenz; `switch.bath_fan` als Aktor-Kandidat | confirmed |

## Context-States

| Rolle | bevorzugter Vorschlag | Fallback-Vorschlag | Live-State | Bewertung |
|---|---|---|---|---|
| Activity State | `sensor.context_activity_state_combined` | `sensor.benni_context_activity_state` | `free_time` | confirmed |
| Bio State | `sensor.context_bio_state_combined` | `sensor.benni_context_bio_state` | `awake` | confirmed |
| Day Context | `sensor.context_day_context_combined` | `sensor.benni_context_day_context` | `werktag` | confirmed |
| Day State | `sensor.context_day_state_combined` | `sensor.benni_context_day_state` | `early_night` | confirmed |
| Presence Band | `sensor.context_presence_band_combined` | `sensor.benni_context_presence_band` | `home` | confirmed |
| Presence Household | `sensor.context_presence_household_combined` | `sensor.benni_context_presence_household` | `nicht_leer` | confirmed |
| Presence Personal | `sensor.context_presence_personal_combined` | `sensor.benni_context_presence_personal` | `zuhause` | confirmed |
| Presence Preheat Active | `binary_sensor.context_presence_preheat_active_combined` | `binary_sensor.benni_context_presence_preheat_active` | `off` | confirmed |
| Presence Transition | `sensor.context_presence_transition_combined` | `sensor.benni_context_presence_transition` | `none` | confirmed |
| Workday State | `sensor.context_day_context_combined` | `sensor.benni_context_day_context` | `werktag` | confirmed |
| Planned Wakeup Time | nicht gefunden | Config Flow Auswahl | n/a | unclear |

## Window-/Door-States

| Oeffnung | Vorschlag | Live-State | Bewertung |
|---|---|---|---|
| Wohnzimmer links offen | `binary_sensor.living_window_left_open_atomic` | `off` | confirmed |
| Wohnzimmer links gekippt | `binary_sensor.living_window_left_tilt_atomic` | `off` | confirmed |
| Wohnzimmer rechts offen | `binary_sensor.living_window_right_open_atomic` | `off` | confirmed |
| Wohnzimmer rechts gekippt | `binary_sensor.living_window_right_tilt_atomic` | `off` | confirmed |
| Terrassentuer offen | `binary_sensor.kitchen_patio_door_open_atomic` | live vorhanden | confirmed |
| Terrassentuer gekippt | `binary_sensor.kitchen_patio_door_tilt_atomic` | live vorhanden | confirmed |
| Bad-Fenster | keines gefunden | n/a | confirmed: Bad hat fachlich kein Fenster |

## Wetter-/Aussenklima-Quellen

| Rolle | Vorschlag | Live-State | Bewertung |
|---|---|---|---|
| reale Aussentemperatur | `sensor.garden_temperature_atomic` | Repo-Atomic; Rohwert live vorhanden | confirmed |
| Wetter-Fallbacktemperatur | `sensor.weather_temperature_atomic` | live vorhanden | confirmed |
| Wetterzustand | `sensor.weather_condition_atomic` | `partlycloudy` | confirmed |
| Wetter-Entity | `weather.dwd_home` | `partlycloudy` | confirmed |
| Aussenhelligkeit Lux | `sensor.garden_illuminance_atomic` | live vorhanden | confirmed |
| Sonnen-Elevation | `sun.sun` | live per Domain-Suche vorhanden | confirmed |
| DWD Forecast +3h | `weather.dwd_home` via `weather.get_forecasts(type=hourly)` | live read-only Forecast-Service vorhanden | confirmed |
| gefuehlte Aussentemperatur | keine echte DWD-/MOSMIX-Entity gefunden; Fallback auf reale Aussentemperatur | n/a | confirmed fallback |

## Raumklima-Quellen

| Raum | Temperatur | Feuchte | Bewertung |
|---|---|---|---|
| Wohnzimmer | `sensor.living_temperature_atomic` | `sensor.living_humidity_atomic` | confirmed |
| Kueche | `sensor.kitchen_temperature_atomic` | `sensor.kitchen_humidity_atomic` | confirmed |
| Bad | `sensor.bath_temperature_atomic` | `sensor.bath_humidity_atomic` | confirmed |
| Thermostat-Messwerte | drei `climate.eve_thermo_20ebp1701*` | Raumzuordnung unbekannt | unclear |

## Aktoren

| Aktor | Kandidat | Bewertung |
|---|---|---|
| Wohnzimmer Thermostat | `climate.eve_thermo_20ebp1701*` | unclear: muss manuell zugeordnet werden |
| Kueche Thermostat | `climate.eve_thermo_20ebp1701*` | unclear: muss manuell zugeordnet werden |
| Bad Thermostat | `climate.eve_thermo_20ebp1701*` | unclear: muss manuell zugeordnet werden |
| Badluefter | `switch.bath_fan` | confirmed, aber korrigierbar |

## Konflikte und offene Luecken

- Repo/YAML erwartet `climate.living_thermostat`, `climate.kitchen_thermostat`, `climate.bath_thermostat`; Live-HA zeigt drei Eve-Thermo-Entities mit generischen IDs. Bewertung: `conflict`; Config Flow muss manuelle Raumzuordnung erzwingen.
- Alte `sensor.climate_*_combined` existieren und liefern Werte, duerfen aber nicht finale Runtime-Abhaengigkeit werden. Bewertung: `confirmed reference`.
- DWD Forecast +3h liegt nicht als Entity-State-Attribut vor, kann aber aus `weather.dwd_home` ueber `weather.get_forecasts(type=hourly)` read-only gelesen werden. Eine zweite DWD-Integration ist dafuer nicht noetig.
- Eine echte gefuehlte Aussentemperatur wurde live nicht gefunden. Alte `*_combined` Feels-like-Sensoren bleiben Migration/Referenz; Runtime-Fallback ist reale Aussentemperatur.
- Namen aus der Candidate Map duerfen nicht hart in Runtime-Logik uebernommen werden. Sie sind nur Vorschlaege und Fallback-Kandidaten im Resolver.

