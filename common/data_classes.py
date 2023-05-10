from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import NamedTuple


class KeysPair(NamedTuple):
    server_key: int
    client_key: int


class Coords(NamedTuple):
    x: int
    y: int


class Axis(Enum):
    X = auto()
    Y = auto()


class Side(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


@dataclass(slots=True)
class Orientation:
    coords: Coords
    side: Side

    def turn_left(self) -> None:
        self.side = Side((self.side.value - 1) % 4)

    def turn_right(self) -> None:
        self.side = Side((self.side.value + 1) % 4)
