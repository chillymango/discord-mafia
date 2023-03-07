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

from chatapi.discord.channel import channel_manager
from chatapi.discord.panel import GamePanel
from chatapi.discord.panel import GraveyardPanel
from chatapi.discord.panel import DayPanel
from chatapi.discord.panel import TribunalPanel
from chatapi.discord.panel import NightPanel
from chatapi.discord.panel import WelcomePanel
from chatapi.discord.permissions import LIVE_PLAYER
from chatapi.discord.permissions import MAFIA_LIVE
from chatapi.discord.permissions import PermissionsManager
from engine.phase import TurnPhase

if T.TYPE_CHECKING:
    from engine.game import Game


class TownHall:
    """
    Primary chat interface
    """

    def __init__(self, game: "Game", guild: "disnake.Guild") -> None:
        self._game = game
        self._guild = guild
        self._prev_state: TurnPhase = None
        self._open = False
        self.ch_bulletin: "disnake.TextChannel" = channel_manager.get_channel("mafia-bulletin")
        self.ch_town_hall: "disnake.TextChannel" = None
        self._discussion_thread = None
        self._permission_manager = PermissionsManager(self._guild)

        self._live_players_role: "disnake.Role" = None
        self._mafia_live_role: "disnake.Role" = None

        # unique to the guild we're playing the game in
        self._user_to_member: T.Dict["disnake.User", "disnake.Member"] = dict()

        # TODO: caching like this is dumb
        self._live_players: T.Set["disnake.Member"] = set()
        self._mafia_live: T.Set["disnake.Member"] = set()

    def initialize(self) -> None:
        # initialize everything up front
        # when appropriate we bump the message by re-sending it
        # and otherwise we just edit the message
        if self.ch_bulletin is None:
            raise ValueError("No bulletin channel created yet")

        self._welcome = {
            actor: WelcomePanel(actor, self._game, self.ch_bulletin)
            for actor in self._game.get_actors() if actor.player.is_human
        }
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

    async def display_welcome(self) -> None:
        await asyncio.gather(*[panel.drive() for panel in self._welcome.values()])

    async def prepare_for_game(self) -> None:
        """
        Lock the primary bulletin channel
        Assign correct users to the Live Players permissions group        
        """
        roles = await self._permission_manager.setup_roles()
        self._live_players_role = roles[LIVE_PLAYER]
        self._mafia_live_role = roles[MAFIA_LIVE]

        # town hall channels
        default_permission = disnake.PermissionOverwrite()
        default_permission.send_messages = False
        default_permission.send_messages_in_threads = False
        live_players_permission = disnake.PermissionOverwrite()
        live_players_permission.send_messages = False
        live_players_permission.send_messages_in_threads = True
        # we lock threads when days expire and always allow live users to comment
        # on current day's thread before it locks
        live_players_permission.send_messages_in_threads = True
        await asyncio.gather(
            self.get_player_members(),
            self.ch_bulletin.edit(overwrites={
                self._guild.default_role: default_permission,
                self._live_players_role: live_players_permission,
            }),
        )
        await asyncio.gather(
            self.update_live_player_permissions(),
            self.update_mafia_player_permissions(),
        )

        # mafia chat channels
        # TODO: cultists / masons as well

    async def get_member_for_user(self, user: "disnake.User") -> None:
        self._user_to_member[user] = await self._guild.fetch_member(user.id)

    async def get_player_members(self) -> None:
        """
        Load Member objects for all players and cache this result for later
        """
        requests = []
        for actor in self._game.get_actors():
            if actor.player.is_bot:
                continue
            requests.append(self.get_member_for_user(actor.player.user))
        await asyncio.gather(*requests)

    async def update_live_player_permissions(self) -> None:
        """
        Add all players to the correct role group and then give that role group

        NOTE: role changes are expensive, don't issue them unless we have to
        TODO: ok we probably shouldn't do this by polling, but for now we can cache
        and assume our requests succeed
        """
        for actor in self._game.get_actors():
            if actor.player.is_bot:
                continue
            member = self._user_to_member[actor.player.user]
            if actor.is_alive:
                if member in self._live_players:
                    continue
                self._live_players.add(member)
                asyncio.create_task(member.add_roles(self._live_players_role))
            else:
                if member not in self._live_players:
                    continue
                self._live_players.discard(member)
                asyncio.create_task(member.remove_roles(self._live_players_role))

    async def update_mafia_player_permissions(self) -> None:
        """
        Mafia players have a dedicated chatroom that's not visible to others
        """

    @property
    def panels(self) -> T.List["GamePanel"]:
        return list(self._daylight.values()) + list(self._night.values()) + \
            [self._graveyard, self._tribunal]

    async def drive(self) -> None:
        """
        Look at game state and make appropriate transitions for panels.

        Panels should be responsible for determining when and what they show.
        The TownHall should just be responsible for calling their updates.

        QUESTION: how does this get triggered?

        Daybreak:
            * day panel should be active

        Daylight:
            * day panel should be active
            * tribunal panel should be active
            * tribunal panel should be controlling
            * if there's a change in eligible day targets (e.g Constable or DF), re-issue the
                day action panel.
        Dusk:
            * both panels should no longer be active

        Night:
            * night panel should be active
        """
        await asyncio.gather(
            *[panel.drive() for panel in self.panels] +
            [self.update_live_player_permissions(), self.update_mafia_player_permissions()]
        )

        # make sure panels update first, then write the discussion thread
        if self._game.turn_phase == TurnPhase.DAYLIGHT and self._discussion_thread is None:
            thread_name = f"Day {self._game.turn_number} Discussion"
            thread_msg = await self.ch_bulletin.send(content=thread_name)
            self._discussion_thread = await self.ch_bulletin.create_thread(name=thread_name, message=thread_msg)
        elif self._game.turn_phase == TurnPhase.DUSK:
            if self._discussion_thread is not None:
                print("Locking discussion thread")
                await self._discussion_thread.edit(archived=True, locked=True)
                self._discussion_thread = None

    @property
    def discussion_thread(self) -> T.Optional["disnake.Thread"]:
        return self._discussion_thread

    async def create_town_hall_channel(self) -> None:
        self.ch_town_hall = await channel_manager.create_channel(self._guild, name="mafia-town-hall")

    async def create_bulletin_channel(self) -> None:
        self.ch_bulletin = await channel_manager.create_channel(self._guild, name="mafia-bulletin")

    async def setup_channels(self) -> None:
        """
        Synchronously set up channels?
        """
        await asyncio.gather(self.create_bulletin_channel(), self.create_town_hall_channel())

    async def create_discussion_thread(self, name: str) -> None:
        """
        Discussion threads are where players can chat and lots of notifications will get sent.
        """
        await self.ch_bulletin.create_thread(name)
