from abc import ABC, abstractmethod
from functools import partial

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


class DefaultMover(Mover):
    async def move_to_start(self) -> NoneServerResult:
        self.logger.debug("Started mover")
        try:
            orientation = await self._get_orientation()
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
        """Moves to 0 by the specified axis

        Args:
            orient (Orientation): orientation object determening current position
            axis (Axis): axis to move along
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

    async def _rotate_to(self, orient: Orientation, to_side: Side) -> None:
        while orient.side != to_side:
            await self._turn_right(orient)

    async def _get_orientation(self) -> Orientation:
        pos = await self._make_move()
        new_pos = await self._make_move()
        if pos == new_pos:  # if found obstacle, turn left and move again
            await self._turn_left()
            new_pos = await self._make_move()

        side = self._determine_side(pos, new_pos)
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
            case Ok(data):
                match self.matcher.match(ClientCommand.CLIENT_OK, data):
                    case Err(err):
                        raise err
                    case Ok(data):
                        return data




