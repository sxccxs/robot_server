from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T
    __match_args__ = ("value",)


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E
    __match_args__ = ("error",)


Result = Ok[T] | Err[E]

NoneResult = Ok[None] | Err[E]
