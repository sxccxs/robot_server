class AuthenticationFailed(Exception):
    pass


class MoveFailed(Exception):
    pass


class GetSecretMessageFailed(Exception):
    pass


class ServerError(Exception):
    pass


class CommandKeyIdOutOfRangeError(ServerError):
    pass


class CommandLoginFailError(ServerError):
    pass


class CommandSyntaxError(ServerError):
    pass


class LogicError(ServerError):
    pass


class ServerTimeoutError(ServerError):
    pass


class CommandNumberFormatError(ServerError):
    pass
