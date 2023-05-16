import asyncio
import logging
import logging.config

import tomllib

from common.config import LOGGING_CONFIG_FILE


def configure_logging() -> None:
    with open(LOGGING_CONFIG_FILE, "rb") as stream:
        config = tomllib.load(stream)

    logging.config.dictConfig(config)


async def main():
    configure_logging()

    from common.config import HOST, KEYS, PORT
    from server.manipulators import RechargingManipulators
    from server.server import Server

    server = Server(HOST, PORT, KEYS, manipulators=RechargingManipulators())
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
