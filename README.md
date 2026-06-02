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

Gefundene Entity-IDs sind nur Vorschlaege im Config Flow. Die Integration soll
am Ende selbst Source of Truth fuer Klima-Entscheidungen sein; alte
`sensor.climate_*_combined` und YAML-Apply-Logik bleiben nur
Migrationsreferenz.
