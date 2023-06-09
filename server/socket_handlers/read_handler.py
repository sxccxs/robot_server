from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import StreamReader, wait_for
from collections import deque
from io import BytesIO
from logging import Logger
from typing import Required, TypedDict, Unpack

from typing_extensions import override

from common.commands import ClientCommand
from common.config import CMD_POSTFIX_B, TIMEOUT, TIMEOUT_RECHARGING
from common.result import Err, Ok
from server.command_handlers.command_matcher import CommandMatcher
from server.exceptions import CommandSyntaxError, LogicError, ServerTimeoutError
from server.server_result import ServerResult

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("read_handler")


class ReadHandlerKwargs(TypedDict, total=False):
    """Key-word arguments dict for a ReadHandler."""

    reader: Required[StreamReader]
    matcher: Required[CommandMatcher]
    logger: Logger
    _chunk_size: int


class ReadHandler(ABC):
    """Abstract class for a socket reading handler."""

    __slots__ = ("_reader", "_matcher", "_logger", "_chunk_size")

    def __init__(
        self, *, reader: StreamReader, matcher: CommandMatcher, logger: Logger = LOGGER, _chunk_size: int = 8
    ) -> None:
        """All parameters are keyword only.

        Args:
            reader: Socket stream reader.
            matcher: Command matching handler.
            logger: (optional) Defaults to sublogger of base package logger.
            _chunk_size: (optional) Size of chunks. Defaults to 8.
        """
        self._reader = reader
        self._matcher = matcher
        self._logger = logger
        self._chunk_size = _chunk_size

    @abstractmethod
    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        """Reads message of given maximum length ended with CMD_POSTFIX_B.

        Args:
            max_len: Max length of the message including CMD_POSTFIX_B.
            timeout: (optional) Timeout of read. Defaults to TIMEOUT.

        Returns:
            ServerResult[bytes]: Ok(message) if read was successful,
            message has correct length and ends with CMD_POSTFIX_B,
            else Err.
        """
        pass


class AnyLengthSepReadHandler(ReadHandler):
    """Read handler which can process messages with any CMD_POSTFIX_B length."""

    __slots__ = ("_msg_queue",)

    def __init__(self, **kwargs: Unpack[ReadHandlerKwargs]) -> None:
        """
        Args:
            kwargs (ReadHandlerKwargs): Parameters of a base socket reading handler.
        """
        super().__init__(**kwargs)
        self._msg_queue = deque[bytes]()

    @override
    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        self._logger.debug("started read")

        msg = self._get_from_queue()
        if msg.endswith(CMD_POSTFIX_B):
            return Ok(msg)

        msg_stream = BytesIO()
        msg_stream.write(msg)
        self._logger.debug(f"started with data: {msg}")

        length = len(msg)
        separator_spliter = self.SeparatorSplitter(msg)

        while length < max_len:
            self._logger.debug("try read")
            match await self._read_chunk(timeout):
                case Err() as err:
                    return err
                case Ok(value):
                    chunk = value

            self._logger.debug(f"recieved data: {chunk}")

            part_of_current, part_of_next = separator_spliter.check(chunk)

            length += len(part_of_current)
            msg_stream.write(part_of_current)

            if part_of_next:
                self._msg_queue.append(part_of_next)

            if part_of_next is not None:
                break

        self._logger.debug(f"return value: {msg_stream.getvalue()}")
        if not (res := msg_stream.getvalue()[:max_len]).endswith(CMD_POSTFIX_B):
            return Err(CommandSyntaxError("Missing message separator."))
        return Ok(res)

    async def _read_chunk(self, timeout: int) -> ServerResult[bytes]:
        """Reads chunk with given timeout.

        Args:
            timeout (int): Timeout of read.

        Returns:
            ServerResult[bytes]: Ok(chunk) if read was successful, else Err(ServerTimeoutError).
        """
        try:
            chunk = await wait_for(self._reader.read(self._chunk_size), timeout=timeout)
        except (TimeoutError, ConnectionResetError):
            return Err(ServerTimeoutError(f"Timeout exceeded: {timeout=}"))

        if chunk == b"":
            return Err(ServerTimeoutError(f"Connection is probably closed by the other side"))

        return Ok(chunk)

    def _get_from_queue(self) -> bytes:
        """Reads from the message queue until CMD_POSTFIX_B found or until queue is empty.

        Returns:
            bytes: Part of/full message received from queue. If queue was empty, returns empty bytes.
        """
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

    class SeparatorSplitter:
        """Object that splits chunks by CMD_POSTFIX_B."""

        __slots__ = ("_matched_bytes",)

        def __init__(self, beginning_value: bytes | None = None):
            """Initializes SeparatorSplitter.

            Args:
                beginning_value (bytes | None, optional): The beginning value of the read, which may end with part of CMD_POSTFIX_B. Defaults to None.
            """
            self._matched_bytes: list[bool] = self._create_matched_empty()

            if beginning_value:
                for i in range(len(CMD_POSTFIX_B), 0, -1):
                    if beginning_value[-i:] == CMD_POSTFIX_B[:i]:
                        self._matched_bytes[:i] = [True] * i
                        break

        def _create_matched_empty(self) -> list[bool]:
            """Creates list of _matched_bytes beginning value.

            Returns:
                list[bool]: List of False of length len(CMD_POSTFIX_B).
            """
            return [False] * len(CMD_POSTFIX_B)

        def check(self, chunk: bytes) -> tuple[bytes, bytes | None]:
            """Checks given chunck for occurrence of CMD_POSTFIX_B.
            If found, splits chunk.

            Args:
                chunk: Chunk to be checked.

            Returns:
                tuple[bytes, bytes | None]: First element is bytes object which belongs to current message.
                Second element is bytes objects of next message (message after CMD_POSTFIX_B).
                If current message didn't end(CMD_POSTFIX_B was not found), second element is None.
            """
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


