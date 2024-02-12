"""Entity for Surepetcare."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

class AutoDartEntity(CoordinatorEntity):
    def __init__(self, coordinator, idx=None):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.coordinator = coordinator
        self.idx = idx
        idx_txt = ""
        idx_id = ""
        if idx is not None :
            idx_txt = f' {idx+1}'
            idx_id = f'_{idx}'
        self._attr_name = f"Autodarts {self.__name__.title()}{idx_txt} {self.coordinator.item.name}"
        self._attr_unique_id = f"{self.coordinator.item.id}_{self.__name__}{idx_id}"
    
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
        super().__init__(coordinator, context=idx)
        self.coordinator = coordinator
        self.idx = idx
        self.board_coordinator = coordinator.board_coordinator 
        idx_txt = ""
        idx_id = ""
        if idx is not None :
            idx_txt = f' {idx+1}'
            idx_id = f'_{idx}'
        self._attr_name = f"Autodarts {self.__name__.title()}{idx_txt} {self.board_coordinator.item.name}"
        self._attr_unique_id = f"{self.board_coordinator.item.id}_{self.__name__}{idx_id}"        

    
    
