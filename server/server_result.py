from typing import TypeVar

from common.result import Result
from server.exceptions import ServerError

T = TypeVar("T")

ServerResult = Result[T, ServerError]
