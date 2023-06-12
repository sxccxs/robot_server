from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from traceback import format_tb
from types import TracebackType
from typing import NotRequired, Self, TypedDict

from typing_extensions import override

from common.commands import ServerCommand
from common.data_classes import KeysPair
from common.result import Err, Ok
from server.exceptions import (
    CommandKeyIdOutOfRangeError,
    CommandLoginFailError,
    CommandSyntaxError,
    LogicError,
    ServerError,
    ServerTimeoutError,
)
from server.manipulators import DefaultManipulators, Manipulators
from server.server_result import NoneServerResult

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("worker")


class WorkerKwargs(TypedDict):
    """Key-word arguments dict for a Worker."""

    worker_id: int
    reader_stream: StreamReader
    writer_stream: StreamWriter
    keys_dict: dict[int, KeysPair]
    manipulators: NotRequired[Manipulators | None]


class Worker(ABC):
    """Abstract class for a worker which fully handles one connection."""

    def __init__(
        self,
        worker_id: int,
        reader_stream: StreamReader,
        writer_stream: StreamWriter,
        keys_dict: dict[int, KeysPair],
        manipulators: Manipulators | None = None,
    ) -> None:
        """Initializes a Worker.

        Args:
            worker_id (int): Worker's unique id.
            reader_stream (StreamReader): Socket stream reader.
            writer_stream (StreamWriter): Socket stream writer.
            keys_dict (dict[int, KeysPair]): Dict of ids and pairs of server and client key.
            manipulators (Manipulators | None, optional): Object with all needed factories defined.Defaults to None.
            If None, DefaultManipulators will be used.
        """
        manipulators = manipulators if manipulators is not None else DefaultManipulators()
        self.worker_id = worker_id
        self.logger = LOGGER.getChild(f"{self.worker_id}#")
        self.matcher = manipulators.get_matcher(logger=self.logger.getChild("matcher"))
        self.creator = manipulators.get_creator(logger=self.logger.getChild("creator"))
        self.reader = manipulators.get_reader(
            reader=reader_stream, matcher=self.matcher, logger=self.logger.getChild("reader")
        )
        self.writer = manipulators.get_writer(
            writer=writer_stream, creator=self.creator, logger=self.logger.getChild("writer")
        )
        self.authenticator = manipulators.get_autheticator(
            reader=self.reader,
            writer=self.writer,
            keys_dict=keys_dict,
            matcher=self.matcher,
            creator=self.creator,
            logger_=self.logger.getChild("authenticator"),
        )
        self.mover = manipulators.get_mover(
            reader=self.reader,
            writer=self.writer,
            matcher=self.matcher,
            creator=self.creator,
            logger_=self.logger.getChild("mover"),
        )
        self.receiver = manipulators.get_receiver(
            reader=self.reader,
            writer=self.writer,
            matcher=self.matcher,
            creator=self.creator,
            logger_=self.logger.getChild("secret_receiver"),
        )

    @abstractmethod
    async def do(self) -> None:
        """Starts worker to handle robot's connection."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Closes passed to worker connection."""
        ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self.close()
        if exc_val is not None:
            self.logger.critical(f"Unexpected error happend: type={exc_type},  value={exc_val}")
            self.logger.critical(f"Traceback: {format_tb(exc_tb)}")


class DefaultWorker(Worker):
    """Default implemenation of Worker to fully handle one robot connection."""

    @override
    async def do(self) -> None:
        self.logger.info(f"Started new worker {self.worker_id}")
        match await self._authenticate():
            case Err():
                return
            case Ok():
                pass

        match await self._move_to_start():
            case Err():
                return
            case Ok():
                await self._get_secret_message()

    @override
    async def close(self) -> None:
        await self.writer.close()
        self.logger.info(f"Ended worker {self.worker_id}")

    async def _authenticate(self) -> NoneServerResult:
        """Handles robot authentication.

        Returns:
            NoneServerResult: Ok(None) if authenticated successfully, else Err(ServerError).
        """
        match await self.authenticator.authenticate():
            case Ok():
                self.logger.info(f"Authenticated successfully")
                return Ok(None)
            case Err(err):
                self.logger.info(f"Error while authenticating: {err=}")
                await self._process_error(err)
                return Err(err)

    async def _move_to_start(self) -> NoneServerResult:
        """Handles robot movement to (0, 0) point.

        Returns:
            NoneServerResult: Ok(None) if authenticated successfully, else Err(ServerError).
        """
        match await self.mover.move_to_start():
            case Ok():
                self.logger.info("Successfully moved to coordinates (0,0)")
                return Ok(None)
            case Err(err):
                self.logger.info(f"Error while moving: {err=}")
                await self._process_error(err)
                return Err(err)

    async def _get_secret_message(self) -> NoneServerResult:
        """Receives secret message from robot, after it moved to (0,0) point.

        Returns:
            NoneServerResult: Ok(None) if authenticated successfully, else Err(ServerError).
        """
        match await self.receiver.receive():
            case Ok():
                self.logger.info("Successfully received secret message")
                return Ok(None)
            case Err(err):
                self.logger.info(f"Error while receiving secret message: {err=}")
                await self._process_error(err)
                return Err(err)

    async def _process_error(self, err: ServerError) -> None:
        """Sends corresponding response for a given error if needed.
        If err is not a CommandSyntaxError, LogicError, CommandKeyIdOutOfRangeError,
        CommandLoginFailError or ServerTimeoutError, raises err.

        Args:
            err (ServerError): Error to handle.

        Raises:
            ServerError: err if err is not of allowed type.
        """
        match err:
            case CommandSyntaxError():
                await self._send_syntax_error()
            case LogicError():
                await self._send_logic_error()
            case CommandKeyIdOutOfRangeError():
                await self._send_key_out_of_range()
            case CommandLoginFailError():
                await self._send_login_failed()
            case ServerTimeoutError():
                pass
            case _:
                raise err

    async def _send_syntax_error(self) -> None:
        """Sends syntax error response."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_SYNTAX_ERROR))

    async def _send_key_out_of_range(self) -> None:
        """Sends key out of range error response."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_KEY_OUT_OF_RANGE_ERROR))

    async def _send_login_failed(self) -> None:
        """Sends login failed error response."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_LOGIN_FAILED))

    async def _send_logic_error(self) -> None:
        """Sends logic error response."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_LOGIC_ERROR))
