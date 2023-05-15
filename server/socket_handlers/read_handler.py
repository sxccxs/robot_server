import asyncio
from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from logging import Logger
from typing import Required, TypedDict

from common.config import TIMEOUT
from server.command_handlers.command_matcher import CommandMatcher
from server.server_result import ServerResult

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("read_handler")


class ReadHandlerKwargs(TypedDict, total=False):
    reader: Required[asyncio.StreamReader]
    matcher: CommandMatcher
    logger: Logger
    _chunk_size: int


@dataclass
class ReadHandler(ABC):
    reader: asyncio.StreamReader
    matcher: CommandMatcher
    _: KW_ONLY
    logger: Logger = LOGGER
    _chunk_size: int = 8
    _msg_queue: deque[bytes] = field(init=False, default_factory=deque)

    @abstractmethod
    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        pass
