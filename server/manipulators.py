from typing import Protocol, Unpack

from server.command_handlers.command_creator import CommandCreator, CommandCreatorKwargs, DefaultCommandCreator
from server.command_handlers.command_matcher import CommandMatcher, CommandMatcherKwargs, DefaultCommandMatcher
from server.services.authenticator import Authenticator, AuthenticatorKwargs, DefaultAuthenticator
from server.services.mover import DefaultMover, Mover, MoverKwargs
from server.services.secret_receiver import DefaultSecretReceiver, SecretReceiver, SecretReceiverKwargs
from server.socket_handlers.read_handler import (
    ReadHandler,
    ReadHandlerKwargs,
    Recharging2BytesReadHandler,
    Split2BytesReadHandler,
)
from server.socket_handlers.write_handler import DefaultWriteHandler, WriteHandler, WriteHandlerKwargs


class Manipulators(Protocol):
    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        ...

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        ...

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        ...

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        ...

    def get_autheticator(self, **kwargs: Unpack[AuthenticatorKwargs]) -> Authenticator:
        ...

    def get_mover(self, **kwargs: Unpack[MoverKwargs]) -> Mover:
        ...

    def get_receiver(self, **kwargs: Unpack[SecretReceiverKwargs]) -> SecretReceiver:
        ...


class DefaultManipulators:
    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        return DefaultCommandMatcher(**kwargs)

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        return DefaultCommandCreator(**kwargs)

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        return Split2BytesReadHandler(**kwargs)

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        return DefaultWriteHandler(**kwargs)

    def get_autheticator(self, **kwargs: Unpack[AuthenticatorKwargs]) -> Authenticator:
        return DefaultAuthenticator(**kwargs)

    def get_mover(self, **kwargs: Unpack[MoverKwargs]) -> Mover:
        return DefaultMover(**kwargs)

    def get_receiver(self, **kwargs: Unpack[SecretReceiverKwargs]) -> SecretReceiver:
        return DefaultSecretReceiver(**kwargs)


class RechargingManipulators(DefaultManipulators):
    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        return Recharging2BytesReadHandler(**kwargs)
