"""Entity contract suggestions for known provider integrations."""
from __future__ import annotations

from dataclasses import dataclass

from .const import (
    CONF_CONTEXT_ACTIVITY,
    CONF_CONTEXT_BIO,
    CONF_CONTEXT_DAY_CONTEXT,
    CONF_CONTEXT_DAY_STATE,
    CONF_CONTEXT_PRESENCE_BAND,
    CONF_CONTEXT_PRESENCE_HOUSEHOLD,
    CONF_CONTEXT_PRESENCE_PERSONAL,
    CONF_CONTEXT_PREHEAT_ACTIVE,
    CONF_CONTEXT_TRANSITION,
    CONF_CONTEXT_WORKDAY,
    PRESET,
)


@dataclass(frozen=True)
class EntityCandidate:
    key: str
    entity_id: str
    provider: str
    reliability: str
    note: str = ""


CONTEXT_CANDIDATES: tuple[EntityCandidate, ...] = (
    EntityCandidate(CONF_CONTEXT_ACTIVITY, "sensor.context_activity_state_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_BIO, "sensor.context_bio_state_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_DAY_CONTEXT, "sensor.context_day_context_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_DAY_STATE, "sensor.context_day_state_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_BAND, "sensor.context_presence_band_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_HOUSEHOLD, "sensor.context_presence_household_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_PERSONAL, "sensor.context_presence_personal_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PREHEAT_ACTIVE, "binary_sensor.context_presence_preheat_active_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_TRANSITION, "sensor.context_presence_transition_combined", "combined.context", "confirmed"),
    EntityCandidate(CONF_CONTEXT_WORKDAY, "sensor.context_day_context_combined", "combined.context", "confirmed"),
)


def candidate_for(key: str) -> str | None:
    for candidate in CONTEXT_CANDIDATES:
        if candidate.key == key:
            return candidate.entity_id
    return PRESET.get(key)

