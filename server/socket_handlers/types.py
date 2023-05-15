from typing import Callable

SeparatorChecker = Callable[[bytes], tuple[bytes, bytes | None]]