class RechargingReadHandler(ReadHandler):
    """Read handler which can read message of any CMD_POSTFIX_B length
    and also takes care of recharging process, if encountered, and possible errors in it."""

    __slots__ = ("_subreader",)

    def __init__(self, **kwargs: Unpack[ReadHandlerKwargs]) -> None:
        """
        Args:
            kwargs (ReadHandlerKwargs): Parameters of a base socket reading handler.
        """
        super().__init__(**kwargs)
        self._subreader = AnyLengthSepReadHandler(**kwargs)

    @override
    async def read(self, max_len: int, *, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        read_length = max(max_len, ClientCommand.CLIENT_RECHARGING.max_len_postfix)  # for correct recharging read
        match await self._subreader.read(read_length, timeout=timeout):
            case Err() as err:
                return err
            case Ok(data):
                pass
        match self._matcher.match_none(ClientCommand.CLIENT_RECHARGING, data):
            case Err():
                match self._matcher.match_none(ClientCommand.CLIENT_FULL_POWER, data):
                    case Ok():
                        return Err(LogicError(f"Unexpected command: {ClientCommand.CLIENT_FULL_POWER.name}"))
                    case Err():
                        return Ok(data[:max_len])
            case Ok():
                self._logger.info("Recharging begin")
                return await self._handle_recharging(max_len, timeout)

    async def _handle_recharging(self, max_len: int, timeout: int = TIMEOUT) -> ServerResult[bytes]:
        """Handles recharging process.

        Args:
            max_len: Max length of the message including CMD_POSTFIX_B.
            timeout: (optional) Timeout of read. Defaults to TIMEOUT.

        Returns:
            ServerResult[bytes]: Ok(message) if recharging and read were successful,
            where message is the original message ment to be received,
            else Err.
        """
        match await self._subreader.read(
            ClientCommand.CLIENT_FULL_POWER.max_len_postfix, timeout=TIMEOUT_RECHARGING
        ):
            case Err() as err:
                self._logger.debug(f"Error while recharging: {err=}")
                return err
            case Ok(data):
                pass
        match self._matcher.match_none(ClientCommand.CLIENT_FULL_POWER, data):
            case Err(err):
                return Err(
                    LogicError(
                        f"Unexpected command. Expected: {ClientCommand.CLIENT_FULL_POWER.name}. Got data: {data}"
                    )
                )
            case Ok():
                self._logger.info("Recharging done")
        match await self._subreader.read(max_len, timeout=timeout):
            case Err() as err:
                return err
            case Ok(data):
                return Ok(data)
