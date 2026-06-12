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
    EntityCandidate(CONF_CONTEXT_ACTIVITY, "sensor.benni_combined_context_activity_state", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_BIO, "sensor.benni_combined_context_bio_state", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_DAY_CONTEXT, "sensor.benni_combined_context_day_context", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_DAY_STATE, "sensor.benni_combined_context_day_state", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_BAND, "sensor.benni_combined_context_presence_band", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_HOUSEHOLD, "sensor.benni_combined_context_presence_household", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PRESENCE_PERSONAL, "sensor.benni_combined_context_presence_personal", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_PREHEAT_ACTIVE, "sensor.benni_combined_context_presence_preheat_active", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_TRANSITION, "sensor.benni_combined_context_presence_transition", "benni_core_devices", "confirmed"),
    EntityCandidate(CONF_CONTEXT_WORKDAY, "sensor.benni_combined_context_day_context", "benni_core_devices", "confirmed"),
)


def candidate_for(key: str) -> str | None:
    for candidate in CONTEXT_CANDIDATES:
        if candidate.key == key:
            return candidate.entity_id
    return PRESET.get(key)

