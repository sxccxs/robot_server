from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import NotRequired, TypedDict

from common.data_classes import KeysPair
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

    @abstractmethod
    async def do(self) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
