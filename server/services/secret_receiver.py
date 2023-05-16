from abc import ABC, abstractmethod

from server.server_result import NoneServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class SecretReceiverKwargs(BaseServiceKwargs):
    pass


class SecretReceiver(BaseService, ABC):
    @abstractmethod
    async def receive(self) -> NoneServerResult:
        "Receives secret message from client"
        ...
