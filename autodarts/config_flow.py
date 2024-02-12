"""Config flow for autodarts integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

from autodarts import AutoDartSession , CloudBoard

from .const import (
    DOMAIN,
    AUTODART_CLIENT_ID,
    AUTODART_REALM_NAME,
    AUTODART_CLIENT_SECRET,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)

async def async_validate_input(email:str, password:str) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    session = AutoDartSession(
        email=email,
        password=password,
        client_id=AUTODART_CLIENT_ID,
        realm_name=AUTODART_REALM_NAME,
        client_secret_key=AUTODART_CLIENT_SECRET,
    )

    if not await session.is_authenticated():
        raise InvalidAuth
        
    # Return info that you want to store in the config entry.
    return session


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for autodarts."""

    VERSION = 1

    session = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self.session = await async_validate_input(user_input["email"], user_input["password"])
                self.data = user_input
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            #except Exception:  # pylint: disable=broad-except
            #    _LOGGER.exception("Unexpected exception")
            #    errors["base"] = "unknown"
            else:
                return await self.async_step_board()
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
    
    async def async_step_board(
        self, user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self.async_set_unique_id(user_input["board_id"])
                self._abort_if_unique_id_configured()
                self.data.update(user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=self.boards[user_input['board_id']], data=self.data)
        
        #self.boards = {}
        #async for cloud_board in CloudBoard.factory(self.session) :
        #    self.boards[cloud_board.id] = f"{cloud_board.name} ({cloud_board.id})"     
        #_LOGGER.error(f"Unexpected exception  {self.boards}")
        self.boards = {cloud_board.id: f"{cloud_board.name} ({cloud_board.id})" async for cloud_board in CloudBoard.factory(self.session)}

        step_board_data_schema = vol.Schema(
            {
                vol.Required("board_id"): vol.In( self.boards ),
            }
        )
        
        return self.async_show_form(
            step_id="board", data_schema=step_board_data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
