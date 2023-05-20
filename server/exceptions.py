class BaseServerError(Exception):
    pass


class AuthenticationFailed(BaseServerError):
    pass


class MoveFailed(BaseServerError):
    pass


class GetSecretMessageFailed(BaseServerError):
    pass


class ServerError(BaseServerError):
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
