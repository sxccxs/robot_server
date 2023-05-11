from abc import ABC, abstractmethod
from logging import Logger
from typing import Literal, NotRequired, TypedDict, overload

from common.commands import ServerCommand
from common.config import ENCODING
from server.command_handlers.types import ServerCommandWithoutArgument

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("creator")


class CommandCreatorKwargs(TypedDict):
    logger: NotRequired[Logger]


class CommandCreator(ABC):
    def __init__(self, *, logger: Logger = LOGGER) -> None:
        self.logger = logger

    @overload
    @abstractmethod
    def create_message(self, cmd: Literal[ServerCommand.SERVER_CONFIRMATION], confirmation_number: int) -> bytes:
        ...

    @overload
    @abstractmethod
    def create_message(self, cmd: ServerCommandWithoutArgument) -> bytes:
        ...

    @abstractmethod
    def create_message(self, cmd: ServerCommand, confirmation_number: int | None = None) -> bytes:
        ...


class DefaultCommandCreator(CommandCreator):
    def create_message(self, cmd: ServerCommand, confirmation_number: int | None = None) -> bytes:
        match cmd:
            case ServerCommand.SERVER_CONFIRMATION:
                self.logger.debug(f"Created {cmd.name} cmd with {confirmation_number=}")
                cmd_text = str(confirmation_number)
            case _:
                self.logger.debug(f"Created {cmd.name} cmd")
                cmd_text = cmd.value
        return cmd_text.encode(ENCODING)
