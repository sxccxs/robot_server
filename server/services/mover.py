from abc import ABC, abstractmethod

from server.server_result import NoneServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class MoverKwargs(BaseServiceKwargs):
    pass


class Mover(BaseService, ABC):
    @abstractmethod
    async def move_to_start(self) -> NoneServerResult:
        pass
