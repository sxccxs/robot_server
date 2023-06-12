from abc import ABC
from dataclasses import InitVar, dataclass, field
from logging import Logger
from typing import NotRequired, TypedDict

from server.command_handlers.command_creator import CommandCreator
from server.command_handlers.command_matcher import CommandMatcher
from server.socket_handlers.read_handler import ReadHandler
from server.socket_handlers.write_handler import WriteHandler

from . import logger as LOGGER_BASE


class BaseServiceKwargs(TypedDict):
    """Key-word arguments dict base for any service."""

    reader: ReadHandler
    writer: WriteHandler
    matcher: CommandMatcher
    creator: CommandCreator
    logger_: NotRequired[Logger]


@dataclass(slots=True)
class BaseService(ABC):
    """Base class for all services."""

    reader: ReadHandler
    """reader (ReadHandler): Handler of socket reading."""

    writer: WriteHandler
    """writer (WriteHandler): Handler of socket writing."""

    matcher: CommandMatcher
    """matcher (CommandMatcher): Commands matching handler."""

    creator: CommandCreator
    """creator (CommandCreator): Commands creation handler."""

    logger_: InitVar[Logger | None]
    """logger_ (Logger | None, optional): Defaults to None.
    If value is None, subloger of base logger for package will be used."""

    logger: Logger = field(init=False)

    def __post_init__(self, logger_: Logger | None):
        """Initializes logger of base service after initialization process."""
        self.logger = logger_ if logger_ is not None else LOGGER_BASE.getChild(self.__class__.__name__)
