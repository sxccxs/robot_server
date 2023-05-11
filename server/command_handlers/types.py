from typing import Literal

from common.commands import ServerCommand

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

