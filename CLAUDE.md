# CLAUDE.md — Climate Policy

**Status:** Kernpfad PR 1-3 angelegt: Inventur/Candidate Map, Context Resolver,
effektive Aussentemperatur, Wohnzimmer-/Kuechen-Policy, interne Apply Engine.
**Letzte Aktualisierung:** 2026-06-01

---

## Was ist dieses Modul

Klima-Policy: entscheidet pro Raum (Wohnzimmer, Küche, Bad) welche Soll-Temperatur + Modus (komfort/spar/boost) anzuwenden sind. Konsumiert Presence + Bio + Day-State + Window-Status + DWD-Wetter. Plus Preheat-Logik: wenn `presence_preheat_active`, vorheizen.

Outputs analog Aggregat-Pattern:
- `sensor.<raum>_climate_mode` (komfort/spar/boost/off)
- `sensor.<raum>_climate_target_temp`
- `sensor.<raum>_climate_plan_hash`
- `binary_sensor.<raum>_climate_apply_blocked`

**Lastenheft:** `einhornzentrale/docs/lastenhefte/reviewed/klimalogik/`

## Architektur-Kontext

Eigene HACS-Custom-Integration. Phase 3 (Aggregat). Konsumiert Foundation + Window-Atomics als HA-Entities.

**Pendant-Briefings:**
- `bennis_toolbox/CLAUDE.md` — Foundation + Pattern
- `einhornzentrale/CLAUDE.md` — YAML + Cut-Over-Status
- `einhornzentrale/docs/roadmap.md` — Phase 3

## Kernpfad

PR 1-3 sind priorisiert, weil schnell ein sicherer Heizpfad gebraucht wird:

- PR 1: Repo-/Live-HA-Inventur, Candidate Map, Skeleton, Config Flow, Basis-Entities
- PR 2: Context Resolver, effektive Aussentemperatur, Wohnzimmer-/Kuechen-Policy
- PR 3: interne Apply Engine mit Auto-Toggle, manuellem Apply, Dry Run und lesbaren Blockgruenden

Frontend/UX startet erst nach lauffaehigem PR-3-Kern.

## Pattern

Referenz: Light Policy (sobald gebaut), sonst `benni_core_user_state` / `benni_core_presence_state` aus `bennis_toolbox/modules/`.
