# Weather Source Analysis

Stand: 2026-06-02, Live-Analyse ueber den `einhornzentrale` Home-Assistant-MCP.

Ziel der Analyse: klaeren, welche DWD-/Weather-Quellen in der Home-Assistant-Testinstanz wirklich vorhanden sind und wie `benni_climate_policy` daraus `Forecast-Temperatur +3h` sowie optional eine gefuehlte Aussentemperatur aufloesen kann.

## Gefundene Entities

### Weather-Entities

| entity_id | Name | Plattform | Status | Bewertung |
|---|---|---|---|---|
| `weather.dwd_home` | `Wuppertal-Buchenhofen` | `dwd` | aktiv, state `rainy` | DWD/hg1337-Kandidat, nutzbar |

Registry/Integration:

- `weather.dwd_home` gehoert zur Integration `dwd` mit Titel `Wuppertal-Buchenhofen`.
- Die Config Entry ist `loaded`, `source=user`, `disabled_by=null`.
- Attribution im State: `Quelle: Deutscher Wetterdienst`.
- Das passt zur installierten HACS-Integration `Deutscher Wetterdienst (by hg1337)`.

Aktuelle Attribute von `weather.dwd_home`:

| Attribut | Wert |
|---|---:|
| `state` | `rainy` |
| `temperature` | `21.4` |
| `humidity` | `70` |
| `pressure` | `1004.5` |
| `wind_speed` | `13.0` |
| `wind_bearing` | `178.0` |
| `wind_gust_speed` | `30.0` |
| `dew_point` | `15.6` |
| `cloud_coverage` | `85.0` |
| `attribution` | `Quelle: Deutscher Wetterdienst` |
| `supported_features` | `3` |

Forecast-relevante Attribute im Entity-State:

- Kein `forecast`-Attribut im Entity-State.
- Kein `forecast_hourly`, `forecast_daily` oder vergleichbarer Forecast-Dump im Entity-State.
- Forecast-Daten werden stattdessen ueber den Home-Assistant-Service `weather.get_forecasts` bereitgestellt.

### DWD-/MOSMIX-/Forecast-Suche

| Suchbegriff | Treffer | Bewertung |
|---|---:|---|
| `dwd` | 3 | `weather.dwd_home` aktiv; zwei Warnlevel-Sensoren unavailable |
| `mosmix` | 0 | keine separate MOSMIX-Entity sichtbar |
| `forecast` | 0 | keine separate Forecast-Entity sichtbar |
| `vorhersage` | 0 | keine separate Vorhersage-Entity sichtbar |

DWD-Warnlevel-Sensoren:

| entity_id | Name | Plattform | Status | Bewertung |
|---|---|---|---|---|
| `sensor.dwd_home_advance_warning_level` | `Vorwarnstufe` | `dwd_weather_warnings` | `unavailable` | keine Forecast-Temperaturquelle |
| `sensor.dwd_home_current_warning_level` | `Aktuelle Warnstufe` | `dwd_weather_warnings` | `unavailable` | keine Forecast-Temperaturquelle |

### Temperatur-/Feels-like-Kandidaten

Relevante aktive Kandidaten:

| entity_id | State | Plattform | Source-Attribut | Bewertung |
|---|---:|---|---|---|
| `sensor.weather_temperature_atomic` | `21.4` | `template` | `weather.dwd_home` | DWD-Now-Temperatur als Template-Atomic |
| `sensor.garden_temperature_atomic` | `19.2` | `template` | `sensor.garden_climate_temperature` | bestehende reale Aussentemperatur laut Candidate Map |
| `sensor.climate_effective_outdoor_temperature` | `17.7` | `benni_climate_policy` | n/a | Ergebnis der Integration, keine Eingangsquelle |
| `sensor.climate_effective_outdoor_temperature_combined` | `19.2` | `template` | `sensor.garden_temperature_atomic` | alte Combined-Schicht |
| `sensor.climate_outdoor_feels_like_temperature_combined` | `19.2` | `template` | `sensor.climate_effective_outdoor_temperature_combined` | alte Combined-Schicht, keine echte DWD-Feels-like-Quelle |

Feels-like-/Apparent-Suche:

| Suchbegriff | Treffer | Bewertung |
|---|---:|---|
| `feels` | 5 | nur `*_combined`-Sensoren |
| `apparent` | 0 | keine echte Apparent-Temperature-Entity |
| `gefuehlt` | 0 | keine echte Gefuehlt-Entity |
| `gefuehlte` / Umlaut-Schreibweise | 0 | keine echte Gefuehlt-Entity |

