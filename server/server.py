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
    """Worker factory protocol."""

    def __call__(self, **kwargs: Unpack[WorkerKwargs]) -> Worker:
        ...


@dataclass
class Server:
    """Main server implementation. Runs forever, waites for robots to connect and passes each to a worker.

    Args:
        hots (str): IP adress for server to run on.
        port (int): Port for server to run on.
        keys (Iterable[KeysPair]): Iterable of server-client keys pairs. Its index will be its id.
        worker_factory (WorkerFactory, optional): Factory to create workers to handle each connection. Defaults to DefaultWorker.
        manipulators (Manipulators | None, optional): Object with all needed for worker factories defined. Defaults to None.
    """

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
        """Starts server."""
        server = await asyncio.start_server(self._run_worker, self.host, self.port)
        logger.info("Server start")
        async with server:
            await server.serve_forever()
        logger.info("Server shutdown")

    async def _run_worker(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Function called when new robot has connected. Creates a new worker and passes a connection to it.

        Args:
            reader (asyncio.StreamReader): Socket stream reader of the connection.
            writer (asyncio.StreamWriter): Socket stream writer of the connection.
        """
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
