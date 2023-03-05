"""
This manages the town's interface during the day.

This should include:
* input controllers
* chat permission handling
* thread creation
"""
from enum import Enum
import typing as T

if T.TYPE_CHECKING:
    import disnake


class TownHall:

    class State(Enum):
        CLOSED = 0
        OPEN = 1

    def __init__(self, guild: "disnake.Guild") -> None:
        self._guild = guild
        self.ch_bulletin: "disnake.TextChannel" = None
        self.ch_town_hall: "disnake.TextChannel" = None

    async def create_lobby_channel(self) -> None:
        self.ch_lobby = await self._guild.create_text_channel(name="mafia-lobby", reason="Creating a Mafia Lobby")

    async def create_town_hall_channel(self) -> None:
        self.ch_town_hall = await self._guild.create_text_channel(name="mafia-town-hall", reason="Starting Mafia Game")

    async def create_bulletin_channel(self) -> None:
        self.ch_bulletin = await self._guild.create_text_channel(name="mafia-bulletin", reason="Starting Mafia Game")

    async def setup_lobby(self) -> None:
        # create the text channels
        self.ch_bulletin = await self._guild.create_text_channel(name="mafia-bulletin", reason="Starting Mafia Game")
        self.ch_town_hall = await self._guild.create_text_channel
