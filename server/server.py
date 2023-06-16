from asyncio import StreamReader, StreamWriter, start_server
from typing import Iterable, Protocol, Unpack
from venv import logger

from common.payloads import KeysPair
from server.manipulators import Manipulators
from server.worker import DefaultWorker, Worker, WorkerKwargs

from . import logger

logger = logger.getChild("server")


class WorkerFactory(Protocol):
    """Worker factory protocol."""

    def __call__(self, **kwargs: Unpack[WorkerKwargs]) -> Worker:
        ...


class Server:
    """Main server implementation. Runs forever, waites for robots to connect and passes each to a worker."""

    def __init__(
        self,
        host: str,
        port: int,
        keys_: Iterable[KeysPair],
        *,
        worker_factory: WorkerFactory = DefaultWorker,
        manipulators: Manipulators | None = None,
    ) -> None:
        """
        Args:
            hots: IP adress for server to run on.
            port: Port for server to run on.
            keys: Iterable of server-client keys pairs. Its index will be its id.
            worker_factory: Keyword parameter. Factory to create workers to handle each connection. Defaults to DefaultWorker.
            manipulators: Keyword parameter. Object with all needed for worker factories defined. Defaults to None.
        """
        self.host = host
        self.port = port
        self.worker_factory = worker_factory
        self.manipulators = manipulators
        self.keys = {ind: value for ind, value in enumerate(keys_)}
        self.next_worker_id = 0

    async def run(self) -> None:
        """Starts server."""
        server = await start_server(self._run_worker, self.host, self.port)
        logger.info("Server start")
        async with server:
            await server.serve_forever()
        logger.info("Server shutdown")

    async def _run_worker(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Function called when new robot has connected. Creates a new worker and passes a connection to it.

        Args:
            reader: Socket stream reader of the connection.
            writer: Socket stream writer of the connection.
        """

        async with self.worker_factory(
            worker_id=self.next_worker_id,
            reader_stream=reader,
            writer_stream=writer,
            keys_dict=self.keys,
            manipulators=self.manipulators,
        ) as worker:
            logger.info(f"Created new connection {worker.worker_id}")
            await worker.do()

        self.next_worker_id += 1
        logger.info(f"Connection {worker.worker_id} closed")
