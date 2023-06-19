from typing import Literal

from common.commands import ClientCommand, ServerCommand

ServerCommandWithoutArgument = Literal[
    ServerCommand.SERVER_MOVE,
    ServerCommand.SERVER_TURN_LEFT,
    ServerCommand.SERVER_TURN_RIGHT,
    ServerCommand.SERVER_PICK_UP,
    ServerCommand.SERVER_LOGOUT,
    ServerCommand.SERVER_KEY_REQUEST,
    ServerCommand.SERVER_OK,
    ServerCommand.SERVER_LOGIN_FAILED,
    ServerCommand.SERVER_SYNTAX_ERROR,
    ServerCommand.SERVER_LOGIC_ERROR,
    ServerCommand.SERVER_KEY_OUT_OF_RANGE_ERROR,
]
"""Type reprezenting all server commands with no arguments."""

StringCommands = Literal[ClientCommand.CLIENT_USERNAME, ClientCommand.CLIENT_MESSAGE]
"""Type reprezenting all client commands with string value."""

NumberCommands = Literal[ClientCommand.CLIENT_CONFIRMATION, ClientCommand.CLIENT_KEY_ID]
"""Type reprezenting all client commands with numeric value."""

NoneValueCommands = Literal[ClientCommand.CLIENT_RECHARGING, ClientCommand.CLIENT_FULL_POWER]
"""Type reprezenting all client commands with no value."""
