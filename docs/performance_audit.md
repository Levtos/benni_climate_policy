# Performance Audit nach PR #14

Datum: 2026-06-03  
HA-Testinstanz: Home Assistant Core 2026.5.4, Zeitzone Europe/Berlin  
Repo-Stand zu Beginn: `main` nach PR #14 (`fix: reduce climate policy update load`)

## Messszenario

### Baseline nach HA-Start, Panel geschlossen

Messfenster: 2026-06-03 09:57:12 bis 10:02:49 Europe/Berlin.

Beobachtete zentrale Entities:

| Entity | History-Eintraege im Fenster | Bewertung |
| --- | ---: | --- |
| `sensor.climate_debug_summary` | 1 | ruhig |
| `sensor.climate_forecast_temperature_3h` | 1 | ruhig im 5-Minuten-Fenster |
| `sensor.climate_outdoor_feels_like_temperature` | 1 | ruhig |
| `sensor.climate_policy_apply_status` | 1 | ruhig |
| `sensor.climate_effective_outdoor_temperature` | 3 | echte Outdoor-/Lux-Aenderungen |
| `sensor.living_room_climate_plan_hash` | 3 | folgt effektiver Temperatur |
| `sensor.kitchen_climate_plan_hash` | 3 | folgt effektiver Temperatur |
| `sensor.bathroom_climate_plan_hash` | 3 | folgt effektiver Temperatur |

Logs:

- Keine `benni_climate_policy`-Warnings im strukturierten HA-Systemlog.
- Keine WebSocket-Warnings mit `pending messages`.
- Keine Recorder-Warnings wegen Attributgroesse.
- Eine alte Recorder-Warnung `Ended unfinished session` ist vorhanden, aber ohne Bezug zu `benni_climate_policy`.

### Panel Overview offen

Der in-app Browser war nicht bei der HA-Testinstanz angemeldet. Ein echter Browser-Netzwerkmitschnitt der Panel-Overview war deshalb nicht moeglich, ohne Zugangsdaten zu verwenden.

Code-Validierung nach PR #14:

- `set hass(...)` ruft `_ensureDebugFetch()` auf.
- `_ensureDebugFetch()` bricht fuer nicht-Debug-Views ueber `_viewNeedsDebug()` ab.
- `overview` ist nicht in `DEBUG_VIEWS`.
- Damit sollte die Overview den Debug-Endpunkt nicht dauerhaft pollen.

Empfehlung: Bei einem angemeldeten Browser kann dies mit Resource-Timing/DevTools gegen `/api/benni_climate_policy/debug` nachgemessen werden.

### Debug-Seite offen

Aus demselben Grund konnte kein echter Browser-Netzwerkmitschnitt der Debug-Seite erstellt werden.

Code-Validierung nach PR #14:

- `debug` ist in `DEBUG_VIEWS`.
- `DEBUG_REFRESH_MS = 60000`.
- Der Debug-Endpunkt wird nur geladen, wenn die View Debug-Daten braucht oder wenn eine Aktion explizit `force=true` setzt.

Erwartung: Auf der Debug-Seite maximal etwa ein Fetch pro 60 Sekunden, solange keine Apply-/Dry-Run-/Tuning-Aktion ausgefuehrt wird.

### Dry Run

Messfenster: 2026-06-03 10:04:42 bis 10:05:17 Europe/Berlin.

Aktion: `benni_climate_policy.dry_run`, global, via HA-MCP.

Beobachtung:

- `sensor.climate_policy_apply_status`: `idle` -> `dry_run`, `action_count=4`.
- `sensor.climate_policy_last_apply`: blieb `never`.
- Keine Climate-/Switch-/Light-Service-Calls wurden ausgefuehrt.
- Keine WebSocket-/Recorder-/Integration-Warnings.
- Um 10:05:15 aenderten sich `sensor.garden_temperature_atomic` und `sensor.garden_illuminance_atomic`; die nachfolgenden Plan-Hash-Updates waren ein normaler Input-trigger und kein Dry-Run-Sturm.

