"""
This manages the town's interface during the day.

This should include:
* input controllers
* chat permission handling
* thread creation
"""
import asyncio
from enum import Enum
import disnake
import typing as T

from chatapi.discord.panel import GraveyardPanel
from chatapi.discord.panel import DayPanel
from chatapi.discord.panel import TribunalPanel
from chatapi.discord.panel import NightPanel

if T.TYPE_CHECKING:
    from engine.game import Game


class TownHall:
    """
    Primary chat interface
    """

    def __init__(self, game: "Game", guild: "disnake.Guild") -> None:
        self._game = game
        self._guild = guild
        self._open = False
        self.ch_bulletin: "disnake.TextChannel" = None
        self.ch_town_hall: "disnake.TextChannel" = None

        # initialize everything up front
        # when appropriate we bump the message by re-sending it
        # and otherwise we just edit the message
        self._graveyard = GraveyardPanel(self._game, self.ch_bulletin)
        self._daylight = {
            actor: DayPanel(actor, self._game, self.ch_bulletin)
            for actor in self._game.get_actors() if actor.player.is_human
        }
        self._tribunal = TribunalPanel(self._game, self.ch_bulletin)
        self._night = {
            actor: NightPanel(actor, self._game, self.ch_bulletin)
            for actor in self._game.get_actors() if actor.player.is_human
        }

    async def create_lobby_channel(self) -> None:
        self.ch_lobby = await self._guild.create_text_channel(name="mafia-lobby", reason="Creating a Mafia Lobby")

    async def create_town_hall_channel(self) -> None:
        self.ch_town_hall = await self._guild.create_text_channel(name="mafia-town-hall", reason="Starting Mafia Game")

    async def create_bulletin_channel(self) -> None:
        self.ch_bulletin = await self._guild.create_text_channel(name="mafia-bulletin", reason="Starting Mafia Game")

    async def setup_lobby(self) -> None:
        await self.create_lobby_channel()

    async def setup_channels(self) -> None:
        """
        Synchronously set up channels?
        """
        await asyncio.gather(self.create_bulletin_channel(), self.create_town_hall_channel())
