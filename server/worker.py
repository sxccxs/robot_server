from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import NotRequired, TypedDict

from common.commands import ServerCommand
from common.data_classes import KeysPair
from common.result import Err, NoneResult, Ok
from server.exceptions import (
    AuthenticationFailed,
    CommandKeyIdOutOfRangeError,
    CommandLoginFailError,
    CommandSyntaxError,
    LogicError,
    ServerError,
    ServerTimeoutError,
)
from server.manipulators import DefaultManipulators, Manipulators

from . import logger as LOGGER_BASE

LOGGER = LOGGER_BASE.getChild("worker")


class WorkerKwargs(TypedDict):
    worker_id: int
    reader_stream: StreamReader
    writer_stream: StreamWriter
    keys_dict: dict[int, KeysPair]
    manipulators: NotRequired[Manipulators | None]


class Worker(ABC):
    def __init__(
        self,
        worker_id: int,
        reader_stream: StreamReader,
        writer_stream: StreamWriter,
        keys_dict: dict[int, KeysPair],
        manipulators: Manipulators | None = None,
    ) -> None:
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

    @abstractmethod
    async def do(self) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class DefaultWorker(Worker):
    async def do(self) -> None:
        self.logger.info(f"Started new worker {self.worker_id}")
        match await self._authenticate():
            case Err():
                return
            case Ok():
                pass

    async def close(self) -> None:
        await self.writer.close()
        self.logger.info(f"Ended worker {self.worker_id}")

    async def _authenticate(self) -> NoneResult[AuthenticationFailed]:
        match await self.authenticator.authenticate():
            case Ok():
                self.logger.info(f"worker {self.worker_id}: Authentication success")
                return Ok(None)
            case Err(err):
                self.logger.info(f"Error while authenticating: {err=}")
                await self._process_error(err)
                return Err(AuthenticationFailed(err))

    async def _process_error(self, err: ServerError) -> None:
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
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_SYNTAX_ERROR))

    async def _send_key_out_of_range(self) -> None:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_KEY_OUT_OF_RANGE_ERROR))

    async def _send_login_failed(self) -> None:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_LOGIN_FAILED))

    async def _send_logic_error(self) -> None:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_LOGIC_ERROR))
