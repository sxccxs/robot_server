from typing import Protocol, Unpack

from server.command_handlers.command_creator import CommandCreator, CommandCreatorKwargs
from server.command_handlers.command_matcher import CommandMatcher, CommandMatcherKwargs
from server.socket_handlers.read_handler import ReadHandler, ReadHandlerKwargs
from server.socket_handlers.write_handler import WriteHandler, WriteHandlerKwargs


class Manipulators(Protocol):
    def get_matcher(self, **kwargs: Unpack[CommandMatcherKwargs]) -> CommandMatcher:
        ...

    def get_creator(self, **kwargs: Unpack[CommandCreatorKwargs]) -> CommandCreator:
        ...

    def get_reader(self, **kwargs: Unpack[ReadHandlerKwargs]) -> ReadHandler:
        ...

    def get_writer(self, **kwargs: Unpack[WriteHandlerKwargs]) -> WriteHandler:
        ...
