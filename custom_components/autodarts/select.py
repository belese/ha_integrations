from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import AUTODART_MATCH_URL, DOMAIN
from .entity import AutoDartChildEntity

_LOGGER = logging.getLogger(__name__)

COMMON_DARTS = ["Miss"]
BULL_DARTS = ["25", "Bull"]
CRICKET_ALLOWED_DARTS = (
    COMMON_DARTS
    + [f"{letter}{number}" for number in range(15, 21) for letter in ["S", "D", "T"]]
    + BULL_DARTS
)
X01_ALLOWED_DARTS = (
    COMMON_DARTS
    + [f"{letter}{number}" for number in range(1, 21) for letter in ["S", "D", "T"]]
    + BULL_DARTS
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    match_coordinator = hass.data[DOMAIN][entry.entry_id]["match_coordinator"]
    darts_select = [DartSelect(match_coordinator, idx) for idx in range(3)]

    async_add_entities(darts_select)


async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    pass


def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]


class DartSelect(AutoDartChildEntity, SelectEntity):
    """Sensor for Autodart Match."""

    __name__ = "dart"

    # entity_description = "Autodarts' match"
    configuration_url = AUTODART_MATCH_URL

    @property
    def turn(self):
        if self.coordinator.data.turns:
            return self.coordinator.data.turns[-1]

    @property
    def throw(self):
        if self.coordinator.data:
            if turn := self.turn:
                # No turn yet
                try:
                    return turn["throws"][self.idx]
                except IndexError:
                    # Dart not yes launched
                    pass

    @property
    def checkout_guide(self):
        if self.coordinator.data:
            if checkout := self.coordinator.data.state.get("checkoutGuide"):
                try:
                    return checkout[self.idx]["name"]
                except IndexError:
                    pass

    @property
    def current_option(self) -> str | None:
        """Return the state of the match."""
        if throw := self.throw:
            name = throw["segment"]["name"]
            if name[0] == "M":  # we don't want MXX as it add a lot options for nothing
                return "Miss"
            else:
                return name
        if self.coordinator.data:
            return ""
        else:
            return None

    @property
    def extra_state_attributes(self) -> dict | None:
        attributes = {"checkout_guide": self.checkout_guide}
        if throw := self.throw:
            attributes.update(
                {
                    "segment": throw["segment"],
                    "coords": throw.get("coords"),
                    "marks": throw["marks"],
                    "entry": throw["entry"],
                }
            )
        return attributes

    @property
    def options(self):
        options = []
        option = self.current_option
        if option is not None:
            options.append(option)

        if not self.coordinator.data:
            return options

        actual_throw = len(self.turn["throws"])
        if (self.idx <= actual_throw and not self.coordinator.data.finished) or (
            self.idx < actual_throw and self.coordinator.data.finished
        ):
            # we can change only an already play dart or next one (if match is not finished)
            if self.coordinator.data.variant == "Cricket":
                return unique(CRICKET_ALLOWED_DARTS + options)
            else:
                return unique(X01_ALLOWED_DARTS + options)

        return options

    async def async_select_option(self, option: str) -> None:
        """Change the dart value."""
        if option == "":
            return
        throw_id = self.idx if self.throw else None
        await self.coordinator.data.async_throw(
            self.get_segment_from_name(option), throw_id=throw_id
        )

    def get_segment_from_name(self, name):
        if name == "Miss":
            number = 0
            bed = "Outside"
            multiplier = 0
        elif name == "Bull":
            number = 25
            bed = "Double"
            multiplier = 2
        elif name == "25":
            number = 25
            bed = "Double"
            multiplier = 1
        else:
            status = name[0]
            if status == "M":
                name = "Miss"  # we don't want MXX as it add a lot options for nothing
                bed = "Outside"
                multiplier = 0
            elif status == "S":
                bed = "Single"
                multiplier = 1
            elif status == "D":
                bed = "Double"
                multiplier = 2
            elif status == "T":
                bed = "Triple"
                multiplier = 3
            number = int(name[1:])

        return {"name": name, "number": number, "bed": bed, "multiplier": multiplier}
