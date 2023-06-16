from abc import ABC, abstractmethod
from typing import Unpack

from typing_extensions import override

from common.commands import ClientCommand, ServerCommand
from common.payloads import KeysPair
from common.result import Err, Ok
from server.exceptions import CommandKeyIdOutOfRangeError, CommandLoginFailError, CommandNumberFormatError
from server.server_result import NoneServerResult, ServerResult
from server.services.base_service import BaseService, BaseServiceKwargs

HASH_MODULO = 0x10000
"""Module for keys encoding."""


class AuthenticatorKwargs(BaseServiceKwargs):
    """Key-word arguments dict for a Authenticator."""

    keys_dict: dict[int, KeysPair]


class Authenticator(BaseService, ABC):
    """Abstract class for an authentication service."""

    __slots__ = ("keys_dict",)

    def __init__(self, *, keys_dict: dict[int, KeysPair], **kwargs: Unpack[BaseServiceKwargs]) -> None:
        """
        Args:
            keys_dict: Keyword parameter. Map of ids and server-client keys pairs.
            kwargs (BaseServiceKwargs): Parameters of a base service class.
        """
        super().__init__(**kwargs)
        self.keys_dict = keys_dict

    @abstractmethod
    async def authenticate(self) -> NoneServerResult:
        """Handles whole robot authentication process.

        Returns:
            NoneServerResult: Ok(None) if authenticated successfully, else Err(ServerError).
        """
        pass

    def _calculate_hash(self, username: str) -> int:
        return (sum((ord(c) for c in username)) * 1000) % HASH_MODULO

    def _encode_hash(self, name_hash: int, server_code: int) -> int:
        return (name_hash + server_code) % HASH_MODULO

    def _decode_hash(self, encoded_hash: int, client_code: int) -> int:
        return (encoded_hash - client_code) % HASH_MODULO


class DefaultAuthenticator(Authenticator):
    """Default authentication service realization."""

    @override
    async def authenticate(self) -> NoneServerResult:
        self.logger.debug("Authenticator started")
        match await self._get_username():
            case Err() as err:
                return err
            case Ok(value):
                username = value
        self.logger.info(f"Got valid name: {username=}")

        await self._send_key_request()

        match await self._get_key_id():
            case Err() as err:
                return err
            case Ok(value):
                key_pair = value

        self.logger.info(
            f"Got valid key id. Using pair "
            + f"server_key={key_pair.server_key} - client_key={key_pair.client_key}"
        )

        name_hash = self._calculate_hash(username)

        await self._send_server_confirmation(name_hash, key_pair.server_key)

        match await self._get_client_confirmation(name_hash, key_pair.client_key):
            case Err() as err:
                return err
            case Ok():
                pass

        self.logger.info(f"Hashes match")

        await self._send_ok()

        self.logger.info(f"Authentication completed")
        return Ok(None)

    async def _get_username(self) -> ServerResult[str]:
        """Receives robot's username and validates it.

        Returns:
            ServerResult[str]: Ok(username) if data was valid else Err(ServerError).
        """
        match await self.reader.read(ClientCommand.CLIENT_USERNAME.max_len_postfix):
            case Ok(value):
                data = value
            case Err(err):
                return Err(err)
        return self.matcher.match(ClientCommand.CLIENT_USERNAME, data)

    async def _get_key_id(self) -> ServerResult[KeysPair]:
        """Receives id of a keys pair, which robot wants to use.
        Checkes if it is a valid id.

        Returns:
            ServerResult[KeysPair]: Ok(keys_pair) if data was valid else Err(ServerError).
        """
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

    async def _get_client_confirmation(self, name_hash: int, client_key: int) -> NoneServerResult:
        """Receives confirmation number from robot, checks if it is a valid number and
        if it encodes client_key.

        Args:
            name_hash: Encoded robot's username.
            client_key: Client key robot has selected for communication.

        Returns:
            NoneServerResult: Ok(None) if value was valid, else Err(ServerError).
        """
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
        """Sends key request."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_KEY_REQUEST))

    async def _send_server_confirmation(self, name_hash: int, server_key: int) -> None:
        """Sends server confirmation message.

        Args:
            name_hash: Encoded robot's username.
            server_key: Server key robot has selected for communication.
        """
        await self.writer.write(
            self.creator.create_message(
                ServerCommand.SERVER_CONFIRMATION, self._encode_hash(name_hash, server_key)
            )
        )

    async def _send_ok(self) -> None:
        """Sends ok message."""
        await self.writer.write(self.creator.create_message(ServerCommand.SERVER_OK))
