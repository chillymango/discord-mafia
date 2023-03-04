import asyncio
import random
import typing as T
import disnake

from chatapi.app.bot import BotUser
from chatapi.app.bot_api import BotApi
from chatapi.app.grpc.run import run_grpc_server
from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.driver import DiscordDriver
from chatapi.discord.driver import WebhookDriver
from chatapi.discord.forward import ForwardChatMessages
from chatapi.discord.input_panel import InputPanel
from chatapi.discord.input_panel import InputController
from chatapi.discord.view import ViewController
from engine.message import Messenger
from engine.game import Game
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import RoleFactory
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
    "Damian Lillard",
    "Kevin Durant",
    "Steph Curry",
    "LeBron James",
    "Goku",
    "Vegeta",
    "Simon the Digger",
    "Kamina",
    "Yoko",
    "Zhuge Liang",
    "Liu Bei",
    "Cao Cao",
    "Sun Quan",
    "Zhou Yu",
    "Zhao Yun",
    "Dong Zhuo",
    "Yuan Shao",
    "Yuan Shu",
    "Gongsun Zan",
    "Napoleon Bonaparte",
    "Arthur Wellington",
    "George Washington",
    "Alexander the Great",
    "Joe Biden",
    "Donald Trump",
    "Barack Obama",
    "George W. Bush",
    "Bill Clinton",
    "George H.W. Bush",
]
random.shuffle(total_set)
BOT_NAMES = set(total_set)


class LobbyState:
    OPEN = 0
    STARTED = 1
    CLOSED = 2


