import asyncio
from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass
from logging import Logger
from typing import Required, TypedDict

from typing_extensions import override

from common.config import CMD_POSTFIX_B
from server.command_handlers.command_creator import CommandCreator

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("write_handler")


class WriteHandlerKwargs(TypedDict, total=False):
    writer: Required[asyncio.StreamWriter]
    creator: CommandCreator
    command_end: bytes
    logger: Logger


@dataclass
class WriteHandler(ABC):
    writer: asyncio.StreamWriter
    creator: CommandCreator
    command_end: bytes = CMD_POSTFIX_B
    _: KW_ONLY
    logger: Logger = LOGGER

    @abstractmethod
    async def write(self, data: bytes) -> None:
        pass

    async def close(self) -> None:
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except ConnectionResetError:
            self.logger.debug("Connection was closed by client")


class DefaultWriteHandler(WriteHandler):
    @override
    async def write(self, data: bytes) -> None:
        self.logger.debug(f"Recieved data: {data}")

        self.writer.write(data)
        self.writer.write(self.command_end)
        await self.writer.drain()

        self.logger.debug(f"Sended message: {data + self.command_end}")
