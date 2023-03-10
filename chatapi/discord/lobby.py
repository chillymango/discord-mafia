import asyncio
import random
import typing as T
import disnake

from chatapi.app.bot import BotUser
from chatapi.app.bot_api import BotApi
from chatapi.app.grpc.run import run_grpc_server
from chatapi.discord.channel import channel_manager
from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.driver import DiscordDriver
from chatapi.discord.driver import WebhookDriver
from chatapi.discord.forward import ForwardChatMessages
from chatapi.discord.input_panel import InputPanel
from chatapi.discord.input_panel import InputController
from chatapi.discord.panel import LobbyPanel
from chatapi.discord.router import router
from chatapi.discord.view import ViewController
from engine.message import Messenger
from engine.game import Game
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import RoleFactory
from engine.session import Session
from engine.setup import do_setup
from engine.setup import EXAMPLE_CONFIG
from engine.stepper import sleep_override
from engine.stepper import Stepper

if T.TYPE_CHECKING:
    from disnake.ext.commands import Bot
    from chatapi.discord.router import Router


class JoinButton(disnake.ui.Button):
    """
    Override callback to attempt to join game

    This is a composite object nested inside Lobby
    """

    async def callback(self, interaction: "disnake.Interaction") -> None:
        print('I WAS CALLED')
        await interaction.send("I acknowledge that you pressed the button")

total_set = [
    # Basketball
    #"Damian Lillard",
    #"Kevin Durant",
    #"Steph Curry",
    #"LeBron James",
    # Anime
    #"Goku",
    #"Vegeta",
    #"Simon the Digger",
    #"Kamina",
    #"Yoko",
    # ROTK
    #"Zhuge Liang",
    #"Liu Bei",
    #"Cao Cao",
    #"Sun Quan",
    #"Zhou Yu",
    #"Zhao Yun",
    #"Dong Zhuo",
    #"Yuan Shao",
    #"Yuan Shu",
    #"Gongsun Zan",
    # Famous Generals
    #"Napoleon Bonaparte",
    #"Arthur Wellington",
    #"Alexander the Great",
    # US Presidents
    "George Washington",
    "Thomas Jefferson",
    "James Madison",
    "Abraham Lincoln",
    "Theodore Roosevelt",
    "William McKinley",
    "Grover Cleveland",
    "Woodrow Wilson",
    "Franklin D. Roosevelt",
    "Harry Truman",
    "Dwight D. Eisenhower",
    "John F. Kennedy",
    "Richard Nixon",
    "Jimmy Carter",
    "George H.W. Bush",
    "Bill Clinton",
    "George W. Bush",
    "Barack Obama",
    "Donald Trump",
    "Joe Biden",
]
random.shuffle(total_set)
BOT_NAMES = set(total_set)


class LobbyState:
    OPEN = 0
    STARTED = 1
    CLOSED = 2


