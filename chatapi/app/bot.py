from uuid import uuid4
from uuid import UUID


class BotUser:

    def __init__(self, name: str, uuid: UUID = None) -> None:
        self._name = name
        self._id: UUID = uuid or uuid4()

    @property
    def id(self) -> str:
        return self._id.hex

    @property
    def name(self) -> str:
        return self._name
