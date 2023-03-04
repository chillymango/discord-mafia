from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ConnectRequest(_message.Message):
    __slots__ = ["request_name", "timestamp"]
    REQUEST_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    request_name: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., request_name: _Optional[str] = ...) -> None: ...

class ConnectResponse(_message.Message):
    __slots__ = ["bot_id", "bot_name", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    BOT_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    bot_name: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_name: _Optional[str] = ..., bot_id: _Optional[str] = ...) -> None: ...

class DisconnectRequest(_message.Message):
    __slots__ = ["bot_id", "leave_game", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    LEAVE_GAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    leave_game: bool
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ..., leave_game: bool = ...) -> None: ...

class DisconnectResponse(_message.Message):
    __slots__ = ["success", "timestamp"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    success: bool
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., success: bool = ...) -> None: ...
