from abc import ABC, abstractmethod

from typing_extensions import override

from common.commands import ClientCommand, ServerCommand
from common.result import Err, Ok
from server.server_result import NoneServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class SecretReceiverKwargs(BaseServiceKwargs):
    """Key-word arguments dict for a SecretReceiver."""

    pass


class SecretReceiver(BaseService, ABC):
    """Abstract class for a secret message receiver service."""

    @abstractmethod
    async def receive(self) -> NoneServerResult:
        """Receives a secret message from robot.

        Returns:
            NoneServerResult: Ok(None) if received successfully, else Err(ServerError).
        """
        ...


class DefaultSecretReceiver(SecretReceiver):
    """Default implementation of secret message receiver service."""

    @override
    async def receive(self) -> NoneServerResult:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_PICK_UP))
        match await self.reader.read(ClientCommand.CLIENT_MESSAGE.max_len_postfix):
            case Err() as err:
                self.logger.info(f"Error in secret receiving: {err=}")
                return err
            case Ok(data):
                pass
        match self.matcher.match(ClientCommand.CLIENT_MESSAGE, data):
            case Err() as err:
                self.logger.info(f"Error in secret receiving: {err=}")
                return err
            case Ok():
                await self.writer.write(self.creator.create_message(ServerCommand.SERVER_LOGOUT))
                self.logger.info("Received successfully")
                return Ok(None)
