from typing import TypeVar

from common.result import NoneResult, Result
from server.exceptions import ServerError

T = TypeVar("T")

ServerResult = Result[T, ServerError]
"""Result with ServerError as an error type."""

NoneServerResult = NoneResult[ServerError]
"""NoneResult with ServerError as an error type."""
