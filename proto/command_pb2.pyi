from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class BoolVoteRequest(_message.Message):
    __slots__ = ["bot_id", "timestamp", "vote"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    VOTE_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    timestamp: float
    vote: bool
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ..., vote: bool = ...) -> None: ...

class BoolVoteResponse(_message.Message):
    __slots__ = ["timestamp"]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ...) -> None: ...

class TargetRequest(_message.Message):
    __slots__ = ["bot_id", "target_name", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    target_name: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ..., target_name: _Optional[str] = ...) -> None: ...

class TargetResponse(_message.Message):
    __slots__ = ["timestamp"]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ...) -> None: ...
