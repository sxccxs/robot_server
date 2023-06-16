class ServerError(Exception):
    """Base exception class for all server exceptions."""


class CommandKeyIdOutOfRangeError(ServerError):
    """Id of keys pair is out of range."""

    pass


class CommandLoginFailError(ServerError):
    """Robot's login failed."""

    pass


class CommandSyntaxError(ServerError):
    """Invalid command syntax."""

    pass


class LogicError(ServerError):
    """Unexpectes command."""

    pass


class ServerTimeoutError(ServerError):
    """Server timeout expired."""

    pass


class CommandNumberFormatError(ServerError):
    """Number is of wrong format."""

    pass