### Weather Resolver

Aktueller Live-Zustand:

- `sensor.climate_forecast_temperature_3h` hat `source=entity`, `reason=configured_forecast_entity`.
- `sensor.climate_outdoor_feels_like_temperature` hat `source=entity`, `reason=configured_feels_like_entity`.
- `sensor.climate_effective_outdoor_temperature` zeigt in `forecast_resolution.last_fetch_at=null`.

Bewertung:

- In diesem Setup wird `weather.get_forecasts(type=hourly)` aktuell nicht genutzt, weil eine Forecast-Entity konfiguriert ist.
- Der PR-#14-Cache ist fuer den Weather-Service-Pfad vorhanden, aber im Live-Szenario nicht aktiv.

## Gefundene Hotspots

### Hotspot: volatile Diagnoseattribute auf Temperatur-Entities

Ein erweitertes History-Fenster von 09:45 bis 10:08 zeigte fuer `sensor.climate_effective_outdoor_temperature` hunderte Attribut-Updates. In den Eintraegen waren haeufig nur Diagnoseattribute veraendert, vor allem:

- `inputs.outdoor_lux`
- `inputs.forecast_resolution.target_time`
- Lux-/Forecast-Diagnosewerte bei unveraendertem oder gerundet gleichem Sensor-State

Zusaetzlich veroeffentlichte `sensor.climate_forecast_temperature_3h` bei konfigurierter Forecast-Entity ein laufendes `target_time=now+3h`, obwohl der eigentliche Forecast-Wert unveraendert blieb.

Das ist ein konkreter, messbarer Recorder-/WebSocket-Hotspot: nicht die Policy-Entscheidung selbst, sondern volatile Diagnose in Entity-Attributen.

## Umgesetzter kleiner Fix

Dateien:

- `custom_components/benni_climate_policy/sensor.py`
- `tests/test_event_hygiene.py`

Aenderung:

- `sensor.climate_effective_outdoor_temperature` veroeffentlicht nur noch kompakte, stabile Attribute:
  - `real_temperature`
  - `effective_temperature`
  - `input_quality`
  - `debug_payload_available`
  - kompakte Input-Quellen/Qualitaeten
- Hochfrequente Rohdiagnosen wie `outdoor_lux`, `sun_elevation`, komplette Forecast-/Feels-like-Resolution-Dumps und laufende `target_time`-Werte bleiben aus Entity-Attributen heraus.
- `sensor.climate_forecast_temperature_3h` nutzt fuer `target_time` nur noch den stabilen `forecast_datetime`; bei konfigurierter Forecast-Entity bleibt der Wert `None`.
- Volle Diagnose bleibt ueber den Debug-Endpunkt verfuegbar.

Nicht geaendert:

- Keine Policy-Fachlogik.
- Keine Apply-/Bad-/Tuning-Fachlogik.
- Keine Forecast-Auswahl.
- Kein Coordinator-Throttle auf Verdacht.

## Empfehlung

Empfehlung: kleiner Fix umgesetzt.

Begruendung:

- Der Hotspot war in HA-History konkret sichtbar.
- Die Aenderung reduziert Recorder-/WebSocket-Last, ohne Entscheidungslogik zu veraendern.
- Ein groesserer Umbau am Coordinator waere erst sinnvoll, wenn nach Deployment weiterhin hohe `recalculate_count`-/Publish-Werte auftreten.

Naechste Messung nach Deployment:

- Mit angemeldetem Browser Overview und Debug-Seite erneut messen.
- `sensor.climate_effective_outdoor_temperature` History ueber 10 Minuten pruefen.
- Erwartung: keine sekundenweisen Attributupdates mehr nur durch Lux-/`target_time`-Diagnose.

## Checks

Nach dem Fix lokal ausgefuehrt:

- `uv run --frozen pytest`: 78 passed
- `python -m compileall custom_components tests`: gruen
- `node --check custom_components\benni_climate_policy\frontend\app\main.js`: gruen
