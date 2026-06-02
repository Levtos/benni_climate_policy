"""Resolve configured and known context entities into typed snapshots."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

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
    CONF_CONTEXT_WAKEUP,
    CONF_CONTEXT_WORKDAY,
)
from .integration_contracts import candidate_for
from .models import ClimateContextSnapshot, SourceValue


def _state_value(hass: "HomeAssistant", entity_id: str | None, *, none_is_valid: bool = False) -> SourceValue:
    if not entity_id:
        return SourceValue(None, None, "missing", False)
    state = hass.states.get(entity_id)
    if state is None:
        return SourceValue(None, entity_id, "missing", False)
    invalid = ("unknown", "unavailable", "") if none_is_valid else ("unknown", "unavailable", "none", "")
    if state.state in invalid:
        return SourceValue(state.state, entity_id, "unknown", False)
    return SourceValue(state.state, entity_id, "ok", False)


def _parse_wakeup(value: SourceValue) -> SourceValue:
    if value.value in (None, "", "unknown", "unavailable", "none"):
        return value
    if isinstance(value.value, datetime):
        return value
    try:
        return SourceValue(datetime.fromisoformat(str(value.value)), value.source_entity_id, value.quality, value.fallback_used)
    except ValueError:
        return SourceValue(value.value, value.source_entity_id, "degraded", value.fallback_used)


class ContextResolver:
    """Uses config-entry selections first, then known contracts as fallback."""

    def __init__(self, hass: "HomeAssistant", config: dict[str, Any]) -> None:
        self.hass = hass
        self.config = config

    def _entity(self, key: str) -> str | None:
        configured = self.config.get(key)
        if configured:
            return str(configured)
        return candidate_for(key)

    def resolve(self) -> ClimateContextSnapshot:
        wakeup = _parse_wakeup(_state_value(self.hass, self._entity(CONF_CONTEXT_WAKEUP)))
        return ClimateContextSnapshot(
            activity_state=_state_value(self.hass, self._entity(CONF_CONTEXT_ACTIVITY)),
            bio_state=_state_value(self.hass, self._entity(CONF_CONTEXT_BIO)),
            day_context=_state_value(self.hass, self._entity(CONF_CONTEXT_DAY_CONTEXT)),
            day_state=_state_value(self.hass, self._entity(CONF_CONTEXT_DAY_STATE)),
            presence_band=_state_value(self.hass, self._entity(CONF_CONTEXT_PRESENCE_BAND)),
            presence_household=_state_value(self.hass, self._entity(CONF_CONTEXT_PRESENCE_HOUSEHOLD)),
            presence_personal=_state_value(self.hass, self._entity(CONF_CONTEXT_PRESENCE_PERSONAL)),
            presence_preheat_active=_state_value(self.hass, self._entity(CONF_CONTEXT_PREHEAT_ACTIVE)),
            presence_transition=_state_value(self.hass, self._entity(CONF_CONTEXT_TRANSITION), none_is_valid=True),
            workday_state=_state_value(self.hass, self._entity(CONF_CONTEXT_WORKDAY)),
            planned_wakeup_time=wakeup,
        )
