from abc import ABC, abstractmethod
from dataclasses import dataclass

from common.data_classes import KeysPair
from server.server_result import ServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class AuthenticatorKwargs(BaseServiceKwargs):
    keys_dict: dict[int, KeysPair]


@dataclass(slots=True)
class Authenticator(BaseService, ABC):
    keys_dict: dict[int, KeysPair]

    @abstractmethod
    async def authenticate(self) -> ServerResult[None]:
        pass
