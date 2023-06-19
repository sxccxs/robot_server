from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger
from typing import Literal, NotRequired, TypedDict

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

    __slots__ = ("_logger",)

    def __init__(self, *, logger: Logger = LOGGER) -> None:
        """
        Args:
            logger: (optional) Keyword parameter. Defaults to sublogger of base package logger.
        """
        self._logger = logger

    @abstractmethod
    def create_message_int(
        self, cmd: Literal[ServerCommand.SERVER_CONFIRMATION], confirmation_number: int
    ) -> bytes:
        """Creates a message of server confirmation from given confirmaton number.

        Args:
            cmd: ServerCommand.SERVER_CONFIRMATION
            confirmation_number: Confirmation number of the authentication. For more info see readme.

        Returns:
            bytes: Created encoded message.
        """
        ...

    @abstractmethod
    def create_message(self, cmd: ServerCommandWithoutArgument) -> bytes:
        """Creates a message of server command, which does not require any arguments.

        Args:
            cmd: Type of command without arguments.

        Returns:
            bytes: Created encoded message.
        """
        ...


class DefaultCommandCreator(CommandCreator):
    """Default realization of command creator."""

    @override
    def create_message_int(
        self, cmd: Literal[ServerCommand.SERVER_CONFIRMATION], confirmation_number: int
    ) -> bytes:
        self._logger.debug(f"Created {cmd.name} cmd with {confirmation_number=}")
        cmd_text = str(confirmation_number)
        return cmd_text.encode(ENCODING)

    @override
    def create_message(self, cmd: ServerCommandWithoutArgument) -> bytes:
        self._logger.debug(f"Created {cmd.name} cmd")
        cmd_text = cmd.cmd_text
        return cmd_text.encode(ENCODING)
