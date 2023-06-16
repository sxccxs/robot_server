from abc import ABC
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
    logger: NotRequired[Logger]


class BaseService(ABC):
    """Base class for all services."""

    __slots__ = ("reader", "writer", "matcher", "creator", "logger")

    def __init__(
        self,
        *,
        reader: ReadHandler,
        writer: WriteHandler,
        matcher: CommandMatcher,
        creator: CommandCreator,
        logger: Logger | None = None,
    ) -> None:
        """All parameters are keyword only.

        Args:
            reader: Handler of socket reading.
            writer: Handler of socket writing.
            matcher: Commands matching handler.
            creator: Commands creation handler.
            logger_: (optional) Defaults to None. If value is None, sublogger of base package logger will be used.
        """
        self.reader = reader
        self.writer = writer
        self.matcher = matcher
        self.creator = creator
        self.logger = logger if logger is not None else LOGGER_BASE.getChild(self.__class__.__name__.lower())
