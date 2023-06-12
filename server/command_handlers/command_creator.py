from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass
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


@dataclass(slots=True)
class CommandCreator(ABC):
    """Abstract class for a server command creator."""

    _: KW_ONLY

    logger: Logger = LOGGER
    """logger (Logger, optional): Logger to be used during message creation.
    Defaults to LOGGER - sublogger of base package logger."""

    @overload
    @abstractmethod
    def create_message(self, cmd: Literal[ServerCommand.SERVER_CONFIRMATION], confirmation_number: int) -> bytes:
        """Creates a message of server confirmation from given confirmaton number.

        Args:
            cmd (Literal[ServerCommand.SERVER_CONFIRMATION]):
            confirmation_number (int): Confirmation number of the authentication. For more info see readme.

        Returns:
            bytes: Created encoded message.
        """
        ...

    @overload
    @abstractmethod
    def create_message(self, cmd: ServerCommandWithoutArgument) -> bytes:
        """Creates a message of server command, which does not require any arguments.

        Args:
            cmd (ServerCommandWithoutArgument): Type of command without arguments.

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
