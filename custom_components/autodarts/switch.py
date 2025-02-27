from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AutoDartChildEntity, AutoDartEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    match_coordinator = hass.data[DOMAIN][entry.entry_id]["match_coordinator"]
    board_coordinator = hass.data[DOMAIN][entry.entry_id]["board_coordinator"]

    cloud_binary_sensor = CloudConnectionBinarySensor(match_coordinator)
    board_binary_sensor = CloudBoardBinarySensor(board_coordinator)

    async_add_entities(
        [
            cloud_binary_sensor,
            board_binary_sensor,
        ]
    )


async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    pass


class CloudConnectionBinarySensor(AutoDartChildEntity, SwitchEntity):
    """Switch to connect autodarts to cloud."""

    __name__ = "cloud connection"

    @property
    def is_on(self) -> bool:
        """Return True if entity is available."""
        return self.board_coordinator.connected

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.board_coordinator.connect()
        # force a match refresh
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.board_coordinator.disconnect()
        # force a match refresh to set state to unknown
        await self.coordinator.async_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.board_coordinator.id)
            },
            name=f"Autodarts {self.board_coordinator.item.name}"
            if self.coordinator.item
            else None,
            manufacturer="Autodarts.io",
            model="Board Manager",
            sw_version=self.board_coordinator.item.version
            if self.coordinator.item
            else None,
        )


class CloudBoardBinarySensor(AutoDartEntity, SwitchEntity):
    __name__ = "board"

    @property
    def is_on(self) -> bool:
        """Return True if entity is available."""
        if self.coordinator.data:
            return self.coordinator.data.state["connected"]

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator.data.async_start()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.coordinator.data.async_stop()

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data:
            return {
                "name": self.coordinator.data.name,
                "ip": self.coordinator.data.ip,
                "connected": self.coordinator.data.connected,
                "os": self.coordinator.data.os,
                "version": self.coordinator.data.version,
            }
