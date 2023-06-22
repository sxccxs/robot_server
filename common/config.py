from pathlib import Path

from common.payloads import KeysPair

BASE_DIR = Path(__file__).resolve().parent.parent
"""Base project directory."""

ENCODING = "ascii"
"""Messages encoding."""

HOST = "localhost"
"""Server host."""

PORT = 9999
"""Server port."""

CMD_POSTFIX = "\a\b"
"""Messages ending sequence."""

CMD_POSTFIX_B = CMD_POSTFIX.encode(ENCODING)
"""Messages ending sequence as bytes."""

KEYS = (
    KeysPair(23019, 32037),
    KeysPair(32037, 29295),
    KeysPair(18789, 13603),
    KeysPair(16443, 29533),
    KeysPair(18189, 21952),
)
"""Pairs of server and client keys for authentication."""

TIMEOUT = 1
"""Response timeout."""

TIMEOUT_RECHARGING = 5
"""Recharging timeout."""


LOGGING_CONFIG_FILE = BASE_DIR / "logging_config.toml"
"""Path logging configuration file."""
