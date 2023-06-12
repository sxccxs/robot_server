from abc import ABC, abstractmethod
from asyncio import StreamWriter
from dataclasses import KW_ONLY, dataclass
from logging import Logger
from typing import Required, TypedDict

from typing_extensions import override

from common.config import CMD_POSTFIX_B
from server.command_handlers.command_creator import CommandCreator

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("write_handler")


class WriteHandlerKwargs(TypedDict, total=False):
    """Key-word arguments dict for a WriteHandler."""

    writer: Required[StreamWriter]
    creator: CommandCreator
    logger: Logger


@dataclass
class WriteHandler(ABC):
    """Abstract class for a socket writting handler."""

    writer: StreamWriter
    """writer (StreamWriter): Socket stream writer."""

    creator: CommandCreator
    """creator (CommandCreator): Command creation handler."""

    _: KW_ONLY

    logger: Logger = LOGGER
    """logger (Logger, optional): Defaults to subloger of base logger for a package."""

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """Writes provided data to the socket.

        Args:
            data (bytes): Data to write.
        """
        pass

    async def close(self) -> None:
        """Closes connection with socket."""
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except ConnectionResetError:
            self.logger.debug("Connection was closed by client")


class DefaultWriteHandler(WriteHandler):
    """Default implementation of socket writing handler."""

    @override
    async def write(self, data: bytes) -> None:
        self.logger.debug(f"Prepared data: {data}")

        self.writer.write(data)
        self.writer.write(CMD_POSTFIX_B)
        await self.writer.drain()

        self.logger.debug(f"Sended message: {data + CMD_POSTFIX_B}")
