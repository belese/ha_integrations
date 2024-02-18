"""Example integration using DataUpdateCoordinator."""

import asyncio
import logging

from autodarts import CloudBoard, Match
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class AutoDartsBaseCoordinator(DataUpdateCoordinator):
    __child__ = None

    def __init__(self, hass, session):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=self.__class__.__name__.lower(),
        )

        self.session = session
        self.item = None
        self._unregister_cb = []
        self.is_waiting = asyncio.Event()

    @property
    def connected(self):
        return True if self.item and self.item.is_connected else False

    def connect(self):
        if self.item and not self.connected:
            self._unregister_cb.append(
                self.item.register_callback(self.on_state_updated)
            )
            self._unregister_cb.append(
                self.item.register_async_callback(
                    self.on_unexpected_close, event="error", topic="events"
                )
            )
            self._unregister_cb.append(
                self.item.register_async_callback(
                    self.on_unexpected_close, event="disconnected", topic="events"
                )
            )
            self.item.connect()

    def disconnect(self):
        if self.item and self.connected:
            while self._unregister_cb:
                cb = self._unregister_cb.pop()
                cb()
            self.item.disconnect()

    def load(self, item, forward_state=True):
        if self.item:
            self.unload()
        self.item = item
        if forward_state:
            self.async_set_updated_data(item)

    def unload(self):
        self.disconnect()
        self.item = None
        self.async_set_updated_data(None)

    async def async_refresh(self):
        if self.item:
            await self.item.async_load()
            self.async_set_updated_data(self.item)

    @callback
    def on_state_updated(self, msg):
        item = self.__child__(msg, self.session)
        self.async_set_updated_data(item)

    @callback
    def on_unexpected_close(self, msg):
        _LOGGER.warning(f"Unexpected web socket closure {msg}")
        # reconnect on error or disconnect from host
        self.item.connect()


class AutoDartsChilBaseCoordinator(AutoDartsBaseCoordinator):
    def __init__(self, hass, board_coordinator):
        super().__init__(hass, board_coordinator.item.session)
        self.board_coordinator = board_coordinator


class AutoDartsBoardCoordinator(AutoDartsBaseCoordinator):
    __child__ = CloudBoard

    def __init__(self, hass, session, id):
        self.id = id
        super().__init__(hass, session)

    def connect(self):
        super().connect()
        self.async_set_updated_data(self.item)

    def disconnect(self):
        super().disconnect()
        self.async_set_updated_data(self.item)

    async def _async_update_data(self):
        board = await self.__child__.from_id(self.session, self.id)
        self.load(board, False)
        super().connect()
        return self.item


class AutoDartsGenericMatchCoordinator(AutoDartsChilBaseCoordinator):
    __child__ = Match


class AutoDartsBoardMatchCoordinator(AutoDartsGenericMatchCoordinator):
    def wait(self):
        # A reset is done before match start(before a Turn exactly) ,
        # Use it as a trigger when not matchId is found
        # That reduce a lot polling api

        if self.is_waiting.is_set():
            return
        self.is_waiting.set()
        handler_cb = []

        @callback
        async def on_board_reset(msg):
            try:
                await self.board_coordinator.async_refresh()
                if match_id := self.board_coordinator.item.match_id:
                    if not self.item or (self.item and self.item.id != match_id):
                        match = await Match.from_id(self.session, match_id)
                        self.load(match)
                        while handler_cb:
                            handler = handler_cb.pop()
                            handler()
            finally:
                self.is_waiting.clear()

        handler_cb.append(
            self.board_coordinator.item.register_async_callback(
                on_board_reset, "Manual reset"
            )
        )

    async def async_refresh(self):
        if match_id := self.board_coordinator.item.match_id:
            if not self.item or (self.item and self.item.id != match_id):
                match = await Match.from_id(self.session, match_id)
                self.load(match, forward_state=False)
            else:
                await self.item.async_load()
        self.async_set_updated_data(self.item)

    def load(self, item, forward_state=True):
        async def async_on_match_ended(msg):
            await self.board_coordinator.async_refresh()
            self.unload()
            self.wait()

        super().load(item, forward_state)
        self._unregister_cb.append(
            self.item.register_async_callback(
                async_on_match_ended, event="delete", topic="events"
            )
        )
        self._unregister_cb.append(
            self.item.register_async_callback(
                async_on_match_ended, event="finish", topic="events"
            )
        )
        self.connect()

    async def _async_update_data(self):
        if not self.board_coordinator.item.match_id:
            self.wait()
        else:
            match = await Match.from_id(
                self.session, self.board_coordinator.item.match_id
            )
            self.load(match, False)
        return self.item