class NewLobby:
    """
    Uhhh yeah the old one's got a bunch of cruft since I just hacked things
    where they fit
    """

    def __init__(self, guild: "disnake.Guild", channel: "disnake.TextChannel",  debug: bool = False):
        self._channel = channel
        self._guild = guild
        self._debug = debug
        self.users: T.List[T.Union["disnake.User", "BotUser"]] = list()
        self.players: T.Dict[T.Union["disnake.User", "BotUser"], Player] = dict()
        self.panel = LobbyPanel(self._channel, self.users, debug=debug)

        self.state = LobbyState.OPEN

        self._session = None

        self._register_callbacks()

    def _register_callbacks(self) -> None:
        #self._router.register_button_custom_callback("advance_game", self.debug_advance_game)
        router.register_button_custom_callback("join", self.add_player)
        router.register_button_custom_callback("leave", self.remove_player)
        router.register_button_custom_callback("start", self.start_game)
        router.register_button_custom_callback("close", self.close_lobby)
        router.register_button_custom_callback("add_bot", self.add_bot)
        router.register_button_custom_callback("remove_bot", self.remove_bot)

    def validate(self, interaction: "disnake.Interaction") -> bool:
        """
        Check first to ensure that lobby host is issuing command
        """
        if interaction.user != self.host:
            return False
        return True

    @property
    def host(self) -> None:
        """
        First non-bot player
        """
        humans = [u for u in self.users if isinstance(u, disnake.Member) or isinstance(u, disnake.User)]
        if not humans:
            return None
        return humans[0]

    async def add_player(self, interaction: "disnake.Interaction") -> None:
        user = interaction.user
        if user in self.users:
            await interaction.send("Already in lobby", ephemeral=True, delete_after=5.0)
        else:
            self.users.append(user)
            if user not in self.players:
                self.players[user] = Player.create_from_user(user)
            await interaction.response.defer()
            await interaction.send(
                "You have successfully joined the lobby.",
                ephemeral=True,
                # NOTE: do not make this a defer, we need at least a response
                delete_after=0.0,
            )
            await self.panel.drive()

    async def remove_player(self, interaction: "disnake.Interaction") -> None:
        user = interaction.user
        if user not in self.users:
            await interaction.send("Not in lobby", ephemeral=True, delete_after=5.0)
        else:
            self.users.remove(user)
            player = self.players[user]

            await interaction.send("You have successfully left the lobby", ephemeral=True)
            await self.panel.drive()

    async def start_game(self, interaction: "disnake.Interaction") -> None:
        # TODO: add support to specify config
        if not self.validate(interaction):
            print(f"someone naughty: {interaction.user.name}")
            await interaction.send("Command only available to lobby host", ephemeral=True, delete_after=5.0)
            return
        self._session = Session(self._guild)
        players = []
        for user in self.users:
            if self.players.get(user):
                players.append(self.players[user])
            else:
                if isinstance(user, BotUser):
                    players.append(Player.create_from_bot(user))
                else:
                    players.append(Player.create_from_user(user))
        
        self._session.add_players(*players)
        try:
            await interaction.send("Game started!")
        except:
            # we don't care actually?
            pass

        await self.panel.close()

        # this just blocks until the game ends
        self.state = LobbyState.STARTED
        await self._session.start()

    async def close_lobby(self, interaction: "disnake.Interaction") -> None:
        if not self.validate(interaction):
            print(f"someone naughty: {interaction.user.name}")
            await interaction.send("Command only available to lobby host", ephemeral=True, delete_after=5.0)
            return
        self.state = LobbyState.CLOSED
        await interaction.send("Closing lobby")
        await self.panel.delete()

    async def add_bot(self, interaction: "disnake.Interaction") -> None:
        """
        Add a fake bot player, add to 15 for testing I guess
        """
        if not self.validate(interaction):
            print(f"someone naughty: {interaction.user.name}")
            await interaction.send("Command only available to lobby host", ephemeral=True, delete_after=5.0)
            return

        bots_to_add = 15 - len(self.users)
        for _ in range(bots_to_add):
            name = BOT_NAMES.pop()
            bot_user = BotUser(name)
            self.users.append(bot_user)
        await self.panel.drive()
        await interaction.response.defer()
        #await interaction.send(f"Added bot players", ephemeral=True, delete_after=0.0)

    async def remove_bot(self, interaction: "disnake.Interaction") -> None:
        """
        Remove a fake bot player
        """
        if not self.validate(interaction):
            import pdb; pdb.set_trace()
            print(f"someone naughty: {interaction.user.name}")
            await interaction.send("Command only available to lobby host", ephemeral=True, delete_after=5.0)
            return

        # remove from bot list and roster
        removed = self.bots.pop()
        self.roster.remove(removed)

        # recycle name into bot pool
        removed_name = removed.name
        BOT_NAMES.add(removed_name)

        # re-render
        await self.update_lobby()
        await interaction.send(f"Removed bot {removed_name}", ephemeral=True, delete_after=10.0)

    @property
    def bots(self) -> T.List["BotUser"]:
        return [user for user in self.users if isinstance(user, BotUser)]

    @property
    def humans(self) -> T.List["disnake.User"]:
        return [user for user in self.users if isinstance(user, disnake.User)]
