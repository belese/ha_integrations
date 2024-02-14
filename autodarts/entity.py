"""Entity for Surepetcare."""
from __future__ import annotations


from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .autodarts_dev import Match

class AutoDartEntity(CoordinatorEntity):
    def __init__(self, coordinator, idx=None):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.coordinator = coordinator
        self.idx = idx
        
    @property
    def name(self) :
        idx_txt = ""  if self.idx is None else f' {self.idx+1}'
        return f"Autodarts {self.__name__.title()}{idx_txt} {self.coordinator.item.name}"
    
    @property
    def unique_id(self) :
        idx_id = "" if self.idx is None else f'_{self.idx}'
        f"{self.coordinator.item.id}_{self.__name__}{idx_id}"
    

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.id)
            },
            name = f"Autodarts {self.coordinator.item.name}",
            manufacturer = "Autodarts.io",
            model = "Board Manager",
            sw_version = self.coordinator.item.version if self.coordinator.item else None,
            #via_device=(hue.DOMAIN, self.api.bridgeid),
        )
    
    
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()



class AutoDartChildEntity(AutoDartEntity):
    """An entity using CoordinatorEntity.
    """
    __name__ = ""

    def __init__(self, coordinator, idx=None):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, idx=idx)
        self.board_coordinator = coordinator.board_coordinator 
    
    @property
    def name(self) :
        idx_txt = ""  if self.idx is None else f' {self.idx+1}'
        return f"Autodarts {self.__name__.title()}{idx_txt} {self.board_coordinator.item.name}"
    
    @property
    def unique_id(self) :
        idx_id = "" if self.idx is None else f'_{self.idx}'
        return f"{self.board_coordinator.item.id}_{self.__name__}{idx_id}"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, f"match_{self.board_coordinator.id}")
            },
            name= f"Autodarts match {self.coordinator.item.name}",
            manufacturer="Autodarts.io",
            model="Board Match",
            via_device=(DOMAIN, self.board_coordinator.id),
        )
    