from enum import Enum

from common.config import CMD_POSTFIX


class TextLength:
    """Object to represent a command. Created either from given length or given message text.
    Also calculates length of the message with postfix.
    """

    __slots__ = ("cmd_text", "max_len", "max_len_postfix")

    def __init__(self, val: int | str) -> None:
        """Initializes TextLength object. If string is given, lengthes are calculated from it,
        if length (without CMD_POSTFIX_B) if given, cmd_text is an empty string.

        Args:
            val (int | str): Command text or command length.
        """
        self.cmd_text: str = val if isinstance(val, str) else ""
        self.max_len: int = val if isinstance(val, int) else len(self.cmd_text)
        self.max_len_postfix: int = self.max_len + len(CMD_POSTFIX)


class ClientCommand(TextLength, Enum):
    """Enum of robot commands."""

    CLIENT_USERNAME = 18
    CLIENT_KEY_ID = 3
    CLIENT_CONFIRMATION = 5
    CLIENT_OK = 10
    CLIENT_RECHARGING = "RECHARGING"
    CLIENT_FULL_POWER = "FULL POWER"
    CLIENT_MESSAGE = 98


class ServerCommand(TextLength, Enum):
    """Enum of server commands."""

    SERVER_CONFIRMATION = 5
    SERVER_MOVE = "102 MOVE"
    SERVER_TURN_LEFT = "103 TURN LEFT"
    SERVER_TURN_RIGHT = "104 TURN RIGHT"
    SERVER_PICK_UP = "105 GET MESSAGE"
    SERVER_LOGOUT = "106 LOGOUT"
    SERVER_KEY_REQUEST = "107 KEY REQUEST"
    SERVER_OK = "200 OK"
    SERVER_LOGIN_FAILED = "300 LOGIN FAILED"
    SERVER_SYNTAX_ERROR = "301 SYNTAX ERROR"
    SERVER_LOGIC_ERROR = "302 LOGIC ERROR"
    SERVER_KEY_OUT_OF_RANGE_ERROR = "303 KEY OUT OF RANGE"
