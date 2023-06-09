from abc import ABC, abstractmethod
from collections import deque
from functools import partial

from typing_extensions import override

from common.commands import ClientCommand, ServerCommand
from common.data_classes import Axis, Coords, Orientation, Side
from common.result import Err, Ok
from server.exceptions import ServerError
from server.server_result import NoneServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class MoverKwargs(BaseServiceKwargs):
    pass


class Mover(BaseService, ABC):
    @abstractmethod
    async def move_to_start(self) -> NoneServerResult:
        pass

    async def _rotate_to(self, orient: Orientation, to_side: Side) -> None:
        if orient.side == to_side:
            return

        if (orient.side - to_side) % 4 == 1:
            await self._turn_left(orient)
            return

        count = 1
        if (orient.side - to_side) % 4 == 2:
            count = 2
        for _ in range(count):
            await self._turn_right(orient)

    async def _get_orientation(self) -> Orientation | None:
        """Determines orientation of the robot by making 2 moves forward.
        If obstacle was encountered, turns left and moves again.

        Returns:
            Orientation | None: If after first move position is (0,0), returns None,
            else determined orientation object.
        """
        pos = await self._make_move()
        if pos == Coords(0, 0):
            return None
        new_pos = await self._make_move()
        if pos == new_pos:  # if found obstacle, turn left and move again
            await self._turn_left()
            new_pos = await self._make_move()

        side = Side.determine_side(pos, new_pos)
        return Orientation(new_pos, side)

    async def _make_move(self) -> Coords:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_MOVE))
        return await self._get_ok_response()

    async def _turn_right(self, orient: Orientation | None = None) -> Coords:
        if orient is not None:
            orient.turn_right()
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_TURN_RIGHT))
        return await self._get_ok_response()

    async def _turn_left(self, orient: Orientation | None = None) -> Coords:
        if orient is not None:
            orient.turn_left()
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_TURN_LEFT))
        return await self._get_ok_response()

    async def _get_ok_response(self) -> Coords:
        match await self.reader.read(ClientCommand.CLIENT_OK.max_len_postfix):
            case Err(err):
                raise err
            case Ok(value):
                data = value
        match self.matcher.match(ClientCommand.CLIENT_OK, data):
            case Err(err):
                raise err
            case Ok(data):
                return data


class DefaultMover(Mover):
    @override
    async def move_to_start(self) -> NoneServerResult:
        self.logger.debug("Started mover")
        try:
            match await self._get_orientation():
                case None:
                    self.logger.info("Moved to (0,0).")
                    return Ok(None)
                case Orientation() as orientation:
                    pass

            self.logger.info(
                f"Starting position: {orientation.coords}, starting orientation: {orientation.side.name}"
            )
            await self._move_to_0(orientation, Axis.X)
            await self._move_to_0(orientation, Axis.Y)
        except ServerError as err:
            self.logger.info("Error while moving")
            return Err(err)

        return Ok(None)

    async def _move_to_0(self, orient: Orientation, axis: Axis) -> None:
        """Moves to 0 by the specified axis.

        Args:
            orient (Orientation): orientation object determening current position.
            axis (Axis): axis to move along.
        """
        self.logger.info(f"Started moving to 0 by axis {axis.name}")
        if axis == Axis.X:
            move_side = Side.LEFT if orient.coords.x > 0 else Side.RIGHT
        else:
            move_side = Side.DOWN if orient.coords.y > 0 else Side.UP

        await self._rotate_to(orient, move_side)

        condition = (lambda: orient.coords.x != 0) if axis == Axis.X else (lambda: orient.coords.y != 0)
        bypasser = (
            partial(self._switch_axis, orient.coords.x) if axis == Axis.X else self._bypass_obstacle
        )  # select a bypasser function for each axis

        while condition():  # while one x or y (depending on axis) is not 0
            new_pos = await self._make_move()
            if new_pos == orient.coords:
                self.logger.debug(f"Found obstacle moving from {orient.coords} with direction: {orient.side.name}")
                orient.coords = await bypasser()
            else:
                orient.coords = new_pos
            self.logger.debug(f"Moved to {orient.coords}")
        self.logger.info(f"Moving done. Moved to new coords: {orient.coords}")

    async def _switch_axis(self, x_coord: int) -> Coords:
        turns = (self._turn_right, self._turn_left) if x_coord < 0 else (self._turn_left, self._turn_right)
        await turns[0]()
        await self._make_move()
        return await turns[1]()

    async def _bypass_obstacle(self) -> Coords:
        await self._turn_right()
        await self._make_move()
        await self._turn_left()
        await self._make_move()
        await self._make_move()
        await self._turn_left()
        await self._make_move()

        return await self._turn_right()


class BFSMover(Mover):
    @override
    async def move_to_start(self) -> NoneServerResult:
        self.logger.debug("Started mover")
        try:
            match await self._get_orientation():
                case None:
                    self.logger.info("Moved to (0,0).")
                    return Ok(None)
                case Orientation() as orientation:
                    pass
            self.logger.info(
                f"Starting position: {orientation.coords}, starting orientation: {orientation.side.name}"
            )
            await self._move_to_center(orientation)
        except ServerError as err:
            self.logger.info("Error while moving")
            return Err(err)

        return Ok(None)

    async def _move_to_center(self, orientation: Orientation) -> None:
        if orientation.coords == Coords(0, 0):
            return
        obstacles = set[Coords]()
        path_queue = self._bfs(orientation.coords, obstacles)
        self.logger.debug(f"Planed way: {path_queue}")
        path_queue.popleft()  # remove current Coords from path
        while path_queue:
            if orientation.coords == Coords(0, 0):
                return
            cur = path_queue.popleft()
            needed_side = Side.determine_side(orientation.coords, cur)
            await self._rotate_to(orientation, needed_side)
            new_coords = await self._make_move()
            if orientation.coords == new_coords:
                obstacles.add(cur)
                path_queue = self._bfs(orientation.coords, obstacles)
                self.logger.debug(f"Obstacle found at {orientation.coords}. New planed way: {path_queue}")
                path_queue.popleft()
            else:
                orientation.coords = new_coords

        self.logger.info("Achieved (0,0).")

    def _bfs(self, start: Coords, obstacles: set[Coords]) -> deque[Coords]:
        backtrack = dict[Coords, Coords]()
        visited = set[Coords]()
        queue: deque[Coords] = deque()
        queue.append(start)
        while queue:
            current = queue.popleft()
            if current == Coords(0, 0):
                break

            if current in visited or current in obstacles:
                continue

            visited.add(current)
            neighbours = (
                Coords(current.x - 1, current.y),
                Coords(current.x + 1, current.y),
                Coords(current.x, current.y - 1),
                Coords(current.x, current.y + 1),
            )
            for n in neighbours:
                if n not in visited:
                    queue.append(n)
                    backtrack[n] = current

        path = deque[Coords]()
        path.append(Coords(0, 0))
        while path[-1] != start:
            path.append(backtrack[path[-1]])
        path.reverse()

        return path
