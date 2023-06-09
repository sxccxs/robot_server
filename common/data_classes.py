from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import NamedTuple, Self


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

    @classmethod
    def determine_side(cls, old_coords: Coords, new_coords: Coords) -> Self:
        """Determines side of the coordinate plane based on coordinates before and after one move.
            Coords must differ, but either in x or y, never both. Difference greater than 1 is ignored.

        Args:
            old_coords (Coords): coorde before move.
            new_coords (Coords): coords after move.

        Raises:
            ValueError: raised if it is impossible to calculate orientation from given coords.

        Returns:
            Side: calculated side of the coordinate plane.
        """
        match (old_coords.x == new_coords.x, old_coords.y == new_coords.y):
            case (True, False):
                return Side.UP if new_coords.y > old_coords.y else Side.DOWN
            case (False, True):
                return Side.RIGHT if new_coords.x > old_coords.x else Side.LEFT
            case _:
                raise ValueError(f"Can't calculate orientation from coords: {old_coords=}, {new_coords=}")


@dataclass(slots=True)
class Orientation:
    coords: Coords
    side: Side

    def turn_left(self) -> None:
        self.side = Side((self.side - 1) % 4)

    def turn_right(self) -> None:
        self.side = Side((self.side + 1) % 4)
