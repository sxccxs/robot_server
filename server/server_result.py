from typing import TypeVar

from common.result import NoneResult, Result
from server.exceptions import ServerError

T = TypeVar("T")

ServerResult = Result[T, ServerError]
NoneServerResult = NoneResult[ServerError]
