from typing import Protocol, Unpack

from server.command_handlers.command_creator import CommandCreator, CommandCreatorKwargs, DefaultCommandCreator
from server.command_handlers.command_matcher import CommandMatcher, CommandMatcherKwargs, DefaultCommandMatcher
from server.socket_handlers.read_handler import ReadHandler, ReadHandlerKwargs, Split2BytesReadHandler
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


class DefaultManipulators:
    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        return DefaultCommandMatcher(**kwargs)

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        return DefaultCommandCreator(**kwargs)

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        return Split2BytesReadHandler(**kwargs)

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        return DefaultWriteHandler(**kwargs)