Die gefundenen `*_feels_like_temperature_combined`-Sensoren sind aktiv, aber sie stammen aus der alten Combined-/Template-Schicht und nicht direkt aus hg1337-DWD/MOSMIX.

### Aktive, unavailable und deaktivierte Kandidaten

Aktive Kandidaten:

- `weather.dwd_home`
- `sensor.weather_temperature_atomic`
- `sensor.garden_temperature_atomic`
- `sensor.climate_outdoor_feels_like_temperature_combined`
- `sensor.climate_effective_outdoor_temperature_combined`

Unavailable Kandidaten:

- `sensor.dwd_home_advance_warning_level`
- `sensor.dwd_home_current_warning_level`

Deaktivierte Kandidaten:

- Fuer die konkret gefundenen Kandidaten meldet die Entity Registry `disabled_by=null`.
- Ueber die verfuegbaren MCP-Suchabfragen wurde keine weitere deaktivierte DWD-/MOSMIX-/Forecast-/Feels-like-Entity sichtbar.

## Forecast-Zugriff

Der Home-Assistant-Service `weather.get_forecasts` ist vorhanden.

Service-Schema:

- Domain: `weather`
- Service: `get_forecasts`
- Pflichtfeld: `type`
- Erlaubte Werte: `daily`, `hourly`, `twice_daily`

Read-only-Abfrage:

```yaml
service: weather.get_forecasts
target:
  entity_id: weather.dwd_home
data:
  type: hourly
return_response: true
```

Ergebnis:

- Die Abfrage war erfolgreich.
- Es wurden stundenweise Forecast-Eintraege fuer `weather.dwd_home` geliefert.
- Die Abfrage erzeugte keine State-Changes (`changed_states: []`).

Erste Forecast-Eintraege:

| datetime UTC | datetime Europe/Berlin | temperature | condition | dew_point | humidity |
|---|---|---:|---|---:|---|
| `2026-06-02T14:00:00+00:00` | `2026-06-02 16:00` | `19.8` | `rainy` | `14.7` | n/a |
| `2026-06-02T15:00:00+00:00` | `2026-06-02 17:00` | `18.8` | `rainy` | `15.1` | n/a |
| `2026-06-02T16:00:00+00:00` | `2026-06-02 18:00` | `18.2` | `rainy` | `15.0` | n/a |
| `2026-06-02T17:00:00+00:00` | `2026-06-02 19:00` | `17.6` | `rainy` | `14.8` | n/a |
| `2026-06-02T18:00:00+00:00` | `2026-06-02 20:00` | `16.9` | `rainy` | `14.5` | n/a |

Live-Zeit waehrend der Analyse:

- `now`: `2026-06-02T16:55:48+02:00`
- `now + 3h`: `2026-06-02T19:55:48+02:00`

Eintrag nahe `now + 3h`:

- Naechster Stuetzpunkt: `2026-06-02T18:00:00+00:00` = `2026-06-02 20:00` Europe/Berlin.
- Temperatur: `16.9`
- Condition: `rainy`
- Dew point: `14.5`
- Humidity: nicht geliefert.

Bewertung: `Forecast-Temperatur +3h` kann aus `weather.dwd_home` ueber `weather.get_forecasts(type=hourly)` gelesen werden. Da die Forecasts stuendlich sind, sollte der Resolver den Eintrag mit der kleinsten Zeitdifferenz zu `now + 3h` waehlen oder den naechsten Forecast-Eintrag ab Zielzeit verwenden. Welche Strategie fachlich gewuenscht ist, muss aus dem Lastenheft bzw. einer expliziten Entscheidung kommen.

## Feels-like-Quelle

Es wurde keine echte hg1337-DWD-/MOSMIX-Entity fuer gefuehlte Aussentemperatur gefunden.

Gefunden wurde nur:

- `sensor.climate_outdoor_feels_like_temperature_combined`
- State waehrend der Analyse: `19.2`
- Source-Attribut: `sensor.climate_effective_outdoor_temperature_combined`
- Plattform: `template`

Bewertung:

- Das ist keine echte DWD-Feels-like-Quelle.
- Es ist eine alte Combined-/Template-Ableitung.
- Fuer `benni_climate_policy` sollte diese Entity nicht als harte Runtime-Abhaengigkeit fuer eine neue Resolver-Schicht dienen.

