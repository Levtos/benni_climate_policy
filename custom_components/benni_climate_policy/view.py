"""Panel registration for the read-only Climate Policy cockpit."""
from __future__ import annotations

import logging
import os

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    FRONTEND_DIR_URL,
    FRONTEND_ENTRY,
    PANEL_ELEMENT,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL_PATH,
)
from .diagnostics import full_debug_payload

_LOGGER = logging.getLogger(__name__)

_BASE = os.path.dirname(__file__)
_APP_DIR = os.path.join(_BASE, "frontend", "app")
_STATIC_FLAG = "_view_static_registered"
_PANEL_FLAG = "_view_panel_registered"
_DEBUG_VIEW_FLAG = "_view_debug_registered"


def _cache_bust() -> str:
    try:
        return str(int(os.path.getmtime(os.path.join(_APP_DIR, "main.js"))))
    except OSError:
        return "0"


async def async_setup_view(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get(_DEBUG_VIEW_FLAG):
        hass.http.register_view(ClimatePolicyDebugView())
        data[_DEBUG_VIEW_FLAG] = True

    if not data.get(_STATIC_FLAG):
        await hass.http.async_register_static_paths([
            StaticPathConfig(FRONTEND_DIR_URL, _APP_DIR, False),
        ])
        data[_STATIC_FLAG] = True

    if data.get(_PANEL_FLAG):
        return

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        require_admin=False,
        config={
            "_panel_custom": {
                "name": PANEL_ELEMENT,
                "module_url": f"{FRONTEND_ENTRY}?{_cache_bust()}",
            },
        },
    )
    data[_PANEL_FLAG] = True


class ClimatePolicyDebugView(HomeAssistantView):
    """Authenticated read-only endpoint for full diagnostics."""

    url = f"/api/{DOMAIN}/debug"
    name = f"api:{DOMAIN}:debug"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        coord = next(
            (
                bucket[DATA_COORDINATOR]
                for bucket in hass.data.get(DOMAIN, {}).values()
                if isinstance(bucket, dict) and DATA_COORDINATOR in bucket
            ),
            None,
        )
        if coord is None:
            return self.json({"error": "coordinator_not_available"}, status_code=404)
        if coord.decision is None:
            await coord.async_evaluate(auto_apply=False)
        decision = coord.decision
        if decision is None:
            return self.json({"error": "decision_not_available"}, status_code=503)
        debug = coord.debug_payload()
        return self.json(full_debug_payload(
            timestamp=dt_util.now(),
            context=decision.context.as_dict(),
            effective_outdoor_temperature=decision.effective_temperature.as_dict(),
            plans={zone: plan.as_dict() for zone, plan in decision.zone_plans.items()},
            debug=debug,
        ))


def async_remove_view(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get(_PANEL_FLAG):
        return
    try:
        async_remove_panel(hass, PANEL_URL_PATH)
    except Exception as err:  # noqa: BLE001 - panel may already be gone during reload
        _LOGGER.debug("panel remove skipped: %s", err)
    data[_PANEL_FLAG] = False
