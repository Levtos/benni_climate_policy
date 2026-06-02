# benni_climate_policy

Eigenstaendige HACS-Custom-Integration fuer Bennis Klima-Policy.

Der aktuelle Kernpfad baut zuerst die praktisch nutzbaren Heizfunktionen:

- Context lesen
- effektive Aussentemperatur berechnen
- Wohnzimmer/Kueche Policy berechnen
- internen Apply Toggle bereitstellen
- manuellen Apply und Dry Run anbieten
- jeden Skip/Block lesbar erklaeren

## Diagnose-Panel

Die Integration registriert ein read-only Panel in der Home-Assistant-Sidebar:

- Titel: `Climate Policy`
- Direktpfad: `/benni-climate-policy`

Das Panel zeigt Context, Zonenplaene, effektive Aussentemperatur, Apply-Status,
konfigurierte Inputs und kompakte Debugdaten. Es veraendert keine Policy-Regeln.

## Weather Resolver

Fuer Wetterdaten wird die vorhandene Home-Assistant-Weather-Entity genutzt. In
der Testinstanz ist `weather.dwd_home` aus `hg1337/homeassistant-dwd` die
bevorzugte DWD-Quelle.

- `Forecast-Temperatur +3h` kann optional als Sensor-Entity konfiguriert werden.
- Wenn keine Forecast-Sensor-Entity gesetzt ist, liest der Resolver
  `weather.get_forecasts(type=hourly)` read-only aus der Weather-Entity und
  waehlt den stundenweisen Forecast-Punkt mit der kleinsten Zeitdifferenz zu
  `now + 3h`.
- Wenn kein stundenweiser Forecast verfuegbar ist, faellt Forecast neutral auf
  die reale Aussentemperatur zurueck.
- `Gefuehlte Aussentemperatur` ist optional. Ohne echte Quelle faellt sie auf
  die reale Aussentemperatur zurueck, sodass der Feels-like-Offset neutral ist.
- Eine zweite DWD-Integration ist nicht erforderlich.

Gefundene Entity-IDs sind nur Vorschlaege im Config Flow. Die Integration soll
am Ende selbst Source of Truth fuer Klima-Entscheidungen sein; alte
`sensor.climate_*_combined` und YAML-Apply-Logik bleiben nur
Migrationsreferenz.
Alte `*_combined` Feels-like-Sensoren sind ebenfalls nur Migration/Referenz und
keine finale Runtime-Abhaengigkeit.
