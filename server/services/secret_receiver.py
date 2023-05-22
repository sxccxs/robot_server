from abc import ABC, abstractmethod

from common.commands import ClientCommand, ServerCommand
from common.result import Err, Ok
from server.server_result import NoneServerResult
from server.services.base_service import BaseService, BaseServiceKwargs


class SecretReceiverKwargs(BaseServiceKwargs):
    pass


class SecretReceiver(BaseService, ABC):
    @abstractmethod
    async def receive(self) -> NoneServerResult:
        "Receives secret message from client"
        ...


class DefaultSecretReceiver(SecretReceiver):
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
