"""The autodarts integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    AUTODART_CLIENT_ID,
    AUTODART_REALM_NAME,
    AUTODART_CLIENT_SECRET,
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH
]

from autodarts import AutoDartSession, CloudBoard
from .coordinator import (
    AutoDartsBoardCoordinator,
    AutoDartsBoardMatchCoordinator,
)     

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up autodarts from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    session = AutoDartSession(
        email=entry.data["email"],
        password=entry.data["password"],
        client_id=AUTODART_CLIENT_ID,
        realm_name=AUTODART_REALM_NAME,
        client_secret_key=AUTODART_CLIENT_SECRET,
    )

    if not await session.is_authenticated():
        raise InvalidAuth
    
    board_coordinator = AutoDartsBoardCoordinator(hass,session,entry.data['board_id'])
    await board_coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id]['board_coordinator'] = board_coordinator

    match_coordinator = AutoDartsBoardMatchCoordinator(hass,board_coordinator)
    await match_coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id]['match_coordinator'] = match_coordinator
    
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            entry, PLATFORMS
        )
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
