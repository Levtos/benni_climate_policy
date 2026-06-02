"""Pure option helpers for Benni Climate Policy."""
from __future__ import annotations

from typing import Any, Mapping

from .const import CONF_APPLY_COOLDOWN_SECONDS, CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS


def apply_cooldown_seconds_from_config(config: Mapping[str, Any]) -> int:
    value = config.get(CONF_APPLY_COOLDOWN_SECONDS, config.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS))
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_COOLDOWN_SECONDS
    return seconds if seconds > 0 else DEFAULT_COOLDOWN_SECONDS
