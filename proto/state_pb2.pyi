from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Actor(_message.Message):
    __slots__ = ["player", "role"]
    PLAYER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    player: Player
    role: Role
    def __init__(self, player: _Optional[_Union[Player, _Mapping]] = ..., role: _Optional[_Union[Role, _Mapping]] = ...) -> None: ...

class Game(_message.Message):
    __slots__ = ["actors", "game_phase", "graveyard", "tribunal", "turn_number", "turn_phase"]
    ACTORS_FIELD_NUMBER: _ClassVar[int]
    GAME_PHASE_FIELD_NUMBER: _ClassVar[int]
    GRAVEYARD_FIELD_NUMBER: _ClassVar[int]
    TRIBUNAL_FIELD_NUMBER: _ClassVar[int]
    TURN_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TURN_PHASE_FIELD_NUMBER: _ClassVar[int]
    actors: _containers.RepeatedCompositeFieldContainer[Actor]
    game_phase: str
    graveyard: _containers.RepeatedCompositeFieldContainer[Tombstone]
    tribunal: Tribunal
    turn_number: int
    turn_phase: str
    def __init__(self, game_phase: _Optional[str] = ..., turn_phase: _Optional[str] = ..., turn_number: _Optional[int] = ..., actors: _Optional[_Iterable[_Union[Actor, _Mapping]]] = ..., graveyard: _Optional[_Iterable[_Union[Tombstone, _Mapping]]] = ..., tribunal: _Optional[_Union[Tribunal, _Mapping]] = ...) -> None: ...

class GetActorRequest(_message.Message):
    __slots__ = ["bot_id", "player_name", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    player_name: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ..., player_name: _Optional[str] = ...) -> None: ...

class GetActorResponse(_message.Message):
    __slots__ = ["actor", "timestamp"]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    actor: Actor
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ...) -> None: ...

class GetGameRequest(_message.Message):
    __slots__ = ["bot_id", "timestamp"]
    BOT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    bot_id: str
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., bot_id: _Optional[str] = ...) -> None: ...

class GetGameResponse(_message.Message):
    __slots__ = ["game", "timestamp"]
    GAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    game: Game
    timestamp: float
    def __init__(self, timestamp: _Optional[float] = ..., game: _Optional[_Union[Game, _Mapping]] = ...) -> None: ...

class Player(_message.Message):
    __slots__ = ["is_bot", "is_human", "name"]
    IS_BOT_FIELD_NUMBER: _ClassVar[int]
    IS_HUMAN_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    is_bot: bool
    is_human: bool
    name: str
    def __init__(self, name: _Optional[str] = ..., is_bot: bool = ..., is_human: bool = ...) -> None: ...

class Role(_message.Message):
    __slots__ = ["action_description", "affiliation", "name", "role_description"]
    ACTION_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    AFFILIATION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ROLE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    action_description: str
    affiliation: str
    name: str
    role_description: str
    def __init__(self, name: _Optional[str] = ..., affiliation: _Optional[str] = ..., role_description: _Optional[str] = ..., action_description: _Optional[str] = ...) -> None: ...

class Tombstone(_message.Message):
    __slots__ = ["epitaph", "player"]
    EPITAPH_FIELD_NUMBER: _ClassVar[int]
    PLAYER_FIELD_NUMBER: _ClassVar[int]
    epitaph: str
    player: Player
    def __init__(self, player: _Optional[_Union[Player, _Mapping]] = ..., epitaph: _Optional[str] = ...) -> None: ...

class Tribunal(_message.Message):
    __slots__ = ["lynch_votes", "skip_votes", "state", "trial_votes"]
    LYNCH_VOTES_FIELD_NUMBER: _ClassVar[int]
    SKIP_VOTES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TRIAL_VOTES_FIELD_NUMBER: _ClassVar[int]
    lynch_votes: _containers.RepeatedCompositeFieldContainer[VoteCount]
    skip_votes: int
    state: str
    trial_votes: _containers.RepeatedCompositeFieldContainer[VoteCount]
    def __init__(self, state: _Optional[str] = ..., trial_votes: _Optional[_Iterable[_Union[VoteCount, _Mapping]]] = ..., lynch_votes: _Optional[_Iterable[_Union[VoteCount, _Mapping]]] = ..., skip_votes: _Optional[int] = ...) -> None: ...

class VoteCount(_message.Message):
    __slots__ = ["count", "player"]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    PLAYER_FIELD_NUMBER: _ClassVar[int]
    count: int
    player: Player
    def __init__(self, player: _Optional[_Union[Player, _Mapping]] = ..., count: _Optional[int] = ...) -> None: ...
