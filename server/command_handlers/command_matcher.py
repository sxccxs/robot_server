from abc import ABC, abstractmethod
from logging import Logger
from typing import Literal, NotRequired, TypedDict, overload

from typing_extensions import override

from common.commands import ClientCommand
from common.config import CMD_POSTFIX_B, ENCODING
from common.data_classes import Coords
from common.result import Err, Ok
from server.command_handlers.reg_checks import is_int, matches_client_okay
from server.command_handlers.types import NonValueCommands, NumberCommands, StringCommands
from server.exceptions import CommandNumberFormatError, CommandSyntaxError
from server.server_result import NoneServerResult, ServerResult

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("matcher")


class CommandMatcherKwargs(TypedDict):
    """Key-word arguments dict for a CommandMatcher."""

    logger: NotRequired[Logger]


class CommandMatcher(ABC):
    """Abstract class for a server command matcher."""

    def __init__(self, *, logger: Logger = LOGGER) -> None:
        """Initializes CommandMatcher.

        Args:
            logger (Logger, optional): Logger to be used during message matching. Defaults to LOGGER - base package logger.
        """
        self.logger = logger

    @overload
    @abstractmethod
    def match(self, cmd: StringCommands, data: bytes) -> ServerResult[str]:
        """Check if given data matches given command type.

        Args:
            cmd (StringCommands): Type of string-value command.
            data (bytes): Data to check.

        Returns:
            ServerResult[str]: Ok(str_value) if matched, else Err(CommandSyntaxError).
        """
        pass

    @overload
    @abstractmethod
    def match(self, cmd: NumberCommands, data: bytes) -> ServerResult[int]:
        """Check if given data matches given command type.

        Args:
            cmd (NumberCommands): Type of number-value command.
            data (bytes): Data to check.

        Returns:
            ServerResult[int]: Ok(num_value) if matched,
            else Err(CommandNumberFormatError) if data wasa numeric value but of wrong format,
            else Err(CommandSyntaxError).
        """
        pass

    @overload
    @abstractmethod
    def match(self, cmd: Literal[ClientCommand.CLIENT_OK], data: bytes) -> ServerResult[Coords]:
        """Check if given data matches given command type.

        Args:
            cmd (Literal[ClientCommand.CLIENT_OK]):
            data (bytes): Data to check.

        Returns:
            ServerResult[Coords]: Ok(coords) if matched, else Err(CommandSyntaxError).
        """
        pass

    @overload
    @abstractmethod
    def match(self, cmd: NonValueCommands, data: bytes) -> NoneServerResult:
        """Check if given data matches given command type.

        Args:
            cmd (NonValueCommands): Type of non-value command.
            data (bytes): Data to check.

        Returns:
            NoneServerResult: Ok(None) if matched, else Err(CommandSyntaxError).
        """
        pass

    @abstractmethod
    def match(self, cmd: ClientCommand, data: bytes) -> ServerResult[str | int | Coords | None]:  # type: ignore
        pass


class DefaultCommandMatcher(CommandMatcher):
    """Default realization of command matcher."""

    @override
    def match(self, cmd: ClientCommand, data: bytes) -> ServerResult[str | int | Coords | None]:
        self.logger.debug(f"Got data in Matcher {data=}")

        if not data.endswith(CMD_POSTFIX_B):
            return Err(CommandSyntaxError("Invalid command format"))

        data = data.rstrip(CMD_POSTFIX_B)

        self.logger.debug(f"Try match {data} as {cmd.name}")

        decoded_data = data.decode(ENCODING)

        match cmd:
            case ClientCommand.CLIENT_USERNAME:
                if 0 < len(decoded_data) <= ClientCommand.CLIENT_USERNAME.max_len:
                    return Ok(decoded_data)
                return Err(CommandSyntaxError(f'Invalid Username format: "{decoded_data}"'))

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

            case ClientCommand.CLIENT_MESSAGE:
                if 0 < len(decoded_data) <= ClientCommand.CLIENT_MESSAGE.max_len:
                    return Ok(decoded_data)
                return Err(CommandSyntaxError("Invalid client message format"))

            case ClientCommand.CLIENT_OK:
                if 0 < len(decoded_data) <= ClientCommand.CLIENT_OK.max_len and matches_client_okay(decoded_data):
                    _, x, y = decoded_data.split(" ")
                    return Ok(Coords(int(x), int(y)))
                return Err(CommandSyntaxError("Invalid OK message"))

            case ClientCommand.CLIENT_RECHARGING:
                if decoded_data == ClientCommand.CLIENT_RECHARGING.cmd_text:
                    return Ok(None)
                return Err(CommandSyntaxError("Invalid recharging message"))

            case ClientCommand.CLIENT_FULL_POWER:
                if decoded_data == ClientCommand.CLIENT_FULL_POWER.cmd_text:
                    return Ok(None)
                return Err(CommandSyntaxError("Invalid full power message"))
