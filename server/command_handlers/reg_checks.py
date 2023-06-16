import re


def is_int(value: str) -> bool:
    """Check if give value is number-like.

    Args:
        value (str): Value to be checked.

    Returns:
        bool: True if matched else False.
    """
    pattern = r"^(\+|-|\d)?\d+$"
    return bool(re.match(pattern, value))


def matches_client_okay(value: str) -> bool:
    """Check if give value is in form of OK repsonse. For more see readme.

    Args:
        value (str): Value to be checked.

    Returns:
        bool: True if matched else False.
    """
    pattern = r"^OK (\+|-)?\d+ (\+|-)?\d+$"
    return bool(re.match(pattern, value))
