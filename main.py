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




if __name__ == "__main__":
    asyncio.run(main())
