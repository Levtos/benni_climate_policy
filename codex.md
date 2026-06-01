# Codex Instructions — Climate Policy

Lies zuerst `CLAUDE.md`. MCP: `einhornzentrale`.

## Aktueller Status

Kernpfad PR 1-3 ist im Aufbau:

- Repository-/Live-HA-Inventur und Candidate Map
- eigene Context-/Weather-/Zone-Resolver
- effektive Aussentemperatur
- Wohnzimmer-/Kuechen-Policy
- interne Apply Engine mit Auto-Toggle, manuellem Apply und Dry Run

## Apply-Grundsatz

YAML-Apply in `einhornzentrale` ist nur Migrations-/Referenzmaterial. Der
Hauptweg ist die interne Apply Engine dieser Integration.

`switch.climate_policy_apply_active` bedeutet Auto-Apply aktiv. Wenn der Toggle
aus ist, darf kein automatischer Apply passieren. Manueller Apply per
Button/Service und `dry_run` bleiben separat moeglich; Safety Gates gelten
weiterhin, Dry Run schreibt nie auf Geraete.

## Anti-Patterns

- ❌ Direkte `climate.*` Service-Calls aus Toolbox-Modulen
- ❌ Lastenheft-Konsolidierung
- ❌ Auf alter VM Features bauen
- ❌ Alte `sensor.climate_*_combined` als finale Runtime-Abhaengigkeit nutzen
