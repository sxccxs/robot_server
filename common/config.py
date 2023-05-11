from pathlib import Path

from common.data_classes import KeysPair

BASE_DIR = Path(__file__).resolve().parent.parent
ENCODING = "ascii"

HOST = "localhost"
PORT = 9999

CMD_POSTFIX = "\a\b"
CMD_POSTFIX_B = CMD_POSTFIX.encode(ENCODING)

KEYS = (
    KeysPair(23019, 32037),
    KeysPair(32037, 29295),
    KeysPair(18789, 13603),
    KeysPair(16443, 29533),
    KeysPair(18189, 21952),
)

TIMEOUT = 1
TIMEOUT_RECHARGING = 5


LOGGING_CONFIG_FILE = BASE_DIR / "logging_config.toml"