class Lobby:
    """
    This should encapsulate all logic pertaining to managing and updating
    a lobby representation.
    """

    def __init__(self, router: "Router", debug: bool = False) -> None:
        print('Creating lobby?')
        # cache last interaction so we can keep sending messages to it
        self._interaction_cache: T.Dict[disnake.User, disnake.Interaction] = dict()
        # cache last message so we can delete it when refreshing
        self._message_cache: T.Dict[disnake.User, disnake.Message] = dict()
        # uh
        self._view_controller: ViewController = None

        self._server_task: asyncio.Task = None
        self._router = router
        self._discord_driver: DiscordDriver = None
        self._webhook_driver: WebhookDriver = None
        self.town_hall: disnake.TextChannel = None
        self.bulletin: disnake.TextChannel = None
        self._guild: disnake.Guild = None
        self.state = LobbyState.OPEN

        self._stepper: Stepper = None
        self._skipper: Stepper = None

        self._debug = debug
        self._game: Game = None

        self._lobby_message: disnake.Message = None
        self.lobby_message: T.Dict[str, T.Any] = dict()
        self.users: T.List[disnake.User] = []
        self.players: T.Dict[disnake.User, Player] = dict()
        self.bots: T.List[Player] = list()
        self.roster: T.List[Player] = list()
        self.pm_channels: T.Dict[disnake.User, disnake.TextChannel] = dict()

        self.construct_lobby_message()

        self._register_callbacks()

    def _register_callbacks(self) -> None:
        self._router.register_button_custom_callback("advance_game", self.debug_advance_game)
        self._router.register_button_general_callback(self.update_interaction_cache)
        self._router.register_button_custom_callback("join", self.add_player)
        self._router.register_button_custom_callback("leave", self.remove_player)
        self._router.register_button_custom_callback("start", self.start_game)
        self._router.register_button_custom_callback("close", self.close_lobby)
        self._router.register_button_custom_callback("add_bot", self.add_bot)
        self._router.register_button_custom_callback("remove_bot", self.remove_bot)

    @property
    def lobby_host(self) -> T.Optional["disnake.User"]:
        """
        First *human* player in lobby is host.

        If lobby is empty (shouldn't happen), there is no host.
        """
        if self.users:
            return self.users[0]
        return None

    def is_lobby_host(self, user: "disnake.User") -> bool:
        return user == self.lobby_host

    async def open_lobby(self, interaction: "disnake.Interaction") -> None:
        """
        Opening a lobby consists of the following actions:
            * create the announcements channel
            * post the lobby info in the announcements channel
        """
        self._guild = interaction.guild
        self.town_hall = await self._guild.create_text_channel(name="mafia-town-hall", reason="Starting Mafia Game")
        self.bulletin = await self._guild.create_text_channel(name="mafia-bulletin", reason="Starting Mafia Game")

    async def close_lobby(self) -> None:
        self.state = LobbyState.CLOSED
        for channel in self.pm_channels.values():
            try:
                await channel.delete(reason="Closing Lobby")
            except:
                pass
        if self.town_hall is not None:
            await self.town_hall.delete(reason="Closing Lobby")
        else:
            print('Town hall was None')
        if self.bulletin is not None:
            await self.bulletin.delete(reason="Closing Lobby")
        else:
            print('Bulletin was None')

    async def add_player(self, interaction: "disnake.Interaction") -> None:
        user = interaction.user
        if user in self.users:
            await interaction.send("Already in lobby", ephemeral=True, delete_after=5.0)
        else:
            self.users.append(user)
            guild = interaction.guild
            self.pm_channels[user] = await guild.create_text_channel(f"mafia-{user.name}")
            if user not in self.players:
                self.players[user] = Player.create_from_user(user)
            if self.players[user] not in self.roster:
                self.roster.append(self.players[user])
            await interaction.send("You have successfully joined the lobby.", ephemeral=True)
            await self.update_lobby()

    async def remove_player(self, interaction: "disnake.Interaction") -> None:
        user = interaction.user
        if user not in self.users:
            await interaction.send("Not in lobby", ephemeral=True, delete_after=5.0)
        else:
            self.users.remove(user)
            player = self.players[user]
            if player in self.roster:
                self.roster.remove(player)

            ch = self.pm_channels.get(user)
            if ch is not None:
                await ch.delete()
            await interaction.send("You have successfully left the lobby", ephemeral=True)
            await self.update_lobby()

    def construct_lobby_message(self) -> T.Dict[str, T.Any]:
        embed = disnake.Embed(title="Mafia Lobby", description="Waiting for players")
        for idx, player in enumerate(self.players):
            embed.add_field(name=f"Player {idx + 1}", value=player.name, inline=False)
        self.lobby_message["embed"] = embed

        # a row for join/leave lobby interaction
        join_leave_row = disnake.ui.ActionRow()

        # TODO: additionally partition this by guild ID or something
        join_leave_row.add_button(style=disnake.ButtonStyle.primary, label="Join Game", custom_id="join")
        join_leave_row.add_button(style=disnake.ButtonStyle.grey, label="Leave Game", custom_id="leave")

        # a row for start lobby interaction maybe?
        start_end_row = disnake.ui.ActionRow()
        start_end_row.add_button(style=disnake.ButtonStyle.green, label="Start Game", custom_id="start")
        start_end_row.add_button(style=disnake.ButtonStyle.red, label="Close Lobby", custom_id="close")

        rows = [join_leave_row, start_end_row]
        if self._debug:
            debug_row = disnake.ui.ActionRow()
            debug_row.add_button(style=disnake.ButtonStyle.danger, label="Add Bot", custom_id="add_bot")
            debug_row.add_button(style=disnake.ButtonStyle.danger, label="Remove Bot", custom_id="remove_bot")
            rows.append(debug_row)
        self.lobby_message["components"] = rows

    async def update_interaction_cache(self, interaction: "disnake.Interaction") -> None:
        self._interaction_cache[interaction.user] = interaction

    async def on_button_click(self, interaction: "disnake.Interaction") -> None:
        # cache the interaction so we can use it later?
        self._interaction_cache[interaction.user] = interaction

        self._seen_interactions[interaction.id] = interaction
        # do not handle interactions more than once???
        if interaction.data.custom_id == "join":
            await self.add_player(interaction, interaction.user)
        elif interaction.data.custom_id == "leave":
            await self.remove_player(interaction, interaction.user)
        elif interaction.data.custom_id == "start":
            await self.start_game(interaction)
        elif interaction.data.custom_id == "close":
            await self.close_lobby()
            await interaction.send("Closed lobby")
        elif interaction.data.custom_id == "add_bot":
            await self.add_bot(interaction)
        elif interaction.data.custom_id == "remove_bot":
            await self.remove_bot(interaction)
        else:
            await interaction.send(f"wtf was clicked? {interaction.data.custom_id}")

    async def add_bot(self, interaction: "disnake.Interaction") -> None:
        """
        Add a fake bot player, add to 15 for testing I guess
        """
        bots_to_add = 15 - len(self.users)
        for _ in range(bots_to_add):
            name = BOT_NAMES.pop()
            bot_player = Player.create_from_bot(BotUser(name))
            self.bots.append(bot_player)
            self.roster.append(bot_player)
        await self.update_lobby()
        await interaction.send(f"Added bot players", ephemeral=True, delete_after=0.0)

    async def remove_bot(self, interaction: "disnake.Interaction") -> None:
        """
        Remove a fake bot player
        """
        # remove from bot list and roster
        removed = self.bots.pop()
        self.roster.remove(removed)

        # recycle name into bot pool
        removed_name = removed.name
        BOT_NAMES.add(removed_name)

        # re-render
        await self.update_lobby()
        await interaction.send(f"Removed bot {removed_name}", ephemeral=True, delete_after=10.0)

    async def update_lobby(self) -> None:
        """
        Lobby is posted in the bulletin channel where it is read-only.
        """
        if not self.users:
            # if there are no more players, just delete everything
            await self.close_lobby()
            return

        if self._lobby_message is not None:
            await self._lobby_message.delete()

        # edit players?
        embed: "disnake.Embed" = self.lobby_message["embed"]
        embed.clear_fields()
        for idx, player in enumerate(self.roster):
            embed.add_field(name=f"Player {idx + 1}", value=player.name, inline=False)

        self._lobby_message = await self.bulletin.send(**self.lobby_message)

    async def drive_updates(self, update: bool = True) -> None:
        """
        Take outputs from input_controller after they've been synthesized and
        issue them back out to all clients

        By default will drive the InputController update first
        """
        if update:
            self._input_controller.drive()

        for user in self.users:
            interaction: "disnake.Interaction" = self._interaction_cache.get(user)
            if interaction is None:
                print(f"Warning: no interaction found for user {user.name}")
                continue
            panel = self._input_controller.get_panel(user)
            to_export = panel.export_to_discord()
            await interaction.send(**to_export, ephemeral=True)

    async def advance_game(self) -> None:
        if self._game is not None and self._skipper is not None:
            await self._skipper.step()
        else:
            print("Cannot skip?")
            return

        if self._input_controller is not None:
            self._input_controller.drive()
            await self.drive_updates()

    async def debug_advance_game(self, interaction: "disnake.Interaction") -> None:
        await self.advance_game()
        await interaction.send("stepped forward one phase", ephemeral=True, delete_after=1.0)

    async def start_game(self, interaction: "disnake.Interaction") -> None:
        """
        Create a game, do role assignments, and yeet the game into the sun
        ...
        Just kidding we create a friendly environment in which the game can survive.
        We will manage that here I guess?
        """
        try:
            await self.inner_start(interaction)
        finally:
            if self._server_task is not None:
                self._server_task.cancel()

    async def inner_start(self, interaction: "disnake.Interaction") -> None:
        from chatapi.discord.mafiabot import grpc_api

        self._game = Game(config=EXAMPLE_CONFIG)
        # start grpc here
        self._server_task = asyncio.ensure_future(run_grpc_server(self._game))

        self._stepper = Stepper(self._game, EXAMPLE_CONFIG)
        self._skipper = Stepper(self._game, EXAMPLE_CONFIG, sleeper=sleep_override)
        self._game.add_players(*self.roster)
        result, msg = do_setup(self._game)

        # override to make me a desired role
        self._game.debug_override_role("chilly mango", "SerialKiller")
        self._game.debug_override_role("asiannub", "Veteran")
        if not result:
            # make this a public facing message if there's a start failure
            print(f"Failed to start game: {msg}")
            await interaction.send(f"Failed to start game: {msg}")
            self._server_task.cancel()
            return

        await interaction.send(f"Starting the game!")

        await self._stepper.step()

        self._input_controller = InputController(self._game, self._router)
        for user in self.users:
            self._input_controller.add_panel(user, debug=self.is_lobby_host(user))

        self._discord_driver = DiscordDriver(self.bulletin, self._interaction_cache, self._input_controller)
        self._webhook_driver = WebhookDriver(self.bulletin)
        print("Setting up Webhook")
        await self._webhook_driver.setup_webhook()
        print("Done setting up Webhook")
        self._bot_driver = BotMessageDriver()
        self._messenger = Messenger(self._game, self._discord_driver, self._bot_driver, self._webhook_driver)
        self._messenger.start_inbound()
        self._game.messenger = self._messenger
        self._message_forwarding = ForwardChatMessages(self._router, self._bot_driver, self._game, self.bulletin)
        self._message_forwarding.enable_forwarding()
        self._view_controller = ViewController(self._input_controller, self._discord_driver, self._interaction_cache)
        self._game.tribunal.view_controller = self._view_controller

        await self.drive_updates()

        # set it to Dusk
        self._game.turn_phase = TurnPhase.DUSK

        # start running turn-by-turn updates?
        while not self._game.concluded:
            # process game loop step
            await self._stepper.step()
            await self._view_controller.drive()
