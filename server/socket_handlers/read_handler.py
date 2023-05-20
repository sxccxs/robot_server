import asyncio
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import KW_ONLY, dataclass, field
from io import BytesIO
from logging import Logger
from typing import Required, TypedDict

from common.commands import ClientCommand
from common.config import CMD_POSTFIX_B, TIMEOUT, TIMEOUT_RECHARGING
from common.result import Err, Ok
from server.command_handlers.command_matcher import CommandMatcher
from server.exceptions import LogicError, ServerTimeoutError
from server.server_result import ServerResult
from server.socket_handlers.types import SeparatorChecker

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


class Split2BytesReadHandler(ReadHandler):
    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        sep = CMD_POSTFIX_B
        self.logger.debug("started read")
        if len(sep) != 2:
            raise ValueError("2 bytes reader takes only 2 bytes long message separator")

        msg = self._get_from_queue(sep)  # get previously received messages if any
        if msg[-2:] == sep:  # if received message was already fully read
            return Ok(msg)

        msg_stream = BytesIO()
        msg_stream.write(msg)

        self.logger.debug(f"started with data: {msg}")
        length = len(msg)  # length of read data

        separator_spliter = self._get_separator_spliter(sep, bool(msg and msg[-1] == sep[0]))

        while length < max_len:
            self.logger.debug("try read")
            try:
                chunk = await asyncio.wait_for(self.reader.read(self._chunk_size), timeout=timeout)
            except (TimeoutError, ConnectionResetError):
                return Err(ServerTimeoutError(f"Timeout exceeded: {timeout=}"))
            if chunk == b"":
                return Err(ServerTimeoutError(f"Connection is probably closed by the other side"))

            self.logger.debug(f"recieved data: {chunk}")

            part_of_current, part_of_next = separator_spliter(chunk)
            length += len(part_of_current)
            msg_stream.write(part_of_current)

            if part_of_next:
                self._msg_queue.append(part_of_next)

            if part_of_next is not None:
                break

        self.logger.debug(f"return value: {msg_stream.getvalue()}")
        return Ok(msg_stream.getvalue()[:max_len])

    def _split_by_separator(self, chunk: bytes, sep: bytes) -> tuple[bytes, bytes]:
        split_index = chunk.index(sep) + len(sep)
        return chunk[:split_index], chunk[split_index:]

    def _get_from_queue(self, sep: bytes) -> bytes:
        """Gets message from queue until separator or until the queue ends"""
        msg_stream = BytesIO()
        separator_spliter = self._get_separator_spliter(sep)

        while self._msg_queue:
            next_chunk = self._msg_queue[0]
            part_of_current, part_of_next = separator_spliter(next_chunk)

            msg_stream.write(part_of_current)

            if part_of_next is not None:
                if part_of_next:  # separator end is in between of the chunk
                    self._msg_queue[0] = part_of_next
                else:  # separator end in the end of the chunk
                    self._msg_queue.popleft()
                return msg_stream.getvalue()
            else:
                self._msg_queue.popleft()

        return msg_stream.getvalue()

    def _get_separator_spliter(self, sep: bytes, found_half: bool = False) -> SeparatorChecker:
        """
        Returns a callable which takes chunk and splits it by separator.
        It returns tuple[bytes, bytes | None].
        Second element is None if current message didn't end.
        """

        def _inner(chunk: bytes) -> tuple[bytes, bytes | None]:
            nonlocal found_half
            if found_half and chunk and chunk[0] == sep[1]:  # if sep was on the start and the end of 2 chunks
                return chunk[0:1], chunk[1:]  # [0:1] to get first byte as bytes instead of int
            elif sep in chunk:
                return self._split_by_separator(chunk, sep)
            elif chunk and chunk[-1] == sep[0]:  # if chunk ends with first symbol of sep
                found_half = True
            else:
                found_half = False

            return chunk, None

        return _inner


@dataclass(slots=True)
class Recharging2BytesReadHandler(ReadHandler):
    _subreader: Split2BytesReadHandler = field(init=False)

    def __post_init__(self) -> None:
        self._subreader = Split2BytesReadHandler(
            self.reader, self.matcher, logger=self.logger, _chunk_size=self._chunk_size
        )

    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        read_length = max(max_len, ClientCommand.CLIENT_RECHARGING.max_len_postfix)  # for correct recharging read
        match await self._subreader.read(read_length, timeout=timeout):
            case Err() as err:
                return err
            case Ok(data):
                pass
        match self.matcher.match(ClientCommand.CLIENT_RECHARGING, data):
            case Err():
                match self.matcher.match(ClientCommand.CLIENT_FULL_POWER, data):
                    case Ok():
                        return Err(LogicError(f"Unexpected command: {ClientCommand.CLIENT_FULL_POWER.name}"))
                    case Err():
                        return Ok(data[:max_len])
            case Ok():
                self.logger.info("Recharging begin")
                return await self._handle_recharging(max_len, timeout)

    async def _handle_recharging(self, max_len: int, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        match await self._subreader.read(
            ClientCommand.CLIENT_FULL_POWER.max_len_postfix, timeout=TIMEOUT_RECHARGING
        ):
            case Err() as err:
                self.logger.debug(f"Error while recharging: {err=}")
                return err
            case Ok(data):
                pass
        match self.matcher.match(ClientCommand.CLIENT_FULL_POWER, data):
            case Err(err):
                return Err(
                    LogicError(
                        f"Unexpected command. Expected: {ClientCommand.CLIENT_FULL_POWER.name}. Got data: {data}"
                    )
                )
            case Ok():
                self.logger.info("Recharging done")
        match await self._subreader.read(max_len, timeout=timeout):
            case Err() as err:
                return err
            case Ok(data):
                return Ok(data)
