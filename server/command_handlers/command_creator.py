from abc import ABC, abstractmethod
from logging import Logger
from typing import Literal, NotRequired, TypedDict, overload

from typing_extensions import override

from common.commands import ServerCommand
from common.config import ENCODING
from server.command_handlers.types import ServerCommandWithoutArgument

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("creator")


class CommandCreatorKwargs(TypedDict):
    """Key-word arguments dict for a CommandCreator."""

    logger: NotRequired[Logger]


class CommandCreator(ABC):
    """Abstract class for a server command creator."""

    __slots__ = ("logger",)

    def __init__(self, *, logger: Logger = LOGGER) -> None:
        """
        Args:
            logger: (optional) Keyword parameter. Defaults to sublogger of base package logger.
        """
        self.logger = logger

    @overload
    @abstractmethod
    def create_message(self, cmd: Literal[ServerCommand.SERVER_CONFIRMATION], confirmation_number: int) -> bytes:
        """Creates a message of server confirmation from given confirmaton number.

        Args:
            cmd: ServerCommand.SERVER_CONFIRMATION
            confirmation_number: Confirmation number of the authentication. For more info see readme.

        Returns:
            bytes: Created encoded message.
        """
        ...

    @overload
    @abstractmethod
    def create_message(self, cmd: ServerCommandWithoutArgument) -> bytes:
        """Creates a message of server command, which does not require any arguments.

        Args:
            cmd: Type of command without arguments.

        Returns:
            bytes: Created encoded message.
        """
        ...

    @abstractmethod
    def create_message(self, cmd: ServerCommand, confirmation_number: int | None = None) -> bytes:
        ...


class DefaultCommandCreator(CommandCreator):
    """Default realization of command creator."""

    @override
    def create_message(self, cmd: ServerCommand, confirmation_number: int | None = None) -> bytes:
        match cmd:
            case ServerCommand.SERVER_CONFIRMATION:
                self.logger.debug(f"Created {cmd.name} cmd with {confirmation_number=}")
                cmd_text = str(confirmation_number)
            case _:
                self.logger.debug(f"Created {cmd.name} cmd")
                cmd_text = cmd.cmd_text
        return cmd_text.encode(ENCODING)
