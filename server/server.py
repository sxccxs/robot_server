import asyncio
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import Iterable, Protocol, Unpack
from venv import logger

from common.data_classes import KeysPair
from server.manipulators import Manipulators
from server.worker import DefaultWorker, Worker, WorkerKwargs

from . import logger

logger = logger.getChild("server")


class WorkerFactory(Protocol):
    def __call__(self, **kwargs: Unpack[WorkerKwargs]) -> Worker:
        ...


@dataclass
class Server:
    host: str
    port: int
    keys_: InitVar[Iterable[KeysPair]]
    _: KW_ONLY
    worker_factory: WorkerFactory = DefaultWorker
    manipulators: Manipulators | None = None
    keys: dict[int, KeysPair] = field(init=False)
    next_worker_id: int = field(init=False, default=0)

    def __post_init__(self, keys_: Iterable[KeysPair]) -> None:
        self.keys = {ind: value for ind, value in enumerate(keys_)}

    async def run(self) -> None:
        server = await asyncio.start_server(self._run_worker, self.host, self.port)
        logger.info("Server start")
        async with server:
            await server.serve_forever()
        logger.info("Server shutdown")

    async def _run_worker(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        worker = self.worker_factory(
            worker_id=self.next_worker_id,
            reader_stream=reader,
            writer_stream=writer,
            keys_dict=self.keys,
            manipulators=self.manipulators,
        )
        self.next_worker_id += 1
        logger.info(f"Created new connection {worker.worker_id}")
        async with worker:
            await worker.do()
        logger.info(f"Connection {worker.worker_id} closed")
