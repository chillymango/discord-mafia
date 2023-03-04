from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ["message", "source", "timestamp"]
    class MessageSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    GAME: Message.MessageSource
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PRIVATE: Message.MessageSource
    PUBLIC: Message.MessageSource
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    message: str
    source: Message.MessageSource
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., source: _Optional[_Union[Message.MessageSource, str]] = ..., message: _Optional[str] = ...) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ["bot_id", "loud", "message", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    LOUD_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    loud: bool
    message: Message
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ..., message: _Optional[_Union[Message, _Mapping]] = ..., loud: bool = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ["error", "success", "timestamp"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    error: str
    success: bool
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., success: bool = ..., error: _Optional[str] = ...) -> None: ...

class SubscribeMessagesRequest(_message.Message):
    __slots__ = ["bot_id", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ...) -> None: ...

class SubscribeMessagesResponse(_message.Message):
    __slots__ = ["messages", "timestamp"]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...

class UnsubscribeMessagesRequest(_message.Message):
    __slots__ = ["bot_id", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ...) -> None: ...

class UnsubscribeMessagesResponse(_message.Message):
    __slots__ = ["error", "success", "timestamp"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    error: str
    success: bool
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., success: bool = ..., error: _Optional[str] = ...) -> None: ...
