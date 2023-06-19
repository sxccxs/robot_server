from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger
from typing import Literal, NotRequired, TypedDict

from typing_extensions import override

from common.commands import ClientCommand
from common.config import CMD_POSTFIX_B, ENCODING
from common.payloads import Coords
from common.result import Err, Ok
from server.command_handlers.reg_checks import is_int, matches_client_okay
from server.command_handlers.types import NoneValueCommands, NumberCommands, StringCommands
from server.exceptions import CommandNumberFormatError, CommandSyntaxError
from server.server_result import NoneServerResult, ServerResult

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("matcher")


class CommandMatcherKwargs(TypedDict):
    """Key-word arguments dict for a CommandMatcher."""

    logger: NotRequired[Logger]


class CommandMatcher(ABC):
    """Abstract class for a server command matcher."""

    __slots__ = ("_logger",)

    def __init__(self, *, logger: Logger = LOGGER) -> None:
        """
        Args:
            logger: (optional) Keyword parameter. Defaults to sublogger of base package logger.
        """
        self._logger = logger

    @abstractmethod
    def match_str(self, cmd: StringCommands, data: bytes) -> ServerResult[str]:
        """Check if given data matches given command type.

        Args:
            cmd: Type of string-value command.
            data: Data to check.

        Returns:
            ServerResult[str]: Ok(str_value) if matched, else Err(CommandSyntaxError).
        """
        ...

    @abstractmethod
    def match_num(self, cmd: NumberCommands, data: bytes) -> ServerResult[int]:
        """Check if given data matches given command type.

        Args:
            cmd: Type of number-value command.
            data: Data to check.

        Returns:
            ServerResult[int]: Ok(num_value) if matched,
            else Err(CommandNumberFormatError) if data wasa numeric value but of wrong format,
            else Err(CommandSyntaxError).
        """
        ...

    @abstractmethod
    def match_ok(self, cmd: Literal[ClientCommand.CLIENT_OK], data: bytes) -> ServerResult[Coords]:
        """Check if given data matches given command type.

        Args:
            cmd: ClientCommand.CLIENT_OK
            data: Data to check.

        Returns:
            ServerResult[Coords]: Ok(coords) if matched, else Err(CommandSyntaxError).
        """
        ...

    @abstractmethod
    def match_none(self, cmd: NoneValueCommands, data: bytes) -> NoneServerResult:
        """Check if given data matches given command type.

        Args:
            cmd: Type of none-value command.
            data: Data to check.

        Returns:
            NoneServerResult: Ok(None) if matched, else Err(CommandSyntaxError).
        """
        ...

    def _decode_data(self, data: bytes) -> ServerResult[str]:
        if not data.endswith(CMD_POSTFIX_B):
            return Err(CommandSyntaxError("Invalid command format"))

        data = data.rstrip(CMD_POSTFIX_B)
        return Ok(data.decode(ENCODING))


class DefaultCommandMatcher(CommandMatcher):
    """Default realization of command matcher."""

    @override
    def match_str(self, cmd: StringCommands, data: bytes) -> ServerResult[str]:
        match self._decode_data(data):
            case Err() as err:
                return err
            case Ok(value):
                decoded_data = value

        match cmd:
            case ClientCommand.CLIENT_USERNAME:
                if 0 < len(decoded_data) <= ClientCommand.CLIENT_USERNAME.max_len:
                    return Ok(decoded_data)
                return Err(CommandSyntaxError(f'Invalid Username format: "{decoded_data}"'))
            case ClientCommand.CLIENT_MESSAGE:
                if 0 < len(decoded_data) <= ClientCommand.CLIENT_MESSAGE.max_len:
                    return Ok(decoded_data)
                return Err(CommandSyntaxError("Invalid client message format"))

    @override
    def match_num(self, cmd: NumberCommands, data: bytes) -> ServerResult[int]:
        match self._decode_data(data):
            case Err() as err:
                return err
            case Ok(value):
                decoded_data = value

        match cmd:
            case ClientCommand.CLIENT_CONFIRMATION:
                if not (0 < len(decoded_data) <= ClientCommand.CLIENT_CONFIRMATION.max_len) or not is_int(
                    decoded_data
                ):
                    return Err(CommandSyntaxError("Not numberic data given for confirmation number"))

                if 0 <= (num := int(decoded_data)) <= 0xFFFF:
                    return Ok(num)
                return Err(
                    CommandNumberFormatError("Confirmation number is not a valid positive 16-bit integer number")
                )

            case ClientCommand.CLIENT_KEY_ID:
                if not (0 < len(decoded_data) <= ClientCommand.CLIENT_KEY_ID.max_len) or not is_int(decoded_data):
                    return Err(CommandSyntaxError("Not numberic data given for key id"))

                if 0 <= (key := int(decoded_data)) <= 999:
                    return Ok(key)
                return Err(
                    CommandNumberFormatError("Key id is not a valid postive integer number in range [0, 999]")
                )

    @override
    def match_ok(self, cmd: Literal[ClientCommand.CLIENT_OK], data: bytes) -> ServerResult[Coords]:
        match self._decode_data(data):
            case Err() as err:
                return err
            case Ok(value):
                decoded_data = value

        if 0 < len(decoded_data) <= ClientCommand.CLIENT_OK.max_len and matches_client_okay(decoded_data):
            _, x, y = decoded_data.split(" ")
            return Ok(Coords(int(x), int(y)))
        return Err(CommandSyntaxError("Invalid OK message"))

    @override
    def match_none(self, cmd: NoneValueCommands, data: bytes) -> NoneServerResult:
        match self._decode_data(data):
            case Err() as err:
                return err
            case Ok(value):
                decoded_data = value

        match cmd:
            case ClientCommand.CLIENT_RECHARGING:
                if decoded_data == ClientCommand.CLIENT_RECHARGING.cmd_text:
                    return Ok(None)
                return Err(CommandSyntaxError("Invalid recharging message"))

            case ClientCommand.CLIENT_FULL_POWER:
                if decoded_data == ClientCommand.CLIENT_FULL_POWER.cmd_text:
                    return Ok(None)
                return Err(CommandSyntaxError("Invalid full power message"))
