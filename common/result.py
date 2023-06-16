from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Class of successful result.

    Args:
        T (type): Any type.
        value (T): Value of the successful result.
    """

    value: T
    __match_args__ = ("value",)


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Class of errored result.

    Args:
        E (type): subclass of Exception.
        error (E): Error describing failed result.
    """

    error: E
    __match_args__ = ("error",)


Result = Ok[T] | Err[E]
"""Result type which is either successful(Ok) or errored(Err)."""

NoneResult = Ok[None] | Err[E]
"""Result type with no value."""
