import re


def is_int(value: str) -> bool:
    pattern = r"^(\+|-|\d)?\d+$"
    return bool(re.match(pattern, value))


def matches_client_okay(data: str) -> bool:
    pattern = r"^OK (\+|-)?\d+ (\+|-)?\d+$"
    return bool(re.match(pattern, data))
