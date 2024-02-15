from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import logging

from homeassistant.components.button import (
    ButtonEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ( 
    DOMAIN,
    AUTODART_MATCH_URL
)

from .entity import AutoDartEntity, AutoDartChildEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    match_coordinator = hass.data[DOMAIN][entry.entry_id]['match_coordinator']
    next_button = NextButton(match_coordinator)
    undo_button = UndoButton(match_coordinator)
    finish_button = FinishButton(match_coordinator)
    async_add_entities(
        [
            next_button,
            undo_button,
            finish_button
        ]
    )

async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    pass

class NextButton(AutoDartChildEntity,ButtonEntity):
    """Button for next Autodart. Depending on the state, it could be next player or next leg"""
    
    __name__ = "next"

    #entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL

    async def async_press(self):
        if self.coordinator.data :
            if self.coordinator.data.finished :
                await self.coordinator.data.async_next_match()
            else :
                await self.coordinator.data.async_next_player()
    
    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data :
            if self.coordinator.data.finished :
                return {'action' : 'next leg'}
            else :
                return {'action' : 'next player'}

class UndoButton(AutoDartChildEntity,ButtonEntity):
    """Button for undo throw on Autodart"""
    
    __name__ = "undo"

    #entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL

    async def async_press(self):
        if self.coordinator.data :
            await self.coordinator.data.async_undo()

class FinishButton(AutoDartChildEntity,ButtonEntity):
    """Button for next Autodart. Depending on the state, it could be cancel or finish math"""
    
    __name__ = "finish"

    #entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL

    async def async_press(self):
        if self.coordinator.data :
            if self.coordinator.data.finished :
                await self.coordinator.data.async_finish()
            else :
                await self.coordinator.data.async_abort()

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data :
            if self.coordinator.data.finished :
                return {'action' : 'finish'}
            else :
                return {'action' : 'cancel'}
