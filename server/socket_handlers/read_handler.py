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
from server.exceptions import CommandSyntaxError, LogicError, ServerTimeoutError
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


class AnyLengthSepReadHandler(ReadHandler):

    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        self.logger.debug("started read")

        msg = self._get_from_queue()
        if msg.endswith(CMD_POSTFIX_B):
            return Ok(msg)

        msg_stream = BytesIO()
        msg_stream.write(msg)
        self.logger.debug(f"started with data: {msg}")

        length = len(msg)
        separator_spliter = self.SeparatorSplitter(msg)

        while length < max_len:
            self.logger.debug("try read")
            match await self._read_chunk(timeout):
                case Err() as err:
                    return err
                case Ok(value):
                    chunk = value

            self.logger.debug(f"recieved data: {chunk}")

            part_of_current, part_of_next = separator_spliter.check(chunk)
            print(part_of_current, part_of_next)
            length += len(part_of_current)
            msg_stream.write(part_of_current)

            if part_of_next:
                self._msg_queue.append(part_of_next)

            if part_of_next is not None:
                break

        self.logger.debug(f"return value: {msg_stream.getvalue()}")
        if not (res := msg_stream.getvalue()[:max_len]).endswith(CMD_POSTFIX_B):
            return Err(CommandSyntaxError("Missing message separator."))
        return Ok(res)

    async def _read_chunk(self, timeout: int) -> ServerResult[bytes]:
        try:
            chunk = await asyncio.wait_for(self.reader.read(self._chunk_size), timeout=timeout)
        except (TimeoutError, ConnectionResetError):
            return Err(ServerTimeoutError(f"Timeout exceeded: {timeout=}"))

        if chunk == b"":
            return Err(ServerTimeoutError(f"Connection is probably closed by the other side"))

        return Ok(chunk)

    def _get_from_queue(self) -> bytes:
        msg_stream = BytesIO()
        separator_spliter = self.SeparatorSplitter()

        while self._msg_queue:
            next_chunk = self._msg_queue[0]
            part_of_current, part_of_next = separator_spliter.check(next_chunk)

            msg_stream.write(part_of_current)

            if part_of_next is not None:
                if part_of_next:  # separator end is in between of the chunks
                    self._msg_queue[0] = part_of_next
                else:  # separator end in the end of the chunk
                    self._msg_queue.popleft()
                return msg_stream.getvalue()
            else:
                self._msg_queue.popleft()

        return msg_stream.getvalue()

    @dataclass(init=False, slots=True)
    class SeparatorSplitter:
        _matched_bytes: list[bool]

        def __init__(self, begging_value: bytes | None = None):

            self._matched_bytes: list[bool] = self._create_matched_empty()

            if begging_value:
                for i in range(len(CMD_POSTFIX_B), 0, -1):
                    if begging_value[-i:] == CMD_POSTFIX_B[:i]:
                        self._matched_bytes[:i] = [True] * i
                        break

        def _create_matched_empty(self) -> list[bool]:
            return [False] * len(CMD_POSTFIX_B)

        def check(self, chunk: bytes) -> tuple[bytes, bytes | None]:
            ind = self._matched_bytes.index(False)

            chunk_ind = 0
            while chunk_ind < len(chunk):
                b = chunk[chunk_ind]

                if ind != 0 and b != CMD_POSTFIX_B[ind]:
                    self._matched_bytes = self._create_matched_empty()
                    ind = 0
                    continue

                chunk_ind += 1

                if b != CMD_POSTFIX_B[ind]:
                    continue

                self._matched_bytes[ind] = True
                ind += 1
                if ind == len(self._matched_bytes):
                    break

            if not self._matched_bytes[-1]:
                return chunk, None

            self._matched_bytes = self._create_matched_empty()
            return chunk[:chunk_ind], chunk[chunk_ind:]


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
