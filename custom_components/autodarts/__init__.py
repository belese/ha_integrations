"""The autodarts integration."""
from __future__ import annotations
import json
from os import walk, path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http.view import HomeAssistantView

from autodarts import AutoDartSession, CloudBoard

from .const import (
    DOMAIN,
    AUTODART_CLIENT_ID,
    AUTODART_REALM_NAME,
    AUTODART_CLIENT_SECRET,
)

from .coordinator import (
    AutoDartsBoardCoordinator,
    AutoDartsBoardMatchCoordinator,
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH
]


DATA_EXTRA_MODULE_URL = 'frontend_extra_module_url'
LOADER_URL = f'/{DOMAIN}/main.js'
LOADER_PATH = f'custom_components/{DOMAIN}/main.js'
ICONS_URL = f'/{DOMAIN}/icons'
ICONLIST_URL = f'/{DOMAIN}/list'
ICONS_PATH = f'custom_components/{DOMAIN}/data'

class ListingView(HomeAssistantView):

    requires_auth = False

    def __init__(self, url, iconpath):
        self.url = url
        self.iconpath = iconpath
        self.name = "Icon Listing"

    async def get(self, request):
        icons = []
        for (dirpath, dirnames, filenames) in walk(self.iconpath):
            icons.extend(
                [
                    {"name": path.join(dirpath[len(self.iconpath):], fn[:-4])}
                    for fn in filenames if fn.endswith(".svg")
                ]
            )
        return json.dumps(icons)


async def async_setup(hass, config):
    hass.http.register_static_path(
            LOADER_URL,
            hass.config.path(LOADER_PATH),
            True
        )
    add_extra_js_url(hass, LOADER_URL)

    """
    for iset in ["darts",]:
        hass.http.register_static_path(
                ICONS_URL + "/" + iset,
                hass.config.path(ICONS_PATH + "/" + iset),
                True
            )
        hass.http.register_view(
                ListingView(
                    ICONLIST_URL + "/" + iset,
                    hass.config.path(ICONS_PATH + "/" + iset)
                )
            )
    """
    hass.http.register_static_path(
            ICONS_URL + "/darts",
            hass.config.path(ICONS_PATH + "/darts"),
            True
        )
    hass.http.register_view(
            ListingView(
                ICONLIST_URL + "/darts",
                hass.config.path(ICONS_PATH + "/darts")
            )
        )
    return True

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
