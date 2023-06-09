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
    reader: ReadHandler
    writer: WriteHandler
    matcher: CommandMatcher
    creator: CommandCreator
    logger_: NotRequired[Logger]


@dataclass(slots=True)
class BaseService(ABC):
    reader: ReadHandler
    writer: WriteHandler
    matcher: CommandMatcher
    creator: CommandCreator
    logger_: InitVar[Logger | None]
    logger: Logger = field(init=False)

    def __post_init__(self, logger_: Logger | None):
        self.logger = logger_ if logger_ is not None else LOGGER_BASE.getChild(self.__class__.__name__)
