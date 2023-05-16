from abc import ABC, abstractmethod
from dataclasses import dataclass

from common.commands import ClientCommand, ServerCommand
from common.data_classes import KeysPair
from common.result import Err, Ok
from server.exceptions import CommandKeyIdOutOfRangeError, CommandLoginFailError, CommandNumberFormatError
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


class DefaultAuthenticator(Authenticator):
    async def authenticate(self) -> ServerResult[None]:
        self.logger.debug("Authenticator started")
        match await self._get_username():
            case Ok(value):
                username = value
            case Err() as err:
                return err
        self.logger.info(f"Got valid name: {username=}")

        await self._send_key_request()

        match await self._get_key_id():
            case Ok(value):
                key_pair = value
            case Err() as err:
                return err

        self.logger.info(
            f"Got valid key id. Using pair "
            + f"server_key={key_pair.server_key} - client_key={key_pair.client_key}"
        )

        name_hash = self._calculate_hash(username)

        await self._send_server_confirmation(name_hash, key_pair.server_key)

        match await self._get_client_confirmation(name_hash, key_pair.client_key):
            case Ok():
                pass
            case Err() as err:
                return err

        self.logger.info(f"Hashes match")

        await self._send_ok()

        self.logger.info(f"Authentication completed")
        return Ok(None)

    async def _get_username(self) -> ServerResult[str]:
        match await self.reader.read(ClientCommand.CLIENT_USERNAME.max_len_postfix):
            case Ok(value):
                data = value
            case Err(err):
                return Err(err)
        return self.matcher.match(ClientCommand.CLIENT_USERNAME, data)

    async def _get_key_id(self) -> ServerResult[KeysPair]:
        match await self.reader.read(ClientCommand.CLIENT_KEY_ID.max_len_postfix):
            case Ok(value):
                data = value
            case Err(err):
                return Err(err)

        match self.matcher.match(ClientCommand.CLIENT_KEY_ID, data):
            case Ok(value):
                key_pair_id = value
            case Err(err):
                match err:
                    case CommandNumberFormatError():
                        return Err(CommandKeyIdOutOfRangeError(err))
                    case _:
                        return Err(err)

        if key_pair_id not in self.keys_dict:
            return Err(CommandKeyIdOutOfRangeError(f"Key id is out of range: key_id={key_pair_id}"))

        return Ok(self.keys_dict[key_pair_id])

    async def _get_client_confirmation(self, name_hash: int, client_key: int) -> ServerResult[None]:
        match await self.reader.read(ClientCommand.CLIENT_CONFIRMATION.max_len_postfix):
            case Ok(value):
                data = value
            case Err(err):
                return Err(err)
        match self.matcher.match(ClientCommand.CLIENT_CONFIRMATION, data):
            case Ok(value):
                confirmation = value
            case Err(err):
                match err:
                    case CommandNumberFormatError():
                        return Err(CommandLoginFailError(err))
                    case _:
                        return Err(err)

        if self._decode_hash(confirmation, client_key) != name_hash:
            return Err(CommandLoginFailError(f"Hashes don't match: provided value={confirmation}"))

        return Ok(None)

    async def _send_key_request(self) -> None:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_KEY_REQUEST))

    async def _send_server_confirmation(self, name_hash: int, server_key: int) -> None:
        await self.writer.write(
            self.creator.create_message(
                ServerCommand.SERVER_CONFIRMATION, self._encode_hash(name_hash, server_key)
            )
        )

    async def _send_ok(self) -> None:
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_OK))

    def _calculate_hash(self, username: str) -> int:
        return (sum((ord(c) for c in username)) * 1000) % 0x10000

    def _encode_hash(self, name_hash: int, server_code: int) -> int:
        return (name_hash + server_code) % 0x10000

    def _decode_hash(self, encoded_hash: int, client_code: int) -> int:
        return (encoded_hash - client_code) % 0x10000