Wenn keine echte `feels_like`-Quelle konfiguriert oder gefunden wird, ist ein sauberer Fallback auf reale Aussentemperatur plausibel: fachlich bedeutet das `feels_like_temperature = real_temperature`, wodurch der `feels_like_offset` neutral bleibt. Alternativ kann `None` beibehalten werden, wie die bestehende Policy es schon toleriert; dann bleibt der Feels-like-Anteil ebenfalls neutral. Die Entscheidung, ob der Debug explizit `fallback_to_real_temperature` zeigen soll, sollte im Folge-PR sichtbar gemacht werden.

## Empfohlene Resolver-Strategie

Aus dem Live-Stand ergibt sich diese Strategie:

1. Bestehende Entity-Konfiguration weiter respektieren.
   - Wenn `forecast_temperature_3h` als Entity konfiguriert ist, diesen Wert weiterhin verwenden.
   - Wenn `outdoor_feels_like` als Entity konfiguriert ist, diesen Wert weiterhin verwenden.

2. Zusaetzlich einen read-only Weather Resolver fuer DWD/HA-Weather ergaenzen.
   - Neuer optionaler Config-/Options-Wert fuer eine Weather-Entity, z. B. `weather_entity`.
   - Kandidat in dieser Instanz: `weather.dwd_home`.
   - Resolver liest aktuelle Weather-Attribute fuer Temperatur, Condition, Dew Point usw.
   - Resolver fragt fuer Forecast +3h `weather.get_forecasts(type=hourly)` ab.
   - Keine Geraete- oder Climate-/Switch-/Light-Service-Calls.
   - Nur Forecast-Service mit `return_response=True`.

3. Forecast +3h aus `weather.dwd_home` ableiten.
   - Zielzeit: `dt_util.now() + timedelta(hours=3)`.
   - Forecast-Liste aus `weather.get_forecasts`.
   - Temperaturfeld: `temperature`.
   - Condition-Feld: `condition`.
   - Optional fuer Diagnose: `dew_point`, `cloud_coverage`, `precipitation_probability`, `wind_speed`.
   - Keine Speicherung grosser Forecast-Listen in Entity-Attributen; falls Diagnose noetig ist, ueber den bestehenden Debug-Endpunkt.

4. Feels-like sauber neutral behandeln.
   - Keine echte DWD-Feels-like-Entity gefunden.
   - Falls keine konfigurierte Feels-like-Entity existiert, `feels_like_temperature` entweder `None` lassen oder explizit auf reale Aussentemperatur fallbacken.
   - Der fachliche Effekt muss neutral bleiben: kein zusaetzlicher Offset ohne echte Quelle.
   - Debug sollte die Quelle sichtbar machen, z. B. `source: missing`, `fallback: real_temperature` oder `not_available`.

5. Keine zweite DWD-Integration installieren.
   - Die vorhandene `dwd`-Integration liefert `weather.dwd_home`.
   - `weather.get_forecasts` liefert stundenweise Forecasts.
   - Eine zweite DWD-Integration erscheint fuer Forecast +3h nicht noetig.

## Offene Fragen

- Soll der +3h-Resolver den zeitlich naechsten Forecast-Punkt waehlen oder den ersten Forecast-Punkt ab `now + 3h`?
- Soll `feels_like_temperature` intern `None` bleiben, wenn keine echte Quelle existiert, oder explizit auf reale Aussentemperatur fallbacken?
- Soll `weather.dwd_home` im Config-/Options-Flow als eigene Weather-Entity ausgewaehlt werden, statt Forecast +3h als numerische Sensor-Entity zu erwarten?
- Soll die bestehende `sensor.weather_temperature_atomic` als Fallback fuer reale DWD-Temperatur angeboten werden, wenn `sensor.garden_temperature_atomic` fehlt?

## Kurzbewertung

- `weather.dwd_home` ist vorhanden, aktiv und kommt aus der DWD-Integration.
- `Forecast-Temperatur +3h` kann aus `weather.dwd_home` ueber `weather.get_forecasts(type=hourly)` gelesen werden.
- Eine echte DWD-/MOSMIX-Feels-like-Entity wurde nicht gefunden.
- Eine zweite DWD-Integration erscheint nicht notwendig.
- Sinnvoller Folge-PR: Weather Resolver in `benni_climate_policy`, der `weather.dwd_home` read-only nutzt und Forecast +3h aus dem HA-Weather-Service ableitet.
