from abc import ABC, abstractmethod
from asyncio import StreamWriter
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


class WriteHandler(ABC):
    """Abstract class for a socket writting handler."""

    def __init__(self, *, writer: StreamWriter, creator: CommandCreator, logger: Logger = LOGGER) -> None:
        """All parameters are keyword only.

        Args:
            writer: Socket stram writer.
            creator: Command creation handler.
            logger: Defaults to sublogger of base package logger.
        """
        self._writer = writer
        self._creator = creator
        self._logger = logger

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
            self._writer.close()
            await self._writer.wait_closed()
        except ConnectionResetError:
            self._logger.debug("Connection was closed by client")


class DefaultWriteHandler(WriteHandler):
    """Default implementation of socket writing handler."""

    @override
    async def write(self, data: bytes) -> None:
        self._logger.debug(f"Prepared data: {data}")

        self._writer.write(data)
        self._writer.write(CMD_POSTFIX_B)
        await self._writer.drain()

        self._logger.debug(f"Sended message: {data + CMD_POSTFIX_B}")
