from typing import Protocol, Unpack

from server.command_handlers.command_creator import CommandCreator, CommandCreatorKwargs, DefaultCommandCreator
from server.command_handlers.command_matcher import CommandMatcher, CommandMatcherKwargs, DefaultCommandMatcher
from server.services.authenticator import Authenticator, AuthenticatorKwargs, DefaultAuthenticator
from server.services.mover import BFSMover, DefaultMover, Mover, MoverKwargs
from server.services.secret_receiver import DefaultSecretReceiver, SecretReceiver, SecretReceiverKwargs
from server.socket_handlers.read_handler import (
    AnyLengthSepReadHandler,
    ReadHandler,
    ReadHandlerKwargs,
    RechargingReadHandler,
)
from server.socket_handlers.write_handler import DefaultWriteHandler, WriteHandler, WriteHandlerKwargs


class Manipulators(Protocol):
    """Inteface of a manipulators object - object with defined factories for all need servicesand handlers."""

    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        """Factory for CommandMatcher."""
        ...

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        """Factory for CommandCreator."""
        ...

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        """Factory for ReadHandler."""
        ...

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        """Factory for WriteHandler."""
        ...

    def get_autheticator(self, **kwargs: Unpack[AuthenticatorKwargs]) -> Authenticator:
        """Factory for Authenticator."""
        ...

    def get_mover(self, **kwargs: Unpack[MoverKwargs]) -> Mover:
        """Factory for Mover."""
        ...

    def get_receiver(self, **kwargs: Unpack[SecretReceiverKwargs]) -> SecretReceiver:
        """Factory for SecretReceiver."""
        ...


class DefaultManipulators:
    """A default implementation of Manipulators protocol."""

    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        """Factory for CommandMatcher.

        Returns:
            CommandMatcher: DefaultCommandMatcher.
        """
        return DefaultCommandMatcher(**kwargs)

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        """Factory for CommandCreator.

        Returns:
            CommandCreator: DefaultCommandCreator.
        """
        return DefaultCommandCreator(**kwargs)

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        """Factory for ReadHandler.

        Returns:
            ReadHandler: AnyLengthSepReadHandler.
        """
        return AnyLengthSepReadHandler(**kwargs)

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        """Factory for WriteHandler.

        Returns:
            WriteHandler: DefaultWriteHandler.
        """
        return DefaultWriteHandler(**kwargs)

    def get_autheticator(self, **kwargs: Unpack[AuthenticatorKwargs]) -> Authenticator:
        """Factory for Authenticator.

        Returns:
            Authenticator: DefaultAuthenticator.
        """
        return DefaultAuthenticator(**kwargs)

    def get_mover(self, **kwargs: Unpack[MoverKwargs]) -> Mover:
        """Factory for Mover.

        Returns:
            Mover: DefaultMover.
        """
        return DefaultMover(**kwargs)

    def get_receiver(self, **kwargs: Unpack[SecretReceiverKwargs]) -> SecretReceiver:
        """Factory for SecretReceiver.

        Returns:
            SecretReceiver: DefaultSecretReceiver.
        """
        return DefaultSecretReceiver(**kwargs)


class RechargingManipulators(DefaultManipulators):
    """An implementation of Manipulators interface suitable for handling recharging."""

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        """Factory for ReadHandler.

        Returns:
            ReadHandler: RechargingReadHandler.
        """
        return RechargingReadHandler(**kwargs)


class ExtendedManipulators(RechargingManipulators):
    """An implementation of Manipulators with extended capabilities."""

    def get_mover(self, **kwargs: Unpack[MoverKwargs]) -> Mover:
        """Factory for Mover.

        Returns:
            Mover: BFSMover.
        """
        return BFSMover(**kwargs)
