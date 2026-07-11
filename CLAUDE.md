# CLAUDE.md — Climate Policy

## GitLab Workflow

- GitLab project `ha-platform/control` is the central workflow truth.
- Relevant work requires a GitLab issue in `ha-platform/control`.
- Before work starts, read the issue description and all issue notes.
- Document current state, decisions, scope changes, tests, commits, merge requests, blockers, and completion in the issue.
- Code changes happen in the matching GitLab repository. `origin` must point to GitLab.
- GitHub is only the public distribution and HACS mirror. Do not develop directly on GitHub and do not push manually to GitHub.
- Plane and Forgejo are historical sources only and are not used for active work.
- Full rules live in `ha-platform/control/AGENTS.md`, `ha-platform/control/CLAUDE.md`, and `ha-platform/control/docs/workflow/`.

## Safety

- Do not put secrets in issues, commits, logs, or reports.
- Do not touch production Home Assistant systems without explicit approval.
- No admin, delete, runner, or bulk actions without explicit approval.

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
