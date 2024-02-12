"""Support for the Airzone Cloud binary sensors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ( 
    DOMAIN,
    MATCH_WAITING,
    MATCH_STARTED,
    MATCH_STOPPED,
    AUTODART_MATCH_URL
)

from .entity import AutoDartEntity, AutoDartChildEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    match_coordinator = hass.data[DOMAIN][entry.entry_id]['match_coordinator']
    board_coordinator = hass.data[DOMAIN][entry.entry_id]['board_coordinator']
    
    board_state_sensor = BoardStateSensor(board_coordinator)
    match_sensor = MatchSensor(match_coordinator)
    turn_sensor = TurnSensor(match_coordinator)
    player_sensors = [ PlayerSensor(match_coordinator, idx) for idx in range(6) ]
    
    async_add_entities(
        [
            match_sensor,
            turn_sensor
        ] + player_sensors
    )

async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    pass


class BoardStateSensor(AutoDartEntity,SensorEntity) :
    __name__ = "board state"

    @property
    def native_value(self) -> str | None:
        """Return the state of the match."""
        if self.coordinator.data :
            return self.coordinator.data.state['status']

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data :
            return {
                "throw": self.coordinator.data.state['numThrows'],
            }


class PlayerSensor(AutoDartChildEntity,SensorEntity) :
    __name__ = "player"

    @property
    def player(self) :
        if self.is_playing :
            return self.coordinator.data.players[self.idx]
    @property
    def score(self) :
        if self.is_playing :
            return self.coordinator.data.scores[self.idx]
    
    @property
    def game_score(self) :
        if self.is_playing :
            return self.coordinator.data.game_scores[self.idx] 
    
    @property
    def segments(self) :
        if self.is_playing :
            return {number: value[self.idx] for number, value in self.coordinator.data.state['segments'].items() }
    
    @property
    def winner(self) :
        if self.is_playing :
            return self.coordinator.data.winner == self.idx
    
    @property
    def stats(self) :
        if self.is_playing :
            stats = self.coordinator.data.stats[self.idx].copy()
            stats.pop('game',None)
            stats.pop('indices',None)
            return stats
    
    @property
    def is_playing(self) :
        if self.coordinator.data :
            return self.idx < len(self.coordinator.data.players)
        return False
    
    @property
    def current(self) :
        if self.coordinator.data :
            return self.idx == self.coordinator.data.player,
        return False
    
    @property
    def native_value(self) -> str | None:
        """Return the state of the match."""
        _LOGGER.warning(f'native_value {self.coordinator.data} {self.coordinator.data} ')
        if player:=self.player :
            return player.name

    @property
    def extra_state_attributes(self) -> dict | None:
        attributes= {'index' : self.idx, "play" : self.is_playing}
        
        if player:=self.player :
            attributes['ppr'] = player.cpuPPR
            attributes['winner'] = self.winner
            attributes['sets'] = self.score['sets']
            attributes['legs'] = self.score['legs']
            attributes['current'] = self.current
            if self.coordinator.data.variant == 'Cricket' :
                attributes['score'] =  {
                    'point' : self.game_score,
                    'segments' : self.segments 
                }
            else :
                attributes['score'] = self.game_score
            attributes['stats'] = self.stats
            if player.user_id :
                attributes['autodarts_id'] = player.user_id

        return attributes

class TurnSensor(AutoDartChildEntity,SensorEntity):
    """Sensor for Autodart Match."""
    __name__ = "turn"

    configuration_url = AUTODART_MATCH_URL

    #entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL
        
    @property
    def native_value(self) -> str | None:
        """Return the state of the match."""
        _LOGGER.warning(f'native_value {self.coordinator.data} {self.coordinator.data} ')
        if not self.coordinator.data :
            return None
        else:
            return self.coordinator.data.turn_score
    
    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data :
            return {
                "bust": self.coordinator.data.turn_busted,
                "player": self.coordinator.data.player,
            }
        return {}

class MatchSensor(AutoDartChildEntity,SensorEntity):
    """Sensor for Autodart Match."""
    __name__ = "match"

    ### Entities properties ###
    device_class = SensorDeviceClass.ENUM
    options = [
        MATCH_WAITING,
        MATCH_STARTED,
        MATCH_STOPPED
    ]

    #entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL
        
    @property
    def native_value(self) -> str | None:
        """Return the state of the match."""
        if not self.board_coordinator.data.match_id :
            if self.board_coordinator.connected :
                return MATCH_WAITING
            else :
                return None
        elif self.coordinator.data :
            if self.coordinator.data.finished :
                return MATCH_STOPPED
            else:
                return MATCH_STARTED

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data :
            return {
                "leg": self.coordinator.data.leg,
                "set": self.coordinator.data.set,
                "round": self.coordinator.data.round,
                "variant": self.coordinator.data.variant,
                "settings": self.coordinator.data.settings,
            }