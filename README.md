# Async TCP/IP Server for robots movement

## Annotation

This is an asynchronous TCP/IP Server implementing communication for automatic control of remote robots. Robots connect to the server, log in and the server guides them to the center of coordinate system. At the destination coordinate, server must pick up a secret message from a robot. On the way to the goal, the robots may encounter obstacles that they must avoid. The server can navigate multiple robots simultaneously and implements a flawless communication protocol.

The implementation of the client is not a part of the project (maybe yet).

## Table of contents

- [Detailed specifications](#detailed-specifications)
  - [Authentication](#authentication)
  - [Movement to the target](#movement-to-the-target)
  - [Picking up a secret message](#picking-up-a-secret-message)
  - [Recharging](#recharging)
- [Error situations](#error-situations)
  - [Authentication errors](#authentication-errors)
  - [Syntax errors](#syntax-errors)
  - [Logical errors](#logical-errors)
  - [Timeout](#timeout)
- [Special situations](#special-situations)
- [Server optimization](#server-optimization)
- [Example of the communication](#example-of-the-communication)
- [Requirements](#requirements)
- [Task Reference](#task-reference)
- [License](#license)

## Detailed specifications

The communication between the server and the robots is implemented by a fully text-based protocol. Each command is terminated by a pair of special symbols defined in [`config.py`](/common/config.py) as constant `CMD_POSTFIX`. Default value is "\a\b" (these are two characters '\a' and '\b'). The server must follow the communication protocol exactly, but it must take into account the imperfect firmware of the robots (see the [Special situations section](#special-situations)).

All command are encoded and decoded with `ENCODING` defined in [`config.py`](/common/config.py) file. Default value is ASCII.

Server messages (showed with default message ending):

| Name                          | Message                                 | Description                                                                                      |
| ----------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------ |
| SERVER_CONFIRMATION           | <16-bit number in decimal notation>\a\b | Message with confirmation code. Can contain a maximum of 5 numbers and the termination sequence. |
| SERVER_MOVE                   | 102 MOVE\a\b                            | Command to move one field forward                                                                |
| SERVER_TURN_LEFT              | 103 TURN LEFT\a\b                       | Command to turn left                                                                             |
| SERVER_TURN_RIGHT             | 104 TURN RIGHT\a\b                      | Command to turn right                                                                            |
| SERVER_PICK_UP                | 105 GET MESSAGE\a\b                     | Command to pick up a secret message                                                              |
| SERVER_LOGOUT                 | 106 LOGOUT\a\b                          | Command to terminate the connection after successful message retrieval                           |
| SERVER_KEY_REQUEST            | 107 KEY REQUEST\a\b                     | Server request for Key ID for communication                                                      |
| SERVER_OK                     | 200 OK\a\b                              | Positive acknowledgement                                                                         |
| SERVER_LOGIN_FAILED           | 300 LOGIN FAILED\a\b                    | Failed authentication                                                                            |
| SERVER_SYNTAX_ERROR           | 301 SYNTAX ERROR\a\b                    | Message syntax error                                                                             |
| SERVER_LOGIC_ERROR            | 302 LOGIC ERROR\a\b                     | Message sent in a bad situation                                                                  |
| SERVER_KEY_OUT_OF_RANGE_ERROR | 303 KEY OUT OF RANGE\a\b                | Key ID not in expected range                                                                     |

Client messages:
|Name |Message |Description | Example | Max length not including `CMD_POSTFIX` |
|-|-|-|-|-|
|CLIENT_USERNAME |\<user name>\a\b | Message with username. The name can be any sequence of characters except the `CMD_POSTFIX` and will never be identical to the contents of the `CLIENT_RECHARGING` or `CLIENT_FULL_POWER` messages.| Umpa_Lumpa\a\b| 18|
|CLIENT_KEY_ID |\<Key ID>\a\b | Message containing Key ID. It can only contain an integer of up to three digits. |2\a\b |3 |
|CLIENT_CONFIRMATION |<16-bit number in decimal notation>\a\b | Message with confirmation code. It can contain a maximum of 5 numbers and the termination sequence.| 1009\a\b| 5|
|CLIENT_OK |OK \<x> \<y>\a\b |Acknowledgement of motion execution, where x and y are the integer coordinates of the robot after executing the motion command. | OK -3 -1\a\b| 10|
|CLIENT_RECHARGING |RECHARGING\a\b |The robot started to recharge and stopped responding to messages. | | 10|
|CLIENT_FULL_POWER |FULL POWER\a\b |The robot has recharged and is taking commands again. | | 10|
|CLIENT_MESSAGE |\<text>\a\b |The text of the secret message that was picked up. It can be any sequence of characters except the `CMD_POSTFIX` and will never be identical to the contents of the `CLIENT_RECHARGING` or `CLIENT_FULL_POWER` messages. | Haf!\a\b| 98|

Time constants (defined in [`config.py`](/common/config.py)):
|Name | Default value| Description |
|-|-|-|
|TIMEOUT|1|Both the server and the client expect a response from the counterpart for the duration of this interval.|
|TIMEOUT_RECHARGING|5| The time interval during which the robot must finish recharging.|

### Authentication

Server and client both know authentication key pairs defined as `KEYS` in [`config.py`](/common/config.py) (Key ID is determined by the order of pairs).
Example:
|Key ID|Server Key|Client Key|
|-|-|-|
| 0| 23019| 32037|
| 1| 32037| 29295|
| 2| 18789| 13603|
| 3| 16443| 29533|
| 4| 18189| 21952|

Each robot starts communication by sending its username (`CLIENT_USERNAME` message). In the next step, the server prompts the client to send the Key ID (`SERVER_KEY_REQUEST` message), which is actually the identifier of the key pair it wants to use for authentication. The client responds with a `CLIENT_KEY_ID` message, in which it sends the Key ID. After that, the server knows the correct key pair so it can compute a "hash" code from the username using the following formula:

```
Username: Mnau!

ASCII representation: 77 110 97 117 33

Resulting hash: ((77 + 110 + 97 + 117 + 33) * 1000) % 65536 = 40784
```

The resulting hash is a 16-bit number in decimal form. The server then adds the server key to the hash so that if the 16-bit capacity is exceeded, the value simply overflows (the following is an example for Key ID 0):

```
(40784 + 23019) % 65536 = 63803
```

The resulting server confirmation code is sent as text to the client in the `SERVER_CONFIRM` message. The client calculates the hash back from the received code and compares it with the expected hash it calculated from the username. If they match, it generates the client's confirmation code. The calculation of the client confirmation code is similar to that of the server, except that the client key is used (the following is an example for Key ID 0):

```
(40784 + 32037) % 65536 = 7285
```

The client confirmation code is sent to the server in the `CLIENT_CONFIRMATION` message, which calculates the hash back from it and compares it to the original username hash. If the two values match, it sends a `SERVER_OK` message, otherwise it responds with a `SERVER_LOGIN_FAILED` message and terminates the connection. The entire sequence is shown in the following figure:

```
Client                      Server
​------------------------------------------
CLIENT_USERNAME     --->
                    <---    SERVER_KEY_REQUEST
CLIENT_KEY_ID       --->
                    <---    SERVER_CONFIRMATION
CLIENT_CONFIRMATION --->
                    <---    SERVER_OK
                              or
                            SERVER_LOGIN_FAILED
                      .
                      .
                      .
```

The server does not know the usernames in advance. Therefore, robots can choose any name they want, but they must know the key set of both the client and the server. The key pair ensures two-way authentication while preventing the authentication process from being compromised by simply eavesdropping on the communication.

### Movement to the target

The robot can only move straight (`SERVER_MOVE`) and is able to perform a turn in place to the right (`SERVER_TURN_RIGHT`) and to the left (`SERVER_TURN_LEFT`). After each movement command, it sends an acknowledgement (`CLIENT_OK`), which includes the current coordinates.

The position of the robot is not known to the server at the beginning of the communication. The server has to find out the position of the robot (position and direction) only from its responses.

In order to prevent the robot from wandering endlessly in space, each robot has a limited number of movements (only moving forward). The number of movements should be sufficient to reasonably move the robot to the target.

Not the most efficient movement algorithm is used at the moment.

The following is a demonstration of communication:

```
Client                  Server
​------------------------------------------
                  .
                  .
                  .
                <---    SERVER_MOVE
                          or
                        SERVER_TURN_LEFT
                          or
                        SERVER_TURN_RIGHT
CLIENT_OK       --->
                <---    SERVER_MOVE
                          or
                        SERVER_TURN_LEFT
                          or
                        SERVER_TURN_RIGHT
CLIENT_OK --->
                <---    SERVER_MOVE
                          or
                        SERVER_TURN_LEFT
                          or
                        SERVER_TURN_RIGHT
                  .
                  .
                  .
```

Just after authentication, the robot expects at least one motion command - `SERVER_MOVE`, `SERVER_TURN_LEFT` or `SERVER_TURN_RIGHT`. You cannot try to pick up the secret right away. There are many obstacles along the way that robots must overcome by detouring. The following rules apply to the obstacles:

- An obstacle always occupies a single coordinate.
- It is guaranteed that each obstacle has all eight surrounding coordinates free (i.e., it can always be easily bypassed).
- It is guaranteed that an obstacle never occupies the coordinate [0,0].
- If the robot hits an obstacle more than 20 times, it will be damaged and terminate the connection.

The obstacle is detected so that the robot is instructed to move forward (`SERVER_MOVE`), but no coordinate change occurs (the `CLIENT_OK` message contains the same coordinates as in the previous step). If the move is not executed, there is no subtraction from the number of remaining robot steps.

Example of communication:

### Picking up a secret message

After the robot reaches the target coordinate [0,0], it attempts to pick up the secret message (`SERVER_PICK_UP` message). If the robot is asked to pick up the message and is not at the target coordinate, the robot self-destructs and communication with the server is interrupted. When the robot attempts to pick up at the target coordinate, it responds with a `CLIENT_MESSAGE` message. The server must respond to this message with a `SERVER_LOGOUT` message. (It is guaranteed that the secret message never matches the `CLIENT_RECHARGING` message, if this message is received by the server after the pick up request it is always a recharge.) Then both the client and the server terminate the connection. Example of message pickup communication:

```
Client                  Server
​------------------------------------------
                  .
                  .
                  .
                <---    SERVER_PICK_UP
CLIENT_MESSAGE  --->
                <---    SERVER_LOGOUT
```

### Recharging

Each of the robots has a limited power source. If it starts to run out of battery, it will notify the server and then start recharging itself from the solar panel. It doesn't respond to any messages while it's recharging. When it finishes, it informs the server and resumes where it left off before recharging. If the robot does not finish recharging within the `TIMEOUT_RECHARGING` interval, the server terminates the connection.

```
Client                    Server
​------------------------------------------
CLIENT_USERNAME   --->
                  <---    SERVER_CONFIRMATION
CLIENT_RECHARGING --->

      ...

CLIENT_FULL_POWER --->
CLIENT_OK         --->
                  <---    SERVER_OK
                            or
                          SERVER_LOGIN_FAILED
                    .
                    .
                    .
```

Another example:

```
Client                  Server
​------------------------------------------
                    .
                    .
                    .
                  <---    SERVER_MOVE
CLIENT_OK         --->
CLIENT_RECHARGING --->

      ...

CLIENT_FULL_POWER --->
                  <---    SERVER_MOVE
CLIENT_OK         --->
                  .
                  .
                  .
```

## Error situations

Some robots may have corrupted firmware and so may not communicate properly. The server should detect this inappropriate behavior and react correctly.

### Authentication errors

If there is a Key ID in the `CLIENT_KEY_ID` message that is not in expected range, the server responds with a `SERVER_KEY_OUT_OF_RANGE_ERROR` error message and terminates the connection. Negative values are also considered a number. If there is not only number, excluding `CMD_POSTFIX`, in the `CLIENT_KEY_ID` message, the server responds with a `SERVER_SYNTAX_ERROR` error.

If there is a numeric value (my be negative) in the `CLIENT_CONFIRMATION` message, excluding `CMD_POSTFIX` that does not match the expected confirmation, the server sends a `SERVER_LOGIN_FAILED` message and terminates the connection. If it is not an only numeric value, the server sends a `SERVER_SYNTAX_ERROR` message and terminates the connection.

### Syntax errors

The server always responds to a syntax error immediately after receiving the message in which it detected the error. The server sends the `SERVER_SYNTAX_ERROR` message to the robot and then must terminate the connection as soon as possible. Syntactically incorrect messages:

- The incoming message is longer than the number of characters defined for each message. Length for every message is defined in the client message summary table.
- The incoming message does not syntactically match any of the `CLIENT_USERNAME`, `CLIENT_KEY_ID`, `CLIENT_CONFIRMATION`, `CLIENT_OK`, `CLIENT_RECHARGING`, and `CLIENT_FULL_POWER` messages.

### Logical errors

The logical error occurs only during recharging - when the robot sends recharging message (`CLIENT_RECHARGING`) and after that sends any other message than `CLIENT_FULL_POWER` or if it sends `CLIENT_FULL_POWER` message without sending `CLIENT_RECHARGING` first. The server responds to such situations by sending a `SERVER_LOGIC_ERROR` message and terminating the connection immediately.

### Timeout

The protocol for communication with robots contains two types of timeout:

- `TIMEOUT` - timeout for communication. If the robot or server receives no communication from its counterpart (but not necessarily the entire message) during this timeout, it considers the connection lost and terminates it immediately.
- `TIMEOUT_RECHARGING` - timeout for recharging the robot. After the server receives the `CLIENT_RECHARGING` message, the robot must send the `CLIENT_FULL_POWER` message within this time interval at the latest. If the robot fails to do so, the server must immediately terminate the connection.

## Special situations

When communicating over a more complicated network infrastructure, two situations can occur:

- The message may arrive split into several parts that are read sequentially from the socket. (This occurs because of segmentation and possible delay of some segments as they travel through the network.)
- Messages sent in quick succession may arrive almost simultaneously. In a single read from the socket, they may both be read at the same time. (This happens when the server does not have time to read the first message from the buffer before the second message arrives.)

## Server optimization

The server optimizes the protocol by not waiting for the completion of a message that is obviously bad. For example, when prompted for authentication, the robot sends only the username portion of the message. For example, the server receives 22 characters of the username, but still has not received the `CMD_POSTFIX` termination sequence. Since the maximum message length is 20 characters (with default `CMD_POSTFIX`), it is clear that the received message cannot be valid. The server therefore responds by not waiting for the rest of the message, but sends a `SERVER_SYNTAX_ERROR` message and terminates the connection. In principle, it should do the same when retrieving a secret message.

## Example of the communication

```
C: "Oompa Loompa\a\b"
S: "107 KEY REQUEST\a\b"
C: "0\a\b"
S: "64907\a\b"
C: "8389\a\b"
S: "200 OK\a\b"
S: "102 MOVE\a\b"
C: "OK 0 0\a\b"
S: "102 MOVE\a\b"
C: "OK -1 0\a\b"
S: "104 TURN RIGHT\a\b"
C: "OK -1 0\a\b"
S: "104 TURN RIGHT\a\b"
C: "OK -1 0\a\b"
S: "102 MOVE\a\b"
C: "OK 0 0\a\b"
S: "105 GET MESSAGE\a\b"
C: "Secret message.\a\b"
S: "106 LOGOUT\a\b"
```

## Requirements

- Python 3.11.3 (or higher)

## Task Reference

ČVUT, FIT, BI-PSI, semestral work 2023

## License

[MIT](LICENSE)
